"""
FINAL FIXED Unit Tests for Advanced Search API 
Полное исправление проблем с authentication и search service mock
"""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
import json

# Import the FastAPI app
try:
    from app.main import app
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from app.main import app


class TestAdvancedSearchAPIFinalFixed:
    """Final fixed tests for Advanced Search API"""
    
    @pytest.fixture
    def client_with_mocks(self):
        """Test client fixture with both auth and search service mocks"""
        from app.security.auth import get_current_user
        from services.search_service import get_search_service
        
        # Mock authentication
        def mock_get_current_user():
            return {
                "id": "test_user_123",
                "sub": "test_user_123", 
                "user_id": "test_user_123",
                "email": "test@example.com",
                "username": "testuser",
                "roles": ["user"],
                "is_active": True,
                "permissions": ["search", "export", "filter"],
                "scopes": ["basic", "search", "export"]
            }
        
        # Mock search service
        async def mock_get_search_service():
            mock_service = Mock()
            # Mock для filter suggestions
            mock_service.get_source_statistics = Mock(return_value={
                "confluence_spaces": {"Engineering": 50, "Product": 30},
                "content_types": {"documentation": 100, "requirements": 75}
            })
            # Mock для advanced search
            mock_service.advanced_search = AsyncMock(return_value={
                "results": [
                    {"id": "doc1", "title": "Test Document 1"},
                    {"id": "doc2", "title": "Test Document 2"}
                ],
                "total_results": 2,
                "search_time_ms": 125.0
            })
            return mock_service
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_search_service] = mock_get_search_service
        
        yield TestClient(app)
        
        # Clean up after test
        app.dependency_overrides.clear()


class TestFilterSuggestionsAPIFinalFixed(TestAdvancedSearchAPIFinalFixed):
    """Final fixed tests for Filter Suggestions API"""
    
    def test_get_filter_suggestions_success(self, client_with_mocks):
        """Test getting filter suggestions with proper auth and service mock"""
        
        # Make request with CORRECT path
        response = client_with_mocks.get("/api/v1/search/advanced/filters/suggestions")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify structure
        for suggestion in data:
            assert "filter_type" in suggestion
            assert "filter_name" in suggestion
            assert "values" in suggestion
    
    def test_get_filter_suggestions_specific_type(self, client_with_mocks):
        """Test getting specific type filter suggestions"""
        
        # Make request with filter type and CORRECT path
        response = client_with_mocks.get("/api/v1/search/advanced/filters/suggestions?filter_type=sources")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_filter_suggestions_unauthorized(self):
        """Test filter suggestions without authentication"""
        from app.security.auth import get_current_user
        
        # Mock no user (unauthorized)
        def mock_get_none_user():
            return None
        
        app.dependency_overrides[get_current_user] = mock_get_none_user
        client = TestClient(app)
        
        response = client.get("/api/v1/search/advanced/filters/suggestions")
        
        # Should return 401 Unauthorized
        assert response.status_code in [401, 403]
        
        # Clean up
        app.dependency_overrides.clear()


class TestFilterPresetsAPIFinalFixed(TestAdvancedSearchAPIFinalFixed):
    """Final fixed tests for Filter Presets API"""
    
    def test_get_filter_presets_success(self, client_with_mocks):
        """Test getting filter presets with proper auth"""
        
        # Make request with CORRECT path
        response = client_with_mocks.get("/api/v1/search/advanced/filters/presets")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "presets" in data
        assert "total_presets" in data
        assert isinstance(data["presets"], dict)
        assert data["total_presets"] > 0
        
        # Check preset structure
        for preset_key, preset_data in data["presets"].items():
            assert "name" in preset_data
            assert "description" in preset_data
            assert "filters" in preset_data


class TestExportAPIFinalFixed(TestAdvancedSearchAPIFinalFixed):
    """Final fixed tests for Export API"""
    
    def test_export_search_results_json(self, client_with_mocks):
        """Test exporting search results in JSON format"""
        
        # Prepare export request
        export_data = {
            "query": "test query",
            "search_type": "semantic",
            "limit": 20
        }
        
        # Make request with CORRECT path
        response = client_with_mocks.post("/api/v1/search/advanced/export?format=json", json=export_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "export_id" in data
        assert data["format"] == "json"
        assert "download_url" in data
        assert "records_count" in data
    
    def test_export_search_results_csv(self, client_with_mocks):
        """Test exporting search results in CSV format"""
        
        # Prepare CSV export request
        export_data = {
            "query": "test query",
            "search_type": "semantic"
        }
        
        # Make request
        response = client_with_mocks.post("/api/v1/search/advanced/export?format=csv", json=export_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "csv"
    
    def test_export_search_results_invalid_format(self, client_with_mocks):
        """Test export with invalid format"""
        
        # Prepare invalid export request
        export_data = {
            "query": "test query"
        }
        
        # Make request with invalid format
        response = client_with_mocks.post("/api/v1/search/advanced/export?format=invalid_format", json=export_data)
        
        # Should return 400 Bad Request for invalid format
        assert response.status_code == 400
        data = response.json()
        assert "error" in data or "detail" in data


class TestAdvancedSearchIntegrationFinalFixed(TestAdvancedSearchAPIFinalFixed):
    """Integration tests for advanced search with proper mocking"""
    
    def test_full_search_workflow(self, client_with_mocks):
        """Test complete search workflow: suggestions -> presets -> search -> export"""
        
        # Step 1: Get filter suggestions
        response1 = client_with_mocks.get("/api/v1/search/advanced/filters/suggestions")
        assert response1.status_code == 200
        
        # Step 2: Get filter presets  
        response2 = client_with_mocks.get("/api/v1/search/advanced/filters/presets")
        assert response2.status_code == 200
        
        # Step 3: Perform advanced search
        search_data = {
            "query": "test query",
            "search_type": "semantic",
            "limit": 10
        }
        
        response3 = client_with_mocks.post("/api/v1/search/advanced/", json=search_data)
        assert response3.status_code == 200
        
        # Step 4: Export results
        export_data = {
            "query": "test query",
            "search_type": "semantic"
        }
        
        response4 = client_with_mocks.post("/api/v1/search/advanced/export?format=json", json=export_data)
        assert response4.status_code == 200


# Test summary
class TestAuthenticationFinalFixed:
    """Final verification that authentication mock works correctly"""
    
    def test_auth_mock_functionality(self):
        """Verify authentication mock works end-to-end"""
        from app.security.auth import get_current_user
        
        def mock_get_current_user():
            return {
                "id": "test_user_123",
                "email": "test@example.com",
                "is_active": True,
                "roles": ["user"]
            }
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        client = TestClient(app)
        
        # Test protected endpoint
        response = client.get("/api/v1/search/advanced/filters/suggestions")
        
        # Should not get 403 Forbidden anymore
        assert response.status_code != 403
        
        # Clean up
        app.dependency_overrides.clear()
    
    def test_search_service_mock_functionality(self):
        """Verify search service mock works correctly"""
        from services.search_service import get_search_service
        from app.security.auth import get_current_user
        
        # Mock both auth and search service
        def mock_get_current_user():
            return {"id": "test", "is_active": True}
        
        async def mock_get_search_service():
            mock_service = Mock()
            mock_service.get_source_statistics = Mock(return_value={
                "confluence_spaces": {"Test": 1}
            })
            return mock_service
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_search_service] = mock_get_search_service
        
        client = TestClient(app)
        response = client.get("/api/v1/search/advanced/filters/suggestions")
        
        # Should work with both mocks
        assert response.status_code == 200
        
        # Clean up
        app.dependency_overrides.clear()


if __name__ == "__main__":
    # Run the final fixed tests
    pytest.main([__file__, "-v", "--tb=short"]) 