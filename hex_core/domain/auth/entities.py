"""
Auth Domain Entities

Pure business entities for authentication domain.
No dependencies on external frameworks or infrastructure.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Set
from enum import Enum
import secrets

from .value_objects import UserId, Email, Password, Token, RefreshToken


class UserStatus(Enum):
    """User account status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class RoleType(Enum):
    """Role type enumeration"""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    GUEST = "guest"


class Entity:
    """Base class for all domain entities"""
    
    def __init__(self, id: str):
        if not id or not id.strip():
            raise ValueError("Entity ID cannot be empty")
        self.id = id
        self.created_at: datetime = datetime.now(timezone.utc)
        self.updated_at: Optional[datetime] = None
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Make entity hashable based on its ID"""
        return hash(self.id)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id='{self.id}')"


@dataclass(frozen=True)
class Permission:
    """Permission entity representing a specific system permission"""
    
    id: str
    name: str
    description: str
    resource: str
    action: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id:
            raise ValueError("Permission ID cannot be empty")
        if not self.name:
            raise ValueError("Permission name cannot be empty")


@dataclass
class Role:
    """Role entity aggregating permissions"""
    
    id: str
    name: str
    description: str
    permissions: Set[Permission] = field(default_factory=set)
    role_type: RoleType = RoleType.USER
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.id:
            raise ValueError("Role ID cannot be empty")
        if not self.name:
            raise ValueError("Role name cannot be empty")
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Role):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Make role hashable based on its ID"""
        return hash(self.id)
    
    def add_permission(self, permission: Permission) -> None:
        """Add permission to role"""
        self.permissions.add(permission)
        self.updated_at = datetime.now(timezone.utc)
    
    def remove_permission(self, permission: Permission) -> None:
        """Remove permission from role"""
        self.permissions.discard(permission)
        self.updated_at = datetime.now(timezone.utc)
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if role has specific permission"""
        return any(p.name == permission_name for p in self.permissions)
    
    @classmethod
    def create(cls, name: str, description: str = "") -> 'Role':
        """Create a new role"""
        return cls(
            id=f"role_{name}",
            name=name,
            description=description
        )


@dataclass
class User:
    """User entity - aggregate root for authentication domain"""
    
    id: UserId
    email: Email
    name: str
    password_hash: Optional[str] = None
    roles: Set[Role] = field(default_factory=set)
    status: UserStatus = UserStatus.ACTIVE
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    profile_data: dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("User name cannot be empty")
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, User):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Make user hashable based on its ID"""
        return hash(self.id.value)
    
    def assign_role(self, role: Role) -> None:
        """Assign role to user"""
        self.roles.add(role)
        self.updated_at = datetime.now(timezone.utc)
    
    def revoke_role(self, role: Role) -> None:
        """Revoke role from user"""
        self.roles.discard(role)
        self.updated_at = datetime.now(timezone.utc)
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has specific permission through their roles"""
        return any(role.has_permission(permission_name) for role in self.roles)
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role"""
        return any(role.name == role_name for role in self.roles)
    
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return any(role.role_type == RoleType.ADMIN for role in self.roles)
    
    def activate(self) -> None:
        """Activate user account"""
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)
    
    def deactivate(self) -> None:
        """Deactivate user account"""
        self.status = UserStatus.INACTIVE
        self.updated_at = datetime.now(timezone.utc)
    
    def suspend(self) -> None:
        """Suspend user account"""
        self.status = UserStatus.SUSPENDED
        self.updated_at = datetime.now(timezone.utc)
    
    def record_login(self) -> None:
        """Record successful login"""
        self.last_login = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def is_active(self) -> bool:
        """Check if user account is active"""
        return self.status == UserStatus.ACTIVE
    
    def update_profile(self, profile_data: dict) -> None:
        """Update user profile data"""
        self.profile_data.update(profile_data)
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class AuthSession:
    """Authentication session entity with JWT support"""
    
    id: str
    user_id: UserId
    token: Token
    refresh_token: RefreshToken
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def __post_init__(self):
        if not self.id:
            raise ValueError("Session ID cannot be empty")
        if self.expires_at <= self.created_at:
            raise ValueError("Session expiration must be in the future")
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, AuthSession):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Make session hashable based on its ID"""
        return hash(self.id)
    
    def is_valid(self) -> bool:
        """Check if session is valid and not expired"""
        return self.is_active and datetime.now(timezone.utc) < self.expires_at
    
    def invalidate(self) -> None:
        """Invalidate the session"""
        self.is_active = False
    
    def extend(self, additional_minutes: int) -> None:
        """Extend session expiration"""
        if self.is_valid():
            self.expires_at = self.expires_at + timedelta(minutes=additional_minutes)
    
    @classmethod
    def create(cls, user_id: UserId, token: Token, refresh_token: RefreshToken) -> 'AuthSession':
        """Create a new authentication session"""
        session_id = secrets.token_urlsafe(32)
        expires_at = token.expires_at or datetime.now(timezone.utc) + timedelta(hours=24)
        
        return cls(
            id=session_id,
            user_id=user_id,
            token=token,
            refresh_token=refresh_token,
            expires_at=expires_at
        ) 