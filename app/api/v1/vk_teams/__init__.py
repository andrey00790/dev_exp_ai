"""
VK Teams Bot API Integration Module

Этот модуль обеспечивает интеграцию с VK Teams через Bot API.
Предоставляет endpoints для управления ботом и webhook'ами.
"""

from .bot_endpoints import router as bot_router
from .webhook_endpoints import router as webhook_router

__all__ = ["bot_router", "webhook_router"] 