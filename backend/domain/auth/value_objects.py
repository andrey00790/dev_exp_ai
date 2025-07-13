"""
Auth Domain Value Objects

Immutable value objects for authentication domain.
Following hexagonal architecture principles.
"""

import hashlib
import re
import secrets
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone, timedelta


@dataclass(frozen=True)
class UserId:
    """User identifier value object"""
    
    value: str
    
    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("UserId must be a non-empty string")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)  
class Email:
    """Email value object with validation"""
    
    value: str
    
    def __post_init__(self):
        if not self.value or "@" not in self.value:
            raise ValueError("Invalid email format")
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def domain(self) -> str:
        """Get email domain"""
        return self.value.split('@')[1]
    
    @property 
    def local_part(self) -> str:
        """Get email local part (before @)"""
        return self.value.split('@')[0]


@dataclass(frozen=True)
class Password:
    """Password value object with strength validation"""
    
    value: str
    
    def __post_init__(self):
        if not self.value or len(self.value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for at least one uppercase, lowercase, and digit
        if not any(c.isupper() for c in self.value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in self.value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in self.value):
            raise ValueError("Password must contain at least one digit")
    
    def hash(self, salt: Optional[str] = None) -> str:
        """Generate password hash"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        password_salt = f"{self.value}{salt}"
        hash_value = hashlib.sha256(password_salt.encode()).hexdigest()
        return f"{salt}:{hash_value}"
    
    def verify(self, hash_value: str) -> bool:
        """Verify password against hash"""
        try:
            salt, stored_hash = hash_value.split(':', 1)
            password_salt = f"{self.value}{salt}"
            computed_hash = hashlib.sha256(password_salt.encode()).hexdigest()
            return computed_hash == stored_hash
        except (ValueError, AttributeError):
            return False


@dataclass(frozen=True)
class Token:
    """JWT access token value object"""
    value: str
    token_type: str = "bearer"
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Token value cannot be empty")
        if self.token_type not in ["bearer", "basic"]:
            raise ValueError("Token type must be 'bearer' or 'basic'")
    
    def is_expired(self) -> bool:
        """Check if token is expired"""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    @classmethod
    def create_access_token(cls, payload: str, expires_in_minutes: int = 15):
        """Create a new access token with expiration"""
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        return cls(
            value=payload,
            token_type="bearer", 
            expires_at=expires_at
        )


@dataclass(frozen=True)
class RefreshToken:
    """JWT refresh token value object"""
    value: str
    expires_at: datetime
    user_id: str
    jti: str  # JWT ID for token blacklisting
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Refresh token value cannot be empty")
        if not self.user_id:
            raise ValueError("User ID cannot be empty")
        if not self.jti:
            raise ValueError("JWT ID cannot be empty")
        if self.expires_at <= datetime.now(timezone.utc):
            raise ValueError("Refresh token cannot be expired at creation")
    
    def is_expired(self) -> bool:
        """Check if refresh token is expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    def is_about_to_expire(self, threshold_days: int = 7) -> bool:
        """Check if refresh token will expire soon"""
        threshold = datetime.now(timezone.utc) + timedelta(days=threshold_days)
        return self.expires_at <= threshold
    
    @classmethod
    def create(cls, user_id: str, expires_in_days: int = 30):
        """Create a new refresh token"""
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        jti = secrets.token_urlsafe(32)
        
        # Create token value (would be JWT in real implementation)
        token_payload = f"{user_id}:{jti}:{expires_at.isoformat()}"
        token_value = hashlib.sha256(token_payload.encode()).hexdigest()
        
        return cls(
            value=token_value,
            expires_at=expires_at,
            user_id=user_id,
            jti=jti
        ) 