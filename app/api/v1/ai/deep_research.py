"""
Deep Research API - REST и WebSocket endpoints для многошагового исследования

Предоставляет API для запуска и управления углубленными исследованиями,
включая real-time обновления через WebSocket соединения.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import (APIRouter, Depends, HTTPException, WebSocket,
                     WebSocketDisconnect)
from pydantic import BaseModel, Field

from app.security.auth import get_current_user
from domain.core.deep_research_engine import (ResearchSession, ResearchStep,
                                              get_deep_research_engine)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deep-research", tags=["Deep Research"])

# =============================================================================
# PYDANTIC МОДЕЛИ
# =============================================================================


class StartResearchRequest(BaseModel):
    """Запрос на начало исследования"""

    query: str = Field(
        ..., min_length=10, max_length=1000, description="Исследовательский запрос"
    )
    max_steps: Optional[int] = Field(
        default=7, ge=3, le=10, description="Максимальное количество шагов"
    )
    user_context: Optional[Dict[str, Any]] = Field(
        default=None, description="Дополнительный контекст пользователя"
    )


class ResearchSessionResponse(BaseModel):
    """Ответ с информацией о сессии исследования"""

    session_id: str
    original_query: str
    research_goal: str
    status: str
    current_step: int
    max_steps: int
    created_at: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResearchStepResponse(BaseModel):
    """Ответ с информацией о шаге исследования"""

    step_id: str
    step_type: str
    title: str
    description: str
    result: str
    confidence: float
    duration: float
    sources_count: int
    status: str
    created_at: str
    completed_at: Optional[str] = None
    next_steps: List[str] = Field(default_factory=list)


class ResearchStatusResponse(BaseModel):
    """Ответ со статусом исследования"""

    session_id: str
    status: str
    current_step: int
    total_steps: int
    progress: float
    duration: float
    overall_confidence: float
    total_sources: int
    final_result: Optional[str] = None


class ResearchEngineStatusResponse(BaseModel):
    """Ответ со статусом движка исследований"""

    engine_status: str
    active_sessions: int
    metrics: Dict[str, Any]
    configuration: Dict[str, Any]
    last_updated: str


# =============================================================================
# УПРАВЛЕНИЕ WEBSOCKET СОЕДИНЕНИЯМИ
# =============================================================================


class WebSocketManager:
    """Менеджер WebSocket соединений для real-time обновлений"""

    def __init__(self):
        # session_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Подключение WebSocket к сессии исследования"""
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = []

        self.active_connections[session_id].append(websocket)
        logger.info(f"🔌 WebSocket подключен к сессии {session_id}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        """Отключение WebSocket"""
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)

            # Удаляем пустые списки
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

        logger.info(f"🔌 WebSocket отключен от сессии {session_id}")

    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any]):
        """Отправка сообщения всем подключенным к сессии WebSocket'ам"""
        if session_id not in self.active_connections:
            return

        disconnected = []
        for websocket in self.active_connections[session_id]:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Ошибка отправки WebSocket сообщения: {e}")
                disconnected.append(websocket)

        # Удаляем отключенные соединения
        for websocket in disconnected:
            self.disconnect(websocket, session_id)


# Глобальный менеджер WebSocket соединений
websocket_manager = WebSocketManager()

# =============================================================================
# REST API ENDPOINTS
# =============================================================================


@router.post("/start", response_model=ResearchSessionResponse)
async def start_research(
    request: StartResearchRequest, current_user: Dict = Depends(get_current_user)
):
    """
    Начать новое исследование

    Создает новую сессию исследования и возвращает её идентификатор.
    Для получения результатов в real-time используйте WebSocket соединение.
    """
    try:
        engine = await get_deep_research_engine()

        session = await engine.start_research(
            query=request.query,
            user_id=current_user.get("user_id", ""),
            max_steps=request.max_steps,
        )

        # Добавляем пользовательский контекст
        if request.user_context:
            session.metadata.update(request.user_context)

        logger.info(f"🔬 Создана сессия исследования: {session.session_id}")

        return ResearchSessionResponse(
            session_id=session.session_id,
            original_query=session.original_query,
            research_goal=session.research_goal,
            status=session.status.value,
            current_step=session.current_step,
            max_steps=session.max_steps,
            created_at=session.created_at.isoformat(),
            metadata=session.metadata,
        )

    except Exception as e:
        logger.error(f"❌ Ошибка создания исследования: {e}")
        raise HTTPException(
            status_code=500, detail=f"Не удалось создать исследование: {str(e)}"
        )


@router.post("/execute/{session_id}")
async def execute_research(
    session_id: str, current_user: Dict = Depends(get_current_user)
):
    """
    Запустить выполнение исследования

    Запускает исследование в фоновом режиме. Результаты будут переданы
    через WebSocket соединение в real-time.
    """
    try:
        engine = await get_deep_research_engine()

        # Проверяем существование сессии
        session_status = await engine.get_session_status(session_id)
        if not session_status:
            raise HTTPException(
                status_code=404, detail="Сессия исследования не найдена"
            )

        # Запускаем исследование в фоновой задаче
        asyncio.create_task(_execute_research_background(session_id))

        return {"message": "Исследование запущено", "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка запуска исследования: {e}")
        raise HTTPException(
            status_code=500, detail=f"Не удалось запустить исследование: {str(e)}"
        )


async def _execute_research_background(session_id: str):
    """Фоновое выполнение исследования с отправкой результатов через WebSocket"""
    try:
        engine = await get_deep_research_engine()

        # Отправляем уведомление о начале
        await websocket_manager.broadcast_to_session(
            session_id,
            {
                "type": "research_started",
                "session_id": session_id,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )

        # Выполняем исследование
        async for step in engine.execute_research(session_id):
            # Отправляем обновление по каждому шагу
            step_data = {
                "type": "step_completed",
                "session_id": session_id,
                "step": {
                    "step_id": step.step_id,
                    "step_type": step.step_type.value,
                    "title": step.title,
                    "description": step.description,
                    "result": step.result,
                    "confidence": step.confidence,
                    "duration": step.duration,
                    "sources_count": len(step.sources),
                    "status": step.status.value,
                    "next_steps": step.next_steps,
                },
                "timestamp": asyncio.get_event_loop().time(),
            }

            await websocket_manager.broadcast_to_session(session_id, step_data)

        # Получаем финальный статус
        final_status = await engine.get_session_status(session_id)

        # Отправляем уведомление о завершении
        await websocket_manager.broadcast_to_session(
            session_id,
            {
                "type": "research_completed",
                "session_id": session_id,
                "final_status": final_status,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )

        logger.info(f"✅ Исследование завершено: {session_id}")

    except Exception as e:
        logger.error(f"❌ Ошибка выполнения исследования {session_id}: {e}")

        # Отправляем уведомление об ошибке
        await websocket_manager.broadcast_to_session(
            session_id,
            {
                "type": "research_error",
                "session_id": session_id,
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time(),
            },
        )


@router.get("/status/{session_id}", response_model=ResearchStatusResponse)
async def get_research_status(
    session_id: str, current_user: Dict = Depends(get_current_user)
):
    """Получить статус исследования"""
    try:
        engine = await get_deep_research_engine()
        status = await engine.get_session_status(session_id)

        if not status:
            raise HTTPException(
                status_code=404, detail="Сессия исследования не найдена"
            )

        return ResearchStatusResponse(**status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса: {e}")
        raise HTTPException(
            status_code=500, detail=f"Не удалось получить статус: {str(e)}"
        )


@router.delete("/cancel/{session_id}")
async def cancel_research(
    session_id: str, current_user: Dict = Depends(get_current_user)
):
    """Отменить исследование"""
    try:
        engine = await get_deep_research_engine()
        success = await engine.cancel_research(session_id)

        if not success:
            raise HTTPException(
                status_code=404, detail="Сессия исследования не найдена"
            )

        # Уведомляем через WebSocket
        await websocket_manager.broadcast_to_session(
            session_id,
            {
                "type": "research_cancelled",
                "session_id": session_id,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )

        return {"message": "Исследование отменено", "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка отмены исследования: {e}")
        raise HTTPException(
            status_code=500, detail=f"Не удалось отменить исследование: {str(e)}"
        )


@router.get("/engine/status", response_model=ResearchEngineStatusResponse)
async def get_engine_status(current_user: Dict = Depends(get_current_user)):
    """Получить статус движка исследований"""
    try:
        engine = await get_deep_research_engine()
        status = await engine.get_engine_status()

        return ResearchEngineStatusResponse(**status)

    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса движка: {e}")
        raise HTTPException(
            status_code=500, detail=f"Не удалось получить статус движка: {str(e)}"
        )


@router.get("/sessions")
async def list_user_sessions(current_user: Dict = Depends(get_current_user)):
    """Получить список сессий пользователя"""
    try:
        engine = await get_deep_research_engine()
        user_id = current_user.get("user_id", "")

        user_sessions = []
        for session in engine.active_sessions.values():
            if session.user_id == user_id:
                user_sessions.append(
                    {
                        "session_id": session.session_id,
                        "original_query": session.original_query,
                        "status": session.status.value,
                        "created_at": session.created_at.isoformat(),
                        "duration": session.duration,
                    }
                )

        return {"sessions": user_sessions, "total": len(user_sessions)}

    except Exception as e:
        logger.error(f"❌ Ошибка получения списка сессий: {e}")
        raise HTTPException(
            status_code=500, detail=f"Не удалось получить список сессий: {str(e)}"
        )


# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================


@router.websocket("/ws/{session_id}")
async def websocket_research_updates(websocket: WebSocket, session_id: str):
    """
    WebSocket соединение для получения real-time обновлений исследования

    Подключитесь к этому endpoint для получения уведомлений о:
    - Начале исследования
    - Завершении каждого шага
    - Завершении исследования
    - Ошибках выполнения
    """
    await websocket_manager.connect(websocket, session_id)

    try:
        # Отправляем приветственное сообщение
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection_established",
                    "session_id": session_id,
                    "message": "Соединение установлено. Ожидаем обновления исследования...",
                    "timestamp": asyncio.get_event_loop().time(),
                }
            )
        )

        # Проверяем статус сессии
        engine = await get_deep_research_engine()
        status = await engine.get_session_status(session_id)

        if status:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "session_status",
                        "session_id": session_id,
                        "status": status,
                        "timestamp": asyncio.get_event_loop().time(),
                    }
                )
            )

        # Ожидаем сообщения от клиента или отключения
        while True:
            try:
                # Ожидаем ping от клиента для поддержания соединения
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "pong",
                                "timestamp": asyncio.get_event_loop().time(),
                            }
                        )
                    )

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.warning(f"Ошибка WebSocket сообщения: {e}")
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"❌ Ошибка WebSocket соединения: {e}")
    finally:
        websocket_manager.disconnect(websocket, session_id)


# =============================================================================
# ДОПОЛНИТЕЛЬНЫЕ УТИЛИТЫ
# =============================================================================


@router.get("/health")
async def health_check():
    """Health check для Deep Research API"""
    try:
        engine = await get_deep_research_engine()
        status = await engine.get_engine_status()

        return {
            "status": "healthy",
            "service": "deep_research_api",
            "engine_status": status["engine_status"],
            "active_sessions": status["active_sessions"],
            "timestamp": asyncio.get_event_loop().time(),
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")
