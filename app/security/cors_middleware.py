"""
Enhanced CORS Middleware для AI Assistant MVP
Защита от cross-origin атак и XSS
"""

import logging
from typing import List, Set, Optional, Dict, Any
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class EnhancedCORSConfig:
    """Enhanced CORS configuration with security focus"""
    
    # Production-safe origins
    ALLOWED_ORIGINS_PRODUCTION = [
        "https://ai-assistant.company.com",
        "https://admin.ai-assistant.company.com", 
        "https://api.ai-assistant.company.com"
    ]
    
    # Development origins
    ALLOWED_ORIGINS_DEVELOPMENT = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ]
    
    # Trusted domains pattern
    TRUSTED_DOMAIN_PATTERNS = [
        r"^https://.*\.company\.com$",
        r"^https://.*\.ai-assistant\.com$"
    ]
    
    # Allowed methods for different endpoints
    ENDPOINT_METHODS = {
        "/api/v1/auth/*": ["POST", "OPTIONS"],
        "/api/v1/users/*": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "/api/v1/documents/*": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "/api/v1/search/*": ["GET", "POST", "OPTIONS"],
        "/api/v1/ai/*": ["POST", "OPTIONS"],
        "/metrics": ["GET", "OPTIONS"],
        "/health": ["GET", "OPTIONS"]
    }
    
    # Allowed headers
    ALLOWED_HEADERS = [
        "accept",
        "accept-encoding", 
        "authorization",
        "content-type",
        "dnt",
        "origin",
        "user-agent",
        "x-csrftoken",
        "x-requested-with",
        "x-api-key",
        "x-trace-id"
    ]
    
    # Exposed headers (what client can access)
    EXPOSED_HEADERS = [
        "x-ratelimit-limit",
        "x-ratelimit-remaining", 
        "x-ratelimit-reset",
        "x-trace-id",
        "x-request-id"
    ]

def is_origin_allowed(origin: str, environment: str = "production") -> bool:
    """Check if origin is allowed"""
    if not origin:
        return False
    
    try:
        parsed = urlparse(origin)
        
        # Must be HTTPS in production
        if environment == "production" and parsed.scheme != "https":
            logger.warning(f"⚠️ Non-HTTPS origin rejected in production: {origin}")
            return False
        
        # Check against explicit allowed origins
        allowed_origins = (
            EnhancedCORSConfig.ALLOWED_ORIGINS_PRODUCTION 
            if environment == "production" 
            else EnhancedCORSConfig.ALLOWED_ORIGINS_DEVELOPMENT
        )
        
        if origin in allowed_origins:
            return True
        
        # Check against trusted domain patterns
        for pattern in EnhancedCORSConfig.TRUSTED_DOMAIN_PATTERNS:
            if re.match(pattern, origin):
                logger.info(f"✅ Origin allowed by pattern: {origin}")
                return True
        
        logger.warning(f"⚠️ Origin rejected: {origin}")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error validating origin {origin}: {e}")
        return False

def get_allowed_methods_for_path(path: str) -> List[str]:
    """Get allowed methods for specific path"""
    for pattern, methods in EnhancedCORSConfig.ENDPOINT_METHODS.items():
        # Convert glob pattern to regex
        regex_pattern = pattern.replace("*", ".*")
        if re.match(regex_pattern, path):
            return methods
    
    # Default methods
    return ["GET", "POST", "OPTIONS"]

class SecurityCORSMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS middleware with security features"""
    
    def __init__(self, app, environment: str = "production", strict_mode: bool = True):
        super().__init__(app)
        self.environment = environment
        self.strict_mode = strict_mode
        
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process CORS with enhanced security"""
        origin = request.headers.get("origin")
        method = request.method
        path = request.url.path
        
        # Skip CORS for non-browser requests (no origin header)
        if not origin and method != "OPTIONS":
            response = await call_next(request)
            self._add_security_headers(response)
            return response
        
        # Handle preflight requests
        if method == "OPTIONS":
            return self._handle_preflight(request, origin, path)
        
        # Validate origin for actual requests
        if origin and not is_origin_allowed(origin, self.environment):
            return self._create_cors_error_response("Origin not allowed")
        
        # Validate method for path
        allowed_methods = get_allowed_methods_for_path(path)
        if method not in allowed_methods:
            return self._create_cors_error_response(f"Method {method} not allowed for {path}")
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers to response
        self._add_cors_headers(response, origin, path)
        self._add_security_headers(response)
        
        return response
    
    def _handle_preflight(self, request: Request, origin: str, path: str) -> Response:
        """Handle CORS preflight requests"""
        # Validate origin
        if not is_origin_allowed(origin, self.environment):
            return self._create_cors_error_response("Origin not allowed")
        
        # Get requested method and headers
        requested_method = request.headers.get("access-control-request-method")
        requested_headers = request.headers.get("access-control-request-headers", "").lower()
        
        # Validate requested method
        allowed_methods = get_allowed_methods_for_path(path)
        if requested_method not in allowed_methods:
            return self._create_cors_error_response(f"Method {requested_method} not allowed")
        
        # Validate requested headers
        if requested_headers:
            requested_headers_list = [h.strip() for h in requested_headers.split(",")]
            for header in requested_headers_list:
                if header not in EnhancedCORSConfig.ALLOWED_HEADERS:
                    logger.warning(f"⚠️ Requested header not allowed: {header}")
                    if self.strict_mode:
                        return self._create_cors_error_response(f"Header {header} not allowed")
        
        # Create preflight response
        response = Response(status_code=200)
        self._add_cors_headers(response, origin, path, preflight=True)
        self._add_security_headers(response)
        
        return response
    
    def _add_cors_headers(self, response: Response, origin: str, path: str, preflight: bool = False):
        """Add CORS headers to response"""
        if origin and is_origin_allowed(origin, self.environment):
            response.headers["Access-Control-Allow-Origin"] = origin
        
        # Always add credentials support for authenticated requests
        response.headers["Access-Control-Allow-Credentials"] = "true"
        
        if preflight:
            # Preflight-specific headers
            allowed_methods = get_allowed_methods_for_path(path)
            response.headers["Access-Control-Allow-Methods"] = ", ".join(allowed_methods)
            response.headers["Access-Control-Allow-Headers"] = ", ".join(EnhancedCORSConfig.ALLOWED_HEADERS)
            response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours
        
        # Expose headers that client can access
        response.headers["Access-Control-Expose-Headers"] = ", ".join(EnhancedCORSConfig.EXPOSED_HEADERS)
    
    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # HSTS (only for HTTPS)
        if self.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.openai.com https://api.anthropic.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        # Permissions policy (Feature policy replacement)
        permissions_policy = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "accelerometer=(), "
            "gyroscope=()"
        )
        response.headers["Permissions-Policy"] = permissions_policy
    
    def _create_cors_error_response(self, message: str) -> Response:
        """Create CORS error response"""
        logger.warning(f"⚠️ CORS error: {message}")
        
        response = Response(
            content=f'{{"error": "CORS Error", "message": "{message}"}}',
            status_code=403,
            media_type="application/json"
        )
        
        # Add security headers even to error responses
        self._add_security_headers(response)
        
        return response

# CSRF Protection
class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware"""
    
    def __init__(self, app, secret_key: str, exempt_paths: List[str] = None):
        super().__init__(app)
        self.secret_key = secret_key
        self.exempt_paths = exempt_paths or [
            "/api/v1/auth/login",
            "/api/v1/auth/register", 
            "/health",
            "/metrics",
            "/docs",
            "/redoc"
        ]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with CSRF protection"""
        # Skip CSRF for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Skip CSRF for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS", "TRACE"]:
            return await call_next(request)
        
        # Skip CSRF for API key authenticated requests
        if request.headers.get("X-API-Key"):
            return await call_next(request)
        
        # Validate CSRF token
        csrf_token = request.headers.get("X-CSRFToken")
        if not csrf_token:
            logger.warning("⚠️ Missing CSRF token")
            return Response(
                content='{"error": "CSRF token required"}',
                status_code=403,
                media_type="application/json"
            )
        
        # In a real implementation, you would validate the token
        # For now, just check that it exists and has reasonable format
        if len(csrf_token) < 32:
            logger.warning("⚠️ Invalid CSRF token format")
            return Response(
                content='{"error": "Invalid CSRF token"}',
                status_code=403,
                media_type="application/json"
            )
        
        return await call_next(request)

# Utility functions for CORS management

def generate_cors_config(environment: str = "production") -> Dict[str, Any]:
    """Generate CORS configuration for FastAPI CORSMiddleware"""
    if environment == "production":
        origins = EnhancedCORSConfig.ALLOWED_ORIGINS_PRODUCTION
    else:
        origins = EnhancedCORSConfig.ALLOWED_ORIGINS_DEVELOPMENT
    
    return {
        "allow_origins": origins,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": EnhancedCORSConfig.ALLOWED_HEADERS,
        "expose_headers": EnhancedCORSConfig.EXPOSED_HEADERS,
        "max_age": 86400
    }

async def validate_cors_configuration() -> Dict[str, Any]:
    """Validate current CORS configuration"""
    try:
        issues = []
        
        # Check if origins are HTTPS in production
        for origin in EnhancedCORSConfig.ALLOWED_ORIGINS_PRODUCTION:
            if not origin.startswith("https://"):
                issues.append(f"Production origin not HTTPS: {origin}")
        
        # Check for wildcard origins (security risk)
        all_origins = (
            EnhancedCORSConfig.ALLOWED_ORIGINS_PRODUCTION + 
            EnhancedCORSConfig.ALLOWED_ORIGINS_DEVELOPMENT
        )
        
        for origin in all_origins:
            if "*" in origin:
                issues.append(f"Wildcard origin detected: {origin}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "total_origins": len(all_origins),
            "production_origins": len(EnhancedCORSConfig.ALLOWED_ORIGINS_PRODUCTION),
            "development_origins": len(EnhancedCORSConfig.ALLOWED_ORIGINS_DEVELOPMENT)
        }
        
    except Exception as e:
        logger.error(f"❌ CORS validation error: {e}")
        return {"valid": False, "error": str(e)} 