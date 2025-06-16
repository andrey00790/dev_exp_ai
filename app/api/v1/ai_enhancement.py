"""
AI Enhancement API endpoints
Управление AI возможностями: fine-tuning, качество RFC, оптимизация поиска
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging
import asyncio
from datetime import datetime

from app.security.auth import get_current_user
from app.security.rate_limiter import rate_limit_ai_operations as rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-enhancement", tags=["AI Enhancement"])

# Pydantic models

class ModelTrainingRequest(BaseModel):
    """Запрос на обучение модели."""
    training_type: str = Field(..., description="Тип обучения: 'full', 'incremental', 'multilingual'")
    use_feedback: bool = Field(True, description="Использовать пользовательский фидбек")
    epochs: Optional[int] = Field(None, description="Количество эпох обучения")
    
class ModelTrainingResponse(BaseModel):
    """Ответ на запрос обучения модели."""
    status: str
    training_id: str
    message: str
    estimated_duration_minutes: int
    
class RFCQualityAnalysisRequest(BaseModel):
    """Запрос на анализ качества RFC."""
    rfc_content: str = Field(..., description="Содержание RFC документа")
    rfc_title: str = Field("", description="Заголовок RFC")
    
class RFCQualityAnalysisResponse(BaseModel):
    """Ответ анализа качества RFC."""
    overall_score: float
    structure_score: float
    completeness_score: float
    technical_depth_score: float
    clarity_score: float
    improvement_suggestions: List[str]
    missing_sections: List[str]
    weak_areas: List[str]
    
class SearchOptimizationRequest(BaseModel):
    """Запрос на оптимизацию поиска."""
    test_queries: Optional[List[str]] = Field(None, description="Тестовые запросы для измерения")
    optimization_type: str = Field("full", description="Тип оптимизации: 'performance', 'quality', 'full'")
    
class SearchOptimizationResponse(BaseModel):
    """Ответ оптимизации поиска."""
    performance_metrics: Dict[str, Any]
    optimization_recommendations: List[Dict[str, Any]]
    cache_statistics: Dict[str, Any]
    improvement_summary: str

# API Endpoints

@router.post("/model/train", response_model=ModelTrainingResponse)
@rate_limit
async def train_model(
    request: ModelTrainingRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Запускает обучение модели семантического поиска.
    
    Поддерживает:
    - Полное переобучение с нуля
    - Инкрементальное обучение на новых данных
    - Мультиязычная оптимизация
    - Использование пользовательского фидбека
    """
    try:
        from model_training import ModelTrainer
        
        logger.info(f"Starting model training: {request.training_type}")
        
        # Создаем тренер модели
        trainer = ModelTrainer()
        
        # Генерируем ID обучения
        training_id = f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Определяем продолжительность в зависимости от типа
        duration_map = {
            "full": 60,
            "incremental": 20,
            "multilingual": 30
        }
        estimated_duration = duration_map.get(request.training_type, 30)
        
        # Запускаем обучение в фоне
        if request.training_type == "full":
            background_tasks.add_task(
                run_full_training_pipeline,
                trainer, training_id, request.use_feedback
            )
        elif request.training_type == "multilingual":
            background_tasks.add_task(
                run_multilingual_optimization,
                trainer, training_id
            )
        else:
            background_tasks.add_task(
                run_incremental_training,
                trainer, training_id, request.use_feedback
            )
        
        return ModelTrainingResponse(
            status="started",
            training_id=training_id,
            message=f"Обучение модели типа '{request.training_type}' запущено",
            estimated_duration_minutes=estimated_duration
        )
        
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка запуска обучения: {str(e)}")

@router.get("/model/training/{training_id}/status")
@rate_limit
async def get_training_status(
    training_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Получает статус обучения модели."""
    try:
        # В реальной реализации здесь будет проверка статуса из базы данных или Redis
        # Пока возвращаем mock статус
        return {
            "training_id": training_id,
            "status": "in_progress",
            "progress_percentage": 65,
            "current_step": "Model fine-tuning",
            "estimated_remaining_minutes": 15,
            "logs": [
                "Training started successfully",
                "Loading training data: 1,234 examples",
                "Fine-tuning model: epoch 3/10",
                "Current loss: 0.234"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get training status: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса: {str(e)}")

@router.post("/rfc/analyze-quality", response_model=RFCQualityAnalysisResponse)
@rate_limit
async def analyze_rfc_quality(
    request: RFCQualityAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Анализирует качество RFC документа.
    
    Оценивает:
    - Структуру документа
    - Полноту содержания
    - Техническую глубину
    - Ясность изложения
    """
    try:
        from services.rfc_quality_enhancer import get_rfc_quality_enhancer
        
        logger.info(f"Analyzing RFC quality: {request.rfc_title}")
        
        # Получаем сервис анализа качества
        quality_enhancer = get_rfc_quality_enhancer()
        
        # Анализируем качество
        metrics = quality_enhancer.analyze_rfc_quality(
            content=request.rfc_content,
            title=request.rfc_title
        )
        
        return RFCQualityAnalysisResponse(
            overall_score=metrics.overall_score,
            structure_score=metrics.structure_score,
            completeness_score=metrics.completeness_score,
            technical_depth_score=metrics.technical_depth_score,
            clarity_score=metrics.clarity_score,
            improvement_suggestions=metrics.improvement_suggestions,
            missing_sections=metrics.missing_sections,
            weak_areas=metrics.weak_areas
        )
        
    except Exception as e:
        logger.error(f"RFC quality analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка анализа качества: {str(e)}")

@router.post("/search/optimize", response_model=SearchOptimizationResponse)
@rate_limit
async def optimize_search(
    request: SearchOptimizationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Оптимизирует производительность семантического поиска.
    
    Включает:
    - Измерение производительности
    - Анализ качества результатов
    - Рекомендации по оптимизации
    - Настройка кэширования
    """
    try:
        from services.vector_search_optimizer import get_vector_search_optimizer
        
        logger.info(f"Starting search optimization: {request.optimization_type}")
        
        # Получаем оптимизатор поиска
        optimizer = get_vector_search_optimizer()
        
        # Используем тестовые запросы или дефолтные
        test_queries = request.test_queries or [
            "OAuth 2.0 authentication implementation",
            "microservices architecture patterns",
            "database optimization techniques",
            "API security best practices",
            "monitoring and observability",
            "Kubernetes deployment strategies",
            "CI/CD pipeline setup",
            "error handling patterns",
            "caching strategies",
            "performance optimization"
        ]
        
        # Измеряем производительность
        performance_metrics = await optimizer.measure_search_performance(test_queries)
        
        # Генерируем рекомендации
        recommendations = optimizer.generate_optimization_recommendations(performance_metrics)
        
        # Получаем статистику кэша
        cache_stats = {
            "cache_size": len(optimizer.query_cache),
            "cache_hit_rate": optimizer.cache_stats["hits"] / (optimizer.cache_stats["hits"] + optimizer.cache_stats["misses"]) if (optimizer.cache_stats["hits"] + optimizer.cache_stats["misses"]) > 0 else 0.0,
            "total_hits": optimizer.cache_stats["hits"],
            "total_misses": optimizer.cache_stats["misses"]
        }
        
        # Создаем сводку улучшений
        improvement_summary = f"Производительность: {performance_metrics.avg_response_time_ms:.0f}ms среднее время отклика, {performance_metrics.queries_per_second:.1f} QPS. Найдено {len(recommendations)} рекомендаций по оптимизации."
        
        return SearchOptimizationResponse(
            performance_metrics={
                "avg_response_time_ms": performance_metrics.avg_response_time_ms,
                "p95_response_time_ms": performance_metrics.p95_response_time_ms,
                "p99_response_time_ms": performance_metrics.p99_response_time_ms,
                "queries_per_second": performance_metrics.queries_per_second,
                "success_rate": performance_metrics.success_rate,
                "cache_hit_rate": performance_metrics.cache_hit_rate,
                "total_queries": performance_metrics.total_queries,
                "failed_queries": performance_metrics.failed_queries
            },
            optimization_recommendations=[
                {
                    "category": rec.category,
                    "priority": rec.priority,
                    "title": rec.title,
                    "description": rec.description,
                    "expected_improvement": rec.expected_improvement,
                    "implementation_effort": rec.implementation_effort
                }
                for rec in recommendations
            ],
            cache_statistics=cache_stats,
            improvement_summary=improvement_summary
        )
        
    except Exception as e:
        logger.error(f"Search optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка оптимизации поиска: {str(e)}")

@router.get("/status")
@rate_limit
async def get_ai_enhancement_status(
    current_user: dict = Depends(get_current_user)
):
    """Получает общий статус AI возможностей."""
    try:
        # Проверяем доступность компонентов
        components_status = {}
        
        # Проверяем ModelTrainer
        try:
            from model_training import ModelTrainer
            trainer = ModelTrainer()
            components_status["model_trainer"] = {
                "status": "available",
                "model_name": trainer.model_name,
                "models_dir": str(trainer.models_dir)
            }
        except Exception as e:
            components_status["model_trainer"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Проверяем RFCQualityEnhancer
        try:
            from services.rfc_quality_enhancer import get_rfc_quality_enhancer
            quality_enhancer = get_rfc_quality_enhancer()
            components_status["rfc_quality_enhancer"] = {
                "status": "available",
                "min_requirements": quality_enhancer.min_requirements
            }
        except Exception as e:
            components_status["rfc_quality_enhancer"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Проверяем VectorSearchOptimizer
        try:
            from services.vector_search_optimizer import get_vector_search_optimizer
            optimizer = get_vector_search_optimizer()
            components_status["vector_search_optimizer"] = {
                "status": "available",
                "cache_size": len(optimizer.query_cache),
                "optimization_config": optimizer.optimization_config
            }
        except Exception as e:
            components_status["vector_search_optimizer"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Общий статус
        all_available = all(comp["status"] == "available" for comp in components_status.values())
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "ready" if all_available else "partial",
            "components": components_status,
            "capabilities": {
                "model_training": components_status.get("model_trainer", {}).get("status") == "available",
                "rfc_quality_analysis": components_status.get("rfc_quality_enhancer", {}).get("status") == "available",
                "search_optimization": components_status.get("vector_search_optimizer", {}).get("status") == "available",
                "multilingual_support": True,
                "fine_tuning": True
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get AI enhancement status: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса: {str(e)}")

# Background tasks

async def run_full_training_pipeline(trainer, training_id: str, use_feedback: bool):
    """Запускает полный пайплайн обучения в фоне."""
    try:
        logger.info(f"Starting full training pipeline: {training_id}")
        result = trainer.run_full_training_pipeline()
        logger.info(f"Training pipeline completed: {training_id}, result: {result}")
        # Здесь можно сохранить результат в базу данных
    except Exception as e:
        logger.error(f"Training pipeline failed: {training_id}, error: {e}")

async def run_multilingual_optimization(trainer, training_id: str):
    """Запускает мультиязычную оптимизацию в фоне."""
    try:
        logger.info(f"Starting multilingual optimization: {training_id}")
        result = trainer.optimize_for_multilingual()
        logger.info(f"Multilingual optimization completed: {training_id}, result: {result}")
    except Exception as e:
        logger.error(f"Multilingual optimization failed: {training_id}, error: {e}")

async def run_incremental_training(trainer, training_id: str, use_feedback: bool):
    """Запускает инкрементальное обучение в фоне."""
    try:
        logger.info(f"Starting incremental training: {training_id}")
        
        # Загружаем фидбек если нужно
        if use_feedback:
            feedback_data = trainer.get_feedback_from_postgres()
            if feedback_data:
                result = trainer.retrain_with_feedback(feedback_data)
            else:
                result = {"status": "skipped", "reason": "no_feedback_data"}
        else:
            # Обучаем на базовых данных
            examples = trainer.load_training_data()
            result = trainer.train_model(examples)
        
        logger.info(f"Incremental training completed: {training_id}, result: {result}")
    except Exception as e:
        logger.error(f"Incremental training failed: {training_id}, error: {e}") 