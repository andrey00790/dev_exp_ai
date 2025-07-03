"""
Security module tests for AI Assistant MVP

Tests for authentication, rate limiting, input validation, and cost control.
"""

import os

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Set environment variables before imports
os.environ["SECRET_KEY"] = "test-secret-key-12345"

from app.main import app
from app.security.auth import USERS_DB, authenticate_user, create_access_token
from app.security.cost_control import BudgetStatus, cost_controller
from app.security.input_validation import (sanitize_string, validate_email,
                                           validate_input)


class TestAuthentication:
    """Test JWT authentication functionality"""

    def test_create_access_token(self):
        """Test JWT token creation"""
        test_data = {"sub": "test_user", "email": "test@example.com"}
        token = create_access_token(test_data)

        assert isinstance(token, str)
        assert len(token) > 10

    def test_authenticate_user_success(self):
        """Test successful user authentication"""
        user = authenticate_user("user@example.com", "user123")

        assert user is not None
        assert user.user_id == "user_001"
        assert user.is_active is True

    def test_authenticate_user_failure(self):
        """Test failed user authentication"""
        user = authenticate_user("nonexistent_user", "wrong_password")
        assert user is None


class TestInputValidation:
    """Test input validation and sanitization"""

    def test_validate_input_safe_content(self):
        """Test validation with safe content"""
        safe_content = "This is a safe string with normal content"
        result = validate_input(safe_content, "test_field")
        assert result == safe_content

    def test_validate_input_sql_injection(self):
        """Test SQL injection detection"""
        dangerous_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM users",
        ]

        for dangerous_input in dangerous_inputs:
            with pytest.raises(ValueError) as exc_info:
                validate_input(dangerous_input, "test_field")
            assert "Invalid content detected" in str(exc_info.value)

    def test_sanitize_string(self):
        """Test string sanitization"""
        test_input = "  Normal text without dangerous content  "
        result = sanitize_string(test_input)

        assert "Normal text" in result

        # Test that dangerous content raises an error
        dangerous_input = "  <script>alert('test')</script>  Normal text  "
        with pytest.raises(ValueError):
            sanitize_string(dangerous_input)

    def test_validate_email(self):
        """Test email validation"""
        valid_emails = ["test@example.com", "user.name@domain.co.uk"]
        invalid_emails = ["invalid-email", "@domain.com", "user@"]

        for email in valid_emails:
            result = validate_email(email)
            assert result == email.lower()

        for email in invalid_emails:
            with pytest.raises(ValueError):
                validate_email(email)


class TestCostControl:
    """Test cost control and budget management"""

    def test_get_user_budget_creation(self):
        """Test automatic budget creation for new users"""
        budget = cost_controller.get_user_budget("new_user")

        assert budget.user_id == "new_user"
        assert budget.daily_limit == 10.0
        assert budget.current_daily == 0.0
        assert budget.status == BudgetStatus.ACTIVE

    def test_calculate_cost(self):
        """Test cost calculation for different providers"""
        # Ollama should be free
        cost = cost_controller.calculate_cost("ollama", "mistral", 1000, 1000)
        assert cost == 0.0

        # OpenAI should have cost
        cost = cost_controller.calculate_cost("openai", "gpt-3.5-turbo", 1000, 1000)
        assert cost > 0.0


class TestAPIEndpoints:
    """Test security integration with API endpoints"""

    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)

    def test_login_endpoint(self):
        """Test login endpoint"""
        response = self.client.post(
            "/auth/login", json={"email": "user@example.com", "password": "user123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(
            "/auth/login",
            json={"email": "invalid@example.com", "password": "wrong_password"},
        )

        assert response.status_code == 401

    def test_demo_users_endpoint(self):
        """Test demo users endpoint"""
        response = self.client.get("/auth/demo-users")

        assert response.status_code == 200
        data = response.json()
        assert "demo_users" in data
        assert len(data["demo_users"]) > 0
