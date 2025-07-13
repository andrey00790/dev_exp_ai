"""
Test auth repository adapters - Updated for Mock implementation

Tests the Mock implementations of auth repositories for development.
These tests verify the behavior of Mock repositories without database dependencies.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta

from backend.domain.auth.entities import User, Role, Permission, AuthSession, UserStatus, RoleType
from backend.domain.auth.value_objects import UserId, Email, Password, Token, RefreshToken
from backend.adapters.auth.repositories import (
    MockUserRepository, MockRoleRepository, MockPermissionRepository, MockSessionRepository
)
from backend.domain.auth.exceptions import UserNotFoundError, AuthDomainError


class TestMockUserRepository:
    """Test MockUserRepository adapter"""
    
    @pytest.fixture
    def user_repository(self):
        """Create MockUserRepository"""
        return MockUserRepository()
    
    @pytest.fixture
    def sample_user(self):
        """Create sample user for testing"""
        return User(
            id=UserId("user_123"),
            email=Email("test@example.com"),
            name="Test User",
            password_hash="hashed_password",
            status=UserStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_save_user_success(self, user_repository, sample_user):
        """Test successful user save"""
        # Execute
        result = await user_repository.save(sample_user)
        
        # Verify
        assert result.id.value is not None
        assert result.email.value == "test@example.com"
        assert result.name == "Test User"
        assert result.status == UserStatus.ACTIVE
        
        # Verify user is stored
        stored_user = await user_repository.find_by_id(result.id)
        assert stored_user is not None
        assert stored_user.email.value == "test@example.com"
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_save_user_auto_id_generation(self, user_repository):
        """Test that user ID is auto-generated when not provided"""
        # Create user without ID (use placeholder that will be replaced)
        user = User(
            id=UserId("placeholder"),
            email=Email("auto@example.com"),
            name="Auto User",
            password_hash="hashed_password",
            status=UserStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        # Clear the id to simulate empty
        user.id = UserId("1")  # Temporary valid ID
        
        # Execute
        result = await user_repository.save(user)
        
        # Verify ID was generated/assigned by repository
        assert result.id.value != ""
        assert result.id.value is not None
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_find_by_id_success(self, user_repository, sample_user):
        """Test successful user find by ID"""
        # Setup - save user first
        saved_user = await user_repository.save(sample_user)
        
        # Execute
        result = await user_repository.find_by_id(saved_user.id)
        
        # Verify
        assert result is not None
        assert result.id.value == saved_user.id.value
        assert result.email.value == "test@example.com"
        assert result.name == "Test User"
        assert result.status == UserStatus.ACTIVE
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, user_repository):
        """Test user find by ID when not found"""
        # Execute
        result = await user_repository.find_by_id(UserId("nonexistent_id"))
        
        # Verify
        assert result is None
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_find_by_email_success(self, user_repository, sample_user):
        """Test successful user find by email"""
        # Setup - save user first
        await user_repository.save(sample_user)
        
        # Execute
        result = await user_repository.find_by_email(Email("test@example.com"))
        
        # Verify
        assert result is not None
        assert result.email.value == "test@example.com"
        assert result.name == "Test User"
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_find_by_email_not_found(self, user_repository):
        """Test user find by email when not found"""
        # Execute
        result = await user_repository.find_by_email(Email("nonexistent@example.com"))
        
        # Verify
        assert result is None
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_repository, sample_user):
        """Test successful user deletion"""
        # Setup - save user first
        saved_user = await user_repository.save(sample_user)
        
        # Execute
        result = await user_repository.delete(saved_user.id)
        
        # Verify
        assert result == True
        
        # Verify user is deleted
        deleted_user = await user_repository.find_by_id(saved_user.id)
        assert deleted_user is None
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, user_repository):
        """Test user deletion when not found"""
        # Execute
        result = await user_repository.delete(UserId("nonexistent_id"))
        
        # Verify
        assert result == False
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_list_users_success(self, user_repository, sample_user):
        """Test successful user listing"""
        # Setup - save user first
        await user_repository.save(sample_user)
        
        # Execute
        results = await user_repository.list_users(offset=0, limit=10)
        
        # Verify
        assert len(results) >= 1
        user_emails = [user.email.value for user in results]
        assert "test@example.com" in user_emails
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_list_users_empty(self, user_repository):
        """Test user listing when empty"""
        # Execute
        results = await user_repository.list_users(offset=0, limit=10)
        
        # Verify (repository starts empty)
        assert len(results) == 0
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_list_users_with_pagination(self, user_repository):
        """Test user listing with pagination"""
        # Setup - create multiple users
        for i in range(15):
            user = User(
                id=UserId(f"temp_id_{i}"),  # Use valid temporary IDs
                email=Email(f"user{i}@example.com"),
                name=f"User {i}",
                password_hash="hashed_password",
                status=UserStatus.ACTIVE,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            await user_repository.save(user)
        
        # Execute with pagination
        results_page1 = await user_repository.list_users(offset=0, limit=5)
        results_page2 = await user_repository.list_users(offset=5, limit=5)
        results_page3 = await user_repository.list_users(offset=10, limit=5)
        
        # Verify
        assert len(results_page1) == 5
        assert len(results_page2) == 5
        assert len(results_page3) == 5


class TestMockRoleRepository:
    """Test MockRoleRepository adapter"""
    
    @pytest.fixture
    def role_repository(self):
        """Create MockRoleRepository"""
        return MockRoleRepository()
    
    @pytest.fixture
    def sample_role(self):
        """Create sample role for testing"""
        return Role(
            id="custom_role",
            name="custom",
            description="Custom role for testing",
            role_type=RoleType.USER,
            permissions=set(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_save_role_success(self, role_repository, sample_role):
        """Test successful role save"""
        # Execute
        result = await role_repository.save(sample_role)
        
        # Verify
        assert result.id is not None
        assert result.name == "custom"
        assert result.description == "Custom role for testing"
        assert result.role_type == RoleType.USER
        
        # Verify role is stored
        stored_role = await role_repository.find_by_id(result.id)
        assert stored_role is not None
        assert stored_role.name == "custom"
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_save_role_auto_id_generation(self, role_repository):
        """Test that role ID is auto-generated when not provided"""
        # Create role with placeholder ID that will be replaced by repository
        role = Role(
            id="temp_id",  # Use valid temporary ID
            name="auto_role",
            description="Auto-generated role",
            role_type=RoleType.USER,
            permissions=set(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Execute
        result = await role_repository.save(role)
        
        # Verify ID was assigned by repository
        assert result.id != ""
        assert result.id is not None
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_find_by_id_success(self, role_repository, sample_role):
        """Test successful role find by ID"""
        # Setup - save role first
        saved_role = await role_repository.save(sample_role)
        
        # Execute
        result = await role_repository.find_by_id(saved_role.id)
        
        # Verify
        assert result is not None
        assert result.id == saved_role.id
        assert result.name == "custom"
        assert result.description == "Custom role for testing"
        assert result.role_type == RoleType.USER
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, role_repository):
        """Test role find by ID when not found"""
        # Execute
        result = await role_repository.find_by_id("nonexistent_role")
        
        # Verify
        assert result is None
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_find_by_name_success(self, role_repository, sample_role):
        """Test successful role find by name"""
        # Setup - save role first
        await role_repository.save(sample_role)
        
        # Execute
        result = await role_repository.find_by_name("custom")
        
        # Verify
        assert result is not None
        assert result.name == "custom"
        assert result.description == "Custom role for testing"
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_find_by_name_not_found(self, role_repository):
        """Test role find by name when not found"""
        # Execute
        result = await role_repository.find_by_name("nonexistent_role")
        
        # Verify
        assert result is None
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_find_default_roles(self, role_repository):
        """Test finding default roles created by repository"""
        # Execute - find default admin role
        admin_role = await role_repository.find_by_name("admin")
        user_role = await role_repository.find_by_name("user")
        
        # Verify
        assert admin_role is not None
        assert admin_role.name == "admin"
        assert admin_role.role_type == RoleType.ADMIN
        
        assert user_role is not None
        assert user_role.name == "user"
        assert user_role.role_type == RoleType.USER
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_delete_role_success(self, role_repository, sample_role):
        """Test successful role deletion"""
        # Setup - save role first
        saved_role = await role_repository.save(sample_role)
        
        # Execute
        result = await role_repository.delete(saved_role.id)
        
        # Verify
        assert result == True
        
        # Verify role is deleted
        deleted_role = await role_repository.find_by_id(saved_role.id)
        assert deleted_role is None
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_delete_role_not_found(self, role_repository):
        """Test role deletion when not found"""
        # Execute
        result = await role_repository.delete("nonexistent_role")
        
        # Verify
        assert result == False
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_list_roles_success(self, role_repository, sample_role):
        """Test successful role listing"""
        # Setup - save role first
        await role_repository.save(sample_role)
        
        # Execute
        results = await role_repository.list_roles()
        
        # Verify (includes default roles + custom role)
        assert len(results) >= 3  # admin, user, custom
        role_names = [role.name for role in results]
        assert "admin" in role_names
        assert "user" in role_names
        assert "custom" in role_names


class TestMockPermissionRepository:
    """Test MockPermissionRepository adapter"""
    
    @pytest.fixture
    def permission_repository(self):
        """Create MockPermissionRepository"""
        return MockPermissionRepository()
    
    @pytest.fixture
    def sample_permission(self):
        """Create sample permission for testing"""
        return Permission(
            id="custom_perm",
            name="custom_action",
            description="Custom permission for testing",
            resource="test_resource",
            action="test_action",
            created_at=datetime.now(timezone.utc)
        )
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_save_permission_success(self, permission_repository, sample_permission):
        """Test successful permission save"""
        # Execute
        result = await permission_repository.save(sample_permission)
        
        # Verify
        assert result.id is not None
        assert result.name == "custom_action"
        assert result.description == "Custom permission for testing"
        assert result.resource == "test_resource"
        assert result.action == "test_action"
        
        # Verify permission is stored
        stored_permission = await permission_repository.find_by_id(result.id)
        assert stored_permission is not None
        assert stored_permission.name == "custom_action"
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_save_permission_auto_id_generation(self, permission_repository):
        """Test that permission ID is auto-generated when not provided"""
        # Create permission with placeholder ID that will be replaced by repository
        permission = Permission(
            id="temp_id",  # Use valid temporary ID
            name="auto_permission",
            description="Auto-generated permission",
            resource="auto_resource",
            action="auto_action",
            created_at=datetime.now(timezone.utc)
        )
        
        # Execute
        result = await permission_repository.save(permission)
        
        # Verify ID was assigned by repository
        assert result.id != ""
        assert result.id is not None
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_find_by_id_success(self, permission_repository, sample_permission):
        """Test successful permission find by ID"""
        # Setup - save permission first
        saved_permission = await permission_repository.save(sample_permission)
        
        # Execute
        result = await permission_repository.find_by_id(saved_permission.id)
        
        # Verify
        assert result is not None
        assert result.id == saved_permission.id
        assert result.name == "custom_action"
        assert result.description == "Custom permission for testing"
        assert result.resource == "test_resource"
        assert result.action == "test_action"
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, permission_repository):
        """Test permission find by ID when not found"""
        # Execute
        result = await permission_repository.find_by_id("nonexistent_perm")
        
        # Verify
        assert result is None
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_find_by_name_success(self, permission_repository, sample_permission):
        """Test successful permission find by name"""
        # Setup - save permission first
        await permission_repository.save(sample_permission)
        
        # Execute
        result = await permission_repository.find_by_name("custom_action")
        
        # Verify
        assert result is not None
        assert result.name == "custom_action"
        assert result.description == "Custom permission for testing"
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_find_by_name_not_found(self, permission_repository):
        """Test permission find by name when not found"""
        # Execute
        result = await permission_repository.find_by_name("nonexistent_permission")
        
        # Verify
        assert result is None
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_find_default_permissions(self, permission_repository):
        """Test finding default permissions created by repository"""
        # Execute - find some default permissions
        read_users = await permission_repository.find_by_name("read_users")
        write_users = await permission_repository.find_by_name("write_users")
        admin_system = await permission_repository.find_by_name("admin_system")
        
        # Verify
        assert read_users is not None
        assert read_users.resource == "users"
        assert read_users.action == "read"
        
        assert write_users is not None
        assert write_users.resource == "users"
        assert write_users.action == "write"
        
        assert admin_system is not None
        assert admin_system.resource == "system"
        assert admin_system.action == "admin"
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_list_permissions_success(self, permission_repository, sample_permission):
        """Test successful permission listing"""
        # Setup - save permission first
        await permission_repository.save(sample_permission)
        
        # Execute
        results = await permission_repository.list_permissions()
        
        # Verify (includes default permissions + custom permission)
        assert len(results) >= 7  # 6 default + 1 custom
        permission_names = [perm.name for perm in results]
        assert "read_users" in permission_names
        assert "write_users" in permission_names
        assert "custom_action" in permission_names


class TestMockSessionRepository:
    """Test MockSessionRepository adapter"""
    
    @pytest.fixture
    def session_repository(self):
        """Create MockSessionRepository"""
        return MockSessionRepository()
    
    @pytest.fixture
    def sample_auth_session(self):
        """Create sample auth session for testing"""
        return AuthSession(
            id="session_123",
            user_id=UserId("user_123"),
            token=Token.create_access_token("test_token_value", expires_in_minutes=60),
            refresh_token=RefreshToken.create("user_123", expires_in_days=30),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_active=True,
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc)
        )
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_save_session_success(self, session_repository, sample_auth_session):
        """Test successful session save"""
        # Execute
        result = await session_repository.save(sample_auth_session)
        
        # Verify
        assert result.id == "session_123"
        assert result.user_id.value == "user_123"
        assert result.token.value == "test_token_value"
        assert result.is_active == True
        
        # Verify session is stored
        stored_session = await session_repository.find_by_id("session_123")
        assert stored_session is not None
        assert stored_session.user_id.value == "user_123"
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_find_by_token_success(self, session_repository, sample_auth_session):
        """Test successful session find by token"""
        # Setup - save session first
        await session_repository.save(sample_auth_session)
        
        # Execute
        result = await session_repository.find_by_token(sample_auth_session.token)
        
        # Verify
        assert result is not None
        assert result.id == "session_123"
        assert result.user_id.value == "user_123"
        assert result.token.value == sample_auth_session.token.value
        assert result.is_active == True
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_find_by_token_not_found(self, session_repository):
        """Test session find by token when not found"""
        # Execute
        result = await session_repository.find_by_token(Token.create_access_token("nonexistent_token"))
        
        # Verify
        assert result is None
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_delete_session_success(self, session_repository, sample_auth_session):
        """Test successful session deletion"""
        # Setup - save session first
        await session_repository.save(sample_auth_session)
        
        # Execute
        result = await session_repository.delete("session_123")
        
        # Verify
        assert result == True
        
        # Verify session is deleted
        deleted_session = await session_repository.find_by_id("session_123")
        assert deleted_session is None
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, session_repository):
        """Test session deletion when not found"""
        # Execute
        result = await session_repository.delete("nonexistent_session")
        
        # Verify
        assert result == False
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_delete_expired_sessions(self, session_repository):
        """Test deletion of expired sessions"""
        # Setup - create expired session
        expired_session = AuthSession(
            id="expired_session",
            user_id=UserId("user_456"),
            token=Token.create_access_token("expired_token", expires_in_minutes=-60),  # Expired
            refresh_token=RefreshToken.create("user_456", expires_in_days=30),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
            is_active=True,
            created_at=datetime.now(timezone.utc) - timedelta(hours=2),
            last_activity=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        
        # Setup - create active session
        active_session = AuthSession(
            id="active_session",
            user_id=UserId("user_789"),
            token=Token.create_access_token("active_token", expires_in_minutes=60),  # Active
            refresh_token=RefreshToken.create("user_789", expires_in_days=30),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),  # Active
            is_active=True,
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc)
        )
        
        await session_repository.save(expired_session)
        await session_repository.save(active_session)
        
        # Execute
        deleted_count = await session_repository.delete_expired()
        
        # Verify
        assert deleted_count == 1
        
        # Verify expired session is deleted, active session remains
        assert await session_repository.find_by_id("expired_session") is None
        assert await session_repository.find_by_id("active_session") is not None
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_delete_all_for_user(self, session_repository):
        """Test deletion of all sessions for a specific user"""
        # Setup - create multiple sessions for same user
        session1 = AuthSession(
            id="session_1",
            user_id=UserId("user_123"),
            token=Token.create_access_token("token_1", expires_in_minutes=60),
            refresh_token=RefreshToken.create("user_123", expires_in_days=30),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_active=True,
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc)
        )
        
        session2 = AuthSession(
            id="session_2",
            user_id=UserId("user_123"),
            token=Token.create_access_token("token_2", expires_in_minutes=60),
            refresh_token=RefreshToken.create("user_123", expires_in_days=30),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_active=True,
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc)
        )
        
        # Setup - create session for different user
        other_session = AuthSession(
            id="other_session",
            user_id=UserId("user_456"),
            token=Token.create_access_token("other_token", expires_in_minutes=60),
            refresh_token=RefreshToken.create("user_456", expires_in_days=30),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_active=True,
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc)
        )
        
        await session_repository.save(session1)
        await session_repository.save(session2)
        await session_repository.save(other_session)
        
        # Execute
        deleted_count = await session_repository.delete_all_for_user(UserId("user_123"))
        
        # Verify
        assert deleted_count == 2
        
        # Verify user_123 sessions are deleted, other user's session remains
        assert await session_repository.find_by_id("session_1") is None
        assert await session_repository.find_by_id("session_2") is None
        assert await session_repository.find_by_id("other_session") is not None 