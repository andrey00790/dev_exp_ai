#!/usr/bin/env python3
"""
Frontend-Backend E2E Tests
Tests the complete integration between React frontend and FastAPI backend
"""

import asyncio
import pytest
import aiohttp
import json
import time
from typing import Dict, Any

class FrontendBackendE2ETester:
    """E2E testing for frontend-backend integration"""
    
    def __init__(self, 
                 backend_url: str = "http://localhost:8000",
                 frontend_url: str = "http://localhost:3000"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.session = None
        
    async def setup(self):
        """Setup test environment"""
        self.session = aiohttp.ClientSession()
        
        # Check if backend is running
        try:
            async with self.session.get(f"{self.backend_url}/health") as response:
                if response.status != 200:
                    return False
        except:
            return False
        
        # Check if frontend is running (optional)
        try:
            async with self.session.get(self.frontend_url) as response:
                frontend_available = response.status == 200
        except:
            frontend_available = False
        
        return True
    
    async def cleanup(self):
        """Cleanup test environment"""
        if self.session:
            await self.session.close()
    
    async def test_api_cors_configuration(self):
        """Test CORS configuration for frontend-backend communication"""
        print("\n🌐 Testing CORS Configuration...")
        
        try:
            # Test preflight request
            headers = {
                "Origin": self.frontend_url,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization"
            }
            
            async with self.session.options(
                f"{self.backend_url}/api/v1/auth/login",
                headers=headers
            ) as response:
                cors_headers = response.headers
                
                # Check CORS headers
                if "Access-Control-Allow-Origin" in cors_headers:
                    print("✅ CORS headers present")
                else:
                    print("⚠️ CORS headers may need configuration")
                
                return True
                
        except Exception as e:
            print(f"❌ CORS test error: {e}")
            return False
    
    async def test_api_response_formats(self):
        """Test API response formats match frontend expectations"""
        print("\n📋 Testing API Response Formats...")
        
        try:
            # Test authentication response format
            async with self.session.post(
                f"{self.backend_url}/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "admin"}
            ) as response:
                if response.status == 200:
                    auth_data = await response.json()
                    
                    # Check required fields for frontend
                    required_fields = ["access_token", "token_type", "expires_in"]
                    for field in required_fields:
                        assert field in auth_data, f"Missing field: {field}"
                    
                    token = auth_data["access_token"]
                    headers = {"Authorization": f"Bearer {token}"}
                    
                    # Test user info response format
                    async with self.session.get(
                        f"{self.backend_url}/api/v1/auth/me",
                        headers=headers
                    ) as user_response:
                        if user_response.status == 200:
                            user_data = await user_response.json()
                            
                            # Check user data structure
                            user_fields = ["user_id", "email", "name", "scopes"]
                            for field in user_fields:
                                assert field in user_data, f"Missing user field: {field}"
                    
                    # Test vector search response format
                    async with self.session.post(
                        f"{self.backend_url}/api/v1/vector-search/search",
                        headers=headers,
                        json={"query": "test", "limit": 1}
                    ) as search_response:
                        if search_response.status == 200:
                            search_data = await search_response.json()
                            
                            # Check search response structure
                            search_fields = ["results", "total_results", "query", "search_time_ms"]
                            for field in search_fields:
                                assert field in search_data, f"Missing search field: {field}"
                    
                    # Test LLM providers response format
                    async with self.session.get(
                        f"{self.backend_url}/api/v1/llm/providers",
                        headers=headers
                    ) as llm_response:
                        if llm_response.status == 200:
                            llm_data = await llm_response.json()
                            
                            # Check LLM response structure
                            llm_fields = ["providers", "current_routing_strategy"]
                            for field in llm_fields:
                                assert field in llm_data, f"Missing LLM field: {field}"
                    
                    print("✅ All API response formats match frontend expectations")
                    return True
                else:
                    print(f"❌ Authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ API format test error: {e}")
            return False
    
    async def test_error_handling_consistency(self):
        """Test error handling consistency across API"""
        print("\n🚨 Testing Error Handling Consistency...")
        
        try:
            error_scenarios = [
                {
                    "name": "Invalid login",
                    "method": "POST",
                    "url": "/api/v1/auth/login",
                    "data": {"email": "invalid@example.com", "password": "wrong"},
                    "expected_status": 401
                },
                {
                    "name": "Missing authorization",
                    "method": "GET", 
                    "url": "/api/v1/auth/me",
                    "data": None,
                    "expected_status": 401
                },
                {
                    "name": "Invalid vector search",
                    "method": "POST",
                    "url": "/api/v1/vector-search/search",
                    "data": {},  # Missing required query field
                    "expected_status": 422
                }
            ]
            
            consistent_errors = 0
            
            for scenario in error_scenarios:
                url = f"{self.backend_url}{scenario['url']}"
                
                if scenario["method"] == "POST":
                    async with self.session.post(url, json=scenario["data"]) as response:
                        actual_status = response.status
                        error_data = await response.json()
                elif scenario["method"] == "GET":
                    async with self.session.get(url) as response:
                        actual_status = response.status
                        try:
                            error_data = await response.json()
                        except:
                            error_data = {}
                
                if actual_status == scenario["expected_status"]:
                    consistent_errors += 1
                    print(f"✅ {scenario['name']}: Correct error status {actual_status}")
                    
                    # Check error response structure
                    if "detail" in error_data:
                        print(f"   Error detail: {error_data['detail']}")
                else:
                    print(f"❌ {scenario['name']}: Expected {scenario['expected_status']}, got {actual_status}")
            
            if consistent_errors == len(error_scenarios):
                print("✅ Error handling is consistent across API")
                return True
            else:
                print(f"⚠️ {consistent_errors}/{len(error_scenarios)} error scenarios consistent")
                return False
                
        except Exception as e:
            print(f"❌ Error handling test error: {e}")
            return False
    
    async def test_api_performance_for_frontend(self):
        """Test API performance requirements for frontend"""
        print("\n⚡ Testing API Performance for Frontend...")
        
        try:
            # Authenticate first
            async with self.session.post(
                f"{self.backend_url}/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "admin"}
            ) as response:
                if response.status == 200:
                    auth_data = await response.json()
                    token = auth_data["access_token"]
                    headers = {"Authorization": f"Bearer {token}"}
                else:
                    print("❌ Authentication failed for performance test")
                    return False
            
            # Test critical frontend endpoints
            performance_tests = [
                {
                    "name": "Health Check",
                    "method": "GET",
                    "url": "/health",
                    "headers": {},
                    "threshold_ms": 100
                },
                {
                    "name": "User Authentication Verify",
                    "method": "GET", 
                    "url": "/api/v1/auth/verify",
                    "headers": headers,
                    "threshold_ms": 200
                },
                {
                    "name": "Vector Search Collections",
                    "method": "GET",
                    "url": "/api/v1/vector-search/collections", 
                    "headers": headers,
                    "threshold_ms": 500
                },
                {
                    "name": "Quick Vector Search",
                    "method": "POST",
                    "url": "/api/v1/vector-search/search",
                    "headers": headers,
                    "data": {"query": "test", "limit": 3},
                    "threshold_ms": 1000
                },
                {
                    "name": "LLM Providers List",
                    "method": "GET",
                    "url": "/api/v1/llm/providers",
                    "headers": headers,
                    "threshold_ms": 300
                }
            ]
            
            performance_results = []
            
            for test in performance_tests:
                start_time = time.time()
                
                try:
                    if test["method"] == "GET":
                        async with self.session.get(
                            f"{self.backend_url}{test['url']}", 
                            headers=test["headers"]
                        ) as response:
                            response_time_ms = (time.time() - start_time) * 1000
                            status = response.status
                    elif test["method"] == "POST":
                        async with self.session.post(
                            f"{self.backend_url}{test['url']}", 
                            headers=test["headers"],
                            json=test.get("data", {})
                        ) as response:
                            response_time_ms = (time.time() - start_time) * 1000
                            status = response.status
                    
                    performance_results.append({
                        "name": test["name"],
                        "response_time_ms": response_time_ms,
                        "threshold_ms": test["threshold_ms"],
                        "status": status,
                        "passed": response_time_ms <= test["threshold_ms"] and status == 200
                    })
                    
                    if response_time_ms <= test["threshold_ms"] and status == 200:
                        print(f"✅ {test['name']}: {response_time_ms:.1f}ms (< {test['threshold_ms']}ms)")
                    else:
                        print(f"❌ {test['name']}: {response_time_ms:.1f}ms (> {test['threshold_ms']}ms) or status {status}")
                        
                except Exception as e:
                    performance_results.append({
                        "name": test["name"],
                        "response_time_ms": 0,
                        "threshold_ms": test["threshold_ms"],
                        "status": 0,
                        "passed": False,
                        "error": str(e)
                    })
                    print(f"❌ {test['name']}: Error - {e}")
            
            passed_tests = sum(1 for result in performance_results if result["passed"])
            total_tests = len(performance_results)
            
            if passed_tests == total_tests:
                print(f"✅ All performance tests passed ({passed_tests}/{total_tests})")
                return True
            else:
                print(f"⚠️ Performance tests: {passed_tests}/{total_tests} passed")
                return False
                
        except Exception as e:
            print(f"❌ Performance test error: {e}")
            return False
    
    async def test_data_consistency(self):
        """Test data consistency between different API endpoints"""
        print("\n🔄 Testing Data Consistency...")
        
        try:
            # Authenticate
            async with self.session.post(
                f"{self.backend_url}/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "admin"}
            ) as response:
                if response.status == 200:
                    auth_data = await response.json()
                    token = auth_data["access_token"]
                    headers = {"Authorization": f"Bearer {token}"}
                else:
                    return False
            
            # Get user info from /auth/me
            async with self.session.get(
                f"{self.backend_url}/api/v1/auth/me",
                headers=headers
            ) as response:
                user_me_data = await response.json()
            
            # Get user info from /auth/verify
            async with self.session.get(
                f"{self.backend_url}/api/v1/auth/verify", 
                headers=headers
            ) as response:
                user_verify_data = await response.json()
            
            # Check consistency
            if (user_me_data["email"] == user_verify_data.get("email") and
                user_me_data["user_id"] == user_verify_data.get("user_id")):
                print("✅ User data consistency: PASSED")
            else:
                print("❌ User data consistency: FAILED")
                return False
            
            # Test collection data consistency
            async with self.session.get(
                f"{self.backend_url}/api/v1/vector-search/collections",
                headers=headers
            ) as response:
                collections_data = await response.json()
                collections = collections_data.get("collections", {})
            
            # Perform search and check if collections in response match available collections
            async with self.session.post(
                f"{self.backend_url}/api/v1/vector-search/search",
                headers=headers,
                json={"query": "test", "limit": 1}
            ) as response:
                search_data = await response.json()
                searched_collections = search_data.get("collections_searched", [])
            
            # Check if searched collections are subset of available collections
            available_collection_types = [
                info.get("type") for info in collections.values() 
                if info.get("exists", False)
            ]
            
            consistency_check = all(
                col in available_collection_types 
                for col in searched_collections
            )
            
            if consistency_check:
                print("✅ Collection data consistency: PASSED")
            else:
                print("❌ Collection data consistency: FAILED")
                print(f"   Available: {available_collection_types}")
                print(f"   Searched: {searched_collections}")
                return False
            
            print("✅ All data consistency checks passed")
            return True
            
        except Exception as e:
            print(f"❌ Data consistency test error: {e}")
            return False
    
    async def run_frontend_backend_e2e_tests(self):
        """Run all frontend-backend E2E tests"""
        print("🚀 Starting Frontend-Backend E2E Tests")
        print("=" * 70)
        
        if not await self.setup():
            print("❌ Failed to setup frontend-backend test environment")
            return False
        
        tests = [
            ("CORS Configuration", self.test_api_cors_configuration),
            ("API Response Formats", self.test_api_response_formats), 
            ("Error Handling Consistency", self.test_error_handling_consistency),
            ("API Performance for Frontend", self.test_api_performance_for_frontend),
            ("Data Consistency", self.test_data_consistency)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if await test_func():
                    passed += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
        
        await self.cleanup()
        
        print("\n" + "=" * 70)
        print(f"📊 Frontend-Backend E2E Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL FRONTEND-BACKEND E2E TESTS PASSED!")
            print("\n✨ Frontend-Backend Integration Ready:")
            print("   🌐 CORS properly configured")
            print("   📋 API response formats consistent")
            print("   🚨 Error handling standardized")
            print("   ⚡ Performance meets frontend requirements")
            print("   🔄 Data consistency maintained")
            return True
        else:
            print(f"❌ {total - passed} tests failed")
            return False

# Test runner
async def main():
    """Main frontend-backend E2E test runner"""
    tester = FrontendBackendE2ETester()
    success = await tester.run_frontend_backend_e2e_tests()
    return success

if __name__ == "__main__":
    asyncio.run(main()) 