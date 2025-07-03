#!/usr/bin/env python3
"""
Демонстрация генерации RFC документов с профессиональными шаблонами

Показывает как AI Assistant создает полноценные RFC документы
по стандартам GitHub, Stripe и других ведущих компаний.

Использование:
    python demo_rfc_templates.py
"""

import asyncio
import httpx
import json
from datetime import datetime


class RFCTemplateDemo:
    """Демонстрация генерации RFC с шаблонами."""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def demo_rfc_generation_with_templates(self) -> None:
        """Демонстрирует генерацию RFC с использованием профессиональных шаблонов."""
        
        print("🚀 RFC GENERATION WITH PROFESSIONAL TEMPLATES")
        print("=" * 60)
        print("Демонстрация генерации RFC документов по стандартам:")
        print("• GitHub Engineering RFCs")
        print("• Stripe RFC Process") 
        print("• Architecture Decision Records (ADR)")
        print("• Industry Best Practices")
        print()
        
        # Тестовые сценарии для разных типов задач
        scenarios = [
            {
                "name": "Проектирование нового функционала",
                "task_type": "new_feature",
                "request": "Спроектировать систему real-time уведомлений для e-commerce платформы. Нужна поддержка push-уведомлений, email, SMS для заказов, доставки, промо-акций с персонализацией.",
                "context": "Ожидается 100K+ активных пользователей, интеграция с мобильными приложениями iOS/Android",
                "answers": [
                    {"question_id": "q1", "answer": "Увеличить конверсию и retention пользователей через персонализированные уведомления"},
                    {"question_id": "q2", "answer": ["Внешние клиенты", "Внутренние пользователи"]},
                    {"question_id": "q3", "answer": "Очень высокая (> 100K)"}
                ]
            },
            {
                "name": "Модернизация существующей системы",
                "task_type": "modify_existing", 
                "request": "Модернизировать legacy API авторизации для поддержки OAuth 2.0, JWT tokens, multi-tenant архитектуры с backward compatibility.",
                "context": "Текущая система на session-based auth, нужна миграция без downtime",
                "answers": [
                    {"question_id": "q1", "answer": "Текущая система использует session cookies, single tenant, MySQL для пользователей"},
                    {"question_id": "q2", "answer": "Масштабируемость, security compliance, API rate limiting"},
                    {"question_id": "q3", "answer": True}  # backward compatibility
                ]
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📋 СЦЕНАРИЙ {i}: {scenario['name']}")
            print("-" * 50)
            
            # 1. Начинаем генерацию
            print(f"1️⃣ Запрос: {scenario['request'][:80]}...")
            
            generation_request = {
                "task_type": scenario["task_type"],
                "initial_request": scenario["request"],
                "context": scenario["context"],
                "user_id": "demo_architect",
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
                    print(f"📝 AI задал {len(questions)} вопросов")
                    
                    # 2. Отвечаем на вопросы
                    print("2️⃣ Отвечаем на вопросы AI...")
                    
                    answer_response = await self.client.post(
                        f"{self.server_url}/api/v1/generate/answer",
                        json={"session_id": session_id, "answers": scenario["answers"]}
                    )
                    
                    if answer_response.status_code == 200:
                        answer_result = answer_response.json()
                        print(f"✅ Готов к генерации: {answer_result['is_ready_to_generate']}")
                        
                        # 3. Генерируем RFC
                        if answer_result['is_ready_to_generate']:
                            print("3️⃣ Генерируем профессиональный RFC документ...")
                            
                            final_response = await self.client.post(
                                f"{self.server_url}/api/v1/generate/finalize",
                                json={
                                    "session_id": session_id,
                                    "additional_requirements": "Включить security considerations и performance metrics"
                                }
                            )
                            
                            if final_response.status_code == 200:
                                rfc_result = final_response.json()
                                rfc = rfc_result["rfc"]
                                
                                print(f"✅ RFC документ сгенерирован!")
                                print(f"🆔 ID: {rfc['id']}")
                                print(f"📄 Название: {rfc['title']}")
                                print(f"📝 Описание: {rfc['summary']}")
                                
                                # Показываем структуру профессионального RFC
                                if 'full_content' in rfc and rfc['full_content']:
                                    await self._display_rfc_structure(rfc)
                                else:
                                    print(f"📚 Секций: {len(rfc['sections'])}")
                                    for section in rfc['sections'][:3]:  # Показываем первые 3
                                        print(f"   • {section['title']}")
                                
                                print(f"🔗 Источники: {', '.join(rfc['sources_used'])}")
                                print(f"🏷️ Метаданные: {json.dumps(rfc['metadata'], indent=2)}")
                                
                                # Показываем предварительный просмотр для первого сценария
                                if i == 1:
                                    await self._show_rfc_preview(rfc)
                            
                            else:
                                print(f"❌ Ошибка генерации RFC: {final_response.text}")
                    else:
                        print(f"❌ Ошибка при ответах: {answer_response.text}")
                else:
                    print(f"❌ Ошибка создания сессии: {response.text}")
                    
            except Exception as e:
                print(f"❌ Ошибка: {e}")
    
    async def _display_rfc_structure(self, rfc: dict) -> None:
        """Отображает структуру сгенерированного RFC."""
        
        print("\n📋 СТРУКТУРА RFC ДОКУМЕНТА:")
        print("-" * 30)
        
        if 'full_content' in rfc and rfc['full_content']:
            # Парсим YAML метаданные
            content = rfc['full_content']
            lines = content.split('\n')
            
            # Извлекаем YAML заголовок
            if lines[0] == '---':
                yaml_end = -1
                for i, line in enumerate(lines[1:], 1):
                    if line == '---':
                        yaml_end = i
                        break
                
                if yaml_end > 0:
                    print("📋 YAML Метаданные:")
                    yaml_lines = lines[1:yaml_end]
                    for line in yaml_lines[:6]:  # Показываем первые 6 строк
                        print(f"   {line}")
                    if len(yaml_lines) > 6:
                        print(f"   ... и еще {len(yaml_lines) - 6} строк")
            
            # Извлекаем заголовки секций
            print("\n📚 Секции документа:")
            section_count = 0
            for line in lines:
                if line.startswith('## ') and not line.startswith('###'):
                    section_count += 1
                    section_title = line[3:].strip()
                    print(f"   {section_count}. {section_title}")
                    if section_count >= 10:  # Ограничиваем вывод
                        remaining = sum(1 for l in lines if l.startswith('## ') and not l.startswith('###')) - 10
                        if remaining > 0:
                            print(f"   ... и еще {remaining} секций")
                        break
            
            print(f"\n📊 Статистика документа:")
            print(f"   • Общее количество строк: {len(lines)}")
            print(f"   • Размер документа: {len(content):,} символов")
            print(f"   • Секций уровня 2 (##): {sum(1 for l in lines if l.startswith('## ') and not l.startswith('###'))}")
            print(f"   • Подсекций уровня 3 (###): {sum(1 for l in lines if l.startswith('### '))}")
        
        else:
            print(f"📚 Секций в структурированном виде: {len(rfc['sections'])}")
            for i, section in enumerate(rfc['sections'][:5], 1):
                print(f"   {i}. {section['title']}")
                content_preview = section['content'][:60] + "..." if len(section['content']) > 60 else section['content']
                print(f"      {content_preview}")
    
    async def _show_rfc_preview(self, rfc: dict) -> None:
        """Показывает предварительный просмотр RFC."""
        
        print("\n🔍 ПРЕДВАРИТЕЛЬНЫЙ ПРОСМОТР RFC:")
        print("=" * 40)
        
        if 'full_content' in rfc and rfc['full_content']:
            content = rfc['full_content']
            lines = content.split('\n')
            
            # Находим и показываем Summary секцию
            in_summary = False
            summary_lines = []
            
            for line in lines:
                if line.strip() == '## Summary':
                    in_summary = True
                    continue
                elif line.startswith('## ') and in_summary:
                    break
                elif in_summary and line.strip():
                    summary_lines.append(line)
            
            if summary_lines:
                print("📝 Summary:")
                for line in summary_lines[:5]:  # Первые 5 строк
                    print(f"   {line}")
                if len(summary_lines) > 5:
                    print("   ...")
            
            # Показываем Context
            in_context = False
            context_lines = []
            
            for line in lines:
                if line.strip() == '## Context':
                    in_context = True
                    continue
                elif line.startswith('## ') and in_context:
                    break
                elif in_context and line.strip():
                    context_lines.append(line)
            
            if context_lines:
                print("\n🔍 Context:")
                for line in context_lines[:3]:  # Первые 3 строки
                    print(f"   {line}")
                if len(context_lines) > 3:
                    print("   ...")
            
            # Показываем Goals
            in_goals = False
            goals_lines = []
            
            for line in lines:
                if line.strip() == '## Goals':
                    in_goals = True
                    continue
                elif line.startswith('## ') and in_goals:
                    break
                elif in_goals and line.strip():
                    goals_lines.append(line)
            
            if goals_lines:
                print("\n🎯 Goals:")
                for line in goals_lines[:4]:  # Первые 4 строки
                    print(f"   {line}")
                if len(goals_lines) > 4:
                    print("   ...")
        
        print("\n💡 Этот RFC готов для:")
        print("   • Technical Review")
        print("   • Architecture Review")
        print("   • Security Review")
        print("   • Implementation Planning")
    
    async def run_demo(self) -> None:
        """Запускает полную демонстрацию RFC шаблонов."""
        
        try:
            # Проверяем доступность сервера
            response = await self.client.get(f"{self.server_url}/health")
            if response.status_code != 200:
                print("❌ Сервер недоступен")
                return
            
            print("🤖 AI ASSISTANT - RFC TEMPLATES DEMONSTRATION")
            print("Генерация профессиональных RFC документов")
            print()
            
            await self.demo_rfc_generation_with_templates()
            
            print("\n🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
            print("\n💡 Преимущества нового подхода:")
            print("   ✅ Профессиональные шаблоны по стандартам индустрии")
            print("   ✅ Полный YAML заголовок с метаданными")
            print("   ✅ Структурированные секции (Summary, Context, Goals, etc.)")
            print("   ✅ Архитектурные диаграммы и API спецификации")
            print("   ✅ Trade-offs анализ и риски")
            print("   ✅ Implementation план с временными рамками")
            print("   ✅ Success metrics и monitoring")
            print("   ✅ Готовность к техническому ревью")
            
            print(f"\n📚 Документация API: {self.server_url}/docs")
            
        except KeyboardInterrupt:
            print("\n⏹️ Демонстрация прервана")
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
        finally:
            await self.client.aclose()


async def main():
    """Главная функция демонстрации."""
    demo = RFCTemplateDemo()
    await demo.run_demo()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}") 