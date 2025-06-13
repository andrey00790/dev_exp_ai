# User Management API
"""
API роутер для управления пользователями
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Заглушка для UserConfigManager
class MockUserConfigManager:
    def create_user_with_defaults(self, username: str, email: str) -> int:
        return 1
    
    def get_user_config(self, user_id: int):
        return MockUserConfig(user_id, "test_user", "test@example.com", {})
    
    def get_user_data_sources(self, user_id: int):
        return [
            {
                "source_type": "jira",
                "source_name": "default",
                "is_enabled_semantic_search": True,
                "is_enabled_architecture_generation": True
            },
            {
                "source_type": "confluence", 
                "source_name": "default",
                "is_enabled_semantic_search": True,
                "is_enabled_architecture_generation": True
            },
            {
                "source_type": "gitlab",
                "source_name": "default",
                "is_enabled_semantic_search": True,
                "is_enabled_architecture_generation": True
            },
            {
                "source_type": "user_files",
                "source_name": "default",
                "is_enabled_semantic_search": False,
                "is_enabled_architecture_generation": True
            }
        ]
    
    def update_data_source_config(self, user_id: int, source_type: str, source_name: str,
                                  is_enabled_semantic_search: bool, is_enabled_architecture_generation: bool):
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

def get_user_config_manager():
    return MockUserConfigManager()

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    config_manager = Depends(get_user_config_manager)
):
    """Создание нового пользователя"""
    try:
        user_id = config_manager.create_user_with_defaults(
            username=request.username,
            email=request.email
        )
        
        return UserResponse(
            id=user_id,
            username=request.username,
            email=request.email
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    config_manager = Depends(get_user_config_manager)
):
    """Получение пользователя по ID"""
    try:
        user_config = config_manager.get_user_config(user_id)
        if not user_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user_config.user_id,
            username=user_config.username,
            email=user_config.email
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )

@router.get("/users/current/settings", response_model=UserSettings)
async def get_user_settings(
    user_id: int = 1,
    config_manager = Depends(get_user_config_manager)
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
                    is_enabled_architecture_generation=ds["is_enabled_architecture_generation"]
                ) for ds in data_sources
            ],
            preferences={
                "language": "en",
                "theme": "light",
                "default_doc_type": "readme"
            }
        )
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user settings: {str(e)}"
        )

@router.put("/users/current/settings", response_model=UserSettings)
async def update_user_settings(
    request: UpdateUserSettingsRequest,
    user_id: int = 1,
    config_manager = Depends(get_user_config_manager)
):
    """Обновление настроек пользователя"""
    try:
        # Обновляем источники данных
        if request.data_sources:
            for ds in request.data_sources:
                config_manager.update_data_source_config(
                    user_id=user_id,
                    source_type=ds.source_type,
                    source_name=ds.source_name,
                    is_enabled_semantic_search=ds.is_enabled_semantic_search,
                    is_enabled_architecture_generation=ds.is_enabled_architecture_generation
                )
        
        # Обновляем preferences (заглушка)
        if request.preferences:
            logger.info(f"Updated preferences for user {user_id}: {request.preferences}")
        
        # Возвращаем обновленные настройки
        return await get_user_settings(user_id, config_manager)
        
    except Exception as e:
        logger.error(f"Error updating user settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user settings: {str(e)}"
        )
