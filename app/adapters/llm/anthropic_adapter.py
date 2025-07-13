"""
Anthropic Claude Adapter для AI Assistant MVP
Реализация BaseLLMAdapter для работы с Anthropic Claude API
"""

import asyncio
import logging
from typing import List, AsyncIterator, Optional, Dict, Any
from datetime import datetime
import json

try:
    import anthropic
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base import (
    BaseLLMAdapter, LLMProvider, LLMMessage, LLMRequest, LLMResponse, 
    LLMStreamChunk, LLMUsage, MessageRole, LLMError, LLMRateLimitError,
    LLMAuthenticationError, LLMQuotaExceededError, LLMModelNotFoundError,
    CostCalculator
)

logger = logging.getLogger(__name__)

class AnthropicAdapter(BaseLLMAdapter):
    """Anthropic Claude implementation of BaseLLMAdapter"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None,
                 timeout: int = 60, max_retries: int = 3):
        super().__init__(api_key, base_url, timeout, max_retries)
        
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic library not installed. Run: pip install anthropic")
        
        self.client = AsyncAnthropic(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries
        )
        
        # Anthropic model mappings
        self.model_aliases = {
            "claude-3": "claude-3-sonnet-20240229",
            "claude-3-sonnet": "claude-3-sonnet-20240229", 
            "claude-3-haiku": "claude-3-haiku-20240307",
            "claude-3-opus": "claude-3-opus-20240229"
        }
        
        # Default system message for Claude
        self.default_system_message = "You are Claude, an AI assistant created by Anthropic."
    
    def get_provider(self) -> LLMProvider:
        return LLMProvider.ANTHROPIC
    
    def _convert_messages_to_anthropic(self, messages: List[LLMMessage]) -> tuple[str, List[Dict[str, str]]]:
        """Convert LLMMessage to Anthropic format"""
        system_message = self.default_system_message
        anthropic_messages = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                # Claude uses system parameter separately
                system_message = msg.content
            elif msg.role in [MessageRole.USER, MessageRole.ASSISTANT]:
                anthropic_messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
            # Skip function messages as Claude doesn't support them directly
        
        return system_message, anthropic_messages
    
    def _resolve_model(self, model: str) -> str:
        """Resolve model alias to actual model name"""
        return self.model_aliases.get(model, model)
    
    async def chat_completion(self, request: LLMRequest) -> LLMResponse:
        """Send chat completion request to Anthropic Claude"""
        try:
            # Convert messages
            system_message, anthropic_messages = self._convert_messages_to_anthropic(request.messages)
            resolved_model = self._resolve_model(request.model)
            
            # Prepare request parameters
            params = {
                "model": resolved_model,
                "max_tokens": request.max_tokens or 1000,  # Required for Claude
                "messages": anthropic_messages,
                "system": system_message
            }
            
            # Add optional parameters
            if request.temperature is not None:
                params["temperature"] = request.temperature
            if request.top_p is not None:
                params["top_p"] = request.top_p
            if request.stop:
                if isinstance(request.stop, str):
                    params["stop_sequences"] = [request.stop]
                else:
                    params["stop_sequences"] = request.stop
            
            # Make API call
            response = await self.client.messages.create(**params)
            
            # Extract content
            content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
            
            # Calculate cost
            cost = CostCalculator.calculate_cost(
                LLMProvider.ANTHROPIC,
                resolved_model,
                response.usage.input_tokens,
                response.usage.output_tokens
            ) if response.usage else 0.0
            
            # Create usage object
            usage = LLMUsage(
                prompt_tokens=response.usage.input_tokens if response.usage else 0,
                completion_tokens=response.usage.output_tokens if response.usage else 0,
                total_tokens=(response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0,
                cost_usd=cost
            )
            
            return LLMResponse(
                content=content,
                role=MessageRole.ASSISTANT,
                finish_reason=response.stop_reason,
                usage=usage,
                model=resolved_model,
                provider=LLMProvider.ANTHROPIC,
                response_id=response.id,
                created_at=datetime.now(),  # Anthropic doesn't provide timestamp
                metadata={"original_model": request.model}
            )
            
        except Exception as e:
            await self._handle_anthropic_error(e)
    
    async def chat_completion_stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Send streaming chat completion request to Anthropic Claude"""
        try:
            # Convert messages
            system_message, anthropic_messages = self._convert_messages_to_anthropic(request.messages)
            resolved_model = self._resolve_model(request.model)
            
            # Prepare request parameters
            params = {
                "model": resolved_model,
                "max_tokens": request.max_tokens or 1000,
                "messages": anthropic_messages,
                "system": system_message,
                "stream": True
            }
            
            # Add optional parameters
            if request.temperature is not None:
                params["temperature"] = request.temperature
            if request.top_p is not None:
                params["top_p"] = request.top_p
            
            # Make streaming API call
            stream = await self.client.messages.create(**params)
            
            async for event in stream:
                if event.type == "content_block_delta":
                    delta = event.delta
                    content = getattr(delta, 'text', '') or ''
                    
                    yield LLMStreamChunk(
                        content=content,
                        finish_reason=None,
                        delta={"text": content}
                    )
                elif event.type == "message_stop":
                    # Final chunk with usage info
                    usage = None
                    if hasattr(event, 'usage'):
                        cost = CostCalculator.calculate_cost(
                            LLMProvider.ANTHROPIC,
                            resolved_model,
                            event.usage.input_tokens,
                            event.usage.output_tokens
                        )
                        usage = LLMUsage(
                            prompt_tokens=event.usage.input_tokens,
                            completion_tokens=event.usage.output_tokens,
                            total_tokens=event.usage.input_tokens + event.usage.output_tokens,
                            cost_usd=cost
                        )
                    
                    yield LLMStreamChunk(
                        content="",
                        finish_reason="stop",
                        usage=usage
                    )
                    
        except Exception as e:
            await self._handle_anthropic_error(e)
    
    async def get_available_models(self) -> List[str]:
        """Get list of available Anthropic models"""
        try:
            # Anthropic doesn't have a models endpoint, return known models
            available_models = [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229", 
                "claude-3-haiku-20240307"
            ]
            
            # Add aliases
            available_models.extend(self.model_aliases.keys())
            return sorted(list(set(available_models)))
            
        except Exception as e:
            logger.error(f"❌ Failed to get Anthropic models: {e}")
            return ["claude-3", "claude-3-sonnet", "claude-3-haiku"]
    
    async def validate_api_key(self) -> bool:
        """Validate Anthropic API key"""
        try:
            # Make a minimal request to validate key
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except Exception as e:
            logger.warning(f"⚠️ Anthropic API key validation failed: {e}")
            return False
    
    async def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate cost for Anthropic request"""
        resolved_model = self._resolve_model(request.model)
        
        # Estimate input tokens
        total_input_text = " ".join([msg.content for msg in request.messages])
        input_tokens = CostCalculator.estimate_tokens(total_input_text)
        
        # Estimate output tokens
        output_tokens = request.max_tokens or 1000  # Claude default
        
        return CostCalculator.calculate_cost(
            LLMProvider.ANTHROPIC,
            resolved_model,
            input_tokens,
            output_tokens
        )
    
    async def _handle_anthropic_error(self, error: Exception) -> None:
        """Handle Anthropic-specific errors"""
        error_message = str(error)
        
        if "rate limit" in error_message.lower():
            raise LLMRateLimitError(
                f"Anthropic rate limit exceeded: {error_message}",
                provider=LLMProvider.ANTHROPIC,
                error_code="rate_limit"
            )
        elif "authentication" in error_message.lower() or "api key" in error_message.lower():
            raise LLMAuthenticationError(
                f"Anthropic authentication failed: {error_message}",
                provider=LLMProvider.ANTHROPIC,
                error_code="auth_error"
            )
        elif "credit" in error_message.lower() or "billing" in error_message.lower():
            raise LLMQuotaExceededError(
                f"Anthropic credit/billing issue: {error_message}",
                provider=LLMProvider.ANTHROPIC,
                error_code="quota_exceeded"
            )
        elif "model" in error_message.lower() and "not found" in error_message.lower():
            raise LLMModelNotFoundError(
                f"Anthropic model not found: {error_message}",
                provider=LLMProvider.ANTHROPIC,
                error_code="model_not_found"
            )
        else:
            raise LLMError(
                f"Anthropic API error: {error_message}",
                provider=LLMProvider.ANTHROPIC,
                error_code="api_error"
            ) 