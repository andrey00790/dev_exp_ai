from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
import time

from models.search import (
    SemanticSearchQuery, SemanticSearchResponse, 
    DataSource, ConfigureSourceRequest, ConfigureSourceResponse,
    UploadFileRequest, UploadFileResponse, FileType,
    SyncTriggerRequest, SyncStatusResponse, SourceType
)
from models.base import BaseResponse
from services.search_service import SearchServiceInterface, get_search_service
from services.data_source_service import DataSourceServiceInterface, get_data_source_service

router = APIRouter()


@router.post(
    "/search",
    response_model=SemanticSearchResponse,
    summary="Semantic Search",
    description="Выполняет семантический поиск по корпоративным данным из настроенных источников"
)
async def semantic_search(
    query: SemanticSearchQuery,
    search_service: SearchServiceInterface = Depends(get_search_service)
) -> SemanticSearchResponse:
    """
    Выполняет семантический поиск по корпоративным данным.
    
    Поиск происходит по векторным представлениям документов из:
    - Confluence
    - Jira  
    - GitLab
    - Загруженных файлов
    - Других настроенных источников
    """
    try:
        start_time = time.time()
        
        # Выполняем семантический поиск
        results = await search_service.semantic_search(query)
        
        search_time_ms = int((time.time() - start_time) * 1000)
        
        # Получаем список источников, по которым производился поиск
        sources_searched = await search_service.get_searched_sources(query)
        
        return SemanticSearchResponse(
            results=results,
            total_found=len(results),
            query=query.query,
            search_time_ms=search_time_ms,
            sources_searched=sources_searched
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при выполнении поиска: {str(e)}"
        )


@router.get(
    "/sources",
    response_model=List[DataSource],
    summary="List Data Sources",
    description="Получает список всех настроенных источников данных"
)
async def list_data_sources(
    include_disabled: bool = False,
    source_service: DataSourceServiceInterface = Depends(get_data_source_service)
) -> List[DataSource]:
    """Возвращает список всех источников данных."""
    try:
        return await source_service.list_sources(include_disabled=include_disabled)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении источников: {str(e)}"
        )


@router.post(
    "/sources",
    response_model=ConfigureSourceResponse,
    summary="Configure Data Source",
    description="Настраивает новый источник данных (Confluence, Jira, GitLab и т.д.)"
)
async def configure_data_source(
    request: ConfigureSourceRequest,
    source_service: DataSourceServiceInterface = Depends(get_data_source_service)
) -> ConfigureSourceResponse:
    """
    Настраивает новый источник данных.
    
    Поддерживаемые источники:
    - Confluence (требует URL и токен)
    - Jira (требует URL, email, токен)
    - GitLab (требует URL и токен)
    - Другие модульно подключаемые источники
    """
    try:
        # Тестируем подключение
        connection_test = await source_service.test_connection(
            request.source_type, 
            request.config
        )
        
        # Создаем источник
        source = await source_service.create_source(request)
        
        return ConfigureSourceResponse(
            source=source,
            message="Источник данных успешно настроен",
            connection_test_passed=connection_test
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при настройке источника: {str(e)}"
        )


@router.put(
    "/sources/{source_id}",
    response_model=ConfigureSourceResponse,
    summary="Update Data Source",
    description="Обновляет настройки источника данных"
)
async def update_data_source(
    source_id: str,
    request: ConfigureSourceRequest,
    source_service: DataSourceServiceInterface = Depends(get_data_source_service)
) -> ConfigureSourceResponse:
    """Обновляет существующий источник данных."""
    try:
        # Тестируем подключение с новыми настройками
        connection_test = await source_service.test_connection(
            request.source_type, 
            request.config
        )
        
        # Обновляем источник
        source = await source_service.update_source(source_id, request)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Источник данных не найден"
            )
        
        return ConfigureSourceResponse(
            source=source,
            message="Источник данных успешно обновлен",
            connection_test_passed=connection_test
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении источника: {str(e)}"
        )


@router.delete(
    "/sources/{source_id}",
    response_model=BaseResponse,
    summary="Delete Data Source", 
    description="Удаляет источник данных и все связанные документы"
)
async def delete_data_source(
    source_id: str,
    source_service: DataSourceServiceInterface = Depends(get_data_source_service)
) -> BaseResponse:
    """Удаляет источник данных."""
    try:
        success = await source_service.delete_source(source_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Источник данных не найден"
            )
        
        return BaseResponse(
            message="Источник данных и все связанные документы удалены"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении источника: {str(e)}"
        )


@router.post(
    "/upload",
    response_model=UploadFileResponse,
    summary="Upload Document",
    description="Загружает документ (PDF, TXT, EPUB, DOC) для индексации и поиска"
)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(None),
    description: str = Form(None),
    tags: str = Form(""),  # Comma-separated tags
    author: str = Form(None),
    search_service: SearchServiceInterface = Depends(get_search_service)
) -> UploadFileResponse:
    """
    Загружает документ для индексации.
    
    Поддерживаемые форматы:
    - PDF
    - TXT
    - EPUB
    - DOC/DOCX
    - Markdown (MD)
    """
    try:
        # Проверяем тип файла
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Имя файла обязательно"
            )
        
        file_extension = file.filename.split('.')[-1].lower()
        try:
            file_type = FileType(file_extension)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неподдерживаемый тип файла: {file_extension}"
            )
        
        # Создаем запрос на загрузку
        upload_request = UploadFileRequest(
            title=title or file.filename,
            description=description,
            tags=[tag.strip() for tag in tags.split(',') if tag.strip()],
            author=author
        )
        
        # Загружаем и обрабатываем файл
        result = await search_service.upload_document(
            file, 
            file_type, 
            upload_request
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при загрузке файла: {str(e)}"
        )


@router.post(
    "/sync",
    response_model=SyncStatusResponse,
    summary="Trigger Data Sync",
    description="Запускает синхронизацию данных из настроенных источников"
)
async def trigger_sync(
    request: SyncTriggerRequest,
    source_service: DataSourceServiceInterface = Depends(get_data_source_service)
) -> SyncStatusResponse:
    """
    Запускает синхронизацию данных из источников.
    
    Оптимизированная синхронизация:
    - Если документ существует и не изменился - пропускаем
    - Если документ новый или изменился - обновляем
    - Если документ удален в источнике - помечаем как удаленный
    """
    try:
        # Запускаем синхронизацию
        sync_results = await source_service.trigger_sync(request)
        
        # Определяем общий статус
        overall_status = "completed"
        if any(result.status == "failed" for result in sync_results):
            overall_status = "failed"
        elif any(result.status == "in_progress" for result in sync_results):
            overall_status = "in_progress"
        
        total_processed = sum(result.documents_processed for result in sync_results)
        
        return SyncStatusResponse(
            results=sync_results,
            overall_status=overall_status,
            message=f"Синхронизация завершена. Обработано документов: {total_processed}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при синхронизации: {str(e)}"
        )


@router.get(
    "/sync/status",
    response_model=SyncStatusResponse,
    summary="Get Sync Status",
    description="Получает статус последней синхронизации"
)
async def get_sync_status(
    source_service: DataSourceServiceInterface = Depends(get_data_source_service)
) -> SyncStatusResponse:
    """Возвращает статус последней синхронизации."""
    try:
        return await source_service.get_sync_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении статуса синхронизации: {str(e)}"
        )


@router.get(
    "/sources/types",
    response_model=List[Dict[str, Any]],
    summary="Get Source Types",
    description="Получает список поддерживаемых типов источников данных"
)
async def get_source_types() -> List[Dict[str, Any]]:
    """
    Возвращает список поддерживаемых типов источников данных
    с описанием необходимых параметров конфигурации.
    """
    return [
        {
            "type": SourceType.CONFLUENCE,
            "name": "Confluence",
            "description": "Atlassian Confluence wiki",
            "required_config": {
                "url": "https://your-domain.atlassian.net",
                "username": "your-email@company.com", 
                "api_token": "your-api-token",
                "space_keys": ["SPACE1", "SPACE2"]  # Optional: specific spaces
            }
        },
        {
            "type": SourceType.JIRA,
            "name": "Jira",
            "description": "Atlassian Jira issue tracker",
            "required_config": {
                "url": "https://your-domain.atlassian.net",
                "username": "your-email@company.com",
                "api_token": "your-api-token", 
                "project_keys": ["PROJ1", "PROJ2"]  # Optional: specific projects
            }
        },
        {
            "type": SourceType.GITLAB,
            "name": "GitLab",
            "description": "GitLab repositories and documentation",
            "required_config": {
                "url": "https://gitlab.company.com",
                "access_token": "your-access-token",
                "project_ids": [123, 456],  # Optional: specific projects
                "include_wikis": True,
                "include_issues": True
            }
        },
        {
            "type": SourceType.GITHUB,
            "name": "GitHub",
            "description": "GitHub repositories and documentation",
            "required_config": {
                "access_token": "your-github-token",
                "organization": "your-org",  # Optional
                "repositories": ["repo1", "repo2"],  # Optional: specific repos
                "include_wikis": True,
                "include_issues": True
            }
        }
    ] 