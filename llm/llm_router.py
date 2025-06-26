"""
Smart LLM Router.

Управляет множественными LLM провайдерами с интеллектуальной маршрутизацией,
автоматическим fallback и оптимизацией по качеству/стоимости.

Enhanced with standardized async patterns for enterprise reliability.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import random

from .providers.base import (
    BaseLLMProvider, LLMRequest, LLMResponse, LLMProvider, LLMModel,
    LLMProviderError, LLMRateLimitError, LLMAuthenticationError
)

# Import standardized async patterns
from app.core.async_utils import AsyncTimeouts, with_timeout, safe_gather
from app.core.exceptions import AsyncTimeoutError

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Стратегии маршрутизации запросов."""
    PRIORITY = "priority"  # По приоритету провайдеров
    COST_OPTIMIZED = "cost_optimized"  # Оптимизация по стоимости
    QUALITY_OPTIMIZED = "quality_optimized"  # Оптимизация по качеству
    BALANCED = "balanced"  # Баланс качество/стоимость
    ROUND_ROBIN = "round_robin"  # Круговая ротация
    AB_TEST = "ab_test"  # A/B тестирование


@dataclass
class RoutingDecision:
    """Решение о маршрутизации запроса."""
    provider: BaseLLMProvider
    reason: str
    estimated_cost: float
    expected_quality: float
    fallback_providers: List[BaseLLMProvider]


class LLMRouter:
    """
    Интеллектуальный роутер для LLM провайдеров.
    
    Возможности:
    - Автоматический выбор оптимального провайдера
    - Fallback при ошибках
    - Мониторинг качества и стоимости
    - A/B тестирование
    - Load balancing
    """
    
    def __init__(self, routing_strategy: RoutingStrategy = RoutingStrategy.BALANCED):
        self.providers: Dict[LLMProvider, BaseLLMProvider] = {}
        self.routing_strategy = routing_strategy
        self.request_count = 0
        self.total_cost = 0.0
        self.provider_performance: Dict[LLMProvider, Dict[str, Any]] = {}
        
        logger.info(f"LLM Router initialized with strategy: {routing_strategy.value}")
    
    def add_provider(self, provider: BaseLLMProvider) -> None:
        """Добавляет провайдера в роутер."""
        self.providers[provider.provider] = provider
        
        # Инициализация метрик производительности
        if provider.provider not in self.provider_performance:
            self.provider_performance[provider.provider] = {
                "success_rate": 1.0,
                "avg_response_time": 0.0,
                "avg_cost": 0.0,
                "total_requests": 0,
                "failed_requests": 0,
                "last_used": None
            }
        
        logger.info(f"Added provider: {provider.provider.value} with model {provider.model.value}")
    
    def get_available_providers(self) -> List[BaseLLMProvider]:
        """Возвращает список доступных провайдеров."""
        return [p for p in self.providers.values() if p.config.enabled]
    
    async def generate(self, request: LLMRequest, max_retries: int = 3) -> LLMResponse:
        """
        Генерирует ответ с автоматическим выбором провайдера и fallback.
        
        Args:
            request: Запрос к LLM
            max_retries: Максимальное количество попыток с разными провайдерами
            
        Returns:
            LLMResponse: Ответ от выбранного провайдера
            
        Raises:
            LLMProviderError: Если все провайдеры недоступны
        """
        
        if not self.providers:
            raise LLMProviderError(LLMProvider.OLLAMA, "No providers available")
        
        # Выбираем оптимальный провайдер
        routing_decision = await self._route_request(request)
        
        # Список провайдеров для попыток (основной + fallback)
        providers_to_try = [routing_decision.provider] + routing_decision.fallback_providers
        
        last_error = None
        
        for attempt, provider in enumerate(providers_to_try[:max_retries]):
            try:
                logger.info(
                    f"Attempt {attempt + 1}: Using {provider.provider.value} "
                    f"(reason: {routing_decision.reason})"
                )
                
                # Выполняем запрос
                response = await provider.generate(request)
                
                # Обновляем метрики успеха
                await self._update_performance_metrics(provider.provider, response, success=True)
                
                # Обновляем общие метрики роутера
                self.request_count += 1
                self.total_cost += response.cost_usd
                
                logger.info(
                    f"✅ Request successful via {provider.provider.value}: "
                    f"${response.cost_usd:.4f}, {response.response_time:.2f}s"
                )
                
                return response
                
            except (LLMRateLimitError, LLMAuthenticationError) as e:
                # Критические ошибки - переходим к следующему провайдеру
                logger.warning(f"Provider {provider.provider.value} failed: {e}")
                await self._update_performance_metrics(provider.provider, None, success=False)
                last_error = e
                continue
                
            except LLMProviderError as e:
                # Общие ошибки провайдера
                logger.warning(f"Provider {provider.provider.value} error: {e}")
                await self._update_performance_metrics(provider.provider, None, success=False)
                last_error = e
                continue
                
            except Exception as e:
                # Неожиданные ошибки
                logger.error(f"Unexpected error with {provider.provider.value}: {e}")
                await self._update_performance_metrics(provider.provider, None, success=False)
                last_error = e
                continue
        
        # Все провайдеры недоступны
        raise LLMProviderError(
            LLMProvider.OLLAMA,
            f"All providers failed. Last error: {last_error}",
            last_error
        )
    
    async def _route_request(self, request: LLMRequest) -> RoutingDecision:
        """Определяет оптимальный провайдер для запроса."""
        
        available_providers = self.get_available_providers()
        
        if not available_providers:
            raise LLMProviderError(LLMProvider.OLLAMA, "No available providers")
        
        if self.routing_strategy == RoutingStrategy.PRIORITY:
            return await self._route_by_priority(available_providers, request)
        
        elif self.routing_strategy == RoutingStrategy.COST_OPTIMIZED:
            return await self._route_by_cost(available_providers, request)
        
        elif self.routing_strategy == RoutingStrategy.QUALITY_OPTIMIZED:
            return await self._route_by_quality(available_providers, request)
        
        elif self.routing_strategy == RoutingStrategy.BALANCED:
            return await self._route_balanced(available_providers, request)
        
        elif self.routing_strategy == RoutingStrategy.ROUND_ROBIN:
            return await self._route_round_robin(available_providers, request)
        
        elif self.routing_strategy == RoutingStrategy.AB_TEST:
            return await self._route_ab_test(available_providers, request)
        
        else:
            # Fallback к приоритету
            return await self._route_by_priority(available_providers, request)
    
    async def _route_by_priority(self, providers: List[BaseLLMProvider], request: LLMRequest) -> RoutingDecision:
        """Маршрутизация по приоритету провайдеров."""
        
        # Сортируем по приоритету (1 = highest)
        sorted_providers = sorted(providers, key=lambda p: p.config.priority)
        primary = sorted_providers[0]
        fallbacks = sorted_providers[1:]
        
        return RoutingDecision(
            provider=primary,
            reason="highest priority",
            estimated_cost=primary.estimate_cost(request),
            expected_quality=primary.config.quality_score,
            fallback_providers=fallbacks
        )
    
    async def _route_by_cost(self, providers: List[BaseLLMProvider], request: LLMRequest) -> RoutingDecision:
        """Маршрутизация по минимальной стоимости."""
        
        # Вычисляем стоимость для каждого провайдера
        costs = [(p, p.estimate_cost(request)) for p in providers]
        
        # Сортируем по стоимости
        sorted_by_cost = sorted(costs, key=lambda x: x[1])
        primary = sorted_by_cost[0][0]
        fallbacks = [p for p, _ in sorted_by_cost[1:]]
        
        return RoutingDecision(
            provider=primary,
            reason=f"lowest cost (${sorted_by_cost[0][1]:.4f})",
            estimated_cost=sorted_by_cost[0][1],
            expected_quality=primary.config.quality_score,
            fallback_providers=fallbacks
        )
    
    async def _route_by_quality(self, providers: List[BaseLLMProvider], request: LLMRequest) -> RoutingDecision:
        """Маршрутизация по максимальному качеству."""
        
        # Сортируем по качеству (убывание)
        sorted_by_quality = sorted(providers, key=lambda p: p.config.quality_score, reverse=True)
        primary = sorted_by_quality[0]
        fallbacks = sorted_by_quality[1:]
        
        return RoutingDecision(
            provider=primary,
            reason=f"highest quality ({primary.config.quality_score:.2f})",
            estimated_cost=primary.estimate_cost(request),
            expected_quality=primary.config.quality_score,
            fallback_providers=fallbacks
        )
    
    async def _route_balanced(self, providers: List[BaseLLMProvider], request: LLMRequest) -> RoutingDecision:
        """Маршрутизация с балансом качество/стоимость."""
        
        scores = []
        for provider in providers:
            cost = provider.estimate_cost(request)
            quality = provider.config.quality_score
            
            # Нормализуем стоимость (меньше = лучше)
            max_cost = max(p.estimate_cost(request) for p in providers)
            cost_score = 1.0 - (cost / max(max_cost, 0.001))  # Избегаем деления на 0
            
            # Комбинированная оценка (50% качество + 50% стоимость)
            combined_score = (quality + cost_score) / 2
            
            scores.append((provider, combined_score, cost, quality))
        
        # Сортируем по комбинированной оценке
        sorted_by_score = sorted(scores, key=lambda x: x[1], reverse=True)
        primary = sorted_by_score[0][0]
        fallbacks = [p for p, _, _, _ in sorted_by_score[1:]]
        
        return RoutingDecision(
            provider=primary,
            reason=f"best balance (score: {sorted_by_score[0][1]:.2f})",
            estimated_cost=sorted_by_score[0][2],
            expected_quality=sorted_by_score[0][3],
            fallback_providers=fallbacks
        )
    
    async def _route_round_robin(self, providers: List[BaseLLMProvider], request: LLMRequest) -> RoutingDecision:
        """Круговая ротация между провайдерами."""
        
        # Выбираем провайдера по кругу
        primary_index = self.request_count % len(providers)
        primary = providers[primary_index]
        
        # Остальные провайдеры как fallback
        fallbacks = providers[:primary_index] + providers[primary_index + 1:]
        
        return RoutingDecision(
            provider=primary,
            reason="round robin rotation",
            estimated_cost=primary.estimate_cost(request),
            expected_quality=primary.config.quality_score,
            fallback_providers=fallbacks
        )
    
    async def _route_ab_test(self, providers: List[BaseLLMProvider], request: LLMRequest) -> RoutingDecision:
        """A/B тестирование между провайдерами."""
        
        # Случайный выбор для A/B тестирования
        primary = random.choice(providers)
        fallbacks = [p for p in providers if p != primary]
        
        return RoutingDecision(
            provider=primary,
            reason="A/B test random selection",
            estimated_cost=primary.estimate_cost(request),
            expected_quality=primary.config.quality_score,
            fallback_providers=fallbacks
        )
    
    async def _update_performance_metrics(
        self, 
        provider_type: LLMProvider, 
        response: Optional[LLMResponse], 
        success: bool
    ) -> None:
        """Обновляет метрики производительности провайдера."""
        
        metrics = self.provider_performance[provider_type]
        metrics["total_requests"] += 1
        
        if success and response:
            # Обновляем метрики успеха
            total_requests = metrics["total_requests"]
            
            # Скользящее среднее времени ответа
            if metrics["avg_response_time"] == 0.0:
                metrics["avg_response_time"] = response.response_time
            else:
                metrics["avg_response_time"] = (
                    (metrics["avg_response_time"] * (total_requests - 1) + response.response_time) 
                    / total_requests
                )
            
            # Скользящее среднее стоимости
            if metrics["avg_cost"] == 0.0:
                metrics["avg_cost"] = response.cost_usd
            else:
                metrics["avg_cost"] = (
                    (metrics["avg_cost"] * (total_requests - 1) + response.cost_usd) 
                    / total_requests
                )
            
            metrics["last_used"] = response.metadata.get("created", "")
            
        else:
            # Увеличиваем счетчик ошибок
            metrics["failed_requests"] += 1
        
        # Обновляем коэффициент успеха
        metrics["success_rate"] = (
            (metrics["total_requests"] - metrics["failed_requests"]) / 
            metrics["total_requests"]
        )
    
    async def get_router_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику роутера.
        Enhanced with timeout protection for provider metrics collection.
        """
        try:
            # Collect provider metrics with timeout protection
            provider_stats = {}
            
            for provider_type, provider in self.providers.items():
                try:
                    metrics = self.provider_performance[provider_type]
                    
                    # Get provider metrics with timeout
                    provider_metrics = await with_timeout(
                        asyncio.to_thread(provider.get_metrics),  # Some metrics might be sync
                        AsyncTimeouts.DATABASE_QUERY,  # 10 seconds for metrics
                        f"Provider {provider_type.value} metrics collection timed out"
                    )
                    
                    provider_stats[provider_type.value] = {
                        **provider_metrics,
                        "performance": metrics,
                        "enabled": provider.config.enabled,
                        "priority": provider.config.priority,
                        "status": "metrics_collected"
                    }
                    
                except AsyncTimeoutError:
                    logger.warning(f"⚠️ Metrics collection timed out for {provider_type.value}")
                    provider_stats[provider_type.value] = {
                        "status": "timeout",
                        "error": "Metrics collection timed out",
                        "enabled": provider.config.enabled,
                        "priority": provider.config.priority
                    }
                except Exception as e:
                    logger.warning(f"⚠️ Failed to collect metrics for {provider_type.value}: {e}")
                    provider_stats[provider_type.value] = {
                        "status": "error",
                        "error": str(e),
                        "enabled": provider.config.enabled,
                        "priority": provider.config.priority
                    }
            
            return {
                "routing_strategy": self.routing_strategy.value,
                "total_requests": self.request_count,
                "total_cost_usd": round(self.total_cost, 4),
                "avg_cost_per_request": round(self.total_cost / max(self.request_count, 1), 4),
                "providers": provider_stats,
                "available_providers": len(self.get_available_providers()),
                "stats_collection_status": "completed"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to collect router stats: {e}")
            return {
                "routing_strategy": self.routing_strategy.value,
                "total_requests": self.request_count,
                "total_cost_usd": round(self.total_cost, 4),
                "avg_cost_per_request": round(self.total_cost / max(self.request_count, 1), 4),
                "providers": {},
                "available_providers": 0,
                "stats_collection_status": "error",
                "error": str(e)
            }
    
    async def health_check_all(self) -> Dict[str, Any]:
        """
        Проверяет здоровье всех провайдеров.
        Enhanced with concurrent execution and timeout protection.
        """
        if not self.providers:
            return {
                "router_status": "no_providers",
                "providers": {},
                "healthy_count": 0,
                "total_count": 0
            }
        
        logger.info(f"🔄 Running health checks for {len(self.providers)} providers...")
        
        try:
            # Run health checks concurrently with timeout
            health_tasks = [
                provider.health_check()
                for provider in self.providers.values()
            ]
            
            results_list = await safe_gather(
                *health_tasks,
                return_exceptions=True,
                timeout=AsyncTimeouts.HTTP_REQUEST,  # 30 seconds for all health checks
                max_concurrency=5  # Limit concurrent health checks
            )
            
            # Process results
            results = {}
            healthy_count = 0
            
            for provider_type, result in zip(self.providers.keys(), results_list):
                if isinstance(result, Exception):
                    results[provider_type.value] = {
                        "provider": provider_type.value,
                        "status": "error",
                        "error": str(result),
                        "error_type": type(result).__name__
                    }
                else:
                    results[provider_type.value] = result
                    if result.get("status") == "healthy":
                        healthy_count += 1
            
            router_status = "healthy" if healthy_count > 0 else "unhealthy"
            if healthy_count == 0 and len(self.providers) > 0:
                router_status = "all_providers_unhealthy"
            
            logger.info(f"✅ Health check completed: {healthy_count}/{len(self.providers)} providers healthy")
            
            return {
                "router_status": router_status,
                "providers": results,
                "healthy_count": healthy_count,
                "total_count": len(results),
                "check_duration_info": "Concurrent health checks with 30s timeout"
            }
            
        except AsyncTimeoutError as e:
            logger.warning(f"⚠️ Health check timed out: {e}")
            return {
                "router_status": "timeout",
                "providers": {
                    provider_type.value: {
                        "provider": provider_type.value,
                        "status": "timeout",
                        "error": "Health check timed out"
                    }
                    for provider_type in self.providers.keys()
                },
                "healthy_count": 0,
                "total_count": len(self.providers),
                "error": f"Health check timed out: {e}"
            }
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {
                "router_status": "error",
                "providers": {},
                "healthy_count": 0,
                "total_count": len(self.providers),
                "error": str(e)
            } 