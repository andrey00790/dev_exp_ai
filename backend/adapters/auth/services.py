"""
Auth Service Adapters

Infrastructure implementations of auth service ports.
These adapters connect domain logic to external systems.
"""

import secrets
import hashlib
import smtplib
from datetime import datetime, timedelta, timezone
from typing import List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import bcrypt
import jwt
from fastapi import BackgroundTasks

from backend.domain.auth.entities import User, Role
from backend.domain.auth.value_objects import UserId, Token
from backend.application.auth.ports import (
    PasswordHasherPort,
    TokenGeneratorPort,
    EmailServicePort,
    EventPublisherPort
)


class BcryptPasswordHasher(PasswordHasherPort):
    """Bcrypt implementation of PasswordHasherPort"""
    
    def __init__(self, rounds: int = 12):
        self.rounds = rounds
    
    def hash_password(self, password) -> str:
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt(rounds=self.rounds)
        password_value = password.value if hasattr(password, 'value') else password
        hashed = bcrypt.hashpw(password_value.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password, hash_value: str) -> bool:
        """Verify password against bcrypt hash"""
        try:
            password_value = password.value if hasattr(password, 'value') else password
            return bcrypt.checkpw(password_value.encode('utf-8'), hash_value.encode('utf-8'))
        except Exception:
            return False


class JWTTokenGenerator(TokenGeneratorPort):
    """JWT implementation of TokenGeneratorPort"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def generate_access_token(self, user_id: UserId, expires_in: timedelta) -> Token:
        """Generate JWT access token"""
        payload = {
            "user_id": user_id.value,
            "type": "access",
            "exp": datetime.now(timezone.utc) + expires_in,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_hex(16)
        }
        
        token_value = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        expires_at = datetime.now(timezone.utc) + expires_in
        
        return Token(value=token_value, token_type="bearer", expires_at=expires_at)
    
    def generate_refresh_token(self, user_id: UserId) -> Token:
        """Generate JWT refresh token"""
        expires_in = timedelta(days=30)  # Refresh tokens last longer
        payload = {
            "user_id": user_id.value,
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + expires_in,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_hex(16)
        }
        
        token_value = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        expires_at = datetime.now(timezone.utc) + expires_in
        
        return Token(value=token_value, token_type="bearer", expires_at=expires_at)
    
    def validate_token(self, token: Token) -> bool:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token.value, self.secret_key, algorithms=[self.algorithm])
            
            # Check expiration
            exp = datetime.fromtimestamp(payload.get('exp', 0), tz=timezone.utc)
            if datetime.now(timezone.utc) > exp:
                return False
                
            return True
        except jwt.InvalidTokenError:
            return False
        except Exception:
            return False
    
    def decode_token(self, token: Token) -> dict:
        """Decode JWT token payload"""
        try:
            return jwt.decode(token.value, self.secret_key, algorithms=[self.algorithm])
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    async def generate_jwt(self, payload: dict) -> str:
        """Generate JWT token from payload"""
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)


class SMTPEmailService(EmailServicePort):
    """SMTP implementation of EmailServicePort"""
    
    def __init__(
        self, 
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        use_tls: bool = True
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls
    
    async def send_welcome_email(self, user: User) -> bool:
        """Send welcome email to user"""
        subject = "Welcome to AI Assistant!"
        
        html_content = f"""
        <html>
        <body>
            <h2>Welcome, {user.name}!</h2>
            <p>Thank you for joining our AI Assistant platform.</p>
            <p>Your account has been successfully created with email: <strong>{user.email.value}</strong></p>
            <p>You can now start using our AI-powered features to enhance your development workflow.</p>
            <br>
            <p>Best regards,<br>AI Assistant Team</p>
        </body>
        </html>
        """
        
        return await self._send_email(user.email.value, subject, html_content)
    
    async def send_password_reset_email(self, user: User, reset_token: str) -> bool:
        """Send password reset email"""
        subject = "Password Reset Request"
        
        reset_url = f"https://your-domain.com/reset-password?token={reset_token}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hello {user.name},</p>
            <p>You have requested to reset your password. Click the link below to proceed:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
            <br>
            <p>Best regards,<br>AI Assistant Team</p>
        </body>
        </html>
        """
        
        return await self._send_email(user.email.value, subject, html_content)
    
    async def send_verification_email(self, user: User, verification_token: str) -> bool:
        """Send email verification"""
        subject = "Verify Your Email Address"
        
        verification_url = f"https://your-domain.com/verify-email?token={verification_token}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Verify Your Email Address</h2>
            <p>Hello {user.name},</p>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_url}">Verify Email</a></p>
            <p>This link will expire in 24 hours.</p>
            <br>
            <p>Best regards,<br>AI Assistant Team</p>
        </body>
        </html>
        """
        
        return await self._send_email(user.email.value, subject, html_content)
    
    async def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Internal method to send email via SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            
            if self.use_tls:
                server.starttls()
            
            server.login(self.username, self.password)
            server.sendmail(self.from_email, [to_email], msg.as_string())
            server.quit()
            
            return True
            
        except Exception as e:
            # Log error in real implementation
            print(f"Email sending failed: {e}")
            return False


class FastAPIEventPublisher(EventPublisherPort):
    """FastAPI background tasks implementation of EventPublisherPort"""
    
    def __init__(self, background_tasks: BackgroundTasks):
        self.background_tasks = background_tasks
    
    async def publish_user_created(self, user: User) -> None:
        """Publish user created event"""
        event_data = {
            "event_type": "user_created",
            "user_id": user.id.value,
            "user_email": user.email.value,
            "user_name": user.name,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.background_tasks.add_task(self._process_event, event_data)
    
    async def publish_user_authenticated(self, user: User) -> None:
        """Publish user authenticated event"""
        event_data = {
            "event_type": "user_authenticated",
            "user_id": user.id.value,
            "user_email": user.email.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.background_tasks.add_task(self._process_event, event_data)
    
    async def publish_user_role_changed(
        self, 
        user: User, 
        old_roles: List[Role], 
        new_roles: List[Role]
    ) -> None:
        """Publish user role changed event"""
        event_data = {
            "event_type": "user_role_changed",
            "user_id": user.id.value,
            "user_email": user.email.value,
            "old_roles": [role.name for role in old_roles],
            "new_roles": [role.name for role in new_roles],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.background_tasks.add_task(self._process_event, event_data)
    
    async def publish_password_changed(self, user: User) -> None:
        """Publish password changed event"""
        event_data = {
            "event_type": "password_changed",
            "user_id": user.id.value,
            "user_email": user.email.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.background_tasks.add_task(self._process_event, event_data)
    
    def _process_event(self, event_data: dict) -> None:
        """Process event (background task)"""
        try:
            # In a real implementation, this would:
            # 1. Send to event bus (RabbitMQ, Kafka, etc.)
            # 2. Store in event store
            # 3. Trigger webhooks
            # 4. Send notifications
            
            print(f"Processing event: {event_data['event_type']} for user {event_data.get('user_id')}")
            
            # Example processing based on event type
            if event_data['event_type'] == 'user_created':
                self._handle_user_created(event_data)
            elif event_data['event_type'] == 'user_authenticated':
                self._handle_user_authenticated(event_data)
            elif event_data['event_type'] == 'user_role_changed':
                self._handle_user_role_changed(event_data)
            elif event_data['event_type'] == 'password_changed':
                self._handle_password_changed(event_data)
                
        except Exception as e:
            print(f"Event processing failed: {e}")
    
    def _handle_user_created(self, event_data: dict) -> None:
        """Handle user created event"""
        # Analytics tracking, welcome email trigger, etc.
        pass
    
    def _handle_user_authenticated(self, event_data: dict) -> None:
        """Handle user authenticated event"""
        # Update last login, security monitoring, etc.
        pass
    
    def _handle_user_role_changed(self, event_data: dict) -> None:
        """Handle user role changed event"""
        # Audit logging, permission cache invalidation, etc.
        pass
    
    def _handle_password_changed(self, event_data: dict) -> None:
        """Handle password changed event"""
        # Security alerts, session invalidation, etc.
        pass


# Mock implementations for testing and development

class MockEmailService(EmailServicePort):
    """Mock email service for testing"""
    
    def __init__(self):
        self.sent_emails = []
    
    async def send_welcome_email(self, user: User) -> bool:
        self.sent_emails.append({
            "type": "welcome",
            "to": user.email.value,
            "user_name": user.name
        })
        return True
    
    async def send_password_reset_email(self, user: User, reset_token: str) -> bool:
        self.sent_emails.append({
            "type": "password_reset",
            "to": user.email.value,
            "token": reset_token
        })
        return True
    
    async def send_verification_email(self, user: User, verification_token: str) -> bool:
        self.sent_emails.append({
            "type": "verification",
            "to": user.email.value,
            "token": verification_token
        })
        return True


class MockEventPublisher(EventPublisherPort):
    """Mock event publisher for testing"""
    
    def __init__(self):
        self.published_events = []
    
    async def publish_user_created(self, user: User) -> None:
        self.published_events.append({
            "type": "user_created",
            "user_id": user.id.value
        })
    
    async def publish_user_authenticated(self, user: User) -> None:
        self.published_events.append({
            "type": "user_authenticated",
            "user_id": user.id.value
        })
    
    async def publish_user_role_changed(
        self, 
        user: User, 
        old_roles: List[Role], 
        new_roles: List[Role]
    ) -> None:
        self.published_events.append({
            "type": "user_role_changed",
            "user_id": user.id.value,
            "old_roles": [r.name for r in old_roles],
            "new_roles": [r.name for r in new_roles]
        })
    
    async def publish_password_changed(self, user: User) -> None:
        self.published_events.append({
            "type": "password_changed",
            "user_id": user.id.value
        })
    
    async def publish_user_logged_in(self, user: User) -> None:
        """Publish user logged in event"""
        self.published_events.append({
            "type": "user_logged_in",
            "user_id": user.id.value
        })
    
    async def publish_user_logged_out(self, user: User) -> None:
        """Publish user logged out event"""
        self.published_events.append({
            "type": "user_logged_out",
            "user_id": user.id.value
        })
    
    async def publish_role_assigned(self, user: User, role: Role) -> None:
        """Publish role assigned event"""
        self.published_events.append({
            "type": "role_assigned",
            "user_id": user.id.value,
            "role_name": role.name
        })
    
    async def publish_role_revoked(self, user: User, role: Role) -> None:
        """Publish role revoked event"""
        self.published_events.append({
            "type": "role_revoked",
            "user_id": user.id.value,
            "role_name": role.name
        }) 