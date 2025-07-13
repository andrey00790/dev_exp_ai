"""
Auth Domain Module for Frontend

Domain entities and utilities for authentication.
"""

from .entities import (
    User,
    Role,
    Permission,
    UserPreferences,
    AuthSession,
    UserStatus,
    RoleType,
    hasPermission,
    hasRole,
    isUserActive,
    isUserAdmin,
    getUserPermissions,
    getUserRoleNames,
    validateEmail,
    validatePassword,
    validateUserName,
    createUser,
    createRole,
    createPermission,
)

__all__ = [
    # Entities
    "User",
    "Role",
    "Permission",
    "UserPreferences",
    "AuthSession",
    
    # Enums
    "UserStatus",
    "RoleType",
    
    # Utility functions
    "hasPermission",
    "hasRole",
    "isUserActive",
    "isUserAdmin",
    "getUserPermissions",
    "getUserRoleNames",
    
    # Validation functions
    "validateEmail",
    "validatePassword",
    "validateUserName",
    
    # Factory functions
    "createUser",
    "createRole",
    "createPermission",
] 