"""Real-Time Position Manager Agent with PnL tracking, DTE time stop, profit targets, and thesis invalidation.

Implements Step 6 of the autonomous multi-agent pipeline:
- Real-Time PnL, Mark-to-Market, and Greek Sensitivity Tracking
- Time Stop (DTE Expiry Exit <= settings.EXIT_DTE)
- Profit Target Take-Profit (net_mark >= settings.TAKE_PROFIT_MULT * entry_debit)
- Stop-Loss Protection (net_mark <= settings.STOP_FRACTION * entry_debit)
- Thesis Invalidation & Opposing Technical Event Reversal
- Momentum Degradation & IV Regime Shift Detection
- Exit OrderPlan Construction & MLEG Order Execution
- Optional Google Gemini Position Health & Thesis Invalidation Advisory
"""

from __future__ import annotations

import os
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
from loguru import logger

from agents.base_agent import BaseAgent, monitor_performance
from graph.state import (
    AgentState,
    ManagedPosition,
    PositionManagerReport,
)
import data_models
from data_models import OpenSpread, LegQuote, ExitDecision, OrderPlan
import pos_and_risk
import options_screener
import broker
import sounds
import settings


_RECENT_EXITS: Dict[str, float] = {}


class PositionManagerAgent(BaseAgent):
    """Real-time position management agent with mechanical exits and momentum health tracking."""
    
    def __init__(self, timeout: Optional[float] = 3.0):
        super().__init__("position_manager", timeout)
        self.enable_cache()
        self._trading_client = None
        self._option_client = None

    def _get_clients(self):
        """Get or reuse Alpaca API clients with persistent HTTP connection pool."""
        if self._trading_client is None:
            try:
                config = broker.load_config()
                self._trading_client, _, self._option_client = broker.build_clients(config)
            except Exception as e:
                logger.error(f"PositionManagerAgent: Failed to build Alpaca clients: {e}")
        return self._trading_client, self._option_client

    @monitor_performance("position_manager", timeout=3.0)
    def execute(self, state: AgentState) -> AgentState:
        """Evaluate all open positions, monitor PnL/Greeks, and trigger mechanical/signal exits."""
        logger.info("Position Manager Agent: Starting real-time position evaluation")
        
        try:
            report = self._evaluate_open_positions(state)
            state.position_report = report
            state.active_positions = report.managed_positions

            if report.exits_triggered:
                logger.warning(
                    f"Position Manager: {len(report.exits_triggered)} exit(s) triggered: "
                    f"{[f'{p.spread_label} ({p.exit_reason})' for p in report.exits_triggered]}"
                )
                self._execute_exits(report.exits_triggered, state)
            else:
                logger.info(
                    f"Position Manager: {report.total_positions} active position(s) healthy | "
                    f"Total Risk: ${report.total_open_risk:.2f} | Unrealized PnL: ${report.total_unrealized_pnl:+.2f}"
                )

        except Exception as e:
            logger.error(f"Position Manager Agent unexpected error: {e}")
            state.position_report = PositionManagerReport(
                total_positions=0,
                total_open_risk=0.0,
                total_unrealized_pnl=0.0,
            )
            state.add_bottleneck(f"Position Manager exception: {str(e)}")

        return state

    def _execute_exits(self, exits: List[ManagedPosition], state: AgentState) -> None:
        """Submit MLEG exit orders for triggered positions (live paper or dry run)."""
        dry_run = getattr(state, "dry_run", True)
        trading, _ = self._get_clients()

        for pos in exits:
            if not pos.exit_plan:
                continue

            now_ts = time.monotonic()
            _RECENT_EXITS[pos.underlying] = now_ts
            try:
                import cli
                cli._RECENT_EXITS[pos.underlying] = now_ts
            except Exception:
                pass

            if dry_run:
                logger.info(
                    f"Position Manager (DRY-RUN): Simulated exit for {pos.spread_label} "
                    f"({pos.exit_reason}) @ limit ${pos.exit_plan.limit_price:.2f}"
                )
                state.execution_receipts.append({
                    "submitted": False,
                    "dry_run": True,
                    "kind": "exit",
                    "spread": pos.spread_label,
                    "reason": pos.exit_reason,
                    "client_order_id": pos.exit_plan.client_order_id,
                    "limit_price": pos.exit_plan.limit_price,
                    "qty": pos.exit_plan.qty,
                })
            else:
                if trading is None:
                    logger.error(f"Position Manager: Trading client unavailable for exit {pos.spread_label}")
                    continue
                logger.info(
                    f"Position Manager (LIVE): Submitting exit order {pos.exit_plan.client_order_id} "
                    f"for {pos.spread_label} ({pos.exit_reason})"
                )
                receipt = broker.submit_paper_order(trading, pos.exit_plan)
                if receipt.submitted:
                    sounds.play_order_sound()
                    logger.info(f"Position Manager: Exit order submitted: {receipt.order_id} ({receipt.status})")
                else:
                    logger.error(f"Position Manager: Exit order rejected: {receipt.error}")
                state.execution_receipts.append({
                    "submitted": receipt.submitted,
                    "dry_run": False,
                    "kind": "exit",
                    "spread": pos.spread_label,
                    "reason": pos.exit_reason,
                    "order_id": receipt.order_id,
                    "client_order_id": pos.exit_plan.client_order_id,
                    "limit_price": pos.exit_plan.limit_price,
                    "qty": pos.exit_plan.qty,
                    "status": receipt.status,
                    "error": receipt.error,
                })

    def _evaluate_open_positions(
        self, state: AgentState, mock_account: Optional[data_models.AccountState] = None
    ) -> PositionManagerReport:
        """Fetch open spreads, compute PnL/Greeks, and evaluate exit rules."""
        trading, option_data = self._get_clients()
        today = datetime.utcnow().date()
        
        # 1. Use pre-fetched account state from Market Scanner (zero duplicate Alpaca calls).
        # Fall back to live fetch only if scanner didn't cache it (e.g., scanner failed).
        account = mock_account or state.account_state
        if account is None:
            if trading is not None:
                try:
                    account = broker.fetch_account_state(trading, settings.SYMBOLS)
                    logger.debug("Position Manager: account_state not cached — fetched live")
                except Exception as e:
                    logger.warning(f"Position Manager: Could not fetch account state: {e}")
                    account = None

        if account is None or not account.legs:
            return PositionManagerReport(
                total_positions=0,
                total_open_risk=0.0,
                total_unrealized_pnl=0.0,
                managed_positions=[],
                exits_triggered=[],
            )

        # 2. Pair held positions into vertical spreads
        spreads, _ = pos_and_risk.pair_spreads(account.legs)
        if not spreads:
            return PositionManagerReport(
                total_positions=0,
                total_open_risk=0.0,
                total_unrealized_pnl=0.0,
                managed_positions=[],
                exits_triggered=[],
            )

        # 3. Batch fetch option snapshots for all leg symbols
        leg_symbols = [s for sp in spreads for s in (sp.long_symbol, sp.short_symbol)]
        snapshots = {}
        if option_data is not None and leg_symbols:
            try:
                snapshots = broker.fetch_option_snapshots(option_data, leg_symbols)
            except Exception as e:
                logger.warning(f"Position Manager: Snapshot fetch failed: {e}")

        managed_list: List[ManagedPosition] = []
        exits_list: List[ManagedPosition] = []
        total_risk = 0.0
        total_pnl = 0.0

        # 4. Evaluate each open spread
        for spread in spreads:
            pos_cost = (spread.net_entry_debit or 0.0) * spread.qty * 100.0
            total_risk += pos_cost

            long_q = broker.leg_quote_from_snapshot(
                spread.long_symbol, 0.0, snapshots.get(spread.long_symbol), None
            )
            short_q = broker.leg_quote_from_snapshot(
                spread.short_symbol, 0.0, snapshots.get(spread.short_symbol), None
            )

            # Check opposing technical events from Market Scanner
            features = state.symbol_features.get(spread.underlying)
            opposing = False
            if features and features.events:
                opposing = pos_and_risk.opposing_event_fired(spread, features.events)

            # Check deterministic exit decision
            exit_decision = pos_and_risk.exit_decision(
                spread,
                long_q,
                short_q,
                today,
                opposing_event=opposing,
            )

            # Check momentum degradation / RSI breakdown
            momentum_reason = self._check_momentum_degradation(spread, features)
            if not exit_decision and momentum_reason:
                net_mark = pos_and_risk._net_mark(long_q, short_q)
                exit_decision = ExitDecision(spread=spread, reason=momentum_reason, net_mark=net_mark)

            # Mark to market and PnL math
            net_mark = exit_decision.net_mark if exit_decision else pos_and_risk._net_mark(long_q, short_q)
            unrealized_pnl = None
            pnl_pct = None
            if net_mark is not None and spread.net_entry_debit is not None:
                unrealized_pnl = round((net_mark - spread.net_entry_debit) * spread.qty * 100.0, 2)
                pnl_pct = round(((net_mark - spread.net_entry_debit) / max(spread.net_entry_debit, 0.01)) * 100.0, 1)
                total_pnl += unrealized_pnl

            dte = (spread.expiration - today).days
            label = f"{spread.underlying} {spread.expiration} {spread.option_type} x{spread.qty}"

            # Net Greeks estimation
            greeks = self._estimate_position_greeks(spread, long_q, short_q)

            # Construct exit plan if exit triggered
            exit_plan = None
            if exit_decision is not None:
                exit_plan = options_screener.build_exit_plan(
                    spread, long_q, short_q, state.cycle_id or "exit"
                )

            # Optional Gemini thesis health review
            thesis_note = None
            if getattr(state, "use_llm", False):
                thesis_note = self._review_position_thesis_llm(spread, pnl_pct, features)

            managed_pos = ManagedPosition(
                spread_label=label,
                underlying=spread.underlying,
                expiration=spread.expiration,
                option_type=spread.option_type,
                qty=spread.qty,
                entry_debit=spread.net_entry_debit,
                current_mark=round(net_mark, 2) if net_mark is not None else None,
                unrealized_pnl=unrealized_pnl,
                pnl_pct=pnl_pct,
                dte=dte,
                greeks=greeks,
                exit_triggered=exit_decision is not None,
                exit_reason=exit_decision.reason if exit_decision else None,
                exit_plan=exit_plan,
                thesis_notes=thesis_note,
            )

            managed_list.append(managed_pos)
            if exit_decision is not None:
                exits_list.append(managed_pos)

        return PositionManagerReport(
            total_positions=len(managed_list),
            total_open_risk=round(total_risk, 2),
            total_unrealized_pnl=round(total_pnl, 2),
            managed_positions=managed_list,
            exits_triggered=exits_list,
        )

    def _check_momentum_degradation(
        self, spread: OpenSpread, features: Optional[data_models.SymbolFeatures]
    ) -> Optional[str]:
        """Check for severe momentum breakdown against open position."""
        if not features:
            return None

        # If holding CALL and RSI drops below oversold panic (e.g. RSI < 30) with bearish MACD
        if spread.option_type == "C":
            if features.rsi is not None and features.rsi < 28.0 and features.macd_hist is not None and features.macd_hist < -0.30:
                return "momentum_breakdown"
        
        # If holding PUT and RSI spikes above overbought (e.g. RSI > 72) with bullish MACD
        if spread.option_type == "P":
            if features.rsi is not None and features.rsi > 72.0 and features.macd_hist is not None and features.macd_hist > 0.30:
                return "momentum_reversal"

        return None

    def _estimate_position_greeks(
        self, spread: OpenSpread, long_q: Optional[LegQuote], short_q: Optional[LegQuote]
    ) -> Dict[str, float]:
        """Estimate position Greeks from quotes or theoretical spread delta/theta."""
        d_long = getattr(long_q, "delta", None) or (0.50 if spread.option_type == "C" else -0.50)
        d_short = getattr(short_q, "delta", None) or (0.35 if spread.option_type == "C" else -0.35)
        net_delta = round((d_long - d_short) * spread.qty * 100.0, 2)

        t_long = getattr(long_q, "theta", None) or -0.04
        t_short = getattr(short_q, "theta", None) or -0.02
        net_theta = round((t_long - t_short) * spread.qty * 100.0, 2)

        return {
            "net_delta": net_delta,
            "net_theta": net_theta,
        }

    def _review_position_thesis_llm(
        self, spread: OpenSpread, pnl_pct: Optional[float], features: Optional[data_models.SymbolFeatures]
    ) -> Optional[str]:
        """Optional Google Gemini LLM Position Health Assessment."""
        import httpx
        api_key = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GOOGLE_API_KEY", "").strip()
        if not api_key:
            return None

        pnl_str = f"{pnl_pct:+.1f}%" if pnl_pct is not None else "Unknown"
        rsi_str = f"{features.rsi:.1f}" if features and features.rsi else "N/A"

        prompt = (
            f"Review open options position: {spread.underlying} {spread.expiration} {spread.option_type} spread. "
            f"Current Unrealized PnL: {pnl_str}, Underlying RSI: {rsi_str}. "
            f"Provide 1 concise sentence on whether this position remains technically sound or requires attention."
        )

        try:
            resp = httpx.post(
                "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                json={
                    "model": "gemini-1.5-flash",
                    "messages": [{"role": "user", "content": prompt}],
                },
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=2.0,
            )
            if resp.status_code == 200:
                body = resp.json()
                return body["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
        return None
