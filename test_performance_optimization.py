"""
Performance Optimization Testing Script
Task 2.1: Performance & Caching - Validation

Tests:
- Cache performance improvements
- Database optimization benefits
- API response time improvements
- System resource usage
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import httpx
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceTester:
    """
    Performance testing suite for AI Assistant MVP
    
    Validates:
    - Response time improvements with caching
    - Cache hit rates and effectiveness
    - Database optimization benefits
    - System stability under load
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {}
        
        # Test credentials
        self.admin_token = None
        self.user_token = None
        
    async def authenticate(self):
        """Authenticate test users"""
        try:
            async with httpx.AsyncClient() as client:
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
                else:
                    logger.error(f"❌ User authentication failed: {user_response.status_code}")
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
    
    async def test_api_response_times(self, endpoint: str, token: str, iterations: int = 10) -> Dict[str, Any]:
        """Test API response times with and without caching"""
        headers = {"Authorization": f"Bearer {token}"}
        response_times = []
        cache_hits = 0
        
        async with httpx.AsyncClient() as client:
            for i in range(iterations):
                start_time = time.time()
                
                try:
                    response = await client.get(f"{self.base_url}{endpoint}", headers=headers)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        response_times.append(response_time)
                        
                        # Check if this was likely a cache hit (faster response)
                        if i > 0 and response_time < response_times[0] * 0.5:
                            cache_hits += 1
                    
                    # Small delay between requests
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Request failed: {e}")
        
        if response_times:
            return {
                "endpoint": endpoint,
                "iterations": iterations,
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "median_response_time": statistics.median(response_times),
                "estimated_cache_hits": cache_hits,
                "cache_hit_rate": (cache_hits / max(iterations - 1, 1)) * 100,
                "all_response_times": response_times
            }
        else:
            return {"error": "No successful responses"}
    
    async def test_cache_effectiveness(self) -> Dict[str, Any]:
        """Test cache effectiveness across multiple endpoints"""
        test_endpoints = [
            "/api/v1/budget/status",
            "/api/v1/budget/usage-history",
            "/api/v1/health",
            "/api/v1/performance/cache/stats"
        ]
        
        cache_results = {}
        
        for endpoint in test_endpoints:
            token = self.admin_token if "performance" in endpoint else self.user_token
            if token:
                logger.info(f"Testing cache performance for: {endpoint}")
                result = await self.test_api_response_times(endpoint, token, iterations=10)
                cache_results[endpoint] = result
            else:
                logger.warning(f"No token available for endpoint: {endpoint}")
        
        return cache_results
    
    async def test_database_performance(self) -> Dict[str, Any]:
        """Test database performance improvements"""
        if not self.admin_token:
            return {"error": "Admin token not available"}
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            async with httpx.AsyncClient() as client:
                # Test database stats endpoint
                response = await client.get(
                    f"{self.base_url}/api/v1/performance/database/stats",
                    headers=headers
                )
                
                if response.status_code == 200:
                    db_stats = response.json()["data"]
                    
                    return {
                        "database_performance": {
                            "avg_response_time": db_stats["connection_stats"]["avg_response_time"],
                            "total_queries": db_stats["connection_stats"]["total_queries"],
                            "slow_queries": db_stats["connection_stats"]["slow_queries"],
                            "pool_size": db_stats["pool_stats"]["pool_size"],
                            "active_connections": db_stats["pool_stats"]["pool_active_connections"]
                        },
                        "optimization_recommendations": db_stats.get("optimization_report", {})
                    }
                else:
                    return {"error": f"Database stats request failed: {response.status_code}"}
                    
        except Exception as e:
            return {"error": f"Database performance test failed: {e}"}
    
    async def test_system_health(self) -> Dict[str, Any]:
        """Test overall system health and performance"""
        if not self.user_token:
            return {"error": "User token not available"}
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        try:
            async with httpx.AsyncClient() as client:
                # Test system health endpoint
                response = await client.get(
                    f"{self.base_url}/api/v1/performance/system/health",
                    headers=headers
                )
                
                if response.status_code == 200:
                    health_data = response.json()["data"]
                    
                    # Test performance summary
                    summary_response = await client.get(
                        f"{self.base_url}/api/v1/performance/metrics/summary",
                        headers=headers
                    )
                    
                    performance_summary = {}
                    if summary_response.status_code == 200:
                        performance_summary = summary_response.json()["data"]
                    
                    return {
                        "system_health": health_data,
                        "performance_summary": performance_summary
                    }
                else:
                    return {"error": f"Health check failed: {response.status_code}"}
                    
        except Exception as e:
            return {"error": f"System health test failed: {e}"}
    
    async def test_load_simulation(self, concurrent_requests: int = 20) -> Dict[str, Any]:
        """Simulate concurrent load and measure performance"""
        if not self.user_token:
            return {"error": "User token not available"}
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        endpoint = "/api/v1/budget/status"
        
        async def make_request():
            async with httpx.AsyncClient() as client:
                start_time = time.time()
                try:
                    response = await client.get(f"{self.base_url}{endpoint}", headers=headers)
                    response_time = time.time() - start_time
                    return {
                        "success": response.status_code == 200,
                        "response_time": response_time,
                        "status_code": response.status_code
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "response_time": time.time() - start_time,
                        "error": str(e)
                    }
        
        logger.info(f"Simulating load with {concurrent_requests} concurrent requests...")
        
        # Execute concurrent requests
        start_time = time.time()
        tasks = [make_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_requests = [r for r in results if isinstance(r, dict) and not r.get("success")]
        
        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            
            return {
                "concurrent_requests": concurrent_requests,
                "total_time": total_time,
                "successful_requests": len(successful_requests),
                "failed_requests": len(failed_requests),
                "success_rate": (len(successful_requests) / concurrent_requests) * 100,
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "requests_per_second": concurrent_requests / total_time
            }
        else:
            return {
                "error": "No successful requests in load test",
                "failed_requests": len(failed_requests),
                "total_requests": concurrent_requests
            }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive performance test suite"""
        logger.info("🚀 Starting comprehensive performance testing...")
        
        # Authenticate first
        await self.authenticate()
        
        if not self.user_token:
            return {"error": "Authentication failed - cannot proceed with tests"}
        
        test_results = {
            "test_timestamp": time.time(),
            "test_suite": "Phase 2: Performance Optimization Validation"
        }
        
        # Test 1: Cache effectiveness
        logger.info("📊 Testing cache effectiveness...")
        test_results["cache_effectiveness"] = await self.test_cache_effectiveness()
        
        # Test 2: Database performance
        logger.info("🗄️ Testing database performance...")
        test_results["database_performance"] = await self.test_database_performance()
        
        # Test 3: System health
        logger.info("🏥 Testing system health...")
        test_results["system_health"] = await self.test_system_health()
        
        # Test 4: Load simulation
        logger.info("⚡ Testing load simulation...")
        test_results["load_simulation"] = await self.test_load_simulation(concurrent_requests=20)
        
        # Calculate overall performance score
        performance_score = self._calculate_performance_score(test_results)
        test_results["overall_performance_score"] = performance_score
        
        return test_results
    
    def _calculate_performance_score(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall performance score"""
        score = 100
        details = []
        
        # Check cache effectiveness
        cache_results = results.get("cache_effectiveness", {})
        total_cache_hits = 0
        total_tests = 0
        
        for endpoint, result in cache_results.items():
            if isinstance(result, dict) and "cache_hit_rate" in result:
                hit_rate = result["cache_hit_rate"]
                total_cache_hits += hit_rate
                total_tests += 1
        
        avg_cache_hit_rate = total_cache_hits / max(total_tests, 1)
        if avg_cache_hit_rate < 30:
            score -= 20
            details.append(f"Low cache hit rate: {avg_cache_hit_rate:.1f}%")
        
        # Check database performance
        db_results = results.get("database_performance", {})
        if isinstance(db_results, dict) and "database_performance" in db_results:
            avg_db_time = db_results["database_performance"].get("avg_response_time", 0)
            if avg_db_time > 0.1:  # >100ms
                score -= 15
                details.append(f"Slow database responses: {avg_db_time:.3f}s")
        
        # Check load test results
        load_results = results.get("load_simulation", {})
        if isinstance(load_results, dict):
            success_rate = load_results.get("success_rate", 0)
            if success_rate < 95:
                score -= 15
                details.append(f"Low success rate under load: {success_rate:.1f}%")
            
            avg_response_time = load_results.get("avg_response_time", 0)
            if avg_response_time > 0.5:  # >500ms
                score -= 10
                details.append(f"Slow responses under load: {avg_response_time:.3f}s")
        
        # Determine grade
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "score": max(0, score),
            "grade": grade,
            "details": details,
            "cache_hit_rate": avg_cache_hit_rate
        }
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted test results"""
        print("\n" + "="*80)
        print("🚀 AI ASSISTANT MVP - PERFORMANCE TEST RESULTS")
        print("="*80)
        
        # Overall score
        performance = results.get("overall_performance_score", {})
        score = performance.get("score", 0)
        grade = performance.get("grade", "Unknown")
        
        print(f"\n📊 OVERALL PERFORMANCE SCORE: {score}/100 (Grade: {grade})")
        
        if performance.get("details"):
            print("\n⚠️ PERFORMANCE ISSUES:")
            for detail in performance["details"]:
                print(f"   • {detail}")
        
        # Cache effectiveness
        print(f"\n💾 CACHE PERFORMANCE:")
        cache_results = results.get("cache_effectiveness", {})
        for endpoint, result in cache_results.items():
            if isinstance(result, dict) and "avg_response_time" in result:
                print(f"   {endpoint}:")
                print(f"     • Avg Response Time: {result['avg_response_time']:.3f}s")
                print(f"     • Cache Hit Rate: {result.get('cache_hit_rate', 0):.1f}%")
        
        # Database performance
        print(f"\n🗄️ DATABASE PERFORMANCE:")
        db_results = results.get("database_performance", {})
        if isinstance(db_results, dict) and "database_performance" in db_results:
            db_perf = db_results["database_performance"]
            print(f"   • Avg Query Time: {db_perf.get('avg_response_time', 0):.3f}s")
            print(f"   • Total Queries: {db_perf.get('total_queries', 0)}")
            print(f"   • Active Connections: {db_perf.get('active_connections', 0)}")
        
        # Load simulation
        print(f"\n⚡ LOAD TEST RESULTS:")
        load_results = results.get("load_simulation", {})
        if isinstance(load_results, dict):
            print(f"   • Concurrent Requests: {load_results.get('concurrent_requests', 0)}")
            print(f"   • Success Rate: {load_results.get('success_rate', 0):.1f}%")
            print(f"   • Avg Response Time: {load_results.get('avg_response_time', 0):.3f}s")
            print(f"   • Requests/Second: {load_results.get('requests_per_second', 0):.1f}")
        
        print("\n" + "="*80)

async def main():
    """Main test execution function"""
    tester = PerformanceTester()
    
    print("🔧 Starting AI Assistant MVP Performance Testing...")
    print("📋 Test Suite: Phase 2 Performance Optimization Validation")
    
    try:
        results = await tester.run_comprehensive_test()
        tester.print_results(results)
        
        # Save results to file
        import json
        with open("performance_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: performance_test_results.json")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 