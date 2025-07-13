"""
Auth Domain Module

Contains pure business logic for authentication and authorization.
Following hexagonal architecture principles - no external dependencies.
"""

from .entities import User, Role, Permission
from .value_objects import UserId, Email, Password, Token
from .services import AuthDomainService, PasswordService
from .exceptions import AuthDomainError, InvalidCredentialsError, UserNotFoundError

__all__ = [
    # Entities
    "User",
    "Role", 
    "Permission",
    
    # Value Objects
    "UserId",
    "Email",
    "Password",
    "Token",
    
    # Domain Services
    "AuthDomainService",
    "PasswordService",
    
    # Exceptions
    "AuthDomainError",
    "InvalidCredentialsError",
    "UserNotFoundError",
]
