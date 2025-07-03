"""
AI Assistant Core Metrics - Метрики для трех ключевых функций:
1. Семантический поиск
2. Генерация RFC (проектирование системы)  
3. Генерация документации по коду
"""

from prometheus_client import (
    Counter, Histogram, Gauge, Summary, 
    generate_latest, CONTENT_TYPE_LATEST
)
import time
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# ===== SEMANTIC SEARCH METRICS =====
semantic_search_requests = Counter(
    'ai_assistant_semantic_search_requests_total',
    'Total semantic search requests',
    ['endpoint', 'status', 'language']
)

semantic_search_duration = Histogram(
    'ai_assistant_semantic_search_duration_seconds',
    'Semantic search request duration',
    ['endpoint', 'collection'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

semantic_search_results = Histogram(
    'ai_assistant_semantic_search_results_count',
    'Number of search results returned',
    ['endpoint', 'query_type'],
    buckets=[0, 1, 5, 10, 25, 50, 100]
)

semantic_search_relevance = Histogram(
    'ai_assistant_semantic_search_relevance_score',
    'Search results relevance score',
    ['endpoint'],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

semantic_search_cache_hits = Counter(
    'ai_assistant_semantic_search_cache_hits_total',
    'Cache hits for semantic search',
    ['cache_type']
)

# ===== RFC GENERATION METRICS =====
rfc_generation_requests = Counter(
    'ai_assistant_rfc_generation_requests_total',
    'Total RFC generation requests',
    ['endpoint', 'task_type', 'status']
)

rfc_generation_duration = Histogram(
    'ai_assistant_rfc_generation_duration_seconds',
    'RFC generation request duration',
    ['task_type', 'template'],
    buckets=[5, 10, 15, 30, 60, 120, 300]
)

rfc_generation_quality = Histogram(
    'ai_assistant_rfc_generation_quality_score',
    'RFC generation quality score (1-5)',
    ['task_type'],
    buckets=[1, 2, 3, 4, 5]
)

rfc_generation_completeness = Histogram(
    'ai_assistant_rfc_generation_completeness_percent',
    'RFC sections completeness percentage',
    ['template'],
    buckets=[50, 60, 70, 80, 85, 90, 95, 98, 100]
)

rfc_generation_tokens = Histogram(
    'ai_assistant_rfc_generation_tokens_used',
    'Tokens used for RFC generation',
    ['llm_provider', 'model'],
    buckets=[1000, 2500, 5000, 7500, 10000, 15000, 20000]
)

# ===== CODE DOCUMENTATION METRICS =====
code_documentation_requests = Counter(
    'ai_assistant_code_documentation_requests_total',
    'Total code documentation requests',
    ['endpoint', 'doc_type', 'language', 'status']
)

code_documentation_duration = Histogram(
    'ai_assistant_code_documentation_duration_seconds',
    'Code documentation generation duration',
    ['doc_type', 'language'],
    buckets=[10, 20, 30, 60, 120, 300, 600]
)

code_documentation_coverage = Histogram(
    'ai_assistant_code_documentation_coverage_percent',
    'Code documentation coverage percentage',
    ['language', 'doc_type'],
    buckets=[50, 60, 70, 80, 85, 90, 95, 98, 100]
)

code_documentation_lines_processed = Histogram(
    'ai_assistant_code_documentation_lines_processed',
    'Lines of code processed for documentation',
    ['language'],
    buckets=[100, 500, 1000, 2500, 5000, 10000, 25000]
)

# ===== AI OPTIMIZATION METRICS =====
ai_optimization_requests = Counter(
    'ai_assistant_ai_optimization_requests_total',
    'Total AI optimization requests',
    ['model_type', 'optimization_type', 'status']
)

ai_optimization_duration = Histogram(
    'ai_assistant_ai_optimization_duration_seconds',
    'AI optimization duration',
    ['model_type', 'optimization_type'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

ai_optimization_improvement = Histogram(
    'ai_assistant_ai_optimization_improvement_percent',
    'AI optimization improvement percentage',
    ['model_type', 'metric_type'],
    buckets=[-50, -25, -10, 0, 10, 25, 50, 75, 100]
)

model_performance_latency = Gauge(
    'ai_assistant_model_performance_latency_ms',
    'Model performance latency in milliseconds',
    ['model_type']
)

model_performance_accuracy = Gauge(
    'ai_assistant_model_performance_accuracy',
    'Model performance accuracy (0-1)',
    ['model_type']
)

model_performance_cost = Gauge(
    'ai_assistant_model_performance_cost_per_request',
    'Model cost per request in USD',
    ['model_type']
)

model_performance_quality = Gauge(
    'ai_assistant_model_performance_quality_score',
    'Model quality score (0-10)',
    ['model_type']
)

benchmark_runs = Counter(
    'ai_assistant_benchmark_runs_total',
    'Total benchmark runs',
    ['status']
)

benchmark_duration = Histogram(
    'ai_assistant_benchmark_duration_seconds',
    'Benchmark duration',
    buckets=[1, 5, 10, 30, 60, 120]
)

# ===== USER EXPERIENCE METRICS =====
user_satisfaction_score = Histogram(
    'ai_assistant_user_satisfaction_score',
    'User satisfaction score (1-5)',
    ['feature', 'user_type'],
    buckets=[1, 2, 3, 4, 5]
)

feature_adoption_rate = Gauge(
    'ai_assistant_feature_adoption_rate_percent',
    'Feature adoption rate percentage',
    ['feature']
)

session_duration = Histogram(
    'ai_assistant_session_duration_seconds',
    'User session duration',
    ['feature'],
    buckets=[60, 300, 600, 1200, 1800, 3600, 7200]
)

# ===== SYSTEM PERFORMANCE METRICS =====
system_uptime = Gauge(
    'ai_assistant_system_uptime_percent',
    'System uptime percentage'
)

error_rate = Gauge(
    'ai_assistant_error_rate_percent',
    'Overall error rate percentage',
    ['component']
)

active_users = Gauge(
    'ai_assistant_active_users_count',
    'Number of active users',
    ['time_period']  # daily, weekly, monthly
)

# ===== BUSINESS VALUE METRICS =====
time_savings = Histogram(
    'ai_assistant_time_savings_percent',
    'Time savings compared to manual work',
    ['feature'],
    buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90]
)

quality_improvement = Histogram(
    'ai_assistant_quality_improvement_percent',
    'Quality improvement compared to manual work',
    ['feature'],
    buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90]
)

# ===== METRIC COLLECTION FUNCTIONS =====

def record_semantic_search_metrics(
    endpoint: str,
    duration: float,
    results_count: int,
    relevance_score: float,
    status: str = "success",
    language: str = "ru",
    collection: str = "default",
    query_type: str = "semantic",
    cache_hit: bool = False
):
    """Записывает метрики семантического поиска."""
    semantic_search_requests.labels(
        endpoint=endpoint, 
        status=status, 
        language=language
    ).inc()
    
    semantic_search_duration.labels(
        endpoint=endpoint, 
        collection=collection
    ).observe(duration)
    
    semantic_search_results.labels(
        endpoint=endpoint, 
        query_type=query_type
    ).observe(results_count)
    
    semantic_search_relevance.labels(
        endpoint=endpoint
    ).observe(relevance_score)
    
    if cache_hit:
        semantic_search_cache_hits.labels(
            cache_type="query_cache"
        ).inc()

def record_rfc_generation_metrics(
    endpoint: str,
    task_type: str,
    duration: float,
    quality_score: float,
    completeness_percent: float,
    tokens_used: int,
    status: str = "success",
    template: str = "default",
    llm_provider: str = "openai",
    model: str = "gpt-4"
):
    """Записывает метрики генерации RFC."""
    rfc_generation_requests.labels(
        endpoint=endpoint,
        task_type=task_type,
        status=status
    ).inc()
    
    rfc_generation_duration.labels(
        task_type=task_type,
        template=template
    ).observe(duration)
    
    rfc_generation_quality.labels(
        task_type=task_type
    ).observe(quality_score)
    
    rfc_generation_completeness.labels(
        template=template
    ).observe(completeness_percent)
    
    rfc_generation_tokens.labels(
        llm_provider=llm_provider,
        model=model
    ).observe(tokens_used)

def record_code_documentation_metrics(
    endpoint: str,
    doc_type: str,
    language: str,
    duration: float,
    coverage_percent: float,
    lines_processed: int,
    status: str = "success"
):
    """Записывает метрики генерации документации."""
    code_documentation_requests.labels(
        endpoint=endpoint,
        doc_type=doc_type,
        language=language,
        status=status
    ).inc()
    
    code_documentation_duration.labels(
        doc_type=doc_type,
        language=language
    ).observe(duration)
    
    code_documentation_coverage.labels(
        language=language,
        doc_type=doc_type
    ).observe(coverage_percent)
    
    code_documentation_lines_processed.labels(
        language=language
    ).observe(lines_processed)

def record_ai_optimization(
    user_id: str,
    model_type: str,
    optimization_type: str,
    duration: float,
    improvements: Dict[str, float],
    status: str = "success"
):
    """Записывает метрики AI оптимизации."""
    ai_optimization_requests.labels(
        model_type=model_type,
        optimization_type=optimization_type,
        status=status
    ).inc()
    
    ai_optimization_duration.labels(
        model_type=model_type,
        optimization_type=optimization_type
    ).observe(duration)
    
    # Записываем улучшения по метрикам
    for metric_type, improvement_percent in improvements.items():
        ai_optimization_improvement.labels(
            model_type=model_type,
            metric_type=metric_type
        ).observe(improvement_percent)

def update_model_performance_metrics(
    model_type: str,
    latency_ms: float,
    accuracy: float,
    cost_per_request: float,
    quality_score: float
):
    """Обновляет метрики производительности модели."""
    model_performance_latency.labels(model_type=model_type).set(latency_ms)
    model_performance_accuracy.labels(model_type=model_type).set(accuracy)
    model_performance_cost.labels(model_type=model_type).set(cost_per_request)
    model_performance_quality.labels(model_type=model_type).set(quality_score)

def record_benchmark_metrics(
    duration: float,
    status: str = "success"
):
    """Записывает метрики бенчмарков."""
    benchmark_runs.labels(status=status).inc()
    benchmark_duration.observe(duration)

def record_user_experience_metrics(
    feature: str,
    satisfaction_score: float,
    session_duration_seconds: float,
    user_type: str = "regular"
):
    """Записывает метрики пользовательского опыта."""
    user_satisfaction_score.labels(
        feature=feature,
        user_type=user_type
    ).observe(satisfaction_score)
    
    session_duration.labels(
        feature=feature
    ).observe(session_duration_seconds)

def update_business_metrics(
    feature: str,
    time_savings_percent: float,
    quality_improvement_percent: float
):
    """Обновляет метрики бизнес-ценности."""
    time_savings.labels(
        feature=feature
    ).observe(time_savings_percent)
    
    quality_improvement.labels(
        feature=feature
    ).observe(quality_improvement_percent)

def update_system_metrics(
    uptime_percent: float,
    component_error_rates: Dict[str, float],
    daily_active_users: int,
    weekly_active_users: int,
    monthly_active_users: int
):
    """Обновляет системные метрики."""
    system_uptime.set(uptime_percent)
    
    for component, error_rate_percent in component_error_rates.items():
        error_rate.labels(component=component).set(error_rate_percent)
    
    active_users.labels(time_period="daily").set(daily_active_users)
    active_users.labels(time_period="weekly").set(weekly_active_users)
    active_users.labels(time_period="monthly").set(monthly_active_users)

def update_feature_adoption_rates(adoption_rates: Dict[str, float]):
    """Обновляет метрики adoption rate для функций."""
    for feature, rate_percent in adoption_rates.items():
        feature_adoption_rate.labels(feature=feature).set(rate_percent)

# ===== MIDDLEWARE AND HANDLERS =====

async def metrics_middleware(request, call_next):
    """Middleware для автоматического сбора метрик."""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Автоматически записываем базовые метрики
        endpoint = request.url.path
        
        if "/search" in endpoint:
            # Метрики поиска записываются в соответствующих handlers
            pass
        elif "/generate" in endpoint:
            # Метрики генерации записываются в соответствующих handlers
            pass
        elif "/documentation" in endpoint:
            # Метрики документации записываются в соответствующих handlers
            pass
            
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Request failed: {e}")
        # Записываем метрики ошибок
        raise

def get_metrics_handler():
    """Handler для получения метрик в формате Prometheus."""
    def handler():
        return {
            "content": generate_latest(),
            "media_type": CONTENT_TYPE_LATEST
        }
    return handler

def initialize_app_info(version: str, environment: str):
    """Инициализирует информацию о приложении."""
    logger.info(f"AI Assistant metrics initialized - version: {version}, env: {environment}")
    
    # Устанавливаем начальные значения метрик
    update_feature_adoption_rates({
        "semantic_search": 0.0,
        "rfc_generation": 0.0,
        "code_documentation": 0.0,
        "ai_optimization": 0.0
    })
    
    update_system_metrics(
        uptime_percent=100.0,
        component_error_rates={
            "semantic_search": 0.0,
            "rfc_generation": 0.0,
            "code_documentation": 0.0,
            "llm_client": 0.0,
            "ai_optimization": 0.0
        },
        daily_active_users=0,
        weekly_active_users=0,
        monthly_active_users=0
    )

# ===== METRIC TARGETS (для мониторинга) =====

METRIC_TARGETS = {
    # Семантический поиск
    "semantic_search_response_time_p95": 1.0,  # секунды
    "semantic_search_relevance_score_avg": 0.8,
    "semantic_search_cache_hit_rate": 0.6,
    
    # Генерация RFC
    "rfc_generation_duration_avg": 30.0,  # секунды
    "rfc_generation_quality_score_avg": 4.0,
    "rfc_generation_completeness_avg": 95.0,  # процент
    
    # Генерация документации
    "code_documentation_duration_avg": 60.0,  # секунды
    "code_documentation_coverage_avg": 90.0,  # процент
    
    # AI Optimization
    "ai_optimization_duration_avg": 5.0,  # секунды
    "ai_optimization_improvement_min": 10.0,  # процент
    "model_performance_latency_max": 2000.0,  # миллисекунды
    "model_performance_accuracy_min": 0.8,
    "model_performance_quality_min": 7.0,
    
    # Пользовательский опыт
    "user_satisfaction_avg": 4.0,
    "feature_adoption_rate_min": 80.0,  # процент
    
    # Система
    "system_uptime_min": 99.5,  # процент
    "error_rate_max": 2.0,  # процент
}

def setup_metrics():
    """Initialize metrics collection and set up default values"""
    logger.info("Setting up AI Assistant metrics")
    initialize_app_info("2.1.0", "production")
    logger.info("Metrics setup completed")
    return True

class MetricsCollector:
    """Класс для централизованного сбора метрик"""
    
    def __init__(self):
        self.metrics = {}
    
    def record(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Записывает метрику"""
        if labels is None:
            labels = {}
        
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append({
            "value": value,
            "labels": labels,
            "timestamp": time.time()
        })

# Глобальный экземпляр сборщика метрик
metrics = MetricsCollector()
