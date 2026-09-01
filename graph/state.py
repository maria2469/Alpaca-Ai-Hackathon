"""Agent state management for multi-agent trading system."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import data_models
from data_models import SymbolFeatures


@dataclass
class MarketSnapshot:
    """Enhanced market data with IV and Greeks."""
    symbol: str
    spot: float
    bid: float
    ask: float
    timestamp: datetime
    iv: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    volume: Optional[float] = None
    unusual_activity: bool = False


@dataclass
class Opportunity:
    """Trading opportunity detected by scanner."""
    symbol: str
    confidence: float
    reason: str
    direction: str  # "CALL" or "PUT"
    features: Dict[str, Any]
    timestamp: datetime


@dataclass
class RegimeBelief:
    """Market regime classification with confidence."""
    regime: str  # "trending_up", "trending_down", "high_vol_chop", "low_vol_drift", "unknown"
    confidence: float
    volatility_level: str  # "low", "medium", "high"
    trend_strength: float
    iv_rank: Optional[float] = None


@dataclass
class AgentPerspective:
    """Generic agent perspective on trading decision."""
    agent_name: str
    action: str  # "BUY_CALL", "BUY_PUT", "HOLD"
    symbol: str
    confidence: float
    reasoning: str
    expected_value: Optional[float] = None
    risk_score: Optional[float] = None


@dataclass
class CriticAnalysis:
    """Critic agent's evaluation of conflicting perspectives."""
    consensus_action: str
    consensus_symbol: Optional[str]
    consensus_probability: float
    conflicting_agents: List[str]
    confidence_score: float
    recommendation: str


@dataclass
class RiskDecision:
    """Portfolio Risk Gate and EV Contract Optimizer decision."""
    approved: bool
    reason: str
    portfolio_risk: float
    greek_exposure: Dict[str, float]
    position_size: float
    selected_spread: Optional[data_models.SpreadQuote] = None
    expected_value: Optional[float] = None
    max_profit: Optional[float] = None
    max_loss: Optional[float] = None
    reward_risk_ratio: Optional[float] = None
    win_probability: Optional[float] = None
    fill_probability: Optional[float] = None
    slippage_bps: Optional[float] = None
    order_plan: Optional[data_models.OrderPlan] = None
    screen_rejections: Dict[str, int] = field(default_factory=dict)
    portfolio_greeks: Dict[str, float] = field(default_factory=dict)
    correlated_cluster_risk: Dict[str, float] = field(default_factory=dict)
    daily_drawdown_pct: float = 0.0
    active_concurrent_trades: int = 0
    event_risk_notes: Optional[str] = None


@dataclass
class ExecutionPlan:
    """Execution plan and fill tracking from Execution Agent."""
    symbol: str
    action: str
    contracts: List[Dict[str, Any]]
    limit_price: float
    order_type: str
    time_in_force: str
    client_order_id: str
    estimated_slippage: float
    fill_probability: float
    status: str = "planned"  # "planned", "submitted", "filled", "partially_filled", "canceled", "rejected", "hold"
    order_id: Optional[str] = None
    fill_price: Optional[float] = None
    filled_qty: int = 0
    slippage_control_mode: str = "mid_spread_peg"
    cancel_replace_count: int = 0
    execution_notes: Optional[str] = None


@dataclass
class ManagedPosition:
    """Real-time monitored spread position status."""
    spread_label: str
    underlying: str
    expiration: date
    option_type: str
    qty: int
    entry_debit: Optional[float]
    current_mark: Optional[float]
    unrealized_pnl: Optional[float]
    pnl_pct: Optional[float]
    dte: int
    greeks: Dict[str, float] = field(default_factory=dict)
    exit_triggered: bool = False
    exit_reason: Optional[str] = None  # "stop", "take_profit", "expiry", "reversal", "momentum_breakdown"
    exit_plan: Optional[data_models.OrderPlan] = None
    thesis_notes: Optional[str] = None


@dataclass
class PositionManagerReport:
    """Report from Real-Time Position Manager Agent."""
    total_positions: int
    total_open_risk: float
    total_unrealized_pnl: float
    managed_positions: List[ManagedPosition] = field(default_factory=list)
    exits_triggered: List[ManagedPosition] = field(default_factory=list)


@dataclass
class TradeMemoryRecord:
    """Full lifecycle trade trace: prediction -> decision -> execution -> outcome."""
    cycle_id: str
    timestamp: datetime
    symbol: str
    action: str  # "BUY_CALL", "BUY_PUT", "HOLD"
    regime: str
    prediction_confidence: float
    consensus_probability: float
    specialist_votes: Dict[str, str] = field(default_factory=dict)
    spread_details: Optional[Dict[str, Any]] = None
    expected_value: Optional[float] = None
    position_size: float = 0.0
    portfolio_risk: float = 0.0
    order_id: Optional[str] = None
    execution_status: str = "hold"
    fill_price: Optional[float] = None
    slippage_bps: Optional[float] = None
    outcome_status: Optional[str] = None  # "open", "take_profit", "stop_loss", "expiry", "reversal"
    realized_pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    post_mortem_lessons: Optional[str] = None


@dataclass
class AnalyticsReport:
    """Aggregated signal performance, calibration, and agent mistake analytics."""
    total_trades_analyzed: int
    win_rate: float
    profit_factor: float
    average_pnl: float
    max_drawdown_pct: float
    regime_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    signal_win_rates: Dict[str, float] = field(default_factory=dict)
    agent_mistake_summary: List[str] = field(default_factory=list)
    recent_lessons: List[str] = field(default_factory=list)


@dataclass
class DebateRound:
    """A round of dialectical cross-examination between Bull, Bear, and Options specialists."""
    round_number: int
    theses: Dict[str, str] = field(default_factory=dict)       # agent_name -> initial proposal
    rebuttals: Dict[str, str] = field(default_factory=dict)    # agent_name -> counter-argument / rebuttal
    concessions: List[str] = field(default_factory=list)       # concession points acknowledged
    critic_notes: str = ""                                     # Critic's synthesis for this round


@dataclass
class AgentState:
    """Shared state passed between agents in the LangGraph."""
    
    # Market State
    market_data: Dict[str, MarketSnapshot] = field(default_factory=dict)
    opportunities: List[Opportunity] = field(default_factory=list)
    scanner_confidence: float = 0.0
    
    # Pre-computed technical indicators (RSI/ATR/MACD/Events) from MarketScanner.
    # Downstream agents read these directly — zero duplicate API calls.
    symbol_features: Dict[str, SymbolFeatures] = field(default_factory=dict)
    
    # Regime Analysis
    regime_belief: Optional[RegimeBelief] = None
    
    # Agent Perspectives & Multi-Turn Deliberation
    agent_perspectives: Dict[str, AgentPerspective] = field(default_factory=dict)
    debate_history: List[DebateRound] = field(default_factory=list)
    working_scratchpad: Dict[str, str] = field(default_factory=dict)
    
    # Critic Evaluation
    critic_analysis: Optional[CriticAnalysis] = None
    
    # EV & Contract Optimizer / Risk Assessment
    risk_decision: Optional[RiskDecision] = None
    selected_spread: Optional[data_models.SpreadQuote] = None
    order_plan: Optional[data_models.OrderPlan] = None
    negotiation_count: int = 0  # Counter for risk-decision negotiation loops (max 1 retry)
    
    # Execution
    execution_plan: Optional[ExecutionPlan] = None
    execution_receipts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Real-Time Position Management
    position_report: Optional[PositionManagerReport] = None
    active_positions: List[ManagedPosition] = field(default_factory=list)
    
    # Shared Alpaca account state — fetched ONCE per cycle in Market Scanner,
    # then read by Risk Gate and Position Manager with zero duplicate API calls.
    account_state: Optional[data_models.AccountState] = None
    use_llm: bool = False

    # Trade Memory & Analytics (Step 7)
    trade_memory_record: Optional[TradeMemoryRecord] = None
    analytics_report: Optional[AnalyticsReport] = None
    
    # Performance tracking
    execution_times: Dict[str, float] = field(default_factory=dict)
    bottlenecks: List[str] = field(default_factory=list)
    
    # Metadata
    cycle_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    dry_run: bool = True
    
    def add_perspective(self, perspective: AgentPerspective) -> None:
        """Add an agent's perspective to the state."""
        self.agent_perspectives[perspective.agent_name] = perspective
    
    def get_consensus_action(self) -> Optional[str]:
        """Get the consensus action from critic analysis."""
        if self.critic_analysis:
            return self.critic_analysis.consensus_action
        return None
    
    def has_bottlenecks(self) -> bool:
        """Check if there are performance bottlenecks."""
        return len(self.bottlenecks) > 0
    
    def add_bottleneck(self, bottleneck: str) -> None:
        """Add a performance bottleneck."""
        self.bottlenecks.append(bottleneck)
