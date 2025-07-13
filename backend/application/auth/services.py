"""
Auth Application Layer

Use case orchestration for authentication functionality.
This layer coordinates domain logic and external services.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from backend.domain.auth.entities import User, AuthSession
from backend.domain.auth.value_objects import UserId, Email, Password, Token, RefreshToken
from backend.domain.auth.exceptions import AuthDomainError, InvalidCredentialsError, UserNotFoundError
from backend.domain.auth.services import AuthDomainService

from backend.application.auth.ports import (
    UserRepositoryPort, RoleRepositoryPort, SessionRepositoryPort,
    PasswordHasherPort, TokenGeneratorPort, EmailServicePort, EventPublisherPort
)


class AuthApplicationService:
    """Application service for authentication use cases"""
    
    def __init__(
        self,
        user_repository: UserRepositoryPort,
        role_repository: RoleRepositoryPort,
        session_repository: SessionRepositoryPort,
        password_hasher: PasswordHasherPort,
        token_generator: TokenGeneratorPort,
        email_service: EmailServicePort,
        event_publisher: EventPublisherPort
    ):
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.session_repository = session_repository
        self.password_hasher = password_hasher
        self.token_generator = token_generator
        self.email_service = email_service
        self.event_publisher = event_publisher
        
        # Domain services
        self.auth_domain_service = AuthDomainService()
    
    async def register_user(self, email: str, name: str, password: str) -> User:
        """Register new user"""
        # Check if user already exists
        existing_user = await self.user_repository.find_by_email(Email(email))
        if existing_user:
            raise AuthDomainError(f"User with email {email} already exists")
        
        # Create user entity
        email_vo = Email(email)
        password_vo = Password(password)
        user = self.auth_domain_service.create_user(email_vo, name, password_vo)
        
        # Hash password using infrastructure
        user.password_hash = self.password_hasher.hash_password(password)
        
        # Save user
        saved_user = await self.user_repository.save(user)
        
        # Send welcome email
        await self.email_service.send_welcome_email(saved_user)
        
        # Publish event
        await self.event_publisher.publish_user_created(saved_user)
        
        return saved_user
    
    async def authenticate_user(self, email: str, password: str) -> Tuple[User, AuthSession]:
        """Authenticate user and create session with JWT tokens"""
        # Find user
        user = await self.user_repository.find_by_email(Email(email))
        if not user:
            raise InvalidCredentialsError("Invalid email or password")
        
        # Check if user has password hash
        if not user.password_hash:
            raise InvalidCredentialsError("User has no password set")
        
        # Verify password
        if not self.password_hasher.verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
        
        # Check if user is active
        if not user.is_active():
            raise AuthDomainError("User account is inactive")
        
        # Generate JWT tokens
        access_token = await self.generate_access_token(user)
        refresh_token = await self.generate_refresh_token(user)
        
        # Create session
        session = AuthSession.create(
            user_id=user.id,
            token=access_token,
            refresh_token=refresh_token
        )
        
        # Save session
        saved_session = await self.session_repository.save(session)
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await self.user_repository.save(user)
        
        # Publish event
        await self.event_publisher.publish_user_logged_in(user)
        
        return user, saved_session
    
    async def refresh_access_token(self, refresh_token_value: str) -> Tuple[User, AuthSession]:
        """Refresh access token using refresh token"""
        # Find session by refresh token
        session = await self.session_repository.find_by_refresh_token(refresh_token_value)
        if not session:
            raise InvalidCredentialsError("Invalid refresh token")
        
        # Check if refresh token is expired
        if session.refresh_token.is_expired():
            # Clean up expired session
            await self.session_repository.delete(session.id)
            raise InvalidCredentialsError("Refresh token expired")
        
        # Get user
        user = await self.user_repository.find_by_id(session.user_id)
        if not user or not user.is_active():
            raise InvalidCredentialsError("User not found or inactive")
        
        # Generate new access token
        new_access_token = await self.generate_access_token(user)
        
        # Optionally rotate refresh token if it's about to expire
        new_refresh_token = session.refresh_token
        if session.refresh_token.is_about_to_expire():
            new_refresh_token = await self.generate_refresh_token(user)
        
        # Update session
        session.token = new_access_token
        session.refresh_token = new_refresh_token
        session.last_activity = datetime.now(timezone.utc)
        
        # Save updated session
        saved_session = await self.session_repository.save(session)
        
        return user, saved_session
    
    async def logout(self, token_value: str) -> None:
        """Logout user by invalidating session"""
        # Find session by token
        session = await self.session_repository.find_by_token(token_value)
        if session:
            # Invalidate session
            await self.session_repository.delete(session.id)
            
            # Publish event
            user = await self.user_repository.find_by_id(session.user_id)
            if user:
                await self.event_publisher.publish_user_logged_out(user)
    
    async def get_user_by_token(self, token_value: str) -> Optional[User]:
        """Get user by access token"""
        # Find session by token
        session = await self.session_repository.find_by_token(token_value)
        if not session:
            return None
        
        # Check if token is expired
        if session.token.is_expired():
            # Clean up expired session
            await self.session_repository.delete(session.id)
            return None
        
        # Get user
        user = await self.user_repository.find_by_id(session.user_id)
        if not user or not user.is_active():
            return None
        
        # Update last activity (session is mutable)
        import dataclasses
        updated_session = dataclasses.replace(session, last_activity=datetime.now(timezone.utc))
        await self.session_repository.save(updated_session)
        
        return user
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> None:
        """Change user password"""
        # Get user
        user = await self.user_repository.find_by_id(UserId(user_id))
        if not user:
            raise UserNotFoundError("User not found")
        
        # Check if user has password hash
        if not user.password_hash:
            raise InvalidCredentialsError("User has no password set")
        
        # Verify old password (user.password_hash is guaranteed to be str after check above)
        assert user.password_hash is not None  # for type checker
        if not self.password_hasher.verify_password(old_password, user.password_hash):
            raise InvalidCredentialsError("Current password is incorrect")
        
        # Hash new password
        new_password_hash = self.password_hasher.hash_password(new_password)
        
        # Update password
        user.password_hash = new_password_hash
        await self.user_repository.save(user)
        
        # Invalidate all sessions for security
        await self.session_repository.delete_all_for_user(user.id)
        
        # Publish event
        await self.event_publisher.publish_password_changed(user)
    
    async def assign_role(self, user_id: str, role_name: str) -> None:
        """Assign role to user"""
        # Get user
        user = await self.user_repository.find_by_id(UserId(user_id))
        if not user:
            raise UserNotFoundError("User not found")
        
        # Get role
        role = await self.role_repository.find_by_name(role_name)
        if not role:
            raise AuthDomainError(f"Role {role_name} not found")
        
        # Assign role
        user.assign_role(role)
        await self.user_repository.save(user)
        
        # Publish event
        await self.event_publisher.publish_role_assigned(user, role)
    
    async def revoke_role(self, user_id: str, role_name: str) -> None:
        """Revoke role from user"""
        # Get user
        user = await self.user_repository.find_by_id(UserId(user_id))
        if not user:
            raise UserNotFoundError("User not found")
        
        # Get role
        role = await self.role_repository.find_by_name(role_name)
        if not role:
            raise AuthDomainError(f"Role {role_name} not found")
        
        # Revoke role
        user.revoke_role(role)
        await self.user_repository.save(user)
        
        # Publish event
        await self.event_publisher.publish_role_revoked(user, role)
    
    async def authorize_user(self, user_id: str, required_permission: str) -> bool:
        """Check if user has required permission"""
        user = await self.user_repository.find_by_id(UserId(user_id))
        if not user:
            return False
        
        return user.has_permission(required_permission)
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        return await self.session_repository.cleanup_expired()
    
    async def generate_access_token(self, user: User) -> Token:
        """Generate JWT access token for user"""
        # Create token payload
        payload = {
            "sub": user.id.value,
            "email": user.email.value,
            "name": user.name,
            "roles": [role.name for role in user.roles],
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),  # 15 minutes
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }
        
        # Generate JWT token
        jwt_token = await self.token_generator.generate_jwt(payload)
        
        return Token.create_access_token(jwt_token, expires_in_minutes=15)
    
    async def generate_refresh_token(self, user: User) -> RefreshToken:
        """Generate JWT refresh token for user"""
        return RefreshToken.create(user.id.value, expires_in_days=30)


class RoleManagementService:
    """Application service for role management"""
    
    def __init__(self, role_repository: RoleRepositoryPort):
        self.role_repository = role_repository
    
    async def create_role(self, name: str, description: str = "") -> None:
        """Create new role"""
        # Check if role already exists
        existing_role = await self.role_repository.find_by_name(name)
        if existing_role:
            raise AuthDomainError(f"Role {name} already exists")
        
        # Create and save role
        from backend.domain.auth.entities import Role
        role = Role.create(name, description)
        await self.role_repository.save(role)
    
    async def delete_role(self, name: str) -> None:
        """Delete role"""
        role = await self.role_repository.find_by_name(name)
        if not role:
            raise AuthDomainError(f"Role {name} not found")
        
        await self.role_repository.delete(role.id) 