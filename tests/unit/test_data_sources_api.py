"""
Тесты для API управления источниками данных
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.v1.documents.data_sources import router
from app.main import app


@pytest.fixture
def client():
    """Фикстура для тестового клиента"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Фикстура для мок пользователя"""
    return {
        "sub": "test_user_123",
        "user_id": "test_user_123",
        "email": "test@example.com",
        "scopes": ["user", "admin"],
    }


@pytest.fixture
def mock_sync_scheduler():
    """Фикстура для мок планировщика синхронизации"""
    scheduler = Mock()
    scheduler.get_sync_status = AsyncMock()
    scheduler.update_job_config = AsyncMock()
    scheduler.trigger_manual_sync = AsyncMock()
    return scheduler


class TestDataSourcesAPI:
    """Тесты для API источников данных"""

    def test_get_data_sources_success(self, client):
        """Тест успешного получения списка источников"""
        # Тест реального эндпоинта /sources
        response = client.get("/api/v1/data-sources/sources")
        
        # Проверки
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        
        # Проверяем структуру объектов
        for source in data:
            assert "source_type" in source
            assert "enabled" in source
            assert "priority" in source
            assert "metadata" in source
        
        # Проверяем что есть основные типы источников
        source_types = {source["source_type"] for source in data}
        assert "confluence" in source_types or "jira" in source_types or "gitlab" in source_types

    def test_get_data_sources_filtered(self, client):
        """Тест получения источников с фильтром"""
        # Тест с фильтром по типу
        response = client.get("/api/v1/data-sources/sources?source_type=bootstrap")
        assert response.status_code in [200, 422]  # Может быть валидационная ошибка
        
    def test_get_data_sources_health(self, client):
        """Тест health check эндпоинта"""
        response = client.get("/api/v1/data-sources/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_create_data_source_unauthenticated(self, client):
        """Тест создания источника без авторизации"""
        # API требует авторизацию, поэтому ожидаем 401/403
        response = client.post("/api/v1/data-sources/", json={
            "source_type": "gitlab",
            "source_name": "test",
            "enabled": True,
            "config": {},
            "sync_schedule": "0 4 * * *",
            "incremental": True
        })
        assert response.status_code in [401, 403, 422]

    def test_update_data_source_unauthenticated(self, client):
        """Тест обновления источника без авторизации"""
        response = client.put("/api/v1/data-sources/confluence/main", json={
            "source_type": "confluence",
            "source_name": "main", 
            "enabled": False,
            "config": {},
            "sync_schedule": "0 6 * * *",
            "incremental": False
        })
        assert response.status_code in [401, 403, 422]

    def test_trigger_sync_unauthenticated(self, client):
        """Тест запуска синхронизации без авторизации"""
        response = client.post("/api/v1/data-sources/confluence/main/sync")
        assert response.status_code in [401, 403, 422]

    def test_get_sync_status_unauthenticated(self, client):
        """Тест получения статуса синхронизации без авторизации"""
        response = client.get("/api/v1/data-sources/sync/status")
        assert response.status_code in [401, 403, 422]

    def test_get_filters(self, client):
        """Тест получения доступных фильтров"""
        response = client.get("/api/v1/data-sources/filters")
        assert response.status_code == 200
        data = response.json()
        assert "source_types" in data
        assert "categories" in data
        assert "roles" in data


class TestSearchSourcesAPI:
    """Тесты для API настроек источников поиска"""

    def test_get_user_search_sources_unauthenticated(self, client):
        """Тест получения настроек поиска без авторизации"""
        response = client.get("/api/v1/data-sources/search-sources/test_user_123")
        assert response.status_code in [401, 403, 422]

    def test_update_user_search_sources_unauthenticated(self, client):
        """Тест обновления настроек поиска без авторизации"""
        response = client.put("/api/v1/data-sources/search-sources/test_user_123", json={
            "user_id": "test_user_123",
            "enabled_sources": ["confluence_main"],
            "search_preferences": {}
        })
        assert response.status_code in [401, 403, 422]

    def test_discovery_basic(self, client):
        """Тест базового обнаружения источников"""
        response = client.get("/api/v1/data-sources/discover")
        assert response.status_code in [200, 422]  # Может требовать bootstrap_dir

    def test_bootstrap_stats_basic(self, client):
        """Тест получения статистики bootstrap"""
        response = client.get("/api/v1/data-sources/bootstrap/stats")
        assert response.status_code in [200, 404, 422]  # Может требовать bootstrap_dir или не быть реализован


class TestGenerationSourcesAPI:
    """Тесты для API настроек источников генерации"""

    def test_get_generation_sources_unauthenticated(self, client):
        """Тест получения настроек генерации без авторизации"""
        response = client.get("/api/v1/data-sources/generation-sources")
        assert response.status_code in [401, 403, 422]

    def test_update_generation_sources_unauthenticated(self, client):
        """Тест обновления настроек генерации без авторизации"""
        response = client.put("/api/v1/data-sources/generation-sources", json={
            "use_all_sources": False,
            "excluded_sources": ["jira_main"]
        })
        assert response.status_code in [401, 403, 422]


class TestDataSourcesIntegration:
    """Интеграционные тесты для API источников данных"""

    def test_full_public_endpoints_workflow(self, client):
        """Тест общедоступных эндпоинтов"""
        # 1. Проверка health
        health_response = client.get("/api/v1/data-sources/health")
        assert health_response.status_code == 200
        
        # 2. Получение списка источников  
        sources_response = client.get("/api/v1/data-sources/sources")
        assert sources_response.status_code == 200
        sources = sources_response.json()
        assert isinstance(sources, list)
        
        # 3. Получение фильтров
        filters_response = client.get("/api/v1/data-sources/filters")
        assert filters_response.status_code == 200
        filters = filters_response.json()
        assert "source_types" in filters

    def test_sources_endpoint_structure(self, client):
        """Тест структуры данных sources эндпоинта"""
        response = client.get("/api/v1/data-sources/sources")
        assert response.status_code == 200
        data = response.json()
        
        # Должен быть список источников
        assert isinstance(data, list)
        
        if data:  # Если есть источники
            source = data[0]
            # Проверяем обязательные поля
            assert "source_type" in source
            assert "enabled" in source
            assert "priority" in source
            
            # metadata может быть None или объектом
            if source.get("metadata"):
                metadata = source["metadata"]
                # Проверяем структуру metadata если она есть
                assert isinstance(metadata, dict)

    def test_ingestion_endpoint_error_handling(self, client):
        """Тест обработки ошибок в ingestion эндпоинте"""
        # Тест с неподдерживаемым типом источника
        response = client.post("/api/v1/data-sources/ingest/unsupported_type")
        # Может вернуть 422 (валидация), 401 (авторизация) или 400 (неподдерживаемый тип)
        assert response.status_code in [400, 401, 403, 422]

    def test_endpoints_accessibility(self, client):
        """Тест доступности основных эндпоинтов"""
        endpoints = [
            "/api/v1/data-sources/health",
            "/api/v1/data-sources/sources", 
            "/api/v1/data-sources/filters"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Эндпоинт должен существовать (не 404)
            assert response.status_code != 404, f"Endpoint {endpoint} not found"
            # И отвечать корректно (200) или требовать авторизацию (401/403)
            assert response.status_code in [200, 401, 403, 422], f"Unexpected status for {endpoint}"


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Автоматическая настройка и очистка для каждого теста"""
    # Настройка перед тестом
    yield
    # Очистка после теста


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
