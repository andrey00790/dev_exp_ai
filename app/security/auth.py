"""
JWT Authentication system for AI Assistant MVP.

Provides secure user authentication with JWT tokens, password hashing,
and user management functionality.
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
import logging

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()

class User(BaseModel):
    """User model for authenticated users."""
    user_id: str
    email: EmailStr
    name: str
    is_active: bool = True
    budget_limit: float = 100.0  # USD limit for LLM usage
    current_usage: float = 0.0   # Current month usage
    scopes: list[str] = ["basic"]  # User permissions
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    """Model for user registration."""
    email: EmailStr
    password: str
    name: str
    budget_limit: Optional[float] = 100.0
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    """Model for user login."""
    email: EmailStr
    password: str

class Token(BaseModel):
    """JWT token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User

class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[str] = None
    email: Optional[str] = None
    scopes: list[str] = []

# In-memory user storage (replace with database in production)
USERS_DB: Dict[str, Dict[str, Any]] = {
    "admin@example.com": {
        "user_id": "admin_001",
        "email": "admin@example.com",
        "name": "Admin User",
        "hashed_password": pwd_context.hash("admin123"),
        "is_active": True,
        "budget_limit": 1000.0,
        "current_usage": 0.0,
        "scopes": ["basic", "admin", "search", "generate"],
        "created_at": datetime.now(),
        "last_login": None
    },
    "user@example.com": {
        "user_id": "user_001", 
        "email": "user@example.com",
        "name": "Test User",
        "hashed_password": pwd_context.hash("user123"),
        "is_active": True,
        "budget_limit": 100.0,
        "current_usage": 0.0,
        "scopes": ["basic", "search", "generate"],
        "created_at": datetime.now(),
        "last_login": None
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email from database."""
    return USERS_DB.get(email)

def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password."""
    user_data = get_user_by_email(email)
    if not user_data:
        return None
    if not verify_password(password, user_data["hashed_password"]):
        return None
    
    # Update last login
    user_data["last_login"] = datetime.now()
    
    return User(**{k: v for k, v in user_data.items() if k != "hashed_password"})

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        scopes: list = payload.get("scopes", [])
        
        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(user_id=user_id, email=email, scopes=scopes)
    
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    token_data = verify_token(token)
    
    user_data = get_user_by_email(token_data.email)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user_data["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return User(**{k: v for k, v in user_data.items() if k != "hashed_password"})

def create_user(user_create: UserCreate) -> User:
    """Create a new user."""
    if get_user_by_email(user_create.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_id = f"user_{secrets.token_hex(8)}"
    hashed_password = get_password_hash(user_create.password)
    
    user_data = {
        "user_id": user_id,
        "email": user_create.email,
        "name": user_create.name,
        "hashed_password": hashed_password,
        "is_active": True,
        "budget_limit": user_create.budget_limit,
        "current_usage": 0.0,
        "scopes": ["basic", "search", "generate"],
        "created_at": datetime.now(),
        "last_login": None
    }
    
    USERS_DB[user_create.email] = user_data
    
    return User(**{k: v for k, v in user_data.items() if k != "hashed_password"})

def login_user(user_login: UserLogin) -> Token:
    """Login user and return JWT token."""
    user = authenticate_user(user_login.email, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.user_id,
            "email": user.email,
            "scopes": user.scopes
        },
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
        user=user
    )

def check_user_scope(user: User, required_scope: str) -> bool:
    """Check if user has required scope."""
    return required_scope in user.scopes

def require_scope(scope: str):
    """Decorator to require specific scope for endpoint access."""
    def scope_checker(user: User = Depends(get_current_user)) -> User:
        if not check_user_scope(user, scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scope: {scope}"
            )
        return user
    return scope_checker

def check_budget_limit(user: User, cost: float) -> bool:
    """Check if user has sufficient budget for operation."""
    return user.current_usage + cost <= user.budget_limit

def update_user_usage(user_email: str, cost: float) -> None:
    """Update user's current usage."""
    if user_email in USERS_DB:
        USERS_DB[user_email]["current_usage"] += cost
        logger.info(f"Updated usage for {user_email}: +${cost:.4f}")

# Convenience dependencies for common scopes
require_admin = require_scope("admin")
require_search = require_scope("search") 
require_generate = require_scope("generate") 