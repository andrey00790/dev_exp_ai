"""
Auth Adapters Module

Infrastructure adapters for authentication domain.
Implements ports using external systems and libraries.
"""

from .repositories import (
    MockUserRepository,
    MockRoleRepository,
    MockPermissionRepository,
    MockSessionRepository
)

from .services import (
    BcryptPasswordHasher,
    JWTTokenGenerator,
    SMTPEmailService,
    FastAPIEventPublisher,
    MockEmailService,
    MockEventPublisher
)

__all__ = [
    # Repositories
    "MockUserRepository",
    "MockRoleRepository", 
    "MockPermissionRepository",
    "MockSessionRepository",
    
    # Services
    "BcryptPasswordHasher",
    "JWTTokenGenerator",
    "SMTPEmailService",
    "FastAPIEventPublisher",
    "MockEmailService",
    "MockEventPublisher",
] 