import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.feedback import (FeedbackAnalytics, FeedbackContext,
                             FeedbackReason, FeedbackRequest, FeedbackStats,
                             FeedbackType, RetrainingRequest,
                             RetrainingResponse, UserFeedback,
                             UserReputationScore)


class FeedbackServiceInterface(ABC):
    """Interface for feedback service."""

    @abstractmethod
    async def create_feedback(self, request: FeedbackRequest) -> UserFeedback:
        """Создает новую обратную связь."""
        pass

    @abstractmethod
    async def calculate_feedback_points(self, feedback: UserFeedback) -> int:
        """Вычисляет очки за обратную связь."""
        pass

    @abstractmethod
    async def update_user_reputation(
        self, user_id: str, feedback: UserFeedback
    ) -> None:
        """Обновляет репутацию пользователя."""
        pass

    @abstractmethod
    async def check_retraining_needed(self, context: FeedbackContext) -> None:
        """Проверяет необходимость переобучения."""
        pass

    @abstractmethod
    async def get_feedback_stats(self, target_id: str) -> Optional[FeedbackStats]:
        """Получает статистику обратной связи."""
        pass

    @abstractmethod
    async def get_feedback_analytics(
        self, context: FeedbackContext = None, date_from: datetime = None
    ) -> List[FeedbackAnalytics]:
        """Получает аналитику обратной связи."""
        pass

    @abstractmethod
    async def create_retraining_job(self, request: RetrainingRequest) -> Any:
        """Создает задачу переобучения."""
        pass

    @abstractmethod
    async def execute_retraining(self, job_id: str) -> None:
        """Выполняет переобучение модели."""
        pass

    @abstractmethod
    async def get_retraining_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Получает статус переобучения."""
        pass

    @abstractmethod
    async def get_user_reputation(self, user_id: str) -> Optional[UserReputationScore]:
        """Получает репутацию пользователя."""
        pass

    @abstractmethod
    async def create_user_reputation(self, user_id: str) -> UserReputationScore:
        """Создает базовую репутацию."""
        pass

    @abstractmethod
    async def get_feedback_trends(
        self, date_from: datetime, context: FeedbackContext = None
    ) -> Dict[str, Any]:
        """Получает тренды обратной связи."""
        pass

    @abstractmethod
    async def moderate_feedback(
        self, feedback_id: str, is_approved: bool, moderation_reason: str = None
    ) -> bool:
        """Модерирует обратную связь."""
        pass

    @abstractmethod
    async def export_feedback_data(
        self,
        context: FeedbackContext = None,
        date_from: datetime = None,
        date_to: datetime = None,
        format: str = "json",
    ) -> Dict[str, Any]:
        """Экспортирует данные обратной связи."""
        pass


class MockFeedbackService(FeedbackServiceInterface):
    """Mock implementation for development."""

    def __init__(self):
        self._feedback: Dict[str, UserFeedback] = {}
        self._reputations: Dict[str, UserReputationScore] = {}
        self._jobs: Dict[str, Dict[str, Any]] = {}

    async def create_feedback(self, request: FeedbackRequest) -> UserFeedback:
        """Создает mock обратную связь."""
        feedback = UserFeedback(
            id=str(uuid.uuid4()),
            user_id="mock_user",  # В реальности будет из аутентификации
            session_id=request.session_id,
            target_id=request.target_id,
            context=request.context,
            feedback_type=request.feedback_type,
            rating=request.rating,
            reason=request.reason,
            comment=request.comment,
            created_at=datetime.now(),
        )
        self._feedback[feedback.id] = feedback
        return feedback

    async def calculate_feedback_points(self, feedback: UserFeedback) -> int:
        """Вычисляет mock очки."""
        base_points = 1
        if feedback.rating:
            base_points += feedback.rating
        if feedback.comment and len(feedback.comment) > 20:
            base_points += 2
        return base_points

    async def update_user_reputation(
        self, user_id: str, feedback: UserFeedback
    ) -> None:
        """Mock обновление репутации."""
        reputation = self._reputations.get(user_id)
        if not reputation:
            reputation = await self.create_user_reputation(user_id)

        reputation.total_feedback_given += 1
        if feedback.feedback_type == FeedbackType.LIKE:
            reputation.helpful_feedback_count += 1

        # Простая формула репутации
        reputation.reputation_score = min(
            10.0,
            reputation.helpful_feedback_count
            / max(1, reputation.total_feedback_given)
            * 10,
        )
        reputation.last_updated = datetime.now()

        self._reputations[user_id] = reputation

    async def check_retraining_needed(self, context: FeedbackContext) -> None:
        """Mock проверка переобучения."""
        # В реальной реализации здесь будет логика определения
        # необходимости переобучения на основе накопленной обратной связи
        pass

    async def get_feedback_stats(self, target_id: str) -> Optional[FeedbackStats]:
        """Mock статистика обратной связи."""
        target_feedback = [
            f for f in self._feedback.values() if f.target_id == target_id
        ]

        if not target_feedback:
            return None

        likes = sum(1 for f in target_feedback if f.feedback_type == FeedbackType.LIKE)
        dislikes = sum(
            1 for f in target_feedback if f.feedback_type == FeedbackType.DISLIKE
        )
        reports = sum(
            1 for f in target_feedback if f.feedback_type == FeedbackType.REPORT
        )

        total = len(target_feedback)
        like_percentage = (likes / total * 100) if total > 0 else 0

        # Находим самую частую причину жалоб
        dislike_reasons = [f.reason for f in target_feedback if f.reason]
        most_common_reason = None
        if dislike_reasons:
            reason_counts = {}
            for reason in dislike_reasons:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
            most_common_reason = max(reason_counts, key=reason_counts.get)

        ratings = [f.rating for f in target_feedback if f.rating]
        avg_rating = sum(ratings) / len(ratings) if ratings else None

        return FeedbackStats(
            target_id=target_id,
            total_feedback=total,
            likes=likes,
            dislikes=dislikes,
            reports=reports,
            average_rating=avg_rating,
            like_percentage=like_percentage,
            most_common_dislike_reason=most_common_reason,
        )

    async def get_feedback_analytics(
        self, context: FeedbackContext = None, date_from: datetime = None
    ) -> List[FeedbackAnalytics]:
        """Mock аналитика обратной связи."""
        feedback_list = list(self._feedback.values())

        if context:
            feedback_list = [f for f in feedback_list if f.context == context]

        if date_from:
            feedback_list = [f for f in feedback_list if f.created_at >= date_from]

        if not feedback_list:
            return []

        total_items = len(set(f.target_id for f in feedback_list))
        total_feedback = len(feedback_list)
        positive_feedback = len(
            [f for f in feedback_list if f.feedback_type == FeedbackType.LIKE]
        )

        # Топ проблем
        reasons = [f.reason for f in feedback_list if f.reason]
        reason_counts = {}
        for reason in reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        top_issues = sorted(
            reason_counts.keys(), key=lambda x: reason_counts[x], reverse=True
        )[:5]

        analytics = FeedbackAnalytics(
            context=context or FeedbackContext.RFC_GENERATION,
            total_items=total_items,
            feedback_coverage=min(1.0, total_feedback / max(1, total_items)),
            positive_ratio=positive_feedback / max(1, total_feedback),
            top_issues=top_issues,
            recommendations=[
                "Улучшить качество генерируемого контента",
                "Добавить больше интерактивных вопросов",
                "Обучить модель на большем количестве примеров",
            ],
        )

        return [analytics]

    async def create_retraining_job(self, request: RetrainingRequest) -> Any:
        """Mock создание задачи переобучения."""
        job_id = str(uuid.uuid4())
        job = {
            "id": job_id,
            "context": request.context,
            "status": "pending",
            "data_points_count": 150,  # Mock количество
            "estimated_duration_minutes": 45,
            "created_at": datetime.now(),
        }
        self._jobs[job_id] = job
        return job

    async def execute_retraining(self, job_id: str) -> None:
        """Mock выполнение переобучения."""
        job = self._jobs.get(job_id)
        if job:
            job["status"] = "completed"
            job["completed_at"] = datetime.now()
            self._jobs[job_id] = job

    async def get_retraining_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Mock статус переобучения."""
        return self._jobs.get(job_id)

    async def get_user_reputation(self, user_id: str) -> Optional[UserReputationScore]:
        """Mock репутация пользователя."""
        return self._reputations.get(user_id)

    async def create_user_reputation(self, user_id: str) -> UserReputationScore:
        """Mock создание репутации."""
        reputation = UserReputationScore(
            user_id=user_id,
            total_feedback_given=0,
            helpful_feedback_count=0,
            reputation_score=5.0,  # Начальная репутация
            expertise_areas=[],
            last_updated=datetime.now(),
        )
        self._reputations[user_id] = reputation
        return reputation

    async def get_feedback_trends(
        self, date_from: datetime, context: FeedbackContext = None
    ) -> Dict[str, Any]:
        """Mock тренды обратной связи."""
        return {
            "period": f"За период с {date_from.strftime('%Y-%m-%d')}",
            "total_feedback": 45,
            "positive_trend": "+12%",
            "negative_trend": "-3%",
            "most_active_users": ["user1", "user2", "user3"],
            "top_issues": ["качество контента", "время ответа", "релевантность"],
            "improvements": [
                "Улучшение времени отклика на 15%",
                "Повышение качества генерации на 8%",
            ],
        }

    async def moderate_feedback(
        self, feedback_id: str, is_approved: bool, moderation_reason: str = None
    ) -> bool:
        """Mock модерация обратной связи."""
        if feedback_id in self._feedback:
            if not is_approved:
                del self._feedback[feedback_id]
            return True
        return False

    async def export_feedback_data(
        self,
        context: FeedbackContext = None,
        date_from: datetime = None,
        date_to: datetime = None,
        format: str = "json",
    ) -> Dict[str, Any]:
        """Mock экспорт данных."""
        return {
            "url": f"https://api.company.com/exports/feedback_{uuid.uuid4().hex[:8]}.{format}",
            "total_records": 234,
            "format": format,
            "expires_at": (datetime.now().timestamp() + 3600),  # Через час
        }


# Global instance
_feedback_service_instance = None


def get_feedback_service() -> FeedbackServiceInterface:
    """Dependency injection для feedback service."""
    global _feedback_service_instance
    if _feedback_service_instance is None:
        _feedback_service_instance = MockFeedbackService()
    return _feedback_service_instance


# Alias for backward compatibility
FeedbackService = MockFeedbackService
