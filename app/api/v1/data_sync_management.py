"""
Data Sync Management API
API для управления синхронизацией данных из различных источников
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.security.auth import get_current_user, User
from app.services.data_sync_scheduler_service import get_data_sync_scheduler

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/data-sync",
    tags=["Data Sync Management"]
)


# Pydantic models
class SyncStatusResponse(BaseModel):
    """Ответ со статусом синхронизации"""
    scheduler_running: bool
    jobs_count: int
    jobs: List[str]
    next_runs: List[Dict]


class PublicSyncStatusResponse(BaseModel):
    """Публичный ответ со статусом синхронизации"""
    scheduler_running: bool
    jobs_count: int
    service_status: str
    next_sync_info: List[Dict]


class ManualSyncRequest(BaseModel):
    """Запрос на ручную синхронизацию"""
    source_type: Optional[str] = Field(None, description="Тип источника: confluence, gitlab, jira, local_files")
    source_name: Optional[str] = Field(None, description="Название источника")


class SyncJobInfo(BaseModel):
    """Информация о задаче синхронизации"""
    job_id: str
    source_type: str
    source_name: str
    enabled: bool
    schedule: str
    next_run: Optional[str]


# Public API Endpoints (without authentication)
@router.get(
    "/health",
    response_model=PublicSyncStatusResponse,
    summary="Sync Health Check",
    description="Получить публичный статус планировщика синхронизации данных (без авторизации)"
)
async def get_sync_health():
    """
    Получить публичный статус планировщика синхронизации данных.
    
    Возвращает базовую информацию о работе планировщика без авторизации.
    """
    try:
        scheduler = await get_data_sync_scheduler()
        status = scheduler.get_sync_status()
        
        # Подготавливаем публичную информацию о следующих запусках
        next_sync_info = []
        for run in status['next_runs'][:3]:  # Показываем только первые 3
            next_sync_info.append({
                "job_name": run['job_name'],
                "next_run": run['next_run'],
                "source_type": run['job_name'].split()[1] if len(run['job_name'].split()) > 1 else "unknown"
            })
        
        service_status = "healthy" if status['scheduler_running'] else "stopped"
        
        return PublicSyncStatusResponse(
            scheduler_running=status['scheduler_running'],
            jobs_count=status['jobs_count'],
            service_status=service_status,
            next_sync_info=next_sync_info
        )
        
    except Exception as e:
        logger.error(f"Failed to get sync health status: {e}")
        return PublicSyncStatusResponse(
            scheduler_running=False,
            jobs_count=0,
            service_status="error",
            next_sync_info=[]
        )


# Protected API Endpoints (with authentication)
@router.get(
    "/status",
    response_model=SyncStatusResponse,
    summary="Sync Status",
    description="Получить детальный статус планировщика синхронизации данных",
    dependencies=[Depends(get_current_user)]
)
async def get_sync_status(current_user: User = Depends(get_current_user)):
    """
    Получить текущий статус планировщика синхронизации данных.
    
    Возвращает:
    - Статус планировщика (работает/остановлен)
    - Количество настроенных задач
    - Список задач
    - Расписание следующих запусков
    """
    try:
        scheduler = await get_data_sync_scheduler()
        status = scheduler.get_sync_status()
        
        return SyncStatusResponse(
            scheduler_running=status['scheduler_running'],
            jobs_count=status['jobs_count'],
            jobs=status['jobs'],
            next_runs=status['next_runs']
        )
        
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.post(
    "/trigger",
    summary="Manual Sync",
    description="Запустить ручную синхронизацию данных",
    dependencies=[Depends(get_current_user)]
)
async def trigger_manual_sync(
    request: ManualSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Запустить ручную синхронизацию данных.
    
    Может синхронизировать:
    - Конкретный источник (указать source_type и source_name)
    - Все источники (не указывать параметры)
    """
    try:
        scheduler = await get_data_sync_scheduler()
        
        if not scheduler.running:
            raise HTTPException(
                status_code=503,
                detail="Data sync scheduler is not running"
            )
        
        # Запуск синхронизации в фоне
        background_tasks.add_task(
            scheduler.trigger_manual_sync,
            request.source_type,
            request.source_name
        )
        
        sync_target = f"{request.source_type}_{request.source_name}" if request.source_type and request.source_name else "all_sources"
        
        logger.info(f"Manual sync triggered by user {current_user.user_id}: {sync_target}")
        
        return {
            "message": "Manual sync triggered successfully",
            "target": sync_target,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger manual sync: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger manual sync: {str(e)}"
        )


@router.get(
    "/jobs",
    response_model=List[SyncJobInfo],
    summary="Sync Jobs",
    description="Получить список всех задач синхронизации",
    dependencies=[Depends(get_current_user)]
)
async def get_sync_jobs(current_user: User = Depends(get_current_user)):
    """
    Получить список всех задач синхронизации.
    
    Возвращает детальную информацию о каждой задаче:
    - ID задачи
    - Тип и название источника
    - Статус (включена/выключена)
    - Расписание
    - Время следующего запуска
    """
    try:
        scheduler = await get_data_sync_scheduler()
        jobs = []
        
        for job_id, job_config in scheduler.sync_jobs.items():
            # Получаем информацию о следующем запуске
            next_run = None
            scheduler_job = scheduler.scheduler.get_job(job_id)
            if scheduler_job and scheduler_job.next_run_time:
                next_run = scheduler_job.next_run_time.isoformat()
            
            jobs.append(SyncJobInfo(
                job_id=job_id,
                source_type=job_config['source_type'],
                source_name=job_config['source_name'],
                enabled=job_config.get('enabled', True),
                schedule=job_config.get('schedule', 'Unknown'),
                next_run=next_run
            ))
        
        return jobs
        
    except Exception as e:
        logger.error(f"Failed to get sync jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync jobs: {str(e)}"
        )


@router.post(
    "/restart",
    summary="Restart Scheduler",
    description="Перезапустить планировщик синхронизации данных",
    dependencies=[Depends(get_current_user)]
)
async def restart_scheduler(current_user: User = Depends(get_current_user)):
    """
    Перезапустить планировщик синхронизации данных.
    
    Полезно при изменении конфигурации или после ошибок.
    """
    try:
        scheduler = await get_data_sync_scheduler()
        
        # Остановка
        if scheduler.running:
            await scheduler.shutdown()
            logger.info("Data sync scheduler stopped for restart")
        
        # Повторная инициализация
        await scheduler.initialize()
        logger.info("Data sync scheduler restarted")
        
        return {
            "message": "Data sync scheduler restarted successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to restart scheduler: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart scheduler: {str(e)}"
        ) 