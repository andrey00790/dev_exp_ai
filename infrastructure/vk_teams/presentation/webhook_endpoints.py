"""
VK Teams Webhook API

Webhook endpoints для обработки событий от VK Teams:
- Получение сообщений
- Обработка команд
- Обработка кнопок
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from infrastructure.vk_teams.infrastructure.bot_adapter_simple import VKTeamsBotAdapter, get_vk_teams_bot_adapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vk-teams/webhook", tags=["VK Teams Webhook"])


class WebhookEvent(BaseModel):
    """Модель события от VK Teams"""
    eventType: str
    eventId: str
    timestamp: int
    payload: Dict[str, Any]


@router.post("/events")
async def handle_webhook_event(
    event: WebhookEvent,
    request: Request,
    bot_adapter: VKTeamsBotAdapter = Depends(get_vk_teams_bot_adapter)
) -> Dict[str, Any]:
    """
    Обработчик webhook событий от VK Teams
    
    Принимает события от VK Teams и обрабатывает их:
    - Новые сообщения
    - Команды
    - Кнопки
    - Другие события
    """
    try:
        # Логируем входящее событие
        logger.info(f"Получено событие VK Teams: {event.eventType} (ID: {event.eventId})")
        
        # Проверяем безопасность запроса (опционально)
        # await bot_adapter.verify_webhook_security(request)
        
        # Обрабатываем событие
        result = await bot_adapter.handle_event(
            event_type=event.eventType,
            event_id=event.eventId,
            timestamp=event.timestamp,
            payload=event.payload
        )
        
        return {
            "success": True,
            "event_id": event.eventId,
            "processed": True,
            "response": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook события {event.eventId}: {e}")
        # Не возвращаем 500, чтобы VK Teams не повторял запрос
        return {
            "success": False,
            "event_id": event.eventId,
            "error": str(e),
            "processed": False
        }


@router.post("/messages")
async def handle_message_event(
    request: Request,
    bot_adapter: VKTeamsBotAdapter = Depends(get_vk_teams_bot_adapter)
) -> Dict[str, Any]:
    """
    Специализированный обработчик для сообщений
    
    Обрабатывает только события новых сообщений
    """
    try:
        # Получаем JSON из запроса
        event_data = await request.json()
        
        logger.info(f"Получено сообщение от VK Teams: {event_data.get('eventId')}")
        
        # Обрабатываем как сообщение
        result = await bot_adapter.handle_message_event(event_data)
        
        return {
            "success": True,
            "message": "Сообщение обработано",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/callback")
async def handle_callback_query(
    request: Request,
    bot_adapter: VKTeamsBotAdapter = Depends(get_vk_teams_bot_adapter)
) -> Dict[str, Any]:
    """
    Обработчик callback запросов (нажатие кнопок)
    
    Обрабатывает события нажатий на inline кнопки
    """
    try:
        # Получаем JSON из запроса
        event_data = await request.json()
        
        logger.info(f"Получен callback от VK Teams: {event_data.get('eventId')}")
        
        # Обрабатываем callback
        result = await bot_adapter.handle_callback_query(event_data)
        
        return {
            "success": True,
            "message": "Callback обработан",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка обработки callback: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/health")
async def webhook_health_check() -> Dict[str, Any]:
    """
    Проверка здоровья webhook endpoint'а
    
    Используется для мониторинга доступности webhook'а
    """
    return {
        "status": "healthy",
        "service": "vk-teams-webhook",
        "ready": True
    }


@router.post("/test")
async def test_webhook(
    test_data: Dict[str, Any],
    bot_adapter: VKTeamsBotAdapter = Depends(get_vk_teams_bot_adapter)
) -> Dict[str, Any]:
    """
    Тестовый endpoint для проверки работы webhook'а
    
    Позволяет протестировать обработку событий без VK Teams
    """
    try:
        logger.info("Тестирование webhook с данными:", test_data)
        
        # Симулируем обработку события
        result = await bot_adapter.test_event_processing(test_data)
        
        return {
            "success": True,
            "message": "Тест webhook'а успешен",
            "test_result": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка тестирования webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка тестирования webhook: {str(e)}"
        ) 