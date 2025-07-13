"""
User model for authentication and authorization
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr
from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    """User model for database"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)  # Nullable for OAuth users
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)  # For VK OAuth
    last_name = Column(String(255), nullable=True)   # For VK OAuth
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # OAuth fields
    oauth_provider = Column(String(50), nullable=True)  # "vk", "google", etc.
    vk_user_id = Column(String(50), unique=True, nullable=True, index=True)  # VK user ID

    # Profile information
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)

    # Preferences
    preferences = Column(JSON, default=dict)
    settings = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Roles and permissions
    roles = Column(JSON, default=list)  # ["user", "admin", "viewer"]
    permissions = Column(JSON, default=list)

    # Budget and usage tracking
    monthly_budget_usd = Column(Integer, default=100)  # $100 default
    current_usage_usd = Column(Integer, default=0)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary"""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "company": self.company,
            "location": self.location,
            "preferences": self.preferences or {},
            "settings": self.settings or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "roles": self.roles or [],
            "permissions": self.permissions or [],
            "monthly_budget_usd": self.monthly_budget_usd,
            "current_usage_usd": self.current_usage_usd,
            "oauth_provider": self.oauth_provider,
            "vk_user_id": self.vk_user_id,
        }

    def has_role(self, role: str) -> bool:
        """Check if user has specific role"""
        return role in (self.roles or [])

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in (self.permissions or [])

    def is_within_budget(self, cost_usd: float = 0) -> bool:
        """Check if user is within monthly budget"""
        return (self.current_usage_usd + cost_usd) <= self.monthly_budget_usd


# Aliases for hexagonal architecture compatibility
UserModel = User


class RoleModel(Base):
    """Role model for database"""
    
    __tablename__ = "roles"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    role_type = Column(String(50), nullable=False, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class PermissionModel(Base):
    """Permission model for database"""
    
    __tablename__ = "permissions"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    resource = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Permission(id={self.id}, name={self.name})>"


class SessionModel(Base):
    """Session model for database"""
    
    __tablename__ = "sessions"
    
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)
    token = Column(String(500), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id})>"


# Pydantic models for API
class UserBase(BaseModel):
    """Base user schema"""

    email: Optional[EmailStr] = None  # Optional for OAuth users
    username: str
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    oauth_provider: Optional[str] = None
    vk_user_id: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema"""

    password: str
    is_admin: Optional[bool] = False
    roles: Optional[List[str]] = ["user"]
    monthly_budget_usd: Optional[int] = 100


class UserUpdate(BaseModel):
    """User update schema"""

    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None
    permissions: Optional[List[str]] = None
    preferences: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    monthly_budget_usd: Optional[int] = None


class UserResponse(UserBase):
    """User response schema"""

    id: int
    is_active: bool
    is_admin: bool
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    roles: List[str] = []
    permissions: List[str] = []
    monthly_budget_usd: int
    current_usage_usd: int

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """User login schema"""

    email: EmailStr
    password: str


class UserToken(BaseModel):
    """User token response"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


# Utility functions for user management
def create_user(db_session, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new user (mock implementation for testing)"""
    email = user_data.get("email", "")
    username = user_data.get("username", "")

    new_user_data = {
        "id": hash(email) % 10000,  # Simple ID generation for testing
        "email": db_session,  # Mock: store session reference
        "username": user_data,
        "full_name": user_data.get("full_name"),
        "is_active": True,
        "is_admin": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "roles": ["user"],
        "permissions": [],
        "monthly_budget_usd": 100,
        "current_usage_usd": 0,
    }
    return new_user_data


def validate_user_data(user_data: Dict[str, Any]) -> bool:
    """Validate user data"""
    try:
        # Check required fields
        required_fields = ["email", "username"]
        for field in required_fields:
            if not user_data.get(field):
                return False

        # Validate email format (basic check)
        email = user_data.get("email", "")
        if "@" not in email or "." not in email:
            return False

        # Validate username length
        username = user_data.get("username", "")
        if len(username) < 3 or len(username) > 50:
            return False

        return True
    except Exception:
        return False


def update_user_profile(
    db_session, user_id: int, update_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Update user profile (mock implementation for testing)"""
    # Mock implementation - in real app would update database
    updated_user = {
        "id": user_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "success": True,
        "session": str(type(db_session).__name__),
    }
    updated_user.update(update_data)
    return updated_user
