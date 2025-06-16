"""
AI Assistant MVP - Главное приложение

Комплексная платформа для автоматизации архитектурной работы с тремя ключевыми функциями:
1. 🔍 Семантический поиск по корпоративным данным
2. 📝 Генерация RFC документов с помощью AI
3. 📖 Генерация документации по коду

Архитектура:
- FastAPI backend с async/await
- PostgreSQL для метаданных
- Qdrant для векторного поиска
- Multi-LLM поддержка (OpenAI, Anthropic, Ollama)
- JWT аутентификация
- Prometheus мониторинг
- Rate limiting защита

Автор: AI Assistant Team
Версия: 4.0
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.api.v1 import health as health_v1, documents, generate, search, feedback, learning, llm_management, documentation, auth, vector_search, users, data_sources, sync, configurations
from app.config import settings
from app.security.rate_limiter import setup_rate_limiting_middleware

# Import monitoring components
try:
    from app.monitoring.metrics import (
        metrics_middleware, 
        get_metrics_handler,
        initialize_app_info
    )
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    logging.warning("Monitoring components not available. Install prometheus-client to enable metrics.")

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Управляет жизненным циклом приложения:
    - Startup: инициализация мониторинга, подключение к БД
    - Shutdown: корректное закрытие соединений и очистка ресурсов
    """
    # Startup
    logger.info(f"Starting {settings.title}...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Initialize monitoring
    if MONITORING_AVAILABLE:
        initialize_app_info(settings.version, settings.environment)
        logger.info("✅ Monitoring initialized")
    
    # Здесь можно добавить инициализацию:
    # - Подключение к базам данных
    # - Инициализация векторного хранилища
    # - Загрузка LLM моделей
    
    yield
    
    # Shutdown  
    logger.info(f"Shutting down {settings.title}...")
    # Здесь можно добавить очистку ресурсов


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Создает и настраивает основное приложение FastAPI со всеми:
    - Middleware (CORS, мониторинг, rate limiting)
    - Роутерами API endpoints
    - Документацией OpenAPI
    - Системой безопасности
    
    Returns:
        FastAPI: Настроенное приложение готовое к запуску
    """
    application = FastAPI(
        title=settings.title,
        description="AI Assistant для ускорения архитектурного дизайна и генерации стандартизированных документов",
        version=settings.version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS middleware для фронтенда
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # В продакшене указать конкретные домены
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add monitoring middleware
    if MONITORING_AVAILABLE:
        application.middleware("http")(metrics_middleware)
        logger.info("✅ Monitoring middleware added")
    
    # Setup rate limiting middleware
    setup_rate_limiting_middleware(application)
    
    # Add metrics endpoint
    if MONITORING_AVAILABLE:
        application.get("/metrics", summary="Prometheus Metrics")(get_metrics_handler())
        logger.info("✅ Metrics endpoint added: /metrics")
    
    # Базовые роутеры
    application.include_router(health.router, tags=["Health"])
    
    # Authentication endpoints
    application.include_router(
        auth.router, 
        tags=["Authentication"]
    )
    
    # API v1 routes
    application.include_router(
        health_v1.router, 
        prefix="/api/v1", 
        tags=["Health V1"]
    )
    
    # Новые роутеры для пользовательских настроек
    application.include_router(users.router, prefix="/api/v1", tags=["User Management"])
    application.include_router(data_sources.router, prefix="/api/v1", tags=["Data Sources"])
    application.include_router(sync.router, prefix="/api/v1/sync", tags=["Data Sync"])
    application.include_router(configurations.router, prefix="/api/v1", tags=["Configurations"])
    
    # Основной функционал AI Assistant
    application.include_router(
        generate.router, 
        prefix="/api/v1", 
        tags=["AI Generation"]
    )
    
    application.include_router(
        search.router, 
        prefix="/api/v1", 
        tags=["Semantic Search"]
    )
    
    # Vector search endpoints (новый семантический поиск)
    application.include_router(
        vector_search.router, 
        prefix="/api/v1", 
        tags=["Vector Search"]
    )
    
    application.include_router(
        feedback.router, 
        prefix="/api/v1", 
        tags=["Feedback System"]
    )
    
    application.include_router(
        learning.router, 
        prefix="/api/v1", 
        tags=["Learning Pipeline"]
    )
    
    application.include_router(
        llm_management.router, 
        prefix="/api/v1", 
        tags=["LLM Management"]
    )
    
    application.include_router(
        documentation.router, 
        prefix="/api/v1", 
        tags=["Code Documentation"]
    )
    
    # Старый функционал документов (для совместимости)
    application.include_router(
        documents.router, 
        prefix="/api/v1", 
        tags=["Documents (Legacy)"]
    )
    
    @application.get("/", summary="Root", description="Корневой endpoint с информацией об AI Assistant")
    async def root():
        """
        Корневой endpoint с информацией о системе.
        
        Возвращает:
        - Название и версию системы
        - Список доступных функций
        - Ссылки на документацию
        - Статус мониторинга
        """
        return {
            "name": settings.title,
            "version": settings.version,
            "description": "AI Assistant для генерации RFC документов и семантического поиска",
            "features": [
                "🤖 AI-генерация RFC документов с интерактивными вопросами",
                "🔍 Семантический поиск по корпоративным данным с Qdrant vector database",
                "📊 Система обратной связи для переобучения модели",
                "🧠 Learning Pipeline с автоматическим переобучением на фидбеке",
                "📝 AI-генерация документации по коду (README, API docs, Technical specs)",
                "🔬 Анализ кода с выявлением паттернов и проблем безопасности",
                "🔐 JWT аутентификация и авторизация с role-based доступом",
                "⚡ Rate limiting для защиты от DDoS и abuse",
                "🛡️ Input validation для предотвращения SQL injection и XSS",
                "💰 Cost control с бюджетами пользователей для LLM calls",
                "🔄 Автоматическая синхронизация с Confluence, Jira, GitLab",
                "📁 Загрузка и индексация документов (PDF, DOC, TXT и др.)",
                "👤 Пользовательские настройки источников данных",
                "🔧 Управление конфигурациями внешних систем",
                "📊 Мониторинг синхронизации в реальном времени",
                "📈 Prometheus metrics и Grafana dashboards" if MONITORING_AVAILABLE else ""
            ],
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "health": "/health",
                "api_v1": "/api/v1",
                "metrics": "/metrics" if MONITORING_AVAILABLE else None
            },
            "status": "running",
            "environment": settings.environment,
            "monitoring": MONITORING_AVAILABLE
        }
    
    logger.info("FastAPI application created successfully")
    logger.info("Available endpoints:")
    logger.info("  - Authentication: POST /api/v1/auth/login")
    logger.info("  - User Profile: GET /api/v1/auth/profile")
    logger.info("  - Budget Info: GET /api/v1/auth/budget")
    logger.info("  - User Management: POST /api/v1/users")
    logger.info("  - User Settings: GET /api/v1/users/current/settings")
    logger.info("  - Data Sources: GET /api/v1/data-sources")
    logger.info("  - Jira Config: POST /api/v1/configurations/jira")
    logger.info("  - Confluence Config: POST /api/v1/configurations/confluence")
    logger.info("  - GitLab Config: POST /api/v1/configurations/gitlab")
    logger.info("  - Sync Tasks: POST /api/v1/sync/tasks")
    logger.info("  - RFC Generation: POST /api/v1/generate")
    logger.info("  - Semantic Search: POST /api/v1/search")
    logger.info("  - Vector Search: POST /api/v1/vector-search/search")
    logger.info("  - Document Indexing: POST /api/v1/vector-search/index")
    logger.info("  - Vector Search Stats: GET /api/v1/vector-search/stats")
    logger.info("  - File Upload & Index: POST /api/v1/vector-search/upload-file")
    logger.info("  - Feedback: POST /api/v1/feedback")
    logger.info("  - Learning Pipeline: POST /api/v1/learning/feedback")
    logger.info("  - LLM Management: GET /api/v1/llm/health")
    logger.info("  - Code Documentation: POST /api/v1/documentation/generate")
    logger.info("  - Code Analysis: POST /api/v1/documentation/analyze")
    logger.info("  - Data Sources: GET /api/v1/sources")
    logger.info("  - File Upload: POST /api/v1/upload")
    if MONITORING_AVAILABLE:
        logger.info("  - Prometheus Metrics: GET /metrics")
    
    return application


app = create_app()


if __name__ == '__main__':
    import uvicorn
    
    logger.info(f"Starting server on {settings.host}:{settings.port} (reload={settings.is_development})")
    uvicorn.run(
        'app.main:app', 
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )
