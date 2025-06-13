"""
Cost Control module for AI Assistant MVP

Provides budget management and cost tracking for LLM usage.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum

from fastapi import HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class UsageType(str, Enum):
    """Types of LLM usage for cost tracking"""
    RFC_GENERATION = "rfc_generation"
    DOCUMENTATION = "documentation"
    SEARCH = "search"
    QUESTION_GENERATION = "question_generation"
    CODE_ANALYSIS = "code_analysis"
    OTHER = "other"

class BudgetStatus(str, Enum):
    """Budget status indicators"""
    ACTIVE = "active"
    WARNING = "warning"    # 80% used
    CRITICAL = "critical"  # 95% used
    EXCEEDED = "exceeded"  # 100% used
    SUSPENDED = "suspended"

class UserBudget(BaseModel):
    """User budget configuration"""
    user_id: str
    daily_limit: float = 10.0
    monthly_limit: float = 100.0
    total_limit: float = 1000.0
    current_daily: float = 0.0
    current_monthly: float = 0.0
    current_total: float = 0.0
    status: BudgetStatus = BudgetStatus.ACTIVE
    last_reset_daily: Optional[datetime] = None
    last_reset_monthly: Optional[datetime] = None

class CostController:
    """Main cost control service"""
    
    def __init__(self):
        self.user_budgets: Dict[str, UserBudget] = {}
        self.token_costs = {
            "ollama": {"input": 0.0, "output": 0.0},
            "openai": {
                "gpt-4": {"input": 0.00003, "output": 0.00006},
                "gpt-3.5-turbo": {"input": 0.0000015, "output": 0.000002}
            },
            "anthropic": {
                "claude-3-opus": {"input": 0.000015, "output": 0.000075},
                "claude-3-sonnet": {"input": 0.000003, "output": 0.000015}
            }
        }
        logger.info("Cost Controller initialized")
    
    def get_user_budget(self, user_id: str) -> UserBudget:
        """Get or create user budget"""
        if user_id not in self.user_budgets:
            self.user_budgets[user_id] = UserBudget(
                user_id=user_id,
                last_reset_daily=datetime.utcnow(),
                last_reset_monthly=datetime.utcnow()
            )
        return self.user_budgets[user_id]
    
    def calculate_cost(self, provider: str, model: str, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost for LLM usage"""
        if provider == "ollama":
            return 0.0
        
        provider_costs = self.token_costs.get(provider, {})
        model_costs = provider_costs.get(model, {"input": 0.00001, "output": 0.00002})
        
        input_cost = tokens_input * model_costs["input"]
        output_cost = tokens_output * model_costs["output"]
        return input_cost + output_cost
    
    async def check_budget_before_request(self, user_id: str, provider: str, model: str, estimated_tokens: int = 1000) -> Dict[str, Any]:
        """Check if user can make request within budget"""
        budget = self.get_user_budget(user_id)
        
        if budget.status == BudgetStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={"error": "Account suspended", "user_id": user_id}
            )
        
        estimated_cost = self.calculate_cost(provider, model, estimated_tokens, estimated_tokens)
        
        if budget.current_daily + estimated_cost > budget.daily_limit:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={"error": "Daily budget exceeded", "user_id": user_id}
            )
        
        if budget.current_monthly + estimated_cost > budget.monthly_limit:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={"error": "Monthly budget exceeded", "user_id": user_id}
            )
        
        return {
            "allowed": True,
            "estimated_cost": estimated_cost,
            "remaining_daily": budget.daily_limit - budget.current_daily,
            "budget_status": budget.status
        }
    
    async def record_usage(self, user_id: str, provider: str, model: str, tokens_input: int, tokens_output: int) -> Dict[str, Any]:
        """Record actual LLM usage and update budgets"""
        actual_cost = self.calculate_cost(provider, model, tokens_input, tokens_output)
        budget = self.get_user_budget(user_id)
        
        budget.current_daily += actual_cost
        budget.current_monthly += actual_cost
        budget.current_total += actual_cost
        
        # Update status
        daily_percentage = (budget.current_daily / budget.daily_limit) * 100
        if daily_percentage >= 100:
            budget.status = BudgetStatus.EXCEEDED
        elif daily_percentage >= 95:
            budget.status = BudgetStatus.CRITICAL
        elif daily_percentage >= 80:
            budget.status = BudgetStatus.WARNING
        else:
            budget.status = BudgetStatus.ACTIVE
        
        logger.info(f"Recorded usage for {user_id}: ${actual_cost:.6f}")
        
        return {
            "cost": actual_cost,
            "total_daily": budget.current_daily,
            "budget_status": budget.status
        }

# Global instance
cost_controller = CostController()

async def check_user_budget(user_id: str, provider: str, model: str, estimated_tokens: int = 1000) -> Dict[str, Any]:
    """Convenience function to check user budget"""
    return await cost_controller.check_budget_before_request(user_id, provider, model, estimated_tokens)
