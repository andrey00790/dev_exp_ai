"""
Enhanced LLM Loader with Multi-Provider Support.

Загрузчик для интеллектуального роутера с поддержкой множественных провайдеров.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .llm_router import LLMRouter, RoutingStrategy
from .providers.base import LLMProvider, LLMModel, LLMRequest, LLMResponse
from .providers.ollama_provider import create_ollama_provider

# Попытка импорта дополнительных провайдеров
try:
    from .providers.openai_provider import create_openai_provider
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from .providers.anthropic_provider import create_anthropic_provider
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Конфигурация для LLM системы."""
    # Основные настройки
    mode: str = "local"  # local, openai, anthropic, multi
    routing_strategy: str = "balanced"  # priority, cost_optimized, quality_optimized, balanced, round_robin, ab_test
    
    # Ollama (локальные модели)
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "mistral:instruct"
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo-preview"
    openai_organization: Optional[str] = None
    
    # Anthropic
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-sonnet-20240229"
    
    # Cohere
    cohere_api_key: Optional[str] = None
    cohere_model: str = "command-r-plus"
    
    # Общие настройки
    max_retries: int = 3
    timeout: float = 60.0
    enable_fallback: bool = True
    cost_limit_per_request: float = 1.0  # USD


class EnhancedLLMClient:
    """
    Улучшенный LLM клиент с поддержкой множественных провайдеров.
    
    Возможности:
    - Автоматический выбор оптимального провайдера
    - Fallback между провайдерами
    - Мониторинг стоимости и качества
    - A/B тестирование
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.router = LLMRouter(
            routing_strategy=RoutingStrategy(config.routing_strategy)
        )
        
        # Инициализация провайдеров
        self._setup_providers()
        
        logger.info(f"Enhanced LLM Client initialized with {len(self.router.providers)} providers")
    
    def _setup_providers(self):
        """Настраивает доступные провайдеры."""
        
        if self.config.mode in ["local", "multi"]:
            # Ollama провайдер (всегда доступен)
            try:
                ollama_provider = create_ollama_provider(
                    model=LLMModel(self.config.ollama_model),
                    base_url=self.config.ollama_url
                )
                self.router.add_provider(ollama_provider)
                logger.info(f"✅ Ollama provider added: {self.config.ollama_model}")
            except Exception as e:
                logger.warning(f"Failed to setup Ollama provider: {e}")
        
        if self.config.mode in ["openai", "multi"]:
            # OpenAI провайдер
            if OPENAI_AVAILABLE and self.config.openai_api_key:
                try:
                    openai_provider = create_openai_provider(
                        api_key=self.config.openai_api_key,
                        model=LLMModel(self.config.openai_model)
                    )
                    self.router.add_provider(openai_provider)
                    logger.info(f"✅ OpenAI provider added: {self.config.openai_model}")
                except Exception as e:
                    logger.warning(f"Failed to setup OpenAI provider: {e}")
            else:
                logger.warning("OpenAI provider not available (missing package or API key)")
        
        if self.config.mode in ["anthropic", "multi"]:
            # Anthropic провайдер
            if ANTHROPIC_AVAILABLE and self.config.anthropic_api_key:
                try:
                    anthropic_provider = create_anthropic_provider(
                        api_key=self.config.anthropic_api_key,
                        model=LLMModel(self.config.anthropic_model)
                    )
                    self.router.add_provider(anthropic_provider)
                    logger.info(f"✅ Anthropic provider added: {self.config.anthropic_model}")
                except Exception as e:
                    logger.warning(f"Failed to setup Anthropic provider: {e}")
            else:
                logger.warning("Anthropic provider not available (missing package or API key)")
        
        if not self.router.providers:
            logger.error("No LLM providers available! Falling back to basic Ollama.")
            # Аварийный fallback к Ollama
            try:
                ollama_provider = create_ollama_provider()
                self.router.add_provider(ollama_provider)
            except Exception as e:
                raise RuntimeError(f"Failed to initialize any LLM provider: {e}")
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Генерирует ответ с автоматическим выбором провайдера.
        
        Args:
            prompt: Основной промпт
            system_prompt: Системный промпт (опционально)
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации
            **kwargs: Дополнительные параметры
            
        Returns:
            str: Сгенерированный текст
        """
        
        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        
        # Проверка лимита стоимости (если задан)
        if self.config.cost_limit_per_request > 0:
            estimated_costs = []
            for provider in self.router.get_available_providers():
                cost = provider.estimate_cost(request)
                estimated_costs.append((provider.provider.value, cost))
            
            min_cost = min(cost for _, cost in estimated_costs) if estimated_costs else 0
            if min_cost > self.config.cost_limit_per_request:
                logger.warning(
                    f"Request exceeds cost limit: ${min_cost:.4f} > ${self.config.cost_limit_per_request:.4f}"
                )
        
        try:
            response = await self.router.generate(request, max_retries=self.config.max_retries)
            
            logger.info(
                f"✅ Generated response via {response.provider.value}: "
                f"{response.total_tokens} tokens, ${response.cost_usd:.4f}, {response.response_time:.2f}s"
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise
    
    async def generate_detailed(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Генерирует ответ с подробными метриками.
        
        Returns:
            LLMResponse: Полный ответ с метриками
        """
        
        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            **kwargs
        )
        
        return await self.router.generate(request, max_retries=self.config.max_retries)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику использования."""
        return await self.router.get_router_stats()
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверяет здоровье всех провайдеров."""
        return await self.router.health_check_all()
    
    async def get_available_models(self) -> Dict[str, List[str]]:
        """Возвращает список доступных моделей по провайдерам."""
        models = {}
        
        for provider_type, provider in self.router.providers.items():
            try:
                if hasattr(provider, 'get_available_models'):
                    provider_models = await provider.get_available_models()
                    models[provider_type.value] = provider_models.get("models", [])
                else:
                    models[provider_type.value] = [provider.model.value]
            except Exception as e:
                logger.warning(f"Failed to get models for {provider_type.value}: {e}")
                models[provider_type.value] = []
        
        return models
    
    def set_routing_strategy(self, strategy: str):
        """Изменяет стратегию маршрутизации."""
        try:
            self.router.routing_strategy = RoutingStrategy(strategy)
            logger.info(f"Routing strategy changed to: {strategy}")
        except ValueError:
            logger.error(f"Invalid routing strategy: {strategy}")
            raise


def load_llm_config() -> LLMConfig:
    """Загружает конфигурацию LLM из переменных окружения."""
    
    return LLMConfig(
        mode=os.getenv("LLM_MODE", "local"),
        routing_strategy=os.getenv("LLM_ROUTING_STRATEGY", "balanced"),
        
        # Ollama
        ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "mistral:instruct"),
        
        # OpenAI
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
        openai_organization=os.getenv("OPENAI_ORGANIZATION"),
        
        # Anthropic
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
        
        # Cohere
        cohere_api_key=os.getenv("COHERE_API_KEY"),
        cohere_model=os.getenv("COHERE_MODEL", "command-r-plus"),
        
        # Общие настройки
        max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
        timeout=float(os.getenv("LLM_TIMEOUT", "60.0")),
        enable_fallback=os.getenv("LLM_ENABLE_FALLBACK", "true").lower() == "true",
        cost_limit_per_request=float(os.getenv("LLM_COST_LIMIT", "1.0"))
    )


def load_llm() -> EnhancedLLMClient:
    """
    Основная функция загрузки LLM клиента.
    
    Совместимость с предыдущей версией для плавного перехода.
    """
    
    config = load_llm_config()
    client = EnhancedLLMClient(config)
    
    return client


# Для обратной совместимости со старым API
class LegacyLLMWrapper:
    """Обертка для обратной совместимости."""
    
    def __init__(self, client: EnhancedLLMClient):
        self.client = client
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Генерирует ответ (совместимость со старым API)."""
        return await self.client.generate(prompt, **kwargs)


def create_legacy_client() -> LegacyLLMWrapper:
    """Создает клиент с обратной совместимостью."""
    enhanced_client = load_llm()
    return LegacyLLMWrapper(enhanced_client)
