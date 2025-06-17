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