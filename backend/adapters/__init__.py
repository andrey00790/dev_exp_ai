"""
Adapters Layer

Infrastructure adapters that implement domain ports.
These adapters connect the application to external systems.
"""

from .auth import (
    MockUserRepository,
    MockRoleRepository,
    MockPermissionRepository,
    MockSessionRepository,
    BcryptPasswordHasher,
    JWTTokenGenerator,
    SMTPEmailService,
    FastAPIEventPublisher,
    MockEmailService,
    MockEventPublisher,
)

__all__ = [
    # Auth adapters
    "MockUserRepository",
    "MockRoleRepository", 
    "MockPermissionRepository",
    "MockSessionRepository",
    "BcryptPasswordHasher",
    "JWTTokenGenerator",
    "SMTPEmailService",
    "FastAPIEventPublisher",
    "MockEmailService",
    "MockEventPublisher",
]
