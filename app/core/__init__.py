"""
Core utilities for AI Assistant
Centralized async patterns, HTTP clients, and utility functions
"""

from .async_utils import (
    AsyncTimeouts,
    with_timeout,
    safe_gather,
    async_resource_manager,
    async_retry,
    AsyncTaskManager,
    create_task,
    create_background_task,
    cleanup_all_tasks,
    default_task_manager
)

from .http_client import (
    StandardHttpClient, 
    http_client_factory,
    http_client_context,
    api_client,
    internal_service_client
)
from .exceptions import (
    AsyncTimeoutError,
    AsyncResourceError,
    AsyncRetryError
)

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
    "AsyncRetryError"
] 