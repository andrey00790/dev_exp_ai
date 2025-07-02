"""
VK Teams Bot Adapter - упрощенная версия
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class VKTeamsBotAdapter:
    """Упрощенный адаптер для VK Teams бота"""
    
    def __init__(self):
        self.user_contexts = {}
    
    async def handle_event(self, event_type: str, event_id: str, timestamp: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка событий от VK Teams"""
        return {"status": "processed", "event_id": event_id}
    
    async def handle_message_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка сообщений"""
        return {"status": "processed"}
    
    async def handle_callback_query(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка callback запросов"""
        return {"status": "processed"}
    
    async def test_event_processing(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Тестовая обработка"""
        return {"test_successful": True, "data": test_data}


_bot_adapter: Optional[VKTeamsBotAdapter] = None


async def get_vk_teams_bot_adapter() -> VKTeamsBotAdapter:
    """Получение экземпляра адаптера"""
    global _bot_adapter
    if _bot_adapter is None:
        _bot_adapter = VKTeamsBotAdapter()
    return _bot_adapter 