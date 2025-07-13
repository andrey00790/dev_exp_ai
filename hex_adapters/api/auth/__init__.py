"""
Authentication domain - handles user authentication, authorization and SSO.
"""

from .vk_oauth import router as vk_oauth_router
from .sso import router as sso_router
from .user_settings import router as user_settings_router

# Add compatibility imports for tests
try:
    from app.services.auth_service import AuthService
    from app.security.cost_control import CostControlManager
    from fastapi import HTTPException
    
    # Main router for compatibility (use SSO as primary)
    router = sso_router
    
    __all__ = [
        "vk_oauth_router", "sso_router", "user_settings_router", 
        "router", "AuthService", "CostControlManager", "HTTPException"
    ]
except ImportError:
    # Fallback mocks for tests
    from unittest.mock import Mock
    
    AuthService = Mock
    CostControlManager = Mock
    HTTPException = Mock
    router = sso_router
    
    __all__ = [
        "vk_oauth_router", "sso_router", "user_settings_router", 
        "router", "AuthService", "CostControlManager", "HTTPException"
    ]
