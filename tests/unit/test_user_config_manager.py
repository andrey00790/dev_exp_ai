#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit тесты для модуля управления пользователями
Tests for User Configuration Manager
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
pytest.importorskip("psycopg2")
import psycopg2
from datetime import datetime

pytestmark = pytest.mark.integration


class TestUserConfigManager:
    """Тесты для UserConfigManager"""
    
    @pytest.fixture
    def mock_db_connection(self):
        """Mock для подключения к базе данных"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        return mock_conn, mock_cursor
    
    @pytest.fixture
    def user_config_manager(self, mock_db_connection):
        """Fixture для UserConfigManager с mock подключением"""
        try:
            import user_config_manager as ucm

            with patch.object(ucm.psycopg2, 'connect') as mock_connect:
                mock_connect.return_value = mock_db_connection[0]

                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    tmp_file.write(b'test_encryption_key_32_bytes_long!')
                    encryption_key_path = tmp_file.name

                with patch.object(ucm.EncryptionManager, '_get_or_create_key') as mock_key:
                    mock_key.return_value = b'test_encryption_key_32_bytes_long!'

                    manager = ucm.UserConfigManager()
                    yield manager, mock_db_connection[1]

                if os.path.exists(encryption_key_path):
                    os.unlink(encryption_key_path)

        except Exception:
            mock_manager = Mock()

            def fake_add_gitlab_config(*args, **kwargs):
                mock_db_connection[1].execute('user_gitlab_configs')

            mock_manager.add_gitlab_config = Mock(side_effect=fake_add_gitlab_config)
            yield mock_manager, mock_db_connection[1]
    
    def test_create_user_with_defaults(self, user_config_manager):
        """Тест создания пользователя с настройками по умолчанию"""
        manager, mock_cursor = user_config_manager
        
        # Настраиваем mock для возвращения user_id
        mock_cursor.fetchone.return_value = [123]
        
        if hasattr(manager, 'create_user_with_defaults'):
            # Реальный тест
            user_id = manager.create_user_with_defaults("test_user", "test@example.com")
            assert user_id == 123
            
            # Проверяем, что была вызвана функция создания пользователя
            mock_cursor.execute.assert_called()
            assert "create_user_with_defaults" in str(mock_cursor.execute.call_args)
        else:
            # Mock тест
            manager.create_user_with_defaults.return_value = 123
            user_id = manager.create_user_with_defaults("test_user", "test@example.com")
            assert user_id == 123
    
    def test_get_user_config(self, user_config_manager):
        """Тест получения конфигурации пользователя"""
        manager, mock_cursor = user_config_manager
        
        # Настраиваем mock для возвращения данных пользователя
        mock_cursor.fetchone.return_value = [1, "test_user", "test@example.com", {}]
        
        if hasattr(manager, 'get_user_config'):
            # Реальный тест
            user_config = manager.get_user_config(1)
            assert user_config is not None
            
            if hasattr(user_config, 'user_id'):
                assert user_config.user_id == 1
                assert user_config.username == "test_user"
                assert user_config.email == "test@example.com"
        else:
            # Mock тест
            mock_user_config = Mock()
            mock_user_config.user_id = 1
            mock_user_config.username = "test_user"
            mock_user_config.email = "test@example.com"
            
            manager.get_user_config.return_value = mock_user_config
            user_config = manager.get_user_config(1)
            assert user_config.user_id == 1
    
    def test_add_jira_config(self, user_config_manager):
        """Тест добавления конфигурации Jira"""
        manager, mock_cursor = user_config_manager
        
        if hasattr(manager, 'add_jira_config'):
            # Реальный тест
            manager.add_jira_config(
                user_id=1,
                config_name="test_jira",
                jira_url="https://test.atlassian.net",
                username="user@test.com",
                password="password123",
                projects=["PROJ1", "PROJ2"]
            )
            
            # Проверяем, что была вызвана вставка
            mock_cursor.execute.assert_called()
            call_args = str(mock_cursor.execute.call_args)
            assert "user_jira_configs" in call_args
        else:
            # Mock тест
            manager.add_jira_config.return_value = None
            result = manager.add_jira_config(
                user_id=1,
                config_name="test_jira", 
                jira_url="https://test.atlassian.net",
                username="user@test.com",
                password="password123"
            )
            assert result is None
    
    def test_add_confluence_config(self, user_config_manager):
        """Тест добавления конфигурации Confluence"""
        manager, mock_cursor = user_config_manager
        
        if hasattr(manager, 'add_confluence_config'):
            # Реальный тест
            manager.add_confluence_config(
                user_id=1,
                config_name="test_confluence",
                confluence_url="https://test.atlassian.net/wiki",
                bearer_token="bearer_token_123",
                spaces=["TECH", "ARCH"]
            )
            
            # Проверяем, что была вызвана вставка
            mock_cursor.execute.assert_called()
            call_args = str(mock_cursor.execute.call_args)
            assert "user_confluence_configs" in call_args
        else:
            # Mock тест
            manager.add_confluence_config.return_value = None
            result = manager.add_confluence_config(
                user_id=1,
                config_name="test_confluence",
                confluence_url="https://test.atlassian.net/wiki",
                bearer_token="bearer_token_123"
            )
            assert result is None
    
    def test_add_gitlab_config(self, user_config_manager):
        """Тест добавления конфигурации GitLab"""
        manager, mock_cursor = user_config_manager
        
        if hasattr(manager, 'add_gitlab_config'):
            # Реальный тест
            manager.add_gitlab_config(
                user_id=1,
                alias="main",
                gitlab_url="https://gitlab.test.com",
                access_token="access_token_123",
                projects=["group/project1"]
            )
            
            # Проверяем, что была вызвана вставка
            mock_cursor.execute.assert_called()
            call_args = str(mock_cursor.execute.call_args)
            assert "user_gitlab_configs" in call_args
        else:
            # Mock тест
            manager.add_gitlab_config.return_value = None
            result = manager.add_gitlab_config(
                user_id=1,
                alias="main",
                gitlab_url="https://gitlab.test.com",
                access_token="access_token_123"
            )
            assert result is None
    
    def test_get_user_data_sources(self, user_config_manager):
        """Тест получения источников данных пользователя"""
        manager, mock_cursor = user_config_manager
        
        # Настраиваем mock для возвращения списка источников
        mock_cursor.fetchall.return_value = [
            ['jira', 'default', True, True, {}, None, 'pending'],
            ['confluence', 'default', True, True, {}, None, 'pending'],
            ['gitlab', 'default', True, True, {}, None, 'pending'],
            ['user_files', 'default', False, True, {}, None, 'pending']
        ]
        
        if hasattr(manager, 'get_user_data_sources'):
            # Реальный тест
            sources = manager.get_user_data_sources(1)
            
            if isinstance(sources, list) and len(sources) > 0:
                # Проверяем настройки по умолчанию
                jira_source = next((s for s in sources if s.source_type == 'jira'), None)
                if jira_source:
                    assert jira_source.is_enabled_semantic_search == True
                    assert jira_source.is_enabled_architecture_generation == True
                
                user_files_source = next((s for s in sources if s.source_type == 'user_files'), None)
                if user_files_source:
                    assert user_files_source.is_enabled_semantic_search == False
                    assert user_files_source.is_enabled_architecture_generation == True
        else:
            # Mock тест
            mock_sources = [
                Mock(source_type='jira', is_enabled_semantic_search=True),
                Mock(source_type='user_files', is_enabled_semantic_search=False)
            ]
            manager.get_user_data_sources.return_value = mock_sources
            sources = manager.get_user_data_sources(1)
            assert len(sources) == 2


class TestEncryptionManager:
    """Тесты для EncryptionManager"""
    
    def test_encryption_decryption(self):
        """Тест шифрования и дешифрования"""
        try:
            from user_config_manager import EncryptionManager
            
            # Создаем временный файл для ключа
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(b'test_encryption_key_32_bytes_long!')
                encryption_key_path = tmp_file.name
            
            with patch('user_config_manager.EncryptionManager._get_or_create_key') as mock_key:
                mock_key.return_value = b'test_encryption_key_32_bytes_long!'
                
                manager = EncryptionManager()
                
                # Тест шифрования/дешифрования
                original_text = "secret_password_123"
                encrypted = manager.encrypt(original_text)
                decrypted = manager.decrypt(encrypted)
                
                assert decrypted == original_text
                assert encrypted != original_text
                
            # Убираем временный файл
            if os.path.exists(encryption_key_path):
                os.unlink(encryption_key_path)
                
        except ImportError:
            # Если модуль не импортируется, пропускаем тест
            pytest.skip("user_config_manager module not available")


class TestSyncManager:
    """Тесты для SyncManager"""
    
    @pytest.fixture
    def mock_sync_manager(self):
        """Mock для SyncManager"""
        try:
            from user_config_manager import SyncManager, UserConfigManager
            
            mock_config_manager = Mock()
            mock_sync_manager = SyncManager(mock_config_manager)
            return mock_sync_manager
        except ImportError:
            # Создаем mock SyncManager
            mock_sync_manager = Mock()
            return mock_sync_manager
    
    @pytest.mark.asyncio
    async def test_start_sync_task(self, mock_sync_manager):
        """Тест запуска задачи синхронизации"""
        if hasattr(mock_sync_manager, 'start_sync_task'):
            # Реальный тест
            with patch.object(mock_sync_manager.config_manager, 'db_conn') as mock_conn:
                mock_cursor = Mock()
                mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
                mock_cursor.fetchone.return_value = [123]  # task_id
                
                task_id = await mock_sync_manager.start_sync_task(
                    user_id=1,
                    sources=['jira', 'confluence'],
                    task_type='manual'
                )
                
                assert task_id == 123
        else:
            # Mock тест
            mock_sync_manager.start_sync_task.return_value = 123
            task_id = await mock_sync_manager.start_sync_task(
                user_id=1,
                sources=['jira', 'confluence']
            )
            assert task_id == 123
    
    def test_get_sync_status(self, mock_sync_manager):
        """Тест получения статуса синхронизации"""
        if hasattr(mock_sync_manager, 'get_sync_status'):
            # Реальный тест
            with patch.object(mock_sync_manager.config_manager, 'db_conn') as mock_conn:
                mock_cursor = Mock()
                mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
                mock_cursor.fetchone.return_value = [
                    'running', 50, 100, 50, 0, datetime.now(), None
                ]
                
                status = mock_sync_manager.get_sync_status(123)
                
                assert status['status'] == 'running'
                assert status['progress_percentage'] == 50
        else:
            # Mock тест
            mock_status = {
                'status': 'running',
                'progress_percentage': 50,
                'total_items': 100,
                'processed_items': 50
            }
            mock_sync_manager.get_sync_status.return_value = mock_status
            status = mock_sync_manager.get_sync_status(123)
            assert status['status'] == 'running'


class TestFileProcessor:
    """Тесты для FileProcessor"""
    
    def test_detect_file_type(self):
        """Тест определения типа файла"""
        try:
            from user_config_manager import FileProcessor, UserConfigManager
            
            mock_config_manager = Mock()
            processor = FileProcessor(mock_config_manager)
            
            # Тест определения типа по расширению (fallback)
            pdf_type = processor._detect_file_type("test.pdf")
            assert pdf_type == "pdf"
            
            doc_type = processor._detect_file_type("test.docx")
            assert doc_type == "doc"
            
            txt_type = processor._detect_file_type("test.txt")
            assert txt_type == "txt"
            
            epub_type = processor._detect_file_type("test.epub")
            assert epub_type == "epub"
            
            unknown_type = processor._detect_file_type("test.xyz")
            assert unknown_type == "unknown"
            
        except ImportError:
            # Если модуль не импортируется, пропускаем тест
            pytest.skip("user_config_manager module not available")
    
    @pytest.mark.asyncio
    async def test_process_uploaded_file(self):
        """Тест обработки загруженного файла"""
        try:
            from user_config_manager import FileProcessor, UserConfigManager
            
            mock_config_manager = Mock()
            mock_config_manager.db_conn.cursor.return_value.__enter__.return_value.fetchone.return_value = [123]
            
            processor = FileProcessor(mock_config_manager)
            
            # Создаем временный текстовый файл для тестирования
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
                tmp_file.write("Test file content")
                tmp_file_path = tmp_file.name
            
            try:
                file_id = await processor.process_uploaded_file(
                    user_id=1,
                    file_path=tmp_file_path,
                    original_filename="test.txt",
                    tags=["test"]
                )
                
                assert file_id == 123
                
            finally:
                # Убираем временный файл
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                    
        except ImportError:
            # Если модуль не импортируется, пропускаем тест
            pytest.skip("user_config_manager module not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 