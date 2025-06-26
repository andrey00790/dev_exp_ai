"""
LLM Service for AI Assistant MVP
Handles interactions with various LLM providers
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    LOCAL = "local"


class LLMModel(str, Enum):
    """Supported LLM models"""
    # OpenAI
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    
    # Anthropic
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    
    # Ollama/Local
    LLAMA2 = "llama2"
    MISTRAL = "mistral"
    CODELLAMA = "codellama"


class LLMRequest:
    """LLM request model"""
    def __init__(
        self,
        prompt: str,
        model: LLMModel = LLMModel.GPT_3_5_TURBO,
        provider: Optional[LLMProvider] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        user_id: Optional[str] = None,
    ):
        self.prompt = prompt
        self.model = model
        self.provider = provider or self._detect_provider(model)
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.system_prompt = system_prompt
        self.context = context or []
        self.user_id = user_id
        self.created_at = datetime.utcnow()
    
    def _detect_provider(self, model: LLMModel) -> LLMProvider:
        """Auto-detect provider from model"""
        if model.value.startswith("gpt"):
            return LLMProvider.OPENAI
        elif model.value.startswith("claude"):
            return LLMProvider.ANTHROPIC
        else:
            return LLMProvider.OLLAMA


class LLMResponse:
    """LLM response model"""
    def __init__(
        self,
        content: str,
        model: LLMModel,
        provider: LLMProvider,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        response_time_ms: float = 0.0,
        request_id: Optional[str] = None,
    ):
        self.content = content
        self.model = model
        self.provider = provider
        self.tokens_used = tokens_used
        self.cost_usd = cost_usd
        self.response_time_ms = response_time_ms
        self.request_id = request_id
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content": self.content,
            "model": self.model.value,
            "provider": self.provider.value,
            "tokens_used": self.tokens_used,
            "cost_usd": self.cost_usd,
            "response_time_ms": self.response_time_ms,
            "request_id": self.request_id,
            "created_at": self.created_at.isoformat(),
        }


class LLMService:
    """Main LLM service class"""
    
    def __init__(self):
        self.providers = {
            LLMProvider.OPENAI: self._mock_openai_client,
            LLMProvider.ANTHROPIC: self._mock_anthropic_client,
            LLMProvider.OLLAMA: self._mock_ollama_client,
            LLMProvider.LOCAL: self._mock_local_client,
        }
        self.request_count = 0
        self.total_cost = 0.0
        
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using specified LLM"""
        start_time = time.time()
        self.request_count += 1
        
        try:
            # Get provider client
            provider_client = self.providers.get(request.provider)
            if not provider_client:
                raise ValueError(f"Unsupported provider: {request.provider}")
            
            # Generate response
            response = await provider_client(request)
            
            # Calculate metrics
            response.response_time_ms = (time.time() - start_time) * 1000
            response.request_id = f"req_{self.request_count}_{int(time.time())}"
            
            # Update cost tracking
            self.total_cost += response.cost_usd
            
            logger.info(
                f"LLM request completed: {request.model.value} -> "
                f"{response.tokens_used} tokens, ${response.cost_usd:.4f}, "
                f"{response.response_time_ms:.1f}ms"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            # Return error response
            return LLMResponse(
                content=f"Error: {str(e)}",
                model=request.model,
                provider=request.provider,
                response_time_ms=(time.time() - start_time) * 1000,
            )
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: LLMModel = LLMModel.GPT_3_5_TURBO,
        user_id: Optional[str] = None,
    ) -> LLMResponse:
        """Chat interface for multi-turn conversations"""
        # Convert messages to prompt
        prompt = self._messages_to_prompt(messages)
        
        request = LLMRequest(
            prompt=prompt,
            model=model,
            context=messages,
            user_id=user_id,
        )
        
        return await self.generate(request)
    
    async def complete(
        self,
        prompt: str,
        model: LLMModel = LLMModel.GPT_3_5_TURBO,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        user_id: Optional[str] = None,
    ) -> LLMResponse:
        """Simple completion interface"""
        request = LLMRequest(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            user_id=user_id,
        )
        
        return await self.generate(request)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "total_requests": self.request_count,
            "total_cost_usd": self.total_cost,
            "supported_providers": [p.value for p in LLMProvider],
            "supported_models": [m.value for m in LLMModel],
        }
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to single prompt"""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_parts.append(f"{role.title()}: {content}")
        return "\n".join(prompt_parts)
    
    # Mock provider implementations (replace with real implementations)
    
    async def _mock_openai_client(self, request: LLMRequest) -> LLMResponse:
        """Mock OpenAI client"""
        await asyncio.sleep(0.5)  # Simulate API delay
        
        # Calculate mock cost
        cost_per_token = 0.002 / 1000  # $0.002 per 1K tokens
        tokens = min(request.max_tokens, len(request.prompt.split()) * 1.3)
        cost = tokens * cost_per_token
        
        return LLMResponse(
            content=f"OpenAI {request.model.value} response to: {request.prompt[:50]}...",
            model=request.model,
            provider=LLMProvider.OPENAI,
            tokens_used=int(tokens),
            cost_usd=cost,
        )
    
    async def _mock_anthropic_client(self, request: LLMRequest) -> LLMResponse:
        """Mock Anthropic client"""
        await asyncio.sleep(0.7)  # Simulate API delay
        
        # Calculate mock cost
        cost_per_token = 0.008 / 1000  # $0.008 per 1K tokens
        tokens = min(request.max_tokens, len(request.prompt.split()) * 1.3)
        cost = tokens * cost_per_token
        
        return LLMResponse(
            content=f"Claude {request.model.value} response to: {request.prompt[:50]}...",
            model=request.model,
            provider=LLMProvider.ANTHROPIC,
            tokens_used=int(tokens),
            cost_usd=cost,
        )
    
    async def _mock_ollama_client(self, request: LLMRequest) -> LLMResponse:
        """Mock Ollama client"""
        await asyncio.sleep(1.0)  # Simulate local processing delay
        
        tokens = min(request.max_tokens, len(request.prompt.split()) * 1.3)
        
        return LLMResponse(
            content=f"Ollama {request.model.value} response to: {request.prompt[:50]}...",
            model=request.model,
            provider=LLMProvider.OLLAMA,
            tokens_used=int(tokens),
            cost_usd=0.0,  # Local models are free
        )
    
    async def _mock_local_client(self, request: LLMRequest) -> LLMResponse:
        """Mock local client"""
        await asyncio.sleep(0.3)  # Fast local processing
        
        tokens = min(request.max_tokens, len(request.prompt.split()) * 1.3)
        
        return LLMResponse(
            content=f"Local {request.model.value} response to: {request.prompt[:50]}...",
            model=request.model,
            provider=LLMProvider.LOCAL,
            tokens_used=int(tokens),
            cost_usd=0.0,  # Local models are free
        )


# Global service instance
llm_service = LLMService()


# Convenience functions
async def generate_text(
    prompt: str,
    model: LLMModel = LLMModel.GPT_3_5_TURBO,
    max_tokens: int = 1000,
    temperature: float = 0.7,
    user_id: Optional[str] = None,
) -> str:
    """Simple text generation function"""
    response = await llm_service.complete(
        prompt=prompt,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        user_id=user_id,
    )
    return response.content


async def chat_completion(
    messages: List[Dict[str, str]],
    model: LLMModel = LLMModel.GPT_3_5_TURBO,
    user_id: Optional[str] = None,
) -> str:
    """Simple chat completion function"""
    response = await llm_service.chat(
        messages=messages,
        model=model,
        user_id=user_id,
    )
    return response.content 