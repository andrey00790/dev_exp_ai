"""
Base LLM Adapter Interface для AI Assistant MVP
Абстрактный слой для различных LLM провайдеров (OpenAI, Anthropic, etc.)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncIterator, Union
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    OLLAMA = "ollama"
    MOCK = "mock"

class MessageRole(Enum):
    """Message roles in conversation"""
    SYSTEM = "system"
    USER = "user" 
    ASSISTANT = "assistant"
    FUNCTION = "function"

@dataclass
class LLMMessage:
    """Standard message format for LLM conversations"""
    role: MessageRole
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass 
class LLMRequest:
    """Standard request format for LLM calls"""
    messages: List[LLMMessage]
    model: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = None
    stream: bool = False
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[Union[str, Dict[str, str]]] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class LLMUsage:
    """Token usage statistics"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: Optional[float] = None

@dataclass
class LLMResponse:
    """Standard response format from LLM"""
    content: str
    role: MessageRole = MessageRole.ASSISTANT
    finish_reason: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    usage: Optional[LLMUsage] = None
    model: Optional[str] = None
    provider: Optional[LLMProvider] = None
    response_id: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class LLMStreamChunk:
    """Chunk for streaming responses"""
    content: str
    finish_reason: Optional[str] = None
    delta: Optional[Dict[str, Any]] = None
    usage: Optional[LLMUsage] = None

class LLMError(Exception):
    """Base exception for LLM operations"""
    def __init__(self, message: str, provider: Optional[LLMProvider] = None, 
                 error_code: Optional[str] = None, retry_after: Optional[int] = None):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code
        self.retry_after = retry_after

class LLMRateLimitError(LLMError):
    """Rate limit exceeded error"""
    pass

class LLMAuthenticationError(LLMError):
    """Authentication/API key error"""
    pass

class LLMQuotaExceededError(LLMError):
    """Quota/billing limit exceeded"""
    pass

class LLMModelNotFoundError(LLMError):
    """Model not available error"""
    pass

class BaseLLMAdapter(ABC):
    """Abstract base class for LLM adapters"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, 
                 timeout: int = 60, max_retries: int = 3):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.provider = self.get_provider()
        
    @abstractmethod
    def get_provider(self) -> LLMProvider:
        """Return the provider type"""
        pass
    
    @abstractmethod
    async def chat_completion(self, request: LLMRequest) -> LLMResponse:
        """Send chat completion request to LLM"""
        pass
    
    @abstractmethod
    async def chat_completion_stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Send streaming chat completion request"""
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """Get list of available models"""
        pass
    
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """Validate API key"""
        pass
    
    async def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate cost for request (optional)"""
        return 0.0
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the adapter"""
        try:
            is_valid = await self.validate_api_key()
            models = await self.get_available_models()
            
            return {
                "status": "healthy" if is_valid else "unhealthy",
                "provider": self.provider.value,
                "api_key_valid": is_valid,
                "available_models": len(models),
                "base_url": self.base_url
            }
        except Exception as e:
            logger.error(f"❌ Health check failed for {self.provider.value}: {e}")
            return {
                "status": "unhealthy",
                "provider": self.provider.value,
                "error": str(e)
            }

class LLMAdapterFactory:
    """Factory for creating LLM adapters"""
    
    _adapters: Dict[LLMProvider, type] = {}
    
    @classmethod
    def register_adapter(cls, provider: LLMProvider, adapter_class: type):
        """Register an adapter class for a provider"""
        cls._adapters[provider] = adapter_class
        logger.info(f"✅ Registered LLM adapter: {provider.value}")
    
    @classmethod
    def create_adapter(cls, provider: LLMProvider, api_key: str, 
                      **kwargs) -> BaseLLMAdapter:
        """Create adapter instance for provider"""
        if provider not in cls._adapters:
            raise ValueError(f"No adapter registered for provider: {provider.value}")
        
        adapter_class = cls._adapters[provider]
        return adapter_class(api_key=api_key, **kwargs)
    
    @classmethod
    def get_available_providers(cls) -> List[LLMProvider]:
        """Get list of available providers"""
        return list(cls._adapters.keys())

# Utility functions

def convert_to_llm_messages(messages: List[Dict[str, str]]) -> List[LLMMessage]:
    """Convert dict messages to LLMMessage objects"""
    llm_messages = []
    for msg in messages:
        role = MessageRole(msg.get("role", "user"))
        content = msg.get("content", "")
        llm_messages.append(LLMMessage(role=role, content=content))
    return llm_messages

def convert_from_llm_messages(messages: List[LLMMessage]) -> List[Dict[str, str]]:
    """Convert LLMMessage objects to dict format"""
    return [
        {
            "role": msg.role.value,
            "content": msg.content,
            **({"name": msg.name} if msg.name else {}),
            **({"function_call": msg.function_call} if msg.function_call else {})
        }
        for msg in messages
    ]

def create_system_message(content: str) -> LLMMessage:
    """Helper to create system message"""
    return LLMMessage(role=MessageRole.SYSTEM, content=content)

def create_user_message(content: str, name: Optional[str] = None) -> LLMMessage:
    """Helper to create user message"""
    return LLMMessage(role=MessageRole.USER, content=content, name=name)

def create_assistant_message(content: str, function_call: Optional[Dict[str, Any]] = None) -> LLMMessage:
    """Helper to create assistant message"""
    return LLMMessage(role=MessageRole.ASSISTANT, content=content, function_call=function_call)

# Cost calculation utilities

class CostCalculator:
    """Utility for calculating LLM costs"""
    
    # Pricing per 1K tokens (USD) - may need updates
    PRICING = {
        LLMProvider.OPENAI: {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
        },
        LLMProvider.ANTHROPIC: {
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        }
    }
    
    @classmethod
    def calculate_cost(cls, provider: LLMProvider, model: str, 
                      input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage"""
        try:
            provider_pricing = cls.PRICING.get(provider, {})
            model_pricing = provider_pricing.get(model, {"input": 0, "output": 0})
            
            input_cost = (input_tokens / 1000) * model_pricing["input"]
            output_cost = (output_tokens / 1000) * model_pricing["output"]
            
            return input_cost + output_cost
            
        except (KeyError, ZeroDivisionError):
            logger.warning(f"⚠️ No pricing data for {provider.value}/{model}")
            return 0.0
    
    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """Rough estimation of token count"""
        # Simple estimation: ~4 characters per token
        return max(1, len(text) // 4) 