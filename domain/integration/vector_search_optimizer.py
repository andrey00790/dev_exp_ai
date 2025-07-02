"""
Vector Search Optimization Service
Оптимизирует производительность семантического поиска и качество результатов
"""

import asyncio
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from adapters.vectorstore.collections import get_collection_manager
from adapters.vectorstore.embeddings import get_embeddings_service

from domain.integration.vector_search_service import (
    SearchRequest, get_vector_search_service)

logger = logging.getLogger(__name__)


@dataclass
class SearchPerformanceMetrics:
    """Метрики производительности поиска."""

    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    queries_per_second: float
    cache_hit_rate: float
    embedding_generation_time_ms: float
    vector_search_time_ms: float
    post_processing_time_ms: float
    total_queries: int
    failed_queries: int
    success_rate: float


@dataclass
class SearchQualityMetrics:
    """Метрики качества поиска."""

    avg_relevance_score: float
    precision_at_1: float
    precision_at_3: float
    precision_at_5: float
    recall_at_10: float
    user_satisfaction_score: float
    click_through_rate: float
    zero_results_rate: float
    duplicate_results_rate: float


@dataclass
class OptimizationRecommendation:
    """Рекомендация по оптимизации."""

    category: str  # "performance", "quality", "infrastructure"
    priority: str  # "high", "medium", "low"
    title: str
    description: str
    expected_improvement: str
    implementation_effort: str
    code_changes_required: bool


class VectorSearchOptimizer:
    """Сервис для оптимизации vector search."""

    def __init__(self):
        """Инициализация оптимизатора."""
        self.search_service = get_vector_search_service()
        self.collection_manager = get_collection_manager()
        self.embeddings_service = get_embeddings_service()

        # Кэш для часто используемых запросов
        self.query_cache = {}
        self.cache_stats = {"hits": 0, "misses": 0}

        # Метрики производительности
        self.performance_history = []
        self.quality_history = []

        # Настройки оптимизации
        self.optimization_config = {
            "cache_size": 1000,
            "cache_ttl_minutes": 60,
            "batch_size_optimization": True,
            "query_preprocessing": True,
            "result_reranking": True,
            "performance_monitoring": True,
        }

        logger.info("VectorSearchOptimizer initialized")

    async def optimize_search_request(self, request: SearchRequest) -> SearchRequest:
        """Оптимизирует поисковый запрос перед выполнением."""
        optimized_request = request

        # 1. Предобработка запроса
        if self.optimization_config["query_preprocessing"]:
            optimized_request = self._preprocess_query(optimized_request)

        # 2. Оптимизация параметров
        optimized_request = self._optimize_search_parameters(optimized_request)

        return optimized_request

    def _preprocess_query(self, request: SearchRequest) -> SearchRequest:
        """Предобрабатывает поисковый запрос."""
        query = request.query.strip()

        # Удаляем лишние пробелы
        query = " ".join(query.split())

        # Расширяем сокращения
        abbreviations = {
            "API": "Application Programming Interface",
            "DB": "database",
            "K8s": "Kubernetes",
            "CI/CD": "Continuous Integration Continuous Deployment",
        }

        for abbr, full_form in abbreviations.items():
            if abbr in query and full_form not in query:
                query = f"{query} {full_form}"

        # Добавляем синонимы для лучшего поиска
        synonyms = {
            "authentication": "auth login security",
            "monitoring": "observability metrics logging",
            "database": "DB storage persistence",
            "microservices": "microservice service architecture",
        }

        for term, synonym_list in synonyms.items():
            if term in query.lower():
                query = f"{query} {synonym_list}"

        return SearchRequest(
            query=query,
            collections=request.collections,
            limit=request.limit,
            filters=request.filters,
            include_snippets=request.include_snippets,
            hybrid_search=request.hybrid_search,
        )

    def _optimize_search_parameters(self, request: SearchRequest) -> SearchRequest:
        """Оптимизирует параметры поиска."""
        # Увеличиваем лимит для лучшего ранжирования
        optimized_limit = min(request.limit * 2, 50)

        # Включаем гибридный поиск для лучшего качества
        hybrid_search = True

        return SearchRequest(
            query=request.query,
            collections=request.collections,
            limit=optimized_limit,
            filters=request.filters,
            include_snippets=request.include_snippets,
            hybrid_search=hybrid_search,
        )

    async def search_with_caching(self, request: SearchRequest) -> List[Dict[str, Any]]:
        """Выполняет поиск с кэшированием."""
        # Создаем ключ кэша
        cache_key = self._create_cache_key(request)

        # Проверяем кэш
        if cache_key in self.query_cache:
            cache_entry = self.query_cache[cache_key]
            if self._is_cache_valid(cache_entry):
                self.cache_stats["hits"] += 1
                logger.debug(f"Cache hit for query: {request.query[:50]}...")
                return cache_entry["results"]

        # Кэш промах - выполняем поиск
        self.cache_stats["misses"] += 1
        start_time = time.time()

        # Оптимизируем запрос
        optimized_request = await self.optimize_search_request(request)

        # Выполняем поиск
        results = await self.search_service.search(optimized_request)

        # Постобработка результатов
        if self.optimization_config["result_reranking"]:
            results = self._rerank_results(results, request.query)

        # Ограничиваем до оригинального лимита
        results = results[: request.limit]

        search_time = (time.time() - start_time) * 1000

        # Сохраняем в кэш
        self._cache_results(cache_key, results, search_time)

        return results

    def _create_cache_key(self, request: SearchRequest) -> str:
        """Создает ключ для кэширования."""
        key_data = {
            "query": request.query.lower().strip(),
            "collections": sorted(request.collections or []),
            "limit": request.limit,
            "filters": request.filters,
            "hybrid_search": request.hybrid_search,
        }
        return str(hash(json.dumps(key_data, sort_keys=True)))

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Проверяет валидность записи в кэше."""
        ttl_minutes = self.optimization_config["cache_ttl_minutes"]
        expiry_time = cache_entry["timestamp"] + timedelta(minutes=ttl_minutes)
        return datetime.now() < expiry_time

    def _cache_results(
        self, cache_key: str, results: List[Dict[str, Any]], search_time: float
    ):
        """Сохраняет результаты в кэш."""
        # Ограничиваем размер кэша
        if len(self.query_cache) >= self.optimization_config["cache_size"]:
            # Удаляем самую старую запись
            oldest_key = min(
                self.query_cache.keys(), key=lambda k: self.query_cache[k]["timestamp"]
            )
            del self.query_cache[oldest_key]

        self.query_cache[cache_key] = {
            "results": results,
            "timestamp": datetime.now(),
            "search_time_ms": search_time,
        }

    def _rerank_results(
        self, results: List[Dict[str, Any]], query: str
    ) -> List[Dict[str, Any]]:
        """Переранжирует результаты для улучшения качества."""
        if not results:
            return results

        # Дополнительные факторы ранжирования
        for result in results:
            original_score = result.get("score", 0.0)

            # Бонус за точное совпадение в заголовке
            title = result.get("title", "").lower()
            if query.lower() in title:
                original_score *= 1.2

            # Бонус за свежесть документа
            created_at = result.get("created_at")
            if created_at:
                try:
                    doc_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    days_old = (datetime.now() - doc_date.replace(tzinfo=None)).days
                    if days_old < 30:  # Документ младше месяца
                        original_score *= 1.1
                    elif days_old > 365:  # Документ старше года
                        original_score *= 0.9
                except:
                    pass

            # Бонус за тип источника
            source_type = result.get("source_type", "")
            if source_type in ["documentation", "best_practices"]:
                original_score *= 1.1

            result["score"] = min(original_score, 1.0)

        # Сортируем по новому счету
        results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return results

    async def measure_search_performance(
        self, test_queries: List[str]
    ) -> SearchPerformanceMetrics:
        """Измеряет производительность поиска."""
        logger.info(f"Measuring search performance with {len(test_queries)} queries")

        response_times = []
        embedding_times = []
        search_times = []
        failed_queries = 0

        start_time = time.time()

        for query in test_queries:
            try:
                query_start = time.time()

                # Измеряем время генерации embedding
                embed_start = time.time()
                embedding = await self.embeddings_service.embed_text(query)
                embed_time = (time.time() - embed_start) * 1000
                embedding_times.append(embed_time)

                # Измеряем время поиска
                search_start = time.time()
                request = SearchRequest(query=query, limit=10)
                results = await self.search_with_caching(request)
                search_time = (time.time() - search_start) * 1000
                search_times.append(search_time)

                total_time = (time.time() - query_start) * 1000
                response_times.append(total_time)

            except Exception as e:
                logger.error(f"Query failed: {query[:50]}... Error: {e}")
                failed_queries += 1

        total_time = time.time() - start_time

        # Рассчитываем метрики
        if response_times:
            avg_response_time = np.mean(response_times)
            p95_response_time = np.percentile(response_times, 95)
            p99_response_time = np.percentile(response_times, 99)
        else:
            avg_response_time = p95_response_time = p99_response_time = 0.0

        queries_per_second = len(test_queries) / total_time if total_time > 0 else 0.0
        success_rate = (
            (len(test_queries) - failed_queries) / len(test_queries)
            if test_queries
            else 0.0
        )

        # Рассчитываем cache hit rate
        total_cache_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        cache_hit_rate = (
            self.cache_stats["hits"] / total_cache_requests
            if total_cache_requests > 0
            else 0.0
        )

        metrics = SearchPerformanceMetrics(
            avg_response_time_ms=avg_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            queries_per_second=queries_per_second,
            cache_hit_rate=cache_hit_rate,
            embedding_generation_time_ms=(
                np.mean(embedding_times) if embedding_times else 0.0
            ),
            vector_search_time_ms=np.mean(search_times) if search_times else 0.0,
            post_processing_time_ms=(
                avg_response_time - np.mean(search_times) if search_times else 0.0
            ),
            total_queries=len(test_queries),
            failed_queries=failed_queries,
            success_rate=success_rate,
        )

        # Сохраняем в историю
        self.performance_history.append(
            {"timestamp": datetime.now(), "metrics": metrics}
        )

        logger.info(
            f"Performance measurement completed: {avg_response_time:.2f}ms avg, {queries_per_second:.2f} QPS"
        )
        return metrics

    def generate_optimization_recommendations(
        self,
        performance_metrics: SearchPerformanceMetrics,
        quality_metrics: Optional[SearchQualityMetrics] = None,
    ) -> List[OptimizationRecommendation]:
        """Генерирует рекомендации по оптимизации."""
        recommendations = []

        # Рекомендации по производительности
        if performance_metrics.avg_response_time_ms > 1000:
            recommendations.append(
                OptimizationRecommendation(
                    category="performance",
                    priority="high",
                    title="Оптимизация времени отклика",
                    description="Среднее время отклика превышает 1 секунду. Рекомендуется оптимизация индексов и кэширования.",
                    expected_improvement="Снижение времени отклика на 30-50%",
                    implementation_effort="medium",
                    code_changes_required=True,
                )
            )

        if performance_metrics.cache_hit_rate < 0.3:
            recommendations.append(
                OptimizationRecommendation(
                    category="performance",
                    priority="medium",
                    title="Улучшение кэширования",
                    description="Низкий коэффициент попаданий в кэш. Рекомендуется увеличить размер кэша и TTL.",
                    expected_improvement="Увеличение cache hit rate до 50-70%",
                    implementation_effort="low",
                    code_changes_required=False,
                )
            )

        if performance_metrics.queries_per_second < 10:
            recommendations.append(
                OptimizationRecommendation(
                    category="infrastructure",
                    priority="high",
                    title="Масштабирование инфраструктуры",
                    description="Низкая пропускная способность. Рекомендуется добавить больше реплик или оптимизировать векторную базу.",
                    expected_improvement="Увеличение QPS в 2-3 раза",
                    implementation_effort="high",
                    code_changes_required=True,
                )
            )

        if performance_metrics.embedding_generation_time_ms > 200:
            recommendations.append(
                OptimizationRecommendation(
                    category="performance",
                    priority="medium",
                    title="Оптимизация генерации embeddings",
                    description="Долгое время генерации embeddings. Рекомендуется батчинг или более быстрая модель.",
                    expected_improvement="Снижение времени генерации на 40-60%",
                    implementation_effort="medium",
                    code_changes_required=True,
                )
            )

        # Рекомендации по качеству
        if quality_metrics:
            if quality_metrics.precision_at_3 < 0.7:
                recommendations.append(
                    OptimizationRecommendation(
                        category="quality",
                        priority="high",
                        title="Улучшение точности поиска",
                        description="Низкая точность поиска. Рекомендуется fine-tuning модели или улучшение ранжирования.",
                        expected_improvement="Увеличение precision@3 до 80-90%",
                        implementation_effort="high",
                        code_changes_required=True,
                    )
                )

            if quality_metrics.zero_results_rate > 0.1:
                recommendations.append(
                    OptimizationRecommendation(
                        category="quality",
                        priority="medium",
                        title="Снижение пустых результатов",
                        description="Высокий процент запросов без результатов. Рекомендуется расширение запросов и fallback стратегии.",
                        expected_improvement="Снижение zero results rate до 5%",
                        implementation_effort="medium",
                        code_changes_required=True,
                    )
                )

        return recommendations

    def get_optimization_report(self) -> Dict[str, Any]:
        """Генерирует отчет по оптимизации."""
        # Тестовые запросы для измерения производительности
        test_queries = [
            "OAuth 2.0 authentication implementation",
            "microservices architecture patterns",
            "database optimization techniques",
            "API security best practices",
            "monitoring and observability",
            "Kubernetes deployment strategies",
            "CI/CD pipeline setup",
            "error handling patterns",
            "caching strategies",
            "performance optimization",
        ]

        # Запускаем измерение производительности
        import asyncio

        performance_metrics = asyncio.run(self.measure_search_performance(test_queries))

        # Генерируем рекомендации
        recommendations = self.generate_optimization_recommendations(
            performance_metrics
        )

        # Статистика кэша
        cache_stats = {
            "cache_size": len(self.query_cache),
            "cache_hit_rate": (
                self.cache_stats["hits"]
                / (self.cache_stats["hits"] + self.cache_stats["misses"])
                if (self.cache_stats["hits"] + self.cache_stats["misses"]) > 0
                else 0.0
            ),
            "total_hits": self.cache_stats["hits"],
            "total_misses": self.cache_stats["misses"],
        }

        return {
            "timestamp": datetime.now().isoformat(),
            "performance_metrics": {
                "avg_response_time_ms": performance_metrics.avg_response_time_ms,
                "p95_response_time_ms": performance_metrics.p95_response_time_ms,
                "p99_response_time_ms": performance_metrics.p99_response_time_ms,
                "queries_per_second": performance_metrics.queries_per_second,
                "success_rate": performance_metrics.success_rate,
                "cache_hit_rate": performance_metrics.cache_hit_rate,
            },
            "cache_statistics": cache_stats,
            "optimization_recommendations": [
                {
                    "category": rec.category,
                    "priority": rec.priority,
                    "title": rec.title,
                    "description": rec.description,
                    "expected_improvement": rec.expected_improvement,
                    "implementation_effort": rec.implementation_effort,
                }
                for rec in recommendations
            ],
            "configuration": self.optimization_config,
        }


# Глобальный экземпляр оптимизатора
_search_optimizer = None


def get_vector_search_optimizer() -> VectorSearchOptimizer:
    """Получить глобальный экземпляр оптимизатора поиска."""
    global _search_optimizer
    if _search_optimizer is None:
        _search_optimizer = VectorSearchOptimizer()
    return _search_optimizer
