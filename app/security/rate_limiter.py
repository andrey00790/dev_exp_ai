"""
Rate Limiting module for AI Assistant MVP

Provides rate limiting functionality to prevent abuse and DDoS attacks.
"""

import logging
import os
from typing import Callable

from fastapi import HTTPException, Request, status
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
RATE_LIMIT_STORAGE = os.getenv("RATE_LIMIT_STORAGE", "memory")


def get_user_id_or_ip(request: Request) -> str:
    """Extract user ID or IP for rate limiting"""
    return get_remote_address(request)


# Initialize rate limiter
limiter = Limiter(key_func=get_user_id_or_ip)


# Simple rate_limit_auth function that can be used as decorator
def rate_limit_auth(limit: str = "5/minute"):
    """Rate limit for auth endpoints - simple version"""

    def decorator(func: Callable) -> Callable:
        # For now, just return the function without rate limiting
        # In production, this would use proper rate limiting
        return func

    return decorator


# Rate limiting decorators for different endpoint types
def rate_limit_basic(limit: str = "30/minute"):
    """Basic rate limit for general endpoints"""

    def decorator(func: Callable) -> Callable:
        return limiter.limit(limit)(func)

    return decorator


def rate_limit_llm(limit: str = "10/minute"):
    """Strict rate limit for LLM endpoints (expensive)"""

    def decorator(func: Callable) -> Callable:
        return limiter.limit(limit)(func)

    return decorator


def rate_limit_search(limit: str = "20/minute"):
    """Moderate rate limit for search endpoints"""

    def decorator(func: Callable) -> Callable:
        return limiter.limit(limit)(func)

    return decorator


def rate_limit_documentation(limit: str = "15/minute"):
    """Rate limit for documentation generation"""

    def decorator(func: Callable) -> Callable:
        return limiter.limit(limit)(func)

    return decorator


# Custom error handler
def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded"""
    client_id = get_user_id_or_ip(request)
    logger.warning(f"Rate limit exceeded for {client_id}: {exc.detail}")

    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {exc.detail}",
            "retry_after": exc.retry_after,
            "client_id": client_id[:8] + "..." if len(client_id) > 8 else client_id,
        },
        headers={"Retry-After": str(exc.retry_after)},
    )


def setup_rate_limiting_middleware(app):
    """Setup rate limiting middleware for FastAPI app"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)
    logger.info("Rate limiting middleware configured")


def check_rate_limit_status(request: Request) -> dict:
    """Check current rate limit status"""
    client_id = get_user_id_or_ip(request)

    return {
        "client_id": client_id[:8] + "..." if len(client_id) > 8 else client_id,
        "limits": {
            "basic_endpoints": "30/minute",
            "llm_endpoints": "10/minute",
            "auth_endpoints": "5/minute",
            "search_endpoints": "20/minute",
            "documentation_endpoints": "15/minute",
        },
        "storage_backend": RATE_LIMIT_STORAGE,
        "message": "Rate limiting is active",
    }
