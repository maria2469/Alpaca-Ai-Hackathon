from datetime import date

import pytest

import pos_and_risk
import settings
from data_models import LegPosition, LegQuote, OpenSpread

EXP = date(2026, 9, 11)
TODAY = date(2026, 8, 31)


@pytest.fixture(autouse=True)
def pinned_settings(monkeypatch):
    """Sizing and exit tests assume these values regardless of trader edits to settings.yaml."""
    monkeypatch.setattr(settings, "PER_ENTRY_FRACTION", 0.005)
    monkeypatch.setattr(settings, "PER_UNDERLYING_FRACTION", 0.02)
    monkeypatch.setattr(settings, "PER_CYCLE_FRACTION", 0.01)
    monkeypatch.setattr(settings, "TOTAL_FRACTION", 0.10)
    monkeypatch.setattr(settings, "STOP_FRACTION", 0.5)
    monkeypatch.setattr(settings, "TAKE_PROFIT_MULT", 2.0)
    monkeypatch.setattr(settings, "TAKE_PROFIT_WIDTH_FRAC", 0.65)
    monkeypatch.setattr(settings, "EXIT_DTE", 2)


def leg(symbol="SPY260911C00650000", underlying="SPY", qty=1, price=3.0, strike=650.0, option_type="C"):
    return LegPosition(
        symbol=symbol, underlying=underlying, expiration=EXP, option_type=option_type,
        strike=strike, qty=qty, avg_entry_price=price,
    )


def quote(bid, ask):
    return LegQuote(symbol="X", strike=0.0, bid=bid, ask=ask, implied_vol=0.2,
                    open_interest=500, quote_time=None)


# --- OCC parsing ---

def test_parse_occ_round_trip():
    assert pos_and_risk.parse_occ("SPY260911C00650000") == ("SPY", EXP, "C", 650.0)
    assert pos_and_risk.parse_occ("IWM260911P00230500") == ("IWM", EXP, "P", 230.5)


@pytest.mark.parametrize("bad", ["", "SPY", "SPY260911X00650000", "SPY261341C00650000", "spy 650 call"])
def test_parse_occ_rejects_garbage(bad):
    assert pos_and_risk.parse_occ(bad) is None


# --- pairing ---

def test_pair_spreads_happy_path():
    legs = (
        leg("SPY260911C00650000", qty=2, price=6.0, strike=650.0),
        leg("SPY260911C00655000", qty=-2, price=3.5, strike=655.0),
    )
    spreads, warnings = pos_and_risk.pair_spreads(legs)
    assert warnings == []
    assert len(spreads) == 1
    spread = spreads[0]
    assert spread.qty == 2
    assert spread.net_entry_debit == 2.5
    assert spread.long_symbol == "SPY260911C00650000"


@pytest.mark.parametrize(
    "legs",
    [
        (leg(qty=1),),  # naked single leg
        (leg(qty=2), leg("SPY260911C00655000", qty=-1, strike=655.0)),  # unequal qty
        (leg(qty=1), leg("SPY260911C00655000", qty=1, strike=655.0)),  # two longs
    ],
)
def test_pair_spreads_warns_and_never_touches_odd_shapes(legs):
    spreads, warnings = pos_and_risk.pair_spreads(tuple(legs))
    assert spreads == []
    assert len(warnings) == 1


def test_pair_spreads_non_debit_pair_has_unknown_debit():
    legs = (
        leg("SPY260911C00650000", qty=1, price=2.0, strike=650.0),
        leg("SPY260911C00655000", qty=-1, price=3.0, strike=655.0),  # credit, not ours
    )
    spreads, _ = pos_and_risk.pair_spreads(legs)
    assert spreads[0].net_entry_debit is None


def test_pair_spreads_two_spreads_same_group_matched_by_qty():
    # Regression: the real AMZN book — two call spreads sharing expiry, x5 and x7
    legs = (
        leg("AMZN260911C00260000", underlying="AMZN", qty=5, price=2.77, strike=260.0),
        leg("AMZN260911C00262500", underlying="AMZN", qty=7, price=1.93, strike=262.5),
        leg("AMZN260911C00267500", underlying="AMZN", qty=-5, price=0.95, strike=267.5),
        leg("AMZN260911C00270000", underlying="AMZN", qty=-7, price=0.63, strike=270.0),
    )
    spreads, warnings = pos_and_risk.pair_spreads(legs)
    assert warnings == []
    by_qty = {s.qty: s for s in spreads}
    assert set(by_qty) == {5, 7}
    assert by_qty[5].long_symbol.endswith("00260000") and by_qty[5].short_symbol.endswith("00267500")
    assert by_qty[7].long_symbol.endswith("00262500") and by_qty[7].short_symbol.endswith("00270000")
    assert by_qty[5].net_entry_debit == pytest.approx(1.82)
    assert by_qty[7].net_entry_debit == pytest.approx(1.30)


def test_pair_spreads_equal_qty_spreads_decompose_by_nearest_strike():
    legs = (
        leg("SPY260911C00650000", qty=2, price=6.0, strike=650.0),
        leg("SPY260911C00660000", qty=2, price=4.0, strike=660.0),
        leg("SPY260911C00655000", qty=-2, price=5.0, strike=655.0),
        leg("SPY260911C00670000", qty=-2, price=2.0, strike=670.0),
    )
    spreads, warnings = pos_and_risk.pair_spreads(legs)
    assert warnings == []
    pairs = {(s.long_symbol[-8:], s.short_symbol[-8:]) for s in spreads}
    assert pairs == {("00650000", "00655000"), ("00660000", "00670000")}


def test_pair_spreads_put_vertical_short_must_be_below_long():
    good = (
        leg("SPY260911P00650000", qty=1, price=6.0, strike=650.0, option_type="P"),
        leg("SPY260911P00640000", qty=-1, price=4.0, strike=640.0, option_type="P"),
    )
    spreads, warnings = pos_and_risk.pair_spreads(good)
    assert warnings == [] and len(spreads) == 1
    assert spreads[0].net_entry_debit == pytest.approx(2.0)
    wrong_side = (
        leg("SPY260911P00650000", qty=1, price=6.0, strike=650.0, option_type="P"),
        leg("SPY260911P00660000", qty=-1, price=8.0, strike=660.0, option_type="P"),
    )
    spreads, warnings = pos_and_risk.pair_spreads(wrong_side)
    assert spreads == [] and len(warnings) == 1


def test_pair_spreads_reports_only_the_leftover_legs():
    legs = (
        leg("SPY260911C00650000", qty=2, price=6.0, strike=650.0),
        leg("SPY260911C00655000", qty=-2, price=3.5, strike=655.0),
        leg("SPY260911C00660000", qty=1, price=2.0, strike=660.0),  # naked extra long
    )
    spreads, warnings = pos_and_risk.pair_spreads(legs)
    assert len(spreads) == 1 and spreads[0].qty == 2
    assert len(warnings) == 1
    assert "SPY260911C00660000" in warnings[0]
    assert "SPY260911C00650000" not in warnings[0]


# --- mechanical exits ---

def spread(debit=2.0, expiration=EXP, underlying="SPY", qty=1, width=10.0):
    # default width 10: 0.65 x width = 6.5 > 2.0 x debit = 4.0, so the debit rule binds
    return OpenSpread(
        underlying=underlying, expiration=expiration, option_type="C",
        long_symbol="L", short_symbol="S", qty=qty, net_entry_debit=debit, width=width,
    )


def test_exit_at_exact_stop_threshold():
    # entry debit 2.00, stop at mark <= 1.00
    decision = pos_and_risk.exit_decision(spread(), quote(1.4, 1.6), quote(0.4, 0.6), TODAY)
    assert decision is not None and decision.reason == "stop" and decision.net_mark == 1.0


def test_exit_at_exact_take_profit_threshold():
    # entry debit 2.00, TP at mark >= 4.00 (pinned 2.0x; settings.yaml may differ)
    decision = pos_and_risk.exit_decision(spread(), quote(4.9, 5.1), quote(0.9, 1.1), TODAY)
    assert decision is not None and decision.reason == "take_profit" and decision.net_mark == 4.0


def test_take_profit_width_trigger_fires_below_debit_multiple():
    # debit 2.0, width 5: width trigger 0.65 x 5 = 3.25 is below the debit trigger 2.0 x 2 = 4.0
    tsla_like = spread(debit=2.0, width=5.0)
    at_width = pos_and_risk.exit_decision(tsla_like, quote(4.2, 4.3), quote(0.95, 1.05), TODAY)
    assert at_width is not None and at_width.reason == "take_profit"
    assert at_width.net_mark == pytest.approx(3.25)
    below = pos_and_risk.exit_decision(tsla_like, quote(4.1, 4.2), quote(0.95, 1.05), TODAY)
    assert below is None  # 3.15 < 3.25


def test_take_profit_without_width_uses_debit_multiple_only():
    no_width = spread(debit=2.0, width=None)
    assert pos_and_risk.exit_decision(no_width, quote(4.2, 4.3), quote(0.95, 1.05), TODAY) is None
    hit = pos_and_risk.exit_decision(no_width, quote(4.9, 5.1), quote(0.9, 1.1), TODAY)
    assert hit is not None and hit.reason == "take_profit" and hit.net_mark == 4.0


def test_hold_between_thresholds():
    assert pos_and_risk.exit_decision(spread(), quote(2.9, 3.1), quote(0.9, 1.1), TODAY) is None


def test_expiry_exit_at_dte_boundary():
    near = spread(expiration=date(2026, 9, 2))  # DTE 2
    decision = pos_and_risk.exit_decision(near, quote(2.9, 3.1), quote(0.9, 1.1), TODAY)
    assert decision is not None and decision.reason == "expiry"
    far = spread(expiration=date(2026, 9, 3))  # DTE 3
    assert pos_and_risk.exit_decision(far, quote(2.9, 3.1), quote(0.9, 1.1), TODAY) is None


def test_expiry_exit_survives_missing_marks():
    near = spread(expiration=date(2026, 9, 1))
    decision = pos_and_risk.exit_decision(near, None, None, TODAY)
    assert decision is not None and decision.reason == "expiry" and decision.net_mark is None


def test_opposing_event_fired_mapping():
    from data_models import Event

    call_spread = spread()  # option_type "C" — bullish
    put_event = (Event(kind="gap_down", direction="PUT"),)
    call_event = (Event(kind="breakout_up", direction="CALL"),)
    assert pos_and_risk.opposing_event_fired(call_spread, put_event) is True
    assert pos_and_risk.opposing_event_fired(call_spread, call_event) is False
    assert pos_and_risk.opposing_event_fired(call_spread, ()) is False
    put_spread = OpenSpread(
        underlying="SPY", expiration=EXP, option_type="P",
        long_symbol="L", short_symbol="S", qty=1, net_entry_debit=2.0,
    )
    assert pos_and_risk.opposing_event_fired(put_spread, call_event) is True
    assert pos_and_risk.opposing_event_fired(put_spread, put_event) is False


def test_held_direction():
    def spread(option_type, strike):
        return OpenSpread(
            underlying="SPY", expiration=date(2026, 9, 11), option_type=option_type,
            long_symbol=f"SPY260911{option_type}{int(strike * 1000):08d}",
            short_symbol=f"SPY260911{option_type}{int((strike + 5) * 1000):08d}",
            qty=1, net_entry_debit=2.0,
        )

    assert pos_and_risk.held_direction([]) is None
    assert pos_and_risk.held_direction([spread("C", 650)]) == "CALL"
    assert pos_and_risk.held_direction([spread("C", 650), spread("C", 660)]) == "CALL"
    assert pos_and_risk.held_direction([spread("P", 640)]) == "PUT"
    assert pos_and_risk.held_direction([spread("C", 650), spread("P", 640)]) is None  # mixed: no add


def test_reversal_exit_fires_between_stop_and_take_profit():
    # marks well inside the hold zone: only the opposing event can trigger this
    decision = pos_and_risk.exit_decision(
        spread(), quote(2.9, 3.1), quote(0.9, 1.1), TODAY, opposing_event=True
    )
    assert decision is not None and decision.reason == "reversal"
    assert decision.net_mark == 2.0


def test_reversal_exit_survives_unknown_debit_and_missing_marks():
    # stop/TP are blocked by unknown debit or missing quotes; reversal is not
    unknown_debit = pos_and_risk.exit_decision(
        spread(debit=None), quote(2.9, 3.1), quote(0.9, 1.1), TODAY, opposing_event=True
    )
    assert unknown_debit is not None and unknown_debit.reason == "reversal"
    no_marks = pos_and_risk.exit_decision(spread(), None, None, TODAY, opposing_event=True)
    assert no_marks is not None and no_marks.reason == "reversal" and no_marks.net_mark is None


def test_expiry_wins_over_reversal():
    near = spread(expiration=date(2026, 9, 1))
    decision = pos_and_risk.exit_decision(near, None, None, TODAY, opposing_event=True)
    assert decision is not None and decision.reason == "expiry"


def test_reversal_exit_can_be_disabled_in_settings(monkeypatch):
    import settings

    monkeypatch.setattr(settings, "REVERSAL_EXIT", False)
    decision = pos_and_risk.exit_decision(
        spread(), quote(2.9, 3.1), quote(0.9, 1.1), TODAY, opposing_event=True
    )
    assert decision is None  # back to hold: stop/TP zone untouched


def test_missing_marks_or_unknown_debit_hold_instead_of_guessing():
    assert pos_and_risk.exit_decision(spread(), None, quote(1, 1.2), TODAY) is None
    assert pos_and_risk.exit_decision(spread(), quote(1, 1.2), quote(None, None), TODAY) is None
    assert pos_and_risk.exit_decision(spread(debit=None), quote(0.1, 0.2), quote(0.0, 0.1), TODAY) is None


# --- risk sizing ---

def test_open_premium_at_risk_sums_or_refuses():
    known = [spread(debit=2.0), spread(debit=1.0)]
    assert pos_and_risk.open_premium_at_risk(known) == 300.0
    assert pos_and_risk.open_premium_at_risk([spread(debit=None)]) is None


def test_size_entry_caps_on_100k_equity():
    # per-entry cap 0.5% of 100k = $500; debit $2.00 -> $200/contract -> qty 2
    qty, reason = pos_and_risk.size_entry(2.0, 100_000.0, 0.0, 0.0, 0.0)
    assert (qty, reason) == (2, None)


def test_size_entry_refusals():
    assert pos_and_risk.size_entry(2.0, None, 0.0, 0.0, 0.0) == (0, "unknown_equity")
    assert pos_and_risk.size_entry(2.0, 0.0, 0.0, 0.0, 0.0) == (0, "unknown_equity")
    assert pos_and_risk.size_entry(2.0, 100_000.0, None, 0.0, 0.0) == (0, "unknown_open_risk")
    assert pos_and_risk.size_entry(2.0, 100_000.0, 0.0, None, 0.0) == (0, "unknown_underlying_risk")
    assert pos_and_risk.size_entry(0.0, 100_000.0, 0.0, 0.0, 0.0) == (0, "bad_debit")
    assert pos_and_risk.size_entry(6.0, 100_000.0, 0.0, 0.0, 0.0) == (
        0, "risk_caps: per_entry room $500 < contract cost $600"
    )


def test_size_entry_cycle_and_total_room():
    # cycle cap 1% = $1000; already spent $900 -> only $100 left -> qty 0 at $2 debit
    assert pos_and_risk.size_entry(2.0, 100_000.0, 0.0, 0.0, 900.0) == (
        0, "risk_caps: per_cycle room $100 < contract cost $200"
    )
    # total cap 10% = $10k; open risk $9,900 -> $100 room -> refused
    assert pos_and_risk.size_entry(2.0, 100_000.0, 9_900.0, 0.0, 0.0) == (
        0, "risk_caps: total room $100 < contract cost $200"
    )
    # open risk exactly at cap -> refused
    assert pos_and_risk.size_entry(2.0, 100_000.0, 10_000.0, 0.0, 0.0) == (
        0, "risk_caps: total room $0 < contract cost $200"
    )


def test_size_entry_per_underlying_room():
    # per-underlying cap 2% = $2,000; $1,900 already at risk on this underlying
    # -> $100 room -> refused at $2 debit even though every other cap has room
    assert pos_and_risk.size_entry(2.0, 100_000.0, 1_900.0, 1_900.0, 0.0) == (
        0, "risk_caps: per_underlying room $100 < contract cost $200"
    )
    # $1,500 at risk on this underlying -> $500 room -> per-entry still allows qty 2
    assert pos_and_risk.size_entry(2.0, 100_000.0, 1_500.0, 1_500.0, 0.0) == (2, None)


def test_over_cap_warnings():
    # cap 2% of 100k = $2,000; AMZN holds $1,050 + $1,000 = $2,050 across two spreads
    book = [
        spread(underlying="AMZN", debit=1.5, qty=7),
        spread(underlying="AMZN", debit=1.0, qty=10),
        spread(underlying="SPY", debit=2.0, qty=1),  # $200, comfortably under
    ]
    warnings = pos_and_risk.over_cap_warnings(book, 100_000.0)
    assert len(warnings) == 1
    assert "AMZN" in warnings[0] and "$2,050" in warnings[0] and "$2,000" in warnings[0]
    # exactly at the cap is not over it
    assert pos_and_risk.over_cap_warnings([spread(debit=2.0, qty=10)], 100_000.0) == []
    # unknown entry debit: skipped, covered by the unknown_open_risk entry refusal
    assert pos_and_risk.over_cap_warnings([spread(underlying="AMZN", debit=None)], 100_000.0) == []
    # unknown equity: no cap to compare against
    assert pos_and_risk.over_cap_warnings(book, None) == []
