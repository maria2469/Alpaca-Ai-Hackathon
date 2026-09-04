"""Everything that touches the environment or Alpaca.

Config comes straight from os.environ (load `.env` with `uv run --env-file .env`).
This is a PAPER-ONLY project: startup aborts on any live-trading signal and the
trading client is always constructed with paper=True hardcoded.

submit_paper_order is the only function in the codebase that submits an order.
Every vendor exception is wrapped to its type name only (`from None`) so request
details and credentials can never leak into logs or tracebacks.
"""

from __future__ import annotations

import os
import concurrent.futures
from datetime import date, datetime, timedelta
from typing import Any, Callable

from alpaca.data.enums import DataFeed, OptionsFeed
from alpaca.data.historical import OptionHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import OptionSnapshotRequest, StockLatestQuoteRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import ContractType, OrderClass, OrderSide, PositionIntent, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import (
    GetOptionContractsRequest,
    GetOrdersRequest,
    LimitOrderRequest,
    OptionLegRequest,
)
from loguru import logger

import pos_and_risk
import settings
from data_models import (
    AccountState,
    Clock,
    Config,
    LegPosition,
    LegQuote,
    OrderPlan,
    OrderReceipt,
    SpreadFill,
)

# Plumbing constants — not trader knobs, so not in settings.yaml.
STOCK_FEED = DataFeed.IEX
OPTION_FEED = OptionsFeed.INDICATIVE  # explicit: the SDK default varies by subscription
SNAPSHOT_BATCH = 100
CONTRACT_PAGE_LIMIT = 1000
MAX_CONTRACT_PAGES = 5

_LIVE_FLAG_VARS = ("ALPACA_LIVE", "ALPACA_LIVE_TRADING", "APCA_LIVE")
_ENDPOINT_VARS = ("ALPACA_BASE_URL", "ALPACA_API_BASE_URL", "APCA_API_BASE_URL", "ALPACA_ENDPOINT")


class ConfigError(Exception):
    pass


class BrokerError(Exception):
    pass


def parse_bool(raw: str, *, name: str) -> bool:
    value = raw.strip().lower()
    if value in ("true", "1", "yes"):
        return True
    if value in ("false", "0", "no"):
        return False
    raise ConfigError(f"{name} must be true or false, got an unrecognized value")


def find_live_trading_signals(env: dict[str, str]) -> list[str]:
    """Names of every env var indicating live trading. Non-empty means abort."""
    findings = []
    paper_raw = env.get("ALPACA_PAPER", "true")
    if not parse_bool(paper_raw, name="ALPACA_PAPER"):
        findings.append("ALPACA_PAPER")
    for name in _LIVE_FLAG_VARS:
        raw = env.get(name, "").strip()
        if raw and parse_bool(raw, name=name):
            findings.append(name)
    for name in _ENDPOINT_VARS:
        if "api.alpaca.markets" in env.get(name, "") and "paper-api" not in env.get(name, ""):
            findings.append(name)
    return findings


def load_config(env: dict[str, str] | None = None) -> Config:
    """Credentials + paper guards from env; strategy values come from settings.yaml."""
    env = dict(os.environ) if env is None else env
    live = find_live_trading_signals(env)
    if live:
        raise ConfigError(
            "live trading signals found in the environment: "
            + ", ".join(live)
            + " — this project is paper-only and refuses to start"
        )
    api_key = env.get("ALPACA_API_KEY", "").strip()
    secret_key = env.get("ALPACA_SECRET_KEY", "").strip()
    if not api_key or not secret_key:
        raise ConfigError("ALPACA_API_KEY and ALPACA_SECRET_KEY are required")
    # OpenRouter API key (commented out in favor of direct Gemini API):
    # openrouter = env.get("OPENROUTER_API_KEY", "").strip() or None
    gemini_key = env.get("GEMINI_API_KEY", "").strip() or env.get("GOOGLE_API_KEY", "").strip() or env.get("OPENROUTER_API_KEY", "").strip() or None
    return Config(
        api_key=api_key,
        secret_key=secret_key,
        symbols=settings.SYMBOLS,
        bar_timeframe=settings.BAR_TIMEFRAME,
        bar_seconds=settings.BAR_SECONDS,
        gemini_api_key=gemini_key,
    )


def build_clients(config: Config) -> tuple[Any, Any, Any]:
    """(trading, stock data, option data) clients. paper=True is hardcoded."""
    trading = TradingClient(config.api_key, config.secret_key, paper=True)
    stock_data = StockHistoricalDataClient(config.api_key, config.secret_key)
    option_data = OptionHistoricalDataClient(config.api_key, config.secret_key)
    return trading, stock_data, option_data


def guarded(label: str, call: Callable[[], Any]) -> Any:
    """Run a vendor call; on failure raise BrokerError naming only the exception type."""
    try:
        return call()
    except Exception as error:
        raise BrokerError(f"{label} failed: {type(error).__name__}") from None


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> int | None:
    number = as_float(value)
    return int(number) if number is not None else None


def fetch_clock(trading: Any) -> Clock:
    raw = guarded("clock read", trading.get_clock)
    return Clock(
        server_time=raw.timestamp,
        is_open=bool(raw.is_open),
        next_close=getattr(raw, "next_close", None),
    )


def fetch_account_state(trading: Any, whitelist: tuple[str, ...]) -> AccountState:
    """Equity, options level, option leg positions and open-order symbols.

    Any read failure raises rather than returning a partial account. An option
    position we cannot parse is reported, never silently managed.
    """
    account = guarded("account read", trading.get_account)
    raw_positions = guarded("positions read", trading.get_all_positions)
    orders_request = GetOrdersRequest(status=QueryOrderStatus.OPEN, limit=500, nested=True)
    raw_orders = guarded("orders read", lambda: trading.get_orders(orders_request))

    legs: list[LegPosition] = []
    unparsed: list[str] = []
    for position in raw_positions:
        # The SDK returns enums (AssetClass.US_OPTION, PositionSide.SHORT) whose
        # str() is "AssetClass.US_OPTION" — match on the lowercase value instead.
        raw_class = getattr(position, "asset_class", None)
        asset_class = str(getattr(raw_class, "value", raw_class) or "").lower()
        if "option" not in asset_class:
            continue  # equities and anything else are out of scope
        symbol = str(position.symbol)
        parsed = pos_and_risk.parse_occ(symbol)
        qty = as_int(getattr(position, "qty", None))
        raw_side = getattr(position, "side", None)
        side = str(getattr(raw_side, "value", raw_side) or "").lower()
        if parsed is None or qty is None or qty == 0:
            unparsed.append(symbol)
            continue
        underlying, expiration, option_type, strike = parsed
        signed_qty = -abs(qty) if "short" in side else abs(qty)
        legs.append(
            LegPosition(
                symbol=symbol,
                underlying=underlying,
                expiration=expiration,
                option_type=option_type,
                strike=strike,
                qty=signed_qty,
                avg_entry_price=as_float(getattr(position, "avg_entry_price", None)),
                unrealized_pl=as_float(getattr(position, "unrealized_pl", None)),
                current_price=as_float(getattr(position, "current_price", None)),
            )
        )

    order_symbols: set[str] = set()
    for order in raw_orders:
        for item in [order, *(getattr(order, "legs", None) or [])]:
            symbol = getattr(item, "symbol", None)
            if symbol:
                order_symbols.add(str(symbol))

    return AccountState(
        equity=as_float(getattr(account, "equity", None)),
        options_level=as_int(getattr(account, "options_trading_level", None)),
        legs=tuple(legs),
        unparsed_positions=tuple(unparsed),
        open_order_symbols=frozenset(order_symbols),
    )


def fetch_open_orders(trading: Any) -> dict[str, str]:
    """Open order ids with a readable label (leg symbols), for fill tracking.

    Lets a restarted `run` resume watching orders submitted by a previous run.
    """
    request = GetOrdersRequest(status=QueryOrderStatus.OPEN, limit=500, nested=True)
    raw_orders = guarded("orders read", lambda: trading.get_orders(request))
    orders: dict[str, str] = {}
    for order in raw_orders:
        order_id = getattr(order, "id", None)
        if not order_id:
            continue
        symbols = [
            str(symbol)
            for item in [order, *(getattr(order, "legs", None) or [])]
            if (symbol := getattr(item, "symbol", None))
        ]
        label = "/".join(symbols) or str(getattr(order, "client_order_id", None) or "unknown")
        orders[str(order_id)] = label
    return orders


def _enum_value(raw: Any) -> str:
    return str(getattr(raw, "value", raw) or "").lower()


def fetch_spread_fills(trading: Any, after: datetime | None) -> list[SpreadFill]:
    """Filled two-leg MLEG orders this agent submitted (client_order_id `sp-...`).

    Read-only, for PnL reporting. Net price is rebuilt from the legs (+buy, −sell)
    rather than trusting the parent's filled_avg_price. Anything not shaped like
    one of our spreads is skipped with a warning, never guessed at.
    """
    request = GetOrdersRequest(
        status=QueryOrderStatus.CLOSED, limit=500, nested=True, after=after
    )
    raw_orders = guarded("closed orders read", lambda: trading.get_orders(request))
    fills: list[SpreadFill] = []
    for order in raw_orders:
        client_order_id = str(getattr(order, "client_order_id", None) or "")
        if not client_order_id.startswith("sp-"):
            continue
        if _enum_value(getattr(order, "order_class", None)) != "mleg":
            continue
        if _enum_value(getattr(order, "status", None)) != "filled":
            continue
        legs = list(getattr(order, "legs", None) or [])
        qty = as_int(getattr(order, "filled_qty", None))
        filled_at = getattr(order, "filled_at", None)
        if len(legs) != 2 or not qty or filled_at is None:
            logger.warning("skipping fill {}: not a two-leg filled spread", client_order_id)
            continue
        intents = {_enum_value(getattr(leg, "position_intent", None)) for leg in legs}
        if intents == {"buy_to_open", "sell_to_open"}:
            intent, long_intent = "enter", "buy_to_open"
        elif intents == {"buy_to_close", "sell_to_close"}:
            intent, long_intent = "exit", "sell_to_close"
        else:
            logger.warning("skipping fill {}: mixed leg intents {}", client_order_id, sorted(intents))
            continue
        net_price = 0.0
        long_symbol = short_symbol = None
        for leg in legs:
            price = as_float(getattr(leg, "filled_avg_price", None))
            symbol = str(getattr(leg, "symbol", None) or "")
            if price is None or pos_and_risk.parse_occ(symbol) is None:
                break
            side = _enum_value(getattr(leg, "side", None))
            net_price += price if side == "buy" else -price
            if _enum_value(getattr(leg, "position_intent", None)) == long_intent:
                long_symbol = symbol
            else:
                short_symbol = symbol
        if long_symbol is None or short_symbol is None:
            logger.warning("skipping fill {}: unreadable leg price or symbol", client_order_id)
            continue
        fills.append(
            SpreadFill(
                client_order_id=client_order_id,
                filled_at=filled_at,
                intent=intent,
                long_symbol=long_symbol,
                short_symbol=short_symbol,
                qty=qty,
                net_price=round(net_price, 4),
            )
        )
    return fills


def cancel_order(trading: Any, order_id: str) -> None:
    """Request cancellation of one open order. Raises BrokerError on refusal.

    Alpaca cancels asynchronously: success here means the request was accepted,
    not that the order is already canceled (it may even still fill).
    """
    guarded("order cancel", lambda: trading.cancel_order_by_id(order_id))


def fetch_spot_mids(
    stock_data: Any, symbols: tuple[str, ...], server_time: datetime | None = None
) -> dict[str, float | None]:
    """Latest quote mid per symbol; None when the quote is missing, crossed, or stale.

    A stock quote older than MAX_QUOTE_AGE_SECONDS against the broker clock is
    treated as missing (the caller gates it as `missing_quote`) — the same rule
    options_screener.check_leg applies to option legs. On 2026-09-02 GLD's IEX
    quote sat frozen at one price for 2.5 hours and passed every gate.
    """
    request = StockLatestQuoteRequest(symbol_or_symbols=list(symbols), feed=STOCK_FEED)
    raw = guarded("quotes read", lambda: stock_data.get_stock_latest_quote(request))
    mids: dict[str, float | None] = {}
    for symbol in symbols:
        quote = raw.get(symbol)
        bid = as_float(getattr(quote, "bid_price", None))
        ask = as_float(getattr(quote, "ask_price", None))
        if not (bid and ask and 0 < bid <= ask):
            mids[symbol] = None
            continue
        if server_time is not None:
            stamp = getattr(quote, "timestamp", None)
            if stamp is None:
                mids[symbol] = None
                continue
            age = server_time.timestamp() - stamp.timestamp()
            # Quotes are fetched after the clock read, so a fresh quote may slightly
            # postdate server_time; only reject implausible or genuinely old stamps.
            if age > settings.MAX_QUOTE_AGE_SECONDS or age < -settings.MAX_QUOTE_AGE_SECONDS:
                mids[symbol] = None
                continue
        mids[symbol] = (bid + ask) / 2
    return mids


def fetch_contracts(
    trading: Any, underlying: str, direction: str, spot: float, today: date
) -> dict[date, dict[float, dict]]:
    """Active contracts by expiration then strike: {exp: {strike: {symbol, open_interest}}}."""
    contract_type = ContractType.CALL if direction == "CALL" else ContractType.PUT
    band = settings.STRIKE_BAND_PCT
    by_expiry: dict[date, dict[float, dict]] = {}
    page_token = None
    for _ in range(MAX_CONTRACT_PAGES):
        request = GetOptionContractsRequest(
            underlying_symbols=[underlying],
            root_symbol=underlying,
            type=contract_type,
            expiration_date_gte=today + timedelta(days=settings.MIN_DTE),
            expiration_date_lte=today + timedelta(days=settings.MAX_EXPIRY_LOOKAHEAD_DAYS),
            strike_price_gte=str(round(spot * (1 - band), 2)),
            strike_price_lte=str(round(spot * (1 + band), 2)),
            limit=CONTRACT_PAGE_LIMIT,
            page_token=page_token,
        )
        response = guarded("contracts read", lambda: trading.get_option_contracts(request))
        for contract in response.option_contracts or []:
            strike = as_float(getattr(contract, "strike_price", None))
            expiration = getattr(contract, "expiration_date", None)
            if strike is None or expiration is None:
                continue
            by_expiry.setdefault(expiration, {})[strike] = {
                "symbol": str(contract.symbol),
                "open_interest": as_int(getattr(contract, "open_interest", None)),
            }
        page_token = getattr(response, "next_page_token", None)
        if not page_token:
            return by_expiry
    raise BrokerError("contracts read failed: too many pages")


def fetch_option_snapshots(option_data: Any, symbols: list[str]) -> dict[str, Any]:
    """Fetch option snapshots with parallelized batch execution for multi-hundred symbol lists."""
    if not symbols:
        return {}
    if len(symbols) <= SNAPSHOT_BATCH:
        request = OptionSnapshotRequest(symbol_or_symbols=symbols, feed=OPTION_FEED)
        return guarded("snapshots read", lambda: option_data.get_option_snapshot(request))

    batches = [symbols[i : i + SNAPSHOT_BATCH] for i in range(0, len(symbols), SNAPSHOT_BATCH)]
    snapshots: dict[str, Any] = {}

    def _fetch_batch(batch: list[str]) -> dict[str, Any]:
        request = OptionSnapshotRequest(symbol_or_symbols=batch, feed=OPTION_FEED)
        return guarded("snapshots read", lambda: option_data.get_option_snapshot(request))

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(batches), 8)) as executor:
        for result in executor.map(_fetch_batch, batches):
            snapshots.update(result)
    return snapshots


def leg_quote_from_snapshot(
    symbol: str, strike: float, snapshot: Any, open_interest: int | None
) -> LegQuote:
    quote = getattr(snapshot, "latest_quote", None) if snapshot is not None else None
    iv = as_float(getattr(snapshot, "implied_volatility", None)) if snapshot is not None else None
    return LegQuote(
        symbol=symbol,
        strike=strike,
        bid=as_float(getattr(quote, "bid_price", None)) if quote is not None else None,
        ask=as_float(getattr(quote, "ask_price", None)) if quote is not None else None,
        implied_vol=iv,
        open_interest=open_interest,
        quote_time=getattr(quote, "timestamp", None) if quote is not None else None,
    )


_ALLOWED_LEG_SHAPES = {
    "enter": {("buy", "buy_to_open"), ("sell", "sell_to_open")},
    "exit": {("sell", "sell_to_close"), ("buy", "buy_to_close")},
}
_SIDE = {"buy": OrderSide.BUY, "sell": OrderSide.SELL}
_INTENT = {
    "buy_to_open": PositionIntent.BUY_TO_OPEN,
    "sell_to_open": PositionIntent.SELL_TO_OPEN,
    "buy_to_close": PositionIntent.BUY_TO_CLOSE,
    "sell_to_close": PositionIntent.SELL_TO_CLOSE,
}


def submit_paper_order(trading: Any, plan: OrderPlan) -> OrderReceipt:
    """The one function that can spend money. Re-validates the plan, then submits.

    An Alpaca refusal never raises: the receipt carries submitted=False and the
    exception type name only.
    """
    shapes = {(leg.side, leg.intent) for leg in plan.legs}
    if (
        plan.order_class != "mleg"
        or plan.time_in_force != "day"
        or plan.kind not in _ALLOWED_LEG_SHAPES
        or shapes != _ALLOWED_LEG_SHAPES[plan.kind]
        or len({leg.symbol for leg in plan.legs}) != 2
        or any(leg.ratio_qty != 1 for leg in plan.legs)
        or plan.qty < 1
        or not plan.client_order_id
        or (plan.kind == "enter" and plan.limit_price <= 0)
    ):
        raise BrokerError("order plan failed validation, refusing to submit")

    request = LimitOrderRequest(
        qty=plan.qty,
        limit_price=plan.limit_price,
        order_class=OrderClass.MLEG,
        time_in_force=TimeInForce.DAY,
        client_order_id=plan.client_order_id,
        legs=[
            OptionLegRequest(
                symbol=leg.symbol,
                ratio_qty=leg.ratio_qty,
                side=_SIDE[leg.side],
                position_intent=_INTENT[leg.intent],
            )
            for leg in plan.legs
        ],
    )
    try:
        order = trading.submit_order(request)
    except Exception as error:
        return OrderReceipt(
            submitted=False,
            client_order_id=plan.client_order_id,
            error=type(error).__name__,
        )
    status = getattr(order, "status", None)
    return OrderReceipt(
        submitted=True,
        client_order_id=plan.client_order_id,
        order_id=str(getattr(order, "id", None)),
        status=str(getattr(status, "value", status)),
    )


def fetch_order_status(trading: Any, order_id: str) -> str | None:
    """Current status of an order ("filled", "canceled", ...), or None if the lookup fails.

    Read-only, notification path: a failure here must never block a cycle.
    """
    try:
        order = trading.get_order_by_id(order_id)
    except Exception:
        return None
    status = getattr(order, "status", None)
    if status is None:
        return None
    return getattr(status, "value", str(status))


def cancel_order(trading: Any, order_id: str) -> bool:
    """Cancel an open order by ID. Returns True if accepted, False on any error.

    Fire-and-forget for background use: a failed cancel is logged by the caller; never raises.
    """
    try:
        trading.cancel_order_by_id(order_id)
        return True
    except Exception:
        return False


def cancel_order_raising(trading: Any, order_id: str) -> None:
    """Cancel an open order by ID, raising BrokerError on failure.

    Use this from interactive CLI commands where the caller wants to surface errors.
    """
    try:
        trading.cancel_order_by_id(order_id)
    except Exception as error:
        raise BrokerError(str(error)) from None
