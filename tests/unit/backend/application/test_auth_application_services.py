"""
Unit Tests for Auth Application Services

Tests for application layer use cases with mocked dependencies.
Following hexagonal architecture testing principles.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone

from backend.domain.auth.entities import User, Role, Permission, AuthSession, UserStatus, RoleType
from backend.domain.auth.value_objects import UserId, Email, Password, Token
from backend.domain.auth.exceptions import (
    AuthDomainError, InvalidCredentialsError, UserNotFoundError
)
from backend.application.auth.services import AuthApplicationService, RoleManagementService


class TestAuthApplicationService:
    """Test AuthApplicationService with mocked dependencies"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        return {
            'user_repository': AsyncMock(),
            'role_repository': AsyncMock(),
            'session_repository': AsyncMock(),
            'password_hasher': Mock(),
            'token_generator': Mock(),
            'email_service': AsyncMock(),
            'event_publisher': AsyncMock()
        }
    
    @pytest.fixture
    def auth_service(self, mock_repositories):
        """Create AuthApplicationService with mocked dependencies"""
        return AuthApplicationService(**mock_repositories)
    
    @pytest.fixture
    def sample_user(self):
        """Create sample user for testing"""
        return User(
            id=UserId("user_123"),
            email=Email("test@example.com"),
            name="Test User",
            password_hash="hashed_password",
            status=UserStatus.ACTIVE
        )
    
    @pytest.fixture
    def sample_role(self):
        """Create sample role for testing"""
        return Role(
            id="role_user",
            name="user", 
            description="Regular user role",
            role_type=RoleType.USER
        )
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, mock_repositories):
        """Test successful user registration"""
        # Arrange
        email = "test@example.com"
        name = "Test User"
        password = "SecurePass123"
        
        mock_repositories['user_repository'].find_by_email.return_value = None
        mock_repositories['password_hasher'].hash_password.return_value = "hashed_password"
        mock_repositories['user_repository'].save.return_value = User(
            id=UserId("user_123"),
            email=Email(email),
            name=name,
            password_hash="hashed_password"
        )
        
        # Act
        result = await auth_service.register_user(email, name, password)
        
        # Assert
        assert result.email.value == email
        assert result.name == name
        assert result.password_hash == "hashed_password"
        
        mock_repositories['user_repository'].find_by_email.assert_called_once()
        mock_repositories['password_hasher'].hash_password.assert_called_once_with(password)
        mock_repositories['user_repository'].save.assert_called_once()
        mock_repositories['email_service'].send_welcome_email.assert_called_once()
        mock_repositories['event_publisher'].publish_user_created.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_user_already_exists(self, auth_service, mock_repositories, sample_user):
        """Test user registration when user already exists"""
        # Arrange
        email = "test@example.com"
        name = "Test User"
        password = "SecurePass123"
        
        mock_repositories['user_repository'].find_by_email.return_value = sample_user
        
        # Act & Assert
        with pytest.raises(AuthDomainError, match="User with email .* already exists"):
            await auth_service.register_user(email, name, password)
        
        mock_repositories['user_repository'].find_by_email.assert_called_once()
        mock_repositories['user_repository'].save.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, mock_repositories, sample_user):
        """Test successful user authentication"""
        # Arrange
        email = "test@example.com"
        password = "SecurePass123"
        
        mock_repositories['user_repository'].find_by_email.return_value = sample_user
        
        sample_session = AuthSession(
            id="session_123",
            user_id=sample_user.id,
            token=Token.generate(),
            expires_at=datetime.now(timezone.utc)
        )
        mock_repositories['session_repository'].save.return_value = sample_session
        mock_repositories['user_repository'].save.return_value = sample_user
        
        # Act
        user, session = await auth_service.authenticate_user(email, password)
        
        # Assert
        assert user == sample_user
        assert session == sample_session
        assert user.last_login is not None
        
        mock_repositories['user_repository'].find_by_email.assert_called_once()
        mock_repositories['session_repository'].save.assert_called_once()
        mock_repositories['user_repository'].save.assert_called_once()
        mock_repositories['event_publisher'].publish_user_authenticated.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service, mock_repositories):
        """Test authentication when user not found"""
        # Arrange
        email = "test@example.com"
        password = "SecurePass123"
        
        mock_repositories['user_repository'].find_by_email.return_value = None
        
        # Act & Assert
        with pytest.raises(UserNotFoundError):
            await auth_service.authenticate_user(email, password)
        
        mock_repositories['user_repository'].find_by_email.assert_called_once()
        mock_repositories['session_repository'].save.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, auth_service, mock_repositories, sample_user):
        """Test authentication when user is inactive"""
        # Arrange
        email = "test@example.com"
        password = "SecurePass123"
        
        sample_user.status = UserStatus.INACTIVE
        mock_repositories['user_repository'].find_by_email.return_value = sample_user
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsError, match="User account is not active"):
            await auth_service.authenticate_user(email, password)
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service, mock_repositories, sample_user):
        """Test successful password change"""
        # Arrange
        user_id = "user_123"
        old_password = "OldPass123"
        new_password = "NewPass123"
        
        mock_repositories['user_repository'].find_by_id.return_value = sample_user
        mock_repositories['password_hasher'].hash_password.return_value = "new_hashed_password"
        mock_repositories['user_repository'].save.return_value = sample_user
        
        # Act
        result = await auth_service.change_password(user_id, old_password, new_password)
        
        # Assert
        assert result is True
        assert sample_user.password_hash == "new_hashed_password"
        
        mock_repositories['user_repository'].find_by_id.assert_called_once()
        mock_repositories['password_hasher'].hash_password.assert_called_once_with(new_password)
        mock_repositories['user_repository'].save.assert_called_once()
        mock_repositories['event_publisher'].publish_password_changed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_password_user_not_found(self, auth_service, mock_repositories):
        """Test password change when user not found"""
        # Arrange
        user_id = "user_123"
        old_password = "OldPass123"
        new_password = "NewPass123"
        
        mock_repositories['user_repository'].find_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(UserNotFoundError):
            await auth_service.change_password(user_id, old_password, new_password)
    
    @pytest.mark.asyncio
    async def test_assign_role_success(self, auth_service, mock_repositories, sample_user, sample_role):
        """Test successful role assignment"""
        # Arrange
        user_id = "user_123"
        role_name = "user"
        
        mock_repositories['user_repository'].find_by_id.return_value = sample_user
        mock_repositories['role_repository'].find_by_name.return_value = sample_role
        mock_repositories['user_repository'].save.return_value = sample_user
        
        # Act
        result = await auth_service.assign_role(user_id, role_name)
        
        # Assert
        assert result is True
        assert sample_role in sample_user.roles
        
        mock_repositories['user_repository'].find_by_id.assert_called_once()
        mock_repositories['role_repository'].find_by_name.assert_called_once_with(role_name)
        mock_repositories['user_repository'].save.assert_called_once()
        mock_repositories['event_publisher'].publish_user_role_changed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_assign_role_user_not_found(self, auth_service, mock_repositories):
        """Test role assignment when user not found"""
        # Arrange
        user_id = "user_123"
        role_name = "user"
        
        mock_repositories['user_repository'].find_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(UserNotFoundError):
            await auth_service.assign_role(user_id, role_name)
    
    @pytest.mark.asyncio
    async def test_assign_role_role_not_found(self, auth_service, mock_repositories, sample_user):
        """Test role assignment when role not found"""
        # Arrange
        user_id = "user_123"
        role_name = "nonexistent"
        
        mock_repositories['user_repository'].find_by_id.return_value = sample_user
        mock_repositories['role_repository'].find_by_name.return_value = None
        
        # Act & Assert
        with pytest.raises(AuthDomainError, match="Role .* not found"):
            await auth_service.assign_role(user_id, role_name)
    
    @pytest.mark.asyncio
    async def test_revoke_role_success(self, auth_service, mock_repositories, sample_user, sample_role):
        """Test successful role revocation"""
        # Arrange
        user_id = "user_123"
        role_name = "user"
        
        # Add role to user first
        sample_user.add_role(sample_role)
        
        mock_repositories['user_repository'].find_by_id.return_value = sample_user
        mock_repositories['role_repository'].find_by_name.return_value = sample_role
        mock_repositories['user_repository'].save.return_value = sample_user
        
        # Act
        result = await auth_service.revoke_role(user_id, role_name)
        
        # Assert
        assert result is True
        assert sample_role not in sample_user.roles
        
        mock_repositories['user_repository'].save.assert_called_once()
        mock_repositories['event_publisher'].publish_user_role_changed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authorize_user_success(self, auth_service, mock_repositories, sample_user):
        """Test successful user authorization"""
        # Arrange
        user_id = "user_123"
        permission = "read_users"
        
        # Add permission to user via role
        perm = Permission(
            id="perm_read",
            name=permission,
            description="Can read users",
            resource="users",
            action="read"
        )
        role = Role(
            id="role_user",
            name="user",
            description="User role"
        )
        role.add_permission(perm)
        sample_user.add_role(role)
        
        mock_repositories['user_repository'].find_by_id.return_value = sample_user
        
        # Act
        result = await auth_service.authorize_user(user_id, permission)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_authorize_user_no_permission(self, auth_service, mock_repositories, sample_user):
        """Test user authorization without required permission"""
        # Arrange
        user_id = "user_123"
        permission = "write_users"
        
        mock_repositories['user_repository'].find_by_id.return_value = sample_user
        
        # Act
        result = await auth_service.authorize_user(user_id, permission)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_user_by_token_success(self, auth_service, mock_repositories, sample_user):
        """Test getting user by valid token"""
        # Arrange
        token = "valid_token"
        
        sample_session = AuthSession(
            id="session_123",
            user_id=sample_user.id,
            token=Token(token),
            expires_at=datetime.now(timezone.utc)
        )
        
        mock_repositories['session_repository'].find_by_token.return_value = sample_session
        mock_repositories['user_repository'].find_by_id.return_value = sample_user
        
        # Act
        result = await auth_service.get_user_by_token(token)
        
        # Assert
        assert result == sample_user
    
    @pytest.mark.asyncio
    async def test_get_user_by_token_invalid_session(self, auth_service, mock_repositories):
        """Test getting user by invalid token"""
        # Arrange
        token = "invalid_token"
        
        mock_repositories['session_repository'].find_by_token.return_value = None
        
        # Act
        result = await auth_service.get_user_by_token(token)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_logout_success(self, auth_service, mock_repositories):
        """Test successful logout"""
        # Arrange
        token = "valid_token"
        
        sample_session = AuthSession(
            id="session_123",
            user_id=UserId("user_123"),
            token=Token(token),
            expires_at=datetime.now(timezone.utc)
        )
        
        mock_repositories['session_repository'].find_by_token.return_value = sample_session
        mock_repositories['session_repository'].save.return_value = sample_session
        
        # Act
        result = await auth_service.logout(token)
        
        # Assert
        assert result is True
        assert sample_session.is_active is False
    
    @pytest.mark.asyncio
    async def test_logout_invalid_token(self, auth_service, mock_repositories):
        """Test logout with invalid token"""
        # Arrange
        token = "invalid_token"
        
        mock_repositories['session_repository'].find_by_token.return_value = None
        
        # Act
        result = await auth_service.logout(token)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, auth_service, mock_repositories):
        """Test cleanup of expired sessions"""
        # Arrange
        mock_repositories['session_repository'].delete_expired.return_value = 5
        
        # Act
        result = await auth_service.cleanup_expired_sessions()
        
        # Assert
        assert result == 5
        mock_repositories['session_repository'].delete_expired.assert_called_once()


class TestRoleManagementService:
    """Test RoleManagementService with mocked dependencies"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories for role management"""
        return {
            'role_repository': AsyncMock(),
            'permission_repository': AsyncMock(),
            'event_publisher': AsyncMock()
        }
    
    @pytest.fixture
    def role_service(self, mock_repositories):
        """Create RoleManagementService with mocked dependencies"""
        return RoleManagementService(**mock_repositories)
    
    @pytest.mark.asyncio
    async def test_create_role_success(self, role_service, mock_repositories):
        """Test successful role creation"""
        # Arrange
        name = "admin"
        description = "Administrator role"
        
        mock_repositories['role_repository'].find_by_name.return_value = None
        mock_repositories['role_repository'].save.return_value = Role(
            id="role_admin",
            name=name,
            description=description
        )
        
        # Act
        result = await role_service.create_role(name, description)
        
        # Assert
        assert result.name == name
        assert result.description == description
        
        mock_repositories['role_repository'].find_by_name.assert_called_once_with(name)
        mock_repositories['role_repository'].save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_role_already_exists(self, role_service, mock_repositories):
        """Test role creation when role already exists"""
        # Arrange
        name = "admin"
        description = "Administrator role"
        
        existing_role = Role(
            id="role_admin",
            name=name,
            description=description
        )
        mock_repositories['role_repository'].find_by_name.return_value = existing_role
        
        # Act & Assert
        with pytest.raises(AuthDomainError, match="Role .* already exists"):
            await role_service.create_role(name, description)
    
    @pytest.mark.asyncio
    async def test_list_roles(self, role_service, mock_repositories):
        """Test listing all roles"""
        # Arrange
        roles = [
            Role(id="role_admin", name="admin", description="Admin role"),
            Role(id="role_user", name="user", description="User role")
        ]
        mock_repositories['role_repository'].list_roles.return_value = roles
        
        # Act
        result = await role_service.list_roles()
        
        # Assert
        assert result == roles
        mock_repositories['role_repository'].list_roles.assert_called_once() 