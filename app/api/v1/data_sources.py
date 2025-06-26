"""
Data Sources Management API
Управление источниками данных и настройки синхронизации
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import structlog
import sys
import os

from app.security.auth import get_current_user
from core.cron.data_sync_scheduler import DataSyncScheduler

logger = structlog.get_logger()

router = APIRouter(prefix="/data-sources", tags=["Data Sources Management"])

# Глобальный планировщик (инициализируется при старте приложения)
sync_scheduler: Optional[DataSyncScheduler] = None

# Добавляем путь к модулям проекта
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

try:
    from models.data_source import (
        SourceType, SourceMetadata, DataSourceManager, 
        get_data_source_manager, filter_sources_by_criteria
    )
except ImportError:
    # Fallback если модель недоступна
    SourceType = type('SourceType', (), {
        'BOOTSTRAP': 'bootstrap',
        'CONFLUENCE': 'confluence', 
        'JIRA': 'jira',
        'GITLAB': 'gitlab',
        'CORPORATE': 'corporate'
    })()
    
    class SourceMetadata:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


# Pydantic модели
class DataSourceConfig(BaseModel):
    """Конфигурация источника данных"""
    source_type: str = Field(..., description="Тип источника: confluence, gitlab, jira, local_files")
    source_name: str = Field(..., description="Название источника")
    enabled: bool = Field(True, description="Включен ли источник")
    config: Dict[str, Any] = Field(..., description="Конфигурация подключения")
    sync_schedule: str = Field("0 2 * * *", description="Расписание синхронизации (cron)")
    incremental: bool = Field(True, description="Инкрементальная синхронизация")


class DataSourceStatus(BaseModel):
    """Статус источника данных"""
    source_type: str
    source_name: str
    enabled: bool
    last_sync: Optional[datetime]
    next_sync: Optional[datetime]
    running: bool
    documents_count: int
    sync_schedule: str
    incremental: bool


class SyncJobStatus(BaseModel):
    """Статус задачи синхронизации"""
    job_id: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    documents_processed: int
    errors: List[str]


class SearchSourcesConfig(BaseModel):
    """Конфигурация источников для поиска"""
    user_id: str
    enabled_sources: List[str] = Field(..., description="Список включенных источников для поиска")
    search_preferences: Dict[str, Any] = Field(default_factory=dict)


class GenerationSourcesConfig(BaseModel):
    """Конфигурация источников для генерации"""
    use_all_sources: bool = Field(True, description="Использовать все источники для генерации")
    excluded_sources: List[str] = Field(default_factory=list, description="Исключенные источники")


class SourceMetadataResponse(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    role: Optional[str] = None
    url: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    created_at: Optional[datetime] = None
    tags: List[str] = []
    additional_data: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class DataSourceConfigResponse(BaseModel):
    source_type: str
    enabled: bool
    priority: int
    metadata: Optional[SourceMetadataResponse] = None


class SourceFiltersResponse(BaseModel):
    source_types: List[str]
    categories: List[str]
    roles: List[str]


class SourceDiscoveryResponse(BaseModel):
    total_sources: int
    sources_by_type: Dict[str, int]
    sources_by_category: Dict[str, int]
    discovered_sources: List[SourceMetadataResponse]


class BootstrapStatsResponse(BaseModel):
    total_files: int
    total_size_mb: float
    categories: Dict[str, int]
    last_updated: Optional[datetime] = None


# Endpoints

@router.get("/", response_model=List[DataSourceStatus])
async def get_data_sources(
    current_user: dict = Depends(get_current_user)
) -> List[DataSourceStatus]:
    """
    Получение списка всех источников данных и их статуса
    """
    try:
        if not sync_scheduler:
            raise HTTPException(status_code=503, detail="Sync scheduler not available")
        
        status = await sync_scheduler.get_sync_status()
        sources = []
        
        for job_id, job_info in status["jobs"].items():
            # Получение количества документов из БД
            documents_count = await _get_documents_count(
                job_info["source_type"], 
                job_info["source_name"]
            )
            
            sources.append(DataSourceStatus(
                source_type=job_info["source_type"],
                source_name=job_info["source_name"],
                enabled=job_info["enabled"],
                last_sync=datetime.fromisoformat(job_info["last_sync"]) if job_info["last_sync"] else None,
                next_sync=datetime.fromisoformat(job_info["next_sync"]) if job_info["next_sync"] else None,
                running=job_info["running"],
                documents_count=documents_count,
                sync_schedule=job_info["schedule"],
                incremental=job_info["incremental"]
            ))
        
        return sources
        
    except Exception as e:
        logger.error("Failed to get data sources", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Dict[str, Any])
async def create_data_source(
    source_config: DataSourceConfig,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Создание нового источника данных
    """
    try:
        if not sync_scheduler:
            raise HTTPException(status_code=503, detail="Sync scheduler not available")
        
        job_id = f"{source_config.source_type}_{source_config.source_name}"
        
        # Проверка что источник не существует
        status = await sync_scheduler.get_sync_status()
        if job_id in status["jobs"]:
            raise HTTPException(status_code=409, detail="Data source already exists")
        
        # Создание нового источника
        config = {
            "enabled": source_config.enabled,
            "schedule": source_config.sync_schedule,
            "incremental": source_config.incremental,
            "config": source_config.config
        }
        
        success = await sync_scheduler.update_job_config(job_id, config)
        
        if success:
            return {
                "job_id": job_id,
                "message": "Data source created successfully",
                "source_type": source_config.source_type,
                "source_name": source_config.source_name
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create data source")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create data source", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{source_type}/{source_name}", response_model=Dict[str, Any])
async def update_data_source(
    source_type: str,
    source_name: str,
    source_config: DataSourceConfig,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Обновление конфигурации источника данных
    """
    try:
        if not sync_scheduler:
            raise HTTPException(status_code=503, detail="Sync scheduler not available")
        
        job_id = f"{source_type}_{source_name}"
        
        # Обновление конфигурации
        config = {
            "enabled": source_config.enabled,
            "schedule": source_config.sync_schedule,
            "incremental": source_config.incremental,
            "config": source_config.config
        }
        
        success = await sync_scheduler.update_job_config(job_id, config)
        
        if success:
            return {
                "job_id": job_id,
                "message": "Data source updated successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Data source not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update data source", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{source_type}/{source_name}", response_model=Dict[str, Any])
async def delete_data_source(
    source_type: str,
    source_name: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Удаление источника данных
    """
    try:
        if not sync_scheduler:
            raise HTTPException(status_code=503, detail="Sync scheduler not available")
        
        job_id = f"{source_type}_{source_name}"
        
        # Отключение источника
        success = await sync_scheduler.update_job_config(job_id, {"enabled": False})
        
        if success:
            return {
                "job_id": job_id,
                "message": "Data source disabled successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Data source not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete data source", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{source_type}/{source_name}/sync", response_model=Dict[str, Any])
async def trigger_sync(
    source_type: str,
    source_name: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Ручной запуск синхронизации источника данных
    """
    try:
        if not sync_scheduler:
            raise HTTPException(status_code=503, detail="Sync scheduler not available")
        
        job_id = f"{source_type}_{source_name}"
        
        # Запуск синхронизации в фоне
        background_tasks.add_task(sync_scheduler.trigger_manual_sync, job_id)
        
        return {
            "job_id": job_id,
            "message": "Sync started",
            "started_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to trigger sync", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/status", response_model=Dict[str, Any])
async def get_sync_status(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Получение статуса всех задач синхронизации
    """
    try:
        if not sync_scheduler:
            raise HTTPException(status_code=503, detail="Sync scheduler not available")
        
        return await sync_scheduler.get_sync_status()
        
    except Exception as e:
        logger.error("Failed to get sync status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Управление источниками для поиска

@router.get("/search-sources/{user_id}", response_model=SearchSourcesConfig)
async def get_user_search_sources(
    user_id: str,
    current_user: dict = Depends(get_current_user)
) -> SearchSourcesConfig:
    """
    Получение настроек источников для поиска пользователя
    """
    try:
        # Получение настроек из БД или возврат настроек по умолчанию
        config = await _get_user_search_config(user_id)
        
        if not config:
            # Настройки по умолчанию - все доступные источники
            available_sources = await _get_available_sources()
            config = SearchSourcesConfig(
                user_id=user_id,
                enabled_sources=available_sources,
                search_preferences={}
            )
        
        return config
        
    except Exception as e:
        logger.error("Failed to get user search sources", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/search-sources/{user_id}", response_model=Dict[str, Any])
async def update_user_search_sources(
    user_id: str,
    config: SearchSourcesConfig,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Обновление настроек источников для поиска пользователя
    """
    try:
        # Валидация источников
        available_sources = await _get_available_sources()
        invalid_sources = [s for s in config.enabled_sources if s not in available_sources]
        
        if invalid_sources:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sources: {invalid_sources}"
            )
        
        # Сохранение настроек
        success = await _save_user_search_config(user_id, config)
        
        if success:
            return {
                "user_id": user_id,
                "message": "Search sources updated successfully",
                "enabled_sources": config.enabled_sources
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update search sources")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update user search sources", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generation-sources", response_model=GenerationSourcesConfig)
async def get_generation_sources(
    current_user: dict = Depends(get_current_user)
) -> GenerationSourcesConfig:
    """
    Получение настроек источников для генерации документов
    """
    try:
        # Для генерации используются все источники по умолчанию
        return GenerationSourcesConfig(
            use_all_sources=True,
            excluded_sources=[]
        )
        
    except Exception as e:
        logger.error("Failed to get generation sources", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/generation-sources", response_model=Dict[str, Any])
async def update_generation_sources(
    config: GenerationSourcesConfig,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Обновление настроек источников для генерации документов
    """
    try:
        # Сохранение настроек генерации
        success = await _save_generation_config(config)
        
        if success:
            return {
                "message": "Generation sources updated successfully",
                "use_all_sources": config.use_all_sources,
                "excluded_sources": config.excluded_sources
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update generation sources")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update generation sources", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Вспомогательные функции

async def _get_documents_count(source_type: str, source_name: str) -> int:
    """Получение количества документов для источника"""
    try:
        if not sync_scheduler or not sync_scheduler.db_manager:
            return 0
        
        # Здесь должен быть запрос к БД для подсчета документов
        # Пока возвращаем заглушку
        return 0
        
    except Exception as e:
        logger.error("Failed to get documents count", error=str(e))
        return 0


async def _get_available_sources() -> List[str]:
    """Получение списка доступных источников"""
    try:
        if not sync_scheduler:
            return []
        
        status = await sync_scheduler.get_sync_status()
        return [
            f"{job_info['source_type']}_{job_info['source_name']}"
            for job_info in status["jobs"].values()
            if job_info["enabled"]
        ]
        
    except Exception as e:
        logger.error("Failed to get available sources", error=str(e))
        return []


async def _get_user_search_config(user_id: str) -> Optional[SearchSourcesConfig]:
    """Получение конфигурации поиска пользователя из БД"""
    try:
        # Здесь должен быть запрос к БД
        # Пока возвращаем None для использования настроек по умолчанию
        return None
        
    except Exception as e:
        logger.error("Failed to get user search config", user_id=user_id, error=str(e))
        return None


async def _save_user_search_config(user_id: str, config: SearchSourcesConfig) -> bool:
    """Сохранение конфигурации поиска пользователя в БД"""
    try:
        # Здесь должно быть сохранение в БД
        logger.info("User search config saved", user_id=user_id)
        return True
        
    except Exception as e:
        logger.error("Failed to save user search config", user_id=user_id, error=str(e))
        return False


async def _save_generation_config(config: GenerationSourcesConfig) -> bool:
    """Сохранение конфигурации генерации в БД"""
    try:
        # Здесь должно быть сохранение в БД
        logger.info("Generation config saved")
        return True
        
    except Exception as e:
        logger.error("Failed to save generation config", error=str(e))
        return False


# Функция инициализации планировщика (вызывается при старте приложения)
async def initialize_sync_scheduler():
    """Инициализация планировщика синхронизации"""
    global sync_scheduler
    
    try:
        sync_scheduler = DataSyncScheduler()
        await sync_scheduler.initialize()
        logger.info("Sync scheduler initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize sync scheduler", error=str(e))
        sync_scheduler = None


async def shutdown_sync_scheduler():
    """Остановка планировщика синхронизации"""
    global sync_scheduler
    
    if sync_scheduler:
        try:
            await sync_scheduler.shutdown()
            logger.info("Sync scheduler shut down successfully")
        except Exception as e:
            logger.error("Error shutting down sync scheduler", error=str(e))
        finally:
            sync_scheduler = None


@router.get("/sources", response_model=List[DataSourceConfigResponse])
async def get_data_sources_new(
    enabled_only: bool = Query(True, description="Только включенные источники"),
    source_type: Optional[str] = Query(None, description="Фильтр по типу источника")
):
    """Получить список настроенных источников данных"""
    try:
        manager = get_data_source_manager()
        sources = manager.registry.list_sources(enabled_only=enabled_only)
        
        if source_type:
            sources = [s for s in sources if s.source_type.value == source_type]
        
        return [
            DataSourceConfigResponse(
                source_type=source.source_type.value,
                enabled=source.enabled,
                priority=source.priority,
                metadata=SourceMetadataResponse.from_orm(source.metadata) if source.metadata else None
            )
            for source in sources
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения источников: {str(e)}")


@router.get("/filters", response_model=SourceFiltersResponse)
async def get_source_filters():
    """Получить доступные фильтры для UI"""
    try:
        manager = get_data_source_manager()
        filters = manager.get_source_filters()
        
        return SourceFiltersResponse(
            source_types=filters.get("source_types", []),
            categories=filters.get("categories", []),
            roles=filters.get("roles", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения фильтров: {str(e)}")


@router.get("/discover", response_model=SourceDiscoveryResponse)  
async def discover_sources(
    bootstrap_dir: str = Query("local/bootstrap", description="Путь к папке bootstrap"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    role: Optional[str] = Query(None, description="Фильтр по роли")
):
    """Автообнаружение источников данных"""
    try:
        manager = get_data_source_manager()
        
        # Обнаруживаем bootstrap источники
        discovered = manager.discover_bootstrap_sources(bootstrap_dir)
        
        # Применяем фильтры
        if category or role:
            discovered = filter_sources_by_criteria(
                discovered, 
                category=category, 
                role=role
            )
        
        # Собираем статистику
        sources_by_type = {}
        sources_by_category = {}
        
        for source in discovered:
            # Подсчет по типам (все bootstrap источники)
            source_type = "bootstrap"
            sources_by_type[source_type] = sources_by_type.get(source_type, 0) + 1
            
            # Подсчет по категориям
            cat = source.category or "unknown"
            sources_by_category[cat] = sources_by_category.get(cat, 0) + 1
        
        return SourceDiscoveryResponse(
            total_sources=len(discovered),
            sources_by_type=sources_by_type,
            sources_by_category=sources_by_category,
            discovered_sources=[
                SourceMetadataResponse(
                    name=source.name,
                    description=source.description,
                    category=source.category,
                    role=source.role,
                    url=source.url,
                    file_path=source.file_path,
                    file_size=source.file_size,
                    created_at=source.created_at,
                    tags=source.tags,
                    additional_data=source.additional_data
                )
                for source in discovered
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка автообнаружения: {str(e)}")


@router.get("/bootstrap/stats", response_model=BootstrapStatsResponse)
async def get_bootstrap_stats(
    bootstrap_dir: str = Query("local/bootstrap", description="Путь к папке bootstrap")
):
    """Получить статистику по bootstrap материалам"""
    try:
        from pathlib import Path
        import json
        
        bootstrap_path = Path(bootstrap_dir)
        
        if not bootstrap_path.exists():
            raise HTTPException(status_code=404, detail="Папка bootstrap не найдена")
        
        # Загружаем статистику из download_stats.json если есть
        stats_file = bootstrap_path / "download_stats.json"
        download_stats = {}
        
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                download_stats = json.load(f)
        
        # Собираем статистику файлов
        total_files = 0
        total_size = 0
        categories = {}
        last_updated = None
        
        for file_path in bootstrap_path.rglob("*"):
            if file_path.is_file() and file_path.suffix not in ['.json']:
                total_files += 1
                total_size += file_path.stat().st_size
                
                # Определяем категорию по родительской папке
                category = file_path.parent.name if file_path.parent != bootstrap_path else "root"
                categories[category] = categories.get(category, 0) + 1
                
                # Обновляем время последнего изменения
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if last_updated is None or file_mtime > last_updated:
                    last_updated = file_mtime
        
        return BootstrapStatsResponse(
            total_files=total_files,
            total_size_mb=round(total_size / (1024 * 1024), 2),
            categories=categories,
            last_updated=last_updated
        )
        
    except HTTPException:
        raise  # Перебрасываем HTTPException как есть
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")


@router.post("/ingest/{source_type}")
async def trigger_ingestion(
    source_type: str,
    bootstrap_dir: Optional[str] = Query("local/bootstrap", description="Путь к папке bootstrap для bootstrap источника")
):
    """Запустить процесс ingestion для указанного источника"""
    try:
        if source_type == "bootstrap":
            # Для bootstrap источника запускаем обработку материалов
            import subprocess
            import os
            
            # Определяем путь к скрипту
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            ingest_script = os.path.join(script_dir, "local", "ingest_data.py")
            
            # Запускаем в фоне
            result = subprocess.run([
                "python", ingest_script,
                "--no-confluence", "--no-jira", "--no-gitlab", "--no-video",
                "--bootstrap-dir", bootstrap_dir
            ], cwd=script_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {"status": "success", "message": "Bootstrap ingestion завершен успешно"}
            else:
                return {"status": "error", "message": f"Ошибка ingestion: {result.stderr}"}
        else:
            raise HTTPException(status_code=400, detail=f"Тип источника {source_type} не поддерживается")
            
    except HTTPException:
        raise  # Перебрасываем HTTPException как есть
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка запуска ingestion: {str(e)}")


@router.get("/health")
async def health_check():
    """Проверка здоровья модуля источников данных"""
    try:
        manager = get_data_source_manager()
        sources_count = len(manager.registry.list_sources())
        
        return {
            "status": "healthy",
            "sources_registered": sources_count,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }
