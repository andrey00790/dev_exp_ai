"""
Rate limiting functionality for the AI Assistant MVP.
"""

import time
from collections import defaultdict, deque
from typing import Dict, Optional

from fastapi import HTTPException, Request


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for given key."""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        while self.requests[key] and self.requests[key][0] < window_start:
            self.requests[key].popleft()

        # Check if under limit
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(now)
            return True

        return False

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for key."""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        while self.requests[key] and self.requests[key][0] < window_start:
            self.requests[key].popleft()

        return max(0, self.max_requests - len(self.requests[key]))


# Global rate limiter instances
auth_rate_limiter = RateLimiter(
    max_requests=10, window_seconds=60
)  # 10 auth attempts per minute
api_rate_limiter = RateLimiter(
    max_requests=100, window_seconds=60
)  # 100 API calls per minute


def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(request: Request, limiter: RateLimiter = None) -> None:
    """Check rate limit for request."""
    if limiter is None:
        limiter = api_rate_limiter

    client_ip = get_client_ip(request)

    if not limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded. Please try again later."
        )


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/api/v1/health"]:
        return await call_next(request)

    # Apply rate limiting
    check_rate_limit(request)

    response = await call_next(request)
    return response


def rate_limit_auth(request: Request) -> None:
    """Rate limit for authentication endpoints."""
    check_rate_limit(request, auth_rate_limiter)
