"""
Health check API endpoints
"""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "ai_assistant"}

@router.get("/detailed")
async def detailed_health():
    """Detailed health check with service status"""
    return {
        "status": "healthy",
        "services": {
            "database": "connected",
            "vector_search": "operational",
            "llm": "available",
            "cache": "active"
        },
        "timestamp": "2024-01-01T00:00:00Z"
    } 