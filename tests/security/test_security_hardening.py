"""
Security Hardening Tests
Comprehensive tests для enhanced security features
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import Request, Response
from fastapi.testclient import TestClient

try:
    from app.security.rate_limiting import (
        RateLimitMiddleware, RateLimitConfig, 
        get_client_identifier, get_user_type,
        check_rate_limit_memory, parse_rate_limit
    )
    from app.security.input_validation import (
        UserRegistrationInput, SecurityValidationError,
        detect_malicious_patterns, sanitize_html, validate_email_format
    )
    from app.security.cors_middleware import (
        SecurityCORSMiddleware, is_origin_allowed,
        get_allowed_methods_for_path
    )
    SECURITY_AVAILABLE = True
except ImportError as e:
    SECURITY_AVAILABLE = False
    pytest.skip(f"Security modules not available: {e}", allow_module_level=True)

# Skip all tests if security is not available
pytestmark = pytest.mark.skipif(not SECURITY_AVAILABLE, reason="Security modules not available")

class TestRateLimiting:
    """Tests for rate limiting functionality"""
    
    def test_parse_rate_limit(self):
        """Test rate limit string parsing"""
        limit, window = parse_rate_limit("100/minute")
        assert limit == 100
        assert window == 60
        
        limit, window = parse_rate_limit("5/second")
        assert limit == 5
        assert window == 1
        
        # Test invalid format
        limit, window = parse_rate_limit("invalid")
        assert limit == 100  # Default fallback
        assert window == 60
    
    def test_get_client_identifier(self):
        """Test client identification logic"""
        # Mock request
        request = MagicMock()
        request.state.user_id = "user123"
        request.headers = {}
        request.client.host = "192.168.1.1"
        
        # Test user ID identification
        client_id = get_client_identifier(request)
        assert client_id == "user:user123"
        
        # Test API key identification
        request.state.user_id = None
        request.headers = {"X-API-Key": "secret_api_key"}
        client_id = get_client_identifier(request)
        assert client_id.startswith("api:")
        
        # Test IP fallback
        request.headers = {}
        client_id = get_client_identifier(request)
        assert client_id == "ip:192.168.1.1"
    
    def test_rate_limit_memory(self):
        """Test in-memory rate limiting"""
        key = "test_key"
        limit = 5
        window = 60
        
        # First 5 requests should be allowed
        for i in range(5):
            allowed, info = check_rate_limit_memory(key, limit, window)
            assert allowed is True
            assert info["remaining"] >= 0
        
        # 6th request should be blocked
        allowed, info = check_rate_limit_memory(key, limit, window)
        assert allowed is False
        assert info["remaining"] == 0
    
    def test_user_type_detection(self):
        """Test user type detection for rate multipliers"""
        # Anonymous user
        request = MagicMock()
        request.state.user = None
        user_type = get_user_type(request)
        assert user_type == "anonymous"
        
        # Admin user
        request.state.user = MagicMock()
        request.state.user.roles = ["admin"]
        request.state.user.scopes = ["admin"]
        user_type = get_user_type(request)
        assert user_type == "admin"
        
        # Regular authenticated user
        request.state.user.roles = ["user"]
        request.state.user.scopes = ["basic"]
        user_type = get_user_type(request)
        assert user_type == "authenticated"

class TestInputValidation:
    """Tests for input validation and security"""
    
    def test_malicious_pattern_detection(self):
        """Test detection of malicious patterns"""
        # SQL injection attempt
        with pytest.raises(SecurityValidationError):
            detect_malicious_patterns("SELECT * FROM users", "query")
        
        # XSS attempt
        with pytest.raises(SecurityValidationError):
            detect_malicious_patterns("<script>alert('xss')</script>", "content")
        
        # Safe content should pass
        detect_malicious_patterns("Hello world", "message")  # Should not raise
    
    def test_html_sanitization(self):
        """Test HTML sanitization"""
        dirty_html = "<script>alert('xss')</script><p>Safe content</p>"
        clean_html = sanitize_html(dirty_html)
        
        assert "<script>" not in clean_html
        assert "Safe content" in clean_html
    
    def test_email_validation(self):
        """Test email validation"""
        # Valid email
        valid_email = validate_email_format("user@example.com")
        assert valid_email == "user@example.com"
        
        # Invalid email
        with pytest.raises(SecurityValidationError):
            validate_email_format("invalid-email")
        
        # Malicious email
        with pytest.raises(SecurityValidationError):
            validate_email_format("user@example.com'; DROP TABLE users; --")
    
    def test_user_registration_validation(self):
        """Test user registration input validation"""
        # Valid input
        valid_data = {
            "email": "user@example.com",
            "password": "SecurePass123",
            "name": "John Doe",
            "phone": "+1234567890"
        }
        
        user_input = UserRegistrationInput(**valid_data)
        assert user_input.email == "user@example.com"
        assert user_input.name == "John Doe"
        
        # Invalid password (too weak)
        invalid_data = valid_data.copy()
        invalid_data["password"] = "weak"
        
        with pytest.raises(Exception):  # ValidationError or ValueError
            UserRegistrationInput(**invalid_data)
        
        # Malicious name
        malicious_data = valid_data.copy()
        malicious_data["name"] = "<script>alert('xss')</script>"
        
        # Should sanitize the name
        user_input = UserRegistrationInput(**malicious_data)
        assert "<script>" not in user_input.name

class TestCORSMiddleware:
    """Tests for CORS middleware"""
    
    def test_origin_validation(self):
        """Test origin validation logic"""
        # Valid production origin
        assert is_origin_allowed("https://ai-assistant.company.com", "production") is True
        
        # Invalid production origin (HTTP)
        assert is_origin_allowed("http://ai-assistant.company.com", "production") is False
        
        # Valid development origin
        assert is_origin_allowed("http://localhost:3000", "development") is True
        
        # Invalid origin
        assert is_origin_allowed("https://malicious-site.com", "production") is False
    
    def test_allowed_methods_for_path(self):
        """Test allowed methods for different paths"""
        # Auth endpoints should be restricted
        methods = get_allowed_methods_for_path("/api/v1/auth/login")
        assert "POST" in methods
        assert "GET" not in methods
        
        # User endpoints should allow CRUD
        methods = get_allowed_methods_for_path("/api/v1/users/123")
        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods

class TestSecurityIntegration:
    """Integration tests for security components"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_middleware_integration(self):
        """Test rate limiting middleware integration"""
        # Mock FastAPI app
        app = MagicMock()
        middleware = RateLimitMiddleware(app, enabled=True)
        
        # Mock request
        request = MagicMock()
        request.url.path = "/api/v1/test"
        request.method = "GET"
        request.state.user = None
        request.client.host = "192.168.1.1"
        request.headers = {}
        
        # Mock call_next
        async def mock_call_next(req):
            response = MagicMock()
            response.headers = {}
            return response
        
        # Test successful request
        response = await middleware.dispatch(request, mock_call_next)
        
        # Should have rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
    
    def test_security_configuration(self):
        """Test security configuration"""
        # Test rate limit configuration
        assert RateLimitConfig.DEFAULT_RATE == "100/minute"
        assert "/api/v1/auth/login" in RateLimitConfig.ENDPOINT_RATES
        assert RateLimitConfig.ENDPOINT_RATES["/api/v1/auth/login"] == "5/minute"
        
        # Test user type multipliers
        assert RateLimitConfig.USER_TYPE_MULTIPLIERS["anonymous"] == 1.0
        assert RateLimitConfig.USER_TYPE_MULTIPLIERS["admin"] == 10.0
    
    def test_security_headers_validation(self):
        """Test security headers validation"""
        from app.security.input_validation import validate_security_headers
        
        # Complete security headers
        good_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Content-Security-Policy": "default-src 'self'"
        }
        
        result = validate_security_headers(good_headers)
        assert result["valid"] is True
        assert len(result["issues"]) == 0
        
        # Missing security headers
        bad_headers = {}
        result = validate_security_headers(bad_headers)
        assert result["valid"] is False
        assert len(result["issues"]) > 0

class TestSecurityMetrics:
    """Tests for security metrics and monitoring"""
    
    def test_rate_limit_health_check(self):
        """Test rate limiting health check"""
        from app.security.rate_limiting import rate_limit_health_check
        
        health = rate_limit_health_check()
        assert "status" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "memory_fallback" in health
        assert "config" in health

class TestSecurityEdgeCases:
    """Tests for security edge cases and error handling"""
    
    def test_rate_limiting_with_errors(self):
        """Test rate limiting behavior with errors"""
        # Test with invalid rate limit configuration
        limit, window = parse_rate_limit("invalid/format")
        assert limit == 100  # Should fallback to default
        assert window == 60
    
    def test_input_validation_edge_cases(self):
        """Test input validation edge cases"""
        # Empty input
        with pytest.raises(SecurityValidationError):
            validate_email_format("")
        
        # Very long email
        long_email = "a" * 300 + "@example.com"
        with pytest.raises(SecurityValidationError):
            validate_email_format(long_email)
    
    def test_cors_edge_cases(self):
        """Test CORS edge cases"""
        # Empty origin
        assert is_origin_allowed("", "production") is False
        
        # Malformed origin
        assert is_origin_allowed("not-a-url", "production") is False

if __name__ == "__main__":
    pytest.main([__file__]) 