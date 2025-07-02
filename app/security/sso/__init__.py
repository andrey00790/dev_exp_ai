"""
SSO (Single Sign-On) Authentication Module

This module provides enterprise SSO authentication support including:
- SAML 2.0 integration
- OAuth 2.0 providers (Google, Microsoft, etc.)
- Enterprise user management
- Provider configuration
"""

from .models import SSOProvider, SSOUser
from .oauth_auth import OAuthAuthHandler
from .saml_auth import SAMLAuthHandler
from .sso_manager import SSOManager

__all__ = [
    "SAMLAuthHandler",
    "OAuthAuthHandler",
    "SSOManager",
    "SSOUser",
    "SSOProvider",
]
