"""
Authentication API endpoints for AI Assistant MVP.

Provides login, registration, and user management endpoints.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBasic
from pydantic import BaseModel

from app.security.auth import (
    User, UserCreate, UserLogin, Token,
    create_user, login_user, get_current_user,
    USERS_DB, update_user_usage
)
from app.security.rate_limiter import rate_limit_auth
from app.security.input_validation import validate_input
from app.security.cost_control import cost_controller

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
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

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@rate_limit_auth("3/minute")  # Very strict for registration
async def register_user(request: Request, user_data: UserCreate):
    """
    Register a new user.
    
    - **email**: Valid email address
    - **password**: Strong password (8+ chars, uppercase, lowercase, digit)
    - **name**: User's display name
    - **budget_limit**: Optional monthly budget limit in USD
    """
    try:
        # Additional validation
        validate_input(user_data.name, "name")
        validate_input(user_data.email, "email")
        
        # Create user
        user = create_user(user_data)
        
        # Login immediately after registration
        login_data = UserLogin(email=user_data.email, password=user_data.password)
        token = login_user(login_data)
        
        logger.info(f"New user registered: {user.email}")
        return token
        
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise

@router.post("/login", response_model=Token)
@rate_limit_auth("5/minute")  # Strict for login attempts
async def login(request: Request, credentials: UserLogin):
    """
    Login with email and password.
    
    Returns JWT access token for authenticated requests.
    """
    try:
        # Additional validation
        validate_input(credentials.email, "email")
        
        token = login_user(credentials)
        logger.info(f"User logged in: {credentials.email}")
        return token
        
    except HTTPException:
        logger.warning(f"Failed login attempt: {credentials.email}")
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login service temporarily unavailable"
        )

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information.
    
    Requires valid JWT token in Authorization header.
    """
    return current_user

@router.get("/verify")
async def verify_token(current_user: User = Depends(get_current_user)):
    """
    Verify JWT token validity.
    
    Returns user info if token is valid, 401 if invalid.
    """
    return {
        "valid": True,
        "user_id": current_user.user_id,
        "email": current_user.email,
        "scopes": current_user.scopes,
        "budget_status": {
            "limit": current_user.budget_limit,
            "current_usage": current_user.current_usage,
            "remaining": current_user.budget_limit - current_user.current_usage
        }
    }

@router.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """
    Refresh JWT token.
    
    Returns new token with extended expiration.
    """
    from app.security.auth import create_access_token
    from datetime import timedelta
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={
            "sub": current_user.user_id,
            "email": current_user.email,
            "scopes": current_user.scopes
        },
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=30 * 60,  # 30 minutes in seconds
        user=current_user
    )

@router.get("/budget")
async def get_budget_info(current_user: User = Depends(get_current_user)):
    """
    Get user's budget information and usage statistics.
    """
    usage_percentage = (current_user.current_usage / current_user.budget_limit) * 100
    
    status_level = "active"
    if usage_percentage >= 100:
        status_level = "exceeded"
    elif usage_percentage >= 95:
        status_level = "critical"
    elif usage_percentage >= 80:
        status_level = "warning"
    
    return {
        "user_id": current_user.user_id,
        "budget_limit": current_user.budget_limit,
        "current_usage": current_user.current_usage,
        "remaining": current_user.budget_limit - current_user.current_usage,
        "usage_percentage": round(usage_percentage, 2),
        "status": status_level,
        "currency": "USD"
    }

@router.get("/scopes")
async def get_user_scopes(current_user: User = Depends(get_current_user)):
    """
    Get user's permission scopes.
    """
    scope_descriptions = {
        "basic": "Basic API access",
        "search": "Semantic search functionality",
        "generate": "RFC and documentation generation",
        "admin": "Administrative functions"
    }
    
    return {
        "user_id": current_user.user_id,
        "scopes": current_user.scopes,
        "scope_descriptions": {
            scope: scope_descriptions.get(scope, "Unknown scope")
            for scope in current_user.scopes
        }
    }

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