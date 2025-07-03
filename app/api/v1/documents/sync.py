from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from app.security.auth import get_current_user
from domain.integration.data_sync_service import (DataSyncService,
                                                  get_data_sync_service)

router = APIRouter()


class SyncRunRequest(BaseModel):
    """Запрос на запуск синхронизации."""

    source_type: str
    source_name: str


@router.post(
    "/run",
    summary="Запустить синхронизацию вручную",
    description="Запускает фоновую задачу для синхронизации указанного источника.",
)
async def run_manual_sync(
    request: SyncRunRequest,
    background_tasks: BackgroundTasks,
    sync_service: DataSyncService = Depends(get_data_sync_service),
    user: dict = Depends(get_current_user),  # Используем фиктивного пользователя
):
    user_id = user.get("user_id", 1)  # Заглушка

    background_tasks.add_task(
        sync_service.sync_source,
        user_id=user_id,
        source_type=request.source_type,
        source_name=request.source_name,
    )

    return {
        "message": f"Синхронизация для {request.source_type}:{request.source_name} запущена в фоновом режиме."
    }


@router.post(
    "/run-startup-sync",
    summary="Запустить синхронизацию при старте",
    description="Запускает синхронизацию для всех источников с флагом auto_sync_on_startup.",
)
async def run_startup_sync(
    sync_service: DataSyncService = Depends(get_data_sync_service),
):
    await sync_service.sync_on_startup()
    return {
        "message": "Синхронизация при старте успешно запущена для всех пользователей."
    }


@router.post(
    "/reschedule",
    summary="Перепланировать фоновые задачи",
    description="Обновляет расписание фоновых задач синхронизации после изменения настроек.",
)
async def reschedule_jobs(
    sync_service: DataSyncService = Depends(get_data_sync_service),
):
    sync_service.schedule_sync_jobs()
    return {"message": "Фоновые задачи успешно перепланированы."}
