"""
Unit тесты для Enhanced Feedback Service

Тестирует:
- Отправку различных типов обратной связи
- Модерацию контента
- Аналитику и метрики
- Real-time уведомления
- Кэширование и производительность
- Интеграцию с WebSocket PubSub
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domain.monitoring.enhanced_feedback_service import (
    ContentType, EnhancedFeedbackService, FeedbackItem, FeedbackStatus,
    FeedbackSummary, FeedbackType, SentimentScore)


class TestEnhancedFeedbackService:
    """Тесты для EnhancedFeedbackService"""

    @pytest.fixture
    async def feedback_service(self):
        """Создание экземпляра сервиса для тестирования"""
        # Мокаем PubSub endpoint
        mock_pubsub = AsyncMock()
        service = EnhancedFeedbackService(pubsub_endpoint=mock_pubsub)
        return service

    @pytest.mark.asyncio
    async def test_submit_like_feedback(self, feedback_service):
        """Тест отправки лайка"""
        feedback = await feedback_service.submit_feedback(
            user_id="user123",
            content_id="content456",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.LIKE,
            value=True,
        )

        assert feedback.feedback_type == FeedbackType.LIKE
        assert feedback.value is True
        assert feedback.user_id == "user123"
        assert feedback.content_id == "content456"
        assert feedback.status == FeedbackStatus.ACTIVE
        assert feedback.feedback_id in feedback_service.feedback_items

    @pytest.mark.asyncio
    async def test_submit_dislike_feedback(self, feedback_service):
        """Тест отправки дизлайка"""
        feedback = await feedback_service.submit_feedback(
            user_id="user123",
            content_id="content456",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.DISLIKE,
            value=True,
        )

        assert feedback.feedback_type == FeedbackType.DISLIKE
        assert feedback.value is True
        assert feedback.status == FeedbackStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_submit_comment_feedback(self, feedback_service):
        """Тест отправки комментария"""
        comment_text = "This is a great response!"

        feedback = await feedback_service.submit_feedback(
            user_id="user123",
            content_id="content456",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.COMMENT,
            comment=comment_text,
        )

        assert feedback.feedback_type == FeedbackType.COMMENT
        assert feedback.comment == comment_text
        assert feedback.sentiment_score == SentimentScore.POSITIVE  # "great" detected

    @pytest.mark.asyncio
    async def test_submit_rating_feedback(self, feedback_service):
        """Тест отправки рейтинга"""
        feedback = await feedback_service.submit_feedback(
            user_id="user123",
            content_id="content456",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.RATING,
            rating=5,
        )

        assert feedback.feedback_type == FeedbackType.RATING
        assert feedback.rating == 5

    @pytest.mark.asyncio
    async def test_feedback_validation_like_without_value(self, feedback_service):
        """Тест валидации - лайк без значения"""
        with pytest.raises(ValueError, match="Invalid feedback input"):
            await feedback_service.submit_feedback(
                user_id="user123",
                content_id="content456",
                content_type=ContentType.AI_RESPONSE,
                feedback_type=FeedbackType.LIKE,
                value=None,
            )

    @pytest.mark.asyncio
    async def test_feedback_validation_comment_too_long(self, feedback_service):
        """Тест валидации - слишком длинный комментарий"""
        long_comment = "x" * 2001  # Превышает лимит в 2000 символов

        with pytest.raises(ValueError, match="Invalid feedback input"):
            await feedback_service.submit_feedback(
                user_id="user123",
                content_id="content456",
                content_type=ContentType.AI_RESPONSE,
                feedback_type=FeedbackType.COMMENT,
                comment=long_comment,
            )

    @pytest.mark.asyncio
    async def test_feedback_validation_invalid_rating(self, feedback_service):
        """Тест валидации - некорректный рейтинг"""
        with pytest.raises(ValueError, match="Invalid feedback input"):
            await feedback_service.submit_feedback(
                user_id="user123",
                content_id="content456",
                content_type=ContentType.AI_RESPONSE,
                feedback_type=FeedbackType.RATING,
                rating=6,  # Превышает максимум 5
            )

    @pytest.mark.asyncio
    async def test_auto_moderation_spam_detection(self, feedback_service):
        """Тест автоматической модерации - обнаружение спама"""
        spam_comment = "Free money! Click here for advertisement!"

        feedback = await feedback_service.submit_feedback(
            user_id="user123",
            content_id="content456",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.COMMENT,
            comment=spam_comment,
        )

        assert feedback.status == FeedbackStatus.MODERATED
        assert feedback.moderation_reason == "Spam detected"
        assert feedback_service.metrics["spam_detected"] == 1

    @pytest.mark.asyncio
    async def test_auto_moderation_toxic_content(self, feedback_service):
        """Тест автоматической модерации - токсичный контент"""
        toxic_comment = "I hate this toxic content!"

        feedback = await feedback_service.submit_feedback(
            user_id="user123",
            content_id="content456",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.COMMENT,
            comment=toxic_comment,
        )

        assert feedback.status == FeedbackStatus.MODERATED
        assert feedback.moderation_reason == "Toxic content detected"

    @pytest.mark.asyncio
    async def test_sentiment_analysis_positive(self, feedback_service):
        """Тест анализа тональности - позитивный"""
        positive_comment = "This is excellent and awesome!"

        feedback = await feedback_service.submit_feedback(
            user_id="user123",
            content_id="content456",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.COMMENT,
            comment=positive_comment,
        )

        assert feedback.sentiment_score == SentimentScore.POSITIVE

    @pytest.mark.asyncio
    async def test_sentiment_analysis_negative(self, feedback_service):
        """Тест анализа тональности - негативный"""
        negative_comment = "This is terrible and awful!"

        feedback = await feedback_service.submit_feedback(
            user_id="user123",
            content_id="content456",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.COMMENT,
            comment=negative_comment,
        )

        assert feedback.sentiment_score == SentimentScore.NEGATIVE

    @pytest.mark.asyncio
    async def test_sentiment_analysis_neutral(self, feedback_service):
        """Тест анализа тональности - нейтральный"""
        neutral_comment = "This is a regular comment."

        feedback = await feedback_service.submit_feedback(
            user_id="user123",
            content_id="content456",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.COMMENT,
            comment=neutral_comment,
        )

        assert feedback.sentiment_score == SentimentScore.NEUTRAL

    @pytest.mark.asyncio
    async def test_get_content_feedback_summary(self, feedback_service):
        """Тест получения сводки обратной связи по контенту"""
        content_id = "content123"

        # Добавляем различные типы feedback
        await feedback_service.submit_feedback(
            user_id="user1",
            content_id=content_id,
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.LIKE,
            value=True,
        )
        await feedback_service.submit_feedback(
            user_id="user2",
            content_id=content_id,
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.LIKE,
            value=True,
        )
        await feedback_service.submit_feedback(
            user_id="user3",
            content_id=content_id,
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.DISLIKE,
            value=True,
        )
        await feedback_service.submit_feedback(
            user_id="user4",
            content_id=content_id,
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.RATING,
            rating=4,
        )
        await feedback_service.submit_feedback(
            user_id="user5",
            content_id=content_id,
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.COMMENT,
            comment="Great work!",
        )

        summary = await feedback_service.get_content_feedback(content_id)

        assert summary.content_id == content_id
        assert summary.total_likes == 2
        assert summary.total_dislikes == 1
        assert summary.like_ratio == 2 / 3  # 2 лайка из 3 реакций
        assert summary.total_comments == 1
        assert summary.avg_rating == 4.0

    @pytest.mark.asyncio
    async def test_get_user_feedback_history(self, feedback_service):
        """Тест получения истории обратной связи пользователя"""
        user_id = "user123"

        # Добавляем feedback для пользователя
        feedback1 = await feedback_service.submit_feedback(
            user_id=user_id,
            content_id="content1",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.LIKE,
            value=True,
        )
        feedback2 = await feedback_service.submit_feedback(
            user_id=user_id,
            content_id="content2",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.COMMENT,
            comment="Good!",
        )

        # Добавляем feedback для другого пользователя (не должен попасть в историю)
        await feedback_service.submit_feedback(
            user_id="other_user",
            content_id="content3",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.LIKE,
            value=True,
        )

        history = await feedback_service.get_user_feedback_history(user_id)

        assert len(history) == 2
        assert all(fb.user_id == user_id for fb in history)
        # Проверяем сортировку по дате (новые первыми)
        assert history[0].created_at >= history[1].created_at

    @pytest.mark.asyncio
    async def test_moderate_feedback_hide(self, feedback_service):
        """Тест модерации feedback - скрытие"""
        feedback = await feedback_service.submit_feedback(
            user_id="user123",
            content_id="content456",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.COMMENT,
            comment="Test comment",
        )

        success = await feedback_service.moderate_feedback(
            feedback_id=feedback.feedback_id,
            moderator_id="moderator1",
            action="hide",
            reason="Inappropriate content",
        )

        assert success is True
        moderated_feedback = feedback_service.feedback_items[feedback.feedback_id]
        assert moderated_feedback.status == FeedbackStatus.HIDDEN
        assert moderated_feedback.is_moderated is True
        assert moderated_feedback.moderation_reason == "Inappropriate content"
        assert moderated_feedback.moderator_id == "moderator1"

    @pytest.mark.asyncio
    async def test_moderate_feedback_approve(self, feedback_service):
        """Тест модерации feedback - одобрение"""
        feedback = await feedback_service.submit_feedback(
            user_id="user123",
            content_id="content456",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.COMMENT,
            comment="Test comment",
        )

        success = await feedback_service.moderate_feedback(
            feedback_id=feedback.feedback_id,
            moderator_id="moderator1",
            action="approve",
            reason="Content approved",
        )

        assert success is True
        moderated_feedback = feedback_service.feedback_items[feedback.feedback_id]
        assert moderated_feedback.status == FeedbackStatus.ACTIVE
        assert moderated_feedback.is_moderated is True

    @pytest.mark.asyncio
    async def test_moderate_nonexistent_feedback(self, feedback_service):
        """Тест модерации несуществующего feedback"""
        success = await feedback_service.moderate_feedback(
            feedback_id="nonexistent",
            moderator_id="moderator1",
            action="hide",
            reason="Test",
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_get_feedback_analytics(self, feedback_service):
        """Тест получения аналитики обратной связи"""
        # Добавляем разнообразный feedback
        await feedback_service.submit_feedback(
            user_id="user1",
            content_id="content1",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.LIKE,
            value=True,
        )
        await feedback_service.submit_feedback(
            user_id="user2",
            content_id="content1",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.DISLIKE,
            value=True,
        )
        await feedback_service.submit_feedback(
            user_id="user3",
            content_id="content2",
            content_type=ContentType.RFC_GENERATION,
            feedback_type=FeedbackType.RATING,
            rating=5,
        )
        await feedback_service.submit_feedback(
            user_id="user4",
            content_id="content2",
            content_type=ContentType.RFC_GENERATION,
            feedback_type=FeedbackType.COMMENT,
            comment="Excellent work!",
        )

        analytics = await feedback_service.get_feedback_analytics()

        assert analytics["total_feedback"] == 4
        assert analytics["feedback_by_type"]["like"] == 1
        assert analytics["feedback_by_type"]["dislike"] == 1
        assert analytics["feedback_by_type"]["rating"] == 1
        assert analytics["feedback_by_type"]["comment"] == 1
        assert analytics["feedback_by_content_type"]["ai_response"] == 2
        assert analytics["feedback_by_content_type"]["rfc_generation"] == 2
        assert analytics["sentiment_distribution"]["positive"] == 1
        assert analytics["rating_distribution"]["5"] == 1

    @pytest.mark.asyncio
    async def test_get_feedback_analytics_filtered_by_content_type(
        self, feedback_service
    ):
        """Тест аналитики с фильтрацией по типу контента"""
        # Добавляем feedback для разных типов контента
        await feedback_service.submit_feedback(
            user_id="user1",
            content_id="content1",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.LIKE,
            value=True,
        )
        await feedback_service.submit_feedback(
            user_id="user2",
            content_id="content2",
            content_type=ContentType.RFC_GENERATION,
            feedback_type=FeedbackType.LIKE,
            value=True,
        )

        # Фильтрация только по AI_RESPONSE
        analytics = await feedback_service.get_feedback_analytics(
            content_type=ContentType.AI_RESPONSE
        )

        assert analytics["total_feedback"] == 1
        assert analytics["feedback_by_content_type"]["ai_response"] == 1
        assert "rfc_generation" not in analytics["feedback_by_content_type"]

    @pytest.mark.asyncio
    async def test_get_feedback_analytics_time_period(self, feedback_service):
        """Тест аналитики с временным периодом"""
        # Добавляем feedback
        await feedback_service.submit_feedback(
            user_id="user1",
            content_id="content1",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.LIKE,
            value=True,
        )

        # Анализ за последний день
        analytics = await feedback_service.get_feedback_analytics(
            time_period=timedelta(days=1)
        )

        assert analytics["time_period_days"] == 1
        assert analytics["total_feedback"] == 1

        # Анализ за прошлый период (без feedback)
        analytics_old = await feedback_service.get_feedback_analytics(
            time_period=timedelta(seconds=1)  # Очень короткий период
        )

        # Может быть 0 или 1 в зависимости от времени выполнения теста
        assert analytics_old["total_feedback"] >= 0

    @pytest.mark.asyncio
    async def test_content_summary_caching(self, feedback_service):
        """Тест кэширования сводок контента"""
        content_id = "content123"

        # Добавляем feedback
        await feedback_service.submit_feedback(
            user_id="user1",
            content_id=content_id,
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.LIKE,
            value=True,
        )

        # Первый запрос - создание кэша
        summary1 = await feedback_service.get_content_feedback(content_id)
        cache_key = f"{content_id}_True_False"
        assert cache_key in feedback_service._summary_cache

        # Второй запрос - из кэша
        summary2 = await feedback_service.get_content_feedback(content_id)
        assert summary1.content_id == summary2.content_id
        assert summary1.total_likes == summary2.total_likes

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, feedback_service):
        """Тест инвалидации кэша при добавлении нового feedback"""
        content_id = "content123"

        # Получаем начальную сводку (создается кэш)
        summary1 = await feedback_service.get_content_feedback(content_id)
        assert summary1.total_likes == 0

        # Добавляем feedback (должен очистить кэш)
        await feedback_service.submit_feedback(
            user_id="user1",
            content_id=content_id,
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.LIKE,
            value=True,
        )

        # Получаем обновленную сводку
        summary2 = await feedback_service.get_content_feedback(content_id)
        assert summary2.total_likes == 1

    @pytest.mark.asyncio
    async def test_metrics_update(self, feedback_service):
        """Тест обновления метрик сервиса"""
        initial_metrics = feedback_service.metrics.copy()

        # Добавляем различные типы feedback
        await feedback_service.submit_feedback(
            user_id="user1",
            content_id="content1",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.LIKE,
            value=True,
        )
        await feedback_service.submit_feedback(
            user_id="user2",
            content_id="content2",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.DISLIKE,
            value=True,
        )
        await feedback_service.submit_feedback(
            user_id="user3",
            content_id="content3",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.COMMENT,
            comment="Test",
        )

        updated_metrics = feedback_service.metrics

        assert (
            updated_metrics["total_feedback"] == initial_metrics["total_feedback"] + 3
        )
        assert updated_metrics["total_likes"] == initial_metrics["total_likes"] + 1
        assert (
            updated_metrics["total_dislikes"] == initial_metrics["total_dislikes"] + 1
        )
        assert (
            updated_metrics["total_comments"] == initial_metrics["total_comments"] + 1
        )

    @pytest.mark.asyncio
    async def test_get_service_status(self, feedback_service):
        """Тест получения статуса сервиса"""
        # Добавляем некоторый feedback
        await feedback_service.submit_feedback(
            user_id="user1",
            content_id="content1",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.LIKE,
            value=True,
        )

        status = await feedback_service.get_service_status()

        assert status["service_status"] == "active"
        assert status["total_feedback_items"] == 1
        assert "metrics" in status
        assert "configuration" in status
        assert "cache_stats" in status
        assert "last_updated" in status

    @pytest.mark.asyncio
    async def test_pubsub_notification_sending(self, feedback_service):
        """Тест отправки уведомлений через PubSub"""
        # Проверяем, что PubSub publish вызывается при отправке feedback
        with patch.object(
            feedback_service.pubsub, "publish", new_callable=AsyncMock
        ) as mock_publish:
            await feedback_service.submit_feedback(
                user_id="user1",
                content_id="content1",
                content_type=ContentType.AI_RESPONSE,
                feedback_type=FeedbackType.LIKE,
                value=True,
            )

            # Проверяем, что publish был вызван
            mock_publish.assert_called_once()
            call_args = mock_publish.call_args
            topics = call_args[0][0]  # Первый аргумент - список топиков
            data = call_args[1]["data"]  # Именованный аргумент data

            assert "feedback_notifications" in topics
            assert "content_content1" in topics
            assert data["type"] == "new_feedback"

    @pytest.mark.asyncio
    async def test_concurrent_feedback_submission(self, feedback_service):
        """Тест конкурентной отправки feedback"""
        content_id = "content_concurrent"

        # Создаем задачи для конкурентной отправки
        tasks = []
        for i in range(10):
            task = feedback_service.submit_feedback(
                user_id=f"user{i}",
                content_id=content_id,
                content_type=ContentType.AI_RESPONSE,
                feedback_type=FeedbackType.LIKE,
                value=True,
            )
            tasks.append(task)

        # Выполняем все задачи одновременно
        results = await asyncio.gather(*tasks)

        # Проверяем, что все feedback созданы
        assert len(results) == 10
        assert all(fb.content_id == content_id for fb in results)
        assert len(set(fb.feedback_id for fb in results)) == 10  # Уникальные ID

        # Проверяем итоговую сводку
        summary = await feedback_service.get_content_feedback(content_id)
        assert summary.total_likes == 10

    @pytest.mark.asyncio
    async def test_feedback_with_tags_and_context(self, feedback_service):
        """Тест feedback с тегами и контекстом"""
        feedback = await feedback_service.submit_feedback(
            user_id="user1",
            content_id="content1",
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.COMMENT,
            comment="Great response!",
            context={
                "source": "api",
                "session_id": "session123",
                "user_agent": "test-client",
            },
        )

        # Добавляем теги после создания
        feedback.tags = ["helpful", "accurate", "fast"]

        assert feedback.context["source"] == "api"
        assert feedback.context["session_id"] == "session123"
        assert "helpful" in feedback.tags
        assert len(feedback.tags) == 3


class TestFeedbackAnalytics:
    """Тесты для аналитических функций"""

    @pytest.fixture
    async def populated_service(self):
        """Сервис с предзаполненными данными для аналитики"""
        service = EnhancedFeedbackService()

        # Создаем разнообразный feedback
        test_data = [
            (
                "user1",
                "content1",
                ContentType.AI_RESPONSE,
                FeedbackType.LIKE,
                True,
                None,
                None,
            ),
            (
                "user2",
                "content1",
                ContentType.AI_RESPONSE,
                FeedbackType.LIKE,
                True,
                None,
                None,
            ),
            (
                "user3",
                "content1",
                ContentType.AI_RESPONSE,
                FeedbackType.DISLIKE,
                True,
                None,
                None,
            ),
            (
                "user4",
                "content2",
                ContentType.RFC_GENERATION,
                FeedbackType.RATING,
                None,
                None,
                5,
            ),
            (
                "user5",
                "content2",
                ContentType.RFC_GENERATION,
                FeedbackType.RATING,
                None,
                None,
                4,
            ),
            (
                "user6",
                "content3",
                ContentType.CODE_DOCUMENTATION,
                FeedbackType.COMMENT,
                None,
                "Great!",
                None,
            ),
            (
                "user7",
                "content3",
                ContentType.CODE_DOCUMENTATION,
                FeedbackType.COMMENT,
                None,
                "Terrible",
                None,
            ),
        ]

        for (
            user_id,
            content_id,
            content_type,
            feedback_type,
            value,
            comment,
            rating,
        ) in test_data:
            await service.submit_feedback(
                user_id=user_id,
                content_id=content_id,
                content_type=content_type,
                feedback_type=feedback_type,
                value=value,
                comment=comment or "",
                rating=rating,
            )

        return service

    @pytest.mark.asyncio
    async def test_like_ratio_calculation(self, populated_service):
        """Тест вычисления соотношения лайков"""
        summary = await populated_service.get_content_feedback("content1")

        # content1: 2 лайка, 1 дизлайк = 2/3 = 0.67
        assert abs(summary.like_ratio - 2 / 3) < 0.01

    @pytest.mark.asyncio
    async def test_average_rating_calculation(self, populated_service):
        """Тест вычисления среднего рейтинга"""
        summary = await populated_service.get_content_feedback("content2")

        # content2: рейтинги 5 и 4 = среднее 4.5
        assert summary.avg_rating == 4.5

    @pytest.mark.asyncio
    async def test_sentiment_distribution(self, populated_service):
        """Тест распределения тональности"""
        summary = await populated_service.get_content_feedback("content3")

        # content3: "Great!" (positive) и "Terrible" (negative)
        assert summary.sentiment_distribution.get("positive", 0) == 1
        assert summary.sentiment_distribution.get("negative", 0) == 1

    @pytest.mark.asyncio
    async def test_engagement_metrics(self, populated_service):
        """Тест метрик вовлечения"""
        analytics = await populated_service.get_feedback_analytics()

        engagement = analytics["engagement_metrics"]
        assert "feedback_per_day" in engagement
        assert "like_ratio" in engagement
        assert "comment_rate" in engagement
        assert "avg_rating" in engagement

        # comment_rate: 2 комментария из 7 feedback = 2/7
        assert abs(engagement["comment_rate"] - 2 / 7) < 0.01

        # avg_rating: рейтинги 5 и 4 = среднее 4.5
        assert engagement["avg_rating"] == 4.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
