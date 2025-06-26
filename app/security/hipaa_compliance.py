"""
HIPAA Compliance Module for AI Assistant MVP
NFR-040: Healthcare Information Portability and Accountability Act Compliance

Provides:
- HIPAA-compliant data handling
- PHI (Protected Health Information) identification and protection
- Audit logging for healthcare data access
- Encryption and security controls for healthcare environments
- HIPAA-specific authentication and authorization
"""

import os
import logging
import hashlib
import uuid
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import re
import json

from fastapi import HTTPException, Request, Response
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)

class PHIDataType(Enum):
    """Types of Protected Health Information"""
    NAME = "name"
    SSN = "ssn"
    DATE_OF_BIRTH = "date_of_birth"
    PHONE = "phone"
    EMAIL = "email"
    ADDRESS = "address"
    MEDICAL_RECORD_NUMBER = "medical_record_number"
    ACCOUNT_NUMBER = "account_number"
    CERTIFICATE_NUMBER = "certificate_number"
    LICENSE_NUMBER = "license_number"
    DEVICE_IDENTIFIER = "device_identifier"
    BIOMETRIC_DATA = "biometric_data"
    PHOTO = "photo"
    IP_ADDRESS = "ip_address"

class HIPAAAccessLevel(Enum):
    """HIPAA access levels"""
    MINIMUM_NECESSARY = "minimum_necessary"
    AUTHORIZED_DISCLOSURE = "authorized_disclosure"
    TREATMENT = "treatment"
    PAYMENT = "payment"
    OPERATIONS = "operations"
    RESEARCH = "research"
    EMERGENCY = "emergency"

@dataclass
class PHIIdentification:
    """PHI identification result"""
    data_type: PHIDataType
    value: str
    confidence: float
    location: tuple
    suggested_redaction: str

@dataclass
class HIPAAAuditLog:
    """HIPAA audit log entry"""
    user_id: str
    action: str
    resource: str
    phi_accessed: List[PHIDataType]
    access_level: HIPAAAccessLevel
    timestamp: datetime
    ip_address: str
    user_agent: str
    justification: Optional[str]
    success: bool
    risk_level: str

class HIPAACompliance:
    """HIPAA Compliance Manager"""
    
    def __init__(self):
        self.encryption_key = self._get_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.phi_patterns = self._init_phi_patterns()
        self.audit_logs: List[HIPAAAuditLog] = []
        self.enabled = os.getenv("HIPAA_COMPLIANCE_ENABLED", "false").lower() == "true"
        
    def _get_encryption_key(self) -> bytes:
        """Generate or retrieve encryption key for PHI"""
        key_env = os.getenv("HIPAA_ENCRYPTION_KEY")
        if key_env:
            return base64.urlsafe_b64decode(key_env.encode())
        
        # Generate new key if not provided
        password = os.getenv("HIPAA_KEY_PASSWORD", "default_hipaa_password_change_in_production").encode()
        salt = os.getenv("HIPAA_KEY_SALT", "default_salt_change_in_production").encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def _init_phi_patterns(self) -> Dict[PHIDataType, List[re.Pattern]]:
        """Initialize PHI detection patterns"""
        return {
            PHIDataType.SSN: [
                re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
                re.compile(r'\b\d{9}\b'),
            ],
            PHIDataType.PHONE: [
                re.compile(r'\b\d{3}-\d{3}-\d{4}\b'),
                re.compile(r'\(\d{3}\)\s*\d{3}-\d{4}'),
                re.compile(r'\b\d{10}\b'),
            ],
            PHIDataType.EMAIL: [
                re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            ],
            PHIDataType.DATE_OF_BIRTH: [
                re.compile(r'\b\d{1,2}/\d{1,2}/\d{4}\b'),
                re.compile(r'\b\d{4}-\d{2}-\d{2}\b'),
                re.compile(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b'),
            ],
            PHIDataType.MEDICAL_RECORD_NUMBER: [
                re.compile(r'\bMRN[:\s]*(\d{6,10})\b', re.IGNORECASE),
                re.compile(r'\bMedical\s+Record[:\s]*(\d{6,10})\b', re.IGNORECASE),
            ],
            PHIDataType.IP_ADDRESS: [
                re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            ],
        }
    
    def identify_phi(self, text: str) -> List[PHIIdentification]:
        """Identify PHI in text"""
        if not self.enabled:
            return []
        
        identifications = []
        
        for phi_type, patterns in self.phi_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(text)
                for match in matches:
                    identification = PHIIdentification(
                        data_type=phi_type,
                        value=match.group(),
                        confidence=0.9,  # High confidence for regex matches
                        location=(match.start(), match.end()),
                        suggested_redaction=self._generate_redaction(phi_type, match.group())
                    )
                    identifications.append(identification)
        
        return identifications
    
    def _generate_redaction(self, phi_type: PHIDataType, value: str) -> str:
        """Generate redacted version of PHI"""
        if phi_type == PHIDataType.SSN:
            return "XXX-XX-" + value[-4:]
        elif phi_type == PHIDataType.PHONE:
            return "XXX-XXX-" + value[-4:]
        elif phi_type == PHIDataType.EMAIL:
            parts = value.split('@')
            if len(parts) == 2:
                return f"{parts[0][:2]}***@{parts[1]}"
        elif phi_type == PHIDataType.DATE_OF_BIRTH:
            return "XX/XX/XXXX"
        elif phi_type == PHIDataType.MEDICAL_RECORD_NUMBER:
            return "MRN: XXXXXX"
        elif phi_type == PHIDataType.IP_ADDRESS:
            parts = value.split('.')
            return f"{parts[0]}.{parts[1]}.XXX.XXX"
        
        # Default redaction
        return "X" * len(value)
    
    def redact_phi(self, text: str, preserve_format: bool = True) -> str:
        """Redact PHI from text"""
        if not self.enabled:
            return text
        
        identifications = self.identify_phi(text)
        redacted_text = text
        
        # Sort by location in reverse order to maintain positions
        identifications.sort(key=lambda x: x.location[0], reverse=True)
        
        for identification in identifications:
            start, end = identification.location
            if preserve_format:
                replacement = identification.suggested_redaction
            else:
                replacement = "[REDACTED]"
            
            redacted_text = redacted_text[:start] + replacement + redacted_text[end:]
        
        return redacted_text
    
    def encrypt_phi(self, data: str) -> str:
        """Encrypt PHI data"""
        if not self.enabled:
            return data
        
        encrypted_data = self.cipher_suite.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_phi(self, encrypted_data: str) -> str:
        """Decrypt PHI data"""
        if not self.enabled:
            return encrypted_data
        
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt PHI data: {e}")
            raise HTTPException(status_code=500, detail="Data decryption failed")
    
    def log_phi_access(
        self,
        user_id: str,
        action: str,
        resource: str,
        phi_types: List[PHIDataType],
        access_level: HIPAAAccessLevel,
        request: Request,
        success: bool = True,
        justification: Optional[str] = None
    ):
        """Log PHI access for audit purposes"""
        if not self.enabled:
            return
        
        audit_log = HIPAAAuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            phi_accessed=phi_types,
            access_level=access_level,
            timestamp=datetime.utcnow(),
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("User-Agent", "unknown"),
            justification=justification,
            success=success,
            risk_level=self._calculate_risk_level(phi_types, access_level)
        )
        
        self.audit_logs.append(audit_log)
        logger.info(f"HIPAA Audit: {audit_log}")
        
        # Store in persistent storage (implement as needed)
        self._store_audit_log(audit_log)
    
    def _calculate_risk_level(self, phi_types: List[PHIDataType], access_level: HIPAAAccessLevel) -> str:
        """Calculate risk level for audit logging"""
        high_risk_types = {
            PHIDataType.SSN, 
            PHIDataType.MEDICAL_RECORD_NUMBER, 
            PHIDataType.BIOMETRIC_DATA
        }
        
        if any(phi_type in high_risk_types for phi_type in phi_types):
            return "HIGH"
        elif access_level in {HIPAAAccessLevel.AUTHORIZED_DISCLOSURE, HIPAAAccessLevel.RESEARCH}:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _store_audit_log(self, audit_log: HIPAAAuditLog):
        """Store audit log in persistent storage"""
        # Implement database storage
        # For now, log to file
        log_data = {
            "user_id": audit_log.user_id,
            "action": audit_log.action,
            "resource": audit_log.resource,
            "phi_accessed": [phi.value for phi in audit_log.phi_accessed],
            "access_level": audit_log.access_level.value,
            "timestamp": audit_log.timestamp.isoformat(),
            "ip_address": audit_log.ip_address,
            "user_agent": audit_log.user_agent,
            "justification": audit_log.justification,
            "success": audit_log.success,
            "risk_level": audit_log.risk_level
        }
        
        # Log to secure audit file
        audit_file = os.getenv("HIPAA_AUDIT_LOG_FILE", "/var/log/hipaa_audit.log")
        try:
            with open(audit_file, "a") as f:
                f.write(json.dumps(log_data) + "\n")
        except Exception as e:
            logger.error(f"Failed to write HIPAA audit log: {e}")
    
    def validate_minimum_necessary(
        self, 
        requested_data: Set[str], 
        user_role: str, 
        purpose: str
    ) -> bool:
        """Validate minimum necessary standard"""
        if not self.enabled:
            return True
        
        # Define minimum necessary data by role and purpose
        minimum_necessary_rules = {
            ("doctor", "treatment"): {"name", "date_of_birth", "medical_record_number"},
            ("nurse", "treatment"): {"name", "medical_record_number"},
            ("admin", "billing"): {"name", "account_number", "insurance_info"},
            ("researcher", "research"): {"age_range", "condition", "treatment_outcome"},
        }
        
        allowed_data = minimum_necessary_rules.get((user_role, purpose), set())
        
        if not requested_data.issubset(allowed_data):
            logger.warning(f"Minimum necessary violation: User {user_role} requested {requested_data} for {purpose}")
            return False
        
        return True
    
    def generate_compliance_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate HIPAA compliance report"""
        if not self.enabled:
            return {"message": "HIPAA compliance not enabled"}
        
        relevant_logs = [
            log for log in self.audit_logs 
            if start_date <= log.timestamp <= end_date
        ]
        
        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_access_events": len(relevant_logs),
            "unique_users": len(set(log.user_id for log in relevant_logs)),
            "access_by_level": {},
            "risk_distribution": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "failed_access_attempts": len([log for log in relevant_logs if not log.success]),
            "phi_types_accessed": {},
            "recommendations": []
        }
        
        for log in relevant_logs:
            # Access level distribution
            level = log.access_level.value
            report["access_by_level"][level] = report["access_by_level"].get(level, 0) + 1
            
            # Risk distribution
            report["risk_distribution"][log.risk_level] += 1
            
            # PHI types accessed
            for phi_type in log.phi_accessed:
                type_name = phi_type.value
                report["phi_types_accessed"][type_name] = report["phi_types_accessed"].get(type_name, 0) + 1
        
        # Generate recommendations
        if report["risk_distribution"]["HIGH"] > 0:
            report["recommendations"].append("Review high-risk PHI access events")
        
        if report["failed_access_attempts"] > 10:
            report["recommendations"].append("Investigate failed access attempts pattern")
        
        return report

# Global HIPAA compliance instance
hipaa_compliance = HIPAACompliance()

def hipaa_middleware(request: Request, call_next):
    """HIPAA compliance middleware"""
    async def dispatch(request: Request, call_next):
        if not hipaa_compliance.enabled:
            return await call_next(request)
        
        # Add HIPAA-specific headers
        response = await call_next(request)
        response.headers["X-HIPAA-Compliant"] = "true"
        response.headers["X-PHI-Protection"] = "enabled"
        
        return response
    
    return dispatch(request, call_next)

def require_hipaa_justification(justification: str):
    """Decorator to require HIPAA justification for PHI access"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if hipaa_compliance.enabled and not justification:
                raise HTTPException(
                    status_code=400, 
                    detail="HIPAA justification required for PHI access"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator

def mask_phi_in_logs(text: str) -> str:
    """Mask PHI in log messages"""
    if not hipaa_compliance.enabled:
        return text
    
    return hipaa_compliance.redact_phi(text, preserve_format=True) 