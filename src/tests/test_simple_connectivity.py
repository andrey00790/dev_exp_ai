import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from starlette.middleware import Middleware
from app.security.auth import User, AuthMiddleware, get_password_hash, USERS_DB
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_smoke_test_app() -> FastAPI:
    from app.api.v1 import auth, users
    
    middleware_config = [
        Middleware(AuthMiddleware)
    ]
    
    app = FastAPI(title="Smoke Test App", middleware=middleware_config)
    
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")

    @app.get("/health_smoke")
    def health_check():
        return {"status": "ok"}

    return app

@pytest.fixture(scope="module")
def smoke_app() -> FastAPI:
    return create_smoke_test_app()

@pytest.fixture(scope="module")
def client(smoke_app: FastAPI) -> TestClient:
    return TestClient(smoke_app)

@pytest.fixture(scope="module")
def authenticated_client(smoke_app: FastAPI) -> TestClient:
    def mock_get_current_user():
        return User(
            user_id="smoke_test_user",
            email="smoke@test.com",
            name="Smoke User",
            is_active=True,
            scopes=["basic"]
        )
    
    from app.security.auth import get_current_user
    smoke_app.dependency_overrides[get_current_user] = mock_get_current_user
    return TestClient(smoke_app)

def test_health_check(client: TestClient):
    response = client.get("/health_smoke")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_unauthenticated_access(client: TestClient):
    response = client.get("/api/v1/users/current/settings")
    assert response.status_code == 401

def test_authenticated_access(authenticated_client: TestClient):
    response = authenticated_client.get("/api/v1/users/current/settings")
    assert response.status_code != 401
    assert response.status_code == 404

def test_login_for_access_token(client: TestClient):
    if "admin@example.com" not in USERS_DB:
        USERS_DB["admin@example.com"] = {
            "name": "Admin",
            "hashed_password": get_password_hash("admin"),
            "email": "admin@example.com",
            "user_id": "admin_user",
            "scopes": ["admin", "basic"],
        }
    response = client.post("/api/v1/auth/token", data={"username": "admin@example.com", "password": "admin"})
    assert response.status_code == 200
    assert "access_token" in response.json()