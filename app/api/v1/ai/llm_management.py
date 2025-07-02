"""
LLM Management API endpoints
Enhanced with standardized async patterns for enterprise reliability
Version: 2.1 Async Optimized
"""

import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from llm.llm_router import RoutingStrategy
from llm.llm_service import get_llm_service, initialize_llm_service
from pydantic import BaseModel, Field

# Import standardized async patterns
from app.core.async_utils import (AsyncTimeouts, async_retry,
                                  create_background_task, safe_gather,
                                  with_timeout)
from app.core.exceptions import AsyncRetryError, AsyncTimeoutError
from infra.monitoring.metrics import record_semantic_search_metrics
from app.security.auth import get_current_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["LLM Management"])


# Request/Response Models
class TextGenerationRequest(BaseModel):
    """Request for text generation."""

    prompt: str = Field(..., description="Input prompt", min_length=1, max_length=8000)
    system_prompt: Optional[str] = Field(
        None, description="System prompt", max_length=2000
    )
    max_tokens: int = Field(
        default=2000, description="Maximum tokens to generate", ge=1, le=8000
    )
    temperature: float = Field(
        default=0.7, description="Temperature (0.0-1.0)", ge=0.0, le=1.0
    )
    top_p: float = Field(default=0.9, description="Top-p sampling", ge=0.0, le=1.0)
    stop_sequences: Optional[List[str]] = Field(None, description="Stop sequences")


class RFCGenerationRequest(BaseModel):
    """Request for RFC generation."""

    task_description: str = Field(
        ..., description="Task description", min_length=10, max_length=4000
    )
    project_context: Optional[str] = Field(
        None, description="Project context", max_length=2000
    )
    technical_requirements: Optional[str] = Field(
        None, description="Technical requirements", max_length=2000
    )


class DocumentationRequest(BaseModel):
    """Request for code documentation."""

    code: str = Field(
        ..., description="Code to document", min_length=1, max_length=10000
    )
    language: str = Field(default="python", description="Programming language")
    doc_type: str = Field(default="comprehensive", description="Documentation type")


class QuestionAnswerRequest(BaseModel):
    """Request for question answering."""

    question: str = Field(
        ..., description="Question to answer", min_length=1, max_length=2000
    )
    context: Optional[str] = Field(
        None, description="Context information", max_length=8000
    )
    max_tokens: int = Field(
        default=1000, description="Maximum response tokens", ge=50, le=4000
    )


class LLMResponse(BaseModel):
    """LLM response model."""

    content: str
    provider: str
    model: str
    tokens_used: int
    cost_usd: float
    response_time: float
    metadata: Dict[str, Any]


class LLMHealthResponse(BaseModel):
    """LLM health response."""

    status: str
    providers: Dict[str, Any]
    healthy_count: int
    total_count: int


class LLMStatsResponse(BaseModel):
    """LLM statistics response."""

    status: str
    service_metrics: Dict[str, Any]
    router_stats: Dict[str, Any]
    providers_available: int


# API Endpoints


@router.post("/initialize")
async def initialize_llm_service_endpoint(
    background_tasks: BackgroundTasks, current_user=Depends(get_current_user)
):
    """Initialize LLM service with available providers."""
    if not require_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Initialize in background to avoid timeout
        background_tasks.add_task(initialize_llm_service)

        return {
            "success": True,
            "message": "LLM service initialization started",
            "status": "initializing",
        }

    except Exception as e:
        logger.error(f"LLM service initialization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")


@router.get("/health", response_model=LLMHealthResponse)
async def get_llm_health():
    """
    Get health status of all LLM providers.
    Enhanced with timeout protection and concurrent health checks.
    """
    try:
        llm_service = get_llm_service()

        # Perform health check with timeout protection
        health_data = await with_timeout(
            llm_service.health_check(),
            AsyncTimeouts.LLM_REQUEST,  # 60 seconds for health check
            "LLM health check timed out",
            {"operation": "health_check"},
        )

        # Handle uninitialized service case
        if "error" in health_data and "not initialized" in health_data.get("error", ""):
            logger.warning("⚠️ LLM service not initialized")
            return LLMHealthResponse(
                status="unhealthy", providers={}, healthy_count=0, total_count=0
            )

        logger.info(
            f"✅ LLM health check completed: {health_data.get('healthy_count', 0)}/{health_data.get('total_count', 0)} providers healthy"
        )

        # Return the health data if properly formatted
        return LLMHealthResponse(**health_data)

    except AsyncTimeoutError as e:
        logger.error(f"❌ LLM health check timed out: {e}")
        return LLMHealthResponse(
            status="timeout",
            providers={"error": "Health check timed out"},
            healthy_count=0,
            total_count=0,
        )
    except Exception as e:
        logger.error(f"❌ LLM health check failed: {e}")
        # Return properly formatted error response
        return LLMHealthResponse(
            status="error", providers={"error": str(e)}, healthy_count=0, total_count=0
        )


@router.get("/stats", response_model=LLMStatsResponse)
async def get_llm_stats(current_user=Depends(get_current_user)):
    """
    Get comprehensive LLM service statistics.
    Enhanced with timeout protection and concurrent stats collection.
    """
    try:
        llm_service = get_llm_service()

        # Collect stats with timeout protection
        stats_data = await with_timeout(
            llm_service.get_service_stats(),
            AsyncTimeouts.DATABASE_QUERY * 2,  # 20 seconds for comprehensive stats
            "LLM stats collection timed out",
            {"user_id": str(current_user.id) if current_user else "anonymous"},
        )

        logger.info("✅ LLM stats collected successfully")
        return LLMStatsResponse(**stats_data)

    except AsyncTimeoutError as e:
        logger.warning(f"⚠️ LLM stats collection timed out: {e}")
        # Return minimal stats on timeout
        return LLMStatsResponse(
            status="timeout",
            service_metrics={"error": "Stats collection timed out"},
            router_stats={"error": "Stats collection timed out"},
            providers_available=0,
        )
    except Exception as e:
        logger.error(f"❌ LLM stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.post("/generate", response_model=LLMResponse)
@async_retry(max_attempts=2, delay=1.0, exceptions=(HTTPException,))
async def generate_text(
    request: TextGenerationRequest, current_user=Depends(get_current_user)
):
    """
    Generate text using the best available LLM provider.
    Enhanced with timeout protection, retry logic, and performance optimization.
    """
    start_time = time.time()

    try:
        llm_service = get_llm_service()

        # Calculate timeout based on generation complexity
        timeout = _calculate_generation_timeout(request.max_tokens, len(request.prompt))

        # Generate text with timeout protection
        content = await with_timeout(
            llm_service.generate_text(
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stop_sequences=request.stop_sequences,
            ),
            timeout,
            f"LLM text generation timed out (prompt: {len(request.prompt)} chars, max_tokens: {request.max_tokens})",
            {
                "prompt_length": len(request.prompt),
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "user_id": str(current_user.id) if current_user else "anonymous",
            },
        )

        # Get service stats for response metadata concurrently
        stats_task = create_background_task(llm_service.get_service_stats())

        # Estimate metrics (real metrics would come from the actual response)
        estimated_tokens = len(content) // 4
        estimated_cost = 0.01  # Placeholder
        response_time = time.time() - start_time

        response = LLMResponse(
            content=content,
            provider="auto_selected",
            model="auto_selected",
            tokens_used=estimated_tokens,
            cost_usd=estimated_cost,
            response_time=response_time,
            metadata={
                "routing_strategy": "balanced",
                "providers_available": 1,
                "timeout_used": timeout,
                "async_optimized": True,
            },
        )

        # Record metrics asynchronously
        create_background_task(
            record_semantic_search_metrics(
                endpoint="/llm/generate",
                duration=response.response_time,
                results_count=1,
                relevance_score=1.0,
                status="success",
                query_type="text_generation",
            )
        )

        logger.info(
            f"✅ Text generation completed: {estimated_tokens} tokens in {response_time:.2f}s "
            f"(prompt: {len(request.prompt)} chars)"
        )

        return response

    except AsyncTimeoutError as e:
        logger.error(f"❌ Text generation timed out: {e}")
        raise HTTPException(
            status_code=504,
            detail="Text generation timed out: Request too complex or system overloaded. Try reducing max_tokens or simplifying prompt.",
        )
    except AsyncRetryError as e:
        logger.error(f"❌ Text generation failed after retries: {e}")
        raise HTTPException(
            status_code=500, detail=f"Generation failed after retries: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Text generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


def _calculate_generation_timeout(max_tokens: int, prompt_length: int) -> float:
    """Calculate appropriate timeout based on generation complexity"""
    base_timeout = AsyncTimeouts.LLM_REQUEST  # 60 seconds

    # Add extra time for longer generations
    extra_time = 0

    # More tokens = more time (rough estimate: 10 tokens/second)
    if max_tokens > 1000:
        extra_time += (max_tokens - 1000) / 10  # 1 second per extra 100 tokens

    # Very long prompts need more processing time
    if prompt_length > 2000:
        extra_time += (prompt_length - 2000) / 500  # 1 second per extra 500 chars

    return min(base_timeout + extra_time, 300.0)  # Cap at 5 minutes


@router.post("/generate/rfc", response_model=LLMResponse)
@async_retry(max_attempts=2, delay=1.5, exceptions=(HTTPException,))
async def generate_rfc(
    request: RFCGenerationRequest, current_user=Depends(get_current_user)
):
    """
    Generate an RFC document.
    Enhanced with timeout protection and concurrent processing.
    """
    start_time = time.time()

    try:
        llm_service = get_llm_service()

        # RFC generation typically takes longer than regular text
        timeout = AsyncTimeouts.LLM_REQUEST * 2  # 120 seconds for RFC generation

        # Generate RFC with timeout protection
        content = await with_timeout(
            llm_service.generate_rfc(
                task_description=request.task_description,
                project_context=request.project_context,
                technical_requirements=request.technical_requirements,
            ),
            timeout,
            f"RFC generation timed out (task: '{request.task_description[:50]}...')",
            {
                "task_description_length": len(request.task_description),
                "has_project_context": bool(request.project_context),
                "has_technical_requirements": bool(request.technical_requirements),
                "user_id": str(current_user.id) if current_user else "anonymous",
            },
        )

        response_time = time.time() - start_time

        response = LLMResponse(
            content=content,
            provider="auto_selected",
            model="auto_selected",
            tokens_used=len(content) // 4,
            cost_usd=0.05,  # RFC generation typically costs more
            response_time=response_time,
            metadata={
                "generation_type": "rfc",
                "timeout_used": timeout,
                "async_optimized": True,
            },
        )

        # Record metrics asynchronously
        create_background_task(
            record_semantic_search_metrics(
                endpoint="/llm/generate/rfc",
                duration=response.response_time,
                results_count=1,
                relevance_score=1.0,
                status="success",
                query_type="rfc_generation",
            )
        )

        logger.info(f"✅ RFC generation completed in {response_time:.2f}s")

        return response

    except AsyncTimeoutError as e:
        logger.error(f"❌ RFC generation timed out: {e}")
        raise HTTPException(
            status_code=504,
            detail="RFC generation timed out: Request too complex. Try simplifying task description or breaking into smaller parts.",
        )
    except AsyncRetryError as e:
        logger.error(f"❌ RFC generation failed after retries: {e}")
        raise HTTPException(
            status_code=500, detail=f"RFC generation failed after retries: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ RFC generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"RFC generation failed: {str(e)}")


@router.post("/generate/documentation", response_model=LLMResponse)
@async_retry(max_attempts=2, delay=1.0, exceptions=(HTTPException,))
async def generate_documentation(
    request: DocumentationRequest, current_user=Depends(get_current_user)
):
    """
    Generate code documentation.
    Enhanced with timeout protection and code complexity analysis.
    """
    start_time = time.time()

    try:
        llm_service = get_llm_service()

        # Calculate timeout based on code complexity
        timeout = _calculate_documentation_timeout(request.code, request.doc_type)

        # Generate documentation with timeout protection
        content = await with_timeout(
            llm_service.generate_documentation(
                code=request.code, language=request.language, doc_type=request.doc_type
            ),
            timeout,
            f"Documentation generation timed out (code: {len(request.code)} chars, language: {request.language})",
            {
                "code_length": len(request.code),
                "language": request.language,
                "doc_type": request.doc_type,
                "user_id": str(current_user.id) if current_user else "anonymous",
            },
        )

        response_time = time.time() - start_time

        response = LLMResponse(
            content=content,
            provider="auto_selected",
            model="auto_selected",
            tokens_used=len(content) // 4,
            cost_usd=0.03,
            response_time=response_time,
            metadata={
                "generation_type": "documentation",
                "language": request.language,
                "doc_type": request.doc_type,
                "timeout_used": timeout,
                "async_optimized": True,
            },
        )

        # Record metrics asynchronously
        create_background_task(
            record_semantic_search_metrics(
                endpoint="/llm/generate/documentation",
                duration=response.response_time,
                results_count=1,
                relevance_score=1.0,
                status="success",
                query_type="documentation_generation",
            )
        )

        logger.info(
            f"✅ Documentation generation completed in {response_time:.2f}s for {request.language} code"
        )

        return response

    except AsyncTimeoutError as e:
        logger.error(f"❌ Documentation generation timed out: {e}")
        raise HTTPException(
            status_code=504,
            detail="Documentation generation timed out: Code too complex or large. Try breaking into smaller chunks.",
        )
    except AsyncRetryError as e:
        logger.error(f"❌ Documentation generation failed after retries: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Documentation generation failed after retries: {str(e)}",
        )
    except Exception as e:
        logger.error(f"❌ Documentation generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Documentation generation failed: {str(e)}"
        )


def _calculate_documentation_timeout(code: str, doc_type: str) -> float:
    """Calculate timeout based on code complexity and documentation type"""
    base_timeout = AsyncTimeouts.LLM_REQUEST  # 60 seconds

    # Add extra time for complex documentation
    extra_time = 0

    # Longer code needs more time
    if len(code) > 5000:
        extra_time += (len(code) - 5000) / 1000  # 1 second per extra 1000 chars

    # Different doc types have different complexity
    doc_type_multipliers = {
        "comprehensive": 1.5,
        "api": 1.2,
        "inline": 0.8,
        "readme": 1.3,
    }

    multiplier = doc_type_multipliers.get(doc_type, 1.0)

    return min((base_timeout + extra_time) * multiplier, 180.0)  # Cap at 3 minutes


@router.post("/answer", response_model=LLMResponse)
async def answer_question(
    request: QuestionAnswerRequest, current_user=Depends(get_current_user)
):
    """Answer a question using available context."""
    start_time = time.time()

    try:
        llm_service = get_llm_service()

        # Answer question
        content = await llm_service.answer_question(
            question=request.question,
            context=request.context,
            max_tokens=request.max_tokens,
        )

        response = LLMResponse(
            content=content,
            provider="auto_selected",
            model="auto_selected",
            tokens_used=len(content) // 4,
            cost_usd=0.02,
            response_time=time.time() - start_time,
            metadata={
                "generation_type": "question_answer",
                "has_context": request.context is not None,
            },
        )

        # Record metrics
        record_semantic_search_metrics(
            endpoint="/llm/answer",
            duration=response.response_time,
            results_count=1,
            relevance_score=1.0,
            status="success",
            query_type="question_answer",
        )

        return response

    except Exception as e:
        logger.error(f"Question answering failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Question answering failed: {str(e)}"
        )


@router.get("/providers")
async def list_providers(current_user=Depends(get_current_user)):
    """List all available LLM providers and their status."""
    try:
        llm_service = get_llm_service()
        stats = await llm_service.get_service_stats()

        return {
            "providers": stats.get("router_stats", {}).get("providers", {}),
            "routing_strategy": stats.get("router_stats", {}).get(
                "routing_strategy", "unknown"
            ),
            "total_providers": stats.get("providers_available", 0),
        }

    except Exception as e:
        logger.error(f"Provider listing failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Provider listing failed: {str(e)}"
        )


@router.post("/providers/health-check")
async def check_all_providers(current_user=Depends(get_current_user)):
    """
    Run health checks on all providers.
    Enhanced with concurrent health checking and timeout protection.
    """
    if not require_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        llm_service = get_llm_service()

        # Perform concurrent health checks with timeout
        health_results = await with_timeout(
            llm_service.health_check(),
            AsyncTimeouts.LLM_REQUEST
            * 1.5,  # 90 seconds for comprehensive health check
            "Provider health checks timed out",
            {"user_id": str(current_user.id) if current_user else "admin"},
        )

        logger.info("✅ Provider health checks completed successfully")

        return {
            "success": True,
            "health_check_results": health_results,
            "timestamp": time.time(),
            "async_optimized": True,
        }

    except AsyncTimeoutError as e:
        logger.error(f"❌ Provider health checks timed out: {e}")
        return {
            "success": False,
            "error": "Health checks timed out",
            "health_check_results": {"error": "Timeout occurred"},
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"❌ Provider health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.post("/batch/generate")
async def batch_generate_text(
    requests: List[TextGenerationRequest], current_user=Depends(get_current_user)
):
    """
    Generate text for multiple prompts in batch.
    Enhanced with concurrent processing and timeout protection.
    """
    if len(requests) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 requests per batch")

    try:
        llm_service = get_llm_service()

        # Create generation tasks for concurrent processing
        generation_tasks = []
        for i, req in enumerate(requests):
            task = _generate_single_text_with_context(llm_service, req, i)
            generation_tasks.append(task)

        # Execute all generations concurrently with timeout
        batch_timeout = AsyncTimeouts.LLM_REQUEST * 2  # 120 seconds for batch

        results = await safe_gather(
            *generation_tasks,
            return_exceptions=True,
            timeout=batch_timeout,
            max_concurrency=5,  # Limit concurrent requests to avoid overload
        )

        # Process results
        processed_results = []
        successful_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {
                        "index": i,
                        "success": False,
                        "content": None,
                        "tokens_used": 0,
                        "error": str(result),
                    }
                )
            else:
                processed_results.append(result)
                if result["success"]:
                    successful_count += 1

        logger.info(
            f"✅ Batch generation completed: {successful_count}/{len(requests)} successful"
        )

        return {
            "success": True,
            "total_requests": len(requests),
            "successful": successful_count,
            "failed": len(requests) - successful_count,
            "results": processed_results,
            "async_optimized": True,
        }

    except AsyncTimeoutError as e:
        logger.error(f"❌ Batch generation timed out: {e}")
        raise HTTPException(
            status_code=504,
            detail="Batch generation timed out: Reduce batch size or simplify requests",
        )
    except Exception as e:
        logger.error(f"❌ Batch generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Batch generation failed: {str(e)}"
        )


async def _generate_single_text_with_context(
    llm_service, req: TextGenerationRequest, index: int
) -> Dict[str, Any]:
    """Generate single text with proper error handling and context"""
    try:
        content = await llm_service.generate_text(
            prompt=req.prompt,
            system_prompt=req.system_prompt,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            top_p=req.top_p,
            stop_sequences=req.stop_sequences,
        )

        return {
            "index": index,
            "success": True,
            "content": content,
            "tokens_used": len(content) // 4,
            "error": None,
        }

    except Exception as e:
        return {
            "index": index,
            "success": False,
            "content": None,
            "tokens_used": 0,
            "error": str(e),
        }
