"""
Test application entry point for AI Assistant MVP.
This is a simplified version of the main app, used for testing purposes.
"""
from fastapi import FastAPI
from app.api.v1 import auth, users, search, generate, vector_search, documentation, feedback, llm_management, learning, data_sources, budget_simple
from app.security.auth import auth_middleware
from app.security.cost_control import cost_control_middleware
from app.security.input_validation import input_validation_middleware
from app.security.security_headers import SecurityHeadersMiddleware
from app.security.rate_limiter import setup_rate_limiting_middleware
from app.monitoring.middleware import MonitoringMiddleware
from app.websocket import handle_websocket_connection

def create_test_app() -> FastAPI:
    """Creates the FastAPI application for testing."""
    app = FastAPI(title="AI Assistant Test App")

    # Add middlewares
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(MonitoringMiddleware)
    app.add_middleware(input_validation_middleware)
    app.add_middleware(auth_middleware)
    app.add_middleware(cost_control_middleware)
    setup_rate_limiting_middleware(app)

    # Include routers
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(search.router, prefix="/api/v1")
    app.include_router(generate.router, prefix="/api/v1")
    app.include_router(vector_search.router, prefix="/api/v1")
    app.include_router(documentation.router, prefix="/api/v1")
    app.include_router(feedback.router, prefix="/api/v1")
    app.include_router(llm_management.router, prefix="/api/v1")
    app.include_router(learning.router, prefix="/api/v1")
    app.include_router(data_sources.router, prefix="/api/v1")
    app.include_router(budget_simple.router, prefix="/api/v1", tags=["Budget"])

    @app.websocket("/ws/{user_id}")
    async def websocket_test_endpoint(websocket: WebSocket, user_id: str):
        await handle_websocket_connection(websocket, user_id)

    return app

app = create_test_app() 