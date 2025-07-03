"""
SSO Database Models

Defines database models for SSO functionality including:
- SSO providers configuration
- SSO user mappings
- Enterprise user profiles
"""

from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import (JSON, Boolean, Column, DateTime, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class SSOProviderType(str, Enum):
    """Supported SSO provider types"""

    SAML = "saml"
    OAUTH_GOOGLE = "oauth_google"
    OAUTH_MICROSOFT = "oauth_microsoft"
    OAUTH_GITHUB = "oauth_github"
    OAUTH_OKTA = "oauth_okta"
    OAUTH_CUSTOM = "oauth_custom"


class SSOProvider(Base):
    """SSO Provider Configuration"""

    __tablename__ = "sso_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    provider_type = Column(String(20), nullable=False)  # SSOProviderType
    enabled = Column(Boolean, default=True, nullable=False)

    # Provider configuration (JSON field)
    config = Column(JSON, nullable=False)

    # SAML specific fields
    entity_id = Column(String(255), nullable=True)
    sso_url = Column(String(500), nullable=True)
    slo_url = Column(String(500), nullable=True)
    x509_cert = Column(Text, nullable=True)

    # OAuth specific fields
    client_id = Column(String(255), nullable=True)
    client_secret = Column(String(255), nullable=True)
    authorization_url = Column(String(500), nullable=True)
    token_url = Column(String(500), nullable=True)
    userinfo_url = Column(String(500), nullable=True)
    scope = Column(String(200), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, nullable=True)

    # Relationships
    sso_users = relationship("SSOUser", back_populates="provider")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "provider_type": self.provider_type,
            "enabled": self.enabled,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SSOUser(Base):
    """SSO User Mapping"""

    __tablename__ = "sso_users"

    id = Column(Integer, primary_key=True, index=True)

    # Link to main user table
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # SSO Provider reference
    provider_id = Column(Integer, ForeignKey("sso_providers.id"), nullable=False)

    # External user identifier from SSO provider
    external_user_id = Column(String(255), nullable=False)

    # User attributes from SSO provider
    external_email = Column(String(255), nullable=True)
    external_name = Column(String(200), nullable=True)
    external_groups = Column(JSON, nullable=True)  # List of groups/roles
    external_attributes = Column(JSON, nullable=True)  # Additional attributes

    # SSO session information
    last_sso_login = Column(DateTime(timezone=True), nullable=True)
    sso_session_id = Column(String(255), nullable=True)

    # Status
    active = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    provider = relationship("SSOProvider", back_populates="sso_users")

    # Unique constraint on provider + external_user_id
    __table_args__ = {"extend_existing": True}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "provider_id": self.provider_id,
            "provider_name": self.provider.name if self.provider else None,
            "external_user_id": self.external_user_id,
            "external_email": self.external_email,
            "external_name": self.external_name,
            "external_groups": self.external_groups,
            "last_sso_login": (
                self.last_sso_login.isoformat() if self.last_sso_login else None
            ),
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SSOSession(Base):
    """SSO Session Tracking"""

    __tablename__ = "sso_sessions"

    id = Column(Integer, primary_key=True, index=True)

    # Session identifiers
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    sso_session_index = Column(String(255), nullable=True)  # SAML SessionIndex

    # User and provider
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("sso_providers.id"), nullable=False)

    # Session metadata
    login_time = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Session data
    session_data = Column(JSON, nullable=True)

    # Status
    active = Column(Boolean, default=True, nullable=False)
    logout_reason = Column(String(100), nullable=True)  # manual, timeout, slo, etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "provider_id": self.provider_id,
            "login_time": self.login_time.isoformat() if self.login_time else None,
            "last_activity": (
                self.last_activity.isoformat() if self.last_activity else None
            ),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "active": self.active,
            "logout_reason": self.logout_reason,
        }


# Default SSO provider configurations
DEFAULT_PROVIDER_CONFIGS = {
    SSOProviderType.OAUTH_GOOGLE: {
        "authorization_url": "https://accounts.google.com/o/oauth2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scope": "openid email profile",
    },
    SSOProviderType.OAUTH_MICROSOFT: {
        "authorization_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
        "scope": "openid email profile",
    },
    SSOProviderType.OAUTH_GITHUB: {
        "authorization_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scope": "user:email",
    },
}
