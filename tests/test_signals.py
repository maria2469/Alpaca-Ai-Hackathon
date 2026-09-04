from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

import signals
from data_models import SymbolFeatures

NOW = datetime(2026, 8, 31, 15, 0, tzinfo=timezone.utc)
BAR_SECONDS = 900  # 15m


def frame(rows: list[dict], *, end: datetime | None = None) -> pd.DataFrame:
    """OHLCV frame with 15m bar-start stamps ending at `end` (a completed bar)."""
    end = end if end is not None else NOW - timedelta(seconds=BAR_SECONDS)
    stamps = [end - timedelta(seconds=BAR_SECONDS * (len(rows) - 1 - i)) for i in range(len(rows))]
    return pd.DataFrame(rows, index=pd.DatetimeIndex(stamps, name="timestamp"))


def ohlc(open_, high, low, close, volume=1000.0):
    return {"open": open_, "high": high, "low": low, "close": close, "volume": volume}


def quiet_rows(count, base=100.0):
    # Gentle linear drift: ATR ~1, tiny bodies/gaps, MACD hist stays one-signed
    # (an oscillating series would fire spurious macd_cross events).
    return [
        ohlc(base + 0.05 * i - 0.02, base + 0.05 * i + 0.5, base + 0.05 * i - 0.5, base + 0.05 * i)
        for i in range(count)
    ]


# --- indicators ---

def test_rsi_bounds_and_direction():
    up = frame([ohlc(100 + i, 100.6 + i, 99.5 + i, 100.5 + i) for i in range(60)])
    down = frame([ohlc(200 - i, 200.6 - i, 199.4 - i, 199.5 - i) for i in range(60)])
    rsi_up = signals.add_indicators(up)["rsi"].iloc[-1]
    rsi_down = signals.add_indicators(down)["rsi"].iloc[-1]
    assert rsi_up == 100.0  # pure gains
    assert 0.0 <= rsi_down < 30.0


def test_rsi_flat_series_is_neutral():
    flat = frame([ohlc(100.0, 100.0, 100.0, 100.0) for _ in range(60)])
    assert signals.add_indicators(flat)["rsi"].iloc[-1] == 50.0  # not overbought


def test_atr_converges_to_constant_true_range():
    df = signals.add_indicators(frame(quiet_rows(120)))
    assert df["atr"].iloc[-1] == pytest.approx(1.0, abs=0.05)  # high-low is 1.0 every bar


def test_macd_hist_positive_after_fresh_uptrend():
    rows = quiet_rows(60) + [
        ohlc(100 + i, 100.6 + i, 99.5 + i, 100.5 + i) for i in range(10)
    ]
    df = signals.add_indicators(frame(rows))
    assert df["macd_hist"].iloc[-1] > 0
    assert {"rsi", "atr", "macd", "macd_signal", "macd_hist", "ema_fast", "ema_slow"} <= set(df.columns)


def test_trend_ema_distances_sign_and_short_history():
    rising = signals.add_indicators(frame([ohlc(100 + i, 100.6 + i, 99.5 + i, 100.5 + i) for i in range(60)]))
    features = signals.build_signal("SPY", rising, 100.0, NOW, BAR_SECONDS)
    # in a steady uptrend the close sits above both trailing EMAs
    assert features.ema_fast_dist is not None and features.ema_fast_dist > 0
    assert features.ema_slow_dist is not None and features.ema_slow_dist > 0
    # the slower anchor trails further behind the rising close
    assert features.ema_slow_dist > features.ema_fast_dist
    import settings

    short = signals.add_indicators(frame(quiet_rows(settings.MIN_BARS - 1)))
    thin = signals.build_signal("SPY", short, 100.0, NOW, BAR_SECONDS)
    assert thin.ema_fast_dist is None and thin.ema_slow_dist is None


# --- events (hand-built atr/macd_hist for exact boundaries) ---

def event_frame(prev: dict, last: dict) -> pd.DataFrame:
    df = frame([prev, last])
    df["atr"] = [prev.get("atr", 1.0), last.get("atr", 1.0)]
    df["macd_hist"] = [prev.get("macd_hist", 1.0), last.get("macd_hist", 1.0)]
    # Ensure RSI is set for testing RSI gates
    df["rsi"] = [prev.get("rsi", 50.0), last.get("rsi", 50.0)]
    return df


def test_gap_event_strictly_above_two_atr():
    prev = ohlc(100, 100.5, 99.5, 100.0)
    fires = signals.detect_events(event_frame(prev, ohlc(102.01, 102.5, 101.5, 102.0)))
    assert [e.kind for e in fires] == ["gap_up"] and fires[0].direction == "CALL"
    at_boundary = signals.detect_events(event_frame(prev, ohlc(102.0, 102.5, 101.5, 102.0)))
    assert at_boundary == ()  # exactly 2 x ATR does not fire
    down = signals.detect_events(event_frame(prev, ohlc(97.99, 98.5, 97.5, 98.0)))
    assert [e.kind for e in down] == ["gap_down"] and down[0].direction == "PUT"


def test_breakout_event_uses_bar_body():
    prev = ohlc(100, 100.5, 99.5, 100.0)
    up = signals.detect_events(event_frame(prev, ohlc(100.0, 102.6, 99.9, 102.01)))
    assert [e.kind for e in up] == ["breakout_up"]
    exact = signals.detect_events(event_frame(prev, ohlc(100.0, 102.5, 99.9, 102.0)))
    assert exact == ()
    down = signals.detect_events(event_frame(prev, ohlc(100.0, 100.1, 97.4, 97.99)))
    assert [e.kind for e in down] == ["breakout_down"] and down[0].direction == "PUT"


def test_macd_cross_events():
    prev = ohlc(100, 100.5, 99.5, 100.0)
    last = ohlc(100, 100.5, 99.5, 100.0)
    df = event_frame(prev, last)
    # Set ATR to 1.0, so threshold is 0.05. macd_hist of 0.5 exceeds threshold.
    df["atr"] = [1.0, 1.0]
    df["macd_hist"] = [-0.5, 0.5]
    assert [e.kind for e in signals.detect_events(df)] == ["macd_cross_up"]
    df["macd_hist"] = [0.5, -0.5]
    assert [e.kind for e in signals.detect_events(df)] == ["macd_cross_down"]
    df["macd_hist"] = [0.5, 0.7]  # same sign: no cross
    assert signals.detect_events(df) == ()
    # Below threshold: should not fire
    df["macd_hist"] = [-0.01, 0.01]  # 0.01 < 0.05 threshold
    assert signals.detect_events(df) == ()


def test_macd_cross_needs_magnitude(monkeypatch):
    import settings

    monkeypatch.setattr(settings, "MACD_MIN_HIST_ATR", 0.05)
    prev = ohlc(100, 100.5, 99.5, 100.0)
    last = ohlc(100, 100.5, 99.5, 100.0)
    df = event_frame(prev, last)  # atr defaults to 1.0 -> floor is |hist| >= 0.05
    df["macd_hist"] = [-0.5, 0.049]  # sub-threshold flip: chop, not momentum
    assert signals.detect_events(df) == ()
    df["macd_hist"] = [-0.5, 0.05]  # exactly at the floor fires
    assert [e.kind for e in signals.detect_events(df)] == ["macd_cross_up"]
    df["macd_hist"] = [0.5, -0.049]
    assert signals.detect_events(df) == ()
    df["macd_hist"] = [0.5, -0.05]
    assert [e.kind for e in signals.detect_events(df)] == ["macd_cross_down"]


def test_events_need_usable_atr_and_two_bars():
    prev = ohlc(100, 100.5, 99.5, 100.0)
    df = event_frame(prev, ohlc(110, 111, 109, 110))
    df["atr"] = [float("nan"), 1.0]
    assert signals.detect_events(df) == ()  # unknown ATR is never guessed around
    assert signals.detect_events(df.iloc[-1:]) == ()  # single bar


def test_gap_and_breakout_can_fire_together_in_fixed_order():
    prev = ohlc(100, 100.5, 99.5, 100.0)
    both = signals.detect_events(event_frame(prev, ohlc(103.0, 106.5, 102.5, 106.0)))
    assert [e.kind for e in both] == ["gap_up", "breakout_up"]


def test_rsi_exhaustion_gates():
    import settings
    prev = ohlc(100, 100.5, 99.5, 100.0)
    # CALL blocked at RSI >= 70
    overbought = event_frame(prev, ohlc(103.0, 106.5, 102.5, 106.0))
    events = signals.detect_events(overbought)
    assert [e.kind for e in events] == ["gap_up", "breakout_up"]
    feat_call = signals.SymbolFeatures("SPY", 106.0, rsi=75.0, atr=1.0, macd_hist=0.5, events=events, bar_age_seconds=0.0)
    assert signals.entry_events(feat_call) == ()  # blocked for entry by RSI gate

    # PUT blocked at RSI <= 30
    oversold = event_frame(prev, ohlc(97.0, 97.5, 93.5, 94.0))
    events = signals.detect_events(oversold)
    assert [e.kind for e in events] == ["gap_down", "breakout_down"]
    feat_put = signals.SymbolFeatures("SPY", 97.0, rsi=25.0, atr=1.0, macd_hist=-0.5, events=events, bar_age_seconds=0.0)
    assert signals.entry_events(feat_put) == ()  # blocked for entry by RSI gate

    # Normal RSI allows events
    normal = event_frame(prev, ohlc(103.0, 106.5, 102.5, 106.0))
    events = signals.detect_events(normal)
    feat_norm = signals.SymbolFeatures("SPY", 106.0, rsi=55.0, atr=1.0, macd_hist=0.5, events=events, bar_age_seconds=0.0)
    assert [e.kind for e in signals.entry_events(feat_norm)] == ["gap_up", "breakout_up"]


# --- build_signal + gates ---

def test_build_signal_full_history():
    df = signals.add_indicators(frame(quiet_rows(60)))
    features = signals.build_signal("SPY", df, 100.0, NOW, BAR_SECONDS)
    assert features.rsi is not None and features.atr is not None and features.macd_hist is not None
    assert features.bar_age_seconds == 0.0
    assert features.events == ()  # quiet series fires nothing


def test_build_signal_short_history_has_no_indicators():
    import settings

    df = signals.add_indicators(frame(quiet_rows(settings.MIN_BARS - 1)))
    features = signals.build_signal("SPY", df, 100.0, NOW, BAR_SECONDS)
    assert features.rsi is None and features.events == ()


def make_features(**overrides):
    base = dict(symbol="SPY", mid=100.0, rsi=55.0, atr=1.0, macd_hist=0.1,
                events=(signals.Event(kind="breakout_up", direction="CALL"),),
                bar_age_seconds=10.0)
    base.update(overrides)
    return SymbolFeatures(**base)


def test_gate_order_first_fail_wins():
    good = make_features()
    assert signals.gate_block(good, False, BAR_SECONDS) == "market_closed"
    stale = make_features(bar_age_seconds=2 * BAR_SECONDS + 1, rsi=None)
    assert signals.gate_block(stale, True, BAR_SECONDS) == "stale_data"
    empty = make_features(bar_age_seconds=None)
    assert signals.gate_block(empty, True, BAR_SECONDS) == "stale_data"
    thin = make_features(macd_hist=None)
    assert signals.gate_block(thin, True, BAR_SECONDS) == "insufficient_history"
    no_quote = make_features(mid=None)
    assert signals.gate_block(no_quote, True, BAR_SECONDS) == "missing_quote"
    quiet = make_features(events=())
    assert signals.gate_block(quiet, True, BAR_SECONDS) == "no_event"
    assert signals.gate_block(good, True, BAR_SECONDS) is None


def test_staleness_scales_with_timeframe():
    features = make_features(bar_age_seconds=3000.0)
    assert signals.gate_block(features, True, 900) == "stale_data"  # 15m bars: stale
    assert signals.gate_block(features, True, 3600) is None  # 1h bars: fine


def test_build_candidates_marks_every_symbol_and_keeps_preset_blocks():
    features = {
        "SPY": make_features(),
        "QQQ": make_features(symbol="QQQ", events=()),
        "NVDA": make_features(symbol="NVDA", gate_block="data_error"),
    }
    by_symbol = {c.symbol: c for c in signals.build_candidates(features, True, BAR_SECONDS)}
    assert by_symbol["SPY"].gate_block is None
    assert by_symbol["QQQ"].gate_block == "no_event"
    assert by_symbol["NVDA"].gate_block == "data_error"  # a preset block survives


def test_entry_events_drops_exhausted_directions(monkeypatch):
    import settings

    monkeypatch.setattr(settings, "RSI_OVERBOUGHT", 70.0)
    monkeypatch.setattr(settings, "RSI_OVERSOLD", 30.0)
    call = signals.Event(kind="breakout_up", direction="CALL")
    put = signals.Event(kind="macd_cross_down", direction="PUT")
    overbought = make_features(rsi=70.0, events=(call, put))
    assert signals.entry_events(overbought) == (put,)  # CALL dropped at/above 70
    oversold = make_features(rsi=30.0, events=(call, put))
    assert signals.entry_events(oversold) == (call,)  # PUT dropped at/below 30
    midrange = make_features(rsi=55.0, events=(call, put))
    assert signals.entry_events(midrange) == (call, put)
    unknown = make_features(rsi=None, events=(call,))
    assert signals.entry_events(unknown) == (call,)  # no RSI -> no filtering


def test_build_candidates_gates_exhausted_symbol_but_exits_see_raw_events(monkeypatch):
    import settings

    monkeypatch.setattr(settings, "RSI_OVERBOUGHT", 70.0)
    monkeypatch.setattr(settings, "RSI_OVERSOLD", 30.0)
    call = signals.Event(kind="gap_up", direction="CALL")
    features = {"SPY": make_features(rsi=75.0, events=(call,))}
    (candidate,) = signals.build_candidates(features, True, BAR_SECONDS)
    assert candidate.gate_block == "rsi_exhausted"
    assert candidate.events == ()  # not offered for entry
    # the raw features are untouched: the exit path (reversal) still sees the event
    assert features["SPY"].events == (call,)
