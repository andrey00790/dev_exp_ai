import os
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Application configuration settings."""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"
    debug: bool = False
    
    # API settings
    title: str = "AI Assistant MVP"
    description: str = "A minimal FastAPI service for development experiments"
    version: str = "1.0.0"
    
    # Logging settings
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create configuration from environment variables."""
        environment = os.getenv("ENVIRONMENT", "development")
        
        config = cls(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            environment=environment,
            debug=environment == "development",
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )
        
        logger.info(f"Configuration loaded: environment={config.environment}")
        return config
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


# Global configuration instance
settings = AppConfig.from_env()


def get_settings() -> AppConfig:
    """Get application settings."""
    return settings


def validate_config() -> bool:
    """Validate configuration settings."""
    try:
        # Проверяем базовые настройки
        if not settings.host:
            return False
        if settings.port <= 0 or settings.port > 65535:
            return False
        if settings.environment not in ["development", "production", "testing"]:
            return False
        if settings.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            return False
        
        return True
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False


def load_environment_config() -> dict:
    """Load configuration from environment variables."""
    return {
        "HOST": os.getenv("HOST", "0.0.0.0"),
        "PORT": os.getenv("PORT", "8000"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "DEBUG": os.getenv("DEBUG", "false").lower() == "true"
    }


def get_database_url() -> str:
    """Get database URL from environment."""
    return os.getenv("DATABASE_URL", "postgresql://localhost:5432/ai_assistant")


def get_redis_url() -> str:
    """Get Redis URL from environment."""
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def get_qdrant_url() -> str:
    """Get Qdrant URL from environment."""
    return os.getenv("QDRANT_URL", "http://localhost:6333") 