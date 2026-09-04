"""LangGraph orchestration for multi-agent trading system with performance optimization."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    logger.error("LangGraph not installed. Run: uv sync")
    raise

from graph.state import AgentState
from agents.base_agent import performance_monitor, BaseAgent


class TradingGraph:
    """Multi-agent trading graph with parallel execution and bottleneck detection."""
    
    def __init__(self, agents: Dict[str, BaseAgent]):
        self.agents = agents
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()
        self.max_cycle_time = 10.0  # Maximum allowed time for full cycle (seconds)
    
    def _build_graph(self) -> StateGraph:
        """Build the complete 7-step LangGraph workflow with risk-decision negotiation loop."""
        workflow = StateGraph(AgentState)
        
        # Add 7 agent nodes
        workflow.add_node("market_scanner", self._market_scanner_node)
        workflow.add_node("regime_agent", self._regime_agent_node)
        workflow.add_node("decision_agent", self._decision_agent_node)
        workflow.add_node("risk_gate", self._risk_gate_node)
        workflow.add_node("execution_agent", self._execution_agent_node)
        workflow.add_node("position_manager", self._position_manager_node)
        workflow.add_node("trade_memory", self._trade_memory_node)
        
        # Define workflow edges
        workflow.set_entry_point("market_scanner")
        workflow.add_edge("market_scanner", "regime_agent")
        workflow.add_edge("regime_agent", "decision_agent")
        workflow.add_edge("decision_agent", "risk_gate")
        
        # Conditional Edge: Risk Gate -> Decision Agent (Negotiation loop) OR Execution Agent
        def route_after_risk_gate(state: AgentState) -> str:
            """Dynamic negotiation: if Risk Gate challenges the contract, loop back for counter-proposal."""
            if (
                state.risk_decision
                and not state.risk_decision.approved
                and state.critic_analysis
                and state.critic_analysis.consensus_action in ("BUY_CALL", "BUY_PUT")
                and state.negotiation_count == 0
                and any(term in state.risk_decision.reason.lower() for term in ("no acceptable spread", "low confidence", "rejected"))
            ):
                logger.info("LangGraph: Risk Gate challenged decision -> Routing back to Decision Agent for counter-proposal")
                state.negotiation_count += 1
                return "decision_agent"
            return "execution_agent"

        workflow.add_conditional_edges(
            "risk_gate",
            route_after_risk_gate,
            {
                "decision_agent": "decision_agent",
                "execution_agent": "execution_agent",
            },
        )

        workflow.add_edge("execution_agent", "position_manager")
        workflow.add_edge("position_manager", "trade_memory")
        workflow.add_edge("trade_memory", END)
        
        return workflow.compile(checkpointer=self.checkpointer)

    def save_graph_image(self, output_path: str = "assets/langgraph_architecture.png") -> None:
        """Render and save the actual LangGraph StateGraph as a PNG file."""
        try:
            png_bytes = self.graph.get_graph().draw_mermaid_png()
            with open(output_path, "wb") as f:
                f.write(png_bytes)
            logger.info(f"LangGraph: Saved architecture diagram to {output_path}")
        except Exception as e:
            logger.warning(f"LangGraph: Could not render graph PNG: {e}")
    
    async def _market_scanner_node(self, state: AgentState) -> AgentState:
        """Market scanner agent node with performance monitoring."""
        start_time = datetime.utcnow()
        logger.info("Executing Market Scanner Agent")
        
        try:
            agent = self.agents["market_scanner"]
            result = await self._execute_agent_with_timeout(agent, state, timeout=3.0)
            state = result
        except Exception as e:
            logger.error(f"Market Scanner failed: {e}")
            state.add_bottleneck(f"Market Scanner failed: {str(e)}")
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        state.execution_times["market_scanner"] = execution_time
        
        if execution_time > 2.0:
            logger.warning(f"Market Scanner slow: {execution_time:.3f}s")
            state.add_bottleneck(f"Market Scanner took {execution_time:.3f}s")
        
        return state
    
    async def _regime_agent_node(self, state: AgentState) -> AgentState:
        """Regime classification agent node with fast fallback."""
        start_time = datetime.utcnow()
        logger.info("Executing Regime Agent")
        
        try:
            agent = self.agents["regime_agent"]
            # Regime agent has shorter timeout - use deterministic fallback if slow
            result = await self._execute_agent_with_timeout(agent, state, timeout=1.5)
            state = result
        except Exception as e:
            logger.warning(f"Regime Agent failed, using fallback: {e}")
            # Fallback to simple regime classification
            state.regime_belief = self._fallback_regime_classification(state)
            state.add_bottleneck(f"Regime Agent timeout, used fallback")
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        state.execution_times["regime_agent"] = execution_time
        
        return state
    
    async def _decision_agent_node(self, state: AgentState) -> AgentState:
        """Decision agent with parallel perspective analysis."""
        start_time = datetime.utcnow()
        logger.info("Executing Decision Agent")
        
        # If this is a negotiation re-entry following a risk challenge:
        if state.risk_decision and not state.risk_decision.approved:
            state.negotiation_count += 1
            if state.critic_analysis and state.critic_analysis.consensus_symbol:
                rejected_sym = state.critic_analysis.consensus_symbol
                logger.info(f"Decision Agent: Counter-proposal deliberation excluding challenged symbol {rejected_sym}")
                state.opportunities = [o for o in state.opportunities if o.symbol != rejected_sym]

        try:
            agent = self.agents["decision_agent"]
            # Decision agent gets more time but has parallel execution
            result = await self._execute_agent_with_timeout(agent, state, timeout=4.0)
            state = result
        except Exception as e:
            logger.error(f"Decision Agent failed: {e}")
            state.add_bottleneck(f"Decision Agent failed: {str(e)}")
            # Fallback to simple decision logic
            state.critic_analysis = self._fallback_decision(state)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        state.execution_times["decision_agent"] = execution_time
        
        if execution_time > 3.0:
            logger.warning(f"Decision Agent slow: {execution_time:.3f}s")
            state.add_bottleneck(f"Decision Agent took {execution_time:.3f}s")
        
        return state
    
    async def _risk_gate_node(self, state: AgentState) -> AgentState:
        """Risk gate agent node (fast deterministic logic)."""
        start_time = datetime.utcnow()
        logger.info("Executing Risk Gate")
        
        try:
            agent = self.agents["risk_gate"]
            result = await self._execute_agent_with_timeout(agent, state, timeout=1.0)
            state = result
        except Exception as e:
            logger.error(f"Risk Gate failed: {e}")
            state.risk_decision = self._fallback_risk_decision(state)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        state.execution_times["risk_gate"] = execution_time
        
        return state
    
    async def _execution_agent_node(self, state: AgentState) -> AgentState:
        """Execution agent node (fast deterministic logic)."""
        start_time = datetime.utcnow()
        logger.info("Executing Execution Agent")
        
        try:
            agent = self.agents["execution_agent"]
            result = await self._execute_agent_with_timeout(agent, state, timeout=1.0)
            state = result
        except Exception as e:
            logger.error(f"Execution Agent failed: {e}")
            state.execution_plan = self._fallback_execution_plan(state)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        state.execution_times["execution_agent"] = execution_time
        
        return state

    async def _position_manager_node(self, state: AgentState) -> AgentState:
        """Position manager agent node (real-time PnL, DTE time stop, TP, stop-loss)."""
        start_time = datetime.utcnow()
        logger.info("Executing Position Manager Agent")
        
        try:
            agent = self.agents["position_manager"]
            result = await self._execute_agent_with_timeout(agent, state, timeout=3.0)
            state = result
        except Exception as e:
            logger.error(f"Position Manager failed: {e}")
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        state.execution_times["position_manager"] = execution_time
        
        return state

    async def _trade_memory_node(self, state: AgentState) -> AgentState:
        """Trade memory agent node (lifecycle trace, signal calibration, mistake analysis)."""
        start_time = datetime.utcnow()
        logger.info("Executing Trade Memory Agent")
        
        try:
            agent = self.agents["trade_memory"]
            result = await self._execute_agent_with_timeout(agent, state, timeout=2.0)
            state = result
        except Exception as e:
            logger.error(f"Trade Memory failed: {e}")
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        state.execution_times["trade_memory"] = execution_time
        
        return state
    
    async def _execute_agent_with_timeout(
        self, 
        agent: BaseAgent, 
        state: AgentState, 
        timeout: float
    ) -> AgentState:
        """Execute an agent with timeout protection."""
        try:
            return await asyncio.wait_for(
                self._run_agent_async(agent, state),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Agent {agent.name} timed out after {timeout}s")
            agent.metrics.timeouts += 1
            raise
    
    async def _run_agent_async(self, agent: BaseAgent, state: AgentState) -> AgentState:
        """Run agent execution asynchronously."""
        # For now, run synchronously but could be made truly async
        return agent.execute(state)
    
    def _fallback_regime_classification(self, state: AgentState) -> Any:
        """Fast fallback regime classification when LLM is too slow."""
        from graph.state import RegimeBelief
        logger.info("Using fast fallback regime classification")
        
        # Simple deterministic fallback based on market data
        if not state.market_data:
            return RegimeBelief(
                regime="unknown",
                confidence=0.5,
                volatility_level="medium",
                trend_strength=0.0
            )
        
        # Use simple logic from existing regime.py as fallback
        # This would be the original deterministic logic
        return RegimeBelief(
            regime="low_vol_drift",
            confidence=0.7,
            volatility_level="low",
            trend_strength=0.3
        )
    
    def _fallback_decision(self, state: AgentState) -> Any:
        """Fallback decision when decision agent fails."""
        from graph.state import CriticAnalysis
        logger.info("Using fallback decision logic")
        
        # Simple fallback: pass if no strong signals
        return CriticAnalysis(
            consensus_action="HOLD",
            consensus_symbol=None,
            consensus_probability=0.8,
            conflicting_agents=[],
            confidence_score=0.7,
            recommendation="Fallback: No strong signals, holding position"
        )
    
    def _fallback_risk_decision(self, state: AgentState) -> Any:
        """Fallback risk decision (conservative)."""
        from graph.state import RiskDecision
        logger.info("Using conservative fallback risk decision")
        
        return RiskDecision(
            approved=False,
            reason="Fallback: Conservative risk decision - reject trade",
            portfolio_risk=0.0,
            greek_exposure={},
            position_size=0.0
        )
    
    def _fallback_execution_plan(self, state: AgentState) -> Any:
        """Fallback execution plan (no trade)."""
        from graph.state import ExecutionPlan
        logger.info("Using fallback execution plan (no trade)")
        
        return ExecutionPlan(
            symbol="",
            action="HOLD",
            contracts=[],
            limit_price=0.0,
            order_type="MARKET",
            time_in_force="DAY",
            client_order_id="fallback-no-trade",
            estimated_slippage=0.0,
            fill_probability=0.0
        )
    
    async def run_cycle(self, initial_state: AgentState) -> AgentState:
        """Run a complete trading cycle with performance monitoring."""
        cycle_start = datetime.utcnow()
        cycle_id = cycle_start.strftime("%Y%m%d-%H%M%S")
        initial_state.cycle_id = cycle_id
        
        logger.info(f"Starting trading cycle {cycle_id}")
        
        try:
            # Run the graph
            config = {"configurable": {"thread_id": cycle_id}}
            result = await self.graph.ainvoke(initial_state, config)
            
            # Handle both dict and AgentState returns
            if isinstance(result, dict):
                final_state = AgentState(**result)
            else:
                final_state = result
            
            cycle_time = (datetime.utcnow() - cycle_start).total_seconds()
            
            # Check for cycle-level bottlenecks
            if cycle_time > self.max_cycle_time:
                logger.warning(f"Cycle {cycle_id} exceeded max time: {cycle_time:.3f}s")
                final_state.add_bottleneck(f"Total cycle time {cycle_time:.3f}s exceeded {self.max_cycle_time}s")
            
            # Log performance summary
            self._log_cycle_performance(final_state, cycle_time)
            
            return final_state
            
        except Exception as e:
            logger.error(f"Cycle {cycle_id} failed: {e}")
            initial_state.add_bottleneck(f"Cycle failed: {str(e)}")
            return initial_state
    
    def _log_cycle_performance(self, state: AgentState, cycle_time: float) -> None:
        """Log performance summary for the cycle."""
        logger.info(f"Cycle {state.cycle_id} completed in {cycle_time:.3f}s")
        
        if state.execution_times:
            times_str = ", ".join([f"{k}={v:.3f}s" for k, v in state.execution_times.items()])
            logger.info(f"Agent execution times: {times_str}")
        
        if state.has_bottlenecks():
            logger.warning(f"Bottlenecks detected: {state.bottlenecks}")
        
        # Log system-wide performance
        logger.info(performance_monitor.get_system_report())


class ParallelExecutionEngine:
    """Execute independent agents in parallel to reduce total cycle time."""
    
    @staticmethod
    async def execute_parallel(
        agents: List[BaseAgent], 
        state: AgentState,
        max_concurrent: int = 3
    ) -> AgentState:
        """Execute multiple agents in parallel with concurrency control."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_semaphore(agent: BaseAgent) -> AgentState:
            async with semaphore:
                return await asyncio.get_event_loop().run_in_executor(
                    None, agent.execute, state
                )
        
        # Execute all agents in parallel
        tasks = [execute_with_semaphore(agent) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge results (last non-exception result wins)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Parallel execution error: {result}")
            elif isinstance(result, AgentState):
                state = result
        
        return state