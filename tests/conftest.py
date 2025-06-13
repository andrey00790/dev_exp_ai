import pytest
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    app = create_app()
    return TestClient(app) 