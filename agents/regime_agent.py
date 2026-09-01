"""Regime Classification Agent with fast deterministic fallback.

Uses the pre-computed SymbolFeatures (RSI/ATR/MACD/events) stored in
state.symbol_features by MarketScannerAgent.  Zero additional API calls —
pure arithmetic from the existing signals module logic.
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime
from loguru import logger

from agents.base_agent import BaseAgent, monitor_performance
from graph.state import AgentState, RegimeBelief
import settings


class RegimeAgent(BaseAgent):
    """Market regime classifier with LLM analysis and fast deterministic fallback."""

    def __init__(self, timeout: Optional[float] = 1.5):
        super().__init__("regime_agent", timeout)
        self.enable_cache()
        self._last_cycle_id: str = ""

    @monitor_performance("regime_agent", timeout=1.5)
    def execute(self, state: AgentState) -> AgentState:
        """Execute regime classification with deterministic speed and optional Gemini LLM."""
        logger.info("Regime Agent: Starting regime classification")

        # Fast-path: return cached result for the same cycle
        if state.cycle_id and state.cycle_id == self._last_cycle_id and state.regime_belief:
            logger.info(f"Regime Agent: Using cached result for cycle {state.cycle_id}")
            return state

        # Check if LLM classification is explicitly requested
        use_llm = getattr(state, "use_llm", False) or getattr(settings, "USE_LLM_REGIME", False)

        if use_llm:
            try:
                regime_belief = self._llm_regime_classification(state)
            except Exception as e:
                logger.warning(f"Regime Agent LLM failed, using deterministic fallback: {e}")
                regime_belief = self._deterministic_regime_classification(state)
                state.add_bottleneck("Regime Agent used deterministic fallback")
        else:
            regime_belief = self._deterministic_regime_classification(state)

        state.regime_belief = regime_belief
        self._last_cycle_id = state.cycle_id

        logger.info(
            f"Regime Agent: Classified as {regime_belief.regime} (confidence: {regime_belief.confidence:.2f})"
        )
        return state

    # ------------------------------------------------------------------
    # LLM path (Google Gemini API)
    # ------------------------------------------------------------------

    def _llm_regime_classification(self, state: AgentState) -> RegimeBelief:
        """LLM-based regime classification using Google Gemini API."""
        import os
        import httpx
        import json
        import settings

        # OpenRouter API key (commented out in favor of Google Gemini API):
        # api_key = getattr(settings, "OPENROUTER_API_KEY", None)
        # if not api_key:
        #     raise ValueError("No OpenRouter API key configured")

        # Google Gemini API key
        api_key = (
            os.environ.get("GEMINI_API_KEY", "").strip()
            or os.environ.get("GOOGLE_API_KEY", "").strip()
            or getattr(settings, "GEMINI_API_KEY", None)
        )
        if not api_key:
            raise ValueError("No Gemini API key configured")

        market_summary = self._prepare_market_summary(state)
        prompt = (
            "You are a market regime classifier. Analyze this market data and classify the "
            "current regime.\n\nMarket Data:\n"
            + market_summary
            + "\n\nClassify into one of these regimes:\n"
            "- trending_up: Strong upward momentum with low volatility\n"
            "- trending_down: Strong downward momentum with low volatility\n"
            "- high_vol_chop: High volatility with no clear direction\n"
            "- low_vol_drift: Low volatility, slow directional movement\n"
            "- unknown: Insufficient data or mixed signals\n\n"
            'Return JSON only: {"regime": "regime_name", "confidence": 0.0-1.0, '
            '"volatility_level": "low/medium/high", "trend_strength": 0.0-1.0}'
        )

        raw_model = getattr(settings, "PRIMARY_MODEL", "gemini-1.5-flash")
        model_name = "gemini-1.5-flash" if "gemini" in raw_model.lower() and "flash" in raw_model.lower() else raw_model

        # [OpenRouter call commented out]:
        # response = httpx.post("https://openrouter.ai/api/v1/chat/completions", ...)

        # Google Gemini OpenAI-compatible v1beta chat endpoint
        response = httpx.post(
            "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            json={
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            },
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=5.0,
        )

        if response.status_code != 200:
            raise Exception(f"Gemini API returned HTTP {response.status_code}")

        result = response.json()
        content = json.loads(result["choices"][0]["message"]["content"])

        return RegimeBelief(
            regime=content.get("regime", "unknown"),
            confidence=content.get("confidence", 0.5),
            volatility_level=content.get("volatility_level", "medium"),
            trend_strength=content.get("trend_strength", 0.5),
        )

    # ------------------------------------------------------------------
    # Deterministic path — existing signals.py logic, zero API calls
    # ------------------------------------------------------------------

    def _deterministic_regime_classification(self, state: AgentState) -> RegimeBelief:
        """Fast deterministic regime classification using pre-computed SymbolFeatures.

        Reads state.symbol_features (RSI/ATR/MACD/events) computed by
        MarketScannerAgent from already-fetched OHLCV.  No network I/O.
        Falls back to IV/delta from state.market_data when features are absent.
        """
        logger.info("Regime Agent: Using deterministic classification with existing signals")

        # ---- Aggregate indicators across all symbols ----
        total_rsi = 0.0
        total_atr = 0.0
        total_macd_hist = 0.0
        total_iv = 0.0
        total_delta = 0.0
        bullish_events = 0
        bearish_events = 0
        rsi_count = atr_count = macd_count = iv_count = delta_count = 0

        # Primary: use pre-computed SymbolFeatures (RSI/ATR/MACD/events)
        for symbol, features in state.symbol_features.items():
            if features.rsi is not None:
                total_rsi += features.rsi
                rsi_count += 1
            if features.atr is not None:
                total_atr += features.atr
                atr_count += 1
            if features.macd_hist is not None:
                total_macd_hist += features.macd_hist
                macd_count += 1
            for event in features.events:
                if event.direction == "CALL":
                    bullish_events += 1
                elif event.direction == "PUT":
                    bearish_events += 1

        # Fallback: use IV/delta from MarketSnapshot when features unavailable
        for symbol, snapshot in state.market_data.items():
            if snapshot.iv is not None:
                total_iv += snapshot.iv
                iv_count += 1
            if snapshot.delta is not None:
                total_delta += snapshot.delta
                delta_count += 1

        # Require at least one data point
        if rsi_count == 0 and iv_count == 0:
            return RegimeBelief(
                regime="unknown",
                confidence=0.5,
                volatility_level="medium",
                trend_strength=0.0,
            )

        avg_rsi = total_rsi / rsi_count if rsi_count else 50.0
        avg_atr = total_atr / atr_count if atr_count else 0.0
        avg_macd_hist = total_macd_hist / macd_count if macd_count else 0.0
        avg_iv = total_iv / iv_count if iv_count else 0.2
        avg_delta = total_delta / delta_count if delta_count else 0.5

        # ---- Volatility: prefer IV, use ATR normalised vs avg_delta as fallback ----
        if iv_count > 0:
            if avg_iv > 0.30:
                volatility_level = "high"
            elif avg_iv < 0.15:
                volatility_level = "low"
            else:
                volatility_level = "medium"
        elif atr_count > 0 and delta_count > 0:
            # ATR relative to price as a rough proxy
            atr_pct = avg_atr / max(avg_delta * 200, 1.0)
            if atr_pct > 0.02:
                volatility_level = "high"
            elif atr_pct < 0.005:
                volatility_level = "low"
            else:
                volatility_level = "medium"
        else:
            volatility_level = "medium"

        # ---- Trend strength: RSI deviation + MACD direction + event balance ----
        # RSI: distance from neutral 50, scaled 0–1
        rsi_strength = abs(avg_rsi - 50.0) / 50.0

        # MACD histogram sign and magnitude (normalised crudely)
        macd_strength = min(abs(avg_macd_hist) * 10, 1.0) if macd_count > 0 else 0.0

        # Event balance: net bullish/bearish events
        total_events = bullish_events + bearish_events
        event_balance = abs(bullish_events - bearish_events) / max(total_events, 1)

        # Delta bias (0.5 = neutral)
        delta_bias = abs(avg_delta - 0.5) * 2 if delta_count > 0 else 0.0

        # Weighted average of available signals
        weights = []
        values = []
        if rsi_count > 0:
            weights.append(0.35); values.append(rsi_strength)
        if macd_count > 0:
            weights.append(0.30); values.append(macd_strength)
        if total_events > 0:
            weights.append(0.20); values.append(event_balance)
        if delta_count > 0:
            weights.append(0.15); values.append(delta_bias)

        if weights:
            norm = sum(weights)
            trend_strength = sum(w * v for w, v in zip(weights, values)) / norm
        else:
            trend_strength = 0.0

        trend_strength = min(trend_strength, 1.0)

        # ---- Direction: RSI > 50 + bullish events + delta > 0.5 => up ----
        bullish_signals = int(avg_rsi > 50) + int(avg_macd_hist > 0) + \
                          int(bullish_events > bearish_events) + int(avg_delta > 0.5)
        bearish_signals = 4 - bullish_signals
        is_bullish = bullish_signals >= bearish_signals

        # ---- Regime classification (same deterministic rules as original PACA) ----
        if volatility_level == "high":
            regime = "high_vol_chop"
        elif trend_strength > 0.55:
            regime = "trending_up" if is_bullish else "trending_down"
        elif trend_strength < 0.25:
            regime = "low_vol_drift"
        else:
            # Moderate trend — directional drift
            regime = "trending_up" if is_bullish else "trending_down"

        # Confidence: higher when multiple signals agree
        confidence = 0.55 + (trend_strength * 0.25)
        confidence = round(min(confidence, 0.90), 4)

        logger.info(
            f"Regime Agent: Deterministic classification - {regime} "
            f"(RSI: {avg_rsi:.1f}, ATR: {avg_atr:.2f}, MACD: {avg_macd_hist:.3f}, Events: {bullish_events}B/{bearish_events}S)"
        )

        return RegimeBelief(
            regime=regime,
            confidence=confidence,
            volatility_level=volatility_level,
            trend_strength=round(trend_strength, 4),
        )

    def _prepare_market_summary(self, state: AgentState) -> str:
        """Prepare market data summary for LLM analysis."""
        if not state.market_data:
            return "No market data available"

        lines = ["Market State Summary:"]

        for symbol, snapshot in state.market_data.items():
            features = state.symbol_features.get(symbol)
            rsi_str = f"{features.rsi:.1f}" if features and features.rsi is not None else "N/A"
            lines.append(
                f"{symbol}: spot={snapshot.spot:.2f}, iv={snapshot.iv or 'N/A'}, "
                f"delta={snapshot.delta or 'N/A'}, rsi={rsi_str}, "
                f"unusual={snapshot.unusual_activity}"
            )

        if state.opportunities:
            lines.append("\nTop Opportunities:")
            for opp in state.opportunities[:3]:
                lines.append(f"  {opp.symbol} {opp.direction} (confidence: {opp.confidence:.2f})")

        return "\n".join(lines)