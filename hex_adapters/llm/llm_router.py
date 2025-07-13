"""
Intelligent LLM Router with Advanced Routing Strategies.

Роутер для балансировки нагрузки между различными LLM провайдерами.
"""

import logging
import random
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .providers.base import (
    BaseLLMProvider, LLMProvider, LLMRequest, LLMResponse
)

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Стратегии маршрутизации запросов."""
    PRIORITY = "priority"  # По приоритету
    COST_OPTIMIZED = "cost_optimized"  # Минимальная стоимость
    QUALITY_OPTIMIZED = "quality_optimized"  # Максимальное качество
    BALANCED = "balanced"  # Сбалансированный подход
    ROUND_ROBIN = "round_robin"  # Поочередно
    AB_TEST = "ab_test"  # A/B тестирование


@dataclass
class ProviderMetrics:
    """Метрики провайдера для принятия решений о маршрутизации."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    avg_response_time: float = 0.0
    last_used: Optional[datetime] = None
    quality_score: float = 0.0  # 0.0 - 1.0

    weight: float = 1.0  # Вес для weighted round robin
    priority: int = 1  # Приоритет (чем меньше, тем выше)
    is_available: bool = True
    error_count_last_hour: int = 0

    # Временные метрики для динамической адаптации
    recent_response_times: List[float] = field(default_factory=list)
    recent_costs: List[float] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Процент успешных запросов."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def avg_cost_per_token(self) -> float:
        """Средняя стоимость за токен."""
        if self.total_tokens == 0:
            return 0.0
        return self.total_cost_usd / self.total_tokens

    def update_metrics(self, response: LLMResponse, success: bool = True):
        """Обновляет метрики на основе ответа."""
        self.total_requests += 1
        self.last_used = datetime.now(timezone.utc)

        if success:
            self.successful_requests += 1
            self.total_cost_usd += response.cost_usd
            self.total_tokens += response.total_tokens

            # Обновляем среднее время ответа
            if self.avg_response_time == 0:
                self.avg_response_time = response.response_time
            else:
                # Экспоненциальное сглаживание
                alpha = 0.1
                self.avg_response_time = (
                    alpha * response.response_time +
                    (1 - alpha) * self.avg_response_time
                )

            # Сохраняем недавние метрики (последние 10)
            self.recent_response_times.append(response.response_time)
            if len(self.recent_response_times) > 10:
                self.recent_response_times.pop(0)

            self.recent_costs.append(response.cost_usd)
            if len(self.recent_costs) > 10:
                self.recent_costs.pop(0)

        else:
            self.failed_requests += 1
            self.error_count_last_hour += 1


class LLMRouter:
    """
    Интеллектуальный роутер для LLM провайдеров.

    Поддерживает различные стратегии маршрутизации:
    - Приоритетная
    - Оптимизация по стоимости
    - Оптимизация по качеству
    - Сбалансированная
    - Round Robin
    - A/B тестирование
    """

    def __init__(self, routing_strategy: RoutingStrategy =
                 RoutingStrategy.BALANCED):
        self.routing_strategy = routing_strategy
        self.providers: Dict[LLMProvider, BaseLLMProvider] = {}
        self.metrics: Dict[LLMProvider, ProviderMetrics] = {}

        # Состояние для Round Robin
        self.round_robin_index = 0

        # A/B тестирование
        self.ab_test_groups = {"A": [], "B": []}
        self.ab_test_split = 0.5  # 50/50 split

        logger.info(f"LLM Router initialized with {routing_strategy.value} "
                    "strategy")

    def add_provider(self, provider: BaseLLMProvider):
        """Добавляет провайдера в роутер."""
        provider_type = provider.provider
        self.providers[provider_type] = provider
        self.metrics[provider_type] = ProviderMetrics()

        logger.info(f"Provider {provider_type.value} added to router")

    def remove_provider(self, provider_type: LLMProvider):
        """Удаляет провайдера из роутера."""
        if provider_type in self.providers:
            del self.providers[provider_type]
            del self.metrics[provider_type]
            logger.info(f"Provider {provider_type.value} removed from "
                        "router")

    def get_available_providers(self) -> List[BaseLLMProvider]:
        """Возвращает список доступных провайдеров."""
        available = []
        for provider_type, provider in self.providers.items():
            metrics = self.metrics[provider_type]
            if metrics.is_available and metrics.error_count_last_hour < 5:
                available.append(provider)
        return available

    async def select_provider(self, request: LLMRequest) -> BaseLLMProvider:
        """
        Выбирает оптимального провайдера на основе стратегии.

        Args:
            request: Запрос для обработки

        Returns:
            BaseLLMProvider: Выбранный провайдер

        Raises:
            RuntimeError: Если нет доступных провайдеров
        """
        available_providers = self.get_available_providers()

        if not available_providers:
            raise RuntimeError("No available LLM providers")

        if len(available_providers) == 1:
            return available_providers[0]

        # Выбор провайдера в зависимости от стратегии
        if self.routing_strategy == RoutingStrategy.PRIORITY:
            return self._select_by_priority(available_providers)
        elif self.routing_strategy == RoutingStrategy.COST_OPTIMIZED:
            return await self._select_by_cost(available_providers, request)
        elif self.routing_strategy == RoutingStrategy.QUALITY_OPTIMIZED:
            return self._select_by_quality(available_providers)
        elif self.routing_strategy == RoutingStrategy.BALANCED:
            return await self._select_balanced(available_providers, request)
        elif self.routing_strategy == RoutingStrategy.ROUND_ROBIN:
            return self._select_round_robin(available_providers)
        elif self.routing_strategy == RoutingStrategy.AB_TEST:
            return self._select_ab_test(available_providers)
        else:
            # Fallback к первому доступному
            return available_providers[0]

    def _select_by_priority(self,
                           providers: List[BaseLLMProvider]) -> BaseLLMProvider:
        """Выбор по приоритету."""
        provider_priorities = []
        for provider in providers:
            metrics = self.metrics[provider.provider]
            provider_priorities.append((provider, metrics.priority))

        # Сортируем по приоритету (меньше = выше приоритет)
        provider_priorities.sort(key=lambda x: x[1])
        return provider_priorities[0][0]

    async def _select_by_cost(self, providers: List[BaseLLMProvider],
                              request: LLMRequest) -> BaseLLMProvider:
        """Выбор по минимальной стоимости."""
        provider_costs = []
        for provider in providers:
            try:
                estimated_cost = provider.estimate_cost(request)
                provider_costs.append((provider, estimated_cost))
            except Exception:
                # Если не удается оценить стоимость, используем историческую
                metrics = self.metrics[provider.provider]
                provider_costs.append((provider, metrics.avg_cost_per_token))

        # Сортируем по стоимости
        provider_costs.sort(key=lambda x: x[1])
        return provider_costs[0][0]

    def _select_by_quality(self,
                          providers: List[BaseLLMProvider]) -> BaseLLMProvider:
        """Выбор по качеству."""
        best_provider = providers[0]
        best_score = 0

        for provider in providers:
            metrics = self.metrics[provider.provider]
            # Комбинированный скор: качество + надежность
            combined_score = (
                metrics.quality_score * 0.7 +
                metrics.success_rate * 0.3
            )

            if combined_score > best_score:
                best_score = combined_score
                best_provider = provider

        return best_provider

    async def _select_balanced(self, providers: List[BaseLLMProvider],
                               request: LLMRequest) -> BaseLLMProvider:
        """Сбалансированный выбор."""
        scores = []

        for provider in providers:
            metrics = self.metrics[provider.provider]

            # Нормализованные метрики (0-1)
            success_rate = metrics.success_rate
            quality_score = metrics.quality_score

            # Инвертированная стоимость (меньше стоимость = выше скор)
            try:
                cost = provider.estimate_cost(request)
                max_cost = max(p.estimate_cost(request) for p in providers)
                cost_score = 1 - (cost / max_cost) if max_cost > 0 else 1
            except Exception:
                cost_score = 0.5

            # Инвертированное время ответа
            if metrics.avg_response_time > 0:
                max_time = max(self.metrics[p.provider].avg_response_time
                               for p in providers
                               if self.metrics[p.provider].avg_response_time > 0)
                time_score = (1 - (metrics.avg_response_time / max_time)
                              if max_time > 0 else 1)
            else:
                time_score = 1

            # Взвешенный скор
            balanced_score = (
                success_rate * 0.3 +
                quality_score * 0.25 +
                cost_score * 0.25 +
                time_score * 0.2
            )

            scores.append((provider, balanced_score))

        # Сортируем по скору
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[0][0]

    def _select_round_robin(self,
                           providers: List[BaseLLMProvider]) -> BaseLLMProvider:
        """Round Robin выбор."""
        if not providers:
            raise RuntimeError("No providers available")

        provider = providers[self.round_robin_index % len(providers)]
        self.round_robin_index += 1

        return provider

    def _select_ab_test(self,
                       providers: List[BaseLLMProvider]) -> BaseLLMProvider:
        """A/B тестирование."""
        if len(providers) < 2:
            return providers[0]

        # Случайно выбираем группу A или B
        group = "A" if random.random() < self.ab_test_split else "B"

        # Если группы не настроены, используем первые два провайдера
        if not self.ab_test_groups["A"] and not self.ab_test_groups["B"]:
            self.ab_test_groups["A"] = [providers[0]]
            self.ab_test_groups["B"] = [providers[1]]

        # Выбираем случайного провайдера из группы
        selected_group = self.ab_test_groups[group]
        if selected_group:
            return random.choice(selected_group)
        else:
            return providers[0]

    async def generate(self, request: LLMRequest,
                       max_retries: int = 3) -> LLMResponse:
        """
        Генерирует ответ через выбранного провайдера.

        Args:
            request: Запрос для обработки
            max_retries: Максимальное количество попыток

        Returns:
            LLMResponse: Ответ от провайдера
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                provider = await self.select_provider(request)
                logger.debug(f"Attempt {attempt + 1}: Using provider "
                             f"{provider.provider.value}")

                # Генерируем ответ
                response = await provider.generate(request)

                # Обновляем метрики
                self.metrics[provider.provider].update_metrics(
                    response, success=True
                )

                logger.info(f"✅ Request completed via "
                           f"{provider.provider.value}: "
                           f"${response.cost_usd:.4f}, "
                           f"{response.response_time:.2f}s")

                return response

            except Exception as e:
                last_exception = e
                logger.warning(f"Provider {provider.provider.value} failed "
                              f"(attempt {attempt + 1}): {e}")

                # Обновляем метрики о неудаче
                fake_response = LLMResponse(
                    content="",
                    provider=provider.provider,
                    model=provider.model,
                    cost_usd=0,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    response_time=0,
                    metadata={}
                )
                self.metrics[provider.provider].update_metrics(
                    fake_response,
                    success=False
                )

                # Временно отключаем провайдера при множественных ошибках
                if self.metrics[provider.provider].error_count_last_hour >= 3:
                    self.metrics[provider.provider].is_available = False
                    logger.warning(f"Provider {provider.provider.value} "
                                  "temporarily disabled due to errors")

        raise RuntimeError(f"All providers failed after {max_retries} "
                          f"attempts. Last error: {last_exception}")

    async def get_router_stats(self) -> Dict[str, Any]:
        """Возвращает статистику роутера."""
        stats = {
            "routing_strategy": self.routing_strategy.value,
            "total_providers": len(self.providers),
            "available_providers": len(self.get_available_providers()),
            "providers": {}
        }

        for provider_type, metrics in self.metrics.items():
            stats["providers"][provider_type.value] = {
                "total_requests": metrics.total_requests,
                "success_rate": metrics.success_rate,
                "avg_response_time": metrics.avg_response_time,
                "total_cost_usd": metrics.total_cost_usd,
                "avg_cost_per_token": metrics.avg_cost_per_token,
                "is_available": metrics.is_available,
                "priority": metrics.priority,
                "quality_score": metrics.quality_score
            }

        return stats

    async def health_check_all(self) -> Dict[str, Any]:
        """Проверяет здоровье всех провайдеров."""
        health_status = {}

        for provider_type, provider in self.providers.items():
            try:
                # Простая проверка здоровья
                test_request = LLMRequest(
                    prompt="Health check",
                    max_tokens=1,
                    temperature=0.0
                )

                start_time = datetime.now(timezone.utc)
                await provider.generate(test_request)
                response_time = (datetime.now(timezone.utc) - start_time).total_seconds()

                health_status[provider_type.value] = {
                    "status": "healthy",
                    "response_time": response_time,
                    "last_check": datetime.now(timezone.utc).isoformat()
                }

                # Обновляем доступность
                self.metrics[provider_type].is_available = True

            except Exception as e:
                health_status[provider_type.value] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.now(timezone.utc).isoformat()
                }

                # Отмечаем как недоступный
                self.metrics[provider_type].is_available = False

        return health_status

    def reset_error_counts(self):
        """Сбрасывает счетчики ошибок (вызывается периодически)."""
        for metrics in self.metrics.values():
            metrics.error_count_last_hour = 0
            if not metrics.is_available and metrics.error_count_last_hour == 0:
                metrics.is_available = True

    def set_ab_test_groups(self, group_a: List[LLMProvider],
                          group_b: List[LLMProvider]):
        """Настраивает группы для A/B тестирования."""
        self.ab_test_groups["A"] = [
            self.providers[pt] for pt in group_a if pt in self.providers
        ]
        self.ab_test_groups["B"] = [
            self.providers[pt] for pt in group_b if pt in self.providers
        ]

        logger.info(f"A/B test groups configured: "
                   f"A={[p.provider.value for p in self.ab_test_groups['A']]}, "
                   f"B={[p.provider.value for p in self.ab_test_groups['B']]}")

    def update_provider_priority(self, provider_type: LLMProvider,
                                priority: int):
        """Обновляет приоритет провайдера."""
        if provider_type in self.metrics:
            self.metrics[provider_type].priority = priority
            logger.info(f"Provider {provider_type.value} priority updated "
                       f"to {priority}")

    def update_provider_weight(self, provider_type: LLMProvider,
                              weight: float):
        """Обновляет вес провайдера для weighted round robin."""
        if provider_type in self.metrics:
            self.metrics[provider_type].weight = weight
            logger.info(f"Provider {provider_type.value} weight updated "
                       f"to {weight}")

    async def estimate_total_cost(self, request: LLMRequest) -> Dict[str, float]:
        """Оценивает стоимость запроса для всех провайдеров."""
        costs = {}
        for provider_type, provider in self.providers.items():
            try:
                cost = provider.estimate_cost(request)
                costs[provider_type.value] = cost
            except Exception:
                costs[provider_type.value] = 0.0
        return costs 