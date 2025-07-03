"""
Debug test to understand authentication issues
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

try:
    from app.main import app
except ImportError:
    import os
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from app.main import app


def test_simple_health_check():
    """Test basic health check without auth"""
    client = TestClient(app)
    response = client.get("/health")
    print(f"Health check response: {response.status_code}")
    assert response.status_code == 200


def test_protected_endpoint_without_auth():
    """Test what happens to protected endpoint without auth"""
    client = TestClient(app)
    response = client.get("/api/v1/search/advanced/filters/suggestions")
    print(f"Protected endpoint without auth: {response.status_code}")
    print(f"Response body: {response.text}")
    # Expect 401 or 403
    assert response.status_code in [401, 403]


@patch("app.api.v1.search.search_advanced.get_current_user")
def test_protected_endpoint_with_mock_auth(mock_get_user):
    """Test protected endpoint with mocked auth"""
    client = TestClient(app)

    # Mock user
    mock_get_user.return_value = {
        "id": "test_user",
        "email": "test@example.com",
        "is_active": True,
        "roles": ["user"],
    }

    response = client.get("/api/v1/search/advanced/filters/suggestions")
    print(f"Protected endpoint with mock auth: {response.status_code}")
    print(f"Response body: {response.text}")
    print(f"Mock called: {mock_get_user.called}")

    # This should work if mock is correctly applied
    # But let's see what actually happens


@pytest.fixture
def mock_current_user():
    """Mock функция для текущего пользователя"""
    with patch("app.api.v1.search.search_advanced.get_current_user") as mock_user:
        mock_user.return_value = Mock(
            id=1, username="test_user", email="test@example.com"
        )
        yield mock_user


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
