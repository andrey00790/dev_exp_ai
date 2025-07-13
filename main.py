#!/usr/bin/env python3
"""
AI Assistant Application with Hexagonal Architecture

Main entry point for the AI assistant application using:
- Hexagonal architecture with clean separation of concerns
- Dependency injection for loose coupling
- Context7 frontend state management integration
- Production-ready configuration
"""

import asyncio
import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

# FastAPI and web framework imports
try:
    from fastapi import FastAPI, HTTPException, Depends
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse
    import uvicorn
except ImportError:
    print("❌ FastAPI dependencies not installed. Run: pip install fastapi uvicorn")
    sys.exit(1)

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

def setup_hexagonal_architecture() -> Dict[str, Any]:
    """
    Setup hexagonal architecture with dependency injection
    
    Returns:
        Dictionary with application components
    """
    try:
        # Import hexagonal architecture components
        from backend.infrastructure.di_container import configure_container, get_container
        from backend.infrastructure.config.di_config import detect_environment
        from backend.application.auth.services import AuthApplicationService, RoleManagementService
        from backend.presentation.auth.routes import create_auth_router
        
        # Detect environment and configure DI container
        environment = detect_environment()
        logger.info(f"🌍 Detected environment: {environment}")
        
        # Setup DI container using simple configuration
        container = configure_container(environment)
        logger.info("📦 Dependency injection container configured")
        
        # Get application services
        auth_service = container.get(AuthApplicationService)
        role_service = container.get(RoleManagementService)
        
        logger.info("✅ Hexagonal architecture initialized successfully")
        
        return {
            'container': container,
            'environment': environment,
            'auth_service': auth_service,
            'role_service': role_service
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to setup hexagonal architecture: {e}")
        raise

def create_application() -> FastAPI:
    """
    Create FastAPI application with hexagonal architecture
    
    Returns:
        Configured FastAPI application
    """
    # Initialize hexagonal architecture
    arch_components = setup_hexagonal_architecture()
    environment = arch_components['environment']
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="AI Assistant with Hexagonal Architecture",
        description="Production-ready AI assistant with clean architecture and Context7 integration",
        version="2.0.0",
        docs_url="/docs",  # Always enable docs
        redoc_url="/redoc",  # Always enable redoc
        lifespan=lifespan
    )
    
    # Configure CORS for frontend integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store architecture components in app state
    app.state.arch = arch_components
    
    # Setup routes
    setup_routes(app)
    
    # Setup middleware
    setup_middleware(app)
    
    # Setup static files for frontend
    setup_static_files(app)
    
    logger.info("🚀 FastAPI application created with hexagonal architecture")
    return app

def setup_routes(app: FastAPI) -> None:
    """Setup all application routes"""
    try:
        # Import auth routes
        from backend.presentation.auth.routes import create_auth_router
        
        # Setup auth routes
        auth_router = create_auth_router()
        app.include_router(auth_router, prefix="/api/v1/auth")
        
        # Import budget management routes
        from app.api.v1.budget_management import router as budget_router
        app.include_router(budget_router, prefix="/api/v1/budget")
        
        # Import data sync management routes
        try:
            from app.api.v1.data_sync_management import router as data_sync_router
            app.include_router(data_sync_router, prefix="/api/v1")
            logger.info("✅ Data sync management routes configured")
        except ImportError as e:
            logger.warning(f"⚠️ Data sync management not available: {e}")
        
        # Import VK Teams routes
        try:
            from infrastructure.vk_teams.presentation.bot_endpoints import router as vk_teams_bot_router
            from infrastructure.vk_teams.presentation.webhook_endpoints import router as vk_teams_webhook_router
            
            app.include_router(vk_teams_bot_router, prefix="/api/v1/vk-teams/bot")
            app.include_router(vk_teams_webhook_router, prefix="/api/v1/vk-teams/webhook")
            
            logger.info("✅ VK Teams routers configured")
        except ImportError as e:
            logger.warning(f"⚠️ VK Teams integration not available: {e}")
        
        logger.info("✅ Routes configured successfully")
        

        # Import app/api/health.py router
        try:
            from app.api.health import router as health_router
            app.include_router(health_router, )
            logger.info("✅ app/api/health.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/health.py router not available: {e}")
        

        # Import app/api/v1/ai_advanced.py router
        try:
            from app.api.v1.ai_advanced import router as ai_advanced_router
            app.include_router(ai_advanced_router, )
            logger.info("✅ app/api/v1/ai_advanced.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/ai_advanced.py router not available: {e}")
        

        # Import app/api/v1/vector_search.py router
        try:
            from app.api.v1.vector_search import router as vector_search_router
            app.include_router(vector_search_router, prefix="/vector-search")
            logger.info("✅ app/api/v1/vector_search.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/vector_search.py router not available: {e}")
        

        # Import app/api/v1/ai_analytics.py router
        try:
            from app.api.v1.ai_analytics import router as ai_analytics_router
            app.include_router(ai_analytics_router, prefix="/analytics")
            logger.info("✅ app/api/v1/ai_analytics.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/ai_analytics.py router not available: {e}")
        

        # Import app/api/v1/auth/user_settings.py router
        try:
            from app.api.v1.auth.user_settings import router as user_settings_router
            app.include_router(user_settings_router, prefix="/user-settings")
            logger.info("✅ app/api/v1/auth/user_settings.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/auth/user_settings.py router not available: {e}")
        

        # Import app/api/v1/auth/sso.py router
        try:
            from app.api.v1.auth.sso import router as sso_router
            app.include_router(sso_router, )
            logger.info("✅ app/api/v1/auth/sso.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/auth/sso.py router not available: {e}")
        

        # Import app/api/v1/search/search_advanced.py router
        try:
            from app.api.v1.search.search_advanced import router as search_advanced_router
            app.include_router(search_advanced_router, prefix="/search/advanced")
            logger.info("✅ app/api/v1/search/search_advanced.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/search/search_advanced.py router not available: {e}")
        

        # Import app/api/v1/search/qdrant_vector_search.py router
        try:
            from app.api.v1.search.qdrant_vector_search import router as qdrant_vector_search_router
            app.include_router(qdrant_vector_search_router, prefix="/qdrant")
            logger.info("✅ app/api/v1/search/qdrant_vector_search.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/search/qdrant_vector_search.py router not available: {e}")
        

        # Import app/api/v1/search/enhanced_search.py router
        try:
            from app.api.v1.search.enhanced_search import router as enhanced_search_router
            app.include_router(enhanced_search_router, prefix="/enhanced-search")
            logger.info("✅ app/api/v1/search/enhanced_search.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/search/enhanced_search.py router not available: {e}")
        

        # Import app/api/v1/ai/generate.py router
        try:
            from app.api.v1.ai.generate import router as generate_router
            app.include_router(generate_router, prefix="/generate")
            logger.info("✅ app/api/v1/ai/generate.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/ai/generate.py router not available: {e}")
        

        # Import app/api/v1/ai/bug_hotspot_detection.py router
        try:
            from app.api.v1.ai.bug_hotspot_detection import router as bug_hotspot_detection_router
            app.include_router(bug_hotspot_detection_router, prefix="/api/v1/hotspots")
            logger.info("✅ app/api/v1/ai/bug_hotspot_detection.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/ai/bug_hotspot_detection.py router not available: {e}")
        

        # Import app/api/v1/ai/ai_optimization.py router
        try:
            from app.api.v1.ai.ai_optimization import router as ai_optimization_router
            app.include_router(ai_optimization_router, prefix="/ai-optimization")
            logger.info("✅ app/api/v1/ai/ai_optimization.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/ai/ai_optimization.py router not available: {e}")
        

        # Import app/api/v1/ai/ai_code_analysis.py router
        try:
            from app.api.v1.ai.ai_code_analysis import router as ai_code_analysis_router
            app.include_router(ai_code_analysis_router, )
            logger.info("✅ app/api/v1/ai/ai_code_analysis.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/ai/ai_code_analysis.py router not available: {e}")
        

        # Import app/api/v1/ai/ai_enhancement.py router
        try:
            from app.api.v1.ai.ai_enhancement import router as ai_enhancement_router
            app.include_router(ai_enhancement_router, prefix="/ai-enhancement")
            logger.info("✅ app/api/v1/ai/ai_enhancement.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/ai/ai_enhancement.py router not available: {e}")
        

        # Import app/api/v1/ai/llm_management.py router
        try:
            from app.api.v1.ai.llm_management import router as llm_management_router
            app.include_router(llm_management_router, prefix="/llm")
            logger.info("✅ app/api/v1/ai/llm_management.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/ai/llm_management.py router not available: {e}")
        

        # Import app/api/v1/ai/learning.py router
        try:
            from app.api.v1.ai.learning import router as learning_router
            app.include_router(learning_router, prefix="/learning")
            logger.info("✅ app/api/v1/ai/learning.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/ai/learning.py router not available: {e}")
        

        # Import app/api/v1/ai/rfc_generation.py router
        try:
            from app.api.v1.ai.rfc_generation import router as rfc_generation_router
            app.include_router(rfc_generation_router, prefix="/rfc")
            logger.info("✅ app/api/v1/ai/rfc_generation.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/ai/rfc_generation.py router not available: {e}")
        

        # Import app/api/v1/ai/ai_agents.py router
        try:
            from app.api.v1.ai.ai_agents import router as ai_agents_router
            app.include_router(ai_agents_router, prefix="/api/v1/ai-agents")
            logger.info("✅ app/api/v1/ai/ai_agents.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/ai/ai_agents.py router not available: {e}")
        

        # Import app/api/v1/ai/deep_research.py router
        try:
            from app.api.v1.ai.deep_research import router as deep_research_router
            app.include_router(deep_research_router, prefix="/deep-research")
            logger.info("✅ app/api/v1/ai/deep_research.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/ai/deep_research.py router not available: {e}")
        

        # Import app/api/v1/ai/core_optimization.py router
        try:
            from app.api.v1.ai.core_optimization import router as core_optimization_router
            app.include_router(core_optimization_router, prefix="/api/v1/core-optimization")
            logger.info("✅ app/api/v1/ai/core_optimization.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/ai/core_optimization.py router not available: {e}")
        

        # Import app/api/v1/documents/documentation.py router
        try:
            from app.api.v1.documents.documentation import router as documentation_router
            app.include_router(documentation_router, )
            logger.info("✅ app/api/v1/documents/documentation.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/documents/documentation.py router not available: {e}")
        

        # Import app/api/v1/documents/documents.py router
        try:
            from app.api.v1.documents.documents import router as documents_router
            app.include_router(documents_router, )
            logger.info("✅ app/api/v1/documents/documents.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/documents/documents.py router not available: {e}")
        

        # Import app/api/v1/documents/data_sources.py router
        try:
            from app.api.v1.documents.data_sources import router as data_sources_router
            app.include_router(data_sources_router, prefix="/data-sources")
            logger.info("✅ app/api/v1/documents/data_sources.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/documents/data_sources.py router not available: {e}")
        

        # Import backend/presentation/auth/routes.py router
        try:
            from backend.presentation.auth.routes import router as routes_router
            app.include_router(routes_router, )
            logger.info("✅ backend/presentation/auth/routes.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ backend/presentation/auth/routes.py router not available: {e}")
        

        # Import app/api/v1/budget_management.py router
        try:
            from app.api.v1.budget_management import router as budget_management_router
            app.include_router(budget_management_router, prefix="/budget")
            logger.info("✅ app/api/v1/budget_management.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/budget_management.py router not available: {e}")
        

        # Import app/api/v1/realtime_monitoring.py router
        try:
            from app.api.v1.realtime_monitoring import router as realtime_monitoring_router
            app.include_router(realtime_monitoring_router, prefix="/monitoring")
            logger.info("✅ app/api/v1/realtime_monitoring.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/realtime_monitoring.py router not available: {e}")
        

        # Import app/api/v1/admin/advanced_security.py router
        try:
            from app.api.v1.admin.advanced_security import router as advanced_security_router
            app.include_router(advanced_security_router, prefix="/api/v1/security")
            logger.info("✅ app/api/v1/admin/advanced_security.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/admin/advanced_security.py router not available: {e}")
        

        # Import app/api/v1/admin/configurations.py router
        try:
            from app.api.v1.admin.configurations import router as configurations_router
            app.include_router(configurations_router, )
            logger.info("✅ app/api/v1/admin/configurations.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/admin/configurations.py router not available: {e}")
        

        # Import app/api/v1/admin/budget_simple.py router
        try:
            from app.api.v1.admin.budget_simple import router as budget_simple_router
            app.include_router(budget_simple_router, prefix="/budget")
            logger.info("✅ app/api/v1/admin/budget_simple.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/admin/budget_simple.py router not available: {e}")
        

        # Import app/api/v1/monitoring/metrics.py router
        try:
            from app.api.v1.monitoring.metrics import router as metrics_router
            app.include_router(metrics_router, )
            logger.info("✅ app/api/v1/monitoring/metrics.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/monitoring/metrics.py router not available: {e}")
        

        # Import app/api/v1/monitoring/team_performance_forecasting.py router
        try:
            from app.api.v1.monitoring.team_performance_forecasting import router as team_performance_forecasting_router
            app.include_router(team_performance_forecasting_router, prefix="/api/v1/team-performance")
            logger.info("✅ app/api/v1/monitoring/team_performance_forecasting.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/monitoring/team_performance_forecasting.py router not available: {e}")
        

        # Import app/api/v1/monitoring/performance.py router
        try:
            from app.api.v1.monitoring.performance import router as performance_router
            app.include_router(performance_router, prefix="/performance")
            logger.info("✅ app/api/v1/monitoring/performance.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/monitoring/performance.py router not available: {e}")
        

        # Import app/api/v1/monitoring/predictive_analytics.py router
        try:
            from app.api.v1.monitoring.predictive_analytics import router as predictive_analytics_router
            app.include_router(predictive_analytics_router, prefix="/api/v1/predictive-analytics")
            logger.info("✅ app/api/v1/monitoring/predictive_analytics.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/monitoring/predictive_analytics.py router not available: {e}")
        

        # Import app/api/v1/data_sync_management.py router
        try:
            from app.api.v1.data_sync_management import router as data_sync_management_router
            app.include_router(data_sync_management_router, prefix="/data-sync")
            logger.info("✅ app/api/v1/data_sync_management.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/data_sync_management.py router not available: {e}")
        

        # Import app/api/v1/datasources/datasource_endpoints.py router
        try:
            from app.api.v1.datasources.datasource_endpoints import router as datasource_endpoints_router
            app.include_router(datasource_endpoints_router, prefix="/datasources")
            logger.info("✅ app/api/v1/datasources/datasource_endpoints.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/datasources/datasource_endpoints.py router not available: {e}")
        

        # Import app/api/v1/realtime/feedback.py router
        try:
            from app.api.v1.realtime.feedback import router as feedback_router
            app.include_router(feedback_router, )
            logger.info("✅ app/api/v1/realtime/feedback.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/realtime/feedback.py router not available: {e}")
        

        # Import app/api/v1/realtime/websocket_endpoints.py router
        try:
            from app.api.v1.realtime.websocket_endpoints import router as websocket_endpoints_router
            app.include_router(websocket_endpoints_router, )
            logger.info("✅ app/api/v1/realtime/websocket_endpoints.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/realtime/websocket_endpoints.py router not available: {e}")
        

        # Import app/api/v1/realtime/enhanced_feedback.py router
        try:
            from app.api.v1.realtime.enhanced_feedback import router as enhanced_feedback_router
            app.include_router(enhanced_feedback_router, prefix="/feedback")
            logger.info("✅ app/api/v1/realtime/enhanced_feedback.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/realtime/enhanced_feedback.py router not available: {e}")
        

        # Import app/api/v1/realtime/async_tasks.py router
        try:
            from app.api.v1.realtime.async_tasks import router as async_tasks_router
            app.include_router(async_tasks_router, prefix="/async-tasks")
            logger.info("✅ app/api/v1/realtime/async_tasks.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ app/api/v1/realtime/async_tasks.py router not available: {e}")
        

        # Import infrastructure/vk_teams/presentation/webhook_endpoints.py router
        try:
            from infrastructure.vk_teams.presentation.webhook_endpoints import router as webhook_endpoints_router
            app.include_router(webhook_endpoints_router, prefix="/vk-teams/webhook")
            logger.info("✅ infrastructure/vk_teams/presentation/webhook_endpoints.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ infrastructure/vk_teams/presentation/webhook_endpoints.py router not available: {e}")
        

        # Import infrastructure/vk_teams/presentation/bot_endpoints.py router
        try:
            from infrastructure.vk_teams.presentation.bot_endpoints import router as bot_endpoints_router
            app.include_router(bot_endpoints_router, prefix="/vk-teams/bot")
            logger.info("✅ infrastructure/vk_teams/presentation/bot_endpoints.py router configured")
        except ImportError as e:
            logger.warning(f"⚠️ infrastructure/vk_teams/presentation/bot_endpoints.py router not available: {e}")
        
    except Exception as e:
        logger.error(f"❌ Failed to setup routes: {e}")
        raise

def setup_middleware(app: FastAPI) -> None:
    """Setup application middleware"""
    try:
        # Try to import custom middleware (may not exist yet)
        # from backend.presentation.middleware.auth import AuthMiddleware
        # from backend.presentation.middleware.performance import PerformanceMiddleware
        
        # Add custom middleware when available
        # app.add_middleware(PerformanceMiddleware)
        # app.add_middleware(AuthMiddleware)
        
        logger.info("✅ Basic middleware configured successfully")
        
    except ImportError:
        logger.warning("⚠️  Custom middleware not available, using basic setup")
    except Exception as e:
        logger.error(f"❌ Failed to setup middleware: {e}")

def setup_static_files(app: FastAPI) -> None:
    """Setup static file serving for frontend"""
    try:
        # Mount frontend build directory
        frontend_build = project_root / "frontend" / "build"
        if frontend_build.exists():
            app.mount("/static", StaticFiles(directory=frontend_build / "static"), name="static")
            
            # Serve React app
            @app.get("/app/{path:path}")
            async def serve_frontend(path: str):
                """Serve React frontend"""
                index_file = frontend_build / "index.html"
                if index_file.exists():
                    with open(index_file, 'r') as f:
                        return HTMLResponse(content=f.read())
                return HTMLResponse(content="<h1>Frontend not built</h1>")
            
            logger.info("✅ Frontend static files configured")
        else:
            logger.warning("⚠️  Frontend build directory not found")
            
    except Exception as e:
        logger.error(f"❌ Failed to setup static files: {e}")

def setup_websocket_handlers(app: FastAPI) -> None:
    """Setup WebSocket handlers for real-time features"""
    try:
        from fastapi import WebSocket, WebSocketDisconnect
        
        # Simple connection manager
        class ConnectionManager:
            def __init__(self):
                self.active_connections: dict = {}
                
            async def connect(self, websocket: WebSocket, user_id: str):
                await websocket.accept()
                self.active_connections[user_id] = websocket
                
            def disconnect(self, user_id: str):
                if user_id in self.active_connections:
                    del self.active_connections[user_id]
                    
            async def send_personal_message(self, message: str, user_id: str):
                if user_id in self.active_connections:
                    await self.active_connections[user_id].send_text(message)
        
        manager = ConnectionManager()
        app.state.websocket_manager = manager # Store manager in app state
        
        @app.websocket("/ws/{user_id}")
        async def websocket_endpoint(websocket: WebSocket, user_id: str):
            """WebSocket endpoint for real-time communication"""
            await manager.connect(websocket, user_id)
            try:
                while True:
                    data = await websocket.receive_text()
                    await manager.send_personal_message(f"Echo: {data}", user_id)
            except WebSocketDisconnect:
                manager.disconnect(user_id)
        
        logger.info("✅ WebSocket handlers configured")
        
    except ImportError:
        logger.warning("⚠️  WebSocket handlers not available")
    except Exception as e:
        logger.error(f"❌ Failed to setup WebSocket handlers: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("🏁 Executing startup tasks...")
    
    try:
        # Database initialization
        try:
            from backend.infrastructure.database.init import initialize_database
            await initialize_database()
            logger.info("✅ Database initialized")
        except ImportError:
            logger.info("ℹ️  Database initialization not available")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            
        # Budget service initialization
        try:
            from app.services.budget_service import init_budget_service
            await init_budget_service()
            logger.info("✅ Budget service initialized")
        except Exception as e:
            logger.error(f"❌ Budget service initialization failed: {e}")
            
        # Data sync scheduler initialization
        try:
            from app.services.data_sync_scheduler_service import init_data_sync_scheduler
            data_sync_scheduler = await init_data_sync_scheduler()
            
            # Store scheduler in app state for shutdown
            app.state.data_sync_scheduler = data_sync_scheduler
            
            logger.info("✅ Data sync scheduler initialized")
            logger.info("🔄 Confluence, GitLab, Jira and local files sync scheduler started")
            
            # Выводим расписание
            status = data_sync_scheduler.get_sync_status()
            if status['next_runs']:
                logger.info("📅 Next scheduled syncs:")
                for run in status['next_runs'][:5]:  # Показываем первые 5
                    logger.info(f"   - {run['job_name']}: {run['next_run']}")
            else:
                logger.info("📅 No scheduled syncs configured")
            
        except Exception as e:
            logger.error(f"❌ Data sync scheduler initialization failed: {e}")
            logger.warning("⚠️  Continuing without data sync scheduler")
            app.state.data_sync_scheduler = None
            
    except Exception as e:
        logger.error(f"❌ Lifespan startup failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Executing shutdown tasks...")
    try:
        # Stop budget service
        try:
            from app.services.budget_service import budget_service
            await budget_service.stop_auto_refill_scheduler()
            logger.info("✅ Budget service stopped")
        except Exception as e:
            logger.error(f"❌ Budget service shutdown failed: {e}")
            
        # Stop data sync scheduler
        try:
            if hasattr(app.state, 'data_sync_scheduler') and app.state.data_sync_scheduler:
                await app.state.data_sync_scheduler.shutdown()
                logger.info("✅ Data sync scheduler stopped")
        except Exception as e:
            logger.error(f"❌ Data sync scheduler shutdown failed: {e}")
            
        # Cleanup tasks
        logger.info("✅ Cleanup completed")
    except Exception as e:
        logger.error(f"❌ Shutdown task failed: {e}")

# Create the application
try:
    app = create_application()
    
    # Setup WebSocket handlers
    setup_websocket_handlers(app)
    
except Exception as e:
    logger.error(f"❌ Failed to create application: {e}")
    sys.exit(1)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Assistant with Hexagonal Architecture")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--demo", action="store_true", help="Run architecture demonstration")
    
    args = parser.parse_args()
    
    if args.demo:
        # Run architecture demo
        print("🎬 Starting Architecture Demonstration...")
        import subprocess
        subprocess.run([sys.executable, "demo_hexagonal_architecture.py"])
        return
    
    # Print startup banner
    print("""
╔══════════════════════════════════════════════════════════════╗
║           AI ASSISTANT - HEXAGONAL ARCHITECTURE             ║
║                    Production Ready v2.0.0                  ║
╠══════════════════════════════════════════════════════════════╣
║  🏗️  Clean Architecture                                     ║
║  📦 Dependency Injection                                    ║
║  ⚛️  Context7 State Management                             ║
║  🚀 Production Optimized                                    ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    environment = app.state.arch['environment']
    logger.info(f"🌍 Environment: {environment}")
    logger.info(f"🌐 Server: http://{args.host}:{args.port}")
    logger.info(f"📚 API Docs: http://{args.host}:{args.port}/docs")
    logger.info(f"💊 Health Check: http://{args.host}:{args.port}/health")
    
    # Run the server
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload and environment == "development",
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main() 