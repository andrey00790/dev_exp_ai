"""
LLM Adapters для AI Assistant MVP
Абстрактный слой для работы с различными LLM провайдерами
"""

from .base import (
    BaseLLMAdapter,
    LLMAdapterFactory,
    LLMProvider,
    MessageRole,
    LLMMessage,
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
    LLMUsage,
    LLMError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMQuotaExceededError,
    LLMModelNotFoundError,
    CostCalculator,
    convert_to_llm_messages,
    convert_from_llm_messages,
    create_system_message,
    create_user_message,
    create_assistant_message
)

# Import and register Mock adapter (always available)
from .mock_adapter import MockLLMAdapter
LLMAdapterFactory.register_adapter(LLMProvider.MOCK, MockLLMAdapter)

# Import other adapters only if libraries are available
try:
    from .openai_adapter import OpenAIAdapter
    LLMAdapterFactory.register_adapter(LLMProvider.OPENAI, OpenAIAdapter)
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from .anthropic_adapter import AnthropicAdapter  
    LLMAdapterFactory.register_adapter(LLMProvider.ANTHROPIC, AnthropicAdapter)
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# Report available adapters
import logging
logger = logging.getLogger(__name__)

available_providers = LLMAdapterFactory.get_available_providers()
logger.info(f"✅ LLM Adapters initialized. Available providers: {[p.value for p in available_providers]}")

__all__ = [
    # Base classes
    "BaseLLMAdapter",
    "LLMAdapterFactory",
    
    # Enums
    "LLMProvider", 
    "MessageRole",
    
    # Data classes
    "LLMMessage",
    "LLMRequest",
    "LLMResponse", 
    "LLMStreamChunk",
    "LLMUsage",
    
    # Exceptions
    "LLMError",
    "LLMRateLimitError",
    "LLMAuthenticationError", 
    "LLMQuotaExceededError",
    "LLMModelNotFoundError",
    
    # Utilities
    "CostCalculator",
    "convert_to_llm_messages",
    "convert_from_llm_messages",
    "create_system_message",
    "create_user_message",
    "create_assistant_message",
    
    # Adapter classes (if available)
    "MockLLMAdapter",
    
    # Availability flags
    "OPENAI_AVAILABLE",
    "ANTHROPIC_AVAILABLE"
]

# Add available adapter classes to exports
if OPENAI_AVAILABLE:
    __all__.append("OpenAIAdapter")

if ANTHROPIC_AVAILABLE:
    __all__.append("AnthropicAdapter") 