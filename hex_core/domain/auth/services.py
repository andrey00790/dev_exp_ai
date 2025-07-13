"""
Auth Domain Services

Pure domain services containing business logic.
No dependencies on infrastructure or external frameworks.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from .entities import User, Role, Permission, AuthSession
from .value_objects import UserId, Email, Password, Token
from .exceptions import InvalidCredentialsError, UserNotFoundError


class PasswordService:
    """Domain service for password-related operations"""
    
    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """Generate a secure random password"""
        if length < 8:
            raise ValueError("Password length must be at least 8 characters")
        
        # Generate password with mixed characters
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Ensure complexity requirements
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            # Regenerate if doesn't meet requirements
            return PasswordService.generate_secure_password(length)
        
        return password
    
    @staticmethod
    def hash_password(password: Password) -> str:
        """Hash password with salt"""
        return password.hash()
    
    @staticmethod
    def verify_password(password: Password, hash_value: str) -> bool:
        """Verify password against hash"""
        return password.verify(hash_value)


class AuthDomainService:
    """Domain service for authentication business logic"""
    
    def __init__(self):
        self.password_service = PasswordService()
    
    def authenticate_user(self, email: Email, password: Password, user: Optional[User]) -> User:
        """Authenticate user with email and password"""
        if user is None:
            raise UserNotFoundError(f"User with email {email} not found")
        
        if not user.is_active():
            raise InvalidCredentialsError("User account is not active")
        
        if user.password_hash is None:
            raise InvalidCredentialsError("User has no password set")
        
        if not self.password_service.verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid password")
        
        # Record successful login
        user.record_login()
        return user
    
    def create_user(self, email: Email, name: str, password: Password) -> User:
        """Create new user with validated data"""
        # Generate user ID (would typically be handled by repository)
        user_id = UserId(secrets.token_hex(16))
        
        # Hash password
        password_hash = self.password_service.hash_password(password)
        
        # Create user entity
        user = User(
            id=user_id,
            email=email,
            name=name,
            password_hash=password_hash
        )
        
        return user
    
    def change_password(self, user: User, old_password: Password, new_password: Password) -> None:
        """Change user password"""
        if user.password_hash is None:
            raise InvalidCredentialsError("User has no current password")
        
        # Verify old password
        if not self.password_service.verify_password(old_password, user.password_hash):
            raise InvalidCredentialsError("Current password is incorrect")
        
        # Set new password
        user.password_hash = self.password_service.hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
    
    def reset_password(self, user: User, new_password: Password) -> None:
        """Reset user password (admin operation)"""
        user.password_hash = self.password_service.hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
    
    def create_session(self, user: User, expires_in_hours: int = 24) -> AuthSession:
        """Create authentication session for user"""
        # Generate session ID and token
        session_id = secrets.token_hex(16)
        token = Token.generate(expires_in_hours=expires_in_hours)
        
        # Create session
        session = AuthSession(
            id=session_id,
            user_id=user.id,
            token=token,
            expires_at=token.expires_at or datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        )
        
        return session
    
    def validate_session(self, session: AuthSession) -> bool:
        """Validate authentication session"""
        return session.is_valid()
    
    def authorize_user(self, user: User, required_permission: str) -> bool:
        """Check if user has required permission"""
        if not user.is_active():
            return False
        
        return user.has_permission(required_permission)
    
    def authorize_role(self, user: User, required_role: str) -> bool:
        """Check if user has required role"""
        if not user.is_active():
            return False
        
        return user.has_role(required_role)
    
    def assign_role(self, user: User, role: Role) -> None:
        """Assign role to user"""
        user.add_role(role)
    
    def revoke_role(self, user: User, role: Role) -> None:
        """Revoke role from user"""
        user.remove_role(role)


class RoleManagementService:
    """Domain service for role and permission management"""
    
    def create_role(self, name: str, description: str, permissions: list[Permission]) -> Role:
        """Create new role with permissions"""
        role_id = secrets.token_hex(8)
        role = Role(
            id=role_id,
            name=name,
            description=description,
            permissions=set(permissions)
        )
        return role
    
    def create_permission(self, name: str, description: str, resource: str, action: str) -> Permission:
        """Create new permission"""
        permission_id = secrets.token_hex(8)
        permission = Permission(
            id=permission_id,
            name=name,
            description=description,
            resource=resource,
            action=action
        )
        return permission
    
    def add_permission_to_role(self, role: Role, permission: Permission) -> None:
        """Add permission to role"""
        role.add_permission(permission)
    
    def remove_permission_from_role(self, role: Role, permission: Permission) -> None:
        """Remove permission from role"""
        role.remove_permission(permission) 