"""Read-only liquidity probe for whitelist candidates.

Usage (from the repo root):
    uv run --env-file .env python .claude/skills/whitelist-candidates/probe.py SYM [SYM ...]

For each symbol it answers, with the trader's CURRENT settings.yaml thresholds:
  * does Alpaca's IEX feed give enough bars at BAR_TIMEFRAME for the indicators?
  * does the strike grid allow a vertical between MIN_WIDTH_PCT and MAX_WIDTH_PCT of spot?
  * which expiries would the screener pick (after the liquid-expiry filter), and how many
    strikes near spot carry OI >= MIN_OPEN_INTEREST in each?
  * during market hours: how many of those legs also pass the quote filter
    (two-sided, <= MAX_LEG_SPREAD_BPS, IV present)?

It only reads: quotes, bars, contracts, option snapshots. No orders, no file edits.
The final say is `cli.py screen SYM --direction CALL|PUT`, which runs the real screener.
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

import broker  # noqa: E402
import market_data  # noqa: E402
import options_screener  # noqa: E402
import settings  # noqa: E402

SNAPSHOT_CAP = 200  # legs per symbol we bother quoting; plenty for a liquidity read


def width_fits(step: float | None, spot: float) -> str:
    if not step:
        return "?"
    lo, hi = spot * settings.MIN_WIDTH_PCT, spot * settings.MAX_WIDTH_PCT
    return "yes" if any(lo <= k * step <= hi for k in range(1, 400)) else "NO"


def strike_step(strikes: list[float]) -> float | None:
    diffs = sorted({round(b - a, 2) for a, b in zip(strikes, strikes[1:]) if b > a})
    return diffs[0] if diffs else None


def near_spot(strike: float, spot: float) -> bool:
    return abs(strike - spot) <= spot * settings.MAX_WIDTH_PCT


def passing_legs(option_data, legs: list[dict]) -> int:
    """Legs whose live snapshot would clear check_leg's quote/IV rules (OI already filtered)."""
    symbols = [leg["symbol"] for leg in legs][:SNAPSHOT_CAP]
    if not symbols:
        return 0
    snapshots = broker.fetch_option_snapshots(option_data, symbols)
    count = 0
    for symbol in symbols:
        snap = snapshots.get(symbol)
        quote = getattr(snap, "latest_quote", None) if snap else None
        bid = broker.as_float(getattr(quote, "bid_price", None))
        ask = broker.as_float(getattr(quote, "ask_price", None))
        iv = broker.as_float(getattr(snap, "implied_volatility", None)) if snap else None
        if not (bid and ask and 0 < bid <= ask and iv and iv > 0):
            continue
        if (ask - bid) / ((bid + ask) / 2) * 10_000 <= settings.MAX_LEG_SPREAD_BPS:
            count += 1
    return count


def probe_side(trading, option_data, symbol: str, direction: str, spot: float,
               today: date, market_open: bool) -> dict:
    by_expiry = broker.fetch_contracts(trading, symbol, direction, spot, today)
    picked = options_screener.pick_expirations(
        options_screener.liquid_expirations(by_expiry, spot), today
    )
    nearest = sorted(by_expiry)[:1]
    step = strike_step(sorted(by_expiry[nearest[0]])) if nearest else None
    per_expiry = []
    liquid_legs: list[dict] = []
    for exp in picked:
        legs = [
            info for strike, info in by_expiry[exp].items()
            if near_spot(strike, spot) and (info["open_interest"] or 0) >= settings.MIN_OPEN_INTEREST
        ]
        per_expiry.append(f"{exp.strftime('%m/%d')}:{len(legs)}")
        liquid_legs.extend(legs)
    passing = passing_legs(option_data, liquid_legs) if market_open else None
    return {
        "listed": len(by_expiry),
        "step": step,
        "picked": per_expiry,
        "liquid": len(liquid_legs),
        "passing": passing,
    }


def verdict(bars: int, fit: str, calls: dict, puts: dict, market_open: bool) -> str:
    if bars < settings.MIN_BARS:
        return f"thin: only {bars} {settings.BAR_TIMEFRAME} bars (< min_bars {settings.MIN_BARS})"
    if fit != "yes":
        return "thin: strike grid cannot make a width in the min/max_width_pct band"
    if not calls["picked"] and not puts["picked"]:
        return "thin: no expiry has enough liquid strikes near spot (see min_liquid_legs_per_expiry)"
    if not market_open:
        return "liquid OI (quotes unverified: market closed — run cli.py screen during hours)"
    if calls["passing"] >= 4 and puts["passing"] >= 4:
        return "strong"
    if calls["passing"] or puts["passing"]:
        return "marginal: few legs clear the quote filter right now"
    return "thin: OI present but quotes wider than max_leg_spread_bps"


def main(symbols: list[str]) -> int:
    if not symbols:
        print(__doc__)
        return 2
    symbols = list(dict.fromkeys(s.strip().upper() for s in symbols if s.strip()))
    config = broker.load_config()
    trading, stock_data, option_data = broker.build_clients(config)
    clock = broker.fetch_clock(trading)
    now, today = clock.server_time, clock.server_time.date()
    print(f"server_time={now.isoformat()} market_open={clock.is_open}")
    print(
        f"thresholds: bars>={settings.MIN_BARS}@{settings.BAR_TIMEFRAME}, "
        f"width {settings.MIN_WIDTH_PCT:.0%}-{settings.MAX_WIDTH_PCT:.0%} of spot, "
        f"OI>={settings.MIN_OPEN_INTEREST} within {settings.MAX_WIDTH_PCT:.0%} of spot, "
        f">={settings.MIN_LIQUID_LEGS_PER_EXPIRY} such strikes per expiry, "
        f"leg spread<={settings.MAX_LEG_SPREAD_BPS:.0f}bps, "
        f"nearest {settings.EXPIRIES_TO_SCREEN} expiries >= {settings.MIN_DTE} DTE"
    )
    in_whitelist = set(settings.SYMBOLS)
    print()

    mids = broker.fetch_spot_mids(stock_data, tuple(symbols))
    for symbol in symbols:
        tag = " (already whitelisted)" if symbol in in_whitelist else ""
        spot = mids.get(symbol)
        spot_note = ""
        try:
            bars = market_data.fetch_ohlcv(stock_data, symbol, settings.BAR_TIMEFRAME, now, 150)
        except market_data.MarketDataError as error:
            print(f"== {symbol}{tag}\n   bars: FAILED ({error}) -> verdict: thin: no IEX bar data\n")
            continue
        if spot is None:
            try:
                daily = market_data.fetch_ohlcv(stock_data, symbol, "1d", datetime.now(timezone.utc), 5)
                spot = float(daily["close"].iloc[-1]) if len(daily) else None
                spot_note = " (last daily close; no live quote)"
            except market_data.MarketDataError:
                spot = None
        if spot is None:
            print(f"== {symbol}{tag}\n   no usable quote or close -> verdict: thin: not a tradeable US equity/ETF?\n")
            continue
        try:
            calls = probe_side(trading, option_data, symbol, "CALL", spot, today, clock.is_open)
            puts = probe_side(trading, option_data, symbol, "PUT", spot, today, clock.is_open)
        except broker.BrokerError as error:
            print(f"== {symbol}{tag}\n   spot {spot:.2f}{spot_note}; contracts: FAILED ({error}) -> verdict: thin: no listed options\n")
            continue
        fit = width_fits(calls["step"] or puts["step"], spot)
        print(f"== {symbol}{tag}")
        print(f"   spot {spot:.2f}{spot_note}   {settings.BAR_TIMEFRAME} bars {len(bars)}   "
              f"strike step {calls['step'] or puts['step']}   width fit {fit}   "
              f"listed expiries {calls['listed']}")
        for label, side in (("CALL", calls), ("PUT", puts)):
            passing = "n/a (closed)" if side["passing"] is None else side["passing"]
            print(f"   {label}: picked {side['picked'] or '[]'}  liquid legs near spot {side['liquid']}  "
                  f"passing quote filter {passing}")
        print(f"   verdict: {verdict(len(bars), fit, calls, puts, clock.is_open)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
