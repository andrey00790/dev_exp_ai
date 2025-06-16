import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch

try:
    from fastapi.testclient import TestClient
    from app.main import create_app
    _FASTAPI_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency may be missing
    _FASTAPI_AVAILABLE = False

@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    if not _FASTAPI_AVAILABLE:
        pytest.skip("FastAPI dependencies are not available")

    app = create_app()
    return TestClient(app)

@pytest.fixture
def authenticated_client():
    """Create a test client with mocked authentication."""
    if not _FASTAPI_AVAILABLE:
        pytest.skip("FastAPI dependencies are not available")

    app = create_app()
    
    # Mock the authentication dependency
    def mock_get_current_user():
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
    
    # Override the dependency
    app.dependency_overrides = {}
    
    # Import and override the auth dependency
    try:
        from app.security.auth import get_current_user
        app.dependency_overrides[get_current_user] = mock_get_current_user
    except ImportError:
        pass
    
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