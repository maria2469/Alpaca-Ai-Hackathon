"""PnL reporting for PACA spreads (read-only).

    uv run --env-file .env pnl.py positions [--json]           open PnL per spread
    uv run --env-file .env pnl.py realized [--json] [--days N]  PnL per closed spread

Open PnL uses Alpaca's own per-leg unrealized_pl and current_price. Realized PnL
is rebuilt from filled MLEG orders: entries and exits are matched by leg-symbol
pair, first in first out. Quantities that cannot be matched are reported, not
guessed. Warnings go to stderr so `--json` stdout stays clean.
"""

from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timedelta, timezone

import pandas as pd
import typer
from loguru import logger

import broker
import pos_and_risk
from cli import setup_logging
from data_models import Config, LegPosition, SpreadFill

app = typer.Typer(add_completion=False, no_args_is_help=True)

POSITION_COLUMNS = [
    "underlying", "expiration", "type", "qty", "long_symbol", "short_symbol",
    "entry_debit", "mark", "cost_basis", "unrealized_pl", "unrealized_pct",
]
REALIZED_COLUMNS = [
    "underlying", "expiration", "type", "qty", "long_symbol", "short_symbol",
    "entry_debit", "exit_credit", "pnl", "pnl_pct", "entered_at", "exited_at",
    "hold_min", "unmatched_qty", "exit_order",
]


def _sub(a: float | None, b: float | None) -> float | None:
    return None if a is None or b is None else round(a - b, 4)


def _add(a: float | None, b: float | None) -> float | None:
    return None if a is None or b is None else round(a + b, 2)


def _pct(pnl: float | None, basis: float | None) -> float | None:
    return None if pnl is None or not basis else round(pnl / basis, 4)


def positions_frame(legs: tuple[LegPosition, ...]) -> tuple[pd.DataFrame, list[str]]:
    """One row per open spread with Alpaca's unrealized PnL. Unpaired legs → warnings."""
    spreads, warnings = pos_and_risk.pair_spreads(legs)
    by_symbol = {leg.symbol: leg for leg in legs}
    rows = []
    for spread in spreads:
        long_leg, short_leg = by_symbol[spread.long_symbol], by_symbol[spread.short_symbol]
        debit = spread.net_entry_debit
        cost_basis = None if debit is None else round(debit * spread.qty * 100, 2)
        unrealized = _add(long_leg.unrealized_pl, short_leg.unrealized_pl)
        rows.append({
            "underlying": spread.underlying,
            "expiration": spread.expiration,
            "type": spread.option_type,
            "qty": spread.qty,
            "long_symbol": spread.long_symbol,
            "short_symbol": spread.short_symbol,
            "entry_debit": debit,
            "mark": _sub(long_leg.current_price, short_leg.current_price),
            "cost_basis": cost_basis,
            "unrealized_pl": unrealized,
            "unrealized_pct": _pct(unrealized, cost_basis),
        })
    return pd.DataFrame(rows, columns=POSITION_COLUMNS), warnings


def realized_frame(fills: list[SpreadFill]) -> tuple[pd.DataFrame, list[str]]:
    """One row per exit fill, matched FIFO to entry fills on the same leg pair."""
    rows = []
    warnings: list[str] = []
    lots: dict[tuple[str, str], deque[list]] = {}  # pair -> [qty_left, debit, filled_at]
    for fill in sorted(fills, key=lambda f: f.filled_at):
        pair = (fill.long_symbol, fill.short_symbol)
        queue = lots.setdefault(pair, deque())
        if fill.intent == "enter":
            queue.append([fill.qty, fill.net_price, fill.filled_at])
            continue
        matched_qty, matched_cost, entered_at = 0, 0.0, None
        while matched_qty < fill.qty and queue:
            lot = queue[0]
            take = min(lot[0], fill.qty - matched_qty)
            matched_qty += take
            matched_cost += take * lot[1]
            entered_at = entered_at or lot[2]
            lot[0] -= take
            if lot[0] == 0:
                queue.popleft()
        unmatched = fill.qty - matched_qty
        if unmatched:
            warnings.append(
                f"{fill.client_order_id}: {unmatched} of {fill.qty} closed spreads have no "
                "matching entry fill in the lookback window"
            )
        entry_debit = round(matched_cost / matched_qty, 4) if matched_qty else None
        exit_credit = round(-fill.net_price, 4)
        pnl = None if entry_debit is None else round((exit_credit - entry_debit) * matched_qty * 100, 2)
        basis = None if entry_debit is None else entry_debit * matched_qty * 100
        parsed = pos_and_risk.parse_occ(fill.long_symbol)
        underlying, expiration, option_type = parsed[:3] if parsed else (None, None, None)
        rows.append({
            "underlying": underlying,
            "expiration": expiration,
            "type": option_type,
            "qty": fill.qty,
            "long_symbol": fill.long_symbol,
            "short_symbol": fill.short_symbol,
            "entry_debit": entry_debit,
            "exit_credit": exit_credit,
            "pnl": pnl,
            "pnl_pct": _pct(pnl, basis),
            "entered_at": entered_at,
            "exited_at": fill.filled_at,
            "hold_min": None if entered_at is None
            else round((fill.filled_at - entered_at).total_seconds() / 60, 1),
            "unmatched_qty": unmatched,
            "exit_order": fill.client_order_id,
        })
    return pd.DataFrame(rows, columns=REALIZED_COLUMNS), warnings


def _bootstrap() -> tuple[Config, object]:
    config = broker.load_config()
    trading, _, _ = broker.build_clients(config)
    return config, trading


def _emit(frame: pd.DataFrame, warnings: list[str], as_json: bool, total_column: str) -> None:
    for warning in warnings:
        logger.warning(warning)
    if as_json:
        typer.echo(json.dumps(frame.to_dict(orient="records"), default=str))
        return
    if frame.empty:
        typer.echo("no spreads")
        return
    typer.echo(frame.to_string(index=False))
    total = frame[total_column].dropna().sum()
    typer.echo(f"total {total_column}: {total:.2f}  ({len(frame)} spreads)")


@app.command()
def positions(
    as_json: bool = typer.Option(False, "--json", help="Print rows as a JSON array."),
) -> None:
    """Open PnL per spread from Alpaca's own position marks (read-only)."""
    setup_logging()
    config, trading = _bootstrap()
    state = broker.fetch_account_state(trading, config.symbols)
    frame, warnings = positions_frame(state.legs)
    warnings += [f"unparsed position: {symbol}" for symbol in state.unparsed_positions]
    _emit(frame, warnings, as_json, "unrealized_pl")


@app.command()
def realized(
    as_json: bool = typer.Option(False, "--json", help="Print rows as a JSON array."),
    days: int = typer.Option(30, "--days", min=1, help="Look back this many days of filled orders."),
) -> None:
    """PnL per closed spread, rebuilt from filled MLEG orders (read-only)."""
    setup_logging()
    _, trading = _bootstrap()
    after = datetime.now(timezone.utc) - timedelta(days=days)
    fills = broker.fetch_spread_fills(trading, after)
    frame, warnings = realized_frame(fills)
    _emit(frame, warnings, as_json, "pnl")


if __name__ == "__main__":
    app()
