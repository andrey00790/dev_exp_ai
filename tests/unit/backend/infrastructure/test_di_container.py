"""
Unit Tests for DI Container and Configuration System

Tests for dependency injection container and configuration management.
Following hexagonal architecture testing principles.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Protocol, Optional
import os
import tempfile
from typing import runtime_checkable

from backend.infrastructure.di_container import DIContainer, DIError
from backend.infrastructure.config.di_config import (
    EnvironmentConfig, DatabaseConfig, AuthConfig, EmailConfig, RedisConfig,
    DIConfiguration, EnhancedDIConfiguration, detect_environment
)


# Test interfaces for DI container testing
@runtime_checkable
class TestServicePort(Protocol):
    """Test service port for DI container testing"""
    def process(self, data: str) -> str:
        ...


@runtime_checkable  
class TestRepositoryPort(Protocol):
    """Test repository port for DI container testing"""
    async def save(self, item: dict) -> dict:
        ...


# Test implementations (renamed to avoid pytest collection)
class MockTestService:
    """Test service implementation"""
    
    def __init__(self, dependency: Optional[str] = None):
        self.dependency = dependency
    
    def process(self, data: str) -> str:
        return f"processed: {data}"


class MockTestRepository:
    """Test repository implementation"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    async def save(self, item: dict) -> dict:
        return {"id": "test_id", **item}


class TestDIContainer:
    """Test DIContainer functionality"""
    
    @pytest.fixture
    def container(self):
        """Create a fresh DI container"""
        return DIContainer()
    
    def test_bind_singleton_success(self, container):
        """Test successful singleton binding"""
        # Execute
        result = container.bind(TestServicePort, MockTestService, lifetime='singleton')
        
        # Verify
        assert result is container  # Should return self for chaining
        assert container.is_bound(TestServicePort)
    
    def test_bind_transient_success(self, container):
        """Test successful transient binding"""
        # Execute
        result = container.bind(TestServicePort, MockTestService, lifetime='transient')
        
        # Verify
        assert result is container
        assert container.is_bound(TestServicePort)
    
    def test_bind_invalid_implementation_fails(self, container):
        """Test binding with invalid implementation fails"""
        class IncompatibleImpl:
            def wrong_method(self):
                pass
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Implementation .* is not compatible"):
            container.bind(TestServicePort, IncompatibleImpl)
    
    def test_resolve_singleton_success(self, container):
        """Test successful singleton resolution"""
        # Setup
        container.bind(TestServicePort, MockTestService, lifetime='singleton')
        
        # Execute
        instance1 = container.get(TestServicePort)
        instance2 = container.get(TestServicePort)
        
        # Verify
        assert instance1 is not None
        assert instance2 is not None
        assert instance1 is instance2  # Same instance for singleton
        assert isinstance(instance1, MockTestService)
    
    def test_resolve_transient_success(self, container):
        """Test successful transient resolution"""
        # Setup
        container.bind(TestServicePort, MockTestService, lifetime='transient')
        
        # Execute
        instance1 = container.get(TestServicePort)
        instance2 = container.get(TestServicePort)
        
        # Verify
        assert instance1 is not None
        assert instance2 is not None
        assert instance1 is not instance2  # Different instances for transient
        assert isinstance(instance1, MockTestService)
        assert isinstance(instance2, MockTestService)
    
    def test_resolve_unbound_interface_fails(self, container):
        """Test resolution of unbound interface fails"""
        # Execute & Verify
        with pytest.raises(DIError, match="No binding found for"):
            container.get(TestServicePort)
    
    def test_resolve_with_dependencies_success(self, container):
        """Test resolution with dependency injection"""
        # Setup
        container.bind_instance(str, "test_dependency")
        container.bind(TestServicePort, MockTestService, lifetime='singleton')
        
        # Execute
        instance = container.get(TestServicePort)
        
        # Verify
        assert instance is not None
        assert isinstance(instance, MockTestService)
    
    def test_bind_factory_success(self, container):
        """Test successful factory binding"""
        # Setup
        def test_factory():
            return MockTestService("factory_dependency")
        
        # Execute
        result = container.bind_factory(TestServicePort, test_factory)
        
        # Verify
        assert result is container
        assert container.is_bound(TestServicePort)
    
    def test_resolve_factory_success(self, container):
        """Test successful factory resolution"""
        # Setup
        def test_factory():
            return MockTestService("factory_dependency")
        
        container.bind_factory(TestServicePort, test_factory)
        
        # Execute
        instance = container.get(TestServicePort)
        
        # Verify
        assert instance is not None
        assert isinstance(instance, MockTestService)
        assert instance.dependency == "factory_dependency"
    
    def test_bind_instance_success(self, container):
        """Test successful instance binding"""
        # Setup
        test_instance = MockTestService("instance_dependency")
        
        # Execute
        result = container.bind_instance(TestServicePort, test_instance)
        
        # Verify
        assert result is container
        assert container.is_bound(TestServicePort)
    
    def test_resolve_instance_success(self, container):
        """Test successful instance resolution"""
        # Setup
        test_instance = MockTestService("instance_dependency")
        container.bind_instance(TestServicePort, test_instance)
        
        # Execute
        instance = container.get(TestServicePort)
        
        # Verify
        assert instance is test_instance  # Same instance
        assert instance.dependency == "instance_dependency"
    
    def test_resolve_with_circular_dependency_fails(self, container):
        """Test resolution with circular dependency fails"""
        # Setup classes with circular dependencies
        class ServiceA:
            def __init__(self, service_b: 'ServiceB'):
                self.service_b = service_b
        
        class ServiceB:
            def __init__(self, service_a: ServiceA):
                self.service_a = service_a
        
        container.bind(ServiceA, ServiceA)
        container.bind(ServiceB, ServiceB)
        
        # Execute & Verify
        with pytest.raises(DIError, match="No binding found for"):
            container.get(ServiceA)
    
    def test_resolve_with_complex_dependencies_success(self, container):
        """Test resolution with complex dependency tree"""
        # Setup
        class DatabaseService:
            def __init__(self, connection_string: str):
                self.connection_string = connection_string
        
        class EmailService:
            def __init__(self, smtp_server: str):
                self.smtp_server = smtp_server
        
        class UserService:
            def __init__(self, db: DatabaseService, email: EmailService):
                self.db = db
                self.email = email
        
        container.bind_instance(str, "postgresql://localhost/test")
        container.bind(DatabaseService, DatabaseService)
        container.bind_instance(EmailService, EmailService("smtp.example.com"))
        container.bind(UserService, UserService)
        
        # Execute
        user_service = container.get(UserService)
        
        # Verify
        assert user_service is not None
        assert isinstance(user_service, UserService)
        assert isinstance(user_service.db, DatabaseService)
        assert isinstance(user_service.email, EmailService)
        assert user_service.db.connection_string == "postgresql://localhost/test"
        assert user_service.email.smtp_server == "smtp.example.com"
    
    def test_clear_container_success(self, container):
        """Test clearing container"""
        # Setup
        container.bind(TestServicePort, MockTestService)
        container.bind_instance(str, "test")
        
        # Execute
        container.clear()
        
        # Verify
        assert not container.is_bound(TestServicePort)
        assert not container.is_bound(str)
    
    def test_is_bound_success(self, container):
        """Test is_bound method"""
        # Initially not bound
        assert not container.is_bound(TestServicePort)
        
        # Bind and check
        container.bind(TestServicePort, MockTestService)
        assert container.is_bound(TestServicePort)
        
        # Clear and check
        container.clear()
        assert not container.is_bound(TestServicePort)
    
    def test_resolve_with_optional_dependencies_success(self, container):
        """Test resolution with optional dependencies"""
        # Setup
        class ServiceWithOptional:
            def __init__(self, required: str, optional: Optional[int] = None):
                self.required = required
                self.optional = optional
        
        container.bind_instance(str, "required_value")
        container.bind(ServiceWithOptional, ServiceWithOptional)
        
        # Execute
        instance = container.get(ServiceWithOptional)
        
        # Verify
        assert instance is not None
        assert instance.required == "required_value"
        assert instance.optional is None
    
    def test_resolve_with_default_values_success(self, container):
        """Test resolution with default parameter values"""
        # Setup
        class ServiceWithDefaults:
            def __init__(self, name: str = "default_name", count: int = 42):
                self.name = name
                self.count = count
        
        container.bind(ServiceWithDefaults, ServiceWithDefaults)
        
        # Execute
        instance = container.get(ServiceWithDefaults)
        
        # Verify
        assert instance is not None
        assert instance.name == "default_name"
        assert instance.count == 42


class TestEnvironmentConfig:
    """Test EnvironmentConfig functionality"""
    
    @pytest.fixture
    def temp_env_vars(self):
        """Setup temporary environment variables"""
        original_env = os.environ.copy()
        yield
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)
    
    def test_development_config_success(self, temp_env_vars):
        """Test development configuration loading"""
        # Setup
        os.environ.update({
            'DATABASE_URL': 'sqlite:///dev.db',
            'SECRET_KEY': 'dev-secret-key',
            'SMTP_SERVER': 'localhost',
            'SMTP_PORT': '1025',
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': '6379'
        })
        
        # Execute
        config = EnvironmentConfig("development")
        
        # Verify
        assert config.environment == "development"
        assert config.database.url == "sqlite:///dev.db"
        assert config.database.echo == True
        assert config.auth.secret_key == "dev-secret-key"
        assert config.auth.access_token_expire_minutes == 60
        assert config.email.smtp_server == "localhost"
        assert config.email.smtp_port == 1025
        assert config.email.use_tls == False
        assert config.redis.host == "localhost"
        assert config.redis.port == 6379
        assert config.redis.db == 0
    
    def test_testing_config_success(self, temp_env_vars):
        """Test testing configuration loading"""
        # Execute
        config = EnvironmentConfig("testing")
        
        # Verify
        assert config.environment == "testing"
        assert config.database.url == "sqlite:///:memory:"
        assert config.database.echo == False
        assert config.auth.secret_key == "test-secret-key"
        assert config.auth.access_token_expire_minutes == 5
        assert config.email.smtp_server == "localhost"
        assert config.email.smtp_port == 1025
        assert config.redis.host == "localhost"
        assert config.redis.port == 6379
        assert config.redis.db == 1
    
    def test_production_config_success(self, temp_env_vars):
        """Test production configuration loading"""
        # Setup
        os.environ.update({
            'DATABASE_URL': 'postgresql://user:pass@prod-db:5432/db',
            'SECRET_KEY': 'prod-secret-key',
            'SMTP_SERVER': 'smtp.prod.com',
            'SMTP_USERNAME': 'prod@example.com',
            'SMTP_PASSWORD': 'prod-password',
            'REDIS_HOST': 'prod-redis',
            'DB_POOL_SIZE': '20',
            'DB_MAX_OVERFLOW': '50',
            'ACCESS_TOKEN_EXPIRE': '15',
            'REFRESH_TOKEN_EXPIRE': '7'
        })
        
        # Execute
        config = EnvironmentConfig("production")
        
        # Verify
        assert config.environment == "production"
        assert config.database.url == "postgresql://user:pass@prod-db:5432/db"
        assert config.database.echo == False
        assert config.database.pool_size == 20
        assert config.database.max_overflow == 50
        assert config.auth.secret_key == "prod-secret-key"
        assert config.auth.access_token_expire_minutes == 15
        assert config.auth.refresh_token_expire_days == 7
        assert config.email.smtp_server == "smtp.prod.com"
        assert config.email.username == "prod@example.com"
        assert config.email.password == "prod-password"
        assert config.redis.host == "prod-redis"
    
    def test_production_config_missing_vars_fails(self, temp_env_vars):
        """Test production configuration fails with missing variables"""
        # Setup - missing required variables
        os.environ.update({
            'DATABASE_URL': 'postgresql://user:pass@prod-db:5432/db',
            # Missing SECRET_KEY, SMTP_SERVER, etc.
        })
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Missing required environment variables"):
            EnvironmentConfig("production")
    
    def test_unknown_environment_fails(self, temp_env_vars):
        """Test unknown environment fails"""
        # Execute & Verify
        with pytest.raises(ValueError, match="Unknown environment: unknown"):
            EnvironmentConfig("unknown")
    
    def test_config_components_success(self, temp_env_vars):
        """Test individual configuration components"""
        # Execute
        config = EnvironmentConfig("development")
        
        # Verify DatabaseConfig
        assert isinstance(config.database, DatabaseConfig)
        assert config.database.url is not None
        assert isinstance(config.database.echo, bool)
        
        # Verify AuthConfig
        assert isinstance(config.auth, AuthConfig)
        assert config.auth.secret_key is not None
        assert config.auth.algorithm == "HS256"
        assert config.auth.access_token_expire_minutes > 0
        
        # Verify EmailConfig
        assert isinstance(config.email, EmailConfig)
        assert config.email.smtp_server is not None
        assert config.email.smtp_port > 0
        
        # Verify RedisConfig
        assert isinstance(config.redis, RedisConfig)
        assert config.redis.host is not None
        assert config.redis.port > 0


class TestDIConfiguration:
    """Test DIConfiguration functionality"""
    
    @pytest.fixture
    def container(self):
        """Create a fresh DI container"""
        return DIContainer()
    
    @pytest.fixture
    def di_config(self, container):
        """Create DIConfiguration instance"""
        return DIConfiguration(container)
    
    def test_configure_development_success(self, di_config):
        """Test development configuration setup"""
        # Execute
        result = di_config.configure_development()
        
        # Verify
        assert result is di_config
        # Verify that ports are bound (we can't test actual bindings without real implementations)
        assert hasattr(di_config, 'container')
    
    def test_configure_testing_success(self, di_config):
        """Test testing configuration setup"""
        # Execute
        result = di_config.configure_testing()
        
        # Verify
        assert result is di_config
        assert hasattr(di_config, 'container')
    
    def test_configure_production_success(self, di_config):
        """Test production configuration setup"""
        # Execute
        result = di_config.configure_production()
        
        # Verify
        assert result is di_config
        assert hasattr(di_config, 'container')


class TestEnhancedDIConfiguration:
    """Test EnhancedDIConfiguration functionality"""
    
    @pytest.fixture
    def container(self):
        """Create a fresh DI container"""
        return DIContainer()
    
    @pytest.fixture
    def env_config(self):
        """Create EnvironmentConfig instance"""
        return EnvironmentConfig("testing")
    
    @pytest.fixture
    def enhanced_di_config(self, container, env_config):
        """Create EnhancedDIConfiguration instance"""
        return EnhancedDIConfiguration(container, env_config)
    
    def test_configure_development_success(self, enhanced_di_config):
        """Test enhanced development configuration setup"""
        # Execute
        result = enhanced_di_config.configure_development()
        
        # Verify
        assert result is enhanced_di_config
        assert hasattr(enhanced_di_config, 'container')
        assert hasattr(enhanced_di_config, 'config')
    
    def test_configure_testing_success(self, enhanced_di_config):
        """Test enhanced testing configuration setup"""
        # Execute
        result = enhanced_di_config.configure_testing()
        
        # Verify
        assert result is enhanced_di_config
        assert hasattr(enhanced_di_config, 'container')
        assert hasattr(enhanced_di_config, 'config')
    
    def test_configure_production_success(self, enhanced_di_config):
        """Test enhanced production configuration setup"""
        # Execute
        result = enhanced_di_config.configure_production()
        
        # Verify
        assert result is enhanced_di_config
        assert hasattr(enhanced_di_config, 'container')
        assert hasattr(enhanced_di_config, 'config')
    
    @patch('backend.infrastructure.config.di_config.create_engine')
    def test_configure_database_adapter_success(self, mock_create_engine, enhanced_di_config):
        """Test database adapter configuration"""
        # Setup
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Execute
        enhanced_di_config._configure_database_adapter()
        
        # Verify
        mock_create_engine.assert_called_once()
        # Verify engine was created with correct parameters
        args, kwargs = mock_create_engine.call_args
        assert enhanced_di_config.config.database.url in args[0]
    
    @patch('backend.infrastructure.config.di_config.create_engine')
    def test_configure_test_database_success(self, mock_create_engine, enhanced_di_config):
        """Test test database configuration"""
        # Setup
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Execute
        enhanced_di_config._configure_test_database()
        
        # Verify
        mock_create_engine.assert_called_once_with("sqlite:///:memory:", echo=False)
    
    def test_configure_email_adapter_success(self, enhanced_di_config):
        """Test email adapter configuration"""
        # Execute
        enhanced_di_config._configure_email_adapter()
        
        # Verify
        assert enhanced_di_config.config.email is not None
        # Verify that email config was bound to container
        assert enhanced_di_config.container.is_bound(EmailConfig)
    
    def test_configure_cache_adapter_success(self, enhanced_di_config):
        """Test cache adapter configuration"""
        # Execute
        enhanced_di_config._configure_cache_adapter()
        
        # Verify
        assert enhanced_di_config.config.redis is not None
        # Verify that redis config was bound to container
        assert enhanced_di_config.container.is_bound(RedisConfig)
    
    def test_configure_mock_email_success(self, enhanced_di_config):
        """Test mock email service configuration"""
        # Execute
        enhanced_di_config._configure_mock_email()
        
        # Verify
        # Should bind mock email service instead of real one
        assert hasattr(enhanced_di_config, 'container')
    
    def test_configure_mock_cache_success(self, enhanced_di_config):
        """Test mock cache service configuration"""
        # Execute
        enhanced_di_config._configure_mock_cache()
        
        # Verify
        # Should bind mock cache service instead of real one
        assert hasattr(enhanced_di_config, 'container')
    
    def test_configure_monitoring_success(self, enhanced_di_config):
        """Test monitoring configuration"""
        # Execute
        enhanced_di_config._configure_monitoring()
        
        # Verify
        # Should configure monitoring services
        assert hasattr(enhanced_di_config, 'container')


class TestEnvironmentDetection:
    """Test environment detection functionality"""
    
    @pytest.fixture
    def temp_env_vars(self):
        """Setup temporary environment variables"""
        original_env = os.environ.copy()
        yield
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)
    
    def test_detect_environment_from_env_var(self, temp_env_vars):
        """Test environment detection from environment variable"""
        # Setup
        os.environ['ENVIRONMENT'] = 'production'
        
        # Execute
        env = detect_environment()
        
        # Verify
        assert env == 'production'
    
    def test_detect_environment_from_app_env_var(self, temp_env_vars):
        """Test environment detection from APP_ENV variable"""
        # Setup
        os.environ['APP_ENV'] = 'staging'
        
        # Execute
        env = detect_environment()
        
        # Verify
        assert env == 'staging'
    
    def test_detect_environment_from_python_env_var(self, temp_env_vars):
        """Test environment detection from PYTHON_ENV variable"""
        # Setup
        os.environ['PYTHON_ENV'] = 'development'
        
        # Execute
        env = detect_environment()
        
        # Verify
        assert env == 'development'
    
    def test_detect_environment_default(self, temp_env_vars):
        """Test environment detection defaults to development"""
        # Setup - no environment variables set
        
        # Execute
        env = detect_environment()
        
        # Verify
        assert env == 'development'
    
    def test_detect_environment_precedence(self, temp_env_vars):
        """Test environment variable precedence"""
        # Setup
        os.environ['ENVIRONMENT'] = 'production'
        os.environ['APP_ENV'] = 'staging'
        os.environ['PYTHON_ENV'] = 'development'
        
        # Execute
        env = detect_environment()
        
        # Verify
        assert env == 'production'  # ENVIRONMENT should have highest precedence


class TestConfigurationIntegration:
    """Test full configuration integration"""
    
    @pytest.fixture
    def temp_env_vars(self):
        """Setup temporary environment variables"""
        original_env = os.environ.copy()
        yield
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)
    
    def test_full_configuration_cycle_development(self, temp_env_vars):
        """Test full configuration cycle for development"""
        # Setup
        os.environ['ENVIRONMENT'] = 'development'
        os.environ['DATABASE_URL'] = 'sqlite:///test.db'
        os.environ['SECRET_KEY'] = 'test-secret'
        
        # Execute
        env = detect_environment()
        config = EnvironmentConfig(env)
        container = DIContainer()
        di_config = DIConfiguration(container)
        di_config.configure_development()
        
        # Verify
        assert env == 'development'
        assert config.database.url == 'sqlite:///test.db'
        assert config.auth.secret_key == 'test-secret'
        assert container is not None
    
    def test_full_configuration_cycle_testing(self, temp_env_vars):
        """Test full configuration cycle for testing"""
        # Setup
        os.environ['ENVIRONMENT'] = 'testing'
        
        # Execute
        env = detect_environment()
        config = EnvironmentConfig(env)
        container = DIContainer()
        di_config = DIConfiguration(container)
        di_config.configure_testing()
        
        # Verify
        assert env == 'testing'
        assert config.database.url == 'sqlite:///:memory:'
        assert config.auth.secret_key == 'test-secret-key'
        assert container is not None
    
    def test_full_configuration_cycle_production(self, temp_env_vars):
        """Test full configuration cycle for production"""
        # Setup
        os.environ.update({
            'ENVIRONMENT': 'production',
            'DATABASE_URL': 'postgresql://user:pass@prod-db:5432/db',
            'SECRET_KEY': 'prod-secret-key',
            'SMTP_SERVER': 'smtp.prod.com',
            'SMTP_USERNAME': 'prod@example.com',
            'SMTP_PASSWORD': 'prod-password',
            'REDIS_HOST': 'prod-redis'
        })
        
        # Execute
        env = detect_environment()
        config = EnvironmentConfig(env)
        container = DIContainer()
        di_config = DIConfiguration(container)
        di_config.configure_production()
        
        # Verify
        assert env == 'production'
        assert config.database.url == 'postgresql://user:pass@prod-db:5432/db'
        assert config.auth.secret_key == 'prod-secret-key'
        assert container is not None 