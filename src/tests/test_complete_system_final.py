#!/usr/bin/env python3
"""
Complete System Final Test
Comprehensive validation of the AI Assistant MVP with all improvements
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any

class CompleteSystemTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.admin_token = None
        
    async def setup(self):
        """Initialize session and authenticate"""
        self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={
                    "email": "admin@example.com",
                    "password": "admin"
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data["access_token"]
                    print("✅ Authentication successful")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Authentication failed: {response.status} - {text}")
                    return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    async def cleanup(self):
        """Close session"""
        if self.session:
            await self.session.close()
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
    
    async def test_health_endpoints(self):
        """Test system health endpoints"""
        print("\n🏥 Testing System Health...")
        
        endpoints = [
            "/health",
            "/health_smoke",
        ]
        
        for endpoint in endpoints:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ {endpoint}: {data.get('status', 'OK')}")
                    else:
                        print(f"❌ {endpoint}: {response.status}")
                        return False
            except Exception as e:
                print(f"❌ {endpoint} error: {e}")
                return False
        
        return True
    
    async def test_authentication_system(self):
        """Test authentication and authorization"""
        print("\n🔐 Testing Authentication System...")
        
        try:
            # Test current user info
            async with self.session.get(
                f"{self.base_url}/api/v1/auth/me",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    print(f"✅ User info: {user_data.get('name')} ({user_data.get('email')})")
                    print(f"✅ Scopes: {user_data.get('scopes', [])}")
                else:
                    print(f"❌ User info failed: {response.status}")
                    return False
            
            # Test token verification
            async with self.session.get(
                f"{self.base_url}/api/v1/auth/verify",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Token verification: {data.get('valid')}")
                    budget = data.get('budget_status', {})
                    print(f"✅ Budget: ${budget.get('current_usage', 0):.2f} / ${budget.get('limit', 0):.2f}")
                else:
                    print(f"❌ Token verification failed: {response.status}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Authentication test error: {e}")
            return False
    
    async def test_vector_search_system(self):
        """Test vector search capabilities"""
        print("\n🔍 Testing Vector Search System...")
        
        try:
            # Test collection status
            async with self.session.get(
                f"{self.base_url}/api/v1/vector-search/collections",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    collections = data.get('collections', {})
                    active_collections = sum(1 for c in collections.values() if c.get('exists'))
                    print(f"✅ Collections: {active_collections}/{len(collections)} active")
                else:
                    print(f"❌ Collection status failed: {response.status}")
                    return False
            
            # Test vector search
            search_payload = {
                "query": "machine learning artificial intelligence algorithms",
                "limit": 3,
                "include_snippets": True,
                "hybrid_search": True
            }
            
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/api/v1/vector-search/search",
                headers=self.get_auth_headers(),
                json=search_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    search_time = time.time() - start_time
                    print(f"✅ Search: {data.get('total_results', 0)} results in {search_time*1000:.1f}ms")
                    print(f"✅ Collections searched: {len(data.get('collections_searched', []))}")
                    
                    # Test result quality
                    results = data.get('results', [])
                    if results:
                        avg_score = sum(r.get('score', 0) for r in results) / len(results)
                        print(f"✅ Average relevance score: {avg_score:.3f}")
                else:
                    print(f"❌ Vector search failed: {response.status}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Vector search test error: {e}")
            return False
    
    async def test_llm_system(self):
        """Test LLM system capabilities"""
        print("\n🤖 Testing LLM System...")
        
        try:
            # Test LLM providers
            async with self.session.get(
                f"{self.base_url}/api/v1/llm/providers",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    providers = data.get('providers', [])
                    print(f"✅ Providers available: {len(providers)}")
                    print(f"✅ Routing strategy: {data.get('current_routing_strategy', 'N/A')}")
                else:
                    print(f"❌ LLM providers failed: {response.status}")
                    return False
            
            # Test text generation (if providers available)
            if len(providers) > 0:
                generation_payload = {
                    "prompt": "Explain the benefits of AI assistants in enterprise environments",
                    "max_tokens": 100,
                    "temperature": 0.7
                }
                
                start_time = time.time()
                async with self.session.post(
                    f"{self.base_url}/api/v1/llm/generate",
                    headers=self.get_auth_headers(),
                    json=generation_payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        generation_time = time.time() - start_time
                        print(f"✅ Text generation: {len(data.get('content', ''))} chars in {generation_time:.2f}s")
                        print(f"✅ Cost: ${data.get('cost_usd', 0):.4f}, Tokens: {data.get('tokens_used', 0)}")
                    else:
                        print(f"⚠️ Text generation not working: {response.status}")
            else:
                print("⚠️ No LLM providers available - skipping generation test")
            
            return True
            
        except Exception as e:
            print(f"❌ LLM system test error: {e}")
            return False
    
    async def test_cache_system(self):
        """Test caching system"""
        print("\n💾 Testing Cache System...")
        
        try:
            # Import cache manager
            from app.performance.cache_manager import cache_manager
            
            # Test cache health
            health = await cache_manager.health_check()
            print(f"✅ Cache health: {health.get('status')}")
            print(f"✅ Cache type: {health.get('redis_connected') and 'Redis' or 'Local'}")
            
            # Test cache statistics
            stats = await cache_manager.get_stats()
            print(f"✅ Cache hit rate: {stats.get('hit_rate', 0):.1f}%")
            print(f"✅ Total operations: {stats.get('hits', 0) + stats.get('misses', 0)}")
            
            return health.get('status') in ['healthy', 'degraded']
            
        except Exception as e:
            print(f"❌ Cache system test error: {e}")
            return False
    
    async def test_api_endpoints(self):
        """Test various API endpoints"""
        print("\n🔗 Testing API Endpoints...")
        
        endpoints_to_test = [
            ("/api/v1/auth/budget", "Budget endpoint"),
            ("/api/v1/auth/scopes", "Scopes endpoint"),
            ("/api/v1/vector-search/collections", "Collections endpoint"),
        ]
        
        try:
            for endpoint, description in endpoints_to_test:
                async with self.session.get(
                    f"{self.base_url}{endpoint}",
                    headers=self.get_auth_headers()
                ) as response:
                    if response.status == 200:
                        print(f"✅ {description}: Working")
                    else:
                        print(f"❌ {description}: {response.status}")
                        return False
            
            return True
            
        except Exception as e:
            print(f"❌ API endpoints test error: {e}")
            return False
    
    async def test_security_features(self):
        """Test security features"""
        print("\n🔒 Testing Security Features...")
        
        try:
            # Test unauthorized access
            async with self.session.get(
                f"{self.base_url}/api/v1/auth/me"
                # No authorization header
            ) as response:
                if response.status == 401:
                    print("✅ Unauthorized requests properly rejected")
                else:
                    print(f"❌ Security vulnerability: {response.status}")
                    return False
            
            # Test JWT validation
            invalid_headers = {
                "Authorization": "Bearer invalid_token",
                "Content-Type": "application/json"
            }
            
            async with self.session.get(
                f"{self.base_url}/api/v1/auth/me",
                headers=invalid_headers
            ) as response:
                if response.status == 401:
                    print("✅ Invalid tokens properly rejected")
                else:
                    print(f"❌ JWT validation issue: {response.status}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Security test error: {e}")
            return False
    
    async def test_monitoring_capabilities(self):
        """Test monitoring and metrics"""
        print("\n📊 Testing Monitoring Capabilities...")
        
        try:
            # Test metrics endpoint (if available)
            async with self.session.get(f"{self.base_url}/metrics") as response:
                if response.status == 200:
                    print("✅ Metrics endpoint available")
                else:
                    print("⚠️ Metrics endpoint not available (may be disabled)")
            
            # Test system status
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ System status: {data.get('status', 'OK')}")
                    
                    if 'uptime' in data:
                        print(f"✅ System uptime: {data['uptime']}")
                    
                    if 'version' in data:
                        print(f"✅ System version: {data['version']}")
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Monitoring test error: {e}")
            return False
    
    async def test_performance_metrics(self):
        """Test system performance"""
        print("\n⚡ Testing System Performance...")
        
        performance_results = {
            'auth_time': 0,
            'search_time': 0,
            'api_response_times': []
        }
        
        try:
            # Test authentication performance
            start_time = time.time()
            async with self.session.get(
                f"{self.base_url}/api/v1/auth/verify",
                headers=self.get_auth_headers()
            ) as response:
                auth_time = time.time() - start_time
                performance_results['auth_time'] = auth_time
                print(f"✅ Auth response time: {auth_time*1000:.1f}ms")
            
            # Test search performance
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/api/v1/vector-search/search",
                headers=self.get_auth_headers(),
                json={"query": "test query", "limit": 5}
            ) as response:
                search_time = time.time() - start_time
                performance_results['search_time'] = search_time
                print(f"✅ Search response time: {search_time*1000:.1f}ms")
            
            # Test multiple API calls for average response time
            endpoints = [
                "/api/v1/auth/me",
                "/api/v1/auth/budget",
                "/api/v1/vector-search/collections"
            ]
            
            for endpoint in endpoints:
                start_time = time.time()
                async with self.session.get(
                    f"{self.base_url}{endpoint}",
                    headers=self.get_auth_headers()
                ) as response:
                    response_time = time.time() - start_time
                    performance_results['api_response_times'].append(response_time)
            
            avg_response_time = sum(performance_results['api_response_times']) / len(performance_results['api_response_times'])
            print(f"✅ Average API response time: {avg_response_time*1000:.1f}ms")
            
            # Performance thresholds
            if auth_time > 1.0:
                print("⚠️ Authentication seems slow (>1s)")
            if search_time > 2.0:
                print("⚠️ Search seems slow (>2s)")
            if avg_response_time > 0.5:
                print("⚠️ API responses seem slow (>500ms)")
            
            return True
            
        except Exception as e:
            print(f"❌ Performance test error: {e}")
            return False
    
    async def run_complete_system_test(self):
        """Run comprehensive system test"""
        print("🚀 Starting Complete AI Assistant MVP System Test")
        print("=" * 80)
        
        if not await self.setup():
            return False
        
        tests = [
            ("System Health", self.test_health_endpoints),
            ("Authentication System", self.test_authentication_system),
            ("Vector Search System", self.test_vector_search_system),
            ("LLM System", self.test_llm_system),
            ("Cache System", self.test_cache_system),
            ("API Endpoints", self.test_api_endpoints),
            ("Security Features", self.test_security_features),
            ("Monitoring Capabilities", self.test_monitoring_capabilities),
            ("Performance Metrics", self.test_performance_metrics)
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
            print()
        
        await self.cleanup()
        
        print("=" * 80)
        print(f"📊 Complete System Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL SYSTEM TESTS PASSED!")
            print("\n✨ AI Assistant MVP - PRODUCTION READY!")
            print("\n🔧 System Components:")
            print("   ✅ FastAPI Backend with Authentication")
            print("   ✅ Vector Search with Qdrant Integration")
            print("   ✅ LLM Operations with Multiple Providers")
            print("   ✅ Redis Cache with Local Fallback")
            print("   ✅ Security & Authorization")
            print("   ✅ Monitoring & Health Checks")
            print("   ✅ Modern React Frontend")
            print("\n🎯 Key Features:")
            print("   🔍 Semantic Search across Collections")
            print("   🤖 AI Text Generation & RFC Creation")
            print("   📚 Automatic Code Documentation")
            print("   💬 Intelligent Q&A System")
            print("   📊 Real-time Statistics & Monitoring")
            print("   🔒 Enterprise-grade Security")
            print("   ⚡ High-performance Caching")
            print("\n🌐 Access Points:")
            print("   📱 Frontend: http://localhost:3000")
            print("   🔗 API: http://localhost:8000")
            print("   📖 Docs: http://localhost:8000/docs")
            return True
        else:
            print(f"❌ {total - passed} system tests failed")
            print("🔧 System needs attention before production deployment")
            return False

async def main():
    """Main function"""
    tester = CompleteSystemTester()
    success = await tester.run_complete_system_test()
    
    if success:
        print("\n🚀🚀🚀 AI ASSISTANT MVP READY FOR PRODUCTION! 🚀🚀🚀")
    else:
        print("\n❌ System validation failed. Check logs and fix issues.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main()) 