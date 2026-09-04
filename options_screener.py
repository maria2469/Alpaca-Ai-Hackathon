"""Option screener: pick the expiry, enumerate debit verticals, filter, rank, plan.

Pure functions over pre-fetched contracts and snapshots. Selection rule
(approved 2026-08-31, width rule revised 2026-09-01, empty-expiry skip added
2026-09-01): the nearest EXPIRIES_TO_SCREEN listed expiries (weeklies included)
with DTE >= MIN_DTE that have at least MIN_LIQUID_LEGS_PER_EXPIRY strikes within
MAX_WIDTH_PCT of spot carrying open interest >= MIN_OPEN_INTEREST, ranked as
one pool; candidate strike pairs within +/-10% of spot
(OTM strikes plus the ATM bracketing strike when OTM_ONLY) whose width is
between MIN_WIDTH_PCT and MAX_WIDTH_PCT of spot;
liquidity filter per leg (open interest floor + quote quality); rank survivors
by reward-to-risk (width - debit) / debit, highest first (rule revised
2026-09-01, was flattest IV skew), ties to tighter combined leg quotes.

Order plans are pure data. Only broker.submit_paper_order acts on one.
"""

from __future__ import annotations

from datetime import date, datetime

import pos_and_risk
import settings
from data_models import LegPlan, LegQuote, OpenSpread, OrderPlan, SpreadQuote

# All thresholds live in settings.yaml (screener section).


def pick_expirations(expirations: set[date], today: date) -> list[date]:
    """The nearest settings.EXPIRIES_TO_SCREEN listed expiries at least
    settings.MIN_DTE days out, nearest first; empty when there are none."""
    eligible = sorted(exp for exp in expirations if (exp - today).days >= settings.MIN_DTE)
    return eligible[: settings.EXPIRIES_TO_SCREEN]


def liquid_expirations(by_expiry: dict[date, dict[float, dict]], spot: float) -> set[date]:
    """Expiries with at least settings.MIN_LIQUID_LEGS_PER_EXPIRY strikes within
    settings.MAX_WIDTH_PCT of spot whose open_interest >= settings.MIN_OPEN_INTEREST
    (None counts as 0).

    ETFs like GLD/USO/XLE list Mon/Tue/Wed daily expiries with a full strike
    grid but ~zero open interest near spot (the few liquid strikes sit far
    out, useless for a 2-5%-wide vertical); without this filter they crowd out
    the liquid Friday weekly and monthly in pick_expirations. Input is the
    {expiry: {strike: {"symbol", "open_interest"}}} shape broker.fetch_contracts returns."""
    liquid: set[date] = set()
    for expiry, strikes in by_expiry.items():
        count = sum(
            1 for strike, info in strikes.items()
            if abs(strike - spot) <= spot * settings.MAX_WIDTH_PCT
            and (info.get("open_interest") or 0) >= settings.MIN_OPEN_INTEREST
        )
        if count >= settings.MIN_LIQUID_LEGS_PER_EXPIRY:
            liquid.add(expiry)
    return liquid


def quote_spread_bps(leg: LegQuote) -> float:
    """Bid-ask spread as basis points of the mid; needs a positive two-sided quote."""
    mid = (leg.bid + leg.ask) / 2  # type: ignore[operator]
    return (leg.ask - leg.bid) / mid * 10_000  # type: ignore[operator]


def check_leg(leg: LegQuote, server_time: datetime) -> str | None:
    """First failing liquidity/quality rule for one leg, or None when acceptable."""
    if leg.open_interest is None or leg.open_interest < settings.MIN_OPEN_INTEREST:
        return "low_open_interest"
    if leg.bid is None or leg.ask is None or leg.quote_time is None:
        return "no_quote"
    if leg.bid <= 0 or leg.ask <= 0 or leg.bid > leg.ask:
        return "crossed_quote"
    age = server_time.timestamp() - leg.quote_time.timestamp()
    # Snapshots are fetched after the clock read, so fresh quotes can legitimately
    # postdate server_time by the fetch latency; only reject implausible timestamps.
    if age < -settings.MAX_QUOTE_AGE_SECONDS:
        return "future_quote"
    if age > settings.MAX_QUOTE_AGE_SECONDS:
        return "stale_quote"
    if quote_spread_bps(leg) > settings.MAX_LEG_SPREAD_BPS:
        return "wide_spread"
    if leg.implied_vol is None or leg.implied_vol <= 0:
        return "missing_iv"
    return None


def enumerate_spreads(
    quotes_by_strike: dict[float, LegQuote],
    direction: str,
    spot: float,
    expiration: date,
    underlying: str,
    server_time: datetime,
) -> tuple[list[SpreadQuote], dict[str, int]]:
    """All acceptable debit verticals at one expiry, plus rejection tallies.

    Bull call: long the lower strike, short the higher. Bear put: long the
    higher strike, short the lower. Both legs must sit inside the strike band
    (out of the money, or the ATM strike bracketing spot, when
    settings.OTM_ONLY) and pass check_leg; the
    width must be within [MIN_WIDTH_PCT, MAX_WIDTH_PCT] of spot; the spread
    must price sanely (settings.MIN_NET_DEBIT <= debit < width) and the debit
    must sit inside [MIN_DEBIT_FRAC, MAX_DEBIT_FRAC] of width — a cheap debit
    means a deep-OTM lottery ticket, an expensive one has no payoff left.
    """
    lo, hi = spot * (1 - settings.STRIKE_BAND_PCT), spot * (1 + settings.STRIKE_BAND_PCT)
    in_band = [s for s in quotes_by_strike if lo <= s <= hi]
    if settings.OTM_ONLY:
        # OTM strikes plus the one ATM strike bracketing spot on the ITM side.
        itm = [s for s in in_band if (s <= spot if direction == "CALL" else s >= spot)]
        atm = (max(itm) if direction == "CALL" else min(itm)) if itm else None
        in_band = [
            s for s in in_band
            if s == atm or (s > spot if direction == "CALL" else s < spot)
        ]
    strikes = sorted(in_band)
    rejections: dict[str, int] = {}

    def _reject(reason: str) -> None:
        rejections[reason] = rejections.get(reason, 0) + 1

    if len(strikes) < 2:
        _reject("too_few_strikes_in_band")
        return [], rejections

    leg_ok: dict[float, bool] = {}
    for strike in strikes:
        reason = check_leg(quotes_by_strike[strike], server_time)
        leg_ok[strike] = reason is None
        if reason is not None:
            _reject(reason)

    spreads: list[SpreadQuote] = []
    min_width, max_width = spot * settings.MIN_WIDTH_PCT, spot * settings.MAX_WIDTH_PCT
    for i, lower in enumerate(strikes):
        for higher in strikes[i + 1:]:
            # Leg failures are already tallied per strike; skip silently so the
            # width tallies count only pairs with acceptable legs.
            if not (leg_ok[lower] and leg_ok[higher]):
                continue
            width = higher - lower
            if width > max_width:
                _reject("too_wide")
                continue
            if width < min_width:
                _reject("too_narrow")
                continue
            if direction == "CALL":
                long_leg, short_leg = quotes_by_strike[lower], quotes_by_strike[higher]
            else:
                long_leg, short_leg = quotes_by_strike[higher], quotes_by_strike[lower]
            net_debit = round(long_leg.ask - short_leg.bid, 2)  # type: ignore[operator]
            if not (settings.MIN_NET_DEBIT <= net_debit < width):
                _reject("bad_debit")
                continue
            if not (settings.MIN_DEBIT_FRAC * width <= net_debit <= settings.MAX_DEBIT_FRAC * width):
                _reject("debit_out_of_band")
                continue
            skew = abs(short_leg.implied_vol - long_leg.implied_vol)  # type: ignore[operator]
            spreads.append(
                SpreadQuote(
                    underlying=underlying,
                    direction=direction,
                    expiration=expiration,
                    long=long_leg,
                    short=short_leg,
                    width=width,
                    net_debit=net_debit,
                    skew=skew,
                )
            )
    return spreads, rejections


def rank_spreads(spreads: list[SpreadQuote]) -> list[SpreadQuote]:
    """Highest reward-to-risk first ((width - debit) / debit); ties go to
    tighter combined leg quotes (summed bid-ask bps)."""
    return sorted(
        spreads,
        key=lambda s: (
            -(s.width - s.net_debit) / s.net_debit,
            quote_spread_bps(s.long) + quote_spread_bps(s.short),
        ),
    )


def select_spread(
    chains: dict[date, dict[float, LegQuote]],
    direction: str,
    spot: float,
    underlying: str,
    server_time: datetime,
) -> tuple[SpreadQuote | None, dict[str, int]]:
    """Best spread across all given expiry chains; rejection tallies are summed."""
    all_spreads: list[SpreadQuote] = []
    tallies: dict[str, int] = {}
    for expiration, quotes_by_strike in chains.items():
        spreads, rejections = enumerate_spreads(
            quotes_by_strike, direction, spot, expiration, underlying, server_time
        )
        all_spreads += spreads
        for reason, count in rejections.items():
            tallies[reason] = tallies.get(reason, 0) + count
    ranked = rank_spreads(all_spreads)
    return (ranked[0] if ranked else None), tallies


def build_entry_plan(spread: SpreadQuote, qty: int, cycle_id: str) -> OrderPlan:
    """Buy-to-open MLEG limit at the marketable net debit."""
    return OrderPlan(
        kind="enter",
        underlying=spread.underlying,
        qty=qty,
        limit_price=spread.net_debit,
        legs=(
            LegPlan(symbol=spread.long.symbol, side="buy", intent="buy_to_open"),
            LegPlan(symbol=spread.short.symbol, side="sell", intent="sell_to_open"),
        ),
        client_order_id=f"sp-{cycle_id}-enter-{spread.underlying}",
    )


def _strike_tag(symbol: str) -> str:
    """Strike in OCC thousandths from an OCC symbol ("...C00262500" -> "262500").

    Digits only on purpose: Alpaca documents a 128-char cap on client_order_id but
    not an allowed character set, so we stay within [A-Za-z0-9-]. Unparseable
    symbols fall back to the raw symbol so the id still differs per spread.
    """
    return symbol[-8:].lstrip("0") or "0" if pos_and_risk.parse_occ(symbol) else symbol


def build_exit_plan(
    spread: OpenSpread,
    long_quote: LegQuote,
    short_quote: LegQuote,
    cycle_id: str,
) -> OrderPlan | None:
    """Sell-to-close MLEG limit at the marketable net price.

    Per the SDK convention the net limit is negative when the close collects a
    credit (the normal case) and positive when closing costs money.

    The client_order_id is unique per (cycle, spread): it carries both strikes,
    because two spreads on the same underlying/expiry/type can exit in one cycle
    and Alpaca refuses a duplicate id (seen 2026-09-01 with two AMZN call spreads).
    """
    if long_quote.bid is None or short_quote.ask is None:
        return None
    limit = round(short_quote.ask - long_quote.bid, 2)
    tag = (
        f"{spread.expiration:%y%m%d}{spread.option_type}"
        f"{_strike_tag(spread.long_symbol)}-{_strike_tag(spread.short_symbol)}"
    )
    return OrderPlan(
        kind="exit",
        underlying=spread.underlying,
        qty=spread.qty,
        limit_price=limit,
        legs=(
            LegPlan(symbol=spread.long_symbol, side="sell", intent="sell_to_close"),
            LegPlan(symbol=spread.short_symbol, side="buy", intent="buy_to_close"),
        ),
        client_order_id=f"sp-{cycle_id}-exit-{spread.underlying}-{tag}",
    )
