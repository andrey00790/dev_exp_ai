"""
Cost Control System for AI Assistant MVP
Task 1.2: Budget tracking and enforcement for LLM API calls

Provides:
- Budget checking before expensive operations
- Usage tracking and logging
- Cost calculation for different LLM providers
- Budget alerts and enforcement
"""

import os
import uuid
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
from fastapi import HTTPException, status, Request
import asyncio

logger = logging.getLogger(__name__)

# LLM Cost Configuration (USD per 1000 tokens)
LLM_PRICING = {
    "openai": {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "text-embedding-ada-002": {"input": 0.0001, "output": 0.0}
    },
    "anthropic": {
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125}
    },
    "ollama": {
        "llama2": {"input": 0.0, "output": 0.0},  # Local model, no cost
        "mistral": {"input": 0.0, "output": 0.0},
        "codellama": {"input": 0.0, "output": 0.0}
    }
}

class CostController:
    """Main cost control and budget enforcement system."""
    
    def __init__(self):
        self.budget_cache = {}  # In-memory cache for performance
        self.cache_ttl = 300  # 5 minutes cache TTL
        
    def calculate_llm_cost(
        self, 
        provider: str, 
        model: str, 
        prompt_tokens: int, 
        completion_tokens: int
    ) -> Decimal:
        """Calculate cost for LLM API call based on token usage."""
        try:
            if provider not in LLM_PRICING:
                logger.warning(f"Unknown LLM provider: {provider}")
                return Decimal("0.001")  # Default minimal cost
                
            if model not in LLM_PRICING[provider]:
                logger.warning(f"Unknown model {model} for provider {provider}")
                # Use first available model pricing as fallback
                model = list(LLM_PRICING[provider].keys())[0]
            
            pricing = LLM_PRICING[provider][model]
            
            # Calculate cost: (tokens / 1000) * price_per_1k_tokens
            input_cost = Decimal(str(prompt_tokens)) / 1000 * Decimal(str(pricing["input"]))
            output_cost = Decimal(str(completion_tokens)) / 1000 * Decimal(str(pricing["output"]))
            
            total_cost = input_cost + output_cost
            logger.debug(f"Cost calculation: {provider}/{model} - {prompt_tokens}+{completion_tokens} tokens = ${total_cost:.6f}")
            
            return total_cost
            
        except Exception as e:
            logger.error(f"Error calculating LLM cost: {e}")
            return Decimal("0.001")  # Fallback cost
    
    async def check_user_budget(self, user_id: str, estimated_cost: Decimal) -> Tuple[bool, Dict[str, Any]]:
        """Check if user has sufficient budget for the operation."""
        try:
            # Check cache first
            cache_key = f"budget_{user_id}"
            now = datetime.now()
            
            if cache_key in self.budget_cache:
                cached_data, cache_time = self.budget_cache[cache_key]
                if (now - cache_time).total_seconds() < self.cache_ttl:
                    budget_info = cached_data
                else:
                    budget_info = await self._get_user_budget_from_auth(user_id)
                    self.budget_cache[cache_key] = (budget_info, now)
            else:
                budget_info = await self._get_user_budget_from_auth(user_id)
                self.budget_cache[cache_key] = (budget_info, now)
            
            if not budget_info:
                logger.warning(f"No budget info found for user {user_id}")
                return False, {"error": "Budget information not found"}
            
            current_usage = Decimal(str(budget_info.get("current_usage", 0)))
            budget_limit = Decimal(str(budget_info.get("budget_limit", 100)))
            
            projected_usage = current_usage + estimated_cost
            usage_percentage = float(projected_usage / budget_limit * 100)
            
            # Check if operation would exceed budget
            if projected_usage > budget_limit:
                return False, {
                    "error": "Budget exceeded",
                    "current_usage": float(current_usage),
                    "budget_limit": float(budget_limit),
                    "estimated_cost": float(estimated_cost),
                    "projected_usage": float(projected_usage),
                    "usage_percentage": usage_percentage
                }
            
            # Check if approaching budget limits (warning thresholds)
            warning_level = None
            if usage_percentage >= 95:
                warning_level = "critical"
            elif usage_percentage >= 80:
                warning_level = "warning"
            
            return True, {
                "approved": True,
                "current_usage": float(current_usage),
                "budget_limit": float(budget_limit),
                "estimated_cost": float(estimated_cost),
                "projected_usage": float(projected_usage),
                "usage_percentage": usage_percentage,
                "remaining_budget": float(budget_limit - projected_usage),
                "warning_level": warning_level
            }
            
        except Exception as e:
            logger.error(f"Error checking user budget: {e}")
            return False, {"error": f"Budget check failed: {str(e)}"}
    
    async def _get_user_budget_from_auth(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user budget info from the auth system."""
        try:
            # Import here to avoid circular imports
            from app.security.auth import USERS_DB
            
            # Find user by ID
            user_data = None
            for email, data in USERS_DB.items():
                if data.get("user_id") == user_id:
                    user_data = data
                    break
            
            if not user_data:
                return None
                
            return {
                "user_id": user_id,
                "email": user_data.get("email"),
                "budget_limit": user_data.get("budget_limit", 100.0),
                "current_usage": user_data.get("current_usage", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error getting user budget from auth: {e}")
            return None
    
    async def log_llm_usage(
        self,
        user_id: str,
        email: str,
        provider: str,
        model: str,
        endpoint: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: Decimal,
        duration_ms: int,
        success: bool = True,
        error_message: str = None
    ) -> str:
        """Log LLM usage for tracking and billing purposes."""
        try:
            request_id = str(uuid.uuid4())
            
            # In a real implementation, this would write to PostgreSQL
            # For now, we'll log and update the in-memory auth system
            
            logger.info(f"LLM Usage Log: {user_id} | {provider}/{model} | {endpoint} | "
                       f"${cost:.6f} | {prompt_tokens}+{completion_tokens} tokens | "
                       f"{duration_ms}ms | {'SUCCESS' if success else 'FAILED'}")
            
            # Update user's current usage in the auth system
            await self._update_user_usage(user_id, cost)
            
            # Clear cache to force refresh
            cache_key = f"budget_{user_id}"
            if cache_key in self.budget_cache:
                del self.budget_cache[cache_key]
            
            return request_id
            
        except Exception as e:
            logger.error(f"Error logging LLM usage: {e}")
            return "error"
    
    async def _update_user_usage(self, user_id: str, cost: Decimal):
        """Update user's current usage in the auth system."""
        try:
            from app.security.auth import USERS_DB
            
            # Find and update user
            for email, user_data in USERS_DB.items():
                if user_data.get("user_id") == user_id:
                    current_usage = user_data.get("current_usage", 0.0)
                    new_usage = current_usage + float(cost)
                    user_data["current_usage"] = new_usage
                    logger.info(f"Updated usage for {user_id}: ${current_usage:.4f} -> ${new_usage:.4f}")
                    break
                    
        except Exception as e:
            logger.error(f"Error updating user usage: {e}")
    
    async def get_usage_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get detailed usage statistics for a user."""
        try:
            budget_info = await self._get_user_budget_from_auth(user_id)
            if not budget_info:
                return {"error": "User budget info not found"}
            
            current_usage = Decimal(str(budget_info["current_usage"]))
            budget_limit = Decimal(str(budget_info["budget_limit"]))
            
            return {
                "user_id": user_id,
                "email": budget_info["email"],
                "current_usage": float(current_usage),
                "budget_limit": float(budget_limit),
                "remaining_budget": float(budget_limit - current_usage),
                "usage_percentage": float(current_usage / budget_limit * 100),
                "budget_status": self._get_budget_status(current_usage, budget_limit),
                "daily_average": 0.0,  # Would calculate from logs
                "monthly_projection": float(current_usage * 30),  # Simple projection
                "last_request": None,  # Would get from logs
                "total_requests": 0,  # Would count from logs
            }
            
        except Exception as e:
            logger.error(f"Error getting usage statistics: {e}")
            return {"error": f"Failed to get statistics: {str(e)}"}
    
    def _get_budget_status(self, current_usage: Decimal, budget_limit: Decimal) -> str:
        """Determine budget status based on usage percentage."""
        percentage = float(current_usage / budget_limit * 100)
        
        if percentage >= 100:
            return "EXCEEDED"
        elif percentage >= 95:
            return "CRITICAL"
        elif percentage >= 80:
            return "WARNING"
        else:
            return "ACTIVE"

# Global instance
cost_controller = CostController()

async def cost_control_middleware(request: Request, call_next):
    """Middleware to check and enforce cost controls for expensive operations."""
    
    # Skip cost control for non-AI endpoints
    if not _is_expensive_endpoint(request.url.path):
        response = await call_next(request)
        return response
    
    try:
        # Get user info from request state (set by auth middleware)
        user_id = getattr(request.state, 'user_id', None)
        if not user_id:
            response = await call_next(request)
            return response
        
        # Estimate cost for the operation
        estimated_cost = _estimate_operation_cost(request.url.path)
        
        # Check budget
        can_proceed, budget_info = await cost_controller.check_user_budget(user_id, estimated_cost)
        
        if not can_proceed:
            from fastapi import Response
            import json
            
            error_response = {
                "detail": "Budget limit exceeded",
                "budget_info": budget_info,
                "suggestion": "Please increase your budget or wait for the next billing period"
            }
            
            return Response(
                content=json.dumps(error_response),
                status_code=402,  # Payment Required
                headers={"Content-Type": "application/json"}
            )
        
        # Add budget info to request state for the endpoint to use
        request.state.budget_info = budget_info
        
        response = await call_next(request)
        return response
        
    except Exception as e:
        logger.error(f"Cost control middleware error: {e}")
        response = await call_next(request)
        return response

def _is_expensive_endpoint(path: str) -> bool:
    """Check if endpoint is expensive (uses LLM APIs)."""
    expensive_endpoints = [
        "/api/v1/generate",
        "/api/v1/search", 
        "/api/v1/documentation/generate",
        "/api/v1/documentation/analyze"
    ]
    return any(path.startswith(endpoint) for endpoint in expensive_endpoints)

def _estimate_operation_cost(path: str) -> Decimal:
    """Estimate cost for different operations."""
    cost_estimates = {
        "/api/v1/generate": Decimal("0.05"),  # RFC generation
        "/api/v1/search": Decimal("0.01"),    # Semantic search
        "/api/v1/documentation/generate": Decimal("0.03"),  # Code docs
        "/api/v1/documentation/analyze": Decimal("0.02"),   # Code analysis
    }
    
    for endpoint, cost in cost_estimates.items():
        if path.startswith(endpoint):
            return cost
    
    return Decimal("0.01")  # Default estimate

# Convenience functions for API endpoints
async def track_llm_request(
    user_id: str,
    provider: str,
    model: str,
    endpoint: str,
    prompt_tokens: int,
    completion_tokens: int,
    duration_ms: int,
    success: bool = True,
    error_message: str = None
) -> str:
    """Track LLM request usage and update user budget."""
    
    # Calculate actual cost
    cost = cost_controller.calculate_llm_cost(provider, model, prompt_tokens, completion_tokens)
    
    # Get user email
    budget_info = await cost_controller._get_user_budget_from_auth(user_id)
    email = budget_info.get("email", "unknown") if budget_info else "unknown"
    
    # Log the usage
    request_id = await cost_controller.log_llm_usage(
        user_id=user_id,
        email=email,
        provider=provider,
        model=model,
        endpoint=endpoint,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost=cost,
        duration_ms=duration_ms,
        success=success,
        error_message=error_message
    )
    
    return request_id

async def check_budget_before_request(user_id: str, estimated_cost: float) -> Tuple[bool, Dict]:
    """Check if user can afford the estimated operation cost."""
    return await cost_controller.check_user_budget(user_id, Decimal(str(estimated_cost)))

async def get_user_budget_status(user_id: str) -> Dict[str, Any]:
    """Get comprehensive budget status for a user."""
    return await cost_controller.get_usage_statistics(user_id)
