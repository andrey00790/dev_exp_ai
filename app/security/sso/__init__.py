"""
SSO (Single Sign-On) Authentication Module

This module provides enterprise SSO authentication support including:
- SAML 2.0 integration
- OAuth 2.0 providers (Google, Microsoft, etc.)
- Enterprise user management
- Provider configuration
"""

from .saml_auth import SAMLAuthHandler
from .oauth_auth import OAuthAuthHandler
from .sso_manager import SSOManager
from .models import SSOUser, SSOProvider

__all__ = [
    "SAMLAuthHandler",
    "OAuthAuthHandler", 
    "SSOManager",
    "SSOUser",
    "SSOProvider"
] 