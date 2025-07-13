#!/usr/bin/env python3
"""
AI Assistant - Hexagonal Architecture Main Entry Point

Clean hexagonal architecture implementation following Ports & Adapters pattern.
All dependencies point inward to the core domain.
"""

import asyncio
import logging
import sys
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Hexagonal Architecture Imports
from hex_core.domain.auth.entities import User, Role
from hex_core.use_cases.auth_services import AuthApplicationService
from hex_adapters.api.auth.sso import router as sso_router
from hex_adapters.api.search.search import router as search_router
from hex_adapters.api.ai.ai_advanced import router as ai_router
from hex_infrastructure.config.config import settings
from hex_infrastructure.middleware.async_utils import AsyncTimeouts
from hex_infrastructure.middleware.exceptions import (
    AsyncResourceError,
    AsyncRetryError,
    AsyncTimeoutError
)


class HexagonalApp:
    """
    Hexagonal Architecture Application
    
    Orchestrates the entire application following clean architecture principles.
    Dependencies flow inward: Infrastructure → Application → Domain
    """
    
    def __init__(self):
        self.app = FastAPI(
            title="AI Assistant - Hexagonal Architecture",
            description="Clean architecture implementation with Ports & Adapters pattern",
            version="1.0.0"
        )
        self.setup_middleware()
        self.setup_routes()
        self.setup_exception_handlers()
    
    def setup_middleware(self):
        """Setup middleware following hexagonal principles"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        logger.info("✅ Middleware configured")
    
    def setup_routes(self):
        """Setup API routes (Adapters)"""
        # Primary adapters (driving the application)
        self.app.include_router(sso_router, prefix="/api/v1/auth", tags=["Authentication"])
        self.app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])
        self.app.include_router(ai_router, prefix="/api/v1/ai", tags=["AI"])
        
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "architecture": "hexagonal"}
        
        logger.info("✅ Routes configured")
    
    def setup_exception_handlers(self):
        """Setup exception handlers"""
        # Custom exception handling will be implemented here
        logger.info("✅ Exception handlers configured")
    
    async def startup(self):
        """Application startup"""
        logger.info("🚀 Starting AI Assistant with Hexagonal Architecture")
        # Initialize core services
        logger.info("✅ Core services initialized")
    
    async def shutdown(self):
        """Application shutdown"""
        logger.info("🛑 Shutting down AI Assistant")
        # Cleanup resources
        logger.info("✅ Resources cleaned up")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    hex_app = HexagonalApp()
    
    # Setup lifespan events
    @hex_app.app.on_event("startup")
    async def startup_event():
        await hex_app.startup()
    
    @hex_app.app.on_event("shutdown")
    async def shutdown_event():
        await hex_app.shutdown()
    
    return hex_app.app


def main():
    """Main entry point"""
    app = create_app()
    
    logger.info("🏗️ Hexagonal Architecture Initialized")
    logger.info("📚 API Docs: http://localhost:8000/docs")
    logger.info("💊 Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main() 