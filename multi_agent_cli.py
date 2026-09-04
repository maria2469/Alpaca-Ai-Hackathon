"""Multi-agent CLI: Primary command center and live paper trading engine.

Coordinates the 7 specialized autonomous agents:
- Market Scanner Agent: Live market data, Greeks, unusual activity, opportunities
- Momentum Trader Agent: Dialectical & quantitative momentum scoring with multi-turn reasoning
- Options Trader Agent: Deterministic options selection and contract confirmation
- Risk Gate Agent: 4-tier portfolio risk caps, Greek limits, cluster risk, drawdown circuit breaker
- Execution Agent: Limit price optimization, slippage bounds, MLEG order submission, fill polling
- Position Manager Agent: Real-time PnL, DTE time stop, TP/SL, momentum breakdown exits
- Trade Memory Agent: Lifecycle trace logging, calibration, win rate attribution, post-mortem reflection

Run as:
    uv run --env-file .env multi_agent_cli.py run            # Dry-run multi-agent cycle
    uv run --env-file .env multi_agent_cli.py run --execute  # Live paper trading order submission
    uv run --env-file .env multi_agent_cli.py live          # Continuous live market trading loop
    uv run --env-file .env multi_agent_cli.py account       # Real-time account & position report
    uv run --env-file .env multi_agent_cli.py status        # Agent performance & trade memory report
"""

from __future__ import annotations

import asyncio
import math
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

from loguru import logger
import typer

import broker
from data_models import to_json_line
from graph import TradingGraph, AgentState
from agents import (
    MarketScannerAgent,
    MomentumTraderAgent,
    OptionsTraderAgent,
    RiskGateAgent,
    ExecutionAgent,
    PositionManagerAgent,
    TradeMemoryAgent,
    performance_monitor,
)
import pos_and_risk
import settings
import sounds

FILL_POLL_TIMEOUT_SECONDS = 20.0
FILL_POLL_INTERVAL_SECONDS = 2.0
ENTRY_ORDER_CANCEL_TIMEOUT_SECONDS = 180.0
_FILLED = ("filled", "FILLED", "partially_filled")
_DEAD = ("canceled", "CANCELED", "expired", "EXPIRED", "rejected", "REJECTED")

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Autonomous Multi-Agent Trading Engine for Alpaca Options.",
)


def setup_logging() -> None:
    """Configure concise timestamped console logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | <level>{message}</level>",
    )


def create_agents() -> dict:
    """Create all 7 specialized trading agents with tuned timeouts."""
    return {
        "market_scanner": MarketScannerAgent(timeout=3.0),
        "momentum_trader": MomentumTraderAgent(timeout=4.0),
        "options_trader": OptionsTraderAgent(timeout=3.0),
        "risk_gate": RiskGateAgent(timeout=3.0),
        "execution_agent": ExecutionAgent(timeout=3.0),
        "position_manager": PositionManagerAgent(timeout=3.0),
        "trade_memory": TradeMemoryAgent(timeout=2.0),
    }


def run_agentic_cycle(
    graph: TradingGraph,
    *,
    execute: bool = False,
    use_llm: bool = False,
) -> AgentState:
    """Execute one full multi-agent cycle through the LangGraph workflow."""
    cycle_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    initial_state = AgentState(
        cycle_id=cycle_id,
        timestamp=datetime.now(timezone.utc),
        dry_run=not execute,
        use_llm=use_llm,
    )
    return asyncio.run(graph.run_cycle(initial_state))


def log_agentic_cycle_summary(state: AgentState) -> None:
    """Display an aesthetically structured terminal summary of the multi-agent cycle."""
    mode_tag = "LIVE PAPER SUBMISSION" if not state.dry_run else "DRY-RUN SIMULATION"
    logger.info("╔══════════════════════════════════════════════════════════════════════╗")
    logger.info(f"║ PACA Multi-Agent Cycle: {state.cycle_id} | Mode: {mode_tag:<22} ║")
    logger.info("╠══════════════════════════════════════════════════════════════════════╣")

    # 1. Market Scanner
    opp_count = len(getattr(state, "opportunities", []))
    conf = getattr(state, "scanner_confidence", 0.0)
    mkt_status = "OPEN" if getattr(state, "market_open", True) else "CLOSED"
    logger.info(f"║ 🔍 Market Scanner: Market {mkt_status} | {opp_count} opportunities found (Conf: {conf:.2f})")

    # 2. Momentum Trader / Decision Agent
    if state.critic_analysis:
        ca = state.critic_analysis
        logger.info(
            f"║ 🧠 Momentum Consensus: {ca.consensus_action} {ca.consensus_symbol or ''} "
            f"(Prob: {ca.consensus_probability:.1%}, Conf: {ca.confidence_score:.2f})"
        )
        trace = state.reasoning_traces.get("momentum_trader")
        if trace:
            logger.info(f"║    Reasoning Turns: {trace.total_turns} | Final Decision: {trace.final_decision}")

    # 3. Selected Spread & Risk Gate
    if state.selected_spread:
        s = state.selected_spread
        long_s = s.long.symbol if s.long else "N/A"
        short_s = s.short.symbol if s.short else "N/A"
        logger.info(
            f"║ 📐 Options Screener: {s.underlying} {s.expiration} {s.direction} spread "
            f"({long_s} / {short_s}) width=${s.width:.2f} debit=${s.net_debit:.2f}"
        )
    if state.risk_decision:
        rd = state.risk_decision
        verdict = "APPROVED" if rd.approved else "REJECTED"
        ev_val = rd.expected_value if rd.expected_value is not None else 0.0
        logger.info(
            f"║ 🛡️ Portfolio Risk Gate: {verdict} | Qty: {rd.position_size}x | "
            f"Risk: ${rd.portfolio_risk:.2f} | EV: ${ev_val:.2f}"
        )
        if not rd.approved:
            logger.info(f"║    Rejection Reason: {rd.reason}")

    # 4. Execution Agent
    if state.execution_plan:
        ep = state.execution_plan
        logger.info(
            f"║ ⚡ Execution Agent: {ep.status.upper()} | Order: {ep.client_order_id} "
            f"limit=${ep.limit_price:.2f} | Slippage: {ep.estimated_slippage * 10000:.1f} bps"
        )
        if ep.order_id:
            logger.info(f"║    Broker Order ID: {ep.order_id}")

    # 5. Position Manager
    if state.position_report:
        pr = state.position_report
        logger.info(
            f"║ 📊 Position Manager: {pr.total_positions} active position(s) | "
            f"Total Risk: ${pr.total_open_risk:.2f} | Unrealized PnL: ${pr.total_unrealized_pnl:+.2f}"
        )
        if pr.exits_triggered:
            for ex in pr.exits_triggered:
                logger.warning(f"║ 🚨 Exit Triggered: {ex.spread_label} -> Reason: {ex.exit_reason}")

    # 6. Trade Memory
    if state.trade_memory_record:
        tm = state.trade_memory_record
        logger.info(f"║ 📚 Trade Memory: Cycle recorded ({tm.action} {tm.symbol})")

    # 7. Bottlenecks
    if state.has_bottlenecks():
        logger.warning(f"║ ⚠️ Bottlenecks: {', '.join(state.bottlenecks)}")

    logger.info("╚══════════════════════════════════════════════════════════════════════╝")


def _extract_new_orders(state: AgentState) -> dict[str, str]:
    """Extract newly submitted order IDs and readable labels from AgentState."""
    new_orders: dict[str, str] = {}
    for receipt in getattr(state, "execution_receipts", []):
        if isinstance(receipt, dict) and receipt.get("submitted") and receipt.get("order_id"):
            oid = receipt["order_id"]
            kind = receipt.get("kind", "order")
            spread = receipt.get("spread") or receipt.get("client_order_id") or "spread"
            new_orders[oid] = f"{kind} {spread}"
    plan = getattr(state, "execution_plan", None)
    if plan and plan.status == "submitted" and plan.order_id:
        if plan.order_id not in new_orders:
            new_orders[plan.order_id] = f"entry {plan.symbol} {plan.action}"
    return new_orders


def _check_fills(trading: object, pending: dict[str, str]) -> None:
    """Check pending order fill status with audio feedback."""
    for order_id, label in list(pending.items()):
        status = broker.fetch_order_status(trading, order_id)
        if status in _FILLED:
            logger.info("FILLED: {} (order {})", label, order_id)
            sounds.play_fill_sound()
            del pending[order_id]
        elif status in _DEAD:
            logger.info("order not filled ({}): {} (order {})", status, label, order_id)
            del pending[order_id]
    if pending:
        logger.info("awaiting fill: {}", ", ".join(pending.values()))


def _cancel_stale_entry_orders(
    trading: object, pending: dict[str, str], order_timestamps: dict[str, float]
) -> None:
    """Cancel pending entry limit orders open longer than ENTRY_ORDER_CANCEL_TIMEOUT_SECONDS."""
    now = time.monotonic()
    for order_id, label in list(pending.items()):
        if not label.startswith("entry"):
            continue
        submitted_at = order_timestamps.get(order_id, now)
        age = now - submitted_at
        if age >= ENTRY_ORDER_CANCEL_TIMEOUT_SECONDS:
            ok = broker.cancel_order(trading, order_id)
            if ok:
                logger.info(
                    "CANCELLED stale entry order (age={:.0f}s): {} (order {})",
                    age,
                    label,
                    order_id,
                )
                del pending[order_id]
                order_timestamps.pop(order_id, None)
            else:
                logger.warning(
                    "failed to cancel stale entry order: {} (order {})", label, order_id
                )


def run_agentic_loop(
    graph: TradingGraph,
    *,
    execute: bool = False,
    loop: bool = False,
    interval: int = settings.LOOP_INTERVAL_SECONDS,
    llm: bool = False,
) -> None:
    """Continuous or single-cycle multi-agent live trading loop."""
    config = broker.load_config()
    trading, _, _ = broker.build_clients(config)

    if execute:
        logger.warning("ARMED: Multi-Agent paper order submission is ENABLED")
    else:
        logger.info("DRY RUN: Multi-Agent simulation only (no live orders submitted)")

    pending: dict[str, str] = {}
    order_timestamps: dict[str, float] = {}

    try:
        pending = broker.fetch_open_orders(trading)
        seed_ts = time.monotonic()
        for oid in pending:
            order_timestamps[oid] = seed_ts
    except broker.BrokerError as error:
        logger.warning("could not list open orders at startup: {}", error)

    if pending:
        logger.info("watching existing open orders for fills: {}", ", ".join(pending.values()))

    while True:
        if execute:
            _cancel_stale_entry_orders(trading, pending, order_timestamps)

        final_state = run_agentic_cycle(graph, execute=execute, use_llm=llm)
        log_agentic_cycle_summary(final_state)

        new = _extract_new_orders(final_state)
        now_ts = time.monotonic()
        for oid in new:
            order_timestamps[oid] = now_ts
        pending.update(new)

        if new:
            deadline = time.monotonic() + FILL_POLL_TIMEOUT_SECONDS
            while True:
                _check_fills(trading, pending)
                if not (new.keys() & pending.keys()) or time.monotonic() >= deadline:
                    break
                time.sleep(FILL_POLL_INTERVAL_SECONDS)

        if not loop:
            _check_fills(trading, pending)
            if pending:
                logger.info("cycle finished; open orders will be watched in future cycles")
            break

        logger.info(
            "Sleeping {}s until next autonomous bar cycle (press Ctrl+C to stop)...", interval
        )
        time.sleep(interval)
        _check_fills(trading, pending)


# ═══════════════════════════════════════════════════════════════════
# CLI Commands
# ═══════════════════════════════════════════════════════════════════

@app.command()
def run(
    execute: bool = typer.Option(
        False, "--execute", help="Actually submit paper orders to Alpaca (dry run otherwise)."
    ),
    loop: bool = typer.Option(
        False, "--loop", help="Run forever on an interval in a continuous live market loop."
    ),
    interval: int = typer.Option(
        settings.LOOP_INTERVAL_SECONDS, "--interval", help="Seconds between cycles with --loop."
    ),
    llm: bool = typer.Option(
        False, "--llm", help="Enable Google Gemini multi-turn reasoning and advisories."
    ),
) -> None:
    """Run autonomous multi-agent trading cycle (or loop). Paper only; dry run unless --execute."""
    setup_logging()
    logger.info("=== Starting Multi-Agent Trading System ===")
    agents = create_agents()
    graph = TradingGraph(agents)
    run_agentic_loop(graph, execute=execute, loop=loop, interval=interval, llm=llm)


@app.command()
def live(
    interval: int = typer.Option(
        settings.LOOP_INTERVAL_SECONDS, "--interval", help="Seconds between cycles."
    ),
    llm: bool = typer.Option(
        False, "--llm", help="Enable Google Gemini multi-turn reasoning and advisories."
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt."
    ),
) -> None:
    """Launch continuous LIVE paper trading using the full autonomous Multi-Agent System."""
    setup_logging()
    if not yes:
        typer.confirm(
            "Start autonomous LIVE paper trading loop on Alpaca paper endpoint?",
            abort=True,
        )
    logger.info("=== PACA Multi-Agent System: LIVE PAPER TRADING ARMED ===")
    agents = create_agents()
    graph = TradingGraph(agents)
    run_agentic_loop(graph, execute=True, loop=True, interval=interval, llm=llm)


@app.command()
def account(
    export: bool = typer.Option(
        False, "--export", help="Also write the snapshot to logs/account.json."
    ),
) -> None:
    """Inspect account equity, options level, and active positions managed by the Multi-Agent System."""
    setup_logging()
    config = broker.load_config()
    trading, _, _ = broker.build_clients(config)
    state = broker.fetch_account_state(trading, config.symbols)
    spreads, warnings = pos_and_risk.pair_spreads(state.legs)
    open_risk = pos_and_risk.open_premium_at_risk(spreads)

    typer.echo(f"Account Equity: ${state.equity:,.2f} | Options Level: {state.options_level}")
    typer.echo(f"Open Premium at Risk: ${open_risk:,.2f}")
    typer.echo(f"Active Spreads: {len(spreads)}")
    for spread in spreads:
        typer.echo(
            f"  {spread.underlying} {spread.expiration} {spread.option_type} x{spread.qty} "
            f"long={spread.long_symbol} short={spread.short_symbol} debit=${spread.net_entry_debit}"
        )
    for warning in warnings:
        typer.echo(f"  WARNING: {warning}")

    if export:
        snapshot = {
            "generated_at": datetime.now(timezone.utc),
            "equity": state.equity,
            "options_level": state.options_level,
            "open_risk": open_risk,
            "spreads": [asdict(s) for s in spreads],
            "warnings": warnings,
            "unparsed_positions": list(state.unparsed_positions),
        }
        path = Path("logs") / "account.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(to_json_line(snapshot) + "\n", encoding="utf-8")
        typer.echo(f"Exported snapshot to {path}")


@app.command()
def status() -> None:
    """Display Multi-Agent System latency report, detected bottlenecks, and Trade Memory stats."""
    setup_logging()
    typer.echo("\n=== Multi-Agent System Status ===")
    typer.echo(performance_monitor.get_system_report())

    # Trade Memory Analytics
    trade_memory = TradeMemoryAgent()
    analytics = trade_memory._compute_performance_analytics()
    typer.echo("\n=== Trade Memory & Calibration Analytics ===")
    typer.echo(f"Total Trades Analyzed: {analytics.total_trades_analyzed}")
    typer.echo(f"Historical Win Rate:   {analytics.win_rate:.1%}")
    typer.echo(f"Profit Factor:         {analytics.profit_factor:.2f}")
    typer.echo(f"Average PnL:           ${analytics.average_pnl:+.2f}")
    typer.echo(f"Max Drawdown:          {analytics.max_drawdown_pct:.1%}")
    if analytics.recent_lessons:
        typer.echo("\nRecent Agent Post-Mortem Lessons:")
        for lesson in analytics.recent_lessons[-3:]:
            typer.echo(f"  • {lesson}")


@app.command()
def candidates() -> None:
    """Run Market Scanner Agent and display detected opportunities across whitelist."""
    setup_logging()
    scanner = MarketScannerAgent()
    state = AgentState(cycle_id="scan", timestamp=datetime.now(timezone.utc), dry_run=True)
    state = scanner.execute(state)
    typer.echo(f"\nMarket Scanner Opportunities ({len(state.opportunities)}):")
    for opp in state.opportunities:
        features = state.symbol_features.get(opp.symbol)
        rsi_str = f"{features.rsi:.1f}" if features and features.rsi is not None else "-"
        macd_str = f"{features.macd_hist:+.3f}" if features and features.macd_hist is not None else "-"
        typer.echo(
            f"  {opp.symbol:<5} {opp.direction:<4} Conf: {opp.confidence:.2f} | "
            f"RSI: {rsi_str:<5} MACD: {macd_str:<7} | Reason: {opp.reason}"
        )


@app.command()
def cancel(
    order_id: str = typer.Argument(
        None, help="Order ID to cancel; omit to cancel ALL open orders."
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt."),
) -> None:
    """Cancel open orders on the Alpaca paper account (all or one by id)."""
    setup_logging()
    config = broker.load_config()
    trading, _, _ = broker.build_clients(config)
    open_orders = broker.fetch_open_orders(trading)
    if not open_orders:
        typer.echo("No open orders found.")
        return
    targets = {order_id: open_orders[order_id]} if order_id else open_orders
    for oid, label in targets.items():
        typer.echo(f"  {oid}  {label}")
    if not yes:
        typer.confirm(f"Cancel {len(targets)} open order(s)?", abort=True)
    for oid, label in targets.items():
        try:
            broker.cancel_order_raising(trading, oid)
            typer.echo(f"Cancel requested: {oid} ({label})")
        except broker.BrokerError as error:
            typer.echo(f"FAIL {oid}: {error}")


@app.command()
def test_performance():
    """Run a single cycle and show performance metrics."""
    setup_logging()
    logger.info("=== Multi-Agent Performance Test ===")
    agents = create_agents()
    graph = TradingGraph(agents)
    final_state = run_agentic_cycle(graph, execute=False)
    log_agentic_cycle_summary(final_state)
    logger.info("\n" + performance_monitor.get_system_report())


@app.command()
def benchmark(cycles: int = typer.Option(5, "--cycles", "-n", help="Number of cycles to run")):
    """Run multiple cycles to benchmark performance."""
    setup_logging()
    logger.info(f"=== Multi-Agent Benchmark ({cycles} cycles) ===")
    agents = create_agents()
    graph = TradingGraph(agents)
    total_time = 0.0

    for i in range(cycles):
        start_time = datetime.now(timezone.utc)
        final_state = run_agentic_cycle(graph, execute=False)
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        total_time += elapsed
        logger.info(f"Cycle {i+1}/{cycles} completed in {elapsed:.3f}s")

    avg_time = total_time / max(cycles, 1)
    logger.info("\n=== Benchmark Summary ===")
    logger.info(f"Total cycles: {cycles}")
    logger.info(f"Total time:   {total_time:.3f}s")
    logger.info(f"Average time: {avg_time:.3f}s per cycle")
    logger.info(f"Throughput:   {60.0 / avg_time:.1f} cycles/min")
    logger.info("\n" + performance_monitor.get_system_report())


@app.command()
def analyze_bottlenecks():
    """Analyze agent latency and bottleneck detection."""
    setup_logging()
    logger.info("=== Bottleneck Analysis ===")
    bottlenecks = performance_monitor.get_bottlenecks()
    if bottlenecks:
        logger.warning(f"⚠️ Identified Bottlenecks:")
        for bottleneck in bottlenecks:
            logger.warning(f"  {bottleneck}")
    else:
        logger.info("✅ No active performance bottlenecks identified.")
    logger.info("\n" + performance_monitor.get_system_report())


@app.command()
def compare_modes():
    """Compare multi-agent vs simulated single-agent cycle execution."""
    setup_logging()
    logger.info("=== Performance Comparison: Multi-Agent vs Single-Agent ===")
    agents = create_agents()
    graph = TradingGraph(agents)

    start_time = datetime.now(timezone.utc)
    final_state = run_agentic_cycle(graph, execute=False)
    multi_agent_time = (datetime.now(timezone.utc) - start_time).total_seconds()

    logger.info(f"Multi-Agent cycle time: {multi_agent_time:.3f}s")
    logger.info(
        f"Multi-Agent advantages: 7 specialized perspectives, independent risk gating, "
        f"real-time PnL/DTE position management, continuous calibration and trade memory."
    )


if __name__ == "__main__":
    app()