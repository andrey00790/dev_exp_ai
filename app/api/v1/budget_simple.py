"""
Budget Management API endpoints for AI Assistant MVP
Simplified version without performance dependencies for compatibility

Provides endpoints for:
- Getting user budget status
- Updating budget limits (admin only)
- Getting usage statistics
- Budget alerts management
"""

import logging
from typing import Dict, Any, List
from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field

from app.security.auth import get_current_user, User, require_admin
from app.security.cost_control import (
    cost_controller, 
    get_user_budget_status,
    check_budget_before_request
)

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

@router.get("/status", response_model=BudgetStatusResponse)
async def get_budget_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's budget status and usage statistics.
    
    Returns comprehensive budget information including:
    - Current usage and remaining budget
    - Usage percentage and status
    - Projections and averages
    - Recent activity summary
    """
    try:
        status_data = await get_user_budget_status(current_user.user_id)
        
        if "error" in status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=status_data["error"]
            )
        
        return BudgetStatusResponse(**status_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting budget status for {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve budget status"
        )

@router.get("/check/{estimated_cost}")
async def check_budget_availability(
    estimated_cost: float,
    current_user: User = Depends(get_current_user)
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
            current_user.user_id, 
            estimated_cost
        )
        
        return {
            "can_proceed": can_proceed,
            "estimated_cost": estimated_cost,
            "budget_info": budget_info,
            "user_id": current_user.user_id
        }
        
    except Exception as e:
        logger.error(f"Error checking budget for {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check budget availability"
        )

@router.post("/update", dependencies=[Depends(require_admin)])
async def update_user_budget(
    budget_update: BudgetUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update user's budget limit (admin only).
    
    Allows administrators to modify user budget limits.
    Logs the change for audit purposes.
    """
    try:
        # Get target user info
        target_budget = await cost_controller._get_user_budget_from_auth(budget_update.user_id)
        
        if not target_budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {budget_update.user_id} not found"
            )
        
        # Update budget in auth system
        from app.security.auth import USERS_DB
        
        for email, user_data in USERS_DB.items():
            if user_data.get("user_id") == budget_update.user_id:
                old_limit = user_data.get("budget_limit", 100.0)
                user_data["budget_limit"] = budget_update.new_budget_limit
                
                logger.info(f"Budget updated by admin {current_user.user_id}: "
                           f"User {budget_update.user_id} budget: ${old_limit:.2f} -> ${budget_update.new_budget_limit:.2f} "
                           f"Reason: {budget_update.reason}")
                
                # Clear cache to force refresh
                cache_key = f"budget_{budget_update.user_id}"
                if cache_key in cost_controller.budget_cache:
                    del cost_controller.budget_cache[cache_key]
                
                return {
                    "success": True,
                    "user_id": budget_update.user_id,
                    "old_budget_limit": old_limit,
                    "new_budget_limit": budget_update.new_budget_limit,
                    "updated_by": current_user.user_id,
                    "reason": budget_update.reason,
                    "timestamp": str(datetime.now())
                }
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {budget_update.user_id} not found in system"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating budget: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update budget"
        )

@router.get("/usage-history")
async def get_usage_history(
    days: int = 7,
    current_user: User = Depends(get_current_user)
):
    """
    Get user's usage history for the specified number of days.
    
    Args:
        days: Number of days to include (default: 7, max: 90)
        
    Returns:
        Usage history with daily breakdown and totals
    """
    try:
        if days > 90:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 90 days allowed for usage history"
            )
        
        # Mock data for demonstration
        mock_usage = []
        total_cost = 0.0
        total_requests = 0
        
        # Generate mock daily usage
        from datetime import datetime, timedelta
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            daily_cost = float(current_user.current_usage) / days * (0.8 + 0.4 * (i % 3))
            daily_requests = int(daily_cost * 20)  # Rough estimation
            
            mock_usage.append({
                "date": date.strftime("%Y-%m-%d"),
                "total_cost": round(daily_cost, 4),
                "total_requests": daily_requests,
                "providers": {
                    "openai": {"cost": daily_cost * 0.6, "requests": int(daily_requests * 0.6)},
                    "anthropic": {"cost": daily_cost * 0.3, "requests": int(daily_requests * 0.3)},
                    "ollama": {"cost": daily_cost * 0.1, "requests": int(daily_requests * 0.1)}
                }
            })
            
            total_cost += daily_cost
            total_requests += daily_requests
        
        return {
            "user_id": current_user.user_id,
            "period_days": days,
            "total_cost": round(total_cost, 4),
            "total_requests": total_requests,
            "average_daily_cost": round(total_cost / days, 4),
            "average_request_cost": round(total_cost / max(total_requests, 1), 6),
            "usage_by_day": list(reversed(mock_usage))  # Most recent first
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage history for {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage history"
        ) 