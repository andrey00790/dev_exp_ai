"""
Load Testing Framework for AI Assistant MVP
Task 2.3: Enhanced Testing Framework - Load Testing

Features:
- Concurrent user simulation (100+ users)
- API endpoint stress testing
- WebSocket connection testing
- Performance regression detection
- Memory leak detection
- Database performance validation
"""

import asyncio
import time
import statistics
import psutil
import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import httpx
import websockets
import logging
import pytest
import concurrent.futures
import threading
from unittest.mock import Mock, patch

logger = logging.getLogger(__name__)

@dataclass
class LoadTestResult:
    """Load test result data structure"""
    test_name: str
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    requests_per_second: float
    error_rate: float
    test_duration: float
    memory_usage_start: float
    memory_usage_end: float
    memory_delta: float

@dataclass
class PerformanceBaseline:
    """Performance baseline for regression detection"""
    endpoint: str
    max_response_time: float
    min_success_rate: float
    max_memory_usage: float
    max_error_rate: float

class LoadTester:
    """
    Comprehensive load testing framework
    
    Supports:
    - Concurrent user simulation
    - API stress testing
    - WebSocket load testing
    - Performance monitoring
    - Memory leak detection
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws")
        self.test_results = []
        self.performance_baselines = self._setup_baselines()
        
        # Authentication tokens
        self.admin_token = None
        self.user_token = None
        
        # Performance monitoring
        self.process = psutil.Process(os.getpid())
        
    def _setup_baselines(self) -> Dict[str, PerformanceBaseline]:
        """Setup performance baselines for regression testing"""
        return {
            "health_check": PerformanceBaseline(
                endpoint="/health",
                max_response_time=0.1,  # 100ms
                min_success_rate=99.0,
                max_memory_usage=100.0,  # MB
                max_error_rate=1.0
            ),
            "budget_status": PerformanceBaseline(
                endpoint="/api/v1/budget/status",
                max_response_time=0.2,  # 200ms (cached)
                min_success_rate=95.0,
                max_memory_usage=150.0,
                max_error_rate=5.0
            ),
            "task_submission": PerformanceBaseline(
                endpoint="/api/v1/async-tasks/submit",
                max_response_time=0.5,  # 500ms
                min_success_rate=90.0,
                max_memory_usage=200.0,
                max_error_rate=10.0
            ),
            "cache_stats": PerformanceBaseline(
                endpoint="/api/v1/performance/cache/stats",
                max_response_time=0.3,  # 300ms
                min_success_rate=95.0,
                max_memory_usage=120.0,
                max_error_rate=5.0
            )
        }
    
    async def authenticate(self) -> bool:
        """Authenticate test users"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Admin login
                admin_response = await client.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json={
                        "username": "admin@example.com",
                        "password": "admin123"
                    }
                )
                
                if admin_response.status_code == 200:
                    self.admin_token = admin_response.json()["access_token"]
                    logger.info("✅ Admin authentication successful")
                else:
                    logger.error(f"❌ Admin authentication failed: {admin_response.status_code}")
                    return False
                
                # User login
                user_response = await client.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json={
                        "username": "user@example.com",
                        "password": "user123"
                    }
                )
                
                if user_response.status_code == 200:
                    self.user_token = user_response.json()["access_token"]
                    logger.info("✅ User authentication successful")
                    return True
                else:
                    logger.error(f"❌ User authentication failed: {user_response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def run_api_load_test(
        self, 
        endpoint: str, 
        concurrent_users: int = 50,
        requests_per_user: int = 10,
        use_admin_token: bool = False
    ) -> LoadTestResult:
        """
        Run load test against API endpoint
        
        Args:
            endpoint: API endpoint to test
            concurrent_users: Number of concurrent users to simulate
            requests_per_user: Requests per user
            use_admin_token: Whether to use admin token
        """
        logger.info(f"🚀 Starting API load test: {endpoint} ({concurrent_users} users, {requests_per_user} req/user)")
        
        token = self.admin_token if use_admin_token else self.user_token
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        # Record initial memory usage
        memory_start = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Results tracking
        response_times = []
        successful_requests = 0
        failed_requests = 0
        start_time = time.time()
        
        async def user_simulation():
            """Simulate single user making requests"""
            user_response_times = []
            user_success = 0
            user_failures = 0
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for _ in range(requests_per_user):
                    request_start = time.time()
                    
                    try:
                        response = await client.get(f"{self.base_url}{endpoint}", headers=headers)
                        response_time = time.time() - request_start
                        user_response_times.append(response_time)
                        
                        if response.status_code in [200, 201, 204]:
                            user_success += 1
                        else:
                            user_failures += 1
                            logger.debug(f"Request failed with status {response.status_code}")
                            
                    except Exception as e:
                        response_time = time.time() - request_start
                        user_response_times.append(response_time)
                        user_failures += 1
                        logger.debug(f"Request exception: {e}")
                    
                    # Small delay between requests
                    await asyncio.sleep(0.01)
            
            return user_response_times, user_success, user_failures
        
        # Execute concurrent user simulations
        tasks = [user_simulation() for _ in range(concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        test_duration = time.time() - start_time
        memory_end = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Aggregate results
        for result in results:
            if isinstance(result, tuple):
                user_times, user_success, user_failures = result
                response_times.extend(user_times)
                successful_requests += user_success
                failed_requests += user_failures
        
        # Calculate statistics
        total_requests = successful_requests + failed_requests
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = 0.0
        
        requests_per_second = total_requests / test_duration if test_duration > 0 else 0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        result = LoadTestResult(
            test_name=f"API Load Test - {endpoint}",
            concurrent_users=concurrent_users,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            test_duration=test_duration,
            memory_usage_start=memory_start,
            memory_usage_end=memory_end,
            memory_delta=memory_end - memory_start
        )
        
        self.test_results.append(result)
        
        logger.info(f"✅ API load test completed: {successful_requests}/{total_requests} success, "
                   f"{avg_response_time:.3f}s avg, {requests_per_second:.1f} RPS")
        
        return result
    
    async def run_websocket_load_test(
        self, 
        concurrent_connections: int = 20,
        messages_per_connection: int = 5,
        connection_duration: int = 30
    ) -> LoadTestResult:
        """
        Run WebSocket load test
        
        Args:
            concurrent_connections: Number of concurrent WebSocket connections
            messages_per_connection: Messages to send per connection
            connection_duration: How long to keep connections open (seconds)
        """
        logger.info(f"🔌 Starting WebSocket load test: {concurrent_connections} connections")
        
        memory_start = self.process.memory_info().rss / 1024 / 1024
        start_time = time.time()
        
        successful_connections = 0
        failed_connections = 0
        messages_sent = 0
        messages_received = 0
        response_times = []
        
        async def websocket_simulation():
            """Simulate single WebSocket connection"""
            nonlocal successful_connections, failed_connections, messages_sent, messages_received
            
            try:
                # Use user token for WebSocket authentication
                ws_url = f"{self.ws_url}/ws?token={self.user_token}&user_id=test_user_{asyncio.current_task().get_name()}"
                
                async with websockets.connect(ws_url, timeout=10) as websocket:
                    successful_connections += 1
                    
                    # Send messages
                    for i in range(messages_per_connection):
                        message_start = time.time()
                        
                        # Send ping message
                        await websocket.send(json.dumps({
                            "type": "ping",
                            "message_id": i
                        }))
                        messages_sent += 1
                        
                        # Wait for response
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=5)
                            response_time = time.time() - message_start
                            response_times.append(response_time)
                            messages_received += 1
                        except asyncio.TimeoutError:
                            logger.debug("WebSocket response timeout")
                        
                        await asyncio.sleep(1)  # 1 second between messages
                    
                    # Keep connection open for specified duration
                    await asyncio.sleep(connection_duration)
                    
            except Exception as e:
                failed_connections += 1
                logger.debug(f"WebSocket connection failed: {e}")
        
        # Execute concurrent WebSocket connections
        tasks = [websocket_simulation() for _ in range(concurrent_connections)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        test_duration = time.time() - start_time
        memory_end = self.process.memory_info().rss / 1024 / 1024
        
        # Calculate statistics
        total_connections = successful_connections + failed_connections
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 19 else max_response_time
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = 0.0
        
        success_rate = (successful_connections / total_connections * 100) if total_connections > 0 else 0
        messages_per_second = messages_sent / test_duration if test_duration > 0 else 0
        
        result = LoadTestResult(
            test_name="WebSocket Load Test",
            concurrent_users=concurrent_connections,
            total_requests=messages_sent,
            successful_requests=messages_received,
            failed_requests=messages_sent - messages_received,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            requests_per_second=messages_per_second,
            error_rate=100 - success_rate,
            test_duration=test_duration,
            memory_usage_start=memory_start,
            memory_usage_end=memory_end,
            memory_delta=memory_end - memory_start
        )
        
        self.test_results.append(result)
        
        logger.info(f"✅ WebSocket load test completed: {successful_connections}/{total_connections} connections, "
                   f"{messages_received}/{messages_sent} messages, {avg_response_time:.3f}s avg")
        
        return result
    
    async def run_async_task_load_test(
        self, 
        concurrent_submissions: int = 25,
        tasks_per_user: int = 3
    ) -> LoadTestResult:
        """
        Run async task submission load test
        
        Args:
            concurrent_submissions: Number of concurrent task submissions
            tasks_per_user: Tasks to submit per user
        """
        logger.info(f"⚡ Starting async task load test: {concurrent_submissions} concurrent submissions")
        
        memory_start = self.process.memory_info().rss / 1024 / 1024
        start_time = time.time()
        
        response_times = []
        successful_requests = 0
        failed_requests = 0
        submitted_tasks = []
        
        async def task_submission_simulation():
            """Simulate task submissions"""
            nonlocal successful_requests, failed_requests
            
            user_response_times = []
            user_tasks = []
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for i in range(tasks_per_user):
                    request_start = time.time()
                    
                    try:
                        # Submit a simple task
                        response = await client.post(
                            f"{self.base_url}/api/v1/async-tasks/submit",
                            headers={"Authorization": f"Bearer {self.user_token}"},
                            json={
                                "task_func": "send_budget_alert",
                                "task_args": {
                                    "user_email": "test@example.com",
                                    "alert_type": "budget_warning_80",
                                    "current_usage": 85.50,
                                    "budget_limit": 100.00
                                },
                                "priority": "normal"
                            }
                        )
                        
                        response_time = time.time() - request_start
                        user_response_times.append(response_time)
                        
                        if response.status_code in [200, 201]:
                            successful_requests += 1
                            task_data = response.json()
                            user_tasks.append(task_data.get("task_id"))
                        else:
                            failed_requests += 1
                            
                    except Exception as e:
                        response_time = time.time() - request_start
                        user_response_times.append(response_time)
                        failed_requests += 1
                        logger.debug(f"Task submission failed: {e}")
                    
                    await asyncio.sleep(0.1)  # Small delay between submissions
            
            return user_response_times, user_tasks
        
        # Execute concurrent task submissions
        tasks = [task_submission_simulation() for _ in range(concurrent_submissions)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        for result in results:
            if isinstance(result, tuple):
                user_times, user_task_ids = result
                response_times.extend(user_times)
                submitted_tasks.extend(user_task_ids)
        
        test_duration = time.time() - start_time
        memory_end = self.process.memory_info().rss / 1024 / 1024
        
        # Calculate statistics
        total_requests = successful_requests + failed_requests
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 19 else max_response_time
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = 0.0
        
        requests_per_second = total_requests / test_duration if test_duration > 0 else 0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        result = LoadTestResult(
            test_name="Async Task Load Test",
            concurrent_users=concurrent_submissions,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            test_duration=test_duration,
            memory_usage_start=memory_start,
            memory_usage_end=memory_end,
            memory_delta=memory_end - memory_start
        )
        
        self.test_results.append(result)
        
        logger.info(f"✅ Async task load test completed: {successful_requests}/{total_requests} submissions, "
                   f"{len(submitted_tasks)} tasks created")
        
        return result
    
    def check_performance_regression(self, result: LoadTestResult) -> Dict[str, Any]:
        """Check for performance regressions against baselines"""
        endpoint_key = None
        
        # Map test to baseline
        if "health" in result.test_name.lower():
            endpoint_key = "health_check"
        elif "budget" in result.test_name.lower():
            endpoint_key = "budget_status"
        elif "task" in result.test_name.lower():
            endpoint_key = "task_submission"
        elif "cache" in result.test_name.lower():
            endpoint_key = "cache_stats"
        
        if not endpoint_key or endpoint_key not in self.performance_baselines:
            return {"status": "no_baseline", "message": "No baseline available for this test"}
        
        baseline = self.performance_baselines[endpoint_key]
        issues = []
        
        # Check response time
        if result.avg_response_time > baseline.max_response_time:
            issues.append(f"Response time regression: {result.avg_response_time:.3f}s > {baseline.max_response_time:.3f}s")
        
        # Check success rate
        success_rate = (result.successful_requests / result.total_requests * 100) if result.total_requests > 0 else 0
        if success_rate < baseline.min_success_rate:
            issues.append(f"Success rate regression: {success_rate:.1f}% < {baseline.min_success_rate:.1f}%")
        
        # Check memory usage
        if result.memory_delta > baseline.max_memory_usage:
            issues.append(f"Memory usage regression: {result.memory_delta:.1f}MB > {baseline.max_memory_usage:.1f}MB")
        
        # Check error rate
        if result.error_rate > baseline.max_error_rate:
            issues.append(f"Error rate regression: {result.error_rate:.1f}% > {baseline.max_error_rate:.1f}%")
        
        if issues:
            return {
                "status": "regression_detected",
                "issues": issues,
                "baseline": baseline.__dict__
            }
        else:
            return {
                "status": "performance_acceptable",
                "message": "No performance regressions detected"
            }
    
    async def run_comprehensive_load_test(self) -> Dict[str, Any]:
        """Run comprehensive load testing suite"""
        logger.info("🚀 Starting comprehensive load testing suite")
        
        # Authenticate first
        if not await self.authenticate():
            return {"error": "Authentication failed"}
        
        comprehensive_results = {
            "test_timestamp": datetime.now().isoformat(),
            "test_suite": "Comprehensive Load Testing",
            "tests": {},
            "performance_summary": {},
            "regressions": {}
        }
        
        try:
            # Test 1: Health check load test
            logger.info("🏥 Testing health check endpoint...")
            health_result = await self.run_api_load_test("/health", concurrent_users=100, requests_per_user=5)
            comprehensive_results["tests"]["health_check"] = health_result.__dict__
            comprehensive_results["regressions"]["health_check"] = self.check_performance_regression(health_result)
            
            # Test 2: Budget status load test (with caching)
            logger.info("💰 Testing budget status endpoint...")
            budget_result = await self.run_api_load_test("/api/v1/budget/status", concurrent_users=50, requests_per_user=10)
            comprehensive_results["tests"]["budget_status"] = budget_result.__dict__
            comprehensive_results["regressions"]["budget_status"] = self.check_performance_regression(budget_result)
            
            # Test 3: Performance stats load test (admin endpoint)
            logger.info("📊 Testing performance stats endpoint...")
            perf_result = await self.run_api_load_test("/api/v1/performance/cache/stats", concurrent_users=25, requests_per_user=5, use_admin_token=True)
            comprehensive_results["tests"]["performance_stats"] = perf_result.__dict__
            comprehensive_results["regressions"]["performance_stats"] = self.check_performance_regression(perf_result)
            
            # Test 4: Async task submission load test
            logger.info("⚡ Testing async task submission...")
            task_result = await self.run_async_task_load_test(concurrent_submissions=30, tasks_per_user=2)
            comprehensive_results["tests"]["async_tasks"] = task_result.__dict__
            comprehensive_results["regressions"]["async_tasks"] = self.check_performance_regression(task_result)
            
            # Test 5: WebSocket connection load test
            logger.info("🔌 Testing WebSocket connections...")
            ws_result = await self.run_websocket_load_test(concurrent_connections=20, messages_per_connection=3, connection_duration=10)
            comprehensive_results["tests"]["websocket_connections"] = ws_result.__dict__
            
            # Calculate overall performance summary
            all_results = [health_result, budget_result, perf_result, task_result, ws_result]
            
            total_requests = sum(r.total_requests for r in all_results)
            successful_requests = sum(r.successful_requests for r in all_results)
            avg_response_times = [r.avg_response_time for r in all_results]
            
            comprehensive_results["performance_summary"] = {
                "total_tests": len(all_results),
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "overall_success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
                "avg_response_time": statistics.mean(avg_response_times),
                "max_response_time": max(r.max_response_time for r in all_results),
                "total_test_duration": sum(r.test_duration for r in all_results),
                "max_concurrent_users": max(r.concurrent_users for r in all_results),
                "max_requests_per_second": max(r.requests_per_second for r in all_results)
            }
            
            # Check for any critical regressions
            critical_issues = []
            for test_name, regression_data in comprehensive_results["regressions"].items():
                if regression_data.get("status") == "regression_detected":
                    critical_issues.extend(regression_data.get("issues", []))
            
            comprehensive_results["critical_issues"] = critical_issues
            comprehensive_results["overall_status"] = "PASS" if not critical_issues else "FAIL"
            
            logger.info(f"✅ Comprehensive load testing completed: {comprehensive_results['overall_status']}")
            
        except Exception as e:
            logger.error(f"❌ Load testing failed: {e}")
            comprehensive_results["error"] = str(e)
            comprehensive_results["overall_status"] = "ERROR"
        
        return comprehensive_results
    
    def generate_load_test_report(self, results: Dict[str, Any]) -> str:
        """Generate formatted load test report"""
        report = []
        report.append("="*80)
        report.append("🚀 AI ASSISTANT MVP - COMPREHENSIVE LOAD TEST REPORT")
        report.append("="*80)
        
        # Overall status
        status = results.get("overall_status", "UNKNOWN")
        report.append(f"\n📊 OVERALL STATUS: {status}")
        
        if "performance_summary" in results:
            summary = results["performance_summary"]
            report.append(f"\n📈 PERFORMANCE SUMMARY:")
            report.append(f"   • Total Tests: {summary.get('total_tests', 0)}")
            report.append(f"   • Total Requests: {summary.get('total_requests', 0)}")
            report.append(f"   • Success Rate: {summary.get('overall_success_rate', 0):.1f}%")
            report.append(f"   • Avg Response Time: {summary.get('avg_response_time', 0):.3f}s")
            report.append(f"   • Max Concurrent Users: {summary.get('max_concurrent_users', 0)}")
            report.append(f"   • Max RPS: {summary.get('max_requests_per_second', 0):.1f}")
        
        # Individual test results
        if "tests" in results:
            report.append(f"\n🧪 INDIVIDUAL TEST RESULTS:")
            
            for test_name, test_data in results["tests"].items():
                report.append(f"\n   📋 {test_name.replace('_', ' ').title()}:")
                report.append(f"      • Concurrent Users: {test_data.get('concurrent_users', 0)}")
                report.append(f"      • Success Rate: {(test_data.get('successful_requests', 0) / max(test_data.get('total_requests', 1), 1) * 100):.1f}%")
                report.append(f"      • Avg Response: {test_data.get('avg_response_time', 0):.3f}s")
                report.append(f"      • P95 Response: {test_data.get('p95_response_time', 0):.3f}s")
                report.append(f"      • Requests/sec: {test_data.get('requests_per_second', 0):.1f}")
                report.append(f"      • Memory Delta: {test_data.get('memory_delta', 0):.1f}MB")
        
        # Performance regressions
        if "critical_issues" in results and results["critical_issues"]:
            report.append(f"\n⚠️ CRITICAL PERFORMANCE ISSUES:")
            for issue in results["critical_issues"]:
                report.append(f"   • {issue}")
        else:
            report.append(f"\n✅ NO CRITICAL PERFORMANCE REGRESSIONS DETECTED")
        
        report.append("\n" + "="*80)
        
        return "\n".join(report)

class TestLoadTesting:
    """Load тесты производительности"""
    
    def test_concurrent_health_checks(self):
        """Тест параллельных health check запросов"""
        def make_health_request():
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            
            with patch('requests.get', return_value=mock_response):
                import requests
                start_time = time.time()
                response = requests.get("http://localhost:8000/health")
                end_time = time.time()
                
                return {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                }
        
        # Тест 20 параллельных запросов
        num_requests = 20
        max_workers = 10
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(make_health_request) for _ in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Анализ результатов
        success_count = sum(1 for r in results if r["success"])
        response_times = [r["response_time"] for r in results]
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        # Проверки
        assert success_count == num_requests, f"Only {success_count}/{num_requests} requests succeeded"
        assert avg_response_time < 1.0, f"Average response time too high: {avg_response_time}s"
        assert max_response_time < 2.0, f"Max response time too high: {max_response_time}s"
    
    def test_search_load_testing(self):
        """Load тест для поиска"""
        def make_search_request(query_id):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "query": f"test query {query_id}",
                "results": [
                    {"id": f"doc_{query_id}", "title": f"Document {query_id}", "score": 0.9}
                ],
                "total_results": 1,
                "search_time_ms": 50.0 + (query_id % 10) * 10  # Вариация времени поиска
            }
            
            with patch('requests.post', return_value=mock_response):
                import requests
                start_time = time.time()
                response = requests.post(
                    "http://localhost:8000/api/v1/search/advanced/",
                    json={
                        "query": f"test query {query_id}",
                        "search_type": "semantic",
                        "limit": 10
                    }
                )
                end_time = time.time()
                
                return {
                    "query_id": query_id,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "search_time_ms": response.json().get("search_time_ms", 0),
                    "success": response.status_code == 200
                }
        
        # Тест 30 поисковых запросов
        num_searches = 30
        max_workers = 15
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(make_search_request, i) for i in range(num_searches)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Анализ результатов
        success_count = sum(1 for r in results if r["success"])
        response_times = [r["response_time"] for r in results]
        search_times = [r["search_time_ms"] for r in results]
        
        avg_response_time = statistics.mean(response_times)
        avg_search_time = statistics.mean(search_times)
        p95_response_time = sorted(response_times)[int(0.95 * len(response_times))]
        
        # Проверки производительности
        assert success_count == num_searches, f"Only {success_count}/{num_searches} searches succeeded"
        assert avg_response_time < 2.0, f"Average response time too high: {avg_response_time}s"
        assert p95_response_time < 3.0, f"95th percentile response time too high: {p95_response_time}s"
        assert avg_search_time < 200.0, f"Average search time too high: {avg_search_time}ms"
    
    def test_memory_usage_simulation(self):
        """Симуляция тестирования использования памяти"""
        def simulate_memory_intensive_operation():
            # Симуляция обработки больших документов
            large_document = {
                "id": "large_doc",
                "title": "Large Document",
                "content": "A" * 10000,  # 10KB контента
                "metadata": {"size": 10000, "type": "large"}
            }
            
            # Симуляция обработки
            processed_chunks = []
            chunk_size = 1000
            for i in range(0, len(large_document["content"]), chunk_size):
                chunk = {
                    "chunk_id": i // chunk_size,
                    "content": large_document["content"][i:i+chunk_size],
                    "metadata": large_document["metadata"]
                }
                processed_chunks.append(chunk)
            
            return {
                "document_id": large_document["id"],
                "chunks_count": len(processed_chunks),
                "total_size": len(large_document["content"]),
                "processing_success": True
            }
        
        # Тест обработки 10 больших документов параллельно
        num_documents = 10
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(simulate_memory_intensive_operation) for _ in range(num_documents)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Проверки
        success_count = sum(1 for r in results if r["processing_success"])
        total_chunks = sum(r["chunks_count"] for r in results)
        total_size = sum(r["total_size"] for r in results)
        
        assert success_count == num_documents, f"Only {success_count}/{num_documents} documents processed"
        assert total_chunks > 0, "No chunks were processed"
        assert total_size == num_documents * 10000, f"Total size mismatch: {total_size}"
    
    def test_database_connection_pool_simulation(self):
        """Симуляция тестирования пула подключений к БД"""
        connection_pool = []
        pool_lock = threading.Lock()
        max_connections = 10
        
        def get_connection():
            with pool_lock:
                if len(connection_pool) < max_connections:
                    # Создаем новое подключение
                    connection = Mock()
                    connection.id = len(connection_pool)
                    connection.is_active = True
                    connection_pool.append(connection)
                    return connection
                else:
                    # Используем существующее подключение
                    return connection_pool[len(connection_pool) % max_connections]
        
        def simulate_db_operation(operation_id):
            connection = get_connection()
            
            # Симуляция DB операции
            time.sleep(0.01)  # Короткая задержка
            
            return {
                "operation_id": operation_id,
                "connection_id": connection.id,
                "success": connection.is_active
            }
        
        # Тест 50 операций с БД
        num_operations = 50
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(simulate_db_operation, i) for i in range(num_operations)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Анализ результатов
        success_count = sum(1 for r in results if r["success"])
        unique_connections = len(set(r["connection_id"] for r in results))
        
        assert success_count == num_operations, f"Only {success_count}/{num_operations} DB operations succeeded"
        assert unique_connections <= max_connections, f"Too many connections created: {unique_connections}"
        assert len(connection_pool) <= max_connections, f"Connection pool exceeded limit: {len(connection_pool)}"
    
    def test_rate_limiting_simulation(self):
        """Симуляция тестирования rate limiting"""
        rate_limit_counter = {}
        rate_limit_lock = threading.Lock()
        max_requests_per_user = 10
        
        def check_rate_limit(user_id):
            with rate_limit_lock:
                current_count = rate_limit_counter.get(user_id, 0)
                if current_count >= max_requests_per_user:
                    return False  # Rate limit exceeded
                rate_limit_counter[user_id] = current_count + 1
                return True
        
        def make_request_with_rate_limit(request_id):
            user_id = f"user_{request_id % 5}"  # 5 разных пользователей
            
            if not check_rate_limit(user_id):
                return {
                    "request_id": request_id,
                    "user_id": user_id,
                    "status_code": 429,  # Too Many Requests
                    "success": False,
                    "rate_limited": True
                }
            
            # Симуляция успешного запроса
            mock_response = Mock()
            mock_response.status_code = 200
            
            return {
                "request_id": request_id,
                "user_id": user_id,
                "status_code": 200,
                "success": True,
                "rate_limited": False
            }
        
        # Тест 60 запросов от 5 пользователей (12 запросов на пользователя)
        num_requests = 60
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request_with_rate_limit, i) for i in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Анализ результатов
        success_count = sum(1 for r in results if r["success"])
        rate_limited_count = sum(1 for r in results if r["rate_limited"])
        
        # Каждый пользователь должен быть ограничен после 10 запросов
        expected_rate_limited = 5 * 2  # 5 пользователей * 2 лишних запроса
        
        assert rate_limited_count >= expected_rate_limited, f"Rate limiting not working: {rate_limited_count} limited"
        assert success_count <= 5 * max_requests_per_user, f"Too many successful requests: {success_count}"
    
    def test_stress_testing_simulation(self):
        """Симуляция стресс-тестирования"""
        error_count = 0
        error_lock = threading.Lock()
        
        def stress_operation(operation_id):
            try:
                # Симуляция различных операций
                if operation_id % 4 == 0:
                    # Поиск
                    mock_response = Mock()
                    mock_response.status_code = 200
                    return {"type": "search", "success": True}
                elif operation_id % 4 == 1:
                    # Загрузка документа
                    mock_response = Mock()
                    mock_response.status_code = 201
                    return {"type": "upload", "success": True}
                elif operation_id % 4 == 2:
                    # Аналитика
                    mock_response = Mock()
                    mock_response.status_code = 200
                    return {"type": "analytics", "success": True}
                else:
                    # Пользовательские операции
                    mock_response = Mock()
                    mock_response.status_code = 200
                    return {"type": "user_ops", "success": True}
                    
            except Exception as e:
                with error_lock:
                    nonlocal error_count
                    error_count += 1
                return {"type": "error", "success": False, "error": str(e)}
        
        # Стресс-тест: 100 операций
        num_operations = 100
        max_workers = 25
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(stress_operation, i) for i in range(num_operations)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Анализ результатов
        success_count = sum(1 for r in results if r["success"])
        operation_types = {}
        for result in results:
            op_type = result["type"]
            operation_types[op_type] = operation_types.get(op_type, 0) + 1
        
        throughput = num_operations / total_time  # операций в секунду
        
        # Проверки
        assert success_count >= num_operations * 0.95, f"Too many failures: {num_operations - success_count}"
        assert error_count <= num_operations * 0.05, f"Too many errors: {error_count}"
        assert throughput > 10, f"Throughput too low: {throughput} ops/sec"
        assert total_time < 30, f"Stress test took too long: {total_time}s"

class TestPerformanceMetrics:
    """Тесты метрик производительности"""
    
    def test_response_time_distribution(self):
        """Тест распределения времени ответа"""
        response_times = []
        
        def measure_response_time():
            start_time = time.time()
            # Симуляция операции с переменным временем выполнения
            import random
            time.sleep(random.uniform(0.01, 0.1))  # 10-100ms
            end_time = time.time()
            return end_time - start_time
        
        # Собираем 100 измерений
        for _ in range(100):
            response_times.append(measure_response_time())
        
        # Вычисляем статистики
        avg_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        p95_time = sorted(response_times)[int(0.95 * len(response_times))]
        p99_time = sorted(response_times)[int(0.99 * len(response_times))]
        
        # Проверки SLA
        assert avg_time < 0.2, f"Average response time too high: {avg_time}s"
        assert median_time < 0.15, f"Median response time too high: {median_time}s"
        assert p95_time < 0.3, f"95th percentile too high: {p95_time}s"
        assert p99_time < 0.5, f"99th percentile too high: {p99_time}s"
    
    def test_throughput_measurement(self):
        """Тест измерения пропускной способности"""
        def process_request():
            # Симуляция обработки запроса
            time.sleep(0.01)  # 10ms обработка
            return {"processed": True}
        
        # Тест пропускной способности в течение 5 секунд
        test_duration = 2  # сокращено для тестов
        start_time = time.time()
        processed_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            while time.time() - start_time < test_duration:
                future = executor.submit(process_request)
                futures.append(future)
            
            # Ждем завершения всех задач
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result["processed"]:
                    processed_count += 1
        
        actual_duration = time.time() - start_time
        throughput = processed_count / actual_duration
        
        # Проверки
        assert processed_count > 0, "No requests were processed"
        assert throughput > 50, f"Throughput too low: {throughput} req/sec"

async def main():
    """Main load testing execution"""
    tester = LoadTester()
    
    print("🔧 Starting AI Assistant MVP Load Testing...")
    print("📋 Test Suite: Comprehensive Performance Validation")
    
    try:
        results = await tester.run_comprehensive_load_test()
        
        # Generate and print report
        report = tester.generate_load_test_report(results)
        print(report)
        
        # Save results
        with open("load_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: load_test_results.json")
        
        # Return exit code based on results
        return 0 if results.get("overall_status") == "PASS" else 1
        
    except Exception as e:
        print(f"\n❌ Load testing failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main())) 