"""
Тесты для планировщика синхронизации данных
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, mock_open
from datetime import datetime, timedelta
import yaml
import tempfile
import os

from core.cron.data_sync_scheduler import DataSyncScheduler, SyncJobConfig


@pytest.fixture
def sample_config():
    """Фикстура с примером конфигурации"""
    return {
        "sync_jobs": [
            {
                "source_type": "confluence",
                "source_name": "main_confluence",
                "enabled": True,
                "schedule": "0 2 * * *",
                "incremental": True,
                "config": {
                    "url": "https://company.atlassian.net",
                    "username": "test@company.com",
                    "api_token": "test_token",
                    "spaces": ["TECH", "PROJ"]
                }
            },
            {
                "source_type": "jira",
                "source_name": "main_jira",
                "enabled": True,
                "schedule": "0 3 * * *",
                "incremental": True,
                "config": {
                    "url": "https://company.atlassian.net",
                    "username": "test@company.com",
                    "api_token": "test_token",
                    "projects": ["PROJ", "TECH"]
                }
            },
            {
                "source_type": "local_files",
                "source_name": "bootstrap",
                "enabled": False,
                "schedule": "*/30 * * * *",
                "incremental": False,
                "config": {
                    "bootstrap_dir": "/app/bootstrap"
                }
            }
        ],
        "global_settings": {
            "max_concurrent_jobs": 3,
            "job_timeout_minutes": 120,
            "retry_failed_jobs": True
        }
    }


@pytest.fixture
def temp_config_file(sample_config):
    """Фикстура для временного файла конфигурации"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(sample_config, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_scheduler():
    """Фикстура для мок планировщика"""
    scheduler = DataSyncScheduler()
    scheduler.scheduler = Mock()
    scheduler.db_manager = Mock()
    scheduler.vector_store = Mock()
    scheduler.content_processor = Mock()
    return scheduler


class TestSyncJobConfig:
    """Тесты для SyncJobConfig"""
    
    def test_sync_job_config_creation(self):
        """Тест создания конфигурации задачи"""
        config = SyncJobConfig(
            source_type="confluence",
            source_name="main",
            enabled=True,
            schedule="0 2 * * *",
            last_sync=None,
            next_sync=None,
            incremental=True,
            config={"url": "https://test.com"}
        )
        
        assert config.source_type == "confluence"
        assert config.source_name == "main"
        assert config.enabled is True
        assert config.schedule == "0 2 * * *"
        assert config.incremental is True
        assert config.config["url"] == "https://test.com"


class TestDataSyncScheduler:
    """Тесты для DataSyncScheduler"""
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, temp_config_file):
        """Тест успешной инициализации планировщика"""
        scheduler = DataSyncScheduler(config_path=temp_config_file)
        
        with patch.object(scheduler, '_initialize_components') as mock_init_components, \
             patch.object(scheduler, '_setup_sync_jobs') as mock_setup_jobs:
            
            mock_init_components.return_value = None
            mock_setup_jobs.return_value = None
            scheduler.scheduler = Mock()
            scheduler.scheduler.start = Mock()
            
            await scheduler.initialize()
            
            # Проверяем что конфигурация загружена
            assert len(scheduler.sync_jobs) == 3
            assert "confluence_main_confluence" in scheduler.sync_jobs
            assert "jira_main_jira" in scheduler.sync_jobs
            assert "local_files_bootstrap" in scheduler.sync_jobs
            
            # Проверяем что компоненты инициализированы
            mock_init_components.assert_called_once()
            mock_setup_jobs.assert_called_once()
            scheduler.scheduler.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_sync_config_success(self, temp_config_file):
        """Тест успешной загрузки конфигурации"""
        scheduler = DataSyncScheduler(config_path=temp_config_file)
        
        await scheduler._load_sync_config()
        
        # Проверяем что задачи загружены правильно
        assert len(scheduler.sync_jobs) == 3
        
        confluence_job = scheduler.sync_jobs["confluence_main_confluence"]
        assert confluence_job.source_type == "confluence"
        assert confluence_job.source_name == "main_confluence"
        assert confluence_job.enabled is True
        assert confluence_job.schedule == "0 2 * * *"
        assert confluence_job.incremental is True
        
        jira_job = scheduler.sync_jobs["jira_main_jira"]
        assert jira_job.source_type == "jira"
        assert jira_job.enabled is True
        
        local_job = scheduler.sync_jobs["local_files_bootstrap"]
        assert local_job.enabled is False
    
    @pytest.mark.asyncio
    async def test_load_sync_config_file_not_found(self):
        """Тест загрузки конфигурации при отсутствии файла"""
        scheduler = DataSyncScheduler(config_path="/nonexistent/config.yml")
        
        with patch.object(scheduler, '_create_default_config') as mock_create_default:
            mock_create_default.return_value = None
            
            await scheduler._load_sync_config()
            
            mock_create_default.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_default_config(self):
        """Тест создания конфигурации по умолчанию"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "sync_config.yml")
            scheduler = DataSyncScheduler(config_path=config_path)
            
            await scheduler._create_default_config()
            
            # Проверяем что файл создан
            assert os.path.exists(config_path)
            
            # Проверяем содержимое
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            assert "sync_jobs" in config
            assert len(config["sync_jobs"]) >= 4  # confluence, gitlab, jira, local_files
            assert "global_settings" in config
    
    @pytest.mark.asyncio
    async def test_initialize_components_success(self, mock_scheduler):
        """Тест инициализации компонентов"""
        main_config = {
            "database": {"url": "postgresql://test"},
            "vector_db": {"url": "http://localhost:6333"},
            "text_processing": {},
            "embeddings": {}
        }
        
        with patch('builtins.open', mock_open(read_data=yaml.dump(main_config))), \
             patch('core.cron.data_sync_scheduler.DatabaseManager') as MockDB, \
             patch('core.cron.data_sync_scheduler.VectorStoreManager') as MockVector, \
             patch('core.cron.data_sync_scheduler.ContentProcessor') as MockProcessor:
            
            # Настройка моков
            mock_db = Mock()
            mock_db.initialize = AsyncMock()
            MockDB.return_value = mock_db
            
            mock_vector = Mock()
            mock_vector.initialize = AsyncMock()
            MockVector.return_value = mock_vector
            
            mock_processor = Mock()
            mock_processor.initialize = AsyncMock()
            MockProcessor.return_value = mock_processor
            
            await mock_scheduler._initialize_components()
            
            # Проверяем что компоненты созданы и инициализированы
            assert mock_scheduler.db_manager is not None
            assert mock_scheduler.vector_store is not None
            assert mock_scheduler.content_processor is not None
            
            mock_db.initialize.assert_called_once()
            mock_vector.initialize.assert_called_once()
            mock_processor.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_setup_sync_jobs_success(self, mock_scheduler, sample_config):
        """Тест настройки задач синхронизации"""
        # Загружаем конфигурацию
        for job_config in sample_config["sync_jobs"]:
            job_id = f"{job_config['source_type']}_{job_config['source_name']}"
            mock_scheduler.sync_jobs[job_id] = SyncJobConfig(
                source_type=job_config["source_type"],
                source_name=job_config["source_name"],
                enabled=job_config["enabled"],
                schedule=job_config["schedule"],
                last_sync=None,
                next_sync=None,
                incremental=job_config["incremental"],
                config=job_config["config"]
            )
        
        await mock_scheduler._setup_sync_jobs()
        
        # Проверяем что задачи добавлены в планировщик
        expected_calls = 2  # Только включенные задачи
        assert mock_scheduler.scheduler.add_job.call_count == expected_calls
        
        # Проверяем параметры вызовов
        calls = mock_scheduler.scheduler.add_job.call_args_list
        job_ids = [call[1]["id"] for call in calls]
        assert "confluence_main_confluence" in job_ids
        assert "jira_main_jira" in job_ids
        assert "local_files_bootstrap" not in job_ids  # Отключена
    
    def test_parse_interval_schedule_minutes(self, mock_scheduler):
        """Тест парсинга интервального расписания в минутах"""
        from apscheduler.triggers.interval import IntervalTrigger
        
        trigger = mock_scheduler._parse_interval_schedule("30m")
        
        assert isinstance(trigger, IntervalTrigger)
        # Проверяем что интервал правильный (30 минут)
    
    def test_parse_interval_schedule_hours(self, mock_scheduler):
        """Тест парсинга интервального расписания в часах"""
        from apscheduler.triggers.interval import IntervalTrigger
        
        trigger = mock_scheduler._parse_interval_schedule("2h")
        
        assert isinstance(trigger, IntervalTrigger)
    
    def test_parse_interval_schedule_days(self, mock_scheduler):
        """Тест парсинга интервального расписания в днях"""
        from apscheduler.triggers.interval import IntervalTrigger
        
        trigger = mock_scheduler._parse_interval_schedule("1d")
        
        assert isinstance(trigger, IntervalTrigger)
    
    def test_parse_interval_schedule_invalid(self, mock_scheduler):
        """Тест парсинга недопустимого интервального расписания"""
        with pytest.raises(ValueError):
            mock_scheduler._parse_interval_schedule("invalid")
        
        with pytest.raises(ValueError):
            mock_scheduler._parse_interval_schedule("30x")
    
    @pytest.mark.asyncio
    async def test_execute_sync_job_confluence(self, mock_scheduler):
        """Тест выполнения задачи синхронизации Confluence"""
        job_config = SyncJobConfig(
            source_type="confluence",
            source_name="test",
            enabled=True,
            schedule="0 2 * * *",
            last_sync=None,
            next_sync=None,
            incremental=True,
            config={"url": "https://test.com"}
        )
        
        mock_scheduler.sync_jobs["confluence_test"] = job_config
        
        with patch.object(mock_scheduler, '_sync_confluence') as mock_sync:
            mock_sync.return_value = None
            
            await mock_scheduler._execute_sync_job("confluence_test")
            
            mock_sync.assert_called_once_with(job_config)
            assert job_config.last_sync is not None
    
    @pytest.mark.asyncio
    async def test_execute_sync_job_already_running(self, mock_scheduler):
        """Тест выполнения задачи которая уже выполняется"""
        job_config = SyncJobConfig(
            source_type="confluence",
            source_name="test",
            enabled=True,
            schedule="0 2 * * *",
            last_sync=None,
            next_sync=None,
            incremental=True,
            config={}
        )
        
        mock_scheduler.sync_jobs["confluence_test"] = job_config
        mock_scheduler.running_jobs["confluence_test"] = True
        
        with patch.object(mock_scheduler, '_sync_confluence') as mock_sync:
            await mock_scheduler._execute_sync_job("confluence_test")
            
            # Синхронизация не должна быть вызвана
            mock_sync.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_sync_job_not_found(self, mock_scheduler):
        """Тест выполнения несуществующей задачи"""
        with patch.object(mock_scheduler, '_sync_confluence') as mock_sync:
            await mock_scheduler._execute_sync_job("nonexistent_job")
            
            mock_sync.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_sync_confluence_success(self, mock_scheduler):
        """Тест синхронизации Confluence"""
        job_config = SyncJobConfig(
            source_type="confluence",
            source_name="test",
            enabled=True,
            schedule="0 2 * * *",
            last_sync=None,
            next_sync=None,
            incremental=True,
            config={"url": "https://test.com", "spaces": ["TECH"]}
        )
        
        with patch('core.cron.data_sync_scheduler.ConfluenceIngestionClient') as MockClient:
            mock_client = Mock()
            mock_client.fetch_content_batches = AsyncMock()
            mock_client.fetch_content_batches.return_value = iter([
                [{"id": "1", "title": "Test Page", "content": "Test content"}]
            ])
            MockClient.return_value = mock_client
            
            # Мокаем обработку контента
            mock_scheduler.content_processor.process_batch = AsyncMock(return_value=[
                {"id": "1", "title": "Test Page", "content": "Test content"}
            ])
            mock_scheduler.db_manager.save_documents = AsyncMock(return_value=1)
            mock_scheduler.vector_store.store_embeddings = AsyncMock()
            
            await mock_scheduler._sync_confluence(job_config)
            
            # Проверяем что клиент был создан и методы вызваны
            MockClient.assert_called_once()
            mock_scheduler.content_processor.process_batch.assert_called_once()
            mock_scheduler.db_manager.save_documents.assert_called_once()
            mock_scheduler.vector_store.store_embeddings.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sync_gitlab_success(self, mock_scheduler):
        """Тест синхронизации GitLab"""
        job_config = SyncJobConfig(
            source_type="gitlab",
            source_name="test",
            enabled=True,
            schedule="0 3 * * *",
            last_sync=None,
            next_sync=None,
            incremental=True,
            config={"url": "https://gitlab.com", "groups": ["backend"]}
        )
        
        with patch('core.cron.data_sync_scheduler.GitLabIngestionClient') as MockClient:
            mock_client = Mock()
            mock_client.fetch_content_batches = AsyncMock()
            mock_client.fetch_content_batches.return_value = iter([
                [{"path": "README.md", "content": "# Project"}]
            ])
            MockClient.return_value = mock_client
            
            mock_scheduler.content_processor.process_batch = AsyncMock(return_value=[
                {"path": "README.md", "content": "# Project"}
            ])
            mock_scheduler.db_manager.save_documents = AsyncMock(return_value=1)
            mock_scheduler.vector_store.store_embeddings = AsyncMock()
            
            await mock_scheduler._sync_gitlab(job_config)
            
            MockClient.assert_called_once()
            mock_scheduler.content_processor.process_batch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sync_local_files_success(self, mock_scheduler):
        """Тест синхронизации локальных файлов"""
        job_config = SyncJobConfig(
            source_type="local_files",
            source_name="bootstrap",
            enabled=True,
            schedule="*/30 * * * *",
            last_sync=None,
            next_sync=None,
            incremental=False,
            config={"bootstrap_dir": "/app/bootstrap"}
        )
        
        with patch('core.cron.data_sync_scheduler.LocalFilesProcessor') as MockProcessor, \
             patch('pathlib.Path') as MockPath:
            
            mock_processor = Mock()
            mock_processor.process_files_batches = AsyncMock()
            mock_processor.process_files_batches.return_value = iter([
                [{"path": "guide.pdf", "content": "Training content"}]
            ])
            MockProcessor.return_value = mock_processor
            
            mock_scheduler.content_processor.process_batch = AsyncMock(return_value=[
                {"path": "guide.pdf", "content": "Training content"}
            ])
            mock_scheduler.db_manager.save_documents = AsyncMock(return_value=1)
            mock_scheduler.vector_store.store_embeddings = AsyncMock()
            
            await mock_scheduler._sync_local_files(job_config)
            
            MockProcessor.assert_called_once()
            mock_scheduler.content_processor.process_batch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_sync_status(self, mock_scheduler):
        """Тест получения статуса синхронизации"""
        # Добавляем тестовые задачи
        job_config = SyncJobConfig(
            source_type="confluence",
            source_name="test",
            enabled=True,
            schedule="0 2 * * *",
            last_sync=datetime(2024, 1, 15, 10, 0),
            next_sync=None,
            incremental=True,
            config={}
        )
        mock_scheduler.sync_jobs["confluence_test"] = job_config
        
        # Мокаем планировщик
        mock_job = Mock()
        mock_job.next_run_time = datetime(2024, 1, 16, 2, 0)
        mock_scheduler.scheduler.get_job.return_value = mock_job
        mock_scheduler.scheduler.running = True
        
        status = await mock_scheduler.get_sync_status()
        
        assert status["scheduler_running"] is True
        assert "jobs" in status
        assert "confluence_test" in status["jobs"]
        
        job_status = status["jobs"]["confluence_test"]
        assert job_status["source_type"] == "confluence"
        assert job_status["source_name"] == "test"
        assert job_status["enabled"] is True
        assert job_status["last_sync"] == "2024-01-15T10:00:00"
        assert job_status["next_sync"] == "2024-01-16T02:00:00"
    
    @pytest.mark.asyncio
    async def test_trigger_manual_sync_success(self, mock_scheduler):
        """Тест ручного запуска синхронизации"""
        job_config = SyncJobConfig(
            source_type="confluence",
            source_name="test",
            enabled=True,
            schedule="0 2 * * *",
            last_sync=None,
            next_sync=None,
            incremental=True,
            config={}
        )
        mock_scheduler.sync_jobs["confluence_test"] = job_config
        
        with patch.object(mock_scheduler, '_execute_sync_job') as mock_execute:
            mock_execute.return_value = None
            
            result = await mock_scheduler.trigger_manual_sync("confluence_test")
            
            assert result is True
            mock_execute.assert_called_once_with("confluence_test")
    
    @pytest.mark.asyncio
    async def test_trigger_manual_sync_job_not_found(self, mock_scheduler):
        """Тест ручного запуска несуществующей задачи"""
        result = await mock_scheduler.trigger_manual_sync("nonexistent_job")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_trigger_manual_sync_already_running(self, mock_scheduler):
        """Тест ручного запуска уже выполняющейся задачи"""
        job_config = SyncJobConfig(
            source_type="confluence",
            source_name="test",
            enabled=True,
            schedule="0 2 * * *",
            last_sync=None,
            next_sync=None,
            incremental=True,
            config={}
        )
        mock_scheduler.sync_jobs["confluence_test"] = job_config
        mock_scheduler.running_jobs["confluence_test"] = True
        
        result = await mock_scheduler.trigger_manual_sync("confluence_test")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_job_config_success(self, mock_scheduler):
        """Тест обновления конфигурации задачи"""
        job_config = SyncJobConfig(
            source_type="confluence",
            source_name="test",
            enabled=True,
            schedule="0 2 * * *",
            last_sync=None,
            next_sync=None,
            incremental=True,
            config={}
        )
        mock_scheduler.sync_jobs["confluence_test"] = job_config
        
        # Мокаем планировщик
        mock_scheduler.scheduler.get_job.return_value = Mock()
        mock_scheduler.scheduler.remove_job = Mock()
        mock_scheduler.scheduler.add_job = Mock()
        
        new_config = {
            "enabled": False,
            "schedule": "0 6 * * *",
            "incremental": False
        }
        
        result = await mock_scheduler.update_job_config("confluence_test", new_config)
        
        assert result is True
        assert job_config.enabled is False
        assert job_config.schedule == "0 6 * * *"
        assert job_config.incremental is False
        
        # Проверяем что задача была удалена из планировщика (так как отключена)
        mock_scheduler.scheduler.remove_job.assert_called_once_with("confluence_test")
    
    @pytest.mark.asyncio
    async def test_update_job_config_not_found(self, mock_scheduler):
        """Тест обновления конфигурации несуществующей задачи"""
        result = await mock_scheduler.update_job_config("nonexistent_job", {})
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_shutdown_success(self, mock_scheduler):
        """Тест корректного завершения работы планировщика"""
        # Мокаем компоненты
        mock_scheduler.db_manager.close = AsyncMock()
        mock_scheduler.vector_store.close = AsyncMock()
        mock_scheduler.content_processor.close = AsyncMock()
        mock_scheduler.scheduler.shutdown = Mock()
        
        await mock_scheduler.shutdown()
        
        # Проверяем что все компоненты были корректно закрыты
        mock_scheduler.scheduler.shutdown.assert_called_once_with(wait=True)
        mock_scheduler.db_manager.close.assert_called_once()
        mock_scheduler.vector_store.close.assert_called_once()
        mock_scheduler.content_processor.close.assert_called_once()


class TestSyncSchedulerIntegration:
    """Интеграционные тесты для планировщика синхронизации"""
    
    @pytest.mark.asyncio
    async def test_full_lifecycle(self, temp_config_file):
        """Тест полного жизненного цикла планировщика"""
        scheduler = DataSyncScheduler(config_path=temp_config_file)
        
        with patch.object(scheduler, '_initialize_components') as mock_init, \
             patch.object(scheduler, '_setup_sync_jobs') as mock_setup, \
             patch.object(scheduler, '_execute_sync_job') as mock_execute:
            
            mock_init.return_value = None
            mock_setup.return_value = None
            mock_execute.return_value = None
            
            scheduler.scheduler = Mock()
            scheduler.scheduler.start = Mock()
            scheduler.scheduler.shutdown = Mock()
            scheduler.scheduler.get_job.return_value = Mock(next_run_time=datetime.now())
            
            # 1. Инициализация
            await scheduler.initialize()
            assert len(scheduler.sync_jobs) == 3
            
            # 2. Получение статуса
            status = await scheduler.get_sync_status()
            assert "jobs" in status
            
            # 3. Ручной запуск задачи
            result = await scheduler.trigger_manual_sync("confluence_main_confluence")
            assert result is True
            
            # 4. Обновление конфигурации
            result = await scheduler.update_job_config("confluence_main_confluence", {
                "enabled": False
            })
            assert result is True
            
            # 5. Завершение работы
            await scheduler.shutdown()
            scheduler.scheduler.shutdown.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 