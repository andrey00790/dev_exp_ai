"""
Input Validation module for AI Assistant MVP

Provides comprehensive input validation and sanitization to prevent
SQL injection, XSS attacks, and other security vulnerabilities.
"""

import re
import html
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from fastapi import HTTPException, status
from pydantic import BaseModel, field_validator, Field

logger = logging.getLogger(__name__)

# Dangerous patterns that should be blocked
DANGEROUS_SQL_PATTERNS = [
    r"(?i)\b(drop|delete|insert|update|create|alter|exec|execute)\b",
    r"(?i)\b(union|select|from|where|having|group by|order by)\b",
    r"(?i)\b(script|javascript|vbscript|onload|onerror|onclick)\b",
    r"[';\"\\-][\s]*(\-\-|#|\/\*)",
    r"(?i)\b(xp_|sp_|sys\.)",
    r"(?i)\b(information_schema|pg_|mysql\.)",
    r"[';\"]\s*(or|and)\s*['\"]?\w*['\"]?\s*=\s*['\"]?\w*['\"]?",  # OR/AND injection patterns
    r";\s*(drop|delete|insert|update)",  # Statement chaining with semicolon
    r"'\s*(or|and)\s*'\w*'\s*=\s*'\w*'",  # Classic OR injection
]

DANGEROUS_XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"vbscript:",
    r"onload\s*=",
    r"onerror\s*=",
    r"onclick\s*=",
    r"onmouseover\s*=",
    r"onfocus\s*=",
    r"onblur\s*=",
    r"<iframe[^>]*>.*?</iframe>",
    r"<object[^>]*>.*?</object>",
    r"<embed[^>]*>.*?</embed>",
]

DANGEROUS_COMMAND_PATTERNS = [
    r"(?i)\b(rm|del|format|fdisk|dd|mkfs)\b",
    r"(?i)\b(sudo|su|chmod|chown)\b", 
    r"(?i)\b(wget|curl|nc|netcat)\b",
    r"(?i)\b(python|perl|ruby|bash|sh|cmd|powershell)\b",
    r"[;&|`$()]",
]

class SecurityValidationError(Exception):
    """Custom exception for security validation failures"""
    pass

def validate_input(value: str, field_name: str = "input") -> str:
    """
    Comprehensive input validation
    
    Args:
        value: Input string to validate
        field_name: Name of the field being validated
        
    Returns:
        Validated and sanitized string
        
    Raises:
        HTTPException: If dangerous patterns detected
    """
    if not isinstance(value, str):
        value = str(value)
    
    # Check for dangerous SQL patterns
    for pattern in DANGEROUS_SQL_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE | re.MULTILINE):
            logger.warning(f"SQL injection attempt detected in {field_name}: {pattern}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid input detected",
                    "field": field_name,
                    "reason": "Potentially dangerous SQL pattern",
                    "code": "SQL_INJECTION_BLOCKED"
                }
            )
    
    # Check for XSS patterns
    for pattern in DANGEROUS_XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE | re.MULTILINE):
            logger.warning(f"XSS attempt detected in {field_name}: {pattern}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid input detected",
                    "field": field_name,
                    "reason": "Potentially dangerous script content",
                    "code": "XSS_BLOCKED"
                }
            )
    
    # Check for command injection patterns
    for pattern in DANGEROUS_COMMAND_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            logger.warning(f"Command injection attempt detected in {field_name}: {pattern}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid input detected",
                    "field": field_name,
                    "reason": "Potentially dangerous command pattern",
                    "code": "COMMAND_INJECTION_BLOCKED"
                }
            )
    
    return value

def sanitize_string(value: str, max_length: int = 10000) -> str:
    """
    Sanitize string input
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        value = str(value)
    
    # Limit length
    if len(value) > max_length:
        value = value[:max_length]
        logger.info(f"String truncated to {max_length} characters")
    
    # HTML escape
    value = html.escape(value)
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Remove excessive whitespace
    value = re.sub(r'\s+', ' ', value).strip()
    
    return value

def validate_url(url: str) -> str:
    """
    Validate URL format and security
    
    Args:
        url: URL to validate
        
    Returns:
        Validated URL
        
    Raises:
        HTTPException: If URL is invalid or dangerous
    """
    try:
        parsed = urlparse(url)
        
        # Check scheme
        if parsed.scheme not in ['http', 'https']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL scheme. Only HTTP and HTTPS allowed."
            )
        
        # Check for localhost/internal IPs (basic check)
        if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
            logger.warning(f"Blocked internal URL access: {url}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Access to internal URLs is not allowed."
            )
        
        return url
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL format."
        )

def validate_email(email: str) -> str:
    """
    Validate email format
    
    Args:
        email: Email address to validate
        
    Returns:
        Validated email
        
    Raises:
        HTTPException: If email format is invalid
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format."
        )
    
    return email.lower()

def validate_user_id(user_id: str) -> str:
    """
    Validate user ID format
    
    Args:
        user_id: User ID to validate
        
    Returns:
        Validated user ID
        
    Raises:
        HTTPException: If user ID format is invalid
    """
    # Allow alphanumeric, underscore, hyphen, dot
    user_id_pattern = r'^[a-zA-Z0-9._-]+$'
    
    if not re.match(user_id_pattern, user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format. Only alphanumeric, underscore, hyphen, and dot allowed."
        )
    
    if len(user_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID too long. Maximum 100 characters."
        )
    
    return user_id

def validate_file_content(content: str, max_size: int = 1024 * 1024) -> str:
    """
    Validate file content for security
    
    Args:
        content: File content to validate
        max_size: Maximum file size in bytes
        
    Returns:
        Validated content
        
    Raises:
        HTTPException: If content is dangerous
    """
    if len(content.encode('utf-8')) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {max_size} bytes."
        )
    
    # Check for binary content (simplified check)
    try:
        content.encode('utf-8')
    except UnicodeEncodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file content. Only UTF-8 text files allowed."
        )
    
    # Validate content for dangerous patterns
    validate_input(content, "file_content")
    
    return content

# Pydantic validators for common use cases
class SecureRFCRequest(BaseModel):
    """Secure RFC generation request model"""
    task_type: str = Field(..., max_length=50)
    initial_request: str = Field(..., max_length=5000)
    context: Optional[str] = Field(None, max_length=10000)
    
    @field_validator('task_type', 'initial_request', 'context')
    def validate_text_fields(cls, v):
        if v is not None:
            return validate_input(v)
        return v

class SecureSearchRequest(BaseModel):
    """Secure search request model"""
    query: str = Field(..., min_length=1, max_length=1000)
    limit: Optional[int] = Field(10, ge=1, le=100)
    
    @field_validator('query')
    def validate_query(cls, v):
        return validate_input(v, "search_query")

class SecureDocumentationRequest(BaseModel):
    """Secure documentation generation request model"""
    code: str = Field(..., max_length=100000)
    language: Optional[str] = Field(None, max_length=50)
    doc_type: Optional[str] = Field("readme", max_length=50)
    
    @field_validator('code')
    def validate_code(cls, v):
        return validate_file_content(v)
    
    @field_validator('language', 'doc_type')
    def validate_string_fields(cls, v):
        if v is not None:
            return validate_input(v)
        return v

class SecureUserCredentials(BaseModel):
    """Secure user credentials model"""
    user_id: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('user_id')
    def validate_user_id_field(cls, v):
        return validate_user_id(v)
    
    @field_validator('password')
    def validate_password(cls, v):
        # Basic password validation
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

def create_validation_summary() -> Dict[str, Any]:
    """
    Create summary of validation rules
    
    Returns:
        Dictionary with validation information
    """
    return {
        "validation_rules": {
            "sql_injection": f"{len(DANGEROUS_SQL_PATTERNS)} patterns blocked",
            "xss_protection": f"{len(DANGEROUS_XSS_PATTERNS)} patterns blocked",
            "command_injection": f"{len(DANGEROUS_COMMAND_PATTERNS)} patterns blocked",
            "max_input_length": "10,000 characters",
            "max_file_size": "1 MB",
            "allowed_url_schemes": ["http", "https"],
            "user_id_format": "alphanumeric, underscore, hyphen, dot"
        },
        "security_features": [
            "HTML escaping",
            "Length limiting",
            "Pattern matching",
            "URL validation",
            "Email validation",
            "File content validation"
        ],
        "status": "Input validation active"
    } 