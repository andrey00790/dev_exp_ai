"""
DataSource API Endpoints
API для управления источниками данных
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
import logging

from app.security.auth import get_current_user, require_admin
from domain.integration.datasource_manager import get_datasource_manager, DataSourceManager
from domain.integration.datasource_interface import DataSourceType, DataSourceConfig
from domain.integration.enhanced_semantic_search import (
    get_enhanced_semantic_search, 
    SemanticSearchConfig,
    EnhancedSemanticSearch
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/datasources", tags=["Data Sources"])


# Request/Response models
class DataSourceInfo(BaseModel):
    """Информация об источнике данных"""
    id: str = Field(..., description="ID источника данных")
    name: str = Field(..., description="Название источника")
    type: str = Field(..., description="Тип источника")
    description: Optional[str] = Field(None, description="Описание")
    enabled: bool = Field(..., description="Включен ли источник")
    status: str = Field(..., description="Статус подключения")
    connected: bool = Field(..., description="Подключен ли источник")
    tables_count: int = Field(0, description="Количество таблиц")
    schema_available: bool = Field(False, description="Доступна ли схема")
    tags: List[str] = Field(default_factory=list, description="Теги")
    # UI поля
    selectable: bool = Field(True, description="Можно ли выбирать для поиска")
    default_enabled: bool = Field(False, description="Включен по умолчанию")
    weight: float = Field(1.0, description="Вес для ранжирования")


class HealthCheckResponse(BaseModel):
    """Ответ проверки состояния источников"""
    total_sources: int = Field(..., description="Общее количество источников")
    healthy_sources: int = Field(..., description="Количество здоровых источников")
    sources: Dict[str, Any] = Field(..., description="Детали по источникам")
    check_time: str = Field(..., description="Время проверки")


class SearchSourcesRequest(BaseModel):
    """Запрос получения источников для поиска"""
    user_id: Optional[str] = Field(None, description="ID пользователя")
    source_types: Optional[List[str]] = Field(None, description="Фильтр по типам источников")


class UpdateSourceSelectionRequest(BaseModel):
    """Запрос обновления выбора источников пользователем"""
    user_id: str = Field(..., description="ID пользователя")
    selected_sources: List[str] = Field(..., description="Выбранные источники")
    source_weights: Optional[Dict[str, float]] = Field(None, description="Веса источников")


@router.get("/", response_model=List[DataSourceInfo])
async def get_available_datasources(
    current_user=Depends(get_current_user)
):
    """Получение списка доступных источников данных"""
    try:
        search_service = await get_enhanced_semantic_search()
        sources = await search_service.get_available_sources_for_ui()
        
        return [DataSourceInfo(**source) for source in sources]
        
    except Exception as e:
        logger.error(f"Failed to get datasources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get datasources: {str(e)}"
        )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check_datasources(
    current_user=Depends(require_admin)
):
    """Проверка состояния всех источников данных"""
    try:
        manager = await get_datasource_manager()
        health_status = await manager.health_check_all()
        
        return HealthCheckResponse(**health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/types")
async def get_supported_types(
    current_user=Depends(get_current_user)
):
    """Получение списка поддерживаемых типов источников данных"""
    supported_types = []
    
    for ds_type in DataSourceType:
        type_info = {
            "type": ds_type.value,
            "name": ds_type.name,
            "description": _get_type_description(ds_type),
            "supported": ds_type in [DataSourceType.CLICKHOUSE, DataSourceType.YDB]
        }
        supported_types.append(type_info)
    
    return {
        "supported_types": supported_types,
        "total_types": len(supported_types),
        "implemented_types": sum(1 for t in supported_types if t["supported"])
    }


def _get_type_description(ds_type: DataSourceType) -> str:
    """Получение описания типа источника данных"""
    descriptions = {
        DataSourceType.CLICKHOUSE: "ClickHouse OLAP база данных для аналитики",
        DataSourceType.YDB: "Yandex Database - распределенная SQL база данных",
        DataSourceType.POSTGRESQL: "PostgreSQL реляционная база данных",
        DataSourceType.CONFLUENCE: "Atlassian Confluence для документации",
        DataSourceType.JIRA: "Atlassian Jira для управления проектами",
        DataSourceType.GITLAB: "GitLab для управления кодом",
        DataSourceType.LOCAL_FILES: "Локальные файлы",
        DataSourceType.S3: "Amazon S3 объектное хранилище",
        DataSourceType.ELASTICSEARCH: "Elasticsearch поисковая система"
    }
    return descriptions.get(ds_type, "Источник данных")


@router.get("/search-config")
async def get_search_configuration(
    user_id: Optional[str] = Query(None, description="ID пользователя"),
    current_user=Depends(get_current_user)
):
    """Получение конфигурации поиска для пользователя"""
    try:
        search_service = await get_enhanced_semantic_search()
        sources = await search_service.get_available_sources_for_ui()
        
        # Источники по умолчанию
        default_sources = search_service._get_default_sources()
        
        # Фильтруем только доступные источники
        available_sources = [s for s in sources if s["enabled"] and s["connected"]]
        
        return {
            "available_sources": available_sources,
            "default_sources": default_sources,
            "user_id": user_id,
            "total_sources": len(available_sources),
            "search_enabled": len(available_sources) > 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get search configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get search configuration: {str(e)}"
        )


@router.post("/search-sources")
async def update_user_search_sources(
    request: UpdateSourceSelectionRequest,
    current_user=Depends(get_current_user)
):
    """Обновление выбора источников для поиска пользователем"""
    try:
        # Валидация выбранных источников
        manager = await get_datasource_manager()
        available_sources = manager.get_available_datasources()
        available_ids = {s["source_id"] for s in available_sources}
        
        invalid_sources = [s for s in request.selected_sources if s not in available_ids]
        if invalid_sources:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid source IDs: {invalid_sources}"
            )
        
        # Здесь можно сохранить выбор пользователя в базу данных
        # Пока возвращаем успешный ответ
        
        return {
            "success": True,
            "user_id": request.user_id,
            "selected_sources": request.selected_sources,
            "source_weights": request.source_weights or {},
            "updated_at": "2024-01-04T12:00:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update search sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update search sources: {str(e)}"
        )


@router.get("/{source_id}")
async def get_datasource_details(
    source_id: str,
    current_user=Depends(get_current_user)
):
    """Получение детальной информации об источнике данных"""
    try:
        manager = await get_datasource_manager()
        datasource = await manager.get_datasource(source_id)
        
        if not datasource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Datasource {source_id} not found"
            )
        
        # Получаем информацию о подключении
        connection_info = datasource.get_connection_info()
        
        # Получаем схему если доступна
        schema_info = None
        if manager.schemas.get(source_id):
            schema = manager.schemas[source_id]
            schema_info = {
                "format_type": schema.format_type,
                "tables_count": len(schema.tables),
                "tables": [
                    {
                        "name": table.name,
                        "fields_count": len(table.fields),
                        "primary_keys": table.primary_keys,
                        "metadata": table.metadata
                    }
                    for table in schema.tables[:10]  # Первые 10 таблиц
                ],
                "detected_at": schema.detected_at.isoformat() if schema.detected_at else None
            }
        
        # Проверка состояния
        health_status = await datasource.health_check()
        
        return {
            "source_info": connection_info,
            "schema_info": schema_info,
            "health_status": health_status,
            "last_updated": "2024-01-04T12:00:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get datasource details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get datasource details: {str(e)}"
        )


@router.post("/{source_id}/test-connection")
async def test_datasource_connection(
    source_id: str,
    current_user=Depends(require_admin)
):
    """Тестирование подключения к источнику данных"""
    try:
        manager = await get_datasource_manager()
        datasource = await manager.get_datasource(source_id)
        
        if not datasource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Datasource {source_id} not found"
            )
        
        # Выполняем health check
        health_status = await datasource.health_check()
        
        return {
            "source_id": source_id,
            "test_result": health_status,
            "success": health_status.get("status") == "healthy",
            "tested_at": "2024-01-04T12:00:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test datasource connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test connection: {str(e)}"
        )


@router.post("/{source_id}/refresh-schema")
async def refresh_datasource_schema(
    source_id: str,
    current_user=Depends(require_admin)
):
    """Обновление схемы источника данных"""
    try:
        manager = await get_datasource_manager()
        datasource = await manager.get_datasource(source_id)
        
        if not datasource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Datasource {source_id} not found"
            )
        
        # Обновляем схему
        schema = await datasource.get_schema()
        manager.schemas[source_id] = schema
        
        return {
            "source_id": source_id,
            "schema_updated": True,
            "tables_count": len(schema.tables),
            "format_type": schema.format_type,
            "refreshed_at": "2024-01-04T12:00:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh schema: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh schema: {str(e)}"
        ) 