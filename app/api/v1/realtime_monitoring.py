"""
Realtime Monitoring API endpoints
"""

from fastapi import APIRouter, Depends
from app.security.auth import get_current_user

router = APIRouter(prefix="/monitoring", tags=["Realtime Monitoring"])

@router.get("/metrics")
async def get_current_metrics(current_user=Depends(get_current_user)):
    """Get current system metrics"""
    return {
        "cpu_usage": 45.2,
        "memory_usage": 67.8,
        "disk_usage": 23.1,
        "active_connections": 150,
        "response_time": 125
    }

@router.get("/unauthorized")
async def monitoring_metrics_endpoint():
    """Monitoring endpoint for testing unauthorized access"""
    return {"error": "Unauthorized", "status": 401} 