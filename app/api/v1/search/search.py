import time
from typing import Any, Dict, List, Optional

import structlog
from fastapi import (APIRouter, Depends, File, Form, HTTPException, Query,
                     UploadFile, status)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.security.auth import get_current_user
from domain.integration.data_source_service import (DataSourceServiceInterface,
                                                    get_data_source_service)
from domain.integration.search_interface import SearchServiceInterface
from domain.integration.search_service import SearchService, get_search_service
from models.base import BaseResponse
from models.search import (ConfigureSourceRequest, ConfigureSourceResponse,
                           DataSource, FileType, SemanticSearchQuery,
                           SemanticSearchResponse, SourceType,
                           SyncStatusResponse, SyncTriggerRequest,
                           UploadFileRequest, UploadFileResponse)

logger = structlog.get_logger()

router = APIRouter(prefix="/search", tags=["Search"])


@router.post(
    "/search",
    response_model=SemanticSearchResponse,
    summary="Semantic Search",
    description="Выполняет семантический поиск по корпоративным данным из настроенных источников",
)
async def semantic_search(
    query: SemanticSearchQuery,
    search_service: SearchServiceInterface = Depends(get_search_service),
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
            sources_searched=sources_searched,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при выполнении поиска: {str(e)}",
        )


@router.get(
    "/sources",
    response_model=List[DataSource],
    summary="List Data Sources",
    description="Получает список всех настроенных источников данных",
)
async def list_data_sources(
    include_disabled: bool = False,
    source_service: DataSourceServiceInterface = Depends(get_data_source_service),
) -> List[DataSource]:
    """Возвращает список всех источников данных."""
    try:
        return await source_service.list_sources(include_disabled=include_disabled)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении источников: {str(e)}",
        )


@router.post(
    "/sources",
    response_model=ConfigureSourceResponse,
    summary="Configure Data Source",
    description="Настраивает новый источник данных (Confluence, Jira, GitLab и т.д.)",
)
async def configure_data_source(
    request: ConfigureSourceRequest,
    source_service: DataSourceServiceInterface = Depends(get_data_source_service),
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
            request.source_type, request.config
        )

        # Создаем источник
        source = await source_service.create_source(request)

        return ConfigureSourceResponse(
            source=source,
            message="Источник данных успешно настроен",
            connection_test_passed=connection_test,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при настройке источника: {str(e)}",
        )


@router.put(
    "/sources/{source_id}",
    response_model=ConfigureSourceResponse,
    summary="Update Data Source",
    description="Обновляет настройки источника данных",
)
async def update_data_source(
    source_id: str,
    request: ConfigureSourceRequest,
    source_service: DataSourceServiceInterface = Depends(get_data_source_service),
) -> ConfigureSourceResponse:
    """Обновляет существующий источник данных."""
    try:
        # Тестируем подключение с новыми настройками
        connection_test = await source_service.test_connection(
            request.source_type, request.config
        )

        # Обновляем источник
        source = await source_service.update_source(source_id, request)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Источник данных не найден",
            )

        return ConfigureSourceResponse(
            source=source,
            message="Источник данных успешно обновлен",
            connection_test_passed=connection_test,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении источника: {str(e)}",
        )


@router.delete(
    "/sources/{source_id}",
    response_model=BaseResponse,
    summary="Delete Data Source",
    description="Удаляет источник данных и все связанные документы",
)
async def delete_data_source(
    source_id: str,
    source_service: DataSourceServiceInterface = Depends(get_data_source_service),
) -> BaseResponse:
    """Удаляет источник данных."""
    try:
        success = await source_service.delete_source(source_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Источник данных не найден",
            )

        return BaseResponse(message="Источник данных и все связанные документы удалены")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении источника: {str(e)}",
        )


@router.post(
    "/upload",
    response_model=UploadFileResponse,
    summary="Upload Document",
    description="Загружает документ (PDF, TXT, EPUB, DOC) для индексации и поиска",
)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(None),
    description: str = Form(None),
    tags: str = Form(""),  # Comma-separated tags
    author: str = Form(None),
    search_service: SearchServiceInterface = Depends(get_search_service),
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
                status_code=status.HTTP_400_BAD_REQUEST, detail="Имя файла обязательно"
            )

        file_extension = file.filename.split(".")[-1].lower()
        try:
            file_type = FileType(file_extension)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неподдерживаемый тип файла: {file_extension}",
            )

        # Создаем запрос на загрузку
        upload_request = UploadFileRequest(
            title=title or file.filename,
            description=description,
            tags=[tag.strip() for tag in tags.split(",") if tag.strip()],
            author=author,
        )

        # Загружаем и обрабатываем файл
        result = await search_service.upload_document(file, file_type, upload_request)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при загрузке файла: {str(e)}",
        )


@router.post(
    "/sync",
    response_model=SyncStatusResponse,
    summary="Trigger Data Sync",
    description="Запускает синхронизацию данных из настроенных источников",
)
async def trigger_sync(
    request: SyncTriggerRequest,
    source_service: DataSourceServiceInterface = Depends(get_data_source_service),
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
            message=f"Синхронизация завершена. Обработано документов: {total_processed}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при синхронизации: {str(e)}",
        )


@router.get(
    "/sync/status",
    response_model=SyncStatusResponse,
    summary="Get Sync Status",
    description="Получает статус последней синхронизации",
)
async def get_sync_status(
    source_service: DataSourceServiceInterface = Depends(get_data_source_service),
) -> SyncStatusResponse:
    """Возвращает статус последней синхронизации."""
    try:
        return await source_service.get_sync_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении статуса синхронизации: {str(e)}",
        )


@router.get(
    "/sources/types",
    response_model=List[Dict[str, Any]],
    summary="Get Source Types",
    description="Получает список поддерживаемых типов источников данных",
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
                "space_keys": ["SPACE1", "SPACE2"],  # Optional: specific spaces
            },
        },
        {
            "type": SourceType.JIRA,
            "name": "Jira",
            "description": "Atlassian Jira issue tracker",
            "required_config": {
                "url": "https://your-domain.atlassian.net",
                "username": "your-email@company.com",
                "api_token": "your-api-token",
                "project_keys": ["PROJ1", "PROJ2"],  # Optional: specific projects
            },
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
                "include_issues": True,
            },
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
                "include_issues": True,
            },
        },
    ]


# Pydantic модели
class SearchRequest(BaseModel):
    """Запрос на поиск"""

    query: str = Field(
        ..., description="Поисковый запрос", min_length=1, max_length=1000
    )
    sources: Optional[List[str]] = Field(
        None,
        description="Источники для поиска (если не указаны - используются настройки пользователя)",
    )
    limit: int = Field(
        10, description="Максимальное количество результатов", ge=1, le=100
    )
    offset: int = Field(0, description="Смещение для пагинации", ge=0)
    filters: Optional[Dict[str, Any]] = Field(
        None, description="Дополнительные фильтры"
    )
    include_snippets: bool = Field(True, description="Включать ли фрагменты текста")
    search_type: str = Field(
        "semantic", description="Тип поиска: semantic, keyword, hybrid"
    )


class SearchResult(BaseModel):
    """Результат поиска"""

    id: str
    title: str
    content: str
    source_type: str
    source_name: str
    url: Optional[str]
    score: float
    highlights: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]
    created_at: Optional[str]
    updated_at: Optional[str]


class SearchResponse(BaseModel):
    """Ответ поиска"""

    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float
    sources_searched: List[str]
    filters_applied: Optional[Dict[str, Any]]
    pagination: Dict[str, Any]


class SourcesListResponse(BaseModel):
    """Список доступных источников"""

    sources: List[Dict[str, Any]]
    total_sources: int
    user_enabled_sources: List[str]


class SearchFeedbackRequest(BaseModel):
    """Запрос на отправку обратной связи"""

    search_id: str = Field(..., description="ID поиска")
    result_id: str = Field(..., description="ID результата")
    feedback_type: str = Field(
        ..., description="Тип обратной связи: like, dislike, irrelevant"
    )
    comment: Optional[str] = Field(None, description="Комментарий")


# Endpoints


@router.post("/", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    current_user: dict = Depends(get_current_user),
    search_service: SearchServiceInterface = Depends(get_search_service),
) -> SearchResponse:
    """
    Поиск документов с возможностью выбора источников

    Поддерживает:
    - Семантический поиск по выбранным источникам
    - Ключевой поиск
    - Гибридный поиск
    - Фильтрацию по метаданным
    - Пагинацию результатов
    """
    import time

    start_time = time.time()

    try:
        user_id = str(current_user.id) if current_user else "anonymous"

        # Определение источников для поиска
        search_sources = request.sources
        if not search_sources:
            # Если источники не указаны, используем настройки пользователя
            search_sources = await _get_user_search_sources(user_id)

        if not search_sources:
            # Если настройки пользователя не найдены, используем все доступные
            search_sources = await _get_all_available_sources()

        # Выполнение поиска
        search_params = {
            "query": request.query,
            "sources": search_sources,
            "limit": request.limit,
            "offset": request.offset,
            "search_type": request.search_type,
            "include_snippets": request.include_snippets,
            "filters": request.filters or {},
        }

        results = await search_service.search_documents(**search_params)

        # Подготовка ответа
        search_time_ms = (time.time() - start_time) * 1000

        # Конвертация результатов
        search_results = []
        for result in results.get("results", []):
            search_results.append(
                SearchResult(
                    id=result.get("id"),
                    title=result.get("title"),
                    content=result.get("content"),
                    source_type=result.get("source_type"),
                    source_name=result.get("source_name"),
                    url=result.get("url"),
                    score=result.get("score", 0.0),
                    highlights=result.get("highlights"),
                    metadata=result.get("metadata"),
                    created_at=result.get("created_at"),
                    updated_at=result.get("updated_at"),
                )
            )

        return SearchResponse(
            query=request.query,
            results=search_results,
            total_results=results.get("total_results", len(search_results)),
            search_time_ms=search_time_ms,
            sources_searched=search_sources,
            filters_applied=request.filters,
            pagination={
                "limit": request.limit,
                "offset": request.offset,
                "has_more": len(search_results) == request.limit,
            },
        )

    except Exception as e:
        logger.error("Search failed", error=str(e), query=request.query)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/sources", response_model=SourcesListResponse)
async def get_available_sources(
    current_user: dict = Depends(get_current_user),
) -> SourcesListResponse:
    """
    Получение списка доступных источников данных для поиска
    """
    try:
        user_id = str(current_user.id) if current_user else "anonymous"

        # Получение всех доступных источников
        all_sources = await _get_all_sources_with_stats()

        # Получение настроек пользователя
        user_enabled = await _get_user_search_sources(user_id)

        return SourcesListResponse(
            sources=all_sources,
            total_sources=len(all_sources),
            user_enabled_sources=user_enabled or [],
        )

    except Exception as e:
        logger.error("Failed to get available sources", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sources/update", response_model=Dict[str, Any])
async def update_user_search_sources(
    sources: List[str], current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Обновление списка источников для поиска пользователя
    """
    try:
        user_id = str(current_user.id) if current_user else "anonymous"

        # Валидация источников
        available_sources = await _get_all_available_sources()
        invalid_sources = [s for s in sources if s not in available_sources]

        if invalid_sources:
            raise HTTPException(
                status_code=400, detail=f"Invalid sources: {invalid_sources}"
            )

        # Сохранение настроек
        success = await _save_user_search_sources(user_id, sources)

        if success:
            return {
                "message": "Search sources updated successfully",
                "user_id": user_id,
                "enabled_sources": sources,
            }
        else:
            raise HTTPException(
                status_code=500, detail="Failed to update search sources"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update user search sources", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., description="Частичный поисковый запрос"),
    limit: int = Query(5, description="Количество предложений", ge=1, le=20),
    current_user: dict = Depends(get_current_user),
    search_service: SearchServiceInterface = Depends(get_search_service),
) -> Dict[str, Any]:
    """
    Получение предложений для автодополнения поиска
    """
    try:
        user_id = str(current_user.id) if current_user else "anonymous"

        # Получение источников пользователя
        user_sources = await _get_user_search_sources(user_id)

        # Получение предложений
        suggestions = await search_service.get_search_suggestions(
            query=query, sources=user_sources, limit=limit
        )

        return {
            "query": query,
            "suggestions": suggestions,
            "sources_used": user_sources,
        }

    except Exception as e:
        logger.error("Failed to get search suggestions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_search_history(
    limit: int = Query(20, description="Количество записей", ge=1, le=100),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Получение истории поисковых запросов пользователя
    """
    try:
        user_id = str(current_user.id) if current_user else "anonymous"

        # Получение истории из БД
        history = await _get_user_search_history(user_id, limit)

        return {"user_id": user_id, "history": history, "total_searches": len(history)}

    except Exception as e:
        logger.error("Failed to get search history", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_search_feedback(
    request: SearchFeedbackRequest, current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Отправка обратной связи по результатам поиска
    """
    try:
        user_id = str(current_user.id) if current_user else "anonymous"

        # Валидация типа обратной связи
        valid_feedback_types = ["like", "dislike", "irrelevant", "helpful"]
        if request.feedback_type not in valid_feedback_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid feedback type. Must be one of: {valid_feedback_types}",
            )

        # Сохранение обратной связи
        feedback_id = await _save_search_feedback(
            user_id=user_id,
            search_id=request.search_id,
            result_id=request.result_id,
            feedback_type=request.feedback_type,
            comment=request.comment,
        )

        return {
            "feedback_id": feedback_id,
            "message": "Feedback submitted successfully",
            "search_id": request.search_id,
            "result_id": request.result_id,
            "feedback_type": request.feedback_type,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to submit search feedback", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def get_search_analytics(
    days: int = Query(30, description="Период в днях", ge=1, le=365),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Получение аналитики поиска (только для администраторов)
    """
    try:
        # Проверка прав администратора
        if "admin" not in (current_user.roles or []):
            raise HTTPException(status_code=403, detail="Admin access required")

        # Получение аналитики
        analytics = await _get_search_analytics(days)

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get search analytics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Вспомогательные функции


async def _get_user_search_sources(user_id: str) -> List[str]:
    """Получение источников поиска пользователя"""
    try:
        # Здесь должен быть запрос к БД для получения настроек пользователя
        # Пока возвращаем все доступные источники
        return await _get_all_available_sources()

    except Exception as e:
        logger.error("Failed to get user search sources", user_id=user_id, error=str(e))
        return []


async def _get_all_available_sources() -> List[str]:
    """Получение всех доступных источников"""
    try:
        # Здесь должен быть запрос к системе управления источниками
        # Пока возвращаем стандартный набор
        return ["confluence_main", "gitlab_main", "jira_main", "local_files_bootstrap"]

    except Exception as e:
        logger.error("Failed to get all available sources", error=str(e))
        return []


async def _get_all_sources_with_stats() -> List[Dict[str, Any]]:
    """Получение всех источников со статистикой"""
    try:
        sources = [
            {
                "id": "confluence_main",
                "name": "Main Confluence",
                "type": "confluence",
                "enabled": True,
                "documents_count": 1250,
                "last_sync": "2024-01-15T10:30:00Z",
                "description": "Основная база знаний Confluence",
            },
            {
                "id": "gitlab_main",
                "name": "Main GitLab",
                "type": "gitlab",
                "enabled": True,
                "documents_count": 850,
                "last_sync": "2024-01-15T11:00:00Z",
                "description": "Документация из GitLab репозиториев",
            },
            {
                "id": "jira_main",
                "name": "Main Jira",
                "type": "jira",
                "enabled": True,
                "documents_count": 2100,
                "last_sync": "2024-01-15T09:45:00Z",
                "description": "Задачи и требования из Jira",
            },
            {
                "id": "local_files_bootstrap",
                "name": "Bootstrap Files",
                "type": "local_files",
                "enabled": True,
                "documents_count": 45,
                "last_sync": "2024-01-15T12:00:00Z",
                "description": "Локальные файлы для обучения",
            },
        ]

        return sources

    except Exception as e:
        logger.error("Failed to get sources with stats", error=str(e))
        return []


async def _save_user_search_sources(user_id: str, sources: List[str]) -> bool:
    """Сохранение источников поиска пользователя"""
    try:
        # Здесь должно быть сохранение в БД
        logger.info("User search sources saved", user_id=user_id, sources=sources)
        return True

    except Exception as e:
        logger.error(
            "Failed to save user search sources", user_id=user_id, error=str(e)
        )
        return False


async def _get_user_search_history(user_id: str, limit: int) -> List[Dict[str, Any]]:
    """Получение истории поиска пользователя"""
    try:
        # Здесь должен быть запрос к БД
        # Пока возвращаем заглушку
        return [
            {
                "search_id": f"search_{i}",
                "query": f"example query {i}",
                "timestamp": f"2024-01-{15-i:02d}T10:00:00Z",
                "results_count": 10 - i,
                "sources_used": ["confluence_main", "gitlab_main"],
            }
            for i in range(min(limit, 10))
        ]

    except Exception as e:
        logger.error("Failed to get user search history", user_id=user_id, error=str(e))
        return []


async def _save_search_feedback(
    user_id: str,
    search_id: str,
    result_id: str,
    feedback_type: str,
    comment: Optional[str],
) -> str:
    """Сохранение обратной связи по поиску"""
    try:
        # Здесь должно быть сохранение в БД
        feedback_id = f"feedback_{search_id}_{result_id}"
        logger.info(
            "Search feedback saved",
            user_id=user_id,
            feedback_id=feedback_id,
            feedback_type=feedback_type,
        )
        return feedback_id

    except Exception as e:
        logger.error("Failed to save search feedback", error=str(e))
        raise


async def _get_search_analytics(days: int) -> Dict[str, Any]:
    """Получение аналитики поиска"""
    try:
        # Здесь должен быть запрос к БД для получения аналитики
        # Пока возвращаем заглушку
        return {
            "period_days": days,
            "total_searches": 1250,
            "unique_users": 85,
            "avg_results_per_search": 8.5,
            "top_queries": [
                {"query": "API documentation", "count": 125},
                {"query": "authentication", "count": 98},
                {"query": "deployment", "count": 87},
            ],
            "sources_usage": {
                "confluence_main": 45.2,
                "gitlab_main": 28.7,
                "jira_main": 18.1,
                "local_files_bootstrap": 8.0,
            },
            "search_quality": {
                "avg_satisfaction": 4.2,
                "click_through_rate": 0.78,
                "zero_results_rate": 0.12,
            },
        }

    except Exception as e:
        logger.error("Failed to get search analytics", error=str(e))
        return {}
