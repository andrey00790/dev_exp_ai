"""
AI Assistant MVP - Working Main Application Entry Point
Minimal dependencies, maximum stability
"""

import logging
import os
from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
import uvicorn

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security middleware imports (with fallbacks)
try:
    from app.security.auth import auth_middleware
    AUTH_AVAILABLE = True
except ImportError:
    logger.warning("Auth middleware not available")
    async def auth_middleware(request, call_next):
        return await call_next(request)
    AUTH_AVAILABLE = False

try:
    from app.security.cost_control import cost_control_middleware
    COST_CONTROL_AVAILABLE = True
except ImportError:
    logger.warning("Cost control middleware not available")
    async def cost_control_middleware(request, call_next):
        return await call_next(request)
    COST_CONTROL_AVAILABLE = False

try:
    from app.security.input_validation import input_validation_middleware
    INPUT_VALIDATION_AVAILABLE = True
except ImportError:
    logger.warning("Input validation middleware not available")
    async def input_validation_middleware(request, call_next):
        return await call_next(request)
    INPUT_VALIDATION_AVAILABLE = False

try:
    from app.security.security_headers import SecurityHeadersMiddleware
    SECURITY_HEADERS_AVAILABLE = True
except ImportError:
    logger.warning("Security headers middleware not available")
    SECURITY_HEADERS_AVAILABLE = False

# WebSocket support
try:
    from app.websocket import handle_websocket_connection
    WEBSOCKET_AVAILABLE = True
except ImportError:
    logger.warning("WebSocket support not available")
    async def handle_websocket_connection(websocket: WebSocket, user_id: str):
        await websocket.accept()
        await websocket.send_text('{"error": "WebSocket handler not available"}')
        await websocket.close()
    WEBSOCKET_AVAILABLE = False

# API routers with individual fallbacks
routers = {}

# Auth router
try:
    from app.api.v1.auth import router as auth_router
    routers['auth'] = auth_router
except ImportError:
    logger.warning("Auth router not available")

# Health endpoint
try:
    from app.api.v1.health import router as health_router
    routers['health'] = health_router
except ImportError:
    from fastapi import APIRouter
    health_router = APIRouter(prefix="/health", tags=["Health"])
    
    @health_router.get("/")
    async def health_check():
        return {"status": "healthy", "version": "2.1.0"}
    
    routers['health'] = health_router

# Search router
try:
    from app.api.v1.search import router as search_router
    routers['search'] = search_router
except ImportError:
    logger.warning("Search router not available")

# Generate router  
try:
    from app.api.v1.generate import router as generate_router
    routers['generate'] = generate_router
except ImportError:
    logger.warning("Generate router not available")

# Vector search router
try:
    from app.api.v1.vector_search import router as vector_search_router
    routers['vector_search'] = vector_search_router
except ImportError:
    logger.warning("Vector search router not available")

# Initialize FastAPI
app = FastAPI(
    title="AI Assistant MVP",
    description="Working AI Assistant with security and core features",
    version="2.1.0",
    docs_url=None,
    redoc_url=None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware (with conditionals)
if SECURITY_HEADERS_AVAILABLE:
    app.add_middleware(SecurityHeadersMiddleware, environment=os.getenv("ENVIRONMENT", "development"))
    logger.info("✅ Security headers middleware added")

# Include routers
for name, router in routers.items():
    try:
        app.include_router(router, prefix="/api/v1")
        logger.info(f"✅ {name} router included")
    except Exception as e:
        logger.error(f"❌ Failed to include {name} router: {e}")

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    user_id = websocket.query_params.get("user_id", "anonymous")
    await handle_websocket_connection(websocket, user_id)

# Root endpoint
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

# Basic health check
@app.get("/health")
async def health_basic():
    return {
        "status": "healthy",
        "version": "2.1.0", 
        "timestamp": "2025-06-17",
        "components": {
            "auth": AUTH_AVAILABLE,
            "cost_control": COST_CONTROL_AVAILABLE,
            "input_validation": INPUT_VALIDATION_AVAILABLE,
            "security_headers": SECURITY_HEADERS_AVAILABLE,
            "websocket": WEBSOCKET_AVAILABLE
        },
        "routers": list(routers.keys())
    }

# Advanced health check
@app.get("/api/v1/health-detailed")
async def health_detailed():
    return {
        "status": "operational",
        "version": "2.1.0",
        "features": {
            "security": {
                "auth": AUTH_AVAILABLE,
                "cost_control": COST_CONTROL_AVAILABLE,
                "input_validation": INPUT_VALIDATION_AVAILABLE,
                "security_headers": SECURITY_HEADERS_AVAILABLE
            },
            "communication": {
                "websocket": WEBSOCKET_AVAILABLE,
                "cors": True
            },
            "api": {
                "routers_count": len(routers),
                "available_routers": list(routers.keys())
            }
        }
    }

# Custom docs endpoints
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

logger.info("🚀 AI Assistant MVP (Working Version) initialized")
logger.info(f"✅ Available routers: {list(routers.keys())}")
logger.info(f"✅ Security features: AUTH={AUTH_AVAILABLE}, COST_CONTROL={COST_CONTROL_AVAILABLE}")

if __name__ == "__main__":
    uvicorn.run(
        "app.main_working:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 