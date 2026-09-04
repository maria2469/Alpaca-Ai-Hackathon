"""Multi-agent CLI with performance monitoring and bottleneck detection."""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from loguru import logger

import typer
from graph import TradingGraph, AgentState
from agents import (
    MarketScannerAgent,
    MomentumTraderAgent,
    OptionsTraderAgent,
    RiskGateAgent,
    ExecutionAgent,
    PositionManagerAgent,
    TradeMemoryAgent,
    performance_monitor
)

app = typer.Typer(add_completion=False, no_args_is_help=True)


def setup_logging() -> None:
    """Setup logging configuration."""
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | <level>{message}</level>",
    )


def create_agents() -> dict:
    """Create all agents with optimized timeouts."""
    return {
        "market_scanner": MarketScannerAgent(timeout=3.0),
        "momentum_trader": MomentumTraderAgent(timeout=4.0),
        "options_trader": OptionsTraderAgent(timeout=3.0),
        "risk_gate": RiskGateAgent(timeout=3.0),
        "execution_agent": ExecutionAgent(timeout=1.0),
        "position_manager": PositionManagerAgent(timeout=3.0),
        "trade_memory": TradeMemoryAgent(timeout=2.0),
    }


@app.command()
def test_performance():
    """Test multi-agent system with performance monitoring."""
    """Run a single cycle and show performance metrics."""
    setup_logging()
    logger.info("=== Multi-Agent Performance Test ===")
    
    # Create agents
    agents = create_agents()
    logger.info(f"Created {len(agents)} agents")
    
    # Create trading graph
    graph = TradingGraph(agents)
    logger.info("Trading graph initialized")
    
    # Create initial state
    initial_state = AgentState(
        cycle_id=datetime.utcnow().strftime("%Y%m%d-%H%M%S"),
        timestamp=datetime.utcnow(),
        dry_run=True
    )
    
    # Run cycle
    logger.info("Starting trading cycle...")
    try:
        final_state = asyncio.run(graph.run_cycle(initial_state))
        
        # Show results
        logger.info("=== Cycle Results ===")
        logger.info(f"Cycle ID: {final_state.cycle_id}")
        logger.info(f"Final action: {final_state.critic_analysis.consensus_action if final_state.critic_analysis else 'N/A'}")
        logger.info(f"Execution times: {final_state.execution_times}")
        
        # Show performance report
        logger.info("\n" + performance_monitor.get_system_report())
        
        # Show bottlenecks
        if final_state.has_bottlenecks():
            logger.warning(f"⚠️ Bottlenecks detected: {final_state.bottlenecks}")
        else:
            logger.info("✅ No performance bottlenecks detected")
        
    except Exception as e:
        logger.error(f"Cycle failed: {e}")
        raise


@app.command()
def benchmark():
    """Run multiple cycles to benchmark performance."""
    setup_logging()
    logger.info("=== Multi-Agent Benchmark ===")
    
    # Create agents
    agents = create_agents()
    graph = TradingGraph(agents)
    
    # Run multiple cycles
    num_cycles = 5
    total_time = 0.0
    
    for i in range(num_cycles):
        logger.info(f"Running cycle {i+1}/{num_cycles}...")
        
        initial_state = AgentState(
            cycle_id=datetime.utcnow().strftime("%Y%m%d-%H%M%S"),
            timestamp=datetime.utcnow(),
            dry_run=True
        )
        
        try:
            start_time = datetime.utcnow()
            final_state = asyncio.run(graph.run_cycle(initial_state))
            cycle_time = (datetime.utcnow() - start_time).total_seconds()
            total_time += cycle_time
            
            logger.info(f"Cycle {i+1} completed in {cycle_time:.3f}s")
            
        except Exception as e:
            logger.error(f"Cycle {i+1} failed: {e}")
    
    # Show summary
    avg_time = total_time / num_cycles
    logger.info(f"\n=== Benchmark Summary ===")
    logger.info(f"Total cycles: {num_cycles}")
    logger.info(f"Total time: {total_time:.3f}s")
    logger.info(f"Average time: {avg_time:.3f}s per cycle")
    logger.info(f"Cycles per minute: {60.0 / avg_time:.1f}")
    
    # Show performance report
    logger.info("\n" + performance_monitor.get_system_report())


@app.command()
def analyze_bottlenecks():
    """Analyze potential bottlenecks in the system."""
    setup_logging()
    logger.info("=== Bottleneck Analysis ===")
    
    # Simulate various agent performance scenarios
    from agents.base_agent import performance_monitor
    
    # Simulate slow market scanner
    performance_monitor.record_execution("market_scanner", 2.5)
    performance_monitor.record_execution("market_scanner", 3.1)
    performance_monitor.record_execution("market_scanner", 2.8)
    
    # Simulate normal regime agent
    performance_monitor.record_execution("regime_agent", 0.8)
    performance_monitor.record_execution("regime_agent", 0.7)
    performance_monitor.record_execution("regime_agent", 0.9)
    
    # Simulate slow decision agent
    performance_monitor.record_execution("decision_agent", 3.5)
    performance_monitor.record_execution("decision_agent", 4.2)
    performance_monitor.record_execution("decision_agent", 3.8)
    
    # Simulate fast risk gate
    performance_monitor.record_execution("risk_gate", 0.3)
    performance_monitor.record_execution("risk_gate", 0.2)
    performance_monitor.record_execution("risk_gate", 0.3)
    
    # Simulate fast execution agent
    performance_monitor.record_execution("execution_agent", 0.2)
    performance_monitor.record_execution("execution_agent", 0.1)
    performance_monitor.record_execution("execution_agent", 0.2)
    
    # Show analysis
    logger.info(performance_monitor.get_system_report())
    
    # Identify bottlenecks
    bottlenecks = performance_monitor.get_bottlenecks()
    if bottlenecks:
        logger.warning(f"\n⚠️ Identified Bottlenecks:")
        for bottleneck in bottlenecks:
            logger.warning(f"  {bottleneck}")
    else:
        logger.info("\n✅ No bottlenecks identified in simulation")


@app.command()
def compare_modes():
    """Compare multi-agent vs single-agent performance."""
    setup_logging()
    logger.info("=== Performance Comparison ===")
    
    # Test multi-agent
    logger.info("\n--- Multi-Agent Mode ---")
    agents = create_agents()
    graph = TradingGraph(agents)
    
    initial_state = AgentState(
        cycle_id=datetime.utcnow().strftime("%Y%m%d-%H%M%S"),
        timestamp=datetime.utcnow(),
        dry_run=True
    )
    
    start_time = datetime.utcnow()
    multi_agent_state = asyncio.run(graph.run_cycle(initial_state))
    multi_agent_time = (datetime.utcnow() - start_time).total_seconds()
    
    logger.info(f"Multi-agent cycle time: {multi_agent_time:.3f}s")
    
    # Get multi-agent metrics
    multi_report = performance_monitor.get_system_report()
    
    # Clear metrics for fair comparison
    performance_monitor.agent_metrics.clear()
    performance_monitor.bottlenecks.clear()
    
    # Simulate single-agent (current system)
    logger.info("\n--- Single-Agent Mode (Simulated) ---")
    # Simulate single agent doing everything
    performance_monitor.record_execution("single_agent", 1.5)
    performance_monitor.record_execution("single_agent", 1.8)
    performance_monitor.record_execution("single_agent", 1.6)
    
    single_report = performance_monitor.get_system_report()
    
    # Show comparison
    logger.info(f"\n=== Comparison Results ===")
    logger.info(f"Multi-agent time: {multi_agent_time:.3f}s")
    logger.info(f"Single-agent time (avg): ~1.6s")
    logger.info(f"Time overhead: {((multi_agent_time - 1.6) / 1.6 * 100):.1f}%")
    
    logger.info(f"\nMulti-agent benefits:")
    logger.info(f"  + Parallel perspective analysis")
    logger.info(f"  + Bottleneck detection and fallback")
    logger.info(f"  + Performance monitoring")
    logger.info(f"  + Better error isolation")
    
    logger.info(f"\nMulti-agent costs:")
    logger.info(f"  - Higher complexity")
    logger.info(f"  - More execution overhead")
    logger.info(f"  - Potentially slower in optimal conditions")


if __name__ == "__main__":
    app()