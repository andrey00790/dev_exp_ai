import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure project root is importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.main import create_app

@pytest.fixture
def client():
    """Create a FastAPI test client."""
    app = create_app()
    return TestClient(app)
