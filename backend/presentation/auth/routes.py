"""
Auth Presentation Layer

FastAPI routes for authentication endpoints.
This layer handles HTTP requests/responses and delegates to application services.
"""

from datetime import timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

from backend.application.auth.services import AuthApplicationService, RoleManagementService
from backend.infrastructure.dependencies import get_auth_service_safe, get_role_service_safe
from backend.domain.auth.exceptions import (
    AuthDomainError,
    InvalidCredentialsError,
    UserNotFoundError
)

# ============================================================================
# Request/Response Models
# ============================================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class AssignRoleRequest(BaseModel):
    role_name: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    roles: List[str]
    status: str
    last_login: Optional[str] = None
    created_at: str

class SessionResponse(BaseModel):
    id: str
    token: str
    refresh_token: str
    expires_at: str
    is_active: bool

class AuthResponse(BaseModel):
    user: UserResponse
    session: SessionResponse

class TokenRefreshRequest(BaseModel):
    refresh_token: str

# ============================================================================
# Dependencies
# ============================================================================

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthApplicationService = Depends(get_auth_service_safe)
):
    """Get current authenticated user"""
    try:
        user = auth_service.get_user_by_token(credentials.credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

def get_current_admin_user(current_user = Depends(get_current_user)):
    """Get current user and ensure they have admin role"""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

# ============================================================================
# Router
# ============================================================================

router = APIRouter(tags=["authentication"])

# ============================================================================
# Authentication Endpoints
# ============================================================================

@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    background_tasks: BackgroundTasks,
    auth_service: AuthApplicationService = Depends(get_auth_service_safe)
):
    """Register a new user"""
    try:
        user = await auth_service.register_user(
            email=request.email,
            name=request.name,
            password=request.password
        )
        
        # Create session for new user
        user, session = await auth_service.authenticate_user(
            email=request.email,
            password=request.password
        )
        
        return AuthResponse(
            user=UserResponse(
                id=user.id.value if hasattr(user.id, 'value') else str(user.id),
                email=user.email.value if hasattr(user.email, 'value') else str(user.email),
                name=user.name,
                roles=[role.name for role in user.roles] if user.roles else [],
                status=user.status.value if hasattr(user.status, 'value') else str(user.status),
                last_login=user.last_login.isoformat() if user.last_login else None,
                created_at=user.created_at.isoformat() if user.created_at else "2024-01-01T00:00:00"
            ),
            session=SessionResponse(
                id=session.id,
                token=session.token.value if hasattr(session.token, 'value') else str(session.token),
                refresh_token="",  # Would implement refresh token logic
                expires_at=session.expires_at.isoformat() if session.expires_at else "2024-12-31T23:59:59",
                is_active=session.is_active
            )
        )
        
    except AuthDomainError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthApplicationService = Depends(get_auth_service_safe)
):
    """Authenticate user and create session"""
    try:
        user, session = await auth_service.authenticate_user(
            email=request.email,
            password=request.password
        )
        
        return AuthResponse(
            user=UserResponse(
                id=user.id.value if hasattr(user.id, 'value') else str(user.id),
                email=user.email.value if hasattr(user.email, 'value') else str(user.email),
                name=user.name,
                roles=[role.name for role in user.roles] if user.roles else [],
                status=user.status.value if hasattr(user.status, 'value') else str(user.status),
                last_login=user.last_login.isoformat() if user.last_login else None,
                created_at=user.created_at.isoformat() if user.created_at else "2024-01-01T00:00:00"
            ),
            session=SessionResponse(
                id=session.id,
                token=session.token.value if hasattr(session.token, 'value') else str(session.token),
                refresh_token="",  # Would implement refresh token logic
                expires_at=session.expires_at.isoformat() if session.expires_at else "2024-12-31T23:59:59",
                is_active=session.is_active
            )
        )
        
    except (InvalidCredentialsError, UserNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthApplicationService = Depends(get_auth_service_safe)
):
    """Logout user by invalidating session"""
    try:
        await auth_service.logout(credentials.credentials)
        return {"message": "Successfully logged out"}
    except Exception:
        # Even if logout fails, return success for security
        return {"message": "Successfully logged out"}

@router.post("/refresh", response_model=SessionResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    auth_service: AuthApplicationService = Depends(get_auth_service_safe)
):
    """Refresh access token"""
    try:
        user, session = await auth_service.refresh_token(request.refresh_token)
        
        return SessionResponse(
            id=session.id,
            token=session.token.value if hasattr(session.token, 'value') else str(session.token),
            refresh_token="",  # Would return new refresh token
            expires_at=session.expires_at.isoformat() if session.expires_at else "2024-12-31T23:59:59",
            is_active=session.is_active
        )
        
    except (InvalidCredentialsError, UserNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

# ============================================================================
# User Profile Endpoints
# ============================================================================

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(
        id=current_user.id.value if hasattr(current_user.id, 'value') else str(current_user.id),
        email=current_user.email.value if hasattr(current_user.email, 'value') else str(current_user.email),
        name=current_user.name,
        roles=[role.name for role in current_user.roles] if current_user.roles else [],
        status=current_user.status.value if hasattr(current_user.status, 'value') else str(current_user.status),
        last_login=current_user.last_login.isoformat() if current_user.last_login else None,
        created_at=current_user.created_at.isoformat() if current_user.created_at else "2024-01-01T00:00:00"
    )

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    name: str,
    current_user = Depends(get_current_user),
    auth_service: AuthApplicationService = Depends(get_auth_service_safe)
):
    """Update user profile"""
    try:
        # Update user name
        current_user.name = name
        updated_user = await auth_service.user_repository.save(current_user)
        
        return UserResponse(
            id=updated_user.id.value if hasattr(updated_user.id, 'value') else str(updated_user.id),
            email=updated_user.email.value if hasattr(updated_user.email, 'value') else str(updated_user.email),
            name=updated_user.name,
            roles=[role.name for role in updated_user.roles] if updated_user.roles else [],
            status=updated_user.status.value if hasattr(updated_user.status, 'value') else str(updated_user.status),
            last_login=updated_user.last_login.isoformat() if updated_user.last_login else None,
            created_at=updated_user.created_at.isoformat() if updated_user.created_at else "2024-01-01T00:00:00"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user = Depends(get_current_user),
    auth_service: AuthApplicationService = Depends(get_auth_service_safe)
):
    """Change user password"""
    try:
        await auth_service.change_password(
            user_id=current_user.id.value if hasattr(current_user.id, 'value') else str(current_user.id),
            old_password=request.old_password,
            new_password=request.new_password
        )
        
        return {"message": "Password changed successfully"}
        
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ============================================================================
# Role Management Endpoints (Admin Only)
# ============================================================================

@router.post("/users/{user_id}/roles")
async def assign_role_to_user(
    user_id: str,
    request: AssignRoleRequest,
    current_admin = Depends(get_current_admin_user),
    auth_service: AuthApplicationService = Depends(get_auth_service_safe)
):
    """Assign role to user (admin only)"""
    try:
        await auth_service.assign_role(user_id, request.role_name)
        return {"message": f"Role {request.role_name} assigned to user {user_id}"}
        
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except AuthDomainError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/users/{user_id}/roles/{role_name}")
async def revoke_role_from_user(
    user_id: str,
    role_name: str,
    current_admin = Depends(get_current_admin_user),
    auth_service: AuthApplicationService = Depends(get_auth_service_safe)
):
    """Revoke role from user (admin only)"""
    try:
        await auth_service.revoke_role(user_id, role_name)
        return {"message": f"Role {role_name} revoked from user {user_id}"}
        
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except AuthDomainError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ============================================================================
# Permission Check Endpoints
# ============================================================================

@router.post("/permissions/check")
async def check_permission(
    permission: str,
    current_user = Depends(get_current_user),
    auth_service: AuthApplicationService = Depends(get_auth_service_safe)
):
    """Check if current user has specific permission"""
    has_permission = await auth_service.authorize_user(
        user_id=current_user.id.value if hasattr(current_user.id, 'value') else str(current_user.id),
        required_permission=permission
    )
    
    return {"hasPermission": has_permission}

@router.get("/permissions")
async def get_user_permissions(current_user = Depends(get_current_user)):
    """Get all permissions for current user"""
    permissions = []
    if current_user.roles:
        for role in current_user.roles:
            for permission in role.permissions:
                if permission.name not in permissions:
                    permissions.append(permission.name)
    
    return permissions

# ============================================================================
# Session Management
# ============================================================================

@router.post("/sessions/cleanup")
async def cleanup_expired_sessions(
    current_admin = Depends(get_current_admin_user),
    auth_service: AuthApplicationService = Depends(get_auth_service_safe)
):
    """Cleanup expired sessions (admin only)"""
    try:
        count = await auth_service.cleanup_expired_sessions()
        return {"message": f"Cleaned up {count} expired sessions"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ============================================================================
# Router Factory Function
# ============================================================================

def create_auth_router(container = None) -> APIRouter:
    """
    Create authentication router with dependency injection
    
    Args:
        container: DI container for service resolution
        
    Returns:
        Configured APIRouter instance
    """
    # The router is already configured above, just return it
    return router 