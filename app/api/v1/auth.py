"""
Authentication API endpoints for AI Assistant MVP

Provides login, token management, and user authentication endpoints.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from pydantic import BaseModel

from app.security.auth import (
    authenticate_user, create_user_token, get_current_user, 
    User, USERS_DB, update_user_usage
)
from app.security.rate_limiter import rate_limit_auth
from app.security.input_validation import SecureUserCredentials, validate_user_id
from app.security.cost_control import cost_controller

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
security_basic = HTTPBasic()

class LoginRequest(BaseModel):
    """Login request model"""
    user_id: str
    password: str

class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str
    expires_in: int
    user_info: Dict[str, Any]

class UserProfileResponse(BaseModel):
    """User profile response model"""
    user_id: str
    email: str
    name: str
    budget_limit: float
    current_usage: float
    scopes: list[str]
    is_active: bool

@router.post("/login", response_model=LoginResponse)
@rate_limit_auth("5/minute")
async def login_for_access_token(
    request: Request,
    credentials: SecureUserCredentials
):
    """
    Authenticate user and return JWT access token
    
    Args:
        request: FastAPI request object
        credentials: User credentials
        
    Returns:
        JWT token and user information
        
    Raises:
        HTTPException: If authentication fails
    """
    logger.info(f"Login attempt for user: {credentials.user_id}")
    
    # Authenticate user
    user = authenticate_user(credentials.user_id, credentials.password)
    if not user:
        logger.warning(f"Authentication failed for user: {credentials.user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning(f"Inactive user login attempt: {credentials.user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    # Create token response
    token_response = create_user_token(user)
    
    logger.info(f"Successful login for user: {credentials.user_id}")
    
    return LoginResponse(
        access_token=token_response["access_token"],
        token_type=token_response["token_type"],
        expires_in=token_response["expires_in"],
        user_info=token_response["user_info"]
    )

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile information
    
    Args:
        current_user: Authenticated user
        
    Returns:
        User profile data
    """
    logger.debug(f"Profile request for user: {current_user.user_id}")
    
    return UserProfileResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        name=current_user.name,
        budget_limit=current_user.budget_limit,
        current_usage=current_user.current_usage,
        scopes=current_user.scopes,
        is_active=current_user.is_active
    )

@router.get("/budget")
async def get_user_budget(current_user: User = Depends(get_current_user)):
    """
    Get user budget information and usage statistics
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Budget and usage information
    """
    logger.debug(f"Budget request for user: {current_user.user_id}")
    
    # Get detailed budget info from cost controller
    budget = cost_controller.get_user_budget(current_user.user_id)
    
    return {
        "user_id": current_user.user_id,
        "budget_status": budget.status,
        "limits": {
            "daily": budget.daily_limit,
            "monthly": budget.monthly_limit,
            "total": budget.total_limit
        },
        "current_usage": {
            "daily": budget.current_daily,
            "monthly": budget.current_monthly,
            "total": budget.current_total
        },
        "remaining": {
            "daily": budget.daily_limit - budget.current_daily,
            "monthly": budget.monthly_limit - budget.current_monthly,
            "total": budget.total_limit - budget.current_total
        },
        "last_reset": {
            "daily": budget.last_reset_daily,
            "monthly": budget.last_reset_monthly
        }
    }

@router.get("/usage-stats")
async def get_usage_statistics(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed usage statistics for user
    
    Args:
        days: Number of days to include in statistics
        current_user: Authenticated user
        
    Returns:
        Detailed usage statistics
    """
    logger.debug(f"Usage stats request for user: {current_user.user_id}, days: {days}")
    
    if days > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 365 days allowed for statistics"
        )
    
    # This would typically query a database
    # For now, return basic statistics
    return {
        "user_id": current_user.user_id,
        "period_days": days,
        "statistics": {
            "total_requests": 0,
            "total_cost": current_user.current_usage,
            "average_cost_per_request": 0.0,
            "most_used_feature": "rfc_generation",
            "peak_usage_day": None
        },
        "breakdown_by_feature": {
            "rfc_generation": {"requests": 0, "cost": 0.0},
            "documentation": {"requests": 0, "cost": 0.0},
            "search": {"requests": 0, "cost": 0.0}
        }
    }

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout user (in a full implementation, this would invalidate the token)
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Logout confirmation
    """
    logger.info(f"Logout for user: {current_user.user_id}")
    
    # In a real implementation, you'd:
    # 1. Add token to blacklist
    # 2. Clean up any session data
    # 3. Log the logout event
    
    return {
        "message": "Successfully logged out",
        "user_id": current_user.user_id,
        "timestamp": "2025-06-11T18:00:00Z"
    }

@router.get("/validate-token")
async def validate_token(current_user: User = Depends(get_current_user)):
    """
    Validate current JWT token and return user info
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Token validation result
    """
    logger.debug(f"Token validation for user: {current_user.user_id}")
    
    return {
        "valid": True,
        "user_id": current_user.user_id,
        "email": current_user.email,
        "name": current_user.name,
        "scopes": current_user.scopes,
        "is_active": current_user.is_active,
        "message": "Token is valid"
    }

@router.get("/demo-users")
async def get_demo_users():
    """
    Get list of demo users for testing (development only)
    
    Returns:
        List of available demo users
    """
    logger.info("Demo users list requested")
    
    demo_users = []
    for user_id, user in USERS_DB.items():
        demo_users.append({
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
            "scopes": user.scopes,
            "budget_limit": user.budget_limit,
            "password": "demo_password"  # Only for demo!
        })
    
    return {
        "demo_users": demo_users,
        "instructions": [
            "Use any demo user credentials to login",
            "Password for all demo users: 'demo_password'",
            "Tokens expire in 60 minutes",
            "Rate limits: 5 auth requests per minute"
        ],
        "warning": "This endpoint is for development only!"
    } 