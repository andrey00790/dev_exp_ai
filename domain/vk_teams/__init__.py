"""
VK Teams Domain Layer

Содержит бизнес-логику для работы с VK Teams ботом:
- BotService - основной сервис бота
- BotAdapter - адаптер интеграции с API
- Models - модели данных
"""

from .bot_service import VKTeamsBotService, get_vk_teams_bot_service
from .bot_adapter_simple import VKTeamsBotAdapter, get_vk_teams_bot_adapter

__all__ = [
    "VKTeamsBotService",
    "get_vk_teams_bot_service", 
    "VKTeamsBotAdapter",
    "get_vk_teams_bot_adapter"
] 