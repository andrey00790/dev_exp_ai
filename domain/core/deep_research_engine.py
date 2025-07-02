"""
Deep Research Engine - Многошаговый режим углубленного анализа

Система интеллектуального исследования запросов с использованием
цепочки обращений к LLM для получения максимально полных и точных ответов.

Возможности:
- Многошаговый анализ с промежуточными результатами
- Ограничение итераций для предотвращения бесконечного анализа
- Интеграция с семантическим поиском и базой знаний
- Real-time отслеживание хода исследования
- Адаптивное планирование следующих шагов
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import uuid4

from domain.core.llm_generation_service import LLMGenerationService
from domain.integration.enhanced_vector_search_service import \
    get_enhanced_vector_search_service

logger = logging.getLogger(__name__)


class ResearchStepType(Enum):
    """Типы шагов исследования"""

    INITIAL_ANALYSIS = "initial_analysis"
    CONTEXT_GATHERING = "context_gathering"
    DEEP_ANALYSIS = "deep_analysis"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"
    FINAL_SUMMARY = "final_summary"


class ResearchStatus(Enum):
    """Статусы исследования"""

    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Статусы отдельных шагов"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ResearchStep:
    """Отдельный шаг исследования"""

    step_id: str = field(default_factory=lambda: str(uuid4()))
    step_type: ResearchStepType = ResearchStepType.INITIAL_ANALYSIS
    status: StepStatus = StepStatus.PENDING
    title: str = ""
    description: str = ""
    query: str = ""
    result: str = ""
    sources: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    duration: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: str = ""
    next_steps: List[str] = field(default_factory=list)


@dataclass
class ResearchSession:
    """Сессия исследования"""

    session_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    original_query: str = ""
    research_goal: str = ""
    status: ResearchStatus = ResearchStatus.CREATED
    steps: List[ResearchStep] = field(default_factory=list)
    current_step: int = 0
    max_steps: int = 7
    final_result: str = ""
    total_sources: int = 0
    overall_confidence: float = 0.0
    duration: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DeepResearchEngine:
    """Движок углубленного исследования"""

    def __init__(self):
        self.llm_service = LLMGenerationService()
        self.active_sessions: Dict[str, ResearchSession] = {}

        # Метрики движка
        self.metrics = {
            "total_sessions": 0,
            "completed_sessions": 0,
            "average_steps": 0.0,
            "average_duration": 0.0,
            "success_rate": 0.0,
        }

        # Конфигурация
        self.config = {
            "max_concurrent_sessions": 10,
            "default_max_steps": 7,
            "step_timeout": 60,  # секунды
            "min_confidence_threshold": 0.6,
            "enable_adaptive_planning": True,
        }

    async def start_research(
        self, query: str, user_id: str = "", max_steps: int = None
    ) -> ResearchSession:
        """Начать новое исследование"""
        if len(self.active_sessions) >= self.config["max_concurrent_sessions"]:
            raise Exception("Превышен лимит одновременных исследований")

        session = ResearchSession(
            user_id=user_id,
            original_query=query,
            research_goal=await self._extract_research_goal(query),
            max_steps=max_steps or self.config["default_max_steps"],
        )

        self.active_sessions[session.session_id] = session
        self.metrics["total_sessions"] += 1

        logger.info(f"🔬 Начато исследование: {session.session_id}")
        return session

    async def execute_research(
        self, session_id: str
    ) -> AsyncGenerator[ResearchStep, None]:
        """Выполнить исследование с генерацией промежуточных результатов"""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Сессия {session_id} не найдена")

        session.status = ResearchStatus.IN_PROGRESS
        start_time = datetime.now()

        try:
            # Планирование шагов исследования
            planned_steps = await self._plan_research_steps(session)
            session.steps = planned_steps

            # Выполнение шагов
            for i, step in enumerate(session.steps):
                if i >= session.max_steps:
                    break

                session.current_step = i
                step.status = StepStatus.RUNNING

                logger.info(f"🔍 Выполняется шаг {i+1}: {step.title}")

                try:
                    await self._execute_step(step, session)
                    step.status = StepStatus.COMPLETED
                    step.completed_at = datetime.now()

                    yield step

                    # Адаптивное планирование следующих шагов
                    if (
                        self.config["enable_adaptive_planning"]
                        and i < len(session.steps) - 1
                    ):
                        await self._adapt_next_steps(session, i)

                    # Проверка достижения цели
                    if await self._is_research_complete(session, step):
                        logger.info(
                            "✅ Исследование завершено досрочно - цель достигнута"
                        )
                        break

                except Exception as e:
                    logger.error(f"❌ Ошибка выполнения шага {i+1}: {e}")
                    step.status = StepStatus.FAILED
                    step.error_message = str(e)
                    yield step
                    continue

            # Финальный синтез результатов
            session.final_result = await self._synthesize_final_result(session)
            session.status = ResearchStatus.COMPLETED
            session.completed_at = datetime.now()
            session.duration = (datetime.now() - start_time).total_seconds()

            self._update_metrics(session)

            logger.info(f"✅ Исследование завершено: {session.session_id}")

        except Exception as e:
            logger.error(f"❌ Критическая ошибка исследования: {e}")
            session.status = ResearchStatus.FAILED
            session.completed_at = datetime.now()
            raise

    async def _extract_research_goal(self, query: str) -> str:
        """Извлечение цели исследования из запроса"""
        system_prompt = """
        Проанализируй пользовательский запрос и сформулируй четкую цель исследования.
        Цель должна быть конкретной, измеримой и достижимой в рамках 5-7 шагов анализа.
        
        Ответь одним предложением, начинающимся с глагола действия.
        """

        try:
            response = await self.llm_service.generate_response(
                query=query, system_prompt=system_prompt, max_tokens=150
            )
            return response.strip()
        except Exception as e:
            logger.warning(f"Не удалось извлечь цель исследования: {e}")
            return f"Провести углубленный анализ запроса: {query}"

    async def _plan_research_steps(
        self, session: ResearchSession
    ) -> List[ResearchStep]:
        """Планирование шагов исследования"""
        planning_prompt = f"""
        Запрос пользователя: {session.original_query}
        Цель исследования: {session.research_goal}
        Максимум шагов: {session.max_steps}
        
        Спланируй оптимальную последовательность шагов для достижения цели.
        Каждый шаг должен логически следовать из предыдущего и приближать к цели.
        
        Доступные типы шагов:
        1. initial_analysis - первичный анализ запроса
        2. context_gathering - сбор контекстной информации
        3. deep_analysis - углубленный анализ конкретных аспектов
        4. synthesis - синтез информации из разных источников
        5. validation - проверка и валидация результатов
        6. final_summary - финальное обобщение
        
        Ответь в формате JSON списка шагов с полями: title, description, step_type, query.
        """

        try:
            response = await self.llm_service.generate_response(
                query=planning_prompt,
                system_prompt="Ты эксперт по планированию исследований. Создавай четкие, логичные планы.",
                max_tokens=800,
            )

            # Парсинг и создание шагов (упрощенная реализация)
            steps = []
            step_types = [
                ResearchStepType.INITIAL_ANALYSIS,
                ResearchStepType.CONTEXT_GATHERING,
                ResearchStepType.DEEP_ANALYSIS,
                ResearchStepType.SYNTHESIS,
                ResearchStepType.VALIDATION,
                ResearchStepType.FINAL_SUMMARY,
            ]

            for i, step_type in enumerate(step_types[: session.max_steps]):
                step = ResearchStep(
                    step_type=step_type,
                    title=f"Шаг {i+1}: {step_type.value.replace('_', ' ').title()}",
                    description=f"Выполнение {step_type.value} для запроса: {session.original_query}",
                    query=session.original_query,
                )
                steps.append(step)

            return steps

        except Exception as e:
            logger.warning(f"Ошибка планирования шагов: {e}")
            # Базовый план
            return [
                ResearchStep(
                    step_type=ResearchStepType.INITIAL_ANALYSIS,
                    title="Первичный анализ",
                    description="Анализ пользовательского запроса",
                    query=session.original_query,
                ),
                ResearchStep(
                    step_type=ResearchStepType.CONTEXT_GATHERING,
                    title="Сбор контекста",
                    description="Поиск релевантной информации",
                    query=session.original_query,
                ),
                ResearchStep(
                    step_type=ResearchStepType.FINAL_SUMMARY,
                    title="Финальное обобщение",
                    description="Подведение итогов исследования",
                    query=session.original_query,
                ),
            ]

    async def _execute_step(self, step: ResearchStep, session: ResearchSession):
        """Выполнение отдельного шага исследования"""
        step_start = datetime.now()

        try:
            # Поиск релевантной информации
            if step.step_type in [
                ResearchStepType.CONTEXT_GATHERING,
                ResearchStepType.DEEP_ANALYSIS,
            ]:
                search_service = await get_enhanced_vector_search_service()
                search_results = await search_service.enhanced_search(
                    query=step.query, limit=10, score_threshold=0.5
                )
                step.sources = [
                    {
                        "title": result.get("title", ""),
                        "content": result.get("content", "")[:500],
                        "source": result.get("source", ""),
                        "score": result.get("score", 0.0),
                    }
                    for result in search_results.get("results", [])
                ]

            # Генерация ответа для шага
            context = self._build_step_context(step, session)
            step_prompt = self._build_step_prompt(step, context)

            response = await self.llm_service.generate_response(
                query=step_prompt,
                system_prompt="Ты эксперт-исследователь. Проводи тщательный анализ и давай обоснованные выводы.",
                max_tokens=1000,
            )

            step.result = response
            step.confidence = self._calculate_step_confidence(step)
            step.duration = (datetime.now() - step_start).total_seconds()

            # Планирование следующих шагов
            if step.step_type != ResearchStepType.FINAL_SUMMARY:
                step.next_steps = await self._suggest_next_steps(step, session)

            logger.info(
                f"✅ Шаг выполнен: {step.title} (уверенность: {step.confidence:.2f})"
            )

        except Exception as e:
            logger.error(f"❌ Ошибка выполнения шага {step.title}: {e}")
            raise

    def _build_step_context(self, step: ResearchStep, session: ResearchSession) -> str:
        """Построение контекста для шага"""
        context_parts = [
            f"Исходный запрос: {session.original_query}",
            f"Цель исследования: {session.research_goal}",
            f"Текущий шаг: {step.title}",
        ]

        # Добавление результатов предыдущих шагов
        completed_steps = [s for s in session.steps if s.status == StepStatus.COMPLETED]
        if completed_steps:
            context_parts.append("Результаты предыдущих шагов:")
            for prev_step in completed_steps[-3:]:  # Последние 3 шага
                context_parts.append(
                    f"- {prev_step.title}: {prev_step.result[:200]}..."
                )

        # Добавление источников
        if step.sources:
            context_parts.append("Найденная информация:")
            for source in step.sources[:3]:  # Топ-3 источника
                context_parts.append(
                    f"- {source['title']}: {source['content'][:150]}..."
                )

        return "\n".join(context_parts)

    def _build_step_prompt(self, step: ResearchStep, context: str) -> str:
        """Построение промпта для шага"""
        step_instructions = {
            ResearchStepType.INITIAL_ANALYSIS: "Проведи первичный анализ запроса, определи ключевые аспекты и области для исследования.",
            ResearchStepType.CONTEXT_GATHERING: "Собери и проанализируй контекстную информацию из доступных источников.",
            ResearchStepType.DEEP_ANALYSIS: "Проведи углубленный анализ конкретных аспектов, используя найденную информацию.",
            ResearchStepType.SYNTHESIS: "Синтезируй информацию из разных источников, найди связи и закономерности.",
            ResearchStepType.VALIDATION: "Проверь и валидируй полученные результаты, оцени их достоверность.",
            ResearchStepType.FINAL_SUMMARY: "Подведи итоги исследования, дай окончательный ответ на запрос.",
        }

        instruction = step_instructions.get(
            step.step_type, "Выполни анализ в рамках текущего шага."
        )

        return f"""
{instruction}

Контекст:
{context}

Требования к ответу:
- Будь конкретным и обоснованным
- Используй найденную информацию
- Указывай источники при необходимости
- Формулируй четкие выводы
- Предлагай направления для дальнейшего исследования (если нужно)
"""

    def _calculate_step_confidence(self, step: ResearchStep) -> float:
        """Расчет уверенности в результатах шага"""
        confidence = 0.5  # Базовое значение

        # Учет наличия источников
        if step.sources:
            confidence += 0.2
            # Учет качества источников
            avg_score = sum(s.get("score", 0) for s in step.sources) / len(step.sources)
            confidence += avg_score * 0.2

        # Учет длины результата (более подробный = более уверенный)
        if len(step.result) > 500:
            confidence += 0.1

        return min(1.0, confidence)

    async def _suggest_next_steps(
        self, step: ResearchStep, session: ResearchSession
    ) -> List[str]:
        """Предложение следующих шагов"""
        try:
            prompt = f"""
            На основе результатов текущего шага: {step.result[:300]}
            
            Предложи 2-3 конкретных направления для дальнейшего исследования.
            Каждое направление должно быть сформулировано как actionable задача.
            """

            response = await self.llm_service.generate_response(
                query=prompt,
                system_prompt="Ты стратег исследования. Предлагай конкретные, выполнимые следующие шаги.",
                max_tokens=200,
            )

            # Простая обработка ответа
            suggestions = [
                s.strip()
                for s in response.split("\n")
                if s.strip() and not s.strip().startswith("-")
            ]
            return suggestions[:3]

        except Exception as e:
            logger.warning(f"Ошибка генерации предложений: {e}")
            return [
                "Продолжить углубленный анализ",
                "Проверить дополнительные источники",
            ]

    async def _adapt_next_steps(
        self, session: ResearchSession, current_step_index: int
    ):
        """Адаптивное планирование следующих шагов"""
        if current_step_index + 1 >= len(session.steps):
            return

        current_step = session.steps[current_step_index]

        # Если уверенность низкая, добавляем дополнительные шаги валидации
        if current_step.confidence < self.config["min_confidence_threshold"]:
            validation_step = ResearchStep(
                step_type=ResearchStepType.VALIDATION,
                title=f"Дополнительная валидация для шага {current_step_index + 1}",
                description=f"Проверка и уточнение результатов: {current_step.title}",
                query=current_step.query,
            )
            session.steps.insert(current_step_index + 1, validation_step)

    async def _is_research_complete(
        self, session: ResearchSession, last_step: ResearchStep
    ) -> bool:
        """Проверка завершенности исследования"""
        # Простая эвристика: если уверенность высокая и есть конкретный результат
        if last_step.confidence > 0.8 and len(last_step.result) > 200:
            return True

        # Если выполнили более 70% шагов с хорошими результатами
        completed_steps = [s for s in session.steps if s.status == StepStatus.COMPLETED]
        if len(completed_steps) >= session.max_steps * 0.7:
            avg_confidence = sum(s.confidence for s in completed_steps) / len(
                completed_steps
            )
            if avg_confidence > 0.7:
                return True

        return False

    async def _synthesize_final_result(self, session: ResearchSession) -> str:
        """Синтез финального результата исследования"""
        completed_steps = [s for s in session.steps if s.status == StepStatus.COMPLETED]

        if not completed_steps:
            return "Исследование не дало конкретных результатов."

        # Сбор всех результатов
        all_results = []
        all_sources = []

        for step in completed_steps:
            if step.result:
                all_results.append(f"{step.title}: {step.result}")
            all_sources.extend(step.sources)

        synthesis_prompt = f"""
        Исходный запрос: {session.original_query}
        Цель исследования: {session.research_goal}
        
        Результаты исследования по шагам:
        {chr(10).join(all_results)}
        
        Общее количество источников: {len(all_sources)}
        
        Синтезируй окончательный ответ на исходный запрос, используя все полученные данные.
        Ответ должен быть:
        - Полным и исчерпывающим
        - Структурированным
        - Содержать конкретные выводы
        - Ссылаться на источники информации
        """

        try:
            final_response = await self.llm_service.generate_response(
                query=synthesis_prompt,
                system_prompt="Ты эксперт-аналитик. Создавай исчерпывающие, структурированные ответы на основе проведенного исследования.",
                max_tokens=1500,
            )

            session.overall_confidence = sum(
                s.confidence for s in completed_steps
            ) / len(completed_steps)
            session.total_sources = len(all_sources)

            return final_response

        except Exception as e:
            logger.error(f"Ошибка синтеза результата: {e}")
            return f"Исследование завершено. Проанализировано {len(completed_steps)} шагов, найдено {len(all_sources)} источников."

    def _update_metrics(self, session: ResearchSession):
        """Обновление метрик движка"""
        if session.status == ResearchStatus.COMPLETED:
            self.metrics["completed_sessions"] += 1

        # Средние значения
        completed_sessions = self.metrics["completed_sessions"]
        if completed_sessions > 0:
            # Среднее количество шагов
            total_steps = sum(
                len(s.steps)
                for s in self.active_sessions.values()
                if s.status == ResearchStatus.COMPLETED
            )
            self.metrics["average_steps"] = total_steps / completed_sessions

            # Средняя длительность
            total_duration = sum(
                s.duration
                for s in self.active_sessions.values()
                if s.status == ResearchStatus.COMPLETED and s.duration > 0
            )
            self.metrics["average_duration"] = total_duration / completed_sessions

            # Процент успеха
            self.metrics["success_rate"] = (
                completed_sessions / self.metrics["total_sessions"]
            )

    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Получение статуса сессии"""
        session = self.active_sessions.get(session_id)
        if not session:
            return None

        return {
            "session_id": session.session_id,
            "status": session.status.value,
            "current_step": session.current_step,
            "total_steps": len(session.steps),
            "progress": session.current_step / max(len(session.steps), 1),
            "duration": session.duration,
            "overall_confidence": session.overall_confidence,
            "total_sources": session.total_sources,
        }

    async def cancel_research(self, session_id: str) -> bool:
        """Отмена исследования"""
        session = self.active_sessions.get(session_id)
        if not session:
            return False

        session.status = ResearchStatus.CANCELLED
        session.completed_at = datetime.now()

        logger.info(f"🚫 Исследование отменено: {session_id}")
        return True

    async def get_engine_status(self) -> Dict[str, Any]:
        """Получение статуса движка"""
        return {
            "engine_status": "active",
            "active_sessions": len(self.active_sessions),
            "metrics": self.metrics,
            "configuration": {
                "max_concurrent_sessions": self.config["max_concurrent_sessions"],
                "default_max_steps": self.config["default_max_steps"],
                "step_timeout": self.config["step_timeout"],
                "min_confidence_threshold": self.config["min_confidence_threshold"],
            },
            "last_updated": datetime.now().isoformat(),
        }


# Глобальный экземпляр
_deep_research_engine: Optional[DeepResearchEngine] = None


async def get_deep_research_engine() -> DeepResearchEngine:
    """Получение глобального экземпляра движка исследований"""
    global _deep_research_engine
    if _deep_research_engine is None:
        _deep_research_engine = DeepResearchEngine()
        logger.info("🔬 Deep Research Engine инициализирован")
    return _deep_research_engine
