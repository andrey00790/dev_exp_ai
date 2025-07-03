"""
SSO Manager

Central coordinator for all SSO authentication flows including:
- Provider management
- Authentication routing
- Session management
- Configuration validation
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from ..auth import create_access_token
from .models import SSOProvider, SSOProviderType, SSOSession, SSOUser
from .oauth_auth import OAuthAuthHandler
from .saml_auth import SAMLAuthHandler

logger = logging.getLogger(__name__)


class SSOManager:
    """Manages all SSO authentication providers and flows"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.saml_handler = SAMLAuthHandler(base_url)
        self.oauth_handler = OAuthAuthHandler(base_url)

    def get_available_providers(self, db: Session) -> List[Dict[str, Any]]:
        """Get list of enabled SSO providers"""
        providers = db.query(SSOProvider).filter(SSOProvider.enabled == True).all()

        result = []
        for provider in providers:
            provider_info = {
                "id": provider.id,
                "name": provider.name,
                "provider_type": provider.provider_type,
                "enabled": provider.enabled,
                "login_url": self._get_login_url(provider),
                "available": self._check_provider_availability(provider),
            }

            # Add provider-specific UI information
            if provider.provider_type.startswith("oauth_"):
                from .oauth_auth import OAUTH_PROVIDER_CONFIGS

                config = OAUTH_PROVIDER_CONFIGS.get(provider.provider_type, {})
                provider_info.update(
                    {
                        "display_name": config.get("name", provider.name),
                        "icon": config.get("icon"),
                        "color": config.get("color"),
                    }
                )

            result.append(provider_info)

        return result

    async def initiate_login(
        self, provider_id: int, request: Request, db: Session
    ) -> Dict[str, Any]:
        """Initiate SSO login for specified provider"""
        provider = self._get_provider(db, provider_id)

        if not provider.enabled:
            raise HTTPException(status_code=400, detail="SSO provider is disabled")

        if provider.provider_type == SSOProviderType.SAML:
            return await self._initiate_saml_login(provider, request)
        elif provider.provider_type.startswith("oauth_"):
            return await self._initiate_oauth_login(provider)
        else:
            raise HTTPException(status_code=400, detail="Unsupported provider type")

    async def handle_saml_acs(
        self, provider_id: int, request: Request, db: Session
    ) -> Tuple[Dict[str, Any], str]:
        """Handle SAML ACS response"""
        provider = self._get_provider(db, provider_id)

        if provider.provider_type != SSOProviderType.SAML:
            raise HTTPException(status_code=400, detail="Not a SAML provider")

        if not self.saml_handler.is_available():
            raise HTTPException(status_code=500, detail="SAML not available")

        return await self.saml_handler.handle_acs_response(request, provider, db)

    async def handle_oauth_callback(
        self, provider_id: int, code: str, state: str, db: Session
    ) -> Tuple[Dict[str, Any], str]:
        """Handle OAuth callback"""
        provider = self._get_provider(db, provider_id)

        if not provider.provider_type.startswith("oauth_"):
            raise HTTPException(status_code=400, detail="Not an OAuth provider")

        if not self.oauth_handler.is_available():
            raise HTTPException(status_code=500, detail="OAuth not available")

        return await self.oauth_handler.handle_callback(provider, code, state, db)

    async def handle_logout(
        self, user_id: int, provider_id: Optional[int], db: Session
    ) -> Optional[str]:
        """Handle SSO logout"""
        # Find active SSO sessions for user
        query = db.query(SSOSession).filter(
            SSOSession.user_id == user_id, SSOSession.active == True
        )

        if provider_id:
            query = query.filter(SSOSession.provider_id == provider_id)

        sessions = query.all()

        # Deactivate sessions
        for session in sessions:
            session.active = False
            session.logout_reason = "manual"

        db.commit()

        # For SAML, initiate SLO if supported
        if provider_id:
            provider = self._get_provider(db, provider_id)
            if provider.provider_type == SSOProviderType.SAML and provider.slo_url:
                # Return SLO URL for redirect
                return (
                    f"{provider.slo_url}?SAMLRequest=..."  # Proper SLO request needed
                )

        return None

    def create_provider(
        self,
        db: Session,
        provider_data: Dict[str, Any],
        created_by: Optional[int] = None,
    ) -> SSOProvider:
        """Create new SSO provider"""
        # Validate provider configuration
        self._validate_provider_config(provider_data)

        provider = SSOProvider(
            name=provider_data["name"],
            provider_type=provider_data["provider_type"],
            enabled=provider_data.get("enabled", True),
            config=provider_data.get("config", {}),
            created_by=created_by,
        )

        # Set provider-specific fields
        if provider.provider_type == SSOProviderType.SAML:
            provider.entity_id = provider_data.get("entity_id")
            provider.sso_url = provider_data.get("sso_url")
            provider.slo_url = provider_data.get("slo_url")
            provider.x509_cert = provider_data.get("x509_cert")
        elif provider.provider_type.startswith("oauth_"):
            provider.client_id = provider_data.get("client_id")
            provider.client_secret = provider_data.get("client_secret")
            provider.authorization_url = provider_data.get("authorization_url")
            provider.token_url = provider_data.get("token_url")
            provider.userinfo_url = provider_data.get("userinfo_url")
            provider.scope = provider_data.get("scope")

        db.add(provider)
        db.commit()

        logger.info(f"Created SSO provider: {provider.name} ({provider.provider_type})")
        return provider

    def update_provider(
        self, db: Session, provider_id: int, update_data: Dict[str, Any]
    ) -> SSOProvider:
        """Update existing SSO provider"""
        provider = self._get_provider(db, provider_id)

        # Update basic fields
        for field in ["name", "enabled", "config"]:
            if field in update_data:
                setattr(provider, field, update_data[field])

        # Update provider-specific fields
        if provider.provider_type == SSOProviderType.SAML:
            for field in ["entity_id", "sso_url", "slo_url", "x509_cert"]:
                if field in update_data:
                    setattr(provider, field, update_data[field])
        elif provider.provider_type.startswith("oauth_"):
            for field in [
                "client_id",
                "client_secret",
                "authorization_url",
                "token_url",
                "userinfo_url",
                "scope",
            ]:
                if field in update_data:
                    setattr(provider, field, update_data[field])

        db.commit()

        logger.info(f"Updated SSO provider: {provider.name}")
        return provider

    def delete_provider(self, db: Session, provider_id: int):
        """Delete SSO provider"""
        provider = self._get_provider(db, provider_id)

        # Check if provider has active users
        active_users = (
            db.query(SSOUser)
            .filter(SSOUser.provider_id == provider_id, SSOUser.active == True)
            .count()
        )

        if active_users > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete provider with {active_users} active users",
            )

        db.delete(provider)
        db.commit()

        logger.info(f"Deleted SSO provider: {provider.name}")

    def get_provider_metadata(self, db: Session, provider_id: int) -> str:
        """Get provider metadata (for SAML)"""
        provider = self._get_provider(db, provider_id)

        if provider.provider_type == SSOProviderType.SAML:
            if not self.saml_handler.is_available():
                raise HTTPException(status_code=500, detail="SAML not available")
            return self.saml_handler.get_metadata(provider)
        else:
            raise HTTPException(
                status_code=400, detail="Metadata only available for SAML providers"
            )

    def get_user_sso_info(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Get SSO information for user"""
        sso_users = (
            db.query(SSOUser)
            .filter(SSOUser.user_id == user_id, SSOUser.active == True)
            .all()
        )

        return [sso_user.to_dict() for sso_user in sso_users]

    def _get_provider(self, db: Session, provider_id: int) -> SSOProvider:
        """Get provider by ID"""
        provider = db.query(SSOProvider).filter(SSOProvider.id == provider_id).first()
        if not provider:
            raise HTTPException(status_code=404, detail="SSO provider not found")
        return provider

    def _get_login_url(self, provider: SSOProvider) -> str:
        """Get login URL for provider"""
        if provider.provider_type == SSOProviderType.SAML:
            return f"{self.base_url}/api/v1/auth/sso/saml/{provider.id}/login"
        elif provider.provider_type.startswith("oauth_"):
            return f"{self.base_url}/api/v1/auth/sso/oauth/{provider.id}/login"
        else:
            return ""

    def _check_provider_availability(self, provider: SSOProvider) -> bool:
        """Check if provider is available (dependencies installed)"""
        if provider.provider_type == SSOProviderType.SAML:
            return self.saml_handler.is_available()
        elif provider.provider_type.startswith("oauth_"):
            return self.oauth_handler.is_available()
        return False

    async def _initiate_saml_login(
        self, provider: SSOProvider, request: Request
    ) -> Dict[str, Any]:
        """Initiate SAML login"""
        redirect_url = await self.saml_handler.initiate_login(request, provider)
        return {"type": "redirect", "url": redirect_url, "provider": provider.name}

    async def _initiate_oauth_login(self, provider: SSOProvider) -> Dict[str, Any]:
        """Initiate OAuth login"""
        authorization_url, state = await self.oauth_handler.initiate_login(provider)
        return {
            "type": "redirect",
            "url": authorization_url,
            "state": state,
            "provider": provider.name,
        }

    def _validate_provider_config(self, provider_data: Dict[str, Any]):
        """Validate provider configuration"""
        required_fields = {
            SSOProviderType.SAML: ["name", "entity_id", "sso_url"],
            SSOProviderType.OAUTH_GOOGLE: ["name", "client_id", "client_secret"],
            SSOProviderType.OAUTH_MICROSOFT: ["name", "client_id", "client_secret"],
            SSOProviderType.OAUTH_GITHUB: ["name", "client_id", "client_secret"],
            SSOProviderType.OAUTH_CUSTOM: [
                "name",
                "client_id",
                "client_secret",
                "authorization_url",
                "token_url",
            ],
        }

        provider_type = provider_data.get("provider_type")
        if provider_type not in required_fields:
            raise HTTPException(status_code=400, detail="Invalid provider type")

        missing_fields = []
        for field in required_fields[provider_type]:
            if field not in provider_data or not provider_data[field]:
                missing_fields.append(field)

        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing_fields)}",
            )


class SSOConfig:
    """SSO configuration settings"""

    def __init__(self):
        self.session_timeout = 3600  # 1 hour
        self.max_sessions_per_user = 5
        self.require_encryption = True
        self.allowed_clock_skew = 300  # 5 minutes for SAML

    @classmethod
    def from_env(cls) -> "SSOConfig":
        """Load configuration from environment variables"""
        import os

        config = cls()
        config.session_timeout = int(os.getenv("SSO_SESSION_TIMEOUT", "3600"))
        config.max_sessions_per_user = int(os.getenv("SSO_MAX_SESSIONS", "5"))
        config.require_encryption = (
            os.getenv("SSO_REQUIRE_ENCRYPTION", "true").lower() == "true"
        )
        config.allowed_clock_skew = int(os.getenv("SSO_CLOCK_SKEW", "300"))

        return config
