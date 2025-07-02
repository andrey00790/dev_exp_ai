"""
Base LLM Provider Interface.

Определяет единый интерфейс для всех LLM провайдеров.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Поддерживаемые LLM провайдеры."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    OLLAMA = "ollama"
    AZURE_OPENAI = "azure_openai"
    GOOGLE_PALM = "google_palm"


class LLMModel(Enum):
    """Модели для каждого провайдера."""
    # OpenAI
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    
    # Anthropic
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    
    # Cohere
    COMMAND_R_PLUS = "command-r-plus"
    COMMAND_R = "command-r"
    
    # Ollama (local)
    MISTRAL_INSTRUCT = "mistral:instruct"
    LLAMA2_7B = "llama2:7b"
    CODELLAMA_13B = "codellama:13b"
    
    # Google PaLM
    PALM_2 = "models/text-bison-001"


@dataclass
class LLMRequest:
    """Запрос к LLM провайдеру."""
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.7
    top_p: float = 0.9
    stop_sequences: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """Ответ от LLM провайдера."""
    content: str
    provider: LLMProvider
    model: LLMModel
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    response_time: float  # в секундах
    cost_usd: float
    metadata: Dict[str, Any]


@dataclass
class LLMProviderConfig:
    """Конфигурация LLM провайдера."""
    provider: LLMProvider
    model: LLMModel
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    organization: Optional[str] = None
    max_retries: int = 3
    timeout: float = 60.0
    enabled: bool = True
    priority: int = 1  # 1 = highest priority
    cost_per_1k_tokens: float = 0.0
    rate_limit_rpm: int = 60  # requests per minute
    quality_score: float = 0.8  # 0-1, historical quality


class BaseLLMProvider(ABC):
    """Базовый класс для всех LLM провайдеров."""
    
    def __init__(self, config: LLMProviderConfig):
        self.config = config
        self.provider = config.provider
        self.model = config.model
        self._request_count = 0
        self._total_cost = 0.0
        self._total_tokens = 0
        
        logger.info(f"Initialized {self.provider.value} provider with model {self.model.value}")
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Генерирует ответ от LLM провайдера.
        
        Args:
            request: Запрос к модели
            
        Returns:
            LLMResponse: Ответ с метриками
            
        Raises:
            LLMProviderError: При ошибках генерации
        """
        pass
    
    @abstractmethod
    async def validate_config(self) -> bool:
        """Проверяет валидность конфигурации провайдера."""
        pass
    
    @abstractmethod
    def estimate_cost(self, request: LLMRequest) -> float:
        """Оценивает стоимость запроса в USD."""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверяет здоровье провайдера."""
        try:
            test_request = LLMRequest(
                prompt="Say 'OK' if you can respond.",
                max_tokens=10,
                temperature=0.0
            )
            
            start_time = time.time()
            response = await self.generate(test_request)
            response_time = time.time() - start_time
            
            return {
                "provider": self.provider.value,
                "model": self.model.value,
                "status": "healthy",
                "response_time": response_time,
                "tokens_used": response.total_tokens,
                "cost": response.cost_usd
            }
            
        except Exception as e:
            return {
                "provider": self.provider.value,
                "model": self.model.value,
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Возвращает метрики использования провайдера."""
        return {
            "provider": self.provider.value,
            "model": self.model.value,
            "request_count": self._request_count,
            "total_cost_usd": round(self._total_cost, 4),
            "total_tokens": self._total_tokens,
            "avg_cost_per_request": round(self._total_cost / max(self._request_count, 1), 4),
            "enabled": self.config.enabled,
            "priority": self.config.priority,
            "quality_score": self.config.quality_score
        }
    
    def _update_metrics(self, response: LLMResponse):
        """Обновляет внутренние метрики."""
        self._request_count += 1
        self._total_cost += response.cost_usd
        self._total_tokens += response.total_tokens


class LLMProviderError(Exception):
    """Базовое исключение для ошибок LLM провайдеров."""
    
    def __init__(self, provider: LLMProvider, message: str, original_error: Optional[Exception] = None):
        self.provider = provider
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{provider.value}] {message}")


class LLMRateLimitError(LLMProviderError):
    """Исключение для превышения rate limit."""
    pass


class LLMQuotaError(LLMProviderError):
    """Исключение для превышения квоты."""
    pass


class LLMAuthenticationError(LLMProviderError):
    """Исключение для ошибок аутентификации."""
    pass 