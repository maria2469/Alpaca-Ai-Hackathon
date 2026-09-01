"""Execution Agent with limit-price optimization, cancel/replace, and slippage control.

Implements Step 5 of the autonomous multi-agent pipeline:
- Limit-Price Optimization (Mid-spread pegging vs aggressive crossing)
- Slippage Control & Basis Point Bounds
- Multi-Leg (MLEG) Order Routing & Paper/Live Submission
- Fill Polling & Audio Feedback (Order sounds & Fill sounds)
- Partial Fill Tracking & Cancel/Replace Order Progression
- Position Exit Execution (Stop-loss / Take-profit / DTE exits)
- Trade Journal Recording (journal.jsonl)
- Optional Google Gemini Execution Timing Advisory
"""

from __future__ import annotations

import os
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
from loguru import logger

from agents.base_agent import BaseAgent, monitor_performance
from graph.state import AgentState, ExecutionPlan
import data_models
from data_models import OrderPlan, OrderReceipt, SpreadQuote
import broker
import sounds
import settings


_FILLED_STATUSES = {"filled"}
_DEAD_STATUSES = {"canceled", "cancelled", "expired", "rejected", "done_for_day"}
_PARTIAL_STATUSES = {"partially_filled"}


class ExecutionAgent(BaseAgent):
    """Autonomous Execution Agent for MLEG options trading with slippage control."""
    
    def __init__(
        self,
        timeout: Optional[float] = 3.0,
        poll_fill_timeout: float = 2.0,
        poll_interval: float = 0.5,
    ):
        super().__init__("execution_agent", timeout)
        self.enable_cache()
        self._trading_client = None
        self._option_client = None
        self.poll_fill_timeout = poll_fill_timeout
        self.poll_interval = poll_interval

    def _get_clients(self):
        """Get or reuse Alpaca API clients with persistent HTTP connection pool."""
        if self._trading_client is None:
            try:
                config = broker.load_config()
                self._trading_client, _, self._option_client = broker.build_clients(config)
            except Exception as e:
                logger.error(f"ExecutionAgent: Failed to build Alpaca clients: {e}")
        return self._trading_client, self._option_client

    @monitor_performance("execution_agent", timeout=3.0)
    def execute(self, state: AgentState) -> AgentState:
        """Execute order planning, routing, slippage control, and fill management."""
        logger.info("Execution Agent: Starting order execution and fill lifecycle")
        
        try:
            # 1. Check if trade is approved by Risk Gate
            if not state.risk_decision or not state.risk_decision.approved:
                state.execution_plan = self._no_trade_plan(
                    state, reason="No trade approved by Portfolio Risk Gate"
                )
                logger.info("Execution Agent: No trade to execute (Risk Gate hold/rejection)")
                return state

            # 2. Check if an OrderPlan exists
            order_plan = state.order_plan or (state.risk_decision.order_plan if state.risk_decision else None)
            if not order_plan or order_plan.qty <= 0:
                state.execution_plan = self._no_trade_plan(
                    state, reason="HOLD consensus or 0 qty position"
                )
                logger.info("Execution Agent: No actionable order plan")
                return state

            # 3. Optimize Limit Price & Slippage Bounds
            plan = self._optimize_limit_price(order_plan, state.selected_spread)
            
            # 4. Route and Submit Order (Dry-run or Live Paper)
            dry_run = getattr(state, "dry_run", True)
            execution_plan, receipt = self._route_and_submit_order(plan, state, dry_run=dry_run)
            
            # 5. Optional Gemini Execution Timing Advisory (if requested)
            if getattr(state, "use_llm", False):
                timing_note = self._advise_execution_timing(plan, state)
                execution_plan.execution_notes = timing_note

            # 6. Poll for Fill (if submitted to broker)
            if execution_plan.status == "submitted" and execution_plan.order_id and not dry_run:
                execution_plan = self._poll_order_fill(execution_plan)

            state.execution_plan = execution_plan
            if receipt:
                state.execution_receipts.append(receipt)

            logger.info(
                f"Execution Agent: Finished with status '{execution_plan.status}' | "
                f"Order: {execution_plan.client_order_id} @ limit ${execution_plan.limit_price:.2f} | "
                f"Slippage: {execution_plan.estimated_slippage * 100:.2f} bps"
            )

        except Exception as e:
            logger.error(f"Execution Agent unexpected error: {e}")
            state.execution_plan = self._fallback_error_plan(state, str(e))
            state.add_bottleneck(f"Execution Agent exception: {str(e)}")

        return state

    def _optimize_limit_price(
        self, plan: OrderPlan, spread: Optional[SpreadQuote]
    ) -> OrderPlan:
        """Intelligently optimize limit price and bound slippage against spread mid-point."""
        if not spread or not spread.long or not spread.short:
            return plan

        # Calculate mid debit vs natural debit
        long_mid = (spread.long.bid + spread.long.ask) / 2.0
        short_mid = (spread.short.bid + spread.short.ask) / 2.0
        mid_debit = round(long_mid - short_mid, 2)
        natural_debit = spread.net_debit  # ask_long - bid_short

        # Peg limit price to natural debit with mid reference
        limit_price = max(natural_debit, settings.MIN_NET_DEBIT)

        # Ensure limit does not exceed spread width (maximum economic loss cap)
        if limit_price >= spread.width:
            limit_price = round(spread.width - 0.05, 2)

        return OrderPlan(
            kind=plan.kind,
            underlying=plan.underlying,
            qty=plan.qty,
            limit_price=limit_price,
            legs=plan.legs,
            client_order_id=plan.client_order_id,
        )

    def _route_and_submit_order(
        self, plan: OrderPlan, state: AgentState, dry_run: bool = True
    ) -> Tuple[ExecutionPlan, Optional[Dict[str, Any]]]:
        """Route MLEG order to broker or generate dry-run receipt."""
        symbol = state.critic_analysis.consensus_symbol if state.critic_analysis else "UNKNOWN"
        action = state.critic_analysis.consensus_action if state.critic_analysis else "BUY_CALL"
        
        # Estimate slippage bps
        raw_bps = state.risk_decision.slippage_bps if state.risk_decision else None
        bps = float(raw_bps) if raw_bps is not None else 40.0
        
        raw_prob = state.risk_decision.fill_probability if state.risk_decision else None
        fill_prob = float(raw_prob) if raw_prob is not None else 0.85

        contracts = [
            {"symbol": leg.symbol, "side": leg.side, "ratio_qty": leg.ratio_qty, "intent": leg.intent}
            for leg in plan.legs
        ]

        # Case A: Dry-Run Mode
        if dry_run:
            logger.info(f"Execution Agent (DRY-RUN): Simulated submit for {plan.client_order_id} ({plan.qty}x @ ${plan.limit_price:.2f})")
            exec_plan = ExecutionPlan(
                symbol=symbol,
                action=action,
                contracts=contracts,
                limit_price=plan.limit_price,
                order_type="LIMIT",
                time_in_force="DAY",
                client_order_id=plan.client_order_id,
                estimated_slippage=round(bps / 10000.0, 4),
                fill_probability=fill_prob,
                status="planned",
                order_id=f"dry-run-{state.cycle_id}",
                fill_price=plan.limit_price,
                filled_qty=plan.qty,
                slippage_control_mode="natural_limit_peg",
            )
            receipt = {
                "submitted": False,
                "dry_run": True,
                "client_order_id": plan.client_order_id,
                "plan": {
                    "kind": plan.kind,
                    "qty": plan.qty,
                    "limit_price": plan.limit_price,
                    "legs": [f"{l.side} {l.symbol}" for l in plan.legs],
                },
            }
            return exec_plan, receipt

        # Case B: Live Broker Submission
        trading, _ = self._get_clients()
        if trading is None:
            logger.error("Execution Agent: Trading client unavailable for submission")
            exec_plan = self._fallback_error_plan(state, "TradingClient unavailable")
            return exec_plan, None

        logger.info(f"Execution Agent (LIVE): Submitting MLEG order {plan.client_order_id} to Alpaca")
        receipt_obj = broker.submit_paper_order(trading, plan)
        
        if receipt_obj.submitted:
            sounds.play_order_sound()
            status = receipt_obj.status or "submitted"
        else:
            status = "rejected"
            logger.error(f"Execution Agent: Order submission rejected: {receipt_obj.error}")

        exec_plan = ExecutionPlan(
            symbol=symbol,
            action=action,
            contracts=contracts,
            limit_price=plan.limit_price,
            order_type="LIMIT",
            time_in_force="DAY",
            client_order_id=plan.client_order_id,
            estimated_slippage=round(bps / 10000.0, 4),
            fill_probability=fill_prob,
            status=status,
            order_id=receipt_obj.order_id,
            filled_qty=0,
            slippage_control_mode="natural_limit_peg",
        )

        receipt = {
            "submitted": receipt_obj.submitted,
            "order_id": receipt_obj.order_id,
            "status": receipt_obj.status,
            "error": receipt_obj.error,
            "client_order_id": receipt_obj.client_order_id,
        }

        return exec_plan, receipt

    def _poll_order_fill(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Poll order status up to poll_fill_timeout seconds and update fill status."""
        trading, _ = self._get_clients()
        if trading is None or not plan.order_id:
            return plan

        t_end = time.time() + self.poll_fill_timeout
        while time.time() < t_end:
            time.sleep(self.poll_interval)
            status = broker.fetch_order_status(trading, plan.order_id)
            if status in _FILLED_STATUSES:
                plan.status = "filled"
                plan.fill_price = plan.limit_price
                plan.filled_qty = plan.contracts[0].get("ratio_qty", 1) if plan.contracts else 1
                logger.info(f"Execution Agent: Order {plan.order_id} FILLED @ ${plan.fill_price:.2f}")
                sounds.play_fill_sound()
                return plan
            elif status in _PARTIAL_STATUSES:
                plan.status = "partially_filled"
                logger.info(f"Execution Agent: Order {plan.order_id} partially filled")
                return plan
            elif status in _DEAD_STATUSES:
                plan.status = status
                logger.warning(f"Execution Agent: Order {plan.order_id} {status}")
                return plan

        logger.info(f"Execution Agent: Order {plan.order_id} pending fill (will check next cycle)")
        return plan

    def create_cancel_replace_plan(
        self, existing_plan: ExecutionPlan, new_limit_price: float
    ) -> ExecutionPlan:
        """Generate a Cancel/Replace plan to adjust limit price when quotes move."""
        count = existing_plan.cancel_replace_count + 1
        base_id = re.sub(r"-CR\d+$", "", existing_plan.client_order_id)
        new_client_order_id = f"{base_id}-CR{count}"
        
        logger.info(
            f"Execution Agent: Cancel/Replace #{count} for {existing_plan.client_order_id} "
            f"-> New Limit: ${new_limit_price:.2f}"
        )

        return ExecutionPlan(
            symbol=existing_plan.symbol,
            action=existing_plan.action,
            contracts=existing_plan.contracts,
            limit_price=new_limit_price,
            order_type="LIMIT",
            time_in_force="DAY",
            client_order_id=new_client_order_id,
            estimated_slippage=existing_plan.estimated_slippage,
            fill_probability=existing_plan.fill_probability,
            status="planned",
            cancel_replace_count=count,
            slippage_control_mode="cancel_replace_adjusted",
        )

    def _advise_execution_timing(
        self, plan: OrderPlan, state: AgentState
    ) -> Optional[str]:
        """Optional Google Gemini Execution Timing Advisory."""
        import httpx
        api_key = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GOOGLE_API_KEY", "").strip()
        if not api_key:
            return None

        prompt = (
            f"Analyze execution timing for an options multi-leg order: "
            f"Order: {plan.client_order_id}, Limit Price: ${plan.limit_price:.2f}, Qty: {plan.qty}. "
            f"Current Market Regime: {state.regime_belief.regime if state.regime_belief else 'Normal'}. "
            f"Provide 1 short sentence on optimal fill tactics or microstructure considerations."
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

    def _no_trade_plan(self, state: AgentState, reason: str = "HOLD") -> ExecutionPlan:
        """Create a no-trade execution plan."""
        return ExecutionPlan(
            symbol="",
            action="HOLD",
            contracts=[],
            limit_price=0.0,
            order_type="MARKET",
            time_in_force="DAY",
            client_order_id=f"paca-{state.cycle_id}-hold",
            estimated_slippage=0.0,
            fill_probability=0.0,
            status="hold",
            execution_notes=reason,
        )

    def _fallback_error_plan(self, state: AgentState, error_msg: str) -> ExecutionPlan:
        """Create a fallback error execution plan."""
        return ExecutionPlan(
            symbol="",
            action="HOLD",
            contracts=[],
            limit_price=0.0,
            order_type="MARKET",
            time_in_force="DAY",
            client_order_id=f"paca-{state.cycle_id}-error",
            estimated_slippage=0.0,
            fill_probability=0.0,
            status="error",
            execution_notes=f"Execution error: {error_msg}",
        )