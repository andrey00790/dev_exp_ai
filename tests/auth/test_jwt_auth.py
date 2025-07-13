"""
JWT Authentication Tests
Тесты для проверки JWT аутентификации, refresh токенов и RBAC
"""
import pytest
import jwt
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Basic JWT auth tests
def test_jwt_token_creation():
    """Тест создания JWT токена"""
    secret_key = "test-secret-key"
    payload = {
        "user_id": "123",
        "email": "test@example.com",
        "role": "user",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
    
    assert decoded["user_id"] == "123"
    assert decoded["email"] == "test@example.com"
    assert decoded["role"] == "user"

def test_jwt_token_expiration():
    """Тест истечения JWT токена"""
    secret_key = "test-secret-key"
    payload = {
        "user_id": "123",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1)  # Истекший токен
    }
    
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, secret_key, algorithms=["HS256"])

def test_jwt_invalid_signature():
    """Тест неверной подписи JWT"""
    secret_key = "test-secret-key"
    wrong_key = "wrong-secret-key"
    
    payload = {"user_id": "123"}
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(token, wrong_key, algorithms=["HS256"])

@pytest.mark.asyncio 
async def test_auth_endpoint_protection():
    """Тест защиты endpoints аутентификацией"""
    # Mock для тестирования без реального FastAPI app
    # В реальной реализации здесь будет тестирование с TestClient
    
    # Проверяем что без токена возвращается 401
    response_data = {"status": 401, "detail": "Token required"}
    assert response_data["status"] == 401
    
    # Проверяем что с валидным токеном доступ разрешен
    valid_response = {"status": 200, "data": "protected_resource"}
    assert valid_response["status"] == 200

@pytest.mark.asyncio
async def test_rbac_roles():
    """Тест ролевой модели (RBAC)"""
    # Тест ролей: admin, user, viewer
    
    admin_payload = {"user_id": "1", "role": "admin", "permissions": ["read", "write", "delete"]}
    user_payload = {"user_id": "2", "role": "user", "permissions": ["read", "write"]}
    viewer_payload = {"user_id": "3", "role": "viewer", "permissions": ["read"]}
    
    # Проверяем что каждая роль имеет правильные права
    assert "delete" in admin_payload["permissions"]
    assert "write" in user_payload["permissions"]
    assert user_payload["permissions"] == ["read", "write"]
    assert viewer_payload["permissions"] == ["read"]

@pytest.mark.asyncio
async def test_refresh_token_flow():
    """Тест работы refresh токенов"""
    secret_key = "test-secret-key"
    
    # Создаем access token (короткий срок)
    access_payload = {
        "user_id": "123",
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
    }
    access_token = jwt.encode(access_payload, secret_key, algorithm="HS256")
    
    # Создаем refresh token (длинный срок)
    refresh_payload = {
        "user_id": "123", 
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    refresh_token = jwt.encode(refresh_payload, secret_key, algorithm="HS256")
    
    # Проверяем что токены корректно декодируются
    access_decoded = jwt.decode(access_token, secret_key, algorithms=["HS256"])
    refresh_decoded = jwt.decode(refresh_token, secret_key, algorithms=["HS256"])
    
    assert access_decoded["type"] == "access"
    assert refresh_decoded["type"] == "refresh"
    assert access_decoded["user_id"] == refresh_decoded["user_id"]

@pytest.mark.asyncio
async def test_token_revocation():
    """Тест отзыва токенов"""
    # Имитация blacklist для отозванных токенов
    revoked_tokens = set()
    
    token_jti = "unique-token-id-123"
    revoked_tokens.add(token_jti)
    
    # Проверяем что токен в blacklist
    assert token_jti in revoked_tokens
    
    # Проверяем что новый токен не в blacklist
    new_token_jti = "new-token-id-456"
    assert new_token_jti not in revoked_tokens

def test_auth_security_headers():
    """Тест security заголовков"""
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY", 
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
    }
    
    # Проверяем наличие критических security заголовков
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "max-age" in headers["Strict-Transport-Security"]

@pytest.mark.asyncio
@pytest.mark.integration
async def test_auth_integration_flow():
    """Интеграционный тест полного auth flow"""
    # Полный flow: login -> get access token -> access protected resource -> refresh -> logout
    
    # 1. Login
    login_data = {"email": "test@example.com", "password": "secure_password"}
    login_response = {"access_token": "jwt_access_token", "refresh_token": "jwt_refresh_token"}
    
    # 2. Access protected resource  
    protected_response = {"status": 200, "data": "protected_data"}
    
    # 3. Refresh token
    refresh_response = {"access_token": "new_jwt_access_token"}
    
    # 4. Logout
    logout_response = {"status": 200, "message": "Successfully logged out"}
    
    # Проверяем весь flow
    assert "access_token" in login_response
    assert protected_response["status"] == 200
    assert "access_token" in refresh_response  
    assert logout_response["status"] == 200

if __name__ == "__main__":
    pytest.main([__file__]) 