"""
Standardized async utilities for AI Assistant
Following FastAPI best practices and functional programming principles
"""

import asyncio
import functools
import logging
import weakref
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from typing import (Any, Awaitable, Callable, Dict, List, Optional, Set, TypeVar,
                    Union)

# Type aliases
JSON = Dict[str, Any]
OptionalStr = Optional[str]

from .exceptions import AsyncResourceError, AsyncRetryError, AsyncTimeoutError

T = TypeVar("T")
logger = logging.getLogger(__name__)


class AsyncTimeouts:
    """Optimized timeout configurations for different operation types"""

    # Network operations - optimized for production performance
    HTTP_REQUEST = 25.0           # ↓ Reduced from 30.0
    WEBSOCKET_MESSAGE = 3.0       # ↓ Reduced from 5.0  
    WEBSOCKET_CONNECT = 8.0       # ↓ Reduced from 10.0

    # Database operations - optimized for responsiveness
    DATABASE_QUERY = 8.0          # ↓ Reduced from 10.0
    DATABASE_TRANSACTION = 25.0   # ↓ Reduced from 30.0
    DATABASE_MIGRATION = 300.0    # Keep same for safety

    # Cache operations - optimized for speed
    CACHE_GET = 1.5               # ↓ Reduced from 2.0
    CACHE_SET = 2.5               # ↓ Reduced from 3.0
    CACHE_CLEAR = 4.0             # ↓ Reduced from 5.0

    # AI/ML operations - balanced optimization
    LLM_REQUEST = 45.0            # ↓ Reduced from 60.0
    VECTOR_SEARCH = 12.0          # ↓ Reduced from 15.0
    EMBEDDING_GENERATION = 25.0   # ↓ Reduced from 30.0

    # File operations - optimized for common file sizes
    FILE_READ = 12.0              # ↓ Reduced from 15.0
    FILE_WRITE = 15.0             # ↓ Reduced from 20.0
    FILE_UPLOAD = 90.0            # ↓ Reduced from 120.0

    # Background tasks - keep conservative for reliability
    BACKGROUND_TASK = 300.0       # Keep same
    SYNC_OPERATION = 600.0        # Keep same

    # Analytics operations - optimized for dashboard responsiveness
    ANALYTICS_QUERY = 20.0        # ↓ Reduced from 30.0
    ANALYTICS_AGGREGATION = 45.0  # ↓ Reduced from 60.0

    # Security operations - optimized for user experience
    SECURITY_AUTH = 10.0          # ↓ Reduced from 15.0
    SECURITY_TOKEN_VALIDATION = 3.0  # ↓ Reduced from 5.0
    SECURITY_PASSWORD_HASH = 2.0  # ↓ Reduced from 3.0
    
    # NEW: Performance-specific timeouts for optimization
    BULK_OPERATION = 60.0         # For bulk database operations
    CONCURRENT_SEARCH = 20.0      # For concurrent vector searches
    CACHE_WARMUP = 30.0          # For cache warming operations
    HEALTH_CHECK = 5.0           # For quick health checks


async def with_timeout(
    coro: Awaitable[T],
    timeout: float,
    timeout_message: OptionalStr = None,
    operation_context: Optional[JSON] = None,
) -> T:
    """
    Standard timeout wrapper with consistent error handling

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        timeout_message: Custom timeout message
        operation_context: Additional context for debugging

    Returns:
        Result of the coroutine

    Raises:
        AsyncTimeoutError: If operation times out
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError as e:
        message = timeout_message or f"Operation timed out after {timeout}s"
        logger.warning(
            f"Timeout: {message}",
            extra={"timeout_duration": timeout, "operation_context": operation_context},
        )
        raise AsyncTimeoutError(
            message=message,
            timeout_duration=timeout,
            operation_context=operation_context,
        ) from e


async def safe_gather(
    *awaitables: Awaitable[Any],
    return_exceptions: bool = True,
    timeout: Optional[float] = None,
    max_concurrency: Optional[int] = None,
) -> List[Any]:
    """
    Safe asyncio.gather with proper exception handling and optional limits

    Args:
        *awaitables: Coroutines to execute concurrently
        return_exceptions: Whether to return exceptions instead of raising
        timeout: Optional timeout for the entire operation
        max_concurrency: Optional limit on concurrent operations

    Returns:
        List of results or exceptions
    """
    if not awaitables:
        return []

    # Apply concurrency limit if specified
    if max_concurrency and len(awaitables) > max_concurrency:
        semaphore = asyncio.Semaphore(max_concurrency)

        async def limited_awaitable(coro: Awaitable[Any]) -> Any:
            async with semaphore:
                return await coro

        awaitables = tuple(limited_awaitable(coro) for coro in awaitables)

    gather_coro = asyncio.gather(*awaitables, return_exceptions=return_exceptions)

    if timeout:
        return await with_timeout(
            gather_coro,
            timeout,
            f"safe_gather timed out with {len(awaitables)} operations",
        )
    else:
        return await gather_coro


@asynccontextmanager
async def async_resource_manager(
    resource_factory: Callable[[], Awaitable[T]],
    cleanup_func: Optional[Callable[[T], Awaitable[None]]] = None,
    resource_name: OptionalStr = None,
):
    """
    Standard async resource management pattern

    Args:
        resource_factory: Function to create the resource
        cleanup_func: Optional cleanup function
        resource_name: Name for logging/debugging

    Yields:
        The created resource

    Raises:
        AsyncResourceError: If resource creation or cleanup fails
    """
    resource = None
    resource_name = resource_name or "unknown_resource"

    try:
        logger.debug(f"Creating async resource: {resource_name}")
        resource = await resource_factory()
        yield resource

    except Exception as e:
        logger.error(f"Failed to create async resource {resource_name}: {e}")
        raise AsyncResourceError(
            message=f"Failed to create resource: {e}",
            resource_type=resource_name,
            resource_context={"error": str(e)},
        ) from e

    finally:
        if resource is not None and cleanup_func is not None:
            try:
                logger.debug(f"Cleaning up async resource: {resource_name}")
                await cleanup_func(resource)
            except Exception as e:
                logger.error(f"Failed to cleanup async resource {resource_name}: {e}")
                # Don't raise cleanup errors to avoid masking original exceptions


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    timeout_per_attempt: Optional[float] = None,
):
    """
    Standard async retry decorator with exponential backoff

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for exponential backoff
        exceptions: Tuple of exceptions to catch and retry
        timeout_per_attempt: Optional timeout for each attempt

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    if timeout_per_attempt:
                        return await with_timeout(
                            func(*args, **kwargs),
                            timeout_per_attempt,
                            f"Retry attempt {attempt + 1} timed out",
                        )
                    else:
                        return await func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e
                    attempt_num = attempt + 1

                    if attempt_num == max_attempts:
                        # Last attempt failed
                        logger.error(
                            f"All {max_attempts} retry attempts failed for {func.__name__}: {e}"
                        )
                        break

                    logger.warning(
                        f"Retry attempt {attempt_num}/{max_attempts} failed for {func.__name__}: {e}, "
                        f"retrying in {current_delay}s"
                    )

                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

            # All attempts failed
            raise AsyncRetryError(
                message=f"Function {func.__name__} failed after {max_attempts} attempts",
                attempts_made=max_attempts,
                max_attempts=max_attempts,
                last_exception=last_exception,
            ) from last_exception

        return wrapper

    return decorator


class AsyncTaskManager:
    """
    Centralized async task management for proper lifecycle handling
    Following FastAPI patterns for background task management
    """

    def __init__(self, name: OptionalStr = None):
        self.name = name or f"AsyncTaskManager-{id(self)}"
        self._tasks: Set[asyncio.Task] = set()
        self._task_metadata: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()

    async def create_task(
        self,
        coro: Awaitable[T],
        name: OptionalStr = None,
        timeout: Optional[float] = None,
    ) -> T:
        """
        Create and track async task with optional timeout

        Args:
            coro: Coroutine to execute
            name: Optional task name for debugging
            timeout: Optional timeout for the task

        Returns:
            Task result
        """
        if timeout:
            coro = with_timeout(coro, timeout, f"Task {name} timed out")

        task = asyncio.create_task(coro, name=name)
        self._tasks.add(task)

        # Store metadata
        self._task_metadata[task] = {
            "name": name,
            "created_at": datetime.now(timezone.utc),
            "timeout": timeout,
        }

        # Clean up completed task
        task.add_done_callback(self._tasks.discard)

        try:
            return await task
        except Exception as e:
            logger.error(f"Task {name or 'unnamed'} failed: {e}")
            raise

    def create_background_task(
        self, coro: Awaitable[Any], name: OptionalStr = None
    ) -> asyncio.Task:
        """
        Create background task that runs independently

        Args:
            coro: Coroutine to execute in background
            name: Optional task name for debugging

        Returns:
            Background task (don't await this)
        """
        task = asyncio.create_task(coro, name=name)
        self._tasks.add(task)

        # Store metadata
        self._task_metadata[task] = {
            "name": name,
            "created_at": datetime.now(timezone.utc),
            "background": True,
        }

        # Clean up completed task and log errors
        def cleanup_and_log(finished_task: asyncio.Task):
            self._tasks.discard(finished_task)
            if finished_task.exception():
                logger.error(
                    f"Background task {name or 'unnamed'} failed: {finished_task.exception()}"
                )

        task.add_done_callback(cleanup_and_log)
        return task

    async def cleanup_tasks(self, timeout: float = 10.0) -> None:
        """
        Clean up all tracked tasks

        Args:
            timeout: Timeout for task cleanup
        """
        if not self._tasks:
            return

        logger.info(f"Cleaning up {len(self._tasks)} tasks in {self.name}")

        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # Wait for cancellation with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._tasks, return_exceptions=True), timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Task cleanup timed out after {timeout}s in {self.name}")

        self._tasks.clear()
        logger.info(f"Task cleanup completed for {self.name}")

    def get_task_stats(self) -> JSON:
        """Get statistics about managed tasks"""
        active_tasks = [t for t in self._tasks if not t.done()]
        completed_tasks = [t for t in self._tasks if t.done()]

        return {
            "manager_name": self.name,
            "total_tasks": len(self._tasks),
            "active_tasks": len(active_tasks),
            "completed_tasks": len(completed_tasks),
            "task_names": [
                self._task_metadata.get(task, {}).get("name", "unnamed")
                for task in active_tasks
            ],
        }


# Global task manager for application-level tasks
default_task_manager = AsyncTaskManager("application_default")


# Convenience functions
async def create_task(
    coro: Awaitable[T], name: OptionalStr = None, timeout: Optional[float] = None
) -> T:
    """Create tracked task using default manager"""
    return await default_task_manager.create_task(coro, name, timeout)


def create_background_task(
    coro: Awaitable[Any], name: OptionalStr = None
) -> asyncio.Task:
    """Create background task using default manager"""
    return default_task_manager.create_background_task(coro, name)


async def cleanup_all_tasks(timeout: float = 10.0) -> None:
    """Cleanup all tasks in default manager"""
    await default_task_manager.cleanup_tasks(timeout)
