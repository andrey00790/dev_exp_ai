"""
LLM Generation Service для AI Assistant MVP
Использует различные LLM для генерации RFC контента
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from adapters.llm.llm_loader import load_llm

from app.models.generation import GenerationSession, TaskType, UserAnswer

logger = logging.getLogger(__name__)


class LLMGenerationService:
    """Сервис для генерации RFC контента с помощью LLM."""

    def __init__(self):
        self.llm = load_llm()
        logger.info(
            f"LLM Generation Service initialized with {type(self.llm).__name__}"
        )

    async def generate_enhanced_rfc_content(
        self, session: GenerationSession, template_vars: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Генерирует улучшенный контент RFC с помощью LLM.

        Заменяет mock генерацию на реальную AI генерацию,
        используя контекст задачи и ответы пользователя.
        """

        # Подготавливаем контекст для LLM
        context = await self._prepare_llm_context(session)

        # Генерируем каждую секцию с помощью LLM
        enhanced_content = {}

        sections_to_generate = [
            ("summary", "Summary - краткое описание"),
            ("context", "Context - контекст и мотивация"),
            ("problem_statement", "Problem Statement - формулировка проблемы"),
            ("goals", "Goals - цели проекта"),
            ("architecture_overview", "Architecture Overview - архитектурное решение"),
            ("implementation_plan", "Implementation Plan - план реализации"),
            ("risk_analysis", "Risk Analysis - анализ рисков"),
            ("success_metrics", "Success Metrics - метрики успеха"),
        ]

        for section_key, section_description in sections_to_generate:
            try:
                content = await self._generate_section_content(
                    section_key, section_description, context, session
                )
                enhanced_content[section_key] = content
                logger.debug(f"Generated {section_key}: {len(content)} characters")

            except Exception as e:
                logger.warning(f"Failed to generate {section_key} with LLM: {e}")
                # Fallback на template контент
                enhanced_content[section_key] = template_vars.get(
                    section_key,
                    f"## {section_description}\n\nКонтент будет сгенерирован...",
                )

        # Заполняем остальные секции из шаблона
        for key, value in template_vars.items():
            if key not in enhanced_content:
                enhanced_content[key] = value

        return enhanced_content

    async def generate_smart_questions(
        self, session: GenerationSession
    ) -> List[Dict[str, Any]]:
        """
        Генерирует умные вопросы на основе контекста задачи с помощью LLM.

        Заменяет статические вопросы на динамически генерируемые.
        """

        prompt = f"""
Ты - опытный архитектор программного обеспечения. Тебе нужно задать 3-4 умных вопроса для сбора требований к проекту.

Задача: {session.task_type.value}
Описание: {session.initial_request}

Сгенерируй 3-4 конкретных вопроса которые помогут понять:
1. Бизнес-цели и приоритеты
2. Технические требования
3. Ограничения и риски
4. Масштаб и нагрузку

Формат ответа:
Q1: [вопрос 1]
Q2: [вопрос 2]  
Q3: [вопрос 3]
Q4: [вопрос 4] (опционально)

Вопросы должны быть конкретными для данной задачи.
"""

        try:
            response = await self.llm.generate(prompt)
            questions = self._parse_questions_from_llm_response(response)
            logger.info(f"Generated {len(questions)} smart questions with LLM")
            return questions

        except Exception as e:
            logger.error(f"Failed to generate questions with LLM: {e}")
            # Fallback на стандартные вопросы
            return self._get_fallback_questions(session.task_type)

    async def _prepare_llm_context(self, session: GenerationSession) -> str:
        """Подготавливает контекст для LLM запросов."""

        answers_text = ""
        if session.answers:
            answers_text = "\n".join(
                [
                    f"- {answer.question_id}: {answer.answer}"
                    for answer in session.answers
                ]
            )

        context = f"""
Тип задачи: {session.task_type.value}
Описание задачи: {session.initial_request}

Ответы пользователя:
{answers_text}

Дата создания: {session.created_at.strftime('%Y-%m-%d')}
"""
        return context.strip()

    async def _generate_section_content(
        self,
        section_key: str,
        section_description: str,
        context: str,
        session: GenerationSession,
    ) -> str:
        """Генерирует контент для конкретной секции RFC."""

        prompts = {
            "summary": f"""
Напиши профессиональное Summary для RFC документа.

Контекст:
{context}

Требования:
- 2-3 предложения
- Четко объясни ЧТО решается
- Укажи ЗАЧЕМ это нужно
- Профессиональный тон

Пример: "Данный RFC описывает архитектуру системы уведомлений для увеличения engagement пользователей. Решение основано на микросервисной архитектуре и обеспечивает масштабируемость до 100K+ пользователей."
""",
            "context": f"""
Напиши секцию Context для RFC документа.

Контекст:
{context}

Структура:
### Текущая ситуация
[описание проблемы]

### Мотивация
[почему нужно решать сейчас]

### Бизнес-цели
[что хочет достичь бизнес]

Требования:
- Конкретные факты
- Четкая мотивация  
- Связь с бизнес-целями
""",
            "problem_statement": f"""
Сформулируй четкое Problem Statement для RFC.

Контекст:
{context}

Требования:
- Начни с "**Проблема:**"
- Одно четкое предложение
- Укажи критичность
- Объясни влияние на бизнес

Пример: "**Проблема:** Отсутствие централизованной системы уведомлений приводит к снижению retention на 15% и усложняет персонализацию контента."
""",
            "goals": f"""
Определи Goals для RFC документа.

Контекст:
{context}

Структура:
**Основные цели:**
- [цель 1]
- [цель 2]
- [цель 3]

**Критерии успеха:**
- [измеримый критерий 1]
- [измеримый критерий 2]

Требования:
- Цели должны быть SMART
- Критерии должны быть измеримыми
- Связь с бизнес-ценностью
""",
            "architecture_overview": f"""
Опиши Architecture Overview для RFC.

Контекст:
{context}

Включи:
1. Высокоуровневую архитектуру
2. Основные компоненты
3. Принципы проектирования
4. Mermaid диаграмму если возможно

Требования:
- Профессиональная терминология
- Четкое разделение ответственности
- Масштабируемость и надежность
""",
            "implementation_plan": f"""
Создай Implementation Plan для RFC.

Контекст:
{context}

Структура:
**Фаза 1: [название] (временные рамки)**
- [задача 1]
- [задача 2]

**Фаза 2: [название] (временные рамки)**
- [задача 1]
- [задача 2]

**Фаза 3: [название] (временные рамки)**
- [задача 1]
- [задача 2]

Требования:
- Реалистичные временные рамки
- Четкие deliverables
- Управление рисками
""",
            "risk_analysis": f"""
Проведи Risk Analysis для RFC.

Контекст:
{context}

Структура:
**Высокие риски:**
- [риск 1]: [описание и митигация]

**Средние риски:**
- [риск 2]: [описание и митигация]

**Митигация:**
- [стратегия 1]
- [стратегия 2]

Требования:
- Реальные технические риски
- Конкретные меры митигации
- Планы отката
""",
            "success_metrics": f"""
Определи Success Metrics для RFC.

Контекст:
{context}

Структура:
**Technical Metrics:**
- [метрика 1]: [целевое значение]
- [метрика 2]: [целевое значение]

**Business Metrics:**
- [метрика 1]: [целевое значение]
- [метрика 2]: [целевое значение]

**Operational Metrics:**
- [метрика 1]: [целевое значение]

**AI Assistant Core Functions Metrics:**
- **RFC Generation Quality** (/api/v1/generate): Качество генерации RFC при создании/изменении/анализе функционала
  - Время генерации RFC: < 30 секунд
  - Полнота секций RFC: > 95%
  - Качество контента (1-5): > 4.0
  - Соответствие шаблону: 100%
- **Semantic Search Accuracy**: Точность семантического поиска по корпоративным данным
  - Precision@5: > 85%
  - Response time: < 500ms
  - Relevance score: > 0.8
  - User satisfaction: > 4.0/5
- **Code Documentation Generation**: Качество автогенерации документации по коду
  - Documentation completeness: > 90%
  - Code coverage: > 80%
  - Generation time: < 60 секунд
  - Developer satisfaction: > 4.0/5

Требования:
- Измеримые KPI
- Реалистичные targets
- Связь с бизнес-целями
- Фокус на трех ключевых функциях AI ассистента
""",
        }

        prompt = prompts.get(
            section_key,
            f"""
Напиши секцию "{section_description}" для RFC документа.

Контекст:
{context}

Требования:
- Профессиональный тон
- Конкретика без воды
- Практическая ценность
""",
        )

        response = await self.llm.generate(prompt)
        return response.strip()

    def _parse_questions_from_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Парсит вопросы из ответа LLM."""

        questions = []
        lines = response.strip().split("\n")

        for line in lines:
            line = line.strip()
            if line.startswith("Q") and ":" in line:
                # Извлекаем вопрос после номера
                question_text = line.split(":", 1)[1].strip()
                if question_text:
                    questions.append(
                        {
                            "id": f"llm_q{len(questions) + 1}",
                            "question": question_text,
                            "question_type": "TEXT",
                            "is_required": True,
                            "context": "Сгенерировано AI на основе контекста задачи",
                        }
                    )

        return questions[:4]  # Максимум 4 вопроса

    def _get_fallback_questions(self, task_type: TaskType) -> List[Dict[str, Any]]:
        """Fallback вопросы если LLM не сработал."""

        base_questions = [
            {
                "id": "fallback_q1",
                "question": "Какова основная бизнес-цель этого проекта?",
                "question_type": "TEXT",
                "is_required": True,
                "context": "Помогает понять приоритеты и критерии успеха",
            },
            {
                "id": "fallback_q2",
                "question": "Какие технические ограничения или требования нужно учесть?",
                "question_type": "TEXT",
                "is_required": True,
                "context": "Важно для архитектурных решений",
            },
            {
                "id": "fallback_q3",
                "question": "Какой ожидаемый масштаб системы?",
                "question_type": "CHOICE",
                "options": [
                    "Малый (< 1K пользователей)",
                    "Средний (1K-10K)",
                    "Большой (10K-100K)",
                    "Очень большой (> 100K)",
                ],
                "is_required": True,
                "context": "Влияет на выбор архитектуры",
            },
        ]

        return base_questions

    async def generate_code_documentation(
        self,
        documentation_type: str,
        context: str,
        target_audience: str = "developers",
        detail_level: str = "detailed",
    ) -> str:
        """
        Генерирует документацию по коду с помощью LLM.

        Args:
            documentation_type: Тип документации (api_docs, readme, etc.)
            context: Контекст анализа кода
            target_audience: Целевая аудитория
            detail_level: Уровень детализации

        Returns:
            Сгенерированная документация в markdown формате
        """

        documentation_prompts = {
            "api_docs": f"""
Создай профессиональную API документацию на основе анализа кода.

Контекст анализа:
{context}

Структура документации:
# API Documentation

## Overview
[Краткое описание API]

## Authentication
[Если применимо]

## Endpoints
[Список всех endpoints с описанием]

## Request/Response Examples
[Примеры запросов и ответов]

## Error Codes
[Коды ошибок и их описание]

Требования:
- Целевая аудитория: {target_audience}
- Уровень детализации: {detail_level}
- Включи примеры использования
- Профессиональный тон
- Практическая ценность
""",
            "readme": f"""
Создай README файл для проекта на основе анализа кода.

Контекст анализа:
{context}

Структура README:
# Project Name

## Description
[Что делает проект]

## Installation
[Как установить]

## Usage
[Как использовать]

## Features
[Основной функционал]

## Examples
[Примеры использования]

## Contributing
[Как контрибьютить]

## License
[Лицензия]

Требования:
- Целевая аудитория: {target_audience}
- Уровень детализации: {detail_level}
- Четкие инструкции
- Примеры кода
- Понятный язык
""",
            "technical_spec": f"""
Создай техническую спецификацию на основе анализа кода.

Контекст анализа:
{context}

Структура спецификации:
# Technical Specification

## Architecture Overview
[Архитектурное решение]

## Components
[Основные компоненты]

## Data Flow
[Поток данных]

## API Design
[Дизайн API если есть]

## Database Schema
[Схема БД если есть]

## Security Considerations
[Вопросы безопасности]

## Performance
[Характеристики производительности]

## Deployment
[Развертывание]

Требования:
- Целевая аудитория: {target_audience}
- Уровень детализации: {detail_level}
- Техническая точность
- Практические рекомендации
""",
            "code_comments": f"""
Сгенерируй комментарии и docstrings для кода.

Контекст анализа:
{context}

Сгенерируй:
1. Описание модуля/файла
2. Docstrings для каждой функции
3. Комментарии к сложной логике
4. Описание параметров и возвращаемых значений

Требования:
- Целевая аудитория: {target_audience}
- Уровень детализации: {detail_level}
- Следуй стандартам документирования языка
- Объясни назначение и логику
- Добавь примеры использования
""",
            "user_guide": f"""
Создай руководство пользователя на основе анализа кода.

Контекст анализа:
{context}

Структура руководства:
# User Guide

## Getting Started
[Первые шаги]

## Features
[Описание функций]

## Step-by-Step Tutorials
[Пошаговые инструкции]

## FAQ
[Частые вопросы]

## Troubleshooting
[Решение проблем]

## Support
[Куда обращаться за помощью]

Требования:
- Целевая аудитория: {target_audience}
- Уровень детализации: {detail_level}
- Простой язык
- Пошаговые инструкции
- Примеры и скриншоты
""",
        }

        # Выбираем подходящий промпт
        prompt = documentation_prompts.get(
            documentation_type,
            f"""
Создай документацию типа "{documentation_type}" на основе анализа кода.

Контекст анализа:
{context}

Требования:
- Целевая аудитория: {target_audience}
- Уровень детализации: {detail_level}
- Профессиональный тон
- Практическая ценность
- Структурированная подача
""",
        )

        try:
            response = await self.llm.generate(prompt)
            logger.info(
                f"Generated {documentation_type} documentation: {len(response)} characters"
            )
            return response.strip()

        except Exception as e:
            logger.error(
                f"Failed to generate {documentation_type} documentation with LLM: {e}"
            )

            # Fallback документация
            return f"""# {documentation_type.replace('_', ' ').title()}

## Overview
Документация сгенерирована на основе анализа кода.

{context}

## Next Steps
Этот документ требует дополнительной проработки и детализации.

---
*Документация сгенерирована AI Assistant*
"""

    async def generate_response(self, prompt: str, context: str = "") -> str:
        """
        Генерирует ответ на основе промпта и контекста.
        Метод для совместимости с deep_research_engine.
        """
        try:
            # Подготавливаем полный промпт
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            
            # Используем существующий LLM для генерации
            response = await self.llm.agenerate(
                [full_prompt],
                max_tokens=2048,
                temperature=0.7
            )
            
            if response and len(response) > 0:
                return response[0].strip()
            else:
                return "Не удалось сгенерировать ответ."
                
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return "Ошибка при генерации ответа."
