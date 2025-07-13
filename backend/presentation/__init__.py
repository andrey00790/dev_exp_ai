"""
Presentation Layer

HTTP handlers and API routes for the application.
This layer handles external communication protocols.
"""

from .auth import router as auth_router

__all__ = ["auth_router"]
