"""
Auth Application Ports

Defines interfaces (ports) for authentication domain.
These ports will be implemented by adapters in the infrastructure layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from backend.domain.auth.entities import User, Role, Permission, AuthSession
from backend.domain.auth.value_objects import UserId, Email, Token


class UserRepositoryPort(ABC):
    """Port for user persistence operations"""
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """Save user to persistence layer"""
        pass
    
    @abstractmethod
    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        """Find user by ID"""
        pass
    
    @abstractmethod
    async def find_by_email(self, email: Email) -> Optional[User]:
        """Find user by email"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: UserId) -> bool:
        """Delete user"""
        pass
    
    @abstractmethod
    async def list_users(self, offset: int = 0, limit: int = 100) -> List[User]:
        """List users with pagination"""
        pass


class RoleRepositoryPort(ABC):
    """Port for role persistence operations"""
    
    @abstractmethod
    async def save(self, role: Role) -> Role:
        """Save role to persistence layer"""
        pass
    
    @abstractmethod
    async def find_by_id(self, role_id: str) -> Optional[Role]:
        """Find role by ID"""
        pass
    
    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Role]:
        """Find role by name"""
        pass
    
    @abstractmethod
    async def delete(self, role_id: str) -> bool:
        """Delete role"""
        pass
    
    @abstractmethod
    async def list_roles(self) -> List[Role]:
        """List all roles"""
        pass


class PermissionRepositoryPort(ABC):
    """Port for permission persistence operations"""
    
    @abstractmethod
    async def save(self, permission: Permission) -> Permission:
        """Save permission to persistence layer"""
        pass
    
    @abstractmethod
    async def find_by_id(self, permission_id: str) -> Optional[Permission]:
        """Find permission by ID"""
        pass
    
    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Permission]:
        """Find permission by name"""
        pass
    
    @abstractmethod
    async def list_permissions(self) -> List[Permission]:
        """List all permissions"""
        pass


class SessionRepositoryPort(ABC):
    """Port for session persistence operations"""
    
    @abstractmethod
    async def save(self, session: AuthSession) -> AuthSession:
        """Save session to persistence layer"""
        pass
    
    @abstractmethod
    async def find_by_id(self, session_id: str) -> Optional[AuthSession]:
        """Find session by ID"""
        pass
    
    @abstractmethod
    async def find_by_token(self, token_value: str) -> Optional[AuthSession]:
        """Find session by access token value"""
        pass
    
    @abstractmethod
    async def find_by_refresh_token(self, refresh_token_value: str) -> Optional[AuthSession]:
        """Find session by refresh token value"""
        pass
    
    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Delete session"""
        pass
    
    @abstractmethod
    async def delete_all_for_user(self, user_id: UserId) -> int:
        """Delete all sessions for user, return count"""
        pass
    
    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Delete expired sessions, return count"""
        pass


class PasswordHasherPort(ABC):
    """Port for password hashing operations"""
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        pass
    
    @abstractmethod
    def verify_password(self, password: str, hash_value: str) -> bool:
        """Verify password against hash"""
        pass


class TokenGeneratorPort(ABC):
    """Port for token generation operations"""
    
    @abstractmethod
    async def generate_jwt(self, payload: Dict[str, Any]) -> str:
        """Generate JWT token from payload"""
        pass
    
    @abstractmethod
    def generate_access_token(self, user_id: UserId, expires_in: timedelta) -> Token:
        """Generate access token"""
        pass
    
    @abstractmethod
    def generate_refresh_token(self, user_id: UserId) -> Token:
        """Generate refresh token"""
        pass
    
    @abstractmethod
    def validate_token(self, token: Token) -> bool:
        """Validate token"""
        pass


class EmailServicePort(ABC):
    """Port for email operations"""
    
    @abstractmethod
    async def send_welcome_email(self, user: User) -> bool:
        """Send welcome email to user"""
        pass
    
    @abstractmethod
    async def send_password_reset_email(self, user: User, reset_token: str) -> bool:
        """Send password reset email"""
        pass
    
    @abstractmethod
    async def send_verification_email(self, user: User, verification_token: str) -> bool:
        """Send email verification"""
        pass


class EventPublisherPort(ABC):
    """Port for domain event publishing"""
    
    @abstractmethod
    async def publish_user_created(self, user: User) -> None:
        """Publish user created event"""
        pass
    
    @abstractmethod
    async def publish_user_logged_in(self, user: User) -> None:
        """Publish user logged in event"""
        pass
    
    @abstractmethod
    async def publish_user_logged_out(self, user: User) -> None:
        """Publish user logged out event"""
        pass
    
    @abstractmethod
    async def publish_role_assigned(self, user: User, role: Role) -> None:
        """Publish role assigned event"""
        pass
    
    @abstractmethod
    async def publish_role_revoked(self, user: User, role: Role) -> None:
        """Publish role revoked event"""
        pass
    
    @abstractmethod
    async def publish_user_authenticated(self, user: User) -> None:
        """Publish user authenticated event"""
        pass
    
    @abstractmethod
    async def publish_user_role_changed(self, user: User, old_roles: List[Role], new_roles: List[Role]) -> None:
        """Publish user role changed event"""
        pass
    
    @abstractmethod
    async def publish_password_changed(self, user: User) -> None:
        """Publish password changed event"""
        pass 