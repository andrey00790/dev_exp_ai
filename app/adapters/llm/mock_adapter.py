"""
Mock LLM Adapter для AI Assistant MVP
Mock реализация BaseLLMAdapter для тестирования без реальных API вызовов
"""

import asyncio
import logging
from typing import List, AsyncIterator, Optional, Dict, Any
from datetime import datetime
import random
import time

from .base import (
    BaseLLMAdapter, LLMProvider, LLMMessage, LLMRequest, LLMResponse, 
    LLMStreamChunk, LLMUsage, MessageRole, LLMError, CostCalculator
)

logger = logging.getLogger(__name__)

class MockLLMAdapter(BaseLLMAdapter):
    """Mock implementation of BaseLLMAdapter for testing"""
    
    def __init__(self, api_key: str = "mock-api-key", base_url: Optional[str] = None,
                 timeout: int = 60, max_retries: int = 3, 
                 simulate_errors: bool = False, response_delay: float = 0.1):
        super().__init__(api_key, base_url, timeout, max_retries)
        self.simulate_errors = simulate_errors
        self.response_delay = response_delay
        
        # Mock responses for different scenarios
        self.mock_responses = {
            "default": "This is a mock response from the AI assistant. I understand your request and I'm ready to help you with various tasks.",
            "greeting": "Hello! I'm a mock AI assistant. How can I help you today?",
            "error": "I apologize, but I encountered an error while processing your request.",
            "long": "This is a longer mock response that simulates a more detailed answer. " * 10,
            "code": "```python\ndef hello_world():\n    return 'Hello, World!'\n```",
            "json": '{"status": "success", "data": {"message": "Mock JSON response", "timestamp": "2024-12-28T15:00:00Z"}}'
        }
        
        # Available mock models
        self.available_models = [
            "mock-gpt-4",
            "mock-gpt-3.5-turbo", 
            "mock-claude-3",
            "mock-llama-2",
            "mock-small",
            "mock-large"
        ]
    
    def get_provider(self) -> LLMProvider:
        return LLMProvider.MOCK
    
    def _get_mock_response(self, request: LLMRequest) -> str:
        """Generate appropriate mock response based on request"""
        if not request.messages:
            return self.mock_responses["default"]
        
        last_message = request.messages[-1].content.lower()
        
        # Pattern matching for different response types
        if any(word in last_message for word in ["hello", "hi", "greeting"]):
            return self.mock_responses["greeting"]
        elif any(word in last_message for word in ["code", "python", "function"]):
            return self.mock_responses["code"]  
        elif any(word in last_message for word in ["json", "data", "api"]):
            return self.mock_responses["json"]
        elif len(last_message) > 200:  # Long query gets long response
            return self.mock_responses["long"]
        elif self.simulate_errors and random.random() < 0.1:  # 10% chance of error
            return self.mock_responses["error"]
        else:
            return self.mock_responses["default"]
    
    def _calculate_mock_tokens(self, text: str) -> int:
        """Calculate mock token count"""
        return max(1, len(text) // 4)  # Rough estimation
    
    async def chat_completion(self, request: LLMRequest) -> LLMResponse:
        """Mock chat completion"""
        # Simulate processing delay
        await asyncio.sleep(self.response_delay)
        
        # Generate mock response
        response_content = self._get_mock_response(request)
        
        # Calculate mock usage
        input_text = " ".join([msg.content for msg in request.messages])
        input_tokens = self._calculate_mock_tokens(input_text)
        output_tokens = self._calculate_mock_tokens(response_content)
        total_tokens = input_tokens + output_tokens
        
        # Mock cost calculation (much cheaper than real APIs)
        cost = total_tokens * 0.00001  # $0.00001 per token
        
        usage = LLMUsage(
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost
        )
        
        return LLMResponse(
            content=response_content,
            role=MessageRole.ASSISTANT,
            finish_reason="stop",
            usage=usage,
            model=request.model,
            provider=LLMProvider.MOCK,
            response_id=f"mock-{int(time.time())}-{random.randint(1000, 9999)}",
            created_at=datetime.now(),
            metadata={
                "mock": True,
                "response_type": "complete",
                "simulated_delay": self.response_delay
            }
        )
    
    async def chat_completion_stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Mock streaming chat completion"""
        response_content = self._get_mock_response(request)
        
        # Split response into chunks
        words = response_content.split()
        chunk_size = 3  # 3 words per chunk
        
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_content = " ".join(chunk_words)
            
            # Add space after chunk (except last one)
            if i + chunk_size < len(words):
                chunk_content += " "
            
            # Simulate streaming delay
            await asyncio.sleep(self.response_delay / 10)
            
            # Determine if this is the last chunk
            is_last_chunk = i + chunk_size >= len(words)
            
            # Create usage for last chunk
            usage = None
            if is_last_chunk:
                input_text = " ".join([msg.content for msg in request.messages])
                input_tokens = self._calculate_mock_tokens(input_text)
                output_tokens = self._calculate_mock_tokens(response_content)
                cost = (input_tokens + output_tokens) * 0.00001
                
                usage = LLMUsage(
                    prompt_tokens=input_tokens,
                    completion_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                    cost_usd=cost
                )
            
            yield LLMStreamChunk(
                content=chunk_content,
                finish_reason="stop" if is_last_chunk else None,
                delta={"content": chunk_content},
                usage=usage
            )
    
    async def get_available_models(self) -> List[str]:
        """Get mock available models"""
        # Simulate slight delay
        await asyncio.sleep(0.05)
        return self.available_models.copy()
    
    async def validate_api_key(self) -> bool:
        """Mock API key validation"""
        # Simulate delay
        await asyncio.sleep(0.1)
        
        # Mock validation logic
        if self.api_key == "invalid-key":
            return False
        elif self.simulate_errors and random.random() < 0.05:  # 5% chance of failure
            return False
        else:
            return True
    
    async def estimate_cost(self, request: LLMRequest) -> float:
        """Mock cost estimation"""
        # Calculate estimated tokens
        input_text = " ".join([msg.content for msg in request.messages])
        input_tokens = self._calculate_mock_tokens(input_text)
        output_tokens = request.max_tokens or 150
        
        # Mock pricing (very cheap)
        return (input_tokens + output_tokens) * 0.00001
    
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check"""
        await asyncio.sleep(0.05)
        
        return {
            "status": "healthy",
            "provider": self.provider.value,
            "api_key_valid": await self.validate_api_key(),
            "available_models": len(self.available_models),
            "base_url": self.base_url,
            "mock_config": {
                "simulate_errors": self.simulate_errors,
                "response_delay": self.response_delay,
                "total_responses": len(self.mock_responses)
            }
        }

# Helper function to create pre-configured mock adapters

def create_fast_mock_adapter() -> MockLLMAdapter:
    """Create a fast mock adapter for quick testing"""
    return MockLLMAdapter(response_delay=0.01, simulate_errors=False)

def create_slow_mock_adapter() -> MockLLMAdapter:
    """Create a slow mock adapter to simulate real API delays"""
    return MockLLMAdapter(response_delay=1.0, simulate_errors=False)

def create_error_mock_adapter() -> MockLLMAdapter:
    """Create a mock adapter that simulates errors"""
    return MockLLMAdapter(response_delay=0.1, simulate_errors=True) 