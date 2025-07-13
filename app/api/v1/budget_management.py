"""
Budget Management API Endpoints

Реальные эндпоинты для управления бюджетами пользователей.
Заменяет все моковые эндпоинты связанные с бюджетами.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.security.auth import get_current_user, User
from app.services.budget_service import (
    budget_service,
    get_user_budget_info,
    manual_refill_user_budget,
    get_budget_refill_history,
    get_budget_system_stats
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/budget", tags=["Budget Management"])


# Request/Response Models
class ManualRefillRequest(BaseModel):
    """Запрос на ручное пополнение бюджета"""
    user_id: str = Field(..., description="ID пользователя")
    amount: float = Field(..., gt=0, description="Сумма пополнения")
    refill_type: str = Field("add", description="Тип пополнения: add или reset")
    reason: Optional[str] = Field(None, description="Причина пополнения")


class BudgetStatusResponse(BaseModel):
    """Ответ со статусом бюджета"""
    user_id: str
    email: str
    current_usage: float
    budget_limit: float
    remaining_balance: float
    usage_percentage: float
    budget_status: str
    last_refill: Optional[Dict[str, Any]] = None
    total_refills: int
    total_refilled: float


class RefillHistoryResponse(BaseModel):
    """Ответ с историей пополнений"""
    refills: List[Dict[str, Any]]
    total_count: int
    page: int
    limit: int


class SystemStatsResponse(BaseModel):
    """Ответ со статистикой системы"""
    total_refills: int
    successful_refills: int
    failed_refills: int
    success_rate: float
    total_amount_refilled: float
    average_refill_amount: float
    recent_refills_24h: int
    recent_amount_24h: float
    last_refill: Optional[str]
    scheduler_running: bool


@router.get(
    "/status",
    response_model=BudgetStatusResponse,
    summary="Budget Status",
    description="Получить текущий статус бюджета пользователя"
)
async def get_budget_status(current_user: User = Depends(get_current_user)):
    """
    Получить текущий статус бюджета пользователя.
    
    Возвращает:
    - Текущее использование
    - Лимит бюджета
    - Остаток
    - Процент использования
    - Статус бюджета
    - Информацию о последнем пополнении
    """
    try:
        # Безопасное извлечение user_id из объекта пользователя
        try:
            user_id = current_user.user_id
        except AttributeError:
            # Если current_user - это словарь, а не объект User
            user_id = current_user.get("user_id") if isinstance(current_user, dict) else None
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID not found in token"
            )
        
        budget_info = await get_user_budget_info(user_id)
        
        if "error" in budget_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=budget_info["error"]
            )
        
        return BudgetStatusResponse(**budget_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting budget status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get budget status: {str(e)}"
        )


@router.post(
    "/refill",
    summary="Manual Budget Refill",
    description="Ручное пополнение бюджета пользователя (только для администраторов)"
)
async def manual_refill(
    request: ManualRefillRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Ручное пополнение бюджета пользователя.
    
    Доступно только администраторам.
    """
    try:
        # Проверяем права администратора
        if "admin" not in current_user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        result = await manual_refill_user_budget(
            user_id=request.user_id,
            amount=request.amount,
            refill_type=request.refill_type
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        logger.info(f"✅ Manual refill completed by {current_user.email}: {request.user_id} +${request.amount}")
        
        return {
            "success": True,
            "message": "Budget refilled successfully",
            "refill_details": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in manual refill: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refill budget: {str(e)}"
        )


@router.get(
    "/history",
    response_model=RefillHistoryResponse,
    summary="Budget Refill History",
    description="Получить историю пополнений бюджета"
)
async def get_refill_history(
    user_id: Optional[str] = Query(None, description="ID пользователя (если не указан - все пользователи)"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    current_user: User = Depends(get_current_user)
):
    """
    Получить историю пополнений бюджета.
    
    Обычные пользователи видят только свою историю.
    Администраторы могут видеть историю всех пользователей.
    """
    try:
        # Проверяем права доступа
        if user_id and user_id != current_user.user_id:
            if "admin" not in current_user.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: can only view own budget history"
                )
        
        # Если пользователь не указан и это не админ, показываем только свою историю
        if not user_id and "admin" not in current_user.scopes:
            user_id = current_user.user_id
        
        # Получаем историю
        history = await get_budget_refill_history(user_id=user_id, limit=limit)
        
        # Пагинация
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_history = history[start_idx:end_idx]
        
        return RefillHistoryResponse(
            refills=paginated_history,
            total_count=len(history),
            page=page,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting refill history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get refill history: {str(e)}"
        )


@router.get(
    "/system-stats",
    response_model=SystemStatsResponse,
    summary="Budget System Statistics",
    description="Получить статистику системы управления бюджетами (только для администраторов)"
)
async def get_system_statistics(current_user: User = Depends(get_current_user)):
    """
    Получить статистику системы управления бюджетами.
    
    Доступно только администраторам.
    """
    try:
        # Проверяем права администратора
        if "admin" not in current_user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        stats = await get_budget_system_stats()
        
        if "error" in stats:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=stats["error"]
            )
        
        return SystemStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting system stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system stats: {str(e)}"
        )


@router.post(
    "/scheduler/restart",
    summary="Restart Budget Scheduler",
    description="Перезапустить планировщик автоматического пополнения (только для администраторов)"
)
async def restart_scheduler(current_user: User = Depends(get_current_user)):
    """
    Перезапустить планировщик автоматического пополнения.
    
    Доступно только администраторам.
    """
    try:
        # Проверяем права администратора
        if "admin" not in current_user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Останавливаем и запускаем планировщик
        await budget_service.stop_auto_refill_scheduler()
        await budget_service.start_auto_refill_scheduler()
        
        logger.info(f"✅ Budget scheduler restarted by {current_user.email}")
        
        return {
            "success": True,
            "message": "Budget scheduler restarted successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Error restarting scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart scheduler: {str(e)}"
        )


@router.post(
    "/scheduler/run-now",
    summary="Run Budget Refill Now",
    description="Запустить пополнение бюджетов немедленно (только для администраторов)"
)
async def run_refill_now(current_user: User = Depends(get_current_user)):
    """
    Запустить пополнение бюджетов немедленно.
    
    Доступно только администраторам.
    """
    try:
        # Проверяем права администратора
        if "admin" not in current_user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Запускаем пополнение
        await budget_service._execute_auto_refill()
        
        logger.info(f"✅ Manual budget refill executed by {current_user.email}")
        
        return {
            "success": True,
            "message": "Budget refill executed successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Error executing manual refill: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute refill: {str(e)}"
        )


@router.get(
    "/config",
    summary="Get Budget Configuration",
    description="Получить конфигурацию системы бюджетов (только для администраторов)"
)
async def get_budget_config(current_user: User = Depends(get_current_user)):
    """
    Получить конфигурацию системы бюджетов.
    
    Доступно только администраторам.
    """
    try:
        # Проверяем права администратора
        if "admin" not in current_user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        config = budget_service.config
        
        # Маскируем чувствительные данные
        safe_config = {
            "auto_refill": {
                "enabled": config["auto_refill"]["enabled"],
                "schedule": config["auto_refill"]["schedule"],
                "refill_settings": {
                    "refill_type": config["auto_refill"]["refill_settings"]["refill_type"],
                    "by_role": config["auto_refill"]["refill_settings"]["by_role"],
                    "minimum_balance": config["auto_refill"]["refill_settings"]["minimum_balance"]
                }
            },
            "monitoring": config["monitoring"],
            "security": {
                "max_limits": config["security"]["max_limits"],
                "audit": config["security"]["audit"]
            }
        }
        
        return {
            "success": True,
            "config": safe_config
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting budget config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get budget config: {str(e)}"
        )


# Совместимость с существующими моковыми эндпоинтами
@router.get(
    "/auth/budget/status",
    response_model=BudgetStatusResponse,
    summary="Budget Status (Legacy)",
    description="Получить статус бюджета (совместимость с legacy API)"
)
async def legacy_budget_status(current_user: User = Depends(get_current_user)):
    """Legacy эндпоинт для совместимости"""
    return await get_budget_status(current_user)


# Эндпоинт для совместимости с мониторингом
@router.get(
    "/monitoring/budget/metrics",
    summary="Budget Metrics",
    description="Получить метрики бюджетов для мониторинга"
)
async def get_budget_metrics(current_user: User = Depends(get_current_user)):
    """
    Получить метрики бюджетов для мониторинга.
    """
    try:
        # Проверяем права
        if "admin" not in current_user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        stats = await get_budget_system_stats()
        
        # Формируем метрики в формате Prometheus
        metrics = {
            "budget_total_refills": stats.get("total_refills", 0),
            "budget_successful_refills": stats.get("successful_refills", 0),
            "budget_failed_refills": stats.get("failed_refills", 0),
            "budget_success_rate": stats.get("success_rate", 0),
            "budget_total_amount_refilled": stats.get("total_amount_refilled", 0),
            "budget_average_refill_amount": stats.get("average_refill_amount", 0),
            "budget_recent_refills_24h": stats.get("recent_refills_24h", 0),
            "budget_recent_amount_24h": stats.get("recent_amount_24h", 0),
            "budget_scheduler_running": 1 if stats.get("scheduler_running", False) else 0
        }
        
        return {
            "success": True,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting budget metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get budget metrics: {str(e)}"
        ) 