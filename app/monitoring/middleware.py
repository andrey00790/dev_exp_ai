"""
Middleware module - Simplified version for testing compatibility
"""

import time
import logging
from typing import Callable, Dict, Any

logger = logging.getLogger(__name__)


class MonitoringMiddleware:
    """Simplified monitoring middleware for testing"""
    
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, scope, receive, send):
        """ASGI middleware call"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        # Simple monitoring logic
        start_time = time.time()
        path = scope.get("path", "/")
        method = scope.get("method", "GET")
        
        # Call the app
        await self.app(scope, receive, send)
        
        # Log completion
        duration = time.time() - start_time
        logger.info(f"{method} {path} completed in {duration:.3f}s")
    
    def extract_request_info(self, scope):
        """Extract request information from ASGI scope"""
        return {
            "method": scope.get("method", "GET"),
            "path": scope.get("path", "/"),
            "headers": dict(scope.get("headers", [])),
        }
    
    def should_monitor_request(self, path: str) -> bool:
        """Determine if request should be monitored"""
        # Skip health checks and static files
        if path in ["/health", "/metrics", "/docs", "/redoc"]:
            return False
        if path.startswith("/static/"):
            return False
        return True


# Re-export other monitoring utilities
try:
    from infra.monitoring.middleware import (
        get_metrics_summary,
        update_user_budget_usage, 
        record_auth_attempt,
        record_rate_limit_hit,
        update_active_sessions
    )
except ImportError:
    # Fallback implementations for testing
    def get_metrics_summary() -> Dict[str, Any]:
        return {"active_requests": 0, "total_requests": 0}
    
    def update_user_budget_usage(user_id: str, usage_percent: float) -> None:
        pass
    
    def record_auth_attempt(method: str, success: bool, user_id: str = "unknown") -> None:
        pass
    
    def record_rate_limit_hit(endpoint: str, user_id: str = "unknown") -> None:
        pass
    
    def update_active_sessions(count: int) -> None:
        pass 