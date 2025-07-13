"""
Auth Repository Adapters - Clean Version

Infrastructure implementations of auth domain ports.
Uses Mock implementations to avoid conflicts with legacy system.
"""

from typing import List, Optional
from datetime import datetime, timezone

from backend.domain.auth.entities import User, Role, Permission, AuthSession
from backend.domain.auth.value_objects import UserId, Email, Token
from backend.application.auth.ports import (
    UserRepositoryPort,
    RoleRepositoryPort,
    PermissionRepositoryPort,
    SessionRepositoryPort
)


# Mock implementations for rapid development
class MockUserRepository(UserRepositoryPort):
    """Mock user repository for development"""
    
    def __init__(self):
        self.users = {}
        self.next_id = 1
    
    async def save(self, user: User) -> User:
        """Save user to memory"""
        if not user.id.value or user.id.value not in self.users:
            user.id = UserId(str(self.next_id))
            self.next_id += 1
        
        self.users[user.id.value] = user
        return user
    
    async def find_by_id(self, user_id: UserId) -> Optional[User]:
        """Find user by ID"""
        return self.users.get(user_id.value)
    
    async def find_by_email(self, email: Email) -> Optional[User]:
        """Find user by email"""
        for user in self.users.values():
            if user.email.value == email.value:
                return user
        return None
    
    async def delete(self, user_id: UserId) -> bool:
        """Delete user"""
        if user_id.value in self.users:
            del self.users[user_id.value]
            return True
        return False
    
    async def list_users(self, offset: int = 0, limit: int = 100) -> List[User]:
        """List users with pagination"""
        users_list = list(self.users.values())
        return users_list[offset:offset + limit]


class MockRoleRepository(RoleRepositoryPort):
    """Mock role repository for development"""
    
    def __init__(self):
        self.roles = {}
        self.next_id = 1
        # Add default roles
        self._create_default_roles()
    
    def _create_default_roles(self):
        """Create default roles"""
        from backend.domain.auth.entities import Role, RoleType
        
        admin_role = Role(
            id=str(self.next_id),
            name="admin",
            description="Administrator role",
            permissions=set(),
            role_type=RoleType.ADMIN,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self.roles[admin_role.id] = admin_role
        self.next_id += 1
        
        user_role = Role(
            id=str(self.next_id),
            name="user",
            description="Regular user role",
            permissions=set(),
            role_type=RoleType.USER,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self.roles[user_role.id] = user_role
        self.next_id += 1
    
    async def save(self, role: Role) -> Role:
        """Save role to memory"""
        if not role.id or role.id not in self.roles:
            role.id = str(self.next_id)
            self.next_id += 1
        
        self.roles[role.id] = role
        return role
    
    async def find_by_id(self, role_id: str) -> Optional[Role]:
        """Find role by ID"""
        return self.roles.get(role_id)
    
    async def find_by_name(self, name: str) -> Optional[Role]:
        """Find role by name"""
        for role in self.roles.values():
            if role.name == name:
                return role
        return None
    
    async def list_roles(self) -> List[Role]:
        """List all roles"""
        return list(self.roles.values())
    
    async def delete(self, role_id: str) -> bool:
        """Delete role"""
        if role_id in self.roles:
            del self.roles[role_id]
            return True
        return False


class MockSessionRepository(SessionRepositoryPort):
    """Mock session repository for development"""
    
    def __init__(self):
        self.sessions = {}
        self.sessions_by_token = {}
    
    async def save(self, session: AuthSession) -> AuthSession:
        """Save session to memory"""
        self.sessions[session.id] = session
        self.sessions_by_token[session.token.value] = session
        return session
    
    async def find_by_id(self, session_id: str) -> Optional[AuthSession]:
        """Find session by ID"""
        return self.sessions.get(session_id)
    
    async def find_by_token(self, token: Token) -> Optional[AuthSession]:
        """Find session by token"""
        return self.sessions_by_token.get(token.value)
    
    async def find_by_refresh_token(self, refresh_token) -> Optional[AuthSession]:
        """Find session by refresh token"""
        for session in self.sessions.values():
            if hasattr(session, 'refresh_token') and session.refresh_token and session.refresh_token.value == refresh_token.value:
                return session
        return None
    
    async def delete(self, session_id: str) -> bool:
        """Delete session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            del self.sessions[session_id]
            if session.token.value in self.sessions_by_token:
                del self.sessions_by_token[session.token.value]
            return True
        return False
    
    async def delete_expired(self) -> int:
        """Delete expired sessions, return count"""
        expired_sessions = []
        current_time = datetime.now(timezone.utc)
        
        for session in self.sessions.values():
            if session.expires_at < current_time or not session.is_active:
                expired_sessions.append(session)
        
        count = len(expired_sessions)
        
        for session in expired_sessions:
            await self.delete(session.id)
        
        return count
    
    async def delete_all_for_user(self, user_id: UserId) -> int:
        """Delete all sessions for user, return count"""
        sessions_to_delete = []
        
        for session in self.sessions.values():
            if session.user_id == user_id:
                sessions_to_delete.append(session)
        
        count = len(sessions_to_delete)
        
        for session in sessions_to_delete:
            await self.delete(session.id)
        
        return count
    
    async def cleanup_expired(self) -> int:
        """Delete expired sessions, return count - alias for delete_expired"""
        return await self.delete_expired()


class MockPermissionRepository(PermissionRepositoryPort):
    """Mock permission repository for development"""
    
    def __init__(self):
        self.permissions = {}
        self.next_id = 1
        # Add default permissions
        self._create_default_permissions()
    
    def _create_default_permissions(self):
        """Create default permissions"""
        default_permissions = [
            ("read", "users", "Read user information"),
            ("write", "users", "Write user information"),
            ("delete", "users", "Delete users"),
            ("read", "roles", "Read role information"),
            ("write", "roles", "Write role information"),
            ("admin", "system", "System administration"),
        ]
        
        for action, resource, description in default_permissions:
            permission = Permission(
                id=str(self.next_id),
                name=f"{action}_{resource}",
                description=description,
                resource=resource,
                action=action,
                created_at=datetime.now(timezone.utc)
            )
            self.permissions[permission.id] = permission
            self.next_id += 1
    
    async def save(self, permission: Permission) -> Permission:
        """Save permission to memory"""
        if not permission.id or permission.id not in self.permissions:
            # Create new permission with generated ID since Permission is frozen
            new_permission = Permission(
                id=str(self.next_id),
                name=permission.name,
                description=permission.description,
                resource=permission.resource,
                action=permission.action,
                created_at=permission.created_at
            )
            self.permissions[new_permission.id] = new_permission
            self.next_id += 1
            return new_permission
        
        self.permissions[permission.id] = permission
        return permission
    
    async def find_by_id(self, permission_id: str) -> Optional[Permission]:
        """Find permission by ID"""
        return self.permissions.get(permission_id)
    
    async def find_by_name(self, name: str) -> Optional[Permission]:
        """Find permission by name"""
        for permission in self.permissions.values():
            if permission.name == name:
                return permission
        return None
    
    async def list_permissions(self) -> List[Permission]:
        """List all permissions"""
        return list(self.permissions.values())


__all__ = [
    "MockUserRepository",
    "MockRoleRepository",
    "MockSessionRepository",
    "MockPermissionRepository"
] 