"""Entry signal, data side: technical indicators + event detection + entry gates.

Pure functions over an OHLCV DataFrame (from market_data.fetch_ohlcv). A symbol
becomes an entry candidate only when at least one event fired on the latest
completed bar (approved 2026-08-31):

  - gap:      |bar open - previous bar close| > 2 x ATR
  - breakout: |bar close - bar open|          > 2 x ATR
  - MACD histogram crossing zero (either direction), only when the new
    histogram magnitude is at least MACD_MIN_HIST_ATR x ATR (approved
    2026-09-02: bare sign flips whipsawed every position on 2026-09-01)

ATR is read as of the PREVIOUS bar so the event bar cannot inflate its own
trigger. Missing data yields None / no event, never a substituted value.

Entry candidacy additionally drops exhausted-direction events (RSI >=
RSI_OVERBOUGHT blocks CALL events, RSI <= RSI_OVERSOLD blocks PUT events);
exits keep seeing the unfiltered events via SymbolFeatures.events.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

import settings
from data_models import Event, SymbolFeatures


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Append rsi, atr, macd, macd_signal, macd_hist columns (input untouched)."""
    out = df.copy()
    close = out["close"]

    delta = close.diff()
    gain = delta.clip(lower=0.0).ewm(alpha=1 / settings.RSI_PERIOD, adjust=False).mean()
    loss = (-delta.clip(upper=0.0)).ewm(alpha=1 / settings.RSI_PERIOD, adjust=False).mean()
    out["rsi"] = 100.0 - 100.0 / (1.0 + gain / loss)
    out.loc[(loss == 0.0) & (gain > 0.0), "rsi"] = 100.0
    out.loc[(loss == 0.0) & (gain == 0.0), "rsi"] = 50.0  # flat run is neutral, not overbought

    prev_close = close.shift(1)
    true_range = pd.concat(
        [out["high"] - out["low"], (out["high"] - prev_close).abs(), (out["low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    out["atr"] = true_range.ewm(alpha=1 / settings.ATR_PERIOD, adjust=False).mean()

    macd = close.ewm(span=settings.MACD_FAST, adjust=False).mean() - close.ewm(span=settings.MACD_SLOW, adjust=False).mean()
    out["macd"] = macd
    out["macd_signal"] = macd.ewm(span=settings.MACD_SIGNAL, adjust=False).mean()
    out["macd_hist"] = out["macd"] - out["macd_signal"]

    # Advisory trend anchors (journaled + shown to the decider; never a gate).
    out["ema_fast"] = close.ewm(span=settings.TREND_EMA_FAST, adjust=False).mean()
    out["ema_slow"] = close.ewm(span=settings.TREND_EMA_SLOW, adjust=False).mean()
    return out


def detect_events(df: pd.DataFrame) -> tuple[Event, ...]:
    """Events on the latest completed bar of an add_indicators() frame."""
    if len(df) < 2 or "atr" not in df.columns:
        return ()
    last, prev = df.iloc[-1], df.iloc[-2]
    atr = prev["atr"]  # previous bar's ATR: the event bar can't move its own goalposts
    if pd.isna(atr) or atr <= 0:
        return ()

    events: list[Event] = []
    gap = last["open"] - prev["close"]
    if abs(gap) > settings.ATR_EVENT_MULT * atr:
        events.append(Event(kind="gap_up" if gap > 0 else "gap_down",
                            direction="CALL" if gap > 0 else "PUT"))
    body = last["close"] - last["open"]
    if abs(body) > settings.ATR_EVENT_MULT * atr:
        events.append(Event(kind="breakout_up" if body > 0 else "breakout_down",
                            direction="CALL" if body > 0 else "PUT"))
    hist, prev_hist = last["macd_hist"], prev["macd_hist"]
    if (
        not pd.isna(hist)
        and not pd.isna(prev_hist)
        and abs(hist) >= settings.MACD_MIN_HIST_ATR * atr  # sub-threshold flips are chop, not momentum
    ):
        if prev_hist <= 0 < hist:
            events.append(Event(kind="macd_cross_up", direction="CALL"))
        elif prev_hist >= 0 > hist:
            events.append(Event(kind="macd_cross_down", direction="PUT"))
    return tuple(events)


def build_signal(
    symbol: str,
    df: pd.DataFrame,
    mid: float | None,
    now: datetime,
    bar_seconds: int,
) -> SymbolFeatures:
    """Indicator readings + events for one symbol from its completed-bars frame."""
    enough = len(df) >= settings.MIN_BARS
    bar_age = None
    if len(df) > 0:
        bar_age = now.timestamp() - (df.index[-1].timestamp() + bar_seconds)

    def _last(column: str) -> float | None:
        if not enough or column not in df.columns:
            return None
        value = df[column].iloc[-1]
        return None if pd.isna(value) else float(value)

    def _dist(ema_column: str) -> float | None:
        close, ema = _last("close"), _last(ema_column)
        return None if close is None or ema is None else close - ema

    return SymbolFeatures(
        symbol=symbol,
        mid=mid,
        rsi=_last("rsi"),
        atr=_last("atr"),
        macd_hist=_last("macd_hist"),
        events=detect_events(df) if enough else (),
        bar_age_seconds=bar_age,
        ema_fast_dist=_dist("ema_fast"),
        ema_slow_dist=_dist("ema_slow"),
    )


def gate_block(features: SymbolFeatures, market_is_open: bool, bar_seconds: int) -> str | None:
    """First failing entry gate, or None when the symbol is a valid candidate.

    Gates block entries only; exits are never gated here. There is deliberately
    no near-open or near-close block: trading both windows is wanted. A symbol
    with no fired event is not a candidate.
    """
    if not market_is_open:
        return "market_closed"
    if features.bar_age_seconds is None or features.bar_age_seconds > settings.STALE_BAR_FACTOR * bar_seconds:
        return "stale_data"
    if features.rsi is None or features.atr is None or features.macd_hist is None:
        return "insufficient_history"
    if features.mid is None or features.mid <= 0:
        return "missing_quote"
    if not features.events:
        return "no_event"
    return None


def entry_events(features: SymbolFeatures) -> tuple[Event, ...]:
    """Events eligible for a NEW entry: exhausted-direction events are dropped.

    RSI >= RSI_OVERBOUGHT drops CALL events (chasing a spent up-move);
    RSI <= RSI_OVERSOLD drops PUT events. Exits are driven by the unfiltered
    SymbolFeatures.events upstream — a capitulation gap must still close a
    held position, so this filter applies only to entry candidacy.
    """
    if features.rsi is None:
        return features.events
    return tuple(
        event
        for event in features.events
        if not (event.direction == "CALL" and features.rsi >= settings.RSI_OVERBOUGHT)
        and not (event.direction == "PUT" and features.rsi <= settings.RSI_OVERSOLD)
    )


def build_candidates(
    features_by_symbol: dict[str, SymbolFeatures],
    market_is_open: bool,
    bar_seconds: int,
) -> list[SymbolFeatures]:
    """Gate every symbol; return all of them with gate_block filled in.

    Candidates carry the RSI-filtered entry events; a symbol whose events all
    fall to the exhaustion filter gates as rsi_exhausted.
    """
    out = []
    for symbol in sorted(features_by_symbol):
        features = features_by_symbol[symbol]
        tradeable_events = entry_events(features)
        block = features.gate_block or gate_block(features, market_is_open, bar_seconds)
        if block is None and features.events and not tradeable_events:
            block = "rsi_exhausted"
        out.append(
            SymbolFeatures(
                symbol=features.symbol,
                mid=features.mid,
                rsi=features.rsi,
                atr=features.atr,
                macd_hist=features.macd_hist,
                events=tradeable_events,
                bar_age_seconds=features.bar_age_seconds,
                gate_block=block,
                ema_fast_dist=features.ema_fast_dist,
                ema_slow_dist=features.ema_slow_dist,
            )
        )
    return out
