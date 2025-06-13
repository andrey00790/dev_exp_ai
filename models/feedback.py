from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class FeedbackType(str, Enum):
    """Типы обратной связи."""
    LIKE = "like"                       # Положительная оценка (👍)
    DISLIKE = "dislike"                 # Отрицательная оценка (👎)
    REPORT = "report"                   # Жалоба на контент


class FeedbackContext(str, Enum):
    """Контекст обратной связи."""
    RFC_GENERATION = "rfc_generation"   # Оценка сгенерированного RFC
    SEARCH_RESULT = "search_result"     # Оценка результата поиска
    AI_QUESTION = "ai_question"         # Оценка вопроса от AI
    OVERALL_SESSION = "overall_session" # Общая оценка сессии


class FeedbackReason(str, Enum):
    """Причины негативной обратной связи."""
    INCORRECT_INFO = "incorrect_info"           # Неверная информация
    NOT_RELEVANT = "not_relevant"               # Не релевантно
    POOR_QUALITY = "poor_quality"               # Плохое качество
    INCOMPLETE = "incomplete"                   # Неполная информация
    UNCLEAR = "unclear"                         # Неясно написано
    TECHNICAL_ERROR = "technical_error"         # Техническая ошибка
    INAPPROPRIATE = "inappropriate"             # Неподходящий контент
    OTHER = "other"                            # Другое


class UserFeedback(BaseModel):
    """Обратная связь от пользователя."""
    id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None    # ID сессии генерации
    target_id: str                      # ID целевого объекта (RFC, результат поиска и т.д.)
    context: FeedbackContext
    feedback_type: FeedbackType
    rating: Optional[int] = Field(None, ge=1, le=5)  # Дополнительная оценка 1-5
    reason: Optional[FeedbackReason] = None           # Причина для негативной оценки
    comment: Optional[str] = Field(None, max_length=1000)  # Текстовый комментарий
    metadata: Dict[str, Any] = {}       # Дополнительные данные для анализа
    created_at: Optional[datetime] = None
    ip_address: Optional[str] = None    # Для защиты от спама
    user_agent: Optional[str] = None


class FeedbackRequest(BaseModel):
    """Запрос на отправку обратной связи."""
    target_id: str
    context: FeedbackContext
    feedback_type: FeedbackType
    rating: Optional[int] = Field(None, ge=1, le=5)
    reason: Optional[FeedbackReason] = None
    comment: Optional[str] = Field(None, max_length=1000)
    session_id: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Ответ на отправку обратной связи."""
    feedback_id: str
    message: str = "Спасибо за обратную связь!"
    points_earned: int = 0              # Очки пользователя за фидбек


class FeedbackStats(BaseModel):
    """Статистика обратной связи."""
    target_id: str
    total_feedback: int
    likes: int
    dislikes: int
    reports: int
    average_rating: Optional[float] = None
    like_percentage: float
    most_common_dislike_reason: Optional[FeedbackReason] = None


class FeedbackAnalytics(BaseModel):
    """Аналитика обратной связи для переобучения."""
    context: FeedbackContext
    total_items: int
    feedback_coverage: float            # Процент элементов с фидбеком
    positive_ratio: float               # Процент положительных оценок
    top_issues: List[FeedbackReason]    # Основные проблемы
    trends: Dict[str, Any] = {}         # Тренды по времени
    recommendations: List[str] = []     # Рекомендации по улучшению


class TrainingDataPoint(BaseModel):
    """Точка данных для переобучения модели."""
    id: Optional[str] = None
    input_data: Dict[str, Any]          # Входные данные (запрос, контекст)
    output_data: Dict[str, Any]         # Выходные данные (ответ системы)
    feedback_score: float               # Агрегированная оценка (-1 до 1)
    user_feedback: List[UserFeedback]   # Список обратной связи
    quality_score: Optional[float] = None     # Оценка качества для обучения
    created_at: Optional[datetime] = None
    is_used_for_training: bool = False


class RetrainingRequest(BaseModel):
    """Запрос на переобучение модели."""
    context: FeedbackContext
    min_feedback_count: int = Field(default=10, ge=1)  # Минимум фидбека для включения
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_reasons: List[FeedbackReason] = []


class RetrainingResponse(BaseModel):
    """Ответ на переобучение модели."""
    job_id: str
    status: str = "started"
    data_points_count: int
    estimated_duration_minutes: int
    message: str


class UserReputationScore(BaseModel):
    """Репутация пользователя для взвешивания фидбека."""
    user_id: str
    total_feedback_given: int
    helpful_feedback_count: int         # Фидбек, который был полезен
    reputation_score: float = Field(..., ge=0.0, le=10.0)
    expertise_areas: List[str] = []     # Области экспертизы
    last_updated: Optional[datetime] = None


class FeedbackModeration(BaseModel):
    """Модерация обратной связи."""
    feedback_id: str
    is_approved: bool = True
    moderation_reason: Optional[str] = None
    moderated_by: Optional[str] = None
    moderated_at: Optional[datetime] = None 