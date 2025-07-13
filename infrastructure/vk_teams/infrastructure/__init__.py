"""
VK Teams Infrastructure Layer

External integrations and adapters for VK Teams integration.
Context7 pattern: Handles external dependencies and API integrations.
"""

from .bot_adapter_simple import VKTeamsBotAdapter, get_vk_teams_bot_adapter
from .bot_adapter import VKTeamsBotAdapter as LegacyAdapter

__all__ = [
    "VKTeamsBotAdapter",
    "get_vk_teams_bot_adapter",
    "LegacyAdapter"
] 