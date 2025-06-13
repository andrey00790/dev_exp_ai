from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from datetime import datetime, timedelta

from models.feedback import (
    FeedbackRequest, FeedbackResponse, UserFeedback,
    FeedbackStats, FeedbackAnalytics, FeedbackContext,
    RetrainingRequest, RetrainingResponse,
    UserReputationScore, FeedbackType
)
from models.base import BaseResponse
from services.feedback_service import FeedbackServiceInterface, get_feedback_service

router = APIRouter()


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit Feedback",
    description="Отправляет обратную связь (лайк/дизлайк) для улучшения качества AI"
)
async def submit_feedback(
    request: FeedbackRequest,
    background_tasks: BackgroundTasks,
    feedback_service: FeedbackServiceInterface = Depends(get_feedback_service)
) -> FeedbackResponse:
    """
    Отправляет обратную связь от пользователя.
    
    Поддерживает:
    - Лайки/дизлайки (как в ChatGPT)
    - Оценки по шкале 1-5
    - Текстовые комментарии
    - Причины негативной обратной связи
    
    Обратная связь используется для переобучения модели.
    """
    try:
        # Сохраняем обратную связь
        feedback = await feedback_service.create_feedback(request)
        
        # Начисляем очки пользователю за фидбек
        points = await feedback_service.calculate_feedback_points(feedback)
        
        # Асинхронно обновляем репутацию пользователя
        if feedback.user_id:
            background_tasks.add_task(
                feedback_service.update_user_reputation,
                feedback.user_id,
                feedback
            )
        
        # Асинхронно проверяем, нужно ли переобучение
        background_tasks.add_task(
            feedback_service.check_retraining_needed,
            feedback.context
        )
        
        return FeedbackResponse(
            feedback_id=feedback.id,
            message="Спасибо за обратную связь! Она поможет улучшить качество AI.",
            points_earned=points
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при сохранении обратной связи: {str(e)}"
        )


@router.get(
    "/feedback/stats/{target_id}",
    response_model=FeedbackStats,
    summary="Get Feedback Stats",
    description="Получает статистику обратной связи для конкретного объекта"
)
async def get_feedback_stats(
    target_id: str,
    feedback_service: FeedbackServiceInterface = Depends(get_feedback_service)
) -> FeedbackStats:
    """Возвращает статистику обратной связи для RFC, результата поиска и т.д."""
    try:
        stats = await feedback_service.get_feedback_stats(target_id)
        if not stats:
            # Возвращаем пустую статистику, если нет обратной связи
            return FeedbackStats(
                target_id=target_id,
                total_feedback=0,
                likes=0,
                dislikes=0,
                reports=0,
                like_percentage=0.0
            )
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении статистики: {str(e)}"
        )


@router.get(
    "/feedback/analytics",
    response_model=List[FeedbackAnalytics],
    summary="Get Feedback Analytics",
    description="Получает аналитику обратной связи для переобучения модели"
)
async def get_feedback_analytics(
    context: FeedbackContext = None,
    days: int = 30,
    feedback_service: FeedbackServiceInterface = Depends(get_feedback_service)
) -> List[FeedbackAnalytics]:
    """
    Возвращает аналитику обратной связи для улучшения модели.
    
    Включает:
    - Процент положительных/отрицательных оценок
    - Основные проблемы
    - Тренды по времени
    - Рекомендации по улучшению
    """
    try:
        date_from = datetime.now() - timedelta(days=days)
        analytics = await feedback_service.get_feedback_analytics(
            context=context,
            date_from=date_from
        )
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении аналитики: {str(e)}"
        )


@router.post(
    "/feedback/retrain",
    response_model=RetrainingResponse,
    summary="Trigger Model Retraining",
    description="Запускает переобучение модели на основе обратной связи"
)
async def trigger_retraining(
    request: RetrainingRequest,
    background_tasks: BackgroundTasks,
    feedback_service: FeedbackServiceInterface = Depends(get_feedback_service)
) -> RetrainingResponse:
    """
    Запускает переобучение модели на основе собранной обратной связи.
    
    Использует только проверенную и качественную обратную связь
    для улучшения точности AI генерации.
    """
    try:
        # Создаем задачу на переобучение
        job = await feedback_service.create_retraining_job(request)
        
        # Запускаем переобучение в фоне
        background_tasks.add_task(
            feedback_service.execute_retraining,
            job.id
        )
        
        return RetrainingResponse(
            job_id=job.id,
            status="started",
            data_points_count=job.data_points_count,
            estimated_duration_minutes=job.estimated_duration_minutes,
            message="Переобучение модели запущено. Вы получите уведомление о завершении."
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при запуске переобучения: {str(e)}"
        )


@router.get(
    "/feedback/retrain/{job_id}",
    response_model=Dict[str, Any],
    summary="Get Retraining Status",
    description="Получает статус задачи переобучения модели"
)
async def get_retraining_status(
    job_id: str,
    feedback_service: FeedbackServiceInterface = Depends(get_feedback_service)
) -> Dict[str, Any]:
    """Возвращает статус задачи переобучения модели."""
    try:
        status_info = await feedback_service.get_retraining_status(job_id)
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача переобучения не найдена"
            )
        return status_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении статуса переобучения: {str(e)}"
        )


@router.get(
    "/feedback/reputation/{user_id}",
    response_model=UserReputationScore,
    summary="Get User Reputation",
    description="Получает репутацию пользователя в системе обратной связи"
)
async def get_user_reputation(
    user_id: str,
    feedback_service: FeedbackServiceInterface = Depends(get_feedback_service)
) -> UserReputationScore:
    """
    Возвращает репутацию пользователя.
    
    Репутация влияет на вес обратной связи при переобучении:
    - Пользователи с высокой репутацией влияют больше
    - Спам и некачественная обратная связь снижает репутацию
    """
    try:
        reputation = await feedback_service.get_user_reputation(user_id)
        if not reputation:
            # Создаем базовую репутацию для нового пользователя
            reputation = await feedback_service.create_user_reputation(user_id)
        return reputation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении репутации: {str(e)}"
        )


@router.get(
    "/feedback/trends",
    response_model=Dict[str, Any],
    summary="Get Feedback Trends",
    description="Получает тренды обратной связи за период времени"
)
async def get_feedback_trends(
    days: int = 30,
    context: FeedbackContext = None,
    feedback_service: FeedbackServiceInterface = Depends(get_feedback_service)
) -> Dict[str, Any]:
    """
    Возвращает тренды обратной связи для мониторинга качества AI.
    
    Включает:
    - Динамику положительных/отрицательных оценок
    - Популярные причины жалоб
    - Сравнение с предыдущими периодами
    """
    try:
        date_from = datetime.now() - timedelta(days=days)
        trends = await feedback_service.get_feedback_trends(
            date_from=date_from,
            context=context
        )
        return trends
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении трендов: {str(e)}"
        )


@router.delete(
    "/feedback/{feedback_id}",
    response_model=BaseResponse,
    summary="Delete Feedback",
    description="Удаляет обратную связь (для модерации)"
)
async def delete_feedback(
    feedback_id: str,
    reason: str = "inappropriate_content",
    feedback_service: FeedbackServiceInterface = Depends(get_feedback_service)
) -> BaseResponse:
    """
    Удаляет обратную связь (только для модераторов).
    
    Используется для удаления неподходящего контента
    или спама в обратной связи.
    """
    try:
        success = await feedback_service.moderate_feedback(
            feedback_id=feedback_id,
            is_approved=False,
            moderation_reason=reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Обратная связь не найдена"
            )
        
        return BaseResponse(
            message="Обратная связь удалена"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении обратной связи: {str(e)}"
        )


@router.get(
    "/feedback/export",
    response_model=Dict[str, Any],
    summary="Export Feedback Data",
    description="Экспортирует данные обратной связи для анализа"
)
async def export_feedback_data(
    context: FeedbackContext = None,
    date_from: datetime = None,
    date_to: datetime = None,
    format: str = "json",
    feedback_service: FeedbackServiceInterface = Depends(get_feedback_service)
) -> Dict[str, Any]:
    """
    Экспортирует данные обратной связи для внешнего анализа.
    
    Поддерживает фильтрацию по:
    - Контексту (RFC генерация, поиск и т.д.)
    - Временному периоду
    - Типу обратной связи
    """
    try:
        if not date_from:
            date_from = datetime.now() - timedelta(days=30)
        if not date_to:
            date_to = datetime.now()
        
        export_data = await feedback_service.export_feedback_data(
            context=context,
            date_from=date_from,
            date_to=date_to,
            format=format
        )
        
        return {
            "export_url": export_data.get("url"),
            "total_records": export_data.get("total_records"),
            "generated_at": datetime.now().isoformat(),
            "filters": {
                "context": context,
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat()
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при экспорте данных: {str(e)}"
        ) 