#!/usr/bin/env python3
"""
System Load E2E Tests
Tests the AI Assistant MVP under realistic load conditions
"""

import asyncio
import aiohttp
import json
import time
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import random

@dataclass
class LoadTestResult:
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    requests_per_second: float
    error_rate: float
    duration: float

class SystemLoadE2ETester:
    """Load testing for the complete AI Assistant system"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.admin_token = None
        self.results: List[LoadTestResult] = []
        
    async def setup(self):
        """Setup load test environment"""
        # Authenticate and get token
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.backend_url}/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "admin"}
            ) as response:
                if response.status == 200:
                    auth_data = await response.json()
                    self.admin_token = auth_data["access_token"]
                    return True
                return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
    
    async def make_request(self, session: aiohttp.ClientSession, method: str, url: str, **kwargs):
        """Make a single request and time it"""
        start_time = time.time()
        try:
            if method.upper() == "GET":
                async with session.get(url, **kwargs) as response:
                    duration = time.time() - start_time
                    return {
                        "success": True,
                        "status": response.status,
                        "duration": duration,
                        "error": None
                    }
            elif method.upper() == "POST":
                async with session.post(url, **kwargs) as response:
                    duration = time.time() - start_time
                    return {
                        "success": True,
                        "status": response.status, 
                        "duration": duration,
                        "error": None
                    }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "success": False,
                "status": 0,
                "duration": duration,
                "error": str(e)
            }
    
    async def run_concurrent_load_test(self, 
                                     test_name: str,
                                     url: str,
                                     method: str = "GET",
                                     concurrent_users: int = 10,
                                     requests_per_user: int = 10,
                                     data: Dict = None):
        """Run concurrent load test"""
        print(f"\n🔥 Load Test: {test_name}")
        print(f"   Concurrent users: {concurrent_users}")
        print(f"   Requests per user: {requests_per_user}")
        print(f"   Total requests: {concurrent_users * requests_per_user}")
        
        async def user_session(user_id: int):
            """Simulate a single user session"""
            results = []
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for i in range(requests_per_user):
                    kwargs = {"headers": self.get_auth_headers()}
                    if data:
                        kwargs["json"] = data
                    
                    result = await self.make_request(session, method, url, **kwargs)
                    results.append(result)
                    
                    # Small delay between requests to simulate realistic usage
                    await asyncio.sleep(random.uniform(0.1, 0.3))
            
            return results
        
        # Start load test
        start_time = time.time()
        
        # Create concurrent user sessions
        tasks = [user_session(user_id) for user_id in range(concurrent_users)]
        user_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect all results
        all_results = []
        for user_result in user_results:
            if isinstance(user_result, list):
                all_results.extend(user_result)
            else:
                # Handle exceptions
                all_results.append({
                    "success": False,
                    "status": 0,
                    "duration": 0,
                    "error": str(user_result)
                })
        
        # Calculate statistics
        total_duration = time.time() - start_time
        total_requests = len(all_results)
        successful_requests = sum(1 for r in all_results if r["success"] and r["status"] == 200)
        failed_requests = total_requests - successful_requests
        
        # Response time statistics
        successful_durations = [r["duration"] for r in all_results if r["success"] and r["status"] == 200]
        
        if successful_durations:
            avg_response_time = statistics.mean(successful_durations)
            min_response_time = min(successful_durations)
            max_response_time = max(successful_durations)
            p95_response_time = statistics.quantiles(successful_durations, n=20)[18]  # 95th percentile
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = 0
        
        requests_per_second = total_requests / total_duration if total_duration > 0 else 0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Create result
        result = LoadTestResult(
            test_name=test_name,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            duration=total_duration
        )
        
        self.results.append(result)
        
        # Print results
        print(f"   ✅ Completed in {total_duration:.2f}s")
        print(f"   📊 Success rate: {(successful_requests/total_requests*100):.1f}%")
        print(f"   ⚡ Avg response time: {avg_response_time*1000:.1f}ms")
        print(f"   🚀 Requests/sec: {requests_per_second:.2f}")
        print(f"   📈 95th percentile: {p95_response_time*1000:.1f}ms")
        
        return result.error_rate < 5.0 and result.avg_response_time < 2.0  # Success criteria
    
    async def test_authentication_load(self):
        """Test authentication system under load"""
        return await self.run_concurrent_load_test(
            test_name="Authentication Load",
            url=f"{self.backend_url}/api/v1/auth/verify",
            method="GET",
            concurrent_users=20,
            requests_per_user=15
        )
    
    async def test_vector_search_load(self):
        """Test vector search system under load"""
        search_queries = [
            "artificial intelligence machine learning",
            "database optimization performance",
            "web development best practices",
            "security authentication JWT",
            "microservices architecture patterns",
            "API design REST GraphQL",
            "data science analytics",
            "cloud computing AWS Azure",
            "DevOps CI/CD automation",
            "monitoring logging metrics"
        ]
        
        # Test with varied search queries
        query = random.choice(search_queries)
        return await self.run_concurrent_load_test(
            test_name="Vector Search Load",
            url=f"{self.backend_url}/api/v1/vector-search/search",
            method="POST", 
            concurrent_users=15,
            requests_per_user=8,
            data={
                "query": query,
                "limit": 5,
                "include_snippets": True,
                "hybrid_search": True
            }
        )
    
    async def test_collections_load(self):
        """Test collections endpoint under load"""
        return await self.run_concurrent_load_test(
            test_name="Collections Load",
            url=f"{self.backend_url}/api/v1/vector-search/collections",
            method="GET",
            concurrent_users=25,
            requests_per_user=10
        )
    
    async def test_llm_providers_load(self):
        """Test LLM providers endpoint under load"""
        return await self.run_concurrent_load_test(
            test_name="LLM Providers Load",
            url=f"{self.backend_url}/api/v1/llm/providers",
            method="GET",
            concurrent_users=20,
            requests_per_user=12
        )
    
    async def test_health_check_load(self):
        """Test health check endpoint under extreme load"""
        return await self.run_concurrent_load_test(
            test_name="Health Check Load",
            url=f"{self.backend_url}/health",
            method="GET",
            concurrent_users=50,
            requests_per_user=20
        )
    
    async def test_mixed_workload(self):
        """Test mixed realistic workload"""
        print(f"\n🌊 Mixed Workload Test")
        print("   Simulating realistic user behavior with mixed requests")
        
        async def realistic_user_session(user_id: int):
            """Simulate realistic user behavior"""
            session_results = []
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = self.get_auth_headers()
                
                # User workflow: login verification -> check collections -> search -> check providers
                workflows = [
                    ("auth/verify", "GET", {}),
                    ("vector-search/collections", "GET", {}),
                    ("vector-search/search", "POST", {
                        "query": f"user {user_id} search query",
                        "limit": 3
                    }),
                    ("llm/providers", "GET", {}),
                    ("auth/budget", "GET", {}),
                ]
                
                for endpoint, method, data in workflows:
                    url = f"{self.backend_url}/api/v1/{endpoint}"
                    kwargs = {"headers": headers}
                    if data:
                        kwargs["json"] = data
                    
                    result = await self.make_request(session, method, url, **kwargs)
                    session_results.append(result)
                    
                    # Realistic delay between actions
                    await asyncio.sleep(random.uniform(0.5, 2.0))
            
            return session_results
        
        # Run mixed workload
        start_time = time.time()
        concurrent_users = 12
        
        tasks = [realistic_user_session(user_id) for user_id in range(concurrent_users)]
        user_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect results
        all_results = []
        for user_result in user_results:
            if isinstance(user_result, list):
                all_results.extend(user_result)
        
        # Calculate stats
        total_duration = time.time() - start_time
        total_requests = len(all_results)
        successful_requests = sum(1 for r in all_results if r["success"] and r["status"] == 200)
        
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        print(f"   ✅ Mixed workload completed in {total_duration:.2f}s")
        print(f"   👥 {concurrent_users} concurrent users")
        print(f"   📊 Success rate: {success_rate:.1f}%")
        print(f"   📈 Total requests: {total_requests}")
        
        return success_rate > 95.0
    
    async def test_sustained_load(self):
        """Test system under sustained load"""
        print(f"\n⏰ Sustained Load Test (60 seconds)")
        print("   Testing system stability under continuous load")
        
        async def sustained_requests():
            """Generate sustained requests for 60 seconds"""
            results = []
            timeout = aiohttp.ClientTimeout(total=10)
            end_time = time.time() + 60  # Run for 60 seconds
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = self.get_auth_headers()
                
                while time.time() < end_time:
                    # Alternate between different endpoints
                    endpoints = [
                        ("/health", "GET", {}),
                        ("/api/v1/auth/verify", "GET", {}),
                        ("/api/v1/vector-search/collections", "GET", {}),
                        ("/api/v1/vector-search/search", "POST", {"query": "sustained test", "limit": 2})
                    ]
                    
                    url_suffix, method, data = random.choice(endpoints)
                    url = f"{self.backend_url}{url_suffix}"
                    
                    kwargs = {"headers": headers} if url_suffix != "/health" else {}
                    if data:
                        kwargs["json"] = data
                    
                    result = await self.make_request(session, method, url, **kwargs)
                    results.append(result)
                    
                    await asyncio.sleep(0.1)  # 10 requests per second
            
            return results
        
        # Run sustained load with multiple workers
        start_time = time.time()
        workers = 8
        
        tasks = [sustained_requests() for _ in range(workers)]
        worker_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect results
        all_results = []
        for worker_result in worker_results:
            if isinstance(worker_result, list):
                all_results.extend(worker_result)
        
        # Calculate stats
        duration = time.time() - start_time
        total_requests = len(all_results)
        successful_requests = sum(1 for r in all_results if r["success"] and r["status"] == 200)
        
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        requests_per_second = total_requests / duration if duration > 0 else 0
        
        print(f"   ✅ Sustained load completed in {duration:.2f}s")
        print(f"   📊 Success rate: {success_rate:.1f}%")
        print(f"   🚀 Avg requests/sec: {requests_per_second:.2f}")
        print(f"   📈 Total requests: {total_requests}")
        
        return success_rate > 98.0 and requests_per_second > 50
    
    def generate_load_test_report(self):
        """Generate comprehensive load test report"""
        print("\n" + "=" * 80)
        print("📊 SYSTEM LOAD TEST REPORT")
        print("=" * 80)
        
        if not self.results:
            print("❌ No load test results available")
            return
        
        # Summary statistics
        total_requests = sum(r.total_requests for r in self.results)
        total_successful = sum(r.successful_requests for r in self.results)
        overall_success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0
        
        print(f"📈 Overall Summary:")
        print(f"   Total requests: {total_requests:,}")
        print(f"   Successful requests: {total_successful:,}")
        print(f"   Overall success rate: {overall_success_rate:.2f}%")
        print(f"   Average RPS: {sum(r.requests_per_second for r in self.results) / len(self.results):.2f}")
        
        print(f"\n📋 Individual Test Results:")
        for result in self.results:
            status = "✅ PASS" if result.error_rate < 5.0 and result.avg_response_time < 2.0 else "❌ FAIL"
            print(f"\n{status} {result.test_name}")
            print(f"   Requests: {result.total_requests:,} (Success: {result.successful_requests:,})")
            print(f"   Success rate: {100 - result.error_rate:.1f}%")
            print(f"   Avg response time: {result.avg_response_time*1000:.1f}ms")
            print(f"   95th percentile: {result.p95_response_time*1000:.1f}ms")
            print(f"   Requests/sec: {result.requests_per_second:.2f}")
            print(f"   Duration: {result.duration:.2f}s")
        
        print(f"\n🎯 Performance Benchmarks:")
        print(f"   ✅ Response time < 2s: {sum(1 for r in self.results if r.avg_response_time < 2.0)}/{len(self.results)}")
        print(f"   ✅ Error rate < 5%: {sum(1 for r in self.results if r.error_rate < 5.0)}/{len(self.results)}")
        print(f"   ✅ RPS > 10: {sum(1 for r in self.results if r.requests_per_second > 10)}/{len(self.results)}")
        
        # Performance classification
        if overall_success_rate > 98 and all(r.avg_response_time < 1.0 for r in self.results):
            print(f"\n🏆 PERFORMANCE GRADE: EXCELLENT")
        elif overall_success_rate > 95 and all(r.avg_response_time < 2.0 for r in self.results):
            print(f"\n🥈 PERFORMANCE GRADE: GOOD")
        elif overall_success_rate > 90:
            print(f"\n🥉 PERFORMANCE GRADE: ACCEPTABLE")
        else:
            print(f"\n⚠️ PERFORMANCE GRADE: NEEDS IMPROVEMENT")
    
    async def run_system_load_tests(self):
        """Run complete system load test suite"""
        print("🚀 Starting System Load E2E Tests")
        print("=" * 80)
        
        if not await self.setup():
            print("❌ Failed to setup load test environment")
            return False
        
        # Define load tests
        load_tests = [
            ("Health Check Load", self.test_health_check_load),
            ("Authentication Load", self.test_authentication_load),
            ("Collections Load", self.test_collections_load),
            ("Vector Search Load", self.test_vector_search_load),
            ("LLM Providers Load", self.test_llm_providers_load),
            ("Mixed Workload", self.test_mixed_workload),
            ("Sustained Load", self.test_sustained_load)
        ]
        
        passed_tests = 0
        total_tests = len(load_tests)
        
        for test_name, test_func in load_tests:
            try:
                print(f"\n🧪 Running {test_name}...")
                if await test_func():
                    passed_tests += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
        
        # Generate comprehensive report
        self.generate_load_test_report()
        
        print("\n" + "=" * 80)
        print(f"📊 Load Test Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests >= total_tests * 0.8:  # 80% pass rate for load tests
            print("🎉 SYSTEM LOAD TESTS PASSED!")
            print("\n🚀 System can handle production load!")
            return True
        else:
            print("❌ System load tests indicate performance issues")
            return False

# Test runner
async def main():
    """Main system load test runner"""
    tester = SystemLoadE2ETester()
    success = await tester.run_system_load_tests()
    return success

if __name__ == "__main__":
    asyncio.run(main()) 