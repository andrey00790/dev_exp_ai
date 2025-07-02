"""
Тесты для API управления источниками данных
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.v1.data_sources import (initialize_sync_scheduler, router,
                                     shutdown_sync_scheduler)
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

    @patch("app.api.v1.data_sources.get_current_user")
    @patch("app.api.v1.data_sources.sync_scheduler")
    def test_get_data_sources_success(
        self, mock_scheduler, mock_auth, client, mock_user
    ):
        """Тест успешного получения списка источников"""
        # Настройка моков
        mock_auth.return_value = mock_user
        mock_scheduler.get_sync_status.return_value = {
            "scheduler_running": True,
            "jobs": {
                "confluence_main": {
                    "source_type": "confluence",
                    "source_name": "main",
                    "enabled": True,
                    "schedule": "0 2 * * *",
                    "last_sync": "2024-01-15T10:00:00Z",
                    "next_sync": "2024-01-16T02:00:00Z",
                    "running": False,
                    "incremental": True,
                },
                "jira_main": {
                    "source_type": "jira",
                    "source_name": "main",
                    "enabled": True,
                    "schedule": "0 3 * * *",
                    "last_sync": "2024-01-15T11:00:00Z",
                    "next_sync": "2024-01-16T03:00:00Z",
                    "running": False,
                    "incremental": True,
                },
            },
        }

        # Выполнение запроса
        response = client.get("/api/v1/data-sources/")

        # Проверки
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        confluence_source = next(s for s in data if s["source_type"] == "confluence")
        assert confluence_source["source_name"] == "main"
        assert confluence_source["enabled"] is True
        assert confluence_source["sync_schedule"] == "0 2 * * *"
        assert confluence_source["running"] is False

    @patch("app.api.v1.data_sources.get_current_user")
    @patch("app.api.v1.data_sources.sync_scheduler")
    def test_get_data_sources_scheduler_unavailable(
        self, mock_scheduler, mock_auth, client, mock_user
    ):
        """Тест получения источников когда планировщик недоступен"""
        mock_auth.return_value = mock_user
        mock_scheduler = None

        response = client.get("/api/v1/data-sources/")

        assert response.status_code == 503
        assert "Sync scheduler not available" in response.json()["detail"]

    @patch("app.api.v1.data_sources.get_current_user")
    @patch("app.api.v1.data_sources.sync_scheduler")
    def test_create_data_source_success(
        self, mock_scheduler, mock_auth, client, mock_user
    ):
        """Тест успешного создания источника данных"""
        mock_auth.return_value = mock_user
        mock_scheduler.get_sync_status.return_value = {"jobs": {}}
        mock_scheduler.update_job_config.return_value = True

        new_source = {
            "source_type": "gitlab",
            "source_name": "new_gitlab",
            "enabled": True,
            "config": {"url": "https://gitlab.example.com", "token": "test_token"},
            "sync_schedule": "0 4 * * *",
            "incremental": True,
        }

        response = client.post("/api/v1/data-sources/", json=new_source)

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "gitlab_new_gitlab"
        assert data["source_type"] == "gitlab"
        assert data["source_name"] == "new_gitlab"
        assert "created successfully" in data["message"]

    @patch("app.api.v1.data_sources.get_current_user")
    @patch("app.api.v1.data_sources.sync_scheduler")
    def test_create_data_source_already_exists(
        self, mock_scheduler, mock_auth, client, mock_user
    ):
        """Тест создания источника который уже существует"""
        mock_auth.return_value = mock_user
        mock_scheduler.get_sync_status.return_value = {"jobs": {"gitlab_existing": {}}}

        new_source = {
            "source_type": "gitlab",
            "source_name": "existing",
            "enabled": True,
            "config": {},
            "sync_schedule": "0 4 * * *",
            "incremental": True,
        }

        response = client.post("/api/v1/data-sources/", json=new_source)

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    @patch("app.api.v1.data_sources.get_current_user")
    @patch("app.api.v1.data_sources.sync_scheduler")
    def test_update_data_source_success(
        self, mock_scheduler, mock_auth, client, mock_user
    ):
        """Тест успешного обновления источника данных"""
        mock_auth.return_value = mock_user
        mock_scheduler.update_job_config.return_value = True

        updated_source = {
            "source_type": "confluence",
            "source_name": "main",
            "enabled": False,
            "config": {"url": "https://updated.atlassian.net"},
            "sync_schedule": "0 6 * * *",
            "incremental": False,
        }

        response = client.put(
            "/api/v1/data-sources/confluence/main", json=updated_source
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "confluence_main"
        assert "updated successfully" in data["message"]

    @patch("app.api.v1.data_sources.get_current_user")
    @patch("app.api.v1.data_sources.sync_scheduler")
    def test_update_data_source_not_found(
        self, mock_scheduler, mock_auth, client, mock_user
    ):
        """Тест обновления несуществующего источника"""
        mock_auth.return_value = mock_user
        mock_scheduler.update_job_config.return_value = False

        updated_source = {
            "source_type": "confluence",
            "source_name": "nonexistent",
            "enabled": True,
            "config": {},
            "sync_schedule": "0 2 * * *",
            "incremental": True,
        }

        response = client.put(
            "/api/v1/data-sources/confluence/nonexistent", json=updated_source
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("app.api.v1.data_sources.get_current_user")
    @patch("app.api.v1.data_sources.sync_scheduler")
    def test_trigger_sync_success(self, mock_scheduler, mock_auth, client, mock_user):
        """Тест успешного запуска синхронизации"""
        mock_auth.return_value = mock_user

        response = client.post("/api/v1/data-sources/confluence/main/sync")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "confluence_main"
        assert data["message"] == "Sync started"
        assert "started_at" in data

    @patch("app.api.v1.data_sources.get_current_user")
    @patch("app.api.v1.data_sources.sync_scheduler")
    def test_get_sync_status_success(
        self, mock_scheduler, mock_auth, client, mock_user
    ):
        """Тест получения статуса синхронизации"""
        mock_auth.return_value = mock_user
        mock_scheduler.get_sync_status.return_value = {
            "scheduler_running": True,
            "jobs": {
                "confluence_main": {
                    "running": True,
                    "last_sync": "2024-01-15T10:00:00Z",
                }
            },
        }

        response = client.get("/api/v1/data-sources/sync/status")

        assert response.status_code == 200
        data = response.json()
        assert data["scheduler_running"] is True
        assert "confluence_main" in data["jobs"]


class TestSearchSourcesAPI:
    """Тесты для API настроек источников поиска"""

    @patch("app.api.v1.data_sources.get_current_user")
    @patch("app.api.v1.data_sources._get_user_search_config")
    @patch("app.api.v1.data_sources._get_available_sources")
    def test_get_user_search_sources_with_config(
        self, mock_available, mock_config, mock_auth, client, mock_user
    ):
        """Тест получения настроек поиска пользователя"""
        mock_auth.return_value = mock_user
        mock_config.return_value = {
            "user_id": "test_user_123",
            "enabled_sources": ["confluence_main", "jira_main"],
            "search_preferences": {},
        }

        response = client.get("/api/v1/data-sources/search-sources/test_user_123")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user_123"
        assert "confluence_main" in data["enabled_sources"]
        assert "jira_main" in data["enabled_sources"]

    @patch("app.api.v1.data_sources.get_current_user")
    @patch("app.api.v1.data_sources._get_user_search_config")
    @patch("app.api.v1.data_sources._get_available_sources")
    def test_get_user_search_sources_default(
        self, mock_available, mock_config, mock_auth, client, mock_user
    ):
        """Тест получения настроек по умолчанию"""
        mock_auth.return_value = mock_user
        mock_config.return_value = None
        mock_available.return_value = ["confluence_main", "jira_main", "gitlab_main"]

        response = client.get("/api/v1/data-sources/search-sources/test_user_123")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user_123"
        assert len(data["enabled_sources"]) == 3

    @patch("app.api.v1.data_sources.get_current_user")
    @patch("app.api.v1.data_sources._get_available_sources")
    @patch("app.api.v1.data_sources._save_user_search_config")
    def test_update_user_search_sources_success(
        self, mock_save, mock_available, mock_auth, client, mock_user
    ):
        """Тест успешного обновления настроек поиска"""
        mock_auth.return_value = mock_user
        mock_available.return_value = ["confluence_main", "jira_main", "gitlab_main"]
        mock_save.return_value = True

        config_update = {
            "user_id": "test_user_123",
            "enabled_sources": ["confluence_main", "gitlab_main"],
            "search_preferences": {},
        }

        response = client.put(
            "/api/v1/data-sources/search-sources/test_user_123", json=config_update
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user_123"
        assert "updated successfully" in data["message"]
        assert data["enabled_sources"] == ["confluence_main", "gitlab_main"]

    @patch("app.api.v1.data_sources.get_current_user")
    @patch("app.api.v1.data_sources._get_available_sources")
    def test_update_user_search_sources_invalid_sources(
        self, mock_available, mock_auth, client, mock_user
    ):
        """Тест обновления с недопустимыми источниками"""
        mock_auth.return_value = mock_user
        mock_available.return_value = ["confluence_main", "jira_main"]

        config_update = {
            "user_id": "test_user_123",
            "enabled_sources": ["confluence_main", "invalid_source"],
            "search_preferences": {},
        }

        response = client.put(
            "/api/v1/data-sources/search-sources/test_user_123", json=config_update
        )

        assert response.status_code == 400
        assert "Invalid sources" in response.json()["detail"]


class TestGenerationSourcesAPI:
    """Тесты для API настроек источников генерации"""

    @patch("app.api.v1.data_sources.get_current_user")
    def test_get_generation_sources_default(self, mock_auth, client, mock_user):
        """Тест получения настроек генерации по умолчанию"""
        mock_auth.return_value = mock_user

        response = client.get("/api/v1/data-sources/generation-sources")

        assert response.status_code == 200
        data = response.json()
        assert data["use_all_sources"] is True
        assert data["excluded_sources"] == []

    @patch("app.api.v1.data_sources.get_current_user")
    @patch("app.api.v1.data_sources._save_generation_config")
    def test_update_generation_sources_success(
        self, mock_save, mock_auth, client, mock_user
    ):
        """Тест успешного обновления настроек генерации"""
        mock_auth.return_value = mock_user
        mock_save.return_value = True

        config_update = {"use_all_sources": False, "excluded_sources": ["jira_main"]}

        response = client.put(
            "/api/v1/data-sources/generation-sources", json=config_update
        )

        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"]
        assert data["use_all_sources"] is False
        assert data["excluded_sources"] == ["jira_main"]


class TestDataSourcesIntegration:
    """Интеграционные тесты для API источников данных"""

    @patch("app.api.v1.data_sources.get_current_user")
    @patch("app.api.v1.data_sources.sync_scheduler")
    def test_full_source_lifecycle(self, mock_scheduler, mock_auth, client, mock_user):
        """Тест полного жизненного цикла источника данных"""
        mock_auth.return_value = mock_user

        # 1. Создание источника
        mock_scheduler.get_sync_status.return_value = {"jobs": {}}
        mock_scheduler.update_job_config.return_value = True

        new_source = {
            "source_type": "confluence",
            "source_name": "test_confluence",
            "enabled": True,
            "config": {"url": "https://test.atlassian.net"},
            "sync_schedule": "0 2 * * *",
            "incremental": True,
        }

        create_response = client.post("/api/v1/data-sources/", json=new_source)
        assert create_response.status_code == 200

        # 2. Получение списка источников
        mock_scheduler.get_sync_status.return_value = {
            "jobs": {
                "confluence_test_confluence": {
                    "source_type": "confluence",
                    "source_name": "test_confluence",
                    "enabled": True,
                    "schedule": "0 2 * * *",
                    "last_sync": None,
                    "next_sync": "2024-01-16T02:00:00Z",
                    "running": False,
                    "incremental": True,
                }
            }
        }

        list_response = client.get("/api/v1/data-sources/")
        assert list_response.status_code == 200
        sources = list_response.json()
        assert len(sources) == 1
        assert sources[0]["source_name"] == "test_confluence"

        # 3. Запуск синхронизации
        sync_response = client.post(
            "/api/v1/data-sources/confluence/test_confluence/sync"
        )
        assert sync_response.status_code == 200

        # 4. Обновление источника
        updated_source = {
            "source_type": "confluence",
            "source_name": "test_confluence",
            "enabled": False,
            "config": {"url": "https://updated.atlassian.net"},
            "sync_schedule": "0 6 * * *",
            "incremental": False,
        }

        update_response = client.put(
            "/api/v1/data-sources/confluence/test_confluence", json=updated_source
        )
        assert update_response.status_code == 200

        # 5. Отключение источника (удаление)
        delete_response = client.delete(
            "/api/v1/data-sources/confluence/test_confluence"
        )
        assert delete_response.status_code == 200

    @patch("app.api.v1.data_sources.get_current_user")
    def test_search_preferences_workflow(self, mock_auth, client, mock_user):
        """Тест рабочего процесса настроек поиска"""
        mock_auth.return_value = mock_user

        with patch(
            "app.api.v1.data_sources._get_user_search_config"
        ) as mock_get_config, patch(
            "app.api.v1.data_sources._get_available_sources"
        ) as mock_available, patch(
            "app.api.v1.data_sources._save_user_search_config"
        ) as mock_save:

            # Настройка моков
            mock_get_config.return_value = None
            mock_available.return_value = [
                "confluence_main",
                "jira_main",
                "gitlab_main",
            ]
            mock_save.return_value = True

            # 1. Получение настроек по умолчанию
            get_response = client.get(
                "/api/v1/data-sources/search-sources/test_user_123"
            )
            assert get_response.status_code == 200
            data = get_response.json()
            assert len(data["enabled_sources"]) == 3

            # 2. Обновление настроек
            config_update = {
                "user_id": "test_user_123",
                "enabled_sources": ["confluence_main", "gitlab_main"],
                "search_preferences": {"prefer_recent": True},
            }

            update_response = client.put(
                "/api/v1/data-sources/search-sources/test_user_123", json=config_update
            )
            assert update_response.status_code == 200

            # Проверяем что save был вызван с правильными параметрами
            mock_save.assert_called_once()
            args, kwargs = mock_save.call_args
            assert args[0] == "test_user_123"
            assert "confluence_main" in args[1].enabled_sources
            assert "gitlab_main" in args[1].enabled_sources
            assert "jira_main" not in args[1].enabled_sources


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Автоматическая настройка и очистка для каждого теста"""
    # Настройка перед тестом
    yield
    # Очистка после теста
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
