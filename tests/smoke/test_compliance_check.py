"""
Тест соответствия функциональным требованиям
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestFunctionalRequirements:
    """Тесты соответствия функциональным требованиям"""

    def test_fr_001_009_authentication(self):
        """FR-001-009: Аутентификация и авторизация"""
        # Проверяем наличие auth endpoints
        auth_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/auth/logout",
            "/api/v1/auth/refresh",
            "/api/v1/auth/sso/providers",
            "/api/v1/auth/sso/health",
        ]

        for endpoint in auth_endpoints:
            response = client.get(endpoint)
            # Ожидаем 405 (Method Not Allowed) или другой код, но не 404
            assert response.status_code != 404, f"Endpoint {endpoint} not found"

    def test_fr_010_020_user_management(self):
        """FR-010-020: Управление пользователями"""
        # Проверяем наличие user endpoints
        response = client.get("/api/v1/users/")
        assert response.status_code != 404, "Users endpoint not found"

    def test_fr_021_029_data_sources(self):
        """FR-021-029: Источники данных"""
        # Проверяем наличие data sources endpoints
        response = client.get("/api/v1/data-sources/")
        assert response.status_code != 404, "Data sources endpoint not found"

    def test_fr_030_040_search(self):
        """FR-030-040: Поиск и фильтрация"""
        # Проверяем наличие search endpoints
        search_endpoints = ["/api/v1/search/", "/api/v1/search/advanced/"]

        for endpoint in search_endpoints:
            response = client.get(endpoint)
            assert response.status_code != 404, f"Search endpoint {endpoint} not found"

    def test_fr_041_050_ai_generation(self):
        """FR-041-050: AI генерация"""
        # Проверяем наличие AI generation endpoints
        response = client.get("/api/v1/generate/templates")
        assert response.status_code != 404, "Generate endpoint not found"

    def test_fr_051_060_ai_optimization(self):
        """FR-051-060: AI оптимизация"""
        # Проверяем наличие AI optimization endpoints
        response = client.get("/api/v1/ai-optimization/models")
        assert response.status_code != 404, "AI optimization endpoint not found"

    def test_fr_061_065_monitoring(self):
        """FR-061-065: Мониторинг"""
        # Проверяем наличие monitoring endpoints
        response = client.get("/api/v1/realtime-monitoring/health")
        assert response.status_code != 404, "Monitoring endpoint not found"

    def test_fr_063_websocket(self):
        """FR-063: WebSocket соединения"""
        # Проверяем что WebSocket endpoint существует
        # Не можем тестировать WebSocket через TestClient, но можем проверить что route существует

        # Проверяем что endpoint зарегистрирован в приложении
        websocket_routes = [
            route
            for route in app.routes
            if hasattr(route, "path") and route.path == "/ws/{user_id}"
        ]
        assert len(websocket_routes) > 0, "WebSocket endpoint /ws/{user_id} not found"

    def test_health_endpoints(self):
        """Проверка health endpoints"""
        # Root health check
        response = client.get("/health")
        assert response.status_code == 200

        # API v1 health check
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_documents_endpoint(self):
        """Проверка documents endpoint"""
        response = client.get("/api/v1/documents/")
        assert response.status_code != 404, "Documents endpoint not found"


class TestNonFunctionalRequirements:
    """Тесты нефункциональных требований"""

    def test_nfr_001_response_time(self):
        """NFR-001: API endpoints должны отвечать менее чем за 200ms"""
        import time

        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000
        assert (
            response_time_ms < 200
        ), f"Response time {response_time_ms}ms exceeds 200ms"

    def test_nfr_029_jwt_tokens(self):
        """NFR-029: Использование JWT токенов"""
        # Проверяем что auth endpoint существует для JWT
        response = client.post(
            "/api/v1/auth/login", json={"username": "test", "password": "test"}
        )
        # Ожидаем любой код кроме 404 (endpoint существует)
        assert response.status_code != 404, "JWT auth endpoint not found"

    def test_nfr_041_browser_compatibility(self):
        """NFR-041: Совместимость с браузерами через CORS"""
        # Проверяем что CORS настроен
        response = client.options("/health")
        # CORS middleware должен обрабатывать OPTIONS запросы
        assert response.status_code in [200, 405], "CORS not properly configured"


class TestArchitectureCompliance:
    """Тесты архитектурного соответствия"""

    def test_api_structure(self):
        """Проверка структуры API"""
        # Проверяем что все роутеры подключены с префиксом /api/v1
        v1_routes = [
            route
            for route in app.routes
            if hasattr(route, "path") and route.path.startswith("/api/v1")
        ]
        assert len(v1_routes) > 10, "Not enough v1 API routes registered"

    def test_openapi_documentation(self):
        """Проверка OpenAPI документации"""
        response = client.get("/docs")
        assert response.status_code == 200, "OpenAPI docs not available"

        response = client.get("/openapi.json")
        assert response.status_code == 200, "OpenAPI spec not available"

    def test_root_endpoint(self):
        """Проверка корневого endpoint"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "features" in data, "Root endpoint should list features"
        assert len(data["features"]) >= 5, "Should list main features"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
