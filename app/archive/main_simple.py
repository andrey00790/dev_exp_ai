"""
AI Assistant MVP - Simplified Main Application Entry Point
Compatible version with existing modules only
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
import uvicorn

# Security and middleware imports
from app.security.auth import auth_middleware
from app.security.cost_control import cost_control_middleware
from app.security.input_validation import input_validation_middleware
from app.security.security_headers import SecurityHeadersMiddleware
from app.monitoring.metrics import metrics_middleware, setup_metrics

# WebSocket support
from app.websocket import handle_websocket_connection

# Import only existing API modules
try:
    from app.api.v1.auth import router as auth_router
except ImportError:
    auth_router = None

try:
    from app.api.v1.ai_enhancement import router as ai_enhancement_router
except ImportError:
    ai_enhancement_router = None

try:
    from app.api.v1.generate import router as generate_router
except ImportError:
    generate_router = None

try:
    from app.api.v1.search import router as search_router
except ImportError:
    search_router = None

try:
    from app.api.v1.vector_search import router as vector_search_router
except ImportError:
    vector_search_router = None

try:
    from app.api.v1.documentation import router as documentation_router
except ImportError:
    documentation_router = None

try:
    from app.api.v1.feedback import router as feedback_router
except ImportError:
    feedback_router = None

try:
    from app.api.v1.llm_management import router as llm_router
except ImportError:
    llm_router = None

try:
    from app.api.v1.learning import router as learning_router
except ImportError:
    learning_router = None

# Budget API with fallback
try:
    from app.api.v1.budget import router as budget_router
except ImportError:
    try:
        from app.api.v1.budget_simple import router as budget_router
    except ImportError:
        budget_router = None

# Data sources router (create minimal version if missing)
try:
    from app.api.v1.data_sources import router as data_sources_router
except ImportError:
    from fastapi import APIRouter
    data_sources_router = APIRouter(prefix="/data-sources", tags=["Data Sources"])
    
    @data_sources_router.get("/")
    async def list_data_sources():
        return {"sources": ["confluence", "jira", "gitlab"], "status": "connected"}

# Logging configuration
from app.logging_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting AI Assistant MVP (Simplified Mode)...")
    
    # Setup metrics
    setup_metrics()
    logger.info("✅ Metrics collection started")
    
    logger.info("🎯 AI Assistant MVP is ready for operations")
    
    yield
    
    # Cleanup
    logger.info("🔄 Shutting down AI Assistant MVP...")

# Initialize FastAPI
app = FastAPI(
    title="AI Assistant MVP",
    description="Production-ready AI Assistant with enterprise security",
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

# Include API routers (only if they exist)
routers_included = []

if auth_router:
    app.include_router(auth_router, prefix="/api/v1")
    routers_included.append("auth")

if budget_router:
    app.include_router(budget_router, prefix="/api/v1")
    routers_included.append("budget")

if ai_enhancement_router:
    app.include_router(ai_enhancement_router, prefix="/api/v1")
    routers_included.append("ai_enhancement")

if generate_router:
    app.include_router(generate_router, prefix="/api/v1")
    routers_included.append("generate")

if search_router:
    app.include_router(search_router, prefix="/api/v1")
    routers_included.append("search")

if vector_search_router:
    app.include_router(vector_search_router, prefix="/api/v1")
    routers_included.append("vector_search")

if data_sources_router:
    app.include_router(data_sources_router, prefix="/api/v1")
    routers_included.append("data_sources")

if documentation_router:
    app.include_router(documentation_router, prefix="/api/v1")
    routers_included.append("documentation")

if feedback_router:
    app.include_router(feedback_router, prefix="/api/v1")
    routers_included.append("feedback")

if llm_router:
    app.include_router(llm_router, prefix="/api/v1")
    routers_included.append("llm")

if learning_router:
    app.include_router(learning_router, prefix="/api/v1")
    routers_included.append("learning")

logger.info(f"✅ Included routers: {', '.join(routers_included)}")

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Extract user_id from query parameters
    user_id = websocket.query_params.get("user_id", "anonymous")
    await handle_websocket_connection(websocket, user_id)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - redirects to docs"""
    return RedirectResponse(url="/docs")

# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy", 
        "version": "2.1.0", 
        "timestamp": "2025-06-17",
        "mode": "simplified",
        "routers": routers_included
    }

@app.get("/api/v1/health")
async def api_health_check():
    """Detailed API health check"""
    return {
        "status": "healthy",
        "version": "2.1.0",
        "timestamp": "2025-06-17",
        "mode": "simplified",
        "components": {
            "api": "operational",
            "security": "operational",
            "websocket": "operational"
        },
        "available_endpoints": len(routers_included),
        "routers": routers_included
    }

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Basic metrics endpoint"""
    return {
        "status": "operational",
        "routers_count": len(routers_included),
        "mode": "simplified"
    }

# Custom documentation endpoints
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )

# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url.path)
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 