from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class TaskType(str, Enum):
    """Типы задач для генерации."""
    NEW_FEATURE = "new_feature"        # Проектирование нового функционала
    MODIFY_EXISTING = "modify_existing" # Изменение существующего
    ANALYZE_CURRENT = "analyze_current" # Анализ текущего функционала


class QuestionType(str, Enum):
    """Типы вопросов от AI."""
    TEXT = "text"                      # Текстовый ответ
    CHOICE = "choice"                  # Выбор из вариантов
    MULTIPLE_CHOICE = "multiple_choice" # Множественный выбор
    BOOLEAN = "boolean"                # Да/Нет
    NUMBER = "number"                  # Числовое значение


class AIQuestion(BaseModel):
    """Вопрос от AI к пользователю."""
    id: str
    question: str
    question_type: QuestionType
    options: Optional[List[str]] = None  # Для choice/multiple_choice
    is_required: bool = True
    context: Optional[str] = None        # Дополнительный контекст
    placeholder: Optional[str] = None    # Плейсхолдер для UI


class UserAnswer(BaseModel):
    """Ответ пользователя на вопрос."""
    question_id: str
    answer: Any                          # Может быть str, int, bool, List[str]
    confidence: Optional[float] = None   # Уверенность пользователя (0-1)


class GenerationSession(BaseModel):
    """Сессия генерации документа."""
    id: Optional[str] = None
    user_id: Optional[str] = None
    task_type: TaskType
    initial_request: str                 # Первоначальный запрос пользователя
    questions: List[AIQuestion] = []     # Вопросы от AI
    answers: List[UserAnswer] = []       # Ответы пользователя
    current_question_index: int = 0      # Текущий вопрос
    is_complete: bool = False           # Завершена ли сессия
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RFCSection(BaseModel):
    """Секция RFC документа."""
    title: str
    content: str
    order: int
    subsections: List['RFCSection'] = []


class GeneratedRFC(BaseModel):
    """Сгенерированный RFC документ."""
    id: Optional[str] = None
    session_id: str
    title: str
    summary: str                         # Краткое описание
    sections: List[RFCSection]
    full_content: Optional[str] = None   # Полный markdown контент RFC
    metadata: Dict[str, Any] = {}        # Авторы, версия, теги
    sources_used: List[str] = []         # Источники данных, использованные для генерации
    created_at: Optional[datetime] = None


class GenerateRequest(BaseModel):
    """Запрос на генерацию."""
    task_type: TaskType
    initial_request: str = Field(..., min_length=10, max_length=2000)
    context: Optional[str] = None        # Дополнительный контекст
    user_id: Optional[str] = None
    search_sources: List[str] = []       # Источники для поиска релевантной информации


class GenerateResponse(BaseModel):
    """Ответ на запрос генерации."""
    session_id: str
    questions: List[AIQuestion] = []     # Следующие вопросы
    is_ready_to_generate: bool = False   # Готов ли генерировать документ
    message: Optional[str] = None        # Сообщение для пользователя


class AnswerRequest(BaseModel):
    """Запрос с ответом на вопрос."""
    session_id: str
    answers: List[UserAnswer]


class FinalGenerationRequest(BaseModel):
    """Запрос на финальную генерацию RFC."""
    session_id: str
    additional_requirements: Optional[str] = None


class FinalGenerationResponse(BaseModel):
    """Ответ с готовым RFC документом."""
    rfc: GeneratedRFC
    message: str = "RFC документ успешно сгенерирован"


# Обновляем рекурсивные модели
RFCSection.model_rebuild() 