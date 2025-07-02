import asyncio
import time
from typing import Any, Dict

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


class SmokeHealthResponse(BaseModel):
    """Smoke test health response model."""

    status: str
    timestamp: float


# Track application start time for uptime calculation
_start_time = time.time()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns the current health status of the service",
)
async def health() -> HealthResponse:
    """
    Perform health checks and return service status.

    Returns:
        HealthResponse: Current service health information
    """
    current_time = time.time()
    uptime = current_time - _start_time

    # Basic health checks
    checks = {
        "api": "healthy",
        "memory": "healthy",  # Could add actual memory usage check
        "database": "not_configured",  # Placeholder for future DB checks
    }

    return HealthResponse(
        status="healthy",
        timestamp=current_time,
        version=settings.version,
        uptime=uptime,
        environment=settings.environment,
        checks=checks,
    )


@router.get(
    "/api/health",
    status_code=status.HTTP_200_OK,
    response_model=SmokeHealthResponse,
    summary="API Health Check (Frontend Compatible)",
    description="Simple health check for frontend compatibility on /api/health path",
)
async def api_health() -> SmokeHealthResponse:
    """
    Simple health check for frontend compatibility.
    
    This endpoint provides the same basic health check but on /api/health path
    to match frontend expectations.

    Returns:
        SmokeHealthResponse: Basic health status
    """
    return SmokeHealthResponse(status="healthy", timestamp=time.time())


@router.get(
    "/health_smoke",
    status_code=status.HTTP_200_OK,
    response_model=SmokeHealthResponse,
    summary="Smoke Health Check",
    description="Simple health check for smoke testing and monitoring",
)
async def health_smoke() -> SmokeHealthResponse:
    """
    Simple smoke test health check.

    Returns:
        SmokeHealthResponse: Basic health status
    """
    return SmokeHealthResponse(status="healthy", timestamp=time.time())
