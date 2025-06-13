"""
OpenAI LLM Provider.

Интеграция с OpenAI API для GPT-4, GPT-3.5-turbo и других моделей.
"""

import asyncio
import time
from typing import Dict, Any, Optional
import logging

try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base import (
    BaseLLMProvider, LLMRequest, LLMResponse, LLMProviderConfig,
    LLMProvider, LLMModel, LLMProviderError, LLMRateLimitError,
    LLMQuotaError, LLMAuthenticationError
)

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider с поддержкой GPT-4, GPT-3.5 и других моделей."""
    
    # Стоимость моделей (USD за 1K токенов)
    MODEL_COSTS = {
        LLMModel.GPT_4: {"input": 0.03, "output": 0.06},
        LLMModel.GPT_4_TURBO: {"input": 0.01, "output": 0.03},
        LLMModel.GPT_3_5_TURBO: {"input": 0.0015, "output": 0.002},
    }
    
    def __init__(self, config: LLMProviderConfig):
        if not OPENAI_AVAILABLE:
            raise LLMProviderError(
                LLMProvider.OPENAI,
                "OpenAI package not installed. Install with: pip install openai"
            )
        
        super().__init__(config)
        
        # Инициализация клиента
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            organization=config.organization,
            base_url=config.api_base,
            timeout=config.timeout,
            max_retries=config.max_retries
        )
        
        logger.info(f"OpenAI provider initialized with model {config.model.value}")
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Генерирует ответ через OpenAI API."""
        start_time = time.time()
        
        try:
            # Подготовка сообщений
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            
            # Параметры запроса
            kwargs = {
                "model": self.config.model.value,
                "messages": messages,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
            }
            
            if request.stop_sequences:
                kwargs["stop"] = request.stop_sequences
            
            # Выполнение запроса
            logger.debug(f"Making OpenAI request with model {self.config.model.value}")
            response = await self.client.chat.completions.create(**kwargs)
            
            # Извлечение данных
            content = response.choices[0].message.content
            usage = response.usage
            
            # Расчет стоимости
            cost = self._calculate_cost(usage.prompt_tokens, usage.completion_tokens)
            
            # Создание ответа
            llm_response = LLMResponse(
                content=content,
                provider=LLMProvider.OPENAI,
                model=self.config.model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                response_time=time.time() - start_time,
                cost_usd=cost,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "model_used": response.model,
                    "request_id": response.id,
                    "created": response.created
                }
            )
            
            # Обновление метрик
            self._update_metrics(llm_response)
            
            logger.info(
                f"OpenAI request completed: {usage.total_tokens} tokens, "
                f"${cost:.4f}, {llm_response.response_time:.2f}s"
            )
            
            return llm_response
            
        except openai.RateLimitError as e:
            logger.warning(f"OpenAI rate limit exceeded: {e}")
            raise LLMRateLimitError(LLMProvider.OPENAI, str(e), e)
            
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication failed: {e}")
            raise LLMAuthenticationError(LLMProvider.OPENAI, str(e), e)
            
        except openai.BadRequestError as e:
            logger.error(f"OpenAI bad request: {e}")
            raise LLMProviderError(LLMProvider.OPENAI, f"Bad request: {e}", e)
            
        except Exception as e:
            logger.error(f"OpenAI request failed: {e}")
            raise LLMProviderError(LLMProvider.OPENAI, f"Request failed: {e}", e)
    
    async def validate_config(self) -> bool:
        """Проверяет валидность конфигурации OpenAI."""
        try:
            # Простой тестовый запрос
            test_request = LLMRequest(
                prompt="Hello",
                max_tokens=5,
                temperature=0.0
            )
            
            await self.generate(test_request)
            logger.info("OpenAI configuration validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"OpenAI configuration validation failed: {e}")
            return False
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """Оценивает стоимость запроса OpenAI."""
        if self.config.model not in self.MODEL_COSTS:
            logger.warning(f"No cost data for model {self.config.model.value}")
            return 0.0
        
        # Примерная оценка токенов (4 символа = 1 токен)
        estimated_prompt_tokens = len(request.prompt) // 4
        if request.system_prompt:
            estimated_prompt_tokens += len(request.system_prompt) // 4
        
        estimated_completion_tokens = request.max_tokens
        
        return self._calculate_cost(estimated_prompt_tokens, estimated_completion_tokens)
    
    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Вычисляет точную стоимость запроса."""
        if self.config.model not in self.MODEL_COSTS:
            return 0.0
        
        costs = self.MODEL_COSTS[self.config.model]
        
        input_cost = (prompt_tokens / 1000) * costs["input"]
        output_cost = (completion_tokens / 1000) * costs["output"]
        
        return input_cost + output_cost
    
    async def get_available_models(self) -> Dict[str, Any]:
        """Получает список доступных моделей OpenAI."""
        try:
            models = await self.client.models.list()
            
            return {
                "provider": "openai",
                "models": [
                    {
                        "id": model.id,
                        "object": model.object,
                        "created": model.created,
                        "owned_by": model.owned_by
                    }
                    for model in models.data
                    if "gpt" in model.id.lower()
                ],
                "total_count": len(models.data)
            }
            
        except Exception as e:
            logger.error(f"Failed to get OpenAI models: {e}")
            return {"provider": "openai", "models": [], "error": str(e)}


def create_openai_provider(api_key: str, model: LLMModel = LLMModel.GPT_4_TURBO) -> OpenAIProvider:
    """Фабричная функция для создания OpenAI провайдера."""
    config = LLMProviderConfig(
        provider=LLMProvider.OPENAI,
        model=model,
        api_key=api_key,
        max_retries=3,
        timeout=60.0,
        priority=1,
        cost_per_1k_tokens=OpenAIProvider.MODEL_COSTS.get(model, {}).get("input", 0.01),
        rate_limit_rpm=60,
        quality_score=0.9
    )
    
    return OpenAIProvider(config) 