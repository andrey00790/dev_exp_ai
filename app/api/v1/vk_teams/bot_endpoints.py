"""
VK Teams Bot Management API

API endpoints для управления VK Teams ботом:
- Статус бота
- Настройки бота
- Статистика использования
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.security.auth import get_current_user
from domain.vk_teams.bot_service import VKTeamsBotService, get_vk_teams_bot_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vk-teams/bot", tags=["VK Teams Bot Management"])


class BotStatusResponse(BaseModel):
    """Ответ статуса бота"""
    is_active: bool
    bot_id: Optional[str] = None
    bot_name: Optional[str] = None
    webhook_url: Optional[str] = None
    last_activity: Optional[str] = None
    stats: Dict[str, Any] = {}


class BotConfigRequest(BaseModel):
    """Запрос настройки бота"""
    bot_token: str
    api_url: str
    webhook_url: Optional[str] = None
    auto_start: bool = True
    allowed_users: Optional[List[str]] = None
    allowed_chats: Optional[List[str]] = None


class BotConfigResponse(BaseModel):
    """Ответ настройки бота"""
    success: bool
    message: str
    config: Dict[str, Any] = {}


@router.get("/status", response_model=BotStatusResponse)
async def get_bot_status(
    current_user: dict = Depends(get_current_user),
    bot_service: VKTeamsBotService = Depends(get_vk_teams_bot_service)
) -> BotStatusResponse:
    """
    Получить статус VK Teams бота
    
    Возвращает информацию о текущем состоянии бота:
    - Активен ли бот
    - Информация о боте
    - Статистика использования
    """
    try:
        status_info = await bot_service.get_bot_status()
        
        return BotStatusResponse(
            is_active=status_info.get("is_active", False),
            bot_id=status_info.get("bot_id"),
            bot_name=status_info.get("bot_name"),
            webhook_url=status_info.get("webhook_url"),
            last_activity=status_info.get("last_activity"),
            stats=status_info.get("stats", {})
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса бота: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения статуса бота: {str(e)}"
        )


@router.post("/configure", response_model=BotConfigResponse)
async def configure_bot(
    config: BotConfigRequest,
    current_user: dict = Depends(get_current_user),
    bot_service: VKTeamsBotService = Depends(get_vk_teams_bot_service)
) -> BotConfigResponse:
    """
    Настроить VK Teams бота
    
    Конфигурирует бота с указанными параметрами:
    - Токен бота
    - API URL
    - Webhook URL
    - Настройки доступа
    """
    try:
        # Проверяем права администратора
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только администраторы могут настраивать бота"
            )
        
        result = await bot_service.configure_bot(
            bot_token=config.bot_token,
            api_url=config.api_url,
            webhook_url=config.webhook_url,
            auto_start=config.auto_start,
            allowed_users=config.allowed_users,
            allowed_chats=config.allowed_chats
        )
        
        return BotConfigResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            config=result.get("config", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка настройки бота: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка настройки бота: {str(e)}"
        )


@router.post("/start")
async def start_bot(
    current_user: dict = Depends(get_current_user),
    bot_service: VKTeamsBotService = Depends(get_vk_teams_bot_service)
) -> Dict[str, Any]:
    """
    Запустить VK Teams бота
    
    Активирует бота для обработки сообщений
    """
    try:
        # Проверяем права администратора
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только администраторы могут управлять ботом"
            )
        
        result = await bot_service.start_bot()
        
        return {
            "success": True,
            "message": "Бот успешно запущен",
            "details": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка запуска бота: {str(e)}"
        )


@router.post("/stop")
async def stop_bot(
    current_user: dict = Depends(get_current_user),
    bot_service: VKTeamsBotService = Depends(get_vk_teams_bot_service)
) -> Dict[str, Any]:
    """
    Остановить VK Teams бота
    
    Деактивирует бота
    """
    try:
        # Проверяем права администратора
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только администраторы могут управлять ботом"
            )
        
        result = await bot_service.stop_bot()
        
        return {
            "success": True,
            "message": "Бот успешно остановлен",
            "details": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка остановки бота: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка остановки бота: {str(e)}"
        )


@router.get("/stats")
async def get_bot_stats(
    current_user: dict = Depends(get_current_user),
    bot_service: VKTeamsBotService = Depends(get_vk_teams_bot_service)
) -> Dict[str, Any]:
    """
    Получить статистику бота
    
    Возвращает статистику использования бота
    """
    try:
        stats = await bot_service.get_bot_statistics()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения статистики: {str(e)}"
        )


@router.get("/health")
async def bot_health_check(
    bot_service: VKTeamsBotService = Depends(get_vk_teams_bot_service)
) -> Dict[str, Any]:
    """
    Проверка здоровья VK Teams бота
    
    Endpoint для мониторинга состояния бота
    """
    try:
        health = await bot_service.health_check()
        
        return {
            "status": "healthy" if health.get("is_healthy") else "unhealthy",
            "details": health,
            "timestamp": health.get("timestamp")
        }
        
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья бота: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": None
        } 