"""
Demo Enhanced Feedback System - Демонстрация расширенной системы обратной связи

Демонстрирует:
- Отправку различных типов feedback (лайки, комментарии, рейтинги)
- Автоматическую модерацию контента
- Анализ тональности комментариев  
- Real-time уведомления через WebSocket
- Аналитику и метрики
- Кэширование и производительность
- Интеграцию с PubSub

Usage:
    python src/demos/demo_enhanced_feedback.py
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

from domain.monitoring.enhanced_feedback_service import (
    EnhancedFeedbackService, get_enhanced_feedback_service,
    FeedbackType, ContentType, FeedbackStatus, SentimentScore
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedFeedbackDemo:
    """Демонстрация Enhanced Feedback System"""
    
    def __init__(self):
        self.service: EnhancedFeedbackService = None
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
    
    async def initialize(self):
        """Инициализация сервиса"""
        try:
            print("🔧 Initializing Enhanced Feedback Service...")
            self.service = await get_enhanced_feedback_service()
            print("✅ Enhanced Feedback Service initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize service: {e}")
            return False
    
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
            # Одобряем один из заблокированных
            feedback_id = moderated_feedback_ids[0]
            success = await self.service.moderate_feedback(
                feedback_id=feedback_id,
                moderator_id="moderator_admin",
                action="approve",
                reason="Content reviewed and approved"
            )
            
            if success:
                print(f"  ✅ Feedback {feedback_id} одобрен модератором")
            
            # Окончательно удаляем другой
            if len(moderated_feedback_ids) > 1:
                feedback_id = moderated_feedback_ids[1]
                success = await self.service.moderate_feedback(
                    feedback_id=feedback_id,
                    moderator_id="moderator_admin",
                    action="remove",
                    reason="Spam content permanently removed"
                )
                
                if success:
                    print(f"  🗑️ Feedback {feedback_id} удален модератором")
        
        # Метрики модерации
        print("\n📊 Метрики модерации:")
        metrics = self.service.metrics
        print(f"  🚨 Обнаружено спама: {metrics['spam_detected']}")
        print(f"  🛡️ Модерированных элементов: {metrics['moderated_items']}")
    
    async def demo_sentiment_analysis(self):
        """Демо 3: Анализ тональности"""
        print("\n" + "="*60)
        print("🎭 ДЕМО 3: Анализ тональности")
        print("="*60)
        
        content_id = "demo_content_sentiment"
        sentiment_results = []
        
        # Анализируем различные типы комментариев
        all_comments = (
            [(comment, 'positive') for comment in self.demo_comments['positive']] +
            [(comment, 'negative') for comment in self.demo_comments['negative']] +
            [(comment, 'neutral') for comment in self.demo_comments['neutral']]
        )
        
        print("🔍 Анализируем тональность комментариев...")
        for i, (comment, expected_sentiment) in enumerate(all_comments):
            feedback = await self.service.submit_feedback(
                user_id=f"sentiment_user_{i}",
                content_id=content_id,
                content_type=ContentType.AI_RESPONSE,
                feedback_type=FeedbackType.COMMENT,
                comment=comment
            )
            
            detected_sentiment = feedback.sentiment_score.value if feedback.sentiment_score else "unknown"
            sentiment_results.append((expected_sentiment, detected_sentiment))
            
            # Индикатор правильности определения
            correct = "✅" if expected_sentiment == detected_sentiment else "❌"
            
            print(f"  {correct} '{comment[:50]}...'")
            print(f"     Ожидалось: {expected_sentiment} | Определено: {detected_sentiment}")
        
        # Статистика точности
        correct_predictions = sum(1 for expected, detected in sentiment_results if expected == detected)
        total_predictions = len(sentiment_results)
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        print(f"\n📈 Точность анализа тональности: {accuracy:.1%} ({correct_predictions}/{total_predictions})")
        
        # Получение сводки с распределением тональности
        summary = await self.service.get_content_feedback(content_id)
        print(f"\n🎭 Распределение тональности в контенте:")
        for sentiment, count in summary.sentiment_distribution.items():
            print(f"  {sentiment}: {count} комментариев")
    
    async def demo_analytics_and_metrics(self):
        """Демо 4: Аналитика и метрики"""
        print("\n" + "="*60)
        print("📊 ДЕМО 4: Аналитика и метрики")
        print("="*60)
        
        # Создаем разнообразный контент для аналитики
        print("📝 Создаем разнообразный контент для аналитики...")
        
        content_types = [ContentType.AI_RESPONSE, ContentType.RFC_GENERATION, ContentType.CODE_DOCUMENTATION]
        feedback_types = [FeedbackType.LIKE, FeedbackType.DISLIKE, FeedbackType.RATING, FeedbackType.COMMENT]
        
        for content_type in content_types:
            for i in range(5):  # 5 элементов каждого типа контента
                content_id = f"analytics_{content_type.value}_{i}"
                
                # Добавляем различные типы feedback
                for j, user_id in enumerate(self.demo_users[:7]):
                    if j < 3:  # Лайки
                        await self.service.submit_feedback(
                            user_id=user_id,
                            content_id=content_id,
                            content_type=content_type,
                            feedback_type=FeedbackType.LIKE,
                            value=True
                        )
                    elif j < 4:  # Дизлайк
                        await self.service.submit_feedback(
                            user_id=user_id,
                            content_id=content_id,
                            content_type=content_type,
                            feedback_type=FeedbackType.DISLIKE,
                            value=True
                        )
                    elif j < 6:  # Рейтинги
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
        
        # Получение общей аналитики
        print("\n📈 Общая аналитика за последнюю неделю:")
        analytics = await self.service.get_feedback_analytics(time_period=timedelta(days=7))
        
        print(f"  📊 Всего обратной связи: {analytics['total_feedback']}")
        print(f"  📅 Период анализа: {analytics['time_period_days']} дней")
        
        print(f"\n📝 Распределение по типам feedback:")
        for feedback_type, count in analytics['feedback_by_type'].items():
            print(f"  {feedback_type}: {count}")
        
        print(f"\n🎯 Распределение по типам контента:")
        for content_type, count in analytics['feedback_by_content_type'].items():
            print(f"  {content_type}: {count}")
        
        print(f"\n🎭 Распределение тональности:")
        for sentiment, count in analytics['sentiment_distribution'].items():
            print(f"  {sentiment}: {count}")
        
        print(f"\n⭐ Распределение рейтингов:")
        for rating, count in analytics['rating_distribution'].items():
            print(f"  {rating} звезд: {count}")
        
        print(f"\n💪 Метрики вовлечения:")
        engagement = analytics['engagement_metrics']
        print(f"  📈 Feedback в день: {engagement['feedback_per_day']:.1f}")
        print(f"  👍 Соотношение лайков: {engagement['like_ratio']:.1%}")
        print(f"  💬 Доля комментариев: {engagement['comment_rate']:.1%}")
        print(f"  ⭐ Средний рейтинг: {engagement['avg_rating']:.1f}")
        
        print(f"\n🏆 Топ контент по количеству feedback:")
        for i, (content_id, feedback_count) in enumerate(analytics['top_content'][:5]):
            print(f"  {i+1}. {content_id}: {feedback_count} feedback")
        
        # Аналитика по конкретному типу контента
        print(f"\n🎯 Аналитика только для AI Response:")
        ai_analytics = await self.service.get_feedback_analytics(
            time_period=timedelta(days=7),
            content_type=ContentType.AI_RESPONSE
        )
        print(f"  📊 AI Response feedback: {ai_analytics['total_feedback']}")
        print(f"  💪 AI Response engagement: {ai_analytics['engagement_metrics']}")
    
    async def demo_user_feedback_history(self):
        """Демо 5: История обратной связи пользователя"""
        print("\n" + "="*60)
        print("👤 ДЕМО 5: История обратной связи пользователя")
        print("="*60)
        
        target_user = "demo_history_user"
        
        # Создаем историю feedback для пользователя
        print(f"📝 Создаем историю feedback для пользователя {target_user}...")
        
        history_data = [
            (ContentType.AI_RESPONSE, FeedbackType.LIKE, True, None, None),
            (ContentType.RFC_GENERATION, FeedbackType.RATING, None, None, 5),
            (ContentType.CODE_DOCUMENTATION, FeedbackType.COMMENT, None, "Great documentation!", None),
            (ContentType.AI_RESPONSE, FeedbackType.DISLIKE, True, None, None),
            (ContentType.DEEP_RESEARCH, FeedbackType.RATING, None, None, 4),
            (ContentType.AI_RESPONSE, FeedbackType.COMMENT, None, "Very helpful response!", None),
        ]
        
        created_feedback = []
        for i, (content_type, feedback_type, value, comment, rating) in enumerate(history_data):
            feedback = await self.service.submit_feedback(
                user_id=target_user,
                content_id=f"history_content_{i}",
                content_type=content_type,
                feedback_type=feedback_type,
                value=value,
                comment=comment or "",
                rating=rating
            )
            created_feedback.append(feedback)
            
            # Небольшая задержка для различия времени создания
            await asyncio.sleep(0.1)
        
        # Получение полной истории
        print(f"\n📚 Полная история feedback пользователя {target_user}:")
        full_history = await self.service.get_user_feedback_history(target_user, limit=20)
        
        for i, feedback in enumerate(full_history):
            print(f"  {i+1}. {feedback.content_type.value} - {feedback.feedback_type.value}")
            print(f"     Создано: {feedback.created_at.strftime('%H:%M:%S')}")
            if feedback.comment:
                print(f"     Комментарий: '{feedback.comment}'")
            if feedback.rating:
                print(f"     Рейтинг: {feedback.rating} звезд")
            print()
        
        # История по типу контента
        print(f"\n🎯 История только для AI Response:")
        ai_history = await self.service.get_user_feedback_history(
            target_user, 
            limit=10, 
            content_type=ContentType.AI_RESPONSE
        )
        
        for feedback in ai_history:
            print(f"  • {feedback.feedback_type.value} на {feedback.content_id}")
        
        print(f"\n📊 Статистика пользователя:")
        print(f"  📈 Всего feedback: {len(full_history)}")
        print(f"  🎯 AI Response feedback: {len(ai_history)}")
        
        # Распределение по типам
        type_distribution = {}
        for feedback in full_history:
            ftype = feedback.feedback_type.value
            type_distribution[ftype] = type_distribution.get(ftype, 0) + 1
        
        print(f"  📊 Распределение по типам:")
        for ftype, count in type_distribution.items():
            print(f"    {ftype}: {count}")
    
    async def demo_performance_and_caching(self):
        """Демо 6: Производительность и кэширование"""
        print("\n" + "="*60)
        print("⚡ ДЕМО 6: Производительность и кэширование")
        print("="*60)
        
        content_id = "performance_test_content"
        
        # Создаем базовый контент
        print("📝 Создаем базовый контент для тестирования...")
        for i in range(10):
            await self.service.submit_feedback(
                user_id=f"perf_user_{i}",
                content_id=content_id,
                content_type=ContentType.AI_RESPONSE,
                feedback_type=FeedbackType.LIKE,
                value=True
            )
        
        # Тест производительности получения сводки
        print("\n⏱️ Тест производительности получения сводки (с кэшированием):")
        
        # Первый запрос (создание кэша)
        start_time = time.time()
        summary1 = await self.service.get_content_feedback(content_id)
        first_request_time = time.time() - start_time
        print(f"  🔄 Первый запрос (создание кэша): {first_request_time*1000:.2f}ms")
        
        # Второй запрос (из кэша)
        start_time = time.time()
        summary2 = await self.service.get_content_feedback(content_id)
        cached_request_time = time.time() - start_time
        print(f"  ⚡ Второй запрос (из кэша): {cached_request_time*1000:.2f}ms")
        
        speedup = first_request_time / cached_request_time if cached_request_time > 0 else float('inf')
        print(f"  🚀 Ускорение: {speedup:.1f}x")
        
        # Тест конкурентной отправки feedback
        print("\n🏃‍♂️ Тест конкурентной отправки feedback:")
        concurrent_content_id = "concurrent_test_content"
        
        start_time = time.time()
        
        # Создаем задачи для конкурентной отправки
        tasks = []
        for i in range(20):
            task = self.service.submit_feedback(
                user_id=f"concurrent_user_{i}",
                content_id=concurrent_content_id,
                content_type=ContentType.AI_RESPONSE,
                feedback_type=FeedbackType.LIKE,
                value=True
            )
            tasks.append(task)
        
        # Выполняем все задачи одновременно
        results = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time
        
        print(f"  ⚡ 20 конкурентных запросов за: {concurrent_time*1000:.2f}ms")
        print(f"  📊 Среднее время на запрос: {concurrent_time*1000/20:.2f}ms")
        print(f"  ✅ Все запросы выполнены успешно: {len(results) == 20}")
        
        # Проверяем итоговую сводку
        final_summary = await self.service.get_content_feedback(concurrent_content_id)
        print(f"  📈 Итоговое количество лайков: {final_summary.total_likes}")
        
        # Статистика кэша
        print("\n🗄️ Статистика кэша:")
        status = await self.service.get_service_status()
        cache_stats = status['cache_stats']
        print(f"  📦 Кэшированных сводок: {cache_stats['cached_summaries']}")
        print(f"  🎯 Потенциальных попаданий в кэш: {cache_stats['cache_hit_potential']}")
    
    async def demo_service_status_and_metrics(self):
        """Демо 7: Статус сервиса и метрики"""
        print("\n" + "="*60)
        print("🔍 ДЕМО 7: Статус сервиса и метрики")
        print("="*60)
        
        # Получение полного статуса сервиса
        print("📊 Получаем полный статус Enhanced Feedback Service...")
        status = await self.service.get_service_status()
        
        print(f"\n🚀 Статус сервиса: {status['service_status']}")
        print(f"📦 Элементов feedback: {status['total_feedback_items']}")
        print(f"📋 Сводок контента: {status['total_content_summaries']}")
        print(f"🕐 Последнее обновление: {status['last_updated']}")
        
        print(f"\n📈 Метрики производительности:")
        metrics = status['metrics']
        for metric_name, metric_value in metrics.items():
            print(f"  {metric_name}: {metric_value}")
        
        print(f"\n⚙️ Конфигурация сервиса:")
        config = status['configuration']
        for config_key, config_value in config.items():
            print(f"  {config_key}: {config_value}")
        
        print(f"\n🗄️ Статистика кэша:")
        cache_stats = status['cache_stats']
        for cache_key, cache_value in cache_stats.items():
            print(f"  {cache_key}: {cache_value}")
    
    async def run_all_demos(self):
        """Запуск всех демонстраций"""
        print("🚀 Enhanced Feedback System - Полная демонстрация")
        print("="*80)
        
        if not await self.initialize():
            return
        
        try:
            # Запускаем все демо
            await self.demo_basic_feedback_submission()
            await self.demo_moderation_system()
            await self.demo_sentiment_analysis()
            await self.demo_analytics_and_metrics()
            await self.demo_user_feedback_history()
            await self.demo_performance_and_caching()
            await self.demo_service_status_and_metrics()
            
            print("\n" + "="*80)
            print("🎉 ВСЕ ДЕМОНСТРАЦИИ ЗАВЕРШЕНЫ УСПЕШНО!")
            print("="*80)
            
            # Финальная статистика
            final_status = await self.service.get_service_status()
            print(f"\n📊 Финальная статистика:")
            print(f"  📦 Всего элементов feedback: {final_status['total_feedback_items']}")
            print(f"  📋 Сводок контента: {final_status['total_content_summaries']}")
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