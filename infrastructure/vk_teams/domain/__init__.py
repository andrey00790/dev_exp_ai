"""
VK Teams Domain Layer

Business logic and entities for VK Teams integration.
Context7 pattern: Pure business logic without external dependencies.
"""

from .bot_models import BotConfig, BotStats, BotMessage, AIAssistantContext

__all__ = [
    "BotConfig",
    "BotStats", 
    "BotMessage",
    "AIAssistantContext"
] 