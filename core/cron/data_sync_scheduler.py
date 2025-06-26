#!/usr/bin/env python3
"""
Data Sync Scheduler - Cron система для автоматической синхронизации данных
Поддерживает настройку расписания для каждого источника данных
"""

import asyncio
import logging
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import structlog

from scripts.ingestion.confluence_client import ConfluenceIngestionClient
from scripts.ingestion.gitlab_client import GitLabIngestionClient
from scripts.ingestion.local_files_processor import LocalFilesProcessor
from scripts.ingestion.database_manager import DatabaseManager
from scripts.ingestion.vector_store_manager import VectorStoreManager
from scripts.ingestion.content_processor import ContentProcessor

logger = structlog.get_logger()


@dataclass
class SyncJobConfig:
    """Конфигурация задачи синхронизации"""
    source_type: str
    source_name: str
    enabled: bool
    schedule: str  # cron expression или interval
    last_sync: Optional[datetime]
    next_sync: Optional[datetime]
    incremental: bool  # инкрементальная или полная синхронизация
    config: Dict[str, Any]


class DataSyncScheduler:
    """Планировщик синхронизации данных"""
    
    def __init__(self, config_path: str = "/app/config/sync_config.yml"):
        self.config_path = config_path
        self.scheduler = AsyncIOScheduler()
        self.sync_jobs: Dict[str, SyncJobConfig] = {}
        self.db_manager = None
        self.vector_store = None
        self.content_processor = None
        self.running_jobs: Dict[str, bool] = {}
        
    async def initialize(self):
        """Инициализация планировщика"""
        try:
            # Загрузка конфигурации
            await self._load_sync_config()
            
            # Инициализация компонентов
            await self._initialize_components()
            
            # Настройка задач
            await self._setup_sync_jobs()
            
            # Запуск планировщика
            self.scheduler.start()
            
            logger.info("Data sync scheduler initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize data sync scheduler", error=str(e))
            raise
    
    async def _load_sync_config(self):
        """Загрузка конфигурации синхронизации"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Парсинг конфигурации задач
            for job_config in config.get("sync_jobs", []):
                job_id = f"{job_config['source_type']}_{job_config['source_name']}"
                
                self.sync_jobs[job_id] = SyncJobConfig(
                    source_type=job_config["source_type"],
                    source_name=job_config["source_name"],
                    enabled=job_config.get("enabled", True),
                    schedule=job_config.get("schedule", "0 2 * * *"),  # По умолчанию в 2:00 каждый день
                    last_sync=None,
                    next_sync=None,
                    incremental=job_config.get("incremental", True),
                    config=job_config.get("config", {})
                )
            
            logger.info("Sync configuration loaded", jobs_count=len(self.sync_jobs))
            
        except FileNotFoundError:
            logger.warning("Sync config file not found, creating default")
            await self._create_default_config()
        except Exception as e:
            logger.error("Failed to load sync config", error=str(e))
            raise
    
    async def _create_default_config(self):
        """Создание конфигурации по умолчанию"""
        default_config = {
            "sync_jobs": [
                {
                    "source_type": "confluence",
                    "source_name": "main_confluence",
                    "enabled": True,
                    "schedule": "0 2 * * *",  # Каждый день в 2:00
                    "incremental": True,
                    "config": {
                        "url": "https://your-company.atlassian.net",
                        "username": "your-email@company.com",
                        "api_token": "your-token",
                        "spaces": ["TECH", "PROJ"]
                    }
                },
                {
                    "source_type": "gitlab",
                    "source_name": "main_gitlab",
                    "enabled": True,
                    "schedule": "0 3 * * *",  # Каждый день в 3:00
                    "incremental": True,
                    "config": {
                        "url": "https://gitlab.company.com",
                        "token": "your-token",
                        "groups": ["backend-team"]
                    }
                },
                {
                    "source_type": "jira",
                    "source_name": "main_jira",
                    "enabled": True,
                    "schedule": "0 4 * * *",  # Каждый день в 4:00
                    "incremental": True,
                    "config": {
                        "url": "https://your-company.atlassian.net",
                        "username": "your-email@company.com",
                        "api_token": "your-token",
                        "projects": ["PROJ", "TECH"]
                    }
                },
                {
                    "source_type": "local_files",
                    "source_name": "bootstrap",
                    "enabled": True,
                    "schedule": "*/30 * * * *",  # Каждые 30 минут
                    "incremental": False,
                    "config": {
                        "bootstrap_dir": "/app/bootstrap",
                        "watch_changes": True
                    }
                }
            ],
            "global_settings": {
                "max_concurrent_jobs": 3,
                "job_timeout_minutes": 120,
                "retry_failed_jobs": True,
                "retry_delay_minutes": 15,
                "cleanup_old_data": True,
                "keep_history_days": 30
            }
        }
        
        # Создание директории если не существует
        import os
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info("Default sync config created", config_path=self.config_path)
        
        # Перезагрузка конфигурации
        await self._load_sync_config()
    
    async def _initialize_components(self):
        """Инициализация компонентов системы"""
        try:
            # Загрузка основной конфигурации
            with open("/app/config/local_config.yml", 'r') as f:
                main_config = yaml.safe_load(f)
            
            # Инициализация компонентов
            self.db_manager = DatabaseManager(main_config["database"])
            await self.db_manager.initialize()
            
            self.vector_store = VectorStoreManager(main_config["vector_db"])
            await self.vector_store.initialize()
            
            self.content_processor = ContentProcessor(
                main_config["text_processing"],
                main_config["embeddings"]
            )
            await self.content_processor.initialize()
            
            logger.info("Sync components initialized")
            
        except Exception as e:
            logger.error("Failed to initialize sync components", error=str(e))
            raise
    
    async def _setup_sync_jobs(self):
        """Настройка задач синхронизации"""
        for job_id, job_config in self.sync_jobs.items():
            if not job_config.enabled:
                logger.info("Skipping disabled job", job_id=job_id)
                continue
            
            try:
                # Парсинг расписания
                if job_config.schedule.count(' ') == 4:
                    # Cron expression
                    trigger = CronTrigger.from_crontab(job_config.schedule)
                else:
                    # Interval (например, "30m", "1h", "2d")
                    trigger = self._parse_interval_schedule(job_config.schedule)
                
                # Добавление задачи в планировщик
                self.scheduler.add_job(
                    func=self._execute_sync_job,
                    trigger=trigger,
                    args=[job_id],
                    id=job_id,
                    name=f"Sync {job_config.source_type} {job_config.source_name}",
                    max_instances=1,
                    coalesce=True,
                    misfire_grace_time=3600  # 1 час
                )
                
                logger.info(
                    "Scheduled sync job",
                    job_id=job_id,
                    source_type=job_config.source_type,
                    schedule=job_config.schedule
                )
                
            except Exception as e:
                logger.error(
                    "Failed to setup sync job",
                    job_id=job_id,
                    error=str(e)
                )
    
    def _parse_interval_schedule(self, schedule: str) -> IntervalTrigger:
        """Парсинг интервального расписания"""
        import re
        
        # Парсинг формата "30m", "1h", "2d"
        match = re.match(r'(\d+)([mhd])', schedule.lower())
        if not match:
            raise ValueError(f"Invalid interval schedule: {schedule}")
        
        value, unit = match.groups()
        value = int(value)
        
        if unit == 'm':
            return IntervalTrigger(minutes=value)
        elif unit == 'h':
            return IntervalTrigger(hours=value)
        elif unit == 'd':
            return IntervalTrigger(days=value)
        else:
            raise ValueError(f"Unsupported time unit: {unit}")
    
    async def _execute_sync_job(self, job_id: str):
        """Выполнение задачи синхронизации"""
        if job_id in self.running_jobs and self.running_jobs[job_id]:
            logger.warning("Job already running, skipping", job_id=job_id)
            return
        
        job_config = self.sync_jobs.get(job_id)
        if not job_config:
            logger.error("Job config not found", job_id=job_id)
            return
        
        self.running_jobs[job_id] = True
        start_time = datetime.now()
        
        try:
            logger.info(
                "Starting sync job",
                job_id=job_id,
                source_type=job_config.source_type,
                incremental=job_config.incremental
            )
            
            # Выполнение синхронизации в зависимости от типа источника
            if job_config.source_type == "confluence":
                await self._sync_confluence(job_config)
            elif job_config.source_type == "gitlab":
                await self._sync_gitlab(job_config)
            elif job_config.source_type == "jira":
                await self._sync_jira(job_config)
            elif job_config.source_type == "local_files":
                await self._sync_local_files(job_config)
            else:
                logger.error("Unknown source type", source_type=job_config.source_type)
                return
            
            # Обновление времени последней синхронизации
            job_config.last_sync = start_time
            
            duration = datetime.now() - start_time
            logger.info(
                "Sync job completed",
                job_id=job_id,
                duration_seconds=duration.total_seconds()
            )
            
        except Exception as e:
            logger.error(
                "Sync job failed",
                job_id=job_id,
                error=str(e)
            )
        finally:
            self.running_jobs[job_id] = False
    
    async def _sync_confluence(self, job_config: SyncJobConfig):
        """Синхронизация данных Confluence"""
        try:
            client = ConfluenceIngestionClient(
                job_config.config,
                {"max_workers": 5, "batch_size": 25, "timeout_seconds": 300}
            )
            
            total_processed = 0
            
            async for batch in client.fetch_content_batches():
                if batch:
                    # Обработка контента
                    processed_batch = await self.content_processor.process_batch(
                        batch, source_type="confluence"
                    )
                    
                    # Сохранение в БД
                    saved_count = await self.db_manager.save_documents(processed_batch)
                    
                    # Сохранение векторов
                    await self.vector_store.store_embeddings(processed_batch)
                    
                    total_processed += saved_count
            
            logger.info(
                "Confluence sync completed",
                source_name=job_config.source_name,
                documents_processed=total_processed
            )
            
        except Exception as e:
            logger.error(
                "Confluence sync failed",
                source_name=job_config.source_name,
                error=str(e)
            )
            raise
    
    async def _sync_gitlab(self, job_config: SyncJobConfig):
        """Синхронизация данных GitLab"""
        try:
            client = GitLabIngestionClient(
                job_config.config,
                {"max_workers": 5, "batch_size": 25, "timeout_seconds": 300}
            )
            
            total_processed = 0
            
            async for batch in client.fetch_content_batches():
                if batch:
                    # Обработка контента
                    processed_batch = await self.content_processor.process_batch(
                        batch, source_type="gitlab"
                    )
                    
                    # Сохранение в БД
                    saved_count = await self.db_manager.save_documents(processed_batch)
                    
                    # Сохранение векторов
                    await self.vector_store.store_embeddings(processed_batch)
                    
                    total_processed += saved_count
            
            logger.info(
                "GitLab sync completed",
                source_name=job_config.source_name,
                documents_processed=total_processed
            )
            
        except Exception as e:
            logger.error(
                "GitLab sync failed",
                source_name=job_config.source_name,
                error=str(e)
            )
            raise
    
    async def _sync_jira(self, job_config: SyncJobConfig):
        """Синхронизация данных Jira"""
        try:
            # Здесь будет реализация Jira клиента
            logger.info("Jira sync not implemented yet")
            
        except Exception as e:
            logger.error(
                "Jira sync failed",
                source_name=job_config.source_name,
                error=str(e)
            )
            raise
    
    async def _sync_local_files(self, job_config: SyncJobConfig):
        """Синхронизация локальных файлов"""
        try:
            from pathlib import Path
            
            processor = LocalFilesProcessor(
                job_config.config,
                {"max_workers": 5, "batch_size": 25, "timeout_seconds": 300}
            )
            
            bootstrap_dir = Path(job_config.config["bootstrap_dir"])
            total_processed = 0
            
            async for batch in processor.process_files_batches(bootstrap_dir):
                if batch:
                    # Обработка контента
                    processed_batch = await self.content_processor.process_batch(
                        batch, source_type="local_files"
                    )
                    
                    # Сохранение в БД
                    saved_count = await self.db_manager.save_documents(processed_batch)
                    
                    # Сохранение векторов
                    await self.vector_store.store_embeddings(processed_batch)
                    
                    total_processed += saved_count
            
            logger.info(
                "Local files sync completed",
                source_name=job_config.source_name,
                documents_processed=total_processed
            )
            
        except Exception as e:
            logger.error(
                "Local files sync failed",
                source_name=job_config.source_name,
                error=str(e)
            )
            raise
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Получение статуса синхронизации"""
        status = {
            "scheduler_running": self.scheduler.running,
            "jobs": {}
        }
        
        for job_id, job_config in self.sync_jobs.items():
            job = self.scheduler.get_job(job_id)
            
            status["jobs"][job_id] = {
                "source_type": job_config.source_type,
                "source_name": job_config.source_name,
                "enabled": job_config.enabled,
                "schedule": job_config.schedule,
                "last_sync": job_config.last_sync.isoformat() if job_config.last_sync else None,
                "next_sync": job.next_run_time.isoformat() if job and job.next_run_time else None,
                "running": self.running_jobs.get(job_id, False),
                "incremental": job_config.incremental
            }
        
        return status
    
    async def trigger_manual_sync(self, job_id: str) -> bool:
        """Ручной запуск синхронизации"""
        if job_id not in self.sync_jobs:
            logger.error("Job not found", job_id=job_id)
            return False
        
        if self.running_jobs.get(job_id, False):
            logger.warning("Job already running", job_id=job_id)
            return False
        
        try:
            # Запуск задачи вне расписания
            await self._execute_sync_job(job_id)
            return True
        except Exception as e:
            logger.error("Manual sync failed", job_id=job_id, error=str(e))
            return False
    
    async def update_job_config(self, job_id: str, config: Dict[str, Any]) -> bool:
        """Обновление конфигурации задачи"""
        if job_id not in self.sync_jobs:
            return False
        
        try:
            job_config = self.sync_jobs[job_id]
            
            # Обновление конфигурации
            if "enabled" in config:
                job_config.enabled = config["enabled"]
            if "schedule" in config:
                job_config.schedule = config["schedule"]
            if "incremental" in config:
                job_config.incremental = config["incremental"]
            if "config" in config:
                job_config.config.update(config["config"])
            
            # Пересоздание задачи в планировщике
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            if job_config.enabled:
                # Добавление обновленной задачи
                if job_config.schedule.count(' ') == 4:
                    trigger = CronTrigger.from_crontab(job_config.schedule)
                else:
                    trigger = self._parse_interval_schedule(job_config.schedule)
                
                self.scheduler.add_job(
                    func=self._execute_sync_job,
                    trigger=trigger,
                    args=[job_id],
                    id=job_id,
                    name=f"Sync {job_config.source_type} {job_config.source_name}",
                    max_instances=1
                )
            
            logger.info("Job config updated", job_id=job_id)
            return True
            
        except Exception as e:
            logger.error("Failed to update job config", job_id=job_id, error=str(e))
            return False
    
    async def shutdown(self):
        """Остановка планировщика"""
        try:
            self.scheduler.shutdown(wait=True)
            
            if self.db_manager:
                await self.db_manager.close()
            if self.vector_store:
                await self.vector_store.close()
            if self.content_processor:
                await self.content_processor.close()
            
            logger.info("Data sync scheduler shut down")
            
        except Exception as e:
            logger.error("Error during scheduler shutdown", error=str(e))


async def main():
    """Главная функция для запуска планировщика"""
    scheduler = DataSyncScheduler()
    
    try:
        await scheduler.initialize()
        
        # Запуск в бесконечном цикле
        while True:
            await asyncio.sleep(60)  # Проверка каждую минуту
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main()) 