"""Tests for Multi-Agent Live Paper Trading System and CLI commands."""

from __future__ import annotations

import json
import time
from datetime import datetime, date, timedelta
from pathlib import Path
import pytest
from typer.testing import CliRunner

import broker
from data_models import (
    SymbolFeatures,
    LegQuote,
    SpreadQuote,
    OpenSpread,
    AccountState,
    LegPosition,
    OrderPlan,
    LegPlan,
)
from graph.state import (
    AgentState,
    MarketSnapshot,
    CriticAnalysis,
    RiskDecision,
    ExecutionPlan,
    ManagedPosition,
    PositionManagerReport,
)
from agents import (
    ExecutionAgent,
    PositionManagerAgent,
    TradeMemoryAgent,
)
import multi_agent_cli
from tests.fakes import (
    FakeOptionDataClient,
    FakeStockDataClient,
    FakeTradingClient,
    fake_clock,
    fake_contract,
    fake_position,
    fake_snapshot,
    breakout_bars,
)


NOW = datetime(2026, 9, 2, 15, 0)
TODAY = NOW.date()
EXP = TODAY + timedelta(days=14)
LONG_OCC = "SPY260916C00650000"
SHORT_OCC = "SPY260916C00655000"


@pytest.fixture(autouse=True)
def silent_sounds(monkeypatch):
    """Keep test runs silent."""
    import sounds
    monkeypatch.setattr(sounds, "play_order_sound", lambda: None)
    monkeypatch.setattr(sounds, "play_fill_sound", lambda: None)


@pytest.fixture
def fake_order_plan():
    return OrderPlan(
        kind="enter",
        underlying="SPY",
        qty=1,
        limit_price=2.00,
        legs=(
            LegPlan(symbol=LONG_OCC, ratio_qty=1, side="buy", intent="buy_to_open"),
            LegPlan(symbol=SHORT_OCC, ratio_qty=1, side="sell", intent="sell_to_open"),
        ),
        client_order_id="test-entry-001",
    )


@pytest.fixture
def fake_spread_quote():
    long_q = LegQuote(LONG_OCC, 650.0, 3.90, 4.10, 0.50, 1000, NOW)
    short_q = LegQuote(SHORT_OCC, 655.0, 1.90, 2.10, 0.35, 1000, NOW)
    return SpreadQuote(
        underlying="SPY",
        direction="CALL",
        expiration=EXP,
        long=long_q,
        short=short_q,
        net_debit=2.00,
        width=5.0,
        skew=0.01,
    )


def test_execution_agent_dry_run(fake_order_plan, fake_spread_quote):
    """In dry-run mode, ExecutionAgent plans but never submits live orders."""
    agent = ExecutionAgent()
    state = AgentState(cycle_id="test-dry-run", timestamp=NOW, dry_run=True)
    state.critic_analysis = CriticAnalysis(
        consensus_action="BUY_CALL",
        consensus_symbol="SPY",
        consensus_probability=0.90,
        conflicting_agents=[],
        confidence_score=0.85,
        recommendation="High conviction CALL",
    )
    state.risk_decision = RiskDecision(
        approved=True,
        reason="Within 4-tier risk budget",
        portfolio_risk=200.0,
        greek_exposure={"delta": 15.0},
        position_size=1.0,
        order_plan=fake_order_plan,
        selected_spread=fake_spread_quote,
        slippage_bps=20.0,
        fill_probability=0.90,
    )
    state.selected_spread = fake_spread_quote
    state.order_plan = fake_order_plan

    result = agent.execute(state)
    assert result.execution_plan is not None
    assert result.execution_plan.status == "planned"
    assert len(result.execution_receipts) == 1
    assert result.execution_receipts[0]["dry_run"] is True
    assert result.execution_receipts[0]["submitted"] is False


def test_execution_agent_live_paper_submission(monkeypatch, fake_order_plan, fake_spread_quote):
    """In armed mode (dry_run=False), ExecutionAgent submits MLEG paper order to broker."""
    trading = FakeTradingClient()
    agent = ExecutionAgent()
    monkeypatch.setattr(agent, "_get_clients", lambda: (trading, None))

    state = AgentState(cycle_id="test-live", timestamp=NOW, dry_run=False)
    state.critic_analysis = CriticAnalysis(
        consensus_action="BUY_CALL",
        consensus_symbol="SPY",
        consensus_probability=0.95,
        conflicting_agents=[],
        confidence_score=0.90,
        recommendation="Live paper trade",
    )
    state.risk_decision = RiskDecision(
        approved=True,
        reason="Approved",
        portfolio_risk=200.0,
        greek_exposure={},
        position_size=1.0,
        order_plan=fake_order_plan,
        selected_spread=fake_spread_quote,
    )
    state.selected_spread = fake_spread_quote
    state.order_plan = fake_order_plan

    result = agent.execute(state)
    assert len(trading.submitted) == 1
    assert result.execution_plan.status in ("accepted", "submitted")
    assert result.execution_plan.order_id == "order-1"
    assert len(result.execution_receipts) == 1
    assert result.execution_receipts[0]["submitted"] is True


def test_position_manager_executes_exit_orders(monkeypatch, tmp_path):
    """PositionManagerAgent triggers exit on stop-loss and submits live closing MLEG order."""
    positions = [
        fake_position(LONG_OCC, 1, 6.0, side="long"),
        fake_position(SHORT_OCC, 1, 4.0, side="short"),  # Entry debit 2.00, stop at 1.00
    ]
    # Mark at 0.90 -> triggers stop exit
    marks = {
        LONG_OCC: fake_snapshot(1.4, 1.6),
        SHORT_OCC: fake_snapshot(0.5, 0.7),
    }
    trading = FakeTradingClient(positions=positions)
    options = FakeOptionDataClient(marks)

    agent = PositionManagerAgent()
    monkeypatch.setattr(agent, "_get_clients", lambda: (trading, options))

    state = AgentState(cycle_id="test-exit", timestamp=NOW, dry_run=False)
    result = agent.execute(state)

    assert result.position_report is not None
    assert len(result.position_report.exits_triggered) == 1
    exit_pos = result.position_report.exits_triggered[0]
    assert exit_pos.exit_reason == "stop"
    assert len(trading.submitted) == 1
    assert len(result.execution_receipts) == 1
    assert result.execution_receipts[0]["kind"] == "exit"
    assert result.execution_receipts[0]["submitted"] is True


def test_trade_memory_records_cycles_journal(tmp_path, monkeypatch):
    """TradeMemoryAgent accurately serializes AgentState to cycles.jsonl without errors."""
    journal_path = tmp_path / "cycles.jsonl"
    import agents.trade_memory as tm_module
    monkeypatch.setattr(tm_module, "CYCLES_JOURNAL_PATH", journal_path)

    agent = TradeMemoryAgent(memory_path=tmp_path / "trade_memory.jsonl")
    state = AgentState(cycle_id="test-journal", timestamp=NOW, dry_run=True)
    state.critic_analysis = CriticAnalysis(
        consensus_action="HOLD",
        consensus_symbol=None,
        consensus_probability=1.0,
        conflicting_agents=[],
        confidence_score=0.70,
        recommendation="Hold position",
    )
    result = agent.execute(state)
    assert journal_path.exists()
    lines = journal_path.read_text().strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["cycle_id"] == "test-journal"
    assert record["dry_run"] is True
    assert record["action"] == "hold"


def test_multi_agent_cli_status(monkeypatch, tmp_path):
    """multi_agent_cli status command prints latency and trade memory report."""
    runner = CliRunner()
    result = runner.invoke(multi_agent_cli.app, ["status"])
    assert result.exit_code == 0
    assert "Multi-Agent System Status" in result.output
    assert "Trade Memory & Calibration Analytics" in result.output


def test_multi_agent_cli_benchmark(monkeypatch):
    """multi_agent_cli benchmark runs specified number of cycles."""
    runner = CliRunner()
    result = runner.invoke(multi_agent_cli.app, ["benchmark", "-n", "2"])
    assert result.exit_code == 0
    assert "Benchmark Summary" in result.output
    assert "Total cycles: 2" in result.output
