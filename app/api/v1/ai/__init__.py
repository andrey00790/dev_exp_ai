"""
AI domain - handles all AI-powered functionality.
"""

from .ai_advanced import router as ai_advanced
from .ai_analytics import router as ai_analytics
from .ai_optimization import router as ai_optimization
from .deep_research import router as deep_research
from .generate import router as generate
from .learning import router as learning
from .llm_management import router as llm_management

__all__ = [
    "ai_optimization",
    "ai_advanced",
    "generate",
    "llm_management",
    "learning",
    "ai_analytics",
    "deep_research",
]
