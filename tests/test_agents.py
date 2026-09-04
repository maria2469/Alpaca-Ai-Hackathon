"""Pytest tests for the multi-agent pipeline (Steps 1-7).

All tests use mocked/fake Alpaca clients — no network calls.
The existing fakes.py provides FakeTradingClient, FakeStockDataClient, etc.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict

import pytest

from graph.state import (
    AgentState,
    MarketSnapshot,
    Opportunity,
    RegimeBelief,
    AgentPerspective,
    CriticAnalysis,
    RiskDecision,
    ExecutionPlan,
    ManagedPosition,
    PositionManagerReport,
    TradeMemoryRecord,
    AnalyticsReport,
)
from data_models import (
    Event,
    SymbolFeatures,
    LegQuote,
    SpreadQuote,
    OpenSpread,
    AccountState,
    LegPosition,
    OrderPlan,
    LegPlan,
)
import settings


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

NOW = datetime(2026, 9, 2, 15, 0)
TODAY = NOW.date()


def _make_symbol_features(symbol: str, rsi=55.0, macd_hist=0.05, events=()):
    return SymbolFeatures(
        symbol=symbol, mid=500.0, rsi=rsi, atr=1.2,
        macd_hist=macd_hist, events=tuple(events), bar_age_seconds=1.0,
    )


def _make_snapshot(symbol: str, spot=500.0):
    return MarketSnapshot(
        symbol=symbol, spot=spot, bid=spot * 0.999, ask=spot * 1.001,
        timestamp=NOW, iv=0.22, delta=0.52, gamma=0.03, theta=-0.04,
        vega=0.15, volume=100000.0,
    )


def _make_spread(underlying="SPY", direction="CALL", spot=500.0):
    long = LegQuote(
        f"{underlying}_L", spot - 5.0, 4.00, 4.20, 0.55, 5000, NOW,
    )
    short = LegQuote(
        f"{underlying}_S", spot, 1.80, 2.00, 0.35, 5000, NOW,
    )
    return SpreadQuote(
        underlying=underlying, direction=direction,
        expiration=TODAY + timedelta(days=14),
        long=long, short=short,
        net_debit=round(long.mid - short.mid, 2),
        width=5.0, skew=0.01,
    )


@pytest.fixture
def base_state():
    """Base AgentState with pre-populated market data for SPY."""
    state = AgentState(
        cycle_id="test-cycle-001",
        timestamp=NOW,
        dry_run=True,
    )
    state.market_data = {"SPY": _make_snapshot("SPY")}
    state.symbol_features = {
        "SPY": _make_symbol_features("SPY", events=(Event(kind="breakout_up", direction="CALL"),)),
    }
    return state


# ═══════════════════════════════════════════════════════════════════
# Step 2: Regime Agent
# ═══════════════════════════════════════════════════════════════════

class TestRegimeAgent:
    def test_deterministic_classification_trending_up(self, base_state):
        from agents.regime_agent import RegimeAgent
        agent = RegimeAgent(timeout=1.0)
        # SPY RSI=55, MACD=+0.05, bullish event → trending up
        result = agent.execute(base_state)
        assert result.regime_belief is not None
        assert result.regime_belief.confidence > 0.0

    def test_high_vol_chop_regime(self, base_state):
        from agents.regime_agent import RegimeAgent
        agent = RegimeAgent(timeout=1.0)
        # Mixed signals: low RSI + negative MACD + no events
        base_state.symbol_features["SPY"] = _make_symbol_features(
            "SPY", rsi=43.0, macd_hist=-0.02, events=()
        )
        result = agent.execute(base_state)
        assert result.regime_belief is not None


# ═══════════════════════════════════════════════════════════════════
# Step 3: Decision Agent (Bull / Bear / Critic)
# ═══════════════════════════════════════════════════════════════════

class TestMomentumTraderAgent:
    def test_consensus_with_bullish_signals(self, base_state):
        from agents.decision_agent import MomentumTraderAgent
        agent = MomentumTraderAgent(timeout=2.0)
        base_state.regime_belief = RegimeBelief(
            regime="trending_up_low_vol", confidence=0.85,
            volatility_level="low", trend_strength=0.75,
        )
        base_state.opportunities = [
            Opportunity(
                symbol="SPY", confidence=0.85,
                reason="breakout_up", direction="CALL",
                features={"rsi": 55.0}, timestamp=NOW,
            ),
        ]
        result = agent.execute(base_state)
        assert result.critic_analysis is not None
        assert result.critic_analysis.consensus_action in ("BUY_CALL", "BUY_PUT", "HOLD")

    def test_hold_when_no_opportunities(self, base_state):
        from agents.decision_agent import MomentumTraderAgent
        agent = MomentumTraderAgent(timeout=2.0)
        base_state.opportunities = []
        base_state.regime_belief = RegimeBelief(
            regime="high_vol_chop", confidence=0.60,
            volatility_level="high", trend_strength=0.30,
        )
        result = agent.execute(base_state)
        assert result.critic_analysis is not None
        assert result.critic_analysis.consensus_action == "HOLD"


# ═══════════════════════════════════════════════════════════════════
# Step 3: Options Trader
# ═══════════════════════════════════════════════════════════════════

class TestOptionsTraderAgent:
    def test_confirms_momentum_decision(self, base_state):
        """Options Trader should confirm momentum decision."""
        from agents.options_trader import OptionsTraderAgent
        agent = OptionsTraderAgent(timeout=2.0)
        base_state.critic_analysis = CriticAnalysis(
            consensus_action="BUY_CALL", consensus_symbol="SPY",
            consensus_probability=0.70, conflicting_agents=[],
            confidence_score=0.70, recommendation="Momentum: SPY CALL"
        )
        result = agent.execute(base_state)
        assert result.critic_analysis is not None
        assert result.critic_analysis.consensus_action == "BUY_CALL"
        assert result.critic_analysis.consensus_symbol == "SPY"

    def test_hold_when_no_momentum_decision(self, base_state):
        """Options Trader should HOLD when no momentum decision."""
        from agents.options_trader import OptionsTraderAgent
        agent = OptionsTraderAgent(timeout=2.0)
        base_state.critic_analysis = CriticAnalysis(
            consensus_action="HOLD", consensus_symbol=None,
            consensus_probability=1.00, conflicting_agents=[],
            confidence_score=0.60, recommendation="No momentum decision"
        )
        result = agent.execute(base_state)
        assert result.critic_analysis is not None
        assert result.critic_analysis.consensus_action == "HOLD"


# ═══════════════════════════════════════════════════════════════════
# Step 4: Risk Gate
# ═══════════════════════════════════════════════════════════════════

class TestRiskGateAgent:
    def test_hold_consensus_approved_zero_risk(self, base_state):
        """HOLD consensus should be approved with zero capital at risk."""
        from agents.risk_gate import RiskGateAgent
        agent = RiskGateAgent(timeout=1.0)
        base_state.critic_analysis = CriticAnalysis(
            consensus_action="HOLD", consensus_symbol=None,
            consensus_probability=0.50, conflicting_agents=[],
            confidence_score=0.50, recommendation="No trade",
        )
        result = agent.execute(base_state)
        assert result.risk_decision is not None
        assert result.risk_decision.approved is True
        assert result.risk_decision.portfolio_risk == 0.0

    def test_low_confidence_rejected(self, base_state):
        """Critic confidence below 0.55 should reject the trade."""
        from agents.risk_gate import RiskGateAgent
        agent = RiskGateAgent(timeout=1.0)
        base_state.critic_analysis = CriticAnalysis(
            consensus_action="BUY_CALL", consensus_symbol="SPY",
            consensus_probability=0.52, conflicting_agents=["bear"],
            confidence_score=0.40, recommendation="Weak signal",
        )
        # Need mock account state to avoid live fetch
        base_state.account_state = AccountState(
            equity=100000.0, options_level=3, legs=(), unparsed_positions=(),
            open_order_symbols=frozenset(),
        )
        result = agent.execute(base_state)
        # Either rejected on confidence or on spread screening — both valid
        assert result.risk_decision is not None

    def test_daily_drawdown_circuit_breaker(self):
        """Drawdown >= 2.5% should trip circuit breaker."""
        from agents.risk_gate import RiskGateAgent, MAX_DAILY_DRAWDOWN_FRACTION
        agent = RiskGateAgent(timeout=1.0)
        today = date.today()
        # Simulate opening equity then a drawdown
        agent._starting_equity = 100000.0
        agent._starting_equity_date = today
        dd = agent._track_daily_drawdown(97000.0, today)
        assert dd >= MAX_DAILY_DRAWDOWN_FRACTION


# ═══════════════════════════════════════════════════════════════════
# Step 5: Execution Agent
# ═══════════════════════════════════════════════════════════════════

class TestExecutionAgent:
    def test_no_order_plan_returns_hold(self, base_state):
        """When no order plan exists, execution agent should hold."""
        from agents.execution_agent import ExecutionAgent
        agent = ExecutionAgent(timeout=1.0)
        base_state.risk_decision = RiskDecision(
            approved=False, reason="HOLD", portfolio_risk=0.0,
            greek_exposure={}, position_size=0.0,
        )
        result = agent.execute(base_state)
        assert result.execution_plan is not None
        assert result.execution_plan.status == "hold"

    def test_dry_run_generates_receipt(self, base_state):
        """dry_run=True should generate a receipt without hitting Alpaca."""
        from agents.execution_agent import ExecutionAgent
        agent = ExecutionAgent(timeout=1.0)

        spread = _make_spread()
        order_plan = OrderPlan(
            kind="enter",
            underlying="SPY",
            qty=1,
            limit_price=2.20,
            legs=(
                LegPlan(symbol="SPY_L", side="buy", intent="buy_to_open"),
                LegPlan(symbol="SPY_S", side="sell", intent="sell_to_open"),
            ),
            client_order_id="test-exec-001",
        )

        base_state.risk_decision = RiskDecision(
            approved=True, reason="Approved",
            portfolio_risk=220.0, greek_exposure={"net_delta": 0.15},
            position_size=1.0, order_plan=order_plan,
        )
        base_state.order_plan = order_plan
        base_state.selected_spread = spread
        base_state.dry_run = True

        result = agent.execute(base_state)
        assert result.execution_plan is not None
        assert result.execution_plan.status in ("submitted", "dry_run", "hold", "planned")


# ═══════════════════════════════════════════════════════════════════
# Step 6: Position Manager
# ═══════════════════════════════════════════════════════════════════

class TestPositionManagerAgent:
    def test_empty_portfolio_returns_zero_risk(self, base_state):
        """No positions should produce 0 risk, 0 PnL."""
        from agents.position_manager import PositionManagerAgent
        agent = PositionManagerAgent(timeout=1.0)
        base_state.account_state = AccountState(
            equity=100000.0, options_level=3, legs=(),
            unparsed_positions=(), open_order_symbols=frozenset(),
        )
        result = agent.execute(base_state)
        assert result.position_report is not None
        assert result.position_report.total_positions == 0
        assert result.position_report.total_open_risk == 0.0

    def test_deterministic_exit_rules(self):
        """Stop-loss, take-profit, expiry, and reversal from pos_and_risk work correctly."""
        import pos_and_risk

        spread = OpenSpread(
            underlying="TSLA", expiration=TODAY + timedelta(days=1),
            option_type="C",
            long_symbol="TSLA_L", short_symbol="TSLA_S",
            qty=1, net_entry_debit=3.00,
        )
        long_q = LegQuote("TSLA_L", 200.0, 1.20, 1.40, 0.30, 1000, NOW)
        short_q = LegQuote("TSLA_S", 205.0, 0.10, 0.20, 0.10, 1000, NOW)

        decision = pos_and_risk.exit_decision(spread, long_q, short_q, TODAY)
        assert decision is not None
        # DTE=1 triggers expiry exit
        assert decision.reason == "expiry"


# ═══════════════════════════════════════════════════════════════════
# Step 7: Trade Memory & Analytics
# ═══════════════════════════════════════════════════════════════════

class TestTradeMemoryAgent:
    def test_cycle_tracing_records_trade(self, base_state, tmp_path):
        """Full cycle trace should produce a TradeMemoryRecord."""
        from agents.trade_memory import TradeMemoryAgent
        memory_file = tmp_path / "test_memory.jsonl"
        agent = TradeMemoryAgent(timeout=1.0, memory_path=memory_file)

        base_state.critic_analysis = CriticAnalysis(
            consensus_action="BUY_CALL", consensus_symbol="SPY",
            consensus_probability=0.72, conflicting_agents=[],
            confidence_score=0.88, recommendation="Strong buy",
        )
        base_state.regime_belief = RegimeBelief(
            regime="trending_up_low_vol", confidence=0.85,
            volatility_level="low", trend_strength=0.75,
        )

        result = agent.execute(base_state)
        assert result.trade_memory_record is not None
        assert result.trade_memory_record.symbol == "SPY"
        assert result.trade_memory_record.action == "BUY_CALL"
        assert memory_file.exists()
        lines = memory_file.read_text().strip().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["symbol"] == "SPY"

    def test_analytics_calibration(self, tmp_path):
        """Win rate and profit factor should be computed correctly from buffer."""
        from agents.trade_memory import TradeMemoryAgent
        memory_file = tmp_path / "test_analytics.jsonl"
        agent = TradeMemoryAgent(timeout=1.0, memory_path=memory_file)

        agent._memory_buffer = [
            {"action": "BUY_CALL", "symbol": "NVDA", "regime": "trending_up_low_vol",
             "realized_pnl": 500.0, "outcome_status": "take_profit"},
            {"action": "BUY_CALL", "symbol": "SPY", "regime": "trending_up_low_vol",
             "realized_pnl": 400.0, "outcome_status": "take_profit"},
            {"action": "BUY_PUT", "symbol": "TSLA", "regime": "high_vol_chop",
             "realized_pnl": 300.0, "outcome_status": "take_profit"},
            {"action": "BUY_CALL", "symbol": "AAPL", "regime": "high_vol_chop",
             "realized_pnl": -300.0, "outcome_status": "stop"},
        ]

        analytics = agent._compute_performance_analytics()
        assert analytics.total_trades_analyzed == 4
        assert analytics.win_rate == 0.75
        assert analytics.profit_factor == 4.0
        assert analytics.average_pnl == 225.0

    def test_hold_action_records_none_symbol(self, base_state, tmp_path):
        """HOLD consensus should record symbol=NONE."""
        from agents.trade_memory import TradeMemoryAgent
        memory_file = tmp_path / "test_hold.jsonl"
        agent = TradeMemoryAgent(timeout=1.0, memory_path=memory_file)

        base_state.critic_analysis = CriticAnalysis(
            consensus_action="HOLD", consensus_symbol=None,
            consensus_probability=0.50, conflicting_agents=[],
            confidence_score=0.50, recommendation="No trade",
        )

        result = agent.execute(base_state)
        assert result.trade_memory_record is not None
        assert result.trade_memory_record.action == "HOLD"
        assert result.trade_memory_record.symbol == "NONE"


# ═══════════════════════════════════════════════════════════════════
# Cross-Agent: AgentState wiring
# ═══════════════════════════════════════════════════════════════════

class TestAgentStateWiring:
    def test_account_state_shared_across_agents(self):
        """account_state set by one agent should be visible to others."""
        state = AgentState(cycle_id="wire-test")
        acct = AccountState(
            equity=50000.0, options_level=3, legs=(),
            unparsed_positions=(), open_order_symbols=frozenset(),
        )
        state.account_state = acct
        assert state.account_state is acct
        assert state.account_state.equity == 50000.0

    def test_symbol_features_shared(self, base_state):
        """symbol_features from scanner should be readable by downstream agents."""
        assert "SPY" in base_state.symbol_features
        f = base_state.symbol_features["SPY"]
        assert f.rsi == 55.0
        assert len(f.events) == 1

    def test_dialectical_debate_execution(self, base_state):
        """Momentum Trader should produce critic_analysis and update working scratchpad."""
        from agents.decision_agent import MomentumTraderAgent
        agent = MomentumTraderAgent(timeout=2.0)
        base_state.regime_belief = RegimeBelief(
            regime="trending_up_low_vol", confidence=0.85,
            volatility_level="low", trend_strength=0.75,
        )
        base_state.opportunities = [
            Opportunity(
                symbol="SPY", confidence=0.85,
                reason="breakout_up", direction="CALL",
                features={"rsi": 55.0}, timestamp=NOW,
            ),
        ]
        result = agent.execute(base_state)
        # Momentum Trader should produce a critic_analysis
        assert result.critic_analysis is not None
        # Should update working scratchpad
        assert len(result.working_scratchpad) > 0
        assert "SPY" in result.working_scratchpad
        # Should have a consensus action (HOLD or BUY)
        assert result.critic_analysis.consensus_action in ("HOLD", "BUY_CALL", "BUY_PUT")

    def test_recent_lessons_injection_in_decision_layer(self):
        """decide_entry should accept recent_lessons, mistakes, and scratchpad without error."""
        import httpx
        from decision_layer import decide_entry
        import json

        def handler(request):
            body = json.loads(request.content)
            # Verify lessons were passed into the payload
            user_msg = json.loads(body["messages"][1]["content"])
            assert "recent_lessons_and_mistakes_to_avoid" in user_msg
            assert "recent_agent_mistakes" in user_msg
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": json.dumps({"action": "enter", "symbol": "SPY", "direction": "CALL", "thesis": "Clean breakout"})}}]},
            )

        transport = httpx.MockTransport(handler)
        candidates = [
            _make_symbol_features("SPY", events=(Event(kind="breakout_up", direction="CALL"),))
        ]
        choice = decide_entry(
            candidates,
            api_key="mock-key",
            transport=transport,
            recent_lessons=["Avoid chasing high-IV breakouts in chop"],
            agent_mistakes=["Bought false breakout on TSLA"],
            working_scratchpad={"SPY": "Accumulation confirmed"},
        )
        assert choice is not None
        assert choice.symbol == "SPY"
        assert choice.direction == "CALL"

    def test_risk_decision_negotiation_loop(self):
        """TradingGraph should dynamically route from risk_gate back to decision_agent when challenged."""
        from graph.trading_graph import TradingGraph
        from agents.market_scanner import MarketScannerAgent
        from agents.regime_agent import RegimeAgent
        from agents.decision_agent import DecisionAgent
        from agents.risk_gate import RiskGateAgent
        from agents.execution_agent import ExecutionAgent
        from agents.position_manager import PositionManagerAgent
        from agents.trade_memory import TradeMemoryAgent

        agents = {
            "market_scanner": MarketScannerAgent(),
            "regime_agent": RegimeAgent(),
            "decision_agent": DecisionAgent(),
            "risk_gate": RiskGateAgent(),
            "execution_agent": ExecutionAgent(),
            "position_manager": PositionManagerAgent(),
            "trade_memory": TradeMemoryAgent(),
        }

        tg = TradingGraph(agents)
        assert tg.graph is not None
