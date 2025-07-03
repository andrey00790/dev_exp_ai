"""
Anthropic (Claude) LLM Provider.

Интеграция с Anthropic API для Claude 3 моделей.
"""

import time
from typing import Dict, Any, Optional
import logging

try:
    import anthropic
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base import (
    BaseLLMProvider, LLMRequest, LLMResponse, LLMProviderConfig,
    LLMProvider, LLMModel, LLMProviderError, LLMRateLimitError,
    LLMQuotaError, LLMAuthenticationError
)

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider с поддержкой Claude 3 моделей."""
    
    # Стоимость моделей (USD за 1K токенов)
    MODEL_COSTS = {
        LLMModel.CLAUDE_3_OPUS: {"input": 0.015, "output": 0.075},
        LLMModel.CLAUDE_3_SONNET: {"input": 0.003, "output": 0.015},
        LLMModel.CLAUDE_3_HAIKU: {"input": 0.00025, "output": 0.00125},
    }
    
    def __init__(self, config: LLMProviderConfig):
        if not ANTHROPIC_AVAILABLE:
            raise LLMProviderError(
                LLMProvider.ANTHROPIC,
                "Anthropic package not installed. Install with: pip install anthropic"
            )
        
        super().__init__(config)
        
        # Инициализация клиента
        self.client = AsyncAnthropic(
            api_key=config.api_key,
            base_url=config.api_base,
            timeout=config.timeout,
            max_retries=config.max_retries
        )
        
        logger.info(f"Anthropic provider initialized with model {config.model.value}")
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Генерирует ответ через Anthropic API."""
        start_time = time.time()
        
        try:
            # Подготовка параметров запроса
            kwargs = {
                "model": self.config.model.value,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
            }
            
            # Anthropic использует messages format
            messages = [{"role": "user", "content": request.prompt}]
            kwargs["messages"] = messages
            
            # System prompt передается отдельно
            if request.system_prompt:
                kwargs["system"] = request.system_prompt
            
            if request.stop_sequences:
                kwargs["stop_sequences"] = request.stop_sequences
            
            # Выполнение запроса
            logger.debug(f"Making Anthropic request with model {self.config.model.value}")
            response = await self.client.messages.create(**kwargs)
            
            # Извлечение данных
            content = response.content[0].text
            usage = response.usage
            
            # Расчет стоимости
            cost = self._calculate_cost(usage.input_tokens, usage.output_tokens)
            
            # Создание ответа
            llm_response = LLMResponse(
                content=content,
                provider=LLMProvider.ANTHROPIC,
                model=self.config.model,
                prompt_tokens=usage.input_tokens,
                completion_tokens=usage.output_tokens,
                total_tokens=usage.input_tokens + usage.output_tokens,
                response_time=time.time() - start_time,
                cost_usd=cost,
                metadata={
                    "stop_reason": response.stop_reason,
                    "stop_sequence": response.stop_sequence,
                    "model_used": response.model,
                    "id": response.id,
                    "role": response.role
                }
            )
            
            # Обновление метрик
            self._update_metrics(llm_response)
            
            logger.info(
                f"Anthropic request completed: {llm_response.total_tokens} tokens, "
                f"${cost:.4f}, {llm_response.response_time:.2f}s"
            )
            
            return llm_response
            
        except anthropic.RateLimitError as e:
            logger.warning(f"Anthropic rate limit exceeded: {e}")
            raise LLMRateLimitError(LLMProvider.ANTHROPIC, str(e), e)
            
        except anthropic.AuthenticationError as e:
            logger.error(f"Anthropic authentication failed: {e}")
            raise LLMAuthenticationError(LLMProvider.ANTHROPIC, str(e), e)
            
        except anthropic.BadRequestError as e:
            logger.error(f"Anthropic bad request: {e}")
            raise LLMProviderError(LLMProvider.ANTHROPIC, f"Bad request: {e}", e)
            
        except Exception as e:
            logger.error(f"Anthropic request failed: {e}")
            raise LLMProviderError(LLMProvider.ANTHROPIC, f"Request failed: {e}", e)
    
    async def validate_config(self) -> bool:
        """Проверяет валидность конфигурации Anthropic."""
        try:
            # Простой тестовый запрос
            test_request = LLMRequest(
                prompt="Hello, Claude!",
                max_tokens=10,
                temperature=0.0
            )
            
            await self.generate(test_request)
            logger.info("Anthropic configuration validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Anthropic configuration validation failed: {e}")
            return False
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """Оценивает стоимость запроса Anthropic."""
        if self.config.model not in self.MODEL_COSTS:
            logger.warning(f"No cost data for model {self.config.model.value}")
            return 0.0
        
        # Примерная оценка токенов (4 символа = 1 токен)
        estimated_prompt_tokens = len(request.prompt) // 4
        if request.system_prompt:
            estimated_prompt_tokens += len(request.system_prompt) // 4
        
        estimated_completion_tokens = request.max_tokens
        
        return self._calculate_cost(estimated_prompt_tokens, estimated_completion_tokens)
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Вычисляет точную стоимость запроса."""
        if self.config.model not in self.MODEL_COSTS:
            return 0.0
        
        costs = self.MODEL_COSTS[self.config.model]
        
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        
        return input_cost + output_cost


def create_anthropic_provider(api_key: str, model: LLMModel = LLMModel.CLAUDE_3_SONNET) -> AnthropicProvider:
    """Фабричная функция для создания Anthropic провайдера."""
    config = LLMProviderConfig(
        provider=LLMProvider.ANTHROPIC,
        model=model,
        api_key=api_key,
        max_retries=3,
        timeout=60.0,
        priority=1,
        cost_per_1k_tokens=AnthropicProvider.MODEL_COSTS.get(model, {}).get("input", 0.003),
        rate_limit_rpm=50,  # Claude имеет более низкие rate limits
        quality_score=0.95  # Claude известен высоким качеством
    )
    
    return AnthropicProvider(config) 