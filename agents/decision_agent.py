"""Decision Agent: Parallel Bull, Bear, Options Specialist Perspectives and Critic Evaluation.

100% deterministic default engine with sub-millisecond execution.
Uses pre-computed SymbolFeatures (RSI, ATR, MACD, Events), IV/Greeks from MarketSnapshot,
and RegimeBelief from RegimeAgent to form a robust consensus decision.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

from agents.base_agent import BaseAgent, monitor_performance
from graph.state import (
    AgentState, AgentPerspective, CriticAnalysis, RegimeBelief, Opportunity
)


class DecisionAgent(BaseAgent):
    """Trade Intelligence Agent: Bull/Bear/Options specialists with Critic arbitration."""

    def __init__(self, timeout: Optional[float] = 2.0):
        super().__init__("decision_agent", timeout)
        self.enable_cache()
        self._last_cycle_id: str = ""

    @monitor_performance("decision_agent", timeout=2.0)
    def execute(self, state: AgentState) -> AgentState:
        """Execute Trade Intelligence analysis with parallel perspectives and critic consensus."""
        logger.info("Decision Agent: Starting Trade Intelligence analysis")

        # Fast-path: return cached result for the same cycle
        if state.cycle_id and state.cycle_id == self._last_cycle_id and state.critic_analysis:
            logger.info(f"Decision Agent: Using cached result for cycle {state.cycle_id}")
            return state

        try:
            # Step 1: Run specialist perspective analyses (deterministic, in-memory)
            perspectives = self._parallel_perspective_analysis(state)

            # Store perspectives in state
            for perspective in perspectives:
                state.add_perspective(perspective)

            # Step 2: Critic evaluation (deterministic arbitration)
            critic_analysis = self._critic_evaluation(state, perspectives)
            state.critic_analysis = critic_analysis
            self._last_cycle_id = state.cycle_id

            logger.info(
                f"Decision Agent: Consensus {critic_analysis.consensus_action} "
                f"on {critic_analysis.consensus_symbol or 'NONE'} "
                f"(probability: {critic_analysis.consensus_probability:.2f}, conf: {critic_analysis.confidence_score:.2f})"
            )

        except Exception as e:
            logger.error(f"Decision Agent failed: {e}")
            state.add_bottleneck(f"Decision Agent failed: {str(e)}")
            state.critic_analysis = self._fallback_decision(state)

        return state

    # ------------------------------------------------------------------
    # Parallel Perspective Generation
    # ------------------------------------------------------------------

    def _parallel_perspective_analysis(self, state: AgentState) -> List[AgentPerspective]:
        """Generate Bull, Bear, and Options specialist perspectives."""
        perspectives = [
            self._bull_perspective(state),
            self._bear_perspective(state),
            self._options_perspective(state),
        ]
        logger.info(f"Decision Agent: Generated {len(perspectives)} specialist perspectives")
        return perspectives

    def _bull_perspective(self, state: AgentState) -> AgentPerspective:
        """Bullish Specialist: Evaluates upward momentum, breakout/gap events, and positive MACD."""
        logger.info("Decision Agent: Evaluating Bull perspective")

        bullish_opps = [o for o in state.opportunities if o.direction == "CALL"]

        if not bullish_opps:
            # Check symbol features directly for emerging bullish setups
            for sym, feat in state.symbol_features.items():
                if feat.rsi and feat.rsi > 52 and feat.macd_hist and feat.macd_hist > 0:
                    snapshot = state.market_data.get(sym)
                    if snapshot and (snapshot.delta or 0.5) > 0.50:
                        bullish_opps.append(
                            Opportunity(
                                symbol=sym,
                                confidence=0.60,
                                reason=f"Emerging bullish momentum | RSI {feat.rsi:.1f} | MACD {feat.macd_hist:.3f}",
                                direction="CALL",
                                features={"rsi": feat.rsi, "macd_hist": feat.macd_hist},
                                timestamp=datetime.utcnow(),
                            )
                        )

        if not bullish_opps:
            return AgentPerspective(
                agent_name="bull_agent",
                action="HOLD",
                symbol="",
                confidence=0.50,
                reasoning="No bullish setups or call opportunities detected",
                expected_value=0.0,
                risk_score=0.5,
            )

        best_opp = max(bullish_opps, key=lambda o: o.confidence)

        # Regime compatibility modifier
        regime_mod = 0.0
        regime = state.regime_belief.regime if state.regime_belief else "unknown"
        if regime == "trending_up":
            regime_mod = 0.15
        elif regime == "low_vol_drift":
            regime_mod = 0.05
        elif regime == "high_vol_chop":
            regime_mod = -0.10
        elif regime == "trending_down":
            regime_mod = -0.25

        raw_conf = best_opp.confidence + regime_mod
        final_conf = max(min(round(raw_conf, 2), 0.95), 0.20)

        # If confidence drops below threshold, recommendation is HOLD
        if final_conf < 0.55:
            return AgentPerspective(
                agent_name="bull_agent",
                action="HOLD",
                symbol=best_opp.symbol,
                confidence=final_conf,
                reasoning=f"Bullish setup on {best_opp.symbol} weakened by {regime} regime",
                expected_value=0.0,
                risk_score=round(1.0 - final_conf, 2),
            )

        return AgentPerspective(
            agent_name="bull_agent",
            action="BUY_CALL",
            symbol=best_opp.symbol,
            confidence=final_conf,
            reasoning=f"Bullish setup: {best_opp.reason} (Regime: {regime})",
            expected_value=round(final_conf * 0.85, 2),
            risk_score=round(1.0 - final_conf, 2),
        )

    def _bear_perspective(self, state: AgentState) -> AgentPerspective:
        """Bearish Specialist: Evaluates downward breakdown, negative events, and MACD cross down."""
        logger.info("Decision Agent: Evaluating Bear perspective")

        bearish_opps = [o for o in state.opportunities if o.direction == "PUT"]

        if not bearish_opps:
            for sym, feat in state.symbol_features.items():
                if feat.rsi and feat.rsi < 48 and feat.macd_hist and feat.macd_hist < 0:
                    snapshot = state.market_data.get(sym)
                    if snapshot and (snapshot.delta or 0.5) < 0.50:
                        bearish_opps.append(
                            Opportunity(
                                symbol=sym,
                                confidence=0.60,
                                reason=f"Emerging bearish breakdown | RSI {feat.rsi:.1f} | MACD {feat.macd_hist:.3f}",
                                direction="PUT",
                                features={"rsi": feat.rsi, "macd_hist": feat.macd_hist},
                                timestamp=datetime.utcnow(),
                            )
                        )

        if not bearish_opps:
            return AgentPerspective(
                agent_name="bear_agent",
                action="HOLD",
                symbol="",
                confidence=0.50,
                reasoning="No bearish setups or put opportunities detected",
                expected_value=0.0,
                risk_score=0.5,
            )

        best_opp = max(bearish_opps, key=lambda o: o.confidence)

        # Regime compatibility modifier
        regime_mod = 0.0
        regime = state.regime_belief.regime if state.regime_belief else "unknown"
        if regime == "trending_down":
            regime_mod = 0.15
        elif regime == "low_vol_drift":
            regime_mod = 0.05
        elif regime == "high_vol_chop":
            regime_mod = -0.10
        elif regime == "trending_up":
            regime_mod = -0.25

        raw_conf = best_opp.confidence + regime_mod
        final_conf = max(min(round(raw_conf, 2), 0.95), 0.20)

        if final_conf < 0.55:
            return AgentPerspective(
                agent_name="bear_agent",
                action="HOLD",
                symbol=best_opp.symbol,
                confidence=final_conf,
                reasoning=f"Bearish setup on {best_opp.symbol} weakened by {regime} regime",
                expected_value=0.0,
                risk_score=round(1.0 - final_conf, 2),
            )

        return AgentPerspective(
            agent_name="bear_agent",
            action="BUY_PUT",
            symbol=best_opp.symbol,
            confidence=final_conf,
            reasoning=f"Bearish setup: {best_opp.reason} (Regime: {regime})",
            expected_value=round(final_conf * 0.85, 2),
            risk_score=round(1.0 - final_conf, 2),
        )

    def _options_perspective(self, state: AgentState) -> AgentPerspective:
        """Options Specialist: Evaluates IV surface, delta leverage, and spread structure viability."""
        logger.info("Decision Agent: Evaluating Options specialist perspective")

        if not state.market_data:
            return AgentPerspective(
                agent_name="options_agent",
                action="HOLD",
                symbol="",
                confidence=0.50,
                reasoning="No market snapshot data available for options analysis",
                expected_value=0.0,
                risk_score=0.5,
            )

        best_symbol = None
        best_action = "HOLD"
        best_score = 0.0
        best_reason = "No optimal options setup"

        # Check candidate opportunities
        for opp in state.opportunities:
            snapshot = state.market_data.get(opp.symbol)
            if not snapshot:
                continue

            iv = snapshot.iv or 0.20
            delta = snapshot.delta or 0.50

            # Optimal IV for debit verticals is 18% to 45%
            if 0.18 <= iv <= 0.45:
                iv_quality = 0.85
            elif iv > 0.45:
                iv_quality = 0.65  # Higher IV increases bid-ask drag
            else:
                iv_quality = 0.60  # Low IV compresses spread profit

            # Delta alignment with opportunity direction
            if opp.direction == "CALL":
                delta_alignment = delta if delta > 0.5 else 0.5
            else:
                delta_alignment = (1.0 - delta) if delta < 0.5 else 0.5

            score = (opp.confidence * 0.50) + (iv_quality * 0.30) + (delta_alignment * 0.20)

            if score > best_score:
                best_score = score
                best_symbol = opp.symbol
                best_action = "BUY_CALL" if opp.direction == "CALL" else "BUY_PUT"
                best_reason = (
                    f"Options structure on {opp.symbol}: IV {iv*100:.1f}% (quality {iv_quality:.2f}), "
                    f"Delta {delta:.2f}, setup {opp.direction}"
                )

        if best_score < 0.55 or not best_symbol:
            return AgentPerspective(
                agent_name="options_agent",
                action="HOLD",
                symbol="",
                confidence=0.50,
                reasoning="Options surface neutral, no high-conviction vertical spread candidate",
                expected_value=0.0,
                risk_score=0.5,
            )

        final_conf = round(min(best_score, 0.92), 2)
        return AgentPerspective(
            agent_name="options_agent",
            action=best_action,
            symbol=best_symbol,
            confidence=final_conf,
            reasoning=best_reason,
            expected_value=round(final_conf * 0.80, 2),
            risk_score=round(1.0 - final_conf, 2),
        )

    # ------------------------------------------------------------------
    # Critic Evaluation (Arbitration Engine)
    # ------------------------------------------------------------------

    def _critic_evaluation(
        self, state: AgentState, perspectives: List[AgentPerspective]
    ) -> CriticAnalysis:
        """Critic arbitration combining Bull, Bear, Options specialists and Regime belief."""
        logger.info("Decision Agent: Critic evaluating specialist perspectives")

        # Fast deterministic critic by default
        return self._deterministic_critic_evaluation(state, perspectives)

    def _deterministic_critic_evaluation(
        self, state: AgentState, perspectives: List[AgentPerspective]
    ) -> CriticAnalysis:
        """Deterministic Critic Arbitration Engine (pure math, <1ms)."""
        regime = state.regime_belief.regime if state.regime_belief else "unknown"

        # Separate active perspectives from HOLD
        active = [p for p in perspectives if p.action in ("BUY_CALL", "BUY_PUT") and p.symbol]

        if not active:
            return CriticAnalysis(
                consensus_action="HOLD",
                consensus_symbol=None,
                consensus_probability=1.0,
                conflicting_agents=[],
                confidence_score=0.60,
                recommendation=f"All specialists recommend HOLD in {regime} regime",
            )

        # Calculate scores per proposed (action, symbol)
        candidate_scores: Dict[tuple[str, str], float] = {}
        for p in active:
            key = (p.action, p.symbol)
            candidate_scores[key] = candidate_scores.get(key, 0.0) + p.confidence

        # Find best candidate proposal
        best_key = max(candidate_scores, key=candidate_scores.get)
        best_action, best_symbol = best_key
        top_score = candidate_scores[best_key]

        # Check agreeing vs conflicting agents
        agreeing_agents = [
            p.agent_name for p in perspectives if p.action == best_action and p.symbol == best_symbol
        ]
        conflicting_agents = [
            p.agent_name for p in perspectives if p.agent_name not in agreeing_agents
        ]

        total_agents = len(perspectives)
        agreement_ratio = len(agreeing_agents) / max(total_agents, 1)

        # Aggregate confidence
        avg_agree_conf = (
            sum(p.confidence for p in perspectives if p.agent_name in agreeing_agents)
            / max(len(agreeing_agents), 1)
        )

        # High vol chop safety dampener: require stronger agreement to trade
        if regime == "high_vol_chop" and agreement_ratio < 0.6:
            return CriticAnalysis(
                consensus_action="HOLD",
                consensus_symbol=None,
                consensus_probability=0.75,
                conflicting_agents=conflicting_agents,
                confidence_score=0.55,
                recommendation=f"High volatility chop regime with mixed specialist signals — holding position for safety",
            )

        # If confidence is below minimum viable threshold, HOLD
        if avg_agree_conf < 0.58:
            return CriticAnalysis(
                consensus_action="HOLD",
                consensus_symbol=None,
                consensus_probability=0.70,
                conflicting_agents=conflicting_agents,
                confidence_score=round(avg_agree_conf, 2),
                recommendation=f"Confidence {avg_agree_conf:.2f} insufficient for entry on {best_symbol} — holding",
            )

        consensus_prob = round(min(agreement_ratio * 0.5 + avg_agree_conf * 0.5, 0.95), 2)
        confidence_score = round(avg_agree_conf, 2)
        recommendation = (
            f"Consensus for {best_action} on {best_symbol} ({len(agreeing_agents)}/{total_agents} specialists agree, "
            f"Regime: {regime})"
        )

        return CriticAnalysis(
            consensus_action=best_action,
            consensus_symbol=best_symbol,
            consensus_probability=consensus_prob,
            conflicting_agents=conflicting_agents,
            confidence_score=confidence_score,
            recommendation=recommendation,
        )

    def _fallback_decision(self, state: AgentState) -> CriticAnalysis:
        """Conservative fallback when decision evaluation fails."""
        logger.warning("Decision Agent: Using conservative fallback decision (HOLD)")
        return CriticAnalysis(
            consensus_action="HOLD",
            consensus_symbol=None,
            consensus_probability=0.80,
            conflicting_agents=[],
            confidence_score=0.50,
            recommendation="Fallback: Holding due to safety/evaluation safeguard",
        )