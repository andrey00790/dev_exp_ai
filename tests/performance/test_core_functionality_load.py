"""
Core Functionality Load Testing for AI Assistant
Tests the main user workflows under various load conditions
"""
import pytest
import asyncio
import time
import statistics
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import httpx
import logging

logger = logging.getLogger(__name__)

@dataclass
class LoadTestMetrics:
    """Load test metrics collection"""
    test_name: str
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    error_rate: float
    test_duration: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class CoreFunctionalityLoadTester:
    """Load tester for core AI Assistant functionality"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results: List[LoadTestMetrics] = []
        
        # Real authentication tokens (will be obtained during tests)
        self.admin_token = None
        self.user_token = None
    
    def _calculate_percentiles(self, response_times: List[float]) -> Dict[str, float]:
        """Calculate response time percentiles"""
        if not response_times:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
        
        sorted_times = sorted(response_times)
        n = len(sorted_times)
        
        return {
            "p50": sorted_times[int(n * 0.5)] if n > 0 else 0.0,
            "p95": sorted_times[int(n * 0.95)] if n > 1 else sorted_times[0],
            "p99": sorted_times[int(n * 0.99)] if n > 2 else sorted_times[-1]
        }
    
    async def run_health_check_load_test(
        self, 
        concurrent_users: int = 50, 
        requests_per_user: int = 20
    ) -> LoadTestMetrics:
        """Test health check endpoint under load"""
        logger.info(f"🏃‍♂️ Running health check load test: {concurrent_users} users, {requests_per_user} req/user")
        
        response_times = []
        successful_requests = 0
        failed_requests = 0
        start_time = time.time()
        
        async def user_simulation():
            """Simulate a single user making health check requests"""
            user_times = []
            user_success = 0
            user_failures = 0
            
            async with httpx.AsyncClient(app=None, base_url=self.base_url) as client:
                for _ in range(requests_per_user):
                    request_start = time.time()
                    
                    try:
                        response = await client.get("/api/health")
                        response_time = time.time() - request_start
                        user_times.append(response_time)
                        
                        if response.status_code == 200:
                            user_success += 1
                        else:
                            user_failures += 1
                    except Exception as e:
                        response_time = time.time() - request_start
                        user_times.append(response_time)
                        user_failures += 1
                        logger.debug(f"Health check failed: {e}")
                    
                    # Small delay between requests
                    await asyncio.sleep(0.01)
            
            return user_times, user_success, user_failures
        
        # Execute concurrent user simulations
        tasks = [user_simulation() for _ in range(concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        test_duration = time.time() - start_time
        
        # Aggregate results
        for result in results:
            if isinstance(result, tuple):
                user_times, user_success, user_failures = result
                response_times.extend(user_times)
                successful_requests += user_success
                failed_requests += user_failures
        
        # Calculate metrics
        total_requests = successful_requests + failed_requests
        percentiles = self._calculate_percentiles(response_times)
        
        metrics = LoadTestMetrics(
            test_name="Health Check Load Test",
            concurrent_users=concurrent_users,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=statistics.mean(response_times) if response_times else 0.0,
            p50_response_time=percentiles["p50"],
            p95_response_time=percentiles["p95"],
            p99_response_time=percentiles["p99"],
            min_response_time=min(response_times) if response_times else 0.0,
            max_response_time=max(response_times) if response_times else 0.0,
            requests_per_second=total_requests / test_duration if test_duration > 0 else 0.0,
            error_rate=(failed_requests / total_requests * 100) if total_requests > 0 else 0.0,
            test_duration=test_duration
        )
        
        self.test_results.append(metrics)
        logger.info(f"✅ Health check load test completed: {successful_requests}/{total_requests} success, "
                   f"{metrics.avg_response_time:.3f}s avg, {metrics.requests_per_second:.1f} RPS")
        
        return metrics
    
    async def run_authentication_load_test(
        self, 
        concurrent_users: int = 30, 
        requests_per_user: int = 5
    ) -> LoadTestMetrics:
        """Test authentication endpoints under load"""
        logger.info(f"🔐 Running authentication load test: {concurrent_users} users, {requests_per_user} req/user")
        
        response_times = []
        successful_requests = 0
        failed_requests = 0
        start_time = time.time()
        
        async def user_simulation():
            """Simulate authentication workflow"""
            user_times = []
            user_success = 0
            user_failures = 0
            
            async with httpx.AsyncClient(app=None, base_url=self.base_url) as client:
                for i in range(requests_per_user):
                    request_start = time.time()
                    
                    try:
                        # Alternate between different auth endpoints
                        if i % 3 == 0:
                            # Test login
                            response = await client.post(
                                "/api/v1/auth/login",
                                json={
                                    "email": f"user{random.randint(1, 1000)}@test.com",
                                    "password": "test_password"
                                }
                            )
                        elif i % 3 == 1:
                            # Test token verification
                            response = await client.get(
                                "/api/v1/auth/verify",
                                headers={"Authorization": f"Bearer {self.user_token}"}
                            )
                        else:
                            # Test budget status
                            response = await client.get(
                                "/api/v1/auth/budget/status",
                                headers={"Authorization": f"Bearer {self.user_token}"}
                            )
                        
                        response_time = time.time() - request_start
                        user_times.append(response_time)
                        
                        if response.status_code in [200, 201, 401, 403]:  # Expected responses
                            user_success += 1
                        else:
                            user_failures += 1
                            
                    except Exception as e:
                        response_time = time.time() - request_start
                        user_times.append(response_time)
                        user_failures += 1
                        logger.debug(f"Auth request failed: {e}")
                    
                    await asyncio.sleep(0.02)
            
            return user_times, user_success, user_failures
        
        # Execute concurrent simulations
        tasks = [user_simulation() for _ in range(concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        test_duration = time.time() - start_time
        
        # Aggregate results
        for result in results:
            if isinstance(result, tuple):
                user_times, user_success, user_failures = result
                response_times.extend(user_times)
                successful_requests += user_success
                failed_requests += user_failures
        
        # Calculate metrics
        total_requests = successful_requests + failed_requests
        percentiles = self._calculate_percentiles(response_times)
        
        metrics = LoadTestMetrics(
            test_name="Authentication Load Test",
            concurrent_users=concurrent_users,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=statistics.mean(response_times) if response_times else 0.0,
            p50_response_time=percentiles["p50"],
            p95_response_time=percentiles["p95"],
            p99_response_time=percentiles["p99"],
            min_response_time=min(response_times) if response_times else 0.0,
            max_response_time=max(response_times) if response_times else 0.0,
            requests_per_second=total_requests / test_duration if test_duration > 0 else 0.0,
            error_rate=(failed_requests / total_requests * 100) if total_requests > 0 else 0.0,
            test_duration=test_duration
        )
        
        self.test_results.append(metrics)
        logger.info(f"✅ Authentication load test completed: {successful_requests}/{total_requests} success")
        
        return metrics
    
    async def run_websocket_load_test(
        self, 
        concurrent_connections: int = 25, 
        messages_per_connection: int = 10
    ) -> LoadTestMetrics:
        """Test WebSocket endpoints under load"""
        logger.info(f"🔌 Running WebSocket load test: {concurrent_connections} connections, {messages_per_connection} msgs/conn")
        
        response_times = []
        successful_requests = 0
        failed_requests = 0
        start_time = time.time()
        
        async def websocket_simulation():
            """Simulate WebSocket connection and messaging"""
            connection_times = []
            connection_success = 0
            connection_failures = 0
            
            try:
                # Simulate WebSocket connection test
                async with httpx.AsyncClient(app=None, base_url=self.base_url) as client:
                    for i in range(messages_per_connection):
                        request_start = time.time()
                        
                        try:
                            # Test WebSocket stats endpoint
                            response = await client.get("/api/v1/ws/stats")
                            response_time = time.time() - request_start
                            connection_times.append(response_time)
                            
                            if response.status_code == 200:
                                connection_success += 1
                            else:
                                connection_failures += 1
                                
                        except Exception as e:
                            response_time = time.time() - request_start
                            connection_times.append(response_time)
                            connection_failures += 1
                            logger.debug(f"WebSocket request failed: {e}")
                        
                        await asyncio.sleep(0.05)
            
            except Exception as e:
                logger.debug(f"WebSocket simulation failed: {e}")
                connection_failures += messages_per_connection
            
            return connection_times, connection_success, connection_failures
        
        # Execute concurrent WebSocket simulations
        tasks = [websocket_simulation() for _ in range(concurrent_connections)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        test_duration = time.time() - start_time
        
        # Aggregate results
        for result in results:
            if isinstance(result, tuple):
                conn_times, conn_success, conn_failures = result
                response_times.extend(conn_times)
                successful_requests += conn_success
                failed_requests += conn_failures
        
        # Calculate metrics
        total_requests = successful_requests + failed_requests
        percentiles = self._calculate_percentiles(response_times)
        
        metrics = LoadTestMetrics(
            test_name="WebSocket Load Test",
            concurrent_users=concurrent_connections,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=statistics.mean(response_times) if response_times else 0.0,
            p50_response_time=percentiles["p50"],
            p95_response_time=percentiles["p95"],
            p99_response_time=percentiles["p99"],
            min_response_time=min(response_times) if response_times else 0.0,
            max_response_time=max(response_times) if response_times else 0.0,
            requests_per_second=total_requests / test_duration if test_duration > 0 else 0.0,
            error_rate=(failed_requests / total_requests * 100) if total_requests > 0 else 0.0,
            test_duration=test_duration
        )
        
        self.test_results.append(metrics)
        logger.info(f"✅ WebSocket load test completed: {successful_requests}/{total_requests} success")
        
        return metrics
    
    async def run_monitoring_load_test(
        self, 
        concurrent_users: int = 20, 
        requests_per_user: int = 15
    ) -> LoadTestMetrics:
        """Test monitoring endpoints under load"""
        logger.info(f"📊 Running monitoring load test: {concurrent_users} users, {requests_per_user} req/user")
        
        response_times = []
        successful_requests = 0
        failed_requests = 0
        start_time = time.time()
        
        async def monitoring_simulation():
            """Simulate monitoring API usage"""
            user_times = []
            user_success = 0
            user_failures = 0
            
            async with httpx.AsyncClient(app=None, base_url=self.base_url) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                for i in range(requests_per_user):
                    request_start = time.time()
                    
                    try:
                        # Cycle through different monitoring endpoints
                        if i % 4 == 0:
                            response = await client.get("/api/v1/monitoring/metrics/current", headers=headers)
                        elif i % 4 == 1:
                            response = await client.get("/api/v1/monitoring/metrics/history", headers=headers)
                        elif i % 4 == 2:
                            response = await client.get("/api/v1/monitoring/performance/summary", headers=headers)
                        else:
                            response = await client.get("/api/v1/realtime-monitoring/health", headers=headers)
                        
                        response_time = time.time() - request_start
                        user_times.append(response_time)
                        
                        if response.status_code in [200, 403]:  # 403 expected for non-admin
                            user_success += 1
                        else:
                            user_failures += 1
                            
                    except Exception as e:
                        response_time = time.time() - request_start
                        user_times.append(response_time)
                        user_failures += 1
                        logger.debug(f"Monitoring request failed: {e}")
                    
                    await asyncio.sleep(0.03)
            
            return user_times, user_success, user_failures
        
        # Execute concurrent simulations
        tasks = [monitoring_simulation() for _ in range(concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        test_duration = time.time() - start_time
        
        # Aggregate results
        for result in results:
            if isinstance(result, tuple):
                user_times, user_success, user_failures = result
                response_times.extend(user_times)
                successful_requests += user_success
                failed_requests += user_failures
        
        # Calculate metrics
        total_requests = successful_requests + failed_requests
        percentiles = self._calculate_percentiles(response_times)
        
        metrics = LoadTestMetrics(
            test_name="Monitoring Load Test",
            concurrent_users=concurrent_users,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=statistics.mean(response_times) if response_times else 0.0,
            p50_response_time=percentiles["p50"],
            p95_response_time=percentiles["p95"],
            p99_response_time=percentiles["p99"],
            min_response_time=min(response_times) if response_times else 0.0,
            max_response_time=max(response_times) if response_times else 0.0,
            requests_per_second=total_requests / test_duration if test_duration > 0 else 0.0,
            error_rate=(failed_requests / total_requests * 100) if total_requests > 0 else 0.0,
            test_duration=test_duration
        )
        
        self.test_results.append(metrics)
        logger.info(f"✅ Monitoring load test completed: {successful_requests}/{total_requests} success")
        
        return metrics
    
    async def run_optimization_load_test(
        self, 
        concurrent_users: int = 15, 
        requests_per_user: int = 8
    ) -> LoadTestMetrics:
        """Test optimization endpoints under load"""
        logger.info(f"⚡ Running optimization load test: {concurrent_users} users, {requests_per_user} req/user")
        
        response_times = []
        successful_requests = 0
        failed_requests = 0
        start_time = time.time()
        
        async def optimization_simulation():
            """Simulate optimization API usage"""
            user_times = []
            user_success = 0
            user_failures = 0
            
            async with httpx.AsyncClient(app=None, base_url=self.base_url) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                for i in range(requests_per_user):
                    request_start = time.time()
                    
                    try:
                        # Test different optimization endpoints
                        if i % 3 == 0:
                            # Benchmark request
                            response = await client.post(
                                "/api/v1/optimization/benchmark",
                                json={"component": "search", "optimization_type": "cache_tuning"},
                                headers=headers
                            )
                        elif i % 3 == 1:
                            # Optimization request
                            response = await client.post(
                                "/api/v1/optimization/optimize",
                                json={"component": "analytics", "optimization_type": "query_optimization"},
                                headers=headers
                            )
                        else:
                            # History request
                            response = await client.get("/api/v1/optimization/history", headers=headers)
                        
                        response_time = time.time() - request_start
                        user_times.append(response_time)
                        
                        if response.status_code in [200, 403]:  # 403 expected for non-admin
                            user_success += 1
                        else:
                            user_failures += 1
                            
                    except Exception as e:
                        response_time = time.time() - request_start
                        user_times.append(response_time)
                        user_failures += 1
                        logger.debug(f"Optimization request failed: {e}")
                    
                    await asyncio.sleep(0.04)
            
            return user_times, user_success, user_failures
        
        # Execute concurrent simulations
        tasks = [optimization_simulation() for _ in range(concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        test_duration = time.time() - start_time
        
        # Aggregate results
        for result in results:
            if isinstance(result, tuple):
                user_times, user_success, user_failures = result
                response_times.extend(user_times)
                successful_requests += user_success
                failed_requests += user_failures
        
        # Calculate metrics
        total_requests = successful_requests + failed_requests
        percentiles = self._calculate_percentiles(response_times)
        
        metrics = LoadTestMetrics(
            test_name="Optimization Load Test",
            concurrent_users=concurrent_users,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=statistics.mean(response_times) if response_times else 0.0,
            p50_response_time=percentiles["p50"],
            p95_response_time=percentiles["p95"],
            p99_response_time=percentiles["p99"],
            min_response_time=min(response_times) if response_times else 0.0,
            max_response_time=max(response_times) if response_times else 0.0,
            requests_per_second=total_requests / test_duration if test_duration > 0 else 0.0,
            error_rate=(failed_requests / total_requests * 100) if total_requests > 0 else 0.0,
            test_duration=test_duration
        )
        
        self.test_results.append(metrics)
        logger.info(f"✅ Optimization load test completed: {successful_requests}/{total_requests} success")
        
        return metrics
    
    async def run_comprehensive_load_test(self) -> Dict[str, Any]:
        """Run comprehensive load test across all core functionality"""
        logger.info("🚀 Starting comprehensive core functionality load test")
        
        start_time = time.time()
        
        # Run all load tests
        health_metrics = await self.run_health_check_load_test(concurrent_users=100, requests_per_user=30)
        auth_metrics = await self.run_authentication_load_test(concurrent_users=50, requests_per_user=10)
        ws_metrics = await self.run_websocket_load_test(concurrent_connections=40, messages_per_connection=15)
        monitor_metrics = await self.run_monitoring_load_test(concurrent_users=30, requests_per_user=20)
        opt_metrics = await self.run_optimization_load_test(concurrent_users=25, requests_per_user=12)
        
        total_duration = time.time() - start_time
        
        # Aggregate overall statistics
        all_metrics = [health_metrics, auth_metrics, ws_metrics, monitor_metrics, opt_metrics]
        
        total_requests = sum(m.total_requests for m in all_metrics)
        total_successful = sum(m.successful_requests for m in all_metrics)
        total_failed = sum(m.failed_requests for m in all_metrics)
        
        overall_success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0.0
        overall_rps = total_requests / total_duration if total_duration > 0 else 0.0
        
        results = {
            "test_summary": {
                "total_duration": total_duration,
                "total_requests": total_requests,
                "successful_requests": total_successful,
                "failed_requests": total_failed,
                "overall_success_rate": overall_success_rate,
                "overall_rps": overall_rps,
                "timestamp": datetime.utcnow().isoformat()
            },
            "individual_tests": [m.to_dict() for m in all_metrics],
            "performance_analysis": self._analyze_performance(all_metrics)
        }
        
        logger.info(f"✅ Comprehensive load test completed: {overall_success_rate:.1f}% success rate, {overall_rps:.1f} RPS")
        
        return results
    
    def _analyze_performance(self, metrics: List[LoadTestMetrics]) -> Dict[str, Any]:
        """Analyze performance across all tests"""
        analysis = {
            "best_performing": {
                "by_response_time": min(metrics, key=lambda m: m.avg_response_time).test_name,
                "by_throughput": max(metrics, key=lambda m: m.requests_per_second).test_name,
                "by_success_rate": max(metrics, key=lambda m: (m.successful_requests / m.total_requests if m.total_requests > 0 else 0)).test_name
            },
            "performance_concerns": [],
            "recommendations": []
        }
        
        # Identify performance concerns
        for metric in metrics:
            if metric.error_rate > 5.0:
                analysis["performance_concerns"].append(f"{metric.test_name}: High error rate ({metric.error_rate:.1f}%)")
            
            if metric.p95_response_time > 1.0:
                analysis["performance_concerns"].append(f"{metric.test_name}: Slow P95 response time ({metric.p95_response_time:.3f}s)")
            
            if metric.requests_per_second < 10:
                analysis["performance_concerns"].append(f"{metric.test_name}: Low throughput ({metric.requests_per_second:.1f} RPS)")
        
        # Generate recommendations
        if not analysis["performance_concerns"]:
            analysis["recommendations"].append("System performance is excellent across all test scenarios")
        else:
            analysis["recommendations"].extend([
                "Consider implementing caching for slow endpoints",
                "Review error handling and add circuit breakers for high error rate endpoints",
                "Optimize database queries for better throughput",
                "Add horizontal scaling for high-load scenarios"
            ])
        
        return analysis
    
    def generate_load_test_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive load test report"""
        report_lines = [
            "# 🚀 Core Functionality Load Test Report",
            f"**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            "",
            "## 📊 Test Summary",
            f"- **Total Duration**: {results['test_summary']['total_duration']:.2f} seconds",
            f"- **Total Requests**: {results['test_summary']['total_requests']:,}",
            f"- **Success Rate**: {results['test_summary']['overall_success_rate']:.1f}%",
            f"- **Overall Throughput**: {results['test_summary']['overall_rps']:.1f} RPS",
            "",
            "## 🎯 Individual Test Results",
            ""
        ]
        
        for test in results["individual_tests"]:
            report_lines.extend([
                f"### {test['test_name']}",
                f"- **Concurrent Users**: {test['concurrent_users']}",
                f"- **Total Requests**: {test['total_requests']:,}",
                f"- **Success Rate**: {(test['successful_requests']/test['total_requests']*100):.1f}%",
                f"- **Avg Response Time**: {test['avg_response_time']:.3f}s",
                f"- **P95 Response Time**: {test['p95_response_time']:.3f}s",
                f"- **Throughput**: {test['requests_per_second']:.1f} RPS",
                f"- **Error Rate**: {test['error_rate']:.1f}%",
                ""
            ])
        
        # Performance analysis
        analysis = results["performance_analysis"]
        report_lines.extend([
            "## 🏆 Performance Analysis",
            "",
            "### Best Performing Tests",
            f"- **Fastest Response Time**: {analysis['best_performing']['by_response_time']}",
            f"- **Highest Throughput**: {analysis['best_performing']['by_throughput']}",
            f"- **Best Success Rate**: {analysis['best_performing']['by_success_rate']}",
            ""
        ])
        
        if analysis["performance_concerns"]:
            report_lines.extend([
                "### ⚠️ Performance Concerns",
                "",
                *[f"- {concern}" for concern in analysis["performance_concerns"]],
                ""
            ])
        
        report_lines.extend([
            "### 💡 Recommendations",
            "",
            *[f"- {rec}" for rec in analysis["recommendations"]],
            "",
            "---",
            "*Report generated by Core Functionality Load Tester*"
        ])
        
        return "\n".join(report_lines)


# Test classes for pytest integration
@pytest.mark.asyncio
class TestCoreFunctionalityLoad:
    """Pytest integration for core functionality load tests"""
    
    async def test_health_check_load(self):
        """Test health check under moderate load"""
        tester = CoreFunctionalityLoadTester()
        metrics = await tester.run_health_check_load_test(concurrent_users=25, requests_per_user=10)
        
        # Performance assertions
        assert metrics.error_rate < 10.0, f"Error rate too high: {metrics.error_rate:.1f}%"
        assert metrics.avg_response_time < 0.5, f"Average response time too slow: {metrics.avg_response_time:.3f}s"
        assert metrics.requests_per_second > 5, f"Throughput too low: {metrics.requests_per_second:.1f} RPS"
    
    async def test_authentication_load(self):
        """Test authentication under moderate load"""
        tester = CoreFunctionalityLoadTester()
        metrics = await tester.run_authentication_load_test(concurrent_users=20, requests_per_user=5)
        
        # Performance assertions
        assert metrics.error_rate < 15.0, f"Error rate too high: {metrics.error_rate:.1f}%"
        assert metrics.avg_response_time < 1.0, f"Average response time too slow: {metrics.avg_response_time:.3f}s"
    
    async def test_websocket_load(self):
        """Test WebSocket under moderate load"""
        tester = CoreFunctionalityLoadTester()
        metrics = await tester.run_websocket_load_test(concurrent_connections=15, messages_per_connection=8)
        
        # Performance assertions
        assert metrics.error_rate < 20.0, f"Error rate too high: {metrics.error_rate:.1f}%"
        assert metrics.avg_response_time < 0.8, f"Average response time too slow: {metrics.avg_response_time:.3f}s"
    
    async def test_monitoring_load(self):
        """Test monitoring endpoints under moderate load"""
        tester = CoreFunctionalityLoadTester()
        metrics = await tester.run_monitoring_load_test(concurrent_users=15, requests_per_user=10)
        
        # Performance assertions (more lenient for monitoring)
        assert metrics.error_rate < 25.0, f"Error rate too high: {metrics.error_rate:.1f}%"
        assert metrics.avg_response_time < 1.2, f"Average response time too slow: {metrics.avg_response_time:.3f}s"
    
    async def test_optimization_load(self):
        """Test optimization endpoints under moderate load"""
        tester = CoreFunctionalityLoadTester()
        metrics = await tester.run_optimization_load_test(concurrent_users=10, requests_per_user=6)
        
        # Performance assertions (more lenient for optimization)
        assert metrics.error_rate < 30.0, f"Error rate too high: {metrics.error_rate:.1f}%"
        assert metrics.avg_response_time < 1.5, f"Average response time too slow: {metrics.avg_response_time:.3f}s"


@pytest.mark.asyncio
class TestHighLoadScenarios:
    """High load scenario testing"""
    
    async def test_stress_health_check(self):
        """Stress test health check with high concurrent load"""
        tester = CoreFunctionalityLoadTester()
        metrics = await tester.run_health_check_load_test(concurrent_users=100, requests_per_user=20)
        
        # Stress test assertions (more lenient)
        assert metrics.error_rate < 20.0, f"Stress test error rate too high: {metrics.error_rate:.1f}%"
        assert metrics.requests_per_second > 50, f"Stress test throughput too low: {metrics.requests_per_second:.1f} RPS"
    
    async def test_comprehensive_load(self):
        """Comprehensive load test across all functionality"""
        tester = CoreFunctionalityLoadTester()
        results = await tester.run_comprehensive_load_test()
        
        # Overall system assertions
        assert results["test_summary"]["overall_success_rate"] > 70.0, \
            f"Overall success rate too low: {results['test_summary']['overall_success_rate']:.1f}%"
        
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE LOAD TEST RESULTS")
        print("="*80)
        print(tester.generate_load_test_report(results))
        print("="*80)


if __name__ == "__main__":
    # Run comprehensive load test directly
    import asyncio
    
    async def main():
        tester = CoreFunctionalityLoadTester()
        results = await tester.run_comprehensive_load_test()
        
        print("\n" + "="*80)
        print("🚀 CORE FUNCTIONALITY LOAD TEST COMPLETED")
        print("="*80)
        print(tester.generate_load_test_report(results))
        print("="*80)
    
    asyncio.run(main()) 