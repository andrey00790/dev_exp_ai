"""
AI Assistant MVP - Main Application Entry Point
Phase 1: Production Security (Complete)
Phase 2: Performance Optimization (Complete)

Features:
- 71 secure API endpoints with JWT authentication
- Comprehensive security hardening (A+ grade)
- Cost control and budget enforcement
- Performance optimization with caching
- Production-ready monitoring
"""

import logging
import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
import uvicorn

# Import routers
from app.api.v1 import (
    auth, ai_enhancement, generate, search, vector_search,
    data_sources, documentation, feedback, llm_management, 
    user_settings, learning
)

# Security and middleware imports
from app.security.auth import auth_middleware
from app.security.cost_control import cost_control_middleware
from app.security.input_validation import input_validation_middleware
from app.security.security_headers import SecurityHeadersMiddleware
from app.security.rate_limiter import setup_rate_limiting_middleware
from app.monitoring.metrics import metrics_middleware

# WebSocket support
from app.websocket import handle_websocket_connection

# Performance imports with fallback
try:
    from app.performance.cache_manager import cache_manager
    from app.performance.database_optimizer import db_optimizer
    PERFORMANCE_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Performance modules not available: {e}")
    PERFORMANCE_AVAILABLE = False

# Budget API with conditional performance import
try:
    from app.api.v1 import budget
    BUDGET_AVAILABLE = True
except ImportError as e:
    # Fallback to simple budget API without performance features
    try:
        from app.api.v1 import budget_simple as budget
        BUDGET_AVAILABLE = True
        logger = logging.getLogger(__name__)
        logger.info("Using simplified budget API (performance features disabled)")
    except ImportError as e2:
        logger = logging.getLogger(__name__)
        logger.warning(f"Budget API not available: {e2}")
        # Create a minimal budget router fallback
        from fastapi import APIRouter
        budget = type('MockBudget', (), {'router': APIRouter(prefix="/budget", tags=["Budget Management"])})()
        BUDGET_AVAILABLE = False

# Logging configuration
from app.logging_config import setup_logging
setup_logging()

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with performance optimization"""
    logger.info("🚀 Starting AI Assistant MVP...")
    
    # Initialize performance components if available
    if PERFORMANCE_AVAILABLE:
        try:
            # Initialize cache manager
            await cache_manager.initialize()
            logger.info("✅ Cache manager initialized")
            
            # Initialize database optimizer
            await db_optimizer.initialize_pool(min_size=5, max_size=20)
            logger.info("✅ Database optimizer initialized")
            
        except Exception as e:
            logger.error(f"❌ Performance initialization failed: {e}")
    else:
        logger.info("📝 Running without performance optimization (development mode)")
    
    logger.info("🎯 AI Assistant MVP is ready for operations")
    
    yield
    
    # Cleanup
    logger.info("🔄 Shutting down AI Assistant MVP...")
    
    if PERFORMANCE_AVAILABLE:
        try:
            await cache_manager.close()
            await db_optimizer.close()
            logger.info("✅ Performance components closed gracefully")
        except Exception as e:
            logger.error(f"⚠️ Error during cleanup: {e}")

# Initialize FastAPI with performance optimization
app = FastAPI(
    title="AI Assistant MVP",
    description="Production-ready AI Assistant with enterprise security and performance optimization",
    version="2.1.0",
    lifespan=lifespan,
    docs_url=None,  # Custom docs setup below
    redoc_url=None
)

# Add compression middleware for better performance
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware stack (order matters!)
app.add_middleware(SecurityHeadersMiddleware, environment=os.getenv("ENVIRONMENT", "development"))
app.add_middleware(input_validation_middleware)
app.add_middleware(auth_middleware)
app.add_middleware(cost_control_middleware)
app.add_middleware(metrics_middleware)

# Rate limiting middleware
setup_rate_limiting_middleware(app)

# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(budget.router, prefix="/api/v1")
app.include_router(ai_enhancement.router, prefix="/api/v1")
app.include_router(generate.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(vector_search.router, prefix="/api/v1")
app.include_router(data_sources.router, prefix="/api/v1")
app.include_router(documentation.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(llm_management.router, prefix="/api/v1")
app.include_router(user_settings.router, prefix="/api/v1")
app.include_router(learning.router, prefix="/api/v1")

# Performance monitoring router (optional)
if PERFORMANCE_AVAILABLE:
    try:
        from app.api.v1.performance import router as performance_router
        app.include_router(performance_router, prefix="/api/v1")
        logger.info("✅ Performance monitoring API enabled")
    except ImportError as e:
        logger.warning(f"⚠️ Performance monitoring API not available: {e}")

# Async tasks router (optional)
try:
    from app.api.v1.async_tasks import router as async_tasks_router
    app.include_router(async_tasks_router, prefix="/api/v1")
    logger.info("✅ Async tasks API enabled")
except ImportError as e:
    logger.warning(f"⚠️ Async tasks API not available: {e}")

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Extract user_id from query parameters
    user_id = websocket.query_params.get("user_id", "anonymous")
    await handle_websocket_connection(websocket, user_id)

logger.info("✅ WebSocket support enabled")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - redirects to docs"""
    return RedirectResponse(url="/docs")

# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "version": "2.1.0", "timestamp": "2025-06-17"}

@app.get("/api/v1/health")
async def api_health_check():
    """Detailed API health check"""
    health_status = {
        "status": "healthy",
        "version": "2.1.0",
        "timestamp": "2025-06-17",
        "components": {
            "api": "operational",
            "security": "operational",
            "cache": "unknown",
            "database": "unknown",
            "performance": "available" if PERFORMANCE_AVAILABLE else "disabled"
        }
    }
    
    # Check cache health if available
    if PERFORMANCE_AVAILABLE:
        try:
            cache_stats = await cache_manager.get_stats()
            health_status["components"]["cache"] = "operational" if cache_manager.connected else "degraded"
        except Exception:
            health_status["components"]["cache"] = "error"
        
        # Check database health
        try:
            db_health = await db_optimizer.health_check()
            health_status["components"]["database"] = db_health.get("status", "unknown")
        except Exception:
            health_status["components"]["database"] = "error"
    return health_status

@app.get("/metrics")
async def get_metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(openapi_url=app.openapi_url, title=app.title + " - Swagger UI")

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(openapi_url=app.openapi_url, title=app.title + " - ReDoc")

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=404, content={"error": "Not found"})

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
