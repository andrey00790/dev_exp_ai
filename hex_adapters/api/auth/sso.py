"""
SSO API Endpoints

Provides REST API endpoints for SSO functionality including:
- SSO provider management
- Authentication initiation
- Callback handling
- Session management
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import (APIRouter, Depends, Form, HTTPException, Query, Request,
                     Response, status)
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from infra.database import get_db
from app.models.user import User
from app.security.auth import get_current_admin_user, get_current_user
from app.security.sso.models import SSOProviderType
from app.security.sso.sso_manager import SSOManager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["SSO Authentication"])

# Initialize SSO manager
sso_manager = SSOManager()


# Pydantic models
class SSOProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider_type: SSOProviderType
    enabled: bool = True

    # SAML fields
    entity_id: Optional[str] = None
    sso_url: Optional[str] = None
    slo_url: Optional[str] = None
    x509_cert: Optional[str] = None

    # OAuth fields
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    authorization_url: Optional[str] = None
    token_url: Optional[str] = None
    userinfo_url: Optional[str] = None
    scope: Optional[str] = None

    # Additional configuration
    config: Optional[Dict[str, Any]] = {}


class SSOProviderUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None

    # SAML fields
    entity_id: Optional[str] = None
    sso_url: Optional[str] = None
    slo_url: Optional[str] = None
    x509_cert: Optional[str] = None

    # OAuth fields
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    authorization_url: Optional[str] = None
    token_url: Optional[str] = None
    userinfo_url: Optional[str] = None
    scope: Optional[str] = None

    # Additional configuration
    config: Optional[Dict[str, Any]] = None


class SSOProviderResponse(BaseModel):
    id: int
    name: str
    provider_type: str
    enabled: bool
    available: bool
    login_url: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class SSOLoginResponse(BaseModel):
    type: str  # "redirect" or "form"
    url: str
    state: Optional[str] = None
    provider: str


class SSOUserInfo(BaseModel):
    id: int
    external_user_id: str
    external_email: Optional[str] = None
    external_name: Optional[str] = None
    provider_name: str
    last_sso_login: Optional[datetime] = None
    active: bool


# Public endpoints (no authentication required)
@router.get("/providers", response_model=List[SSOProviderResponse])
async def get_available_providers(db: Session = Depends(get_db)):
    """Get list of available SSO providers for login"""
    try:
        providers = sso_manager.get_available_providers(db)
        return providers
    except Exception as e:
        logger.error(f"Failed to get SSO providers: {e}")
        raise HTTPException(status_code=500, detail="Failed to get SSO providers")


@router.get("/login/{provider_id}", response_model=SSOLoginResponse)
async def initiate_sso_login(
    provider_id: int, request: Request, db: Session = Depends(get_db)
):
    """Initiate SSO login flow for specified provider"""
    try:
        login_info = await sso_manager.initiate_login(provider_id, request, db)
        return login_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate SSO login: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate SSO login")


# SAML endpoints
@router.post("/saml/{provider_id}/acs")
async def saml_acs(provider_id: int, request: Request, db: Session = Depends(get_db)):
    """Handle SAML ACS (Assertion Consumer Service) response"""
    try:
        user_data, access_token = await sso_manager.handle_saml_acs(
            provider_id, request, db
        )

        # Return token in secure HTTP-only cookie
        response = JSONResponse(
            {
                "message": "SAML authentication successful",
                "user": {
                    "email": user_data.get("external_email"),
                    "name": user_data.get("external_name"),
                },
            }
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=3600,
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SAML ACS handling failed: {e}")
        raise HTTPException(status_code=500, detail="SAML authentication failed")


@router.get("/saml/{provider_id}/sls")
async def saml_sls(provider_id: int, request: Request, db: Session = Depends(get_db)):
    """Handle SAML SLS (Single Logout Service) request"""
    try:
        # Handle SLO request
        # Implementation depends on your session management
        return {"message": "Logout successful"}
    except Exception as e:
        logger.error(f"SAML SLS handling failed: {e}")
        raise HTTPException(status_code=500, detail="SAML logout failed")


@router.get("/saml/{provider_id}/metadata", response_class=Response)
async def saml_metadata(provider_id: int, db: Session = Depends(get_db)):
    """Get SAML metadata for this service provider"""
    try:
        metadata = sso_manager.get_provider_metadata(db, provider_id)
        return Response(content=metadata, media_type="application/xml")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SAML metadata generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate SAML metadata")


# OAuth endpoints
@router.get("/oauth/{provider_id}/callback")
async def oauth_callback(
    provider_id: int,
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Handle OAuth callback with authorization code"""
    if error:
        logger.error(f"OAuth callback error: {error}")
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    try:
        user_data, access_token = await sso_manager.handle_oauth_callback(
            provider_id, code, state, db
        )

        # Redirect to frontend with token
        frontend_url = f"http://localhost:3000/auth/callback?token={access_token}"
        return RedirectResponse(url=frontend_url, status_code=status.HTTP_302_FOUND)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback handling failed: {e}")
        raise HTTPException(status_code=500, detail="OAuth authentication failed")


# Protected endpoints (require authentication)
@router.post("/logout")
async def sso_logout(
    provider_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Logout from SSO session"""
    try:
        logout_url = await sso_manager.handle_logout(current_user.id, provider_id, db)

        response_data = {"message": "Logout successful"}
        if logout_url:
            response_data["redirect_url"] = logout_url

        return response_data

    except Exception as e:
        logger.error(f"SSO logout failed: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")


@router.get("/user/info", response_model=List[SSOUserInfo])
async def get_user_sso_info(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get SSO information for current user"""
    try:
        sso_info = sso_manager.get_user_sso_info(db, current_user.id)
        return sso_info
    except Exception as e:
        logger.error(f"Failed to get user SSO info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get SSO information")


# Admin endpoints (require admin privileges)
@router.post("/admin/providers", response_model=SSOProviderResponse)
async def create_sso_provider(
    provider_data: SSOProviderCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Create new SSO provider (admin only)"""
    try:
        provider = sso_manager.create_provider(
            db, provider_data.dict(), created_by=current_user.id
        )
        return provider.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create SSO provider: {e}")
        raise HTTPException(status_code=500, detail="Failed to create SSO provider")


@router.get("/admin/providers", response_model=List[SSOProviderResponse])
async def list_all_sso_providers(
    current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)
):
    """List all SSO providers (admin only)"""
    try:
        providers = sso_manager.get_available_providers(db)
        return providers
    except Exception as e:
        logger.error(f"Failed to list SSO providers: {e}")
        raise HTTPException(status_code=500, detail="Failed to list SSO providers")


@router.put("/admin/providers/{provider_id}", response_model=SSOProviderResponse)
async def update_sso_provider(
    provider_id: int,
    update_data: SSOProviderUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Update SSO provider configuration (admin only)"""
    try:
        provider = sso_manager.update_provider(
            db, provider_id, update_data.dict(exclude_unset=True)
        )
        return provider.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update SSO provider: {e}")
        raise HTTPException(status_code=500, detail="Failed to update SSO provider")


@router.delete("/admin/providers/{provider_id}")
async def delete_sso_provider(
    provider_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Delete SSO provider (admin only)"""
    try:
        sso_manager.delete_provider(db, provider_id)
        return {"message": "SSO provider deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete SSO provider: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete SSO provider")


@router.post("/admin/providers/{provider_id}/test")
async def test_sso_provider(
    provider_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Test SSO provider configuration (admin only)"""
    try:
        # Basic configuration validation
        provider = sso_manager._get_provider(db, provider_id)
        availability = sso_manager._check_provider_availability(provider)

        result = {
            "provider_id": provider_id,
            "provider_name": provider.name,
            "provider_type": provider.provider_type,
            "available": availability,
            "enabled": provider.enabled,
            "configuration_valid": True,  # Add more validation logic here
        }

        if provider.provider_type == "saml":
            try:
                # Test SAML metadata generation
                metadata = sso_manager.get_provider_metadata(db, provider_id)
                result["saml_metadata_valid"] = bool(metadata)
            except Exception as e:
                result["saml_metadata_valid"] = False
                result["saml_error"] = str(e)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test SSO provider: {e}")
        raise HTTPException(status_code=500, detail="Failed to test SSO provider")


# Health check endpoint
@router.get("/health")
async def sso_health_check():
    """SSO service health check"""
    return {
        "status": "healthy",
        "saml_available": sso_manager.saml_handler.is_available(),
        "oauth_available": sso_manager.oauth_handler.is_available(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
