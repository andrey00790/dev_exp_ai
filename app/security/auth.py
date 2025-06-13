"""
JWT Authentication module for AI Assistant MVP

Provides secure authentication using JWT tokens with proper validation,
user management, and access control for all API endpoints.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "ai-assistant-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

security = HTTPBearer()

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    scopes: list[str] = []

class User(BaseModel):
    user_id: str
    email: str
    name: str
    is_active: bool = True
    budget_limit: float = 100.0  # Default budget in USD
    current_usage: float = 0.0
    scopes: list[str] = ["basic"]  # Default permissions

# Simple in-memory user store (replace with database in production)
USERS_DB: Dict[str, User] = {
    "demo_user": User(
        user_id="demo_user",
        email="demo@ai-assistant.com", 
        name="Demo User",
        budget_limit=50.0,
        scopes=["basic", "rfc_generation", "documentation"]
    ),
    "admin_user": User(
        user_id="admin_user",
        email="admin@ai-assistant.com",
        name="Admin User", 
        budget_limit=1000.0,
        scopes=["basic", "rfc_generation", "documentation", "admin"]
    )
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a new JWT access token
    
    Args:
        data: Token payload data
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Created access token for user: {data.get('sub', 'unknown')}")
    return encoded_jwt

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """
    Verify and decode JWT token
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        TokenData: Decoded token data
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("Token missing 'sub' claim")
            raise credentials_exception
            
        token_data = TokenData(
            user_id=user_id,
            email=payload.get("email"),
            scopes=payload.get("scopes", [])
        )
        logger.debug(f"Token verified for user: {user_id}")
        return token_data
        
    except JWTError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        raise credentials_exception

async def get_current_user(token_data: TokenData = Depends(verify_token)) -> User:
    """
    Get current authenticated user
    
    Args:
        token_data: Validated token data
        
    Returns:
        User: Current user object
        
    Raises:
        HTTPException: If user not found or inactive
    """
    user = USERS_DB.get(token_data.user_id)
    if user is None:
        logger.warning(f"User not found: {token_data.user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {token_data.user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    logger.debug(f"Retrieved current user: {user.user_id}")
    return user

def require_scope(required_scope: str):
    """
    Dependency to check if user has required scope/permission
    
    Args:
        required_scope: Required permission scope
        
    Returns:
        Dependency function
    """
    async def check_scope(current_user: User = Depends(get_current_user)):
        if required_scope not in current_user.scopes:
            logger.warning(f"User {current_user.user_id} lacks scope: {required_scope}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires '{required_scope}' permission"
            )
        return current_user
    
    return check_scope

# Authentication utility functions
def authenticate_user(user_id: str, password: str) -> Optional[User]:
    """
    Authenticate user credentials (simplified for demo)
    
    Args:
        user_id: User identifier
        password: User password
        
    Returns:
        User object if authenticated, None otherwise
    """
    # In production, verify password hash from database
    if user_id in USERS_DB and password == "demo_password":
        logger.info(f"User authenticated: {user_id}")
        return USERS_DB[user_id]
    
    logger.warning(f"Authentication failed for user: {user_id}")
    return None

def create_user_token(user: User) -> Dict[str, Any]:
    """
    Create token response for authenticated user
    
    Args:
        user: Authenticated user
        
    Returns:
        Token response dictionary
    """
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.user_id,
            "email": user.email,
            "scopes": user.scopes
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_info": {
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
            "budget_limit": user.budget_limit,
            "current_usage": user.current_usage,
            "scopes": user.scopes
        }
    }

def update_user_usage(user_id: str, cost: float) -> None:
    """
    Update user's current usage/cost
    
    Args:
        user_id: User identifier
        cost: Cost to add to current usage
    """
    if user_id in USERS_DB:
        USERS_DB[user_id].current_usage += cost
        logger.info(f"Updated usage for {user_id}: +${cost:.4f}")
    else:
        logger.warning(f"Attempted to update usage for unknown user: {user_id}") 