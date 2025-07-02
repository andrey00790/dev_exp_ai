"""
Enhanced Async Processing Engine for AI Assistant
Phase 3: Core Logic Improvements

Advanced Features:
- Intelligent load balancing and task distribution
- Advanced async patterns with circuit breakers
- Smart resource management and cleanup
- Enterprise-grade error handling and recovery
- Adaptive timeout management
- Advanced concurrency control
- Request coalescing and deduplication
- Smart retry with exponential backoff and jitter
"""

import asyncio
import contextlib
import hashlib
import json
import logging
import statistics
import time
import uuid
import weakref
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import (Any, Awaitable, Callable, Dict, List, Optional, Set, Tuple,
                    TypeVar, Union)

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
    p99_response_time: float = 0.0
    throughput_per_second: float = 0.0
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class TaskContext:
    """Enhanced task execution context"""

    task_id: str
    task_type: TaskType
    priority: int
    timeout: float
    retry_attempts: int
    created_at: datetime
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)


class CircuitBreaker:
    """Circuit breaker pattern implementation for resilience"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: tuple = (Exception,),
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

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
                        "time_until_retry": self.recovery_timeout
                        - (time.time() - self.last_failure_time),
                    },
                )
            else:
                self.state = "half_open"

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type and issubclass(exc_type, self.expected_exception):
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
                logger.info("Circuit breaker closed - recovered")


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
            # Clean up completed request
            self.pending_requests.pop(request_key, None)
            self.request_timestamps.pop(request_key, None)


class AdaptiveTimeout:
    """Adaptive timeout management based on historical performance"""

    def __init__(self, base_timeout: float = 30.0, percentile: float = 0.95):
        self.base_timeout = base_timeout
        self.percentile = percentile
        self.response_times: deque = deque(maxlen=100)
        self.last_calculation = time.time()

    def record_response_time(self, response_time: float):
        """Record response time for timeout calculation"""
        self.response_times.append(response_time)

    def get_adaptive_timeout(self) -> float:
        """Calculate adaptive timeout based on historical data"""
        if len(self.response_times) < 10:
            return self.base_timeout

        # Calculate percentile-based timeout
        times = sorted(self.response_times)
        percentile_index = int(len(times) * self.percentile)
        percentile_time = times[min(percentile_index, len(times) - 1)]

        # Add safety margin (50%) and cap at reasonable limits
        adaptive_timeout = percentile_time * 1.5
        return max(
            min(adaptive_timeout, self.base_timeout * 3), self.base_timeout * 0.5
        )


class EnhancedAsyncEngine:
    """
    Enhanced Async Processing Engine with enterprise features

    Features:
    - Intelligent load balancing
    - Circuit breaker pattern
    - Request coalescing
    - Adaptive timeouts
    - Advanced resource management
    - Comprehensive monitoring
    """

    def __init__(
        self,
        max_concurrent_tasks: int = 100,
        enable_circuit_breaker: bool = True,
        enable_request_coalescing: bool = True,
        enable_adaptive_timeouts: bool = True,
    ):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.enable_circuit_breaker = enable_circuit_breaker
        self.enable_request_coalescing = enable_request_coalescing
        self.enable_adaptive_timeouts = enable_adaptive_timeouts

        # Core components
        self.task_manager = AsyncTaskManager("enhanced_async_engine")
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.request_coalescer = (
            RequestCoalescer() if enable_request_coalescing else None
        )
        self.adaptive_timeouts: Dict[str, AdaptiveTimeout] = {}

        # State management
        self.state = EngineState.STARTING
        self.metrics = ProcessingMetrics()
        self.task_queues: Dict[TaskType, asyncio.Queue] = {
            task_type: asyncio.Queue() for task_type in TaskType
        }

        # Performance tracking
        self.response_times: deque = deque(maxlen=1000)
        self.error_counts: defaultdict = defaultdict(int)
        self.resource_usage_history: deque = deque(maxlen=100)

        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()

    async def initialize(self) -> bool:
        """Initialize the enhanced async engine"""
        try:
            logger.info("🚀 Initializing Enhanced Async Engine...")

            # Initialize cache manager
            await cache_manager.initialize()

            # Start background monitoring
            self._start_background_tasks()

            # Update state
            self.state = EngineState.HEALTHY
            logger.info("✅ Enhanced Async Engine initialized successfully")
            return True

        except Exception as e:
            self.state = EngineState.FAILING
            logger.error(f"❌ Failed to initialize Enhanced Async Engine: {e}")
            return False

    def _start_background_tasks(self):
        """Start background monitoring and maintenance tasks"""
        background_tasks = [
            self._metrics_collector(),
            self._resource_monitor(),
            self._health_checker(),
            self._cleanup_manager(),
        ]

        for task_coro in background_tasks:
            task = create_background_task(
                task_coro, name=f"engine_{task_coro.__name__}"
            )
            self.background_tasks.add(task)

    async def execute_with_intelligence(
        self,
        func: Callable[..., Awaitable[T]],
        task_context: TaskContext,
        *args,
        **kwargs,
    ) -> T:
        """
        Execute function with intelligent optimization

        Features:
        - Adaptive timeouts
        - Circuit breaker protection
        - Request coalescing
        - Load balancing
        - Comprehensive error handling
        """
        start_time = time.time()
        func_name = func.__name__

        try:
            # Apply request coalescing if enabled
            if self.enable_request_coalescing and self.request_coalescer:
                request_key = self.request_coalescer.get_request_key(
                    func_name, args, kwargs
                )

                return await self.request_coalescer.coalesce_request(
                    request_key,
                    lambda: self._execute_with_features(
                        func, task_context, *args, **kwargs
                    ),
                )
            else:
                return await self._execute_with_features(
                    func, task_context, *args, **kwargs
                )

        except Exception as e:
            self._record_error(func_name, e, time.time() - start_time)
            raise
        finally:
            # Record response time
            response_time = time.time() - start_time
            self.response_times.append(response_time)

            if self.enable_adaptive_timeouts:
                timeout_manager = self._get_adaptive_timeout_manager(func_name)
                timeout_manager.record_response_time(response_time)

    async def _execute_with_features(
        self,
        func: Callable[..., Awaitable[T]],
        task_context: TaskContext,
        *args,
        **kwargs,
    ) -> T:
        """Internal execution with all features applied"""
        func_name = func.__name__

        # Acquire semaphore for concurrency control
        async with self.semaphore:
            # Apply circuit breaker if enabled
            if self.enable_circuit_breaker:
                circuit_breaker = self._get_circuit_breaker(func_name)
                async with circuit_breaker:
                    return await self._execute_with_timeout(
                        func, task_context, *args, **kwargs
                    )
            else:
                return await self._execute_with_timeout(
                    func, task_context, *args, **kwargs
                )

    async def _execute_with_timeout(
        self,
        func: Callable[..., Awaitable[T]],
        task_context: TaskContext,
        *args,
        **kwargs,
    ) -> T:
        """Execute with adaptive timeout"""
        func_name = func.__name__

        # Determine timeout
        if self.enable_adaptive_timeouts:
            timeout_manager = self._get_adaptive_timeout_manager(func_name)
            timeout = timeout_manager.get_adaptive_timeout()
        else:
            timeout = task_context.timeout

        # Execute with timeout
        return await with_timeout(
            func(*args, **kwargs),
            timeout,
            f"Function {func_name} timed out",
            {
                "task_id": task_context.task_id,
                "timeout": timeout,
                "adaptive": self.enable_adaptive_timeouts,
            },
        )

    def _get_circuit_breaker(self, func_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for function"""
        if func_name not in self.circuit_breakers:
            self.circuit_breakers[func_name] = CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=60.0,
                expected_exception=(Exception,),
            )
        return self.circuit_breakers[func_name]

    def _get_adaptive_timeout_manager(self, func_name: str) -> AdaptiveTimeout:
        """Get or create adaptive timeout manager for function"""
        if func_name not in self.adaptive_timeouts:
            # Set base timeout based on function type
            base_timeout = self._get_base_timeout_for_function(func_name)
            self.adaptive_timeouts[func_name] = AdaptiveTimeout(
                base_timeout=base_timeout, percentile=0.95
            )
        return self.adaptive_timeouts[func_name]

    def _get_base_timeout_for_function(self, func_name: str) -> float:
        """Determine base timeout based on function characteristics"""
        timeout_mappings = {
            # LLM operations
            "llm_generate": AsyncTimeouts.LLM_REQUEST,
            "llm_analyze": AsyncTimeouts.LLM_REQUEST,
            # Vector operations
            "vector_search": AsyncTimeouts.VECTOR_SEARCH,
            "vector_embed": AsyncTimeouts.EMBEDDING_GENERATION,
            # Database operations
            "db_query": AsyncTimeouts.DATABASE_QUERY,
            "db_transaction": AsyncTimeouts.DATABASE_TRANSACTION,
            # File operations
            "file_read": AsyncTimeouts.FILE_READ,
            "file_write": AsyncTimeouts.FILE_WRITE,
            # Network operations
            "http_request": AsyncTimeouts.HTTP_REQUEST,
            "api_call": AsyncTimeouts.HTTP_REQUEST,
            # Cache operations
            "cache_get": AsyncTimeouts.CACHE_GET,
            "cache_set": AsyncTimeouts.CACHE_SET,
        }

        # Find matching timeout
        for pattern, timeout in timeout_mappings.items():
            if pattern in func_name.lower():
                return timeout

        # Default timeout
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
                "total_errors": self.error_counts[func_name],
            },
        )

    async def process_batch_intelligently(
        self,
        tasks: List[Tuple[Callable[..., Awaitable[T]], TaskContext, tuple, dict]],
        batch_size: Optional[int] = None,
    ) -> List[Union[T, Exception]]:
        """
        Process batch of tasks with intelligent optimization

        Features:
        - Dynamic batch sizing
        - Task type grouping
        - Load balancing
        - Error isolation
        """
        if not tasks:
            return []

        # Determine optimal batch size
        if batch_size is None:
            batch_size = self._calculate_optimal_batch_size(tasks)

        # Group tasks by type for optimization
        task_groups = self._group_tasks_by_type(tasks)

        # Process groups concurrently
        all_results = []
        group_tasks = []

        for task_type, group_tasks_data in task_groups.items():
            group_task = self._process_task_group(
                task_type, group_tasks_data, batch_size
            )
            group_tasks.append(group_task)

        # Execute all groups concurrently
        group_results = await safe_gather(
            *group_tasks, return_exceptions=True, max_concurrency=len(TaskType)
        )

        # Flatten results maintaining original order
        result_map = {}
        for i, group_result in enumerate(group_results):
            if isinstance(group_result, Exception):
                # Handle group failure
                task_type = list(task_groups.keys())[i]
                logger.error(f"Task group {task_type} failed: {group_result}")
                continue

            for task_index, result in group_result:
                result_map[task_index] = result

        # Build final results in original order
        final_results = []
        for i in range(len(tasks)):
            if i in result_map:
                final_results.append(result_map[i])
            else:
                final_results.append(
                    AsyncRetryError(
                        message="Task failed in batch processing",
                        attempts_made=0,
                        max_attempts=1,
                    )
                )

        return final_results

    def _calculate_optimal_batch_size(
        self, tasks: List[Tuple[Callable, TaskContext, tuple, dict]]
    ) -> int:
        """Calculate optimal batch size based on task types and system load"""
        # Analyze task types
        task_type_counts = defaultdict(int)
        for _, task_context, _, _ in tasks:
            task_type_counts[task_context.task_type] += 1

        # Base batch size on dominant task type
        dominant_task_type = max(task_type_counts.items(), key=lambda x: x[1])[0]

        # Batch size recommendations by task type
        batch_sizes = {
            TaskType.CPU_INTENSIVE: 10,
            TaskType.IO_BOUND: 50,
            TaskType.MEMORY_INTENSIVE: 5,
            TaskType.NETWORK_HEAVY: 20,
            TaskType.MIXED_WORKLOAD: 25,
        }

        base_batch_size = batch_sizes.get(dominant_task_type, 20)

        # Adjust based on current system load
        current_load = len(self.response_times) / 1000  # Approximation
        load_factor = max(0.5, 1.0 - current_load)

        optimal_batch_size = int(base_batch_size * load_factor)
        return max(1, min(optimal_batch_size, self.max_concurrent_tasks))

    def _group_tasks_by_type(
        self, tasks: List[Tuple[Callable, TaskContext, tuple, dict]]
    ) -> Dict[TaskType, List[Tuple[int, Callable, TaskContext, tuple, dict]]]:
        """Group tasks by type for optimized processing"""
        groups = defaultdict(list)

        for i, (func, task_context, args, kwargs) in enumerate(tasks):
            groups[task_context.task_type].append((i, func, task_context, args, kwargs))

        return dict(groups)

    async def _process_task_group(
        self,
        task_type: TaskType,
        group_tasks: List[Tuple[int, Callable, TaskContext, tuple, dict]],
        batch_size: int,
    ) -> List[Tuple[int, Union[T, Exception]]]:
        """Process a group of tasks of the same type"""
        results = []

        # Process in batches
        for i in range(0, len(group_tasks), batch_size):
            batch = group_tasks[i : i + batch_size]

            # Create execution tasks
            batch_exec_tasks = []
            for task_index, func, task_context, args, kwargs in batch:
                exec_task = self.execute_with_intelligence(
                    func, task_context, *args, **kwargs
                )
                batch_exec_tasks.append((task_index, exec_task))

            # Execute batch
            batch_results = await safe_gather(
                *[task for _, task in batch_exec_tasks],
                return_exceptions=True,
                max_concurrency=batch_size,
            )

            # Collect results with original indices
            for i, (original_index, _) in enumerate(batch_exec_tasks):
                results.append((original_index, batch_results[i]))

        return results

    async def _metrics_collector(self):
        """Background task for collecting performance metrics"""
        while self.state != EngineState.SHUTDOWN:
            try:
                await asyncio.sleep(30)  # Collect every 30 seconds

                # Calculate metrics
                if self.response_times:
                    self.metrics.avg_response_time = statistics.mean(
                        self.response_times
                    )
                    sorted_times = sorted(self.response_times)
                    p95_index = int(len(sorted_times) * 0.95)
                    p99_index = int(len(sorted_times) * 0.99)
                    self.metrics.p95_response_time = sorted_times[p95_index]
                    self.metrics.p99_response_time = sorted_times[p99_index]

                # Calculate error rate
                total_requests = (
                    self.metrics.successful_requests + self.metrics.failed_requests
                )
                if total_requests > 0:
                    self.metrics.error_rate = (
                        self.metrics.failed_requests / total_requests
                    ) * 100

                # Update timestamp
                self.metrics.last_updated = datetime.now()

                logger.debug(
                    f"Metrics updated: {self.metrics.avg_response_time:.3f}s avg, {self.metrics.error_rate:.1f}% error rate"
                )

            except Exception as e:
                logger.error(f"Error in metrics collector: {e}")

    async def _resource_monitor(self):
        """Monitor system resources and adjust engine state"""
        while self.state != EngineState.SHUTDOWN:
            try:
                await asyncio.sleep(15)  # Monitor every 15 seconds

                # Check task queue sizes
                total_queued = sum(queue.qsize() for queue in self.task_queues.values())

                # Check semaphore availability
                available_slots = self.semaphore._value

                # Determine engine state
                if total_queued > self.max_concurrent_tasks * 2:
                    self.state = EngineState.OVERLOADED
                elif self.metrics.error_rate > 50:
                    self.state = EngineState.FAILING
                elif self.metrics.error_rate > 25 or available_slots < 5:
                    self.state = EngineState.DEGRADED
                else:
                    self.state = EngineState.HEALTHY

                logger.debug(
                    f"Engine state: {self.state.value}, queued: {total_queued}, available: {available_slots}"
                )

            except Exception as e:
                logger.error(f"Error in resource monitor: {e}")

    async def _health_checker(self):
        """Perform health checks and recovery actions"""
        while self.state != EngineState.SHUTDOWN:
            try:
                await asyncio.sleep(60)  # Check every minute

                # Check cache manager health
                cache_health = await cache_manager.health_check()
                if cache_health["status"] != "healthy":
                    logger.warning(f"Cache manager unhealthy: {cache_health}")

                # Reset circuit breakers if necessary
                current_time = time.time()
                for func_name, cb in self.circuit_breakers.items():
                    if (
                        cb.state == "open"
                        and cb.last_failure_time
                        and current_time - cb.last_failure_time
                        > cb.recovery_timeout * 2
                    ):
                        cb.state = "closed"
                        cb.failure_count = 0
                        logger.info(f"Reset circuit breaker for {func_name}")

            except Exception as e:
                logger.error(f"Error in health checker: {e}")

    async def _cleanup_manager(self):
        """Background cleanup and maintenance"""
        while self.state != EngineState.SHUTDOWN:
            try:
                await asyncio.sleep(300)  # Cleanup every 5 minutes

                # Clean up completed background tasks
                completed_tasks = [
                    task for task in self.background_tasks if task.done()
                ]
                for task in completed_tasks:
                    self.background_tasks.discard(task)
                    if task.exception():
                        logger.error(f"Background task failed: {task.exception()}")

                # Limit response times history
                if len(self.response_times) > 1000:
                    # Keep only recent 500 entries
                    recent_times = list(self.response_times)[-500:]
                    self.response_times.clear()
                    self.response_times.extend(recent_times)

                logger.debug("Cleanup completed")

            except Exception as e:
                logger.error(f"Error in cleanup manager: {e}")

    async def get_engine_stats(self) -> Dict[str, Any]:
        """Get comprehensive engine statistics"""
        # Circuit breaker states
        cb_states = {
            func_name: {
                "state": cb.state,
                "failure_count": cb.failure_count,
                "last_failure": cb.last_failure_time,
            }
            for func_name, cb in self.circuit_breakers.items()
        }

        # Adaptive timeout info
        timeout_info = {
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
                "p99_response_time": self.metrics.p99_response_time,
                "error_rate": self.metrics.error_rate,
                "last_updated": self.metrics.last_updated.isoformat(),
            },
            "concurrency": {
                "max_concurrent_tasks": self.max_concurrent_tasks,
                "available_slots": self.semaphore._value,
                "active_tasks": self.max_concurrent_tasks - self.semaphore._value,
            },
            "task_queues": {
                task_type.value: queue.qsize()
                for task_type, queue in self.task_queues.items()
            },
            "circuit_breakers": cb_states,
            "adaptive_timeouts": timeout_info,
            "features": {
                "circuit_breaker_enabled": self.enable_circuit_breaker,
                "request_coalescing_enabled": self.enable_request_coalescing,
                "adaptive_timeouts_enabled": self.enable_adaptive_timeouts,
            },
            "background_tasks": len(self.background_tasks),
            "error_counts": dict(self.error_counts),
            "timestamp": datetime.now().isoformat(),
        }

    async def shutdown(self, timeout: float = 30.0):
        """Graceful shutdown of the engine"""
        logger.info("🔄 Shutting down Enhanced Async Engine...")
        self.state = EngineState.SHUTDOWN

        try:
            # Cancel background tasks
            for task in self.background_tasks:
                task.cancel()

            # Wait for tasks to complete
            if self.background_tasks:
                await asyncio.wait_for(
                    asyncio.gather(*self.background_tasks, return_exceptions=True),
                    timeout=timeout,
                )

            # Cleanup task manager
            await self.task_manager.cleanup_tasks(timeout=10.0)

            # Close cache manager
            await cache_manager.close()

            logger.info("✅ Enhanced Async Engine shutdown completed")

        except asyncio.TimeoutError:
            logger.warning("⚠️ Engine shutdown timed out")
        except Exception as e:
            logger.error(f"❌ Error during engine shutdown: {e}")


# Global engine instance
enhanced_engine = EnhancedAsyncEngine(
    max_concurrent_tasks=100,
    enable_circuit_breaker=True,
    enable_request_coalescing=True,
    enable_adaptive_timeouts=True,
)


# Convenience functions
async def execute_intelligently(
    func: Callable[..., Awaitable[T]],
    task_type: TaskType = TaskType.MIXED_WORKLOAD,
    priority: int = 5,
    timeout: float = 30.0,
    user_id: Optional[str] = None,
    *args,
    **kwargs,
) -> T:
    """Execute function with intelligent optimization"""
    task_context = TaskContext(
        task_id=str(uuid.uuid4()),
        task_type=task_type,
        priority=priority,
        timeout=timeout,
        retry_attempts=3,
        created_at=datetime.now(),
        user_id=user_id,
    )

    return await enhanced_engine.execute_with_intelligence(
        func, task_context, *args, **kwargs
    )


async def process_batch_smart(
    tasks: List[Tuple[Callable[..., Awaitable[T]], TaskType, tuple, dict]],
    batch_size: Optional[int] = None,
) -> List[Union[T, Exception]]:
    """Process batch of tasks with intelligent optimization"""
    enhanced_tasks = []

    for func, task_type, args, kwargs in tasks:
        task_context = TaskContext(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            priority=5,
            timeout=30.0,
            retry_attempts=3,
            created_at=datetime.now(),
        )
        enhanced_tasks.append((func, task_context, args, kwargs))

    return await enhanced_engine.process_batch_intelligently(enhanced_tasks, batch_size)


async def initialize_enhanced_engine() -> bool:
    """Initialize the global enhanced engine"""
    return await enhanced_engine.initialize()


async def shutdown_enhanced_engine(timeout: float = 30.0):
    """Shutdown the global enhanced engine"""
    await enhanced_engine.shutdown(timeout)


async def get_enhanced_engine_stats() -> Dict[str, Any]:
    """Get enhanced engine statistics"""
    return await enhanced_engine.get_engine_stats()
