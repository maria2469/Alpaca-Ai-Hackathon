"""Portfolio Risk Gate & EV Contract Optimizer Agent.

Implements Step 4 of the autonomous multi-agent pipeline:
- Position Risk & 4-Tier Fractional Portfolio Equity Sizing (pos_and_risk.py)
- Portfolio Greeks Aggregation (Delta, Gamma, Theta, Vega)
- Correlated Sector / Index Exposure Management (Tech Cluster vs Indices)
- Daily Drawdown (DD) Protection Circuit Breaker
- Max Concurrent Active Spreads Cap
- Contract Selection & Expected Value (EV) Optimization (options_screener.py)
- Alpaca Multi-Leg (MLEG) Order Plan Construction
- Optional Google Gemini Event/News Risk Advisory
"""

from __future__ import annotations

import time
import math
import os
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, date
from loguru import logger

from agents.base_agent import BaseAgent, monitor_performance
from graph.state import AgentState, RiskDecision
import data_models
from data_models import SpreadQuote, OrderPlan, LegQuote, OpenSpread
import options_screener
import pos_and_risk
import broker
import settings


# Correlated Asset Clusters for Cross-Asset Exposure Management
CLUSTERS: Dict[str, Set[str]] = {
    "TECH_CLUSTER": {"NVDA", "MSFT", "AAPL", "AMZN", "TSLA", "QQQ"},
    "BROAD_INDEX": {"SPY"},
    "SMALL_CAP": {"IWM"},
}

MAX_CORRELATED_CLUSTER_FRACTION: float = 0.04  # Max 4.0% of equity in any single correlated cluster
MAX_DAILY_DRAWDOWN_FRACTION: float = 0.025     # Max 2.5% daily drawdown circuit breaker
MAX_CONCURRENT_SPREADS: int = 5                # Max 5 concurrent active spread positions
MAX_PORTFOLIO_DELTA: float = 50.0              # Max portfolio directional delta limit


class RiskGateAgent(BaseAgent):
    """Portfolio Risk Gate Agent with Greeks, correlation, drawdown, and 4-tier risk caps."""
    
    def __init__(self, timeout: Optional[float] = 3.0):
        super().__init__("risk_gate", timeout)
        self.enable_cache()
        self._trading_client = None
        self._option_client = None
        self._last_cycle_id: str = ""
        self._starting_equity: Optional[float] = None
        self._starting_equity_date: Optional[date] = None
        # TTL cache: (symbol, direction) -> (timestamp, result_tuple)
        # Prevents re-fetching the same option chain within 30 seconds.
        self._option_chain_cache: Dict[str, tuple] = {}

    def _get_clients(self):
        """Get or reuse Alpaca API clients with persistent HTTP connection pool."""
        if self._trading_client is None:
            try:
                config = broker.load_config()
                self._trading_client, _, self._option_client = broker.build_clients(config)
            except Exception as e:
                logger.error(f"RiskGateAgent: Failed to build Alpaca clients: {e}")
        return self._trading_client, self._option_client

    def _track_daily_drawdown(self, current_equity: float, today: date) -> float:
        """Track daily drawdown from opening / starting equity."""
        if self._starting_equity_date != today or self._starting_equity is None:
            self._starting_equity = current_equity
            self._starting_equity_date = today
            return 0.0
        
        if self._starting_equity <= 0:
            return 0.0
        
        # Drawdown as positive fraction: (peak - current) / peak
        dd = (self._starting_equity - current_equity) / self._starting_equity
        return max(round(dd, 4), 0.0)

    @monitor_performance("risk_gate", timeout=3.0)
    def execute(self, state: AgentState) -> AgentState:
        """Execute Portfolio Risk Gating and Contract Optimization."""
        logger.info("Portfolio Risk Gate: Starting comprehensive risk assessment")
        
        # Fast-path: return cached decision for same cycle
        if state.cycle_id and state.cycle_id == self._last_cycle_id and state.risk_decision:
            logger.info(f"Risk Gate: Using cached decision for cycle {state.cycle_id}")
            return state

        try:
            # Step 1: Check critic consensus action
            critic = state.critic_analysis
            if not critic or critic.consensus_action == "HOLD" or not critic.consensus_symbol:
                risk_decision = RiskDecision(
                    approved=True,
                    reason="HOLD consensus: No trade proposed, 0 capital at risk",
                    portfolio_risk=0.0,
                    greek_exposure={"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0},
                    position_size=0.0,
                )
                state.risk_decision = risk_decision
                self._last_cycle_id = state.cycle_id
                logger.info("Portfolio Risk Gate: APPROVED (HOLD - no capital deployed)")
                return state

            symbol = critic.consensus_symbol
            action = critic.consensus_action
            direction = "CALL" if action == "BUY_CALL" else "PUT"
            
            snapshot = state.market_data.get(symbol)
            spot = snapshot.spot if snapshot else None
            
            if spot is None:
                risk_decision = RiskDecision(
                    approved=False,
                    reason=f"Missing spot quote for consensus candidate {symbol}",
                    portfolio_risk=0.0,
                    greek_exposure={},
                    position_size=0.0,
                )
                state.risk_decision = risk_decision
                return state

            # Step 2: Screen Option Contracts & Compute EV
            spread, rejections, ev_metrics = self._screen_and_optimize_contract(
                state, symbol, direction, spot
            )

            if spread is None:
                risk_decision = RiskDecision(
                    approved=False,
                    reason=f"No acceptable spread found for {symbol} {direction} (Rejections: {rejections})",
                    portfolio_risk=0.0,
                    greek_exposure={},
                    position_size=0.0,
                    screen_rejections=rejections,
                )
                state.risk_decision = risk_decision
                logger.info(f"Portfolio Risk Gate: REJECTED - No acceptable spread for {symbol} {direction}")
                return state

            # Step 3: Run Full Portfolio Risk Assessment & Gating
            risk_decision = self._size_and_gate_position(
                state, spread, ev_metrics, rejections
            )
            
            # Step 4: Optional Gemini Event/News Risk Scan (if requested)
            if getattr(state, "use_llm", False):
                event_notes = self._scan_event_news_risk(symbol, direction, spread)
                risk_decision.event_risk_notes = event_notes

            state.risk_decision = risk_decision
            state.selected_spread = spread
            if risk_decision.order_plan:
                state.order_plan = risk_decision.order_plan

            self._last_cycle_id = state.cycle_id
            verdict = "APPROVED" if risk_decision.approved else "REJECTED"
            logger.info(
                f"Portfolio Risk Gate: {verdict} - Size: {risk_decision.position_size}x | "
                f"EV: ${ev_metrics.get('ev', 0):.2f} | Risk: ${risk_decision.portfolio_risk:.2f} | "
                f"Reason: {risk_decision.reason}"
            )

        except Exception as e:
            logger.error(f"Portfolio Risk Gate unexpected error: {e}")
            state.risk_decision = self._conservative_fallback_decision(f"Exception: {str(e)}")
            state.add_bottleneck(f"Risk Gate exception: {str(e)}")
        
        return state
    
    def _screen_and_optimize_contract(
        self,
        state: AgentState,
        symbol: str,
        direction: str,
        spot: float,
    ) -> Tuple[Optional[SpreadQuote], Dict[str, int], Dict[str, float]]:
        """Screen vertical spreads from live option chain and optimize EV, PnL & slippage.
        
        Results are cached per symbol+direction for 30 seconds to avoid redundant
        Alpaca API calls when the same candidate appears in back-to-back cycles.
        """
        cache_key = f"{symbol}:{direction}"
        cached = self._option_chain_cache.get(cache_key)
        if cached:
            ts, result = cached
            if time.monotonic() - ts < 30.0:
                logger.debug(f"Risk Gate: Option chain cache hit for {symbol} {direction}")
                return result
        trading, option_data = self._get_clients()
        rejections: Dict[str, int] = {}
        ev_metrics: Dict[str, float] = {}

        if trading is None or option_data is None:
            return None, {"client_error": 1}, ev_metrics

        try:
            # Synchronize clock with Alpaca server time
            try:
                clock = broker.fetch_clock(trading)
                clock_time = clock.server_time
                today = clock.server_time.date()
            except Exception:
                clock_time = datetime.utcnow()
                today = datetime.utcnow().date()

            # 1. Fetch available option contracts for underlying
            by_expiry = broker.fetch_contracts(trading, symbol, direction, spot, today)
            expirations = options_screener.pick_expirations(set(by_expiry.keys()), today)
            
            if not expirations:
                return None, {"no_eligible_expiries": 1}, ev_metrics

            # 2. Fetch live option snapshots
            contract_symbols = [
                info["symbol"] for exp in expirations for info in by_expiry[exp].values()
            ]
            snapshots = broker.fetch_option_snapshots(option_data, contract_symbols)

            # 3. Build quote chains
            chains: Dict[date, Dict[float, LegQuote]] = {}
            for exp in expirations:
                chains[exp] = {}
                for strike, info in by_expiry[exp].items():
                    sym = info["symbol"]
                    chains[exp][strike] = broker.leg_quote_from_snapshot(
                        sym, strike, snapshots.get(sym), info["open_interest"]
                    )

            # 4. Enumerate & select best spread
            spread, rejections = options_screener.select_spread(
                chains, direction, spot, symbol, clock_time
            )

            if spread is None:
                return None, rejections, ev_metrics

            # 5. Calculate Quantitative EV & Options Metrics
            max_profit = round((spread.width - spread.net_debit) * 100.0, 2)
            max_loss = round(spread.net_debit * 100.0, 2)
            reward_risk = round((spread.width - spread.net_debit) / max(spread.net_debit, 0.01), 2)
            
            # Base probability from Critic consensus modulated by moneyness / delta
            critic_prob = state.critic_analysis.consensus_probability if state.critic_analysis else 0.55
            delta_val = getattr(spread.long, "delta", None) or 0.50
            delta_mod = delta_val / 0.50
            win_prob = min(max(round(critic_prob * delta_mod, 3), 0.35), 0.85)

            # Expected Value: EV = (P_win * Max_Profit) - ((1 - P_win) * Max_Loss)
            ev = round((win_prob * max_profit) - ((1.0 - win_prob) * max_loss), 2)

            # Leg Slippage & Fill Probability
            long_bps = options_screener.quote_spread_bps(spread.long) if spread.long else 50.0
            short_bps = options_screener.quote_spread_bps(spread.short) if spread.short else 50.0
            combined_bps = round(long_bps + short_bps, 1)
            fill_prob = round(min(max(1.0 - (combined_bps / 500.0) * 0.25, 0.50), 0.98), 2)

            # Theta / IV effect
            theta_long = getattr(spread.long, "theta", None) or -0.04
            theta_short = getattr(spread.short, "theta", None) or -0.02
            net_theta = round(theta_long - theta_short, 4)

            ev_metrics = {
                "max_profit": max_profit,
                "max_loss": max_loss,
                "reward_risk": reward_risk,
                "win_prob": win_prob,
                "ev": ev,
                "combined_bps": combined_bps,
                "fill_prob": fill_prob,
                "net_theta": net_theta,
                "skew": round(spread.skew, 4),
            }

            result = spread, rejections, ev_metrics
            self._option_chain_cache[cache_key] = (time.monotonic(), result)
            return result

        except Exception as e:
            logger.warning(f"Error screening options for {symbol}: {e}")
            return None, {"screening_error": 1}, ev_metrics

    def _size_and_gate_position(
        self,
        state: AgentState,
        spread: SpreadQuote,
        ev_metrics: Dict[str, float],
        rejections: Dict[str, int],
        account_state: Optional[data_models.AccountState] = None,
    ) -> RiskDecision:
        """Run complete Portfolio Risk Gate checks, Greeks, Correlated Clusters, and 4-Tier Sizing."""
        trading, _ = self._get_clients()
        today = datetime.utcnow().date()
        
        # 1. Use pre-fetched account state from Market Scanner (zero duplicate Alpaca calls).
        # Fall back to live fetch only if scanner didn't cache it.
        if account_state is None:
            account_state = state.account_state  # Pre-fetched by MarketScannerAgent
        
        if account_state is None:
            logger.debug("Risk Gate: account_state not cached — fetching live (scanner may have failed)")
            try:
                account_state = broker.fetch_account_state(trading, settings.SYMBOLS)
            except Exception:
                account_state = None

        equity = account_state.equity if account_state and account_state.equity else 100000.0
        held_legs = account_state.legs if account_state else ()
        open_order_symbols = account_state.open_order_symbols if account_state else frozenset()
        
        # 2. Pair held positions and measure current open risk
        held_spreads, warnings = pos_and_risk.pair_spreads(held_legs)
        open_risk = pos_and_risk.open_premium_at_risk(held_spreads) or 0.0
        
        underlying_spreads = [s for s in held_spreads if s.underlying == spread.underlying]
        underlying_risk = pos_and_risk.open_premium_at_risk(underlying_spreads) or 0.0

        # 3. Daily Drawdown Circuit Breaker Check
        daily_dd_pct = self._track_daily_drawdown(equity, today)
        if daily_dd_pct >= MAX_DAILY_DRAWDOWN_FRACTION:
            return RiskDecision(
                approved=False,
                reason=f"Daily Drawdown Circuit Breaker tripped: -{daily_dd_pct:.1%} >= -{MAX_DAILY_DRAWDOWN_FRACTION:.1%} max allowed",
                portfolio_risk=0.0,
                greek_exposure={},
                position_size=0.0,
                selected_spread=spread,
                daily_drawdown_pct=daily_dd_pct,
                active_concurrent_trades=len(held_spreads),
                screen_rejections=rejections,
            )

        # 4. Max Concurrent Active Trades Gate
        if len(held_spreads) >= MAX_CONCURRENT_SPREADS:
            return RiskDecision(
                approved=False,
                reason=f"Max concurrent trades limit reached ({len(held_spreads)}/{MAX_CONCURRENT_SPREADS})",
                portfolio_risk=0.0,
                greek_exposure={},
                position_size=0.0,
                selected_spread=spread,
                daily_drawdown_pct=daily_dd_pct,
                active_concurrent_trades=len(held_spreads),
                screen_rejections=rejections,
            )

        # 5. Check for open order conflict on same underlying
        if any(spread.underlying in sym for sym in open_order_symbols):
            return RiskDecision(
                approved=False,
                reason=f"Pending order already active for {spread.underlying}",
                portfolio_risk=0.0,
                greek_exposure={},
                position_size=0.0,
                selected_spread=spread,
                daily_drawdown_pct=daily_dd_pct,
                active_concurrent_trades=len(held_spreads),
                screen_rejections=rejections,
            )

        # 6. Check confidence threshold
        confidence = state.critic_analysis.confidence_score if state.critic_analysis else 0.5
        if confidence < 0.55:
            return RiskDecision(
                approved=False,
                reason=f"Critic confidence {confidence:.2f} below threshold (0.55)",
                portfolio_risk=0.0,
                greek_exposure={},
                position_size=0.0,
                selected_spread=spread,
                daily_drawdown_pct=daily_dd_pct,
                active_concurrent_trades=len(held_spreads),
                screen_rejections=rejections,
            )

        # 7. Correlated Cluster Risk Check
        cluster_risks = self._calculate_correlated_cluster_risks(held_spreads, equity)
        target_cluster = self._get_symbol_cluster(spread.underlying)
        current_cluster_risk = cluster_risks.get(target_cluster, 0.0)
        max_cluster_cap = equity * MAX_CORRELATED_CLUSTER_FRACTION

        if current_cluster_risk >= max_cluster_cap:
            return RiskDecision(
                approved=False,
                reason=f"Correlated cluster limit reached for {target_cluster}: ${current_cluster_risk:,.0f} >= cap ${max_cluster_cap:,.0f}",
                portfolio_risk=0.0,
                greek_exposure={},
                position_size=0.0,
                selected_spread=spread,
                correlated_cluster_risk=cluster_risks,
                daily_drawdown_pct=daily_dd_pct,
                active_concurrent_trades=len(held_spreads),
                screen_rejections=rejections,
            )

        # 8. Deterministic 4-Tier Fractional Risk Sizing (pos_and_risk.py)
        qty, refusal_reason = pos_and_risk.size_entry(
            spread.net_debit, equity, open_risk, underlying_risk, cycle_spent=0.0
        )

        # Greek calculations (Spread Greeks + Portfolio Greeks)
        spread_greeks = self._calculate_spread_greeks(spread)
        portfolio_greeks = self._aggregate_portfolio_greeks(held_spreads, spread, qty)

        # 9. Portfolio Directional Delta Limit Check
        if abs(portfolio_greeks.get("net_delta", 0.0)) > MAX_PORTFOLIO_DELTA:
            return RiskDecision(
                approved=False,
                reason=f"Portfolio net delta {portfolio_greeks['net_delta']:.1f} exceeds limit (±{MAX_PORTFOLIO_DELTA})",
                portfolio_risk=0.0,
                greek_exposure=spread_greeks,
                position_size=0.0,
                selected_spread=spread,
                portfolio_greeks=portfolio_greeks,
                correlated_cluster_risk=cluster_risks,
                daily_drawdown_pct=daily_dd_pct,
                active_concurrent_trades=len(held_spreads),
                screen_rejections=rejections,
            )

        if refusal_reason is not None or qty < 1:
            return RiskDecision(
                approved=False,
                reason=f"Risk sizing refused: {refusal_reason or 'qty=0'}",
                portfolio_risk=0.0,
                greek_exposure=spread_greeks,
                position_size=0.0,
                selected_spread=spread,
                expected_value=ev_metrics.get("ev"),
                max_profit=ev_metrics.get("max_profit"),
                max_loss=ev_metrics.get("max_loss"),
                reward_risk_ratio=ev_metrics.get("reward_risk"),
                win_probability=ev_metrics.get("win_prob"),
                fill_probability=ev_metrics.get("fill_prob"),
                slippage_bps=ev_metrics.get("combined_bps"),
                portfolio_greeks=portfolio_greeks,
                correlated_cluster_risk=cluster_risks,
                daily_drawdown_pct=daily_dd_pct,
                active_concurrent_trades=len(held_spreads),
                screen_rejections=rejections,
            )

        # 10. Build Alpaca MLEG OrderPlan
        order_plan = options_screener.build_entry_plan(spread, qty, state.cycle_id or "cycle")
        portfolio_risk = round(qty * spread.net_debit * 100.0, 2)

        return RiskDecision(
            approved=True,
            reason=(
                f"Approved {qty}x {spread.direction} {spread.underlying} {spread.expiration} "
                f"[{spread.long.strike}/{spread.short.strike}] @ debit ${spread.net_debit:.2f} | "
                f"EV: ${ev_metrics.get('ev', 0):.2f} (Reward/Risk: {ev_metrics.get('reward_risk', 0):.1f}x)"
            ),
            portfolio_risk=portfolio_risk,
            greek_exposure=spread_greeks,
            position_size=float(qty),
            selected_spread=spread,
            expected_value=ev_metrics.get("ev"),
            max_profit=ev_metrics.get("max_profit"),
            max_loss=ev_metrics.get("max_loss"),
            reward_risk_ratio=ev_metrics.get("reward_risk"),
            win_probability=ev_metrics.get("win_prob"),
            fill_probability=ev_metrics.get("fill_prob"),
            slippage_bps=ev_metrics.get("combined_bps"),
            order_plan=order_plan,
            portfolio_greeks=portfolio_greeks,
            correlated_cluster_risk=cluster_risks,
            daily_drawdown_pct=daily_dd_pct,
            active_concurrent_trades=len(held_spreads),
            screen_rejections=rejections,
        )

    def _get_symbol_cluster(self, symbol: str) -> str:
        """Map symbol to correlated cluster category."""
        for cluster_name, syms in CLUSTERS.items():
            if symbol in syms:
                return cluster_name
        return "OTHER"

    def _calculate_correlated_cluster_risks(
        self, held_spreads: List[OpenSpread], equity: float
    ) -> Dict[str, float]:
        """Sum open premium at risk per correlated cluster."""
        cluster_risks: Dict[str, float] = {k: 0.0 for k in CLUSTERS}
        cluster_risks["OTHER"] = 0.0

        for spread in held_spreads:
            if spread.net_entry_debit is not None:
                cost = spread.net_entry_debit * spread.qty * 100.0
                cluster = self._get_symbol_cluster(spread.underlying)
                cluster_risks[cluster] = cluster_risks.get(cluster, 0.0) + cost

        return cluster_risks

    def _calculate_spread_greeks(self, spread: SpreadQuote) -> Dict[str, float]:
        """Calculate net Greek exposure for the candidate spread."""
        d_long = getattr(spread.long, "delta", None) or 0.50
        d_short = getattr(spread.short, "delta", None) or 0.35
        
        t_long = getattr(spread.long, "theta", None) or -0.05
        t_short = getattr(spread.short, "theta", None) or -0.02
        
        v_long = getattr(spread.long, "vega", None) or 0.10
        v_short = getattr(spread.short, "vega", None) or 0.08

        return {
            "net_delta": round(d_long - d_short, 3),
            "net_theta": round(t_long - t_short, 4),
            "net_vega": round(v_long - v_short, 4),
            "iv_skew": round(spread.skew, 4),
        }

    def _aggregate_portfolio_greeks(
        self, held_spreads: List[OpenSpread], candidate_spread: SpreadQuote, qty: int
    ) -> Dict[str, float]:
        """Aggregate total Greeks across all held positions plus new proposed position."""
        total_delta = 0.0
        total_gamma = 0.0
        total_theta = 0.0
        total_vega = 0.0

        # Estimated Greeks per held spread (approximation based on debit spread structure)
        for spread in held_spreads:
            multiplier = spread.qty * (1.0 if spread.option_type == "C" else -1.0)
            total_delta += multiplier * 0.15 * 100.0
            total_theta += spread.qty * -0.03 * 100.0

        # Add candidate spread
        cand_greeks = self._calculate_spread_greeks(candidate_spread)
        mult = qty * (1.0 if candidate_spread.direction == "CALL" else -1.0)
        total_delta += mult * cand_greeks["net_delta"] * 100.0
        total_theta += qty * cand_greeks["net_theta"] * 100.0
        total_vega += qty * cand_greeks["net_vega"] * 100.0

        return {
            "net_delta": round(total_delta, 2),
            "net_theta": round(total_theta, 2),
            "net_vega": round(total_vega, 2),
        }

    def _scan_event_news_risk(
        self, symbol: str, direction: str, spread: SpreadQuote
    ) -> Optional[str]:
        """Optional Google Gemini LLM Advisory Scan for high-impact macro/earnings risk."""
        import httpx
        import json

        api_key = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GOOGLE_API_KEY", "").strip()
        if not api_key:
            return None

        prompt = (
            f"Analyze potential high-impact macro or event risk for entering a {direction} vertical debit spread on {symbol} "
            f"expiring {spread.expiration} (Width: ${spread.width}, Debit: ${spread.net_debit}). "
            f"Briefly identify if any imminent binary event (earnings, FOMC, CPI) introduces asymmetric risk. "
            f"Reply in 1 concise sentence."
        )

        try:
            resp = httpx.post(
                "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                json={
                    "model": "gemini-1.5-flash",
                    "messages": [{"role": "user", "content": prompt}],
                },
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=3.0,
            )
            if resp.status_code == 200:
                body = resp.json()
                return body["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
        return None

    def _conservative_fallback_decision(self, reason: str) -> RiskDecision:
        """Conservative fallback risk decision."""
        return RiskDecision(
            approved=False,
            reason=f"Risk Gate Fallback: {reason}",
            portfolio_risk=0.0,
            greek_exposure={},
            position_size=0.0,
        )