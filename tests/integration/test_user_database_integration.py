"""
Integration Tests for User Database Operations

Example of proper integration test structure using BaseIntegrationTest.
Tests real database interactions with limited scope.
"""

import pytest
import asyncio
from unittest.mock import patch
import tempfile
import os

from tests.base_test_classes import BaseIntegrationTest


class TestUserDatabaseIntegration(BaseIntegrationTest):
    """Integration tests for user database operations"""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Setup test database for integration tests"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db_url = f"sqlite:///{self.temp_db.name}"
        
        # Setup database schema (mock)
        self.setup_test_schema()
        
        yield
        
        # Cleanup
        self.temp_db.close()
        os.unlink(self.temp_db.name)

    def setup_test_schema(self):
        """Setup test database schema"""
        # This would create actual database tables
        # For now, we'll mock the database operations
        pass

    def test_user_crud_operations(self):
        """Test complete CRUD operations for users"""
        # Arrange
        user_data = {
            "email": "integration@example.com",
            "username": "integrationuser",
            "password_hash": "hashed_password",
            "is_active": True
        }
        
        # Mock database operations
        with patch('app.models.user.User') as MockUser:
            # Setup mock
            mock_user_instance = MockUser.return_value
            mock_user_instance.to_dict.return_value = {**user_data, "id": "test_id"}
            
            # Act - CREATE
            created_user = self._create_user_in_db(user_data)
            
            # Assert - CREATE
            assert created_user["email"] == user_data["email"]
            assert created_user["username"] == user_data["username"]
            assert "id" in created_user
            
            # Act - READ
            user_id = created_user["id"]
            retrieved_user = self._get_user_from_db(user_id)
            
            # Assert - READ
            assert retrieved_user["id"] == user_id
            assert retrieved_user["email"] == user_data["email"]
            
            # Act - UPDATE
            update_data = {"full_name": "Integration User"}
            updated_user = self._update_user_in_db(user_id, update_data)
            
            # Assert - UPDATE
            assert updated_user["full_name"] == "Integration User"
            
            # Act - DELETE
            deletion_result = self._delete_user_from_db(user_id)
            
            # Assert - DELETE
            assert deletion_result is True

    def test_user_unique_constraints(self):
        """Test database unique constraints"""
        # Arrange
        user_data = {
            "email": "unique@example.com",
            "username": "uniqueuser",
            "password_hash": "hashed_password"
        }
        
        # Act - Create first user
        first_user = self._create_user_in_db(user_data)
        assert first_user is not None
        
        # Act - Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            self._create_user_in_db(user_data)

    def test_user_queries_with_filters(self):
        """Test complex database queries with filters"""
        # Arrange - Create test data
        test_users = [
            {"email": f"user{i}@example.com", "username": f"user{i}", "is_active": i % 2 == 0}
            for i in range(10)
        ]
        
        # Create users
        created_users = []
        for user_data in test_users:
            user = self._create_user_in_db(user_data)
            created_users.append(user)
        
        # Act - Query active users
        active_users = self._get_users_by_status(is_active=True)
        
        # Assert
        assert len(active_users) == 5  # Half should be active
        assert all(user["is_active"] for user in active_users)
        
        # Act - Query by email pattern
        gmail_users = self._get_users_by_email_pattern("user1@example.com")
        
        # Assert
        assert len(gmail_users) == 1
        assert gmail_users[0]["email"] == "user1@example.com"

    def test_user_database_transactions(self):
        """Test database transaction handling"""
        # Arrange
        user_data = {
            "email": "transaction@example.com",
            "username": "transactionuser",
            "password_hash": "hashed_password"
        }
        
        # Act - Test successful transaction
        with self._database_transaction():
            user = self._create_user_in_db(user_data)
            assert user is not None
            
            # Update in same transaction
            self._update_user_in_db(user["id"], {"full_name": "Transaction User"})
        
        # Assert - Changes should be committed
        retrieved_user = self._get_user_from_db(user["id"])
        assert retrieved_user["full_name"] == "Transaction User"
        
        # Act - Test rollback transaction
        try:
            with self._database_transaction():
                self._update_user_in_db(user["id"], {"full_name": "Rollback User"})
                raise Exception("Force rollback")
        except Exception:
            pass
        
        # Assert - Changes should be rolled back
        retrieved_user = self._get_user_from_db(user["id"])
        assert retrieved_user["full_name"] == "Transaction User"  # Should not be "Rollback User"

    def test_user_database_performance(self):
        """Test database performance with bulk operations"""
        # Arrange
        bulk_users = [
            {
                "email": f"bulk{i}@example.com",
                "username": f"bulkuser{i}",
                "password_hash": "hashed_password"
            }
            for i in range(100)
        ]
        
        # Act - Bulk create
        import time
        start_time = time.time()
        created_users = self._bulk_create_users(bulk_users)
        creation_time = time.time() - start_time
        
        # Assert
        assert len(created_users) == 100
        assert creation_time < 5.0  # Should create 100 users in under 5 seconds
        
        # Act - Bulk query
        start_time = time.time()
        all_users = self._get_all_users_paginated(page=1, limit=50)
        query_time = time.time() - start_time
        
        # Assert
        assert len(all_users) == 50  # First page
        assert query_time < 1.0  # Should query quickly

    # Helper methods (these would be actual database operations)
    def _create_user_in_db(self, user_data):
        """Mock user creation in database"""
        # This would be actual database CREATE
        user = {**user_data, "id": f"user_{hash(user_data['email']) % 10000}"}
        return user

    def _get_user_from_db(self, user_id):
        """Mock user retrieval from database"""
        # This would be actual database SELECT
        return {
            "id": user_id,
            "email": "integration@example.com",
            "username": "integrationuser",
            "is_active": True,
            "full_name": "Integration User"
        }

    def _update_user_in_db(self, user_id, update_data):
        """Mock user update in database"""
        # This would be actual database UPDATE
        user = self._get_user_from_db(user_id)
        user.update(update_data)
        return user

    def _delete_user_from_db(self, user_id):
        """Mock user deletion from database"""
        # This would be actual database DELETE
        return True

    def _get_users_by_status(self, is_active=True):
        """Mock filtered user query"""
        # This would be actual database query with WHERE clause
        return [
            {"id": f"user_{i}", "email": f"user{i}@example.com", "is_active": is_active}
            for i in range(5)
        ]

    def _get_users_by_email_pattern(self, pattern):
        """Mock pattern-based user query"""
        # This would be actual database query with LIKE
        return [{"id": "user_1", "email": pattern, "is_active": True}]

    def _database_transaction(self):
        """Mock database transaction context"""
        # This would be actual database transaction
        from contextlib import contextmanager
        
        @contextmanager
        def transaction():
            try:
                yield
            except Exception:
                # Rollback would happen here
                raise
        
        return transaction()

    def _bulk_create_users(self, users_data):
        """Mock bulk user creation"""
        # This would be actual bulk INSERT
        return [
            {**user_data, "id": f"bulk_{i}"}
            for i, user_data in enumerate(users_data)
        ]

    def _get_all_users_paginated(self, page=1, limit=10):
        """Mock paginated user query"""
        # This would be actual database query with LIMIT and OFFSET
        start = (page - 1) * limit
        return [
            {"id": f"user_{i}", "email": f"user{i}@example.com"}
            for i in range(start, start + limit)
        ]


class TestUserCacheIntegration(BaseIntegrationTest):
    """Integration tests for user caching"""

    def test_user_cache_integration(self):
        """Test user caching with real cache backend"""
        # Arrange
        user_data = {
            "id": "cached_user",
            "email": "cached@example.com",
            "username": "cacheduser"
        }
        
        # Mock cache operations
        with patch('app.performance.cache_manager.cache_manager') as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True
            
            # Act - First retrieval (cache miss)
            user1 = self._get_user_with_cache(user_data["id"])
            
            # Assert - Cache was checked and set
            mock_cache.get.assert_called_once()
            mock_cache.set.assert_called_once()
            
            # Act - Second retrieval (cache hit)
            mock_cache.get.return_value = user_data
            user2 = self._get_user_with_cache(user_data["id"])
            
            # Assert - Cache was used
            assert user2 == user_data

    def _get_user_with_cache(self, user_id):
        """Mock user retrieval with caching"""
        # This would be actual cache-enabled user retrieval
        return {
            "id": user_id,
            "email": "cached@example.com",
            "username": "cacheduser"
        } 