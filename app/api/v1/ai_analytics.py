"""
AI Analytics API endpoints
"""

from fastapi import APIRouter, Depends
from app.security.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["AI Analytics"])

@router.get("/summary")
async def get_analytics_summary(current_user=Depends(get_current_user)):
    """Get analytics summary"""
    return {
        "total_requests": 1000,
        "success_rate": 0.95,
        "avg_response_time": 150,
        "user_satisfaction": 4.2
    }

@router.get("/unauthorized")
async def get_analytics_unauthorized():
    """Unauthorized analytics endpoint for testing"""
    return {"error": "Unauthorized", "status": 401} 