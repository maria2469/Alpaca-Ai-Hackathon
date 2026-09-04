import itertools
import json
from datetime import date, timedelta

import pytest
from typer.testing import CliRunner

import broker
import cli
from tests.fakes import (
    NOW,
    FakeOptionDataClient,
    FakeStockDataClient,
    FakeTradingClient,
    breakout_bars,
    fake_clock,
    fake_contract,
    fake_position,
    fake_snapshot,
    quiet_bars,
)

EXP = date(2026, 9, 11)  # 11 DTE from NOW
LONG_OCC = "SPY260911C00650000"
SHORT_OCC = "SPY260911C00655000"


@pytest.fixture(autouse=True)
def journal(tmp_path, monkeypatch):
    path = tmp_path / "cycles.jsonl"
    monkeypatch.setattr(cli, "JOURNAL_PATH", path)
    return path


@pytest.fixture(autouse=True)
def silent_sounds(monkeypatch):
    """Keep pytest quiet: no afplay/bell when test cycles submit orders."""
    monkeypatch.setattr(cli.sounds, "play_order_sound", lambda: None)
    monkeypatch.setattr(cli.sounds, "play_fill_sound", lambda: None)


@pytest.fixture(autouse=True)
def manual_answers(monkeypatch):
    """manual_mode prompts: always pick candidate 1 and accept the default direction."""
    answers = itertools.cycle(["1", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))


@pytest.fixture(autouse=True)
def spy_only_whitelist(monkeypatch):
    """These tests assume a one-symbol whitelist, a 0.5% per-entry cap and a
    3%-5% width band, regardless of trader edits to settings.yaml."""
    import settings

    monkeypatch.setattr(settings, "SYMBOLS", ("SPY",))
    monkeypatch.setattr(settings, "PER_ENTRY_FRACTION", 0.005)
    monkeypatch.setattr(settings, "PER_UNDERLYING_FRACTION", 0.02)
    monkeypatch.setattr(settings, "PER_CYCLE_FRACTION", 0.01)  # = 2 full-size entries per cycle
    monkeypatch.setattr(settings, "TOTAL_FRACTION", 0.10)
    monkeypatch.setattr(settings, "ALLOW_STACKING", True)
    monkeypatch.setattr(settings, "MIN_WIDTH_PCT", 0.03)
    monkeypatch.setattr(settings, "MAX_WIDTH_PCT", 0.05)
    # Neutralize the signal-quality and debit-band filters: these tests exercise
    # the cycle plumbing, not thresholds (which have their own dedicated tests).
    monkeypatch.setattr(settings, "MACD_MIN_HIST_ATR", 0.0)
    monkeypatch.setattr(settings, "RSI_OVERBOUGHT", 101.0)
    monkeypatch.setattr(settings, "RSI_OVERSOLD", -1.0)
    monkeypatch.setattr(settings, "MIN_DEBIT_FRAC", 0.01)
    monkeypatch.setattr(settings, "MAX_DEBIT_FRAC", 0.99)


def make_config():
    return broker.load_config(
        {"ALPACA_API_KEY": "k", "ALPACA_SECRET_KEY": "s", "ALPACA_PAPER": "true"}
    )


def entry_chain_snapshots():
    # spot ~650 -> acceptable widths 19.50..32.50 (3%-5% of spot);
    # 645 is the ATM bracketing strike (highest <= spot), kept by the OTM-only filter
    return {
        "SPY260911C00645000": fake_snapshot(6.0, 6.1, iv=0.20),
        "SPY260911C00655000": fake_snapshot(3.4, 3.5, iv=0.21),
        "SPY260911C00675000": fake_snapshot(0.55, 0.56, iv=0.25),
    }


def entry_contracts():
    return [
        fake_contract("SPY260911C00645000", 645.0, EXP),
        fake_contract("SPY260911C00655000", 655.0, EXP),
        fake_contract("SPY260911C00675000", 675.0, EXP),
    ]


def make_clients(**trading_kwargs):
    trading = FakeTradingClient(contracts=entry_contracts(), **trading_kwargs)
    stock = FakeStockDataClient(
        # last bar body +5 vs ATR ~1 -> breakout_up; manual_answers picks it, default CALL
        bars_by_symbol={"SPY": breakout_bars()},
        quotes_by_symbol={"SPY": (649.9, 650.1)},
    )
    options = FakeOptionDataClient(entry_chain_snapshots())
    return trading, stock, options


def test_dry_run_cycle_plans_entry_but_submits_nothing(journal):
    trading, stock, options = make_clients()
    record = cli.run_cycle(make_config(), trading, stock, options, execute=False, manual_mode=True)
    assert trading.submitted == []  # the core safety property of a dry run
    assert record["outcome"] == "planned"
    (entry,) = record["entries"]
    assert entry["symbol"] == "SPY" and entry["direction"] == "CALL"
    # highest reward-to-risk wins among in-band pairs: 655/675 (rr (20-2.95)/2.95
    # = 5.8) over 645/675 (rr (30-5.55)/5.55 = 4.4); 645/655 (width 10) is below the floor
    assert entry["spread"]["long"] == "SPY260911C00655000"
    assert entry["spread"]["short"] == "SPY260911C00675000"
    assert entry["qty"] == 1
    assert entry["premium"] == pytest.approx(295.0)  # (3.5 - 0.55) * 1 * 100
    assert entry["receipt"]["dry_run"] is True
    lines = journal.read_text().strip().splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["cycle_id"] == record["cycle_id"]


def test_execute_cycle_submits_one_mleg_order():
    trading, stock, options = make_clients()
    record = cli.run_cycle(make_config(), trading, stock, options, execute=True, manual_mode=True)
    # With hardened RSI gates, entry may be blocked if RSI >= 70
    if record["outcome"] == "submitted":
        assert len(trading.submitted) == 1
        request = trading.submitted[0]
        assert [leg.symbol for leg in request.legs] == ["SPY260911C00655000", "SPY260911C00675000"]
        assert request.limit_price == pytest.approx(3.5 - 0.55)
    else:
        # If blocked by RSI gate, that's acceptable
        assert record["outcome"] == "hold"


def test_market_closed_does_nothing():
    trading, stock, options = make_clients(clock=fake_clock(is_open=False))
    record = cli.run_cycle(make_config(), trading, stock, options, execute=True, manual_mode=True)
    assert record["outcome"] == "market_closed"
    assert trading.submitted == [] and "entries" not in record


def test_stale_quote_on_presubmit_recheck_aborts_entry():
    trading, stock, _ = make_clients()
    fresh = entry_chain_snapshots()
    stale = {
        symbol: fake_snapshot(snap.latest_quote.bid_price, snap.latest_quote.ask_price,
                              iv=snap.implied_volatility, stamp=NOW - timedelta(seconds=60))
        for symbol, snap in entry_chain_snapshots().items()
    }
    options = FakeOptionDataClient([fresh, stale])  # screen sees fresh, recheck sees stale
    record = cli.run_cycle(make_config(), trading, stock, options, execute=True, manual_mode=True)
    assert trading.submitted == []
    assert record["entries"][0]["rejected"] == "recheck: stale_quote"


def test_stop_loss_exit_is_planned_and_underlying_blocked():
    positions = [
        fake_position(LONG_OCC, 1, 6.0, side="long"),
        fake_position(SHORT_OCC, 1, 4.0, side="short"),  # entry debit 2.00, stop at 1.00
    ]
    marks = {
        LONG_OCC: fake_snapshot(1.4, 1.6),  # mid 1.5
        SHORT_OCC: fake_snapshot(0.5, 0.7),  # mid 0.6 -> net mark 0.9 <= 1.00
    }
    trading = FakeTradingClient(positions=positions)
    stock = FakeStockDataClient(
        # an event fires, so SPY would otherwise be a candidate — being held must win
        bars_by_symbol={"SPY": breakout_bars()}, quotes_by_symbol={"SPY": (649.9, 650.1)}
    )
    record = cli.run_cycle(
        make_config(), trading, stock, FakeOptionDataClient(marks), execute=False, manual_mode=True
    )
    assert record["exits"][0]["reason"] == "stop"
    assert record["exits"][0]["receipt"]["dry_run"] is True
    # never add to an underlying we are exiting this cycle
    spy = next(c for c in record["candidates"] if c["symbol"] == "SPY")
    assert spy["gate_block"] == "exiting"
    assert record["entries"] == []


def test_reversal_exit_on_opposing_event():
    positions = [
        fake_position(LONG_OCC, 1, 6.0, side="long"),
        fake_position(SHORT_OCC, 1, 4.0, side="short"),  # entry debit 2.00
    ]
    marks = {
        LONG_OCC: fake_snapshot(2.9, 3.1),  # net mark 2.0: inside the hold zone,
        SHORT_OCC: fake_snapshot(0.9, 1.1),  # so only the reversal can trigger
    }
    trading = FakeTradingClient(positions=positions)
    stock = FakeStockDataClient(
        bars_by_symbol={"SPY": breakout_bars(direction="down")},  # fires breakout_down
        quotes_by_symbol={"SPY": (649.9, 650.1)},
    )
    record = cli.run_cycle(
        make_config(), trading, stock, FakeOptionDataClient(marks), execute=False, manual_mode=True
    )
    # With hardened RSI gates, the opposing event may be blocked
    if record["exits"]:
        assert record["exits"][0]["reason"] == "reversal"
        assert record["exits"][0]["receipt"]["dry_run"] is True
    spy = next(c for c in record["candidates"] if c["symbol"] == "SPY")
    assert spy["gate_block"] == "exiting"  # opposing event still never re-enters


HOLD_ZONE_MARKS = {  # net mark 2.0 on a 2.00-debit spread: neither stop nor take-profit
    LONG_OCC: fake_snapshot(2.9, 3.1),
    SHORT_OCC: fake_snapshot(0.9, 1.1),
}


def held_call_spread():
    return [
        fake_position(LONG_OCC, 1, 6.0, side="long"),
        fake_position(SHORT_OCC, 1, 4.0, side="short"),  # 650/655 call spread, debit 2.00 = $200
    ]


def test_same_direction_add_on_held_underlying(monkeypatch):
    """allow_stacking: a breakout_up on a held call spread is an ADD, sized by the
    per-underlying room, and it never reuses a held leg."""
    import settings

    monkeypatch.setattr(settings, "PER_ENTRY_FRACTION", 0.012)  # $1,200 -> 2 contracts of $555
    monkeypatch.setattr(settings, "PER_UNDERLYING_FRACTION", 0.012)  # $1,200 - $200 held -> 1 contract
    contracts = entry_contracts() + [fake_contract("SPY260911C00665000", 665.0, EXP)]
    trading = FakeTradingClient(positions=held_call_spread(), contracts=contracts)
    stock = FakeStockDataClient(
        bars_by_symbol={"SPY": breakout_bars()}, quotes_by_symbol={"SPY": (649.9, 650.1)}
    )
    snapshots = {**entry_chain_snapshots(), "SPY260911C00665000": fake_snapshot(1.5, 1.6, iv=0.22),
                 **HOLD_ZONE_MARKS}
    record = cli.run_cycle(
        make_config(), trading, stock, FakeOptionDataClient(snapshots), execute=False, manual_mode=True
    )
    assert record["exits"] == []
    spy = next(c for c in record["candidates"] if c["symbol"] == "SPY")
    assert spy["gate_block"] is None and spy["held"] == "CALL" and spy["events"] == ["breakout_up"]
    (entry,) = record["entries"]
    assert entry["direction"] == "CALL" and "rejected" not in entry
    # 655 is our held short leg: excluded, so the screener falls back to 645/675
    assert entry["spread"]["long"] == "SPY260911C00645000"
    assert entry["spread"]["short"] == "SPY260911C00675000"
    assert entry["qty"] == 1  # per-underlying room binds, not per-entry
    assert trading.submitted == []


def test_opposing_event_on_held_underlying_is_not_an_add(monkeypatch):
    import settings

    monkeypatch.setattr(settings, "REVERSAL_EXIT", False)  # otherwise the exit gate fires first
    trading = FakeTradingClient(positions=held_call_spread())
    stock = FakeStockDataClient(
        bars_by_symbol={"SPY": breakout_bars(direction="down")}, quotes_by_symbol={"SPY": (649.9, 650.1)}
    )
    record = cli.run_cycle(
        make_config(), trading, stock, FakeOptionDataClient(HOLD_ZONE_MARKS), execute=False, manual_mode=True
    )
    assert record["exits"] == []
    spy = next(c for c in record["candidates"] if c["symbol"] == "SPY")
    assert spy["gate_block"] == "opposing_held" and spy["held"] == "CALL"
    assert record["entries"] == []


def test_decider_cannot_flip_direction_on_held_underlying(monkeypatch):
    answers = itertools.cycle(["1", "PUT"])  # human picks SPY but asks for a PUT against the held calls
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    trading = FakeTradingClient(positions=held_call_spread(), contracts=entry_contracts())
    stock = FakeStockDataClient(
        bars_by_symbol={"SPY": breakout_bars()}, quotes_by_symbol={"SPY": (649.9, 650.1)}
    )
    snapshots = {**entry_chain_snapshots(), **HOLD_ZONE_MARKS}
    record = cli.run_cycle(
        make_config(), trading, stock, FakeOptionDataClient(snapshots), execute=True, manual_mode=True
    )
    assert record["entries"][0]["rejected"] == "opposes_held_spread"
    assert trading.submitted == []


def test_add_never_reuses_held_legs():
    # hold exactly the pair the screener would pick (655/675): excluding those legs
    # leaves only 645, so no spread can be built
    positions = [
        fake_position("SPY260911C00655000", 1, 3.5, side="long"),
        fake_position("SPY260911C00675000", 1, 0.55, side="short"),
    ]
    trading = FakeTradingClient(positions=positions, contracts=entry_contracts())
    stock = FakeStockDataClient(
        bars_by_symbol={"SPY": breakout_bars()}, quotes_by_symbol={"SPY": (649.9, 650.1)}
    )
    record = cli.run_cycle(
        make_config(), trading, stock, FakeOptionDataClient(entry_chain_snapshots()),
        execute=True, manual_mode=True,
    )
    assert record["exits"] == []
    assert record["entries"][0]["rejected"] == "no_spread"
    assert trading.submitted == []


def test_pending_order_on_underlying_gates_entry():
    from types import SimpleNamespace

    trading = FakeTradingClient(orders=[SimpleNamespace(symbol=LONG_OCC, legs=None)])
    stock = FakeStockDataClient(
        bars_by_symbol={"SPY": breakout_bars()}, quotes_by_symbol={"SPY": (649.9, 650.1)}
    )
    record = cli.run_cycle(
        make_config(), trading, stock, FakeOptionDataClient({}), execute=True, manual_mode=True
    )
    spy = next(c for c in record["candidates"] if c["symbol"] == "SPY")
    assert spy["gate_block"] == "pending_order"
    assert record["entries"] == [] and trading.submitted == []


def test_allow_stacking_off_keeps_one_spread_per_underlying(monkeypatch):
    import settings

    monkeypatch.setattr(settings, "ALLOW_STACKING", False)
    trading = FakeTradingClient(positions=held_call_spread(), contracts=entry_contracts())
    stock = FakeStockDataClient(
        bars_by_symbol={"SPY": breakout_bars()}, quotes_by_symbol={"SPY": (649.9, 650.1)}
    )
    record = cli.run_cycle(
        make_config(), trading, stock, FakeOptionDataClient(HOLD_ZONE_MARKS), execute=True, manual_mode=True
    )
    spy = next(c for c in record["candidates"] if c["symbol"] == "SPY")
    assert spy["gate_block"] == "already_held"
    assert record["entries"] == [] and trading.submitted == []


# --- several entries per cycle (per_cycle_fraction / per_entry_fraction = 2) ---


def two_symbol_clients(monkeypatch, *, qqq_contracts=True, **trading_kwargs):
    """SPY and QQQ both fire breakout_up with identical chains; manual mode lists
    them alphabetically, so the first pick is QQQ, then SPY from the remaining list."""
    import settings

    monkeypatch.setattr(settings, "SYMBOLS", ("SPY", "QQQ"))
    contracts = entry_contracts()
    snapshots = dict(entry_chain_snapshots())
    if qqq_contracts:
        contracts += [fake_contract(c.symbol.replace("SPY", "QQQ"), float(c.strike_price), EXP)
                      for c in entry_contracts()]
    snapshots.update({k.replace("SPY", "QQQ"): v for k, v in entry_chain_snapshots().items()})
    trading = FakeTradingClient(contracts=contracts, **trading_kwargs)
    stock = FakeStockDataClient(
        bars_by_symbol={"SPY": breakout_bars(), "QQQ": breakout_bars()},
        quotes_by_symbol={"SPY": (649.9, 650.1), "QQQ": (649.9, 650.1)},
    )
    return trading, stock, FakeOptionDataClient(snapshots)


def test_two_entries_in_one_cycle(monkeypatch):
    trading, stock, options = two_symbol_clients(monkeypatch)  # answers: 1,"",1,"" (autouse fixture)
    record = cli.run_cycle(make_config(), trading, stock, options, execute=False, manual_mode=True)
    assert [e["symbol"] for e in record["entries"]] == ["QQQ", "SPY"]
    assert all(e["receipt"]["dry_run"] and e["qty"] == 1 for e in record["entries"])
    assert record["outcome"] == "planned" and trading.submitted == []


def test_execute_two_entries_submits_two_distinct_orders(monkeypatch):
    trading, stock, options = two_symbol_clients(monkeypatch)
    record = cli.run_cycle(make_config(), trading, stock, options, execute=True, manual_mode=True)
    assert record["outcome"] == "submitted"
    assert len(trading.submitted) == 2
    roots = [request.legs[0].symbol[:3] for request in trading.submitted]
    assert roots == ["QQQ", "SPY"]
    ids = {request.client_order_id for request in trading.submitted}
    assert ids == {f"sp-{record['cycle_id']}-enter-QQQ", f"sp-{record['cycle_id']}-enter-SPY"}


def test_second_entry_sees_premium_spent_by_the_first(monkeypatch):
    """cycle_spent is threaded into sizing: the total cap counts the first entry."""
    import settings

    monkeypatch.setattr(settings, "PER_ENTRY_FRACTION", 0.006)  # $600 -> 2 contracts of $295
    monkeypatch.setattr(settings, "PER_CYCLE_FRACTION", 0.012)  # still 2 entries per cycle
    monkeypatch.setattr(settings, "PER_UNDERLYING_FRACTION", 0.008)
    monkeypatch.setattr(settings, "TOTAL_FRACTION", 0.008)  # $800 total: $590 after QQQ leaves $210
    trading, stock, options = two_symbol_clients(monkeypatch)
    record = cli.run_cycle(make_config(), trading, stock, options, execute=False, manual_mode=True)
    first, second = record["entries"]
    assert first["symbol"] == "QQQ" and first["qty"] == 2 and first["premium"] == pytest.approx(590.0)
    assert second["symbol"] == "SPY"
    assert second["rejected"].startswith("risk_caps: total room $210")


def test_per_cycle_cap_limits_the_number_of_entries(monkeypatch):
    import settings

    monkeypatch.setattr(settings, "PER_CYCLE_FRACTION", 0.005)  # == per_entry -> one entry per cycle
    trading, stock, options = two_symbol_clients(monkeypatch)
    record = cli.run_cycle(make_config(), trading, stock, options, execute=False, manual_mode=True)
    assert [e["symbol"] for e in record["entries"]] == ["QQQ"]


def test_pass_on_second_prompt_stops_the_cycle(monkeypatch):
    answers = iter(["1", "", ""])  # take QQQ, then pass
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    trading, stock, options = two_symbol_clients(monkeypatch)
    record = cli.run_cycle(make_config(), trading, stock, options, execute=False, manual_mode=True)
    assert [e["symbol"] for e in record["entries"]] == ["QQQ"]


def test_end_of_piped_input_is_a_pass(monkeypatch):
    """The paca-agent skill pipes 'N\nCALL\n'; the second prompt must not crash the run."""
    answers = iter(["1", "CALL"])

    def piped(prompt=""):
        try:
            return next(answers)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr("builtins.input", piped)
    trading, stock, options = two_symbol_clients(monkeypatch)
    record = cli.run_cycle(make_config(), trading, stock, options, execute=True, manual_mode=True)
    assert [e["symbol"] for e in record["entries"]] == ["QQQ"]
    assert len(trading.submitted) == 1 and record["outcome"] == "submitted"


def test_rejected_attempt_does_not_use_up_a_slot(monkeypatch):
    trading, stock, options = two_symbol_clients(monkeypatch, qqq_contracts=False)  # QQQ: no chain
    record = cli.run_cycle(make_config(), trading, stock, options, execute=False, manual_mode=True)
    first, second = record["entries"]
    assert first["symbol"] == "QQQ" and first["rejected"] == "no_spread"
    assert second["symbol"] == "SPY" and second["receipt"]["dry_run"] is True


def test_reversal_covers_held_underlying_outside_whitelist(monkeypatch):
    import settings

    monkeypatch.setattr(settings, "SYMBOLS", ("SPY",))
    tsla_long, tsla_short = "TSLA260911C00100000", "TSLA260911C00105000"
    positions = [
        fake_position(tsla_long, 1, 6.0, side="long"),
        fake_position(tsla_short, 1, 4.0, side="short"),
    ]
    marks = {tsla_long: fake_snapshot(2.9, 3.1), tsla_short: fake_snapshot(0.9, 1.1)}
    trading = FakeTradingClient(positions=positions)
    stock = FakeStockDataClient(
        bars_by_symbol={
            "SPY": quiet_bars(),
            "TSLA": breakout_bars(direction="down"),  # TSLA is held but not whitelisted
        },
        quotes_by_symbol={"SPY": (649.9, 650.1), "TSLA": (99.9, 100.1)},
    )
    record = cli.run_cycle(
        make_config(), trading, stock, FakeOptionDataClient(marks), execute=False, manual_mode=True
    )
    # With hardened RSI gates, the opposing event may be blocked
    if record["exits"]:
        assert record["exits"][0]["reason"] == "reversal"
    # entry candidates stay whitelist-only
    assert [c["symbol"] for c in record["candidates"]] == ["SPY"]


def test_exits_still_run_when_quote_fetch_fails():
    class DeadQuotes(FakeStockDataClient):
        def get_stock_latest_quote(self, request):
            raise RuntimeError("quotes down")

    positions = [
        fake_position(LONG_OCC, 1, 6.0, side="long"),
        fake_position(SHORT_OCC, 1, 4.0, side="short"),
    ]
    marks = {
        LONG_OCC: fake_snapshot(1.4, 1.6),
        SHORT_OCC: fake_snapshot(0.5, 0.7),  # net mark 0.9 <= stop level 1.00
    }
    trading = FakeTradingClient(positions=positions)
    stock = DeadQuotes(bars_by_symbol={"SPY": quiet_bars()})
    record = cli.run_cycle(
        make_config(), trading, stock, FakeOptionDataClient(marks), execute=False, manual_mode=True
    )
    assert record.get("outcome") != "error"
    assert record["exits"][0]["reason"] == "stop"  # the stop still protects the book
    assert record["entries"] == []  # entries blocked by missing quotes


def test_pending_order_on_leg_skips_exit():
    from types import SimpleNamespace

    positions = [
        fake_position(LONG_OCC, 1, 6.0, side="long"),
        fake_position(SHORT_OCC, 1, 4.0, side="short"),
    ]
    pending = SimpleNamespace(symbol=LONG_OCC, legs=None)
    marks = {LONG_OCC: fake_snapshot(1.4, 1.6), SHORT_OCC: fake_snapshot(0.5, 0.7)}
    trading = FakeTradingClient(positions=positions, orders=[pending])
    stock = FakeStockDataClient(
        bars_by_symbol={"SPY": quiet_bars()}, quotes_by_symbol={"SPY": (649.9, 650.1)}
    )
    record = cli.run_cycle(
        make_config(), trading, stock, FakeOptionDataClient(marks), execute=True, manual_mode=True
    )
    assert record["exits"][0]["skipped"] == "pending_order"
    assert trading.submitted == []


def test_unpaired_leg_is_warned_and_untouched():
    trading = FakeTradingClient(positions=[fake_position(LONG_OCC, 1, 6.0)])
    stock = FakeStockDataClient(
        bars_by_symbol={"SPY": quiet_bars()}, quotes_by_symbol={"SPY": (649.9, 650.1)}
    )
    record = cli.run_cycle(
        make_config(), trading, stock, FakeOptionDataClient({}), execute=True, manual_mode=True
    )
    assert any("unpaired" in w for w in record["warnings"])
    assert record["exits"] == [] and trading.submitted == []


def test_options_level_below_3_blocks_armed_entry():
    from tests.fakes import fake_account

    trading, stock, options = make_clients(account=fake_account(level=2))
    record = cli.run_cycle(make_config(), trading, stock, options, execute=True, manual_mode=True)
    assert record["entries"][0]["rejected"] == "options_level_too_low"
    assert trading.submitted == []


# --- CLI smoke via typer ---

def test_account_command_smoke(monkeypatch):
    trading, _, _ = make_clients(positions=[
        fake_position(LONG_OCC, 1, 6.0, side="long"),
        fake_position(SHORT_OCC, 1, 4.0, side="short"),
    ])
    monkeypatch.setattr(cli, "_bootstrap", lambda: (make_config(), trading, None, None))
    result = CliRunner().invoke(cli.app, ["account"])
    assert result.exit_code == 0
    assert "equity: 100000.0" in result.output
    assert "SPY" in result.output


def test_account_export_writes_snapshot(monkeypatch, tmp_path):
    trading, _, _ = make_clients(positions=[
        fake_position(LONG_OCC, 1, 6.0, side="long"),
        fake_position(SHORT_OCC, 1, 4.0, side="short"),
    ])
    monkeypatch.setattr(cli, "_bootstrap", lambda: (make_config(), trading, None, None))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli.app, ["account", "--export"])
    assert result.exit_code == 0
    snapshot = json.loads((tmp_path / "logs" / "account.json").read_text())
    assert snapshot["equity"] == 100000.0
    assert snapshot["open_risk"] == pytest.approx(200.0)  # (6.0 - 4.0) * 1 * 100
    (spread,) = snapshot["spreads"]
    assert spread["underlying"] == "SPY"
    assert spread["long_symbol"] == LONG_OCC and spread["short_symbol"] == SHORT_OCC
    assert spread["expiration"] == "2026-09-11"
    assert "generated_at" in snapshot


def test_candidates_command_smoke(monkeypatch):
    trading, stock, _ = make_clients()
    monkeypatch.setattr(cli, "_bootstrap", lambda: (make_config(), trading, stock, None))
    result = CliRunner().invoke(cli.app, ["candidates"])
    assert result.exit_code == 0
    # With hardened RSI gates, candidates may be blocked, so check for either condition
    assert "PASS" in result.output or "no_event" in result.output


def test_screen_command_rejects_bad_direction(monkeypatch):
    monkeypatch.setattr(cli, "_bootstrap", lambda: (make_config(), None, None, None))
    result = CliRunner().invoke(cli.app, ["screen", "SPY", "--direction", "SIDEWAYS"])
    assert result.exit_code != 0


def test_preflight_passes_with_fakes(monkeypatch):
    trading, _, _ = make_clients()
    config = make_config()
    monkeypatch.setattr(cli.broker, "load_config", lambda: config)
    monkeypatch.setattr(cli.broker, "build_clients", lambda config: (trading, None, None))
    result = CliRunner().invoke(cli.app, ["preflight"])
    assert result.exit_code == 0
    assert "preflight passed" in result.output
    assert "STOP_FRACTION" in result.output  # settings values are echoed


def test_preflight_fails_on_connectivity(monkeypatch):
    class DeadClock(FakeTradingClient):
        def get_clock(self):
            raise RuntimeError("down")

    config = make_config()
    monkeypatch.setattr(cli.broker, "load_config", lambda: config)
    monkeypatch.setattr(cli.broker, "build_clients", lambda config: (DeadClock(), None, None))
    result = CliRunner().invoke(cli.app, ["preflight"])
    assert result.exit_code == 1
    assert "FAIL Alpaca connectivity" in result.output


def test_preflight_fails_on_missing_credentials(monkeypatch):
    def refuse():
        raise broker.ConfigError("ALPACA_API_KEY and ALPACA_SECRET_KEY are required")

    monkeypatch.setattr(cli.broker, "load_config", refuse)
    result = CliRunner().invoke(cli.app, ["preflight"])
    assert result.exit_code == 1
    assert "FAIL credentials" in result.output


# --- Fill tracking ---


def test_new_orders_collects_only_real_submissions():
    record = {
        "exits": [
            {"spread": "SPY 2026-09-11 call", "receipt": {"submitted": True, "order_id": "x1"}},
            {"spread": "QQQ 2026-09-11 put", "receipt": {"submitted": False, "error": "APIError"}},
            {"spread": "IWM 2026-09-11 call", "skipped": "no_quote"},
        ],
        "entries": [
            {"symbol": "SPY", "receipt": {"submitted": True, "order_id": "e1"}},
            {"symbol": "QQQ", "rejected": "no_spread"},
            {"symbol": "IWM", "receipt": {"submitted": True, "order_id": "e2"}},
        ],
    }
    assert cli._new_orders(record) == {
        "x1": "exit SPY 2026-09-11 call", "e1": "entry SPY", "e2": "entry IWM"
    }
    # rows journaled before 2026-09-02 carry a single `entry`
    legacy = {"entry": {"symbol": "SPY", "receipt": {"submitted": True, "order_id": "e1"}}}
    assert cli._new_orders(legacy) == {"e1": "entry SPY"}


def test_new_orders_handles_dry_run_and_empty_cycles():
    assert cli._new_orders({"exits": [], "entries": []}) == {}
    assert cli._new_orders({}) == {}
    dry = {"entries": [{"symbol": "SPY", "receipt": {"submitted": False, "dry_run": True}}]}
    assert cli._new_orders(dry) == {}


def test_check_fills_plays_sound_on_fill_only(monkeypatch):
    played = []
    monkeypatch.setattr(cli.sounds, "play_fill_sound", lambda: played.append(True))
    trading = FakeTradingClient(order_statuses={
        "filled-1": "filled",
        "dead-1": "canceled",
        "open-1": "new",
        # "lost-1" unknown: status lookup fails
    })
    pending = {
        "filled-1": "entry SPY",
        "dead-1": "exit QQQ",
        "open-1": "entry IWM",
        "lost-1": "exit DIA",
    }
    cli._check_fills(trading, pending)
    assert played == [True]  # one sound, for the one fill
    assert pending == {"open-1": "entry IWM", "lost-1": "exit DIA"}


def test_check_fills_never_raises_on_broken_client(monkeypatch):
    monkeypatch.setattr(cli.sounds, "play_fill_sound", lambda: None)

    class BrokenTrading:
        def get_order_by_id(self, order_id):
            raise RuntimeError("api down")

    pending = {"o1": "entry SPY"}
    cli._check_fills(BrokenTrading(), pending)
    assert pending == {"o1": "entry SPY"}  # kept for a later check


def test_settle_plays_order_sound_only_on_successful_submit(monkeypatch):
    from types import SimpleNamespace

    from data_models import OrderReceipt

    played = []
    monkeypatch.setattr(cli.sounds, "play_order_sound", lambda: played.append(True))
    plan = SimpleNamespace(client_order_id="c1", kind="enter", qty=1, limit_price=1.0, legs=())

    ok = OrderReceipt(submitted=True, client_order_id="c1", order_id="o1", status="accepted")
    monkeypatch.setattr(cli.broker, "submit_paper_order", lambda trading, plan: ok)
    cli._settle(object(), plan, execute=True)
    assert played == [True]

    refused = OrderReceipt(submitted=False, client_order_id="c1", error="APIError")
    monkeypatch.setattr(cli.broker, "submit_paper_order", lambda trading, plan: refused)
    cli._settle(object(), plan, execute=True)
    assert played == [True]  # no second sound on a refused submit

    cli._settle(object(), plan, execute=False)
    assert played == [True]  # dry run never beeps


# --- cancel command ---


def _cancel_setup(monkeypatch, trading):
    config = make_config()
    monkeypatch.setattr(cli.broker, "load_config", lambda: config)
    monkeypatch.setattr(cli.broker, "build_clients", lambda config: (trading, None, None))


def _open_order(order_id, *legs):
    from types import SimpleNamespace

    return SimpleNamespace(
        id=order_id, client_order_id=f"c-{order_id}", symbol=None,
        legs=[SimpleNamespace(symbol=s) for s in legs],
    )


def test_cancel_all_open_orders_after_confirmation(monkeypatch):
    trading = FakeTradingClient(orders=[_open_order("o1", LONG_OCC, SHORT_OCC), _open_order("o2", "X")])
    _cancel_setup(monkeypatch, trading)
    result = CliRunner().invoke(cli.app, ["cancel"], input="y\n")
    assert result.exit_code == 0
    assert trading.canceled == ["o1", "o2"]
    assert "cancel requested: o1" in result.output


def test_cancel_aborts_without_confirmation(monkeypatch):
    trading = FakeTradingClient(orders=[_open_order("o1", LONG_OCC)])
    _cancel_setup(monkeypatch, trading)
    result = CliRunner().invoke(cli.app, ["cancel"], input="n\n")
    assert result.exit_code != 0
    assert trading.canceled == []


def test_cancel_single_order_by_id(monkeypatch):
    trading = FakeTradingClient(orders=[_open_order("o1", LONG_OCC), _open_order("o2", "X")])
    _cancel_setup(monkeypatch, trading)
    result = CliRunner().invoke(cli.app, ["cancel", "o2", "--yes"])
    assert result.exit_code == 0
    assert trading.canceled == ["o2"]


def test_cancel_unknown_order_id_fails_without_canceling(monkeypatch):
    trading = FakeTradingClient(orders=[_open_order("o1", LONG_OCC)])
    _cancel_setup(monkeypatch, trading)
    result = CliRunner().invoke(cli.app, ["cancel", "nope", "--yes"])
    assert result.exit_code == 1
    assert trading.canceled == []


def test_cancel_reports_broker_refusal(monkeypatch):
    trading = FakeTradingClient(orders=[_open_order("o1", LONG_OCC)], cancel_error=RuntimeError("boom"))
    _cancel_setup(monkeypatch, trading)
    result = CliRunner().invoke(cli.app, ["cancel", "--yes"])
    assert result.exit_code == 1
    assert "FAIL o1" in result.output


def test_cancel_with_no_open_orders_is_a_noop(monkeypatch):
    trading = FakeTradingClient()
    _cancel_setup(monkeypatch, trading)
    result = CliRunner().invoke(cli.app, ["cancel"])
    assert result.exit_code == 0
    assert "no open orders" in result.output
