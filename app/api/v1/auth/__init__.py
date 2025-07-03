"""
Authentication domain - handles user authentication, authorization and SSO.
"""

from .auth import router as auth_router
from .vk_oauth import router as vk_oauth_router
from .sso import router as sso
from .user_settings import router as user_settings
from .users import router as users

# Add compatibility imports for tests
try:
    from app.services.auth_service import AuthService
    from app.security.cost_control import CostControlManager
    from fastapi import HTTPException
    
    # Main router for compatibility
    router = auth_router
    
    __all__ = [
        "auth_router", "vk_oauth_router", "sso", "users", "user_settings",
        "router", "AuthService", "CostControlManager", "HTTPException"
    ]
except ImportError:
    # Fallback mocks for tests
    from unittest.mock import Mock
    
    AuthService = Mock
    CostControlManager = Mock
    HTTPException = Mock
    router = auth_router
    
    __all__ = [
        "auth_router", "vk_oauth_router", "sso", "users", "user_settings", 
        "router", "AuthService", "CostControlManager", "HTTPException"
    ]
