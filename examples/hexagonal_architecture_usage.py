"""
Examples of using the new hexagonal architecture.

This file demonstrates how to use the new architecture with:
- Domain entities and value objects
- Application services with dependency injection
- Adapters for external dependencies
- Context7 state management
"""

import asyncio
from datetime import datetime
from typing import Optional

# Domain layer imports
from backend.domain.auth.entities import User, Role, Permission, UserStatus, RoleType
from backend.domain.auth.value_objects import UserId, Email, Password, Token
from backend.domain.auth.domain_services import AuthDomainService

# Application layer imports
from backend.application.auth.services import AuthApplicationService, RoleManagementService
from backend.application.auth.ports import UserRepositoryPort, RoleRepositoryPort

# Infrastructure layer imports
from backend.infrastructure.di_container import configure_container, inject, DIContext, DIContainer


# Example 1: Basic user registration and authentication
async def example_basic_auth():
    """Example of basic authentication flow using hexagonal architecture."""
    print("=== Example 1: Basic Authentication ===")
    
    # Configure DI container for development
    container = configure_container('development')
    
    # Get application service (automatically resolves dependencies)
    auth_service = container.get(AuthApplicationService)
    
    try:
        # Register a new user
        print("1. Registering new user...")
        user = await auth_service.register_user(
            email="john.doe@example.com",
            name="John Doe",
            password="SecurePassword123"
        )
        print(f"   User registered: {user.name} ({user.email.value})")
        
        # Authenticate user
        print("2. Authenticating user...")
        auth_user, session = await auth_service.authenticate_user(
            email="john.doe@example.com",
            password="SecurePassword123"
        )
        print(f"   Authentication successful: {auth_user.name}")
        print(f"   Session created: {session.id}")
        
        # Check user permissions
        print("3. Checking permissions...")
        has_permission = await auth_service.authorize_user(
            user_id=user.id.value,
            permission="read_profile"
        )
        print(f"   Has read_profile permission: {has_permission}")
        
    except Exception as e:
        print(f"   Error: {e}")


# Example 2: Role and permission management
async def example_role_management():
    """Example of role and permission management."""
    print("\n=== Example 2: Role Management ===")
    
    container = configure_container('development')
    role_service = container.get(RoleManagementService)
    auth_service = container.get(AuthApplicationService)
    
    try:
        # Create roles
        print("1. Creating roles...")
        admin_role = await role_service.create_role(
            name="admin",
            description="Administrator role with full access"
        )
        user_role = await role_service.create_role(
            name="user",
            description="Regular user role"
        )
        print(f"   Created roles: {admin_role.name}, {user_role.name}")
        
        # Create permissions
        print("2. Creating permissions...")
        read_perm = Permission(
            id="perm_read",
            name="read_users",
            description="Can read user data",
            resource="users",
            action="read"
        )
        write_perm = Permission(
            id="perm_write",
            name="write_users",
            description="Can write user data",
            resource="users",
            action="write"
        )
        
        # Add permissions to roles
        admin_role.add_permission(read_perm)
        admin_role.add_permission(write_perm)
        user_role.add_permission(read_perm)
        
        print(f"   Admin role permissions: {[p.name for p in admin_role.permissions]}")
        print(f"   User role permissions: {[p.name for p in user_role.permissions]}")
        
        # Assign role to user
        print("3. Assigning roles to user...")
        user = await auth_service.register_user(
            email="jane.smith@example.com",
            name="Jane Smith",
            password="SecurePassword123"
        )
        
        await auth_service.assign_role(user.id.value, "admin")
        print(f"   Assigned admin role to {user.name}")
        
        # Check permissions
        has_write = await auth_service.authorize_user(user.id.value, "write_users")
        print(f"   User has write permission: {has_write}")
        
    except Exception as e:
        print(f"   Error: {e}")


# Example 3: Domain-driven design with value objects
def example_domain_objects():
    """Example of working with domain entities and value objects."""
    print("\n=== Example 3: Domain Objects ===")
    
    try:
        # Create user with value objects
        print("1. Creating user with value objects...")
        user_id = UserId("user_12345")
        email = Email("alice@example.com")
        password = Password("StrongPassword123")
        
        user = User(
            id=user_id,
            email=email,
            name="Alice Johnson",
            password_hash=password.hash()
        )
        
        print(f"   User created: {user.name}")
        print(f"   Email domain: {user.email.domain}")
        print(f"   User ID: {user.id.value}")
        
        # Domain logic
        print("2. Domain business logic...")
        user.activate()
        user.record_login()
        
        print(f"   User status: {user.status}")
        print(f"   Last login: {user.last_login}")
        print(f"   Is active: {user.is_active()}")
        
        # Role management
        print("3. Role management...")
        admin_role = Role(
            id="role_admin",
            name="admin",
            description="Administrator role",
            role_type=RoleType.ADMIN
        )
        
        user.add_role(admin_role)
        print(f"   User is admin: {user.is_admin()}")
        print(f"   User has role 'admin': {user.has_role('admin')}")
        
    except Exception as e:
        print(f"   Error: {e}")


# Example 4: Testing with mock adapters
async def example_testing_with_mocks():
    """Example of testing with mock adapters."""
    print("\n=== Example 4: Testing with Mocks ===")
    
    # Create test container with mock implementations
    test_container = DIContainer()
    
    # Configure for testing (uses mock implementations)
    configure_container('testing')
    
    with DIContext(test_container):
        auth_service = inject(AuthApplicationService)
        
        try:
            # Test user registration
            print("1. Testing user registration...")
            user = await auth_service.register_user(
                email="test@example.com",
                name="Test User",
                password="TestPassword123"
            )
            print(f"   Mock registration successful: {user.name}")
            
            # Test authentication
            print("2. Testing authentication...")
            auth_user, session = await auth_service.authenticate_user(
                email="test@example.com",
                password="TestPassword123"
            )
            print(f"   Mock authentication successful: {auth_user.name}")
            
        except Exception as e:
            print(f"   Test error: {e}")


# Example 5: Advanced dependency injection patterns
async def example_advanced_di():
    """Example of advanced dependency injection patterns."""
    print("\n=== Example 5: Advanced DI Patterns ===")
    
    container = DIContainer()
    
    # Factory binding example
    def create_special_user_repo():
        """Factory function for creating specialized repository."""
        print("   Creating specialized user repository...")
        # Return mock or specialized implementation
        from backend.adapters.auth.mock_repositories import MockUserRepository
        return MockUserRepository()
    
    # Bind factory
    container.bind_factory(UserRepositoryPort, create_special_user_repo)
    
    # Instance binding example
    special_config = {"database_url": "sqlite:///test.db", "debug": True}
    container.bind_instance(dict, special_config)
    
    with DIContext(container):
        # Resolve dependencies
        user_repo = inject(UserRepositoryPort)
        config = inject(dict)
        
        print(f"   User repository type: {type(user_repo).__name__}")
        print(f"   Config: {config}")


# Example 6: Context7 integration with backend
def example_context7_integration():
    """Example of Context7 frontend integration with backend."""
    print("\n=== Example 6: Context7 Integration ===")
    
    print("1. Frontend Context7 State Management:")
    print("   - AuthContext manages authentication state")
    print("   - AIAnalysisContext handles AI analysis sessions")
    print("   - AppContext provides global state management")
    print("   - All contexts use adapters to communicate with backend")
    
    print("\n2. Backend API Integration:")
    print("   - FastAPI routes use DI container to resolve services")
    print("   - Application services orchestrate domain logic")
    print("   - Domain events are published for frontend updates")
    print("   - WebSocket connections for real-time updates")
    
    print("\n3. Data Flow:")
    print("   Frontend Context7 → API Adapters → Backend Ports → Domain Services")
    print("   Domain Events → Event Publishers → WebSocket → Frontend Updates")


# Example 7: Error handling and domain exceptions
async def example_error_handling():
    """Example of proper error handling in hexagonal architecture."""
    print("\n=== Example 7: Error Handling ===")
    
    container = configure_container('development')
    auth_service = container.get(AuthApplicationService)
    
    # Example of domain validation errors
    try:
        print("1. Testing domain validation...")
        invalid_email = Email("invalid-email")  # This will fail
    except ValueError as e:
        print(f"   Domain validation error: {e}")
    
    # Example of application service errors
    try:
        print("2. Testing application service errors...")
        await auth_service.authenticate_user(
            email="nonexistent@example.com",
            password="password"
        )
    except Exception as e:
        print(f"   Application service error: {e}")
    
    # Example of proper error handling
    try:
        print("3. Proper error handling...")
        user = await auth_service.register_user(
            email="valid@example.com",
            name="Valid User",
            password="ValidPassword123"
        )
        print(f"   Success: {user.name} registered")
    except Exception as e:
        print(f"   Handled error: {e}")


# Main execution
async def main():
    """Run all examples."""
    print("Hexagonal Architecture Examples")
    print("=" * 50)
    
    # Run examples
    await example_basic_auth()
    await example_role_management()
    example_domain_objects()
    await example_testing_with_mocks()
    await example_advanced_di()
    example_context7_integration()
    await example_error_handling()
    
    print("\n" + "=" * 50)
    print("All examples completed successfully!")


if __name__ == "__main__":
    asyncio.run(main()) 