import time
from typing import Dict, Any

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.config import settings

router = APIRouter()

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: float
    version: str
    uptime: float
    environment: str
    checks: Dict[str, Any] = {}

# Track application start time for uptime calculation
_start_time = time.time()

@router.get(
    '/health', 
    status_code=status.HTTP_200_OK,
    response_model=HealthResponse,
    summary="Health Check V1",
    description="Returns the current health status of the service (API v1)"
)
async def health() -> HealthResponse:
    """
    Perform health checks and return service status.
    
    Returns:
        HealthResponse: Current service health information
    """
    current_time = time.time()
    uptime = current_time - _start_time
    
    # Extended health checks for v1
    checks = {
        "api": "healthy",
        "database": "not_configured",
        "vectorstore": "not_configured", 
        "llm": "not_configured",
        "memory": "healthy"
    }
    
    return HealthResponse(
        status="healthy",
        timestamp=current_time,
        version=settings.version,
        uptime=uptime,
        environment=settings.environment,
        checks=checks
    )

@router.get("/health", summary="Health Check V1", description="Проверяет работоспособность API v1")
def health_check_v1():
    return {"status": "ok", "api_version": "v1", "app_version": settings.version} 