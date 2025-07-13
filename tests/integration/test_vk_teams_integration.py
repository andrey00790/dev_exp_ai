"""
Интеграционные тесты для VK Teams бота
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from main import app

client = TestClient(app)


class TestVKTeamsBotIntegration:
    """Тесты интеграции VK Teams бота"""

    def test_bot_health_endpoint(self):
        """Тест health check endpoint бота"""
        response = client.get("/api/v1/vk-teams/bot/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data

    def test_webhook_health_endpoint(self):
        """Тест health check endpoint webhook"""
        response = client.get("/api/v1/vk-teams/webhook/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "vk-teams-webhook"

    def test_webhook_test_endpoint(self):
        """Тест тестового webhook endpoint"""
        test_data = {
            "test_event": "message",
            "test_data": {"text": "Hello Bot!"}
        }
        
        response = client.post(
            "/api/v1/vk-teams/webhook/test",
            json=test_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Тест webhook'а успешен"

    @patch('domain.vk_teams.bot_service.get_vk_teams_bot_service')
    def test_bot_status_unauthorized(self, mock_service):
        """Тест получения статуса без авторизации"""
        response = client.get("/api/v1/vk-teams/bot/status")
        # Ожидаем ошибку авторизации
        assert response.status_code in [401, 422]

    def test_webhook_event_processing(self):
        """Тест обработки webhook события"""
        event_data = {
            "eventType": "newMessage",
            "eventId": "test-event-123",
            "timestamp": 1640995200,
            "payload": {
                "chat": {"chatId": "test-chat"},
                "from": {"userId": "test-user"},
                "text": "Hello"
            }
        }
        
        response = client.post(
            "/api/v1/vk-teams/webhook/events",
            json=event_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["event_id"] == "test-event-123"

    def test_webhook_message_processing(self):
        """Тест обработки сообщения через webhook"""
        message_data = {
            "eventType": "newMessage",
            "payload": {
                "chat": {"chatId": "test-chat"},
                "from": {"userId": "test-user"},
                "text": "Test message"
            }
        }
        
        response = client.post(
            "/api/v1/vk-teams/webhook/messages",
            json=message_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    def test_webhook_callback_processing(self):
        """Тест обработки callback через webhook"""
        callback_data = {
            "eventType": "callbackQuery",
            "payload": {
                "callbackData": "action:search",
                "from": {"userId": "test-user"},
                "message": {"chat": {"chatId": "test-chat"}}
            }
        }
        
        response = client.post(
            "/api/v1/vk-teams/webhook/callback",
            json=callback_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    def test_invalid_webhook_data(self):
        """Тест обработки невалидных данных webhook"""
        invalid_data = {
            "invalid": "data"
        }
        
        response = client.post(
            "/api/v1/vk-teams/webhook/events",
            json=invalid_data
        )
        
        # Должен обработать ошибку gracefully
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_bot_adapter_creation(self):
        """Тест создания экземпляра bot adapter"""
        from domain.vk_teams.bot_adapter_simple import get_vk_teams_bot_adapter
        
        adapter = await get_vk_teams_bot_adapter()
        assert adapter is not None
        assert hasattr(adapter, 'handle_event')
        assert hasattr(adapter, 'handle_message_event')

    @pytest.mark.asyncio
    async def test_bot_service_creation(self):
        """Тест создания экземпляра bot service"""
        from domain.vk_teams.bot_service import get_vk_teams_bot_service
        
        service = await get_vk_teams_bot_service()
        assert service is not None
        assert hasattr(service, 'configure_bot')
        assert hasattr(service, 'start_bot')
        assert hasattr(service, 'stop_bot')

    def test_bot_models_import(self):
        """Тест импорта моделей бота"""
        from domain.vk_teams.bot_models import BotConfig, BotMessage, BotStats
        
        # Создаем тестовые экземпляры
        config = BotConfig(
            bot_token="test_token",
            api_url="https://test.com"
        )
        assert config.bot_token == "test_token"
        assert config.is_user_allowed("any_user") is True  # Пустой список = разрешено всем
        
        message = BotMessage(
            chat_id="test_chat",
            user_id="test_user",
            text="Test message"
        )
        assert message.chat_id == "test_chat"
        assert message.is_from_bot is False
        
        stats = BotStats()
        assert stats.total_messages == 0
        stats.record_message(message)
        assert stats.total_messages == 1

    def test_main_app_includes_vk_teams_routes(self):
        """Тест что VK Teams роутеры подключены к приложению"""
        # Проверяем что роуты VK Teams присутствуют в приложении
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        
        vk_teams_routes = [
            route for route in routes 
            if '/vk-teams/' in route
        ]
        
        assert len(vk_teams_routes) > 0, "VK Teams роуты не найдены в приложении"

    def test_openapi_includes_vk_teams_tags(self):
        """Тест что VK Teams теги включены в OpenAPI схему"""
        openapi_schema = app.openapi()
        
        # Проверяем наличие VK Teams endpoints в схеме
        paths = openapi_schema.get("paths", {})
        vk_teams_paths = [
            path for path in paths.keys() 
            if '/vk-teams/' in path
        ]
        
        assert len(vk_teams_paths) > 0, "VK Teams пути не найдены в OpenAPI схеме" 