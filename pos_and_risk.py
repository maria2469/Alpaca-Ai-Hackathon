"""Position manager + risk manager: pure money math.

Pairs raw option legs into vertical spreads, decides mechanical exits
(stop / take-profit / expiry), and sizes new entries against the
equity-relative caps. The LLM is never consulted here.
"""

from __future__ import annotations

import math
import re
from datetime import date, datetime

import settings
from data_models import Event, ExitDecision, LegPosition, LegQuote, OpenSpread

# Exit thresholds and risk caps live in settings.yaml (approved 2026-08-31).

_OCC = re.compile(r"^([A-Z]{1,6})(\d{6})([CP])(\d{8})$")


def parse_occ(symbol: str) -> tuple[str, date, str, float] | None:
    """OCC option symbol -> (underlying, expiration, type, strike), or None."""
    match = _OCC.match(symbol.strip().upper())
    if match is None:
        return None
    root, yymmdd, option_type, strike_raw = match.groups()
    try:
        expiration = datetime.strptime(yymmdd, "%y%m%d").date()
    except ValueError:
        return None
    return root, expiration, option_type, int(strike_raw) / 1000.0


def pair_spreads(
    legs: tuple[LegPosition, ...],
) -> tuple[list[OpenSpread], list[str]]:
    """Group option legs into debit verticals; anything unrecognized is a warning.

    A spread is one long and one short leg with equal absolute quantity on the
    same underlying, expiration and type, with the short on the debit side
    (calls: above the long strike; puts: below). A group may hold several such
    spreads: each long is matched to the nearest unused short of equal quantity.
    Leftover legs are reported and never touched by this agent.
    """
    groups: dict[tuple[str, date, str], list[LegPosition]] = {}
    for leg in legs:
        groups.setdefault((leg.underlying, leg.expiration, leg.option_type), []).append(leg)

    spreads: list[OpenSpread] = []
    warnings: list[str] = []
    for (underlying, expiration, option_type), members in sorted(groups.items()):
        # For calls the debit side is up (short strike > long strike), for puts down.
        upward = option_type == "C"
        longs = sorted(
            (leg for leg in members if leg.qty > 0),
            key=lambda leg: leg.strike, reverse=not upward,
        )
        free_shorts = sorted(
            (leg for leg in members if leg.qty < 0),
            key=lambda leg: leg.strike, reverse=not upward,
        )
        leftovers: list[LegPosition] = [leg for leg in members if leg.qty == 0]
        for long_leg in longs:
            short_leg = next(
                (
                    s for s in free_shorts
                    if -s.qty == long_leg.qty
                    and (s.strike > long_leg.strike if upward else s.strike < long_leg.strike)
                ),
                None,
            )
            if short_leg is None:
                leftovers.append(long_leg)
                continue
            free_shorts.remove(short_leg)
            net_entry_debit = None
            if long_leg.avg_entry_price is not None and short_leg.avg_entry_price is not None:
                debit = long_leg.avg_entry_price - short_leg.avg_entry_price
                net_entry_debit = debit if debit > 0 else None  # non-debit pair: unknown
            spreads.append(
                OpenSpread(
                    underlying=underlying,
                    expiration=expiration,
                    option_type=option_type,
                    long_symbol=long_leg.symbol,
                    short_symbol=short_leg.symbol,
                    qty=long_leg.qty,
                    net_entry_debit=net_entry_debit,
                    width=abs(short_leg.strike - long_leg.strike),
                )
            )
        leftovers.extend(free_shorts)
        if leftovers:
            warnings.append(
                f"unpaired legs on {underlying} {expiration} {option_type}: "
                + ", ".join(f"{leg.symbol} qty={leg.qty}" for leg in leftovers)
            )
    return spreads, warnings


def opposing_event_fired(spread: OpenSpread, events: tuple[Event, ...]) -> bool:
    """True when any entry event points against the spread's direction.

    A call spread ("C") is bullish, so any PUT-direction event opposes it;
    a put spread ("P") is bearish, so any CALL-direction event opposes it.
    """
    against = "PUT" if spread.option_type == "C" else "CALL"
    return any(event.direction == against for event in events)


def held_direction(spreads: list[OpenSpread]) -> str | None:
    """Direction of the spreads held on ONE underlying: "CALL" for call spreads,
    "PUT" for put spreads, None when nothing is held or both types are (no add
    is allowed against a mixed book)."""
    types = {spread.option_type for spread in spreads}
    if types == {"C"}:
        return "CALL"
    if types == {"P"}:
        return "PUT"
    return None


def exit_decision(
    spread: OpenSpread,
    long_quote: LegQuote | None,
    short_quote: LegQuote | None,
    today: date,
    opposing_event: bool = False,
) -> ExitDecision | None:
    """Mechanical exit verdict for one open spread, or None to keep holding.

    Precedence: expiry, reversal, stop, take-profit. Take-profit fires at the
    lower of TAKE_PROFIT_MULT x entry debit and TAKE_PROFIT_WIDTH_FRAC x strike
    width (mark/width ~ implied probability of a full payoff, so the width rule
    means the same remaining reward:risk on every spread). Expiry (DTE <=
    settings.EXIT_DTE) and reversal (an entry event against the spread, if
    settings.REVERSAL_EXIT) exit even on missing marks or unknown entry debit —
    they are signal-based. Stop and take-profit need both a known entry debit
    and fresh two-sided marks; when either is unknown we hold and let the
    caller log the gap rather than guess.
    """
    dte = (spread.expiration - today).days
    if dte <= settings.EXIT_DTE:
        net_mark = _net_mark(long_quote, short_quote)
        return ExitDecision(spread=spread, reason="expiry", net_mark=net_mark)
    if opposing_event and settings.REVERSAL_EXIT:
        net_mark = _net_mark(long_quote, short_quote)
        return ExitDecision(spread=spread, reason="reversal", net_mark=net_mark)
    if spread.net_entry_debit is None:
        return None
    net_mark = _net_mark(long_quote, short_quote)
    if net_mark is None:
        return None
    if net_mark <= settings.STOP_FRACTION * spread.net_entry_debit:
        return ExitDecision(spread=spread, reason="stop", net_mark=net_mark)
    tp_debit = settings.TAKE_PROFIT_MULT * spread.net_entry_debit
    tp_width = settings.TAKE_PROFIT_WIDTH_FRAC * spread.width if spread.width is not None else None
    target = tp_debit if tp_width is None else min(tp_debit, tp_width)
    if net_mark >= target:
        return ExitDecision(spread=spread, reason="take_profit", net_mark=net_mark)
    return None


def _net_mark(long_quote: LegQuote | None, short_quote: LegQuote | None) -> float | None:
    if long_quote is None or short_quote is None:
        return None
    if long_quote.mid is None or short_quote.mid is None:
        return None
    return long_quote.mid - short_quote.mid


def open_premium_at_risk(spreads: list[OpenSpread]) -> float | None:
    """Total entry debit of all open spreads in dollars; None if any is unknown.

    An unknown component makes the whole figure unknown so the risk manager
    refuses new entries instead of undercounting exposure.
    """
    total = 0.0
    for spread in spreads:
        if spread.net_entry_debit is None:
            return None
        total += spread.net_entry_debit * spread.qty * 100.0
    return total


def over_cap_warnings(spreads: list[OpenSpread], equity: float | None) -> list[str]:
    """One warning per underlying whose open premium exceeds the per-underlying cap.

    Observation only — never blocks or closes anything. Unknown equity or an
    underlying with an unknown entry debit is skipped: those cases already
    surface through the entry refusals and unknown-debit warnings.
    """
    if equity is None or equity <= 0:
        return []
    cap = settings.PER_UNDERLYING_FRACTION * equity
    warnings = []
    for underlying in sorted({s.underlying for s in spreads}):
        at_risk = open_premium_at_risk([s for s in spreads if s.underlying == underlying])
        if at_risk is not None and at_risk > cap:
            warnings.append(
                f"{underlying} over per-underlying cap: ${at_risk:,.0f} at risk"
                f" > ${cap:,.0f} ({settings.PER_UNDERLYING_FRACTION:.1%} of equity)"
            )
    return warnings


def size_entry(
    net_debit: float,
    equity: float | None,
    open_risk: float | None,
    underlying_risk: float | None,
    cycle_spent: float,
) -> tuple[int, str | None]:
    """Contracts to buy for one spread entry, or (0, reason) when refused.

    `underlying_risk` is the open premium already at risk on the entry's own
    underlying, so held spreads plus this entry stay under the per-underlying cap.
    """
    if equity is None or equity <= 0:
        return 0, "unknown_equity"
    if open_risk is None:
        return 0, "unknown_open_risk"
    if underlying_risk is None:
        return 0, "unknown_underlying_risk"
    if net_debit <= 0:
        return 0, "bad_debit"
    rooms = {
        "per_entry": settings.PER_ENTRY_FRACTION * equity,
        "per_underlying": settings.PER_UNDERLYING_FRACTION * equity - underlying_risk,
        "per_cycle": settings.PER_CYCLE_FRACTION * equity - cycle_spent,
        "total": settings.TOTAL_FRACTION * equity - open_risk - cycle_spent,
    }
    binding = min(rooms, key=rooms.get)  # type: ignore[arg-type]
    qty = math.floor(rooms[binding] / (net_debit * 100.0))
    if qty < 1:
        return 0, (
            f"risk_caps: {binding} room ${rooms[binding]:,.0f}"
            f" < contract cost ${net_debit * 100.0:,.0f}"
        )
    return qty, None
