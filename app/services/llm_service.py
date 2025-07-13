"""
LLM Service для AI Assistant MVP
Высокоуровневый сервис для работы с LLM адаптерами
"""

import logging
from typing import Dict, List, Optional, AsyncIterator, Any, Enum
from datetime import datetime
import os

from app.adapters.llm import (
    LLMAdapterFactory, LLMProvider, BaseLLMAdapter,
    LLMRequest, LLMResponse, LLMStreamChunk, LLMMessage,
    create_system_message, create_user_message, create_assistant_message,
    LLMError, LLMRateLimitError, LLMAuthenticationError
)
from app.core.exceptions import ServiceError

logger = logging.getLogger(__name__)

class LLMServiceError(ServiceError):
    """LLM service specific error"""
    pass

class LLMService:
    """High-level service for LLM operations"""
    
    def __init__(self):
        self.adapters: Dict[LLMProvider, BaseLLMAdapter] = {}
        self.default_provider: Optional[LLMProvider] = None
        self.system_prompt = "You are a helpful AI assistant."
        
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize LLM service with configuration"""
        try:
            # Initialize adapters based on configuration
            for provider_name, provider_config in config.get('providers', {}).items():
                if not provider_config.get('enabled', False):
                    continue
                    
                provider = LLMProvider(provider_name)
                api_key = provider_config.get('api_key') or os.getenv(f"{provider_name.upper()}_API_KEY")
                
                if not api_key:
                    logger.warning(f"⚠️ No API key found for {provider_name}")
                    continue
                
                try:
                    adapter = LLMAdapterFactory.create_adapter(
                        provider=provider,
                        api_key=api_key,
                        base_url=provider_config.get('base_url'),
                        timeout=provider_config.get('timeout', 60),
                        max_retries=provider_config.get('max_retries', 3)
                    )
                    
                    # Validate adapter
                    is_valid = await adapter.validate_api_key()
                    if is_valid:
                        self.adapters[provider] = adapter
                        logger.info(f"✅ Initialized {provider_name} LLM adapter")
                        
                        # Set first valid adapter as default
                        if not self.default_provider:
                            self.default_provider = provider
                    else:
                        logger.error(f"❌ Invalid API key for {provider_name}")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to initialize {provider_name} adapter: {e}")
            
            # Initialize Mock adapter as fallback
            if not self.adapters:
                mock_adapter = LLMAdapterFactory.create_adapter(LLMProvider.MOCK, "mock-key")
                self.adapters[LLMProvider.MOCK] = mock_adapter
                self.default_provider = LLMProvider.MOCK
                logger.info("✅ Initialized Mock LLM adapter as fallback")
            
            # Set system prompt
            self.system_prompt = config.get('system_prompt', self.system_prompt)
            
            logger.info(f"🤖 LLM Service initialized with {len(self.adapters)} adapters")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM service: {e}")
            raise LLMServiceError(f"LLM service initialization failed: {e}")
    
    def get_adapter(self, provider: Optional[LLMProvider] = None) -> BaseLLMAdapter:
        """Get LLM adapter for provider"""
        target_provider = provider or self.default_provider
        
        if not target_provider or target_provider not in self.adapters:
            if self.adapters:
                # Fallback to first available adapter
                target_provider = list(self.adapters.keys())[0]
                logger.warning(f"⚠️ Falling back to {target_provider.value} adapter")
            else:
                raise LLMServiceError("No LLM adapters available")
        
        return self.adapters[target_provider]
    
    async def chat_completion(
        self,
        messages: List[str],
        model: str = "gpt-4",
        provider: Optional[LLMProvider] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> LLMResponse:
        """Send chat completion request"""
        try:
            adapter = self.get_adapter(provider)
            
            # Convert string messages to LLMMessage objects
            llm_messages = []
            
            # Add system message
            system_text = system_prompt or self.system_prompt
            llm_messages.append(create_system_message(system_text))
            
            # Add user messages (assume they alternate user/assistant)
            for i, msg in enumerate(messages):
                if i % 2 == 0:  # Even indices are user messages
                    llm_messages.append(create_user_message(msg))
                else:  # Odd indices are assistant messages (for conversation history)
                    llm_messages.append(create_assistant_message(msg))
            
            # Create request
            request = LLMRequest(
                messages=llm_messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                user_id=user_id
            )
            
            # Make request
            response = await adapter.chat_completion(request)
            
            logger.info(f"✅ Chat completion: {response.usage.total_tokens} tokens, ${response.usage.cost_usd:.4f}")
            
            return response
            
        except LLMError as e:
            logger.error(f"❌ LLM error: {e}")
            raise LLMServiceError(f"LLM request failed: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error in chat completion: {e}")
            raise LLMServiceError(f"Chat completion failed: {e}")
    
    async def chat_completion_stream(
        self,
        messages: List[str],
        model: str = "gpt-4",
        provider: Optional[LLMProvider] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> AsyncIterator[LLMStreamChunk]:
        """Send streaming chat completion request"""
        try:
            adapter = self.get_adapter(provider)
            
            # Convert string messages to LLMMessage objects
            llm_messages = []
            
            # Add system message
            system_text = system_prompt or self.system_prompt
            llm_messages.append(create_system_message(system_text))
            
            # Add user messages
            for i, msg in enumerate(messages):
                if i % 2 == 0:
                    llm_messages.append(create_user_message(msg))
                else:
                    llm_messages.append(create_assistant_message(msg))
            
            # Create request
            request = LLMRequest(
                messages=llm_messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                user_id=user_id,
                stream=True
            )
            
            # Stream response
            async for chunk in adapter.chat_completion_stream(request):
                yield chunk
                
        except LLMError as e:
            logger.error(f"❌ LLM streaming error: {e}")
            raise LLMServiceError(f"LLM streaming failed: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error in chat streaming: {e}")
            raise LLMServiceError(f"Chat streaming failed: {e}")
    
    async def get_available_models(self, provider: Optional[LLMProvider] = None) -> List[str]:
        """Get available models for provider"""
        try:
            adapter = self.get_adapter(provider)
            models = await adapter.get_available_models()
            return models
        except Exception as e:
            logger.error(f"❌ Failed to get models: {e}")
            return []
    
    async def estimate_cost(
        self,
        messages: List[str],
        model: str = "gpt-4",
        provider: Optional[LLMProvider] = None,
        max_tokens: Optional[int] = None
    ) -> float:
        """Estimate cost for request"""
        try:
            adapter = self.get_adapter(provider)
            
            # Convert to LLMMessage objects
            llm_messages = []
            llm_messages.append(create_system_message(self.system_prompt))
            
            for i, msg in enumerate(messages):
                if i % 2 == 0:
                    llm_messages.append(create_user_message(msg))
                else:
                    llm_messages.append(create_assistant_message(msg))
            
            request = LLMRequest(
                messages=llm_messages,
                model=model,
                max_tokens=max_tokens
            )
            
            return await adapter.estimate_cost(request)
            
        except Exception as e:
            logger.error(f"❌ Failed to estimate cost: {e}")
            return 0.0
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for all adapters"""
        health_status = {
            "status": "healthy",
            "adapters": {},
            "default_provider": self.default_provider.value if self.default_provider else None,
            "total_adapters": len(self.adapters)
        }
        
        healthy_adapters = 0
        
        for provider, adapter in self.adapters.items():
            try:
                adapter_health = await adapter.health_check()
                health_status["adapters"][provider.value] = adapter_health
                
                if adapter_health.get("status") == "healthy":
                    healthy_adapters += 1
                    
            except Exception as e:
                health_status["adapters"][provider.value] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Overall status
        if healthy_adapters == 0:
            health_status["status"] = "unhealthy"
        elif healthy_adapters < len(self.adapters):
            health_status["status"] = "degraded"
        
        return health_status
    
    def get_supported_providers(self) -> List[LLMProvider]:
        """Get list of configured providers"""
        return list(self.adapters.keys())

# Global service instance
llm_service: Optional[LLMService] = None

def get_llm_service() -> LLMService:
    """Get global LLM service instance (compatibility function)"""
    global llm_service
    if llm_service is None:
        llm_service = LLMService()
    return llm_service

async def initialize_llm_service(config: Optional[Dict[str, Any]] = None) -> None:
    """Initialize global LLM service (compatibility function)"""
    service = get_llm_service()
    if config is None:
        # Default configuration
        config = {
            "providers": {
                "openai": {
                    "enabled": True,
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "model": "gpt-4"
                },
                "anthropic": {
                    "enabled": True,
                    "api_key": os.getenv("ANTHROPIC_API_KEY"),
                    "model": "claude-3-sonnet-20240229"
                }
            },
            "system_prompt": "You are a helpful AI assistant."
        }
    await service.initialize(config)

# Compatibility enum for routing strategy (simplified)
class RoutingStrategy(Enum):
    """Simple routing strategy for compatibility"""
    PRIORITY = "priority"
    COST_OPTIMIZED = "cost_optimized"
    QUALITY_OPTIMIZED = "quality_optimized"
    BALANCED = "balanced"
    ROUND_ROBIN = "round_robin"

async def chat_completion(messages: List[str], **kwargs) -> LLMResponse:
    """Convenience function for chat completion"""
    service = get_llm_service()
    return await service.chat_completion(messages, **kwargs)

async def chat_completion_stream(messages: List[str], **kwargs) -> AsyncIterator[LLMStreamChunk]:
    """Convenience function for streaming chat completion"""
    service = get_llm_service()
    async for chunk in service.chat_completion_stream(messages, **kwargs):
        yield chunk

async def get_available_models(provider: Optional[LLMProvider] = None) -> List[str]:
    """Convenience function to get available models"""
    service = get_llm_service()
    return await service.get_available_models(provider)
