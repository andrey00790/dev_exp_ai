"""
Dependency Injection Configuration

Environment-specific configuration for dependency injection container.
Handles different environments: development, testing, production.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

from backend.infrastructure.di_container import DIContainer, DIConfiguration
from backend.application.auth.ports import (
    UserRepositoryPort, RoleRepositoryPort, SessionRepositoryPort,
    PasswordHasherPort, TokenGeneratorPort, EmailServicePort, EventPublisherPort
)


def print_section(title: str, description: str):
    """Helper function to print formatted section headers"""
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print(f"   {description}")
    print('='*60)


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    url: str
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class AuthConfig:
    """Authentication configuration settings."""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30


@dataclass
class EmailConfig:
    """Email service configuration."""
    smtp_server: str
    smtp_port: int = 587
    use_tls: bool = True
    username: Optional[str] = None
    password: Optional[str] = None
    from_email: str = "noreply@example.com"
    template_dir: str = "templates/email"


@dataclass
class RedisConfig:
    """Redis configuration for caching and sessions."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    max_connections: int = 10


class EnvironmentConfig:
    """Environment-specific configuration loader."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables."""
        if self.environment == "development":
            self._load_development_config()
        elif self.environment == "testing":
            self._load_testing_config()
        elif self.environment == "production":
            self._load_production_config()
        else:
            raise ValueError(f"Unknown environment: {self.environment}")
    
    def _load_development_config(self):
        """Load development configuration."""
        self.database = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite:///dev.db"),
            echo=True,
            pool_size=5
        )
        
        self.auth = AuthConfig(
            secret_key=os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"),
            access_token_expire_minutes=60  # Longer for development
        )
        
        self.email = EmailConfig(
            smtp_server=os.getenv("SMTP_SERVER", "localhost"),
            smtp_port=int(os.getenv("SMTP_PORT", "1025")),  # MailHog for dev
            use_tls=False,
            username=None,
            password=None
        )
        
        self.redis = RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=0
        )
    
    def _load_testing_config(self):
        """Load testing configuration."""
        self.database = DatabaseConfig(
            url=os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:"),
            echo=False
        )
        
        self.auth = AuthConfig(
            secret_key="test-secret-key",
            access_token_expire_minutes=5  # Short for testing
        )
        
        self.email = EmailConfig(
            smtp_server="localhost",
            smtp_port=1025,
            use_tls=False
        )
        
        self.redis = RedisConfig(
            host="localhost",
            port=6379,
            db=1  # Use different DB for testing
        )
    
    def _load_production_config(self):
        """Load production configuration."""
        # Production requires all environment variables
        required_vars = [
            "DATABASE_URL", "SECRET_KEY", "SMTP_SERVER", 
            "SMTP_USERNAME", "SMTP_PASSWORD", "REDIS_HOST"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        self.database = DatabaseConfig(
            url=os.getenv("DATABASE_URL"),
            echo=False,
            pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "50"))
        )
        
        self.auth = AuthConfig(
            secret_key=os.getenv("SECRET_KEY"),
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE", "15")),
            refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE", "7"))
        )
        
        self.email = EmailConfig(
            smtp_server=os.getenv("SMTP_SERVER"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            username=os.getenv("SMTP_USERNAME"),
            password=os.getenv("SMTP_PASSWORD"),
            from_email=os.getenv("FROM_EMAIL", "noreply@example.com")
        )
        
        self.redis = RedisConfig(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),
            ssl=os.getenv("REDIS_SSL", "false").lower() == "true"
        )


class EnhancedDIConfiguration(DIConfiguration):
    """Enhanced DI configuration with environment-specific settings."""
    
    def __init__(self, container: DIContainer, config: EnvironmentConfig):
        super().__init__(container)
        self.config = config
    
    def configure_development(self):
        """Configure for development with enhanced settings."""
        super().configure_development()
        
        # Add development-specific configurations
        self._configure_database_adapter()
        self._configure_email_adapter()
        self._configure_cache_adapter()
        
        return self
    
    def configure_testing(self):
        """Configure for testing with mock implementations."""
        super().configure_testing()
        
        # Override with in-memory implementations for testing
        self._configure_test_database()
        self._configure_mock_email()
        self._configure_mock_cache()
        
        return self
    
    def configure_production(self):
        """Configure for production with production-ready implementations."""
        super().configure_production()
        
        # Add production-specific configurations
        self._configure_database_adapter()
        self._configure_email_adapter()
        self._configure_cache_adapter()
        self._configure_monitoring()
        
        return self
    
    def _configure_database_adapter(self):
        """Configure database adapter with environment settings using async drivers."""
        # Bind database configuration as instance
        self.container.bind_instance(DatabaseConfig, self.config.database)
        
        # Factory for async database session
        def create_async_db_session():
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
            
            # Convert sync URL to async URL if needed
            db_url = self.config.database.url
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
            elif db_url.startswith("sqlite:///"):
                db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
            
            async_engine = create_async_engine(
                db_url,
                echo=self.config.database.echo,
                pool_size=self.config.database.pool_size,
                max_overflow=self.config.database.max_overflow,
                pool_timeout=self.config.database.pool_timeout,
                pool_recycle=self.config.database.pool_recycle
            )
            
            AsyncSessionLocal = async_sessionmaker(
                async_engine, class_=AsyncSession, expire_on_commit=False
            )
            return AsyncSessionLocal()
        
        # Bind async session factory
        from sqlalchemy.ext.asyncio import AsyncSession
        self.container.bind_factory(AsyncSession, create_async_db_session)
        
        # Keep sync session for backward compatibility
        def create_sync_db_session():
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            
            engine = create_engine(
                self.config.database.url,
                echo=self.config.database.echo,
                pool_size=self.config.database.pool_size,
                max_overflow=self.config.database.max_overflow,
                pool_timeout=self.config.database.pool_timeout,
                pool_recycle=self.config.database.pool_recycle
            )
            
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            return SessionLocal()
        
        # Bind sync session factory
        from sqlalchemy.orm import Session
        self.container.bind_factory(Session, create_sync_db_session)
    
    def _configure_email_adapter(self):
        """Configure email adapter with environment settings."""
        self.container.bind_instance(EmailConfig, self.config.email)
        
        # Configure SMTP email service with settings
        from backend.adapters.auth.services import SMTPEmailService
        
        def create_email_service():
            return SMTPEmailService(
                smtp_server=self.config.email.smtp_server,
                smtp_port=self.config.email.smtp_port,
                use_tls=self.config.email.use_tls,
                username=self.config.email.username,
                password=self.config.email.password,
                from_email=self.config.email.from_email
            )
        
        self.container.bind_factory(EmailServicePort, create_email_service)
    
    def _configure_cache_adapter(self):
        """Configure caching adapter with Redis."""
        self.container.bind_instance(RedisConfig, self.config.redis)
        
        # Factory for Redis connection
        def create_redis_client():
            import redis
            return redis.Redis(
                host=self.config.redis.host,
                port=self.config.redis.port,
                db=self.config.redis.db,
                password=self.config.redis.password,
                ssl=self.config.redis.ssl,
                max_connections=self.config.redis.max_connections,
                decode_responses=True
            )
        
        # Bind Redis client
        import redis
        self.container.bind_factory(redis.Redis, create_redis_client)
    
    def _configure_test_database(self):
        """Configure in-memory database for testing using async drivers."""
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        
        # Use async SQLite for testing
        async_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        AsyncSessionLocal = async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )
        
        def create_async_test_session():
            return AsyncSessionLocal()
        
        from sqlalchemy.ext.asyncio import AsyncSession
        self.container.bind_factory(AsyncSession, create_async_test_session)
        
        # Keep sync version for backward compatibility
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        sync_engine = create_engine("sqlite:///:memory:", echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
        
        def create_sync_test_session():
            return SessionLocal()
        
        from sqlalchemy.orm import Session
        self.container.bind_factory(Session, create_sync_test_session)
    
    def _configure_mock_email(self):
        """Configure mock email service for testing."""
        from backend.adapters.auth.mock_services import MockEmailService
        self.container.bind(EmailServicePort, MockEmailService)
    
    def _configure_mock_cache(self):
        """Configure mock cache for testing."""
        class MockRedis:
            def __init__(self):
                self.data = {}
            
            def get(self, key):
                return self.data.get(key)
            
            def set(self, key, value, ex=None):
                self.data[key] = value
                return True
            
            def delete(self, key):
                return self.data.pop(key, None) is not None
        
        import redis
        self.container.bind_instance(redis.Redis, MockRedis())
    
    def _configure_monitoring(self):
        """Configure monitoring and observability for production."""
        # Add monitoring configuration
        self.container.bind_instance(dict, {
            "monitoring": {
                "enabled": True,
                "metrics_port": int(os.getenv("METRICS_PORT", "9090")),
                "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "30")),
                "log_level": os.getenv("LOG_LEVEL", "INFO")
            }
        })


def setup_di_container(environment: str = "development") -> DIContainer:
    """
    Set up and configure the DI container for the specified environment.
    
    Args:
        environment: Environment name ('development', 'testing', 'production')
    
    Returns:
        Configured DIContainer instance
    """
    # Load environment configuration
    env_config = EnvironmentConfig(environment)
    
    # Create container
    container = DIContainer()
    
    # Configure container with environment-specific settings
    config = EnhancedDIConfiguration(container, env_config)
    
    if environment == "development":
        config.configure_development()
    elif environment == "testing":
        config.configure_testing()
    elif environment == "production":
        config.configure_production()
    else:
        raise ValueError(f"Unknown environment: {environment}")
    
    return container


# Environment detection
def detect_environment() -> str:
    """
    Detect the current environment from environment variables.
    
    Returns:
        Environment name
    """
    env = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
    
    if env in ["prod", "production"]:
        return "production"
    elif env in ["test", "testing"]:
        return "testing"
    elif env in ["dev", "development"]:
        return "development"
    else:
        return "development"


# Default container setup
def get_configured_container() -> DIContainer:
    """
    Get a pre-configured DI container for the detected environment.
    
    Returns:
        Configured DIContainer instance
    """
    environment = detect_environment()
    return setup_di_container(environment) 


def demo_infrastructure_layer():
    """Demonstrate infrastructure layer"""
    print_section("INFRASTRUCTURE LAYER", "Configuration and cross-cutting concerns")
    
    try:
        from backend.infrastructure.di_container import DIContainer
        from backend.infrastructure.config.di_config import EnvironmentConfig, detect_environment
        
        print("🏗️  Infrastructure Components:")
        
        # Environment detection
        current_env = detect_environment()
        print(f"   • Current environment: {current_env}")
        
        # Configuration
        env_config = EnvironmentConfig(current_env)
        print(f"   • Database URL: {env_config.database.url}")
        print(f"   • Auth algorithm: {env_config.auth.algorithm}")
        
        # DI Container capabilities
        container = DIContainer()
        print(f"   • DI Container: {type(container).__name__}")
        print("   • Supports: Singleton, Transient, Factory bindings")
        print("   • Auto-dependency resolution")
        print("   • Testing contexts")
        
        # Environment configurations
        print("\n🌍 Environment Configurations:")
        environments = [
            ("Development", "SQLite, local email, debug mode"),
            ("Testing", "In-memory DB, mock services"),
            ("Production", "PostgreSQL, real email, monitoring")
        ]
        
        for name, description in environments:
            print(f"   • {name}: {description}")
            
        return True
            
    except Exception as e:
        print(f"❌ Infrastructure layer error: {e}")
        return False 