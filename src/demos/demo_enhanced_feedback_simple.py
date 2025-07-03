"""
Demo Enhanced Feedback System (Simple) - Демонстрация без внешних зависимостей

Демонстрирует core функциональность Enhanced Feedback System:
- Отправку различных типов feedback
- Автоматическую модерацию
- Анализ тональности
- Аналитику и метрики
- Кэширование

Usage:
    python src/demos/demo_enhanced_feedback_simple.py
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Simplified versions of the service classes (без PubSub зависимости)

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
    value: Optional[Any] = None
    comment: str = ""
    rating: Optional[int] = None
    
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
    feedback_velocity: float = 0.0
    
    updated_at: datetime = field(default_factory=datetime.now)

class SimplifiedEnhancedFeedbackService:
    """Упрощенная версия Enhanced Feedback Service для демо"""
    
    def __init__(self):
        # Хранилища данных
        self.feedback_items: Dict[str, FeedbackItem] = {}
        self.content_summaries: Dict[str, FeedbackSummary] = {}
        self.user_feedback_history: Dict[str, List[str]] = {}
        
        # Конфигурация
        self.config = {
            'max_comment_length': 2000,
            'auto_moderation_enabled': True,
            'sentiment_analysis_enabled': True,
            'spam_detection_enabled': True
        }
        
        # Метрики
        self.metrics = {
            'total_feedback': 0,
            'total_likes': 0,
            'total_dislikes': 0,
            'total_comments': 0,
            'spam_detected': 0,
            'moderated_items': 0
        }
        
        # Кэш
        self._summary_cache: Dict[str, FeedbackSummary] = {}
        self._cache_ttl = timedelta(minutes=5)
        self._last_cache_update: Dict[str, datetime] = {}
        
        # Модерация
        self._spam_keywords = {
            'spam', 'advertisement', 'promotion', 'click here', 'free money'
        }
        self._toxic_keywords = {
            'hate', 'abuse', 'toxic', 'harassment'
        }
    
    async def submit_feedback(self, user_id: str, content_id: str, 
                             content_type: ContentType, feedback_type: FeedbackType,
                             value: Any = None, comment: str = "", 
                             rating: Optional[int] = None,
                             context: Dict[str, Any] = None) -> FeedbackItem:
        """Отправка обратной связи"""
        # Валидация
        if not self._validate_feedback_input(feedback_type, value, comment, rating):
            raise ValueError("Invalid feedback input")
        
        # Создание элемента
        feedback = FeedbackItem(
            user_id=user_id,
            content_id=content_id,
            content_type=content_type,
            feedback_type=feedback_type,
            value=value,
            comment=comment.strip(),
            rating=rating,
            context=context or {}
        )
        
        # Автоматическая модерация
        if self.config['auto_moderation_enabled']:
            await self._moderate_feedback(feedback)
        
        # Анализ тональности
        if feedback.comment and self.config['sentiment_analysis_enabled']:
            feedback.sentiment_score = await self._analyze_sentiment(feedback.comment)
        
        # Сохранение
        self.feedback_items[feedback.feedback_id] = feedback
        
        # Обновление истории пользователя
        if user_id not in self.user_feedback_history:
            self.user_feedback_history[user_id] = []
        self.user_feedback_history[user_id].append(feedback.feedback_id)
        
        # Обновление метрик
        self._update_metrics(feedback)
        
        # Очистка кэша
        self._invalidate_cache(content_id)
        
        logger.info(f"✅ Feedback submitted: {feedback.feedback_id} for content {content_id}")
        return feedback
    
    async def get_content_feedback(self, content_id: str, 
                                  include_comments: bool = True,
                                  include_moderated: bool = False) -> FeedbackSummary:
        """Получение обратной связи по контенту"""
        # Проверка кэша
        cache_key = f"{content_id}_{include_comments}_{include_moderated}"
        if self._is_cache_valid(cache_key):
            return self._summary_cache[cache_key]
        
        # Фильтрация feedback
        content_feedback = [
            fb for fb in self.feedback_items.values()
            if fb.content_id == content_id and (include_moderated or not fb.is_moderated)
        ]
        
        if not content_feedback:
            return FeedbackSummary(content_id=content_id)
        
        # Вычисление сводки
        summary = await self._calculate_content_summary(content_id, content_feedback)
        
        # Сохранение в кэш
        self._summary_cache[cache_key] = summary
        self._last_cache_update[cache_key] = datetime.now()
        
        return summary
    
    async def get_user_feedback_history(self, user_id: str, 
                                      limit: int = 50,
                                      content_type: Optional[ContentType] = None) -> List[FeedbackItem]:
        """Получение истории обратной связи пользователя"""
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
                fb for fb in user_feedback 
                if fb.content_type == content_type
            ]
        
        # Сортировка по дате
        user_feedback.sort(key=lambda x: x.created_at, reverse=True)
        
        return user_feedback[:limit]
    
    async def moderate_feedback(self, feedback_id: str, 
                               moderator_id: str,
                               action: str = "hide",
                               reason: str = "") -> bool:
        """Модерация обратной связи"""
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
        
        self.metrics['moderated_items'] += 1
        self._invalidate_cache(feedback.content_id)
        
        logger.info(f"✅ Feedback moderated: {feedback_id} by {moderator_id}")
        return True
    
    async def get_feedback_analytics(self, 
                                   time_period: timedelta = timedelta(days=7),
                                   content_type: Optional[ContentType] = None) -> Dict[str, Any]:
        """Получение аналитики обратной связи"""
        cutoff_date = datetime.now() - time_period
        
        # Фильтрация feedback
        filtered_feedback = [
            fb for fb in self.feedback_items.values()
            if fb.created_at >= cutoff_date and 
            (not content_type or fb.content_type == content_type)
        ]
        
        if not filtered_feedback:
            return {'total_feedback': 0}
        
        # Вычисление аналитики
        analytics = {
            'time_period_days': time_period.days,
            'total_feedback': len(filtered_feedback),
            'feedback_by_type': {},
            'feedback_by_content_type': {},
            'sentiment_distribution': {},
            'rating_distribution': {},
            'top_content': [],
            'engagement_metrics': {}
        }
        
        # Распределение по типам
        for fb in filtered_feedback:
            fb_type = fb.feedback_type.value
            content_type_val = fb.content_type.value
            
            analytics['feedback_by_type'][fb_type] = analytics['feedback_by_type'].get(fb_type, 0) + 1
            analytics['feedback_by_content_type'][content_type_val] = analytics['feedback_by_content_type'].get(content_type_val, 0) + 1
            
            if fb.sentiment_score:
                sentiment = fb.sentiment_score.value
                analytics['sentiment_distribution'][sentiment] = analytics['sentiment_distribution'].get(sentiment, 0) + 1
            
            if fb.rating:
                rating = str(fb.rating)
                analytics['rating_distribution'][rating] = analytics['rating_distribution'].get(rating, 0) + 1
        
        # Топ контент
        content_feedback_count = {}
        for fb in filtered_feedback:
            content_id = fb.content_id
            content_feedback_count[content_id] = content_feedback_count.get(content_id, 0) + 1
        
        analytics['top_content'] = sorted(
            content_feedback_count.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Метрики вовлечения
        analytics['engagement_metrics'] = {
            'feedback_per_day': len(filtered_feedback) / max(time_period.days, 1),
            'like_ratio': self._calculate_like_ratio(filtered_feedback),
            'comment_rate': len([fb for fb in filtered_feedback if fb.comment]) / len(filtered_feedback),
            'avg_rating': self._calculate_avg_rating(filtered_feedback)
        }
        
        return analytics
    
    def _validate_feedback_input(self, feedback_type: FeedbackType, 
                                value: Any, comment: str, rating: Optional[int]) -> bool:
        """Валидация входных данных"""
        if feedback_type in [FeedbackType.LIKE, FeedbackType.DISLIKE]:
            return value is not None and isinstance(value, bool)
        elif feedback_type == FeedbackType.COMMENT:
            return len(comment.strip()) > 0 and len(comment) <= self.config['max_comment_length']
        elif feedback_type == FeedbackType.RATING:
            return rating is not None and 1 <= rating <= 5
        return True
    
    async def _moderate_feedback(self, feedback: FeedbackItem):
        """Автоматическая модерация"""
        if not feedback.comment:
            return
        
        comment_lower = feedback.comment.lower()
        
        # Проверка на спам
        if any(keyword in comment_lower for keyword in self._spam_keywords):
            feedback.status = FeedbackStatus.MODERATED
            feedback.moderation_reason = "Spam detected"
            self.metrics['spam_detected'] += 1
            return
        
        # Проверка на токсичность
        if any(keyword in comment_lower for keyword in self._toxic_keywords):
            feedback.status = FeedbackStatus.MODERATED
            feedback.moderation_reason = "Toxic content detected"
            return
    
    async def _analyze_sentiment(self, comment: str) -> SentimentScore:
        """Анализ тональности"""
        comment_lower = comment.lower()
        
        positive_words = {'good', 'great', 'excellent', 'awesome', 'perfect', 'love', 'best'}
        negative_words = {'bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'poor'}
        
        positive_count = sum(1 for word in positive_words if word in comment_lower)
        negative_count = sum(1 for word in negative_words if word in comment_lower)
        
        if positive_count > negative_count + 1:
            return SentimentScore.POSITIVE
        elif negative_count > positive_count + 1:
            return SentimentScore.NEGATIVE
        else:
            return SentimentScore.NEUTRAL
    
    async def _calculate_content_summary(self, content_id: str, 
                                       feedback_list: List[FeedbackItem]) -> FeedbackSummary:
        """Вычисление сводки контента"""
        summary = FeedbackSummary(content_id=content_id)
        
        if not feedback_list:
            return summary
        
        # Подсчет лайков/дизлайков
        likes = [fb for fb in feedback_list if fb.feedback_type == FeedbackType.LIKE and fb.value]
        dislikes = [fb for fb in feedback_list if fb.feedback_type == FeedbackType.DISLIKE and fb.value]
        
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
        sentiments = [fb.sentiment_score.value for fb in feedback_list if fb.sentiment_score]
        summary.sentiment_distribution = {
            sentiment: sentiments.count(sentiment) 
            for sentiment in set(sentiments)
        }
        
        # Временные метрики
        if feedback_list:
            summary.last_feedback_at = max(fb.created_at for fb in feedback_list)
            
            time_span = (datetime.now() - min(fb.created_at for fb in feedback_list)).total_seconds() / 3600
            if time_span > 0:
                summary.feedback_velocity = len(feedback_list) / time_span
        
        return summary
    
    def _update_metrics(self, feedback: FeedbackItem):
        """Обновление метрик"""
        self.metrics['total_feedback'] += 1
        
        if feedback.feedback_type == FeedbackType.LIKE and feedback.value:
            self.metrics['total_likes'] += 1
        elif feedback.feedback_type == FeedbackType.DISLIKE and feedback.value:
            self.metrics['total_dislikes'] += 1
        elif feedback.feedback_type == FeedbackType.COMMENT:
            self.metrics['total_comments'] += 1
    
    def _invalidate_cache(self, content_id: str):
        """Инвалидация кэша для контента"""
        keys_to_remove = [key for key in self._summary_cache.keys() if key.startswith(content_id)]
        for key in keys_to_remove:
            self._summary_cache.pop(key, None)
            self._last_cache_update.pop(key, None)
    
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
        likes = len([fb for fb in feedback_list if fb.feedback_type == FeedbackType.LIKE and fb.value])
        dislikes = len([fb for fb in feedback_list if fb.feedback_type == FeedbackType.DISLIKE and fb.value])
        
        total = likes + dislikes
        return likes / total if total > 0 else 0.0
    
    def _calculate_avg_rating(self, feedback_list: List[FeedbackItem]) -> float:
        """Вычисление среднего рейтинга"""
        ratings = [fb.rating for fb in feedback_list if fb.rating]
        return sum(ratings) / len(ratings) if ratings else 0.0
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Получение статуса сервиса"""
        return {
            'service_status': 'active',
            'total_feedback_items': len(self.feedback_items),
            'total_content_summaries': len(self.content_summaries),
            'metrics': self.metrics,
            'configuration': self.config,
            'cache_stats': {
                'cached_summaries': len(self._summary_cache),
                'cache_hit_potential': len(self._last_cache_update)
            },
            'last_updated': datetime.now().isoformat()
        }

class EnhancedFeedbackDemo:
    """Демонстрация Enhanced Feedback System"""
    
    def __init__(self):
        self.service = SimplifiedEnhancedFeedbackService()
        self.demo_users = [f"user_{i}" for i in range(1, 11)]
        self.demo_content_ids = [f"content_{i}" for i in range(1, 6)]
        self.demo_comments = {
            'positive': [
                "This is excellent and very helpful!",
                "Great work, perfect solution!",
                "Awesome response, love it!",
                "Best answer I've seen!",
                "Outstanding quality content!"
            ],
            'negative': [
                "This is terrible and awful!",
                "Horrible response, hate it!",
                "Worst answer ever!",
                "Bad quality, very poor!",
                "Completely useless content!"
            ],
            'neutral': [
                "This is okay, nothing special.",
                "Average response, could be better.",
                "Regular content, meets expectations.",
                "Standard quality answer.",
                "Normal response, typical result."
            ],
            'spam': [
                "Free money! Click here for advertisement!",
                "Spam content! Buy our products now!",
                "Promotion! Free gifts! Visit our site!",
                "Advertisement! Best deals! Click here!"
            ],
            'toxic': [
                "I hate this toxic content!",
                "This is harassment and abuse!",
                "Toxic behavior, very bad!",
                "Harassment! This is awful!"
            ]
        }
    
    async def demo_basic_feedback_submission(self):
        """Демо 1: Базовая отправка обратной связи"""
        print("\n" + "="*60)
        print("📝 ДЕМО 1: Базовая отправка обратной связи")
        print("="*60)
        
        content_id = "demo_content_1"
        
        # Лайки и дизлайки
        print("👍 Отправляем лайки и дизлайки...")
        for i, user_id in enumerate(self.demo_users[:5]):
            feedback_type = FeedbackType.LIKE if i < 3 else FeedbackType.DISLIKE
            value = True
            
            feedback = await self.service.submit_feedback(
                user_id=user_id,
                content_id=content_id,
                content_type=ContentType.AI_RESPONSE,
                feedback_type=feedback_type,
                value=value
            )
            
            print(f"  ✓ {user_id}: {feedback_type.value} - {feedback.feedback_id}")
        
        # Рейтинги
        print("\n⭐ Отправляем рейтинги...")
        for i, user_id in enumerate(self.demo_users[5:8]):
            rating = random.randint(3, 5)
            
            feedback = await self.service.submit_feedback(
                user_id=user_id,
                content_id=content_id,
                content_type=ContentType.AI_RESPONSE,
                feedback_type=FeedbackType.RATING,
                rating=rating
            )
            
            print(f"  ✓ {user_id}: {rating} stars - {feedback.feedback_id}")
        
        # Комментарии
        print("\n💬 Отправляем комментарии...")
        for i, user_id in enumerate(self.demo_users[8:]):
            comment_type = ['positive', 'negative', 'neutral'][i % 3]
            comment = random.choice(self.demo_comments[comment_type])
            
            feedback = await self.service.submit_feedback(
                user_id=user_id,
                content_id=content_id,
                content_type=ContentType.AI_RESPONSE,
                feedback_type=FeedbackType.COMMENT,
                comment=comment
            )
            
            sentiment = feedback.sentiment_score.value if feedback.sentiment_score else "unknown"
            print(f"  ✓ {user_id}: '{comment[:30]}...' - Sentiment: {sentiment}")
        
        # Получение сводки
        print("\n📊 Получаем сводку по контенту...")
        summary = await self.service.get_content_feedback(content_id, include_comments=True)
        
        print(f"  📈 Лайки: {summary.total_likes}")
        print(f"  📉 Дизлайки: {summary.total_dislikes}")
        print(f"  💯 Соотношение лайков: {summary.like_ratio:.2%}")
        print(f"  💬 Комментарии: {summary.total_comments}")
        print(f"  ⭐ Средний рейтинг: {summary.avg_rating:.1f}")
        print(f"  🎭 Тональность: {summary.sentiment_distribution}")
    
    async def demo_moderation_system(self):
        """Демо 2: Система модерации"""
        print("\n" + "="*60)
        print("🛡️ ДЕМО 2: Система модерации")
        print("="*60)
        
        content_id = "demo_content_moderation"
        moderated_feedback_ids = []
        
        # Отправляем спам-контент
        print("🚫 Отправляем спам-контент (автоматическая модерация)...")
        for i, spam_comment in enumerate(self.demo_comments['spam'][:2]):
            feedback = await self.service.submit_feedback(
                user_id=f"spammer_{i}",
                content_id=content_id,
                content_type=ContentType.AI_RESPONSE,
                feedback_type=FeedbackType.COMMENT,
                comment=spam_comment
            )
            
            status = "МОДЕРИРОВАН" if feedback.status == FeedbackStatus.MODERATED else "АКТИВЕН"
            print(f"  🚨 Спам: '{spam_comment[:40]}...' - Статус: {status}")
            
            if feedback.status == FeedbackStatus.MODERATED:
                print(f"    Причина: {feedback.moderation_reason}")
                moderated_feedback_ids.append(feedback.feedback_id)
        
        # Отправляем токсичный контент
        print("\n☣️ Отправляем токсичный контент...")
        for i, toxic_comment in enumerate(self.demo_comments['toxic'][:2]):
            feedback = await self.service.submit_feedback(
                user_id=f"toxic_user_{i}",
                content_id=content_id,
                content_type=ContentType.AI_RESPONSE,
                feedback_type=FeedbackType.COMMENT,
                comment=toxic_comment
            )
            
            status = "МОДЕРИРОВАН" if feedback.status == FeedbackStatus.MODERATED else "АКТИВЕН"
            print(f"  ☣️ Токсичность: '{toxic_comment[:40]}...' - Статус: {status}")
            
            if feedback.status == FeedbackStatus.MODERATED:
                print(f"    Причина: {feedback.moderation_reason}")
                moderated_feedback_ids.append(feedback.feedback_id)
        
        # Отправляем нормальный контент
        print("\n✅ Отправляем нормальный контент...")
        normal_feedback = await self.service.submit_feedback(
            user_id="normal_user",
            content_id=content_id,
            content_type=ContentType.AI_RESPONSE,
            feedback_type=FeedbackType.COMMENT,
            comment="This is a regular, helpful comment."
        )
        
        print(f"  ✅ Нормальный: 'This is a regular, helpful comment.' - Статус: {normal_feedback.status.value}")
        
        # Ручная модерация
        print("\n👨‍💼 Ручная модерация контента...")
        if moderated_feedback_ids:
            feedback_id = moderated_feedback_ids[0]
            success = await self.service.moderate_feedback(
                feedback_id=feedback_id,
                moderator_id="moderator_admin",
                action="approve",
                reason="Content reviewed and approved"
            )
            
            if success:
                print(f"  ✅ Feedback {feedback_id} одобрен модератором")
        
        # Метрики модерации
        print("\n📊 Метрики модерации:")
        metrics = self.service.metrics
        print(f"  🚨 Обнаружено спама: {metrics['spam_detected']}")
        print(f"  🛡️ Модерированных элементов: {metrics['moderated_items']}")
    
    async def demo_analytics_and_performance(self):
        """Демо 3: Аналитика и производительность"""
        print("\n" + "="*60)
        print("📊 ДЕМО 3: Аналитика и производительность")
        print("="*60)
        
        # Создаем разнообразный контент
        print("📝 Создаем контент для аналитики...")
        
        content_types = [ContentType.AI_RESPONSE, ContentType.RFC_GENERATION, ContentType.CODE_DOCUMENTATION]
        
        for content_type in content_types:
            for i in range(3):
                content_id = f"analytics_{content_type.value}_{i}"
                
                # Добавляем feedback
                for j, user_id in enumerate(self.demo_users[:5]):
                    if j < 2:  # Лайки
                        await self.service.submit_feedback(
                            user_id=user_id,
                            content_id=content_id,
                            content_type=content_type,
                            feedback_type=FeedbackType.LIKE,
                            value=True
                        )
                    elif j < 3:  # Дизлайк
                        await self.service.submit_feedback(
                            user_id=user_id,
                            content_id=content_id,
                            content_type=content_type,
                            feedback_type=FeedbackType.DISLIKE,
                            value=True
                        )
                    elif j < 4:  # Рейтинг
                        await self.service.submit_feedback(
                            user_id=user_id,
                            content_id=content_id,
                            content_type=content_type,
                            feedback_type=FeedbackType.RATING,
                            rating=random.randint(3, 5)
                        )
                    else:  # Комментарий
                        comment = random.choice(self.demo_comments['positive'] + self.demo_comments['neutral'])
                        await self.service.submit_feedback(
                            user_id=user_id,
                            content_id=content_id,
                            content_type=content_type,
                            feedback_type=FeedbackType.COMMENT,
                            comment=comment
                        )
        
        # Получение аналитики
        print("\n📈 Общая аналитика:")
        analytics = await self.service.get_feedback_analytics(time_period=timedelta(days=7))
        
        print(f"  📊 Всего обратной связи: {analytics['total_feedback']}")
        print(f"  📝 Распределение по типам: {analytics['feedback_by_type']}")
        print(f"  🎯 По типам контента: {analytics['feedback_by_content_type']}")
        print(f"  🎭 Тональность: {analytics['sentiment_distribution']}")
        print(f"  ⭐ Рейтинги: {analytics['rating_distribution']}")
        
        engagement = analytics['engagement_metrics']
        print(f"\n💪 Метрики вовлечения:")
        print(f"  📈 Feedback в день: {engagement['feedback_per_day']:.1f}")
        print(f"  👍 Соотношение лайков: {engagement['like_ratio']:.1%}")
        print(f"  💬 Доля комментариев: {engagement['comment_rate']:.1%}")
        print(f"  ⭐ Средний рейтинг: {engagement['avg_rating']:.1f}")
        
        print(f"\n🏆 Топ контент:")
        for i, (content_id, count) in enumerate(analytics['top_content'][:3]):
            print(f"  {i+1}. {content_id}: {count} feedback")
        
        # Тест производительности
        print(f"\n⚡ Тест производительности кэширования:")
        test_content_id = "performance_test"
        
        # Создаем тестовые данные
        for i in range(5):
            await self.service.submit_feedback(
                user_id=f"perf_user_{i}",
                content_id=test_content_id,
                content_type=ContentType.AI_RESPONSE,
                feedback_type=FeedbackType.LIKE,
                value=True
            )
        
        # Первый запрос (создание кэша)
        start_time = time.time()
        summary1 = await self.service.get_content_feedback(test_content_id)
        first_time = time.time() - start_time
        print(f"  🔄 Первый запрос: {first_time*1000:.2f}ms")
        
        # Второй запрос (из кэша)
        start_time = time.time()
        summary2 = await self.service.get_content_feedback(test_content_id)
        cached_time = time.time() - start_time
        print(f"  ⚡ Кэшированный запрос: {cached_time*1000:.2f}ms")
        
        speedup = first_time / cached_time if cached_time > 0 else float('inf')
        print(f"  🚀 Ускорение: {speedup:.1f}x")
    
    async def demo_service_status(self):
        """Демо 4: Статус сервиса"""
        print("\n" + "="*60)
        print("🔍 ДЕМО 4: Статус сервиса")
        print("="*60)
        
        status = await self.service.get_service_status()
        
        print(f"\n🚀 Статус сервиса: {status['service_status']}")
        print(f"📦 Элементов feedback: {status['total_feedback_items']}")
        print(f"📋 Сводок контента: {status['total_content_summaries']}")
        
        print(f"\n📈 Метрики:")
        for metric, value in status['metrics'].items():
            print(f"  {metric}: {value}")
        
        print(f"\n🗄️ Статистика кэша:")
        cache_stats = status['cache_stats']
        print(f"  📦 Кэшированных сводок: {cache_stats['cached_summaries']}")
        print(f"  🎯 Потенциальных попаданий: {cache_stats['cache_hit_potential']}")
    
    async def run_all_demos(self):
        """Запуск всех демонстраций"""
        print("🚀 Enhanced Feedback System - Демонстрация")
        print("="*80)
        
        try:
            await self.demo_basic_feedback_submission()
            await self.demo_moderation_system()
            await self.demo_analytics_and_performance()
            await self.demo_service_status()
            
            print("\n" + "="*80)
            print("🎉 ВСЕ ДЕМОНСТРАЦИИ ЗАВЕРШЕНЫ УСПЕШНО!")
            print("="*80)
            
            # Финальная статистика
            final_status = await self.service.get_service_status()
            print(f"\n📊 Финальная статистика:")
            print(f"  📦 Всего элементов feedback: {final_status['total_feedback_items']}")
            print(f"  🎯 Метрики: {final_status['metrics']}")
            
        except Exception as e:
            print(f"\n❌ Ошибка во время выполнения демо: {e}")
            logger.exception("Demo execution failed")

async def main():
    """Главная функция"""
    demo = EnhancedFeedbackDemo()
    await demo.run_all_demos()

if __name__ == "__main__":
    asyncio.run(main())