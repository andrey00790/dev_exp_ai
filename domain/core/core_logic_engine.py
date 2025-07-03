"""
Core Logic Engine for AI Assistant - Phase 3
Enhanced async patterns with intelligent processing and enterprise features

Features:
- Circuit breaker pattern for resilience
- Adaptive timeouts based on historical performance  
- Request coalescing for duplicate operations
- Intelligent load balancing and resource management
- Advanced error handling and recovery
- Comprehensive monitoring and metrics
"""

import asyncio
import hashlib
import json
import logging
import statistics
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (Any, Awaitable, Callable, Dict, List, Optional, Tuple,
                    TypeVar)

from app.core.async_utils import (AsyncTaskManager, AsyncTimeouts, async_retry,
                                  create_background_task, safe_gather,
                                  with_timeout)
from app.core.exceptions import (AsyncResourceError, AsyncRetryError,
                                 AsyncTimeoutError)
from app.performance.cache_manager import cache_manager

logger = logging.getLogger(__name__)
T = TypeVar("T")


class EngineState(Enum):
    """Engine operational states"""

    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OVERLOADED = "overloaded"
    FAILING = "failing"
    SHUTDOWN = "shutdown"


class TaskType(Enum):
    """Task type classification for optimization"""

    CPU_INTENSIVE = "cpu_intensive"
    IO_BOUND = "io_bound"
    MEMORY_INTENSIVE = "memory_intensive"
    NETWORK_HEAVY = "network_heavy"
    MIXED_WORKLOAD = "mixed_workload"


@dataclass
class ProcessingMetrics:
    """Processing performance metrics"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class CircuitBreaker:
    """Circuit breaker pattern for resilience"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, half_open, open

    async def __aenter__(self):
        if self.state == "open":
            if time.time() - self.last_failure_time < self.recovery_timeout:
                raise AsyncResourceError(
                    message="Circuit breaker is open",
                    resource_type="circuit_breaker",
                    resource_context={
                        "state": self.state,
                        "failure_count": self.failure_count,
                    },
                )
            self.state = "half_open"
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(
                    f"Circuit breaker opened after {self.failure_count} failures"
                )
        else:
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("Circuit breaker recovered")


class RequestCoalescer:
    """Request coalescing for duplicate operations"""

    def __init__(self, ttl: float = 5.0):
        self.ttl = ttl
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.request_timestamps: Dict[str, float] = {}

    def get_request_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate unique key for request deduplication"""
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": sorted(kwargs.items()) if kwargs else [],
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def coalesce_request(
        self, request_key: str, coro_factory: Callable[[], Awaitable[T]]
    ) -> T:
        """Coalesce duplicate requests"""
        current_time = time.time()

        # Clean up expired requests
        expired_keys = [
            key
            for key, timestamp in self.request_timestamps.items()
            if current_time - timestamp > self.ttl
        ]
        for key in expired_keys:
            self.pending_requests.pop(key, None)
            self.request_timestamps.pop(key, None)

        # Check if request is already pending
        if request_key in self.pending_requests:
            logger.debug(f"Coalescing duplicate request: {request_key}")
            return await self.pending_requests[request_key]

        # Create new request
        future = asyncio.create_task(coro_factory())
        self.pending_requests[request_key] = future
        self.request_timestamps[request_key] = current_time

        try:
            result = await future
            return result
        finally:
            self.pending_requests.pop(request_key, None)
            self.request_timestamps.pop(request_key, None)


class AdaptiveTimeout:
    """Adaptive timeout management based on historical performance"""

    def __init__(self, base_timeout: float = 30.0, percentile: float = 0.95):
        self.base_timeout = base_timeout
        self.percentile = percentile
        self.response_times: deque = deque(maxlen=100)

    def record_response_time(self, response_time: float):
        """Record response time for timeout calculation"""
        self.response_times.append(response_time)

    def get_adaptive_timeout(self) -> float:
        """Calculate adaptive timeout based on historical data"""
        if len(self.response_times) < 10:
            return self.base_timeout

        times = sorted(self.response_times)
        percentile_index = int(len(times) * self.percentile)
        percentile_time = times[min(percentile_index, len(times) - 1)]

        # Add safety margin and cap at reasonable limits
        adaptive_timeout = percentile_time * 1.5
        return max(
            min(adaptive_timeout, self.base_timeout * 3), self.base_timeout * 0.5
        )


class CoreLogicEngine:
    """
    Core Logic Engine with enhanced async patterns

    Features:
    - Circuit breaker protection
    - Request coalescing
    - Adaptive timeouts
    - Intelligent load balancing
    - Comprehensive monitoring
    """

    def __init__(self, max_concurrent_tasks: int = 100):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)

        # Core components
        self.task_manager = AsyncTaskManager("core_logic_engine")
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.request_coalescer = RequestCoalescer()
        self.adaptive_timeouts: Dict[str, AdaptiveTimeout] = {}

        # State and metrics
        self.state = EngineState.STARTING
        self.metrics = ProcessingMetrics()
        self.response_times: deque = deque(maxlen=1000)
        self.error_counts: defaultdict = defaultdict(int)

        # Background tasks
        self.background_tasks = set()

    async def initialize(self) -> bool:
        """Initialize the core logic engine"""
        try:
            logger.info("🚀 Initializing Core Logic Engine...")

            # Initialize cache manager
            await cache_manager.initialize()

            # Start background monitoring
            self._start_background_tasks()

            self.state = EngineState.HEALTHY
            logger.info("✅ Core Logic Engine initialized successfully")
            return True

        except Exception as e:
            self.state = EngineState.FAILING
            logger.error(f"❌ Failed to initialize Core Logic Engine: {e}")
            return False

    def _start_background_tasks(self):
        """Start background monitoring tasks"""
        tasks = [
            self._metrics_collector(),
            self._health_monitor(),
            self._cleanup_manager(),
        ]

        for task_coro in tasks:
            task = create_background_task(
                task_coro, name=f"engine_{task_coro.__name__}"
            )
            self.background_tasks.add(task)

    async def execute_with_intelligence(
        self,
        func: Callable[..., Awaitable[T]],
        task_type: TaskType = TaskType.MIXED_WORKLOAD,
        enable_circuit_breaker: bool = True,
        enable_coalescing: bool = True,
        enable_adaptive_timeout: bool = True,
        user_id: Optional[str] = None,
        *args,
        **kwargs,
    ) -> T:
        """Execute function with intelligent optimization"""
        start_time = time.time()
        func_name = func.__name__

        try:
            # Request coalescing
            if enable_coalescing:
                request_key = self.request_coalescer.get_request_key(
                    func_name, args, kwargs
                )
                return await self.request_coalescer.coalesce_request(
                    request_key,
                    lambda: self._execute_with_features(
                        func,
                        func_name,
                        enable_circuit_breaker,
                        enable_adaptive_timeout,
                        *args,
                        **kwargs,
                    ),
                )
            else:
                return await self._execute_with_features(
                    func,
                    func_name,
                    enable_circuit_breaker,
                    enable_adaptive_timeout,
                    *args,
                    **kwargs,
                )

        except Exception as e:
            self._record_error(func_name, e, time.time() - start_time)
            raise
        finally:
            response_time = time.time() - start_time
            self.response_times.append(response_time)

            if enable_adaptive_timeout:
                timeout_manager = self._get_adaptive_timeout_manager(func_name)
                timeout_manager.record_response_time(response_time)

    async def _execute_with_features(
        self,
        func: Callable[..., Awaitable[T]],
        func_name: str,
        enable_circuit_breaker: bool,
        enable_adaptive_timeout: bool,
        *args,
        **kwargs,
    ) -> T:
        """Internal execution with features"""
        async with self.semaphore:
            if enable_circuit_breaker:
                circuit_breaker = self._get_circuit_breaker(func_name)
                async with circuit_breaker:
                    return await self._execute_with_timeout(
                        func, func_name, enable_adaptive_timeout, *args, **kwargs
                    )
            else:
                return await self._execute_with_timeout(
                    func, func_name, enable_adaptive_timeout, *args, **kwargs
                )

    async def _execute_with_timeout(
        self,
        func: Callable[..., Awaitable[T]],
        func_name: str,
        enable_adaptive_timeout: bool,
        *args,
        **kwargs,
    ) -> T:
        """Execute with adaptive timeout"""
        if enable_adaptive_timeout:
            timeout_manager = self._get_adaptive_timeout_manager(func_name)
            timeout = timeout_manager.get_adaptive_timeout()
        else:
            timeout = self._get_base_timeout_for_function(func_name)

        return await with_timeout(
            func(*args, **kwargs),
            timeout,
            f"Function {func_name} timed out",
            {"function": func_name, "timeout": timeout},
        )

    def _get_circuit_breaker(self, func_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for function"""
        if func_name not in self.circuit_breakers:
            self.circuit_breakers[func_name] = CircuitBreaker()
        return self.circuit_breakers[func_name]

    def _get_adaptive_timeout_manager(self, func_name: str) -> AdaptiveTimeout:
        """Get or create adaptive timeout manager"""
        if func_name not in self.adaptive_timeouts:
            base_timeout = self._get_base_timeout_for_function(func_name)
            self.adaptive_timeouts[func_name] = AdaptiveTimeout(
                base_timeout=base_timeout
            )
        return self.adaptive_timeouts[func_name]

    def _get_base_timeout_for_function(self, func_name: str) -> float:
        """Determine base timeout based on function characteristics"""
        timeout_mappings = {
            "llm_": AsyncTimeouts.LLM_REQUEST,
            "vector_": AsyncTimeouts.VECTOR_SEARCH,
            "db_": AsyncTimeouts.DATABASE_QUERY,
            "file_": AsyncTimeouts.FILE_READ,
            "http_": AsyncTimeouts.HTTP_REQUEST,
            "cache_": AsyncTimeouts.CACHE_GET,
        }

        for pattern, timeout in timeout_mappings.items():
            if pattern in func_name.lower():
                return timeout

        return AsyncTimeouts.HTTP_REQUEST

    def _record_error(self, func_name: str, error: Exception, response_time: float):
        """Record error for monitoring"""
        self.error_counts[func_name] += 1
        self.metrics.failed_requests += 1

        logger.error(
            f"Function {func_name} failed after {response_time:.3f}s: {error}",
            extra={
                "function_name": func_name,
                "error_type": type(error).__name__,
                "response_time": response_time,
            },
        )

    async def process_batch_intelligently(
        self,
        tasks: List[Tuple[Callable[..., Awaitable[T]], TaskType, tuple, dict]],
        batch_size: Optional[int] = None,
    ) -> List[Any]:
        """Process batch of tasks with intelligent optimization"""
        if not tasks:
            return []

        batch_size = batch_size or min(len(tasks), self.max_concurrent_tasks // 2)
        results = []

        for i in range(0, len(tasks), batch_size):
            batch = tasks[i : i + batch_size]

            batch_tasks = []
            for func, task_type, args, kwargs in batch:
                task = self.execute_with_intelligence(func, task_type, *args, **kwargs)
                batch_tasks.append(task)

            batch_results = await safe_gather(
                *batch_tasks, return_exceptions=True, max_concurrency=batch_size
            )

            results.extend(batch_results)

        return results

    async def _metrics_collector(self):
        """Background metrics collection"""
        while self.state != EngineState.SHUTDOWN:
            try:
                await asyncio.sleep(30)

                if self.response_times:
                    self.metrics.avg_response_time = statistics.mean(
                        self.response_times
                    )
                    sorted_times = sorted(self.response_times)
                    p95_index = int(len(sorted_times) * 0.95)
                    self.metrics.p95_response_time = sorted_times[p95_index]

                total_requests = (
                    self.metrics.successful_requests + self.metrics.failed_requests
                )
                if total_requests > 0:
                    self.metrics.error_rate = (
                        self.metrics.failed_requests / total_requests
                    ) * 100

                self.metrics.last_updated = datetime.now()

            except Exception as e:
                logger.error(f"Error in metrics collector: {e}")

    async def _health_monitor(self):
        """Monitor engine health and adjust state"""
        while self.state != EngineState.SHUTDOWN:
            try:
                await asyncio.sleep(15)

                available_slots = self.semaphore._value

                if self.metrics.error_rate > 50:
                    self.state = EngineState.FAILING
                elif self.metrics.error_rate > 25 or available_slots < 5:
                    self.state = EngineState.DEGRADED
                else:
                    self.state = EngineState.HEALTHY

            except Exception as e:
                logger.error(f"Error in health monitor: {e}")

    async def _cleanup_manager(self):
        """Background cleanup and maintenance"""
        while self.state != EngineState.SHUTDOWN:
            try:
                await asyncio.sleep(300)

                # Clean up completed tasks
                completed_tasks = [
                    task for task in self.background_tasks if task.done()
                ]
                for task in completed_tasks:
                    self.background_tasks.discard(task)
                    if task.exception():
                        logger.error(f"Background task failed: {task.exception()}")

                # Limit response times history
                if len(self.response_times) > 1000:
                    recent_times = list(self.response_times)[-500:]
                    self.response_times.clear()
                    self.response_times.extend(recent_times)

            except Exception as e:
                logger.error(f"Error in cleanup manager: {e}")

    async def get_engine_stats(self) -> Dict[str, Any]:
        """Get comprehensive engine statistics"""
        circuit_breaker_states = {
            func_name: {
                "state": cb.state,
                "failure_count": cb.failure_count,
                "last_failure": cb.last_failure_time,
            }
            for func_name, cb in self.circuit_breakers.items()
        }

        adaptive_timeout_info = {
            func_name: {
                "current_timeout": at.get_adaptive_timeout(),
                "base_timeout": at.base_timeout,
                "sample_count": len(at.response_times),
            }
            for func_name, at in self.adaptive_timeouts.items()
        }

        return {
            "engine_state": self.state.value,
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "avg_response_time": self.metrics.avg_response_time,
                "p95_response_time": self.metrics.p95_response_time,
                "error_rate": self.metrics.error_rate,
                "last_updated": self.metrics.last_updated.isoformat(),
            },
            "concurrency": {
                "max_concurrent_tasks": self.max_concurrent_tasks,
                "available_slots": self.semaphore._value,
                "active_tasks": self.max_concurrent_tasks - self.semaphore._value,
            },
            "circuit_breakers": circuit_breaker_states,
            "adaptive_timeouts": adaptive_timeout_info,
            "background_tasks": len(self.background_tasks),
            "error_counts": dict(self.error_counts),
            "timestamp": datetime.now().isoformat(),
        }

    async def shutdown(self, timeout: float = 30.0):
        """Graceful shutdown"""
        logger.info("🔄 Shutting down Core Logic Engine...")
        self.state = EngineState.SHUTDOWN

        try:
            for task in self.background_tasks:
                task.cancel()

            if self.background_tasks:
                await asyncio.wait_for(
                    asyncio.gather(*self.background_tasks, return_exceptions=True),
                    timeout=timeout,
                )

            await self.task_manager.cleanup_tasks(timeout=10.0)
            await cache_manager.close()

            logger.info("✅ Core Logic Engine shutdown completed")

        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")


# Global engine instance
core_engine = CoreLogicEngine(max_concurrent_tasks=100)


# Convenience functions
async def execute_intelligently(
    func: Callable[..., Awaitable[T]],
    task_type: TaskType = TaskType.MIXED_WORKLOAD,
    enable_circuit_breaker: bool = True,
    enable_coalescing: bool = True,
    enable_adaptive_timeout: bool = True,
    user_id: Optional[str] = None,
    *args,
    **kwargs,
) -> T:
    """Execute function with intelligent optimization"""
    return await core_engine.execute_with_intelligence(
        func,
        task_type,
        enable_circuit_breaker,
        enable_coalescing,
        enable_adaptive_timeout,
        user_id,
        *args,
        **kwargs,
    )


async def process_batch_smart(
    tasks: List[Tuple[Callable[..., Awaitable[T]], TaskType, tuple, dict]],
    batch_size: Optional[int] = None,
) -> List[Any]:
    """Process batch of tasks intelligently"""
    return await core_engine.process_batch_intelligently(tasks, batch_size)


async def initialize_core_engine() -> bool:
    """Initialize the global core engine"""
    return await core_engine.initialize()


async def shutdown_core_engine(timeout: float = 30.0):
    """Shutdown the global core engine"""
    await core_engine.shutdown(timeout)


async def get_core_engine_stats() -> Dict[str, Any]:
    """Get core engine statistics"""
    return await core_engine.get_engine_stats()
