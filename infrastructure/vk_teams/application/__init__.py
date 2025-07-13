"""
VK Teams Application Layer

Use cases and services for VK Teams integration.
Context7 pattern: Orchestrates business logic and external dependencies.
"""

from .bot_service import VKTeamsBotService, get_vk_teams_bot_service

__all__ = [
    "VKTeamsBotService",
    "get_vk_teams_bot_service"
] 