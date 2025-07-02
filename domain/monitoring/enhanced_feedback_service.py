"""
Enhanced Feedback Service - Расширенная система обратной связи

Система сбора и обработки обратной связи пользователей с поддержкой:
- Лайки/дизлайки для всех типов контента
- Комментарии пользователей с rich text
- Real-time уведомления через WebSocket PubSub
- Интеграция с ML pipeline для переобучения
- Аналитика и метрики обратной связи
- Модерация контента
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

# Используем паттерны из Context7 документации для WebSocket PubSub
from fastapi_websocket_pubsub import PubSubEndpoint

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Типы обратной связи"""

    LIKE = "like"
    DISLIKE = "dislike"
    COMMENT = "comment"
    RATING = "rating"
    REPORT = "report"


class ContentType(Enum):
    """Типы контента для feedback"""

    SEARCH_RESULT = "search_result"
    RFC_GENERATION = "rfc_generation"
    CODE_DOCUMENTATION = "code_documentation"
    DEEP_RESEARCH = "deep_research"
    AI_RESPONSE = "ai_response"
    CHAT_MESSAGE = "chat_message"


class FeedbackStatus(Enum):
    """Статусы feedback"""

    ACTIVE = "active"
    MODERATED = "moderated"
    HIDDEN = "hidden"
    PROCESSED = "processed"


class SentimentScore(Enum):
    """Оценка тональности"""

    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


@dataclass
class FeedbackItem:
    """Элемент обратной связи"""

    feedback_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    content_id: str = ""
    content_type: ContentType = ContentType.AI_RESPONSE
    feedback_type: FeedbackType = FeedbackType.LIKE
    status: FeedbackStatus = FeedbackStatus.ACTIVE

    # Основные данные
    value: Optional[Any] = (
        None  # True/False для лайков, текст для комментариев, число для рейтинга
    )
    comment: str = ""
    rating: Optional[int] = None  # 1-5 звезд

    # Метаданные
    sentiment_score: Optional[SentimentScore] = None
    confidence: float = 0.0
    tags: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    # Временные метки
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None

    # Модерация
    is_moderated: bool = False
    moderation_reason: str = ""
    moderator_id: str = ""


@dataclass
class FeedbackSummary:
    """Сводка обратной связи по контенту"""

    content_id: str = ""
    content_type: ContentType = ContentType.AI_RESPONSE

    # Статистика лайков/дизлайков
    total_likes: int = 0
    total_dislikes: int = 0
    like_ratio: float = 0.0

    # Статистика комментариев
    total_comments: int = 0
    avg_rating: float = 0.0
    sentiment_distribution: Dict[str, int] = field(default_factory=dict)

    # Популярные теги
    popular_tags: List[str] = field(default_factory=list)

    # Временные метрики
    last_feedback_at: Optional[datetime] = None
    feedback_velocity: float = 0.0  # feedback per hour

    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class FeedbackNotification:
    """Уведомление о новой обратной связи"""

    notification_id: str = field(default_factory=lambda: str(uuid4()))
    feedback_id: str = ""
    content_id: str = ""
    user_id: str = ""
    notification_type: str = ""
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class EnhancedFeedbackService:
    """Расширенный сервис обратной связи"""

    def __init__(self, pubsub_endpoint: Optional[PubSubEndpoint] = None):
        self.pubsub = pubsub_endpoint or PubSubEndpoint()

        # Хранилища данных
        self.feedback_items: Dict[str, FeedbackItem] = {}
        self.content_summaries: Dict[str, FeedbackSummary] = {}
        self.user_feedback_history: Dict[str, List[str]] = {}

        # Конфигурация
        self.config = {
            "max_comment_length": 2000,
            "auto_moderation_enabled": True,
            "sentiment_analysis_enabled": True,
            "real_time_notifications": True,
            "feedback_aggregation_interval": 60,  # секунды
            "spam_detection_enabled": True,
        }

        # Метрики
        self.metrics = {
            "total_feedback": 0,
            "total_likes": 0,
            "total_dislikes": 0,
            "total_comments": 0,
            "avg_sentiment": 0.0,
            "moderated_items": 0,
            "spam_detected": 0,
        }

        # Кэш для производительности
        self._summary_cache: Dict[str, FeedbackSummary] = {}
        self._cache_ttl = timedelta(minutes=5)
        self._last_cache_update: Dict[str, datetime] = {}

        # Модерация
        self._spam_keywords = {
            "spam",
            "advertisement",
            "promotion",
            "click here",
            "free money",
        }
        self._toxic_keywords = {"hate", "abuse", "toxic", "harassment"}

    async def submit_feedback(
        self,
        user_id: str,
        content_id: str,
        content_type: ContentType,
        feedback_type: FeedbackType,
        value: Any = None,
        comment: str = "",
        rating: Optional[int] = None,
        context: Dict[str, Any] = None,
    ) -> FeedbackItem:
        """Отправка обратной связи"""
        try:
            # Валидация входных данных
            if not self._validate_feedback_input(feedback_type, value, comment, rating):
                raise ValueError("Invalid feedback input")

            # Создание элемента обратной связи
            feedback = FeedbackItem(
                user_id=user_id,
                content_id=content_id,
                content_type=content_type,
                feedback_type=feedback_type,
                value=value,
                comment=comment.strip(),
                rating=rating,
                context=context or {},
            )

            # Автоматическая модерация
            if self.config["auto_moderation_enabled"]:
                await self._moderate_feedback(feedback)

            # Анализ тональности для комментариев
            if feedback.comment and self.config["sentiment_analysis_enabled"]:
                feedback.sentiment_score = await self._analyze_sentiment(
                    feedback.comment
                )

            # Сохранение
            self.feedback_items[feedback.feedback_id] = feedback

            # Обновление истории пользователя
            if user_id not in self.user_feedback_history:
                self.user_feedback_history[user_id] = []
            self.user_feedback_history[user_id].append(feedback.feedback_id)

            # Обновление сводки контента
            await self._update_content_summary(content_id, content_type)

            # Обновление метрик
            self._update_metrics(feedback)

            # Real-time уведомления
            if self.config["real_time_notifications"]:
                await self._send_feedback_notification(feedback)

            logger.info(
                f"✅ Feedback submitted: {feedback.feedback_id} for content {content_id}"
            )
            return feedback

        except Exception as e:
            logger.error(f"❌ Error submitting feedback: {e}")
            raise

    async def get_content_feedback(
        self,
        content_id: str,
        include_comments: bool = True,
        include_moderated: bool = False,
    ) -> FeedbackSummary:
        """Получение обратной связи по контенту"""
        try:
            # Проверка кэша
            cache_key = f"{content_id}_{include_comments}_{include_moderated}"
            if self._is_cache_valid(cache_key):
                return self._summary_cache[cache_key]

            # Фильтрация feedback по контенту
            content_feedback = [
                fb
                for fb in self.feedback_items.values()
                if fb.content_id == content_id
                and (include_moderated or not fb.is_moderated)
            ]

            if not content_feedback:
                return FeedbackSummary(content_id=content_id)

            # Вычисление сводки
            summary = await self._calculate_content_summary(
                content_id, content_feedback
            )

            # Добавление комментариев если нужно
            if include_comments:
                summary.comments = [
                    {
                        "feedback_id": fb.feedback_id,
                        "user_id": fb.user_id,
                        "comment": fb.comment,
                        "rating": fb.rating,
                        "sentiment": (
                            fb.sentiment_score.value if fb.sentiment_score else None
                        ),
                        "created_at": fb.created_at.isoformat(),
                        "tags": fb.tags,
                    }
                    for fb in content_feedback
                    if fb.feedback_type == FeedbackType.COMMENT and fb.comment
                ]

            # Сохранение в кэш
            self._summary_cache[cache_key] = summary
            self._last_cache_update[cache_key] = datetime.now()

            return summary

        except Exception as e:
            logger.error(f"❌ Error getting content feedback: {e}")
            raise

    async def get_user_feedback_history(
        self, user_id: str, limit: int = 50, content_type: Optional[ContentType] = None
    ) -> List[FeedbackItem]:
        """Получение истории обратной связи пользователя"""
        try:
            if user_id not in self.user_feedback_history:
                return []

            feedback_ids = self.user_feedback_history[user_id]
            user_feedback = [
                self.feedback_items[fb_id]
                for fb_id in feedback_ids
                if fb_id in self.feedback_items
            ]

            # Фильтрация по типу контента
            if content_type:
                user_feedback = [
                    fb for fb in user_feedback if fb.content_type == content_type
                ]

            # Сортировка по дате (новые первыми)
            user_feedback.sort(key=lambda x: x.created_at, reverse=True)

            return user_feedback[:limit]

        except Exception as e:
            logger.error(f"❌ Error getting user feedback history: {e}")
            return []

    async def moderate_feedback(
        self,
        feedback_id: str,
        moderator_id: str,
        action: str = "hide",
        reason: str = "",
    ) -> bool:
        """Модерация обратной связи"""
        try:
            if feedback_id not in self.feedback_items:
                return False

            feedback = self.feedback_items[feedback_id]

            if action == "hide":
                feedback.status = FeedbackStatus.HIDDEN
            elif action == "approve":
                feedback.status = FeedbackStatus.ACTIVE
            elif action == "remove":
                feedback.status = FeedbackStatus.MODERATED

            feedback.is_moderated = True
            feedback.moderation_reason = reason
            feedback.moderator_id = moderator_id
            feedback.updated_at = datetime.now()

            # Обновление сводки контента
            await self._update_content_summary(
                feedback.content_id, feedback.content_type
            )

            # Уведомление о модерации
            if self.config["real_time_notifications"]:
                await self._send_moderation_notification(feedback, action, reason)

            self.metrics["moderated_items"] += 1

            logger.info(f"✅ Feedback moderated: {feedback_id} by {moderator_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error moderating feedback: {e}")
            return False

    async def get_feedback_analytics(
        self,
        time_period: timedelta = timedelta(days=7),
        content_type: Optional[ContentType] = None,
    ) -> Dict[str, Any]:
        """Получение аналитики обратной связи"""
        try:
            cutoff_date = datetime.now() - time_period

            # Фильтрация feedback по времени и типу
            filtered_feedback = [
                fb
                for fb in self.feedback_items.values()
                if fb.created_at >= cutoff_date
                and (not content_type or fb.content_type == content_type)
            ]

            if not filtered_feedback:
                return {"total_feedback": 0}

            # Вычисление аналитики
            analytics = {
                "time_period_days": time_period.days,
                "total_feedback": len(filtered_feedback),
                "feedback_by_type": {},
                "feedback_by_content_type": {},
                "sentiment_distribution": {},
                "rating_distribution": {},
                "top_content": [],
                "engagement_metrics": {},
                "trends": {},
            }

            # Распределение по типам
            for fb in filtered_feedback:
                fb_type = fb.feedback_type.value
                content_type_val = fb.content_type.value

                analytics["feedback_by_type"][fb_type] = (
                    analytics["feedback_by_type"].get(fb_type, 0) + 1
                )
                analytics["feedback_by_content_type"][content_type_val] = (
                    analytics["feedback_by_content_type"].get(content_type_val, 0) + 1
                )

                if fb.sentiment_score:
                    sentiment = fb.sentiment_score.value
                    analytics["sentiment_distribution"][sentiment] = (
                        analytics["sentiment_distribution"].get(sentiment, 0) + 1
                    )

                if fb.rating:
                    rating = str(fb.rating)
                    analytics["rating_distribution"][rating] = (
                        analytics["rating_distribution"].get(rating, 0) + 1
                    )

            # Топ контент по обратной связи
            content_feedback_count = {}
            for fb in filtered_feedback:
                content_id = fb.content_id
                content_feedback_count[content_id] = (
                    content_feedback_count.get(content_id, 0) + 1
                )

            analytics["top_content"] = sorted(
                content_feedback_count.items(), key=lambda x: x[1], reverse=True
            )[:10]

            # Метрики вовлечения
            analytics["engagement_metrics"] = {
                "feedback_per_day": len(filtered_feedback) / max(time_period.days, 1),
                "like_ratio": self._calculate_like_ratio(filtered_feedback),
                "comment_rate": len([fb for fb in filtered_feedback if fb.comment])
                / len(filtered_feedback),
                "avg_rating": self._calculate_avg_rating(filtered_feedback),
            }

            return analytics

        except Exception as e:
            logger.error(f"❌ Error getting feedback analytics: {e}")
            return {"error": str(e)}

    async def _validate_feedback_input(
        self,
        feedback_type: FeedbackType,
        value: Any,
        comment: str,
        rating: Optional[int],
    ) -> bool:
        """Валидация входных данных"""
        if feedback_type in [FeedbackType.LIKE, FeedbackType.DISLIKE]:
            return value is not None and isinstance(value, bool)
        elif feedback_type == FeedbackType.COMMENT:
            return (
                len(comment.strip()) > 0
                and len(comment) <= self.config["max_comment_length"]
            )
        elif feedback_type == FeedbackType.RATING:
            return rating is not None and 1 <= rating <= 5
        return True

    async def _moderate_feedback(self, feedback: FeedbackItem):
        """Автоматическая модерация контента"""
        if not feedback.comment:
            return

        comment_lower = feedback.comment.lower()

        # Проверка на спам
        if self._detect_spam(comment_lower):
            feedback.status = FeedbackStatus.MODERATED
            feedback.moderation_reason = "Spam detected"
            self.metrics["spam_detected"] += 1
            return

        # Проверка на токсичность
        if self._detect_toxicity(comment_lower):
            feedback.status = FeedbackStatus.MODERATED
            feedback.moderation_reason = "Toxic content detected"
            return

    def _detect_spam(self, comment: str) -> bool:
        """Определение спама"""
        return any(keyword in comment for keyword in self._spam_keywords)

    def _detect_toxicity(self, comment: str) -> bool:
        """Определение токсичного контента"""
        return any(keyword in comment for keyword in self._toxic_keywords)

    async def _analyze_sentiment(self, comment: str) -> SentimentScore:
        """Анализ тональности комментария"""
        # Простая эвристика для демонстрации
        comment_lower = comment.lower()

        positive_words = {
            "good",
            "great",
            "excellent",
            "awesome",
            "perfect",
            "love",
            "best",
        }
        negative_words = {
            "bad",
            "terrible",
            "awful",
            "hate",
            "worst",
            "horrible",
            "poor",
        }

        positive_count = sum(1 for word in positive_words if word in comment_lower)
        negative_count = sum(1 for word in negative_words if word in comment_lower)

        if positive_count > negative_count + 1:
            return SentimentScore.POSITIVE
        elif negative_count > positive_count + 1:
            return SentimentScore.NEGATIVE
        else:
            return SentimentScore.NEUTRAL

    async def _update_content_summary(self, content_id: str, content_type: ContentType):
        """Обновление сводки контента"""
        content_feedback = [
            fb
            for fb in self.feedback_items.values()
            if fb.content_id == content_id and fb.status == FeedbackStatus.ACTIVE
        ]

        summary = await self._calculate_content_summary(content_id, content_feedback)
        summary.content_type = content_type

        self.content_summaries[content_id] = summary

        # Очистка кэша для этого контента
        keys_to_remove = [
            key for key in self._summary_cache.keys() if key.startswith(content_id)
        ]
        for key in keys_to_remove:
            self._summary_cache.pop(key, None)
            self._last_cache_update.pop(key, None)

    async def _calculate_content_summary(
        self, content_id: str, feedback_list: List[FeedbackItem]
    ) -> FeedbackSummary:
        """Вычисление сводки контента"""
        summary = FeedbackSummary(content_id=content_id)

        if not feedback_list:
            return summary

        # Подсчет лайков/дизлайков
        likes = [
            fb
            for fb in feedback_list
            if fb.feedback_type == FeedbackType.LIKE and fb.value
        ]
        dislikes = [
            fb
            for fb in feedback_list
            if fb.feedback_type == FeedbackType.DISLIKE and fb.value
        ]

        summary.total_likes = len(likes)
        summary.total_dislikes = len(dislikes)

        total_reactions = summary.total_likes + summary.total_dislikes
        if total_reactions > 0:
            summary.like_ratio = summary.total_likes / total_reactions

        # Подсчет комментариев
        comments = [fb for fb in feedback_list if fb.comment]
        summary.total_comments = len(comments)

        # Средний рейтинг
        ratings = [fb.rating for fb in feedback_list if fb.rating]
        if ratings:
            summary.avg_rating = sum(ratings) / len(ratings)

        # Распределение тональности
        sentiments = [
            fb.sentiment_score.value for fb in feedback_list if fb.sentiment_score
        ]
        summary.sentiment_distribution = {
            sentiment: sentiments.count(sentiment) for sentiment in set(sentiments)
        }

        # Популярные теги
        all_tags = []
        for fb in feedback_list:
            all_tags.extend(fb.tags)

        tag_counts = {tag: all_tags.count(tag) for tag in set(all_tags)}
        summary.popular_tags = sorted(
            tag_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]
        summary.popular_tags = [tag for tag, count in summary.popular_tags]

        # Временные метрики
        if feedback_list:
            summary.last_feedback_at = max(fb.created_at for fb in feedback_list)

            # Скорость обратной связи (feedback в час)
            time_span = (
                datetime.now() - min(fb.created_at for fb in feedback_list)
            ).total_seconds() / 3600
            if time_span > 0:
                summary.feedback_velocity = len(feedback_list) / time_span

        return summary

    def _update_metrics(self, feedback: FeedbackItem):
        """Обновление метрик"""
        self.metrics["total_feedback"] += 1

        if feedback.feedback_type == FeedbackType.LIKE and feedback.value:
            self.metrics["total_likes"] += 1
        elif feedback.feedback_type == FeedbackType.DISLIKE and feedback.value:
            self.metrics["total_dislikes"] += 1
        elif feedback.feedback_type == FeedbackType.COMMENT:
            self.metrics["total_comments"] += 1

    async def _send_feedback_notification(self, feedback: FeedbackItem):
        """Отправка уведомления о новой обратной связи"""
        try:
            notification = FeedbackNotification(
                feedback_id=feedback.feedback_id,
                content_id=feedback.content_id,
                user_id=feedback.user_id,
                notification_type="new_feedback",
                message=f"New {feedback.feedback_type.value} on {feedback.content_type.value}",
                data={
                    "feedback_type": feedback.feedback_type.value,
                    "content_type": feedback.content_type.value,
                    "sentiment": (
                        feedback.sentiment_score.value
                        if feedback.sentiment_score
                        else None
                    ),
                },
            )

            # Отправка через PubSub (используя паттерны из Context7)
            await self.pubsub.publish(
                ["feedback_notifications", f"content_{feedback.content_id}"],
                data={
                    "type": "new_feedback",
                    "notification": {
                        "id": notification.notification_id,
                        "feedback_id": feedback.feedback_id,
                        "content_id": feedback.content_id,
                        "message": notification.message,
                        "data": notification.data,
                        "timestamp": notification.created_at.isoformat(),
                    },
                },
            )

        except Exception as e:
            logger.warning(f"⚠️ Failed to send feedback notification: {e}")

    async def _send_moderation_notification(
        self, feedback: FeedbackItem, action: str, reason: str
    ):
        """Отправка уведомления о модерации"""
        try:
            await self.pubsub.publish(
                ["moderation_notifications", f"user_{feedback.user_id}"],
                data={
                    "type": "feedback_moderated",
                    "feedback_id": feedback.feedback_id,
                    "action": action,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to send moderation notification: {e}")

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Проверка актуальности кэша"""
        if cache_key not in self._summary_cache:
            return False

        last_update = self._last_cache_update.get(cache_key)
        if not last_update:
            return False

        return datetime.now() - last_update < self._cache_ttl

    def _calculate_like_ratio(self, feedback_list: List[FeedbackItem]) -> float:
        """Вычисление соотношения лайков"""
        likes = len(
            [
                fb
                for fb in feedback_list
                if fb.feedback_type == FeedbackType.LIKE and fb.value
            ]
        )
        dislikes = len(
            [
                fb
                for fb in feedback_list
                if fb.feedback_type == FeedbackType.DISLIKE and fb.value
            ]
        )

        total = likes + dislikes
        return likes / total if total > 0 else 0.0

    def _calculate_avg_rating(self, feedback_list: List[FeedbackItem]) -> float:
        """Вычисление среднего рейтинга"""
        ratings = [fb.rating for fb in feedback_list if fb.rating]
        return sum(ratings) / len(ratings) if ratings else 0.0

    async def get_service_status(self) -> Dict[str, Any]:
        """Получение статуса сервиса"""
        return {
            "service_status": "active",
            "total_feedback_items": len(self.feedback_items),
            "total_content_summaries": len(self.content_summaries),
            "metrics": self.metrics,
            "configuration": self.config,
            "cache_stats": {
                "cached_summaries": len(self._summary_cache),
                "cache_hit_potential": len(self._last_cache_update),
            },
            "last_updated": datetime.now().isoformat(),
        }


# Глобальный экземпляр
_enhanced_feedback_service: Optional[EnhancedFeedbackService] = None


async def get_enhanced_feedback_service() -> EnhancedFeedbackService:
    """Получение глобального экземпляра сервиса"""
    global _enhanced_feedback_service
    if _enhanced_feedback_service is None:
        _enhanced_feedback_service = EnhancedFeedbackService()
        logger.info("✅ Enhanced Feedback Service инициализирован")
    return _enhanced_feedback_service
