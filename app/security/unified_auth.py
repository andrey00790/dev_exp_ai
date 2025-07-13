"""
Unified Authentication Service for VK Teams Integration

Поддерживает:
- Email/password авторизацию
- VK OAuth авторизацию
- Связывание VK ID с внутренними пользователями
- Единую модель пользователя для всех систем
"""

import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr

from app.security.auth import USERS_DB, User, create_access_token, verify_password, get_password_hash
from app.security.vk_auth import VKAuthService, VKUserInfo
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthResult(BaseModel):
    """Результат аутентификации"""
    user: User
    access_token: str
    auth_provider: str  # "email", "vk_oauth", "vk_teams"
    is_new_user: bool = False


class UnifiedAuthService:
    """Единый сервис авторизации для всех провайдеров"""
    
    def __init__(self):
        self.vk_auth_service = None
        if settings.vk_oauth_enabled:
            self.vk_auth_service = VKAuthService(
                client_id=settings.vk_oauth_client_id,
                client_secret=settings.vk_oauth_client_secret,
                redirect_uri=settings.vk_oauth_redirect_uri
            )
    
    async def authenticate_email_password(self, email: str, password: str) -> Optional[AuthResult]:
        """Авторизация по email/password"""
        try:
            user_data = USERS_DB.get(email)
            if not user_data:
                return None
            
            if not verify_password(password, user_data["hashed_password"]):
                return None
            
            if not user_data.get("is_active", True):
                return None
            
            # Создаем объект User
            user = self._create_user_from_dict(user_data)
            
            # Создаем токен
            token_data = {
                "sub": user.user_id,
                "email": user.email,
                "scopes": user.scopes,
                "auth_provider": "email"
            }
            access_token = create_access_token(data=token_data)
            
            logger.info(f"✅ Email authentication successful: {email}")
            
            return AuthResult(
                user=user,
                access_token=access_token,
                auth_provider="email",
                is_new_user=False
            )
            
        except Exception as e:
            logger.error(f"❌ Email authentication failed for {email}: {e}")
            return None
    
    async def authenticate_vk_oauth(self, authorization_code: str) -> Optional[AuthResult]:
        """Авторизация через VK OAuth"""
        if not self.vk_auth_service:
            logger.error("VK OAuth service not configured")
            return None
        
        try:
            # Получаем информацию о VK пользователе
            vk_user_info = await self.vk_auth_service.exchange_code_for_user_info(authorization_code)
            
            # Проверяем права доступа
            if not self.vk_auth_service.is_user_allowed(vk_user_info.user_id):
                logger.warning(f"VK user {vk_user_info.user_id} not allowed")
                return None
            
            # Ищем или создаем пользователя
            user, is_new = await self._find_or_create_vk_user(vk_user_info)
            
            # Создаем токен
            token_data = {
                "sub": user.user_id,
                "email": user.email,
                "scopes": user.scopes,
                "auth_provider": "vk_oauth",
                "vk_user_id": user.vk_user_id
            }
            access_token = create_access_token(data=token_data)
            
            logger.info(f"✅ VK OAuth authentication successful: {vk_user_info.user_id}")
            
            return AuthResult(
                user=user,
                access_token=access_token,
                auth_provider="vk_oauth",
                is_new_user=is_new
            )
            
        except Exception as e:
            logger.error(f"❌ VK OAuth authentication failed: {e}")
            return None
    
    async def authenticate_vk_teams_user(self, vk_user_id: str) -> Optional[User]:
        """Авторизация пользователя VK Teams по VK ID"""
        try:
            # Проверяем права доступа
            if self.vk_auth_service and not self.vk_auth_service.is_user_allowed(vk_user_id):
                logger.warning(f"VK Teams user {vk_user_id} not allowed")
                return None
            
            # Ищем пользователя по VK ID
            user = self._find_user_by_vk_id(vk_user_id)
            
            if user:
                logger.info(f"✅ VK Teams user found: {vk_user_id}")
                return user
            
            # Если пользователь не найден, создаем временного для VK Teams
            user = await self._create_vk_teams_user(vk_user_id)
            logger.info(f"✅ VK Teams temporary user created: {vk_user_id}")
            
            return user
            
        except Exception as e:
            logger.error(f"❌ VK Teams authentication failed for {vk_user_id}: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Получение пользователя по ID"""
        for email, user_data in USERS_DB.items():
            if user_data.get("user_id") == user_id:
                return self._create_user_from_dict(user_data)
        return None
    
    def get_user_by_vk_id(self, vk_user_id: str) -> Optional[User]:
        """Получение пользователя по VK ID"""
        return self._find_user_by_vk_id(vk_user_id)
    
    async def link_vk_account(self, user_id: str, vk_user_info: VKUserInfo) -> bool:
        """Связывание VK аккаунта с существующим пользователем"""
        try:
            # Находим пользователя
            user_data = None
            email = None
            for email_key, data in USERS_DB.items():
                if data.get("user_id") == user_id:
                    user_data = data
                    email = email_key
                    break
            
            if not user_data:
                return False
            
            # Обновляем данные VK
            user_data.update({
                "vk_user_id": vk_user_info.user_id,
                "oauth_provider": "vk",
                "external_user_id": vk_user_info.user_id,
                "first_name": vk_user_info.first_name,
                "last_name": vk_user_info.last_name,
                "avatar_url": vk_user_info.photo_url
            })
            
            logger.info(f"✅ VK account linked: {user_id} -> {vk_user_info.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to link VK account: {e}")
            return False
    
    def _create_user_from_dict(self, user_data: Dict[str, Any]) -> User:
        """Создание объекта User из словаря"""
        return User(
            user_id=user_data.get("user_id", ""),
            email=user_data.get("email", ""),
            name=user_data.get("name", ""),
            is_active=user_data.get("is_active", True),
            scopes=user_data.get("scopes", ["basic"]),
            budget_limit=user_data.get("budget_limit", 100.0),
            current_usage=user_data.get("current_usage", 0.0),
            vk_user_id=user_data.get("vk_user_id"),
            oauth_provider=user_data.get("oauth_provider"),
            external_user_id=user_data.get("external_user_id"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            avatar_url=user_data.get("avatar_url")
        )
    
    def _find_user_by_vk_id(self, vk_user_id: str) -> Optional[User]:
        """Поиск пользователя по VK ID"""
        for email, user_data in USERS_DB.items():
            if user_data.get("vk_user_id") == vk_user_id:
                return self._create_user_from_dict(user_data)
        return None
    
    async def _find_or_create_vk_user(self, vk_user_info: VKUserInfo) -> tuple[User, bool]:
        """Поиск или создание пользователя по VK данным"""
        # Сначала ищем по VK ID
        user = self._find_user_by_vk_id(vk_user_info.user_id)
        if user:
            return user, False
        
        # Ищем по email если есть
        if vk_user_info.email:
            user_data = USERS_DB.get(vk_user_info.email)
            if user_data:
                # Обновляем существующего пользователя VK данными
                user_data.update({
                    "vk_user_id": vk_user_info.user_id,
                    "oauth_provider": "vk",
                    "external_user_id": vk_user_info.user_id,
                    "first_name": vk_user_info.first_name,
                    "last_name": vk_user_info.last_name,
                    "avatar_url": vk_user_info.photo_url
                })
                return self._create_user_from_dict(user_data), False
        
        # Создаем нового пользователя
        return await self._create_new_vk_user(vk_user_info), True
    
    async def _create_new_vk_user(self, vk_user_info: VKUserInfo) -> User:
        """Создание нового пользователя из VK данных"""
        user_id = f"vk_{vk_user_info.user_id}"
        
        # Определяем email - используем VK email или создаем временный
        email = vk_user_info.email or f"vk_{vk_user_info.user_id}@vk.temp"
        
        # Создаем запись пользователя
        user_data = {
            "user_id": user_id,
            "email": email,
            "name": f"{vk_user_info.first_name} {vk_user_info.last_name}".strip(),
            "hashed_password": get_password_hash("vk_oauth_user"),  # Заглушка
            "is_active": True,
            "scopes": ["basic", "vk_user"],
            "budget_limit": 1000.0,  # Базовый лимит для VK пользователей
            "current_usage": 0.0,
            "vk_user_id": vk_user_info.user_id,
            "oauth_provider": "vk",
            "external_user_id": vk_user_info.user_id,
            "first_name": vk_user_info.first_name,
            "last_name": vk_user_info.last_name,
            "avatar_url": vk_user_info.photo_url
        }
        
        # Сохраняем в базу
        USERS_DB[email] = user_data
        
        logger.info(f"✅ Created new VK user: {vk_user_info.user_id}")
        
        return self._create_user_from_dict(user_data)
    
    async def _create_vk_teams_user(self, vk_user_id: str) -> User:
        """Создание временного пользователя для VK Teams"""
        user_id = f"vk_teams_{vk_user_id}"
        email = f"vk_teams_{vk_user_id}@vk.temp"
        
        user_data = {
            "user_id": user_id,
            "email": email,
            "name": f"VK Teams User {vk_user_id}",
            "hashed_password": get_password_hash("vk_teams_temp_user"),
            "is_active": True,
            "scopes": ["basic", "vk_teams"],
            "budget_limit": 500.0,  # Базовый лимит для VK Teams
            "current_usage": 0.0,
            "vk_user_id": vk_user_id,
            "oauth_provider": "vk_teams",
            "external_user_id": vk_user_id,
            "first_name": "VK Teams",
            "last_name": f"User {vk_user_id}"
        }
        
        # Сохраняем временного пользователя
        USERS_DB[email] = user_data
        
        return self._create_user_from_dict(user_data)


# Глобальный экземпляр сервиса
unified_auth_service = UnifiedAuthService()


# Функции для обратной совместимости
async def authenticate_user_unified(email: str, password: str) -> Optional[User]:
    """Универсальная аутентификация"""
    result = await unified_auth_service.authenticate_email_password(email, password)
    return result.user if result else None


async def authenticate_vk_user(vk_user_id: str) -> Optional[User]:
    """Аутентификация VK пользователя для VK Teams"""
    return await unified_auth_service.authenticate_vk_teams_user(vk_user_id)


def get_user_by_vk_id(vk_user_id: str) -> Optional[User]:
    """Получение пользователя по VK ID"""
    return unified_auth_service.get_user_by_vk_id(vk_user_id) 