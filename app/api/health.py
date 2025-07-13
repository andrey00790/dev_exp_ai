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
    """Simple health check response model for smoke testing."""

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


# Create endpoints needed for load testing
@router.get(
    "/api/v1/health",
    status_code=status.HTTP_200_OK,
    response_model=SmokeHealthResponse,
    summary="API V1 Health Check",
    description="Health check for API v1 compatibility",
)
async def api_v1_health() -> SmokeHealthResponse:
    """API v1 health check."""
    return SmokeHealthResponse(status="healthy", timestamp=time.time())


@router.get(
    "/api/v1/auth/budget/status",
    status_code=status.HTTP_200_OK,
    summary="Mock Budget Status",
    description="Mock budget status for load testing",
)
async def mock_budget_status():
    """Mock budget status for load testing."""
    return {
        "current_usage": 25.50,
        "budget_limit": 100.0,
        "remaining": 74.50,
        "period": "monthly",
        "reset_date": "2024-02-01T00:00:00Z"
    }


@router.get(
    "/api/v1/ws/stats",
    status_code=status.HTTP_200_OK,
    summary="Mock WebSocket Stats",
    description="Mock WebSocket statistics for load testing",
)
async def mock_ws_stats():
    """Mock WebSocket statistics for load testing."""
    return {
        "active_connections": 15,
        "total_connections": 1250,
        "messages_sent": 45000,
        "messages_received": 44500,
        "average_response_time": 0.125
    }


@router.get(
    "/api/v1/monitoring/metrics/current",
    status_code=status.HTTP_200_OK,
    summary="Mock Current Metrics",
    description="Mock current metrics for load testing",
)
async def mock_current_metrics():
    """Mock current metrics for load testing."""
    return {
        "cpu_usage": 35.2,
        "memory_usage": 512.0,
        "disk_usage": 45.8,
        "network_io": {
            "bytes_sent": 5000000,
            "bytes_recv": 12000000
        },
        "timestamp": time.time()
    }
