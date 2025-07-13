"""
Document Generation API with All Sources Support
Генерация документов с использованием всех источников данных
Enhanced with standardized async patterns for enterprise reliability
Version: 2.1 Async Optimized
"""

import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

# Import standardized async patterns
from app.core.async_utils import (AsyncTimeouts, async_retry,
                                  create_background_task, safe_gather,
                                  with_timeout)
from app.core.exceptions import AsyncRetryError, AsyncTimeoutError
from app.security.auth import get_current_user
from domain.core.generation_service import (GenerationServiceInterface,
                                            get_generation_service)
from models.base import BaseResponse
from models.generation import (AIQuestion, AnswerRequest,
                               FinalGenerationRequest, FinalGenerationResponse,
                               GeneratedRFC, GenerateRequest, GenerateResponse,
                               GenerationSession, QuestionType, RFCSection,
                               TaskType)

logger = structlog.get_logger()

router = APIRouter(prefix="/generate", tags=["Document Generation"])


# Pydantic модели
class RFCGenerationRequest(BaseModel):
    """Запрос на генерацию RFC"""

    task_description: str = Field(..., description="Описание задачи", min_length=10)
    project_context: Optional[str] = Field(None, description="Контекст проекта")
    technical_requirements: Optional[str] = Field(
        None, description="Технические требования"
    )
    stakeholders: Optional[List[str]] = Field(
        None, description="Заинтересованные стороны"
    )
    priority: str = Field(
        "medium", description="Приоритет: low, medium, high, critical"
    )
    use_all_sources: bool = Field(
        True, description="Использовать все доступные источники"
    )
    excluded_sources: Optional[List[str]] = Field(
        None, description="Исключенные источники"
    )
    template_type: str = Field("standard", description="Тип шаблона RFC")


class ArchitectureGenerationRequest(BaseModel):
    """Запрос на генерацию архитектурного документа"""

    system_name: str = Field(..., description="Название системы")
    system_description: str = Field(..., description="Описание системы")
    requirements: List[str] = Field(..., description="Требования к системе")
    constraints: Optional[List[str]] = Field(None, description="Ограничения")
    architecture_type: str = Field("microservices", description="Тип архитектуры")
    include_diagrams: bool = Field(True, description="Включать диаграммы")
    use_all_sources: bool = Field(
        True, description="Использовать все источники для контекста"
    )


class DocumentationGenerationRequest(BaseModel):
    """Запрос на генерацию документации"""

    doc_type: str = Field(
        ..., description="Тип документации: api, user_guide, technical_spec"
    )
    title: str = Field(..., description="Заголовок документа")
    content_outline: Optional[List[str]] = Field(
        None, description="Структура документа"
    )
    target_audience: str = Field("developers", description="Целевая аудитория")
    detail_level: str = Field("detailed", description="Уровень детализации")
    include_examples: bool = Field(True, description="Включать примеры")
    use_all_sources: bool = Field(True, description="Использовать все источники")


class GenerationResponse(BaseModel):
    """Ответ генерации"""

    task_id: str
    status: str
    content: Optional[str]
    metadata: Dict[str, Any]
    sources_used: List[str]
    generation_time_ms: float
    tokens_used: Optional[int]
    cost_estimate: Optional[float]


class GenerationStatus(BaseModel):
    """Статус генерации"""

    task_id: str
    status: str
    progress: float
    started_at: str
    estimated_completion: Optional[str]
    error_message: Optional[str]


# Добавляем новые Pydantic модели для enhanced RFC generation


class EnhancedRFCRequest(BaseModel):
    """Enhanced RFC generation request with diagrams and analysis"""

    task_description: str = Field(
        ..., description="Описание задачи для RFC", min_length=10
    )
    project_path: Optional[str] = Field(
        None, description="Путь к проекту для анализа архитектуры"
    )
    project_context: Optional[str] = Field(None, description="Контекст проекта")
    technical_requirements: Optional[str] = Field(
        None, description="Технические требования"
    )
    stakeholders: Optional[List[str]] = Field(
        None, description="Заинтересованные стороны"
    )
    priority: str = Field(
        "medium", description="Приоритет: low, medium, high, critical"
    )
    template_type: str = Field(
        "architecture", description="Тип шаблона: architecture, design, process, api"
    )
    include_diagrams: bool = Field(True, description="Включать Mermaid диаграммы")
    include_codebase_analysis: bool = Field(
        True, description="Включать анализ кодовой базы"
    )
    use_all_sources: bool = Field(
        True, description="Использовать все доступные источники"
    )
    excluded_sources: Optional[List[str]] = Field(
        None, description="Исключенные источники"
    )


class ProjectAnalysisRequest(BaseModel):
    """Request for project architecture analysis"""

    project_path: str = Field(..., description="Путь к проекту")
    analysis_depth: str = Field(
        "standard", description="Глубина анализа: quick, standard, comprehensive"
    )
    include_suggestions: bool = Field(
        True, description="Включать рекомендации по улучшению"
    )


class EnhancedGenerationResponse(GenerationResponse):
    """Enhanced response with diagrams and analysis data"""

    rfc_data: Optional[Dict[str, Any]] = Field(
        None, description="Структурированные данные RFC"
    )
    diagrams: Optional[Dict[str, str]] = Field(None, description="Mermaid диаграммы")
    project_analysis: Optional[Dict[str, Any]] = Field(
        None, description="Анализ проекта"
    )
    architecture_recommendations: Optional[List[str]] = Field(
        None, description="Архитектурные рекомендации"
    )


# Endpoints


@router.post("/rfc", response_model=GenerationResponse)
@async_retry(max_attempts=2, delay=2.0, exceptions=(HTTPException,))
async def generate_rfc(
    request: RFCGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    generation_service: GenerationServiceInterface = Depends(get_generation_service),
) -> GenerationResponse:
    """
    Генерация RFC документа с использованием всех источников данных
    Enhanced with async patterns for enterprise reliability and performance

    Использует:
    - Confluence для поиска существующих RFC и стандартов
    - GitLab для анализа кода и архитектурных решений
    - Jira для понимания требований и задач
    - Локальные файлы для корпоративных стандартов

    Optimizations:
    - Concurrent context gathering from multiple sources
    - Intelligent timeout calculation based on complexity
    - Retry logic with exponential backoff
    - Background task processing for large operations
    """
    start_time = time.time()

    try:
        user_id = str(current_user.id) if current_user else "anonymous"

        # Calculate timeout based on RFC complexity
        timeout = _calculate_rfc_generation_timeout(request)

        # Execute RFC generation with timeout protection
        result = await with_timeout(
            _generate_rfc_internal(request, user_id, generation_service),
            timeout,
            f"RFC generation timed out (task: '{request.task_description[:50]}...', sources: {request.use_all_sources})",
            {
                "task_description_length": len(request.task_description),
                "has_project_context": bool(request.project_context),
                "has_technical_requirements": bool(request.technical_requirements),
                "use_all_sources": request.use_all_sources,
                "user_id": user_id,
            },
        )

        generation_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"✅ RFC generation completed in {generation_time_ms:.1f}ms "
            f"(task: '{request.task_description[:50]}...', sources: {len(result.get('sources_used', []))})"
        )

        return GenerationResponse(
            task_id=result.get("task_id", ""),
            status=result.get("status", "completed"),
            content=result.get("content", ""),
            metadata={
                "rfc_type": request.template_type,
                "priority": request.priority,
                "context_sources_count": result.get("context_sources_count", 0),
                "template_used": result.get("template_used", "standard"),
                "timeout_used": timeout,
                "async_optimized": True,
            },
            sources_used=result.get("sources_used", []),
            generation_time_ms=generation_time_ms,
            tokens_used=result.get("tokens_used"),
            cost_estimate=result.get("cost_estimate"),
        )

    except AsyncTimeoutError as e:
        logger.error(f"❌ RFC generation timed out: {e}")
        raise HTTPException(
            status_code=504,
            detail="RFC generation timed out: Task too complex or system overloaded. Try simplifying requirements or breaking into smaller parts.",
        )
    except AsyncRetryError as e:
        logger.error(f"❌ RFC generation failed after retries: {e}")
        raise HTTPException(
            status_code=500, detail=f"RFC generation failed after retries: {str(e)}"
        )
    except Exception as e:
        logger.error("RFC generation failed", error=str(e), user_id=user_id)
        raise HTTPException(status_code=500, detail=f"RFC generation failed: {str(e)}")


async def _generate_rfc_internal(
    request: RFCGenerationRequest,
    user_id: str,
    generation_service: GenerationServiceInterface,
) -> Dict[str, Any]:
    """Internal RFC generation with concurrent processing"""

    # Step 1: Determine sources concurrently with validation
    sources_task = _get_generation_sources(
        use_all=request.use_all_sources, excluded=request.excluded_sources or []
    )

    # Step 2: Start context gathering immediately (don't wait for sources validation)
    context_task = _gather_context_from_sources(
        query=request.task_description,
        sources=None,  # Will use all available sources initially
        context_type="rfc",
    )

    # Execute both tasks concurrently
    sources_to_use, context_data = await safe_gather(
        sources_task,
        context_task,
        return_exceptions=True,
        timeout=AsyncTimeouts.DATABASE_QUERY * 3,  # 30 seconds for data gathering
        max_concurrency=2,
    )

    # Handle potential exceptions
    if isinstance(sources_to_use, Exception):
        logger.warning(f"⚠️ Sources detection failed: {sources_to_use}, using defaults")
        sources_to_use = ["confluence_main"]

    if isinstance(context_data, Exception):
        logger.warning(
            f"⚠️ Context gathering failed: {context_data}, using minimal context"
        )
        context_data = []

    # Step 3: Generate RFC with enhanced parameters
    generation_params = {
        "task_description": request.task_description,
        "project_context": request.project_context,
        "technical_requirements": request.technical_requirements,
        "stakeholders": request.stakeholders,
        "priority": request.priority,
        "template_type": request.template_type,
        "context_data": context_data,
        "user_id": user_id,
    }

    # Generate RFC with service
    result = await generation_service.generate_rfc(**generation_params)

    # Add metadata
    result["sources_used"] = sources_to_use
    result["context_sources_count"] = len(context_data)

    return result


def _calculate_rfc_generation_timeout(request: RFCGenerationRequest) -> float:
    """Calculate appropriate timeout based on RFC complexity"""
    base_timeout = AsyncTimeouts.LLM_REQUEST * 2  # 120 seconds for RFC generation

    # Add extra time based on complexity factors
    extra_time = 0

    # Task description length
    if len(request.task_description) > 1000:
        extra_time += (
            len(request.task_description) - 1000
        ) / 200  # 1s per 200 extra chars

    # Additional context adds processing time
    if request.project_context and len(request.project_context) > 500:
        extra_time += len(request.project_context) / 500  # 1s per 500 chars

    if request.technical_requirements and len(request.technical_requirements) > 500:
        extra_time += len(request.technical_requirements) / 500

    # Using all sources requires more time
    if request.use_all_sources:
        extra_time += 30  # 30 seconds for comprehensive source analysis

    # Priority affects timeout
    priority_multipliers = {
        "critical": 2.0,  # Critical tasks get more time
        "high": 1.5,
        "medium": 1.0,
        "low": 0.8,
    }
    multiplier = priority_multipliers.get(request.priority, 1.0)

    return min((base_timeout + extra_time) * multiplier, 600.0)  # Cap at 10 minutes


@router.post("/architecture", response_model=GenerationResponse)
@async_retry(max_attempts=2, delay=2.0, exceptions=(HTTPException,))
async def generate_architecture(
    request: ArchitectureGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    generation_service: GenerationServiceInterface = Depends(get_generation_service),
) -> GenerationResponse:
    """
    Генерация архитектурного документа с использованием всех источников
    Enhanced with concurrent processing and intelligent timeout management

    Анализирует:
    - Существующие архитектурные решения из Confluence
    - Код и структуру проектов из GitLab
    - Требования и ограничения из Jira
    - Корпоративные стандарты из локальных файлов
    """
    start_time = time.time()

    try:
        user_id = str(current_user.id) if current_user else "anonymous"

        # Calculate timeout based on architecture complexity
        timeout = _calculate_architecture_generation_timeout(request)

        # Execute architecture generation with timeout protection
        result = await with_timeout(
            _generate_architecture_internal(request, user_id, generation_service),
            timeout,
            f"Architecture generation timed out (system: '{request.system_name}', type: {request.architecture_type})",
            {
                "system_name": request.system_name,
                "system_description_length": len(request.system_description),
                "requirements_count": len(request.requirements),
                "architecture_type": request.architecture_type,
                "include_diagrams": request.include_diagrams,
                "user_id": user_id,
            },
        )

        generation_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"✅ Architecture generation completed in {generation_time_ms:.1f}ms "
            f"(system: '{request.system_name}', type: {request.architecture_type})"
        )

        return GenerationResponse(
            task_id=result.get("task_id", ""),
            status=result.get("status", "completed"),
            content=result.get("content", ""),
            metadata={
                "architecture_type": request.architecture_type,
                "includes_diagrams": request.include_diagrams,
                "patterns_analyzed": result.get("patterns_analyzed", 0),
                "requirements_count": len(request.requirements),
                "timeout_used": timeout,
                "async_optimized": True,
            },
            sources_used=result.get("sources_used", []),
            generation_time_ms=generation_time_ms,
            tokens_used=result.get("tokens_used"),
            cost_estimate=result.get("cost_estimate"),
        )

    except AsyncTimeoutError as e:
        logger.error(f"❌ Architecture generation timed out: {e}")
        raise HTTPException(
            status_code=504,
            detail="Architecture generation timed out: System too complex. Try breaking into smaller components or simplifying requirements.",
        )
    except AsyncRetryError as e:
        logger.error(f"❌ Architecture generation failed after retries: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Architecture generation failed after retries: {str(e)}",
        )
    except Exception as e:
        logger.error("Architecture generation failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=500, detail=f"Architecture generation failed: {str(e)}"
        )


async def _generate_architecture_internal(
    request: ArchitectureGenerationRequest,
    user_id: str,
    generation_service: GenerationServiceInterface,
) -> Dict[str, Any]:
    """Internal architecture generation with concurrent processing"""

    # Concurrent tasks for data gathering
    tasks = [
        _get_generation_sources(use_all=request.use_all_sources, excluded=[]),
        _gather_context_from_sources(
            query=f"{request.system_name} {request.system_description}",
            sources=None,
            context_type="architecture",
        ),
    ]

    # If we need architectural patterns analysis, add it as a concurrent task
    if request.architecture_type:
        # Start pattern analysis concurrently (we'll provide context later)
        pattern_analysis_task = _analyze_architectural_patterns_placeholder(
            request.architecture_type
        )
        tasks.append(pattern_analysis_task)

    # Execute all data gathering tasks concurrently
    results = await safe_gather(
        *tasks,
        return_exceptions=True,
        timeout=AsyncTimeouts.DATABASE_QUERY
        * 4,  # 40 seconds for comprehensive data gathering
        max_concurrency=3,
    )

    # Process results
    sources_to_use = (
        results[0] if not isinstance(results[0], Exception) else ["confluence_main"]
    )
    context_data = results[1] if not isinstance(results[1], Exception) else []
    architectural_patterns = (
        results[2] if len(results) > 2 and not isinstance(results[2], Exception) else []
    )

    # Now analyze patterns with actual context data if we didn't do it concurrently
    if not architectural_patterns:
        architectural_patterns = await _analyze_architectural_patterns(
            context_data, request.architecture_type
        )

    # Prepare generation parameters
    generation_params = {
        "system_name": request.system_name,
        "system_description": request.system_description,
        "requirements": request.requirements,
        "constraints": request.constraints,
        "architecture_type": request.architecture_type,
        "include_diagrams": request.include_diagrams,
        "context_data": context_data,
        "architectural_patterns": architectural_patterns,
        "user_id": user_id,
    }

    # Generate architecture
    result = await generation_service.generate_architecture(**generation_params)

    # Add metadata
    result["sources_used"] = sources_to_use
    result["patterns_analyzed"] = len(architectural_patterns)

    return result


def _calculate_architecture_generation_timeout(
    request: ArchitectureGenerationRequest,
) -> float:
    """Calculate timeout based on architecture complexity"""
    base_timeout = AsyncTimeouts.LLM_REQUEST * 2  # 120 seconds

    extra_time = 0

    # System complexity
    if len(request.system_description) > 1000:
        extra_time += (len(request.system_description) - 1000) / 300

    # Requirements count
    extra_time += len(request.requirements) * 2  # 2 seconds per requirement

    # Constraints add complexity
    if request.constraints:
        extra_time += len(request.constraints) * 2

    # Diagrams require more processing
    if request.include_diagrams:
        extra_time += 30  # 30 seconds for diagram generation

    # Different architecture types have different complexity
    architecture_multipliers = {
        "microservices": 1.5,
        "monolith": 1.0,
        "serverless": 1.3,
        "event_driven": 1.4,
        "layered": 1.1,
    }
    multiplier = architecture_multipliers.get(request.architecture_type, 1.0)

    return min((base_timeout + extra_time) * multiplier, 480.0)  # Cap at 8 minutes


async def _analyze_architectural_patterns_placeholder(
    architecture_type: str,
) -> List[Dict[str, Any]]:
    """Placeholder for concurrent architectural pattern analysis"""
    # This is a placeholder that returns basic patterns
    # In a real implementation, this would analyze patterns concurrently
    basic_patterns = {
        "microservices": [
            {"pattern": "Service Discovery", "relevance": 0.9},
            {"pattern": "API Gateway", "relevance": 0.8},
            {"pattern": "Circuit Breaker", "relevance": 0.7},
        ],
        "monolith": [
            {"pattern": "Layered Architecture", "relevance": 0.9},
            {"pattern": "MVC Pattern", "relevance": 0.8},
        ],
        "serverless": [
            {"pattern": "Function as a Service", "relevance": 0.9},
            {"pattern": "Event-Driven Architecture", "relevance": 0.8},
        ],
    }

    return basic_patterns.get(architecture_type, [])


@router.post("/documentation", response_model=GenerationResponse)
@async_retry(max_attempts=2, delay=1.5, exceptions=(HTTPException,))
async def generate_documentation(
    request: DocumentationGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    generation_service: GenerationServiceInterface = Depends(get_generation_service),
) -> GenerationResponse:
    """
    Генерация документации с использованием всех источников
    Enhanced with concurrent processing and smart timeout management

    Создает документацию на основе:
    - Существующей документации из Confluence
    - Кода и комментариев из GitLab
    - Требований из Jira
    - Шаблонов из локальных файлов
    """
    start_time = time.time()

    try:
        user_id = str(current_user.id) if current_user else "anonymous"

        # Calculate timeout based on documentation complexity
        timeout = _calculate_documentation_generation_timeout(request)

        # Execute documentation generation with timeout protection
        result = await with_timeout(
            _generate_documentation_internal(request, user_id, generation_service),
            timeout,
            f"Documentation generation timed out (title: '{request.title}', type: {request.doc_type})",
            {
                "title": request.title,
                "doc_type": request.doc_type,
                "target_audience": request.target_audience,
                "detail_level": request.detail_level,
                "include_examples": request.include_examples,
                "user_id": user_id,
            },
        )

        generation_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"✅ Documentation generation completed in {generation_time_ms:.1f}ms "
            f"(title: '{request.title}', type: {request.doc_type})"
        )

        return GenerationResponse(
            task_id=result.get("task_id", ""),
            status=result.get("status", "completed"),
            content=result.get("content", ""),
            metadata={
                "doc_type": request.doc_type,
                "target_audience": request.target_audience,
                "detail_level": request.detail_level,
                "includes_examples": request.include_examples,
                "existing_docs_analyzed": result.get("existing_docs_analyzed", 0),
                "timeout_used": timeout,
                "async_optimized": True,
            },
            sources_used=result.get("sources_used", []),
            generation_time_ms=generation_time_ms,
            tokens_used=result.get("tokens_used"),
            cost_estimate=result.get("cost_estimate"),
        )

    except AsyncTimeoutError as e:
        logger.error(f"❌ Documentation generation timed out: {e}")
        raise HTTPException(
            status_code=504,
            detail="Documentation generation timed out: Content too complex. Try reducing scope or detail level.",
        )
    except AsyncRetryError as e:
        logger.error(f"❌ Documentation generation failed after retries: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Documentation generation failed after retries: {str(e)}",
        )
    except Exception as e:
        logger.error("Documentation generation failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=500, detail=f"Documentation generation failed: {str(e)}"
        )


async def _generate_documentation_internal(
    request: DocumentationGenerationRequest,
    user_id: str,
    generation_service: GenerationServiceInterface,
) -> Dict[str, Any]:
    """Internal documentation generation with concurrent processing"""

    # Concurrent data gathering tasks
    tasks = [
        _get_generation_sources(use_all=request.use_all_sources, excluded=[]),
        _gather_context_from_sources(
            query=request.title, sources=None, context_type="documentation"
        ),
    ]

    # Execute data gathering concurrently
    sources_to_use, context_data = await safe_gather(
        *tasks,
        return_exceptions=True,
        timeout=AsyncTimeouts.DATABASE_QUERY * 3,  # 30 seconds
        max_concurrency=2,
    )

    # Handle exceptions
    if isinstance(sources_to_use, Exception):
        sources_to_use = ["confluence_main"]
    if isinstance(context_data, Exception):
        context_data = []

    # Analyze existing documentation concurrently with parameter preparation
    existing_docs_task = _analyze_existing_documentation(context_data, request.doc_type)

    # Prepare basic parameters while analysis runs
    generation_params = {
        "doc_type": request.doc_type,
        "title": request.title,
        "content_outline": request.content_outline,
        "target_audience": request.target_audience,
        "detail_level": request.detail_level,
        "include_examples": request.include_examples,
        "context_data": context_data,
        "user_id": user_id,
    }

    # Wait for existing docs analysis to complete
    existing_docs = await existing_docs_task
    generation_params["existing_docs"] = existing_docs

    # Generate documentation
    result = await generation_service.generate_documentation(**generation_params)

    # Add metadata
    result["sources_used"] = sources_to_use
    result["existing_docs_analyzed"] = len(existing_docs)

    return result


def _calculate_documentation_generation_timeout(
    request: DocumentationGenerationRequest,
) -> float:
    """Calculate timeout based on documentation complexity"""
    base_timeout = AsyncTimeouts.LLM_REQUEST * 1.5  # 90 seconds

    extra_time = 0

    # Title and outline complexity
    if request.content_outline:
        extra_time += len(request.content_outline) * 3  # 3 seconds per outline item

    # Detail level affects generation time
    detail_multipliers = {
        "basic": 0.8,
        "detailed": 1.0,
        "comprehensive": 1.5,
        "expert": 2.0,
    }
    multiplier = detail_multipliers.get(request.detail_level, 1.0)

    # Examples require more time
    if request.include_examples:
        extra_time += 20  # 20 seconds for example generation

    # Different doc types have different complexity
    doc_type_multipliers = {
        "api": 1.2,
        "user_guide": 1.0,
        "technical_spec": 1.4,
        "tutorial": 1.3,
        "reference": 1.1,
    }
    doc_multiplier = doc_type_multipliers.get(request.doc_type, 1.0)

    return min(
        (base_timeout + extra_time) * multiplier * doc_multiplier, 360.0
    )  # Cap at 6 minutes


# Enhanced helper functions with concurrent processing


async def _get_generation_sources(use_all: bool, excluded: List[str]) -> List[str]:
    """Determine sources for generation with validation"""
    try:
        all_sources = [
            "confluence_main",
            "gitlab_main",
            "jira_main",
            "local_files_bootstrap",
        ]

        if use_all:
            # Use all sources except excluded ones
            return [source for source in all_sources if source not in excluded]
        else:
            # Use only essential sources
            return ["confluence_main", "local_files_bootstrap"]

    except Exception as e:
        logger.error("Failed to get generation sources", error=str(e))
        return ["confluence_main"]


async def _gather_context_from_sources(
    query: str, sources: Optional[List[str]], context_type: str
) -> List[Dict[str, Any]]:
    """Gather context from all sources concurrently"""
    try:
        # Use default sources if none provided
        if sources is None:
            sources = await _get_generation_sources(use_all=True, excluded=[])

        # Create search tasks for concurrent execution
        search_tasks = [
            _search_in_source(source, query, context_type) for source in sources
        ]

        # Execute searches concurrently with timeout
        search_results = await safe_gather(
            *search_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.DATABASE_QUERY * 2,  # 20 seconds for all searches
            max_concurrency=4,  # Limit concurrent source searches
        )

        # Aggregate successful results
        context_data = []
        for source, result in zip(sources, search_results):
            if isinstance(result, Exception):
                logger.warning(f"⚠️ Search failed for source {source}: {result}")
                continue

            context_data.extend(result)

        # Limit context size and prioritize by relevance
        context_data = sorted(
            context_data, key=lambda x: x.get("relevance_score", 0), reverse=True
        )
        return context_data[:20]  # Top 20 most relevant documents

    except Exception as e:
        logger.error("Failed to gather context from sources", error=str(e))
        return []


async def _search_in_source(
    source: str, query: str, context_type: str
) -> List[Dict[str, Any]]:
    """Поиск в конкретном источнике"""
    try:
        # Здесь должен быть реальный поиск
        # Пока возвращаем заглушку
        return [
            {
                "source": source,
                "title": f"Relevant document from {source}",
                "content": f"Mock content for {query} from {source}",
                "relevance_score": 0.85,
                "doc_type": context_type,
            }
        ]

    except Exception as e:
        logger.error("Failed to search in source", source=source, error=str(e))
        return []


async def _analyze_architectural_patterns(
    context_data: List[Dict[str, Any]], architecture_type: str
) -> List[Dict[str, Any]]:
    """Анализ архитектурных паттернов"""
    try:
        # Анализ существующих архитектурных решений
        patterns = []

        for doc in context_data:
            if "architecture" in doc.get("content", "").lower():
                patterns.append(
                    {
                        "pattern_type": architecture_type,
                        "source_doc": doc["title"],
                        "description": doc["content"][:200] + "...",
                        "relevance": doc.get("relevance_score", 0.5),
                    }
                )

        return patterns[:5]  # Топ-5 паттернов

    except Exception as e:
        logger.error("Failed to analyze architectural patterns", error=str(e))
        return []


async def _analyze_existing_documentation(
    context_data: List[Dict[str, Any]], doc_type: str
) -> List[Dict[str, Any]]:
    """Анализ существующей документации"""
    try:
        existing_docs = []

        for doc in context_data:
            if doc_type.lower() in doc.get("content", "").lower():
                existing_docs.append(
                    {
                        "doc_type": doc_type,
                        "title": doc["title"],
                        "structure_elements": _extract_structure_elements(
                            doc["content"]
                        ),
                        "quality_score": doc.get("relevance_score", 0.5),
                    }
                )

        return existing_docs[:3]  # Топ-3 документа

    except Exception as e:
        logger.error("Failed to analyze existing documentation", error=str(e))
        return []


def _extract_structure_elements(content: str) -> List[str]:
    """Извлечение элементов структуры документа"""
    try:
        import re

        # Поиск заголовков
        headers = re.findall(r"^#+\s+(.+)$", content, re.MULTILINE)

        # Поиск списков
        lists = re.findall(r"^\s*[-\*\+]\s+(.+)$", content, re.MULTILINE)

        elements = headers + lists[:5]  # Ограничиваем количество

        return elements[:10]

    except Exception as e:
        logger.error("Failed to extract structure elements", error=str(e))
        return []


@router.get("/status/{task_id}", response_model=GenerationStatus)
async def get_generation_status(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    generation_service: GenerationServiceInterface = Depends(get_generation_service),
) -> GenerationStatus:
    """
    Получение статуса задачи генерации
    """
    try:
        status = await generation_service.get_task_status(task_id)

        if not status:
            raise HTTPException(status_code=404, detail="Task not found")

        return GenerationStatus(
            task_id=task_id,
            status=status.get("status", "unknown"),
            progress=status.get("progress", 0.0),
            started_at=status.get("started_at", ""),
            estimated_completion=status.get("estimated_completion"),
            error_message=status.get("error_message"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get generation status", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def get_available_templates(
    template_type: Optional[str] = None, current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Получение доступных шаблонов для генерации
    """
    try:
        templates = {
            "rfc": [
                {
                    "id": "standard",
                    "name": "Standard RFC",
                    "description": "Стандартный шаблон RFC с полной структурой",
                },
                {
                    "id": "technical",
                    "name": "Technical RFC",
                    "description": "Технический RFC для архитектурных решений",
                },
                {
                    "id": "process",
                    "name": "Process RFC",
                    "description": "RFC для описания процессов и процедур",
                },
            ],
            "architecture": [
                {
                    "id": "microservices",
                    "name": "Microservices Architecture",
                    "description": "Архитектура микросервисов",
                },
                {
                    "id": "monolith",
                    "name": "Monolithic Architecture",
                    "description": "Монолитная архитектура",
                },
                {
                    "id": "serverless",
                    "name": "Serverless Architecture",
                    "description": "Бессерверная архитектура",
                },
            ],
            "documentation": [
                {
                    "id": "api",
                    "name": "API Documentation",
                    "description": "Документация API",
                },
                {
                    "id": "user_guide",
                    "name": "User Guide",
                    "description": "Руководство пользователя",
                },
                {
                    "id": "technical_spec",
                    "name": "Technical Specification",
                    "description": "Техническая спецификация",
                },
            ],
        }

        if template_type:
            return {
                "template_type": template_type,
                "templates": templates.get(template_type, []),
            }

        return {"all_templates": templates, "total_types": len(templates)}

    except Exception as e:
        logger.error("Failed to get templates", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources/usage")
async def get_sources_usage_stats(
    days: int = 30, current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Статистика использования источников для генерации
    """
    try:
        # Проверка прав администратора
        if "admin" not in (current_user.roles or []):
            raise HTTPException(status_code=403, detail="Admin access required")

        stats = await _get_sources_usage_stats(days)

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get sources usage stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Вспомогательные функции


async def _get_sources_usage_stats(days: int) -> Dict[str, Any]:
    """Статистика использования источников"""
    try:
        # Здесь должен быть запрос к БД
        return {
            "period_days": days,
            "total_generations": 245,
            "sources_usage": {
                "confluence_main": {
                    "usage_count": 198,
                    "percentage": 80.8,
                    "avg_relevance": 0.82,
                },
                "gitlab_main": {
                    "usage_count": 156,
                    "percentage": 63.7,
                    "avg_relevance": 0.75,
                },
                "jira_main": {
                    "usage_count": 134,
                    "percentage": 54.7,
                    "avg_relevance": 0.68,
                },
                "local_files_bootstrap": {
                    "usage_count": 89,
                    "percentage": 36.3,
                    "avg_relevance": 0.91,
                },
            },
            "generation_types": {"rfc": 98, "architecture": 76, "documentation": 71},
        }

    except Exception as e:
        logger.error("Failed to get sources usage stats", error=str(e))
        return {}


@router.post("/rfc/enhanced", response_model=EnhancedGenerationResponse)
@async_retry(max_attempts=2, delay=2.0, exceptions=(HTTPException,))
async def generate_enhanced_rfc(
    request: EnhancedRFCRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    generation_service: GenerationServiceInterface = Depends(get_generation_service),
) -> EnhancedGenerationResponse:
    """
    🚀 Enhanced RFC Generation with Architecture Analysis and Mermaid Diagrams

    Features:
    - Automatic codebase architecture analysis
    - Mermaid diagram generation (architecture, dependencies, deployment)
    - Multi-source context gathering (Confluence, GitLab, Jira)
    - Professional RFC templates
    - Architecture recommendations
    - Project health assessment

    Perfect for:
    - System architecture changes
    - New feature implementation
    - Technical debt reduction
    - Performance improvements
    """
    start_time = time.time()

    try:
        user_id = str(current_user.id) if current_user else "anonymous"

        logger.info(
            f"🚀 Starting enhanced RFC generation: {request.task_description[:50]}..."
        )

        # Calculate comprehensive timeout
        timeout = _calculate_enhanced_rfc_timeout(request)

        # Execute enhanced RFC generation
        result = await with_timeout(
            _generate_enhanced_rfc_internal(request, user_id, generation_service),
            timeout,
            f"Enhanced RFC generation timed out (task: '{request.task_description[:50]}...', project: {bool(request.project_path)})",
            {
                "task_description_length": len(request.task_description),
                "has_project_path": bool(request.project_path),
                "include_diagrams": request.include_diagrams,
                "include_codebase_analysis": request.include_codebase_analysis,
                "template_type": request.template_type,
                "user_id": user_id,
            },
        )

        generation_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"✅ Enhanced RFC generation completed in {generation_time_ms:.1f}ms "
            f"(diagrams: {len(result.get('diagrams', {}))}, analysis: {bool(result.get('project_analysis'))})"
        )

        return EnhancedGenerationResponse(
            task_id=result.get("task_id", ""),
            status=result.get("status", "completed"),
            content=result.get("content", ""),
            metadata={
                **result.get("metadata", {}),
                "enhanced_features": {
                    "diagrams_generated": len(result.get("diagrams", {})),
                    "codebase_analyzed": bool(result.get("project_analysis")),
                    "template_type": request.template_type,
                    "timeout_used": timeout,
                    "async_optimized": True,
                },
            },
            sources_used=result.get("sources_used", []),
            generation_time_ms=generation_time_ms,
            tokens_used=result.get("tokens_used"),
            cost_estimate=result.get("cost_estimate"),
            rfc_data=result.get("rfc_data"),
            diagrams=(
                result.get("rfc_data", {}).get("diagrams", {})
                if result.get("rfc_data")
                else {}
            ),
            project_analysis=result.get("project_analysis"),
            architecture_recommendations=result.get("architecture_recommendations", []),
        )

    except AsyncTimeoutError as e:
        logger.error(f"❌ Enhanced RFC generation timed out: {e}")
        raise HTTPException(
            status_code=504,
            detail="Enhanced RFC generation timed out: Project too complex or analysis taking too long. Try reducing scope or disabling codebase analysis.",
        )
    except AsyncRetryError as e:
        logger.error(f"❌ Enhanced RFC generation failed after retries: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced RFC generation failed after retries: {str(e)}",
        )
    except Exception as e:
        logger.error("Enhanced RFC generation failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=500, detail=f"Enhanced RFC generation failed: {str(e)}"
        )


async def _generate_enhanced_rfc_internal(
    request: EnhancedRFCRequest,
    user_id: str,
    generation_service: GenerationServiceInterface,
) -> Dict[str, Any]:
    """Internal enhanced RFC generation with comprehensive analysis"""

    # Step 1: Concurrent data gathering
    tasks = [
        _get_generation_sources(
            use_all=request.use_all_sources, excluded=request.excluded_sources or []
        ),
        _gather_context_from_sources(
            query=request.task_description, sources=None, context_type="enhanced_rfc"
        ),
    ]

    # Step 2: Add project analysis if requested
    project_analysis_task = None
    if request.project_path and request.include_codebase_analysis:
        # Start project analysis concurrently
        project_analysis_task = _analyze_project_for_rfc(request.project_path)
        tasks.append(project_analysis_task)

    # Execute all data gathering tasks concurrently
    results = await safe_gather(
        *tasks,
        return_exceptions=True,
        timeout=AsyncTimeouts.DATABASE_QUERY
        * 5,  # 50 seconds for comprehensive data gathering
        max_concurrency=3,
    )

    # Process results
    sources_to_use = (
        results[0] if not isinstance(results[0], Exception) else ["confluence_main"]
    )
    context_data = results[1] if not isinstance(results[1], Exception) else []
    project_analysis = None
    if len(results) > 2 and not isinstance(results[2], Exception):
        project_analysis = results[2]

    # Step 3: Generate enhanced RFC with all data
    generation_params = {
        "task_description": request.task_description,
        "project_context": request.project_context,
        "technical_requirements": request.technical_requirements,
        "stakeholders": request.stakeholders,
        "priority": request.priority,
        "template_type": request.template_type,
        "context_data": context_data,
        "user_id": user_id,
        "project_path": (
            request.project_path if request.include_codebase_analysis else None
        ),
    }

    # Generate RFC with enhanced service
    result = await generation_service.generate_rfc(**generation_params)

    # Step 4: Add enhancement metadata
    result["sources_used"] = sources_to_use
    result["context_sources_count"] = len(context_data)

    # Extract architecture recommendations if project was analyzed
    if project_analysis and hasattr(project_analysis, "improvement_suggestions"):
        result["architecture_recommendations"] = (
            project_analysis.improvement_suggestions
        )

    return result


def _calculate_enhanced_rfc_timeout(request: EnhancedRFCRequest) -> float:
    """Calculate timeout for enhanced RFC generation"""
    base_timeout = AsyncTimeouts.LLM_REQUEST * 3  # 180 seconds for enhanced RFC

    extra_time = 0

    # Task complexity
    if len(request.task_description) > 1000:
        extra_time += (len(request.task_description) - 1000) / 150

    # Project analysis adds significant time
    if request.project_path and request.include_codebase_analysis:
        extra_time += 60  # 60 seconds for project analysis

    # Diagram generation
    if request.include_diagrams:
        extra_time += 30  # 30 seconds for diagram generation

    # Additional context processing
    if request.project_context and len(request.project_context) > 500:
        extra_time += len(request.project_context) / 400

    if request.technical_requirements and len(request.technical_requirements) > 500:
        extra_time += len(request.technical_requirements) / 400

    # Template type complexity
    template_multipliers = {
        "architecture": 1.5,  # Most complex
        "design": 1.2,
        "api": 1.3,
        "process": 1.0,  # Simplest
    }
    multiplier = template_multipliers.get(request.template_type, 1.0)

    # Priority affects timeout
    priority_multipliers = {"critical": 2.0, "high": 1.5, "medium": 1.0, "low": 0.8}
    priority_multiplier = priority_multipliers.get(request.priority, 1.0)

    total_timeout = (base_timeout + extra_time) * multiplier * priority_multiplier
    return min(total_timeout, 900.0)  # Cap at 15 minutes


async def _analyze_project_for_rfc(project_path: str) -> Optional[Any]:
    """Analyze project for RFC generation"""
    try:
        from domain.rfc_generation.rfc_analyzer import \
            analyze_project_architecture

        return await analyze_project_architecture(project_path)
    except Exception as e:
        logger.warning(f"Project analysis failed: {e}")
        return None


@router.post("/architecture/analyze", response_model=Dict[str, Any])
@async_retry(max_attempts=2, delay=1.0, exceptions=(HTTPException,))
async def analyze_project_architecture_endpoint(
    request: ProjectAnalysisRequest,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    🔍 Project Architecture Analysis

    Analyzes codebase architecture and provides:
    - Component identification and relationships
    - Technology stack detection
    - Architecture patterns recognition
    - Improvement recommendations
    - Mermaid diagrams generation
    - Health score assessment

    Use this before generating RFCs for data-driven decisions.
    """
    start_time = time.time()

    try:
        user_id = str(current_user.id) if current_user else "anonymous"

        logger.info(f"🔍 Starting project analysis: {request.project_path}")

        # Calculate timeout based on analysis depth
        timeout_multipliers = {
            "quick": 1.0,  # 30 seconds
            "standard": 2.0,  # 60 seconds
            "comprehensive": 4.0,  # 120 seconds
        }
        timeout = AsyncTimeouts.ANALYTICS_AGGREGATION * timeout_multipliers.get(
            request.analysis_depth, 2.0
        )

        # Execute analysis
        result = await with_timeout(
            _analyze_project_internal(request, user_id),
            timeout,
            f"Project analysis timed out (path: {request.project_path}, depth: {request.analysis_depth})",
            {
                "project_path": request.project_path,
                "analysis_depth": request.analysis_depth,
                "user_id": user_id,
            },
        )

        analysis_time_ms = (time.time() - start_time) * 1000

        logger.info(f"✅ Project analysis completed in {analysis_time_ms:.1f}ms")

        return {
            "status": "completed",
            "analysis_time_ms": analysis_time_ms,
            "project_path": request.project_path,
            "analysis_depth": request.analysis_depth,
            **result,
        }

    except AsyncTimeoutError as e:
        logger.error(f"❌ Project analysis timed out: {e}")
        raise HTTPException(
            status_code=504,
            detail=f"Project analysis timed out: Project too large or complex. Try 'quick' analysis or analyze smaller components.",
        )
    except Exception as e:
        logger.error(
            "Project analysis failed", error=str(e), project_path=request.project_path
        )
        raise HTTPException(
            status_code=500, detail=f"Project analysis failed: {str(e)}"
        )


async def _analyze_project_internal(
    request: ProjectAnalysisRequest, user_id: str
) -> Dict[str, Any]:
    """Internal project analysis implementation"""

    from domain.core.mermaid_diagram_generator import generate_all_diagrams
    from domain.rfc_generation.rfc_analyzer import (
        analyze_project_architecture, quick_health_check)

    try:
        # Step 1: Perform architecture analysis
        if request.analysis_depth == "quick":
            # Quick health check only
            health_data = await quick_health_check(request.project_path)
            return {
                "analysis_type": "quick_health_check",
                "health_data": health_data,
                "components_count": health_data.get("components_count", 0),
                "technologies": health_data.get("technologies", []),
                "recommendations": health_data.get("top_suggestions", []),
            }

        # Full analysis
        analysis = await analyze_project_architecture(request.project_path)

        # Step 2: Generate diagrams if comprehensive analysis
        diagrams = {}
        if request.analysis_depth == "comprehensive":
            try:
                diagrams = await generate_all_diagrams(analysis)
            except Exception as e:
                logger.warning(f"Diagram generation failed: {e}")

        # Step 3: Format response
        result = {
            "analysis_type": request.analysis_depth,
            "components": [
                {
                    "name": comp.name,
                    "service_type": comp.service_type,
                    "files_count": len(comp.files),
                    "technology_stack": comp.technology_stack,
                    "interfaces": comp.interfaces,
                }
                for comp in analysis.components
            ],
            "dependencies_graph": analysis.dependencies_graph,
            "technology_inventory": analysis.technology_inventory,
            "metrics": analysis.metrics,
            "improvement_suggestions": (
                analysis.improvement_suggestions if request.include_suggestions else []
            ),
            "diagrams": diagrams,
            "health_score": _calculate_health_score(analysis),
        }

        return result

    except Exception as e:
        logger.error(f"Internal project analysis failed: {e}")
        raise


def _calculate_health_score(analysis) -> int:
    """Calculate project health score"""
    base_score = 100

    # Monolith penalty
    if len(analysis.components) == 1:
        base_score -= 20

    # Large codebase penalty
    if analysis.metrics.get("total_files", 0) > 100:
        base_score -= 10

    # No tech detected penalty
    if not analysis.technology_inventory:
        base_score -= 30

    # Quality issues penalty
    if hasattr(analysis, "quality_issues") and analysis.quality_issues:
        critical_issues = [
            i for i in analysis.quality_issues if i.severity == "critical"
        ]
        base_score -= len(critical_issues) * 10

    return max(0, min(100, base_score))


@router.post("/rfc/from-analysis", response_model=EnhancedGenerationResponse)
@async_retry(max_attempts=2, delay=2.0, exceptions=(HTTPException,))
async def generate_rfc_from_analysis(
    analysis_data: Dict[str, Any],
    rfc_request: EnhancedRFCRequest,
    current_user: dict = Depends(get_current_user),
    generation_service: GenerationServiceInterface = Depends(get_generation_service),
) -> EnhancedGenerationResponse:
    """
    📊 Generate RFC from Pre-computed Analysis

    Uses existing project analysis data to generate RFC without re-analyzing.
    Perfect for iterative RFC creation based on the same codebase analysis.

    Workflow:
    1. First call /architecture/analyze
    2. Then call this endpoint with analysis results
    3. Get RFC with pre-computed diagrams and recommendations
    """
    start_time = time.time()

    try:
        user_id = str(current_user.id) if current_user else "anonymous"

        logger.info(
            f"📊 Generating RFC from pre-computed analysis: {rfc_request.task_description[:50]}..."
        )

        # Use the analysis data directly
        generation_params = {
            "task_description": rfc_request.task_description,
            "project_context": rfc_request.project_context,
            "technical_requirements": rfc_request.technical_requirements,
            "stakeholders": rfc_request.stakeholders,
            "priority": rfc_request.priority,
            "template_type": rfc_request.template_type,
            "context_data": [],  # Could be enhanced with source data
            "user_id": user_id,
            "project_path": None,  # Don't re-analyze
        }

        # Generate RFC
        result = await generation_service.generate_rfc(**generation_params)

        # Enhance with pre-computed analysis
        result["project_analysis"] = analysis_data
        result["architecture_recommendations"] = analysis_data.get(
            "improvement_suggestions", []
        )

        # Use pre-computed diagrams
        if "diagrams" in analysis_data:
            if "rfc_data" not in result:
                result["rfc_data"] = {}
            result["rfc_data"]["diagrams"] = analysis_data["diagrams"]

        generation_time_ms = (time.time() - start_time) * 1000

        logger.info(f"✅ RFC from analysis completed in {generation_time_ms:.1f}ms")

        return EnhancedGenerationResponse(
            task_id=result.get("task_id", ""),
            status=result.get("status", "completed"),
            content=result.get("content", ""),
            metadata={
                **result.get("metadata", {}),
                "generated_from_analysis": True,
                "analysis_reused": True,
            },
            sources_used=result.get("sources_used", []),
            generation_time_ms=generation_time_ms,
            tokens_used=result.get("tokens_used"),
            cost_estimate=result.get("cost_estimate"),
            rfc_data=result.get("rfc_data"),
            diagrams=(
                result.get("rfc_data", {}).get("diagrams", {})
                if result.get("rfc_data")
                else {}
            ),
            project_analysis=result.get("project_analysis"),
            architecture_recommendations=result.get("architecture_recommendations", []),
        )

    except Exception as e:
        logger.error("RFC from analysis generation failed", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"RFC from analysis failed: {str(e)}"
        )
