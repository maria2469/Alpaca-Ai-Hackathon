"""Frozen dataclasses shared by every module. No SDK imports, no pydantic."""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Config:
    api_key: str
    secret_key: str
    symbols: tuple[str, ...]  # from settings.yaml
    bar_timeframe: str  # from settings.yaml, e.g. "15m", "1h", "1d", "1w"
    bar_seconds: int
    openrouter_api_key: str | None

    def __repr__(self) -> str:  # credentials must never reach logs or tracebacks
        return (
            f"Config(symbols={self.symbols!r}, bar_timeframe={self.bar_timeframe!r}, "
            "api_key=<hidden>, secret_key=<hidden>, openrouter_api_key=<hidden>)"
        )

    __str__ = __repr__


@dataclass(frozen=True)
class Clock:
    server_time: datetime
    is_open: bool
    next_close: datetime | None


@dataclass(frozen=True)
class LegPosition:
    symbol: str  # OCC option symbol
    underlying: str
    expiration: date
    option_type: str  # "C" or "P"
    strike: float
    qty: int  # signed: positive = long, negative = short
    avg_entry_price: float | None  # per share
    unrealized_pl: float | None = None  # dollars, Alpaca's own mark (pnl.py)
    current_price: float | None = None  # per share, Alpaca's own mark (pnl.py)


@dataclass(frozen=True)
class AccountState:
    equity: float | None
    options_level: int | None
    legs: tuple[LegPosition, ...]
    unparsed_positions: tuple[str, ...]  # anything we refuse to manage
    open_order_symbols: frozenset[str]  # every symbol appearing on any open order (legs included)


@dataclass(frozen=True)
class Event:
    kind: str  # gap_up/gap_down/breakout_up/breakout_down/macd_cross_up/macd_cross_down
    direction: str  # "CALL" or "PUT"


@dataclass(frozen=True)
class SymbolFeatures:
    symbol: str
    mid: float | None  # underlying quote midpoint
    rsi: float | None
    atr: float | None
    macd_hist: float | None
    events: tuple[Event, ...]
    bar_age_seconds: float | None
    gate_block: str | None = None  # None = tradeable candidate
    ema_fast_dist: float | None = None  # close − fast trend EMA ($): advisory, never a gate
    ema_slow_dist: float | None = None  # close − slow trend EMA ($): advisory, never a gate
    held: str | None = None  # "CALL"/"PUT" when a spread is already held: a new entry is an add


@dataclass(frozen=True)
class EntryChoice:
    symbol: str
    direction: str  # "CALL" or "PUT"
    thesis: str
    model: str


@dataclass(frozen=True)
class LegQuote:
    symbol: str
    strike: float
    bid: float | None
    ask: float | None
    implied_vol: float | None
    open_interest: int | None
    quote_time: datetime | None

    @property
    def mid(self) -> float | None:
        if self.bid is None or self.ask is None:
            return None
        return (self.bid + self.ask) / 2


@dataclass(frozen=True)
class SpreadQuote:
    underlying: str
    direction: str  # "CALL" or "PUT"
    expiration: date
    long: LegQuote
    short: LegQuote
    width: float
    net_debit: float
    skew: float  # |short IV - long IV|, ranking key (flattest first)


@dataclass(frozen=True)
class OpenSpread:
    underlying: str
    expiration: date
    option_type: str  # "C" or "P"
    long_symbol: str
    short_symbol: str
    qty: int  # spread quantity (positive)
    net_entry_debit: float | None  # per share; None = unknown, blocks stop/TP math
    width: float | None = None  # per share strike width; None = unknown, skips the width TP trigger


@dataclass(frozen=True)
class ExitDecision:
    spread: OpenSpread
    reason: str  # "stop" | "take_profit" | "expiry"
    net_mark: float | None


@dataclass(frozen=True)
class LegPlan:
    symbol: str
    side: str  # "buy" | "sell"
    intent: str  # "buy_to_open" | "sell_to_open" | "buy_to_close" | "sell_to_close"
    ratio_qty: int = 1


@dataclass(frozen=True)
class OrderPlan:
    kind: str  # "enter" | "exit"
    underlying: str
    qty: int
    limit_price: float  # net: positive = debit paid, negative = credit received
    legs: tuple[LegPlan, LegPlan]
    client_order_id: str
    order_class: str = "mleg"
    time_in_force: str = "day"


@dataclass(frozen=True)
class OrderReceipt:
    submitted: bool
    client_order_id: str
    order_id: str | None = None
    status: str | None = None
    error: str | None = None  # exception type name only, never message text


@dataclass(frozen=True)
class SpreadFill:
    """One filled two-leg MLEG order, as read back from Alpaca (pnl.py)."""

    client_order_id: str
    filled_at: datetime
    intent: str  # "enter" (legs *_to_open) | "exit" (legs *_to_close)
    long_symbol: str  # the leg bought to open / sold to close
    short_symbol: str
    qty: int
    net_price: float  # per share: +buy legs −sell legs → entry = +debit, exit = −credit


def journal_entries(record: dict) -> list[dict]:
    """Entry attempts of one journal row. Rows written before 2026-09-02 carry a
    single `entry` (dict or None); newer rows carry an `entries` list."""
    if record.get("entries") is not None:
        return list(record["entries"])
    entry = record.get("entry")
    return [entry] if entry else []


def to_json_line(obj: object) -> str:
    """One JSON line for the cycle journal. Dataclasses and datetimes are handled."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        obj = dataclasses.asdict(obj)
    return json.dumps(obj, default=str, separators=(",", ":"))
