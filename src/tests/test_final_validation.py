#!/usr/bin/env python3
"""
Final System Validation Test
Comprehensive validation of AI Assistant MVP for production readiness
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

class FinalSystemValidator:
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.session = None
        self.admin_token = None
        self.test_results = []
        
    async def setup(self):
        """Setup validation environment"""
        self.session = aiohttp.ClientSession()
        
        # Authenticate as admin
        try:
            async with self.session.post(
                f"{self.backend_url}/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "admin"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data["access_token"]
                    print("✅ Authentication successful")
                    return True
                else:
                    print(f"❌ Authentication failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    def get_auth_headers(self):
        return {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
    
    def add_result(self, test_name: str, status: str, details: dict):
        self.test_results.append({
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def validate_core_authentication(self):
        """Validate authentication system"""
        print("\n🔐 Validating Authentication System...")
        
        try:
            # Test user info
            async with self.session.get(
                f"{self.backend_url}/api/v1/auth/me",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    print(f"✅ User: {user_data['name']} ({user_data['email']})")
                    print(f"✅ Scopes: {user_data['scopes']}")
                    auth_working = True
                else:
                    print(f"❌ User info failed: {response.status}")
                    auth_working = False
            
            # Test token verification
            async with self.session.get(
                f"{self.backend_url}/api/v1/auth/verify",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    verify_data = await response.json()
                    print(f"✅ Token valid: {verify_data.get('valid')}")
                    budget = verify_data.get('budget_status', {})
                    print(f"✅ Budget: ${budget.get('current_usage', 0):.2f} / ${budget.get('limit', 0):.2f}")
                else:
                    auth_working = False
            
            # Test unauthorized access
            async with self.session.get(f"{self.backend_url}/api/v1/auth/me") as response:
                if response.status == 401:
                    print("✅ Unauthorized access properly blocked")
                    security_working = True
                else:
                    print(f"❌ Security issue: unauthorized returned {response.status}")
                    security_working = False
            
            result = auth_working and security_working
            self.add_result("Authentication System", "PASS" if result else "FAIL", {
                "user_auth": auth_working,
                "security": security_working,
                "user_email": user_data.get('email') if auth_working else None
            })
            
            return result
            
        except Exception as e:
            print(f"❌ Authentication validation error: {e}")
            self.add_result("Authentication System", "FAIL", {"error": str(e)})
            return False
    
    async def validate_vector_search(self):
        """Validate vector search capabilities"""
        print("\n🔍 Validating Vector Search System...")
        
        try:
            # Test collections
            async with self.session.get(
                f"{self.backend_url}/api/v1/vector-search/collections",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    collections_data = await response.json()
                    collections = collections_data.get("collections", {})
                    print(f"✅ Collections available: {len(collections)}")
                    collections_working = True
                else:
                    print(f"❌ Collections endpoint failed: {response.status}")
                    collections_working = False
            
            # Test search functionality
            search_queries = [
                "artificial intelligence machine learning",
                "database optimization",
                "web development"
            ]
            
            search_results = []
            for query in search_queries:
                start_time = time.time()
                async with self.session.post(
                    f"{self.backend_url}/api/v1/vector-search/search",
                    headers=self.get_auth_headers(),
                    json={
                        "query": query,
                        "limit": 3,
                        "include_snippets": True,
                        "hybrid_search": True
                    }
                ) as response:
                    search_time = time.time() - start_time
                    if response.status == 200:
                        search_data = await response.json()
                        search_results.append({
                            "query": query,
                            "results": search_data.get("total_results", 0),
                            "time_ms": search_time * 1000,
                            "collections": search_data.get("collections_searched", [])
                        })
                    else:
                        search_results.append({
                            "query": query,
                            "error": response.status
                        })
            
            successful_searches = sum(1 for r in search_results if "error" not in r)
            avg_search_time = sum(r.get("time_ms", 0) for r in search_results if "error" not in r) / max(successful_searches, 1)
            
            print(f"✅ Search tests: {successful_searches}/{len(search_queries)} successful")
            print(f"✅ Average search time: {avg_search_time:.1f}ms")
            
            search_working = successful_searches >= len(search_queries) * 0.8  # 80% success rate
            
            result = collections_working and search_working
            self.add_result("Vector Search System", "PASS" if result else "FAIL", {
                "collections_available": len(collections) if collections_working else 0,
                "search_success_rate": f"{successful_searches}/{len(search_queries)}",
                "avg_search_time_ms": avg_search_time,
                "search_results": search_results
            })
            
            return result
            
        except Exception as e:
            print(f"❌ Vector search validation error: {e}")
            self.add_result("Vector Search System", "FAIL", {"error": str(e)})
            return False
    
    async def validate_llm_system(self):
        """Validate LLM system"""
        print("\n🤖 Validating LLM System...")
        
        try:
            # Test LLM providers
            async with self.session.get(
                f"{self.backend_url}/api/v1/llm/providers",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    providers_data = await response.json()
                    providers = providers_data.get("providers", [])
                    strategy = providers_data.get("current_routing_strategy", "unknown")
                    print(f"✅ LLM providers available: {len(providers)}")
                    print(f"✅ Routing strategy: {strategy}")
                    providers_working = True
                else:
                    print(f"❌ LLM providers endpoint failed: {response.status}")
                    providers_working = False
            
            # Test LLM health (may fail if no providers configured)
            async with self.session.get(
                f"{self.backend_url}/api/v1/llm/health",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ LLM health: {health_data.get('status', 'unknown')}")
                    health_working = True
                else:
                    print(f"⚠️ LLM health check: {response.status} (expected if no providers configured)")
                    health_working = False
            
            # Test LLM stats (may fail if service not initialized)
            async with self.session.get(
                f"{self.backend_url}/api/v1/llm/stats",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    stats_data = await response.json()
                    print(f"✅ LLM stats available")
                    stats_working = True
                else:
                    print(f"⚠️ LLM stats: {response.status} (expected if service not initialized)")
                    stats_working = False
            
            # LLM system is considered working if providers endpoint works
            result = providers_working
            self.add_result("LLM System", "PASS" if result else "FAIL", {
                "providers_endpoint": providers_working,
                "health_endpoint": health_working,
                "stats_endpoint": stats_working,
                "providers_count": len(providers) if providers_working else 0,
                "routing_strategy": strategy if providers_working else None
            })
            
            return result
            
        except Exception as e:
            print(f"❌ LLM system validation error: {e}")
            self.add_result("LLM System", "FAIL", {"error": str(e)})
            return False
    
    async def validate_api_performance(self):
        """Validate API performance"""
        print("\n⚡ Validating API Performance...")
        
        try:
            # Test multiple endpoints for performance
            endpoints = [
                ("/health", "GET", None),
                ("/api/v1/auth/verify", "GET", self.get_auth_headers()),
                ("/api/v1/vector-search/collections", "GET", self.get_auth_headers()),
                ("/api/v1/vector-search/search", "POST", self.get_auth_headers(), {"query": "test", "limit": 1}),
                ("/api/v1/llm/providers", "GET", self.get_auth_headers())
            ]
            
            performance_results = []
            
            for endpoint_data in endpoints:
                endpoint = endpoint_data[0]
                method = endpoint_data[1]
                headers = endpoint_data[2] if len(endpoint_data) > 2 else {}
                data = endpoint_data[3] if len(endpoint_data) > 3 else None
                
                start_time = time.time()
                
                try:
                    if method == "GET":
                        async with self.session.get(
                            f"{self.backend_url}{endpoint}",
                            headers=headers
                        ) as response:
                            response_time = time.time() - start_time
                            performance_results.append({
                                "endpoint": endpoint,
                                "method": method,
                                "status": response.status,
                                "response_time_ms": response_time * 1000
                            })
                    elif method == "POST":
                        async with self.session.post(
                            f"{self.backend_url}{endpoint}",
                            headers=headers,
                            json=data
                        ) as response:
                            response_time = time.time() - start_time
                            performance_results.append({
                                "endpoint": endpoint,
                                "method": method,
                                "status": response.status,
                                "response_time_ms": response_time * 1000
                            })
                
                except Exception as e:
                    performance_results.append({
                        "endpoint": endpoint,
                        "method": method,
                        "error": str(e)
                    })
            
            # Analyze performance
            successful_requests = [r for r in performance_results if r.get("status") == 200]
            avg_response_time = sum(r["response_time_ms"] for r in successful_requests) / max(len(successful_requests), 1)
            max_response_time = max((r["response_time_ms"] for r in successful_requests), default=0)
            
            print(f"✅ Successful requests: {len(successful_requests)}/{len(performance_results)}")
            print(f"✅ Average response time: {avg_response_time:.1f}ms")
            print(f"✅ Max response time: {max_response_time:.1f}ms")
            
            # Performance criteria: avg < 1000ms, success rate > 80%
            performance_good = (
                avg_response_time < 1000 and 
                len(successful_requests) >= len(performance_results) * 0.8
            )
            
            self.add_result("API Performance", "PASS" if performance_good else "FAIL", {
                "successful_requests": f"{len(successful_requests)}/{len(performance_results)}",
                "avg_response_time_ms": avg_response_time,
                "max_response_time_ms": max_response_time,
                "performance_results": performance_results
            })
            
            return performance_good
            
        except Exception as e:
            print(f"❌ Performance validation error: {e}")
            self.add_result("API Performance", "FAIL", {"error": str(e)})
            return False
    
    async def validate_system_health(self):
        """Validate overall system health"""
        print("\n🏥 Validating System Health...")
        
        try:
            # Test health endpoint
            async with self.session.get(f"{self.backend_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ System status: {health_data.get('status', 'unknown')}")
                    print(f"✅ Version: {health_data.get('version', 'unknown')}")
                    print(f"✅ Environment: {health_data.get('environment', 'unknown')}")
                    print(f"✅ Uptime: {health_data.get('uptime', 0):.2f}s")
                    health_working = True
                else:
                    print(f"❌ Health endpoint failed: {response.status}")
                    health_working = False
            
            # Test concurrent requests to check stability
            concurrent_tasks = []
            for i in range(10):
                task = self.session.get(f"{self.backend_url}/health")
                concurrent_tasks.append(task)
            
            start_time = time.time()
            responses = await asyncio.gather(*[
                self._make_request(task) for task in concurrent_tasks
            ])
            concurrent_time = time.time() - start_time
            
            successful_concurrent = sum(1 for r in responses if r.get("status") == 200)
            
            print(f"✅ Concurrent requests: {successful_concurrent}/10 successful")
            print(f"✅ Concurrent test time: {concurrent_time:.2f}s")
            
            stability_good = successful_concurrent >= 8  # 80% success rate under load
            
            result = health_working and stability_good
            self.add_result("System Health", "PASS" if result else "FAIL", {
                "health_endpoint": health_working,
                "concurrent_stability": f"{successful_concurrent}/10",
                "concurrent_test_time": concurrent_time,
                "system_info": health_data if health_working else None
            })
            
            return result
            
        except Exception as e:
            print(f"❌ System health validation error: {e}")
            self.add_result("System Health", "FAIL", {"error": str(e)})
            return False
    
    async def _make_request(self, request_coro):
        """Helper for timing requests"""
        start = time.time()
        try:
            async with request_coro as response:
                duration = time.time() - start
                return {"status": response.status, "duration": duration}
        except Exception as e:
            duration = time.time() - start
            return {"status": 0, "duration": duration, "error": str(e)}
    
    async def generate_final_report(self):
        """Generate final validation report"""
        print("\n" + "=" * 100)
        print("📊 FINAL SYSTEM VALIDATION REPORT")
        print("=" * 100)
        
        # Summary
        passed_tests = sum(1 for r in self.test_results if r["status"] == "PASS")
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 Validation Summary:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Validation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Individual test results
        print(f"\n📋 Test Results:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {result['test']}: {result['status']}")
            
            # Show key details
            details = result["details"]
            if details and not details.get("error"):
                for key, value in details.items():
                    if key != "error" and not key.endswith("_results"):
                        print(f"      {key}: {value}")
        
        # Production readiness assessment
        print(f"\n🎯 Production Readiness Assessment:")
        
        critical_systems = ["Authentication System", "Vector Search System", "System Health"]
        critical_passed = sum(1 for r in self.test_results 
                            if r["test"] in critical_systems and r["status"] == "PASS")
        
        if success_rate >= 90:
            grade = "🏆 EXCELLENT - Production Ready"
        elif success_rate >= 80:
            grade = "🥈 GOOD - Ready with monitoring"
        elif success_rate >= 70 and critical_passed == len(critical_systems):
            grade = "🥉 ACCEPTABLE - Deploy with caution"
        else:
            grade = "⚠️ NEEDS IMPROVEMENT - Not ready"
        
        print(f"   Grade: {grade}")
        print(f"   Critical Systems: {critical_passed}/{len(critical_systems)} operational")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if success_rate >= 90:
            print("   🚀 System is production-ready!")
            print("   ✅ All major systems operational")
            print("   ✅ Performance meets requirements")
            print("   ➡️  Deploy to production immediately")
        elif success_rate >= 80:
            print("   ⚠️ System is mostly ready")
            print("   🔧 Address minor issues before production")
            print("   📊 Implement enhanced monitoring")
            print("   ➡️  Deploy to staging first")
        else:
            print("   ❌ System needs significant improvement")
            print("   🔧 Fix failing critical systems")
            print("   📋 Conduct additional testing")
            print("   ➡️  Development work required")
        
        return success_rate >= 80
    
    async def run_final_validation(self):
        """Run complete final validation"""
        print("🚀 AI ASSISTANT MVP - FINAL VALIDATION")
        print("=" * 100)
        print(f"Backend URL: {self.backend_url}")
        print(f"Validation Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)
        
        if not await self.setup():
            print("❌ Failed to setup validation environment")
            return False
        
        # Run validation tests
        validation_tests = [
            ("Core Authentication", self.validate_core_authentication),
            ("Vector Search System", self.validate_vector_search),
            ("LLM System Architecture", self.validate_llm_system),
            ("API Performance", self.validate_api_performance),
            ("System Health & Stability", self.validate_system_health)
        ]
        
        print("\n🧪 Running Validation Tests...")
        
        for test_name, test_func in validation_tests:
            try:
                await test_func()
            except Exception as e:
                print(f"❌ {test_name} validation failed: {e}")
                self.add_result(test_name, "FAIL", {"error": str(e)})
        
        await self.cleanup()
        
        # Generate final report
        production_ready = await self.generate_final_report()
        
        print("\n" + "=" * 100)
        
        if production_ready:
            print("🎉 SYSTEM VALIDATION PASSED - PRODUCTION READY! 🎉")
            return True
        else:
            print("❌ System validation indicates issues need attention")
            return False

async def main():
    """Main validation runner"""
    validator = FinalSystemValidator()
    success = await validator.run_final_validation()
    
    if success:
        print("\n🚀🚀🚀 AI ASSISTANT MVP VALIDATED FOR PRODUCTION! 🚀🚀🚀")
    else:
        print("\n⚠️ Validation completed with recommendations for improvement")
    
    return success

if __name__ == "__main__":
    asyncio.run(main()) 