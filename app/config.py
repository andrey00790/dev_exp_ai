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