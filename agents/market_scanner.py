"""Market Scanner Agent with performance optimization and enhanced market state."""

from __future__ import annotations

import time
import math
import concurrent.futures
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

try:
    from scipy.stats import norm
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False

from agents.base_agent import BaseAgent, monitor_performance
from graph.state import AgentState, MarketSnapshot, Opportunity
from data_models import SymbolFeatures
import market_data
import broker
import signals as signals_module
import settings


class MarketScannerAgent(BaseAgent):
    """Enhanced market scanner with IV, Greeks, and unusual activity detection."""
    
    def __init__(self, timeout: Optional[float] = 3.0):
        super().__init__("market_scanner", timeout)
        self.enable_cache()  # Enable caching by default
        self._stock_client = None
        self._trading_client = None
        self._option_client = None
    
    def _get_clients(self):
        """Get or build cached Alpaca API clients with persistent HTTP connection pool."""
        if self._stock_client is None:
            try:
                config = broker.load_config()
                self._trading_client, self._stock_client, self._option_client = broker.build_clients(config)
            except Exception as e:
                logger.error(f"Failed to build clients: {e}")
        return self._trading_client, self._stock_client, self._option_client
    
    @monitor_performance("market_scanner", timeout=3.0)
    def execute(self, state: AgentState) -> AgentState:
        """Execute market scanning with performance optimization."""
        logger.info("Market Scanner: Starting market data collection")
        
        try:
            # Step 1: Collect market data for all symbols (parallel for performance)
            market_snapshots, symbol_features = self._collect_market_data(state)
            state.market_data = market_snapshots
            # Store pre-computed indicators so downstream agents don't re-fetch
            state.symbol_features = symbol_features
            
            # Step 2: Detect opportunities from already-collected data
            opportunities = self._detect_opportunities(state)
            state.opportunities = opportunities
            
            # Step 3: Calculate scanner confidence
            state.scanner_confidence = self._calculate_scanner_confidence(opportunities)
            
            logger.info(f"Market Scanner: Found {len(opportunities)} opportunities, "
                       f"confidence: {state.scanner_confidence:.2f}")
            
        except Exception as e:
            logger.error(f"Market Scanner error: {e}")
            state.add_bottleneck(f"Market Scanner failed: {str(e)}")
        
        return state
    
    def _collect_market_data(
        self, state: AgentState
    ) -> tuple[Dict[str, MarketSnapshot], Dict]:
        """Collect market data in parallel and compute signals — no duplicate API calls.
        
        Also pre-fetches Alpaca account state in parallel with bar data so Risk Gate
        and Position Manager can reuse it without any duplicate API roundtrips.
        """
        import concurrent.futures
        from data_models import SymbolFeatures

        market_snapshots: Dict[str, MarketSnapshot] = {}
        symbol_features: Dict[str, SymbolFeatures] = {}
        
        # Get symbols from settings
        try:
            import settings
            symbols = settings.SYMBOLS
        except Exception:
            symbols = ["SPY", "QQQ", "IWM", "AAPL", "NVDA", "TSLA", "MSFT", "AMZN"]
        
        logger.info(f"Market Scanner: Collecting data for {len(symbols)} symbols in parallel")
        
        # Build clients once with connection reuse
        trading, stock_client, option_data = self._get_clients()
        if stock_client is None:
            return market_snapshots, symbol_features
        
        now = datetime.utcnow()
        
        # Process each symbol in parallel
        def process_symbol(symbol: str) -> Optional[tuple]:
            """Fetch OHLCV once, derive snapshot + technical indicators — zero extra calls."""
            try:
                logger.debug(f"Fetching data for {symbol}...")
                
                df = market_data.fetch_ohlcv(stock_client, symbol, "5m", now, lookback_bars=50)
                
                if df is None or df.empty:
                    logger.warning(f"No data for {symbol}")
                    return None
                
                logger.debug(f"Got {len(df)} bars for {symbol}")
                
                latest = df.iloc[-1]
                spot = float(latest["close"])
                
                # Build snapshot from the fetched data
                iv = self._estimate_iv(df)
                delta, gamma, theta, vega = self._calculate_greeks(spot, iv or 0.2)
                
                snapshot = MarketSnapshot(
                    symbol=symbol,
                    spot=spot,
                    bid=spot * 0.999,
                    ask=spot * 1.001,
                    timestamp=now,
                    volume=float(latest.get("volume", 0)),
                    unusual_activity=self._detect_unusual_activity(df),
                    iv=iv,
                    delta=delta,
                    gamma=gamma,
                    theta=theta,
                    vega=vega,
                )
                
                # Compute RSI / ATR / MACD / Events using existing signals module
                # This runs on already-fetched data — NO additional API call
                try:
                    df_with_indicators = signals_module.add_indicators(df)
                    features = signals_module.build_signal(
                        symbol=symbol,
                        df=df_with_indicators,
                        mid=spot,
                        now=now,
                        bar_seconds=300,  # 5m bars = 300 seconds
                    )
                except Exception as sig_err:
                    logger.warning(f"Signals computation failed for {symbol}: {sig_err}")
                    features = SymbolFeatures(
                        symbol=symbol,
                        mid=spot,
                        rsi=None,
                        atr=None,
                        macd_hist=None,
                        events=(),
                        bar_age_seconds=None,
                    )
                
                logger.debug(f"Processed {symbol}: spot=${spot:.2f}, rsi={features.rsi}")
                return symbol, snapshot, features
                
            except Exception as e:
                logger.warning(f"Error collecting data for {symbol}: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                return None

        def prefetch_account_and_clock() -> tuple[Optional[object], Optional[bool]]:
            """Pre-fetch Alpaca account state and market clock in parallel."""
            if trading is None:
                return None, None
            acct = None
            is_open = None
            try:
                import settings as _s
                acct = broker.fetch_account_state(trading, _s.SYMBOLS)
            except Exception as e:
                logger.debug(f"Account prefetch: {e}")
            try:
                clock = broker.fetch_clock(trading)
                is_open = clock.is_open
            except Exception as e:
                logger.debug(f"Clock prefetch: {e}")
            return acct, is_open
        
        # Execute all symbols + account prefetch in parallel — account fetch piggybacks
        # on the same network window as bar collection at zero marginal wall-clock cost.
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(symbols) + 1) as executor:
            account_future = executor.submit(prefetch_account_and_clock)
            symbol_futures = [executor.submit(process_symbol, sym) for sym in symbols]
            
            for future in concurrent.futures.as_completed(symbol_futures):
                result = future.result()
                if result:
                    sym, snapshot, features = result
                    market_snapshots[sym] = snapshot
                    symbol_features[sym] = features
            
            # Store pre-fetched account state & clock — downstream agents read this, never re-fetch
            try:
                acct, is_open = account_future.result(timeout=5.0)
                if acct is not None:
                    state.account_state = acct
                    logger.debug("Market Scanner: Account state pre-fetched and cached in AgentState")
                if is_open is not None:
                    state.market_open = is_open
                    if not is_open:
                        logger.info("Market Scanner: Market is currently closed according to Alpaca clock")
            except Exception:
                pass
        
        logger.info(f"Market Scanner: Collected data for {len(market_snapshots)} symbols")
        return market_snapshots, symbol_features
    
    def _detect_opportunities(self, state: AgentState) -> List[Opportunity]:
        """Detect trading opportunities from pre-computed SymbolFeatures and IV/Greek data."""
        opportunities = []

        for symbol, snapshot in state.market_data.items():
            try:
                features = state.symbol_features.get(symbol)
                fired_events = features.events if features else ()
                rsi = features.rsi if features and features.rsi is not None else 50.0
                macd_hist = features.macd_hist if features and features.macd_hist is not None else 0.0

                # 1. Event-driven opportunities (strongest signal from signals.py)
                for event in fired_events:
                    direction = event.direction  # "CALL" or "PUT"
                    base_conf = 0.70

                    # Adjust confidence based on RSI confirmation
                    if direction == "CALL" and 45 <= rsi <= 70:
                        base_conf += 0.10
                    elif direction == "PUT" and 30 <= rsi <= 55:
                        base_conf += 0.10

                    # Adjust based on MACD confirmation
                    if (direction == "CALL" and macd_hist > 0) or (direction == "PUT" and macd_hist < 0):
                        base_conf += 0.05

                    # Adjust based on IV level
                    if snapshot.iv and 0.15 <= snapshot.iv <= 0.45:
                        base_conf += 0.05

                    confidence = min(round(base_conf, 2), 0.95)
                    opportunity = Opportunity(
                        symbol=symbol,
                        confidence=confidence,
                        reason=f"Event {event.kind} ({direction}) | RSI: {rsi:.1f} | IV: {snapshot.iv or 0:.2f}",
                        direction=direction,
                        features={
                            "event": event.kind,
                            "rsi": rsi,
                            "macd_hist": macd_hist,
                            "iv": snapshot.iv,
                            "delta": snapshot.delta,
                            "spot": snapshot.spot,
                        },
                        timestamp=datetime.utcnow(),
                    )
                    opportunities.append(opportunity)
                    logger.info(f"Market Scanner Opportunity (Event): {symbol} {direction} (conf: {confidence:.2f})")

                # 2. Momentum / IV Volatility expansion setups (when no explicit event fired yet)
                if not fired_events and snapshot.iv and snapshot.iv > 0.15:
                    # Direction based on RSI + Delta + MACD
                    bullish_score = int(rsi > 52) + int(macd_hist > 0) + int((snapshot.delta or 0.5) > 0.51)
                    bearish_score = int(rsi < 48) + int(macd_hist < 0) + int((snapshot.delta or 0.5) < 0.49)

                    if bullish_score >= 2:
                        conf = min(0.55 + (bullish_score * 0.05) + (snapshot.iv * 0.15), 0.75)
                        opportunity = Opportunity(
                            symbol=symbol,
                            confidence=round(conf, 2),
                            reason=f"Momentum setup (CALL) | RSI: {rsi:.1f} | MACD: {macd_hist:.3f}",
                            direction="CALL",
                            features={
                                "rsi": rsi,
                                "macd_hist": macd_hist,
                                "iv": snapshot.iv,
                                "delta": snapshot.delta,
                                "spot": snapshot.spot,
                            },
                            timestamp=datetime.utcnow(),
                        )
                        opportunities.append(opportunity)
                    elif bearish_score >= 2:
                        conf = min(0.55 + (bearish_score * 0.05) + (snapshot.iv * 0.15), 0.75)
                        opportunity = Opportunity(
                            symbol=symbol,
                            confidence=round(conf, 2),
                            reason=f"Momentum setup (PUT) | RSI: {rsi:.1f} | MACD: {macd_hist:.3f}",
                            direction="PUT",
                            features={
                                "rsi": rsi,
                                "macd_hist": macd_hist,
                                "iv": snapshot.iv,
                                "delta": snapshot.delta,
                                "spot": snapshot.spot,
                            },
                            timestamp=datetime.utcnow(),
                        )
                        opportunities.append(opportunity)

            except Exception as e:
                logger.warning(f"Error detecting opportunity for {symbol}: {e}")
                continue

        # Sort by confidence descending
        opportunities.sort(key=lambda x: x.confidence, reverse=True)
        return opportunities[:6]
    
    def _calculate_scanner_confidence(self, opportunities: list) -> float:
        """Calculate overall scanner confidence."""
        if not opportunities:
            return 0.0
        
        # Average confidence of top opportunities
        avg_confidence = sum(o.confidence for o in opportunities[:3]) / min(len(opportunities), 3)
        return avg_confidence
    
    def _detect_unusual_activity(self, df) -> bool:
        """Detect unusual trading activity (volume spikes, etc.)."""
        if df.empty or len(df) < 20:
            return False
        
        # Simple volume spike detection
        recent_volume = df["volume"].iloc[-1]
        avg_volume = df["volume"].iloc[-20:].mean()
        
        if recent_volume > avg_volume * 2.0:
            return True
        
        return False
    
    def _estimate_iv(self, df, bar_seconds: int = 300) -> Optional[float]:
        """Estimate annualized volatility from intraday/daily bar returns."""
        if df.empty or len(df) < 15:
            return 0.22  # Default IV
        
        try:
            returns = df["close"].pct_change().dropna()
            if len(returns) < 10:
                return 0.22
            
            # Annualize based on bar duration: 252 trading days * 6.5 hours = 5,896,800 seconds
            trading_seconds_year = 252 * 6.5 * 3600
            bars_per_year = max(trading_seconds_year / max(bar_seconds, 60), 252)
            
            ann_vol = float(returns.std() * (bars_per_year ** 0.5))
            return round(min(max(ann_vol, 0.12), 0.85), 4)
        except Exception as e:
            logger.warning(f"Error estimating IV: {e}")
            return 0.22
    
    def _calculate_greeks(self, spot: float, iv: float) -> tuple:
        """Calculate option Greeks (simplified Black-Scholes)."""
        if not _HAS_SCIPY:
            return 0.5, 0.1, -0.05, 0.2

        # Assume ATM option with 7 days to expiration
        T = 7.0 / 365.0
        K = spot  # ATM
        r = 0.05  # Risk-free rate
        
        try:
            sqrt_T = math.sqrt(T)
            iv_sqrt_T = iv * sqrt_T
            if iv_sqrt_T <= 0.0:
                return 0.5, 0.1, -0.05, 0.2

            d1 = (math.log(spot / K) + (r + 0.5 * iv * iv) * T) / iv_sqrt_T
            d2 = d1 - iv_sqrt_T
            
            delta = float(norm.cdf(d1))
            gamma = float(norm.pdf(d1) / (spot * iv_sqrt_T))
            theta = float((-spot * norm.pdf(d1) * iv / (2.0 * sqrt_T) - r * K * math.exp(-r * T) * norm.cdf(d2)) / 365.0)
            vega = float(spot * sqrt_T * norm.pdf(d1) / 100.0)
            
            return delta, gamma, theta, vega
        except (ValueError, ZeroDivisionError):
            return 0.5, 0.1, -0.05, 0.2