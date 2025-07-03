"""
FINAL FIXED Unit Tests for Advanced Search API 
✅ Authentication: dependency override
✅ Search service: AsyncMock
✅ API paths: corrected
"""

from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

try:
    from app.main import app
except ImportError:
    import os
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from app.main import app


class TestAdvancedSearchAPIFinalFixed:
    """Final fixed tests for Advanced Search API"""

    @pytest.fixture
    def client_with_mocks(self):
        """Test client with working auth and search service mocks"""
        from app.security.auth import get_current_user
        from domain.integration.search_service import get_search_service

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
                "scopes": ["basic", "search", "export"],
            }

        # Mock search service with AsyncMock
        async def mock_get_search_service():
            mock_service = Mock()
            mock_service.get_source_statistics = AsyncMock(
                return_value={
                    "confluence_spaces": {"Engineering": 50, "Product": 30},
                    "content_types": {"documentation": 100, "requirements": 75},
                }
            )
            mock_service.advanced_search = AsyncMock(
                return_value={
                    "results": [
                        {"id": "doc1", "title": "Test Document 1"},
                        {"id": "doc2", "title": "Test Document 2"},
                    ],
                    "total_results": 2,
                    "search_time_ms": 125.0,
                }
            )
            return mock_service

        # Override dependencies
        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_search_service] = mock_get_search_service

        yield TestClient(app)

        # Clean up
        app.dependency_overrides.clear()


class TestFilterSuggestionsAPIFixed(TestAdvancedSearchAPIFinalFixed):
    """Fixed tests for Filter Suggestions API"""

    def test_get_filter_suggestions_success(self, client_with_mocks):
        """Test getting filter suggestions - WORKING VERSION"""

        response = client_with_mocks.get("/api/v1/search/advanced/filters/suggestions")

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
        """Test specific type filter suggestions"""

        response = client_with_mocks.get(
            "/api/v1/search/advanced/filters/suggestions?filter_type=sources"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestFilterPresetsAPIFixed(TestAdvancedSearchAPIFinalFixed):
    """Fixed tests for Filter Presets API"""

    def test_get_filter_presets_success(self, client_with_mocks):
        """Test getting filter presets"""

        response = client_with_mocks.get("/api/v1/search/advanced/filters/presets")

        assert response.status_code == 200
        data = response.json()
        assert "presets" in data
        assert "total_presets" in data
        assert isinstance(data["presets"], dict)
        assert data["total_presets"] > 0


class TestExportAPIFixed(TestAdvancedSearchAPIFinalFixed):
    """Fixed tests for Export API"""

    def test_export_search_results_json(self, client_with_mocks):
        """Test JSON export"""

        export_data = {"query": "test query", "search_type": "semantic", "limit": 20}

        response = client_with_mocks.post(
            "/api/v1/search/advanced/export?format=json", json=export_data
        )

        assert response.status_code == 200
        data = response.json()
        assert "export_id" in data
        assert data["format"] == "json"
        assert "download_url" in data

    def test_export_search_results_invalid_format(self, client_with_mocks):
        """Test invalid export format"""

        export_data = {"query": "test query"}

        response = client_with_mocks.post(
            "/api/v1/search/advanced/export?format=invalid_format", json=export_data
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data or "detail" in data


class TestAdvancedSearchIntegrationFixed(TestAdvancedSearchAPIFinalFixed):
    """Integration workflow tests"""

    def test_full_search_workflow(self, client_with_mocks):
        """Test complete workflow: suggestions -> presets -> search -> export"""

        # Step 1: Filter suggestions
        response1 = client_with_mocks.get("/api/v1/search/advanced/filters/suggestions")
        assert response1.status_code == 200

        # Step 2: Filter presets
        response2 = client_with_mocks.get("/api/v1/search/advanced/filters/presets")
        assert response2.status_code == 200

        # Step 3: Advanced search
        search_data = {"query": "test query", "search_type": "semantic", "limit": 10}
        response3 = client_with_mocks.post("/api/v1/search/advanced/", json=search_data)
        assert response3.status_code == 200

        # Step 4: Export results
        export_data = {"query": "test query", "search_type": "semantic"}
        response4 = client_with_mocks.post(
            "/api/v1/search/advanced/export?format=json", json=export_data
        )
        assert response4.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
