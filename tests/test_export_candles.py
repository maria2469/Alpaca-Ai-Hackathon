from datetime import date, datetime, timedelta, timezone

import pandas as pd

import export_candles
import signals
from data_models import OpenSpread, SpreadFill

NOW = datetime(2026, 9, 1, 15, 0, tzinfo=timezone.utc)
BAR = 300


def frame(rows, end=NOW):
    stamps = [end - timedelta(seconds=BAR * (len(rows) - 1 - i)) for i in range(len(rows))]
    return pd.DataFrame(rows, index=pd.DatetimeIndex(stamps, name="timestamp"))


def ohlc(o, h, l, c):
    return {"open": o, "high": h, "low": l, "close": c, "volume": 1000.0}


def quiet(count, base=100.0):
    return [ohlc(base + 0.05 * i - 0.02, base + 0.05 * i + 0.5, base + 0.05 * i - 0.5, base + 0.05 * i)
            for i in range(count)]


# --- bar_events matches detect_events on the last bar ---

def _last_bar_events(rows):
    df = signals.add_indicators(frame(rows))
    return export_candles.bar_events(df)[-1], [e.kind for e in signals.detect_events(df)]


def test_bar_events_quiet_has_none():
    ours, theirs = _last_bar_events(quiet(60))
    assert ours == theirs == []


def test_bar_events_breakout_matches():
    rows = quiet(60)
    prev = rows[-2]["close"]
    rows[-1] = ohlc(prev, prev + 5.2, prev - 0.2, prev + 5.0)
    ours, theirs = _last_bar_events(rows)
    assert "breakout_up" in ours and ours == theirs


def test_bar_events_gap_down_matches():
    rows = quiet(60)
    prev = rows[-2]["close"]
    rows[-1] = ohlc(prev - 5.0, prev - 4.8, prev - 5.2, prev - 5.0)
    ours, theirs = _last_bar_events(rows)
    assert "gap_down" in ours and ours == theirs


def test_bar_events_first_bars_and_nan_atr_are_empty():
    df = signals.add_indicators(frame(quiet(5)))
    df.loc[df.index[2], "atr"] = float("nan")
    events = export_candles.bar_events(df)
    assert events[0] == [] and events[3] == []  # bar 3 uses bar 2's (NaN) ATR
    assert len(events) == 5


# --- frame_to_rows ---

def test_frame_to_rows_epoch_and_nan():
    df = export_candles.add_emas(signals.add_indicators(frame(quiet(3))))
    rows = export_candles.frame_to_rows(df)
    assert len(rows) == 3 and len(rows[0]) == len(export_candles.COLUMNS)
    assert rows[-1][0] == int(NOW.timestamp())
    assert rows[0][export_candles.COLUMNS.index("rsi")] is None  # first-bar RSI has no delta yet
    assert rows[-1][export_candles.COLUMNS.index("ema11")] is not None


# --- build_spreads ---

LONG, SHORT = "NVDA260909C00227500", "NVDA260909C00235000"
T_ENTER = datetime(2026, 9, 1, 15, 47, 30, tzinfo=timezone.utc)
T_EXIT = datetime(2026, 9, 1, 18, 50, 0, tzinfo=timezone.utc)

JOURNAL = [
    {
        "cycle_id": "20260901-154703",
        "started_at": "2026-09-01 15:47:03.069001+00:00",
        "candidates": [{"symbol": "NVDA", "events": ["gap_up"]}],
        "entry": {"symbol": "NVDA", "thesis": "gap and go", "spread": {"long": LONG, "short": SHORT}},
        "exits": [],
    },
    {
        "cycle_id": "20260901-185000",
        "started_at": "2026-09-01 18:50:00+00:00",
        "entry": None,
        "exits": [{"spread": "NVDA 2026-09-09 C", "reason": "reversal",
                   "receipt": {"client_order_id": "sp-20260901-185000-exit-NVDA-260909C"}}],
    },
]


def test_build_spreads_joins_journal_rows_with_entries_list():
    first = dict(JOURNAL[0])
    first.pop("entry")
    first["entries"] = [
        {"symbol": "AAPL", "thesis": "wrong one", "spread": {"long": "AAPL260909C00300000", "short": "AAPL260909C00310000"}},
        {"symbol": "NVDA", "thesis": "gap and go", "spread": {"long": LONG, "short": SHORT}},
    ]
    realized = [{
        "underlying": "NVDA", "qty": 11, "long_symbol": LONG, "short_symbol": SHORT,
        "entry_debit": 0.86, "exit_credit": 0.70, "pnl": -176.0, "pnl_pct": -0.186,
        "entered_at": T_ENTER, "exited_at": T_EXIT, "exit_order": "sp-20260901-185000-exit-NVDA-260909C",
    }]
    row = export_candles.build_spreads(realized, [], [], [first, JOURNAL[1]])["NVDA"][0]
    assert row["thesis"] == "gap and go" and row["cycle_id"] == "20260901-154703"


def test_build_spreads_closed_row_joins_journal():
    realized = [{
        "underlying": "NVDA", "qty": 11, "long_symbol": LONG, "short_symbol": SHORT,
        "entry_debit": 0.86, "exit_credit": 0.70, "pnl": -176.0, "pnl_pct": -0.186,
        "entered_at": T_ENTER, "exited_at": T_EXIT, "exit_order": "sp-20260901-185000-exit-NVDA-260909C",
    }]
    out = export_candles.build_spreads(realized, [], [], JOURNAL)
    row = out["NVDA"][0]
    assert row["status"] == "closed"
    assert (row["type"], row["direction"], row["expiration"]) == ("C", "CALL", "2026-09-09")
    assert (row["long_strike"], row["short_strike"]) == (227.5, 235.0)
    assert row["entered_at"] == int(T_ENTER.timestamp()) and row["exited_at"] == int(T_EXIT.timestamp())
    assert row["exit_reason"] == "reversal"
    assert row["thesis"] == "gap and go" and row["events_at_entry"] == ["gap_up"]
    assert row["cycle_id"] == "20260901-154703"


def test_build_spreads_open_row_uses_enter_fill_time():
    spread = OpenSpread("NVDA", date(2026, 9, 9), "C", LONG, SHORT, 11, 0.86)
    fills = [SpreadFill("sp-20260901-154703-enter-NVDA", T_ENTER, "enter", LONG, SHORT, 11, 0.86)]
    out = export_candles.build_spreads([], [spread], fills, JOURNAL)
    row = out["NVDA"][0]
    assert row["status"] == "open" and row["exited_at"] is None and row["pnl"] is None
    assert row["entered_at"] == int(T_ENTER.timestamp())
    assert row["entry_debit"] == 0.86 and row["thesis"] == "gap and go"


def test_build_spreads_unmatched_journal_gives_nulls():
    spread = OpenSpread("SPY", date(2026, 9, 9), "P", "SPY260909P00640000", "SPY260909P00635000", 3, 1.2)
    out = export_candles.build_spreads([], [spread], [], JOURNAL)
    row = out["SPY"][0]
    assert row["entered_at"] is None and row["thesis"] is None and row["exit_reason"] is None
    assert row["direction"] == "PUT" and row["long_strike"] == 640.0
