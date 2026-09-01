"""Multi-agent trading system with performance optimization."""

from agents.base_agent import BaseAgent, AgentMetrics, performance_monitor
from agents.market_scanner import MarketScannerAgent
from agents.regime_agent import RegimeAgent
from agents.decision_agent import DecisionAgent
from agents.risk_gate import RiskGateAgent
from agents.execution_agent import ExecutionAgent

__all__ = [
    "BaseAgent",
    "AgentMetrics",
    "performance_monitor",
    "MarketScannerAgent",
    "RegimeAgent",
    "DecisionAgent",
    "RiskGateAgent",
    "ExecutionAgent",
]
