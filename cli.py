"""Typer CLI + the cycle engine that wires the diagram together.

Entry signal + option screener -> risk manager -> execution -> account state
-> position manager. Dry run is the default; --execute is the only way an
order reaches Alpaca (paper endpoint, enforced in broker.py).

Run as: uv run --env-file .env cli.py <command>
"""

from __future__ import annotations

import math
import sys
import time
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path

import typer
from loguru import logger

import broker
import decision_layer
import market_data
import options_screener
import pos_and_risk
import settings
import signals
import sounds
from data_models import (
    Config,
    EntryChoice,
    OpenSpread,
    OrderPlan,
    SpreadQuote,
    SymbolFeatures,
    journal_entries,
    to_json_line,
)

JOURNAL_PATH = Path("logs") / "cycles.jsonl"
MIN_OPTIONS_LEVEL = 3  # spreads need Alpaca options trading level 3
FILL_POLL_TIMEOUT_SECONDS = 20.0
FILL_POLL_INTERVAL_SECONDS = 2.0
ENTRY_ORDER_CANCEL_TIMEOUT_SECONDS = 180.0  # cancel unfilled entry limit orders after 3 minutes
POST_EXIT_COOLDOWN_SECONDS = 600.0  # 10 minute cooldown per symbol after a trade exit

_RECENT_EXITS: dict[str, float] = {}  # symbol -> exit timestamp
_FILLED = ("filled", "FILLED", "partially_filled")
_DEAD = ("canceled", "CANCELED", "expired", "EXPIRED", "rejected", "REJECTED")

app = typer.Typer(add_completion=False, no_args_is_help=True)


def setup_logging() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | <level>{message}</level>",
    )


def append_journal(record: dict) -> None:
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with JOURNAL_PATH.open("a", encoding="utf-8") as handle:
        handle.write(to_json_line(record) + "\n")


def _bootstrap() -> tuple[Config, object, object, object]:
    config = broker.load_config()
    trading, stock_data, option_data = broker.build_clients(config)
    return config, trading, stock_data, option_data


def _screen_spread(
    trading: object,
    option_data: object,
    underlying: str,
    direction: str,
    spot: float,
    clock_time: datetime,
    today,
    exclude_symbols: frozenset[str] = frozenset(),
) -> tuple[SpreadQuote | None, dict]:
    """Fetch chains + snapshots for one underlying and pick the best spread
    across the nearest settings.EXPIRIES_TO_SCREEN eligible expiries.

    `exclude_symbols` are legs we already hold on this underlying. An add must
    never touch them: Alpaca nets positions per contract, so buying a strike we
    are short would shrink the held leg, leave the held spread unpaired, and
    put it beyond the stop/take-profit manager.
    """
    by_expiry = broker.fetch_contracts(trading, underlying, direction, spot, today)
    if exclude_symbols:
        by_expiry = {
            exp: {k: info for k, info in chain.items() if info["symbol"] not in exclude_symbols}
            for exp, chain in by_expiry.items()
        }
    expirations = options_screener.pick_expirations(
        options_screener.liquid_expirations(by_expiry, spot), today
    )
    if not expirations:
        return None, {"no_expiration": 1}
    symbols = [
        info["symbol"] for exp in expirations for info in by_expiry[exp].values()
    ]
    snapshots = broker.fetch_option_snapshots(option_data, symbols)
    chains = {
        exp: {
            strike: broker.leg_quote_from_snapshot(
                info["symbol"],
                strike,
                snapshots.get(info["symbol"]),
                info["open_interest"],
            )
            for strike, info in by_expiry[exp].items()
        }
        for exp in expirations
    }
    return options_screener.select_spread(
        chains, direction, spot, underlying, clock_time
    )


def run_cycle(
    config: Config,
    trading: object,
    stock_data: object,
    option_data: object,
    *,
    execute: bool,
    manual_mode: bool,
    llm_transport: object | None = None,
) -> dict:
    """One full cycle. Returns the journal record (also appended to the journal)."""
    started = datetime.now(timezone.utc)
    cycle_id = started.strftime("%Y%m%d-%H%M%S")
    record: dict = {"cycle_id": cycle_id, "started_at": started, "dry_run": not execute}

    try:
        clock = broker.fetch_clock(trading)
        account = broker.fetch_account_state(trading, config.symbols)
    except broker.BrokerError as error:
        logger.error("cycle aborted: {}", error)
        record["outcome"] = "error"
        record["error"] = str(error)
        append_journal(record)
        return record

    spreads, warnings = pos_and_risk.pair_spreads(account.legs)
    open_risk = pos_and_risk.open_premium_at_risk(spreads)
    record.update(
        {
            "market_open": clock.is_open,
            "equity": account.equity,
            "options_level": account.options_level,
            "open_spreads": [
                f"{s.underlying} {s.expiration} {s.option_type} x{s.qty}"
                for s in spreads
            ],
            "open_risk": open_risk,
            "warnings": warnings
            + [f"unparsed position: {p}" for p in account.unparsed_positions]
            + pos_and_risk.over_cap_warnings(spreads, account.equity),
        }
    )
    for warning in record["warnings"]:
        logger.warning(warning)

    if not clock.is_open:
        logger.info("market closed; nothing to do")
        record["outcome"] = "market_closed"
        append_journal(record)
        return record

    # --- Trading signals: needed by the reversal exit AND the entry side, so they
    # cover the whitelist plus every held underlying (even one removed from the list)
    watch_symbols = tuple(
        dict.fromkeys(config.symbols + tuple(s.underlying for s in spreads))
    )
    try:
        mids = broker.fetch_spot_mids(stock_data, watch_symbols, clock.server_time)
    except broker.BrokerError as error:
        # Exits must still run on a quote outage; entries will gate out naturally.
        logger.error("quote read failed, exits still run, entries blocked: {}", error)
        mids = {symbol: None for symbol in watch_symbols}
    features = _build_trading_signals(
        watch_symbols, config, stock_data, mids, clock.server_time
    )

    # --- Position manager: mechanical exits run before entries and are never gated ---
    exits: list[dict] = []
    exiting: set[str] = set()  # underlyings with an exit this cycle: never add to those
    if spreads:
        leg_symbols = [
            s for spread in spreads for s in (spread.long_symbol, spread.short_symbol)
        ]
        try:
            snapshots = broker.fetch_option_snapshots(option_data, leg_symbols)
        except broker.BrokerError as error:
            logger.error("exit snapshot read failed: {}", error)
            snapshots = {}
        for spread in spreads:
            long_q = broker.leg_quote_from_snapshot(
                spread.long_symbol, 0.0, snapshots.get(spread.long_symbol), None
            )
            short_q = broker.leg_quote_from_snapshot(
                spread.short_symbol, 0.0, snapshots.get(spread.short_symbol), None
            )
            opposing = (
                spread.underlying in features
                and pos_and_risk.opposing_event_fired(
                    spread, features[spread.underlying].events
                )
            )
            decision = pos_and_risk.exit_decision(
                spread,
                long_q,
                short_q,
                clock.server_time.date(),
                opposing_event=opposing,
            )
            if decision is None:
                if spread.net_entry_debit is None:
                    logger.warning(
                        "cannot compute stop/TP for {} (unknown entry debit)",
                        spread.underlying,
                    )
                continue
            entry: dict = {
                "spread": f"{spread.underlying} {spread.expiration} {spread.option_type}",
                "reason": decision.reason,
                "net_mark": decision.net_mark,
            }
            if {spread.long_symbol, spread.short_symbol} & account.open_order_symbols:
                entry["skipped"] = "pending_order"
            else:
                plan = options_screener.build_exit_plan(
                    spread, long_q, short_q, cycle_id
                )
                if plan is None:
                    entry["skipped"] = "no_quote"
                else:
                    entry["receipt"] = _settle(trading, plan, execute)
            if entry.get("receipt", {}).get("submitted"):
                _RECENT_EXITS[spread.underlying] = time.monotonic()
            exits.append(entry)
            exiting.add(spread.underlying)
            logger.info(
                "exit {}: {}",
                entry["spread"],
                entry.get("receipt", entry.get("skipped")),
            )
    record["exits"] = exits

    # --- Entry candidates: whitelist symbols only ---
    whitelist_features = {symbol: features[symbol] for symbol in config.symbols}
    pending = {
        pos_and_risk.parse_occ(sym)[0]
        for sym in account.open_order_symbols
        if pos_and_risk.parse_occ(sym) is not None
    }
    now_ts = time.monotonic()
    held_by_underlying: dict[str, list[OpenSpread]] = {}
    for spread in spreads:
        held_by_underlying.setdefault(spread.underlying, []).append(spread)
    candidates = []
    for c in signals.build_candidates(
        whitelist_features, clock.is_open, config.bar_seconds
    ):
        if c.gate_block is None:
            c = _gate_held(
                c,
                held_by_underlying.get(c.symbol, []),
                pending=c.symbol in pending,
                exiting=c.symbol in exiting,
            )
        if c.gate_block is None and (now_ts - _RECENT_EXITS.get(c.symbol, 0.0) < POST_EXIT_COOLDOWN_SECONDS):
            c = replace(c, gate_block="post_exit_cooldown")
        candidates.append(c)
    record["candidates"] = [
        {
            "symbol": c.symbol,
            "mid": c.mid,  # journaled so the post-close review can grade decisions against later prices
            "events": [e.kind for e in c.events],
            "rsi": c.rsi,
            "atr": c.atr,
            "macd_hist": c.macd_hist,
            "ema_fast_dist": c.ema_fast_dist,
            "ema_slow_dist": c.ema_slow_dist,
            "held": c.held,
            "gate_block": c.gate_block,
        }
        for c in candidates
    ]
    tradeable = [c for c in candidates if c.gate_block is None]
    logger.info("candidates passing gates: {}", [c.symbol for c in tradeable] or "none")

    # --- Decision + screener + risk + execution ---
    # One decision at a time; ask again with the remaining candidates until the
    # cycle has placed floor(per_cycle / per_entry) entries (2 with the shipped
    # settings), the decider passes, or candidates run out. Rejected attempts
    # (no spread, risk caps, recheck) consume their symbol but not a slot.
    max_entries = max(
        1, math.floor(settings.PER_CYCLE_FRACTION / settings.PER_ENTRY_FRACTION)
    )
    entries: list[dict] = []
    record["entries"] = entries
    cycle_spent = 0.0  # premium committed by earlier entries in this cycle
    planned = 0
    remaining = list(tradeable)
    while remaining and planned < max_entries:
        choice = _decide(remaining, config, manual_mode, llm_transport)
        if choice is None:
            break
        remaining = [c for c in remaining if c.symbol != choice.symbol]
        held = held_by_underlying.get(choice.symbol, [])
        if held and choice.direction != pos_and_risk.held_direction(held):
            # Deterministic guard: an add must follow the held spread's direction,
            # whatever the decider (LLM or human) replied.
            entry = {
                "symbol": choice.symbol,
                "direction": choice.direction,
                "thesis": choice.thesis,
                "model": choice.model,
                "rejected": "opposes_held_spread",
            }
            logger.info(
                "entry refused: {} {} opposes the held spread", choice.symbol, choice.direction
            )
        else:
            entry = _attempt_entry(
                choice,
                features[choice.symbol].mid,
                config,
                trading,
                option_data,
                account.equity,
                open_risk,
                pos_and_risk.open_premium_at_risk(held),
                account.open_order_symbols,
                cycle_id,
                execute,
                cycle_spent=cycle_spent,
                exclude_symbols=frozenset(
                    leg for s in held for leg in (s.long_symbol, s.short_symbol)
                ),
            )
        entries.append(entry)
        receipt = entry.get("receipt") or {}
        if receipt.get("submitted") or receipt.get("dry_run"):
            cycle_spent += entry["premium"]
            planned += 1

    submitted = any(
        (e.get("receipt") or {}).get("submitted") for e in exits + entries
    )
    record["outcome"] = (
        "submitted"
        if submitted
        else ("planned" if not execute and (exits or entries) else "hold")
    )

    # Rich hold reason — makes it easy to see exactly why no entry was taken
    if record["outcome"] == "hold":
        if not candidates:
            record["hold_reason"] = "no_candidates"
        elif not tradeable:
            blocking = {c.gate_block for c in candidates if c.gate_block}
            record["hold_reason"] = sorted(blocking)[0] if blocking else "all_gated"
        elif choice is None:
            from decision_layer import compute_quantitative_edge_score
            has_quant_edge = any(
                compute_quantitative_edge_score(c) >= 0.55 for c in tradeable
            )
            if not has_quant_edge:
                record["hold_reason"] = "insufficient_quantitative_edge"
            else:
                record["hold_reason"] = "llm_pass"
        else:
            record["hold_reason"] = "entry_rejected_by_risk"
        logger.info("hold_reason: {}", record["hold_reason"])

    append_journal(record)
    return record


def _gate_held(
    c: SymbolFeatures, held: list[OpenSpread], *, pending: bool, exiting: bool
) -> SymbolFeatures:
    """Entry gates for an underlying we already hold or have an open order on.

    allow_stacking off: any held or pending underlying is out (already_held).
    allow_stacking on: a further entry is allowed only as an ADD in the held
    spread's direction — a pending order or a same-cycle exit still blocks,
    events against the held direction are dropped, and the candidate carries
    the held direction so the decider knows it is adding.
    """
    if not held and not pending:
        return c
    if not settings.ALLOW_STACKING:
        return replace(c, gate_block="already_held")
    if pending:
        return replace(c, gate_block="pending_order")
    if exiting:
        return replace(c, gate_block="exiting")
    direction = pos_and_risk.held_direction(held)  # None = mixed book, no add
    aligned = tuple(e for e in c.events if e.direction == direction)
    if not aligned:
        return replace(c, gate_block="opposing_held", held=direction)
    return replace(c, events=aligned, held=direction)


def _build_trading_signals(
    symbols: tuple[str, ...],
    config: Config,
    stock_data: object,
    mids: dict,
    now: datetime,
) -> dict[str, SymbolFeatures]:
    """Create the trading signals: OHLCV -> RSI/ATR/MACD -> events, per symbol.

    A failed symbol is marked data_error and skipped, never invented — one bad
    symbol must not kill the cycle.
    """
    features: dict[str, SymbolFeatures] = {}
    for symbol in symbols:
        try:
            frame = market_data.fetch_ohlcv(
                stock_data, symbol, config.bar_timeframe, now
            )
            frame = signals.add_indicators(frame)
            features[symbol] = signals.build_signal(
                symbol, frame, mids.get(symbol), now, config.bar_seconds
            )
        except market_data.MarketDataError as error:
            logger.warning("{}", error)
            features[symbol] = SymbolFeatures(
                symbol=symbol,
                mid=mids.get(symbol),
                rsi=None,
                atr=None,
                macd_hist=None,
                events=(),
                bar_age_seconds=None,
                gate_block="data_error",
            )
    return features


def _decide(
    tradeable, config: Config, manual_mode: bool, llm_transport
) -> EntryChoice | None:
    if manual_mode:
        choice = decision_layer.manual_decide(tradeable)
    else:
        # if not config.openrouter_api_key:
        #     logger.error("OPENROUTER_API_KEY missing; use --manual-mode or set the key")
        #     return None
        if not config.gemini_api_key:
            logger.error("GEMINI_API_KEY missing; use --manual-mode or set the key in .env")
            return None
        try:
            choice = decision_layer.decide_entry(
                tradeable, config.gemini_api_key, transport=llm_transport
            )
        except decision_layer.LlmError as error:
            logger.error("LLM decision failed, holding: {}", error)
            return None
    if choice:
        logger.info(
            "entry choice: {} {} ({})", choice.symbol, choice.direction, choice.model
        )
    else:
        logger.info("no entry this cycle")
    return choice


def _veto(entry: dict, reason: str) -> dict:
    """Record a pre-order veto on the entry and say so in the log, not just the journal."""
    entry["rejected"] = reason
    logger.info(
        "entry vetoed before submit: {} {} — {}", entry.get("symbol"), entry.get("direction"), reason
    )
    return entry


def _attempt_entry(
    choice: EntryChoice,
    spot: float | None,
    config: Config,
    trading: object,
    option_data: object,
    equity: float | None,
    open_risk: float | None,
    underlying_risk: float | None,
    pending_symbols: frozenset[str],
    cycle_id: str,
    execute: bool,
    *,
    cycle_spent: float,
    exclude_symbols: frozenset[str] = frozenset(),
) -> dict:
    entry: dict = {
        "symbol": choice.symbol,
        "direction": choice.direction,
        "thesis": choice.thesis,
        "model": choice.model,
    }
    if spot is None:
        entry["rejected"] = "missing_quote"
        return entry
    try:
        # Fresh clock: the cycle-start clock is stale by now (manual mode can sit at
        # the prompt for minutes), and quotes newer than it fail check_leg's
        # future_quote sanity check.
        screen_clock = broker.fetch_clock(trading)
        spread, rejections = _screen_spread(
            trading,
            option_data,
            choice.symbol,
            choice.direction,
            spot,
            screen_clock.server_time,
            screen_clock.server_time.date(),
            exclude_symbols,
        )
    except broker.BrokerError as error:
        entry["rejected"] = str(error)
        return entry
    entry["screen_rejections"] = rejections
    if spread is None:
        entry["rejected"] = "no_spread"
        logger.info(
            "no acceptable spread for {} {}: {}",
            choice.symbol,
            choice.direction,
            rejections,
        )
        return entry
    entry["spread"] = {
        "long": spread.long.symbol,
        "short": spread.short.symbol,
        "expiration": spread.expiration,
        "width": spread.width,
        "net_debit": spread.net_debit,
        "skew": round(spread.skew, 4),
    }
    qty, reason = pos_and_risk.size_entry(
        spread.net_debit, equity, open_risk, underlying_risk, cycle_spent=cycle_spent
    )
    if reason is not None:
        entry["rejected"] = reason
        logger.info("entry refused by risk manager: {}", reason)
        return entry
    entry["qty"] = qty

    # Fresh pre-submit re-check: account conflicts + re-quoted legs against a fresh clock.
    try:
        fresh_clock = broker.fetch_clock(trading)
        fresh_account = broker.fetch_account_state(trading, config.symbols)
        fresh_snaps = broker.fetch_option_snapshots(
            option_data, [spread.long.symbol, spread.short.symbol]
        )
    except broker.BrokerError as error:
        return _veto(entry, f"recheck: {error}")
    if {spread.long.symbol, spread.short.symbol} & fresh_account.open_order_symbols:
        return _veto(entry, "pending_order_conflict")
    long_q = broker.leg_quote_from_snapshot(
        spread.long.symbol,
        spread.long.strike,
        fresh_snaps.get(spread.long.symbol),
        spread.long.open_interest,
    )
    short_q = broker.leg_quote_from_snapshot(
        spread.short.symbol,
        spread.short.strike,
        fresh_snaps.get(spread.short.symbol),
        spread.short.open_interest,
    )
    for leg in (long_q, short_q):
        failure = options_screener.check_leg(leg, fresh_clock.server_time)
        if failure is not None:
            return _veto(entry, f"recheck: {failure}")
    fresh_debit = round(long_q.ask - short_q.bid, 2)  # type: ignore[operator]
    if not (settings.MIN_NET_DEBIT <= fresh_debit < spread.width):
        return _veto(entry, "recheck: bad_debit")
    if not (settings.MIN_DEBIT_FRAC * spread.width <= fresh_debit <= settings.MAX_DEBIT_FRAC * spread.width):
        return _veto(entry, "recheck: debit_out_of_band")
    qty, reason = pos_and_risk.size_entry(
        fresh_debit, fresh_account.equity, open_risk, underlying_risk, cycle_spent=cycle_spent
    )
    if reason is not None:
        return _veto(entry, f"recheck: {reason}")
    if execute and (fresh_account.options_level or 0) < MIN_OPTIONS_LEVEL:
        return _veto(entry, "options_level_too_low")

    fresh_spread = SpreadQuote(
        underlying=spread.underlying,
        direction=spread.direction,
        expiration=spread.expiration,
        long=long_q,
        short=short_q,
        width=spread.width,
        net_debit=fresh_debit,
        skew=spread.skew,
    )
    entry["premium"] = round(fresh_debit * qty * 100.0, 2)  # dollars this entry commits
    plan = options_screener.build_entry_plan(fresh_spread, qty, cycle_id)
    entry["receipt"] = _settle(trading, plan, execute)
    return entry


def _settle(trading: object, plan: OrderPlan, execute: bool) -> dict:
    if not execute:
        return {
            "submitted": False,
            "dry_run": True,
            "plan": {
                "kind": plan.kind,
                "qty": plan.qty,
                "limit_price": plan.limit_price,
                "legs": [f"{l.side} {l.symbol}" for l in plan.legs],
                "client_order_id": plan.client_order_id,
            },
        }
    receipt = broker.submit_paper_order(trading, plan)
    logger.info(
        "order {}: submitted={} status={} error={}",
        plan.client_order_id,
        receipt.submitted,
        receipt.status,
        receipt.error,
    )
    if receipt.submitted:
        sounds.play_order_sound()
    return {
        "submitted": receipt.submitted,
        "order_id": receipt.order_id,
        "status": receipt.status,
        "error": receipt.error,
        "client_order_id": receipt.client_order_id,
    }


# --- Fill tracking: sound + log when a submitted order actually fills ---
FILL_POLL_TIMEOUT_SECONDS = 30  # short poll right after a cycle submits an order
FILL_POLL_INTERVAL_SECONDS = 2
_FILLED = {"filled"}
_DEAD = {"canceled", "cancelled", "expired", "rejected", "done_for_day"}
# anything else (new, accepted, partially_filled, ...) stays pending


def _new_orders(record: dict) -> dict[str, str]:
    """order_id -> readable label for every order the cycle actually submitted."""
    orders: dict[str, str] = {}
    for exit_entry in record.get("exits") or []:
        receipt = exit_entry.get("receipt") or {}
        if receipt.get("submitted") and receipt.get("order_id"):
            orders[receipt["order_id"]] = f"exit {exit_entry.get('spread')}"
    for entry in journal_entries(record):
        receipt = entry.get("receipt") or {}
        if receipt.get("submitted") and receipt.get("order_id"):
            orders[receipt["order_id"]] = f"entry {entry.get('symbol')}"
    return orders


def _cancel_stale_entry_orders(
    trading: object, pending: dict[str, str], order_timestamps: dict[str, float]
) -> None:
    """Cancel any pending entry limit orders that have been open longer than the timeout.

    Eliminates fill latency: a signal at T0 should not result in a fill at T+10 min
    when the market has already moved on.  Exit orders are never cancelled here.
    """
    now = time.monotonic()
    for order_id, label in list(pending.items()):
        if not label.startswith("entry "):
            continue
        submitted_at = order_timestamps.get(order_id, now)
        age = now - submitted_at
        if age >= ENTRY_ORDER_CANCEL_TIMEOUT_SECONDS:
            ok = broker.cancel_order(trading, order_id)
            if ok:
                logger.info(
                    "CANCELLED stale entry order (age={:.0f}s): {} (order {})",
                    age, label, order_id,
                )
                del pending[order_id]
                order_timestamps.pop(order_id, None)
            else:
                logger.warning(
                    "failed to cancel stale entry order: {} (order {})", label, order_id
                )


def _check_fills(trading: object, pending: dict[str, str]) -> None:
    """Resolve pending orders in place; sound + log on a fill. Notification only, never raises."""
    for order_id, label in list(pending.items()):
        status = broker.fetch_order_status(trading, order_id)
        if status in _FILLED:
            logger.info("FILLED: {} (order {})", label, order_id)
            sounds.play_fill_sound()
            del pending[order_id]
        elif status in _DEAD:
            logger.info("order not filled ({}): {} (order {})", status, label, order_id)
            del pending[order_id]
        # None (lookup failed) or still open: keep waiting
    if pending:
        logger.info("awaiting fill: {}", ", ".join(pending.values()))



@app.command()
def run(
    execute: bool = typer.Option(
        False, help="Actually submit paper orders (dry run otherwise)."
    ),
    manual_mode: bool = typer.Option(
        False, help="Pick the entry candidate yourself instead of asking the LLM."
    ),
    loop: bool = typer.Option(False, help="Run forever on an interval."),
    interval: int = typer.Option(
        settings.LOOP_INTERVAL_SECONDS, help="Seconds between cycles with --loop."
    ),
    engine: str = typer.Option(
        "agentic",
        help="Trading engine: 'agentic' (Multi-Agent System) or 'legacy' (procedural single-thread).",
    ),
    llm: bool = typer.Option(
        False, help="Enable Gemini LLM multi-turn reasoning and advisories."
    ),
) -> None:
    """Run trading cycle (or loop). Defaults to autonomous Multi-Agent System."""
    setup_logging()

    # Route to Multi-Agent System by default unless legacy or manual mode requested
    if engine.lower() == "agentic" and not manual_mode:
        from multi_agent_cli import run_agentic_loop, create_agents
        from graph import TradingGraph
        logger.info("Initializing PACA Multi-Agent System (TradingGraph)...")
        agents = create_agents()
        graph = TradingGraph(agents)
        run_agentic_loop(
            graph,
            execute=execute,
            loop=loop,
            interval=interval,
            llm=llm,
        )
        return

    config, trading, stock_data, option_data = _bootstrap()
    if execute:
        logger.warning("ARMED: paper order submission is enabled")
    # Seed fill tracking from orders already open at the broker, so a restart
    # resumes watching what a previous run submitted.
    pending: dict[str, str] = {}  # order_id -> label
    order_timestamps: dict[str, float] = {}  # order_id -> time.monotonic() at submission
    try:
        pending = broker.fetch_open_orders(trading)
        seed_ts = time.monotonic()
        for oid in pending:
            order_timestamps[oid] = seed_ts
    except broker.BrokerError as error:
        logger.warning("could not list open orders at startup: {}", error)
    if pending:
        logger.info("watching open orders for fills: {}", ", ".join(pending.values()))
    while True:
        # Cancel entry orders stale beyond the timeout before running a new bar
        if execute:
            _cancel_stale_entry_orders(trading, pending, order_timestamps)
        record = run_cycle(
            config,
            trading,
            stock_data,
            option_data,
            execute=execute,
            manual_mode=manual_mode,
        )
        logger.info("cycle {} outcome: {}", record["cycle_id"], record.get("outcome"))
        new = _new_orders(record)
        # Stamp submission time for every brand-new order
        now_ts = time.monotonic()
        for oid in new:
            order_timestamps[oid] = now_ts
        pending.update(new)
        if new:
            # Short poll for instant fill feedback, timeboxed so an old
            # straggler can never stall the loop.
            deadline = time.monotonic() + FILL_POLL_TIMEOUT_SECONDS
            while True:
                _check_fills(trading, pending)
                if not (new.keys() & pending.keys()) or time.monotonic() >= deadline:
                    break
                time.sleep(FILL_POLL_INTERVAL_SECONDS)
        if not loop:
            _check_fills(trading, pending)  # final status check before exit
            if pending:
                logger.info(
                    "exiting with open orders; a later `run` resumes watching them"
                )
            break
        time.sleep(interval)
        _check_fills(trading, pending)  # catch slow fills from earlier cycles


@app.command()
def live(
    interval: int = typer.Option(
        settings.LOOP_INTERVAL_SECONDS, "--interval", help="Seconds between cycles in live market loop."
    ),
    llm: bool = typer.Option(
        False, "--llm", help="Enable Google Gemini multi-turn reasoning and advisories."
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt."
    ),
) -> None:
    """Launch continuous LIVE paper trading using the autonomous Multi-Agent System."""
    setup_logging()
    if not yes:
        typer.confirm(
            "Start autonomous LIVE paper trading loop on Alpaca paper endpoint?",
            abort=True,
        )
    from multi_agent_cli import run_agentic_loop, create_agents
    from graph import TradingGraph
    logger.info("=== PACA Multi-Agent System: LIVE PAPER TRADING ARMED ===")
    agents = create_agents()
    graph = TradingGraph(agents)
    run_agentic_loop(graph, execute=True, loop=True, interval=interval, llm=llm)


@app.command()
def preflight() -> None:
    """Pre-flight smoke test: settings.yaml, credentials + paper guards, connectivity."""
    setup_logging()
    try:
        values = settings.load_settings()
    except settings.SettingsError as error:
        typer.echo(f"FAIL settings.yaml: {error}")
        raise typer.Exit(1)
    typer.echo(
        f"OK   settings.yaml — all {len(values)} required values present and sane:"
    )
    for name in sorted(values):
        typer.echo(f"       {name} = {values[name]}")

    try:
        config = broker.load_config()
    except broker.ConfigError as error:
        typer.echo(f"FAIL credentials: {error}")
        raise typer.Exit(1)
    typer.echo("OK   credentials + paper-only guards (.env)")

    try:
        trading, _, _ = broker.build_clients(config)
        clock = broker.fetch_clock(trading)
    except broker.BrokerError as error:
        typer.echo(f"FAIL Alpaca connectivity: {error}")
        raise typer.Exit(1)
    state = "open" if clock.is_open else "closed"
    typer.echo(
        f"OK   Alpaca connectivity — market {state}, server time {clock.server_time}"
    )
    typer.echo("preflight passed")


@app.command()
def account(
    export: bool = typer.Option(
        False, "--export", help="Also write the snapshot to logs/account.json (dashboard data)."
    ),
) -> None:
    """Show equity, options level, paired spreads and warnings (read-only)."""
    setup_logging()
    config, trading, _, _ = _bootstrap()
    state = broker.fetch_account_state(trading, config.symbols)
    for leg in state.legs:
        logger.info("position: {} qty={} avg_entry={}", leg.symbol, leg.qty, leg.avg_entry_price)
    spreads, warnings = pos_and_risk.pair_spreads(state.legs)
    open_risk = pos_and_risk.open_premium_at_risk(spreads)
    typer.echo(f"equity: {state.equity}  options_level: {state.options_level}")
    typer.echo(f"open premium at risk: {open_risk}")
    for spread in spreads:
        typer.echo(
            f"  {spread.underlying} {spread.expiration} {spread.option_type} x{spread.qty} "
            f"long={spread.long_symbol} short={spread.short_symbol} entry_debit={spread.net_entry_debit}"
        )
    for warning in warnings:
        typer.echo(f"  WARNING {warning}")
    for symbol in state.unparsed_positions:
        typer.echo(f"  WARNING unparsed position: {symbol}")
    if export:
        snapshot = {
            "generated_at": datetime.now(timezone.utc),
            "equity": state.equity,
            "options_level": state.options_level,
            "open_risk": open_risk,
            "spreads": [asdict(s) for s in spreads],
            "warnings": warnings,
            "unparsed_positions": list(state.unparsed_positions),
        }
        path = Path("logs") / "account.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(to_json_line(snapshot) + "\n", encoding="utf-8")
        typer.echo(f"exported {path}")


@app.command()
def cancel(
    order_id: str = typer.Argument(
        None, help="Order id to cancel; omit to cancel ALL open orders."
    ),
    yes: bool = typer.Option(False, "--yes", help="Skip the confirmation prompt."),
) -> None:
    """Cancel open orders on the paper account (all of them, or one by id)."""
    setup_logging()
    _, trading, _, _ = _bootstrap()
    open_orders = broker.fetch_open_orders(trading)
    if not open_orders:
        typer.echo("no open orders")
        return
    if order_id is not None:
        if order_id not in open_orders:
            typer.echo(f"order {order_id} is not open (open: {list(open_orders)})")
            raise typer.Exit(1)
        targets = {order_id: open_orders[order_id]}
    else:
        targets = open_orders
    for oid, label in targets.items():
        typer.echo(f"  {oid}  {label}")
    if not yes:
        typer.confirm(f"cancel {len(targets)} open order(s)?", abort=True)
    failed = False
    for oid, label in targets.items():
        try:
            broker.cancel_order_raising(trading, oid)
            typer.echo(f"cancel requested: {oid}  {label}")
        except broker.BrokerError as error:
            failed = True
            typer.echo(f"FAIL {oid}  {label}: {error}")
    if failed:
        raise typer.Exit(1)


@app.command()
def candidates() -> None:
    """Show indicators, events and gate results for every whitelisted symbol (read-only)."""
    setup_logging()
    config, trading, stock_data, _ = _bootstrap()
    clock = broker.fetch_clock(trading)
    mids = broker.fetch_spot_mids(stock_data, config.symbols, clock.server_time)
    features = _build_trading_signals(
        config.symbols, config, stock_data, mids, clock.server_time
    )
    for c in signals.build_candidates(features, clock.is_open, config.bar_seconds):
        events = ",".join(e.kind for e in c.events) or "-"
        rsi = f"{c.rsi:.1f}" if c.rsi is not None else "-"
        atr = f"{c.atr:.3f}" if c.atr is not None else "-"
        hist = f"{c.macd_hist:+.4f}" if c.macd_hist is not None else "-"
        ema_fast = f"{c.ema_fast_dist:+.2f}" if c.ema_fast_dist is not None else "-"
        ema_slow = f"{c.ema_slow_dist:+.2f}" if c.ema_slow_dist is not None else "-"
        typer.echo(
            f"{c.symbol:<6} mid={c.mid} rsi={rsi} atr={atr} macd_hist={hist} "
            f"ema{settings.TREND_EMA_FAST}={ema_fast} ema{settings.TREND_EMA_SLOW}={ema_slow} "
            f"events={events} gate={c.gate_block or 'PASS'}"
        )


@app.command()
def screen(
    symbol: str = typer.Argument(..., help="Underlying symbol, e.g. SPY"),
    direction: str = typer.Option(..., "--direction", help="CALL or PUT"),
) -> None:
    """Show the exact spread the screener would pick (read-only, no LLM, no order)."""
    setup_logging()
    direction = direction.upper()
    if direction not in ("CALL", "PUT"):
        raise typer.BadParameter("--direction must be CALL or PUT")
    config, trading, stock_data, option_data = _bootstrap()
    clock = broker.fetch_clock(trading)
    symbol = symbol.upper()
    spot = broker.fetch_spot_mids(stock_data, (symbol,), clock.server_time)[symbol]
    if spot is None:
        typer.echo("no usable underlying quote")
        raise typer.Exit(1)
    spread, rejections = _screen_spread(
        trading,
        option_data,
        symbol,
        direction,
        spot,
        clock.server_time,
        clock.server_time.date(),
    )
    typer.echo(f"spot: {spot}  rejections: {rejections}")
    if spread is None:
        typer.echo("no acceptable spread")
        raise typer.Exit(1)
    typer.echo(
        f"{spread.direction} {spread.underlying} {spread.expiration}: "
        f"long {spread.long.symbol} @ {spread.long.strike} / short {spread.short.symbol} @ {spread.short.strike}\n"
        f"width={spread.width} net_debit={spread.net_debit} skew={spread.skew:.4f} "
        f"OI long/short={spread.long.open_interest}/{spread.short.open_interest}"
    )


if __name__ == "__main__":
    app()
