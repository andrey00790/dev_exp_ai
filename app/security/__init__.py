"""
Security module for AI Assistant MVP
Enhanced security features with rate limiting, JWT, CORS, and input validation
"""

from .auth import (
    create_access_token,
    verify_token,
    get_current_user,
    User,
    TokenData,
    UserLogin,
    Token
)

from .rate_limiting import (
    RateLimitMiddleware,
    RateLimitConfig,
    get_rate_limit_status,
    reset_rate_limit,
    rate_limit_health_check
)

from .input_validation import (
    SecureTextField,
    SecureEmailField,
    SecureUrlField,
    UserRegistrationInput,
    DocumentUploadInput,
    SearchQueryInput,
    AIRequestInput,
    validate_request_body,
    SecurityValidationError
)

from .cors_middleware import (
    SecurityCORSMiddleware,
    CSRFProtectionMiddleware,
    EnhancedCORSConfig,
    generate_cors_config,
    validate_cors_configuration
)

# Try to import enhanced JWT if available
try:
    from .jwt_enhanced import (
        TokenPair,
        LoginRequest,
        RefreshRequest,
        authenticate_user,
        create_token_pair,
        blacklist_token,
        is_token_blacklisted
    )
    JWT_ENHANCED_AVAILABLE = True
except ImportError:
    JWT_ENHANCED_AVAILABLE = False

__all__ = [
    # Core auth
    "create_access_token",
    "verify_token", 
    "get_current_user",
    "User",
    "TokenData",
    "UserLogin",
    "Token",
    
    # Rate limiting
    "RateLimitMiddleware",
    "RateLimitConfig",
    "get_rate_limit_status",
    "reset_rate_limit",
    "rate_limit_health_check",
    
    # Input validation
    "SecureTextField",
    "SecureEmailField", 
    "SecureUrlField",
    "UserRegistrationInput",
    "DocumentUploadInput",
    "SearchQueryInput", 
    "AIRequestInput",
    "validate_request_body",
    "SecurityValidationError",
    
    # CORS & CSRF
    "SecurityCORSMiddleware",
    "CSRFProtectionMiddleware",
    "EnhancedCORSConfig",
    "generate_cors_config",
    "validate_cors_configuration",
    
    # Enhanced JWT (if available)
    "JWT_ENHANCED_AVAILABLE"
]

# Add enhanced JWT exports if available
if JWT_ENHANCED_AVAILABLE:
    __all__.extend([
        "TokenPair",
        "LoginRequest", 
        "RefreshRequest",
        "authenticate_user",
        "create_token_pair",
        "blacklist_token",
        "is_token_blacklisted"
    ])
