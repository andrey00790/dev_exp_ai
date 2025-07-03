"""
Core utilities for AI Assistant
Centralized async patterns, HTTP clients, and utility functions
"""

from .async_utils import (AsyncTaskManager, AsyncTimeouts,
                          async_resource_manager, async_retry,
                          cleanup_all_tasks, create_background_task,
                          create_task, default_task_manager, safe_gather,
                          with_timeout)
from .exceptions import AsyncResourceError, AsyncRetryError, AsyncTimeoutError
from .http_client import (StandardHttpClient, api_client, http_client_context,
                          http_client_factory, internal_service_client)

__all__ = [
    # Async utilities
    "AsyncTimeouts",
    "with_timeout",
    "safe_gather",
    "async_resource_manager",
    "async_retry",
    "AsyncTaskManager",
    "create_task",
    "create_background_task",
    "cleanup_all_tasks",
    "default_task_manager",
    # HTTP clients
    "StandardHttpClient",
    "http_client_factory",
    "http_client_context",
    "api_client",
    "internal_service_client",
    # Exceptions
    "AsyncTimeoutError",
    "AsyncResourceError",
    "AsyncRetryError",
]
