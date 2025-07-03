"""
AI Assistant MVP - Monitoring Middleware
Comprehensive request monitoring and metrics collection for FastAPI
"""

import time
import logging
import uuid
from typing import Callable, Dict, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from prometheus_client import Counter, Histogram, Gauge, Info

from infra.monitoring.apm import apm_manager, active_request_context, record_http_metrics

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'status_class']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status_class'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

REQUEST_SIZE = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    buckets=[64, 256, 1024, 4096, 16384, 65536, 262144, 1048576]
)

RESPONSE_SIZE = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint', 'status_class'],
    buckets=[64, 256, 1024, 4096, 16384, 65536, 262144, 1048576]
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Number of active HTTP requests'
)

ERROR_COUNT = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['method', 'endpoint', 'status_code', 'error_type']
)

# User activity metrics
USER_SESSIONS = Gauge(
    'user_sessions_active',
    'Number of active user sessions'
)

USER_REQUESTS = Counter(
    'user_requests_total',
    'Total requests per user',
    ['user_id', 'endpoint']
)

# Business metrics
API_USAGE_BY_FEATURE = Counter(
    'api_feature_usage_total',
    'API usage by feature',
    ['feature', 'user_type', 'success']
)

BUDGET_USAGE = Gauge(
    'user_budget_usage_percent',
    'User budget usage percentage',
    ['user_id']
)

# Security metrics
AUTH_ATTEMPTS = Counter(
    'auth_attempts_total',
    'Authentication attempts',
    ['method', 'success', 'user_id']
)

RATE_LIMIT_HITS = Counter(
    'rate_limit_hits_total',
    'Rate limit hits',
    ['endpoint', 'user_id']
)

# Application info
APP_INFO = Info(
    'ai_assistant_app_info',
    'AI Assistant application information'
)

# Set application info
APP_INFO.info({
    'version': '2.1.0',
    'environment': 'production',
    'service': 'ai-assistant-mvp'
})

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Comprehensive monitoring middleware for FastAPI applications."""
    
    def __init__(self, app, enable_detailed_logging: bool = True):
        super().__init__(app)
        self.enable_detailed_logging = enable_detailed_logging
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with comprehensive monitoring."""
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start time for duration calculation
        start_time = time.time()
        
        # Extract request information
        method = request.method
        path = self._normalize_path(request.url.path)
        user_agent = request.headers.get("user-agent", "unknown")
        user_id = self._extract_user_id(request)
        
        # Calculate request size
        request_size = self._get_request_size(request)
        
        # Track active requests
        ACTIVE_REQUESTS.inc()
        
        # Log request start if detailed logging is enabled
        if self.enable_detailed_logging:
            logger.info(
                f"Request started: {request_id} {method} {path}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "user_id": user_id,
                    "user_agent": user_agent,
                    "request_size": request_size
                }
            )
        
        response = None
        error_type = None
        
        try:
            # Process request with APM tracing
            with active_request_context(request_id, f"{method} {path}"):
                response = await call_next(request)
                
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"Request error: {request_id} {method} {path} - {error_type}: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "error_type": error_type,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise
        
        finally:
            # Calculate metrics
            duration = time.time() - start_time
            status_code = getattr(response, 'status_code', 500) if response else 500
            status_class = f"{status_code // 100}xx"
            response_size = self._get_response_size(response) if response else 0
            
            # Update Prometheus metrics
            self._update_metrics(
                method, path, status_code, status_class, duration,
                request_size, response_size, user_id, error_type
            )
            
            # Update APM metrics
            record_http_metrics(method, path, status_code, duration)
            
            # Track active requests
            ACTIVE_REQUESTS.dec()
            
            # Log request completion if detailed logging is enabled
            if self.enable_detailed_logging:
                log_level = logging.WARNING if status_code >= 400 else logging.INFO
                logger.log(
                    log_level,
                    f"Request completed: {request_id} {method} {path} {status_code} {duration:.3f}s",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                        "duration": duration,
                        "response_size": response_size,
                        "user_id": user_id
                    }
                )
        
        return response
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path for metrics (remove IDs, etc.)."""
        # Replace common ID patterns
        import re
        
        # Replace UUIDs
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{uuid}', path, flags=re.IGNORECASE)
        
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Replace email addresses
        path = re.sub(r'/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '/{email}', path)
        
        return path
    
    def _extract_user_id(self, request: Request) -> str:
        """Extract user ID from request for user-specific metrics."""
        # Try to get user ID from different sources
        user_id = "anonymous"
        
        # From request state (set by auth middleware)
        if hasattr(request.state, 'user') and request.state.user:
            user_id = getattr(request.state.user, 'user_id', 'unknown')
        
        # From headers (for API keys, etc.)
        elif 'x-user-id' in request.headers:
            user_id = request.headers['x-user-id']
        
        # From JWT token (basic extraction)
        elif 'authorization' in request.headers:
            auth_header = request.headers['authorization']
            if auth_header.startswith('Bearer '):
                # In production, decode JWT properly
                user_id = "authenticated"
        
        return user_id
    
    def _get_request_size(self, request: Request) -> int:
        """Calculate request size in bytes."""
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                return int(content_length)
            except ValueError:
                pass
        return 0
    
    def _get_response_size(self, response: Response) -> int:
        """Calculate response size in bytes."""
        if response and hasattr(response, 'headers'):
            content_length = response.headers.get("content-length")
            if content_length:
                try:
                    return int(content_length)
                except ValueError:
                    pass
        return 0
    
    def _update_metrics(self, method: str, path: str, status_code: int, status_class: str,
                       duration: float, request_size: int, response_size: int,
                       user_id: str, error_type: str = None) -> None:
        """Update all Prometheus metrics."""
        
        # Basic request metrics
        REQUEST_COUNT.labels(
            method=method,
            endpoint=path,
            status_code=status_code,
            status_class=status_class
        ).inc()
        
        REQUEST_DURATION.labels(
            method=method,
            endpoint=path,
            status_class=status_class
        ).observe(duration)
        
        if request_size > 0:
            REQUEST_SIZE.labels(
                method=method,
                endpoint=path
            ).observe(request_size)
        
        if response_size > 0:
            RESPONSE_SIZE.labels(
                method=method,
                endpoint=path,
                status_class=status_class
            ).observe(response_size)
        
        # Error metrics
        if status_code >= 400:
            ERROR_COUNT.labels(
                method=method,
                endpoint=path,
                status_code=status_code,
                error_type=error_type or "http_error"
            ).inc()
        
        # User-specific metrics
        if user_id != "anonymous":
            USER_REQUESTS.labels(
                user_id=user_id,
                endpoint=path
            ).inc()
        
        # Feature-specific metrics
        feature = self._extract_feature_from_path(path)
        if feature:
            user_type = "authenticated" if user_id != "anonymous" else "anonymous"
            success = status_code < 400
            
            API_USAGE_BY_FEATURE.labels(
                feature=feature,
                user_type=user_type,
                success=str(success)
            ).inc()
    
    def _extract_feature_from_path(self, path: str) -> str:
        """Extract feature name from API path."""
        # Map API paths to features
        feature_mapping = {
            '/api/v1/generate': 'rfc_generation',
            '/api/v1/search': 'semantic_search',
            '/api/v1/vector-search': 'vector_search',
            '/api/v1/documentation': 'code_documentation',
            '/api/v1/ai-enhancement': 'ai_enhancement',
            '/api/v1/auth': 'authentication',
            '/api/v1/budget': 'budget_management',
            '/api/v1/feedback': 'feedback',
            '/api/v1/learning': 'learning',
            '/api/v1/llm': 'llm_management',
            '/api/v1/data-sources': 'data_sources',
        }
        
        # Find matching feature
        for api_path, feature in feature_mapping.items():
            if path.startswith(api_path):
                return feature
        
        return None

# Business metrics functions
def update_user_budget_usage(user_id: str, usage_percent: float) -> None:
    """Update user budget usage metrics."""
    BUDGET_USAGE.labels(user_id=user_id).set(usage_percent)

def record_auth_attempt(method: str, success: bool, user_id: str = "unknown") -> None:
    """Record authentication attempt."""
    AUTH_ATTEMPTS.labels(
        method=method,
        success=str(success),
        user_id=user_id
    ).inc()

def record_rate_limit_hit(endpoint: str, user_id: str = "unknown") -> None:
    """Record rate limit hit."""
    RATE_LIMIT_HITS.labels(
        endpoint=endpoint,
        user_id=user_id
    ).inc()

def update_active_sessions(count: int) -> None:
    """Update active user sessions count."""
    USER_SESSIONS.set(count)

# Utility functions for custom metrics
def get_metrics_summary() -> Dict[str, Any]:
    """Get current metrics summary."""
    return {
        "active_requests": ACTIVE_REQUESTS._value._value,
        "total_requests": sum(REQUEST_COUNT._child_samples()),
        "total_errors": sum(ERROR_COUNT._child_samples()),
        "active_sessions": USER_SESSIONS._value._value,
    } 