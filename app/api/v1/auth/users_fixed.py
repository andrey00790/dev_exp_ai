# User Management API (Fixed Version)
"""
API роутер для управления пользователями с исправленной валидацией
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)
router = APIRouter()


# Исправленная заглушка для UserConfigManager с валидацией
class MockUserConfigManager:
    def __init__(self):
        # Симуляция базы данных пользователей
        self.users_db: Dict[int, Dict] = {}
        self.emails_db: Dict[str, int] = {}  # email -> user_id mapping
        self.next_user_id = 1

    def create_user_with_defaults(self, username: str, email: str) -> int:
        # Проверяем дублирующийся email
        if email in self.emails_db:
            raise ValueError(f"User with email {email} already exists")

        user_id = self.next_user_id
        self.next_user_id += 1

        # Сохраняем пользователя
        self.users_db[user_id] = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "is_active": True,
        }
        self.emails_db[email] = user_id

        return user_id

    def get_user_config(self, user_id: int):
        user_data = self.users_db.get(user_id)
        if not user_data:
            return None
        return MockUserConfig(
            user_data["user_id"], user_data["username"], user_data["email"], {}
        )

    def get_user_data_sources(self, user_id: int):
        # Проверяем существование пользователя
        if user_id not in self.users_db:
            raise ValueError(f"User {user_id} not found")

        return [
            {
                "source_type": "jira",
                "source_name": "default",
                "is_enabled_semantic_search": True,
                "is_enabled_architecture_generation": True,
            },
            {
                "source_type": "confluence",
                "source_name": "default",
                "is_enabled_semantic_search": True,
                "is_enabled_architecture_generation": True,
            },
            {
                "source_type": "gitlab",
                "source_name": "default",
                "is_enabled_semantic_search": True,
                "is_enabled_architecture_generation": True,
            },
            {
                "source_type": "user_files",
                "source_name": "default",
                "is_enabled_semantic_search": False,
                "is_enabled_architecture_generation": True,
            },
        ]

    def update_data_source_config(
        self,
        user_id: int,
        source_type: str,
        source_name: str,
        is_enabled_semantic_search: bool,
        is_enabled_architecture_generation: bool,
    ):
        if user_id not in self.users_db:
            raise ValueError(f"User {user_id} not found")

        logger.info(f"Updated {source_type}:{source_name} for user {user_id}")
        return True


class MockUserConfig:
    def __init__(self, user_id: int, username: str, email: str, settings: dict):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.settings = settings


# Pydantic models
class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool = True


class DataSourceConfig(BaseModel):
    source_type: str
    source_name: str
    is_enabled_semantic_search: bool
    is_enabled_architecture_generation: bool


class UserSettings(BaseModel):
    data_sources: List[DataSourceConfig] = []
    preferences: dict = {}


class UpdateUserSettingsRequest(BaseModel):
    data_sources: Optional[List[DataSourceConfig]] = None
    preferences: Optional[dict] = None


# Глобальный экземпляр для сохранения состояния между запросами
_mock_user_manager = MockUserConfigManager()


def get_user_config_manager():
    return _mock_user_manager


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest, config_manager=Depends(get_user_config_manager)
):
    """Создание нового пользователя"""
    try:
        user_id = config_manager.create_user_with_defaults(
            username=request.username, email=request.email
        )

        return UserResponse(id=user_id, username=request.username, email=request.email)
    except ValueError as e:
        # Дублирующийся email или другая ошибка валидации
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, config_manager=Depends(get_user_config_manager)):
    """Получение пользователя по ID"""
    try:
        user_config = config_manager.get_user_config(user_id)
        if not user_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return UserResponse(
            id=user_config.user_id,
            username=user_config.username,
            email=user_config.email,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}",
        )


@router.get("/users/current/settings", response_model=UserSettings)
async def get_user_settings(
    user_id: int = 1, config_manager=Depends(get_user_config_manager)
):
    """Получение настроек пользователя"""
    try:
        data_sources = config_manager.get_user_data_sources(user_id)

        return UserSettings(
            data_sources=[
                DataSourceConfig(
                    source_type=ds["source_type"],
                    source_name=ds["source_name"],
                    is_enabled_semantic_search=ds["is_enabled_semantic_search"],
                    is_enabled_architecture_generation=ds[
                        "is_enabled_architecture_generation"
                    ],
                )
                for ds in data_sources
            ],
            preferences={
                "language": "en",
                "theme": "light",
                "default_doc_type": "readme",
            },
        )
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user settings: {str(e)}",
        )
