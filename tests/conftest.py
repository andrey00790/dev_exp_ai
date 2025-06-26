import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, WebSocket
import asyncio
import tempfile
from unittest.mock import Mock, AsyncMock, patch

# Define a simplified app creation function directly in conftest
def create_test_app() -> FastAPI:
    """Creates a simplified FastAPI application for testing."""
    try:
        from app.api.v1 import auth, users, search, generate, vector_search, documentation, feedback, llm_management, learning, data_sources, budget_simple
        from app.api import health  # Add health router
        from app.security.auth import auth_middleware, User
        from app.security.cost_control import cost_control_middleware
        from app.security.input_validation import input_validation_middleware
        from app.security.security_headers import SecurityHeadersMiddleware
        from app.security.rate_limiter import setup_rate_limiting_middleware
        from app.monitoring.middleware import MonitoringMiddleware
        from app.websocket import handle_websocket_connection

        app = FastAPI(title="AI Assistant Test App")

        # Add middlewares
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(MonitoringMiddleware)
        # app.add_middleware(input_validation_middleware)  # Skip for testing
        app.add_middleware(auth_middleware)
        # app.add_middleware(cost_control_middleware)  # Skip for testing
        setup_rate_limiting_middleware(app)

        # Include health router first (root level)
        app.include_router(health.router)
        
        # Include v1 API routers
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
    except ImportError as e:
        print(f"Warning: Could not create full test app: {e}")
        # Return minimal app for basic testing
        app = FastAPI(title="AI Assistant Test App - Minimal")
        
        @app.get("/health")
        async def health():
            return {"status": "ok"}
            
        return app

@pytest.fixture(scope="session")
def app():
    """Создает экземпляр FastAPI приложения для тестов с отключенной аутентификацией"""
    from app.main import app
    from app.security.auth import get_current_user, get_current_admin_user
    
    # Mock функции аутентификации для тестов
    def mock_get_current_user():
        return {
            "id": "test_user_123",
            "sub": "test_user_123",
            "user_id": "test_user_123",
            "email": "test@example.com", 
            "username": "testuser",
            "full_name": "Test User",
            "is_active": True,
            "is_admin": False,
            "scopes": ["basic", "search", "generate"]
        }
    
    def mock_get_current_admin_user():
        return {
            "id": "test_admin_123",
            "sub": "test_admin_123", 
            "user_id": "test_admin_123",
            "email": "admin@example.com",
            "username": "admin", 
            "full_name": "Test Admin",
            "is_active": True,
            "is_admin": True,
            "scopes": ["basic", "admin", "search", "generate"]
        }
    
    # Переопределяем зависимости для тестов
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_current_admin_user] = mock_get_current_admin_user
    
    yield app
    
    # Очищаем переопределения после тестов
    app.dependency_overrides.clear()

@pytest.fixture
def client(app):
    """Создает тестовый клиент с отключенной аутентификацией"""
    return TestClient(app)

@pytest.fixture
def authenticated_client(app):
    """Создает аутентифицированный тестовый клиент"""
    return TestClient(app)

@pytest.fixture(autouse=True)
def reset_user_manager_state():
    """Автоматически сбрасывает состояние MockUserConfigManager между тестами"""
    try:
        from app.api.v1.users import reset_user_manager_state
        reset_user_manager_state()
    except ImportError:
        pass
    yield
    try:
        from app.api.v1.users import reset_user_manager_state
        reset_user_manager_state()
    except ImportError:
        pass

@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing."""
    mock_connection = Mock()
    mock_cursor = Mock()
    
    # Configure cursor methods
    mock_cursor.execute = Mock()
    mock_cursor.fetchone = Mock()
    mock_cursor.fetchall = Mock()
    mock_cursor.fetchmany = Mock()
    mock_cursor.close = Mock()
    
    # Configure connection methods
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.cursor.return_value.__exit__.return_value = None
    mock_connection.commit = Mock()
    mock_connection.rollback = Mock()
    mock_connection.close = Mock()
    
    return mock_connection, mock_cursor

@pytest.fixture
def mock_user_config_manager():
    """Mock UserConfigManager for testing."""
    manager = Mock()
    
    # Configure async methods
    manager.create_user_with_defaults = AsyncMock()
    manager.get_user_config = AsyncMock()
    manager.add_jira_config = AsyncMock()
    manager.add_confluence_config = AsyncMock()
    manager.add_gitlab_config = AsyncMock()
    manager.sync_user_data = AsyncMock()
    
    # Configure sync methods
    manager.get_user_by_id = Mock()
    manager.update_user = Mock()
    manager.delete_user = Mock()
    
    return manager

@pytest.fixture
def mock_encryption_manager():
    """Mock EncryptionManager for testing."""
    manager = Mock()
    manager.encrypt = Mock(return_value=b'encrypted_data')
    manager.decrypt = Mock(return_value='decrypted_data')
    return manager

@pytest.fixture
def mock_file_processor():
    """Mock FileProcessor for testing."""
    processor = Mock()
    processor.process_uploaded_file = AsyncMock()
    processor.extract_text_from_pdf = Mock()
    processor.extract_text_from_docx = Mock()
    processor.extract_text_from_txt = Mock()
    return processor

@pytest.fixture
def mock_sync_manager():
    """Mock SyncManager for testing."""
    manager = Mock()
    manager.sync_all_sources = AsyncMock()
    manager.sync_jira_data = AsyncMock()
    manager.sync_confluence_data = AsyncMock()
    manager.sync_gitlab_data = AsyncMock()
    manager.get_sync_status = Mock()
    return manager

@pytest.fixture
def temp_encryption_key():
    """Create temporary encryption key file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        # Create a valid 32-byte key
        key = b'test_encryption_key_32_bytes_long!'
        tmp_file.write(key)
        tmp_file.flush()
        yield tmp_file.name, key
    
    # Cleanup
    if os.path.exists(tmp_file.name):
        os.unlink(tmp_file.name)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def integration_services():
    """Запускает все сервисы для интеграционных тестов."""
    import subprocess
    import time
    
    print("🚀 Запуск всех сервисов для интеграционных тестов...")
    
    # Запускаем docker-compose
    try:
        subprocess.run(["docker-compose", "up", "-d", "--build"], check=True)
        time.sleep(60) # Даем время на запуск
        yield
    finally:
        print("🛑 Остановка сервисов...")
        subprocess.run(["docker-compose", "down", "--remove-orphans"])

@pytest.fixture
def mock_vector_search_service():
    """Mock VectorSearchService for testing."""
    service = Mock()
    service.search = AsyncMock(return_value=[])
    service.index_document = AsyncMock()
    service.delete_document = AsyncMock()
    service.get_stats = AsyncMock(return_value={"total_documents": 0})
    return service

@pytest.fixture
def mock_generation_service():
    """Mock GenerationService for testing."""
    service = Mock()
    service.generate_rfc = AsyncMock(return_value={"rfc_content": "Test RFC"})
    service.generate_documentation = AsyncMock()
    service.ask_clarifying_questions = AsyncMock()
    return service

@pytest.fixture
def mock_feedback_service():
    """Mock FeedbackService for testing."""
    service = Mock()
    service.submit_feedback = AsyncMock(return_value={"status": "success"})
    service.get_feedback_stats = AsyncMock()
    return service

@pytest.fixture
def mock_auth_user():
    """Mock authenticated user for testing."""
    try:
        from app.security.auth import User
        return User(
            user_id="test_user",
            email="test@example.com", 
            name="Test User",
            is_active=True,
            budget_limit=100.0,
            current_usage=0.0,
            scopes=["basic", "admin", "search", "generate"]
        )
    except ImportError:
        # Fallback mock if auth module not available
        mock_user = Mock()
        mock_user.user_id = "test_user"
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.is_active = True
        mock_user.scopes = ["basic", "admin"]
        return mock_user

# ================ TEST CONTAINERS CONFIGURATION ================

@pytest.fixture(scope="session")
def test_config():
    """Тестовая конфигурация"""
    try:
        from tests.test_config import get_test_config
        return get_test_config()
    except ImportError:
        return None

@pytest.fixture(scope="session")
def docker_available():
    """Проверяем доступность Docker"""
    try:
        from tests.test_config import is_docker_available
        return is_docker_available()
    except ImportError:
        return False

@pytest.fixture(scope="session")
def services_status():
    """Статус тестовых сервисов"""
    try:
        from tests.test_config import check_test_services
        return check_test_services()
    except ImportError:
        return {}

@pytest.fixture(scope="session")
def test_database(test_config):
    """Настройка тестовой базы данных"""
    if not test_config:
        yield None
        return
        
    try:
        from tests.test_config import setup_test_database
        engine = setup_test_database()
        yield engine
    except Exception as e:
        print(f"Warning: Could not setup test database: {e}")
        yield None

@pytest.fixture(scope="session")
def test_qdrant(test_config):
    """Настройка тестового Qdrant"""
    if not test_config:
        yield None
        return
        
    try:
        from tests.test_config import setup_test_qdrant
        client = setup_test_qdrant()
        yield client
    except Exception as e:
        print(f"Warning: Could not setup test Qdrant: {e}")
        yield None

@pytest.fixture(scope="session")
def test_redis(test_config):
    """Настройка тестового Redis"""
    if not test_config:
        yield None
        return
        
    try:
        from tests.test_config import setup_test_redis
        client = setup_test_redis()
        yield client
    except Exception as e:
        print(f"Warning: Could not setup test Redis: {e}")
        yield None

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Очистка после каждого теста"""
    yield
    # Очистка выполняется после каждого теста
    try:
        from tests.test_config import cleanup_test_environment
        cleanup_test_environment()
    except Exception:
        pass

@pytest.fixture
def mock_openai():
    """Mock OpenAI API"""
    with patch('openai.ChatCompletion.create') as mock_chat, \
         patch('openai.Embedding.create') as mock_embedding:
        
        mock_chat.return_value = {
            "choices": [{"message": {"content": "Mock response"}}],
            "usage": {"total_tokens": 100}
        }
        
        mock_embedding.return_value = {
            "data": [{"embedding": [0.1] * 1536}],
            "usage": {"total_tokens": 50}
        }
        
        yield {"chat": mock_chat, "embedding": mock_embedding}

@pytest.fixture
def mock_qdrant():
    """Mock Qdrant client"""
    with patch('qdrant_client.QdrantClient') as mock_client:
        mock_instance = Mock()
        mock_instance.search.return_value = [
            Mock(id="doc1", score=0.95, payload={"title": "Test Doc"})
        ]
        mock_instance.upsert.return_value = Mock(status="success")
        mock_client.return_value = mock_instance
        yield mock_instance