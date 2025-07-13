"""
Advanced Security System for AI Assistant MVP
Version: 8.0 Enterprise Security

Comprehensive security hardening including:
- Multi-factor authentication (MFA)
- Advanced threat detection
- Zero-trust security patterns
- Real-time security monitoring
- Automated incident response
"""

import asyncio
import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import bcrypt
import pyotp
import qrcode
from io import BytesIO
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, and_, or_

from app.core.async_utils import async_retry, with_timeout
from app.database.session import get_async_session

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Security threat levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(Enum):
    """Types of security events"""
    LOGIN_ATTEMPT = "login_attempt"
    LOGIN_FAILED = "login_failed"
    LOGIN_SUCCESS = "login_success"
    MFA_CHALLENGE = "mfa_challenge"
    MFA_FAILED = "mfa_failed"
    MFA_SUCCESS = "mfa_success"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"
    MALICIOUS_INPUT = "malicious_input"
    SESSION_HIJACK = "session_hijack"


@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: SecurityEventType
    threat_level: ThreatLevel
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    details: Dict[str, Any]
    resolved: bool = False
    response_action: Optional[str] = None


@dataclass
class MFASetup:
    """MFA setup information"""
    user_id: str
    secret: str
    qr_code: str
    backup_codes: List[str]
    enabled: bool = False


class AdvancedSecurityManager:
    """Advanced security management system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.failed_attempts = {}  # Track failed login attempts
        self.suspicious_ips = set()  # Suspicious IP addresses
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for sensitive data"""
        try:
            # In production, this should come from secure key management
            key_material = b"ai_assistant_security_key_v8_enterprise"
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"ai_assistant_salt",
                iterations=100000,
            )
            return base64.urlsafe_b64encode(kdf.derive(key_material))
        except Exception as e:
            self.logger.error(f"Error creating encryption key: {e}")
            return Fernet.generate_key()

    @async_retry(max_attempts=3, delay=1.0)
    async def setup_mfa_for_user(self, user_id: str) -> MFASetup:
        """Setup MFA for a user"""
        try:
            # Generate secret for TOTP
            secret = pyotp.random_base32()
            
            # Generate QR code
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user_id,
                issuer_name="AI Assistant MVP"
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffered = BytesIO()
            img.save(buffered)
            qr_code_b64 = base64.b64encode(buffered.getvalue()).decode()
            
            # Generate backup codes
            backup_codes = [secrets.token_hex(4) for _ in range(10)]
            
            # Store in database (encrypted)
            async with get_async_session() as session:
                encrypted_secret = self.fernet.encrypt(secret.encode()).decode()
                encrypted_codes = self.fernet.encrypt(json.dumps(backup_codes).encode()).decode()
                
                await session.execute(
                    text("""
                        INSERT INTO user_mfa (user_id, secret, backup_codes, enabled, created_at)
                        VALUES (:user_id, :secret, :backup_codes, :enabled, :created_at)
                        ON CONFLICT (user_id) DO UPDATE SET
                            secret = :secret,
                            backup_codes = :backup_codes,
                            enabled = :enabled,
                            updated_at = :created_at
                    """),
                    {
                        "user_id": user_id,
                        "secret": encrypted_secret,
                        "backup_codes": encrypted_codes,
                        "enabled": False,
                        "created_at": datetime.now(timezone.utc)
                    }
                )
                await session.commit()
            
            self.logger.info(f"✅ MFA setup initiated for user: {user_id}")
            
            return MFASetup(
                user_id=user_id,
                secret=secret,
                qr_code=qr_code_b64,
                backup_codes=backup_codes,
                enabled=False
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error setting up MFA for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="MFA setup failed")

    async def verify_mfa_token(self, user_id: str, token: str, is_backup_code: bool = False) -> bool:
        """Verify MFA token or backup code"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    text("SELECT secret, backup_codes, enabled FROM user_mfa WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )
                mfa_data = result.fetchone()
                
                if not mfa_data or not mfa_data.enabled:
                    return False
                
                # Decrypt stored data
                secret = self.fernet.decrypt(mfa_data.secret.encode()).decode()
                backup_codes = json.loads(self.fernet.decrypt(mfa_data.backup_codes.encode()).decode())
                
                if is_backup_code:
                    # Verify backup code
                    if token in backup_codes:
                        # Remove used backup code
                        backup_codes.remove(token)
                        encrypted_codes = self.fernet.encrypt(json.dumps(backup_codes).encode()).decode()
                        
                        await session.execute(
                            text("UPDATE user_mfa SET backup_codes = :backup_codes WHERE user_id = :user_id"),
                            {"backup_codes": encrypted_codes, "user_id": user_id}
                        )
                        await session.commit()
                        
                        await self.log_security_event(
                            SecurityEvent(
                                event_type=SecurityEventType.MFA_SUCCESS,
                                threat_level=ThreatLevel.LOW,
                                user_id=user_id,
                                ip_address="",
                                user_agent="",
                                timestamp=datetime.now(timezone.utc),
                                details={"method": "backup_code"}
                            )
                        )
                        return True
                else:
                    # Verify TOTP token
                    totp = pyotp.TOTP(secret)
                    if totp.verify(token, valid_window=1):  # Allow 1 step tolerance
                        await self.log_security_event(
                            SecurityEvent(
                                event_type=SecurityEventType.MFA_SUCCESS,
                                threat_level=ThreatLevel.LOW,
                                user_id=user_id,
                                ip_address="",
                                user_agent="",
                                timestamp=datetime.now(timezone.utc),
                                details={"method": "totp"}
                            )
                        )
                        return True
                
                # Log failed MFA attempt
                await self.log_security_event(
                    SecurityEvent(
                        event_type=SecurityEventType.MFA_FAILED,
                        threat_level=ThreatLevel.MEDIUM,
                        user_id=user_id,
                        ip_address="",
                        user_agent="",
                        timestamp=datetime.now(timezone.utc),
                        details={"method": "backup_code" if is_backup_code else "totp"}
                    )
                )
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error verifying MFA for user {user_id}: {e}")
            return False

    async def enable_mfa_for_user(self, user_id: str, verification_token: str) -> bool:
        """Enable MFA after initial verification"""
        try:
            # First verify the token
            if await self.verify_mfa_token(user_id, verification_token):
                async with get_async_session() as session:
                    await session.execute(
                        text("UPDATE user_mfa SET enabled = true WHERE user_id = :user_id"),
                        {"user_id": user_id}
                    )
                    await session.commit()
                
                self.logger.info(f"✅ MFA enabled for user: {user_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error enabling MFA for user {user_id}: {e}")
            return False

    async def detect_suspicious_activity(self, request: Request, user_id: Optional[str] = None) -> bool:
        """Advanced threat detection"""
        try:
            ip_address = request.client.host
            user_agent = request.headers.get("user-agent", "")
            
            # Check for suspicious patterns
            suspicious_indicators = []
            
            # 1. Rate limiting check
            if await self._check_rate_limiting(ip_address, user_id):
                suspicious_indicators.append("rate_limit_exceeded")
            
            # 2. Geolocation anomaly (simplified)
            if await self._check_geolocation_anomaly(ip_address, user_id):
                suspicious_indicators.append("geolocation_anomaly")
            
            # 3. User agent analysis
            if self._analyze_user_agent(user_agent):
                suspicious_indicators.append("suspicious_user_agent")
            
            # 4. Session behavior analysis
            if await self._analyze_session_behavior(request, user_id):
                suspicious_indicators.append("anomalous_behavior")
            
            # 5. Known malicious IP check
            if ip_address in self.suspicious_ips:
                suspicious_indicators.append("known_malicious_ip")
            
            if suspicious_indicators:
                threat_level = self._calculate_threat_level(suspicious_indicators)
                
                await self.log_security_event(
                    SecurityEvent(
                        event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                        threat_level=threat_level,
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        timestamp=datetime.now(timezone.utc),
                        details={"indicators": suspicious_indicators}
                    )
                )
                
                # Auto-response based on threat level
                if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                    await self._auto_response(ip_address, user_id, threat_level)
                
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error in threat detection: {e}")
            return False

    async def validate_input_security(self, input_data: Any, input_type: str = "general") -> Tuple[bool, List[str]]:
        """Advanced input validation and sanitization"""
        try:
            violations = []
            
            if isinstance(input_data, str):
                # SQL injection patterns
                sql_patterns = [
                    r"(\bunion\b.*\bselect\b)",
                    r"(\bdrop\b.*\btable\b)",
                    r"(\binsert\b.*\binto\b)",
                    r"(\bdelete\b.*\bfrom\b)",
                    r"(\bupdate\b.*\bset\b)",
                    r"(--\s*$)",
                    r"(/\*.*\*/)",
                    r"(\bor\b.*=.*\bor\b)",
                    r"(\band\b.*=.*\band\b)"
                ]
                
                # XSS patterns
                xss_patterns = [
                    r"<script[^>]*>",
                    r"javascript:",
                    r"vbscript:",
                    r"onload\s*=",
                    r"onerror\s*=",
                    r"onclick\s*="
                ]
                
                # Command injection patterns
                cmd_patterns = [
                    r"[;&|`]",
                    r"\$\(",
                    r"\.\.\/",
                    r"\/etc\/passwd",
                    r"\/bin\/",
                    r"cmd\.exe"
                ]
                
                import re
                
                # Check SQL injection
                for pattern in sql_patterns:
                    if re.search(pattern, input_data, re.IGNORECASE):
                        violations.append("sql_injection_attempt")
                        break
                
                # Check XSS
                for pattern in xss_patterns:
                    if re.search(pattern, input_data, re.IGNORECASE):
                        violations.append("xss_attempt")
                        break
                
                # Check command injection
                for pattern in cmd_patterns:
                    if re.search(pattern, input_data, re.IGNORECASE):
                        violations.append("command_injection_attempt")
                        break
                
                # Check for excessive length (potential DoS)
                if len(input_data) > 10000:  # 10KB limit
                    violations.append("excessive_input_length")
                
                # Check for binary content in text fields
                try:
                    input_data.encode('utf-8')
                except UnicodeEncodeError:
                    violations.append("invalid_encoding")
            
            elif isinstance(input_data, dict):
                # Recursive validation for nested structures
                for key, value in input_data.items():
                    is_valid, sub_violations = await self.validate_input_security(value, input_type)
                    violations.extend(sub_violations)
            
            elif isinstance(input_data, list):
                # Validate list items
                for item in input_data:
                    is_valid, sub_violations = await self.validate_input_security(item, input_type)
                    violations.extend(sub_violations)
            
            # Log security violations
            if violations:
                await self.log_security_event(
                    SecurityEvent(
                        event_type=SecurityEventType.MALICIOUS_INPUT,
                        threat_level=ThreatLevel.HIGH,
                        user_id=None,
                        ip_address="",
                        user_agent="",
                        timestamp=datetime.now(timezone.utc),
                        details={"violations": violations, "input_type": input_type}
                    )
                )
            
            return len(violations) == 0, violations
            
        except Exception as e:
            self.logger.error(f"❌ Error in input validation: {e}")
            return False, ["validation_error"]

    async def log_security_event(self, event: SecurityEvent) -> None:
        """Log security events with alerting"""
        try:
            async with get_async_session() as session:
                await session.execute(
                    text("""
                        INSERT INTO security_events 
                        (event_type, threat_level, user_id, ip_address, user_agent, timestamp, details, resolved)
                        VALUES (:event_type, :threat_level, :user_id, :ip_address, :user_agent, :timestamp, :details, :resolved)
                    """),
                    {
                        "event_type": event.event_type.value,
                        "threat_level": event.threat_level.value,
                        "user_id": event.user_id,
                        "ip_address": event.ip_address,
                        "user_agent": event.user_agent,
                        "timestamp": event.timestamp,
                        "details": json.dumps(event.details),
                        "resolved": event.resolved
                    }
                )
                await session.commit()
            
            # Real-time alerting for high-threat events
            if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                await self._send_security_alert(event)
            
            self.logger.warning(
                f"🔒 Security Event: {event.event_type.value} | "
                f"Threat: {event.threat_level.value} | "
                f"User: {event.user_id or 'Anonymous'} | "
                f"IP: {event.ip_address}"
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error logging security event: {e}")

    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Get real-time security dashboard data"""
        try:
            async with get_async_session() as session:
                # Recent security events
                events_query = await session.execute(
                    text("""
                        SELECT event_type, threat_level, COUNT(*) as count
                        FROM security_events 
                        WHERE timestamp >= NOW() - INTERVAL '24 hours'
                        GROUP BY event_type, threat_level
                        ORDER BY count DESC
                    """)
                )
                recent_events = [
                    {"type": row[0], "level": row[1], "count": row[2]}
                    for row in events_query.fetchall()
                ]
                
                # Threat statistics
                threat_stats = await session.execute(
                    text("""
                        SELECT 
                            threat_level,
                            COUNT(*) as total_events,
                            COUNT(CASE WHEN resolved = false THEN 1 END) as unresolved_events
                        FROM security_events 
                        WHERE timestamp >= NOW() - INTERVAL '7 days'
                        GROUP BY threat_level
                    """)
                )
                threat_statistics = {
                    row[0]: {"total": row[1], "unresolved": row[2]}
                    for row in threat_stats.fetchall()
                }
                
                # Top suspicious IPs
                suspicious_ips_query = await session.execute(
                    text("""
                        SELECT ip_address, COUNT(*) as incident_count
                        FROM security_events 
                        WHERE timestamp >= NOW() - INTERVAL '24 hours'
                        AND threat_level IN ('high', 'critical')
                        GROUP BY ip_address
                        ORDER BY incident_count DESC
                        LIMIT 10
                    """)
                )
                top_suspicious_ips = [
                    {"ip": row[0], "incidents": row[1]}
                    for row in suspicious_ips_query.fetchall()
                ]
                
                return {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "recent_events": recent_events,
                    "threat_statistics": threat_statistics,
                    "top_suspicious_ips": top_suspicious_ips,
                    "total_suspicious_ips": len(self.suspicious_ips),
                    "mfa_adoption_rate": await self._get_mfa_adoption_rate(session)
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error getting security dashboard: {e}")
            return {"error": "Dashboard unavailable"}

    # Helper methods
    async def _check_rate_limiting(self, ip_address: str, user_id: Optional[str]) -> bool:
        """Check if rate limits are exceeded"""
        # Simplified rate limiting check
        key = f"rate_limit:{ip_address}:{user_id or 'anonymous'}"
        current_time = time.time()
        
        # In production, use Redis for proper rate limiting
        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = []
        
        # Clean old attempts (older than 1 hour)
        self.failed_attempts[ip_address] = [
            timestamp for timestamp in self.failed_attempts[ip_address]
            if current_time - timestamp < 3600
        ]
        
        # Check if more than 10 attempts in last hour
        return len(self.failed_attempts[ip_address]) > 10

    async def _check_geolocation_anomaly(self, ip_address: str, user_id: Optional[str]) -> bool:
        """Check for geolocation anomalies"""
        # Simplified geolocation check
        # In production, integrate with IP geolocation service
        return False

    def _analyze_user_agent(self, user_agent: str) -> bool:
        """Analyze user agent for suspicious patterns"""
        suspicious_patterns = [
            "bot", "crawler", "spider", "scraper",
            "sqlmap", "nikto", "nmap", "burp"
        ]
        return any(pattern in user_agent.lower() for pattern in suspicious_patterns)

    async def _analyze_session_behavior(self, request: Request, user_id: Optional[str]) -> bool:
        """Analyze session behavior for anomalies"""
        # Simplified behavior analysis
        # In production, implement ML-based anomaly detection
        return False

    def _calculate_threat_level(self, indicators: List[str]) -> ThreatLevel:
        """Calculate threat level based on indicators"""
        critical_indicators = ["sql_injection_attempt", "command_injection_attempt"]
        high_indicators = ["xss_attempt", "known_malicious_ip"]
        medium_indicators = ["rate_limit_exceeded", "suspicious_user_agent"]
        
        if any(indicator in critical_indicators for indicator in indicators):
            return ThreatLevel.CRITICAL
        elif any(indicator in high_indicators for indicator in indicators):
            return ThreatLevel.HIGH
        elif any(indicator in medium_indicators for indicator in indicators):
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW

    async def _auto_response(self, ip_address: str, user_id: Optional[str], threat_level: ThreatLevel) -> None:
        """Automated security response"""
        try:
            if threat_level == ThreatLevel.CRITICAL:
                # Block IP immediately
                self.suspicious_ips.add(ip_address)
                
                if user_id:
                    # Disable user account temporarily
                    async with get_async_session() as session:
                        await session.execute(
                            text("UPDATE users SET is_active = false WHERE user_id = :user_id"),
                            {"user_id": user_id}
                        )
                        await session.commit()
                
                self.logger.critical(f"🚨 CRITICAL THREAT - Auto-blocked IP: {ip_address}, User: {user_id}")
                
            elif threat_level == ThreatLevel.HIGH:
                # Add to suspicious list
                self.suspicious_ips.add(ip_address)
                self.logger.warning(f"⚠️ HIGH THREAT - Added to watchlist: {ip_address}")
                
        except Exception as e:
            self.logger.error(f"❌ Error in auto-response: {e}")

    async def _send_security_alert(self, event: SecurityEvent) -> None:
        """Send security alerts to administrators"""
        try:
            # In production, integrate with alerting systems (PagerDuty, Slack, etc.)
            alert_message = (
                f"🔒 SECURITY ALERT\n"
                f"Type: {event.event_type.value}\n"
                f"Threat Level: {event.threat_level.value}\n"
                f"User: {event.user_id or 'Unknown'}\n"
                f"IP: {event.ip_address}\n"
                f"Time: {event.timestamp}\n"
                f"Details: {json.dumps(event.details, indent=2)}"
            )
            
            self.logger.critical(alert_message)
            
            # Store alert for dashboard
            async with get_async_session() as session:
                await session.execute(
                    text("""
                        INSERT INTO security_alerts (alert_message, threat_level, timestamp, resolved)
                        VALUES (:message, :level, :timestamp, :resolved)
                    """),
                    {
                        "message": alert_message,
                        "level": event.threat_level.value,
                        "timestamp": event.timestamp,
                        "resolved": False
                    }
                )
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"❌ Error sending security alert: {e}")

    async def _get_mfa_adoption_rate(self, session: AsyncSession) -> float:
        """Get MFA adoption rate"""
        try:
            total_users_query = await session.execute(
                text("SELECT COUNT(*) FROM users WHERE is_active = true")
            )
            total_users = total_users_query.scalar() or 0
            
            mfa_users_query = await session.execute(
                text("SELECT COUNT(*) FROM user_mfa WHERE enabled = true")
            )
            mfa_users = mfa_users_query.scalar() or 0
            
            return (mfa_users / total_users * 100) if total_users > 0 else 0.0
            
        except Exception:
            return 0.0


# Global security manager instance
security_manager = AdvancedSecurityManager()


# Utility functions for easy access
async def setup_mfa(user_id: str) -> MFASetup:
    """Setup MFA for user"""
    return await security_manager.setup_mfa_for_user(user_id)


async def verify_mfa(user_id: str, token: str, is_backup: bool = False) -> bool:
    """Verify MFA token"""
    return await security_manager.verify_mfa_token(user_id, token, is_backup)


async def detect_threats(request: Request, user_id: Optional[str] = None) -> bool:
    """Detect security threats"""
    return await security_manager.detect_suspicious_activity(request, user_id)


async def validate_input(input_data: Any, input_type: str = "general") -> Tuple[bool, List[str]]:
    """Validate input for security"""
    return await security_manager.validate_input_security(input_data, input_type)


async def get_security_status() -> Dict[str, Any]:
    """Get security dashboard status"""
    return await security_manager.get_security_dashboard() 