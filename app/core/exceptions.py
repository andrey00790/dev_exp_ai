"""
Async-specific exceptions for AI Assistant
Following FastAPI error handling best practices
"""

import asyncio
from typing import Optional, Any, Dict


class AsyncTimeoutError(asyncio.TimeoutError):
    """Standardized async timeout error with context"""
    
    def __init__(
        self, 
        message: str = "Operation timed out",
        timeout_duration: Optional[float] = None,
        operation_context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.timeout_duration = timeout_duration
        self.operation_context = operation_context or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        context_str = ""
        if self.timeout_duration:
            context_str += f" (timeout: {self.timeout_duration}s)"
        if self.operation_context:
            context_str += f" (context: {self.operation_context})"
        return f"{self.message}{context_str}"


class AsyncResourceError(Exception):
    """Error in async resource management"""
    
    def __init__(
        self,
        message: str = "Async resource error",
        resource_type: Optional[str] = None,
        resource_context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.resource_type = resource_type
        self.resource_context = resource_context or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        context_str = ""
        if self.resource_type:
            context_str += f" (resource: {self.resource_type})"
        if self.resource_context:
            context_str += f" (context: {self.resource_context})"
        return f"{self.message}{context_str}"


class AsyncRetryError(Exception):
    """Error in async retry operations"""
    
    def __init__(
        self,
        message: str = "Async retry exhausted",
        attempts_made: int = 0,
        max_attempts: int = 0,
        last_exception: Optional[Exception] = None
    ):
        self.message = message
        self.attempts_made = attempts_made
        self.max_attempts = max_attempts
        self.last_exception = last_exception
        super().__init__(self.message)
    
    def __str__(self) -> str:
        return (
            f"{self.message} (attempts: {self.attempts_made}/{self.max_attempts})"
            f"{f' last_error: {self.last_exception}' if self.last_exception else ''}"
        ) 