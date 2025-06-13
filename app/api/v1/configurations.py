# Configuration API Router
"""
Configuration Management API
API роутер для управления конфигурациями внешних систем
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Модели данных
class JiraConfigRequest(BaseModel):
    config_name: str
    jira_url: str
    username: str
    password: str
    projects: Optional[List[str]] = []
    is_default: bool = False

class ConfluenceConfigRequest(BaseModel):
    config_name: str
    confluence_url: str
    bearer_token: str
    spaces: Optional[List[str]] = []
    is_default: bool = False

class GitLabConfigRequest(BaseModel):
    alias: str
    gitlab_url: str
    access_token: str
    projects: Optional[List[str]] = []

class ConfigResponse(BaseModel):
    id: int
    config_name: str
    url: str
    is_default: bool = False

# Mock конфигурации
class MockConfigManager:
    def add_jira_config(self, user_id: int, config_name: str, jira_url: str, 
                       username: str, password: str, projects: List[str] = None):
        logger.info(f"Added Jira config '{config_name}' for user {user_id}")
        return {"id": 1, "config_name": config_name, "url": jira_url}
    
    def get_jira_configs(self, user_id: int):
        return [{"id": 1, "config_name": "default", "url": "https://jira.company.com", "is_default": True}]

def get_config_manager():
    return MockConfigManager()

@router.post("/configurations/jira", response_model=ConfigResponse)
async def create_jira_config(
    request: JiraConfigRequest,
    user_id: int = 1,
    config_manager = Depends(get_config_manager)
):
    """Создание конфигурации Jira"""
    try:
        result = config_manager.add_jira_config(
            user_id=user_id,
            config_name=request.config_name,
            jira_url=request.jira_url,
            username=request.username,
            password=request.password,
            projects=request.projects
        )
        
        return ConfigResponse(
            id=result["id"],
            config_name=result["config_name"],
            url=result["url"],
            is_default=request.is_default
        )
    except Exception as e:
        logger.error(f"Error creating Jira config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Jira configuration: {str(e)}"
        )

@router.get("/configurations/jira", response_model=List[ConfigResponse])
async def get_jira_configs(
    user_id: int = 1,
    config_manager = Depends(get_config_manager)
):
    """Получение конфигураций Jira пользователя"""
    try:
        configs = config_manager.get_jira_configs(user_id)
        return [
            ConfigResponse(
                id=config["id"],
                config_name=config["config_name"],
                url=config["url"],
                is_default=config["is_default"]
            ) for config in configs
        ]
    except Exception as e:
        logger.error(f"Error getting Jira configs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Jira configurations: {str(e)}"
        )
