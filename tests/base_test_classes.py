"""
Base Test Classes for Test Pyramid Structure

Provides common functionality for different test levels:
- BaseUnitTest: For isolated unit tests with mocks
- BaseIntegrationTest: For integration tests with real dependencies
- BaseE2ETest: For end-to-end tests with full application
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseUnitTest(ABC):
    """
    Base class for unit tests.
    
    Characteristics:
    - Fast execution (<1 second per test)
    - All external dependencies mocked
    - Tests isolated business logic
    - No database, no network calls
    """
    
    @pytest.fixture(autouse=True)
    def setup_unit_test(self):
        """Setup common mocks for unit tests"""
        # Mock external dependencies
        self.mock_patches = []
        
        # Common mocks
        self.mock_db = Mock()
        self.mock_redis = Mock()
        self.mock_llm_service = AsyncMock()
        self.mock_vector_search = AsyncMock()
        
        # Setup return values
        self.mock_llm_service.generate_response.return_value = "Mock LLM response"
        self.mock_vector_search.search.return_value = []
        
        logger.info("Unit test setup completed")
        yield
        
        # Cleanup
        for patch_obj in self.mock_patches:
            patch_obj.stop()
        logger.info("Unit test cleanup completed")
    
    def create_mock_user(self, user_id: str = "test_user") -> Dict[str, Any]:
        """Create a mock user for testing"""
        return {
            "id": user_id,
            "email": f"{user_id}@example.com",
            "username": user_id,
            "is_active": True,
            "is_admin": False,
            "scopes": ["basic", "search"]
        }
    
    def create_mock_document(self, doc_id: str = "test_doc") -> Dict[str, Any]:
        """Create a mock document for testing"""
        return {
            "id": doc_id,
            "title": f"Test Document {doc_id}",
            "content": f"Test content for {doc_id}",
            "source": "test",
            "created_at": "2024-01-01T00:00:00Z"
        }
    
    def assert_mock_called_with_timeout(self, mock_func, timeout: float = 1.0):
        """Assert mock was called within timeout"""
        import time
        start_time = time.time()
        while time.time() - start_time < timeout:
            if mock_func.called:
                return True
            time.sleep(0.1)
        raise AssertionError(f"Mock {mock_func} was not called within {timeout}s")


class BaseIntegrationTest(ABC):
    """
    Base class for integration tests.
    
    Characteristics:
    - Medium execution time (1-10 seconds per test)
    - Real database connections
    - External service integrations
    - Limited scope (single module integration)
    """
    
    @pytest.fixture(autouse=True)
    def setup_integration_test(self):
        """Setup integration test environment"""
        # Use test database
        self.test_db_url = "sqlite:///test_integration.db"
        
        # Real connections but limited scope
        self.db_session = None
        self.redis_client = None
        
        logger.info("Integration test setup completed")
        yield
        
        # Cleanup
        if self.db_session:
            self.db_session.close()
        if self.redis_client:
            self.redis_client.close()
        logger.info("Integration test cleanup completed")
    
    async def setup_test_database(self):
        """Setup test database with schema"""
        # This would create test tables
        pass
    
    async def cleanup_test_database(self):
        """Cleanup test database"""
        # This would drop test tables
        pass
    
    def create_test_data(self, count: int = 5) -> List[Dict[str, Any]]:
        """Create test data for integration tests"""
        return [
            {
                "id": f"test_{i}",
                "title": f"Test Document {i}",
                "content": f"Test content {i}",
                "source": "test_integration"
            }
            for i in range(count)
        ]
    
    def assert_database_state(self, expected_count: int, table_name: str = "documents"):
        """Assert database state"""
        # This would check actual database state
        pass


class BaseE2ETest(ABC):
    """
    Base class for end-to-end tests.
    
    Characteristics:
    - Slow execution (>10 seconds per test)
    - Full application stack
    - Real user scenarios
    - HTTP API testing
    """
    
    @pytest.fixture(autouse=True)
    def setup_e2e_test(self):
        """Setup E2E test environment"""
        # Full application setup
        self.client = None
        self.auth_headers = {}
        
        logger.info("E2E test setup completed")
        yield
        
        # Cleanup
        if self.client:
            self.client.close()
        logger.info("E2E test cleanup completed")
    
    def get_test_client(self) -> TestClient:
        """Get test client with full app"""
        if not self.client:
            try:
                from main import app
                self.client = TestClient(app)
            except ImportError:
                # Fallback to mock app
                from tests.conftest import create_test_app
                self.client = TestClient(create_test_app())
        return self.client
    
    def authenticate_user(self, user_type: str = "user") -> Dict[str, str]:
        """Authenticate user and return headers"""
        if user_type == "admin":
            token = "test_admin_token"
        else:
            token = "test_user_token"
        
        self.auth_headers = {"Authorization": f"Bearer {token}"}
        return self.auth_headers
    
    def make_authenticated_request(self, method: str, url: str, **kwargs) -> Any:
        """Make authenticated HTTP request"""
        client = self.get_test_client()
        kwargs.setdefault("headers", {}).update(self.auth_headers)
        
        if method.upper() == "GET":
            return client.get(url, **kwargs)
        elif method.upper() == "POST":
            return client.post(url, **kwargs)
        elif method.upper() == "PUT":
            return client.put(url, **kwargs)
        elif method.upper() == "DELETE":
            return client.delete(url, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    
    def assert_response_success(self, response, expected_status: int = 200):
        """Assert response is successful"""
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"
    
    def assert_response_error(self, response, expected_status: int = 400):
        """Assert response is error"""
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"
    
    def run_user_journey(self, steps: List[Dict[str, Any]]) -> List[Any]:
        """Run a complete user journey"""
        results = []
        
        for step in steps:
            method = step["method"]
            url = step["url"]
            expected_status = step.get("expected_status", 200)
            
            response = self.make_authenticated_request(method, url, **step.get("kwargs", {}))
            
            if expected_status:
                self.assert_response_success(response, expected_status)
            
            results.append(response)
        
        return results


class BasePerformanceTest(ABC):
    """
    Base class for performance tests.
    
    Characteristics:
    - Measure execution time
    - Memory usage tracking
    - Load testing capabilities
    - Performance regression detection
    """
    
    @pytest.fixture(autouse=True)
    def setup_performance_test(self):
        """Setup performance test environment"""
        import time
        import psutil
        
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss
        
        logger.info("Performance test setup completed")
        yield
        
        # Cleanup and measurements
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        self.execution_time = end_time - self.start_time
        self.memory_usage = end_memory - self.start_memory
        
        logger.info(f"Performance test completed: {self.execution_time:.2f}s, {self.memory_usage/1024/1024:.2f}MB")
    
    def assert_performance_benchmark(self, max_time: float = 10.0, max_memory_mb: float = 100.0):
        """Assert performance benchmarks"""
        assert self.execution_time <= max_time, f"Test took {self.execution_time:.2f}s, expected <{max_time}s"
        
        memory_mb = self.memory_usage / 1024 / 1024
        assert memory_mb <= max_memory_mb, f"Test used {memory_mb:.2f}MB, expected <{max_memory_mb}MB"
    
    def measure_operation(self, operation_func, *args, **kwargs):
        """Measure operation performance"""
        import time
        
        start_time = time.time()
        result = operation_func(*args, **kwargs)
        end_time = time.time()
        
        return result, end_time - start_time


# Utility functions for test classification
def is_unit_test(test_class) -> bool:
    """Check if test class is a unit test"""
    return issubclass(test_class, BaseUnitTest)


def is_integration_test(test_class) -> bool:
    """Check if test class is an integration test"""
    return issubclass(test_class, BaseIntegrationTest)


def is_e2e_test(test_class) -> bool:
    """Check if test class is an E2E test"""
    return issubclass(test_class, BaseE2ETest)


def is_performance_test(test_class) -> bool:
    """Check if test class is a performance test"""
    return issubclass(test_class, BasePerformanceTest)


# Pytest markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.performance = pytest.mark.performance
pytest.mark.slow = pytest.mark.slow 