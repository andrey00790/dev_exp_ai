"""
Ollama LLM Provider.

Интеграция с локальными моделями через Ollama API.
"""

import asyncio
import time
import json
import logging
from typing import Dict, Any, Optional, List
import aiohttp

from .base import (
    BaseLLMProvider, LLMRequest, LLMResponse, LLMProviderConfig,
    LLMProvider, LLMModel, LLMProviderError, LLMRateLimitError
)

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Ollama provider для локальных моделей."""
    
    def __init__(self, config: LLMProviderConfig, base_url: str = "http://localhost:11434"):
        super().__init__(config)
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        
        logger.info(f"Ollama provider initialized with model {config.model.value} at {base_url}")
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Генерирует ответ через Ollama API."""
        start_time = time.time()
        
        try:
            # Подготовка запроса
            system_prompt = request.system_prompt or ""
            full_prompt = f"{system_prompt}\n\nUser: {request.prompt}\n\nAssistant:"
            
            payload = {
                "model": self.config.model.value,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                    "num_predict": request.max_tokens,
                }
            }
            
            if request.stop_sequences:
                payload["options"]["stop"] = request.stop_sequences
            
            # Выполнение запроса
            logger.debug(f"Making Ollama request with model {self.config.model.value}")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as session:
                async with session.post(
                    f"{self.api_url}/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 404:
                        raise LLMProviderError(
                            LLMProvider.OLLAMA, 
                            f"Model {self.config.model.value} not found. Please pull it first with: ollama pull {self.config.model.value}"
                        )
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise LLMProviderError(
                            LLMProvider.OLLAMA,
                            f"Ollama API error: {response.status}, {error_text}"
                        )
                    
                    result = await response.json()
            
            # Извлечение данных
            content = result.get("response", "").strip()
            
            # Ollama не всегда возвращает точную информацию о токенах
            # Используем приблизительную оценку: 4 символа = 1 токен
            prompt_tokens = len(full_prompt) // 4
            completion_tokens = len(content) // 4
            total_tokens = prompt_tokens + completion_tokens
            
            # Локальные модели бесплатны
            cost = 0.0
            
            # Создание ответа
            llm_response = LLMResponse(
                content=content,
                provider=LLMProvider.OLLAMA,
                model=self.config.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                response_time=time.time() - start_time,
                cost_usd=cost,
                metadata={
                    "model_used": result.get("model", self.config.model.value),
                    "context": result.get("context", []),
                    "eval_count": result.get("eval_count", 0),
                    "eval_duration": result.get("eval_duration", 0),
                    "load_duration": result.get("load_duration", 0),
                    "prompt_eval_count": result.get("prompt_eval_count", 0),
                    "prompt_eval_duration": result.get("prompt_eval_duration", 0),
                    "total_duration": result.get("total_duration", 0)
                }
            )
            
            # Обновление метрик
            self._update_metrics(llm_response)
            
            logger.info(
                f"Ollama request completed: {total_tokens} tokens, "
                f"${cost:.4f}, {llm_response.response_time:.2f}s"
            )
            
            return llm_response
            
        except aiohttp.ClientError as e:
            logger.error(f"Ollama connection error: {e}")
            raise LLMProviderError(
                LLMProvider.OLLAMA, 
                f"Connection error: {e}. Make sure Ollama is running at {self.base_url}"
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Ollama request timeout after {self.config.timeout}s")
            raise LLMProviderError(
                LLMProvider.OLLAMA,
                f"Request timeout after {self.config.timeout}s"
            )
            
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            raise LLMProviderError(LLMProvider.OLLAMA, f"Request failed: {e}")
    
    async def validate_config(self) -> bool:
        """Проверяет валидность конфигурации Ollama."""
        try:
            # Проверяем доступность Ollama API
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.api_url}/tags") as response:
                    if response.status != 200:
                        return False
                    
                    data = await response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    
                    if self.config.model.value not in models:
                        logger.warning(
                            f"Model {self.config.model.value} not found in Ollama. "
                            f"Available models: {models}"
                        )
                        return False
            
            # Тестовый запрос
            test_request = LLMRequest(
                prompt="Hello",
                max_tokens=5,
                temperature=0.0
            )
            
            await self.generate(test_request)
            logger.info("Ollama configuration validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Ollama configuration validation failed: {e}")
            return False
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """Оценивает стоимость запроса Ollama (всегда 0.0 для локальных моделей)."""
        return 0.0
    
    async def get_available_models(self) -> Dict[str, Any]:
        """Получает список доступных моделей Ollama."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.api_url}/tags") as response:
                    if response.status != 200:
                        return {"provider": "ollama", "models": [], "error": "Failed to connect to Ollama"}
                    
                    data = await response.json()
                    models = data.get("models", [])
                    
                    return {
                        "provider": "ollama",
                        "models": [
                            {
                                "name": model["name"],
                                "modified_at": model.get("modified_at", ""),
                                "size": model.get("size", 0),
                                "digest": model.get("digest", ""),
                            }
                            for model in models
                        ],
                        "total_count": len(models),
                        "base_url": self.base_url
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get Ollama models: {e}")
            return {"provider": "ollama", "models": [], "error": str(e)}
    
    async def pull_model(self, model_name: str) -> Dict[str, Any]:
        """Загружает модель в Ollama."""
        try:
            payload = {"name": model_name}
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
                async with session.post(
                    f"{self.api_url}/pull",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Failed to pull model: {response.status}, {error_text}"
                        }
                    
                    return {"success": True, "model": model_name}
                    
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return {"success": False, "error": str(e)}


def create_ollama_provider(
    model: LLMModel = LLMModel.MISTRAL_INSTRUCT,
    base_url: str = "http://localhost:11434"
) -> OllamaProvider:
    """Фабричная функция для создания Ollama провайдера."""
    config = LLMProviderConfig(
        provider=LLMProvider.OLLAMA,
        model=model,
        max_retries=3,
        timeout=120.0,  # Ollama может быть медленным
        priority=3,  # Низкий приоритет (локальные модели как fallback)
        cost_per_1k_tokens=0.0,  # Бесплатно
        rate_limit_rpm=1000,  # Высокий лимит для локальных моделей
        quality_score=0.7  # Обычно ниже чем у коммерческих API
    )
    
    return OllamaProvider(config, base_url) 