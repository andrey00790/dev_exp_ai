import pytest
from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "uptime" in data
    assert "environment" in data
    assert "checks" in data

    # Проверяем структуру checks
    checks = data["checks"]
    assert "api" in checks
    assert "memory" in checks
    assert "database" in checks
