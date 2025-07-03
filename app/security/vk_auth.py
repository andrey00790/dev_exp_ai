"""
VK OAuth authentication service.
Handles VK OAuth flow and user validation.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import httpx
import logging
from urllib.parse import urlencode
import yaml
import os

from requests_oauth2client import OAuth2Client
from app.config import get_settings
from app.core.exceptions import VKOAuthError, VKUserNotAllowedError
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class VKUserInfo:
    """VK user information from OAuth"""
    user_id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    photo_url: Optional[str] = None
    username: Optional[str] = None


class VKAuthService:
    """Service for VK OAuth authentication and user validation"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: Optional[str] = None
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri or settings.VK_OAUTH_REDIRECT_URI
        
        # Initialize OAuth2 client
        self.oauth_client = OAuth2Client(
            authorization_endpoint="https://oauth.vk.com/authorize",
            token_endpoint="https://oauth.vk.com/access_token",
            client_id=self.client_id,
            client_secret=self.client_secret,
        )

    async def exchange_code_for_user_info(self, authorization_code: str) -> VKUserInfo:
        """
        Exchange authorization code for access token and get user info.
        """
        try:
            # Exchange code for access token
            token_data = await self._exchange_code_for_token(authorization_code)
            access_token = token_data.get("access_token")
            vk_user_id = token_data.get("user_id")
            
            if not access_token or not vk_user_id:
                raise VKOAuthError("Failed to get access token or user ID from VK")
            
            # Get user information
            user_info = await self._get_user_info(access_token, vk_user_id)
            
            return VKUserInfo(
                user_id=str(vk_user_id),
                first_name=user_info.get("first_name", ""),
                last_name=user_info.get("last_name", ""),
                email=user_info.get("email"),
                photo_url=user_info.get("photo_200_orig"),
                username=user_info.get("screen_name")
            )
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during VK OAuth: {e}")
            raise VKOAuthError(f"HTTP error: {e}")
        except Exception as e:
            logger.error(f"Error exchanging VK code for user info: {e}")
            raise VKOAuthError(f"Failed to get user info: {e}")

    async def _exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        url = "https://oauth.vk.com/access_token"
        
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=params)
            response.raise_for_status()
            
            data = await response.json()
            
            if "error" in data:
                error_msg = data.get("error_description", data.get("error"))
                raise VKOAuthError(f"VK token exchange error: {error_msg}")
            
            return data

    async def _get_user_info(self, access_token: str, user_id: str) -> Dict[str, Any]:
        """Get user information from VK API"""
        url = "https://api.vk.com/method/users.get"
        
        params = {
            "access_token": access_token,
            "user_ids": user_id,
            "fields": "email,screen_name,photo_200_orig",
            "v": "5.131"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = await response.json()
            
            if "error" in data:
                error_msg = data["error"].get("error_msg", "Unknown VK API error")
                raise VKOAuthError(f"VK API error: {error_msg}")
            
            users = data.get("response", [])
            if not users:
                raise VKOAuthError("No user data returned from VK API")
            
            return users[0]

    def is_user_allowed(self, vk_user_id: str) -> bool:
        """Check if VK user is in the allowed list"""
        allowed_users = self._get_allowed_vk_users()
        return str(vk_user_id) in allowed_users

    def _get_allowed_vk_users(self) -> List[str]:
        """Get allowed VK users from configuration"""
        # Try to get from environment variable first
        if hasattr(settings, 'ALLOWED_VK_USERS') and settings.ALLOWED_VK_USERS:
            if isinstance(settings.ALLOWED_VK_USERS, str):
                # Parse comma-separated string
                return [user.strip() for user in settings.ALLOWED_VK_USERS.split(',') if user.strip()]
            elif isinstance(settings.ALLOWED_VK_USERS, list):
                return [str(user) for user in settings.ALLOWED_VK_USERS]
        
        # Try to load from YAML config file
        config_path = os.path.join(os.getcwd(), "config", "vk_users.yml")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return [str(user) for user in config.get('allowed_vk_users', [])]
            except Exception as e:
                logger.warning(f"Failed to load VK users config from {config_path}: {e}")
        
        # Fallback to empty list
        logger.warning("No allowed VK users configured. All users will be denied access.")
        return []

    async def find_or_create_user(self, db: AsyncSession, vk_user_info: VKUserInfo) -> User:
        """Find existing user or create new one based on VK user info"""
        try:
            # Try to find user by VK user ID
            stmt = select(User).where(User.vk_user_id == vk_user_info.user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                # Update user info if needed
                updated = False
                if user.first_name != vk_user_info.first_name:
                    user.first_name = vk_user_info.first_name
                    updated = True
                if user.last_name != vk_user_info.last_name:
                    user.last_name = vk_user_info.last_name
                    updated = True
                if vk_user_info.email and user.email != vk_user_info.email:
                    user.email = vk_user_info.email
                    updated = True
                
                if updated:
                    await db.commit()
                    await db.refresh(user)
                
                return user
            
            # Create new user
            user_data = {
                "vk_user_id": vk_user_info.user_id,
                "first_name": vk_user_info.first_name,
                "last_name": vk_user_info.last_name,
                "username": vk_user_info.username or f"vk_{vk_user_info.user_id}",
                "email": vk_user_info.email,
                "is_active": True,
                "oauth_provider": "vk"
            }
            
            user = User(**user_data)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"Created new user for VK user {vk_user_info.user_id}")
            return user
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error finding/creating user for VK user {vk_user_info.user_id}: {e}")
            raise VKOAuthError(f"Failed to create/find user: {e}")

    async def validate_vk_user_access(self, vk_user_id: str) -> bool:
        """
        Validate that VK user has access to the application.
        This method can be used by VK Teams bot.
        """
        if not self.is_user_allowed(vk_user_id):
            raise VKUserNotAllowedError(vk_user_id)
        return True 