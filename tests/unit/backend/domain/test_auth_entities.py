"""
Unit Tests for Auth Domain Entities

Tests for pure domain logic without external dependencies.
Following hexagonal architecture testing principles.
"""

import pytest
from datetime import datetime, timezone, timedelta

from backend.domain.auth.entities import (
    User, Role, Permission, AuthSession,
    UserStatus, RoleType
)
from backend.domain.auth.value_objects import UserId, Email, Password, Token


class TestPermission:
    """Test Permission entity"""
    
    def test_create_permission_success(self):
        """Test successful permission creation"""
        permission = Permission(
            id="perm_read",
            name="read_users",
            description="Can read user data",
            resource="users",
            action="read"
        )
        
        assert permission.id == "perm_read"
        assert permission.name == "read_users"
        assert permission.resource == "users"
        assert permission.action == "read"
        assert isinstance(permission.created_at, datetime)
    
    def test_create_permission_empty_id_fails(self):
        """Test permission creation fails with empty ID"""
        with pytest.raises(ValueError, match="Permission ID cannot be empty"):
            Permission(
                id="",
                name="read_users",
                description="Can read user data",
                resource="users",
                action="read"
            )
    
    def test_create_permission_empty_name_fails(self):
        """Test permission creation fails with empty name"""
        with pytest.raises(ValueError, match="Permission name cannot be empty"):
            Permission(
                id="perm_read",
                name="",
                description="Can read user data",
                resource="users",
                action="read"
            )


class TestRole:
    """Test Role entity"""
    
    def test_create_role_success(self):
        """Test successful role creation"""
        role = Role(
            id="role_admin",
            name="admin",
            description="Administrator role",
            role_type=RoleType.ADMIN
        )
        
        assert role.id == "role_admin"
        assert role.name == "admin"
        assert role.role_type == RoleType.ADMIN
        assert len(role.permissions) == 0
        assert isinstance(role.created_at, datetime)
    
    def test_add_permission_to_role(self):
        """Test adding permission to role"""
        role = Role(
            id="role_admin",
            name="admin",
            description="Administrator role"
        )
        
        permission = Permission(
            id="perm_read",
            name="read_users",
            description="Can read user data",
            resource="users",
            action="read"
        )
        
        role.add_permission(permission)
        
        assert len(role.permissions) == 1
        assert permission in role.permissions
        assert role.updated_at is not None
    
    def test_remove_permission_from_role(self):
        """Test removing permission from role"""
        role = Role(
            id="role_admin",
            name="admin",
            description="Administrator role"
        )
        
        permission = Permission(
            id="perm_read",
            name="read_users",
            description="Can read user data",
            resource="users",
            action="read"
        )
        
        role.add_permission(permission)
        role.remove_permission(permission)
        
        assert len(role.permissions) == 0
        assert permission not in role.permissions
    
    def test_has_permission(self):
        """Test checking if role has permission"""
        role = Role(
            id="role_admin",
            name="admin",
            description="Administrator role"
        )
        
        permission = Permission(
            id="perm_read",
            name="read_users",
            description="Can read user data",
            resource="users",
            action="read"
        )
        
        role.add_permission(permission)
        
        assert role.has_permission("read_users") is True
        assert role.has_permission("write_users") is False


class TestUser:
    """Test User entity"""
    
    def test_create_user_success(self):
        """Test successful user creation"""
        user = User(
            id=UserId("user_123"),
            email=Email("test@example.com"),
            name="Test User",
            password_hash="hashed_password"
        )
        
        assert user.id.value == "user_123"
        assert user.email.value == "test@example.com"
        assert user.name == "Test User"
        assert user.status == UserStatus.ACTIVE
        assert len(user.roles) == 0
        assert isinstance(user.created_at, datetime)
    
    def test_create_user_empty_name_fails(self):
        """Test user creation fails with empty name"""
        with pytest.raises(ValueError, match="User name cannot be empty"):
            User(
                id=UserId("user_123"),
                email=Email("test@example.com"),
                name="   ",
                password_hash="hashed_password"
            )
    
    def test_add_role_to_user(self):
        """Test adding role to user"""
        user = User(
            id=UserId("user_123"),
            email=Email("test@example.com"),
            name="Test User"
        )
        
        role = Role(
            id="role_admin",
            name="admin",
            description="Administrator role"
        )
        
        user.add_role(role)
        
        assert len(user.roles) == 1
        assert role in user.roles
        assert user.updated_at is not None
    
    def test_remove_role_from_user(self):
        """Test removing role from user"""
        user = User(
            id=UserId("user_123"),
            email=Email("test@example.com"),
            name="Test User"
        )
        
        role = Role(
            id="role_admin",
            name="admin",
            description="Administrator role"
        )
        
        user.add_role(role)
        user.remove_role(role)
        
        assert len(user.roles) == 0
        assert role not in user.roles
    
    def test_has_permission_through_role(self):
        """Test user has permission through role"""
        user = User(
            id=UserId("user_123"),
            email=Email("test@example.com"),
            name="Test User"
        )
        
        permission = Permission(
            id="perm_read",
            name="read_users",
            description="Can read user data",
            resource="users",
            action="read"
        )
        
        role = Role(
            id="role_admin",
            name="admin",
            description="Administrator role"
        )
        role.add_permission(permission)
        user.add_role(role)
        
        assert user.has_permission("read_users") is True
        assert user.has_permission("write_users") is False
    
    def test_has_role(self):
        """Test user has specific role"""
        user = User(
            id=UserId("user_123"),
            email=Email("test@example.com"),
            name="Test User"
        )
        
        role = Role(
            id="role_admin",
            name="admin",
            description="Administrator role"
        )
        user.add_role(role)
        
        assert user.has_role("admin") is True
        assert user.has_role("user") is False
    
    def test_is_admin(self):
        """Test checking if user is admin"""
        user = User(
            id=UserId("user_123"),
            email=Email("test@example.com"),
            name="Test User"
        )
        
        admin_role = Role(
            id="role_admin",
            name="admin",
            description="Administrator role",
            role_type=RoleType.ADMIN
        )
        
        user_role = Role(
            id="role_user",
            name="user",
            description="Regular user role",
            role_type=RoleType.USER
        )
        
        # User is not admin initially
        assert user.is_admin() is False
        
        # Add user role - still not admin
        user.add_role(user_role)
        assert user.is_admin() is False
        
        # Add admin role - now is admin
        user.add_role(admin_role)
        assert user.is_admin() is True
    
    def test_user_status_changes(self):
        """Test user status change methods"""
        user = User(
            id=UserId("user_123"),
            email=Email("test@example.com"),
            name="Test User"
        )
        
        # Initially active
        assert user.is_active() is True
        assert user.status == UserStatus.ACTIVE
        
        # Deactivate
        user.deactivate()
        assert user.is_active() is False
        assert user.status == UserStatus.INACTIVE
        assert user.updated_at is not None
        
        # Suspend
        user.suspend()
        assert user.status == UserStatus.SUSPENDED
        
        # Reactivate
        user.activate()
        assert user.is_active() is True
        assert user.status == UserStatus.ACTIVE
    
    def test_record_login(self):
        """Test recording user login"""
        user = User(
            id=UserId("user_123"),
            email=Email("test@example.com"),
            name="Test User"
        )
        
        assert user.last_login is None
        
        user.record_login()
        
        assert user.last_login is not None
        assert isinstance(user.last_login, datetime)
        assert user.updated_at is not None
    
    def test_update_profile(self):
        """Test updating user profile"""
        user = User(
            id=UserId("user_123"),
            email=Email("test@example.com"),
            name="Test User"
        )
        
        profile_data = {
            "avatar_url": "https://example.com/avatar.jpg",
            "bio": "Software developer"
        }
        
        user.update_profile(profile_data)
        
        assert user.profile_data["avatar_url"] == "https://example.com/avatar.jpg"
        assert user.profile_data["bio"] == "Software developer"
        assert user.updated_at is not None


class TestAuthSession:
    """Test AuthSession entity"""
    
    def test_create_session_success(self):
        """Test successful session creation"""
        token = Token.generate()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        session = AuthSession(
            id="session_123",
            user_id=UserId("user_123"),
            token=token,
            expires_at=expires_at
        )
        
        assert session.id == "session_123"
        assert session.user_id.value == "user_123"
        assert session.token == token
        assert session.expires_at == expires_at
        assert session.is_active is True
        assert isinstance(session.created_at, datetime)
    
    def test_create_session_empty_id_fails(self):
        """Test session creation fails with empty ID"""
        token = Token.generate()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        with pytest.raises(ValueError, match="Session ID cannot be empty"):
            AuthSession(
                id="",
                user_id=UserId("user_123"),
                token=token,
                expires_at=expires_at
            )
    
    def test_create_session_past_expiration_fails(self):
        """Test session creation fails with past expiration"""
        token = Token.generate()
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)  # Past time
        
        with pytest.raises(ValueError, match="Session expiration must be in the future"):
            AuthSession(
                id="session_123",
                user_id=UserId("user_123"),
                token=token,
                expires_at=expires_at
            )
    
    def test_session_validity(self):
        """Test session validity checks"""
        token = Token.generate()
        future_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        past_expiry = datetime.now(timezone.utc) - timedelta(hours=1)
        
        # Valid session
        valid_session = AuthSession(
            id="session_123",
            user_id=UserId("user_123"),
            token=token,
            expires_at=future_expiry
        )
        assert valid_session.is_valid() is True
        
        # Expired session
        expired_session = AuthSession(
            id="session_124",
            user_id=UserId("user_123"),
            token=token,
            expires_at=future_expiry  # Will be overridden
        )
        # Manually set to expired (simulating time passage)
        expired_session.expires_at = past_expiry
        assert expired_session.is_valid() is False
        
        # Inactive session
        valid_session.invalidate()
        assert valid_session.is_valid() is False
    
    def test_invalidate_session(self):
        """Test invalidating session"""
        token = Token.generate()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        session = AuthSession(
            id="session_123",
            user_id=UserId("user_123"),
            token=token,
            expires_at=expires_at
        )
        
        assert session.is_active is True
        
        session.invalidate()
        
        assert session.is_active is False
        assert session.is_valid() is False
    
    def test_extend_session(self):
        """Test extending session expiration"""
        token = Token.generate()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        session = AuthSession(
            id="session_123",
            user_id=UserId("user_123"),
            token=token,
            expires_at=expires_at
        )
        
        original_expiry = session.expires_at
        
        session.extend(30)  # Extend by 30 minutes
        
        # Should be extended (approximately)
        assert session.expires_at > original_expiry 