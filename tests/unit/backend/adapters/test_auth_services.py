"""
Unit Tests for Auth Service Adapters

Tests for infrastructure adapters that implement auth service ports.
Following hexagonal architecture testing principles.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from backend.domain.auth.value_objects import Password, Token, RefreshToken
from backend.adapters.auth.services import (
    BcryptPasswordHasher, JWTTokenGenerator, SMTPEmailService,
    FastAPIEventPublisher, MockEmailService, MockEventPublisher
)
from backend.application.auth.ports import (
    PasswordHasherPort, TokenGeneratorPort, EmailServicePort, EventPublisherPort
)


class TestBcryptPasswordHasher:
    """Test BcryptPasswordHasher adapter"""
    
    @pytest.fixture
    def password_hasher(self):
        """Create BcryptPasswordHasher instance"""
        return BcryptPasswordHasher()
    
    @pytest.fixture
    def sample_password(self):
        """Create sample password for testing"""
        return Password("Test_password_123")
    
    def test_hash_password_success(self, password_hasher, sample_password):
        """Test successful password hashing"""
        # Execute
        hashed = password_hasher.hash_password(sample_password)
        
        # Verify
        assert hashed is not None
        assert hashed != sample_password.value
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash prefix
    
    def test_hash_password_different_each_time(self, password_hasher, sample_password):
        """Test password hashing produces different hashes each time"""
        # Execute
        hash1 = password_hasher.hash_password(sample_password)
        hash2 = password_hasher.hash_password(sample_password)
        
        # Verify
        assert hash1 != hash2  # Different salts should produce different hashes
    
    def test_verify_password_success(self, password_hasher, sample_password):
        """Test successful password verification"""
        # Setup
        hashed = password_hasher.hash_password(sample_password)
        
        # Execute
        result = password_hasher.verify_password(sample_password, hashed)
        
        # Verify
        assert result == True
    
    def test_verify_password_wrong_password_fails(self, password_hasher, sample_password):
        """Test password verification with wrong password"""
        # Setup
        hashed = password_hasher.hash_password(sample_password)
        wrong_password = Password("WrongPassword123!")
        
        # Execute
        result = password_hasher.verify_password(wrong_password, hashed)
        
        # Verify
        assert result == False
    
    def test_verify_password_corrupted_hash_fails(self, password_hasher, sample_password):
        """Test password verification with corrupted hash"""
        # Setup
        corrupted_hash = "corrupted_hash"
        
        # Execute
        result = password_hasher.verify_password(sample_password, corrupted_hash)
        
        # Verify
        assert result == False
    
    def test_verify_password_empty_hash_fails(self, password_hasher, sample_password):
        """Test password verification with empty hash"""
        # Setup
        empty_hash = ""
        
        # Execute
        result = password_hasher.verify_password(sample_password, empty_hash)
        
        # Verify
        assert result == False
    
    @patch('bcrypt.hashpw')
    def test_hash_password_with_specific_rounds(self, mock_hashpw, password_hasher, sample_password):
        """Test password hashing uses correct number of rounds"""
        # Setup
        mock_hashpw.return_value = b"$2b$12$mocked_hash"
        
        # Execute
        password_hasher.hash_password(sample_password)
        
        # Verify
        mock_hashpw.assert_called_once()
        # Verify salt generation uses correct rounds (default 12)
        args, kwargs = mock_hashpw.call_args
        assert len(args) == 2
        assert args[0] == sample_password.value.encode('utf-8')
    
    @patch('bcrypt.checkpw')
    def test_verify_password_calls_bcrypt_checkpw(self, mock_checkpw, password_hasher, sample_password):
        """Test password verification calls bcrypt.checkpw"""
        # Setup
        mock_checkpw.return_value = True
        hashed = "$2b$12$mocked_hash"
        
        # Execute
        result = password_hasher.verify_password(sample_password, hashed)
        
        # Verify
        assert result == True
        mock_checkpw.assert_called_once_with(
            sample_password.value.encode('utf-8'),
            hashed.encode('utf-8')
        )


class TestJWTTokenGenerator:
    """Test JWTTokenGenerator adapter"""
    
    @pytest.fixture
    def token_generator(self):
        """Create JWTTokenGenerator instance"""
        return JWTTokenGenerator(
            secret_key="test_secret_key",
            algorithm="HS256"
        )
    
    @pytest.fixture
    def sample_user_id(self):
        """Create sample user ID for token generation"""
        from backend.domain.auth.value_objects import UserId
        return UserId("user_123")
    
    @pytest.fixture
    def sample_expires_in(self):
        """Create sample expiration time"""
        from datetime import timedelta
        return timedelta(minutes=30)
    
    def test_generate_access_token_success(self, token_generator, sample_user_id, sample_expires_in):
        """Test successful access token generation"""
        # Execute
        token = token_generator.generate_access_token(sample_user_id, sample_expires_in)
        
        # Verify
        from backend.domain.auth.value_objects import Token
        assert isinstance(token, Token)
        assert token.value is not None
        assert len(token.value) > 0
        assert token.token_type == "bearer"
        assert token.expires_at is not None
        
        # Verify token can be decoded
        import jwt
        decoded = jwt.decode(token.value, "test_secret_key", algorithms=["HS256"])
        assert decoded["user_id"] == "user_123"
        assert decoded["type"] == "access"
        assert "exp" in decoded
    
    def test_generate_access_token_with_expiration(self, token_generator, sample_user_id, sample_expires_in):
        """Test access token generation includes correct expiration"""
        # Execute
        token = token_generator.generate_access_token(sample_user_id, sample_expires_in)
        
        # Verify expiration
        decoded = jwt.decode(token.value, "test_secret_key", algorithms=["HS256"])
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        
        # Should expire in approximately 30 minutes
        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=30)
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 5  # Allow 5 seconds tolerance
    
    def test_generate_refresh_token_success(self, token_generator, sample_user_id):
        """Test successful refresh token generation"""
        # Execute
        token = token_generator.generate_refresh_token(sample_user_id)
        
        # Verify
        assert isinstance(token, Token)
        assert token.value is not None
        assert len(token.value) > 0
        assert token.token_type == "bearer"
        assert token.expires_at is not None
        
        # Verify token can be decoded
        decoded = jwt.decode(token.value, "test_secret_key", algorithms=["HS256"])
        assert decoded["user_id"] == "user_123"
        assert decoded["type"] == "refresh"
        assert "exp" in decoded
    
    def test_generate_refresh_token_with_expiration(self, token_generator, sample_user_id):
        """Test refresh token generation includes correct expiration"""
        # Execute
        token = token_generator.generate_refresh_token(sample_user_id)
        
        # Verify expiration
        decoded = jwt.decode(token.value, "test_secret_key", algorithms=["HS256"])
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        
        # Should expire in approximately 30 days
        expected_exp = datetime.now(timezone.utc) + timedelta(days=30)
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 60  # Allow 1 minute tolerance
    
    def test_validate_token_success(self, token_generator, sample_user_id, sample_expires_in):
        """Test successful token validation"""
        # Setup
        token = token_generator.generate_access_token(sample_user_id, sample_expires_in)
        
        # Execute
        result = token_generator.validate_token(token)
        
        # Verify
        assert result is True
    
    def test_validate_token_invalid_token_fails(self, token_generator):
        """Test token validation with invalid token"""
        # Setup
        invalid_token = Token("invalid_token")
        
        # Execute
        result = token_generator.validate_token(invalid_token)
        
        # Verify
        assert result is False
    
    def test_validate_token_expired_token_fails(self, token_generator, sample_user_id):
        """Test token validation with expired token"""
        # Setup - create token with past expiration
        past_time = datetime.now(timezone.utc) - timedelta(minutes=1)
        payload = {
            "user_id": "user_123",
            "type": "access",
            "exp": past_time.timestamp()
        }
        expired_token = Token(jwt.encode(payload, "test_secret_key", algorithm="HS256"))
        
        # Execute
        result = token_generator.validate_token(expired_token)
        
        # Verify
        assert result is False
    
    def test_decode_token_success(self, token_generator, sample_user_id, sample_expires_in):
        """Test successful token decoding"""
        # Setup
        token = token_generator.generate_access_token(sample_user_id, sample_expires_in)
        
        # Execute
        payload = token_generator.decode_token(token)
        
        # Verify
        assert payload is not None
        assert payload["user_id"] == "user_123"
        assert payload["type"] == "access"
        assert "exp" in payload
    
    def test_decode_token_invalid_token_fails(self, token_generator):
        """Test token decoding with invalid token"""
        # Setup
        invalid_token = Token("invalid_token")
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Invalid token"):
            token_generator.decode_token(invalid_token)
    
    @pytest.mark.asyncio
    async def test_generate_jwt_success(self, token_generator):
        """Test successful JWT generation"""
        # Setup
        payload = {
            "user_id": "user_123",
            "email": "test@example.com",
            "exp": (datetime.now(timezone.utc) + timedelta(hours=2)).timestamp()
        }
        
        # Execute
        jwt_token = await token_generator.generate_jwt(payload)
        
        # Verify
        assert jwt_token is not None
        assert len(jwt_token) > 0
        
        # Verify token can be decoded
        decoded = jwt.decode(jwt_token, "test_secret_key", algorithms=["HS256"], options={"verify_exp": False})
        assert decoded["user_id"] == "user_123"
        assert decoded["email"] == "test@example.com"


class TestSMTPEmailService:
    """Test SMTPEmailService adapter"""
    
    @pytest.fixture
    def email_service(self):
        """Create SMTPEmailService instance"""
        return SMTPEmailService(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="test_password",
            use_tls=True
        )
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_send_email_success(self, email_service):
        """Test successful email sending"""
        with patch('smtplib.SMTP') as mock_smtp:
            # Setup
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            mock_server.starttls.return_value = None
            mock_server.login.return_value = None
            mock_server.send_message.return_value = None
            mock_server.quit.return_value = None
            
            # Execute
            await email_service.send_email(
                to="recipient@example.com",
                subject="Test Subject",
                body="Test Body"
            )
            
            # Verify
            mock_smtp.assert_called_once_with("smtp.example.com", 587)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("test@example.com", "test_password")
            mock_server.send_message.assert_called_once()
            mock_server.quit.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_send_email_with_html_body(self, email_service):
        """Test email sending with HTML body"""
        with patch('smtplib.SMTP') as mock_smtp:
            # Setup
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            mock_server.starttls.return_value = None
            mock_server.login.return_value = None
            mock_server.send_message.return_value = None
            mock_server.quit.return_value = None
            
            # Execute
            await email_service.send_email(
                to="recipient@example.com",
                subject="Test Subject",
                body="<h1>Test HTML Body</h1>",
                is_html=True
            )
            
            # Verify
            mock_server.send_message.assert_called_once()
            # Verify HTML content was set
            sent_message = mock_server.send_message.call_args[0][0]
            assert sent_message.is_multipart()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_send_email_smtp_connection_error(self, email_service):
        """Test email sending with SMTP connection error"""
        with patch('smtplib.SMTP') as mock_smtp:
            # Setup
            mock_smtp.side_effect = smtplib.SMTPConnectError("Connection failed")
            
            # Execute & Verify
            with pytest.raises(Exception, match="Connection failed"):
                await email_service.send_email(
                    to="recipient@example.com",
                    subject="Test Subject",
                    body="Test Body"
                )
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_send_email_authentication_error(self, email_service):
        """Test email sending with authentication error"""
        with patch('smtplib.SMTP') as mock_smtp:
            # Setup
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            mock_server.starttls.return_value = None
            mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
            mock_server.quit.return_value = None
            
            # Execute & Verify
            with pytest.raises(smtplib.SMTPAuthenticationError):
                await email_service.send_email(
                    to="recipient@example.com",
                    subject="Test Subject",
                    body="Test Body"
                )
            
            # Verify cleanup
            mock_server.quit.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_send_email_without_tls(self, email_service):
        """Test email sending without TLS"""
        # Setup service without TLS
        email_service_no_tls = SMTPEmailService(
            smtp_server="smtp.example.com",
            smtp_port=25,
            username="test@example.com",
            password="test_password",
            use_tls=False
        )
        
        with patch('smtplib.SMTP') as mock_smtp:
            # Setup
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            mock_server.login.return_value = None
            mock_server.send_message.return_value = None
            mock_server.quit.return_value = None
            
            # Execute
            await email_service_no_tls.send_email(
                to="recipient@example.com",
                subject="Test Subject",
                body="Test Body"
            )
            
            # Verify
            mock_smtp.assert_called_once_with("smtp.example.com", 25)
            mock_server.starttls.assert_not_called()  # TLS not used
            mock_server.login.assert_called_once()
            mock_server.send_message.assert_called_once()
            mock_server.quit.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_send_welcome_email_success(self, email_service):
        """Test successful welcome email sending"""
        with patch('smtplib.SMTP') as mock_smtp:
            # Setup
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            mock_server.starttls.return_value = None
            mock_server.login.return_value = None
            mock_server.send_message.return_value = None
            mock_server.quit.return_value = None
            
            # Execute
            await email_service.send_welcome_email(
                to="newuser@example.com",
                username="newuser"
            )
            
            # Verify
            mock_server.send_message.assert_called_once()
            sent_message = mock_server.send_message.call_args[0][0]
            assert "Welcome" in sent_message["Subject"]
            assert "newuser" in sent_message.get_payload()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_send_password_reset_email_success(self, email_service):
        """Test successful password reset email sending"""
        with patch('smtplib.SMTP') as mock_smtp:
            # Setup
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            mock_server.starttls.return_value = None
            mock_server.login.return_value = None
            mock_server.send_message.return_value = None
            mock_server.quit.return_value = None
            
            # Execute
            await email_service.send_password_reset_email(
                to="user@example.com",
                reset_token="reset_token_123"
            )
            
            # Verify
            mock_server.send_message.assert_called_once()
            sent_message = mock_server.send_message.call_args[0][0]
            assert "Password Reset" in sent_message["Subject"]
            assert "reset_token_123" in sent_message.get_payload()


class TestFastAPIEventPublisher:
    """Test FastAPIEventPublisher adapter"""
    
    @pytest.fixture
    def event_publisher(self):
        """Create FastAPIEventPublisher instance"""
        return FastAPIEventPublisher()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_publish_event_success(self, event_publisher):
        """Test successful event publishing"""
        with patch('logging.getLogger') as mock_get_logger:
            # Setup
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Execute
            await event_publisher.publish(
                event_type="user.created",
                data={"user_id": "user_123", "email": "test@example.com"}
            )
            
            # Verify
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "user.created" in log_message
            assert "user_123" in log_message
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_publish_event_with_empty_data(self, event_publisher):
        """Test event publishing with empty data"""
        with patch('logging.getLogger') as mock_get_logger:
            # Setup
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Execute
            await event_publisher.publish(
                event_type="system.health_check",
                data={}
            )
            
            # Verify
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "system.health_check" in log_message
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_publish_event_with_complex_data(self, event_publisher):
        """Test event publishing with complex data"""
        with patch('logging.getLogger') as mock_get_logger:
            # Setup
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            complex_data = {
                "user_id": "user_123",
                "metadata": {
                    "timestamp": "2023-01-01T00:00:00Z",
                    "source": "api",
                    "tags": ["test", "demo"]
                },
                "counts": [1, 2, 3]
            }
            
            # Execute
            await event_publisher.publish(
                event_type="user.activity",
                data=complex_data
            )
            
            # Verify
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "user.activity" in log_message
            assert "user_123" in log_message


class TestMockEmailService:
    """Test MockEmailService adapter"""
    
    @pytest.fixture
    def mock_email_service(self):
        """Create MockEmailService instance"""
        return MockEmailService()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_email_service):
        """Test successful mock email sending"""
        # Execute
        await mock_email_service.send_email(
            to="recipient@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        
        # Verify
        assert len(mock_email_service.sent_emails) == 1
        sent_email = mock_email_service.sent_emails[0]
        assert sent_email["to"] == "recipient@example.com"
        assert sent_email["subject"] == "Test Subject"
        assert sent_email["body"] == "Test Body"
        assert sent_email["is_html"] == False
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_send_email_with_html(self, mock_email_service):
        """Test mock email sending with HTML"""
        # Execute
        await mock_email_service.send_email(
            to="recipient@example.com",
            subject="Test Subject",
            body="<h1>Test HTML Body</h1>",
            is_html=True
        )
        
        # Verify
        assert len(mock_email_service.sent_emails) == 1
        sent_email = mock_email_service.sent_emails[0]
        assert sent_email["to"] == "recipient@example.com"
        assert sent_email["subject"] == "Test Subject"
        assert sent_email["body"] == "<h1>Test HTML Body</h1>"
        assert sent_email["is_html"] == True
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_send_welcome_email_success(self, mock_email_service):
        """Test successful mock welcome email sending"""
        # Execute
        await mock_email_service.send_welcome_email(
            to="newuser@example.com",
            username="newuser"
        )
        
        # Verify
        assert len(mock_email_service.sent_emails) == 1
        sent_email = mock_email_service.sent_emails[0]
        assert sent_email["to"] == "newuser@example.com"
        assert "Welcome" in sent_email["subject"]
        assert "newuser" in sent_email["body"]
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_send_password_reset_email_success(self, mock_email_service):
        """Test successful mock password reset email sending"""
        # Execute
        await mock_email_service.send_password_reset_email(
            to="user@example.com",
            reset_token="reset_token_123"
        )
        
        # Verify
        assert len(mock_email_service.sent_emails) == 1
        sent_email = mock_email_service.sent_emails[0]
        assert sent_email["to"] == "user@example.com"
        assert "Password Reset" in sent_email["subject"]
        assert "reset_token_123" in sent_email["body"]
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_multiple_emails_tracking(self, mock_email_service):
        """Test tracking of multiple emails"""
        # Execute
        await mock_email_service.send_email(
            to="user1@example.com",
            subject="Subject 1",
            body="Body 1"
        )
        await mock_email_service.send_email(
            to="user2@example.com",
            subject="Subject 2",
            body="Body 2"
        )
        
        # Verify
        assert len(mock_email_service.sent_emails) == 2
        assert mock_email_service.sent_emails[0]["to"] == "user1@example.com"
        assert mock_email_service.sent_emails[1]["to"] == "user2@example.com"
    
    def test_clear_sent_emails(self, mock_email_service):
        """Test clearing sent emails"""
        # Setup
        mock_email_service.sent_emails = [{"test": "email"}]
        
        # Execute
        mock_email_service.clear_sent_emails()
        
        # Verify
        assert len(mock_email_service.sent_emails) == 0


class TestMockEventPublisher:
    """Test MockEventPublisher adapter"""
    
    @pytest.fixture
    def mock_event_publisher(self):
        """Create MockEventPublisher instance"""
        return MockEventPublisher()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_publish_event_success(self, mock_event_publisher):
        """Test successful mock event publishing"""
        # Execute
        await mock_event_publisher.publish(
            event_type="user.created",
            data={"user_id": "user_123", "email": "test@example.com"}
        )
        
        # Verify
        assert len(mock_event_publisher.published_events) == 1
        published_event = mock_event_publisher.published_events[0]
        assert published_event["event_type"] == "user.created"
        assert published_event["data"]["user_id"] == "user_123"
        assert published_event["data"]["email"] == "test@example.com"
        assert "timestamp" in published_event
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_publish_event_with_empty_data(self, mock_event_publisher):
        """Test mock event publishing with empty data"""
        # Execute
        await mock_event_publisher.publish(
            event_type="system.health_check",
            data={}
        )
        
        # Verify
        assert len(mock_event_publisher.published_events) == 1
        published_event = mock_event_publisher.published_events[0]
        assert published_event["event_type"] == "system.health_check"
        assert published_event["data"] == {}
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_multiple_events_tracking(self, mock_event_publisher):
        """Test tracking of multiple events"""
        # Execute
        await mock_event_publisher.publish(
            event_type="user.created",
            data={"user_id": "user_123"}
        )
        await mock_event_publisher.publish(
            event_type="user.updated",
            data={"user_id": "user_123", "field": "email"}
        )
        
        # Verify
        assert len(mock_event_publisher.published_events) == 2
        assert mock_event_publisher.published_events[0]["event_type"] == "user.created"
        assert mock_event_publisher.published_events[1]["event_type"] == "user.updated"
    
    def test_clear_published_events(self, mock_event_publisher):
        """Test clearing published events"""
        # Setup
        mock_event_publisher.published_events = [{"test": "event"}]
        
        # Execute
        mock_event_publisher.clear_published_events()
        
        # Verify
        assert len(mock_event_publisher.published_events) == 0
    
    def test_get_events_by_type(self, mock_event_publisher):
        """Test getting events by type"""
        # Setup
        mock_event_publisher.published_events = [
            {"event_type": "user.created", "data": {"user_id": "user_1"}},
            {"event_type": "user.updated", "data": {"user_id": "user_1"}},
            {"event_type": "user.created", "data": {"user_id": "user_2"}},
        ]
        
        # Execute
        user_created_events = mock_event_publisher.get_events_by_type("user.created")
        
        # Verify
        assert len(user_created_events) == 2
        assert user_created_events[0]["data"]["user_id"] == "user_1"
        assert user_created_events[1]["data"]["user_id"] == "user_2"
    
    def test_get_events_by_type_not_found(self, mock_event_publisher):
        """Test getting events by type when none found"""
        # Setup
        mock_event_publisher.published_events = [
            {"event_type": "user.created", "data": {"user_id": "user_1"}},
        ]
        
        # Execute
        system_events = mock_event_publisher.get_events_by_type("system.health_check")
        
        # Verify
        assert len(system_events) == 0 