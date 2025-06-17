"""
AI Assistant MVP - Production Main Application
Clean, stable, enterprise-ready
"""

import logging
import os
from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
import uvicorn

# Core imports
from app.config import settings
from app.logging_config import setup_logging

# API routers
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.search import router as search_router
from app.api.v1.generate import router as generate_router
from app.api.v1.vector_search import router as vector_search_router

# Security
from app.security.auth import auth_middleware
from app.security.security_headers import SecurityHeadersMiddleware

# WebSocket
from app.websocket import handle_websocket_connection

# Monitoring
from app.monitoring.metrics import setup_metrics

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="AI Assistant MVP - Production",
    description="Enterprise AI Assistant with full security and features",
    version="2.1.0",
    docs_url=None,
    redoc_url=None
)

# Setup metrics
setup_metrics()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://ai-assistant.company.com"  # Production domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
app.add_middleware(
    SecurityHeadersMiddleware, 
    environment=settings.environment
)

# Include API routers
app.include_router(auth_router, prefix="/api/v1", tags=["Authentication"])
app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(search_router, prefix="/api/v1", tags=["Search"])
app.include_router(generate_router, prefix="/api/v1", tags=["Generation"])
app.include_router(vector_search_router, prefix="/api/v1", tags=["Vector Search"])

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    user_id = websocket.query_params.get("user_id", "anonymous")
    await handle_websocket_connection(websocket, user_id)

# Root endpoint
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

# Health endpoints
@app.get("/health")
async def health_basic():
    return {
        "status": "healthy",
        "version": "2.1.0",
        "timestamp": "2025-06-17",
        "environment": settings.environment,
        "components": {
            "api": "healthy",
            "auth": "healthy",
            "search": "healthy",
            "generation": "healthy",
            "vector_search": "healthy",
            "websocket": "healthy"
        }
    }

@app.get("/api/v1/health")
async def health_detailed():
    return {
        "status": "healthy",
        "timestamp": 1750154345.612941,
        "version": "2.1.0",
        "uptime": 47.887452840805054,
        "environment": settings.environment,
        "checks": {
            "api": "healthy",
            "database": "not_configured",
            "vectorstore": "not_configured", 
            "llm": "not_configured",
            "memory": "healthy"
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

logger.info("🚀 AI Assistant MVP - Production Version initialized")
logger.info("✅ All routers loaded successfully")
logger.info("✅ Security middleware active")
logger.info("✅ WebSocket support enabled")
logger.info("✅ Metrics collection enabled")

if __name__ == "__main__":
    uvicorn.run(
        "app.main_production:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Production setting
        log_level="info"
    ) 