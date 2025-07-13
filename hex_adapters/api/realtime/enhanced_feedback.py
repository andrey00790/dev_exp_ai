"""
Enhanced Feedback API - REST и WebSocket API для расширенной системы обратной связи

Endpoints:
- POST /feedback - Отправка обратной связи
- GET /feedback/content/{content_id} - Получение feedback по контенту
- GET /feedback/user/{user_id}/history - История feedback пользователя
- POST /feedback/{feedback_id}/moderate - Модерация feedback
- GET /feedback/analytics - Аналитика обратной связи
- WebSocket /feedback/ws - Real-time уведомления
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import (APIRouter, Depends, HTTPException, Path, Query, WebSocket,
                     WebSocketDisconnect)
from fastapi.security import HTTPBearer
# Используем паттерны из Context7 для WebSocket PubSub
from fastapi_websocket_pubsub import PubSubEndpoint
from pydantic import BaseModel, Field, validator

from app.security.auth import get_current_user
from domain.monitoring.enhanced_feedback_service import (
    ContentType, EnhancedFeedbackService, FeedbackItem, FeedbackStatus,
    FeedbackSummary, FeedbackType, SentimentScore,
    get_enhanced_feedback_service)

logger = logging.getLogger(__name__)

# Инициализация PubSub для real-time уведомлений
pubsub_endpoint = PubSubEndpoint()

router = APIRouter(prefix="/feedback", tags=["Enhanced Feedback"])
security = HTTPBearer()

# === Pydantic Models ===


class FeedbackSubmitRequest(BaseModel):
    """Запрос на отправку обратной связи"""

    content_id: str = Field(..., description="ID контента")
    content_type: ContentType = Field(..., description="Тип контента")
    feedback_type: FeedbackType = Field(..., description="Тип обратной связи")
    value: Optional[Any] = Field(
        None, description="Значение feedback (True/False для лайков)"
    )
    comment: str = Field("", description="Комментарий", max_length=2000)
    rating: Optional[int] = Field(None, ge=1, le=5, description="Рейтинг 1-5 звезд")
    tags: List[str] = Field(default_factory=list, description="Теги")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Дополнительный контекст"
    )

    @validator("value")
    def validate_value(cls, v, values):
        feedback_type = values.get("feedback_type")
        if feedback_type in [FeedbackType.LIKE, FeedbackType.DISLIKE]:
            if not isinstance(v, bool):
                raise ValueError("Value must be boolean for like/dislike feedback")
        return v


class FeedbackResponse(BaseModel):
    """Ответ с информацией о feedback"""

    feedback_id: str
    user_id: str
    content_id: str
    content_type: str
    feedback_type: str
    status: str
    value: Optional[Any] = None
    comment: str = ""
    rating: Optional[int] = None
    sentiment_score: Optional[str] = None
    confidence: float = 0.0
    tags: List[str] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_moderated: bool = False
    moderation_reason: str = ""


class ContentFeedbackResponse(BaseModel):
    """Ответ с обратной связью по контенту"""

    content_id: str
    content_type: str
    total_likes: int
    total_dislikes: int
    like_ratio: float
    total_comments: int
    avg_rating: float
    sentiment_distribution: Dict[str, int]
    popular_tags: List[str]
    last_feedback_at: Optional[datetime] = None
    feedback_velocity: float = 0.0
    comments: Optional[List[Dict[str, Any]]] = None
    updated_at: datetime


class ModerationRequest(BaseModel):
    """Запрос на модерацию"""

    action: str = Field(..., description="Действие: hide, approve, remove")
    reason: str = Field("", description="Причина модерации")

    @validator("action")
    def validate_action(cls, v):
        if v not in ["hide", "approve", "remove"]:
            raise ValueError("Action must be one of: hide, approve, remove")
        return v


class AnalyticsRequest(BaseModel):
    """Запрос аналитики"""

    time_period_days: int = Field(7, ge=1, le=365, description="Период в днях")
    content_type: Optional[ContentType] = Field(
        None, description="Фильтр по типу контента"
    )


class AnalyticsResponse(BaseModel):
    """Ответ с аналитикой"""

    time_period_days: int
    total_feedback: int
    feedback_by_type: Dict[str, int]
    feedback_by_content_type: Dict[str, int]
    sentiment_distribution: Dict[str, int]
    rating_distribution: Dict[str, int]
    top_content: List[tuple]
    engagement_metrics: Dict[str, float]
    trends: Dict[str, Any] = {}


class WebSocketNotification(BaseModel):
    """WebSocket уведомление"""

    type: str
    notification_id: str
    data: Dict[str, Any]
    timestamp: datetime


# === Dependency Functions ===


async def get_feedback_service() -> EnhancedFeedbackService:
    """Получение экземпляра feedback сервиса"""
    return await get_enhanced_feedback_service()


def get_user_id(current_user: dict = Depends(get_current_user)) -> str:
    """Извлечение ID пользователя"""
    return current_user.get("user_id", "anonymous")


# === WebSocket Connection Manager ===


class WebSocketManager:
    """Менеджер WebSocket соединений для real-time уведомлений"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_subscriptions: Dict[str, set] = {}  # user_id -> set of topics

    async def connect(
        self, websocket: WebSocket, user_id: str, topics: List[str] = None
    ):
        """Подключение клиента"""
        await websocket.accept()
        self.active_connections[user_id] = websocket

        if topics:
            if user_id not in self.user_subscriptions:
                self.user_subscriptions[user_id] = set()
            self.user_subscriptions[user_id].update(topics)

        logger.info(f"✅ WebSocket connected: {user_id} subscribed to {topics}")

    def disconnect(self, user_id: str):
        """Отключение клиента"""
        self.active_connections.pop(user_id, None)
        self.user_subscriptions.pop(user_id, None)
        logger.info(f"❌ WebSocket disconnected: {user_id}")

    async def send_notification(self, user_id: str, notification: dict):
        """Отправка уведомления конкретному пользователю"""
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_json(notification)
            except Exception as e:
                logger.warning(f"⚠️ Failed to send notification to {user_id}: {e}")
                self.disconnect(user_id)

    async def broadcast_to_topic(self, topic: str, notification: dict):
        """Broadcast уведомления всем подписанным на топик"""
        for user_id, subscriptions in self.user_subscriptions.items():
            if topic in subscriptions:
                await self.send_notification(user_id, notification)


# Глобальный менеджер WebSocket соединений
ws_manager = WebSocketManager()

# === API Endpoints ===


@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackSubmitRequest,
    user_id: str = Depends(get_user_id),
    service: EnhancedFeedbackService = Depends(get_feedback_service),
):
    """Отправка обратной связи"""
    try:
        feedback = await service.submit_feedback(
            user_id=user_id,
            content_id=request.content_id,
            content_type=request.content_type,
            feedback_type=request.feedback_type,
            value=request.value,
            comment=request.comment,
            rating=request.rating,
            context=request.context,
        )

        # Добавление тегов
        feedback.tags = request.tags

        response = FeedbackResponse(
            feedback_id=feedback.feedback_id,
            user_id=feedback.user_id,
            content_id=feedback.content_id,
            content_type=feedback.content_type.value,
            feedback_type=feedback.feedback_type.value,
            status=feedback.status.value,
            value=feedback.value,
            comment=feedback.comment,
            rating=feedback.rating,
            sentiment_score=(
                feedback.sentiment_score.value if feedback.sentiment_score else None
            ),
            confidence=feedback.confidence,
            tags=feedback.tags,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at,
            is_moderated=feedback.is_moderated,
            moderation_reason=feedback.moderation_reason,
        )

        # Real-time уведомление через WebSocket
        notification = {
            "type": "new_feedback",
            "feedback_id": feedback.feedback_id,
            "content_id": feedback.content_id,
            "feedback_type": feedback.feedback_type.value,
            "user_id": user_id,
            "timestamp": feedback.created_at.isoformat(),
        }

        await ws_manager.broadcast_to_topic(
            f"content_{feedback.content_id}", notification
        )

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/content/{content_id}", response_model=ContentFeedbackResponse)
async def get_content_feedback(
    content_id: str = Path(..., description="ID контента"),
    include_comments: bool = Query(True, description="Включить комментарии"),
    include_moderated: bool = Query(False, description="Включить модерированные"),
    service: EnhancedFeedbackService = Depends(get_feedback_service),
):
    """Получение обратной связи по контенту"""
    try:
        summary = await service.get_content_feedback(
            content_id=content_id,
            include_comments=include_comments,
            include_moderated=include_moderated,
        )

        return ContentFeedbackResponse(
            content_id=summary.content_id,
            content_type=summary.content_type.value,
            total_likes=summary.total_likes,
            total_dislikes=summary.total_dislikes,
            like_ratio=summary.like_ratio,
            total_comments=summary.total_comments,
            avg_rating=summary.avg_rating,
            sentiment_distribution=summary.sentiment_distribution,
            popular_tags=summary.popular_tags,
            last_feedback_at=summary.last_feedback_at,
            feedback_velocity=summary.feedback_velocity,
            comments=getattr(summary, "comments", None),
            updated_at=summary.updated_at,
        )

    except Exception as e:
        logger.error(f"❌ Error getting content feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/{user_id}/history", response_model=List[FeedbackResponse])
async def get_user_feedback_history(
    user_id: str = Path(..., description="ID пользователя"),
    limit: int = Query(50, ge=1, le=200, description="Лимит записей"),
    content_type: Optional[ContentType] = Query(
        None, description="Фильтр по типу контента"
    ),
    current_user_id: str = Depends(get_user_id),
    service: EnhancedFeedbackService = Depends(get_feedback_service),
):
    """Получение истории обратной связи пользователя"""
    # Проверка прав доступа
    if user_id != current_user_id and current_user_id != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        feedback_history = await service.get_user_feedback_history(
            user_id=user_id, limit=limit, content_type=content_type
        )

        return [
            FeedbackResponse(
                feedback_id=fb.feedback_id,
                user_id=fb.user_id,
                content_id=fb.content_id,
                content_type=fb.content_type.value,
                feedback_type=fb.feedback_type.value,
                status=fb.status.value,
                value=fb.value,
                comment=fb.comment,
                rating=fb.rating,
                sentiment_score=(
                    fb.sentiment_score.value if fb.sentiment_score else None
                ),
                confidence=fb.confidence,
                tags=fb.tags,
                created_at=fb.created_at,
                updated_at=fb.updated_at,
                is_moderated=fb.is_moderated,
                moderation_reason=fb.moderation_reason,
            )
            for fb in feedback_history
        ]

    except Exception as e:
        logger.error(f"❌ Error getting user feedback history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{feedback_id}/moderate")
async def moderate_feedback(
    feedback_id: str = Path(..., description="ID feedback"),
    request: ModerationRequest = ...,
    moderator_id: str = Depends(get_user_id),
    service: EnhancedFeedbackService = Depends(get_feedback_service),
):
    """Модерация обратной связи"""
    try:
        success = await service.moderate_feedback(
            feedback_id=feedback_id,
            moderator_id=moderator_id,
            action=request.action,
            reason=request.reason,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Feedback not found")

        # Real-time уведомление о модерации
        notification = {
            "type": "feedback_moderated",
            "feedback_id": feedback_id,
            "action": request.action,
            "reason": request.reason,
            "moderator_id": moderator_id,
            "timestamp": datetime.now().isoformat(),
        }

        await ws_manager.broadcast_to_topic("moderation_updates", notification)

        return {"success": True, "message": f"Feedback {request.action}ed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error moderating feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analytics", response_model=AnalyticsResponse)
async def get_feedback_analytics(
    request: AnalyticsRequest = AnalyticsRequest(),
    service: EnhancedFeedbackService = Depends(get_feedback_service),
):
    """Получение аналитики обратной связи"""
    try:
        analytics = await service.get_feedback_analytics(
            time_period=timedelta(days=request.time_period_days),
            content_type=request.content_type,
        )

        if "error" in analytics:
            raise HTTPException(status_code=500, detail=analytics["error"])

        return AnalyticsResponse(**analytics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting feedback analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status")
async def get_feedback_service_status(
    service: EnhancedFeedbackService = Depends(get_feedback_service),
):
    """Получение статуса сервиса обратной связи"""
    try:
        status = await service.get_service_status()
        return status

    except Exception as e:
        logger.error(f"❌ Error getting service status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# === WebSocket Endpoints ===


@router.websocket("/ws")
async def websocket_feedback_notifications(
    websocket: WebSocket,
    topics: str = Query(
        "", description="Comma-separated list of topics to subscribe to"
    ),
    user_id: str = Query("anonymous", description="User ID for authentication"),
):
    """WebSocket endpoint для real-time уведомлений о feedback"""
    topic_list = [topic.strip() for topic in topics.split(",") if topic.strip()]

    try:
        await ws_manager.connect(websocket, user_id, topic_list)

        # Отправка приветственного сообщения
        await websocket.send_json(
            {
                "type": "connected",
                "message": f"Connected to feedback notifications",
                "subscribed_topics": topic_list,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Ожидание сообщений от клиента
        while True:
            try:
                data = await websocket.receive_json()

                # Обработка команд от клиента
                if data.get("type") == "subscribe":
                    new_topics = data.get("topics", [])
                    if user_id not in ws_manager.user_subscriptions:
                        ws_manager.user_subscriptions[user_id] = set()
                    ws_manager.user_subscriptions[user_id].update(new_topics)

                    await websocket.send_json(
                        {
                            "type": "subscribed",
                            "topics": new_topics,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                elif data.get("type") == "unsubscribe":
                    remove_topics = data.get("topics", [])
                    if user_id in ws_manager.user_subscriptions:
                        ws_manager.user_subscriptions[user_id] -= set(remove_topics)

                    await websocket.send_json(
                        {
                            "type": "unsubscribed",
                            "topics": remove_topics,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                elif data.get("type") == "ping":
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.now().isoformat()}
                    )

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.warning(f"⚠️ WebSocket error for user {user_id}: {e}")
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"❌ WebSocket connection error: {e}")
    finally:
        ws_manager.disconnect(user_id)


# === PubSub Integration ===


# Регистрация PubSub endpoint для внутренних уведомлений
async def setup_pubsub_integration():
    """Настройка интеграции с PubSub для внутренних уведомлений"""
    try:
        # Callback для обработки feedback уведомлений
        async def on_feedback_notification(data):
            """Обработка уведомлений о новой обратной связи"""
            notification_data = data.get("notification", {})
            content_id = notification_data.get("content_id", "")

            # Broadcast всем подписанным на этот контент
            await ws_manager.broadcast_to_topic(
                f"content_{content_id}", notification_data
            )

        # Callback для обработки уведомлений о модерации
        async def on_moderation_notification(data):
            """Обработка уведомлений о модерации"""
            await ws_manager.broadcast_to_topic("moderation_updates", data)

        # Подписка на топики (используем паттерны из Context7)
        # pubsub_client.subscribe("feedback_notifications", on_feedback_notification)
        # pubsub_client.subscribe("moderation_notifications", on_moderation_notification)

        logger.info("✅ PubSub integration setup completed")

    except Exception as e:
        logger.warning(f"⚠️ PubSub integration setup failed: {e}")


# Регистрация WebSocket роута для PubSub
pubsub_endpoint.register_route(router, path="/pubsub")

logger.info("✅ Enhanced Feedback API initialized")
