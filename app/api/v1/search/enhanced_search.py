"""
Enhanced Semantic Search API Endpoints
API для расширенного семантического поиска с множественными источниками
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import logging

from app.security.auth import get_current_user
from domain.integration.enhanced_semantic_search import (
    get_enhanced_semantic_search,
    SemanticSearchConfig,
    SearchCandidate,
    SearchResult
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced-search", tags=["Enhanced Semantic Search"])


# Request/Response models
class EnhancedSearchRequest(BaseModel):
    """Запрос расширенного семантического поиска"""
    query: str = Field(..., description="Поисковый запрос", min_length=1, max_length=1000)
    user_id: Optional[str] = Field(None, description="ID пользователя")
    selected_sources: Optional[List[str]] = Field(None, description="Выбранные источники")
    source_types: Optional[List[str]] = Field(None, description="Фильтр по типам источников")
    limit: int = Field(20, description="Максимальное количество результатов", ge=1, le=100)
    include_snippets: bool = Field(True, description="Включать ли фрагменты текста")
    hybrid_search: bool = Field(True, description="Использовать ли гибридный поиск")
    source_weights: Optional[Dict[str, float]] = Field(None, description="Веса источников")


class SearchCandidateResponse(BaseModel):
    """Кандидат результата поиска"""
    id: str = Field(..., description="ID документа")
    title: str = Field(..., description="Заголовок")
    content: str = Field(..., description="Содержимое")
    source_id: str = Field(..., description="ID источника")
    source_type: str = Field(..., description="Тип источника")
    score: float = Field(..., description="Релевантность", ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные")
    snippet: Optional[str] = Field(None, description="Фрагмент текста")


class EnhancedSearchResponse(BaseModel):
    """Ответ расширенного семантического поиска"""
    candidates: List[SearchCandidateResponse] = Field(..., description="Результаты поиска")
    total_results: int = Field(..., description="Общее количество результатов")
    search_time_ms: float = Field(..., description="Время поиска в миллисекундах")
    sources_searched: List[str] = Field(..., description="Источники, в которых выполнялся поиск")
    query: str = Field(..., description="Поисковый запрос")
    search_stats: Dict[str, Any] = Field(default_factory=dict, description="Статистика поиска")


@router.post("/search", response_model=EnhancedSearchResponse)
async def enhanced_semantic_search(
    request: EnhancedSearchRequest,
    current_user=Depends(get_current_user)
):
    """
    Выполнение расширенного семантического поиска
    
    Поддерживает:
    - Поиск по выбранным источникам
    - Параллельный поиск по множественным источникам
    - Гибридный поиск (векторный + полнотекстовый)
    - Настраиваемые веса источников
    """
    try:
        logger.info(f"Enhanced search request: query='{request.query}', sources={request.selected_sources}")
        
        # Получаем сервис расширенного поиска
        search_service = await get_enhanced_semantic_search()
        
        # Подготавливаем конфигурацию поиска
        search_config = SemanticSearchConfig(
            user_id=request.user_id,
            selected_sources=request.selected_sources or [],
            limit=request.limit,
            include_snippets=request.include_snippets,
            hybrid_search=request.hybrid_search,
            source_weights=request.source_weights or {}
        )
        
        # Применяем фильтр по типам источников если указан
        if request.source_types:
            from domain.integration.datasource_interface import DataSourceType
            try:
                source_types = [DataSourceType(st) for st in request.source_types]
                search_config.source_types = source_types
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid source type: {str(e)}"
                )
        
        # Выполняем поиск
        search_result = await search_service.search(request.query, search_config)
        
        # Преобразуем результаты в формат ответа
        candidates_response = []
        for candidate in search_result.candidates:
            candidate_response = SearchCandidateResponse(
                id=candidate.id,
                title=candidate.title,
                content=candidate.content,
                source_id=candidate.source_id,
                source_type=candidate.source_type.value,
                score=candidate.score,
                metadata=candidate.metadata,
                snippet=candidate.snippet
            )
            candidates_response.append(candidate_response)
        
        # Статистика поиска
        search_stats = {
            "sources_available": len(search_config.selected_sources or []),
            "sources_searched": len(search_result.sources_searched),
            "avg_score": sum(c.score for c in candidates_response) / len(candidates_response) if candidates_response else 0.0,
            "hybrid_search_used": search_config.hybrid_search,
            "user_id": request.user_id
        }
        
        response = EnhancedSearchResponse(
            candidates=candidates_response,
            total_results=search_result.total_results,
            search_time_ms=search_result.search_time_ms,
            sources_searched=search_result.sources_searched,
            query=search_result.query,
            search_stats=search_stats
        )
        
        logger.info(f"Enhanced search completed: {len(candidates_response)} results in {search_result.search_time_ms:.2f}ms")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/sources")
async def get_available_search_sources(
    user_id: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """Получение списка доступных источников для поиска"""
    try:
        search_service = await get_enhanced_semantic_search()
        sources = await search_service.get_available_sources_for_ui()
        
        # Фильтруем только подключенные источники
        available_sources = [s for s in sources if s.get("connected", False)]
        
        return {
            "available_sources": available_sources,
            "total_sources": len(available_sources),
            "default_sources": search_service._get_default_sources(),
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Failed to get search sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get search sources: {str(e)}"
        )


@router.get("/config")
async def get_search_configuration(
    user_id: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """Получение конфигурации поиска"""
    try:
        search_service = await get_enhanced_semantic_search()
        sources = await search_service.get_available_sources_for_ui()
        
        # Базовая конфигурация
        config = {
            "search_enabled": len(sources) > 0,
            "max_results_limit": 100,
            "default_limit": 20,
            "hybrid_search_available": True,
            "source_selection_enabled": True,
            "weight_customization_enabled": True,
            "available_source_types": list(set(s.get("type", "") for s in sources)),
            "total_sources": len(sources),
            "connected_sources": len([s for s in sources if s.get("connected", False)])
        }
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to get search configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get search configuration: {str(e)}"
        )


@router.post("/test")
async def test_enhanced_search(
    current_user=Depends(get_current_user)
):
    """Тестирование расширенного семантического поиска"""
    try:
        # Тестовый запрос
        test_request = EnhancedSearchRequest(
            query="test search query",
            limit=5,
            include_snippets=True,
            hybrid_search=False  # Отключаем гибридный поиск для простого теста
        )
        
        # Выполняем тестовый поиск
        result = await enhanced_semantic_search(test_request, current_user)
        
        return {
            "test_passed": True,
            "results_count": len(result.candidates),
            "search_time_ms": result.search_time_ms,
            "sources_searched": result.sources_searched,
            "message": "Enhanced search test completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Enhanced search test failed: {e}")
        return {
            "test_passed": False,
            "error": str(e),
            "message": "Enhanced search test failed"
        } 