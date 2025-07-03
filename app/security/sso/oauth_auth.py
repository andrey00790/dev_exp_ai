"""
OAuth 2.0 Authentication Handler

Provides OAuth 2.0 SSO authentication functionality including:
- Multiple OAuth providers (Google, Microsoft, GitHub, etc.)
- Authorization code flow
- Token management
- User profile retrieval
"""

import base64
import hashlib
import json
import logging
import secrets
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse

try:
    from authlib.integrations.requests_client import OAuth2Session
    from authlib.oauth2 import OAuth2Error

    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False
    OAuth2Session = None
    OAuth2Error = Exception

from datetime import datetime, timedelta

import httpx
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_password_hash
from .models import (DEFAULT_PROVIDER_CONFIGS, SSOProvider, SSOProviderType,
                     SSOSession, SSOUser)

logger = logging.getLogger(__name__)


class OAuthAuthHandler:
    """Handles OAuth 2.0 authentication flows"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        if not OAUTH_AVAILABLE:
            logger.warning("authlib not available. OAuth authentication disabled.")

    def is_available(self) -> bool:
        """Check if OAuth authentication is available"""
        return OAUTH_AVAILABLE

    async def initiate_login(
        self, provider: SSOProvider, state: Optional[str] = None
    ) -> Tuple[str, str]:
        """Initiate OAuth login flow"""
        if not self.is_available():
            raise HTTPException(status_code=500, detail="OAuth not available")

        # Generate state parameter for CSRF protection
        if not state:
            state = secrets.token_urlsafe(32)

        # Get provider configuration
        config = self._get_provider_config(provider)

        # Build OAuth client
        client = OAuth2Session(
            client_id=provider.client_id,
            client_secret=provider.client_secret,
            redirect_uri=self._get_redirect_uri(provider),
            scope=config.get("scope", "openid email profile"),
        )

        # Generate authorization URL
        authorization_url, oauth_state = client.create_authorization_url(
            config["authorization_url"], state=state
        )

        # Add PKCE for enhanced security (if supported)
        if provider.provider_type in [
            SSOProviderType.OAUTH_GOOGLE,
            SSOProviderType.OAUTH_MICROSOFT,
        ]:
            code_verifier = (
                base64.urlsafe_b64encode(secrets.token_bytes(32))
                .decode("utf-8")
                .rstrip("=")
            )
            code_challenge = (
                base64.urlsafe_b64encode(
                    hashlib.sha256(code_verifier.encode("utf-8")).digest()
                )
                .decode("utf-8")
                .rstrip("=")
            )

            authorization_url += (
                f"&code_challenge={code_challenge}&code_challenge_method=S256"
            )
            # Store code_verifier in session or cache for later use
            # For now, we'll include it in the state (in production, use secure session storage)
            state = f"{state}:{code_verifier}"

        logger.info(f"OAuth login initiated for provider: {provider.name}")
        return authorization_url, state

    async def handle_callback(
        self, provider: SSOProvider, code: str, state: str, db: Session
    ) -> Tuple[Dict[str, Any], str]:
        """Handle OAuth callback with authorization code"""
        if not self.is_available():
            raise HTTPException(status_code=500, detail="OAuth not available")

        try:
            # Extract PKCE verifier from state if present
            code_verifier = None
            if ":" in state:
                state, code_verifier = state.rsplit(":", 1)

            # Get provider configuration
            config = self._get_provider_config(provider)

            # Exchange authorization code for tokens
            token_data = await self._exchange_code_for_tokens(
                provider, config, code, code_verifier
            )

            # Get user profile using access token
            user_profile = await self._get_user_profile(
                provider, config, token_data["access_token"]
            )

            # Map OAuth profile to user data
            user_data = self._map_oauth_profile(provider, user_profile, token_data)

            # Find or create SSO user
            sso_user = await self._find_or_create_sso_user(db, provider, user_data)

            # Create SSO session
            await self._create_sso_session(db, sso_user, token_data)

            # Generate JWT token
            access_token = create_access_token(data={"sub": str(sso_user.user_id)})

            logger.info(
                f"OAuth authentication successful for user: {user_data['external_user_id']}"
            )
            return user_data, access_token

        except Exception as e:
            logger.error(f"OAuth callback handling failed: {e}")
            raise HTTPException(
                status_code=400, detail=f"OAuth authentication failed: {str(e)}"
            )

    async def refresh_token(
        self, provider: SSOProvider, refresh_token: str
    ) -> Dict[str, Any]:
        """Refresh OAuth access token"""
        if not self.is_available():
            raise HTTPException(status_code=500, detail="OAuth not available")

        config = self._get_provider_config(provider)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                config["token_url"],
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": provider.client_id,
                    "client_secret": provider.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to refresh token")

            return response.json()

    async def revoke_token(
        self, provider: SSOProvider, token: str, token_type: str = "access_token"
    ):
        """Revoke OAuth token"""
        config = self._get_provider_config(provider)
        revoke_url = config.get("revoke_url")

        if not revoke_url:
            logger.warning(f"No revoke URL configured for provider: {provider.name}")
            return

        async with httpx.AsyncClient() as client:
            await client.post(
                revoke_url,
                data={
                    "token": token,
                    "token_type_hint": token_type,
                    "client_id": provider.client_id,
                    "client_secret": provider.client_secret,
                },
            )

    def _get_provider_config(self, provider: SSOProvider) -> Dict[str, Any]:
        """Get provider configuration with defaults"""
        config = DEFAULT_PROVIDER_CONFIGS.get(provider.provider_type, {}).copy()

        # Override with provider-specific config
        if provider.config:
            config.update(provider.config)

        # Add provider-specific URLs
        if provider.authorization_url:
            config["authorization_url"] = provider.authorization_url
        if provider.token_url:
            config["token_url"] = provider.token_url
        if provider.userinfo_url:
            config["userinfo_url"] = provider.userinfo_url
        if provider.scope:
            config["scope"] = provider.scope

        return config

    def _get_redirect_uri(self, provider: SSOProvider) -> str:
        """Get OAuth redirect URI for provider"""
        return f"{self.base_url}/api/v1/auth/sso/oauth/{provider.id}/callback"

    async def _exchange_code_for_tokens(
        self,
        provider: SSOProvider,
        config: Dict[str, Any],
        code: str,
        code_verifier: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._get_redirect_uri(provider),
            "client_id": provider.client_id,
            "client_secret": provider.client_secret,
        }

        # Add PKCE verifier if present
        if code_verifier:
            token_data["code_verifier"] = code_verifier

        async with httpx.AsyncClient() as client:
            response = await client.post(
                config["token_url"],
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                raise HTTPException(
                    status_code=400, detail="Failed to exchange authorization code"
                )

            return response.json()

    async def _get_user_profile(
        self, provider: SSOProvider, config: Dict[str, Any], access_token: str
    ) -> Dict[str, Any]:
        """Get user profile from OAuth provider"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                config["userinfo_url"],
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                logger.error(f"User profile retrieval failed: {response.text}")
                raise HTTPException(
                    status_code=400, detail="Failed to get user profile"
                )

            return response.json()

    def _map_oauth_profile(
        self, provider: SSOProvider, profile: Dict[str, Any], token_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map OAuth profile to user data"""
        user_data = {
            "external_user_id": None,
            "external_email": None,
            "external_name": None,
            "external_groups": [],
            "external_attributes": profile,
            "oauth_tokens": token_data,
        }

        # Provider-specific mapping
        if provider.provider_type == SSOProviderType.OAUTH_GOOGLE:
            user_data.update(
                {
                    "external_user_id": profile.get("id") or profile.get("sub"),
                    "external_email": profile.get("email"),
                    "external_name": profile.get("name"),
                    "external_first_name": profile.get("given_name"),
                    "external_last_name": profile.get("family_name"),
                }
            )

        elif provider.provider_type == SSOProviderType.OAUTH_MICROSOFT:
            user_data.update(
                {
                    "external_user_id": profile.get("id") or profile.get("sub"),
                    "external_email": profile.get("mail")
                    or profile.get("userPrincipalName"),
                    "external_name": profile.get("displayName"),
                    "external_first_name": profile.get("givenName"),
                    "external_last_name": profile.get("surname"),
                }
            )

        elif provider.provider_type == SSOProviderType.OAUTH_GITHUB:
            user_data.update(
                {
                    "external_user_id": str(profile.get("id")),
                    "external_email": profile.get("email"),
                    "external_name": profile.get("name") or profile.get("login"),
                    "external_username": profile.get("login"),
                }
            )

        else:
            # Generic OAuth mapping
            user_data.update(
                {
                    "external_user_id": profile.get("id")
                    or profile.get("sub")
                    or profile.get("user_id"),
                    "external_email": profile.get("email"),
                    "external_name": profile.get("name") or profile.get("display_name"),
                    "external_username": profile.get("username")
                    or profile.get("login"),
                }
            )

        # Fallback to email as user ID if no ID found
        if not user_data["external_user_id"]:
            user_data["external_user_id"] = user_data["external_email"]

        return user_data

    async def _find_or_create_sso_user(
        self, db: Session, provider: SSOProvider, user_data: Dict[str, Any]
    ) -> SSOUser:
        """Find existing SSO user or create new one"""
        external_user_id = user_data["external_user_id"]

        # Try to find existing SSO user
        sso_user = (
            db.query(SSOUser)
            .filter(
                SSOUser.provider_id == provider.id,
                SSOUser.external_user_id == external_user_id,
            )
            .first()
        )

        if sso_user:
            # Update existing user data
            sso_user.external_email = user_data.get("external_email")
            sso_user.external_name = user_data.get("external_name")
            sso_user.external_groups = user_data.get("external_groups", [])
            sso_user.external_attributes = user_data.get("external_attributes", {})
            sso_user.last_sso_login = datetime.utcnow()
            db.commit()
            return sso_user

        # Create new user in main users table first
        from ...models.user import User  # Assuming we have a User model

        user = User(
            email=user_data.get(
                "external_email", f"{external_user_id}@{provider.name}"
            ),
            username=user_data.get("external_name", external_user_id),
            hashed_password=get_password_hash("sso_user_no_password"),
            is_active=True,
            is_sso_user=True,
        )
        db.add(user)
        db.flush()

        # Create SSO user mapping
        sso_user = SSOUser(
            user_id=user.id,
            provider_id=provider.id,
            external_user_id=external_user_id,
            external_email=user_data.get("external_email"),
            external_name=user_data.get("external_name"),
            external_groups=user_data.get("external_groups", []),
            external_attributes=user_data.get("external_attributes", {}),
            last_sso_login=datetime.utcnow(),
            active=True,
        )
        db.add(sso_user)
        db.commit()

        logger.info(
            f"Created new OAuth SSO user: {external_user_id} for provider: {provider.name}"
        )
        return sso_user

    async def _create_sso_session(
        self, db: Session, sso_user: SSOUser, token_data: Dict[str, Any]
    ):
        """Create SSO session record"""
        session_id = secrets.token_urlsafe(32)
        expires_at = None

        # Calculate expiration time from token data
        if "expires_in" in token_data:
            expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])

        sso_session = SSOSession(
            session_id=session_id,
            user_id=sso_user.user_id,
            provider_id=sso_user.provider_id,
            expires_at=expires_at,
            session_data=token_data,
            active=True,
        )

        db.add(sso_session)
        db.commit()

        return sso_session


# OAuth provider configurations
OAUTH_PROVIDER_CONFIGS = {
    SSOProviderType.OAUTH_GOOGLE: {
        "name": "Google",
        "icon": "google",
        "color": "#4285f4",
        "scope": "openid email profile",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
    },
    SSOProviderType.OAUTH_MICROSOFT: {
        "name": "Microsoft",
        "icon": "microsoft",
        "color": "#0078d4",
        "scope": "openid email profile",
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
    },
    SSOProviderType.OAUTH_GITHUB: {
        "name": "GitHub",
        "icon": "github",
        "color": "#333333",
        "scope": "user:email",
        "userinfo_url": "https://api.github.com/user",
    },
}
