"""
OpenAI Adapter для AI Assistant MVP
Реализация BaseLLMAdapter для работы с OpenAI API
"""

import asyncio
import logging
from typing import List, AsyncIterator, Optional, Dict, Any
from datetime import datetime
import json

try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base import (
    BaseLLMAdapter, LLMProvider, LLMMessage, LLMRequest, LLMResponse, 
    LLMStreamChunk, LLMUsage, MessageRole, LLMError, LLMRateLimitError,
    LLMAuthenticationError, LLMQuotaExceededError, LLMModelNotFoundError,
    CostCalculator
)

logger = logging.getLogger(__name__)

class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI implementation of BaseLLMAdapter"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, 
                 timeout: int = 60, max_retries: int = 3):
        super().__init__(api_key, base_url, timeout, max_retries)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries
        )
        
        # OpenAI model mappings
        self.model_aliases = {
            "gpt-4": "gpt-4-0125-preview",
            "gpt-4-turbo": "gpt-4-turbo-preview",
            "gpt-3.5": "gpt-3.5-turbo",
            "gpt-3.5-turbo": "gpt-3.5-turbo-0125"
        }
    
    def get_provider(self) -> LLMProvider:
        return LLMProvider.OPENAI
    
    def _convert_messages_to_openai(self, messages: List[LLMMessage]) -> List[Dict[str, str]]:
        """Convert LLMMessage to OpenAI format"""
        openai_messages = []
        for msg in messages:
            openai_msg = {
                "role": msg.role.value,
                "content": msg.content
            }
            if msg.name:
                openai_msg["name"] = msg.name
            if msg.function_call:
                openai_msg["function_call"] = msg.function_call
            
            openai_messages.append(openai_msg)
        
        return openai_messages
    
    def _resolve_model(self, model: str) -> str:
        """Resolve model alias to actual model name"""
        return self.model_aliases.get(model, model)
    
    async def chat_completion(self, request: LLMRequest) -> LLMResponse:
        """Send chat completion request to OpenAI"""
        try:
            # Convert messages
            openai_messages = self._convert_messages_to_openai(request.messages)
            resolved_model = self._resolve_model(request.model)
            
            # Prepare request parameters
            params = {
                "model": resolved_model,
                "messages": openai_messages,
                "stream": False
            }
            
            # Add optional parameters
            if request.max_tokens:
                params["max_tokens"] = request.max_tokens
            if request.temperature is not None:
                params["temperature"] = request.temperature
            if request.top_p is not None:
                params["top_p"] = request.top_p
            if request.frequency_penalty is not None:
                params["frequency_penalty"] = request.frequency_penalty
            if request.presence_penalty is not None:
                params["presence_penalty"] = request.presence_penalty
            if request.stop:
                params["stop"] = request.stop
            if request.functions:
                params["functions"] = request.functions
            if request.function_call:
                params["function_call"] = request.function_call
            if request.user_id:
                params["user"] = request.user_id
            
            # Make API call
            response = await self.client.chat.completions.create(**params)
            
            # Extract response data
            choice = response.choices[0]
            message = choice.message
            
            # Calculate cost
            usage_data = response.usage
            cost = CostCalculator.calculate_cost(
                LLMProvider.OPENAI, 
                resolved_model,
                usage_data.prompt_tokens,
                usage_data.completion_tokens
            ) if usage_data else 0.0
            
            # Create usage object
            usage = LLMUsage(
                prompt_tokens=usage_data.prompt_tokens if usage_data else 0,
                completion_tokens=usage_data.completion_tokens if usage_data else 0,
                total_tokens=usage_data.total_tokens if usage_data else 0,
                cost_usd=cost
            )
            
            return LLMResponse(
                content=message.content or "",
                role=MessageRole.ASSISTANT,
                finish_reason=choice.finish_reason,
                function_call=getattr(message, 'function_call', None),
                usage=usage,
                model=resolved_model,
                provider=LLMProvider.OPENAI,
                response_id=response.id,
                created_at=datetime.fromtimestamp(response.created),
                metadata={"original_model": request.model}
            )
            
        except Exception as e:
            await self._handle_openai_error(e)
    
    async def chat_completion_stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Send streaming chat completion request to OpenAI"""
        try:
            # Convert messages
            openai_messages = self._convert_messages_to_openai(request.messages)
            resolved_model = self._resolve_model(request.model)
            
            # Prepare request parameters
            params = {
                "model": resolved_model,
                "messages": openai_messages,
                "stream": True
            }
            
            # Add optional parameters
            if request.max_tokens:
                params["max_tokens"] = request.max_tokens
            if request.temperature is not None:
                params["temperature"] = request.temperature
            if request.top_p is not None:
                params["top_p"] = request.top_p
            if request.user_id:
                params["user"] = request.user_id
            
            # Make streaming API call
            stream = await self.client.chat.completions.create(**params)
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    delta = choice.delta
                    
                    content = getattr(delta, 'content', '') or ''
                    finish_reason = choice.finish_reason
                    
                    # Create usage if available (usually in last chunk)
                    usage = None
                    if hasattr(chunk, 'usage') and chunk.usage:
                        cost = CostCalculator.calculate_cost(
                            LLMProvider.OPENAI,
                            resolved_model,
                            chunk.usage.prompt_tokens,
                            chunk.usage.completion_tokens
                        )
                        usage = LLMUsage(
                            prompt_tokens=chunk.usage.prompt_tokens,
                            completion_tokens=chunk.usage.completion_tokens,
                            total_tokens=chunk.usage.total_tokens,
                            cost_usd=cost
                        )
                    
                    yield LLMStreamChunk(
                        content=content,
                        finish_reason=finish_reason,
                        delta=delta.__dict__ if delta else {},
                        usage=usage
                    )
                    
        except Exception as e:
            await self._handle_openai_error(e)
    
    async def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models"""
        try:
            models = await self.client.models.list()
            # Filter for chat models only
            chat_models = []
            for model in models.data:
                if any(prefix in model.id for prefix in ["gpt-3.5", "gpt-4"]):
                    chat_models.append(model.id)
            
            # Add aliases
            chat_models.extend(self.model_aliases.keys())
            return sorted(list(set(chat_models)))
            
        except Exception as e:
            logger.error(f"❌ Failed to get OpenAI models: {e}")
            # Return default models if API call fails
            return ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
    
    async def validate_api_key(self) -> bool:
        """Validate OpenAI API key"""
        try:
            # Try to list models to validate key
            await self.client.models.list()
            return True
        except Exception as e:
            logger.warning(f"⚠️ OpenAI API key validation failed: {e}")
            return False
    
    async def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate cost for OpenAI request"""
        resolved_model = self._resolve_model(request.model)
        
        # Estimate input tokens
        total_input_text = " ".join([msg.content for msg in request.messages])
        input_tokens = CostCalculator.estimate_tokens(total_input_text)
        
        # Estimate output tokens
        output_tokens = request.max_tokens or 150  # Default estimation
        
        return CostCalculator.calculate_cost(
            LLMProvider.OPENAI,
            resolved_model,
            input_tokens,
            output_tokens
        )
    
    async def _handle_openai_error(self, error: Exception) -> None:
        """Handle OpenAI-specific errors"""
        error_message = str(error)
        
        if "rate limit" in error_message.lower():
            raise LLMRateLimitError(
                f"OpenAI rate limit exceeded: {error_message}",
                provider=LLMProvider.OPENAI,
                error_code="rate_limit"
            )
        elif "authentication" in error_message.lower() or "api key" in error_message.lower():
            raise LLMAuthenticationError(
                f"OpenAI authentication failed: {error_message}",
                provider=LLMProvider.OPENAI,
                error_code="auth_error"
            )
        elif "quota" in error_message.lower() or "billing" in error_message.lower():
            raise LLMQuotaExceededError(
                f"OpenAI quota exceeded: {error_message}",
                provider=LLMProvider.OPENAI,
                error_code="quota_exceeded"
            )
        elif "model" in error_message.lower() and "not found" in error_message.lower():
            raise LLMModelNotFoundError(
                f"OpenAI model not found: {error_message}",
                provider=LLMProvider.OPENAI,
                error_code="model_not_found"
            )
        else:
            raise LLMError(
                f"OpenAI API error: {error_message}",
                provider=LLMProvider.OPENAI,
                error_code="api_error"
            ) 