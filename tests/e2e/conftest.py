#!/usr/bin/env python3
"""
E2E Test Configuration and Fixtures
"""

import pytest
import asyncio
import httpx
import time
import os
from typing import AsyncGenerator
from pathlib import Path


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def e2e_app_url() -> str:
    """Get E2E application URL"""
    return os.getenv("E2E_APP_URL", "http://localhost:8001")


@pytest.fixture(scope="session")
async def e2e_client(e2e_app_url: str) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Shared HTTP client for E2E tests"""
    async with httpx.AsyncClient(
        base_url=e2e_app_url,
        timeout=30.0,
        follow_redirects=True
    ) as client:
        yield client


@pytest.fixture(scope="session")
async def wait_for_services(e2e_client: httpx.AsyncClient):
    """Wait for all services to be ready before running tests"""
    print("\n🔄 Waiting for services to be ready...")
    
    max_wait = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = await e2e_client.get("/health")
            if response.status_code == 200:
                print("✅ Services are ready!")
                return
        except Exception as e:
            print(f"⏳ Waiting for services... ({e})")
        
        await asyncio.sleep(5)
    
    raise TimeoutError("Services did not become ready within timeout period")


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Get test data directory path"""
    return Path(__file__).parent.parent.parent / "test-data"


@pytest.fixture(scope="session")
def e2e_config():
    """E2E test configuration"""
    return {
        "app_url": os.getenv("E2E_APP_URL", "http://localhost:8001"),
        "jira_url": os.getenv("E2E_JIRA_URL", "http://localhost:8082"),
        "confluence_url": os.getenv("E2E_CONFLUENCE_URL", "http://localhost:8083"),
        "gitlab_url": os.getenv("E2E_GITLAB_URL", "http://localhost:8084"),
        "timeout": 30.0,
        "max_retries": 3,
        "retry_delay": 2.0
    }


@pytest.fixture
async def authenticated_client(e2e_client: httpx.AsyncClient):
    """Client with authentication token"""
    # For now, just return the base client
    # In the future, implement proper authentication
    return e2e_client


@pytest.fixture
def performance_threshold():
    """Performance thresholds for E2E tests"""
    return {
        "max_response_time": 2.0,  # seconds
        "max_concurrent_requests": 50,
        "min_success_rate": 0.95,  # 95%
        "max_error_rate": 0.05     # 5%
    }


# Pytest markers
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.slow = pytest.mark.slow
pytest.mark.integration = pytest.mark.integration 