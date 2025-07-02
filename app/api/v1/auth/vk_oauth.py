"""
VK OAuth 2.0 integration endpoints for user authentication.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import logging
from urllib.parse import urlencode
import secrets

from requests_oauth2client import OAuth2Client, AuthorizationRequest
from app.config import get_settings
from app.core.exceptions import VKOAuthError
from app.security.vk_auth import VKAuthService, VKUserInfo
from app.security.auth import create_access_token
from app.models.user import User
from infra.database.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


class VKAuthConfig(BaseModel):
    """VK OAuth configuration"""
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str = "email"


class VKAuthResponse(BaseModel):
    """VK OAuth callback response"""
    access_token: str
    token_type: str = "bearer"
    user_info: Dict[str, Any]


@router.get("/vk/login")
async def vk_oauth_login(request: Request):
    """
    Initiate VK OAuth login flow.
    Redirects user to VK authorization page.
    """
    if not settings.VK_OAUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VK OAuth is not enabled"
        )
    
    try:
        # Create VK OAuth client
        oauth_client = OAuth2Client(
            authorization_endpoint="https://oauth.vk.com/authorize",
            token_endpoint="https://oauth.vk.com/access_token",
            client_id=settings.VK_OAUTH_CLIENT_ID,
            client_secret=settings.VK_OAUTH_CLIENT_SECRET,
        )
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in session (in production use Redis or secure storage)
        request.session["vk_oauth_state"] = state
        
        # Create authorization request
        auth_request = AuthorizationRequest(
            authorization_endpoint="https://oauth.vk.com/authorize",
            client_id=settings.VK_OAUTH_CLIENT_ID,
            redirect_uri=settings.VK_OAUTH_REDIRECT_URI,
            scope=settings.VK_OAUTH_SCOPE,
            state=state,
            response_type="code"
        )
        
        logger.info(f"Redirecting to VK OAuth: {auth_request.uri}")
        return RedirectResponse(url=auth_request.uri)
        
    except Exception as e:
        logger.error(f"VK OAuth login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate VK OAuth login"
        )


@router.get("/vk/callback")
async def vk_oauth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle VK OAuth callback.
    Exchange authorization code for access token and validate user.
    """
    if not settings.VK_OAUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VK OAuth is not enabled"
        )
    
    # Check for OAuth errors
    if error:
        logger.error(f"VK OAuth error: {error} - {error_description}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"VK OAuth error: {error_description or error}"
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )
    
    # Validate CSRF state
    stored_state = request.session.get("vk_oauth_state")
    if not stored_state or stored_state != state:
        logger.error("Invalid OAuth state parameter")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    
    # Clean up state from session
    request.session.pop("vk_oauth_state", None)
    
    try:
        # Initialize VK auth service
        vk_auth = VKAuthService(
            client_id=settings.VK_OAUTH_CLIENT_ID,
            client_secret=settings.VK_OAUTH_CLIENT_SECRET,
            redirect_uri=settings.VK_OAUTH_REDIRECT_URI
        )
        
        # Exchange code for token and get user info
        user_info = await vk_auth.exchange_code_for_user_info(code)
        
        # Check if user is allowed
        if not vk_auth.is_user_allowed(user_info.user_id):
            logger.warning(f"VK user {user_info.user_id} is not in allowed list")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Your VK account is not authorized to access this application."
            )
        
        # Find or create user in our system
        user = await vk_auth.find_or_create_user(db, user_info)
        
        # Create JWT access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        logger.info(f"VK OAuth successful for user {user_info.user_id}")
        
        return VKAuthResponse(
            access_token=access_token,
            user_info={
                "vk_user_id": user_info.user_id,
                "first_name": user_info.first_name,
                "last_name": user_info.last_name,
                "email": user_info.email,
                "photo_url": user_info.photo_url
            }
        )
        
    except VKOAuthError as e:
        logger.error(f"VK OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"VK OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process VK OAuth callback"
        )


@router.get("/vk/check-access/{vk_user_id}")
async def check_vk_user_access(vk_user_id: str):
    """
    Check if a VK user has access to the application.
    This is useful for VK Teams bot integration.
    """
    if not settings.VK_OAUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VK OAuth is not enabled"
        )
    
    vk_auth = VKAuthService(
        client_id=settings.VK_OAUTH_CLIENT_ID,
        client_secret=settings.VK_OAUTH_CLIENT_SECRET
    )
    
    has_access = vk_auth.is_user_allowed(vk_user_id)
    
    return {
        "vk_user_id": vk_user_id,
        "has_access": has_access,
        "message": "Access granted" if has_access else "Access denied"
    }


@router.get("/vk/config")
async def get_vk_oauth_config():
    """
    Get VK OAuth configuration for frontend.
    Returns only public configuration.
    """
    if not settings.VK_OAUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VK OAuth is not enabled"
        )
    
    return {
        "enabled": settings.VK_OAUTH_ENABLED,
        "client_id": settings.VK_OAUTH_CLIENT_ID,
        "redirect_uri": settings.VK_OAUTH_REDIRECT_URI,
        "scope": settings.VK_OAUTH_SCOPE,
        "login_url": f"{request.url_for('vk_oauth_login')}"
    } 