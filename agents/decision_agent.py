from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from loguru import logger

from agents.base_agent import BaseAgent, monitor_performance
from graph.state import AgentState, CriticAnalysis, ReasoningTrace

# Import main system decision logic
import decision_layer
from data_models import SymbolFeatures


class MomentumTraderAgent(BaseAgent):
    """Momentum Trader: Uses multi-turn LLM reasoning to decide which underlying to trade and direction."""

    def __init__(self, timeout: Optional[float] = 4.0):
        super().__init__("momentum_trader", timeout)
        self.enable_cache()
        self._last_cycle_id: str = ""

    @monitor_performance("momentum_trader", timeout=4.0)
    def execute(self, state: AgentState) -> AgentState:
        """Execute momentum-based entry decision using multi-turn LLM reasoning."""
        logger.info("Momentum Trader: Starting multi-turn LLM reasoning")

        # Initialize reasoning trace
        reasoning_trace = ReasoningTrace(
            agent_name="momentum_trader",
            cycle_id=state.cycle_id or "unknown"
        )
        state.reasoning_traces["momentum_trader"] = reasoning_trace

        # Fast-path: return cached result for the same cycle
        if state.cycle_id and state.cycle_id == self._last_cycle_id and state.critic_analysis:
            logger.info(f"Momentum Trader: Using cached result for cycle {state.cycle_id}")
            return state

        try:
            # Reasoning Step 1: Candidate Collection
            reasoning_trace.add_step(
                step_name="Candidate Collection",
                reasoning="Gathering trading opportunities from market scanner",
                conclusion=f"Found {len(state.opportunities)} opportunities",
                metadata={"opportunity_count": len(state.opportunities)}
            )

            # Convert opportunities to SymbolFeatures for decision_layer
            candidates = []
            for opp in state.opportunities:
                features = state.symbol_features.get(opp.symbol)
                if features:
                    candidates.append(features)

            if not candidates:
                logger.info("Momentum Trader: No candidates available - HOLD")
                reasoning_trace.add_step(
                    step_name="Candidate Filter",
                    reasoning="No candidates with valid features found",
                    conclusion="HOLD - No valid candidates",
                    metadata={"filtered_count": 0}
                )
                reasoning_trace.final_decision = "HOLD"
                reasoning_trace.confidence = 1.0
                state.critic_analysis = CriticAnalysis(
                    consensus_action="HOLD",
                    consensus_symbol=None,
                    consensus_probability=1.00,
                    conflicting_agents=[],
                    confidence_score=0.60,
                    recommendation="No candidates available"
                )
                return state

            # Reasoning Step 2: Quantitative Pre-filter
            reasoning_trace.add_step(
                step_name="Quantitative Pre-filter",
                reasoning="Applying quantitative edge score filter (threshold: 0.55)",
                conclusion=f"Filtering {len(candidates)} candidates",
                metadata={"initial_count": len(candidates)}
            )

            qualified = [c for c in candidates if decision_layer.compute_quantitative_edge_score(c) >= 0.55]

            qualified_scores = {c.symbol: decision_layer.compute_quantitative_edge_score(c) for c in qualified}
            reasoning_trace.add_step(
                step_name="Quantitative Scoring",
                reasoning="Computed quantitative edge scores for all candidates",
                conclusion=f"{len(qualified)} candidates passed threshold",
                metadata={"qualified_scores": qualified_scores}
            )

            if not qualified:
                logger.info("Momentum Trader: No candidates passed quantitative edge filter - HOLD")
                reasoning_trace.add_step(
                    step_name="Quantitative Filter Result",
                    reasoning="No candidates met quantitative edge threshold of 0.55",
                    conclusion="HOLD - Insufficient quantitative edge",
                    metadata={"threshold": 0.55, "max_score": max([decision_layer.compute_quantitative_edge_score(c) for c in candidates]) if candidates else 0}
                )
                reasoning_trace.final_decision = "HOLD"
                reasoning_trace.confidence = 1.0
                state.critic_analysis = CriticAnalysis(
                    consensus_action="HOLD",
                    consensus_symbol=None,
                    consensus_probability=1.00,
                    conflicting_agents=[],
                    confidence_score=0.60,
                    recommendation="No candidates passed quantitative edge filter"
                )
                return state

            # Reasoning Step 3: Context Integration
            reasoning_trace.add_step(
                step_name="Context Integration",
                reasoning="Integrating recent lessons, agent mistakes, and working scratchpad",
                conclusion=f"Context loaded: {len(state.recent_lessons or [])} lessons, {len(state.agent_mistakes or [])} mistakes",
                metadata={
                    "recent_lessons_count": len(state.recent_lessons or []),
                    "agent_mistakes_count": len(state.agent_mistakes or []),
                    "working_scratchpad_keys": list(state.working_scratchpad.keys()) if state.working_scratchpad else []
                }
            )

            # Reasoning Step 4: LLM Decision
            import settings
            api_key = getattr(settings, 'GEMINI_API_KEY', None)

            if not api_key:
                logger.warning("Momentum Trader: No GEMINI_API_KEY - using deterministic fallback")
                reasoning_trace.add_step(
                    step_name="LLM Decision",
                    reasoning="No API key available, falling back to deterministic scoring",
                    conclusion="Using deterministic fallback",
                    metadata={"api_key_available": False}
                )
                state.critic_analysis = self._deterministic_fallback(qualified, state, reasoning_trace)
            else:
                try:
                    working_scratchpad = state.working_scratchpad if state.working_scratchpad else {}

                    reasoning_trace.add_step(
                        step_name="LLM Invocation",
                        reasoning="Invoking LLM for final entry decision with full context",
                        conclusion=f"Submitting {len(qualified)} qualified candidates to LLM",
                        metadata={
                            "candidate_symbols": [c.symbol for c in qualified],
                            "api_model": getattr(settings, 'PRIMARY_MODEL', 'gemini-2.5-flash')
                        }
                    )

                    choice = decision_layer.decide_entry(
                        qualified,
                        api_key,
                        recent_lessons=state.recent_lessons,
                        agent_mistakes=state.agent_mistakes,
                        working_scratchpad=working_scratchpad
                    )

                    if choice:
                        action = "BUY_CALL" if choice.direction == "CALL" else "BUY_PUT"
                        reasoning_trace.add_step(
                            step_name="LLM Decision Result",
                            reasoning=f"LLM selected {choice.symbol} {choice.direction} based on thesis",
                            conclusion=f"ENTRY: {choice.symbol} {choice.direction}",
                            metadata={
                                "symbol": choice.symbol,
                                "direction": choice.direction,
                                "thesis": choice.thesis
                            }
                        )
                        state.critic_analysis = CriticAnalysis(
                            consensus_action=action,
                            consensus_symbol=choice.symbol,
                            consensus_probability=0.70,
                            conflicting_agents=[],
                            confidence_score=0.70,
                            recommendation=choice.thesis or f"LLM decision: {choice.symbol} {choice.direction}"
                        )
                        reasoning_trace.final_decision = f"{choice.symbol} {choice.direction}"
                        reasoning_trace.confidence = 0.70
                        logger.info(f"Momentum Trader: LLM chose {choice.symbol} {choice.direction}")
                    else:
                        reasoning_trace.add_step(
                            step_name="LLM Decision Result",
                            reasoning="LLM chose to hold - no compelling setup found",
                            conclusion="HOLD - LLM decision",
                            metadata={"decision": "hold"}
                        )
                        state.critic_analysis = CriticAnalysis(
                            consensus_action="HOLD",
                            consensus_symbol=None,
                            consensus_probability=1.00,
                            conflicting_agents=[],
                            confidence_score=0.60,
                            recommendation="LLM chose HOLD"
                        )
                        reasoning_trace.final_decision = "HOLD"
                        reasoning_trace.confidence = 1.0
                        logger.info("Momentum Trader: LLM chose HOLD")
                except decision_layer.LlmError as e:
                    logger.error(f"Momentum Trader: LLM error: {e} - using deterministic fallback")
                    reasoning_trace.add_step(
                        step_name="LLM Error",
                        reasoning=f"LLM invocation failed: {e}",
                        conclusion="Falling back to deterministic scoring",
                        metadata={"error": str(e)}
                    )
                    state.critic_analysis = self._deterministic_fallback(qualified, state, reasoning_trace)

            self._last_cycle_id = state.cycle_id

            # Reasoning Step 5: Final Summary
            reasoning_trace.add_step(
                step_name="Decision Summary",
                reasoning=f"Final decision after {reasoning_trace.total_turns} reasoning turns",
                conclusion=reasoning_trace.final_decision,
                metadata={
                    "total_turns": reasoning_trace.total_turns,
                    "final_confidence": reasoning_trace.confidence
                }
            )

            # Step 6: Update working scratchpad
            self._update_working_scratchpad(state, state.critic_analysis)

            # Log reasoning trace summary
            logger.info(f"\n{reasoning_trace.to_summary()}")

        except Exception as e:
            logger.error(f"Momentum Trader failed: {e}")
            state.add_bottleneck(f"Momentum Trader failed: {str(e)}")
            reasoning_trace.add_step(
                step_name="Error",
                reasoning=f"Execution failed: {e}",
                conclusion="HOLD - Error fallback",
                metadata={"error": str(e)}
            )
            state.critic_analysis = self._fallback_decision(state)

        return state

    def _deterministic_fallback(self, candidates: List, state: AgentState, reasoning_trace: ReasoningTrace) -> CriticAnalysis:
        """Deterministic fallback when LLM is unavailable - uses quantitative scoring."""
        if not candidates:
            reasoning_trace.add_step(
                step_name="Deterministic Fallback",
                reasoning="No candidates available for deterministic fallback",
                conclusion="HOLD - No candidates",
                metadata={}
            )
            return CriticAnalysis(
                consensus_action="HOLD",
                consensus_symbol=None,
                consensus_probability=1.00,
                conflicting_agents=[],
                confidence_score=0.60,
                recommendation="No candidates available"
            )

        # Pick best candidate by quantitative edge score
        best = max(candidates, key=lambda c: decision_layer.compute_quantitative_edge_score(c))
        score = decision_layer.compute_quantitative_edge_score(best)

        reasoning_trace.add_step(
            step_name="Deterministic Fallback",
            reasoning=f"Selecting best candidate by quantitative edge score",
            conclusion=f"Best: {best.symbol} (score: {score:.2f})",
            metadata={"best_symbol": best.symbol, "best_score": score}
        )

        if score < 0.55:
            reasoning_trace.add_step(
                step_name="Deterministic Filter",
                reasoning=f"Best candidate score {score:.2f} below threshold 0.55",
                conclusion="HOLD - Insufficient quantitative edge",
                metadata={"score": score, "threshold": 0.55}
            )
            return CriticAnalysis(
                consensus_action="HOLD",
                consensus_symbol=None,
                consensus_probability=1.00,
                conflicting_agents=[],
                confidence_score=0.60,
                recommendation=f"Best candidate {best.symbol} score {score:.2f} below threshold"
            )

        # Determine direction from events
        direction = "CALL"
        if best.events:
            for event in best.events:
                if event.direction == "PUT":
                    direction = "PUT"
                    break

        action = "BUY_CALL" if direction == "CALL" else "BUY_PUT"

        reasoning_trace.final_decision = f"{best.symbol} {direction}"
        reasoning_trace.confidence = score

        return CriticAnalysis(
            consensus_action=action,
            consensus_symbol=best.symbol,
            consensus_probability=score,
            conflicting_agents=[],
            confidence_score=score,
            recommendation=f"Deterministic fallback: {best.symbol} {direction} (score: {score:.2f})"
        )

    def _update_working_scratchpad(self, state: AgentState, critic: CriticAnalysis) -> None:
        """Update working scratchpad with momentum trader thesis."""
        now_str = datetime.utcnow().strftime("%H:%M")
        if critic.consensus_action in ("BUY_CALL", "BUY_PUT") and critic.consensus_symbol:
            sym = critic.consensus_symbol
            state.working_scratchpad[sym] = (
                f"[{now_str}] Momentum Thesis ({critic.consensus_action}): {critic.recommendation}"
            )

    def _fallback_decision(self, state: AgentState) -> CriticAnalysis:
        """Conservative fallback when decision evaluation fails."""
        logger.warning("Momentum Trader: Using conservative fallback decision (HOLD)")
        return CriticAnalysis(
            consensus_action="HOLD",
            consensus_symbol=None,
            consensus_probability=0.80,
            conflicting_agents=[],
            confidence_score=0.50,
            recommendation="Fallback: Holding due to safety/evaluation safeguard",
        )


# Backward compatibility alias
DecisionAgent = MomentumTraderAgent