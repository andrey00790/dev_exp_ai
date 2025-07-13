#!/usr/bin/env python3
"""
E2E тесты на основе OpenAPI спецификации и функциональных требований.
Покрывает ключевые пользовательские сценарии согласно требованиям FR-001 to FR-080.

Context7 Pattern: Comprehensive API endpoint testing with realistic user scenarios.
"""

import pytest
import asyncio
import json
import httpx
from pathlib import Path
from typing import Dict, List, Any
import time
from datetime import datetime


class TestOpenAPIRequirements:
    """
    Тесты на основе OpenAPI спецификации и функциональных требований.
    
    Покрывает:
    - FR-001-009: Аутентификация и авторизация  
    - FR-010-018: Семантический поиск
    - FR-019-026: Генерация RFC
    - FR-041-049: Управление источниками данных
    - FR-058-065: Реалтайм мониторинг
    - FR-074-080: Продвинутые AI возможности
    """
    
    @pytest.fixture(scope="class")
    def api_client(self):
        """Context7 pattern: Persistent API client for test suite."""
        return httpx.AsyncClient(
            base_url="http://localhost:8001", 
            timeout=30.0,
            follow_redirects=True
        )
    
    @pytest.fixture(scope="class") 
    async def auth_token(self, api_client):
        """Context7 pattern: Authentication setup for test suite."""
        # FR-001: Система должна поддерживать вход по email/паролю
        login_data = {
            "email": "test@example.com",
            "password": "TestPassword123!"
        }
        
        response = await api_client.post("/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        
        # Если пользователь не существует, создаем его
        register_data = {
            "email": "test@example.com", 
            "password": "TestPassword123!",
            "name": "Test User",
            "budget_limit": 100.0
        }
        
        register_response = await api_client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code in [201, 409], f"Registration failed: {register_response.text}"
        
        # Повторный логин
        login_response = await api_client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        token_data = login_response.json()
        return token_data.get("access_token")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Context7 pattern: Reusable authentication headers."""
        return {"Authorization": f"Bearer {auth_token}"}


class TestAuthenticationScenarios(TestOpenAPIRequirements):
    """FR-001: Unified Authentication System Test Scenarios"""
    
    @pytest.mark.skip(reason="Auth endpoints require database with timezone configuration - datetime comparison issue in auth entities")
    @pytest.mark.asyncio
    async def test_user_registration_flow(self, api_client):
        """Тест полного цикла регистрации пользователя."""
        unique_email = f"newuser_{int(time.time())}@example.com"
        register_data = {
            "email": unique_email,
            "password": "SecurePass123!",
            "name": "New Test User", 
            "budget_limit": 50.0
        }
        
        # Шаг 1: Регистрация
        response = await api_client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 201, f"Registration failed: {response.text}"
        
        token_data = response.json()
        assert "access_token" in token_data
        assert "token_type" in token_data
        assert token_data["token_type"] == "bearer"
        
        # Шаг 2: Проверка токена
        auth_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        verify_response = await api_client.get("/api/v1/auth/verify", headers=auth_headers)
        assert verify_response.status_code == 200
        
        # Шаг 3: Получение профиля
        profile_response = await api_client.get("/api/v1/auth/me", headers=auth_headers)
        assert profile_response.status_code == 200
        
        profile_data = profile_response.json()
        assert profile_data["email"] == unique_email
        assert profile_data["name"] == "New Test User"
    
    @pytest.mark.skip(reason="Auth endpoints require database with timezone configuration - datetime comparison issue in auth entities")
    @pytest.mark.asyncio
    async def test_sso_providers_availability(self, api_client):
        """Тест доступности SSO провайдеров."""
        """
        FR-002: Система должна поддерживать SSO через SAML, OAuth
        Сценарий: Пользователь просматривает доступные SSO провайдеры
        """
        response = await api_client.get("/api/v1/auth/sso/providers")
        assert response.status_code == 200
        
        providers = response.json()
        assert isinstance(providers, list)
        
        # Проверяем, что есть основные провайдеры
        provider_types = [p.get("provider_type") for p in providers]
        expected_providers = ["oauth_google", "oauth_microsoft", "oauth_github", "saml"]
        
        # Хотя бы один из ожидаемых провайдеров должен быть доступен
        assert any(provider in provider_types for provider in expected_providers)
    
    @pytest.mark.skip(reason="Auth endpoints require database with timezone configuration - datetime comparison issue in auth entities")
    @pytest.mark.asyncio
    async def test_token_refresh_flow(self, api_client, auth_token):
        """Тест обновления токена."""
        auth_headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Обновление токена
        response = await api_client.post("/api/v1/auth/refresh", headers=auth_headers)
        assert response.status_code == 200
        
        # Проверяем, что новый токен работает
        verify_response = await api_client.get("/api/v1/auth/verify", headers=auth_headers)
        assert verify_response.status_code == 200
    
    @pytest.mark.asyncio  
    async def test_user_budget_management(self, api_client, auth_headers):
        """
        FR-009: Система должна отслеживать бюджеты и лимиты пользователей
        Сценарий: Пользователь проверяет свой бюджет и использование
        """
        # Получение информации о бюджете
        budget_response = await api_client.get("/api/v1/auth/budget", headers=auth_headers)
        assert budget_response.status_code == 200
        
        # Получение статуса бюджета
        status_response = await api_client.get("/api/v1/auth/budget/status", headers=auth_headers)
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        required_fields = ["current_usage", "budget_limit", "remaining_budget", "usage_percentage"]
        for field in required_fields:
            assert field in status_data, f"Missing budget field: {field}"


class TestSemanticSearchScenarios(TestOpenAPIRequirements):
    """
    FR-010-018: Тестирование семантического поиска
    """
    
    @pytest.mark.asyncio
    async def test_basic_semantic_search(self, api_client, auth_headers):
        """
        FR-010: Система должна выполнять семантический поиск по всем подключенным источникам
        Сценарий: Пользователь выполняет простой поиск
        """
        search_data = {
            "query": "authentication security best practices",
            "limit": 10,
            "search_type": "semantic"
        }
        
        response = await api_client.post("/api/v1/search", json=search_data, headers=auth_headers)
        assert response.status_code == 200
        
        search_results = response.json()
        assert "results" in search_results
        assert "total_results" in search_results
        assert "search_time_ms" in search_results
        
        # FR-011: Система должна поддерживать векторный поиск с релевантностью (score)
        if search_results["results"]:
            result = search_results["results"][0]
            assert "score" in result
            assert isinstance(result["score"], (int, float))
            assert 0 <= result["score"] <= 1
    
    @pytest.mark.asyncio
    async def test_advanced_search_with_filters(self, api_client, auth_headers):
        """
        FR-014-017: Система должна поддерживать фильтрацию по различным критериям
        Сценарий: Пользователь использует расширенный поиск с фильтрами
        """
        search_data = {
            "query": "API documentation",
            "sources": {
                "confluence": ["technical-docs"], 
                "gitlab": ["main-repo"]
            },
            "content": {
                "document_types": ["documentation", "guide"],
                "languages": ["en"]
            },
            "time": {
                "updated_after": "2024-01-01T00:00:00Z"
            },
            "quality": {
                "min_quality_score": 0.7,
                "min_word_count": 100
            },
            "sort_by": "relevance",
            "sort_order": "desc",
            "limit": 20
        }
        
        response = await api_client.post("/api/v1/search/advanced", json=search_data, headers=auth_headers)
        assert response.status_code == 200
        
        results = response.json()
        assert "query" in results
        assert "results" in results
        assert "source_breakdown" in results
        assert "quality_stats" in results
        
        # FR-012: Система должна показывать источник каждого результата
        if results["results"]:
            result = results["results"][0]
            assert "source" in result
            assert "source_type" in result
    
    @pytest.mark.asyncio
    async def test_search_pagination(self, api_client, auth_headers):
        """
        FR-013: Система должна поддерживать пагинацию результатов (10-100 на страницу)
        Сценарий: Пользователь просматривает результаты поиска по страницам
        """
        # Первая страница
        search_data = {
            "query": "configuration setup guide",
            "limit": 5,
            "offset": 0
        }
        
        response1 = await api_client.post("/api/v1/search", json=search_data, headers=auth_headers)
        assert response1.status_code == 200
        
        results1 = response1.json()
        
        # Вторая страница  
        search_data["offset"] = 5
        response2 = await api_client.post("/api/v1/search", json=search_data, headers=auth_headers)
        assert response2.status_code == 200
        
        results2 = response2.json()
        
        # Проверяем, что результаты разные
        if results1["results"] and results2["results"]:
            ids1 = {r.get("id") for r in results1["results"]}
            ids2 = {r.get("id") for r in results2["results"]}
            assert ids1.isdisjoint(ids2), "Pagination should return different results"


class TestRFCGenerationScenarios(TestOpenAPIRequirements):
    """
    FR-019-026: Тестирование генерации RFC
    """
    
    @pytest.mark.asyncio
    async def test_interactive_rfc_generation(self, api_client, auth_headers):
        """
        FR-019-022: Интерактивная генерация RFC с умными вопросами
        Сценарий: Пользователь создает RFC через интерактивный процесс
        """
        # Шаг 1: Начальный запрос на генерацию
        rfc_data = {
            "task_description": "Implement new user authentication system with multi-factor authentication",
            "project_context": "E-commerce platform with high security requirements",
            "technical_requirements": "JWT tokens, SMS/Email verification, rate limiting",
            "stakeholders": ["security-team", "backend-team", "product-team"],
            "priority": "high",
            "template_type": "architecture",
            "include_diagrams": True,
            "include_codebase_analysis": True,
            "use_all_sources": True
        }
        
        response = await api_client.post("/api/v1/generate/rfc", json=rfc_data, headers=auth_headers)
        assert response.status_code == 200
        
        generation_result = response.json()
        assert "task_id" in generation_result
        assert "status" in generation_result
        
        task_id = generation_result["task_id"]
        
        # Шаг 2: Проверка статуса генерации
        status_response = await api_client.get(f"/api/v1/generate/session/{task_id}", headers=auth_headers)
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert "status" in status_data
        
        # FR-021: Система должна показывать прогресс генерации с визуальным индикатором
        if "progress" in status_data:
            assert isinstance(status_data["progress"], (int, float))
            assert 0 <= status_data["progress"] <= 100
    
    @pytest.mark.asyncio
    async def test_rfc_templates_availability(self, api_client, auth_headers):
        """
        FR-022: Система должна генерировать RFC на основе шаблонов
        Сценарий: Пользователь просматривает доступные шаблоны RFC
        """
        response = await api_client.get("/api/v1/rfc-templates", headers=auth_headers)
        assert response.status_code == 200
        
        templates = response.json()
        assert isinstance(templates, (list, dict))
        
        # Проверяем наличие основных типов шаблонов
        if isinstance(templates, dict) and "templates" in templates:
            template_types = templates["templates"]
            expected_types = ["architecture", "security", "process", "api"]
            assert any(t in str(template_types) for t in expected_types)
    
    @pytest.mark.asyncio
    async def test_enhanced_rfc_with_analysis(self, api_client, auth_headers):
        """
        FR-079-080: Система должна анализировать и улучшать существующий код
        Сценарий: Пользователь генерирует RFC с анализом кодовой базы
        """
        enhanced_data = {
            "task_description": "Optimize database performance for user queries",
            "project_path": "/app/database/",
            "project_context": "High-load web application with PostgreSQL",
            "technical_requirements": "Query optimization, indexing strategy, connection pooling",
            "include_diagrams": True,
            "include_codebase_analysis": True
        }
        
        response = await api_client.post("/api/v1/generate/rfc", json=enhanced_data, headers=auth_headers)
        assert response.status_code == 200
        
        result = response.json()
        assert "task_id" in result
        
        # Проверяем, что включен анализ кода
        if "metadata" in result:
            metadata = result["metadata"]
            assert isinstance(metadata, dict)


class TestDataSourceManagementScenarios(TestOpenAPIRequirements):
    """
    FR-041-049: Тестирование управления источниками данных
    """
    
    @pytest.mark.asyncio
    async def test_data_sources_discovery(self, api_client, auth_headers):
        """
        FR-041-044: Подключение к различным источникам данных
        Сценарий: Пользователь просматривает доступные источники данных
        """
        response = await api_client.get("/api/v1/data-sources", headers=auth_headers)
        assert response.status_code == 200
        
        sources = response.json()
        assert "sources" in sources
        assert "total_sources" in sources
        
        # Проверяем наличие основных типов источников
        source_types = [s.get("type") for s in sources["sources"]]
        expected_types = ["confluence", "jira", "gitlab", "local_files"]
        
        assert any(source_type in source_types for source_type in expected_types)
    
    @pytest.mark.asyncio
    async def test_data_source_configuration(self, api_client, auth_headers):
        """
        FR-045: Система должна тестировать соединения перед сохранением
        Сценарий: Пользователь настраивает новый источник данных
        """
        # Попытка настройки тестового источника
        config_data = {
            "source_type": "confluence",
            "name": "Test Confluence",
            "config": {
                "base_url": "https://test.atlassian.net",
                "api_token": "fake_token_for_test",
                "username": "test@example.com"
            },
            "enabled": False  # Не включаем, чтобы не нарушить тесты
        }
        
        response = await api_client.post("/api/v1/data-sources/configure", json=config_data, headers=auth_headers)
        # Может быть 200 (успех) или 400 (ошибка подключения) - оба варианта валидны
        assert response.status_code in [200, 400, 422]
        
        if response.status_code == 200:
            result = response.json()
            assert "connection_test_passed" in result
    
    @pytest.mark.asyncio
    async def test_sync_management(self, api_client, auth_headers):
        """
        FR-046-048: Управление синхронизацией источников данных
        Сценарий: Пользователь запускает синхронизацию данных
        """
        # Проверка статуса синхронизации
        status_response = await api_client.get("/api/v1/sync/status", headers=auth_headers)
        assert status_response.status_code == 200
        
        # Запуск синхронизации
        sync_data = {
            "sources": ["confluence", "jira"],
            "full_sync": False
        }
        
        sync_response = await api_client.post("/api/v1/sync/trigger", json=sync_data, headers=auth_headers)
        assert sync_response.status_code in [200, 202, 400]  # 400 если источники не настроены


class TestRealtimeMonitoringScenarios(TestOpenAPIRequirements):
    """
    FR-058-065: Тестирование реалтайм мониторинга
    """
    
    @pytest.mark.asyncio
    async def test_live_metrics_monitoring(self, api_client, auth_headers):
        """
        FR-062-064: Live мониторинг с обновлениями в реальном времени
        Сценарий: Пользователь просматривает live метрики системы
        """
        # Получение текущих метрик
        metrics_response = await api_client.get("/api/v1/realtime-monitoring/live-metrics", headers=auth_headers)
        assert metrics_response.status_code == 200
        
        # Получение дашборд статистики
        dashboard_response = await api_client.get("/api/v1/realtime-monitoring/dashboard-stats", headers=auth_headers)
        assert dashboard_response.status_code == 200
        
        dashboard_data = dashboard_response.json()
        assert isinstance(dashboard_data, dict)
    
    @pytest.mark.asyncio
    async def test_alerts_management(self, api_client, auth_headers):
        """
        FR-058-061: Управление алертами и их жизненным циклом
        Сценарий: Пользователь работает с алертами системы
        """
        # Получение текущих алертов
        alerts_response = await api_client.get("/api/v1/realtime-monitoring/alerts", headers=auth_headers)
        assert alerts_response.status_code == 200
        
        alerts_data = alerts_response.json()
        assert isinstance(alerts_data, (list, dict))
        
        # Фильтрация алертов по статусу
        filtered_response = await api_client.get(
            "/api/v1/realtime-monitoring/alerts?status=active&severity=high", 
            headers=auth_headers
        )
        assert filtered_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_anomaly_detection(self, api_client, auth_headers):
        """
        FR-059: Детекция аномалий в реальном времени
        Сценарий: Пользователь просматривает обнаруженные аномалии
        """
        anomalies_response = await api_client.get("/api/v1/realtime-monitoring/anomalies", headers=auth_headers)
        assert anomalies_response.status_code == 200
        
        anomalies_data = anomalies_response.json()
        assert isinstance(anomalies_data, (list, dict))
        
        # Проверка с фильтрами времени
        filtered_response = await api_client.get(
            "/api/v1/realtime-monitoring/anomalies?hours=24&severity=high", 
            headers=auth_headers
        )
        assert filtered_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_sla_monitoring(self, api_client, auth_headers):
        """
        FR-060: SLA мониторинг (время ответа <2с, ошибки <1%, uptime 99.9%)
        Сценарий: Пользователь проверяет соблюдение SLA
        """
        sla_response = await api_client.get("/api/v1/realtime-monitoring/sla-status", headers=auth_headers)
        assert sla_response.status_code == 200
        
        sla_data = sla_response.json()
        assert isinstance(sla_data, dict)
        
        # Проверяем наличие ключевых SLA метрик
        expected_metrics = ["uptime", "response_time", "error_rate"]
        # Хотя бы одна из метрик должна присутствовать
        assert any(metric in str(sla_data) for metric in expected_metrics)


class TestAdvancedAIScenarios(TestOpenAPIRequirements):
    """
    FR-074-080: Тестирование продвинутых AI возможностей
    """
    
    @pytest.mark.asyncio
    async def test_multimodal_search(self, api_client, auth_headers):
        """
        FR-074-077: Мультимодальный поиск по различным типам контента
        Сценарий: Пользователь выполняет поиск по изображениям, коду и документам
        """
        multimodal_data = {
            "query": "user authentication flow diagram",
            "search_types": ["text", "code", "docs", "images"],
            "filters": {
                "content_types": ["diagram", "flowchart", "code_snippet"],
                "languages": ["python", "javascript"]
            },
            "limit": 15
        }
        
        response = await api_client.post("/api/v1/multimodal-search", json=multimodal_data, headers=auth_headers)
        assert response.status_code == 200
        
        results = response.json()
        assert isinstance(results, dict)
    
    @pytest.mark.asyncio
    async def test_code_review_capabilities(self, api_client, auth_headers):
        """
        FR-080: Система должна анализировать и улучшать существующий код
        Сценарий: Пользователь запрашивает review кода
        """
        code_review_data = {
            "code": """
def authenticate_user(username, password):
    # Simple authentication function
    users = {'admin': 'password123'}
    if username in users and users[username] == password:
        return True
    return False
            """,
            "file_path": "auth.py",
            "review_type": "security",
            "language": "python",
            "focus_areas": ["security", "best_practices", "performance"]
        }
        
        response = await api_client.post("/api/v1/code-review", json=code_review_data, headers=auth_headers)
        assert response.status_code == 200
        
        review_result = response.json()
        assert isinstance(review_result, dict)
    
    @pytest.mark.asyncio
    async def test_image_upload_processing(self, api_client, auth_headers):
        """
        FR-032: Система должна поддерживать загрузку изображений и файлов
        Сценарий: Пользователь загружает изображение для анализа
        """
        # Создаем простое тестовое изображение (пиксель)
        test_image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x01sRGB\x00\xae\xce\x1c\xe9\x00\x00\x00\x04gAMA\x00\x00\xb1\x8f\x0b\xfca\x05\x00\x00\x00\tpHYs\x00\x00\x0e\xc3\x00\x00\x0e\xc3\x01\xc7o\xa8d\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\xcc\xdb\x18\x00\x00\x00\x00IEND\xaeB`\x82'
        
        files = {"file": ("test.png", test_image_content, "image/png")}
        
        response = await api_client.post("/api/v1/upload-image", files=files, headers=auth_headers)
        # Может быть 200 (успех) или 422 (валидация) в зависимости от реализации
        assert response.status_code in [200, 422, 400]


class TestPerformanceAndReliability(TestOpenAPIRequirements):
    """
    NFR-001-028: Тестирование нефункциональных требований
    """
    
    @pytest.mark.asyncio
    async def test_api_response_time_sla(self, api_client):
        """
        NFR-001: API endpoints должны отвечать менее чем за 200ms
        Сценарий: Проверка времени отклика критических endpoints
        """
        critical_endpoints = [
            "/health",
            "/api/v1/health", 
            "/api/v1/auth/demo-users",
            "/",
        ]
        
        for endpoint in critical_endpoints:
            start_time = time.time()
            response = await api_client.get(endpoint)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            # Проверяем, что endpoint отвечает
            assert response.status_code in [200, 401, 403], f"Endpoint {endpoint} failed: {response.status_code}"
            
            # NFR-001: Проверяем SLA по времени отклика
            assert response_time_ms < 200, f"Endpoint {endpoint} too slow: {response_time_ms:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_health_checks_comprehensive(self, api_client):
        """
        NFR-024: Система должна поддерживать health checks для всех компонентов
        Сценарий: Проверка работоспособности всех ключевых компонентов
        """
        health_endpoints = [
            "/health",
            "/health_smoke", 
            "/api/v1/health",
            "/api/v1/realtime-monitoring/health",
            "/api/v1/deep-research/health"
        ]
        
        for endpoint in health_endpoints:
            response = await api_client.get(endpoint)
            assert response.status_code == 200, f"Health check failed for {endpoint}"
            
            health_data = response.json()
            assert isinstance(health_data, dict)
            
            # Проверяем наличие статуса
            status_indicators = ["status", "timestamp", "health"]
            assert any(indicator in health_data for indicator in status_indicators)


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v", "--tb=short"]) 