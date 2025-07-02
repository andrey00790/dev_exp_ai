"""
Budget Management API endpoints for AI Assistant MVP
Task 1.2: Cost Control - API for budget tracking and management
Task 2.1: Enhanced with Performance Caching

Provides endpoints for:
- Getting user budget status (cached)
- Updating budget limits (admin only)
- Getting usage statistics (cached)
- Budget alerts management
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.performance.cache_manager import cache_manager
from app.security.auth import User, get_current_user, require_admin
from app.security.cost_control import (check_budget_before_request,
                                       cost_controller, get_user_budget_status)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/budget", tags=["Budget Management"])


class BudgetStatusResponse(BaseModel):
    """Budget status response model."""

    user_id: str
    email: str
    current_usage: float
    budget_limit: float
    remaining_budget: float
    usage_percentage: float
    budget_status: str
    daily_average: float = 0.0
    monthly_projection: float = 0.0
    last_request: str = None
    total_requests: int = 0


class BudgetUpdateRequest(BaseModel):
    """Budget update request model."""

    user_id: str
    new_budget_limit: float = Field(gt=0, description="New budget limit in USD")
    reason: str = Field(description="Reason for budget change")


class UsageLogEntry(BaseModel):
    """Usage log entry model."""

    timestamp: str
    provider: str
    model: str
    endpoint: str
    cost: float
    tokens: int
    duration_ms: int
    success: bool


class BudgetAlertResponse(BaseModel):
    """Budget alert response model."""

    alert_id: str
    user_id: str
    alert_type: str
    threshold_percentage: int
    current_usage: float
    budget_limit: float
    alert_sent_at: str
    resolved_at: str = None


@router.get("/status", response_model=BudgetStatusResponse)
async def get_budget_status(current_user: User = Depends(get_current_user)):
    """
    Get current user's budget status and usage statistics.

    Cached for 60 seconds to improve performance.

    Returns comprehensive budget information including:
    - Current usage and remaining budget
    - Usage percentage and status
    - Projections and averages
    - Recent activity summary
    """
    try:
        # Check cache first
        cache_key = f"budget_status_{current_user.user_id}"
        cached_status = await cache_manager.get(cache_key, "budget_status")

        if cached_status:
            logger.debug(f"Cache hit for budget status: {current_user.user_id}")
            return BudgetStatusResponse(**cached_status)

        # Get fresh data
        status_data = await get_user_budget_status(current_user.user_id)

        if "error" in status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=status_data["error"]
            )

        # Cache the result
        await cache_manager.set(cache_key, status_data, "budget_status", ttl=60)
        logger.debug(f"Cached budget status for: {current_user.user_id}")

        return BudgetStatusResponse(**status_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting budget status for {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve budget status",
        )


@router.get("/check/{estimated_cost}")
async def check_budget_availability(
    estimated_cost: float, current_user: User = Depends(get_current_user)
):
    """
    Check if user can afford an operation with estimated cost.

    Args:
        estimated_cost: Estimated cost in USD for the operation

    Returns:
        Budget check result with approval status and details
    """
    try:
        can_proceed, budget_info = await check_budget_before_request(
            current_user.user_id, estimated_cost
        )

        return {
            "can_proceed": can_proceed,
            "estimated_cost": estimated_cost,
            "budget_info": budget_info,
            "user_id": current_user.user_id,
        }

    except Exception as e:
        logger.error(f"Error checking budget for {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check budget availability",
        )


@router.post("/update", dependencies=[Depends(require_admin)])
async def update_user_budget(
    budget_update: BudgetUpdateRequest, current_user: User = Depends(get_current_user)
):
    """
    Update user's budget limit (admin only).

    Allows administrators to modify user budget limits.
    Logs the change for audit purposes.
    Clears cache after update.
    """
    try:
        # Get target user info
        target_budget = await cost_controller._get_user_budget_from_auth(
            budget_update.user_id
        )

        if not target_budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {budget_update.user_id} not found",
            )

        # Update budget in auth system
        from app.security.auth import USERS_DB

        for email, user_data in USERS_DB.items():
            if user_data.get("user_id") == budget_update.user_id:
                old_limit = user_data.get("budget_limit", 100.0)
                user_data["budget_limit"] = budget_update.new_budget_limit

                logger.info(
                    f"Budget updated by admin {current_user.user_id}: "
                    f"User {budget_update.user_id} budget: ${old_limit:.2f} -> ${budget_update.new_budget_limit:.2f} "
                    f"Reason: {budget_update.reason}"
                )

                # Clear cache to force refresh
                cache_key = f"budget_{budget_update.user_id}"
                if cache_key in cost_controller.budget_cache:
                    del cost_controller.budget_cache[cache_key]

                # Clear budget status cache
                status_cache_key = f"budget_status_{budget_update.user_id}"
                await cache_manager.delete(status_cache_key, "budget_status")

                # Clear related caches
                await cache_manager.clear_pattern(f"budget_{budget_update.user_id}")

                return {
                    "success": True,
                    "user_id": budget_update.user_id,
                    "old_budget_limit": old_limit,
                    "new_budget_limit": budget_update.new_budget_limit,
                    "updated_by": current_user.user_id,
                    "reason": budget_update.reason,
                    "timestamp": str(datetime.now()),
                }

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {budget_update.user_id} not found in system",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating budget: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update budget",
        )


@router.get("/usage-history")
async def get_usage_history(
    days: int = 7, current_user: User = Depends(get_current_user)
):
    """
    Get user's usage history for the specified number of days.

    Cached for 5 minutes to improve performance.

    Args:
        days: Number of days to include (default: 7, max: 90)

    Returns:
        Usage history with daily breakdown and totals
    """
    try:
        if days > 90:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 90 days allowed for usage history",
            )

        # Check cache first
        cache_key = f"usage_history_{current_user.user_id}_{days}"
        cached_history = await cache_manager.get(cache_key, "api_response")

        if cached_history:
            logger.debug(f"Cache hit for usage history: {current_user.user_id}")
            return cached_history

        # For now, return mock data
        # In production, this would query the llm_usage_logs table

        mock_usage = []
        total_cost = 0.0
        total_requests = 0

        # Generate mock daily usage
        from datetime import datetime, timedelta

        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            daily_cost = (
                float(current_user.current_usage) / days * (0.8 + 0.4 * (i % 3))
            )
            daily_requests = int(daily_cost * 20)  # Rough estimation

            mock_usage.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "total_cost": round(daily_cost, 4),
                    "total_requests": daily_requests,
                    "providers": {
                        "openai": {
                            "cost": daily_cost * 0.6,
                            "requests": int(daily_requests * 0.6),
                        },
                        "anthropic": {
                            "cost": daily_cost * 0.3,
                            "requests": int(daily_requests * 0.3),
                        },
                        "ollama": {
                            "cost": daily_cost * 0.1,
                            "requests": int(daily_requests * 0.1),
                        },
                    },
                }
            )

            total_cost += daily_cost
            total_requests += daily_requests

        return {
            "user_id": current_user.user_id,
            "period_days": days,
            "total_cost": round(total_cost, 4),
            "total_requests": total_requests,
            "average_daily_cost": round(total_cost / days, 4),
            "average_request_cost": round(total_cost / max(total_requests, 1), 6),
            "usage_by_day": list(reversed(mock_usage)),  # Most recent first
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage history for {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage history",
        )


@router.get("/alerts")
async def get_budget_alerts(
    resolved: bool = None, current_user: User = Depends(get_current_user)
):
    """
    Get budget alerts for the current user.

    Args:
        resolved: Filter by resolved status (None for all, True for resolved, False for active)

    Returns:
        List of budget alerts with details
    """
    try:
        # For now, return mock alert data
        # In production, this would query the budget_alerts table

        mock_alerts = []

        # Generate mock alerts based on current usage
        usage_percentage = (
            current_user.current_usage / current_user.budget_limit
        ) * 100

        if usage_percentage >= 80:
            mock_alerts.append(
                {
                    "alert_id": "alert_001",
                    "user_id": current_user.user_id,
                    "alert_type": "warning_80",
                    "threshold_percentage": 80,
                    "current_usage": current_user.current_usage,
                    "budget_limit": current_user.budget_limit,
                    "alert_sent_at": "2025-06-16T20:00:00Z",
                    "resolved_at": (
                        None if usage_percentage >= 80 else "2025-06-16T22:00:00Z"
                    ),
                }
            )

        if usage_percentage >= 95:
            mock_alerts.append(
                {
                    "alert_id": "alert_002",
                    "user_id": current_user.user_id,
                    "alert_type": "warning_95",
                    "threshold_percentage": 95,
                    "current_usage": current_user.current_usage,
                    "budget_limit": current_user.budget_limit,
                    "alert_sent_at": "2025-06-16T21:00:00Z",
                    "resolved_at": None,
                }
            )

        # Filter by resolved status if specified
        if resolved is not None:
            mock_alerts = [
                alert
                for alert in mock_alerts
                if (alert["resolved_at"] is not None) == resolved
            ]

        return {
            "user_id": current_user.user_id,
            "total_alerts": len(mock_alerts),
            "alerts": mock_alerts,
        }

    except Exception as e:
        logger.error(f"Error getting budget alerts for {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve budget alerts",
        )


@router.get("/overview", dependencies=[Depends(require_admin)])
async def get_budget_overview(current_user: User = Depends(get_current_user)):
    """
    Get system-wide budget overview (admin only).

    Returns aggregate statistics for all users including:
    - Total system usage and costs
    - Users approaching budget limits
    - Top spenders and usage patterns
    """
    try:
        from app.security.auth import USERS_DB

        total_users = len(USERS_DB)
        total_budget = sum(
            user.get("budget_limit", 100.0) for user in USERS_DB.values()
        )
        total_usage = sum(user.get("current_usage", 0.0) for user in USERS_DB.values())

        # Find users with high usage
        high_usage_users = []
        warning_users = []

        for email, user_data in USERS_DB.items():
            usage = user_data.get("current_usage", 0.0)
            limit = user_data.get("budget_limit", 100.0)
            percentage = (usage / limit) * 100 if limit > 0 else 0

            user_summary = {
                "user_id": user_data.get("user_id"),
                "email": email,
                "usage": usage,
                "limit": limit,
                "percentage": round(percentage, 2),
            }

            if percentage >= 80:
                warning_users.append(user_summary)

            if usage > 10:  # Top spenders (>$10)
                high_usage_users.append(user_summary)

        # Sort by usage percentage
        warning_users.sort(key=lambda x: x["percentage"], reverse=True)
        high_usage_users.sort(key=lambda x: x["usage"], reverse=True)

        return {
            "system_overview": {
                "total_users": total_users,
                "total_budget_allocated": round(total_budget, 2),
                "total_usage": round(total_usage, 2),
                "system_usage_percentage": round((total_usage / total_budget) * 100, 2),
                "remaining_budget": round(total_budget - total_usage, 2),
            },
            "alerts": {
                "users_over_80_percent": len(warning_users),
                "users_over_95_percent": len(
                    [u for u in warning_users if u["percentage"] >= 95]
                ),
                "users_exceeded": len(
                    [u for u in warning_users if u["percentage"] >= 100]
                ),
            },
            "top_spenders": high_usage_users[:10],
            "warning_users": warning_users[:10],
            "generated_at": str(datetime.now()),
            "generated_by": current_user.user_id,
        }

    except Exception as e:
        logger.error(f"Error generating budget overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate budget overview",
        )
