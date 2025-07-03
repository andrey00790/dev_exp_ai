#!/usr/bin/env python3
"""
Simple E2E Tests - работает с текущим API
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List

class SimpleE2ETester:
    """Простые E2E тесты"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.session = None
        self.results = []
        
    async def setup(self):
        """Setup test environment"""
        self.session = aiohttp.ClientSession()
        return True
    
    async def cleanup(self):
        """Cleanup test environment"""
        if self.session:
            await self.session.close()
    
    async def add_result(self, name: str, status: str, duration: float, details: Dict[str, Any]):
        """Add test result"""
        self.results.append({
            "name": name,
            "status": status,
            "duration": duration,
            "details": details
        })
    
    async def test_server_running(self):
        """Test if server is running"""
        start_time = time.time()
        
        try:
            # Try multiple endpoints to see which one works
            endpoints_to_try = [
                "/health",
                "/api/v1/health", 
                "/docs",
                "/"
            ]
            
            working_endpoints = []
            for endpoint in endpoints_to_try:
                try:
                    async with self.session.get(f"{self.backend_url}{endpoint}") as response:
                        if response.status in [200, 307]:  # 307 is redirect
                            working_endpoints.append(endpoint)
                except:
                    pass
            
            if working_endpoints:
                duration = time.time() - start_time
                await self.add_result(
                    "Server Running Check",
                    "PASSED",
                    duration,
                    {
                        "working_endpoints": working_endpoints,
                        "total_checked": len(endpoints_to_try)
                    }
                )
                return True
            else:
                duration = time.time() - start_time
                await self.add_result(
                    "Server Running Check",
                    "FAILED",
                    duration,
                    {"error": "No endpoints responding"}
                )
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            await self.add_result(
                "Server Running Check",
                "FAILED",
                duration,
                {"error": str(e)}
            )
            return False
    
    async def test_openapi_docs(self):
        """Test OpenAPI documentation"""
        start_time = time.time()
        
        try:
            async with self.session.get(f"{self.backend_url}/openapi.json") as response:
                if response.status == 200:
                    data = await response.json()
                    endpoint_count = sum(len(methods) for methods in data.get("paths", {}).values())
                    
                    duration = time.time() - start_time
                    await self.add_result(
                        "OpenAPI Documentation",
                        "PASSED",
                        duration,
                        {
                            "title": data.get("info", {}).get("title", "Unknown"),
                            "version": data.get("info", {}).get("version", "Unknown"),
                            "endpoint_count": endpoint_count
                        }
                    )
                    return True
                else:
                    duration = time.time() - start_time 
                    await self.add_result(
                        "OpenAPI Documentation",
                        "FAILED",
                        duration,
                        {"error": f"HTTP {response.status}"}
                    )
                    return False
                    
        except Exception as e:
            duration = time.time() - start_time
            await self.add_result(
                "OpenAPI Documentation",
                "FAILED",
                duration,
                {"error": str(e)}
            )
            return False
    
    async def test_basic_endpoints(self):
        """Test basic endpoints"""
        start_time = time.time()
        
        try:
            # Test basic endpoints without authentication
            endpoints_to_test = [
                {"method": "GET", "path": "/health", "expected": 200},
                {"method": "GET", "path": "/docs", "expected": [200, 307]},
                {"method": "GET", "path": "/openapi.json", "expected": 200},
            ]
            
            results = []
            for endpoint in endpoints_to_test:
                try:
                    if endpoint["method"] == "GET":
                        async with self.session.get(f"{self.backend_url}{endpoint['path']}") as response:
                            expected = endpoint["expected"]
                            if isinstance(expected, list):
                                success = response.status in expected
                            else:
                                success = response.status == expected
                            
                            results.append({
                                "path": endpoint["path"],
                                "status": response.status,
                                "success": success
                            })
                except Exception as e:
                    results.append({
                        "path": endpoint["path"],
                        "status": 0,
                        "success": False,
                        "error": str(e)
                    })
            
            successful = sum(1 for r in results if r["success"])
            total = len(results)
            
            duration = time.time() - start_time
            await self.add_result(
                "Basic Endpoints Test",
                "PASSED" if successful > 0 else "FAILED",
                duration,
                {
                    "successful_endpoints": successful,
                    "total_endpoints": total,
                    "success_rate": f"{(successful/total)*100:.1f}%",
                    "results": results
                }
            )
            return successful > 0
            
        except Exception as e:
            duration = time.time() - start_time
            await self.add_result(
                "Basic Endpoints Test",
                "FAILED",
                duration,
                {"error": str(e)}
            )
            return False
    
    async def test_search_endpoints(self):
        """Test search endpoints"""
        start_time = time.time()
        
        try:
            # Try different search endpoints
            search_endpoints = [
                {"path": "/api/v1/search", "method": "POST", "data": {"query": "test", "limit": 5}},
                {"path": "/api/v1/vector-search/health", "method": "GET"},
            ]
            
            results = []
            for endpoint in search_endpoints:
                try:
                    if endpoint["method"] == "POST":
                        async with self.session.post(
                            f"{self.backend_url}{endpoint['path']}", 
                            json=endpoint.get("data", {})
                        ) as response:
                            results.append({
                                "path": endpoint["path"],
                                "method": endpoint["method"],
                                "status": response.status,
                                "success": response.status in [200, 401, 422]  # Accept auth errors
                            })
                    else:
                        async with self.session.get(f"{self.backend_url}{endpoint['path']}") as response:
                            results.append({
                                "path": endpoint["path"],
                                "method": endpoint["method"],
                                "status": response.status,
                                "success": response.status in [200, 401]  # Accept auth errors
                            })
                except Exception as e:
                    results.append({
                        "path": endpoint["path"],
                        "method": endpoint["method"],
                        "status": 0,
                        "success": False,
                        "error": str(e)
                    })
            
            successful = sum(1 for r in results if r["success"])
            total = len(results)
            
            duration = time.time() - start_time
            await self.add_result(
                "Search Endpoints Test",
                "PASSED" if successful > 0 else "FAILED",
                duration,
                {
                    "successful_endpoints": successful,
                    "total_endpoints": total,
                    "results": results
                }
            )
            return successful > 0
            
        except Exception as e:
            duration = time.time() - start_time
            await self.add_result(
                "Search Endpoints Test",
                "FAILED",
                duration,
                {"error": str(e)}
            )
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Simple E2E Tests...")
        
        await self.setup()
        
        tests = [
            self.test_server_running,
            self.test_openapi_docs,
            self.test_basic_endpoints,
            self.test_search_endpoints
        ]
        
        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {e}")
                results.append(False)
        
        await self.cleanup()
        
        # Print results
        passed = sum(results)
        total = len(results)
        success_rate = (passed / total) * 100
        
        print(f"\n📊 Simple E2E Test Results:")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 Detailed Results:")
        for result in self.results:
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            print(f"{status_icon} {result['name']}: {result['status']} ({result['duration']:.2f}s)")
            if result["status"] == "FAILED":
                print(f"   Error: {result['details'].get('error', 'Unknown error')}")
            else:
                print(f"   Details: {result['details']}")
        
        return success_rate

async def main():
    """Main test runner"""
    tester = SimpleE2ETester()
    success_rate = await tester.run_all_tests()
    
    if success_rate >= 75.0:
        print(f"\n🎉 E2E tests mostly successful ({success_rate:.1f}%)!")
        return 0
    else:
        print(f"\n⚠️ E2E tests need improvement ({success_rate:.1f}%).")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main()) 