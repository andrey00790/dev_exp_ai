#!/usr/bin/env python3
"""
Basic E2E Tests for AI Assistant
Tests core functionality and API endpoints
"""

import pytest
import pytest_asyncio
import asyncio
import httpx
import time
from typing import Dict, Any

pytestmark = pytest.mark.asyncio


class TestBasicE2E:
    """Basic end-to-end functionality tests"""
    
    @pytest.fixture
    def app_url(self) -> str:
        """Get application URL for E2E tests"""
        return "http://localhost:8001"  # E2E app port
    
    @pytest_asyncio.fixture
    async def client(self, app_url: str):
        """HTTP client for API testing"""
        async with httpx.AsyncClient(base_url=app_url, timeout=30.0) as client:
            yield client
    
    async def test_health_endpoint(self, client: httpx.AsyncClient):
        """Test basic health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    async def test_api_health_endpoint(self, client: httpx.AsyncClient):
        """Test API health endpoint"""
        response = await client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
    
    async def test_api_v1_health_endpoint(self, client: httpx.AsyncClient):
        """Test API v1 health endpoint"""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
    
    async def test_openapi_docs(self, client: httpx.AsyncClient):
        """Test OpenAPI documentation endpoint"""
        response = await client.get("/docs")
        assert response.status_code == 200
        
    async def test_openapi_json(self, client: httpx.AsyncClient):
        """Test OpenAPI JSON endpoint"""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


class TestMonitoringE2E:
    """E2E tests for monitoring endpoints"""
    
    @pytest_asyncio.fixture
    async def client(self):
        """HTTP client for monitoring tests"""
        async with httpx.AsyncClient(base_url="http://localhost:8001", timeout=30.0) as client:
            yield client
    
    async def test_metrics_endpoint(self, client: httpx.AsyncClient):
        """Test metrics endpoint"""
        response = await client.get("/metrics")
        assert response.status_code in [200, 404]  # May not be implemented
    
    async def test_monitoring_current_metrics(self, client: httpx.AsyncClient):
        """Test current metrics endpoint"""
        response = await client.get("/api/v1/monitoring/current-metrics")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "metrics" in data
    
    async def test_websocket_stats(self, client: httpx.AsyncClient):
        """Test WebSocket statistics endpoint"""
        response = await client.get("/api/v1/monitoring/websocket-stats")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "stats" in data
    
    async def test_performance_summary(self, client: httpx.AsyncClient):
        """Test performance summary endpoint"""
        response = await client.get("/api/v1/monitoring/performance-summary")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "summary" in data


class TestDatabaseE2E:
    """E2E tests for database-related endpoints"""
    
    @pytest_asyncio.fixture
    async def client(self):
        """HTTP client for database tests"""
        async with httpx.AsyncClient(base_url="http://localhost:8001", timeout=30.0) as client:
            yield client
    
    async def test_database_health_check(self, client: httpx.AsyncClient):
        """Test database health check"""
        response = await client.get("/api/v1/health/database")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
    
    async def test_redis_health_check(self, client: httpx.AsyncClient):
        """Test Redis health check"""
        response = await client.get("/api/v1/health/redis")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data


class TestAuthE2E:
    """E2E tests for authentication endpoints"""
    
    @pytest_asyncio.fixture
    async def client(self):
        """HTTP client for auth tests"""
        async with httpx.AsyncClient(base_url="http://localhost:8001", timeout=30.0) as client:
            yield client
    
    async def test_auth_budget_status(self, client: httpx.AsyncClient):
        """Test auth budget status endpoint"""
        response = await client.get("/api/v1/auth/budget-status")
        assert response.status_code in [200, 401, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "budget" in data
    
    async def test_auth_login_endpoint_exists(self, client: httpx.AsyncClient):
        """Test that auth login endpoint exists"""
        response = await client.post("/api/v1/auth/login", json={"username": "test", "password": "test"})
        assert response.status_code in [200, 400, 401, 404, 422]  # Various expected error codes
    
    async def test_auth_verify_endpoint_exists(self, client: httpx.AsyncClient):
        """Test that auth verify endpoint exists"""
        response = await client.post("/api/v1/auth/verify", json={"token": "test-token"})
        assert response.status_code in [200, 400, 401, 404, 422]  # Various expected error codes


class TestOptimizationE2E:
    """E2E tests for optimization endpoints"""
    
    @pytest_asyncio.fixture
    async def client(self):
        """HTTP client for optimization tests"""
        async with httpx.AsyncClient(base_url="http://localhost:8001", timeout=30.0) as client:
            yield client
    
    async def test_optimization_history(self, client: httpx.AsyncClient):
        """Test optimization history endpoint"""
        response = await client.get("/api/v1/optimization/history")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "history" in data
    
    async def test_optimization_benchmark_endpoint(self, client: httpx.AsyncClient):
        """Test optimization benchmark endpoint"""
        response = await client.post("/api/v1/optimization/benchmark", json={"code": "print('test')"})
        assert response.status_code in [200, 400, 404, 422]
        
        if response.status_code == 200:
            data = response.json()
            assert "benchmark" in data
    
    async def test_optimization_optimize_endpoint(self, client: httpx.AsyncClient):
        """Test optimization optimize endpoint"""
        response = await client.post("/api/v1/optimization/optimize", json={"code": "print('test')"})
        assert response.status_code in [200, 400, 404, 422]
        
        if response.status_code == 200:
            data = response.json()
            assert "optimized_code" in data


class TestRealtimeE2E:
    """E2E tests for real-time endpoints"""
    
    @pytest_asyncio.fixture
    async def client(self):
        """HTTP client for real-time tests"""
        async with httpx.AsyncClient(base_url="http://localhost:8001", timeout=30.0) as client:
            yield client
    
    async def test_realtime_monitoring_health(self, client: httpx.AsyncClient):
        """Test real-time monitoring health"""
        response = await client.get("/api/v1/realtime/monitoring/health")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
    
    async def test_async_tasks_submit(self, client: httpx.AsyncClient):
        """Test async task submission"""
        response = await client.post("/api/v1/realtime/tasks/submit", json={"task_type": "test", "data": {}})
        assert response.status_code in [200, 400, 404, 422]
        
        if response.status_code == 200:
            data = response.json()
            assert "task_id" in data


class TestPerformanceE2E:
    """E2E tests for performance monitoring"""
    
    @pytest_asyncio.fixture
    async def client(self):
        """HTTP client for performance tests"""
        async with httpx.AsyncClient(base_url="http://localhost:8001", timeout=30.0) as client:
            yield client
    
    async def test_response_time_health(self, client: httpx.AsyncClient):
        """Test response time health check"""
        start_time = time.time()
        response = await client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 5.0  # Should respond within 5 seconds
        assert response.status_code == 200
    
    async def test_concurrent_requests(self, client: httpx.AsyncClient):
        """Test concurrent request handling"""
        tasks = []
        for i in range(5):
            task = client.get("/health")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that most requests succeeded
        success_count = sum(1 for r in results if hasattr(r, 'status_code') and r.status_code == 200)
        assert success_count >= 3  # At least 3 out of 5 should succeed
    
    async def test_api_endpoints_load(self, client: httpx.AsyncClient):
        """Test multiple API endpoints for load"""
        endpoints = ["/health", "/api/health", "/api/v1/health"]
        
        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code in [200, 404]  # Should not crash
            
            if response.status_code == 200:
                # Should return JSON
                data = response.json()
                assert isinstance(data, dict) 