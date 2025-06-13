"""
LLM Management API.

API endpoints для управления LLM роутером, мониторинга провайдеров
и настройки стратегий маршрутизации.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from llm.llm_loader import load_llm
from llm.llm_router import RoutingStrategy

router = APIRouter(prefix="/llm", tags=["LLM Management"])


class LLMTestRequest(BaseModel):
    """Запрос для тестирования LLM."""
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: int = 100
    temperature: float = 0.7
    provider: Optional[str] = None  # Принудительный выбор провайдера


class RoutingStrategyRequest(BaseModel):
    """Запрос на изменение стратегии маршрутизации."""
    strategy: str  # priority, cost_optimized, quality_optimized, balanced, round_robin, ab_test


class LLMStatsResponse(BaseModel):
    """Ответ со статистикой LLM."""
    routing_strategy: str
    total_requests: int
    total_cost_usd: float
    avg_cost_per_request: float
    available_providers: int
    providers: Dict[str, Any]


@router.get(
    "/health",
    summary="LLM Health Check",
    description="Проверяет здоровье всех LLM провайдеров"
)
async def llm_health_check() -> Dict[str, Any]:
    """
    Проверяет состояние всех LLM провайдеров.
    
    **Возвращает:**
    - Статус каждого провайдера
    - Время отклика
    - Доступность моделей
    - Общий статус системы
    """
    
    try:
        llm_client = load_llm()
        health_status = await llm_client.health_check()
        
        return {
            "success": True,
            "data": health_status,
            "message": f"Health check completed. {health_status['healthy_count']}/{health_status['total_count']} providers healthy"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=LLMStatsResponse,
    summary="LLM Statistics",
    description="Возвращает подробную статистику использования LLM"
)
async def get_llm_stats() -> LLMStatsResponse:
    """
    Получает статистику использования LLM роутера.
    
    **Включает:**
    - Общее количество запросов
    - Суммарную стоимость
    - Производительность провайдеров
    - Стратегию маршрутизации
    """
    
    try:
        llm_client = load_llm()
        stats = await llm_client.get_stats()
        
        return LLMStatsResponse(
            routing_strategy=stats["routing_strategy"],
            total_requests=stats["total_requests"],
            total_cost_usd=stats["total_cost_usd"],
            avg_cost_per_request=stats["avg_cost_per_request"],
            available_providers=stats["available_providers"],
            providers=stats["providers"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get LLM stats: {str(e)}"
        )


@router.get(
    "/models",
    summary="Available Models",
    description="Возвращает список доступных моделей по провайдерам"
)
async def get_available_models() -> Dict[str, Any]:
    """
    Получает список всех доступных моделей.
    
    **Группирует по провайдерам:**
    - OpenAI: GPT-4, GPT-3.5-turbo
    - Anthropic: Claude 3 модели
    - Ollama: Локальные модели
    """
    
    try:
        llm_client = load_llm()
        models = await llm_client.get_available_models()
        
        return {
            "success": True,
            "data": models,
            "total_providers": len(models),
            "message": "Available models retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available models: {str(e)}"
        )


@router.post(
    "/test",
    summary="Test LLM Generation",
    description="Тестирует генерацию с заданными параметрами"
)
async def test_llm_generation(request: LLMTestRequest) -> Dict[str, Any]:
    """
    Тестирует LLM генерацию с детальными метриками.
    
    **Параметры:**
    - prompt: Тестовый промпт
    - provider: Принудительный выбор провайдера (опционально)
    - system_prompt: Системный промпт (опционально)
    
    **Возвращает:**
    - Сгенерированный текст
    - Метрики производительности
    - Стоимость запроса
    - Использованный провайдер
    """
    
    try:
        llm_client = load_llm()
        
        # Генерируем ответ с детальными метриками
        response = await llm_client.generate_detailed(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return {
            "success": True,
            "data": {
                "content": response.content,
                "provider": response.provider.value,
                "model": response.model.value,
                "metrics": {
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "total_tokens": response.total_tokens,
                    "response_time": response.response_time,
                    "cost_usd": response.cost_usd
                },
                "metadata": response.metadata
            },
            "message": f"Test completed via {response.provider.value}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test generation failed: {str(e)}"
        )


@router.post(
    "/routing-strategy",
    summary="Change Routing Strategy",
    description="Изменяет стратегию маршрутизации запросов"
)
async def set_routing_strategy(request: RoutingStrategyRequest) -> Dict[str, Any]:
    """
    Изменяет стратегию маршрутизации LLM роутера.
    
    **Доступные стратегии:**
    - `priority`: По приоритету провайдеров
    - `cost_optimized`: Минимальная стоимость
    - `quality_optimized`: Максимальное качество
    - `balanced`: Баланс качество/стоимость
    - `round_robin`: Круговая ротация
    - `ab_test`: A/B тестирование
    """
    
    try:
        # Проверяем валидность стратегии
        valid_strategies = [s.value for s in RoutingStrategy]
        if request.strategy not in valid_strategies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid strategy. Valid options: {valid_strategies}"
            )
        
        llm_client = load_llm()
        llm_client.set_routing_strategy(request.strategy)
        
        return {
            "success": True,
            "data": {
                "new_strategy": request.strategy,
                "valid_strategies": valid_strategies
            },
            "message": f"Routing strategy changed to: {request.strategy}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change routing strategy: {str(e)}"
        )


@router.get(
    "/performance",
    summary="Provider Performance",
    description="Подробная аналитика производительности провайдеров"
)
async def get_provider_performance() -> Dict[str, Any]:
    """
    Возвращает детальную аналитику производительности каждого провайдера.
    
    **Метрики:**
    - Коэффициент успеха
    - Среднее время ответа
    - Средняя стоимость
    - Частота использования
    - История ошибок
    """
    
    try:
        llm_client = load_llm()
        stats = await llm_client.get_stats()
        
        # Расширенная аналитика
        performance_analysis = {}
        
        for provider_name, provider_data in stats["providers"].items():
            performance = provider_data.get("performance", {})
            
            # Рейтинг провайдера (комбинированная метрика)
            success_rate = performance.get("success_rate", 0)
            avg_response_time = performance.get("avg_response_time", float('inf'))
            avg_cost = performance.get("avg_cost", 0)
            
            # Нормализованный рейтинг (чем выше, тем лучше)
            if avg_response_time > 0:
                time_score = min(1.0, 10.0 / avg_response_time)  # 10 секунд = идеал
            else:
                time_score = 0.0
            
            cost_score = 1.0 if avg_cost == 0 else min(1.0, 0.01 / max(avg_cost, 0.001))  # $0.01 = идеал
            
            overall_rating = (success_rate * 0.5 + time_score * 0.3 + cost_score * 0.2)
            
            performance_analysis[provider_name] = {
                **provider_data,
                "rating": round(overall_rating, 3),
                "recommendation": _get_provider_recommendation(
                    success_rate, avg_response_time, avg_cost, provider_data.get("enabled", False)
                )
            }
        
        return {
            "success": True,
            "data": {
                "overall_stats": {
                    "total_requests": stats["total_requests"],
                    "total_cost_usd": stats["total_cost_usd"],
                    "routing_strategy": stats["routing_strategy"]
                },
                "provider_performance": performance_analysis,
                "recommendations": _get_system_recommendations(performance_analysis)
            },
            "message": "Performance analysis completed"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance data: {str(e)}"
        )


def _get_provider_recommendation(
    success_rate: float, 
    avg_response_time: float, 
    avg_cost: float,
    enabled: bool
) -> str:
    """Генерирует рекомендацию для провайдера."""
    
    if not enabled:
        return "Провайдер отключен"
    
    if success_rate < 0.5:
        return "Низкая надежность - рассмотрите отключение"
    elif success_rate < 0.8:
        return "Средняя надежность - требует мониторинга"
    elif avg_response_time > 30:
        return "Медленный ответ - не подходит для real-time"
    elif avg_cost > 0.1:
        return "Высокая стоимость - используйте для критических задач"
    elif success_rate > 0.95 and avg_response_time < 5:
        return "Отличная производительность - рекомендуется"
    else:
        return "Хорошая производительность"


def _get_system_recommendations(performance_data: Dict[str, Any]) -> List[str]:
    """Генерирует общие рекомендации для системы."""
    
    recommendations = []
    
    # Анализ количества провайдеров
    enabled_providers = [
        name for name, data in performance_data.items() 
        if data.get("enabled", False)
    ]
    
    if len(enabled_providers) == 1:
        recommendations.append("Рекомендуется добавить дополнительные провайдеры для отказоустойчивости")
    
    # Анализ стоимости
    total_cost = sum(
        data.get("performance", {}).get("avg_cost", 0) 
        for data in performance_data.values()
    )
    
    if total_cost > 0.05:
        recommendations.append("Высокая средняя стоимость - рассмотрите стратегию 'cost_optimized'")
    
    # Анализ производительности
    low_performance_providers = [
        name for name, data in performance_data.items()
        if data.get("rating", 0) < 0.5
    ]
    
    if low_performance_providers:
        recommendations.append(f"Низкая производительность: {', '.join(low_performance_providers)}")
    
    if not recommendations:
        recommendations.append("Система работает оптимально")
    
    return recommendations


@router.post(
    "/benchmark",
    summary="LLM Benchmark",
    description="Запускает бенчмарк всех доступных провайдеров"
)
async def run_llm_benchmark() -> Dict[str, Any]:
    """
    Запускает бенчмарк тестирование всех провайдеров.
    
    **Тестирует:**
    - Время отклика
    - Качество ответов
    - Стоимость
    - Надежность
    """
    
    try:
        llm_client = load_llm()
        
        benchmark_prompts = [
            "What is artificial intelligence?",
            "Explain quantum computing in simple terms.",
            "Write a Python function to calculate factorial.",
            "Describe the benefits of microservices architecture."
        ]
        
        results = {}
        
        for i, prompt in enumerate(benchmark_prompts):
            try:
                response = await llm_client.generate_detailed(
                    prompt=prompt,
                    max_tokens=150,
                    temperature=0.3  # Детерминированность для сравнения
                )
                
                test_key = f"test_{i+1}"
                results[test_key] = {
                    "prompt": prompt,
                    "provider": response.provider.value,
                    "model": response.model.value,
                    "response_time": response.response_time,
                    "cost_usd": response.cost_usd,
                    "tokens": response.total_tokens,
                    "content_length": len(response.content),
                    "success": True
                }
                
            except Exception as e:
                results[f"test_{i+1}"] = {
                    "prompt": prompt,
                    "success": False,
                    "error": str(e)
                }
        
        # Агрегированная статистика
        successful_tests = [r for r in results.values() if r.get("success")]
        
        if successful_tests:
            avg_response_time = sum(r["response_time"] for r in successful_tests) / len(successful_tests)
            total_cost = sum(r["cost_usd"] for r in successful_tests)
            avg_tokens = sum(r["tokens"] for r in successful_tests) / len(successful_tests)
        else:
            avg_response_time = 0
            total_cost = 0
            avg_tokens = 0
        
        return {
            "success": True,
            "data": {
                "individual_tests": results,
                "summary": {
                    "total_tests": len(benchmark_prompts),
                    "successful_tests": len(successful_tests),
                    "success_rate": len(successful_tests) / len(benchmark_prompts),
                    "avg_response_time": round(avg_response_time, 2),
                    "total_cost_usd": round(total_cost, 4),
                    "avg_tokens": round(avg_tokens)
                }
            },
            "message": f"Benchmark completed: {len(successful_tests)}/{len(benchmark_prompts)} tests successful"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Benchmark failed: {str(e)}"
        ) 