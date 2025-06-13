from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
import uuid
import time
from datetime import datetime

from models.generation import (
    GenerateRequest, GenerateResponse, AnswerRequest, 
    FinalGenerationRequest, FinalGenerationResponse,
    GenerationSession, AIQuestion, QuestionType, TaskType,
    RFCSection, GeneratedRFC
)
from models.base import BaseResponse
from services.generation_service import GenerationServiceInterface, get_generation_service

router = APIRouter()


@router.post(
    "/generate",
    response_model=GenerateResponse,
    summary="Start RFC Generation",
    description="Инициирует процесс генерации RFC документа с интерактивными вопросами"
)
async def start_generation(
    request: GenerateRequest,
    service: GenerationServiceInterface = Depends(get_generation_service)
) -> GenerateResponse:
    """
    Начинает процесс генерации RFC документа.
    
    AI анализирует запрос и задает наводящие вопросы для получения
    полной информации, необходимой для создания качественного RFC.
    """
    try:
        session = await service.start_generation_session(request)
        questions = await service.generate_initial_questions(session)
        
        return GenerateResponse(
            session_id=session.id,
            questions=questions,
            is_ready_to_generate=False,
            message="Отлично! Для создания качественного RFC документа мне нужно задать несколько вопросов."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при инициализации генерации: {str(e)}"
        )


@router.post(
    "/generate/answer",
    response_model=GenerateResponse,
    summary="Answer AI Questions",
    description="Отправляет ответы на вопросы AI и получает следующие вопросы или готовность к генерации"
)
async def answer_questions(
    request: AnswerRequest,
    service: GenerationServiceInterface = Depends(get_generation_service)
) -> GenerateResponse:
    """
    Обрабатывает ответы пользователя на вопросы AI.
    
    Возвращает либо следующие вопросы, либо сигнал о готовности
    к генерации финального RFC документа.
    """
    try:
        session = await service.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия генерации не найдена"
            )
        
        # Сохраняем ответы
        await service.save_answers(session.id, request.answers)
        
        # Проверяем, достаточно ли информации
        is_ready = await service.is_ready_for_generation(session.id)
        
        if is_ready:
            return GenerateResponse(
                session_id=session.id,
                questions=[],
                is_ready_to_generate=True,
                message="Отлично! У меня есть вся необходимая информация для создания RFC документа."
            )
        else:
            # Генерируем следующие вопросы
            next_questions = await service.generate_follow_up_questions(session.id)
            return GenerateResponse(
                session_id=session.id,
                questions=next_questions,
                is_ready_to_generate=False,
                message="Спасибо за ответы! У меня есть еще несколько вопросов."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обработке ответов: {str(e)}"
        )


@router.post(
    "/generate/finalize",
    response_model=FinalGenerationResponse,
    summary="Generate Final RFC",
    description="Генерирует финальный RFC документ на основе собранной информации"
)
async def generate_final_rfc(
    request: FinalGenerationRequest,
    background_tasks: BackgroundTasks,
    service: GenerationServiceInterface = Depends(get_generation_service)
) -> FinalGenerationResponse:
    """
    Генерирует финальный RFC документ.
    
    Использует лучшие мировые практики от Google, Uber, Stripe, AWS, 
    Netflix, Facebook, Cloudflare для создания профессионального RFC.
    """
    try:
        session = await service.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия генерации не найдена"
            )
        
        if not await service.is_ready_for_generation(session.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Недостаточно информации для генерации RFC. Ответьте на все вопросы."
            )
        
        # Генерируем RFC документ
        rfc = await service.generate_rfc_document(
            session.id, 
            request.additional_requirements
        )
        
        # Асинхронно создаем обучающие данные
        background_tasks.add_task(
            service.create_training_data_point,
            session.id,
            rfc.id
        )
        
        return FinalGenerationResponse(
            rfc=rfc,
            message="RFC документ успешно сгенерирован! Вы можете оставить обратную связь для улучшения качества."
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации RFC: {str(e)}"
        )


@router.get(
    "/generate/session/{session_id}",
    response_model=GenerationSession,
    summary="Get Generation Session",
    description="Получает информацию о сессии генерации"
)
async def get_generation_session(
    session_id: str,
    service: GenerationServiceInterface = Depends(get_generation_service)
) -> GenerationSession:
    """Получает детали сессии генерации."""
    try:
        session = await service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия генерации не найдена"
            )
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении сессии: {str(e)}"
        )


@router.get(
    "/generate/rfc/{rfc_id}",
    response_model=GeneratedRFC,
    summary="Get Generated RFC",
    description="Получает сгенерированный RFC документ по ID"
)
async def get_generated_rfc(
    rfc_id: str,
    service: GenerationServiceInterface = Depends(get_generation_service)
) -> GeneratedRFC:
    """Получает сгенерированный RFC документ."""
    try:
        rfc = await service.get_rfc(rfc_id)
        if not rfc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFC документ не найден"
            )
        return rfc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении RFC: {str(e)}"
        )


@router.delete(
    "/generate/session/{session_id}",
    response_model=BaseResponse,
    summary="Cancel Generation Session",
    description="Отменяет сессию генерации"
)
async def cancel_generation_session(
    session_id: str,
    service: GenerationServiceInterface = Depends(get_generation_service)
) -> BaseResponse:
    """Отменяет активную сессию генерации."""
    try:
        success = await service.cancel_session(session_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия генерации не найдена"
            )
        
        return BaseResponse(
            message="Сессия генерации отменена"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при отмене сессии: {str(e)}"
        )


@router.get(
    "/generate/examples",
    response_model=Dict[str, Any],
    summary="Get Example Requests",
    description="Получает примеры запросов для разных типов задач"
)
async def get_example_requests() -> Dict[str, Any]:
    """
    Возвращает примеры запросов для разных типов задач генерации.
    
    Помогает пользователям понять, как правильно формулировать запросы.
    """
    return {
        "new_feature": {
            "title": "Проектирование нового функционала",
            "example": "Нужно спроектировать систему уведомлений для мобильного приложения. Пользователи должны получать push-уведомления о важных событиях, с возможностью настройки типов уведомлений.",
            "tips": [
                "Опишите бизнес-цель функционала",
                "Укажите целевую аудиторию",
                "Опишите ожидаемое поведение пользователей"
            ]
        },
        "modify_existing": {
            "title": "Изменение существующего функционала",
            "example": "Нужно улучшить существующую систему авторизации, добавив двухфакторную аутентификацию и SSO интеграцию с внутренними сервисами компании.",
            "tips": [
                "Опишите текущее состояние системы",
                "Укажите проблемы, которые нужно решить",
                "Опишите желаемое будущее состояние"
            ]
        },
        "analyze_current": {
            "title": "Анализ текущего функционала",
            "example": "Нужно проанализировать производительность API платежной системы и предложить архитектурные улучшения для обработки увеличенной нагрузки.",
            "tips": [
                "Предоставьте метрики текущей производительности",
                "Опишите ожидаемую нагрузку",
                "Укажите бюджетные ограничения"
            ]
        }
    } 