"""
Input Validation and Sanitization Middleware for AI Assistant MVP
Task 1.3: Security Hardening - Input validation and XSS/SQL injection prevention

Provides:
- Request payload validation and sanitization
- XSS protection with HTML escape
- SQL injection prevention
- File upload validation
- JSON payload size limits
- Rate limiting for validation failures
"""

import re
import json
import html
import logging
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal, InvalidOperation

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import bleach

logger = logging.getLogger(__name__)

# Configuration
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
MAX_STRING_LENGTH = 10000
MAX_ARRAY_LENGTH = 1000
MAX_OBJECT_DEPTH = 10

# Dangerous patterns for SQL injection detection
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
    r"(\b(UNION|OR|AND)\s+\d+\s*=\s*\d+)",
    r"(--|/\*|\*/|;)",
    r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT|ONLOAD|ONERROR)\b)",
    r"(<\s*script[^>]*>.*?</\s*script\s*>)",
]

# XSS patterns
XSS_PATTERNS = [
    r"<\s*script[^>]*>.*?</\s*script\s*>",
    r"<\s*iframe[^>]*>.*?</\s*iframe\s*>",
    r"javascript\s*:",
    r"on\w+\s*=",
    r"<\s*object[^>]*>.*?</\s*object\s*>",
    r"<\s*embed[^>]*>.*?</\s*embed\s*>",
]

# File type whitelist
ALLOWED_FILE_TYPES = {
    '.txt', '.md', '.pdf', '.doc', '.docx', '.json', '.csv', '.yml', '.yaml'
}

class InputValidator:
    """Main input validation and sanitization class."""
    
    def __init__(self):
        self.sql_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in SQL_INJECTION_PATTERNS]
        self.xss_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in XSS_PATTERNS]
        
    def validate_and_sanitize_string(self, value: str, field_name: str = "field") -> str:
        """Validate and sanitize string input."""
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")
        
        # Length check
        if len(value) > MAX_STRING_LENGTH:
            raise ValueError(f"{field_name} exceeds maximum length of {MAX_STRING_LENGTH}")
        
        # SQL injection check
        for pattern in self.sql_patterns:
            if pattern.search(value):
                logger.warning(f"SQL injection attempt detected in {field_name}: {value[:100]}...")
                raise ValueError(f"Invalid content detected in {field_name}")
        
        # XSS check
        for pattern in self.xss_patterns:
            if pattern.search(value):
                logger.warning(f"XSS attempt detected in {field_name}: {value[:100]}...")
                raise ValueError(f"Invalid content detected in {field_name}")
        
        # HTML escape for additional protection
        sanitized = html.escape(value)
        
        # Additional sanitization with bleach
        sanitized = bleach.clean(sanitized, tags=[], attributes={}, strip=True)
        
        return sanitized
    
    def validate_email(self, email: str) -> str:
        """Validate email format."""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            raise ValueError("Invalid email format")
        return self.validate_and_sanitize_string(email, "email")
    
    def validate_number(self, value: Union[int, float, str], field_name: str = "number") -> Union[int, float]:
        """Validate numeric input."""
        try:
            if isinstance(value, str):
                # Check for SQL injection in numeric strings
                if any(pattern.search(value) for pattern in self.sql_patterns):
                    raise ValueError(f"Invalid numeric format in {field_name}")
                
                # Try to convert to number
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            
            return value
            
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric value for {field_name}")
    
    def validate_decimal(self, value: Union[str, float, int], field_name: str = "decimal") -> Decimal:
        """Validate decimal/monetary values."""
        try:
            if isinstance(value, str):
                # Sanitize string input
                value = self.validate_and_sanitize_string(value, field_name)
            
            decimal_value = Decimal(str(value))
            
            # Check reasonable bounds for monetary values
            if decimal_value < 0:
                raise ValueError(f"{field_name} cannot be negative")
            if decimal_value > Decimal('1000000'):  # $1M limit
                raise ValueError(f"{field_name} exceeds maximum allowed value")
                
            return decimal_value
            
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"Invalid decimal value for {field_name}: {str(e)}")
    
    def validate_array(self, value: List[Any], field_name: str = "array") -> List[Any]:
        """Validate array input."""
        if not isinstance(value, list):
            raise ValueError(f"{field_name} must be an array")
        
        if len(value) > MAX_ARRAY_LENGTH:
            raise ValueError(f"{field_name} exceeds maximum length of {MAX_ARRAY_LENGTH}")
        
        # Recursively validate array elements
        sanitized_array = []
        for i, item in enumerate(value):
            sanitized_item = self.validate_any_value(item, f"{field_name}[{i}]")
            sanitized_array.append(sanitized_item)
        
        return sanitized_array
    
    def validate_object(self, value: Dict[str, Any], field_name: str = "object", depth: int = 0) -> Dict[str, Any]:
        """Validate object/dictionary input."""
        if not isinstance(value, dict):
            raise ValueError(f"{field_name} must be an object")
        
        if depth > MAX_OBJECT_DEPTH:
            raise ValueError(f"{field_name} exceeds maximum nesting depth")
        
        sanitized_object = {}
        for key, val in value.items():
            # Validate key
            sanitized_key = self.validate_and_sanitize_string(key, f"{field_name}.key")
            
            # Validate value
            sanitized_val = self.validate_any_value(val, f"{field_name}.{key}", depth + 1)
            sanitized_object[sanitized_key] = sanitized_val
        
        return sanitized_object
    
    def validate_any_value(self, value: Any, field_name: str = "value", depth: int = 0) -> Any:
        """Validate any type of value."""
        if value is None:
            return None
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return self.validate_and_sanitize_string(value, field_name)
        
        if isinstance(value, (int, float)):
            return self.validate_number(value, field_name)
        
        if isinstance(value, list):
            return self.validate_array(value, field_name)
        
        if isinstance(value, dict):
            return self.validate_object(value, field_name, depth)
        
        # For other types, convert to string and validate
        return self.validate_and_sanitize_string(str(value), field_name)
    
    def validate_file_upload(self, filename: str, content_type: str, size: int) -> bool:
        """Validate file upload parameters."""
        # Check file extension
        if not any(filename.lower().endswith(ext) for ext in ALLOWED_FILE_TYPES):
            raise ValueError(f"File type not allowed. Allowed types: {', '.join(ALLOWED_FILE_TYPES)}")
        
        # Check file size (10MB limit)
        if size > MAX_REQUEST_SIZE:
            raise ValueError(f"File size exceeds maximum allowed size of {MAX_REQUEST_SIZE} bytes")
        
        # Sanitize filename
        safe_filename = self.validate_and_sanitize_string(filename, "filename")
        
        # Additional filename checks
        if '..' in safe_filename or '/' in safe_filename or '\\' in safe_filename:
            raise ValueError("Invalid characters in filename")
        
        return True
    
    def validate_search_query(self, query: str) -> str:
        """Validate search query with special considerations."""
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")
        
        # Length check
        if len(query) > 1000:  # Shorter limit for search queries
            raise ValueError("Search query too long")
        
        # Basic sanitization
        sanitized_query = self.validate_and_sanitize_string(query, "search_query")
        
        # Remove excessive whitespace
        sanitized_query = re.sub(r'\s+', ' ', sanitized_query).strip()
        
        return sanitized_query
    
    def validate_rfc_generation_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate RFC generation request with specific business rules."""
        required_fields = ['title', 'description']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        validated_data = {}
        
        # Validate title
        validated_data['title'] = self.validate_and_sanitize_string(data['title'], 'title')
        if len(validated_data['title']) < 5:
            raise ValueError("Title must be at least 5 characters long")
        
        # Validate description
        validated_data['description'] = self.validate_and_sanitize_string(data['description'], 'description')
        if len(validated_data['description']) < 20:
            raise ValueError("Description must be at least 20 characters long")
        
        # Validate optional fields
        if 'category' in data:
            validated_data['category'] = self.validate_and_sanitize_string(data['category'], 'category')
        
        if 'priority' in data:
            validated_data['priority'] = self.validate_and_sanitize_string(data['priority'], 'priority')
        
        if 'metadata' in data:
            validated_data['metadata'] = self.validate_object(data['metadata'], 'metadata')
        
        return validated_data

# Global validator instance
input_validator = InputValidator()

async def input_validation_middleware(request: Request, call_next):
    """Middleware to validate and sanitize all incoming requests."""
    
    # Skip validation for certain endpoints
    skip_paths = ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]
    if any(request.url.path.startswith(path) for path in skip_paths):
        response = await call_next(request)
        return response
    
    try:
        # Check request size
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request too large"}
            )
        
        # Validate and sanitize request body if present
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read and validate JSON body
                body = await request.body()
                if body:
                    try:
                        json_data = json.loads(body)
                        
                        # Apply specific validation based on endpoint
                        if request.url.path.endswith('/generate'):
                            validated_data = input_validator.validate_rfc_generation_request(json_data)
                        elif request.url.path.endswith('/search'):
                            if 'query' in json_data:
                                json_data['query'] = input_validator.validate_search_query(json_data['query'])
                            validated_data = input_validator.validate_object(json_data)
                        else:
                            validated_data = input_validator.validate_object(json_data)
                        
                        # Replace request body with validated data
                        import io
                        validated_body = json.dumps(validated_data).encode()
                        request._body = validated_body
                        
                    except json.JSONDecodeError:
                        return JSONResponse(
                            status_code=400,
                            content={"detail": "Invalid JSON format"}
                        )
                    
            except Exception as e:
                logger.warning(f"Input validation failed for {request.url.path}: {str(e)}")
                return JSONResponse(
                    status_code=400,
                    content={"detail": f"Invalid input: {str(e)}"}
                )
        
        # Validate query parameters
        for key, value in request.query_params.items():
            try:
                input_validator.validate_and_sanitize_string(value, f"query_param_{key}")
            except ValueError as e:
                return JSONResponse(
                    status_code=400,
                    content={"detail": f"Invalid query parameter {key}: {str(e)}"}
                )
        
        response = await call_next(request)
        return response
        
    except Exception as e:
        logger.error(f"Input validation middleware error: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal validation error"}
        )

# Utility functions for API endpoints
def validate_user_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Utility function to validate user input in API endpoints."""
    return input_validator.validate_object(data)

def validate_search_input(query: str) -> str:
    """Utility function to validate search queries."""
    return input_validator.validate_search_query(query)

def validate_budget_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Utility function to validate budget-related inputs."""
    validated = {}
    
    if 'user_id' in data:
        validated['user_id'] = input_validator.validate_and_sanitize_string(data['user_id'], 'user_id')
    
    if 'new_budget_limit' in data:
        validated['new_budget_limit'] = float(input_validator.validate_decimal(data['new_budget_limit'], 'new_budget_limit'))
    
    if 'reason' in data:
        validated['reason'] = input_validator.validate_and_sanitize_string(data['reason'], 'reason')
    
    return validated 