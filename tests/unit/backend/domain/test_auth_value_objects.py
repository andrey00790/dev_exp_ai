"""
Unit Tests for Auth Domain Value Objects

Tests for immutable value objects with validation logic.
"""

import pytest
from datetime import datetime, timezone, timedelta

from backend.domain.auth.value_objects import (
    UserId, Email, Password, Token, RefreshToken
)


class TestUserId:
    """Test UserId value object"""
    
    def test_create_user_id_success(self):
        """Test successful UserId creation"""
        user_id = UserId("user_123")
        assert user_id.value == "user_123"
        assert str(user_id) == "user_123"
    
    def test_create_user_id_empty_fails(self):
        """Test UserId creation fails with empty value"""
        with pytest.raises(ValueError, match="UserId must be a non-empty string"):
            UserId("")
    
    def test_create_user_id_none_fails(self):
        """Test UserId creation fails with None"""
        with pytest.raises(ValueError, match="UserId must be a non-empty string"):
            UserId(None)
    
    def test_user_id_immutable(self):
        """Test UserId is immutable"""
        user_id = UserId("user_123")
        
        # Should not be able to modify
        with pytest.raises(AttributeError):
            user_id.value = "user_456"


class TestEmail:
    """Test Email value object"""
    
    def test_create_email_success(self):
        """Test successful Email creation"""
        email = Email("test@example.com")
        assert email.value == "test@example.com"
        assert str(email) == "test@example.com"
    
    def test_email_domain_property(self):
        """Test email domain property"""
        email = Email("user@example.com")
        assert email.domain == "example.com"
    
    def test_email_local_part_property(self):
        """Test email local part property"""
        email = Email("user@example.com")
        assert email.local_part == "user"
    
    def test_create_email_empty_fails(self):
        """Test Email creation fails with empty value"""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("")
    
    def test_create_email_invalid_format_fails(self):
        """Test Email creation fails with invalid format"""
        invalid_emails = [
            "invalid",        # No @ symbol
            "test.example.com"  # No @ symbol
        ]
        
        for invalid_email in invalid_emails:
            with pytest.raises(ValueError, match="Invalid email format"):
                Email(invalid_email)
    
    def test_valid_email_formats(self):
        """Test various valid email formats"""
        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "123@example.org",
            "a@b.co"
        ]
        
        for valid_email in valid_emails:
            email = Email(valid_email)
            assert email.value == valid_email
    
    def test_email_immutable(self):
        """Test Email is immutable"""
        email = Email("test@example.com")
        
        # Should not be able to modify
        with pytest.raises(AttributeError):
            email.value = "other@example.com"


class TestPassword:
    """Test Password value object"""
    
    def test_create_password_success(self):
        """Test successful Password creation"""
        password = Password("SecurePass123")
        assert password.value == "SecurePass123"
    
    def test_create_password_empty_fails(self):
        """Test Password creation fails with empty value"""
        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            Password("")
    
    def test_create_password_too_short_fails(self):
        """Test Password creation fails when too short"""
        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            Password("Short1")
    
    def test_create_password_no_uppercase_fails(self):
        """Test Password creation fails without uppercase"""
        with pytest.raises(ValueError, match="Password must contain at least one uppercase letter"):
            Password("lowercase123")
    
    def test_create_password_no_lowercase_fails(self):
        """Test Password creation fails without lowercase"""
        with pytest.raises(ValueError, match="Password must contain at least one lowercase letter"):
            Password("UPPERCASE123")
    
    def test_create_password_no_digit_fails(self):
        """Test Password creation fails without digit"""
        with pytest.raises(ValueError, match="Password must contain at least one digit"):
            Password("SecurePassword")
    
    def test_password_hash_generation(self):
        """Test password hash generation"""
        password = Password("SecurePass123")
        
        hash1 = password.hash()
        hash2 = password.hash()
        
        # Hashes should be different due to random salt
        assert hash1 != hash2
        assert ":" in hash1  # Should contain salt separator
        assert ":" in hash2
    
    def test_password_hash_with_custom_salt(self):
        """Test password hash with custom salt"""
        password = Password("SecurePass123")
        custom_salt = "custom_salt_123"
        
        hash1 = password.hash(custom_salt)
        hash2 = password.hash(custom_salt)
        
        # Same salt should produce same hash
        assert hash1 == hash2
        assert hash1.startswith(custom_salt + ":")
    
    def test_password_verification_success(self):
        """Test successful password verification"""
        password = Password("SecurePass123")
        hash_value = password.hash()
        
        assert password.verify(hash_value) is True
    
    def test_password_verification_failure(self):
        """Test password verification failure"""
        password1 = Password("SecurePass123")
        password2 = Password("DifferentPass123")
        
        hash_value = password1.hash()
        
        assert password2.verify(hash_value) is False
    
    def test_password_verification_invalid_hash(self):
        """Test password verification with invalid hash format"""
        password = Password("SecurePass123")
        
        invalid_hashes = [
            "invalid_hash",
            "no_separator",
            ":only_separator",
            "multiple:separators:here"
        ]
        
        for invalid_hash in invalid_hashes:
            assert password.verify(invalid_hash) is False
    
    def test_password_immutable(self):
        """Test Password is immutable"""
        password = Password("SecurePass123")
        
        # Should not be able to modify
        with pytest.raises(AttributeError):
            password.value = "DifferentPass123"


class TestToken:
    """Test Token value object"""
    
    def test_create_token_success(self):
        """Test successful Token creation"""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        token = Token("abc123token", "bearer", expires_at)
        
        assert token.value == "abc123token"
        assert token.token_type == "bearer"
        assert token.expires_at == expires_at
        # Token string representation shows full info, not just value
        assert "abc123token" in str(token)
    
    def test_create_token_default_type(self):
        """Test Token creation with default type"""
        token = Token("abc123token")
        assert token.token_type == "Bearer"
    
    def test_create_token_empty_value_fails(self):
        """Test Token creation fails with empty value"""
        with pytest.raises(ValueError, match="Token value cannot be empty"):
            Token("")
    
    def test_create_token_empty_type_fails(self):
        """Test Token creation fails with empty type"""
        with pytest.raises(ValueError, match="Token type cannot be empty"):
            Token("abc123token", "")
    
    def test_token_expiration_check(self):
        """Test token expiration checking"""
        # Future expiration - not expired
        future_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        future_token = Token("token123", expires_at=future_expiry)
        assert future_token.is_expired() is False
        assert future_token.is_valid() is True
        
        # Past expiration - expired
        past_expiry = datetime.now(timezone.utc) - timedelta(hours=1)
        past_token = Token("token123", expires_at=past_expiry)
        assert past_token.is_expired() is True
        assert past_token.is_valid() is False
        
        # No expiration - never expires
        no_expiry_token = Token("token123")
        assert no_expiry_token.is_expired() is False
        assert no_expiry_token.is_valid() is True
    
    def test_token_generate_class_method(self):
        """Test Token.generate class method"""
        token = Token.generate()
        
        assert len(token.value) > 0
        assert token.token_type == "Bearer"
        assert token.expires_at is not None
        assert token.expires_at > datetime.now(timezone.utc)
        assert token.is_valid() is True
    
    def test_token_generate_custom_params(self):
        """Test Token.generate with custom parameters"""
        token = Token.generate("JWT", 2)  # JWT type, 2 hours
        
        assert token.token_type == "JWT"
        assert token.expires_at is not None
        
        # Should expire in approximately 2 hours
        expected_expiry = datetime.now(timezone.utc) + timedelta(hours=2)
        time_diff = abs((token.expires_at - expected_expiry).total_seconds())
        assert time_diff < 60  # Within 1 minute tolerance
    
    def test_token_immutable(self):
        """Test Token is immutable"""
        token = Token("abc123token")
        
        # Should not be able to modify
        with pytest.raises(AttributeError):
            token.value = "different_token"


class TestRefreshToken:
    """Test RefreshToken value object"""
    
    def test_create_refresh_token_success(self):
        """Test successful RefreshToken creation"""
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        refresh_token = RefreshToken("refresh_abc123", "user_123", expires_at)
        
        assert refresh_token.value == "refresh_abc123"
        assert refresh_token.user_id == "user_123"
        assert refresh_token.expires_at == expires_at
        assert str(refresh_token) == "refresh_abc123"
    
    def test_create_refresh_token_empty_value_fails(self):
        """Test RefreshToken creation fails with empty value"""
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        
        with pytest.raises(ValueError, match="Refresh token value cannot be empty"):
            RefreshToken("", "user_123", expires_at)
    
    def test_create_refresh_token_empty_user_id_fails(self):
        """Test RefreshToken creation fails with empty user_id"""
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            RefreshToken("refresh_abc123", "", expires_at)
    
    def test_refresh_token_expiration_check(self):
        """Test refresh token expiration checking"""
        # Future expiration - not expired
        future_expiry = datetime.now(timezone.utc) + timedelta(days=30)
        future_token = RefreshToken("refresh123", "user_123", future_expiry)
        assert future_token.is_expired() is False
        assert future_token.is_valid() is True
        
        # Past expiration - expired
        past_expiry = datetime.now(timezone.utc) - timedelta(days=1)
        past_token = RefreshToken("refresh123", "user_123", past_expiry)
        assert past_token.is_expired() is True
        assert past_token.is_valid() is False
    
    def test_refresh_token_generate_class_method(self):
        """Test RefreshToken.generate class method"""
        refresh_token = RefreshToken.generate("user_123")
        
        assert len(refresh_token.value) > 0
        assert refresh_token.user_id == "user_123"
        assert refresh_token.expires_at is not None
        assert refresh_token.expires_at > datetime.now(timezone.utc)
        assert refresh_token.is_valid() is True
    
    def test_refresh_token_generate_custom_expiry(self):
        """Test RefreshToken.generate with custom expiry"""
        refresh_token = RefreshToken.generate("user_123", 7)  # 7 days
        
        # Should expire in approximately 7 days
        expected_expiry = datetime.now(timezone.utc) + timedelta(days=7)
        time_diff = abs((refresh_token.expires_at - expected_expiry).total_seconds())
        assert time_diff < 3600  # Within 1 hour tolerance
    
    def test_refresh_token_immutable(self):
        """Test RefreshToken is immutable"""
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        refresh_token = RefreshToken("refresh_abc123", "user_123", expires_at)
        
        # Should not be able to modify
        with pytest.raises(AttributeError):
            refresh_token.value = "different_token" 