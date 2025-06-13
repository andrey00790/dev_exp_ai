import pytest

try:
    from fastapi.testclient import TestClient
    from app.main import create_app
    _FASTAPI_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency may be missing
    _FASTAPI_AVAILABLE = False

@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    if not _FASTAPI_AVAILABLE:
        pytest.skip("FastAPI dependencies are not available")

    app = create_app()
    return TestClient(app)
