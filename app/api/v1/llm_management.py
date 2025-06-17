"""
LLM Management API endpoints
Enhanced with new LLM service integration
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from app.security.auth import get_current_user, require_admin
from llm.llm_service import get_llm_service, initialize_llm_service
from llm.llm_router import RoutingStrategy
from app.monitoring.metrics import record_semantic_search_metrics
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["LLM Management"])

# Request/Response Models
class TextGenerationRequest(BaseModel):
    """Request for text generation."""
    prompt: str = Field(..., description="Input prompt", min_length=1, max_length=8000)
    system_prompt: Optional[str] = Field(None, description="System prompt", max_length=2000)
    max_tokens: int = Field(default=2000, description="Maximum tokens to generate", ge=1, le=8000)
    temperature: float = Field(default=0.7, description="Temperature (0.0-1.0)", ge=0.0, le=1.0)
    top_p: float = Field(default=0.9, description="Top-p sampling", ge=0.0, le=1.0)
    stop_sequences: Optional[List[str]] = Field(None, description="Stop sequences")

class RFCGenerationRequest(BaseModel):
    """Request for RFC generation."""
    task_description: str = Field(..., description="Task description", min_length=10, max_length=4000)
    project_context: Optional[str] = Field(None, description="Project context", max_length=2000)
    technical_requirements: Optional[str] = Field(None, description="Technical requirements", max_length=2000)

class DocumentationRequest(BaseModel):
    """Request for code documentation."""
    code: str = Field(..., description="Code to document", min_length=1, max_length=10000)
    language: str = Field(default="python", description="Programming language")
    doc_type: str = Field(default="comprehensive", description="Documentation type")

class QuestionAnswerRequest(BaseModel):
    """Request for question answering."""
    question: str = Field(..., description="Question to answer", min_length=1, max_length=2000)
    context: Optional[str] = Field(None, description="Context information", max_length=8000)
    max_tokens: int = Field(default=1000, description="Maximum response tokens", ge=50, le=4000)

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
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
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
            "status": "initializing"
        }
        
    except Exception as e:
        logger.error(f"LLM service initialization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")

@router.get("/health", response_model=LLMHealthResponse)
async def get_llm_health():
    """Get health status of all LLM providers."""
    try:
        llm_service = get_llm_service()
        health_data = await llm_service.health_check()
        
        return LLMHealthResponse(**health_data)
        
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/stats", response_model=LLMStatsResponse)
async def get_llm_stats(current_user = Depends(get_current_user)):
    """Get comprehensive LLM service statistics."""
    try:
        llm_service = get_llm_service()
        stats_data = await llm_service.get_service_stats()
        
        return LLMStatsResponse(**stats_data)
        
    except Exception as e:
        logger.error(f"LLM stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

@router.post("/generate", response_model=LLMResponse)
async def generate_text(
    request: TextGenerationRequest,
    current_user = Depends(get_current_user)
):
    """Generate text using the best available LLM provider."""
    start_time = time.time()
    
    try:
        llm_service = get_llm_service()
        
        # Generate text
        content = await llm_service.generate_text(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            stop_sequences=request.stop_sequences
        )
        
        # Get service stats for response metadata
        stats = await llm_service.get_service_stats()
        router_stats = stats.get("router_stats", {})
        
        # Estimate metrics (real metrics would come from the actual response)
        estimated_tokens = len(content) // 4
        estimated_cost = 0.01  # Placeholder
        
        response = LLMResponse(
            content=content,
            provider="auto_selected",
            model="auto_selected",
            tokens_used=estimated_tokens,
            cost_usd=estimated_cost,
            response_time=time.time() - start_time,
            metadata={
                "routing_strategy": router_stats.get("routing_strategy", "unknown"),
                "providers_available": stats.get("providers_available", 0)
            }
        )
        
        # Record metrics
        record_semantic_search_metrics(
            endpoint="/llm/generate",
            duration=response.response_time,
            results_count=1,
            relevance_score=1.0,
            status="success",
            query_type="text_generation"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Text generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@router.post("/generate/rfc", response_model=LLMResponse)
async def generate_rfc(
    request: RFCGenerationRequest,
    current_user = Depends(get_current_user)
):
    """Generate an RFC document."""
    start_time = time.time()
    
    try:
        llm_service = get_llm_service()
        
        # Generate RFC
        content = await llm_service.generate_rfc(
            task_description=request.task_description,
            project_context=request.project_context,
            technical_requirements=request.technical_requirements
        )
        
        response = LLMResponse(
            content=content,
            provider="auto_selected",
            model="auto_selected",
            tokens_used=len(content) // 4,
            cost_usd=0.05,  # RFC generation typically costs more
            response_time=time.time() - start_time,
            metadata={"generation_type": "rfc"}
        )
        
        # Record metrics
        record_semantic_search_metrics(
            endpoint="/llm/generate/rfc",
            duration=response.response_time,
            results_count=1,
            relevance_score=1.0,
            status="success",
            query_type="rfc_generation"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"RFC generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"RFC generation failed: {str(e)}")

@router.post("/generate/documentation", response_model=LLMResponse)
async def generate_documentation(
    request: DocumentationRequest,
    current_user = Depends(get_current_user)
):
    """Generate code documentation."""
    start_time = time.time()
    
    try:
        llm_service = get_llm_service()
        
        # Generate documentation
        content = await llm_service.generate_documentation(
            code=request.code,
            language=request.language,
            doc_type=request.doc_type
        )
        
        response = LLMResponse(
            content=content,
            provider="auto_selected",
            model="auto_selected",
            tokens_used=len(content) // 4,
            cost_usd=0.03,
            response_time=time.time() - start_time,
            metadata={
                "generation_type": "documentation",
                "language": request.language,
                "doc_type": request.doc_type
            }
        )
        
        # Record metrics
        record_semantic_search_metrics(
            endpoint="/llm/generate/documentation",
            duration=response.response_time,
            results_count=1,
            relevance_score=1.0,
            status="success",
            query_type="documentation_generation"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Documentation generation failed: {str(e)}")

@router.post("/answer", response_model=LLMResponse)
async def answer_question(
    request: QuestionAnswerRequest,
    current_user = Depends(get_current_user)
):
    """Answer a question using available context."""
    start_time = time.time()
    
    try:
        llm_service = get_llm_service()
        
        # Answer question
        content = await llm_service.answer_question(
            question=request.question,
            context=request.context,
            max_tokens=request.max_tokens
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
                "has_context": request.context is not None
            }
        )
        
        # Record metrics
        record_semantic_search_metrics(
            endpoint="/llm/answer",
            duration=response.response_time,
            results_count=1,
            relevance_score=1.0,
            status="success",
            query_type="question_answer"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Question answering failed: {e}")
        raise HTTPException(status_code=500, detail=f"Question answering failed: {str(e)}")

@router.get("/providers")
async def list_providers(current_user = Depends(get_current_user)):
    """List all available LLM providers and their status."""
    try:
        llm_service = get_llm_service()
        stats = await llm_service.get_service_stats()
        
        return {
            "providers": stats.get("router_stats", {}).get("providers", {}),
            "routing_strategy": stats.get("router_stats", {}).get("routing_strategy", "unknown"),
            "total_providers": stats.get("providers_available", 0)
        }
        
    except Exception as e:
        logger.error(f"Provider listing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Provider listing failed: {str(e)}")

@router.post("/providers/health-check")
async def check_all_providers(
    current_user = Depends(get_current_user)
):
    """Run health checks on all providers."""
    if not require_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        llm_service = get_llm_service()
        health_results = await llm_service.health_check()
        
        return {
            "success": True,
            "health_check_results": health_results,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Provider health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Batch operations

@router.post("/batch/generate")
async def batch_generate_text(
    requests: List[TextGenerationRequest],
    current_user = Depends(get_current_user)
):
    """Generate text for multiple prompts in batch."""
    if len(requests) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 requests per batch")
    
    try:
        llm_service = get_llm_service()
        results = []
        
        for i, req in enumerate(requests):
            try:
                content = await llm_service.generate_text(
                    prompt=req.prompt,
                    system_prompt=req.system_prompt,
                    max_tokens=req.max_tokens,
                    temperature=req.temperature,
                    top_p=req.top_p,
                    stop_sequences=req.stop_sequences
                )
                
                results.append({
                    "index": i,
                    "success": True,
                    "content": content,
                    "tokens_used": len(content) // 4,
                    "error": None
                })
                
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "content": None,
                    "tokens_used": 0,
                    "error": str(e)
                })
        
        successful_count = sum(1 for r in results if r["success"])
        
        return {
            "success": True,
            "total_requests": len(requests),
            "successful": successful_count,
            "failed": len(requests) - successful_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch generation failed: {str(e)}") 