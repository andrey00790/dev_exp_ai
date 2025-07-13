"""
SAML 2.0 Authentication Handler

Provides SAML 2.0 SSO authentication functionality including:
- SAML assertion validation
- User attribute mapping
- Session management
- Single Logout (SLO) support
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

try:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.errors import OneLogin_Saml2_Error
    from onelogin.saml2.settings import OneLogin_Saml2_Settings
    from onelogin.saml2.utils import OneLogin_Saml2_Utils

    SAML_AVAILABLE = True
except ImportError:
    SAML_AVAILABLE = False
    OneLogin_Saml2_Auth = None
    OneLogin_Saml2_Settings = None
    OneLogin_Saml2_Utils = None
    OneLogin_Saml2_Error = Exception

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_password_hash
from .models import SSOProvider, SSOProviderType, SSOSession, SSOUser

logger = logging.getLogger(__name__)


class SAMLAuthHandler:
    """Handles SAML 2.0 authentication flows"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        if not SAML_AVAILABLE:
            logger.warning("python-saml not available. SAML authentication disabled.")

    def is_available(self) -> bool:
        """Check if SAML authentication is available"""
        return SAML_AVAILABLE

    def build_saml_settings(self, provider: SSOProvider) -> Dict[str, Any]:
        """Build SAML settings from provider configuration"""
        if not self.is_available():
            raise HTTPException(status_code=500, detail="SAML not available")

        # Base URLs for this application
        acs_url = f"{self.base_url}/api/v1/auth/sso/saml/{provider.id}/acs"
        sls_url = f"{self.base_url}/api/v1/auth/sso/saml/{provider.id}/sls"
        metadata_url = f"{self.base_url}/api/v1/auth/sso/saml/{provider.id}/metadata"

        settings = {
            "sp": {
                "entityId": f"{self.base_url}/saml/metadata",
                "assertionConsumerService": {
                    "url": acs_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
                "singleLogoutService": {
                    "url": sls_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                "x509cert": "",
                "privateKey": "",
            },
            "idp": {
                "entityId": provider.entity_id,
                "singleSignOnService": {
                    "url": provider.sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "singleLogoutService": {
                    "url": provider.slo_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": provider.x509_cert or "",
            },
        }

        # Merge with provider-specific config
        if provider.config:
            settings.update(provider.config)

        return settings

    def init_saml_auth(
        self, request: Request, provider: SSOProvider
    ) -> OneLogin_Saml2_Auth:
        """Initialize SAML Auth object"""
        if not self.is_available():
            raise HTTPException(status_code=500, detail="SAML not available")

        # Convert FastAPI request to format expected by python-saml
        url_data = urlparse(str(request.url))
        saml_request = {
            "https": "on" if url_data.scheme == "https" else "off",
            "http_host": url_data.hostname,
            "server_port": (
                str(url_data.port)
                if url_data.port
                else ("443" if url_data.scheme == "https" else "80")
            ),
            "script_name": request.url.path,
            "get_data": dict(request.query_params),
            "post_data": {},
        }

        # Add POST data if available
        if hasattr(request, "_body") and request._body:
            try:
                # Try to parse form data
                import urllib.parse

                saml_request["post_data"] = urllib.parse.parse_qs(
                    request._body.decode()
                )
            except Exception as e:
                logger.warning(f"Failed to parse POST data: {e}")

        settings = self.build_saml_settings(provider)
        return OneLogin_Saml2_Auth(saml_request, settings)

    async def initiate_login(self, request: Request, provider: SSOProvider) -> str:
        """Initiate SAML login flow"""
        try:
            auth = self.init_saml_auth(request, provider)
            return auth.login()
        except Exception as e:
            logger.error(f"SAML login initiation failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to initiate SAML login")

    async def handle_acs_response(
        self, request: Request, provider: SSOProvider, db: Session
    ) -> Tuple[Dict[str, Any], str]:
        """Handle SAML ACS (Assertion Consumer Service) response"""
        try:
            auth = self.init_saml_auth(request, provider)
            auth.process_response()

            errors = auth.get_errors()
            if errors:
                logger.error(f"SAML authentication errors: {errors}")
                raise HTTPException(
                    status_code=400,
                    detail=f"SAML authentication failed: {'; '.join(errors)}",
                )

            if not auth.is_authenticated():
                raise HTTPException(
                    status_code=401, detail="SAML authentication failed"
                )

            # Extract user attributes
            attributes = auth.get_attributes()
            nameid = auth.get_nameid()
            session_index = auth.get_session_index()

            logger.info(f"SAML authentication successful for user: {nameid}")

            # Map SAML attributes to user data
            user_data = self._map_saml_attributes(attributes, nameid)

            # Find or create SSO user
            sso_user = await self._find_or_create_sso_user(
                db, provider, nameid, user_data, session_index
            )

            # Generate JWT token
            access_token = create_access_token(data={"sub": str(sso_user.user_id)})

            return user_data, access_token

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"SAML ACS handling failed: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to process SAML response"
            )

    async def handle_sls_request(
        self, request: Request, provider: SSOProvider, db: Session
    ) -> Optional[str]:
        """Handle SAML SLS (Single Logout Service) request"""
        try:
            auth = self.init_saml_auth(request, provider)
            url = auth.process_slo(
                delete_session_cb=lambda: self._delete_saml_session(
                    db, auth.get_nameid()
                )
            )

            errors = auth.get_errors()
            if errors:
                logger.error(f"SAML logout errors: {errors}")
                return None

            return url

        except Exception as e:
            logger.error(f"SAML SLS handling failed: {e}")
            return None

    async def get_metadata(self, provider: SSOProvider) -> str:
        """Generate SAML metadata for this SP"""
        try:
            settings = self.build_saml_settings(provider)
            saml_settings = OneLogin_Saml2_Settings(settings)
            metadata = saml_settings.get_sp_metadata()

            errors = saml_settings.check_sp_settings()
            if errors:
                logger.warning(f"SAML metadata warnings: {errors}")

            return metadata

        except Exception as e:
            logger.error(f"SAML metadata generation failed: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to generate SAML metadata"
            )

    def _map_saml_attributes(
        self, attributes: Dict[str, Any], nameid: str
    ) -> Dict[str, Any]:
        """Map SAML attributes to user data"""
        # Common SAML attribute mappings
        attr_mapping = {
            "email": [
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
                "email",
                "mail",
            ],
            "first_name": [
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
                "givenName",
                "firstName",
            ],
            "last_name": [
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname",
                "sn",
                "surname",
                "lastName",
            ],
            "display_name": [
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
                "displayName",
                "cn",
            ],
            "groups": ["http://schemas.xmlsoap.org/claims/Group", "groups", "memberOf"],
        }

        user_data = {
            "external_user_id": nameid,
            "external_email": nameid,  # Default to nameid if email not found
            "external_name": nameid,
            "external_groups": [],
            "external_attributes": attributes,
        }

        # Map known attributes
        for user_field, saml_attrs in attr_mapping.items():
            for saml_attr in saml_attrs:
                if saml_attr in attributes and attributes[saml_attr]:
                    value = attributes[saml_attr]
                    if isinstance(value, list) and value:
                        user_data[f"external_{user_field}"] = (
                            value[0] if user_field != "groups" else value
                        )
                    elif not isinstance(value, list):
                        user_data[f"external_{user_field}"] = value
                    break

        # Build full name if not provided
        if user_data.get("external_name") == nameid:
            first = user_data.get("external_first_name", "")
            last = user_data.get("external_last_name", "")
            if first or last:
                user_data["external_name"] = f"{first} {last}".strip()

        return user_data

    async def _find_or_create_sso_user(
        self,
        db: Session,
        provider: SSOProvider,
        external_user_id: str,
        user_data: Dict[str, Any],
        session_index: Optional[str] = None,
    ) -> SSOUser:
        """Find existing SSO user or create new one"""
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
            sso_user.external_groups = user_data.get("external_groups")
            sso_user.external_attributes = user_data.get("external_attributes")
            sso_user.last_sso_login = datetime.now(timezone.utc)
            sso_user.sso_session_id = session_index
            db.commit()
            return sso_user

        # Create new user in main users table first
        from ...models.user import User  # Assuming we have a User model

        user = User(
            email=user_data.get(
                "external_email", f"{external_user_id}@{provider.name}"
            ),
            username=user_data.get("external_name", external_user_id),
            hashed_password=get_password_hash(
                "sso_user_no_password"
            ),  # SSO users don't need passwords
            is_active=True,
            is_sso_user=True,
        )
        db.add(user)
        db.flush()  # Get the user ID

        # Create SSO user mapping
        sso_user = SSOUser(
            user_id=user.id,
            provider_id=provider.id,
            external_user_id=external_user_id,
            external_email=user_data.get("external_email"),
            external_name=user_data.get("external_name"),
            external_groups=user_data.get("external_groups"),
            external_attributes=user_data.get("external_attributes"),
            last_sso_login=datetime.now(timezone.utc),
            sso_session_id=session_index,
            active=True,
        )
        db.add(sso_user)
        db.commit()

        logger.info(
            f"Created new SSO user: {external_user_id} for provider: {provider.name}"
        )
        return sso_user

    def _delete_saml_session(self, db: Session, nameid: str):
        """Delete SAML session (callback for SLO)"""
        try:
            # Find and deactivate SSO sessions
            sso_sessions = (
                db.query(SSOSession)
                .join(SSOUser)
                .filter(SSOUser.external_user_id == nameid, SSOSession.active == True)
                .all()
            )

            for session in sso_sessions:
                session.active = False
                session.logout_reason = "slo"

            db.commit()
            logger.info(f"Deleted SAML sessions for user: {nameid}")

        except Exception as e:
            logger.error(f"Failed to delete SAML session: {e}")
            db.rollback()


# SAML configuration templates
SAML_CONFIG_TEMPLATES = {
    "azure_ad": {
        "entity_id": "https://sts.windows.net/{tenant_id}/",
        "sso_url": "https://login.microsoftonline.com/{tenant_id}/saml2",
        "slo_url": "https://login.microsoftonline.com/{tenant_id}/saml2",
        "name_id_format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
    },
    "okta": {
        "entity_id": "http://www.okta.com/{okta_org}",
        "sso_url": "https://{okta_org}.okta.com/app/{app_id}/sso/saml",
        "slo_url": "https://{okta_org}.okta.com/app/{app_id}/slo/saml",
        "name_id_format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
    },
    "google": {
        "entity_id": "https://accounts.google.com/o/saml2?idpid={idp_id}",
        "sso_url": "https://accounts.google.com/o/saml2/idp?idpid={idp_id}",
        "slo_url": "https://accounts.google.com/logout",
        "name_id_format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
    },
}
