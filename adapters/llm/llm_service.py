"""
LLM Service - High-level interface for LLM operations

Предоставляет простой интерфейс для генерации текста с автоматическим
управлением провайдерами, мониторингом и fallback.

Updated with standardized async patterns for enterprise reliability.
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

# Import standardized async patterns
from app.core.async_utils import (
    AsyncTimeouts, 
    with_timeout, 
    async_retry,
    safe_gather,
    create_background_task
)
from app.core.exceptions import AsyncTimeoutError, AsyncRetryError

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
    
    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def initialize(self) -> bool:
        """
        Initialize LLM service with providers from environment.
        Uses concurrent initialization with timeout protection.
        
        Returns:
            bool: True if at least one provider was initialized
        """
        try:
            return await with_timeout(
                self._initialize_internal(),
                AsyncTimeouts.LLM_REQUEST,  # 60 seconds for initialization
                "LLM service initialization timed out"
            )
        except (AsyncTimeoutError, AsyncRetryError) as e:
            logger.error(f"❌ LLM service initialization failed: {e}")
            return False
    
    async def _initialize_internal(self) -> bool:
        """Internal initialization with concurrent provider setup"""
        logger.info("🔄 Initializing LLM service with concurrent provider setup...")
        
        # Prepare provider initialization tasks
        provider_tasks = []
        
        # OpenAI Provider
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            provider_tasks.append(
                ("OpenAI", self._initialize_openai_provider(openai_key))
            )
        else:
            logger.info("ℹ️ OpenAI API key not found, skipping OpenAI provider")
        
        # Anthropic Provider  
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            provider_tasks.append(
                ("Anthropic", self._initialize_anthropic_provider(anthropic_key))
            )
        else:
            logger.info("ℹ️ Anthropic API key not found, skipping Anthropic provider")
        
        # Initialize providers concurrently
        providers_added = 0
        if provider_tasks:
            logger.info(f"🔄 Initializing {len(provider_tasks)} providers concurrently...")
            
            results = await safe_gather(
                *[task for _, task in provider_tasks],
                return_exceptions=True,
                timeout=AsyncTimeouts.LLM_REQUEST,
                max_concurrency=3  # Limit concurrent provider initializations
            )
            
            # Process results
            for i, (provider_name, result) in enumerate(zip([name for name, _ in provider_tasks], results)):
                if isinstance(result, Exception):
                    logger.error(f"❌ {provider_name} provider initialization failed: {result}")
                elif result:
                    providers_added += 1
                    logger.info(f"✅ {provider_name} provider initialized successfully")
                else:
                    logger.warning(f"⚠️ {provider_name} provider validation failed")
        
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
    
    async def _initialize_openai_provider(self, api_key: str) -> bool:
        """Initialize OpenAI provider with timeout protection"""
        try:
            openai_provider = create_openai_provider(
                api_key=api_key,
                model=LLMModel.GPT_4_TURBO
            )
            
            # Validate configuration with timeout
            valid = await with_timeout(
                openai_provider.validate_config(),
                AsyncTimeouts.HTTP_REQUEST,  # 30 seconds for validation
                "OpenAI provider validation timed out"
            )
            
            if valid:
                self.router.add_provider(openai_provider)
                return True
            else:
                logger.warning("❌ OpenAI provider validation failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI provider: {e}")
            return False
    
    async def _initialize_anthropic_provider(self, api_key: str) -> bool:
        """Initialize Anthropic provider with timeout protection"""
        try:
            anthropic_provider = create_anthropic_provider(
                api_key=api_key,
                model=LLMModel.CLAUDE_3_SONNET
            )
            
            # Validate configuration with timeout
            valid = await with_timeout(
                anthropic_provider.validate_config(),
                AsyncTimeouts.HTTP_REQUEST,  # 30 seconds for validation
                "Anthropic provider validation timed out"
            )
            
            if valid:
                self.router.add_provider(anthropic_provider)
                return True
            else:
                logger.warning("❌ Anthropic provider validation failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Anthropic provider: {e}")
            return False
    
    @async_retry(max_attempts=2, delay=1.0, exceptions=(LLMProviderError,))
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
        Enhanced with timeout protection and retry logic.
        
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
            AsyncTimeoutError: If generation times out
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
            # Apply timeout based on expected generation time
            timeout = self._calculate_generation_timeout(max_tokens)
            
            response = await with_timeout(
                self.router.generate(request),
                timeout,
                f"LLM text generation timed out (prompt length: {len(prompt)}, max_tokens: {max_tokens})",
                {"prompt_length": len(prompt), "max_tokens": max_tokens, "temperature": temperature}
            )
            
            # Update service metrics
            self._total_requests += 1
            self._total_cost += response.cost_usd
            
            logger.info(
                f"✅ Text generated: {response.total_tokens} tokens, "
                f"${response.cost_usd:.4f}, {response.response_time:.2f}s via {response.provider.value}"
            )
            
            return response.content
            
        except (AsyncTimeoutError, AsyncRetryError) as e:
            logger.error(f"❌ Text generation failed with timeout/retry error: {e}")
            raise LLMProviderError(LLMProvider.OLLAMA, f"Generation failed: {e}")
        except Exception as e:
            logger.error(f"❌ Text generation failed: {e}")
            raise
    
    def _calculate_generation_timeout(self, max_tokens: int) -> float:
        """Calculate appropriate timeout based on generation requirements"""
        # Base timeout for LLM requests
        base_timeout = AsyncTimeouts.LLM_REQUEST
        
        # Add extra time for longer generations (rough estimate: 100 tokens/second)
        if max_tokens > 1000:
            extra_time = (max_tokens - 1000) / 100  # 1 second per extra 100 tokens
            return min(base_timeout + extra_time, 300.0)  # Cap at 5 minutes
        
        return base_timeout
    
    @async_retry(max_attempts=2, delay=2.0, exceptions=(LLMProviderError,))
    async def generate_rfc(
        self,
        task_description: str,
        project_context: Optional[str] = None,
        technical_requirements: Optional[str] = None
    ) -> str:
        """
        Generate an RFC document using specialized prompts.
        Enhanced with timeout protection for long-form generation.
        
        Args:
            task_description: Description of the task/feature
            project_context: Optional project context
            technical_requirements: Optional technical requirements
            
        Returns:
            str: Generated RFC document
            
        Raises:
            LLMProviderError: If RFC generation fails
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
        
        try:
            logger.info(f"🔄 Generating RFC for task: {task_description[:100]}...")
            
            # RFC generation needs more time and tokens
            return await with_timeout(
                self.generate_text(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=4000,
                    temperature=0.3  # Lower temperature for more structured output
                ),
                AsyncTimeouts.LLM_REQUEST * 2,  # 120 seconds for RFC generation
                f"RFC generation timed out for task: {task_description[:50]}...",
                {"task_description_length": len(task_description), "has_context": bool(project_context)}
            )
            
        except AsyncTimeoutError as e:
            logger.error(f"❌ RFC generation timed out: {e}")
            raise LLMProviderError(LLMProvider.OLLAMA, f"RFC generation timed out: {e}")
        except Exception as e:
            logger.error(f"❌ RFC generation failed: {e}")
            raise
    
    @async_retry(max_attempts=2, delay=1.5, exceptions=(LLMProviderError,))
    async def generate_documentation(
        self,
        code: str,
        language: str = "python",
        doc_type: str = "comprehensive"
    ) -> str:
        """
        Generate documentation for code.
        Enhanced with timeout protection and context validation.
        
        Args:
            code: The code to document
            language: Programming language
            doc_type: Type of documentation (brief, comprehensive, api)
            
        Returns:
            str: Generated documentation
            
        Raises:
            LLMProviderError: If documentation generation fails
            ValueError: If code is too large or empty
        """
        # Validate input
        if not code.strip():
            raise ValueError("Code cannot be empty")
        
        if len(code) > 50000:  # Limit code size for practical reasons
            raise ValueError(f"Code too large ({len(code)} chars). Maximum 50,000 characters.")
        
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
        
        try:
            logger.info(f"🔄 Generating {doc_type} documentation for {language} code ({len(code)} chars)...")
            
            return await with_timeout(
                self.generate_text(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=3000,
                    temperature=0.2  # Low temperature for consistent documentation style
                ),
                AsyncTimeouts.LLM_REQUEST * 1.5,  # 90 seconds for documentation
                f"Documentation generation timed out for {language} code",
                {"code_length": len(code), "language": language, "doc_type": doc_type}
            )
            
        except AsyncTimeoutError as e:
            logger.error(f"❌ Documentation generation timed out: {e}")
            raise LLMProviderError(LLMProvider.OLLAMA, f"Documentation generation timed out: {e}")
        except Exception as e:
            logger.error(f"❌ Documentation generation failed: {e}")
            raise
    
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
        """Get comprehensive service statistics with timeout protection."""
        if not self.initialized:
            return {
                "status": "not_initialized",
                "error": "Service not initialized"
            }
        
        try:
            # Get router stats with timeout
            router_stats = await with_timeout(
                self.router.get_router_stats(),
                AsyncTimeouts.DATABASE_QUERY,  # 10 seconds for stats collection
                "Service stats collection timed out"
            )
            
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
            
        except AsyncTimeoutError as e:
            logger.warning(f"⚠️ Service stats collection timed out: {e}")
            return {
                "status": "timeout",
                "error": f"Stats collection timed out: {e}",
                "service_metrics": {
                    "total_requests": self._total_requests,
                    "total_cost_usd": round(self._total_cost, 4),
                    "avg_cost_per_request": round(self._total_cost / max(self._total_requests, 1), 4)
                }
            }
        except Exception as e:
            logger.error(f"❌ Failed to get service stats: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of all providers with timeout protection."""
        if not self.initialized:
            return {
                "status": "unhealthy",
                "error": "Service not initialized"
            }
        
        try:
            # Health check with timeout
            health_results = await with_timeout(
                self.router.health_check_all(),
                AsyncTimeouts.HTTP_REQUEST,  # 30 seconds for health checks
                "LLM service health check timed out"
            )
            
            # Add service-level health information
            health_results.update({
                "service_initialized": self.initialized,
                "total_requests_processed": self._total_requests,
                "service_uptime_info": "healthy" if self.initialized else "not_initialized"
            })
            
            return health_results
            
        except AsyncTimeoutError as e:
            logger.warning(f"⚠️ Health check timed out: {e}")
            return {
                "status": "timeout",
                "error": f"Health check timed out: {e}",
                "service_initialized": self.initialized,
                "providers_available": len(self.router.get_available_providers()) if hasattr(self.router, 'get_available_providers') else 0
            }
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "service_initialized": self.initialized
            }
    
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