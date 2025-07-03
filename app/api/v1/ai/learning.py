"""
API endpoints for Learning Pipeline.

Обеспечивает сбор фидбека пользователей и автоматическое переобучение модели.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from domain.core.learning_pipeline_service import get_learning_service
from models.feedback import FeedbackType

router = APIRouter(prefix="/learning", tags=["Learning Pipeline"])


class RFCFeedbackRequest(BaseModel):
    """Запрос на фидбек по RFC."""

    rfc_id: str
    feedback_type: FeedbackType  # like, dislike
    rating: Optional[int] = None  # 1-5 звезд
    comment: Optional[str] = None
    improvement_suggestions: Optional[str] = None


class LearningStatsResponse(BaseModel):
    """Статистика обучения."""

    total_examples: int
    average_quality: float
    quality_distribution: Dict[str, int]
    ready_for_retraining: bool
    last_retraining: Optional[str] = None
    message: str


@router.post(
    "/feedback",
    status_code=status.HTTP_200_OK,
    summary="Submit RFC Feedback",
    description="Отправляет фидбек по сгенерированному RFC и запускает переобучение при достижении порога",
)
async def submit_rfc_feedback(request: RFCFeedbackRequest) -> Dict[str, Any]:
    """
    Отправляет фидбек по RFC и автоматически запускает переобучение модели.

    **Процесс:**
    1. Сохраняет фидбек пользователя
    2. Обновляет обучающий датасет
    3. Проверяет нужно ли переобучение
    4. Автоматически запускает переобучение если собрано достаточно примеров

    **Переобучение запускается при:**
    - Накоплении 10+ качественных примеров
    - Достижении порога качества фидбека
    """

    try:
        learning_service = get_learning_service()

        # Собираем фидбек и запускаем переобучение если нужно
        result = await learning_service.collect_user_feedback(
            rfc_id=request.rfc_id,
            feedback_type=request.feedback_type,
            rating=request.rating,
            comment=request.comment,
        )

        return {"success": True, "data": result, "message": result["message"]}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process feedback: {str(e)}",
        )


@router.get(
    "/stats",
    response_model=LearningStatsResponse,
    summary="Get Learning Statistics",
    description="Возвращает статистику процесса обучения модели",
)
async def get_learning_statistics() -> LearningStatsResponse:
    """
    Получает текущую статистику процесса обучения.

    **Включает:**
    - Количество собранных примеров
    - Среднее качество фидбека
    - Распределение по категориям качества
    - Готовность к переобучению
    - Информацию о последнем переобучении
    """

    try:
        learning_service = get_learning_service()
        stats = await learning_service.get_learning_stats()

        # Формируем понятное сообщение
        if stats["ready_for_retraining"]:
            message = (
                f"🎯 Готово к переобучению! Собрано {stats['total_examples']} примеров."
            )
        else:
            remaining = 10 - stats["total_examples"]  # min_examples_for_retraining = 10
            message = f"📊 Собрано {stats['total_examples']} примеров. Нужно еще {remaining} для переобучения."

        return LearningStatsResponse(
            total_examples=stats["total_examples"],
            average_quality=stats["average_quality"],
            quality_distribution=stats["quality_distribution"],
            ready_for_retraining=stats["ready_for_retraining"],
            last_retraining=stats["last_retraining"],
            message=message,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get learning stats: {str(e)}",
        )


@router.post(
    "/manual-retrain",
    status_code=status.HTTP_200_OK,
    summary="Manual Model Retraining",
    description="Запускает ручное переобучение модели (для админов)",
)
async def manual_retrain() -> Dict[str, Any]:
    """
    Запускает ручное переобучение модели независимо от порога.

    **Использование:** Для админов/разработчиков когда нужно
    принудительно переобучить модель.
    """

    try:
        learning_service = get_learning_service()

        # Принудительно запускаем переобучение
        result = await learning_service._trigger_retraining()

        return {
            "success": True,
            "data": result,
            "message": "Ручное переобучение модели запущено",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger manual retraining: {str(e)}",
        )


@router.get(
    "/health",
    summary="Learning Pipeline Health",
    description="Проверяет статус Learning Pipeline",
)
async def learning_health() -> Dict[str, Any]:
    """Проверяет здоровье Learning Pipeline."""

    try:
        learning_service = get_learning_service()
        stats = await learning_service.get_learning_stats()

        # Определяем статус
        if stats["total_examples"] == 0:
            health_status = "initializing"
        elif stats["ready_for_retraining"]:
            health_status = "ready_for_retraining"
        else:
            health_status = "collecting_feedback"

        return {
            "status": "healthy",
            "learning_status": health_status,
            "examples_collected": stats["total_examples"],
            "average_quality": stats["average_quality"],
            "last_retraining": stats["last_retraining"],
            "timestamp": "2025-06-11",
            "message": "Learning Pipeline работает нормально",
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Проблемы с Learning Pipeline",
        }
