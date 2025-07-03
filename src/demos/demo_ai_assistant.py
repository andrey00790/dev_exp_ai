#!/usr/bin/env python3
"""
Демонстрационный скрипт для AI Assistant MVP

Показывает основные возможности новой архитектуры:
1. AI-генерация RFC документов с интерактивными вопросами
2. Семантический поиск по корпоративным данным  
3. Система обратной связи для переобучения модели
4. Управление источниками данных
5. Автоматическая синхронизация

Использование:
    python demo_ai_assistant.py [--server-url http://localhost:8000]
"""

import asyncio
import json
import sys
from typing import Dict, Any
import httpx
import argparse
from datetime import datetime


class AIAssistantDemo:
    """Демонстрация возможностей AI Assistant MVP."""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def check_health(self) -> bool:
        """Проверяет доступность сервера."""
        try:
            response = await self.client.get(f"{self.server_url}/health")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Сервер недоступен: {e}")
            return False
    
    async def demo_rfc_generation(self) -> None:
        """Демонстрирует генерацию RFC документа."""
        print("\n🚀 === ДЕМОНСТРАЦИЯ ГЕНЕРАЦИИ RFC ДОКУМЕНТА ===")
        
        # 1. Начинаем генерацию с интерактивными вопросами
        print("\n1️⃣ Начинаем генерацию RFC для нового функционала...")
        
        generation_request = {
            "task_type": "new_feature",
            "initial_request": "Нужно спроектировать систему уведомлений для мобильного приложения. Пользователи должны получать push-уведомления о важных событиях, с возможностью настройки типов уведомлений.",
            "context": "Система должна быть масштабируемой и поддерживать различные типы устройств",
            "user_id": "demo_user",
            "search_sources": ["confluence-main", "gitlab-rfcs"]
        }
        
        try:
            response = await self.client.post(
                f"{self.server_url}/api/v1/generate",
                json=generation_request
            )
            
            if response.status_code == 200:
                result = response.json()
                session_id = result["session_id"]
                questions = result["questions"]
                
                print(f"✅ Сессия создана: {session_id}")
                print(f"📝 AI задал {len(questions)} вопросов:")
                
                for i, question in enumerate(questions, 1):
                    print(f"\n   {i}. {question['question']}")
                    if question.get('options'):
                        for j, option in enumerate(question['options'], 1):
                            print(f"      {j}) {option}")
                    if question.get('context'):
                        print(f"      💡 {question['context']}")
                
                # 2. Отвечаем на вопросы
                print("\n2️⃣ Отвечаем на вопросы AI...")
                
                answers = [
                    {"question_id": "q1", "answer": "Увеличить пользовательскую вовлеченность и информировать о критических событиях"},
                    {"question_id": "q2", "answer": ["Внешние клиенты", "Внутренние пользователи"]},
                    {"question_id": "q3", "answer": "Высокая (10K-100K)"}
                ]
                
                answer_response = await self.client.post(
                    f"{self.server_url}/api/v1/generate/answer",
                    json={"session_id": session_id, "answers": answers}
                )
                
                if answer_response.status_code == 200:
                    answer_result = answer_response.json()
                    print(f"✅ Ответы сохранены")
                    print(f"🎯 Готов к генерации: {answer_result['is_ready_to_generate']}")
                    
                    if answer_result['is_ready_to_generate']:
                        # 3. Генерируем финальный RFC
                        print("\n3️⃣ Генерируем финальный RFC документ...")
                        
                        final_response = await self.client.post(
                            f"{self.server_url}/api/v1/generate/finalize",
                            json={
                                "session_id": session_id,
                                "additional_requirements": "Особое внимание к безопасности и производительности"
                            }
                        )
                        
                        if final_response.status_code == 200:
                            rfc_result = final_response.json()
                            rfc = rfc_result["rfc"]
                            
                            print(f"✅ RFC документ сгенерирован!")
                            print(f"📄 Название: {rfc['title']}")
                            print(f"📝 Описание: {rfc['summary']}")
                            print(f"📚 Разделов: {len(rfc['sections'])}")
                            print(f"🔗 Источники: {', '.join(rfc['sources_used'])}")
                            
                            # Показываем структуру RFC
                            print("\n📋 Структура RFC:")
                            for section in rfc['sections']:
                                print(f"   {section['title']}")
                                content_preview = section['content'][:100] + "..." if len(section['content']) > 100 else section['content']
                                print(f"      {content_preview}")
                            
                            return rfc
                        else:
                            print(f"❌ Ошибка генерации RFC: {final_response.text}")
                    else:
                        print("❓ Нужно ответить на дополнительные вопросы")
                else:
                    print(f"❌ Ошибка при сохранении ответов: {answer_response.text}")
            else:
                print(f"❌ Ошибка при начале генерации: {response.text}")
                
        except Exception as e:
            print(f"❌ Ошибка при генерации RFC: {e}")
    
    async def demo_semantic_search(self) -> None:
        """Демонстрирует семантический поиск."""
        print("\n🔍 === ДЕМОНСТРАЦИЯ СЕМАНТИЧЕСКОГО ПОИСКА ===")
        
        search_queries = [
            "микросервисная архитектура API gateway",
            "система уведомлений push notifications",
            "безопасность API аутентификация",
            "мониторинг производительности metrics"
        ]
        
        for i, query in enumerate(search_queries, 1):
            print(f"\n{i}️⃣ Поиск: '{query}'")
            
            try:
                search_request = {
                    "query": query,
                    "sources": [],  # Поиск по всем источникам
                    "source_types": ["confluence", "gitlab", "uploaded_file"],
                    "limit": 3,
                    "threshold": 0.7,
                    "include_content": False
                }
                
                response = await self.client.post(
                    f"{self.server_url}/api/v1/search",
                    json=search_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    results = result["results"]
                    
                    print(f"   📊 Найдено: {result['total_found']} результатов за {result['search_time_ms']}мс")
                    print(f"   🔍 Источники: {', '.join(result['sources_searched'])}")
                    
                    if results:
                        print("   📄 Топ результаты:")
                        for j, doc in enumerate(results, 1):
                            print(f"      {j}. {doc['title']} ({doc['relevance_score']:.2f})")
                            print(f"         📁 {doc['source_name']} | 👤 {doc.get('author', 'N/A')}")
                            print(f"         💬 {doc['snippet'][:80]}...")
                            if doc.get('highlights'):
                                print(f"         🔍 Ключевые слова: {', '.join(doc['highlights'][:3])}")
                    else:
                        print("   ❌ Результатов не найдено")
                else:
                    print(f"   ❌ Ошибка поиска: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Ошибка при поиске: {e}")
    
    async def demo_feedback_system(self, rfc_id: str = None) -> None:
        """Демонстрирует систему обратной связи."""
        print("\n👍 === ДЕМОНСТРАЦИЯ СИСТЕМЫ ОБРАТНОЙ СВЯЗИ ===")
        
        # Используем RFC ID из предыдущей демонстрации или создаем демо ID
        target_id = rfc_id or "demo_rfc_12345"
        
        # 1. Отправляем положительную обратную связь
        print("\n1️⃣ Отправляем положительную обратную связь...")
        
        try:
            feedback_request = {
                "target_id": target_id,
                "context": "rfc_generation",
                "feedback_type": "like",
                "rating": 5,
                "comment": "Отличный RFC! Все аспекты архитектуры подробно описаны, особенно понравился раздел о безопасности.",
                "session_id": "demo_session"
            }
            
            response = await self.client.post(
                f"{self.server_url}/api/v1/feedback",
                json=feedback_request
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Обратная связь отправлена: {result['feedback_id']}")
                print(f"   🎉 {result['message']}")
                print(f"   🏆 Заработано очков: {result['points_earned']}")
            else:
                print(f"   ❌ Ошибка отправки: {response.text}")
        
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        # 2. Отправляем критическую обратную связь
        print("\n2️⃣ Отправляем критическую обратную связь...")
        
        try:
            critical_feedback = {
                "target_id": target_id,
                "context": "rfc_generation", 
                "feedback_type": "dislike",
                "rating": 2,
                "reason": "incomplete",
                "comment": "RFC неполный, не хватает деталей по интеграции с внешними системами.",
                "session_id": "demo_session"
            }
            
            response = await self.client.post(
                f"{self.server_url}/api/v1/feedback",
                json=critical_feedback
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Критика отправлена: {result['feedback_id']}")
                print(f"   📝 {result['message']}")
            else:
                print(f"   ❌ Ошибка отправки: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        # 3. Получаем статистику обратной связи
        print("\n3️⃣ Получаем статистику обратной связи...")
        
        try:
            response = await self.client.get(
                f"{self.server_url}/api/v1/feedback/stats/{target_id}"
            )
            
            if response.status_code == 200:
                stats = response.json()
                print(f"   📊 Статистика для {target_id}:")
                print(f"      📝 Всего отзывов: {stats['total_feedback']}")
                print(f"      👍 Лайков: {stats['likes']}")
                print(f"      👎 Дизлайков: {stats['dislikes']}")
                print(f"      📈 Процент лайков: {stats['like_percentage']:.1f}%")
                if stats.get('average_rating'):
                    print(f"      ⭐ Средняя оценка: {stats['average_rating']:.1f}/5")
                if stats.get('most_common_dislike_reason'):
                    print(f"      ⚠️ Основная проблема: {stats['most_common_dislike_reason']}")
            else:
                print(f"   ❌ Ошибка получения статистики: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        # 4. Получаем аналитику для переобучения
        print("\n4️⃣ Получаем аналитику для переобучения модели...")
        
        try:
            response = await self.client.get(
                f"{self.server_url}/api/v1/feedback/analytics?context=rfc_generation&days=30"
            )
            
            if response.status_code == 200:
                analytics = response.json()
                if analytics:
                    for analytic in analytics:
                        print(f"   🤖 Аналитика для {analytic['context']}:")
                        print(f"      📊 Всего элементов: {analytic['total_items']}")
                        print(f"      📈 Покрытие обратной связью: {analytic['feedback_coverage']:.1%}")
                        print(f"      👍 Процент положительных: {analytic['positive_ratio']:.1%}")
                        if analytic.get('top_issues'):
                            print(f"      ⚠️ Основные проблемы: {', '.join(analytic['top_issues'][:3])}")
                        if analytic.get('recommendations'):
                            print(f"      💡 Рекомендации:")
                            for rec in analytic['recommendations'][:2]:
                                print(f"         • {rec}")
                else:
                    print("   📊 Недостаточно данных для аналитики")
            else:
                print(f"   ❌ Ошибка получения аналитики: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    async def demo_data_sources(self) -> None:
        """Демонстрирует управление источниками данных."""
        print("\n🔗 === ДЕМОНСТРАЦИЯ УПРАВЛЕНИЯ ИСТОЧНИКАМИ ДАННЫХ ===")
        
        # 1. Получаем список источников
        print("\n1️⃣ Получаем список настроенных источников...")
        
        try:
            response = await self.client.get(f"{self.server_url}/api/v1/sources")
            
            if response.status_code == 200:
                sources = response.json()
                print(f"   📚 Найдено {len(sources)} источников:")
                
                for source in sources:
                    status = "🟢" if source['is_enabled'] else "🔴"
                    last_sync = source.get('last_sync', 'Никогда')
                    print(f"      {status} {source['name']} ({source['source_type']})")
                    print(f"         🔄 Последняя синхронизация: {last_sync}")
            else:
                print(f"   ❌ Ошибка получения источников: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        # 2. Получаем типы поддерживаемых источников
        print("\n2️⃣ Получаем типы поддерживаемых источников...")
        
        try:
            response = await self.client.get(f"{self.server_url}/api/v1/sources/types")
            
            if response.status_code == 200:
                source_types = response.json()
                print(f"   🛠️ Поддерживается {len(source_types)} типов источников:")
                
                for source_type in source_types:
                    print(f"      📌 {source_type['name']} ({source_type['type']})")
                    print(f"         📝 {source_type['description']}")
                    
                    config_keys = list(source_type['required_config'].keys())[:3]
                    print(f"         🔧 Конфигурация: {', '.join(config_keys)}...")
            else:
                print(f"   ❌ Ошибка получения типов: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        # 3. Получаем статус синхронизации
        print("\n3️⃣ Получаем статус последней синхронизации...")
        
        try:
            response = await self.client.get(f"{self.server_url}/api/v1/sync/status")
            
            if response.status_code == 200:
                sync_status = response.json()
                print(f"   🔄 {sync_status['message']}")
                print(f"   📊 Общий статус: {sync_status['overall_status']}")
                
                if sync_status.get('results'):
                    print("   📋 Детали по источникам:")
                    for result in sync_status['results']:
                        status_icon = "✅" if result['status'] == "completed" else "❌"
                        print(f"      {status_icon} {result['source_name']}: {result['documents_processed']} документов")
                        if result.get('duration_seconds'):
                            print(f"         ⏱️ Длительность: {result['duration_seconds']:.1f}с")
            else:
                print(f"   ❌ Ошибка получения статуса: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    async def demo_examples(self) -> None:
        """Демонстрирует примеры запросов."""
        print("\n📚 === ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ===")
        
        try:
            response = await self.client.get(f"{self.server_url}/api/v1/generate/examples")
            
            if response.status_code == 200:
                examples = response.json()
                
                for task_type, example in examples.items():
                    print(f"\n📝 {example['title']}:")
                    print(f"   💡 Пример запроса:")
                    print(f"      \"{example['example']}\"")
                    print(f"   💭 Советы:")
                    for tip in example['tips']:
                        print(f"      • {tip}")
            else:
                print(f"❌ Ошибка получения примеров: {response.text}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    async def run_full_demo(self) -> None:
        """Запускает полную демонстрацию всех возможностей."""
        print("🤖 AI ASSISTANT MVP - ДЕМОНСТРАЦИЯ ВОЗМОЖНОСТЕЙ")
        print("=" * 60)
        
        # Проверяем доступность сервера
        if not await self.check_health():
            print("\n❌ Сервер недоступен. Убедитесь, что AI Assistant запущен:")
            print("   python3 app/main.py")
            return
        
        print("✅ Сервер доступен, начинаем демонстрацию...")
        
        # Получаем информацию о системе
        try:
            response = await self.client.get(f"{self.server_url}/")
            if response.status_code == 200:
                info = response.json()
                print(f"\n🏷️ {info['name']} v{info['version']}")
                print(f"📝 {info['description']}")
                print(f"🌍 Окружение: {info['environment']}")
                print(f"📊 Статус: {info['status']}")
                
                print("\n🚀 Доступные возможности:")
                for feature in info['features']:
                    print(f"   {feature}")
        except Exception as e:
            print(f"⚠️ Не удалось получить информацию о системе: {e}")
        
        # Запускаем демонстрации
        try:
            # Демонстрация RFC генерации
            rfc = await self.demo_rfc_generation()
            rfc_id = rfc.get('id') if rfc else None
            
            # Демонстрация семантического поиска
            await self.demo_semantic_search()
            
            # Демонстрация системы обратной связи
            await self.demo_feedback_system(rfc_id)
            
            # Демонстрация управления источниками
            await self.demo_data_sources()
            
            # Примеры использования
            await self.demo_examples()
            
            print("\n🎉 === ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА ===")
            print("\n💡 Следующие шаги:")
            print("   1. Настройте реальные источники данных (Confluence, Jira, GitLab)")
            print("   2. Интегрируйте с OpenAI или настройте локальный LLM")
            print("   3. Настройте автоматическую синхронизацию через cron")
            print("   4. Разработайте веб-интерфейс для пользователей")
            print("   5. Настройте мониторинг и аналитику")
            
            print(f"\n📚 API документация: {self.server_url}/docs")
            print(f"🔍 Альтернативная документация: {self.server_url}/redoc")
            
        except KeyboardInterrupt:
            print("\n⏹️ Демонстрация прервана пользователем")
        except Exception as e:
            print(f"\n❌ Ошибка во время демонстрации: {e}")
        finally:
            await self.client.aclose()


async def main():
    """Главная функция демонстрации."""
    parser = argparse.ArgumentParser(
        description="Демонстрация AI Assistant MVP"
    )
    parser.add_argument(
        "--server-url",
        default="http://localhost:8000",
        help="URL сервера AI Assistant (по умолчанию: http://localhost:8000)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Быстрая демонстрация (только основные функции)"
    )
    
    args = parser.parse_args()
    
    print(f"🔗 Подключение к серверу: {args.server_url}")
    
    demo = AIAssistantDemo(args.server_url)
    
    if args.quick:
        print("⚡ Режим быстрой демонстрации")
        if await demo.check_health():
            await demo.demo_rfc_generation()
            await demo.demo_semantic_search()
        await demo.client.aclose()
    else:
        await demo.run_full_demo()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1) 