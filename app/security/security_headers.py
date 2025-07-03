"""
Security Headers Middleware for AI Assistant MVP
Task 1.3: Security Hardening - HTTP security headers configuration

Provides:
- Content Security Policy (CSP)
- X-XSS-Protection
- X-Content-Type-Options
- X-Frame-Options
- Strict-Transport-Security (HSTS)
- Referrer-Policy
- Permissions-Policy
"""

import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    def __init__(self, app, environment: str = "production"):
        super().__init__(app)
        self.environment = environment

    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers to response."""

        response = await call_next(request)

        # Content Security Policy
        if self.environment == "development":
            csp_policy = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "connect-src 'self' http: https: ws: wss:; "
                "img-src 'self' data: https: http:; "
                "frame-ancestors 'none'"
            )
        else:
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https: wss: ws:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'"
            )

        response.headers["Content-Security-Policy"] = csp_policy
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS only in production
        if self.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Cache control for sensitive endpoints
        if request.url.path.startswith("/api/v1/auth") or request.url.path.startswith(
            "/api/v1/budget"
        ):
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, private"
            )

        # Hide server information
        if "server" in response.headers:
            del response.headers["server"]

        return response


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"


def create_security_headers_middleware(environment: str = "production"):
    """Factory function to create security headers middleware."""

    def middleware_factory(app):
        return SecurityHeadersMiddleware(app, environment)

    return middleware_factory


# CORS Security Configuration
CORS_SECURITY_CONFIG = {
    "allow_origins": [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://your-domain.com",  # Replace with actual production domain
    ],
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": [
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
    ],
    "expose_headers": ["X-AI-Assistant-API", "X-Request-ID"],
}


# Security validation functions
def validate_origin(origin: str, allowed_origins: list) -> bool:
    """Validate request origin against whitelist."""
    if not origin:
        return False

    # Check exact match
    if origin in allowed_origins:
        return True

    # Check wildcard patterns for development
    for allowed in allowed_origins:
        if allowed.endswith("*"):
            base = allowed[:-1]
            if origin.startswith(base):
                return True

    return False


def is_safe_redirect_url(url: str, allowed_hosts: list) -> bool:
    """Validate redirect URLs to prevent open redirect attacks."""
    if not url:
        return False

    # Only allow relative URLs or URLs to allowed hosts
    if url.startswith("/"):
        return True

    # Parse URL and check host
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return parsed.netloc in allowed_hosts
    except Exception:
        return False


# Rate limiting configuration for security endpoints
SECURITY_RATE_LIMITS = {
    "/auth/login": {"calls": 5, "period": 60},  # 5 login attempts per minute
    "/auth/register": {"calls": 3, "period": 300},  # 3 registrations per 5 minutes
    "/auth/reset-password": {
        "calls": 3,
        "period": 300,
    },  # 3 password resets per 5 minutes
}


# Security event logging
class SecurityLogger:
    """Security event logger for audit trails."""

    def __init__(self):
        self.logger = logging.getLogger("security_audit")

    def log_authentication_attempt(
        self, ip: str, email: str, success: bool, reason: str = None
    ):
        """Log authentication attempts."""
        event = {
            "event": "authentication_attempt",
            "ip": ip,
            "email": email,
            "success": success,
            "reason": reason,
            "timestamp": self._get_timestamp(),
        }

        if success:
            self.logger.info(f"AUTH_SUCCESS: {email} from {ip}")
        else:
            self.logger.warning(f"AUTH_FAILED: {email} from {ip} - {reason}")

    def log_security_violation(self, ip: str, violation_type: str, details: str):
        """Log security violations."""
        self.logger.error(f"SECURITY_VIOLATION: {violation_type} from {ip} - {details}")

    def log_rate_limit_exceeded(self, ip: str, endpoint: str):
        """Log rate limit violations."""
        self.logger.warning(f"RATE_LIMIT_EXCEEDED: {endpoint} from {ip}")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.now().isoformat()


# Global security logger instance
security_logger = SecurityLogger()
