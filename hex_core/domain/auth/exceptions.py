"""
Auth Domain Exceptions

Domain-specific exceptions for authentication business logic.
Following hexagonal architecture principles.
"""


class AuthDomainError(Exception):
    """Base exception for authentication domain"""
    
    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__


class InvalidCredentialsError(AuthDomainError):
    """Raised when user credentials are invalid"""
    
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message, "INVALID_CREDENTIALS")


class UserNotFoundError(AuthDomainError):
    """Raised when user is not found"""
    
    def __init__(self, message: str = "User not found"):
        super().__init__(message, "USER_NOT_FOUND")


class UserAlreadyExistsError(AuthDomainError):
    """Raised when attempting to create user that already exists"""
    
    def __init__(self, message: str = "User already exists"):
        super().__init__(message, "USER_ALREADY_EXISTS")


class InactiveUserError(AuthDomainError):
    """Raised when user account is inactive"""
    
    def __init__(self, message: str = "User account is inactive"):
        super().__init__(message, "INACTIVE_USER")


class InvalidTokenError(AuthDomainError):
    """Raised when token is invalid or expired"""
    
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message, "INVALID_TOKEN")


class InsufficientPermissionsError(AuthDomainError):
    """Raised when user lacks required permissions"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "INSUFFICIENT_PERMISSIONS")


class RoleNotFoundError(AuthDomainError):
    """Raised when role is not found"""
    
    def __init__(self, message: str = "Role not found"):
        super().__init__(message, "ROLE_NOT_FOUND")


class PermissionNotFoundError(AuthDomainError):
    """Raised when permission is not found"""
    
    def __init__(self, message: str = "Permission not found"):
        super().__init__(message, "PERMISSION_NOT_FOUND")


class SessionExpiredError(AuthDomainError):
    """Raised when session has expired"""
    
    def __init__(self, message: str = "Session has expired"):
        super().__init__(message, "SESSION_EXPIRED")


class SessionInvalidError(AuthDomainError):
    """Raised when session is invalid"""
    
    def __init__(self, message: str = "Session is invalid"):
        super().__init__(message, "SESSION_INVALID") 