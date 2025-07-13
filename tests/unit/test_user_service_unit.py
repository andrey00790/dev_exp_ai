"""
Unit Tests for User Service

Example of proper unit test structure using BaseUnitTest.
Tests isolated business logic with all dependencies mocked.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from tests.base_test_classes import BaseUnitTest


class TestUserServiceUnit(BaseUnitTest):
    """Unit tests for user service business logic"""

    def setup_method(self):
        """Setup for each test method"""
        # Mock the user service
        self.mock_user_repo = Mock()
        self.mock_password_hasher = Mock()
        self.mock_email_service = AsyncMock()
        
        # Setup return values
        self.mock_password_hasher.hash_password.return_value = "hashed_password"
        self.mock_password_hasher.verify_password.return_value = True
        self.mock_email_service.send_email.return_value = True

    def test_create_user_success(self):
        """Test successful user creation"""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123"
        }
        
        expected_user = self.create_mock_user("testuser")
        self.mock_user_repo.create.return_value = expected_user
        
        # Act
        with patch('app.services.user_service.UserRepository', return_value=self.mock_user_repo):
            with patch('app.services.user_service.PasswordHasher', return_value=self.mock_password_hasher):
                # This would be the actual service call
                result = self._create_user_with_mocks(user_data)
        
        # Assert
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        self.mock_password_hasher.hash_password.assert_called_once_with("password123")
        self.mock_user_repo.create.assert_called_once()

    def test_create_user_duplicate_email(self):
        """Test user creation with duplicate email"""
        # Arrange
        user_data = {
            "email": "existing@example.com",
            "username": "testuser",
            "password": "password123"
        }
        
        # Mock repository to raise exception
        self.mock_user_repo.create.side_effect = ValueError("Email already exists")
        
        # Act & Assert
        with patch('app.services.user_service.UserRepository', return_value=self.mock_user_repo):
            with patch('app.services.user_service.PasswordHasher', return_value=self.mock_password_hasher):
                with pytest.raises(ValueError, match="Email already exists"):
                    self._create_user_with_mocks(user_data)

    def test_validate_user_password_success(self):
        """Test successful password validation"""
        # Arrange
        user = self.create_mock_user()
        user["password_hash"] = "hashed_password"
        password = "correct_password"
        
        self.mock_password_hasher.verify_password.return_value = True
        
        # Act
        result = self._validate_password_with_mocks(user, password)
        
        # Assert
        assert result is True
        self.mock_password_hasher.verify_password.assert_called_once_with(password, "hashed_password")

    def test_validate_user_password_failure(self):
        """Test failed password validation"""
        # Arrange
        user = self.create_mock_user()
        user["password_hash"] = "hashed_password"
        password = "wrong_password"
        
        self.mock_password_hasher.verify_password.return_value = False
        
        # Act
        result = self._validate_password_with_mocks(user, password)
        
        # Assert
        assert result is False
        self.mock_password_hasher.verify_password.assert_called_once_with(password, "hashed_password")

    def test_user_update_profile_success(self):
        """Test successful user profile update"""
        # Arrange
        user_id = "test_user_123"
        update_data = {
            "full_name": "Test User Updated",
            "bio": "Updated bio"
        }
        
        existing_user = self.create_mock_user(user_id)
        updated_user = existing_user.copy()
        updated_user.update(update_data)
        
        self.mock_user_repo.get_by_id.return_value = existing_user
        self.mock_user_repo.update.return_value = updated_user
        
        # Act
        result = self._update_user_profile_with_mocks(user_id, update_data)
        
        # Assert
        assert result["full_name"] == "Test User Updated"
        assert result["bio"] == "Updated bio"
        self.mock_user_repo.get_by_id.assert_called_once_with(user_id)
        self.mock_user_repo.update.assert_called_once()

    def test_user_deactivation_success(self):
        """Test successful user deactivation"""
        # Arrange
        user_id = "test_user_123"
        user = self.create_mock_user(user_id)
        user["is_active"] = False
        
        self.mock_user_repo.update.return_value = user
        
        # Act
        result = self._deactivate_user_with_mocks(user_id)
        
        # Assert
        assert result["is_active"] is False
        self.mock_user_repo.update.assert_called_once()

    # Helper methods for testing (these would be actual service methods)
    def _create_user_with_mocks(self, user_data):
        """Mock user creation logic"""
        # Hash password
        hashed_password = self.mock_password_hasher.hash_password(user_data["password"])
        
        # Create user
        user_to_create = {
            "email": user_data["email"],
            "username": user_data["username"],
            "password_hash": hashed_password,
            "is_active": True
        }
        
        return self.mock_user_repo.create(user_to_create)

    def _validate_password_with_mocks(self, user, password):
        """Mock password validation logic"""
        return self.mock_password_hasher.verify_password(password, user["password_hash"])

    def _update_user_profile_with_mocks(self, user_id, update_data):
        """Mock user profile update logic"""
        user = self.mock_user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.update(update_data)
        return self.mock_user_repo.update(user)

    def _deactivate_user_with_mocks(self, user_id):
        """Mock user deactivation logic"""
        update_data = {"is_active": False}
        return self.mock_user_repo.update({"id": user_id, **update_data})


# Performance unit tests
class TestUserServicePerformance(BaseUnitTest):
    """Performance unit tests for user service"""

    def test_user_creation_performance(self):
        """Test user creation performance"""
        # Arrange
        user_data = {
            "email": "perf@example.com",
            "username": "perfuser",
            "password": "password123"
        }
        
        # Act - measure operation
        result, execution_time = self.measure_operation(
            self._create_user_with_mocks, user_data
        )
        
        # Assert
        assert execution_time < 0.1  # Should be very fast for unit test
        assert result is not None

    def test_bulk_user_validation_performance(self):
        """Test bulk user validation performance"""
        # Arrange
        users = [self.create_mock_user(f"user_{i}") for i in range(100)]
        
        # Act
        start_time = time.time()
        results = [self._validate_user_data_with_mocks(user) for user in users]
        execution_time = time.time() - start_time
        
        # Assert
        assert execution_time < 0.5  # Should handle 100 users quickly
        assert all(results)  # All should be valid

    def _validate_user_data_with_mocks(self, user):
        """Mock user data validation"""
        return bool(user.get("email") and user.get("username"))

    def measure_operation(self, operation_func, *args, **kwargs):
        """Measure operation performance"""
        import time
        
        start_time = time.time()
        result = operation_func(*args, **kwargs)
        end_time = time.time()
        
        return result, end_time - start_time 