#!/usr/bin/env python3
"""
Data Sync Scheduler Service
Упрощенная версия планировщика для интеграции с main.py
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import yaml

logger = logging.getLogger(__name__)


class DataSyncSchedulerService:
    """Сервис планировщика синхронизации данных"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.running = False
        self.config = None
        self.sync_jobs = {}
        
    async def initialize(self):
        """Инициализация планировщика"""
        try:
            # Загрузка конфигурации
            config_path = "config/sync_config.yml"
            
            if not os.path.exists(config_path):
                logger.warning(f"Sync config file not found: {config_path}")
                await self._create_default_config(config_path)
                
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
                
            # Настройка задач
            await self._setup_sync_jobs()
            
            # Запуск планировщика
            self.scheduler.start()
            self.running = True
            
            logger.info("✅ Data sync scheduler service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize data sync scheduler: {e}")
            raise
            
    async def _create_default_config(self, config_path: str):
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
                        "username": "ai-assistant@company.com",
                        "api_token": "${CONFLUENCE_API_TOKEN}",
                        "spaces": ["TECH", "PROJ", "ARCH", "API"]
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
                        "token": "${GITLAB_API_TOKEN}",
                        "groups": ["backend-team", "frontend-team", "devops-team"]
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
                        "username": "ai-assistant@company.com",
                        "api_token": "${JIRA_API_TOKEN}",
                        "projects": ["PROJ", "TECH", "ARCH", "BUG"]
                    }
                },
                {
                    "source_type": "local_files",
                    "source_name": "bootstrap",
                    "enabled": True,
                    "schedule": "*/30 * * * *",  # Каждые 30 минут
                    "incremental": False,
                    "config": {
                        "bootstrap_dir": "./local",
                        "supported_formats": [".pdf", ".txt", ".md", ".docx"],
                        "watch_changes": True
                    }
                }
            ],
            "global_settings": {
                "max_concurrent_jobs": 3,
                "job_timeout_minutes": 120,
                "retry_failed_jobs": True,
                "retry_delay_minutes": 15,
                "max_retries": 3,
                "cleanup_old_data": True,
                "keep_history_days": 30
            }
        }
        
        # Создание директории если не существует
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
            
        logger.info(f"Default sync config created: {config_path}")
        
    async def _setup_sync_jobs(self):
        """Настройка задач синхронизации"""
        if not self.config or 'sync_jobs' not in self.config:
            logger.warning("No sync jobs configured")
            return
            
        for job_config in self.config['sync_jobs']:
            if not job_config.get('enabled', True):
                continue
                
            job_id = f"{job_config['source_type']}_{job_config['source_name']}"
            
            try:
                # Создание cron trigger
                trigger = CronTrigger.from_crontab(job_config.get('schedule', '0 2 * * *'))
                
                # Добавление задачи в планировщик
                self.scheduler.add_job(
                    func=self._execute_sync_job,
                    trigger=trigger,
                    args=[job_id, job_config],
                    id=job_id,
                    name=f"Sync {job_config['source_type']} {job_config['source_name']}",
                    max_instances=1,
                    coalesce=True,
                    misfire_grace_time=3600  # 1 час
                )
                
                self.sync_jobs[job_id] = job_config
                
                logger.info(f"📅 Scheduled sync job: {job_config['source_type']} {job_config['source_name']} ({job_config['schedule']})")
                
            except Exception as e:
                logger.error(f"❌ Failed to setup sync job {job_id}: {e}")
                
    async def _execute_sync_job(self, job_id: str, job_config: Dict):
        """Выполнение задачи синхронизации"""
        start_time = datetime.now(timezone.utc)
        
        logger.info(f"🔄 Starting sync job: {job_id}")
        
        try:
            source_type = job_config['source_type']
            source_name = job_config['source_name']
            
            if source_type == "confluence":
                await self._sync_confluence(job_config)
            elif source_type == "gitlab":
                await self._sync_gitlab(job_config)
            elif source_type == "jira":
                await self._sync_jira(job_config)
            elif source_type == "local_files":
                await self._sync_local_files(job_config)
            else:
                logger.warning(f"Unknown source type: {source_type}")
                
            duration = datetime.now(timezone.utc) - start_time
            logger.info(f"✅ Sync job completed: {job_id} ({duration.total_seconds():.2f}s)")
            
        except Exception as e:
            logger.error(f"❌ Sync job failed: {job_id} - {e}")
            
    async def _sync_confluence(self, job_config: Dict):
        """Синхронизация данных Confluence"""
        logger.info(f"🔄 Confluence sync: {job_config['source_name']}")
        
        # Здесь будет реальная логика синхронизации
        # Пока что имитация
        await asyncio.sleep(2)
        
        logger.info(f"✅ Confluence sync completed: {job_config['source_name']}")
        
    async def _sync_gitlab(self, job_config: Dict):
        """Синхронизация данных GitLab"""
        logger.info(f"🔄 GitLab sync: {job_config['source_name']}")
        
        # Здесь будет реальная логика синхронизации
        # Пока что имитация
        await asyncio.sleep(2)
        
        logger.info(f"✅ GitLab sync completed: {job_config['source_name']}")
        
    async def _sync_jira(self, job_config: Dict):
        """Синхронизация данных Jira"""
        logger.info(f"🔄 Jira sync: {job_config['source_name']}")
        
        # Здесь будет реальная логика синхронизации
        # Пока что имитация
        await asyncio.sleep(2)
        
        logger.info(f"✅ Jira sync completed: {job_config['source_name']}")
        
    async def _sync_local_files(self, job_config: Dict):
        """Синхронизация локальных файлов"""
        logger.info(f"🔄 Local files sync: {job_config['source_name']}")
        
        # Здесь будет реальная логика синхронизации
        # Пока что имитация
        await asyncio.sleep(1)
        
        logger.info(f"✅ Local files sync completed: {job_config['source_name']}")
        
    async def trigger_manual_sync(self, source_type: str = None, source_name: str = None):
        """Запуск ручной синхронизации"""
        if source_type and source_name:
            job_id = f"{source_type}_{source_name}"
            if job_id in self.sync_jobs:
                logger.info(f"🔄 Manual sync triggered: {job_id}")
                await self._execute_sync_job(job_id, self.sync_jobs[job_id])
            else:
                logger.warning(f"Job not found: {job_id}")
        else:
            # Запуск всех задач
            logger.info("🔄 Manual sync triggered for all sources")
            for job_id, job_config in self.sync_jobs.items():
                await self._execute_sync_job(job_id, job_config)
                
    def get_sync_status(self) -> Dict:
        """Получение статуса синхронизации"""
        return {
            "scheduler_running": self.running,
            "jobs_count": len(self.sync_jobs),
            "jobs": list(self.sync_jobs.keys()),
            "next_runs": self._get_next_runs()
        }
        
    def _get_next_runs(self) -> List[Dict]:
        """Получение расписания следующих запусков"""
        next_runs = []
        
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            if next_run:
                next_runs.append({
                    "job_id": job.id,
                    "job_name": job.name,
                    "next_run": next_run.isoformat()
                })
                
        return sorted(next_runs, key=lambda x: x['next_run'])
        
    async def shutdown(self):
        """Остановка планировщика"""
        if self.running:
            self.scheduler.shutdown()
            self.running = False
            logger.info("✅ Data sync scheduler stopped")


# Глобальный экземпляр
data_sync_scheduler = None


async def init_data_sync_scheduler():
    """Инициализация глобального экземпляра планировщика"""
    global data_sync_scheduler
    data_sync_scheduler = DataSyncSchedulerService()
    await data_sync_scheduler.initialize()
    return data_sync_scheduler


async def get_data_sync_scheduler():
    """Получение глобального экземпляра планировщика"""
    global data_sync_scheduler
    if data_sync_scheduler is None:
        data_sync_scheduler = await init_data_sync_scheduler()
    return data_sync_scheduler 