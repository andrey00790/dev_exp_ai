"""
Enhanced Input Validation для AI Assistant MVP
Защита от injection атак и malicious input
"""

import re
import logging
from typing import Any, Dict, List, Optional, Union, Type
from pydantic import BaseModel, Field, validator, ValidationError
from fastapi import HTTPException, status
import bleach
import html
from urllib.parse import urlparse
import ipaddress

logger = logging.getLogger(__name__)

# Security patterns
SUSPICIOUS_PATTERNS = [
    # SQL Injection patterns
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
    r"(--|;|\/\*|\*\/)",
    r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
    
    # XSS patterns
    r"(<script[^>]*>.*?</script>)",
    r"(javascript:|vbscript:|onload=|onerror=)",
    r"(<iframe|<object|<embed)",
    
    # Command injection patterns
    r"(\||;|&&|\$\(|\`)",
    r"(\b(rm|ls|cat|pwd|whoami|id|ps|kill)\b)",
    
    # Path traversal
    r"(\.\./|\.\.\\)",
    r"(/etc/passwd|/etc/shadow|/windows/system32)",
    
    # LDAP injection
    r"(\*|\(|\)|\||&)",
    
    # NoSQL injection
    r"(\$where|\$ne|\$gt|\$lt|\$in|\$nin)"
]

# Compile patterns for performance
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in SUSPICIOUS_PATTERNS]

class SecurityValidationError(HTTPException):
    """Custom exception for security validation failures"""
    
    def __init__(self, detail: str, field: str = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security validation failed: {detail}" + (f" (field: {field})" if field else "")
        )

def detect_malicious_patterns(text: str, field_name: str = "input") -> None:
    """Detect potentially malicious patterns in input text"""
    if not isinstance(text, str):
        return
    
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            logger.warning(f"⚠️ Suspicious pattern detected in {field_name}: {pattern.pattern}")
            raise SecurityValidationError(
                f"Potentially malicious content detected in {field_name}",
                field_name
            )

def sanitize_html(text: str, allowed_tags: List[str] = None) -> str:
    """Sanitize HTML content to prevent XSS"""
    if not isinstance(text, str):
        return text
    
    # Default safe tags
    if allowed_tags is None:
        allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br', 'span']
    
    # Clean HTML
    clean_text = bleach.clean(
        text,
        tags=allowed_tags,
        attributes={},
        strip=True
    )
    
    # Additional HTML entity encoding
    return html.escape(clean_text, quote=False)

def validate_email_format(email: str) -> str:
    """Enhanced email validation"""
    if not email:
        raise SecurityValidationError("Email cannot be empty", "email")
    
    # Basic format check
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise SecurityValidationError("Invalid email format", "email")
    
    # Check for suspicious patterns
    detect_malicious_patterns(email, "email")
    
    # Length check
    if len(email) > 254:  # RFC 5321 limit
        raise SecurityValidationError("Email too long", "email")
    
    return email.lower().strip()

def validate_url(url: str, allowed_schemes: List[str] = None) -> str:
    """Validate URL format and scheme"""
    if not url:
        raise SecurityValidationError("URL cannot be empty", "url")
    
    try:
        parsed = urlparse(url)
        
        # Check scheme
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']
        
        if parsed.scheme not in allowed_schemes:
            raise SecurityValidationError(
                f"URL scheme must be one of: {allowed_schemes}",
                "url"
            )
        
        # Check for malicious patterns
        detect_malicious_patterns(url, "url")
        
        return url.strip()
        
    except Exception as e:
        raise SecurityValidationError(f"Invalid URL format: {e}", "url")

def validate_ip_address(ip: str) -> str:
    """Validate IP address format"""
    if not ip:
        raise SecurityValidationError("IP address cannot be empty", "ip")
    
    try:
        # Try to parse as IPv4 or IPv6
        ipaddress.ip_address(ip)
        return ip.strip()
        
    except ValueError:
        raise SecurityValidationError("Invalid IP address format", "ip")

def validate_filename(filename: str) -> str:
    """Validate filename for security"""
    if not filename:
        raise SecurityValidationError("Filename cannot be empty", "filename")
    
    # Check for path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise SecurityValidationError("Filename contains invalid characters", "filename")
    
    # Check for malicious patterns
    detect_malicious_patterns(filename, "filename")
    
    # Length check
    if len(filename) > 255:
        raise SecurityValidationError("Filename too long", "filename")
    
    # Check for dangerous extensions
    dangerous_extensions = ['.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js']
    if any(filename.lower().endswith(ext) for ext in dangerous_extensions):
        raise SecurityValidationError("Dangerous file extension", "filename")
    
    return filename.strip()

class SecureBaseModel(BaseModel):
    """Base model with security validation"""
    
    class Config:
        # Validate assignment to catch changes after creation
        validate_assignment = True
        # Allow population by field name or alias
        allow_population_by_field_name = True
        # Use enum values
        use_enum_values = True

class SecureTextField(str):
    """Secure text field with automatic validation"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, value: Any, field: str = "text") -> str:
        if not isinstance(value, str):
            raise ValidationError("Value must be a string", cls)
        
        # Check for malicious patterns
        detect_malicious_patterns(value, field)
        
        # Sanitize HTML
        clean_value = sanitize_html(value)
        
        return clean_value

class SecureEmailField(str):
    """Secure email field with validation"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValidationError("Email must be a string", cls)
        
        return validate_email_format(value)

class SecureUrlField(str):
    """Secure URL field with validation"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValidationError("URL must be a string", cls)
        
        return validate_url(value)

# Enhanced Pydantic models for common inputs

class UserRegistrationInput(SecureBaseModel):
    """Secure user registration input"""
    email: SecureEmailField = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    name: SecureTextField = Field(..., min_length=1, max_length=100, description="User full name")
    phone: Optional[str] = Field(None, regex=r'^\+?[\d\s\-\(\)]{10,20}$', description="Phone number")
    
    @validator('password')
    def validate_password(cls, value):
        # Check password strength
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        if not re.search(r'[A-Z]', value):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', value):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', value):
            raise ValueError("Password must contain at least one digit")
        
        # Check for malicious patterns
        detect_malicious_patterns(value, "password")
        
        return value

class DocumentUploadInput(SecureBaseModel):
    """Secure document upload input"""
    title: SecureTextField = Field(..., min_length=1, max_length=200, description="Document title")
    description: Optional[SecureTextField] = Field(None, max_length=1000, description="Document description")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME content type")
    tags: Optional[List[SecureTextField]] = Field(None, description="Document tags")
    
    @validator('filename')
    def validate_filename_field(cls, value):
        return validate_filename(value)
    
    @validator('content_type')
    def validate_content_type(cls, value):
        # Allow only safe content types
        allowed_types = [
            'text/plain', 'text/html', 'text/markdown',
            'application/pdf', 'application/json',
            'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ]
        
        if value not in allowed_types:
            raise ValueError(f"Content type not allowed: {value}")
        
        return value
    
    @validator('tags')
    def validate_tags(cls, value):
        if value:
            # Limit number of tags
            if len(value) > 10:
                raise ValueError("Too many tags (max 10)")
            
            # Validate each tag
            for tag in value:
                if len(tag) > 50:
                    raise ValueError("Tag too long (max 50 characters)")
        
        return value

class SearchQueryInput(SecureBaseModel):
    """Secure search query input"""
    query: SecureTextField = Field(..., min_length=1, max_length=500, description="Search query")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Results limit")
    offset: Optional[int] = Field(0, ge=0, description="Results offset")
    search_type: Optional[str] = Field("semantic", regex=r'^(semantic|vector|hybrid|text)$', description="Search type")
    
    @validator('filters')
    def validate_filters(cls, value):
        if value:
            # Limit filter complexity
            if len(value) > 10:
                raise ValueError("Too many filters")
            
            # Validate filter values
            for key, val in value.items():
                if isinstance(val, str):
                    detect_malicious_patterns(val, f"filter.{key}")
        
        return value

class AIRequestInput(SecureBaseModel):
    """Secure AI request input"""
    prompt: SecureTextField = Field(..., min_length=1, max_length=4000, description="AI prompt")
    model: Optional[str] = Field("gpt-4", regex=r'^(gpt-3\.5-turbo|gpt-4|claude-3|llama-2)$', description="AI model")
    max_tokens: Optional[int] = Field(1000, ge=1, le=4000, description="Max response tokens")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Response creativity")
    context: Optional[List[str]] = Field(None, description="Additional context")
    
    @validator('context')
    def validate_context(cls, value):
        if value:
            # Limit context size
            if len(value) > 10:
                raise ValueError("Too much context provided")
            
            total_length = sum(len(item) for item in value)
            if total_length > 10000:
                raise ValueError("Context too long")
            
            # Validate each context item
            for item in value:
                detect_malicious_patterns(item, "context")
        
        return value

# Validation middleware function
async def validate_request_body(body: Dict[str, Any], model_class: Type[SecureBaseModel]) -> SecureBaseModel:
    """Validate request body against secure model"""
    try:
        return model_class(**body)
    except ValidationError as e:
        logger.warning(f"⚠️ Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Input validation failed: {e}"
        )
    except SecurityValidationError:
        # Re-raise security errors as-is
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal validation error"
        )

# Security headers validation
def validate_security_headers(headers: Dict[str, str]) -> Dict[str, Any]:
    """Validate security-related headers"""
    issues = []
    
    # Check for required security headers
    required_headers = [
        'X-Content-Type-Options',
        'X-Frame-Options', 
        'X-XSS-Protection'
    ]
    
    for header in required_headers:
        if header not in headers:
            issues.append(f"Missing security header: {header}")
    
    # Validate CSP header
    csp = headers.get('Content-Security-Policy')
    if not csp:
        issues.append("Missing Content-Security-Policy header")
    elif 'unsafe-eval' in csp or 'unsafe-inline' in csp:
        issues.append("CSP contains unsafe directives")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "headers_checked": len(headers)
    }
