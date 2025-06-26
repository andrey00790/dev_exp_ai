"""
User Settings API
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter(prefix="/user-settings", tags=["User Settings"])


@router.get("/")
async def get_user_settings() -> Dict[str, Any]:
    """Get user settings"""
    return {
        "theme": "light",
        "language": "en",
        "notifications": True,
        "ai_model": "gpt-3.5-turbo"
    }


@router.put("/")
async def update_user_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Update user settings"""
    return {"message": "Settings updated successfully", "settings": settings} 