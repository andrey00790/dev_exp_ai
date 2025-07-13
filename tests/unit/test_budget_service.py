"""
Unit tests for Budget Service

Tests for budget management functionality including:
- Budget status checking
- Manual refill operations
- Auto-refill scheduling
- Budget history tracking
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.budget_service import (
    BudgetService,
    BudgetRefillRecord,
    RefillType,
    RefillStatus,
    get_user_budget_info,
    manual_refill_user_budget,
    get_budget_refill_history,
    get_budget_system_stats
)


class TestBudgetService:
    """Test cases for BudgetService class"""
    
    @pytest.fixture
    def budget_service(self):
        """Create a BudgetService instance for testing"""
        service = BudgetService()
        service.config = {
            "auto_refill": {
                "enabled": True,
                "schedule": {
                    "cron": "0 0 * * *",
                    "timezone": "Europe/Moscow"
                },
                "refill_settings": {
                    "refill_type": "reset",
                    "by_role": {
                        "admin": {"enabled": True, "amount": 10000.0, "reset_usage": True},
                        "user": {"enabled": True, "amount": 1000.0, "reset_usage": True},
                        "basic": {"enabled": True, "amount": 100.0, "reset_usage": True}
                    },
                    "individual_users": {},
                    "minimum_balance": {
                        "enabled": True,
                        "threshold": 10.0,
                        "emergency_refill": 50.0
                    }
                }
            },
            "security": {
                "max_limits": {"single_refill": 100000.0},
                "audit": {"enabled": True}
            },
            "monitoring": {"enabled": True}
        }
        return service
    
    @pytest.fixture
    def sample_users_db(self):
        """Sample users database for testing"""
        return {
            "admin@example.com": {
                "user_id": "admin_001",
                "email": "admin@example.com",
                "name": "Admin User",
                "is_active": True,
                "scopes": ["admin", "basic"],
                "budget_limit": 10000.0,
                "current_usage": 500.0
            },
            "user@example.com": {
                "user_id": "user_001",
                "email": "user@example.com",
                "name": "Regular User",
                "is_active": True,
                "scopes": ["basic"],
                "budget_limit": 1000.0,
                "current_usage": 100.0
            }
        }
    
    def test_determine_user_role(self, budget_service):
        """Test user role determination"""
        assert budget_service._determine_user_role(["admin", "basic"]) == "admin"
        assert budget_service._determine_user_role(["generate", "basic"]) == "user"
        assert budget_service._determine_user_role(["basic"]) == "basic"
        assert budget_service._determine_user_role([]) == "basic"
    
    def test_get_budget_status(self, budget_service):
        """Test budget status calculation"""
        current_usage = 250.0
        budget_limit = 1000.0
        usage_percentage = (current_usage / budget_limit) * 100
        
        assert budget_service._get_budget_status(usage_percentage) == "ACTIVE"
        assert budget_service._get_budget_status(85.0) == "WARNING"
        assert budget_service._get_budget_status(96.0) == "CRITICAL"
        assert budget_service._get_budget_status(105.0) == "EXCEEDED"
    
    @patch('app.services.budget_service.USERS_DB')
    @pytest.mark.asyncio
    async def test_get_user_budget_info(self, mock_users_db, budget_service, sample_users_db):
        """Test getting user budget information"""
        mock_users_db.items.return_value = sample_users_db.items()
        
        # Test existing user
        result = await budget_service.get_user_budget_info("user_001")
        
        assert result["user_id"] == "user_001"
        assert result["email"] == "user@example.com"
        assert result["current_usage"] == 100.0
        assert result["budget_limit"] == 1000.0
        assert result["remaining_balance"] == 900.0
        assert result["usage_percentage"] == 10.0
        assert result["budget_status"] == "ACTIVE"
        
        # Test non-existing user
        result = await budget_service.get_user_budget_info("non_existing")
        assert "error" in result
    
    @patch('app.services.budget_service.USERS_DB')
    @pytest.mark.asyncio
    async def test_manual_refill_add_type(self, mock_users_db, budget_service, sample_users_db):
        """Test manual refill with ADD type"""
        mock_users_db.items.return_value = sample_users_db.items()
        
        # Test successful refill
        result = await budget_service.manual_refill("user_001", 500.0, "add")
        
        assert result["success"] is True
        assert result["amount"] == 500.0
        assert result["refill_type"] == "add"
        assert "new_balance" in result
        assert "timestamp" in result
        
        # Check if refill was recorded
        assert len(budget_service.refill_history) == 1
        refill_record = budget_service.refill_history[0]
        assert refill_record.user_id == "user_001"
        assert refill_record.amount == 500.0
        assert refill_record.refill_type == RefillType.ADD
        assert refill_record.status == RefillStatus.SUCCESS
    
    @patch('app.services.budget_service.USERS_DB')
    @pytest.mark.asyncio
    async def test_manual_refill_reset_type(self, mock_users_db, budget_service, sample_users_db):
        """Test manual refill with RESET type"""
        mock_users_db.items.return_value = sample_users_db.items()
        
        # Test successful refill
        result = await budget_service.manual_refill("user_001", 2000.0, "reset")
        
        assert result["success"] is True
        assert result["amount"] == 2000.0
        assert result["refill_type"] == "reset"
        
        # Check if refill was recorded
        assert len(budget_service.refill_history) == 1
        refill_record = budget_service.refill_history[0]
        assert refill_record.refill_type == RefillType.RESET
    
    @pytest.mark.asyncio
    async def test_manual_refill_amount_limit(self, budget_service):
        """Test manual refill with amount exceeding limit"""
        result = await budget_service.manual_refill("user_001", 200000.0, "add")
        
        assert "error" in result
        assert "exceeds maximum limit" in result["error"]
    
    @patch('app.services.budget_service.USERS_DB')
    @pytest.mark.asyncio
    async def test_get_users_for_refill(self, mock_users_db, budget_service, sample_users_db):
        """Test getting users for refill"""
        mock_users_db.items.return_value = sample_users_db.items()
        
        users = await budget_service._get_users_for_refill()
        
        assert len(users) == 2
        
        # Check admin user
        admin_user = next((u for u in users if u["email"] == "admin@example.com"), None)
        assert admin_user is not None
        assert admin_user["role"] == "admin"
        assert admin_user["config"]["amount"] == 10000.0
        
        # Check regular user
        regular_user = next((u for u in users if u["email"] == "user@example.com"), None)
        assert regular_user is not None
        assert regular_user["role"] == "basic"
        assert regular_user["config"]["amount"] == 100.0
    
    @patch('app.services.budget_service.USERS_DB')
    @pytest.mark.asyncio
    async def test_refill_user_budget(self, mock_users_db, budget_service, sample_users_db):
        """Test refilling user budget"""
        mock_users_db.items.return_value = sample_users_db.items()
        
        user_info = {
            "user_id": "user_001",
            "email": "user@example.com",
            "role": "basic",
            "config": {
                "amount": 1000.0,
                "reset_usage": True,
                "refill_type": "reset"
            }
        }
        
        result = await budget_service._refill_user_budget(user_info)
        
        assert result.status == RefillStatus.SUCCESS
        assert result.user_id == "user_001"
        assert result.amount == 1000.0
        assert result.refill_type == RefillType.RESET
        assert result.new_balance == 1000.0
    
    @pytest.mark.asyncio
    async def test_get_refill_history(self, budget_service):
        """Test getting refill history"""
        # Add some test records
        budget_service.refill_history = [
            BudgetRefillRecord(
                user_id="user_001",
                email="user@example.com",
                amount=500.0,
                refill_type=RefillType.ADD,
                previous_balance=500.0,
                new_balance=1000.0,
                status=RefillStatus.SUCCESS,
                timestamp=datetime.now()
            ),
            BudgetRefillRecord(
                user_id="user_002",
                email="user2@example.com",
                amount=200.0,
                refill_type=RefillType.RESET,
                previous_balance=100.0,
                new_balance=200.0,
                status=RefillStatus.SUCCESS,
                timestamp=datetime.now() - timedelta(hours=1)
            )
        ]
        
        # Test getting all history
        history = await budget_service.get_refill_history()
        assert len(history) == 2
        
        # Test getting history for specific user
        user_history = await budget_service.get_refill_history(user_id="user_001")
        assert len(user_history) == 1
        assert user_history[0]["user_id"] == "user_001"
        
        # Test with limit
        limited_history = await budget_service.get_refill_history(limit=1)
        assert len(limited_history) == 1
    
    @pytest.mark.asyncio
    async def test_get_system_stats(self, budget_service):
        """Test getting system statistics"""
        # Add some test records
        budget_service.refill_history = [
            BudgetRefillRecord(
                user_id="user_001",
                email="user@example.com",
                amount=500.0,
                refill_type=RefillType.ADD,
                previous_balance=500.0,
                new_balance=1000.0,
                status=RefillStatus.SUCCESS,
                timestamp=datetime.now()
            ),
            BudgetRefillRecord(
                user_id="user_002",
                email="user2@example.com",
                amount=200.0,
                refill_type=RefillType.RESET,
                previous_balance=100.0,
                new_balance=200.0,
                status=RefillStatus.FAILED,
                timestamp=datetime.now() - timedelta(hours=1),
                error_message="Test error"
            )
        ]
        
        stats = await budget_service.get_system_stats()
        
        assert stats["total_refills"] == 2
        assert stats["successful_refills"] == 1
        assert stats["failed_refills"] == 1
        assert stats["success_rate"] == 0.5
        assert stats["total_amount_refilled"] == 500.0
        assert stats["average_refill_amount"] == 500.0
        assert "last_refill" in stats
        assert stats["scheduler_running"] is False
    
    @pytest.mark.asyncio
    async def test_scheduler_lifecycle(self, budget_service):
        """Test scheduler start/stop lifecycle"""
        # Initially not running
        assert budget_service._running is False
        
        # Start scheduler
        await budget_service.start_auto_refill_scheduler()
        assert budget_service._running is True
        
        # Stop scheduler
        await budget_service.stop_auto_refill_scheduler()
        assert budget_service._running is False


class TestBudgetFunctions:
    """Test standalone budget functions"""
    
    @patch('app.services.budget_service.budget_service')
    @pytest.mark.asyncio
    async def test_get_user_budget_info_function(self, mock_service):
        """Test get_user_budget_info function"""
        mock_service.get_user_budget_info.return_value = {
            "user_id": "test_user",
            "budget_limit": 1000.0,
            "current_usage": 100.0
        }
        
        result = await get_user_budget_info("test_user")
        
        mock_service.get_user_budget_info.assert_called_once_with("test_user")
        assert result["user_id"] == "test_user"
        assert result["budget_limit"] == 1000.0
    
    @patch('app.services.budget_service.budget_service')
    @pytest.mark.asyncio
    async def test_manual_refill_user_budget_function(self, mock_service):
        """Test manual_refill_user_budget function"""
        mock_service.manual_refill.return_value = {
            "success": True,
            "amount": 500.0,
            "refill_type": "add"
        }
        
        result = await manual_refill_user_budget("test_user", 500.0, "add")
        
        mock_service.manual_refill.assert_called_once_with("test_user", 500.0, "add")
        assert result["success"] is True
        assert result["amount"] == 500.0
    
    @patch('app.services.budget_service.budget_service')
    @pytest.mark.asyncio
    async def test_get_budget_refill_history_function(self, mock_service):
        """Test get_budget_refill_history function"""
        mock_service.get_refill_history.return_value = [
            {
                "user_id": "test_user",
                "amount": 500.0,
                "status": "success"
            }
        ]
        
        result = await get_budget_refill_history("test_user", 100)
        
        mock_service.get_refill_history.assert_called_once_with("test_user", 100)
        assert len(result) == 1
        assert result[0]["user_id"] == "test_user"
    
    @patch('app.services.budget_service.budget_service')
    @pytest.mark.asyncio
    async def test_get_budget_system_stats_function(self, mock_service):
        """Test get_budget_system_stats function"""
        mock_service.get_system_stats.return_value = {
            "total_refills": 10,
            "successful_refills": 9,
            "failed_refills": 1,
            "success_rate": 0.9
        }
        
        result = await get_budget_system_stats()
        
        mock_service.get_system_stats.assert_called_once()
        assert result["total_refills"] == 10
        assert result["success_rate"] == 0.9


class TestBudgetRefillRecord:
    """Test BudgetRefillRecord dataclass"""
    
    def test_budget_refill_record_creation(self):
        """Test creating a BudgetRefillRecord"""
        record = BudgetRefillRecord(
            user_id="test_user",
            email="test@example.com",
            amount=500.0,
            refill_type=RefillType.ADD,
            previous_balance=1000.0,
            new_balance=1500.0,
            status=RefillStatus.SUCCESS,
            timestamp=datetime.now()
        )
        
        assert record.user_id == "test_user"
        assert record.email == "test@example.com"
        assert record.amount == 500.0
        assert record.refill_type == RefillType.ADD
        assert record.status == RefillStatus.SUCCESS
        assert record.error_message is None
        assert record.metadata is None
    
    def test_budget_refill_record_with_error(self):
        """Test creating a BudgetRefillRecord with error"""
        record = BudgetRefillRecord(
            user_id="test_user",
            email="test@example.com",
            amount=0.0,
            refill_type=RefillType.RESET,
            previous_balance=1000.0,
            new_balance=1000.0,
            status=RefillStatus.FAILED,
            timestamp=datetime.now(),
            error_message="Test error message",
            metadata={"test": "data"}
        )
        
        assert record.status == RefillStatus.FAILED
        assert record.error_message == "Test error message"
        assert record.metadata == {"test": "data"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 