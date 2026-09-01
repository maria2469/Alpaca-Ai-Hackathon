"""Base agent class with performance monitoring and bottleneck detection."""

from __future__ import annotations

import time
import json
import hashlib
import signal
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from functools import wraps
from loguru import logger

# Check if SIGALRM is available on this OS (Unix vs Windows)
_HAS_SIGALRM = hasattr(signal, "SIGALRM")


@dataclass
class AgentMetrics:
    """Performance metrics for an agent."""
    agent_name: str
    total_calls: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    max_time: float = 0.0
    min_time: float = float('inf')
    timeouts: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    last_execution_time: float = 0.0
    
    def update(self, execution_time: float, cached: bool = False) -> None:
        """Update metrics with a new execution."""
        self.total_calls += 1
        self.total_time += execution_time
        self.avg_time = self.total_time / self.total_calls
        self.max_time = max(self.max_time, execution_time)
        self.min_time = min(self.min_time, execution_time)
        self.last_execution_time = execution_time
        
        if cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def is_bottleneck(self, threshold_seconds: float = 2.0) -> bool:
        """Check if this agent is a performance bottleneck."""
        return self.avg_time > threshold_seconds or self.max_time > threshold_seconds * 2
    
    def get_performance_report(self) -> str:
        """Generate a performance report."""
        cache_hit_rate = (self.cache_hits / max(self.total_calls, 1)) * 100
        return (
            f"{self.agent_name}: calls={self.total_calls}, "
            f"avg={self.avg_time:.3f}s, max={self.max_time:.3f}s, "
            f"timeouts={self.timeouts}, cache_hit={cache_hit_rate:.1f}%"
        )


class PerformanceMonitor:
    """Monitor and detect performance bottlenecks across agents."""
    
    def __init__(self, warning_threshold: float = 2.0, critical_threshold: float = 5.0):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.agent_metrics: dict[str, AgentMetrics] = {}
        self.bottlenecks: list[str] = []
    
    def register_agent(self, agent_name: str) -> AgentMetrics:
        """Register a new agent for monitoring."""
        if agent_name not in self.agent_metrics:
            self.agent_metrics[agent_name] = AgentMetrics(agent_name=agent_name)
        return self.agent_metrics[agent_name]
    
    def record_execution(self, agent_name: str, execution_time: float, cached: bool = False) -> None:
        """Record an agent execution."""
        metrics = self.register_agent(agent_name)
        metrics.update(execution_time, cached)
        
        # Check for bottlenecks
        if execution_time > self.critical_threshold:
            self.bottlenecks.append(
                f"CRITICAL: {agent_name} took {execution_time:.3f}s "
                f"(threshold: {self.critical_threshold}s)"
            )
            logger.warning(f"Performance bottleneck detected: {agent_name} took {execution_time:.3f}s")
        elif execution_time > self.warning_threshold:
            logger.warning(f"Slow execution: {agent_name} took {execution_time:.3f}s")
    
    def get_bottlenecks(self) -> list[str]:
        """Get current performance bottlenecks."""
        return self.bottlenecks.copy()
    
    def clear_bottlenecks(self) -> None:
        """Clear the bottleneck list."""
        self.bottlenecks.clear()
    
    def get_system_report(self) -> str:
        """Generate a system-wide performance report."""
        lines = ["=== Multi-Agent Performance Report ==="]
        
        total_time = sum(m.total_time for m in self.agent_metrics.values())
        total_calls = sum(m.total_calls for m in self.agent_metrics.values())
        
        lines.append(f"Total calls: {total_calls}")
        lines.append(f"Total time: {total_time:.3f}s")
        lines.append(f"Overall avg: {total_time / max(total_calls, 1):.3f}s per call")
        lines.append("")
        
        # Sort by average time (slowest first)
        sorted_metrics = sorted(
            self.agent_metrics.values(),
            key=lambda m: m.avg_time,
            reverse=True
        )
        
        for metrics in sorted_metrics:
            status = "⚠️ BOTTLENECK" if metrics.is_bottleneck(self.warning_threshold) else "✅ OK"
            lines.append(f"{status} {metrics.get_performance_report()}")
        
        if self.bottlenecks:
            lines.append("")
            lines.append("=== Bottlenecks ===")
            for bottleneck in self.bottlenecks:
                lines.append(f"  {bottleneck}")
        
        return "\n".join(lines)


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(agent_name: str, timeout: Optional[float] = None):
    """Decorator to monitor agent performance with optional timeout."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.monotonic()
            result = None
            timed_out = False
            
            try:
                if timeout is not None and _HAS_SIGALRM:
                    def timeout_handler(signum, frame):
                        raise TimeoutError(f"Agent {agent_name} timed out after {timeout}s")
                    
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(int(timeout))
                    try:
                        result = func(*args, **kwargs)
                    finally:
                        signal.alarm(0)
                else:
                    result = func(*args, **kwargs)
                    
            except TimeoutError as e:
                timed_out = True
                metrics = performance_monitor.register_agent(agent_name)
                metrics.timeouts += 1
                logger.error(f"Agent timeout: {agent_name} - {e}")
                raise
            except Exception as e:
                logger.error(f"Agent error: {agent_name} - {e}")
                raise
            finally:
                execution_time = time.monotonic() - start_time
                if not timed_out:
                    performance_monitor.record_execution(agent_name, execution_time)
            
            return result
        
        return wrapper
    return decorator


class BaseAgent:
    """Base class for all trading agents with performance monitoring."""
    
    def __init__(self, name: str, timeout: Optional[float] = None):
        self.name = name
        self.timeout = timeout
        self.metrics = performance_monitor.register_agent(name)
        self._cache: dict[str, Any] = {}
        self._cache_enabled = False
    
    def enable_cache(self) -> None:
        """Enable result caching for this agent."""
        self._cache_enabled = True
    
    def disable_cache(self) -> None:
        """Disable result caching for this agent."""
        self._cache_enabled = False
        self._cache.clear()
    
    def _get_cache_key(self, *args, **kwargs) -> str:
        """Generate a fast cache key from arguments."""
        key_str = f"{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_str.encode("utf-8")).hexdigest()
    
    def _cached_call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with caching support."""
        if not self._cache_enabled:
            return func(*args, **kwargs)

        cache_key = self._get_cache_key(func.__name__, *args, **kwargs)
        if cache_key in self._cache:
            performance_monitor.record_execution(self.name, 0.0, cached=True)
            return self._cache[cache_key]
        
        result = func(*args, **kwargs)
        self._cache[cache_key] = result
        return result
    
    def execute(self, *args, **kwargs) -> Any:
        """Execute the agent's main logic with monitoring."""
        raise NotImplementedError("Subclasses must implement execute()")
    
    def get_metrics(self) -> AgentMetrics:
        """Get this agent's performance metrics."""
        return self.metrics
    
    def clear_cache(self) -> None:
        """Clear the agent's cache."""
        self._cache.clear()
