"""
LLM Management API endpoints
"""

from fastapi import APIRouter, Depends
from app.security.auth import get_current_user

router = APIRouter(prefix="/llm", tags=["LLM Management"])

@router.get("/models")
async def get_available_models(current_user=Depends(get_current_user)):
    """Get list of available LLM models"""
    return {
        "models": [
            {"name": "gpt-4", "provider": "openai", "status": "available"},
            {"name": "claude-3", "provider": "anthropic", "status": "available"},
            {"name": "llama-2", "provider": "ollama", "status": "available"}
        ]
    }

@router.get("/health")
async def llm_health():
    """LLM service health check"""
    return {"status": "healthy", "service": "llm_management"}

@router.post("/generate")
async def generate_response(
    prompt: str,
    model: str = "gpt-4",
    current_user=Depends(get_current_user)
):
    """Generate LLM response"""
    return {
        "response": f"Generated response for: {prompt}",
        "model": model,
        "success": True
    } 