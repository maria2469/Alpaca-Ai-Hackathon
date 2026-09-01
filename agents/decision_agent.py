from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from loguru import logger

from agents.base_agent import BaseAgent, monitor_performance
from graph.state import (
    AgentState, AgentPerspective, CriticAnalysis, RegimeBelief, Opportunity, DebateRound
)


class DecisionAgent(BaseAgent):
    """Trade Intelligence Agent: Bull/Bear/Options specialists with 2-round dialectical debate."""

    def __init__(self, timeout: Optional[float] = 2.0):
        super().__init__("decision_agent", timeout)
        self.enable_cache()
        self._last_cycle_id: str = ""

    @monitor_performance("decision_agent", timeout=2.0)
    def execute(self, state: AgentState) -> AgentState:
        """Execute Trade Intelligence analysis with 2-round dialectical debate and critic consensus."""
        logger.info("Decision Agent: Starting Trade Intelligence analysis with Dialectical Debate")

        # Fast-path: return cached result for the same cycle if negotiation_count is 0
        if state.cycle_id and state.cycle_id == self._last_cycle_id and state.critic_analysis and state.negotiation_count == 0:
            logger.info(f"Decision Agent: Using cached result for cycle {state.cycle_id}")
            return state

        try:
            # Step 1: Run 2-Round Dialectical Cross-Examination Debate
            perspectives, debate_round = self._dialectical_debate(state)

            # Store perspectives & debate history in state
            for perspective in perspectives:
                state.add_perspective(perspective)
            state.debate_history.append(debate_round)

            # Step 2: Critic arbitration synthesizing the debate
            critic_analysis = self._critic_evaluation(state, perspectives, debate_round)
            state.critic_analysis = critic_analysis
            self._last_cycle_id = state.cycle_id

            # Step 3: Update inter-cycle working scratchpad with winning narrative
            self._update_working_scratchpad(state, critic_analysis, debate_round)

            logger.info(
                f"Decision Agent: Consensus {critic_analysis.consensus_action} "
                f"on {critic_analysis.consensus_symbol or 'NONE'} "
                f"(probability: {critic_analysis.consensus_probability:.2f}, conf: {critic_analysis.confidence_score:.2f}) | "
                f"Debate: {len(debate_round.concessions)} concession(s)"
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
    # 2-Round Dialectical Cross-Examination Engine
    # ------------------------------------------------------------------

    def _dialectical_debate(
        self, state: AgentState
    ) -> Tuple[List[AgentPerspective], DebateRound]:
        """Conduct a 2-round structured debate between Bull, Bear, and Options specialists."""
        # Round 1: Initial specialist theses
        bull_p = self._bull_perspective(state)
        bear_p = self._bear_perspective(state)
        options_p = self._options_perspective(state)

        round_1_theses = {
            "bull_agent": f"{bull_p.action} {bull_p.symbol} (conf: {bull_p.confidence:.2f}) - {bull_p.reasoning}",
            "bear_agent": f"{bear_p.action} {bear_p.symbol} (conf: {bear_p.confidence:.2f}) - {bear_p.reasoning}",
            "options_agent": f"{options_p.action} {options_p.symbol} (conf: {options_p.confidence:.2f}) - {options_p.reasoning}",
        }

        rebuttals: Dict[str, str] = {}
        concessions: List[str] = []

        # Round 2: Dialectical Cross-Examination & Rebuttal
        # Case 1: Bull proposed BUY_CALL -> Bear cross-examines Bull on resistance / chop
        if bull_p.action == "BUY_CALL" and bull_p.symbol:
            bear_challenge, bull_defense, concession = self._cross_examine_bull(bull_p, state)
            rebuttals["bear_challenge_to_bull"] = bear_challenge
            rebuttals["bull_defense"] = bull_defense
            if concession:
                concessions.append(concession)
                # Adjust bull confidence based on concession/defense
                if "penalized" in concession:
                    bull_p.confidence = max(round(bull_p.confidence - 0.08, 2), 0.35)
                elif "conceded" in concession:
                    bull_p.confidence = min(round(bull_p.confidence + 0.05, 2), 0.95)

        # Case 2: Bear proposed BUY_PUT -> Bull cross-examines Bear on oversold support
        if bear_p.action == "BUY_PUT" and bear_p.symbol:
            bull_challenge, bear_defense, concession = self._cross_examine_bear(bear_p, state)
            rebuttals["bull_challenge_to_bear"] = bull_challenge
            rebuttals["bear_defense"] = bear_defense
            if concession:
                concessions.append(concession)
                if "penalized" in concession:
                    bear_p.confidence = max(round(bear_p.confidence - 0.08, 2), 0.35)
                elif "conceded" in concession:
                    bear_p.confidence = min(round(bear_p.confidence + 0.05, 2), 0.95)

        # Options Specialist reassesses viability given the debate
        options_p = self._options_reassessment(options_p, bull_p, bear_p, state)
        round_1_theses["options_agent_reassessment"] = (
            f"{options_p.action} {options_p.symbol} (conf: {options_p.confidence:.2f}) - {options_p.reasoning}"
        )

        debate_round = DebateRound(
            round_number=2,
            theses=round_1_theses,
            rebuttals=rebuttals,
            concessions=concessions,
            critic_notes=f"Debate completed with {len(concessions)} concession/adjustment(s)",
        )

        perspectives = [bull_p, bear_p, options_p]
        return perspectives, debate_round

    def _cross_examine_bull(
        self, bull_p: AgentPerspective, state: AgentState
    ) -> Tuple[str, str, Optional[str]]:
        """Bear challenges Bull proposal on resistance, overbought RSI, and regime chop."""
        sym = bull_p.symbol
        features = state.symbol_features.get(sym)
        regime = state.regime_belief.regime if state.regime_belief else "unknown"
        scratchpad_context = state.working_scratchpad.get(sym, "")

        challenge = f"Bear challenge on {sym}: Checking overbought RSI & resistance in {regime} regime."
        defense = f"Bull defense on {sym}: Technical setup supported by price action."
        concession = None

        if features:
            rsi = features.rsi or 50.0
            events = [e.kind for e in features.events] if features.events else []

            # Check if Bull is buying into severe overbought RSI or regime chop
            if rsi > 68.0 and "breakout_up" not in events:
                challenge = f"Bear challenge: RSI is overbought at {rsi:.1f} without a 2x ATR breakout. High risk of mean-reversion."
                defense = f"Bull acknowledges elevated RSI {rsi:.1f}."
                concession = f"Bull penalized: RSI {rsi:.1f} overbought without breakout confirmation."
            elif regime == "high_vol_chop" and not events:
                challenge = f"Bear challenge: Regime is high_vol_chop with no entry event. False breakout risk is elevated."
                defense = f"Bull concedes lack of explicit event in chop regime."
                concession = "Bull penalized: Unfavorable high_vol_chop regime with no entry event."
            elif "breakout_up" in events or "gap_up" in events or "accumulation" in scratchpad_context.lower():
                defense = f"Bull rebuttal: Confirmed by event(s) {events} and ongoing accumulation scratchpad thesis."
                challenge = f"Bear concedes: Strong event volume {events} overrides standard resistance."
                concession = f"Bear conceded to Bull on {sym} event strength."

        return challenge, defense, concession

    def _cross_examine_bear(
        self, bear_p: AgentPerspective, state: AgentState
    ) -> Tuple[str, str, Optional[str]]:
        """Bull challenges Bear proposal on oversold support and trend strength."""
        sym = bear_p.symbol
        features = state.symbol_features.get(sym)
        regime = state.regime_belief.regime if state.regime_belief else "unknown"

        challenge = f"Bull challenge on {sym}: Checking oversold support in {regime} regime."
        defense = f"Bear defense on {sym}: Breakdown momentum intact."
        concession = None

        if features:
            rsi = features.rsi or 50.0
            events = [e.kind for e in features.events] if features.events else []

            if rsi < 32.0 and "breakout_down" not in events:
                challenge = f"Bull challenge: RSI is heavily oversold at {rsi:.1f}. High risk of short squeeze bounce."
                defense = f"Bear acknowledges extreme oversold RSI {rsi:.1f}."
                concession = f"Bear penalized: RSI {rsi:.1f} oversold without breakdown confirmation."
            elif regime == "trending_up":
                challenge = f"Bull challenge: Fighting strong upward macro trend ({regime}). Short trades carry high failure rate."
                defense = f"Bear concedes strong macro trend headwind."
                concession = "Bear penalized: Counter-trend short in trending_up regime."
            elif "breakout_down" in events or "gap_down" in events:
                defense = f"Bear rebuttal: Clean breakdown event(s) {events} confirmed."
                challenge = f"Bull concedes: Breakdown event {events} validates short exposure."
                concession = f"Bull conceded to Bear on {sym} breakdown strength."

        return challenge, defense, concession

    def _options_reassessment(
        self,
        options_p: AgentPerspective,
        bull_p: AgentPerspective,
        bear_p: AgentPerspective,
        state: AgentState,
    ) -> AgentPerspective:
        """Options specialist reassesses candidate liquidity and delta leverage after debate."""
        if bull_p.action == "BUY_CALL" and bull_p.confidence >= 0.60:
            snapshot = state.market_data.get(bull_p.symbol)
            if snapshot and snapshot.iv and (0.18 <= snapshot.iv <= 0.42):
                return AgentPerspective(
                    agent_name="options_agent",
                    action="BUY_CALL",
                    symbol=bull_p.symbol,
                    confidence=round(min(bull_p.confidence * 0.95, 0.92), 2),
                    reasoning=f"Options surface confirms viable CALL spread on {bull_p.symbol} (IV: {snapshot.iv*100:.1f}%)",
                    expected_value=round(bull_p.confidence * 0.85, 2),
                    risk_score=round(1.0 - bull_p.confidence, 2),
                )

        if bear_p.action == "BUY_PUT" and bear_p.confidence >= 0.60:
            snapshot = state.market_data.get(bear_p.symbol)
            if snapshot and snapshot.iv and (0.18 <= snapshot.iv <= 0.42):
                return AgentPerspective(
                    agent_name="options_agent",
                    action="BUY_PUT",
                    symbol=bear_p.symbol,
                    confidence=round(min(bear_p.confidence * 0.95, 0.92), 2),
                    reasoning=f"Options surface confirms viable PUT spread on {bear_p.symbol} (IV: {snapshot.iv*100:.1f}%)",
                    expected_value=round(bear_p.confidence * 0.85, 2),
                    risk_score=round(1.0 - bear_p.confidence, 2),
                )

        return options_p

    def _update_working_scratchpad(
        self,
        state: AgentState,
        critic: CriticAnalysis,
        debate: DebateRound,
    ) -> None:
        """Update the multi-bar working scratchpad with the winning trade thesis narrative."""
        now_str = datetime.utcnow().strftime("%H:%M")
        if critic.consensus_action in ("BUY_CALL", "BUY_PUT") and critic.consensus_symbol:
            sym = critic.consensus_symbol
            state.working_scratchpad[sym] = (
                f"[{now_str}] Active Thesis ({critic.consensus_action}): {critic.recommendation} | "
                f"Debate: {len(debate.concessions)} concessions. Watching spread execution & follow-through."
            )
        elif state.opportunities:
            top_opp = state.opportunities[0]
            state.working_scratchpad[top_opp.symbol] = (
                f"[{now_str}] Watched ({top_opp.symbol}): Top setup {top_opp.direction} passed Critic debate "
                f"(Action: HOLD, conf: {critic.confidence_score:.2f}). Monitoring for cleaner trigger."
            )

    # ------------------------------------------------------------------
    # Critic Evaluation (Arbitration Engine)
    # ------------------------------------------------------------------

    def _critic_evaluation(
        self,
        state: AgentState,
        perspectives: List[AgentPerspective],
        debate_round: Optional[DebateRound] = None,
    ) -> CriticAnalysis:
        """Critic arbitration combining Bull, Bear, Options specialists, debate results, and Regime."""
        logger.info("Decision Agent: Critic arbitrating dialectical debate")
        return self._deterministic_critic_evaluation(state, perspectives, debate_round)

    def _deterministic_critic_evaluation(
        self,
        state: AgentState,
        perspectives: List[AgentPerspective],
        debate_round: Optional[DebateRound] = None,
    ) -> CriticAnalysis:
        """Deterministic Critic Arbitration Engine synthesizing debate points."""
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

        # Apply debate concession bonus / penalty
        debate_modifier = 0.0
        if debate_round and debate_round.concessions:
            for c in debate_round.concessions:
                if "conceded to" in c.lower():
                    debate_modifier += 0.03
                elif "penalized" in c.lower():
                    debate_modifier -= 0.04

        calibrated_conf = max(min(avg_agree_conf + debate_modifier, 0.95), 0.20)

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
        if calibrated_conf < 0.58:
            return CriticAnalysis(
                consensus_action="HOLD",
                consensus_symbol=None,
                consensus_probability=0.70,
                conflicting_agents=conflicting_agents,
                confidence_score=round(calibrated_conf, 2),
                recommendation=f"Confidence {calibrated_conf:.2f} insufficient for entry on {best_symbol} after debate — holding",
            )

        consensus_prob = round(min(agreement_ratio * 0.5 + calibrated_conf * 0.5, 0.95), 2)
        confidence_score = round(calibrated_conf, 2)
        recommendation = (
            f"Consensus for {best_action} on {best_symbol} ({len(agreeing_agents)}/{total_agents} specialists agree, "
            f"Debate: {len(debate_round.concessions) if debate_round else 0} concessions, Regime: {regime})"
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