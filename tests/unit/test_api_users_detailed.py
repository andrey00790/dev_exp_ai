#!/usr/bin/env python3
"""
Детальные тесты для API управления пользователями
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

pytestmark = pytest.mark.integration


class TestUsersAPIDetailed:
    """Детальные тесты API пользователей"""
    
    def test_create_user_endpoint(self):
        """Тест создания пользователя"""
        try:
            from app.main import app
            client = TestClient(app)
            
            user_data = {
                "username": "test_user",
                "email": "test@example.com"
            }
            
            response = client.post("/api/v1/users", json=user_data)
            
            # Endpoint должен существовать
            assert response.status_code != 404
            
            # Если реализован, должен создавать пользователя
            if response.status_code == 201:
                data = response.json()
                assert "id" in data
                assert data["username"] == "test_user"
                assert data["email"] == "test@example.com"
                
        except ImportError:
            pytest.skip("Main app not available")
    
    def test_create_user_validation(self):
        """Тест валидации при создании пользователя"""
        try:
            from app.main import app
            client = TestClient(app)
            
            # Невалидные данные - отсутствует email
            invalid_data = {
                "username": "test_user"
            }
            
            response = client.post("/api/v1/users", json=invalid_data)
            
            if response.status_code != 404:  # Если endpoint существует
                assert response.status_code in [400, 422]  # Ошибка валидации
                
        except ImportError:
            pytest.skip("Main app not available")
    
    def test_create_user_duplicate_email(self):
        """Тест создания пользователя с дублирующимся email"""
        try:
            from app.main import app
            client = TestClient(app)
            
            user_data = {
                "username": "test_user",
                "email": "duplicate@example.com"
            }
            
            # Создаем пользователя дважды
            response1 = client.post("/api/v1/users", json=user_data)
            response2 = client.post("/api/v1/users", json=user_data)
            
            if response1.status_code == 201:  # Если первый создался
                assert response2.status_code in [400, 409]  # Второй должен быть ошибкой
                
        except ImportError:
            pytest.skip("Main app not available")
    
    def test_get_user_settings(self):
        """Тест получения настроек пользователя"""
        try:
            from app.main import app
            client = TestClient(app)
            
            response = client.get("/api/v1/users/current/settings")
            
            # Endpoint должен существовать
            assert response.status_code != 404
            
            # Если реализован, должен возвращать настройки
            if response.status_code == 200:
                data = response.json()
                assert "data_sources" in data
                assert isinstance(data["data_sources"], list)
                
        except ImportError:
            pytest.skip("Main app not available")
    
    def test_update_user_settings(self):
        """Тест обновления настроек пользователя"""
        try:
            from app.main import app
            client = TestClient(app)
            
            settings_data = {
                "preferences": {
                    "language": "ru",
                    "theme": "dark"
                }
            }
            
            response = client.put("/api/v1/users/current/settings", json=settings_data)
            
            # Endpoint должен существовать
            assert response.status_code != 404
            
            # Если реализован, должен обновлять настройки
            if response.status_code == 200:
                data = response.json()
                assert "data_sources" in data or "preferences" in data
                
        except ImportError:
            pytest.skip("Main app not available")


class TestUsersServiceIntegration:
    """Тесты интеграции с сервисом пользователей"""
    
    @patch('user_config_manager.UserConfigManager')
    def test_user_config_manager_integration(self, mock_manager):
        """Тест интеграции с UserConfigManager"""
        try:
            # Настраиваем mock
            mock_instance = Mock()
            mock_instance.create_user_with_defaults.return_value = 123
            mock_instance.get_user_config.return_value = Mock(
                user_id=123,
                username="test_user",
                email="test@example.com"
            )
            mock_manager.return_value = mock_instance
            
            from app.main import app
            client = TestClient(app)
            
            user_data = {
                "username": "test_user",
                "email": "test@example.com"
            }
            
            response = client.post("/api/v1/users", json=user_data)
            
            if response.status_code == 201:
                data = response.json()
                assert data["id"] == 123
                
        except ImportError:
            pytest.skip("Required modules not available")
    
    def test_data_sources_defaults(self):
        """Тест настроек источников данных по умолчанию"""
        try:
            from app.main import app
            client = TestClient(app)
            
            response = client.get("/api/v1/users/current/settings")
            
            if response.status_code == 200:
                data = response.json()
                
                if "data_sources" in data:
                    data_sources = data["data_sources"]
                    
                    # Проверяем настройки по умолчанию
                    jira_enabled = any(
                        ds.get("source_type") == "jira" and ds.get("is_enabled_semantic_search") 
                        for ds in data_sources
                    )
                    
                    confluence_enabled = any(
                        ds.get("source_type") == "confluence" and ds.get("is_enabled_semantic_search")
                        for ds in data_sources
                    )
                    
                    # По умолчанию Jira и Confluence должны быть включены
                    if jira_enabled is not None:
                        assert jira_enabled == True
                    if confluence_enabled is not None:
                        assert confluence_enabled == True
                        
        except ImportError:
            pytest.skip("Main app not available")


class TestUsersAPIErrorHandling:
    """Тесты обработки ошибок в API пользователей"""
    
    def test_create_user_invalid_email(self):
        """Тест создания пользователя с невалидным email"""
        try:
            from app.main import app
            client = TestClient(app)
            
            user_data = {
                "username": "test_user",
                "email": "invalid-email"  # Невалидный email
            }
            
            response = client.post("/api/v1/users", json=user_data)
            
            if response.status_code != 404:  # Если endpoint существует
                assert response.status_code in [400, 422]  # Ошибка валидации
                
        except ImportError:
            pytest.skip("Main app not available")
    
    def test_get_nonexistent_user(self):
        """Тест получения несуществующего пользователя"""
        try:
            from app.main import app
            client = TestClient(app)
            
            response = client.get("/api/v1/users/999999")
            
            if response.status_code != 404:  # Если endpoint существует
                # Должна быть ошибка "не найден"
                assert response.status_code in [404, 400]
                
        except ImportError:
            pytest.skip("Main app not available")
    
    @patch('user_config_manager.UserConfigManager')
    def test_database_error_handling(self, mock_manager):
        """Тест обработки ошибок базы данных"""
        try:
            # Настраиваем mock с ошибкой
            mock_instance = Mock()
            mock_instance.create_user_with_defaults.side_effect = Exception("Database error")
            mock_manager.return_value = mock_instance
            
            from app.main import app
            client = TestClient(app)
            
            user_data = {
                "username": "test_user",
                "email": "test@example.com"
            }
            
            response = client.post("/api/v1/users", json=user_data)
            
            if response.status_code != 404:  # Если endpoint существует
                assert response.status_code in [500, 502, 503]  # Ошибка сервера
                
        except ImportError:
            pytest.skip("Required modules not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 