"""
Deep Research Engine Demo - Демонстрация многошагового исследования

Демонстрирует возможности DeepResearch Engine:
- Создание и выполнение исследований
- Real-time отслеживание прогресса
- Анализ результатов каждого шага
- WebSocket подключения
"""

import asyncio
import json
import logging
import time
import websockets
from datetime import datetime
from typing import Dict, Any

from domain.core.deep_research_engine import get_deep_research_engine, ResearchStatus

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeepResearchDemo:
    """Демо-класс для тестирования DeepResearch Engine"""
    
    def __init__(self):
        self.engine = None
        self.demo_queries = [
            "Какие лучшие практики для разработки микросервисов?",
            "Как организовать CI/CD pipeline для Python проектов?",
            "Какие методы машинного обучения подходят для анализа текстов?",
            "Как обеспечить безопасность веб-приложений?",
            "Что такое DevOps и как его внедрить в компании?"
        ]

    async def initialize(self):
        """Инициализация движка исследований"""
        try:
            self.engine = await get_deep_research_engine()
            logger.info("🔬 Deep Research Engine инициализирован")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            return False

    async def demo_basic_research(self):
        """Демонстрация базового исследования"""
        print("\n" + "="*80)
        print("🔬 DEEP RESEARCH ENGINE DEMO - БАЗОВОЕ ИССЛЕДОВАНИЕ")
        print("="*80)
        
        query = self.demo_queries[0]
        print(f"📝 Запрос: {query}")
        
        try:
            # Создание сессии исследования
            session = await self.engine.start_research(
                query=query,
                user_id="demo_user",
                max_steps=5
            )
            
            print(f"✅ Сессия создана: {session.session_id}")
            print(f"🎯 Цель исследования: {session.research_goal}")
            print(f"📊 Максимум шагов: {session.max_steps}")
            
            # Выполнение исследования
            print("\n🔍 ВЫПОЛНЕНИЕ ИССЛЕДОВАНИЯ:")
            print("-" * 60)
            
            step_count = 0
            async for step in self.engine.execute_research(session.session_id):
                step_count += 1
                print(f"\n📋 Шаг {step_count}: {step.title}")
                print(f"   Тип: {step.step_type.value}")
                print(f"   Статус: {step.status.value}")
                print(f"   Уверенность: {step.confidence:.2f}")
                print(f"   Время выполнения: {step.duration:.2f}с")
                print(f"   Источников найдено: {len(step.sources)}")
                
                if step.result:
                    print(f"   Результат: {step.result[:200]}...")
                
                if step.next_steps:
                    print(f"   Следующие шаги: {', '.join(step.next_steps[:2])}")
                
                time.sleep(0.5)  # Пауза для наглядности
            
            # Получение финального результата
            final_status = await self.engine.get_session_status(session.session_id)
            if final_status:
                print("\n✅ ИССЛЕДОВАНИЕ ЗАВЕРШЕНО!")
                print(f"📊 Общая уверенность: {final_status.get('overall_confidence', 0):.2f}")
                print(f"📚 Всего источников: {final_status.get('total_sources', 0)}")
                print(f"⏱️ Общее время: {final_status.get('duration', 0):.2f}с")
                
                if final_status.get('final_result'):
                    print(f"\n📝 Финальный результат:")
                    print(f"{final_status['final_result'][:500]}...")
            
            return session.session_id
            
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения исследования: {e}")
            return None

    async def demo_multiple_research(self):
        """Демонстрация множественных исследований"""
        print("\n" + "="*80)
        print("🔬 МНОЖЕСТВЕННЫЕ ИССЛЕДОВАНИЯ")
        print("="*80)
        
        sessions = []
        
        # Запускаем несколько исследований
        for i, query in enumerate(self.demo_queries[:3], 1):
            print(f"\n🚀 Запуск исследования {i}: {query[:50]}...")
            
            try:
                session = await self.engine.start_research(
                    query=query,
                    user_id=f"demo_user_{i}",
                    max_steps=3  # Меньше шагов для быстроты
                )
                sessions.append(session)
                print(f"✅ Сессия {i} создана: {session.session_id}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка создания сессии {i}: {e}")
        
        # Проверяем статусы
        print(f"\n📊 Создано сессий: {len(sessions)}")
        
        for i, session in enumerate(sessions, 1):
            status = await self.engine.get_session_status(session.session_id)
            if status:
                print(f"   Сессия {i}: {status['status']} (шагов: {status['total_steps']})")
        
        return sessions

    async def demo_research_cancellation(self):
        """Демонстрация отмены исследования"""
        print("\n" + "="*80)
        print("🚫 ОТМЕНА ИССЛЕДОВАНИЯ")
        print("="*80)
        
        query = "Тестовый запрос для отмены"
        
        try:
            # Создаем исследование
            session = await self.engine.start_research(
                query=query,
                user_id="demo_cancel_user",
                max_steps=7
            )
            
            print(f"✅ Создана сессия для отмены: {session.session_id}")
            
            # Имитируем немедленную отмену
            success = await self.engine.cancel_research(session.session_id)
            
            if success:
                print("✅ Исследование успешно отменено")
                
                # Проверяем статус
                status = await self.engine.get_session_status(session.session_id)
                if status:
                    print(f"📊 Статус после отмены: {status['status']}")
            else:
                print("❌ Не удалось отменить исследование")
                
        except Exception as e:
            logger.error(f"❌ Ошибка демонстрации отмены: {e}")

    async def demo_engine_status(self):
        """Демонстрация получения статуса движка"""
        print("\n" + "="*80)
        print("📊 СТАТУС ДВИЖКА ИССЛЕДОВАНИЙ")
        print("="*80)
        
        try:
            status = await self.engine.get_engine_status()
            
            print(f"🔧 Статус движка: {status['engine_status']}")
            print(f"🔄 Активных сессий: {status['active_sessions']}")
            
            print(f"\n📈 МЕТРИКИ:")
            metrics = status.get('metrics', {})
            for key, value in metrics.items():
                print(f"   {key}: {value}")
            
            print(f"\n⚙️ КОНФИГУРАЦИЯ:")
            config = status.get('configuration', {})
            for key, value in config.items():
                print(f"   {key}: {value}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса: {e}")

    async def demo_adaptive_planning(self):
        """Демонстрация адаптивного планирования"""
        print("\n" + "="*80)
        print("🧠 АДАПТИВНОЕ ПЛАНИРОВАНИЕ ШАГОВ")
        print("="*80)
        
        # Сложный запрос для демонстрации адаптивности
        complex_query = """
        Мне нужно создать систему автоматического тестирования для веб-приложения.
        Приложение написано на Python с использованием FastAPI и React фронтендом.
        Какие инструменты и подходы лучше использовать для unit, integration и e2e тестов?
        """
        
        try:
            session = await self.engine.start_research(
                query=complex_query,
                user_id="demo_adaptive_user",
                max_steps=6
            )
            
            print(f"✅ Создана сессия: {session.session_id}")
            print(f"🎯 Цель: {session.research_goal}")
            
            print("\n🔍 АДАПТИВНОЕ ВЫПОЛНЕНИЕ:")
            print("-" * 60)
            
            async for step in self.engine.execute_research(session.session_id):
                print(f"\n📋 {step.title}")
                print(f"   Уверенность: {step.confidence:.2f}")
                
                # Показываем адаптивные предложения
                if step.next_steps:
                    print(f"   Адаптивные предложения:")
                    for suggestion in step.next_steps[:2]:
                        print(f"     • {suggestion}")
                
                if step.confidence < 0.6:
                    print(f"   ⚠️ Низкая уверенность - может потребоваться дополнительная валидация")
                
                time.sleep(0.3)
            
            print("\n✅ Адаптивное исследование завершено!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка адаптивного планирования: {e}")

    async def demo_performance_metrics(self):
        """Демонстрация метрик производительности"""
        print("\n" + "="*80)
        print("⚡ МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ")
        print("="*80)
        
        start_time = time.time()
        session_times = []
        
        # Запускаем 3 быстрых исследования для замера времени
        for i in range(3):
            query = f"Тест производительности {i+1}: быстрый анализ веб-технологий"
            
            session_start = time.time()
            
            try:
                session = await self.engine.start_research(
                    query=query,
                    user_id=f"perf_user_{i}",
                    max_steps=3
                )
                
                # Выполняем исследование
                step_count = 0
                async for step in self.engine.execute_research(session.session_id):
                    step_count += 1
                
                session_end = time.time()
                session_time = session_end - session_start
                session_times.append(session_time)
                
                print(f"✅ Исследование {i+1}: {step_count} шагов за {session_time:.2f}с")
                
            except Exception as e:
                logger.error(f"❌ Ошибка в тесте производительности {i+1}: {e}")
        
        total_time = time.time() - start_time
        
        print(f"\n📊 РЕЗУЛЬТАТЫ ПРОИЗВОДИТЕЛЬНОСТИ:")
        print(f"   Общее время: {total_time:.2f}с")
        print(f"   Среднее время на исследование: {sum(session_times)/len(session_times):.2f}с")
        print(f"   Быстрейшее исследование: {min(session_times):.2f}с")
        print(f"   Медленнейшее исследование: {max(session_times):.2f}с")

    async def run_all_demos(self):
        """Запуск всех демонстраций"""
        print("🔬 DEEP RESEARCH ENGINE - ПОЛНАЯ ДЕМОНСТРАЦИЯ")
        print("="*80)
        
        if not await self.initialize():
            print("❌ Не удалось инициализировать движок")
            return
        
        try:
            # Демонстрация статуса движка
            await self.demo_engine_status()
            
            # Базовое исследование
            await self.demo_basic_research()
            
            # Множественные исследования
            await self.demo_multiple_research()
            
            # Адаптивное планирование
            await self.demo_adaptive_planning()
            
            # Отмена исследования
            await self.demo_research_cancellation()
            
            # Метрики производительности
            await self.demo_performance_metrics()
            
            # Финальный статус
            print("\n" + "="*80)
            print("📊 ФИНАЛЬНЫЙ СТАТУС ДВИЖКА")
            print("="*80)
            await self.demo_engine_status()
            
            print("\n🎉 ВСЕ ДЕМОНСТРАЦИИ ЗАВЕРШЕНЫ УСПЕШНО!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в демонстрации: {e}")

async def main():
    """Главная функция демонстрации"""
    demo = DeepResearchDemo()
    await demo.run_all_demos()

if __name__ == "__main__":
    asyncio.run(main()) 