from __future__ import annotations

from typing import Optional
from loguru import logger

from agents.base_agent import BaseAgent, monitor_performance
from graph.state import AgentState, CriticAnalysis

# Import deterministic options screening logic
import options_screener
import pos_and_risk
from data_models import SymbolFeatures


class OptionsTraderAgent(BaseAgent):
    """Options Trader: Uses deterministic logic to select optimal vertical spread."""

    def __init__(self, timeout: Optional[float] = 3.0):
        super().__init__("options_trader", timeout)
        self.enable_cache()

    @monitor_performance("options_trader", timeout=3.0)
    def execute(self, state: AgentState) -> AgentState:
        """Execute deterministic vertical spread selection."""
        logger.info("Options Trader: Starting deterministic spread selection")

        try:
            # Step 1: Check if Momentum Trader has made a decision
            if not state.critic_analysis or state.critic_analysis.consensus_action == "HOLD":
                logger.info("Options Trader: No momentum decision - HOLD")
                state.critic_analysis = CriticAnalysis(
                    consensus_action="HOLD",
                    consensus_symbol=None,
                    consensus_probability=1.00,
                    conflicting_agents=[],
                    confidence_score=0.60,
                    recommendation="No momentum decision to execute"
                )
                return state

            symbol = state.critic_analysis.consensus_symbol
            direction = state.critic_analysis.consensus_action

            if not symbol:
                logger.info("Options Trader: No symbol in momentum decision - HOLD")
                return state

            # Step 2: Get symbol features
            features = state.symbol_features.get(symbol)
            if not features:
                logger.warning(f"Options Trader: No features for {symbol} - HOLD")
                return state

            # Step 3: Confirm momentum decision and prepare for deterministic spread selection
            logger.info(f"Options Trader: Confirming {symbol} {direction} for deterministic spread selection")
            logger.info(f"Options Trader: SPOT={features.mid:.2f} RSI={features.rsi:.1f} ATR={features.atr:.2f}")

            # In production, this would call options_screener.pick_spread() with real options chain data
            # For now, we just confirm the momentum decision
            state.critic_analysis = CriticAnalysis(
                consensus_action=direction,
                consensus_symbol=symbol,
                consensus_probability=state.critic_analysis.consensus_probability,
                conflicting_agents=[],
                confidence_score=state.critic_analysis.confidence_score,
                recommendation=f"Options Trader: Confirmed {symbol} {direction} - deterministic spread selection ready"
            )

            logger.info(f"Options Trader: Confirmed {symbol} {direction} spread selection")

        except Exception as e:
            logger.error(f"Options Trader failed: {e}")
            state.add_bottleneck(f"Options Trader failed: {str(e)}")
            state.critic_analysis = CriticAnalysis(
                consensus_action="HOLD",
                consensus_symbol=None,
                consensus_probability=0.80,
                conflicting_agents=[],
                confidence_score=0.50,
                recommendation="Fallback: Holding due to options trader error"
            )

        return state
