"""
Dependency Injection Container

Manages dependency injection for hexagonal architecture.
Binds ports (interfaces) to their concrete adapter implementations.
"""

from typing import Type, TypeVar, Dict, Any, Optional, Union
from abc import ABC, abstractmethod
import inspect

T = TypeVar('T')


class DIContainer:
    """
    Dependency Injection Container following hexagonal architecture principles.
    
    Manages the binding of ports (interfaces) to adapters (implementations).
    Supports singleton and transient lifetimes.
    """
    
    def __init__(self):
        self._bindings: Dict[Type, Dict[str, Any]] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Any] = {}
    
    def bind(self, interface: Type[T], implementation: Type[T], lifetime: str = 'singleton') -> 'DIContainer':
        """
        Bind an interface to its implementation.
        
        Args:
            interface: The interface/port to bind
            implementation: The concrete implementation/adapter
            lifetime: 'singleton' or 'transient'
        
        Returns:
            Self for method chaining
        """
        if not self._is_interface_compatible(interface, implementation):
            raise ValueError(f"Implementation {implementation} is not compatible with interface {interface}")
        
        self._bindings[interface] = {
            'implementation': implementation,
            'lifetime': lifetime
        }
        return self
    
    def bind_factory(self, interface: Type[T], factory: callable) -> 'DIContainer':
        """
        Bind an interface to a factory function.
        
        Args:
            interface: The interface/port to bind
            factory: Factory function that creates the implementation
        
        Returns:
            Self for method chaining
        """
        self._factories[interface] = factory
        return self
    
    def bind_instance(self, interface: Type[T], instance: T) -> 'DIContainer':
        """
        Bind an interface to a specific instance.
        
        Args:
            interface: The interface/port to bind
            instance: The specific instance to use
        
        Returns:
            Self for method chaining
        """
        self._singletons[interface] = instance
        return self
    
    def get(self, interface: Type[T]) -> T:
        """
        Resolve an interface to its implementation.
        
        Args:
            interface: The interface/port to resolve
        
        Returns:
            The concrete implementation instance
        
        Raises:
            DIError: If the interface is not bound or cannot be resolved
        """
        # Check if we have a specific instance bound
        if interface in self._singletons:
            return self._singletons[interface]
        
        # Check if we have a factory bound
        if interface in self._factories:
            factory = self._factories[interface]
            instance = factory()
            if not isinstance(instance, interface):
                raise DIError(f"Factory for {interface} returned incompatible type {type(instance)}")
            return instance
        
        # Check if we have a binding
        if interface not in self._bindings:
            raise DIError(f"No binding found for {interface}")
        
        binding = self._bindings[interface]
        implementation = binding['implementation']
        lifetime = binding['lifetime']
        
        # Handle singleton lifetime
        if lifetime == 'singleton':
            if interface not in self._singletons:
                self._singletons[interface] = self._create_instance(implementation)
            return self._singletons[interface]
        
        # Handle transient lifetime
        elif lifetime == 'transient':
            return self._create_instance(implementation)
        
        else:
            raise DIError(f"Unknown lifetime: {lifetime}")
    
    def _create_instance(self, implementation: Type[T]) -> T:
        """
        Create an instance of the implementation, resolving dependencies.
        
        Args:
            implementation: The class to instantiate
        
        Returns:
            Instance of the implementation
        """
        # Get constructor signature
        sig = inspect.signature(implementation.__init__)
        
        # Skip 'self' parameter
        parameters = list(sig.parameters.values())[1:]
        
        # Resolve dependencies
        kwargs = {}
        for param in parameters:
            if param.annotation != inspect.Parameter.empty:
                try:
                    kwargs[param.name] = self.get(param.annotation)
                except DIError:
                    # If dependency cannot be resolved and has no default, raise error
                    if param.default == inspect.Parameter.empty:
                        raise DIError(f"Cannot resolve dependency {param.annotation} for {implementation}")
        
        try:
            return implementation(**kwargs)
        except Exception as e:
            raise DIError(f"Failed to create instance of {implementation}: {e}")
    
    def _is_interface_compatible(self, interface: Type, implementation: Type) -> bool:
        """
        Check if implementation is compatible with interface.
        
        Args:
            interface: The interface/port
            implementation: The concrete implementation
        
        Returns:
            True if compatible, False otherwise
        """
        # Check if implementation inherits from interface
        if issubclass(implementation, interface):
            return True
        
        # Check if implementation has all required methods of interface
        interface_methods = set(dir(interface))
        implementation_methods = set(dir(implementation))
        
        # Filter out private methods and properties
        interface_methods = {m for m in interface_methods if not m.startswith('_')}
        implementation_methods = {m for m in implementation_methods if not m.startswith('_')}
        
        return interface_methods.issubset(implementation_methods)
    
    def is_bound(self, interface: Type) -> bool:
        """
        Check if an interface is bound.
        
        Args:
            interface: The interface to check
        
        Returns:
            True if bound, False otherwise
        """
        return (interface in self._bindings or 
                interface in self._singletons or 
                interface in self._factories)
    
    def clear(self):
        """Clear all bindings and singletons."""
        self._bindings.clear()
        self._singletons.clear()
        self._factories.clear()


class DIError(Exception):
    """Exception raised by dependency injection container."""
    pass


class DIConfiguration:
    """
    Configuration class for setting up dependency injection.
    
    Provides methods to configure different environments (development, testing, production).
    """
    
    def __init__(self, container: DIContainer):
        self.container = container
    
    def configure_development(self):
        """Configure container for development environment."""
        from backend.adapters.auth.repositories import (
            MockUserRepository, MockRoleRepository, MockSessionRepository, MockPermissionRepository
        )
        from backend.adapters.auth.services import (
            BcryptPasswordHasher, JWTTokenGenerator, MockEmailService, MockEventPublisher
        )
        from backend.application.auth.ports import (
            UserRepositoryPort, RoleRepositoryPort, SessionRepositoryPort, PermissionRepositoryPort,
            PasswordHasherPort, TokenGeneratorPort, EmailServicePort, EventPublisherPort
        )
        from backend.application.auth.services import AuthApplicationService, RoleManagementService
        
        # Bind repositories (using mock implementations for development)
        self.container.bind(UserRepositoryPort, MockUserRepository)
        self.container.bind(RoleRepositoryPort, MockRoleRepository)
        self.container.bind(SessionRepositoryPort, MockSessionRepository)
        self.container.bind(PermissionRepositoryPort, MockPermissionRepository)
        
        # Bind services
        self.container.bind(PasswordHasherPort, BcryptPasswordHasher)
        self.container.bind_factory(TokenGeneratorPort, lambda: JWTTokenGenerator("dev_secret_key"))
        self.container.bind(EmailServicePort, MockEmailService)
        self.container.bind(EventPublisherPort, MockEventPublisher)
        
        # Bind application services
        self.container.bind(AuthApplicationService, AuthApplicationService)
        self.container.bind(RoleManagementService, RoleManagementService)
        
        return self
    
    def configure_testing(self):
        """Configure container for testing environment."""
        from backend.adapters.auth.repositories import (
            MockUserRepository, MockRoleRepository, MockSessionRepository, MockPermissionRepository
        )
        from backend.adapters.auth.services import (
            BcryptPasswordHasher, JWTTokenGenerator, MockEmailService, MockEventPublisher
        )
        from backend.application.auth.ports import (
            UserRepositoryPort, RoleRepositoryPort, SessionRepositoryPort, PermissionRepositoryPort,
            PasswordHasherPort, TokenGeneratorPort, EmailServicePort, EventPublisherPort
        )
        from backend.application.auth.services import AuthApplicationService, RoleManagementService
        
        # Bind mock repositories
        self.container.bind(UserRepositoryPort, MockUserRepository)
        self.container.bind(RoleRepositoryPort, MockRoleRepository)
        self.container.bind(SessionRepositoryPort, MockSessionRepository)
        self.container.bind(PermissionRepositoryPort, MockPermissionRepository)
        
        # Bind services (mostly mocks for testing)
        self.container.bind(PasswordHasherPort, BcryptPasswordHasher)
        self.container.bind_factory(TokenGeneratorPort, lambda: JWTTokenGenerator("test_secret_key"))
        self.container.bind(EmailServicePort, MockEmailService)
        self.container.bind(EventPublisherPort, MockEventPublisher)
        
        # Bind application services
        self.container.bind(AuthApplicationService, AuthApplicationService)
        self.container.bind(RoleManagementService, RoleManagementService)
        
        return self
    
    def configure_production(self):
        """Configure container for production environment."""
        from backend.adapters.auth.repositories import (
            MockUserRepository, MockRoleRepository, MockSessionRepository, MockPermissionRepository
        )
        from backend.adapters.auth.services import (
            BcryptPasswordHasher, JWTTokenGenerator, MockEmailService, MockEventPublisher
        )
        from backend.application.auth.ports import (
            UserRepositoryPort, RoleRepositoryPort, SessionRepositoryPort, PermissionRepositoryPort,
            PasswordHasherPort, TokenGeneratorPort, EmailServicePort, EventPublisherPort
        )
        from backend.application.auth.services import AuthApplicationService, RoleManagementService
        
        # Bind repositories (using mock for now, will switch to real DBs later)
        self.container.bind(UserRepositoryPort, MockUserRepository)
        self.container.bind(RoleRepositoryPort, MockRoleRepository)
        self.container.bind(SessionRepositoryPort, MockSessionRepository)
        self.container.bind(PermissionRepositoryPort, MockPermissionRepository)
        
        # Bind services with production configurations
        self.container.bind(PasswordHasherPort, BcryptPasswordHasher)
        self.container.bind_factory(TokenGeneratorPort, lambda: JWTTokenGenerator("prod_secret_key"))
        self.container.bind(EmailServicePort, MockEmailService)
        self.container.bind(EventPublisherPort, MockEventPublisher)
        
        # Bind application services
        self.container.bind(AuthApplicationService, AuthApplicationService)
        self.container.bind(RoleManagementService, RoleManagementService)
        
        return self


# Global container instance
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """
    Get the global DI container instance.
    
    Returns:
        The global DIContainer instance
    """
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def configure_container(environment: str = 'development') -> DIContainer:
    """
    Configure the global DI container for a specific environment.
    
    Args:
        environment: The environment to configure for ('development', 'testing', 'production')
    
    Returns:
        The configured DIContainer instance
    """
    container = get_container()
    container.clear()  # Clear any existing bindings
    
    config = DIConfiguration(container)
    
    if environment == 'development':
        config.configure_development()
    elif environment == 'testing':
        config.configure_testing()
    elif environment == 'production':
        config.configure_production()
    else:
        raise ValueError(f"Unknown environment: {environment}")
    
    return container


def inject(interface: Type[T]) -> T:
    """
    Inject a dependency using the global container.
    
    Args:
        interface: The interface/port to inject
    
    Returns:
        The concrete implementation instance
    """
    return get_container().get(interface)


# Context manager for temporary container configuration
class DIContext:
    """Context manager for temporary DI container configuration."""
    
    def __init__(self, container: DIContainer):
        self.container = container
        self.original_container = None
    
    def __enter__(self):
        global _container
        self.original_container = _container
        _container = self.container
        return self.container
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        global _container
        _container = self.original_container 