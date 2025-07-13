"""
Rate Limiting Middleware для AI Assistant MVP  
Simplified version without Redis async issues
"""

import time
import logging
from typing import Dict, Optional, Tuple, Callable, Any
from collections import defaultdict, deque
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib

logger = logging.getLogger(__name__)

# In-memory store для rate limiting (production должен использовать Redis)
in_memory_store: Dict[str, deque] = defaultdict(lambda: deque())
cleanup_timestamps: Dict[str, float] = {}

class RateLimitConfig:
    """Configuration for rate limiting rules"""
    
    # Default rates (requests per window)
    DEFAULT_RATE = "100/minute"
    
    # Endpoint-specific rates
    ENDPOINT_RATES = {
        # Authentication endpoints (strict)
        "/api/v1/auth/login": "5/minute",
        "/api/v1/auth/register": "3/minute", 
        "/api/v1/auth/refresh": "10/minute",
        "/api/v1/auth/logout": "20/minute",
        
        # AI operations (medium)
        "/api/v1/ai/chat": "30/minute",
        "/api/v1/ai/search": "50/minute",
        "/api/v1/ai/analyze": "20/minute",
        "/api/v1/ai/generate": "15/minute",
        
        # Search operations (medium)
        "/api/v1/search/semantic": "40/minute",
        "/api/v1/search/vector": "60/minute",
        "/api/v1/search/hybrid": "30/minute",
        
        # Document operations (medium)
        "/api/v1/documents/upload": "10/minute",
        "/api/v1/documents/process": "15/minute",
        "/api/v1/documents/delete": "20/minute",
        
        # Admin operations (restricted)
        "/api/v1/admin/users": "20/minute",
        "/api/v1/admin/system": "10/minute",
        "/api/v1/admin/metrics": "30/minute",
        
        # Public endpoints (generous)
        "/api/v1/health": "200/minute",
        "/api/v1/status": "100/minute",
        "/metrics": "60/minute",
        
        # Development endpoints (restricted)
        "/api/v1/debug": "5/minute",
        "/api/v1/test": "10/minute"
    }
    
    # User type multipliers
    USER_TYPE_MULTIPLIERS = {
        "anonymous": 1.0,      # Base rate
        "authenticated": 2.0,   # 2x for authenticated users
        "premium": 5.0,        # 5x for premium users
        "admin": 10.0,         # 10x for admins
        "system": 50.0         # 50x for system accounts
    }
    
    # Method-based rates
    METHOD_RATES = {
        "GET": 1.0,      # Base rate
        "POST": 0.5,     # Slower for writes
        "PUT": 0.5,      # Slower for updates
        "DELETE": 0.3,   # Slowest for deletes
        "PATCH": 0.7     # Medium for patches
    }

def parse_rate_limit(rate_string: str) -> Tuple[int, int]:
    """Parse rate limit string like '100/minute' into (limit, window_seconds)"""
    try:
        limit_str, window_str = rate_string.split('/')
        limit = int(limit_str)
        
        window_map = {
            'second': 1,
            'minute': 60,
            'hour': 3600,
            'day': 86400
        }
        
        window_seconds = window_map.get(window_str, 60)
        return limit, window_seconds
        
    except (ValueError, KeyError) as e:
        logger.error(f"❌ Invalid rate limit format: {rate_string}, error: {e}")
        return 100, 60  # Default fallback

def get_client_identifier(request: Request) -> str:
    """Get unique client identifier for rate limiting"""
    # Priority order for identification
    # 1. User ID from JWT token (if authenticated)
    user_id = getattr(request.state, 'user_id', None)
    if user_id:
        return f"user:{user_id}"
    
    # 2. API key (if present)
    api_key = request.headers.get('X-API-Key')
    if api_key:
        # Hash API key for privacy
        hashed_key = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        return f"api:{hashed_key}"
    
    # 3. IP address (fallback)
    client_ip = request.client.host if request.client else "unknown"
    
    # 4. Consider X-Forwarded-For for proxy scenarios
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()
    
    return f"ip:{client_ip}"

def get_user_type(request: Request) -> str:
    """Determine user type for rate limiting multiplier"""
    # Check if user is authenticated
    user = getattr(request.state, 'user', None)
    if not user:
        return "anonymous"
    
    # Check user roles/scopes
    user_scopes = getattr(user, 'scopes', [])
    user_roles = getattr(user, 'roles', [])
    
    if 'system' in user_roles:
        return "system"
    elif 'admin' in user_roles or 'admin' in user_scopes:
        return "admin"
    elif 'premium' in user_scopes:
        return "premium"
    elif user:
        return "authenticated"
    else:
        return "anonymous"

def check_rate_limit_memory(key: str, limit: int, window: int) -> Tuple[bool, Dict[str, Any]]:
    """Check rate limit using in-memory store"""
    current_time = time.time()
    window_start = current_time - window
    
    # Clean old entries periodically
    if key not in cleanup_timestamps or current_time - cleanup_timestamps[key] > 60:
        # Remove entries older than window
        requests = in_memory_store[key]
        while requests and requests[0] < window_start:
            requests.popleft()
        cleanup_timestamps[key] = current_time
    
    # Check current rate
    requests = in_memory_store[key]
    current_requests = len(requests)
    
    is_allowed = current_requests < limit
    
    if is_allowed:
        requests.append(current_time)
    
    # Calculate reset time
    reset_time = int(current_time + window)
    if requests:
        reset_time = int(requests[0] + window)
    
    return is_allowed, {
        "limit": limit,
        "remaining": max(0, limit - current_requests - (1 if is_allowed else 0)),
        "reset": reset_time,
        "retry_after": max(0, reset_time - int(current_time)) if not is_allowed else 0
    }

def get_rate_limit_for_request(request: Request) -> Tuple[int, int]:
    """Get rate limit configuration for specific request"""
    path = request.url.path
    method = request.method
    user_type = get_user_type(request)
    
    # Get base rate for endpoint
    base_rate = RateLimitConfig.ENDPOINT_RATES.get(path, RateLimitConfig.DEFAULT_RATE)
    limit, window = parse_rate_limit(base_rate)
    
    # Apply user type multiplier
    user_multiplier = RateLimitConfig.USER_TYPE_MULTIPLIERS.get(user_type, 1.0)
    
    # Apply method multiplier
    method_multiplier = RateLimitConfig.METHOD_RATES.get(method, 1.0)
    
    # Calculate final limit
    final_limit = int(limit * user_multiplier * method_multiplier)
    
    logger.debug(f"Rate limit for {method} {path}: {final_limit}/{window}s (user: {user_type})")
    
    return final_limit, window

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting middleware with comprehensive protection"""
    
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting"""
        if not self.enabled:
            return await call_next(request)
        
        # Skip rate limiting for certain paths
        skip_paths = ["/docs", "/redoc", "/openapi.json", "/favicon.ico"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        try:
            # Get client identifier
            client_id = get_client_identifier(request)
            
            # Get rate limit for this request
            limit, window = get_rate_limit_for_request(request)
            
            # Create rate limit key
            rate_key = f"rate_limit:{client_id}:{request.url.path}:{request.method}"
            
            # Check rate limit
            is_allowed, limit_info = check_rate_limit_memory(rate_key, limit, window)
            
            if not is_allowed:
                # Rate limit exceeded
                logger.warning(
                    f"⚠️ Rate limit exceeded: {client_id} for {request.method} {request.url.path}"
                )
                
                # Create rate limit response
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Limit: {limit_info['limit']} per {window} seconds",
                        "retry_after": limit_info['retry_after']
                    }
                )
                
                # Add rate limit headers
                response.headers["X-RateLimit-Limit"] = str(limit_info['limit'])
                response.headers["X-RateLimit-Remaining"] = str(limit_info['remaining'])
                response.headers["X-RateLimit-Reset"] = str(limit_info['reset'])
                response.headers["Retry-After"] = str(limit_info['retry_after'])
                
                return response
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to successful responses
            response.headers["X-RateLimit-Limit"] = str(limit_info['limit'])
            response.headers["X-RateLimit-Remaining"] = str(limit_info['remaining'])
            response.headers["X-RateLimit-Reset"] = str(limit_info['reset'])
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Rate limiting error: {e}")
            # Continue with request if rate limiting fails
            return await call_next(request)

# Rate limiting utilities

def get_rate_limit_status(client_id: str, endpoint: str, method: str) -> Dict[str, Any]:
    """Get current rate limit status for client/endpoint"""
    try:
        rate_key = f"rate_limit:{client_id}:{endpoint}:{method}"
        current_count = len(in_memory_store.get(rate_key, []))
        
        return {
            "current_requests": current_count,
            "window_remaining": 60,  # Default window
            "key": rate_key
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get rate limit status: {e}")
        return {"error": str(e)}

def reset_rate_limit(client_id: str, endpoint: str = "*", method: str = "*") -> bool:
    """Reset rate limit for client (admin function)"""
    try:
        if endpoint == "*":
            # Reset all endpoints for client
            pattern = f"rate_limit:{client_id}:"
        else:
            # Reset specific endpoint
            pattern = f"rate_limit:{client_id}:{endpoint}:{method}"
        
        # Clear from in-memory store
        keys_to_remove = [k for k in in_memory_store.keys() if k.startswith(pattern)]
        for key in keys_to_remove:
            del in_memory_store[key]
        
        logger.info(f"✅ Rate limit reset for {client_id}, pattern: {pattern}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to reset rate limit: {e}")
        return False

# Health check for rate limiting system
def rate_limit_health_check() -> Dict[str, Any]:
    """Health check for rate limiting system"""
    try:
        # Test in-memory store
        memory_test_key = f"memory_test:{time.time()}"
        in_memory_store[memory_test_key].append(time.time())
        memory_healthy = len(in_memory_store[memory_test_key]) > 0
        del in_memory_store[memory_test_key]
        
        return {
            "status": "healthy" if memory_healthy else "degraded",
            "redis_available": False,
            "memory_fallback": memory_healthy,
            "total_keys": len(in_memory_store),
            "config": {
                "default_rate": RateLimitConfig.DEFAULT_RATE,
                "endpoints_configured": len(RateLimitConfig.ENDPOINT_RATES)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Rate limit health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        } 