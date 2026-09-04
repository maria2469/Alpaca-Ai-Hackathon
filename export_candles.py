"""Export bars + indicators + spread entries/exits for the paca-candles surge page.

    uv run --env-file .env export_candles.py [--days 10] [--out surge_artifacts/paca-candles/data.json]

Read-only. One JSON document: for every whitelisted symbol, completed OHLCV
bars with the signals.py indicators (RSI, ATR, MACD) plus display-only EMA 11/22,
the entry events that fired on each bar, and every spread this agent filled
(closed spreads from pnl.realized_frame, open ones from the account). Exit
reasons and entry theses are joined from logs/cycles.jsonl; anything that
cannot be matched is null, never guessed. Nothing here touches the trading path.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import typer
from loguru import logger

import broker
import market_data
import pnl
import pos_and_risk
import settings
import signals
from cli import JOURNAL_PATH, setup_logging
from data_models import OpenSpread, SpreadFill, journal_entries

EMA_FAST = 11  # display-only overlays; not used by signals.py
EMA_SLOW = 22
RTH_BARS_PER_DAY = 78  # 6.5h of 5m bars
COLUMNS = [
    "t", "open", "high", "low", "close", "volume",
    "rsi", "atr", "macd", "macd_signal", "macd_hist", "ema11", "ema22",
]
DEFAULT_OUT = Path("surge_artifacts") / "paca-candles" / "data.json"


# --- pure helpers -----------------------------------------------------------

def add_emas(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ema11"] = out["close"].ewm(span=EMA_FAST, adjust=False).mean()
    out["ema22"] = out["close"].ewm(span=EMA_SLOW, adjust=False).mean()
    return out


def bar_events(df: pd.DataFrame) -> list[list[str]]:
    """signals.detect_events applied to EVERY bar (same rules, previous-bar ATR)."""
    n = len(df)
    if n == 0 or "atr" not in df.columns:
        return [[] for _ in range(n)]
    atr_prev = df["atr"].shift(1)
    gap = df["open"] - df["close"].shift(1)
    body = df["close"] - df["open"]
    hist, hist_prev = df["macd_hist"], df["macd_hist"].shift(1)
    out: list[list[str]] = []
    for i in range(n):
        atr = atr_prev.iloc[i]
        events: list[str] = []
        if i == 0 or pd.isna(atr) or atr <= 0:
            out.append(events)
            continue
        if abs(gap.iloc[i]) > settings.ATR_EVENT_MULT * atr:
            events.append("gap_up" if gap.iloc[i] > 0 else "gap_down")
        if abs(body.iloc[i]) > settings.ATR_EVENT_MULT * atr:
            events.append("breakout_up" if body.iloc[i] > 0 else "breakout_down")
        h, hp = hist.iloc[i], hist_prev.iloc[i]
        if not pd.isna(h) and not pd.isna(hp) and abs(h) >= settings.MACD_MIN_HIST_ATR * atr:
            if hp <= 0 < h:
                events.append("macd_cross_up")
            elif hp >= 0 > h:
                events.append("macd_cross_down")
        out.append(events)
    return out


def _num(value) -> float | None:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) or math.isinf(f) else f


def _epoch(value) -> int | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return int(value.timestamp())


def frame_to_rows(df: pd.DataFrame) -> list[list]:
    """One list per bar in COLUMNS order; NaN -> None; t = epoch seconds UTC."""
    rows = []
    for stamp, row in df.iterrows():
        values = [_num(row.get(col)) for col in COLUMNS[1:]]
        rows.append([_epoch(stamp)] + [None if v is None else round(v, 4) for v in values])
    return rows


def load_journal(path: Path = JOURNAL_PATH) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def _exit_reasons(journal: list[dict]) -> dict[str, str]:
    reasons = {}
    for rec in journal:
        for ex in rec.get("exits") or []:
            coid = ((ex.get("receipt") or {}).get("client_order_id"))
            if coid and ex.get("reason"):
                reasons[coid] = ex["reason"]
    return reasons


def _journal_entry(journal: list[dict], long_symbol: str, short_symbol: str,
                   entered_at: int | None) -> tuple[dict, dict] | None:
    """Latest journaled (cycle, entry) for this leg pair that started at/before the fill."""
    best, best_t = None, None
    for rec in journal:
        started = _epoch(rec.get("started_at")) if rec.get("started_at") else None
        if started is None or (entered_at is not None and started > entered_at + 60):
            continue
        for entry in journal_entries(rec):
            spread = entry.get("spread") or {}
            if spread.get("long") != long_symbol or spread.get("short") != short_symbol:
                continue
            if best_t is None or started > best_t:
                best, best_t = (rec, entry), started
    return best


def _leg_info(long_symbol: str, short_symbol: str) -> dict:
    long_p = pos_and_risk.parse_occ(long_symbol)
    short_p = pos_and_risk.parse_occ(short_symbol)
    option_type = long_p[2] if long_p else None
    return {
        "type": option_type,
        "direction": {"C": "CALL", "P": "PUT"}.get(option_type),
        "expiration": long_p[1].isoformat() if long_p else None,
        "long_strike": long_p[3] if long_p else None,
        "short_strike": short_p[3] if short_p else None,
    }


def _with_journal(row: dict, journal: list[dict]) -> dict:
    found = _journal_entry(journal, row["long_symbol"], row["short_symbol"], row["entered_at"])
    rec, entry = found if found else ({}, {})
    cand = next((c for c in (rec or {}).get("candidates") or [] if c.get("symbol") == row["underlying"]), None)
    row["thesis"] = entry.get("thesis")
    row["events_at_entry"] = (cand or {}).get("events")
    row["cycle_id"] = (rec or {}).get("cycle_id")
    return row


def build_spreads(
    realized_rows: list[dict],
    open_spreads: list[OpenSpread],
    fills: list[SpreadFill],
    journal: list[dict],
) -> dict[str, list[dict]]:
    """Per-underlying spread history: closed rows from realized_frame, then open ones."""
    reasons = _exit_reasons(journal)
    by_symbol: dict[str, list[dict]] = {}

    for r in realized_rows:
        row = {
            "status": "closed",
            "underlying": r["underlying"],
            "long_symbol": r["long_symbol"],
            "short_symbol": r["short_symbol"],
            **_leg_info(r["long_symbol"], r["short_symbol"]),
            "qty": int(r["qty"]),
            "entered_at": _epoch(r.get("entered_at")),
            "exited_at": _epoch(r.get("exited_at")),
            "entry_debit": _num(r.get("entry_debit")),
            "exit_credit": _num(r.get("exit_credit")),
            "pnl": _num(r.get("pnl")),
            "pnl_pct": _num(r.get("pnl_pct")),
            "exit_reason": reasons.get(r.get("exit_order")),
            "exit_order": r.get("exit_order"),
        }
        by_symbol.setdefault(row["underlying"], []).append(_with_journal(row, journal))

    for spread in open_spreads:
        entries = [f for f in fills if f.intent == "enter"
                   and (f.long_symbol, f.short_symbol) == (spread.long_symbol, spread.short_symbol)]
        latest = max(entries, key=lambda f: f.filled_at) if entries else None
        row = {
            "status": "open",
            "underlying": spread.underlying,
            "long_symbol": spread.long_symbol,
            "short_symbol": spread.short_symbol,
            **_leg_info(spread.long_symbol, spread.short_symbol),
            "qty": spread.qty,
            "entered_at": _epoch(latest.filled_at) if latest else None,
            "exited_at": None,
            "entry_debit": _num(spread.net_entry_debit),
            "exit_credit": None,
            "pnl": None,
            "pnl_pct": None,
            "exit_reason": None,
            "exit_order": None,
        }
        by_symbol.setdefault(row["underlying"], []).append(_with_journal(row, journal))

    for rows in by_symbol.values():
        rows.sort(key=lambda r: r["entered_at"] or 0)
    return by_symbol


def settings_block() -> dict:
    return {
        "rsi_period": settings.RSI_PERIOD,
        "atr_period": settings.ATR_PERIOD,
        "macd": [settings.MACD_FAST, settings.MACD_SLOW, settings.MACD_SIGNAL],
        "atr_event_mult": settings.ATR_EVENT_MULT,
        "macd_min_hist_atr": settings.MACD_MIN_HIST_ATR,
        "rsi_overbought": settings.RSI_OVERBOUGHT,
        "rsi_oversold": settings.RSI_OVERSOLD,
        "ema": [EMA_FAST, EMA_SLOW],
    }


def symbol_block(frame: pd.DataFrame, spreads: list[dict]) -> dict:
    if frame.empty:
        return {"bars": [], "events": [], "spreads": spreads}
    enriched = add_emas(signals.add_indicators(frame))
    rows = frame_to_rows(enriched)
    events = [[row[0], kinds] for row, kinds in zip(rows, bar_events(enriched)) if kinds]
    return {"bars": rows, "events": events, "spreads": spreads}


# --- CLI ---------------------------------------------------------------------

app = typer.Typer(add_completion=False)


@app.command()
def export(
    days: int = typer.Option(10, "--days", min=1, help="Trading days of bars to export."),
    out: Path = typer.Option(DEFAULT_OUT, "--out", help="Output JSON path."),
) -> None:
    """Write data.json for the paca-candles page (read-only)."""
    setup_logging()
    config = broker.load_config()
    trading, stock_data, _ = broker.build_clients(config)
    now = datetime.now(timezone.utc)
    warnings: list[str] = []

    fills = broker.fetch_spread_fills(trading, now - timedelta(days=days + 5))
    realized, realized_warnings = pnl.realized_frame(fills)
    warnings += realized_warnings
    state = broker.fetch_account_state(trading, config.symbols)
    open_spreads, pair_warnings = pos_and_risk.pair_spreads(state.legs)
    warnings += pair_warnings
    spreads = build_spreads(realized.to_dict(orient="records"), open_spreads, fills, load_journal())

    lookback = days * RTH_BARS_PER_DAY + market_data.DEFAULT_LOOKBACK_BARS
    symbols = {}
    for symbol in config.symbols:
        try:
            frame = market_data.fetch_ohlcv(stock_data, symbol, config.bar_timeframe, now, lookback_bars=lookback)
        except market_data.MarketDataError as error:
            warnings.append(str(error))
            frame = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        symbols[symbol] = symbol_block(frame, spreads.get(symbol, []))
        logger.info("{}: {} bars, {} events, {} spreads", symbol, len(symbols[symbol]["bars"]),
                    len(symbols[symbol]["events"]), len(symbols[symbol]["spreads"]))

    doc = {
        "generated_at": now.isoformat(),
        "timeframe": config.bar_timeframe,
        "days": days,
        "settings": settings_block(),
        "columns": COLUMNS,
        "symbols": symbols,
        "warnings": warnings,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, separators=(",", ":"), default=str), encoding="utf-8")
    tmp.replace(out)
    logger.info("wrote {} ({} KB)", out, out.stat().st_size // 1024)


if __name__ == "__main__":
    app()
