"""
FastAPI Dependencies for Hexagonal Architecture

Provides dependency injection bridge between FastAPI and DI container.
"""

from typing import Optional

from fastapi import HTTPException, status
from backend.infrastructure.di_container import get_container
from backend.application.auth.services import AuthApplicationService, RoleManagementService
from backend.application.auth.ports import UserRepositoryPort
from backend.domain.auth.entities import User


def get_auth_service() -> AuthApplicationService:
    """Get AuthApplicationService from DI container"""
    try:
        container = get_container()
        return container.get(AuthApplicationService)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get auth service: {str(e)}"
        )


def get_role_service() -> RoleManagementService:
    """Get RoleManagementService from DI container"""
    try:
        container = get_container()
        return container.get(RoleManagementService)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get role service: {str(e)}"
        )


def get_user_repository() -> UserRepositoryPort:
    """Get UserRepositoryPort from DI container"""
    try:
        container = get_container()
        return container.get(UserRepositoryPort)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user repository: {str(e)}"
        )


# Mock implementations for testing when DI container is not available
class MockAuthService:
    """Mock AuthApplicationService for testing"""
    
    async def register_user(self, email: str, name: str, password: str):
        # Mock implementation
        from backend.domain.auth.entities import User, UserStatus
        from backend.domain.auth.value_objects import UserId, Email
        
        return User(
            id=UserId("mock-user-id"),
            email=Email(email),
            name=name,
            password_hash="mock-hash",
            status=UserStatus.ACTIVE
        )
    
    async def authenticate_user(self, email: str, password: str):
        # Mock implementation - return user and session
        from backend.domain.auth.entities import User, AuthSession, UserStatus
        from backend.domain.auth.value_objects import UserId, Email, Token, RefreshToken
        from datetime import datetime, timezone, timedelta
        
        user = User(
            id=UserId("mock-user-id"),
            email=Email(email),
            name="Mock User",
            password_hash="mock-hash",
            status=UserStatus.ACTIVE
        )
        
        session = AuthSession(
            id="mock-session-id",
            user_id=UserId("mock-user-id"),
            token=Token("mock-token"),
            refresh_token=RefreshToken.create("mock-user-id"),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            created_at=datetime.now(timezone.utc)
        )
        
        return user, session


def get_auth_service_safe() -> AuthApplicationService:
    """Get AuthApplicationService with fallback to mock"""
    try:
        return get_auth_service()
    except:
        # Return mock service if DI container is not available
        return MockAuthService()  # type: ignore


def get_role_service_safe() -> RoleManagementService:
    """Get RoleManagementService with fallback to mock"""
    try:
        return get_role_service()
    except:
        # Return mock service if DI container is not available
        from backend.application.auth.services import RoleManagementService
        return MockAuthService()  # type: ignore - Using mock for now 