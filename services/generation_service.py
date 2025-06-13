from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from models.generation import (
    GenerateRequest, GenerationSession, AIQuestion, 
    UserAnswer, GeneratedRFC, QuestionType, TaskType, RFCSection
)

logger = logging.getLogger(__name__)


class GenerationServiceInterface(ABC):
    """Interface for RFC generation service."""
    
    @abstractmethod
    async def start_generation_session(self, request: GenerateRequest) -> GenerationSession:
        """Начинает новую сессию генерации RFC."""
        pass
    
    @abstractmethod
    async def generate_initial_questions(self, session: GenerationSession) -> List[AIQuestion]:
        """Генерирует первоначальные вопросы на основе запроса."""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[GenerationSession]:
        """Получает сессию по ID."""
        pass
    
    @abstractmethod
    async def save_answers(self, session_id: str, answers: List[UserAnswer]) -> bool:
        """Сохраняет ответы пользователя."""
        pass
    
    @abstractmethod
    async def is_ready_for_generation(self, session_id: str) -> bool:
        """Проверяет, достаточно ли информации для генерации RFC."""
        pass
    
    @abstractmethod
    async def generate_follow_up_questions(self, session_id: str) -> List[AIQuestion]:
        """Генерирует дополнительные вопросы."""
        pass
    
    @abstractmethod
    async def generate_rfc_document(self, session_id: str, additional_requirements: str = None) -> GeneratedRFC:
        """Генерирует финальный RFC документ."""
        pass
    
    @abstractmethod
    async def get_rfc(self, rfc_id: str) -> Optional[GeneratedRFC]:
        """Получает сгенерированный RFC по ID."""
        pass
    
    @abstractmethod
    async def cancel_session(self, session_id: str) -> bool:
        """Отменяет сессию генерации."""
        pass
    
    @abstractmethod
    async def create_training_data_point(self, session_id: str, rfc_id: str) -> None:
        """Создает точку данных для обучения."""
        pass


logger = logging.getLogger(__name__)


class MockGenerationService(GenerationServiceInterface):
    """Mock implementation for development."""
    
    def __init__(self):
        self._sessions: dict[str, GenerationSession] = {}
        self._rfcs: dict[str, GeneratedRFC] = {}
    
    async def start_generation_session(self, request: GenerateRequest) -> GenerationSession:
        """Начинает новую сессию генерации RFC."""
        session = GenerationSession(
            id=str(uuid.uuid4()),
            user_id=request.user_id,
            task_type=request.task_type,
            initial_request=request.initial_request,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self._sessions[session.id] = session
        return session
    
    async def generate_initial_questions(self, session: GenerationSession) -> List[AIQuestion]:
        """Генерирует первоначальные вопросы на основе запроса с помощью LLM."""
        
        try:
            # Используем LLM для генерации умных вопросов
            from services.llm_generation_service import LLMGenerationService
            llm_service = LLMGenerationService()
            
            llm_questions_data = await llm_service.generate_smart_questions(session)
            
            # Конвертируем в AIQuestion объекты
            questions = []
            for q_data in llm_questions_data:
                question = AIQuestion(
                    id=q_data["id"],
                    question=q_data["question"],
                    question_type=QuestionType(q_data["question_type"]),
                    context=q_data.get("context", ""),
                    is_required=q_data.get("is_required", True),
                    options=q_data.get("options", [])
                )
                questions.append(question)
            
            if questions:
                session.questions = questions
                session.current_question_index = 0
                self._sessions[session.id] = session
                return questions
                
        except Exception as e:
            # Fallback на статические вопросы
            import logging
            logging.warning(f"LLM question generation failed, using fallback: {e}")
        
        # Fallback на статические вопросы
        questions = []
        
        if session.task_type == TaskType.NEW_FEATURE:
            questions = [
                AIQuestion(
                    id="q1",
                    question="Какова основная бизнес-цель этого функционала?",
                    question_type=QuestionType.TEXT,
                    context="Это поможет мне понять приоритеты и критерии успеха."
                ),
                AIQuestion(
                    id="q2", 
                    question="Кто является целевой аудиторией?",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    options=["Внутренние пользователи", "Внешние клиенты", "Разработчики", "Админы", "Другое"]
                ),
                AIQuestion(
                    id="q3",
                    question="Какой ожидаемый объем нагрузки?",
                    question_type=QuestionType.CHOICE,
                    options=["Низкая (< 1K пользователей)", "Средняя (1K-10K)", "Высокая (10K-100K)", "Очень высокая (> 100K)"]
                )
            ]
        elif session.task_type == TaskType.MODIFY_EXISTING:
            questions = [
                AIQuestion(
                    id="q1",
                    question="Опишите текущую реализацию системы",
                    question_type=QuestionType.TEXT,
                    context="Мне нужно понимать исходное состояние для планирования изменений."
                ),
                AIQuestion(
                    id="q2",
                    question="Какие конкретные проблемы нужно решить?",
                    question_type=QuestionType.TEXT
                ),
                AIQuestion(
                    id="q3",
                    question="Есть ли ограничения по обратной совместимости?",
                    question_type=QuestionType.BOOLEAN
                )
            ]
        else:  # ANALYZE_CURRENT
            questions = [
                AIQuestion(
                    id="q1",
                    question="Какие метрики производительности вас беспокоят?",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    options=["Время отклика", "Пропускная способность", "Потребление памяти", "CPU нагрузка", "Ошибки"]
                ),
                AIQuestion(
                    id="q2",
                    question="Предоставьте текущие метрики системы",
                    question_type=QuestionType.TEXT,
                    placeholder="Например: RPS: 1000, время отклика: 200мс, CPU: 80%"
                )
            ]
        
        session.questions = questions
        session.current_question_index = 0
        self._sessions[session.id] = session
        
        return questions
    
    async def get_session(self, session_id: str) -> Optional[GenerationSession]:
        """Получает сессию по ID."""
        return self._sessions.get(session_id)
    
    async def save_answers(self, session_id: str, answers: List[UserAnswer]) -> bool:
        """Сохраняет ответы пользователя."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        session.answers.extend(answers)
        session.updated_at = datetime.now()
        self._sessions[session_id] = session
        return True
    
    async def is_ready_for_generation(self, session_id: str) -> bool:
        """Проверяет, достаточно ли информации для генерации RFC."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        # Простая логика: если есть ответы на все вопросы
        answered_question_ids = {answer.question_id for answer in session.answers}
        required_question_ids = {q.id for q in session.questions if q.is_required}
        
        return required_question_ids.issubset(answered_question_ids)
    
    async def generate_follow_up_questions(self, session_id: str) -> List[AIQuestion]:
        """Генерирует дополнительные вопросы."""
        # В mock версии просто возвращаем пустой список
        # В реальной реализации здесь будет логика AI для генерации вопросов
        return []
    
    async def generate_rfc_document(self, session_id: str, additional_requirements: str = None) -> GeneratedRFC:
        """Генерирует финальный RFC документ на основе профессиональных шаблонов."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Используем template service для генерации профессионального RFC
        from services.template_service import get_template_service
        template_service = get_template_service()
        
        # Генерируем полный RFC контент с использованием шаблона
        try:
            rfc_content = await template_service.generate_rfc_content(session)
            
            # Извлекаем заголовок из сгенерированного контента
            lines = rfc_content.split('\n')
            title_line = next((line for line in lines if line.startswith('title:')), None)
            title = title_line.split('title: ')[1] if title_line else f"RFC: {session.initial_request[:50]}..."
            
            # Создаем секции из markdown контента
            sections = await self._parse_rfc_sections(rfc_content)
            
        except Exception as e:
            # Fallback на простую генерацию
            rfc_content = f"""# RFC: {session.initial_request[:50]}...

## Summary
{session.initial_request}

## Implementation
Детальная реализация будет определена на основе технического анализа и ответов пользователя.
"""
            title = f"RFC: {session.initial_request[:50]}..."
            sections = [
                RFCSection(
                    title="Summary",
                    content=session.initial_request,
                    order=1
                )
            ]
        
        rfc = GeneratedRFC(
            id=str(uuid.uuid4()),
            session_id=session_id,
            title=title,
            summary="Профессиональный RFC документ, сгенерированный по лучшим практикам GitHub, Stripe и других компаний.",
            sections=sections,
            full_content=rfc_content,  # Полный markdown контент
            metadata={
                "task_type": session.task_type,
                "questions_answered": len(session.answers),
                "generation_date": datetime.now().isoformat(),
                "template_used": "rfc_template.md",
                "additional_requirements": additional_requirements
            },
            sources_used=["User Input", "Best Practices Templates", "Industry Standards"],
            created_at=datetime.now()
        )
        
        self._rfcs[rfc.id] = rfc
        session.is_complete = True
        self._sessions[session_id] = session
        
        # 🧠 Интеграция с Learning Pipeline для сбора фидбека и переобучения
        try:
            from services.learning_pipeline_service import get_learning_service
            learning_service = get_learning_service()
            
            # Запускаем процесс сбора фидбека и подготовки к переобучению
            learning_result = await learning_service.process_rfc_completion(rfc, session)
            
            # Добавляем информацию о learning в метаданные RFC
            rfc.metadata["learning_pipeline"] = learning_result
            
            logger.info(f"Learning pipeline activated for RFC {rfc.id}: {learning_result['examples_collected']} examples collected")
            
        except Exception as e:
            logger.warning(f"Learning pipeline failed for RFC {rfc.id}: {e}")
            # RFC генерация продолжается даже если learning pipeline не сработал
        
        return rfc
    
    async def _parse_rfc_sections(self, rfc_content: str) -> List[RFCSection]:
        """Парсит markdown контент RFC в секции."""
        
        sections = []
        lines = rfc_content.split('\n')
        current_section = None
        current_content = []
        order = 0
        
        for line in lines:
            # Ищем заголовки секций (## Header)
            if line.startswith('## ') and not line.startswith('###'):
                # Сохраняем предыдущую секцию
                if current_section:
                    sections.append(RFCSection(
                        title=current_section,
                        content='\n'.join(current_content).strip(),
                        order=order
                    ))
                    current_content = []
                    order += 1
                
                # Начинаем новую секцию
                current_section = line[3:].strip()
            elif current_section:
                current_content.append(line)
        
        # Добавляем последнюю секцию
        if current_section:
            sections.append(RFCSection(
                title=current_section,
                content='\n'.join(current_content).strip(),
                order=order
            ))
        
        return sections
    
    async def get_rfc(self, rfc_id: str) -> Optional[GeneratedRFC]:
        """Получает сгенерированный RFC по ID."""
        return self._rfcs.get(rfc_id)
    
    async def cancel_session(self, session_id: str) -> bool:
        """Отменяет сессию генерации."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    async def create_training_data_point(self, session_id: str, rfc_id: str) -> None:
        """Создает точку данных для обучения."""
        # В реальной реализации здесь будет создание обучающих данных
        # для улучшения модели генерации RFC
        pass


# Global instance
_generation_service_instance = None

def get_generation_service() -> GenerationServiceInterface:
    """Dependency injection для generation service."""
    global _generation_service_instance
    if _generation_service_instance is None:
        _generation_service_instance = MockGenerationService()
    return _generation_service_instance 