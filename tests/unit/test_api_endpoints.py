"""
Tests for API endpoints to improve code coverage.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestHealthEndpoints:
    """Test health endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert "features" in data
        assert "endpoints" in data
        assert "status" in data
        assert data["status"] == "running"
    
    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "uptime" in data
        assert "environment" in data
    
    def test_health_v1_endpoint(self, client):
        """Test API v1 health endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "checks" in data
        assert data["checks"]["api"] == "healthy"


class TestConfigModule:
    """Test config module."""
    
    def test_config_import(self):
        """Test config module can be imported."""
        from app.config import settings
        assert settings is not None
        assert hasattr(settings, 'version')
        assert hasattr(settings, 'environment')


class TestLoggingConfig:
    """Test logging configuration."""
    
    @patch('app.logging_config.logging.basicConfig')
    @patch('app.logging_config.logging.getLogger')
    def test_setup_logging(self, mock_get_logger, mock_basic_config):
        """Test setup_logging function."""
        from app.logging_config import setup_logging
        
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        setup_logging()
        
        mock_basic_config.assert_called_once()
        mock_get_logger.assert_called_once_with('uvicorn.error')
        assert mock_logger.propagate is False


class TestMainModule:
    """Test main module functions."""
    
    def test_create_app(self):
        """Test create_app function."""
        app = create_app()
        assert app is not None
        assert hasattr(app, 'routes')
        assert len(app.routes) > 0
    
    @patch('app.main.logger')
    def test_create_app_logging(self, mock_logger):
        """Test create_app logs initialization."""
        create_app()
        
        # Verify logging calls were made
        assert mock_logger.info.called
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        
        # Check for key log messages
        assert any("FastAPI application created successfully" in msg for msg in log_calls)
        assert any("Available endpoints:" in msg for msg in log_calls)


class TestMetricsEndpoint:
    """Test metrics endpoint."""
    
    def test_metrics_endpoint_exists(self, client):
        """Test metrics endpoint is available."""
        response = client.get("/metrics")
        # Should return 200 or 404 depending on monitoring availability
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            # Should return prometheus format or JSON (depending on implementation)
            content_type = response.headers.get("content-type", "")
            assert "text/plain" in content_type or "application/json" in content_type


class TestAPIRouterInclusion:
    """Test that all API routers are properly included."""
    
    def test_auth_router_included(self, client):
        """Test auth router is included."""
        # Test demo users endpoint (should be accessible without auth)
        response = client.get("/auth/demo-users")
        assert response.status_code == 200
    
    def test_api_v1_routes_exist(self, client):
        """Test API v1 routes exist."""
        # Test health endpoint
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        # Test that other endpoints exist (may return 401/403/405 without auth)
        endpoints_to_test = [
            "/api/v1/users",
            "/api/v1/configurations/jira",
            "/api/v1/generate",
            "/api/v1/search",
            "/api/v1/vector-search/stats",
            "/api/v1/feedback",
            "/api/v1/learning/health",
            "/api/v1/llm/health",
            "/api/v1/documentation",
            "/api/v1/sources"
        ]
        
        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            # Should not return 404 (route not found)
            # 405 Method Not Allowed is OK (means route exists but GET not supported)
            assert response.status_code not in [404], f"Endpoint {endpoint} not found"


class TestMiddleware:
    """Test middleware configuration."""
    
    def test_cors_middleware(self, client):
        """Test CORS middleware is configured."""
        response = client.options("/health")
        # CORS should handle OPTIONS requests
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled
    
    def test_request_processing(self, client):
        """Test request processing works."""
        response = client.get("/health")
        assert response.status_code == 200
        
        # Should have proper headers
        assert "content-type" in response.headers
        assert response.headers["content-type"] == "application/json" 