import re
from datetime import date, datetime, timedelta, timezone

import pytest

import options_screener as screener
import settings
from data_models import LegQuote, OpenSpread

NOW = datetime(2026, 8, 31, 15, 0, tzinfo=timezone.utc)
TODAY = NOW.date()
EXP = date(2026, 9, 11)


@pytest.fixture(autouse=True)
def pinned_screener_settings(monkeypatch):
    """These tests assume a 3%-5% width band and chains that straddle spot,
    regardless of trader edits to settings.yaml; the OTM-only filter has its
    own dedicated tests below."""
    monkeypatch.setattr(settings, "OTM_ONLY", False)
    monkeypatch.setattr(settings, "MIN_WIDTH_PCT", 0.03)
    monkeypatch.setattr(settings, "MAX_WIDTH_PCT", 0.05)
    monkeypatch.setattr(settings, "EXPIRIES_TO_SCREEN", 3)
    # Wide-open debit band: the band has its own dedicated test below.
    monkeypatch.setattr(settings, "MIN_DEBIT_FRAC", 0.01)
    monkeypatch.setattr(settings, "MAX_DEBIT_FRAC", 0.99)


def leg(
    symbol="OPT", strike=100.0, bid=2.0, ask=2.05, iv=0.20, oi=500,
    stamp=NOW, **_,
):
    return LegQuote(
        symbol=symbol, strike=strike, bid=bid, ask=ask,
        implied_vol=iv, open_interest=oi, quote_time=stamp,
    )


# --- expiration ---

def test_pick_expirations_nearest_n_at_least_5_dte(monkeypatch):
    monkeypatch.setattr(settings, "EXPIRIES_TO_SCREEN", 2)
    friday_weekly = date(2026, 9, 4)  # DTE 4 -> too near
    next_weekly = date(2026, 9, 8)  # DTE 8 -> nearest eligible
    monthly = date(2026, 9, 18)
    later = date(2026, 9, 25)  # third eligible -> beyond the N=2 cut
    listed = {friday_weekly, next_weekly, monthly, later}
    assert screener.pick_expirations(listed, TODAY) == [next_weekly, monthly]
    assert screener.pick_expirations({friday_weekly}, TODAY) == []
    boundary = date(2026, 9, 5)  # DTE exactly 5 qualifies
    assert screener.pick_expirations({boundary}, TODAY) == [boundary]


def test_liquid_expirations_drops_expiries_without_two_liquid_strikes(monkeypatch):
    monkeypatch.setattr(settings, "MIN_OPEN_INTEREST", 100)
    monkeypatch.setattr(settings, "MIN_LIQUID_LEGS_PER_EXPIRY", 2)
    spot = 400.0  # MAX_WIDTH_PCT is pinned to 0.05 -> strikes 380..420 count
    daily = date(2026, 9, 8)  # GLD Tuesday: liquid OI only far out of the money
    weekly = date(2026, 9, 11)
    thin = date(2026, 9, 14)  # one liquid strike near spot
    by_expiry = {
        daily: {
            400.0: {"symbol": "A", "open_interest": 0},
            401.0: {"symbol": "B", "open_interest": None},
            430.0: {"symbol": "C", "open_interest": 900},  # outside 5% of spot
            440.0: {"symbol": "D", "open_interest": 900},
        },
        weekly: {400.0: {"symbol": "E", "open_interest": 100}, 420.0: {"symbol": "F", "open_interest": 2500}},
        thin: {400.0: {"symbol": "G", "open_interest": 800}, 401.0: {"symbol": "H", "open_interest": 99}},
    }
    assert screener.liquid_expirations(by_expiry, spot) == {weekly}
    assert screener.liquid_expirations({}, spot) == set()


# --- leg quality ---

@pytest.mark.parametrize(
    ("bad_leg", "reason"),
    [
        (leg(oi=99), "low_open_interest"),
        (leg(oi=None), "low_open_interest"),
        (leg(bid=None), "no_quote"),
        (leg(stamp=None), "no_quote"),
        (leg(bid=2.2, ask=2.1), "crossed_quote"),
        (leg(bid=0.0), "crossed_quote"),
        (leg(stamp=NOW + timedelta(seconds=11)), "future_quote"),  # > 10s ahead
        (leg(stamp=NOW - timedelta(seconds=11)), "stale_quote"),
        (leg(bid=1.0, ask=1.2), "wide_spread"),  # ~1818 bps
        (leg(iv=None), "missing_iv"),
        (leg(iv=0.0), "missing_iv"),
    ],
)
def test_check_leg_rejections(bad_leg, reason):
    assert screener.check_leg(bad_leg, NOW) == reason


def test_check_leg_accepts_good_quote():
    assert screener.check_leg(leg(), NOW) is None
    # quotes fetched after the clock read may postdate it slightly; still fresh
    assert screener.check_leg(leg(stamp=NOW + timedelta(seconds=5)), NOW) is None


# --- enumeration ---

def chain(strikes_and_quotes):
    return {strike: q for strike, q in strikes_and_quotes.items()}


def good_chain():
    # strikes 95..105, tight quotes, all legs pass; spot 100 -> widths 3..5 acceptable
    return {
        95.0: leg("C95", 95.0, bid=6.0, ask=6.1, iv=0.20, oi=800),
        100.0: leg("C100", 100.0, bid=3.4, ask=3.5, iv=0.21, oi=900),
        105.0: leg("C105", 105.0, bid=1.5, ask=1.55, iv=0.25, oi=700),
    }


def test_enumerate_call_spread_sides_and_pricing():
    spreads, rejections = screener.enumerate_spreads(good_chain(), "CALL", 100.0, EXP, "SPY", NOW)
    assert rejections == {"too_wide": 1}  # 95/105: width 10 = 10% of spot
    pair = {(s.long.symbol, s.short.symbol) for s in spreads}
    # bull call: long the lower strike, short the higher; 95/105 (width 10 = 10%
    # of spot) is outside the 3%-5% width band
    assert pair == {("C95", "C100"), ("C100", "C105")}
    near = next(s for s in spreads if (s.long.symbol, s.short.symbol) == ("C95", "C100"))
    assert near.net_debit == round(6.1 - 3.4, 2)
    assert near.width == 5.0


def put_chain():
    # put premiums rise with strike
    return {
        95.0: leg("P95", 95.0, bid=1.5, ask=1.55, iv=0.22, oi=700),
        100.0: leg("P100", 100.0, bid=3.4, ask=3.5, iv=0.21, oi=900),
        105.0: leg("P105", 105.0, bid=6.0, ask=6.1, iv=0.20, oi=800),
    }


def test_enumerate_put_spread_reverses_sides():
    spreads, _ = screener.enumerate_spreads(put_chain(), "PUT", 100.0, EXP, "SPY", NOW)
    pair = {(s.long.symbol, s.short.symbol) for s in spreads}
    # bear put: long the higher strike, short the lower
    assert pair == {("P105", "P100"), ("P100", "P95")}


def test_strike_band_excludes_far_strikes():
    quotes = good_chain()
    quotes[125.0] = leg("C125", 125.0)  # outside +10% of spot 100
    spreads, _ = screener.enumerate_spreads(quotes, "CALL", 100.0, EXP, "SPY", NOW)
    assert all("C125" not in (s.long.symbol, s.short.symbol) for s in spreads)


def test_too_few_strikes_in_band_is_tallied():
    quotes = {125.0: leg("C125", 125.0)}  # outside +10% of spot 100
    spreads, rejections = screener.enumerate_spreads(quotes, "CALL", 100.0, EXP, "SPY", NOW)
    assert spreads == [] and rejections == {"too_few_strikes_in_band": 1}


def test_width_band_is_3_to_5_pct_of_spot():
    quotes = {
        96.0 + i: leg(f"C{i}", 96.0 + i, bid=10.0 - 0.5 * i, ask=10.05 - 0.5 * i, oi=500)
        for i in range(9)  # strikes 96..104, $1 steps
    }
    spreads, _ = screener.enumerate_spreads(quotes, "CALL", 100.0, EXP, "SPY", NOW)
    # spot 100 -> only widths 3.0..5.0 qualify (min 3%, max 5%)
    assert spreads and {s.width for s in spreads} == {3.0, 4.0, 5.0}


def test_otm_plus_atm_call_keeps_bracketing_strike(monkeypatch):
    monkeypatch.setattr(settings, "OTM_ONLY", True)
    quotes = {
        96.0 + i: leg(f"C{i}", 96.0 + i, bid=10.0 - 0.5 * i, ask=10.05 - 0.5 * i, oi=500)
        for i in range(9)  # strikes 96..104, $1 steps
    }
    spreads, _ = screener.enumerate_spreads(quotes, "CALL", 100.0, EXP, "SPY", NOW)
    # kept strikes: ATM 100 (highest <= spot) plus OTM 101..104; 96..99 excluded
    assert {(s.long.strike, s.short.strike) for s in spreads} == {
        (100.0, 103.0), (100.0, 104.0), (101.0, 104.0),
    }


def test_otm_plus_atm_put_keeps_bracketing_strike(monkeypatch):
    monkeypatch.setattr(settings, "OTM_ONLY", True)
    quotes = {
        96.0 + i: leg(f"P{i}", 96.0 + i, bid=5.0 + 0.5 * i, ask=5.05 + 0.5 * i, oi=500)
        for i in range(9)  # put premiums rise with strike
    }
    spreads, _ = screener.enumerate_spreads(quotes, "PUT", 100.0, EXP, "SPY", NOW)
    # kept strikes: ATM 100 (lowest >= spot) plus OTM 96..99; 101..104 excluded
    assert {(s.long.strike, s.short.strike) for s in spreads} == {
        (99.0, 96.0), (100.0, 96.0), (100.0, 97.0),
    }


def test_debit_band_rejects_lottery_and_overpriced(monkeypatch):
    monkeypatch.setattr(settings, "MIN_DEBIT_FRAC", 0.25)
    monkeypatch.setattr(settings, "MAX_DEBIT_FRAC", 0.45)
    quotes = {
        95.0: leg("C95", 95.0, bid=6.0, ask=6.1),     # 95/100: debit 2.7 / width 5 = 0.54 -> too expensive
        100.0: leg("C100", 100.0, bid=3.4, ask=3.5),
        103.0: leg("C103", 103.0, bid=3.0, ask=3.05),  # 100/103: debit 0.5 / width 3 = 0.17 -> lottery ticket
        105.0: leg("C105", 105.0, bid=1.5, ask=1.55),  # 100/105: debit 2.0 / width 5 = 0.40 -> kept
    }
    spreads, rejections = screener.enumerate_spreads(quotes, "CALL", 100.0, EXP, "SPY", NOW)
    assert {(s.long.symbol, s.short.symbol) for s in spreads} == {("C100", "C105")}
    assert rejections.get("debit_out_of_band") == 2


def test_debit_sanity_rejections():
    quotes = {
        95.0: leg("A", 95.0, bid=8.2, ask=8.4, iv=0.2),
        100.0: leg("B", 100.0, bid=3.1, ask=3.2, iv=0.2),
    }
    # debit 8.4 - 3.1 = 5.3 >= width 5 -> rejected
    spreads, rejections = screener.enumerate_spreads(quotes, "CALL", 100.0, EXP, "SPY", NOW)
    assert spreads == [] and rejections.get("bad_debit") == 1


def test_bad_leg_blocks_pairs_but_not_others():
    quotes = good_chain()
    quotes[95.0] = leg("C95", 95.0, bid=6.0, ask=6.1, iv=None)  # kills any pair using 95
    spreads, rejections = screener.enumerate_spreads(quotes, "CALL", 100.0, EXP, "SPY", NOW)
    assert rejections.get("missing_iv") == 1
    assert {(s.long.symbol, s.short.symbol) for s in spreads} == {("C100", "C105")}


# --- ranking ---

def test_rank_reward_to_risk_first_with_quote_tiebreak():
    tight = leg("T", 100.0, bid=2.00, ask=2.02)   # ~100 bps quote
    wide = leg("W", 105.0, bid=1.90, ask=2.10)    # ~1000 bps quote
    from data_models import SpreadQuote

    def sq(long, short, width, debit):
        return SpreadQuote(
            underlying="SPY", direction="CALL", expiration=EXP,
            long=long, short=short, width=width, net_debit=debit, skew=0.0,
        )

    poor = sq(tight, tight, 5.0, 2.5)  # (5 - 2.5) / 2.5 = 1.0
    rich = sq(wide, wide, 5.0, 1.0)    # (5 - 1.0) / 1.0 = 4.0 -> wins despite wide quotes
    assert screener.rank_spreads([poor, rich])[0] is rich
    # tie on reward-to-risk -> tighter combined leg quotes win
    tie_wide = sq(wide, wide, 5.0, 2.5)
    tie_tight = sq(tight, tight, 5.0, 2.5)
    assert screener.rank_spreads([tie_wide, tie_tight])[0] is tie_tight


def test_select_spread_ranks_across_expiries():
    near, far = date(2026, 9, 11), date(2026, 9, 18)
    # near chain's best: 100/105, debit 3.5 - 1.5 = 2.0 -> rr 1.5
    # far chain: 95/100, debit 5.1 - 4.0 = 1.1 -> rr 3.55, best overall
    far_chain = {
        95.0: leg("F95", 95.0, bid=5.0, ask=5.1, iv=0.20, oi=800),
        100.0: leg("F100", 100.0, bid=4.0, ask=4.1, iv=0.21, oi=900),
    }
    best, tallies = screener.select_spread(
        {near: good_chain(), far: far_chain}, "CALL", 100.0, "SPY", NOW
    )
    assert best is not None and best.expiration == far
    assert (best.long.symbol, best.short.symbol) == ("F95", "F100")
    assert tallies == {"too_wide": 1}  # near chain's 95/105 pair; summed across chains


# --- order plans ---

def open_spread():
    return OpenSpread(
        underlying="SPY", expiration=EXP, option_type="C",
        long_symbol="SPY260911C00450000", short_symbol="SPY260911C00455000", qty=2, net_entry_debit=2.0,
    )


def test_entry_plan_is_deterministic_and_debit_positive():
    spreads, _ = screener.enumerate_spreads(good_chain(), "CALL", 100.0, EXP, "SPY", NOW)
    top = screener.rank_spreads(spreads)[0]
    plan = screener.build_entry_plan(top, 2, "20260831-150000")
    assert plan.client_order_id == "sp-20260831-150000-enter-SPY"
    assert plan.kind == "enter" and plan.qty == 2 and plan.limit_price > 0
    assert plan.legs[0].intent == "buy_to_open" and plan.legs[1].intent == "sell_to_open"
    again = screener.build_entry_plan(top, 2, "20260831-150000")
    assert again.client_order_id == plan.client_order_id  # duplicate prevention key


def test_exit_plan_credit_is_negative_net_price():
    long_q = leg("LSYM", 95.0, bid=6.0, ask=6.2)
    short_q = leg("SSYM", 100.0, bid=3.0, ask=3.2)
    plan = screener.build_exit_plan(open_spread(), long_q, short_q, "20260831-150000")
    assert plan is not None
    assert plan.limit_price == round(3.2 - 6.0, 2) == -2.8  # credit -> negative
    assert plan.legs[0].intent == "sell_to_close" and plan.legs[1].intent == "buy_to_close"
    assert plan.qty == 2
    assert plan.client_order_id == "sp-20260831-150000-exit-SPY-260911C450000-455000"


def test_exit_plan_ids_differ_for_two_spreads_same_expiry_and_type():
    # 2026-09-01 18:50: two AMZN 2026-09-11 call spreads exited in one cycle and shared an id,
    # so Alpaca refused the second order. The strikes must make the ids distinct.
    exp = date(2026, 9, 11)
    a = OpenSpread(underlying="AMZN", expiration=exp, option_type="C",
                   long_symbol="AMZN260911C00260000", short_symbol="AMZN260911C00267500", qty=5, net_entry_debit=1.82)
    b = OpenSpread(underlying="AMZN", expiration=exp, option_type="C",
                   long_symbol="AMZN260911C00262500", short_symbol="AMZN260911C00270000", qty=7, net_entry_debit=1.30)
    ids = {screener.build_exit_plan(s, leg(bid=1.0, ask=1.1), leg(bid=0.5, ask=0.6), "20260901-185000").client_order_id
           for s in (a, b)}
    assert ids == {"sp-20260901-185000-exit-AMZN-260911C260000-267500", "sp-20260901-185000-exit-AMZN-260911C262500-270000"}
    # Alpaca caps the id at 128 chars and documents no character set: stay alphanumeric + hyphen.
    assert all(len(i) <= 128 and re.fullmatch(r"[A-Za-z0-9-]+", i) for i in ids)


def test_exit_plan_refuses_missing_quotes():
    assert screener.build_exit_plan(open_spread(), leg(bid=None), leg(), "cid") is None
