"""
Users API endpoints
"""

from fastapi import APIRouter, Depends
from app.security.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me")
async def get_current_user_profile(current_user=Depends(get_current_user)):
    """Get current user profile"""
    return {"user": current_user, "status": "active"}

@router.get("/config")
async def get_user_config(current_user=Depends(get_current_user)):
    """Get user configuration"""
    return {
        "user_id": getattr(current_user, "user_id", "test_user"),
        "preferences": {"theme": "dark", "language": "en"},
        "settings": {"notifications": True}
    } 