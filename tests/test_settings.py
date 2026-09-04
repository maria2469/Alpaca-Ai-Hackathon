import copy
from pathlib import Path

import pytest
import yaml

import settings

SHIPPED = Path(settings.SETTINGS_PATH)


def shipped_raw() -> dict:
    return yaml.safe_load(SHIPPED.read_text(encoding="utf-8"))


def test_shipped_settings_file_validates():
    values = settings.load_settings()
    assert values["SYMBOLS"][0] == "SPY"
    assert values["BAR_SECONDS"] == 300  # shipped file trades 5m bars
    assert 0 < values["STOP_FRACTION"] < 1


def test_every_constant_is_exposed_on_the_module():
    for name in settings.load_settings():
        assert hasattr(settings, name), f"settings.{name} missing"


def broken(mutate) -> dict:
    raw = copy.deepcopy(shipped_raw())
    mutate(raw)
    return raw


@pytest.mark.parametrize(
    ("mutate", "expect_in_message"),
    [
        (lambda r: r.pop("symbols"), "symbols"),
        (lambda r: r["exits"].pop("stop_fraction"), "stop_fraction"),
        (lambda r: r["exits"].update(stop_fractoin=0.5), "stop_fractoin"),  # typo'd key
        (lambda r: r.update(unexpected_section=1), "unexpected_section"),
        (lambda r: r["exits"].update(stop_fraction=5), "exits.stop_fraction"),
        (lambda r: r["exits"].update(take_profit_mult=0.5), "exits.take_profit_mult"),
        (lambda r: r["risk"].update(total_fraction="lots"), "risk.total_fraction"),
        (lambda r: r["risk"].update(per_entry_fraction=0.03), "risk.per_entry_fraction"),  # > per_underlying
        (lambda r: r["risk"].update(per_underlying_fraction=0.2), "risk.per_underlying_fraction"),  # > total
        (lambda r: r["signals"].update(macd_fast=30), "signals.macd_fast"),  # >= slow
        (lambda r: r["signals"].update(rsi_period=0), "signals.rsi_period"),
        (lambda r: r["screener"].update(strike_band_pct=0.9), "screener.strike_band_pct"),
        (lambda r: r["screener"].update(min_width_pct=0), "screener.min_width_pct"),
        (lambda r: r["screener"].update(min_width_pct=0.06), "screener.min_width_pct"),  # > max
        (lambda r: r["screener"].update(max_width_pct=0.9), "screener.max_width_pct"),
        (lambda r: r["screener"].update(otm_only=1), "screener.otm_only"),  # must be a bool
        (lambda r: r["screener"].update(expiries_to_screen=0), "screener.expiries_to_screen"),
        (lambda r: r.update(bar_timeframe="fifteen"), "bar_timeframe"),
        (lambda r: r.update(symbols=[]), "symbols"),
        (lambda r: r.update(symbols="SPY"), "symbols"),  # string, not a list
        (lambda r: r["llm"].update(primary_model=""), "llm.primary_model"),
        (lambda r: r["exits"].update(reversal_exit=1), "exits.reversal_exit"),  # must be a bool
        (lambda r: r["risk"].update(allow_stacking=1), "risk.allow_stacking"),  # must be a bool
        (lambda r: r["signals"].update(macd_min_hist_atr=1.5), "signals.macd_min_hist_atr"),
        (lambda r: r["signals"].update(rsi_overbought=40), "signals.rsi_overbought"),  # < 50
        (lambda r: r["signals"].update(rsi_oversold=60), "signals.rsi_oversold"),  # > 50
        (lambda r: r["signals"].update(rsi_overbought=50, rsi_oversold=50), "signals.rsi_oversold"),  # >= overbought
        (lambda r: r["screener"].update(min_debit_frac=0), "screener.min_debit_frac"),
        (lambda r: r["screener"].update(max_debit_frac=1), "screener.max_debit_frac"),
        (lambda r: r["screener"].update(min_debit_frac=0.5, max_debit_frac=0.4), "screener.min_debit_frac"),  # > max
        (lambda r: r["signals"].update(trend_ema_fast=0), "signals.trend_ema_fast"),
        (lambda r: r["signals"].update(trend_ema_fast=50, trend_ema_slow=50), "signals.trend_ema_fast"),  # >= slow
    ],
)
def test_validate_rejects_and_names_the_key(mutate, expect_in_message):
    with pytest.raises(settings.SettingsError) as excinfo:
        settings.validate(broken(mutate))
    assert expect_in_message in str(excinfo.value)


def test_load_settings_reports_missing_file_and_bad_yaml(tmp_path):
    with pytest.raises(settings.SettingsError):
        settings.load_settings(tmp_path / "nope.yaml")
    bad = tmp_path / "bad.yaml"
    bad.write_text("symbols: [unclosed", encoding="utf-8")
    with pytest.raises(settings.SettingsError):
        settings.load_settings(bad)


def test_load_settings_from_custom_file(tmp_path):
    raw = shipped_raw()
    raw["symbols"] = ["iwm", "spy", "IWM"]  # normalizes: upper + dedupe, order kept
    custom = tmp_path / "custom.yaml"
    custom.write_text(yaml.safe_dump(raw), encoding="utf-8")
    values = settings.load_settings(custom)
    assert values["SYMBOLS"] == ("IWM", "SPY")


def test_parse_timeframe():
    assert settings.parse_timeframe("15m") == (15, "m", 900)
    assert settings.parse_timeframe("1h") == (1, "h", 3600)
    assert settings.parse_timeframe("1d") == (1, "d", 86400)
    assert settings.parse_timeframe("1w") == (1, "w", 604800)
    for bad in ("", "m", "15x", "0m", "1.5h", "fifteen"):
        with pytest.raises(settings.SettingsError):
            settings.parse_timeframe(bad)
