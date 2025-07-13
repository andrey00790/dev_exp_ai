"""
VK Teams Integration Infrastructure Module

Clean Architecture structure for VK Teams Bot integration:
- domain: Business logic and entities
- application: Use cases and services
- infrastructure: External integrations and adapters
- presentation: API endpoints and controllers

Context7 pattern: Centralized, well-structured integration module
"""

from .application.bot_service import VKTeamsBotService, get_vk_teams_bot_service
from .infrastructure.bot_adapter_simple import VKTeamsBotAdapter, get_vk_teams_bot_adapter
from .presentation.bot_endpoints import router as bot_router
from .presentation.webhook_endpoints import router as webhook_router

__all__ = [
    "VKTeamsBotService",
    "get_vk_teams_bot_service",
    "VKTeamsBotAdapter", 
    "get_vk_teams_bot_adapter",
    "bot_router",
    "webhook_router"
] 