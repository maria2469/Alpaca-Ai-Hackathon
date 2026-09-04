import json
from datetime import date, timedelta

from typer.testing import CliRunner

import broker
import pnl
from data_models import LegPosition, SpreadFill
from tests.fakes import NOW, FakeTradingClient, fake_mleg_fill, fake_position

LONG, SHORT = "AAPL260911C00330000", "AAPL260911C00340000"
EXP = date(2026, 9, 11)


def leg(symbol, strike, qty, avg, upl=None, cur=None):
    return LegPosition(
        symbol=symbol, underlying="AAPL", expiration=EXP, option_type="C", strike=strike,
        qty=qty, avg_entry_price=avg, unrealized_pl=upl, current_price=cur,
    )


def fill(coid, intent, qty, long_price, short_price, at=NOW):
    net = long_price - short_price if intent == "enter" else short_price - long_price
    return SpreadFill(
        client_order_id=coid, filled_at=at, intent=intent,
        long_symbol=LONG, short_symbol=SHORT, qty=qty, net_price=net,
    )


# --- positions_frame ---------------------------------------------------------


def test_positions_frame_sums_alpaca_marks_per_spread():
    legs = (leg(LONG, 330, 1, 3.9, upl=-40.0, cur=3.5), leg(SHORT, 340, -1, 1.25, upl=7.0, cur=1.18))
    frame, warnings = pnl.positions_frame(legs)
    assert warnings == []
    row = frame.iloc[0].to_dict()
    assert row["qty"] == 1
    assert row["entry_debit"] == 2.65
    assert row["mark"] == 2.32
    assert row["cost_basis"] == 265.0
    assert row["unrealized_pl"] == -33.0
    assert row["unrealized_pct"] == round(-33.0 / 265.0, 4)


def test_positions_frame_missing_mark_is_none_not_crash():
    legs = (leg(LONG, 330, 1, 3.9, upl=-40.0), leg(SHORT, 340, -1, 1.25))
    frame, _ = pnl.positions_frame(legs)
    row = frame.iloc[0].to_dict()
    assert row["unrealized_pl"] is None and row["mark"] is None and row["unrealized_pct"] is None


def test_positions_frame_unpaired_leg_is_warning_not_row():
    frame, warnings = pnl.positions_frame((leg(LONG, 330, 1, 3.9, upl=-40.0),))
    assert frame.empty
    assert len(warnings) == 1 and LONG in warnings[0]


# --- realized_frame ----------------------------------------------------------


def test_realized_frame_matches_exit_to_entry():
    fills = [
        fill("sp-1-enter-AAPL", "enter", 1, 3.9, 1.25),
        fill("sp-2-exit-AAPL-260911C", "exit", 1, 3.5, 1.18, at=NOW + timedelta(minutes=30)),
    ]
    frame, warnings = pnl.realized_frame(fills)
    assert warnings == []
    row = frame.iloc[0].to_dict()
    assert (row["underlying"], row["expiration"], row["type"]) == ("AAPL", EXP, "C")
    assert row["entry_debit"] == 2.65 and row["exit_credit"] == 2.32
    assert row["pnl"] == -33.0
    assert row["pnl_pct"] == round(-33.0 / 265.0, 4)
    assert row["hold_min"] == 30.0 and row["unmatched_qty"] == 0


def test_realized_frame_fifo_weights_two_entries():
    fills = [
        fill("sp-1-enter-AAPL", "enter", 1, 3.0, 1.0),  # debit 2.00
        fill("sp-2-enter-AAPL", "enter", 3, 4.0, 1.0, at=NOW + timedelta(minutes=1)),  # debit 3.00
        fill("sp-3-exit-AAPL-260911C", "exit", 4, 4.0, 1.0, at=NOW + timedelta(minutes=2)),  # credit 3.00
    ]
    frame, warnings = pnl.realized_frame(fills)
    assert warnings == [] and len(frame) == 1
    row = frame.iloc[0].to_dict()
    assert row["entry_debit"] == 2.75  # (1*2 + 3*3) / 4
    assert row["pnl"] == 100.0  # (3.00 - 2.75) * 4 * 100
    assert row["entered_at"] == NOW


def test_realized_frame_exit_without_entry_is_flagged():
    frame, warnings = pnl.realized_frame([fill("sp-9-exit-AAPL-260911C", "exit", 2, 3.5, 1.18)])
    row = frame.iloc[0].to_dict()
    assert row["unmatched_qty"] == 2 and row["pnl"] is None and row["entry_debit"] is None
    assert len(warnings) == 1 and "sp-9-exit" in warnings[0]


def test_realized_frame_ignores_open_entries():
    frame, warnings = pnl.realized_frame([fill("sp-1-enter-AAPL", "enter", 1, 3.9, 1.25)])
    assert frame.empty and warnings == []


# --- broker.fetch_spread_fills ------------------------------------------------


def test_fetch_spread_fills_reads_legs_and_filters_noise():
    orders = [
        fake_mleg_fill("sp-1-enter-AAPL", [(LONG, "buy", "buy_to_open", 3.9), (SHORT, "sell", "sell_to_open", 1.25)], 1),
        fake_mleg_fill("sp-2-exit-AAPL-260911C", [(LONG, "sell", "sell_to_close", 3.5), (SHORT, "buy", "buy_to_close", 1.18)], 1),
        fake_mleg_fill("manual-order", [(LONG, "buy", "buy_to_open", 3.9), (SHORT, "sell", "sell_to_open", 1.25)], 1),
        fake_mleg_fill("sp-3-enter-AAPL", [(LONG, "buy", "buy_to_open", 3.9)], 1),  # one leg
    ]
    fills = broker.fetch_spread_fills(FakeTradingClient(closed_orders=orders), after=None)
    assert [f.client_order_id for f in fills] == ["sp-1-enter-AAPL", "sp-2-exit-AAPL-260911C"]
    enter, exit_ = fills
    assert (enter.intent, enter.long_symbol, enter.short_symbol, enter.net_price) == ("enter", LONG, SHORT, 2.65)
    assert (exit_.intent, exit_.long_symbol, exit_.short_symbol, exit_.net_price) == ("exit", LONG, SHORT, -2.32)


# --- CLI ---------------------------------------------------------------------


def test_positions_cli_json(monkeypatch):
    trading = FakeTradingClient(positions=[
        fake_position(LONG, 1, 3.9, unrealized_pl=-40.0, current_price=3.5),
        fake_position(SHORT, 1, 1.25, side="short", unrealized_pl=7.0, current_price=1.18),
    ])
    monkeypatch.setattr(pnl, "_bootstrap", lambda: (broker.load_config({
        "ALPACA_API_KEY": "k", "ALPACA_SECRET_KEY": "s", "OPENROUTER_API_KEY": "o"}), trading))
    result = CliRunner().invoke(pnl.app, ["positions", "--json"])
    assert result.exit_code == 0, result.output
    rows = json.loads(result.stdout)
    assert rows[0]["unrealized_pl"] == -33.0 and rows[0]["long_symbol"] == LONG


def test_realized_cli_table(monkeypatch):
    trading = FakeTradingClient(closed_orders=[
        fake_mleg_fill("sp-1-enter-AAPL", [(LONG, "buy", "buy_to_open", 3.9), (SHORT, "sell", "sell_to_open", 1.25)], 1),
        fake_mleg_fill("sp-2-exit-AAPL-260911C", [(LONG, "sell", "sell_to_close", 3.5), (SHORT, "buy", "buy_to_close", 1.18)], 1,
                       filled_at=NOW + timedelta(minutes=5)),
    ])
    monkeypatch.setattr(pnl, "_bootstrap", lambda: (None, trading))
    result = CliRunner().invoke(pnl.app, ["realized", "--days", "7"])
    assert result.exit_code == 0, result.output
    assert "-33.0" in result.stdout and "total pnl: -33.00" in result.stdout


def test_realized_cli_json_shape_for_dashboard(monkeypatch):
    trading = FakeTradingClient(closed_orders=[
        fake_mleg_fill("sp-1-enter-AAPL", [(LONG, "buy", "buy_to_open", 3.9), (SHORT, "sell", "sell_to_open", 1.25)], 1),
        fake_mleg_fill("sp-2-exit-AAPL-260911C", [(LONG, "sell", "sell_to_close", 3.5), (SHORT, "buy", "buy_to_close", 1.18)], 1,
                       filled_at=NOW + timedelta(minutes=5)),
    ])
    monkeypatch.setattr(pnl, "_bootstrap", lambda: (None, trading))
    result = CliRunner().invoke(pnl.app, ["realized", "--json"])
    assert result.exit_code == 0, result.output
    rows = json.loads(result.stdout)
    assert len(rows) == 1
    # Keys the surge dashboard's Realized tab reads.
    assert set(pnl.REALIZED_COLUMNS) <= set(rows[0])
    assert rows[0]["pnl"] == -33.0 and rows[0]["unmatched_qty"] == 0
    assert rows[0]["exited_at"].startswith("2026-08-31 15:05:00")
