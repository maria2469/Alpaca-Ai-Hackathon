"""Loads and validates settings.yaml — every trader-tunable knob in one place.

The file is validated key by key: a missing key, an unknown (typo'd) key, a
wrong type, or an out-of-range value raises SettingsError naming the exact key.
Validated values are exposed as module constants (settings.STOP_FRACTION etc.),
loaded once at import so any command fails fast on a bad file.

SDK-free on purpose: the pure modules (signals, positions, options_screener)
import this without pulling in the Alpaca SDK.
"""

from __future__ import annotations

from pathlib import Path

import yaml

SETTINGS_PATH = Path(__file__).parent / "settings.yaml"

_TIMEFRAME_SECONDS = {"m": 60, "h": 3600, "d": 86400, "w": 7 * 86400}


class SettingsError(Exception):
    pass


def parse_timeframe(raw: object) -> tuple[int, str, int]:
    """'15m' -> (15, 'm', 900). Raises SettingsError on anything unrecognized."""
    text = str(raw).strip().lower()
    if len(text) < 2 or text[-1] not in _TIMEFRAME_SECONDS or not text[:-1].isdigit():
        raise SettingsError(
            f"settings.yaml: bar_timeframe must look like 5m/15m/1h/1d/1w, got {raw!r}"
        )
    amount = int(text[:-1])
    if amount < 1:
        raise SettingsError("settings.yaml: bar_timeframe amount must be at least 1")
    return amount, text[-1], amount * _TIMEFRAME_SECONDS[text[-1]]


def _fail(path: str, message: str, value: object) -> None:
    raise SettingsError(f"settings.yaml: {path}: {message}, got {value!r}")


def _section(raw: dict, name: str, keys: set[str]) -> dict:
    section = raw.get(name)
    if not isinstance(section, dict):
        _fail(name, "must be a mapping section", section)
    unknown = set(section) - keys
    if unknown:
        _fail(name, f"unknown key(s) {sorted(unknown)} — a typo?", sorted(unknown))
    missing = keys - set(section)
    if missing:
        _fail(name, f"missing required key(s) {sorted(missing)}", None)
    return section


def _number(section: dict, path: str, key: str, lo: float, hi: float = float("inf"),
            *, lo_open: bool = False, hi_open: bool = False) -> float:
    value = section[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(f"{path}.{key}", "must be a number", value)
    below = value <= lo if lo_open else value < lo
    above = value >= hi if hi_open else value > hi
    if below or above:
        bounds = f"{'(' if lo_open else '['}{lo}, {hi}{')' if hi_open else ']'}"
        _fail(f"{path}.{key}", f"must be in {bounds}", value)
    return float(value)


def _integer(section: dict, path: str, key: str, lo: int) -> int:
    value = section[key]
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(f"{path}.{key}", "must be a whole number", value)
    if value < lo:
        _fail(f"{path}.{key}", f"must be at least {lo}", value)
    return value


def _string_list(value: object, path: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(s, str) or not s.strip() for s in value):
        _fail(path, "must be a list of symbols/strings", value)
    return tuple(dict.fromkeys(s.strip().upper() for s in value))


_TOP_KEYS = {"symbols", "bar_timeframe", "loop_interval_seconds",
             "signals", "screener", "risk", "exits", "llm"}
_SIGNAL_KEYS = {"rsi_period", "atr_period", "macd_fast", "macd_slow", "macd_signal",
                "atr_event_mult", "macd_min_atr_mult", "rsi_call_max", "rsi_put_min",
                "stale_bar_factor", "min_bars"}
_SCREENER_KEYS = {"min_dte", "max_expiry_lookahead_days", "expiries_to_screen",
                  "strike_band_pct", "otm_only", "min_width_pct", "max_width_pct",
                  "min_open_interest", "max_quote_age_seconds", "max_leg_spread_bps",
                  "min_net_debit"}
_RISK_KEYS = {"per_entry_fraction", "per_underlying_fraction", "per_cycle_fraction",
              "total_fraction"}
_EXIT_KEYS = {"stop_fraction", "take_profit_mult", "exit_dte", "reversal_exit"}
_LLM_KEYS = {"primary_model", "fallback_models"}


def validate(raw: object) -> dict[str, object]:
    """Full check of a parsed settings.yaml; returns {CONSTANT_NAME: value}."""
    if not isinstance(raw, dict):
        raise SettingsError("settings.yaml: the file must be a YAML mapping")
    unknown = set(raw) - _TOP_KEYS
    if unknown:
        _fail("top level", f"unknown key(s) {sorted(unknown)} — a typo?", sorted(unknown))
    missing = _TOP_KEYS - set(raw)
    if missing:
        _fail("top level", f"missing required key(s) {sorted(missing)}", None)

    values: dict[str, object] = {}
    values["SYMBOLS"] = _string_list(raw["symbols"], "symbols")
    if not values["SYMBOLS"]:
        _fail("symbols", "must list at least one symbol", raw["symbols"])
    _, _, bar_seconds = parse_timeframe(raw["bar_timeframe"])
    values["BAR_TIMEFRAME"] = str(raw["bar_timeframe"]).strip()
    values["BAR_SECONDS"] = bar_seconds
    values["LOOP_INTERVAL_SECONDS"] = _integer(raw, "top level", "loop_interval_seconds", 1)

    sig = _section(raw, "signals", _SIGNAL_KEYS)
    values["RSI_PERIOD"] = _integer(sig, "signals", "rsi_period", 1)
    values["ATR_PERIOD"] = _integer(sig, "signals", "atr_period", 1)
    values["MACD_FAST"] = _integer(sig, "signals", "macd_fast", 1)
    values["MACD_SLOW"] = _integer(sig, "signals", "macd_slow", 1)
    values["MACD_SIGNAL"] = _integer(sig, "signals", "macd_signal", 1)
    if values["MACD_FAST"] >= values["MACD_SLOW"]:
        _fail("signals.macd_fast", "must be smaller than macd_slow", sig["macd_fast"])
    values["ATR_EVENT_MULT"] = _number(sig, "signals", "atr_event_mult", 0, lo_open=True)
    values["MACD_MIN_ATR_MULT"] = _number(sig, "signals", "macd_min_atr_mult", 0)
    values["RSI_CALL_MAX"] = _number(sig, "signals", "rsi_call_max", 50, 100, hi_open=True)
    values["RSI_PUT_MIN"] = _number(sig, "signals", "rsi_put_min", 0, 50, hi_open=True)
    if values["RSI_PUT_MIN"] >= values["RSI_CALL_MAX"]:
        _fail("signals.rsi_put_min", "must be less than rsi_call_max", sig["rsi_put_min"])
    values["STALE_BAR_FACTOR"] = _number(sig, "signals", "stale_bar_factor", 1)
    values["MIN_BARS"] = _integer(sig, "signals", "min_bars",
                                  values["MACD_SLOW"] + values["MACD_SIGNAL"])

    scr = _section(raw, "screener", _SCREENER_KEYS)
    values["MIN_DTE"] = _integer(scr, "screener", "min_dte", 1)
    values["MAX_EXPIRY_LOOKAHEAD_DAYS"] = _integer(
        scr, "screener", "max_expiry_lookahead_days", values["MIN_DTE"] + 1)
    values["EXPIRIES_TO_SCREEN"] = _integer(scr, "screener", "expiries_to_screen", 1)
    values["STRIKE_BAND_PCT"] = _number(scr, "screener", "strike_band_pct", 0, 0.5, lo_open=True)
    if not isinstance(scr["otm_only"], bool):
        _fail("screener.otm_only", "must be true or false", scr["otm_only"])
    values["OTM_ONLY"] = scr["otm_only"]
    values["MIN_WIDTH_PCT"] = _number(scr, "screener", "min_width_pct", 0, 0.5, lo_open=True)
    values["MAX_WIDTH_PCT"] = _number(scr, "screener", "max_width_pct", 0, 0.5, lo_open=True)
    if values["MIN_WIDTH_PCT"] > values["MAX_WIDTH_PCT"]:
        _fail("screener.min_width_pct", "must not exceed max_width_pct", scr["min_width_pct"])
    values["MIN_OPEN_INTEREST"] = _integer(scr, "screener", "min_open_interest", 0)
    values["MAX_QUOTE_AGE_SECONDS"] = _number(scr, "screener", "max_quote_age_seconds", 0, lo_open=True)
    values["MAX_LEG_SPREAD_BPS"] = _number(scr, "screener", "max_leg_spread_bps", 0, lo_open=True)
    values["MIN_NET_DEBIT"] = _number(scr, "screener", "min_net_debit", 0, lo_open=True)

    risk = _section(raw, "risk", _RISK_KEYS)
    values["PER_ENTRY_FRACTION"] = _number(risk, "risk", "per_entry_fraction", 0, 1, lo_open=True)
    values["PER_UNDERLYING_FRACTION"] = _number(risk, "risk", "per_underlying_fraction", 0, 1, lo_open=True)
    values["PER_CYCLE_FRACTION"] = _number(risk, "risk", "per_cycle_fraction", 0, 1, lo_open=True)
    values["TOTAL_FRACTION"] = _number(risk, "risk", "total_fraction", 0, 1, lo_open=True)
    if values["PER_ENTRY_FRACTION"] > values["PER_UNDERLYING_FRACTION"]:
        _fail("risk.per_entry_fraction", "must not exceed per_underlying_fraction",
              risk["per_entry_fraction"])
    if values["PER_UNDERLYING_FRACTION"] > values["TOTAL_FRACTION"]:
        _fail("risk.per_underlying_fraction", "must not exceed total_fraction",
              risk["per_underlying_fraction"])

    exits = _section(raw, "exits", _EXIT_KEYS)
    values["STOP_FRACTION"] = _number(exits, "exits", "stop_fraction", 0, 1, lo_open=True, hi_open=True)
    values["TAKE_PROFIT_MULT"] = _number(exits, "exits", "take_profit_mult", 1, lo_open=True)
    values["EXIT_DTE"] = _integer(exits, "exits", "exit_dte", 0)
    if not isinstance(exits["reversal_exit"], bool):
        _fail("exits.reversal_exit", "must be true or false", exits["reversal_exit"])
    values["REVERSAL_EXIT"] = exits["reversal_exit"]

    llm = _section(raw, "llm", _LLM_KEYS)
    primary = llm["primary_model"]
    if not isinstance(primary, str) or not primary.strip():
        _fail("llm.primary_model", "must be a non-empty model name", primary)
    values["PRIMARY_MODEL"] = primary.strip()
    fallbacks = llm["fallback_models"]
    if not isinstance(fallbacks, list) or any(not isinstance(m, str) or not m.strip() for m in fallbacks):
        _fail("llm.fallback_models", "must be a list of model names (may be empty)", fallbacks)
    values["FALLBACK_MODELS"] = tuple(m.strip() for m in fallbacks)

    return values


def load_settings(path: Path = SETTINGS_PATH) -> dict[str, object]:
    """Parse + validate the YAML file; raises SettingsError with the exact problem."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise SettingsError(f"cannot read {path}: {type(error).__name__}") from None
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise SettingsError(f"{path} is not valid YAML: {error}") from None
    return validate(raw)


# Loaded once at import: a bad settings.yaml stops every command immediately.
_VALUES = load_settings()
SYMBOLS: tuple[str, ...] = _VALUES["SYMBOLS"]  # type: ignore[assignment]
BAR_TIMEFRAME: str = _VALUES["BAR_TIMEFRAME"]  # type: ignore[assignment]
BAR_SECONDS: int = _VALUES["BAR_SECONDS"]  # type: ignore[assignment]
LOOP_INTERVAL_SECONDS: int = _VALUES["LOOP_INTERVAL_SECONDS"]  # type: ignore[assignment]
RSI_PERIOD: int = _VALUES["RSI_PERIOD"]  # type: ignore[assignment]
ATR_PERIOD: int = _VALUES["ATR_PERIOD"]  # type: ignore[assignment]
MACD_FAST: int = _VALUES["MACD_FAST"]  # type: ignore[assignment]
MACD_SLOW: int = _VALUES["MACD_SLOW"]  # type: ignore[assignment]
MACD_SIGNAL: int = _VALUES["MACD_SIGNAL"]  # type: ignore[assignment]
ATR_EVENT_MULT: float = _VALUES["ATR_EVENT_MULT"]  # type: ignore[assignment]
MACD_MIN_ATR_MULT: float = _VALUES["MACD_MIN_ATR_MULT"]  # type: ignore[assignment]
RSI_CALL_MAX: float = _VALUES["RSI_CALL_MAX"]  # type: ignore[assignment]
RSI_PUT_MIN: float = _VALUES["RSI_PUT_MIN"]  # type: ignore[assignment]
STALE_BAR_FACTOR: float = _VALUES["STALE_BAR_FACTOR"]  # type: ignore[assignment]
MIN_BARS: int = _VALUES["MIN_BARS"]  # type: ignore[assignment]
MIN_DTE: int = _VALUES["MIN_DTE"]  # type: ignore[assignment]
MAX_EXPIRY_LOOKAHEAD_DAYS: int = _VALUES["MAX_EXPIRY_LOOKAHEAD_DAYS"]  # type: ignore[assignment]
EXPIRIES_TO_SCREEN: int = _VALUES["EXPIRIES_TO_SCREEN"]  # type: ignore[assignment]
STRIKE_BAND_PCT: float = _VALUES["STRIKE_BAND_PCT"]  # type: ignore[assignment]
OTM_ONLY: bool = _VALUES["OTM_ONLY"]  # type: ignore[assignment]
MIN_WIDTH_PCT: float = _VALUES["MIN_WIDTH_PCT"]  # type: ignore[assignment]
MAX_WIDTH_PCT: float = _VALUES["MAX_WIDTH_PCT"]  # type: ignore[assignment]
MIN_OPEN_INTEREST: int = _VALUES["MIN_OPEN_INTEREST"]  # type: ignore[assignment]
MAX_QUOTE_AGE_SECONDS: float = _VALUES["MAX_QUOTE_AGE_SECONDS"]  # type: ignore[assignment]
MAX_LEG_SPREAD_BPS: float = _VALUES["MAX_LEG_SPREAD_BPS"]  # type: ignore[assignment]
MIN_NET_DEBIT: float = _VALUES["MIN_NET_DEBIT"]  # type: ignore[assignment]
PER_ENTRY_FRACTION: float = _VALUES["PER_ENTRY_FRACTION"]  # type: ignore[assignment]
PER_UNDERLYING_FRACTION: float = _VALUES["PER_UNDERLYING_FRACTION"]  # type: ignore[assignment]
PER_CYCLE_FRACTION: float = _VALUES["PER_CYCLE_FRACTION"]  # type: ignore[assignment]
TOTAL_FRACTION: float = _VALUES["TOTAL_FRACTION"]  # type: ignore[assignment]
STOP_FRACTION: float = _VALUES["STOP_FRACTION"]  # type: ignore[assignment]
TAKE_PROFIT_MULT: float = _VALUES["TAKE_PROFIT_MULT"]  # type: ignore[assignment]
EXIT_DTE: int = _VALUES["EXIT_DTE"]  # type: ignore[assignment]
REVERSAL_EXIT: bool = _VALUES["REVERSAL_EXIT"]  # type: ignore[assignment]
PRIMARY_MODEL: str = _VALUES["PRIMARY_MODEL"]  # type: ignore[assignment]
FALLBACK_MODELS: tuple[str, ...] = _VALUES["FALLBACK_MODELS"]  # type: ignore[assignment]
