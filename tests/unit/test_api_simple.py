"""
Упрощенные тесты API
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app


@pytest.fixture
def client():
    """Фикстура для тестового клиента"""
    return TestClient(app)


def test_root_endpoint(client):
    """Тест корневого endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "AI Assistant API"
    assert "version" in data
    assert "features" in data
    assert isinstance(data["features"], list)


def test_health_check(client):
    """Тест проверки здоровья приложения"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@patch('app.api.v1.data_sources.get_current_user')
def test_data_sources_endpoint_with_auth(mock_auth, client):
    """Тест endpoint источников данных с мокированной аутентификацией"""
    # Настройка мока аутентификации
    mock_auth.return_value = {
        "sub": "test_user",
        "user_id": "test_user",
        "email": "test@example.com",
        "scopes": ["user"]
    }
    
    response = client.get("/api/v1/data-sources/")
    
    # Должен вернуть успешный ответ с mock данными
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2  # У нас 2 mock источника
    
    # Проверяем структуру первого источника
    first_source = data[0]
    assert "job_id" in first_source
    assert "source_type" in first_source
    assert "source_name" in first_source
    assert "enabled" in first_source


@patch('app.api.v1.data_sources.get_current_user')
def test_create_data_source(mock_auth, client):
    """Тест создания источника данных"""
    mock_auth.return_value = {
        "sub": "test_user",
        "user_id": "test_user",
        "email": "test@example.com",
        "scopes": ["user"]
    }
    
    new_source = {
        "source_type": "confluence",
        "source_name": "test_confluence",
        "enabled": True,
        "config": {"url": "https://test.atlassian.net"},
        "sync_schedule": "0 2 * * *",
        "incremental": True
    }
    
    response = client.post("/api/v1/data-sources/", json=new_source)
    
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "confluence_test_confluence"
    assert data["source_type"] == "confluence"
    assert data["source_name"] == "test_confluence"
    assert data["enabled"] is True


def test_api_structure():
    """Тест структуры API"""
    # Проверяем что все необходимые модули импортируются
    from app.api.v1 import data_sources, search_advanced
    from services import search_service, data_source_service
    from models import document, search
    
    # Проверяем что роутеры существуют
    assert hasattr(data_sources, 'router')
    assert hasattr(search_advanced, 'router')
    
    # Проверяем что сервисы существуют
    assert hasattr(search_service, 'SearchService')
    assert hasattr(search_service, 'get_search_service')
    assert hasattr(data_source_service, 'DataSourceService')
    assert hasattr(data_source_service, 'get_data_source_service')


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 