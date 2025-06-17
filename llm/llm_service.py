"""
LLM Service - High-level interface for LLM operations

Предоставляет простой интерфейс для генерации текста с автоматическим
управлением провайдерами, мониторингом и fallback.
"""

import os
import logging
from typing import Dict, Any, Optional, List
import asyncio

from .llm_router import LLMRouter, RoutingStrategy
from .providers.base import (
    LLMRequest, LLMResponse, LLMProvider, LLMModel, 
    LLMProviderConfig, LLMProviderError
)
from .providers.openai_provider import OpenAIProvider, create_openai_provider
from .providers.anthropic_provider import AnthropicProvider, create_anthropic_provider

logger = logging.getLogger(__name__)


class LLMService:
    """
    High-level LLM service with automatic provider management.
    
    Features:
    - Automatic provider initialization from environment
    - Intelligent routing and fallback
    - Cost and performance monitoring
    - Simple interface for common operations
    """
    
    def __init__(self, routing_strategy: RoutingStrategy = RoutingStrategy.BALANCED):
        self.router = LLMRouter(routing_strategy)
        self.initialized = False
        self._total_requests = 0
        self._total_cost = 0.0
        
        logger.info("LLM Service initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize LLM service with providers from environment.
        
        Returns:
            bool: True if at least one provider was initialized
        """
        providers_added = 0
        
        # OpenAI Provider
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                openai_provider = create_openai_provider(
                    api_key=openai_key,
                    model=LLMModel.GPT_4_TURBO
                )
                
                # Validate configuration
                if await openai_provider.validate_config():
                    self.router.add_provider(openai_provider)
                    providers_added += 1
                    logger.info("✅ OpenAI provider initialized")
                else:
                    logger.warning("❌ OpenAI provider validation failed")
                    
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI provider: {e}")
        else:
            logger.info("ℹ️ OpenAI API key not found, skipping OpenAI provider")
        
        # Anthropic Provider
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                anthropic_provider = create_anthropic_provider(
                    api_key=anthropic_key,
                    model=LLMModel.CLAUDE_3_SONNET
                )
                
                # Validate configuration
                if await anthropic_provider.validate_config():
                    self.router.add_provider(anthropic_provider)
                    providers_added += 1
                    logger.info("✅ Anthropic provider initialized")
                else:
                    logger.warning("❌ Anthropic provider validation failed")
                    
            except Exception as e:
                logger.error(f"❌ Failed to initialize Anthropic provider: {e}")
        else:
            logger.info("ℹ️ Anthropic API key not found, skipping Anthropic provider")
        
        # Mock Provider for testing (if no real providers available)
        if providers_added == 0:
            logger.warning("No real LLM providers available, creating mock provider")
            mock_provider = self._create_mock_provider()
            self.router.add_provider(mock_provider)
            providers_added += 1
            logger.info("✅ Mock provider initialized for testing")
        
        self.initialized = providers_added > 0
        
        if self.initialized:
            logger.info(f"🚀 LLM Service initialized with {providers_added} providers")
        else:
            logger.error("❌ LLM Service initialization failed - no providers available")
        
        return self.initialized
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """
        Generate text using the best available LLM provider.
        
        Args:
            prompt: The input prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Randomness (0.0-1.0)
            top_p: Nucleus sampling parameter
            stop_sequences: Optional stop sequences
            
        Returns:
            str: Generated text
            
        Raises:
            LLMProviderError: If all providers fail
        """
        if not self.initialized:
            await self.initialize()
        
        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop_sequences=stop_sequences
        )
        
        try:
            response = await self.router.generate(request)
            
            # Update service metrics
            self._total_requests += 1
            self._total_cost += response.cost_usd
            
            logger.info(
                f"✅ Text generated: {response.total_tokens} tokens, "
                f"${response.cost_usd:.4f}, {response.response_time:.2f}s via {response.provider.value}"
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"❌ Text generation failed: {e}")
            raise
    
    async def generate_rfc(
        self,
        task_description: str,
        project_context: Optional[str] = None,
        technical_requirements: Optional[str] = None
    ) -> str:
        """
        Generate an RFC document using specialized prompts.
        
        Args:
            task_description: Description of the task/feature
            project_context: Optional project context
            technical_requirements: Optional technical requirements
            
        Returns:
            str: Generated RFC document
        """
        system_prompt = """You are an expert technical writer and software architect. 
Generate a comprehensive RFC (Request for Comments) document that follows industry best practices.

The RFC should include:
1. Problem Statement
2. Proposed Solution
3. Technical Architecture
4. Implementation Plan
5. Testing Strategy
6. Risk Assessment
7. Timeline and Milestones

Write in clear, technical language appropriate for engineering teams."""
        
        # Build comprehensive prompt
        prompt_parts = [f"Task Description: {task_description}"]
        
        if project_context:
            prompt_parts.append(f"Project Context: {project_context}")
        
        if technical_requirements:
            prompt_parts.append(f"Technical Requirements: {technical_requirements}")
        
        prompt_parts.append("\nPlease generate a detailed RFC document for this task.")
        
        prompt = "\n\n".join(prompt_parts)
        
        return await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=4000,
            temperature=0.3  # Lower temperature for more structured output
        )
    
    async def generate_documentation(
        self,
        code: str,
        language: str = "python",
        doc_type: str = "comprehensive"
    ) -> str:
        """
        Generate documentation for code.
        
        Args:
            code: The code to document
            language: Programming language
            doc_type: Type of documentation (brief, comprehensive, api)
            
        Returns:
            str: Generated documentation
        """
        system_prompt = f"""You are an expert technical documentation writer.
Generate clear, comprehensive documentation for {language} code.

Include:
1. Overview and purpose
2. Function/class descriptions
3. Parameter documentation
4. Return value descriptions
5. Usage examples
6. Error handling
7. Dependencies

Write in clear, professional language suitable for developers."""
        
        prompt = f"""Please generate {doc_type} documentation for this {language} code:

```{language}
{code}
```

Provide thorough documentation that would help other developers understand and use this code."""
        
        return await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=3000,
            temperature=0.2  # Low temperature for consistent documentation style
        )
    
    async def answer_question(
        self,
        question: str,
        context: Optional[str] = None,
        max_tokens: int = 1000
    ) -> str:
        """
        Answer a question using available context.
        
        Args:
            question: The question to answer
            context: Optional context information
            max_tokens: Maximum response length
            
        Returns:
            str: Generated answer
        """
        system_prompt = """You are a helpful AI assistant. Provide accurate, clear, and concise answers.
If you're not certain about something, say so. Base your answers on the provided context when available."""
        
        if context:
            prompt = f"Context: {context}\n\nQuestion: {question}\n\nPlease provide a helpful answer based on the context."
        else:
            prompt = f"Question: {question}\n\nPlease provide a helpful answer."
        
        return await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=0.5
        )
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics."""
        if not self.initialized:
            return {
                "status": "not_initialized",
                "error": "Service not initialized"
            }
        
        # Get router stats
        router_stats = await self.router.get_router_stats()
        
        # Add service-level stats
        return {
            "status": "healthy" if self.initialized else "error",
            "service_metrics": {
                "total_requests": self._total_requests,
                "total_cost_usd": round(self._total_cost, 4),
                "avg_cost_per_request": round(self._total_cost / max(self._total_requests, 1), 4)
            },
            "router_stats": router_stats,
            "providers_available": len(self.router.get_available_providers())
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of all providers."""
        if not self.initialized:
            return {
                "status": "unhealthy",
                "error": "Service not initialized"
            }
        
        return await self.router.health_check_all()
    
    def _create_mock_provider(self) -> "MockLLMProvider":
        """Create a mock provider for testing."""
        from .providers.base import BaseLLMProvider
        
        class MockLLMProvider(BaseLLMProvider):
            async def generate(self, request: LLMRequest) -> LLMResponse:
                import time
                
                # Simulate processing time
                await asyncio.sleep(0.1)
                
                # Generate mock response
                mock_content = f"Mock response to: {request.prompt[:50]}..."
                
                return LLMResponse(
                    content=mock_content,
                    provider=LLMProvider.OLLAMA,  # Use as mock provider
                    model=LLMModel.LLAMA2_7B,
                    prompt_tokens=len(request.prompt) // 4,
                    completion_tokens=len(mock_content) // 4,
                    total_tokens=(len(request.prompt) + len(mock_content)) // 4,
                    response_time=0.1,
                    cost_usd=0.0,  # Mock is free
                    metadata={"mock": True}
                )
            
            async def validate_config(self) -> bool:
                return True
            
            def estimate_cost(self, request: LLMRequest) -> float:
                return 0.0
        
        config = LLMProviderConfig(
            provider=LLMProvider.OLLAMA,
            model=LLMModel.LLAMA2_7B,
            enabled=True,
            priority=10,  # Low priority
            cost_per_1k_tokens=0.0,
            quality_score=0.5
        )
        
        return MockLLMProvider(config)


# Global LLM service instance
_llm_service = None


def get_llm_service() -> LLMService:
    """Get global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


async def initialize_llm_service() -> bool:
    """Initialize the global LLM service."""
    service = get_llm_service()
    return await service.initialize() 