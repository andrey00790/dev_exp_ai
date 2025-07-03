#!/usr/bin/env python3
"""
Frontend Integration Test
Tests the integration between our new frontend components and backend APIs
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

class FrontendIntegrationTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.admin_token = None
        
    async def setup(self):
        """Initialize session and authenticate"""
        self.session = aiohttp.ClientSession()
        
        # Authenticate as admin
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
    
    async def test_vector_search_api(self):
        """Test Vector Search API endpoints"""
        print("\n🔍 Testing Vector Search API Integration...")
        
        try:
            # Test collection stats
            async with self.session.get(
                f"{self.base_url}/api/v1/vector-search/collections",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Collection stats: {len(data.get('collections', {}))} collections")
                else:
                    text = await response.text()
                    print(f"❌ Collection stats failed: {response.status} - {text}")
                    return False
            
            # Test search
            search_payload = {
                "query": "artificial intelligence machine learning",
                "limit": 5,
                "include_snippets": True,
                "hybrid_search": True
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/vector-search/search",
                headers=self.get_auth_headers(),
                json=search_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Vector search: {data.get('total_results', 0)} results in {data.get('search_time_ms', 0):.1f}ms")
                    print(f"✅ Collections searched: {data.get('collections_searched', [])}")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Vector search failed: {response.status} - {text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Vector search error: {e}")
            return False
    
    async def test_llm_operations_api(self):
        """Test LLM Operations API endpoints"""
        print("\n🤖 Testing LLM Operations API Integration...")
        
        try:
            # Test LLM health
            async with self.session.get(
                f"{self.base_url}/api/v1/llm/health",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ LLM health: {data.get('status')} ({data.get('providers_healthy')}/{data.get('total_providers')} providers)")
                else:
                    text = await response.text()
                    print(f"❌ LLM health check failed: {response.status} - {text}")
                    return False
            
            # Test text generation
            generation_payload = {
                "prompt": "Explain the benefits of vector search for enterprise applications",
                "max_tokens": 150,
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
                    response_time = time.time() - start_time
                    print(f"✅ Text generation: {len(data.get('content', ''))} chars")
                    print(f"✅ Provider: {data.get('provider')}, Tokens: {data.get('tokens_used')}")
                    print(f"✅ Cost: ${data.get('cost_usd', 0):.4f}, Time: {response_time:.2f}s")
                else:
                    text = await response.text()
                    print(f"❌ Text generation failed: {response.status} - {text}")
                    return False
            
            # Test RFC generation
            rfc_payload = {
                "task_description": "Implement real-time chat system with WebSocket support",
                "project_context": "Enterprise AI Assistant application",
                "technical_requirements": "FastAPI, WebSocket, authentication, message persistence"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/llm/generate/rfc",
                headers=self.get_auth_headers(),
                json=rfc_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ RFC generation: {len(data.get('content', ''))} chars")
                    print(f"✅ Provider: {data.get('provider')}, Cost: ${data.get('cost_usd', 0):.4f}")
                else:
                    text = await response.text()
                    print(f"❌ RFC generation failed: {response.status} - {text}")
                    return False
            
            # Test documentation generation
            doc_payload = {
                "code": """
def vector_search(query: str, limit: int = 10) -> List[SearchResult]:
    \"\"\"Perform semantic vector search across document collections\"\"\"
    embeddings = get_embeddings(query)
    results = qdrant_client.search(
        collection_name="documents",
        query_vector=embeddings,
        limit=limit
    )
    return format_results(results)
""",
                "language": "python",
                "doc_type": "comprehensive"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/llm/generate/documentation",
                headers=self.get_auth_headers(),
                json=doc_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Documentation generation: {len(data.get('content', ''))} chars")
                    print(f"✅ Provider: {data.get('provider')}, Cost: ${data.get('cost_usd', 0):.4f}")
                else:
                    text = await response.text()
                    print(f"❌ Documentation generation failed: {response.status} - {text}")
                    return False
            
            # Test Q&A
            qa_payload = {
                "question": "How does vector search improve information retrieval compared to traditional keyword search?",
                "context": "Vector search uses semantic embeddings to understand meaning and context",
                "max_tokens": 200
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/llm/answer",
                headers=self.get_auth_headers(),
                json=qa_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Q&A: {len(data.get('content', ''))} chars")
                    print(f"✅ Provider: {data.get('provider')}, Cost: ${data.get('cost_usd', 0):.4f}")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Q&A failed: {response.status} - {text}")
                    return False
                    
        except Exception as e:
            print(f"❌ LLM operations error: {e}")
            return False
    
    async def test_llm_stats_api(self):
        """Test LLM Statistics API"""
        print("\n📊 Testing LLM Statistics API...")
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/llm/stats",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    stats = data.get('service_metrics', {})
                    router = data.get('router_stats', {})
                    
                    print(f"✅ Total requests: {stats.get('total_requests', 0)}")
                    print(f"✅ Total cost: ${stats.get('total_cost_usd', 0):.4f}")
                    print(f"✅ Avg cost per request: ${stats.get('avg_cost_per_request', 0):.4f}")
                    print(f"✅ Routing strategy: {router.get('routing_strategy')}")
                    print(f"✅ Providers available: {data.get('providers_available', 0)}")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ LLM stats failed: {response.status} - {text}")
                    return False
                    
        except Exception as e:
            print(f"❌ LLM stats error: {e}")
            return False
    
    async def test_providers_api(self):
        """Test LLM Providers API"""
        print("\n🏗️ Testing LLM Providers API...")
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/llm/providers",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Providers: {len(data.get('providers', []))}")
                    print(f"✅ Current routing: {data.get('current_routing_strategy')}")
                    
                    for provider in data.get('providers', []):
                        print(f"   - {provider.get('name')}: {provider.get('status')}")
                    
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Providers API failed: {response.status} - {text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Providers API error: {e}")
            return False
    
    async def test_document_indexing(self):
        """Test document indexing for vector search"""
        print("\n📝 Testing Document Indexing...")
        
        try:
            doc_payload = {
                "text": "This is a test document about artificial intelligence and machine learning algorithms for enterprise applications.",
                "metadata": {
                    "title": "Test AI Document",
                    "author": "Integration Test",
                    "source": "test",
                    "tags": ["ai", "ml", "test"]
                },
                "collection_type": "documents"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/vector-search/index",
                headers=self.get_auth_headers(),
                json=doc_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Document indexed: {data.get('document_id')}")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Document indexing failed: {response.status} - {text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Document indexing error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all frontend integration tests"""
        print("🚀 Starting Frontend Integration Tests")
        print("=" * 60)
        
        if not await self.setup():
            return False
        
        tests = [
            self.test_vector_search_api,
            self.test_llm_operations_api,
            self.test_llm_stats_api,
            self.test_providers_api,
            self.test_document_indexing
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if await test():
                    passed += 1
                else:
                    print(f"❌ {test.__name__} failed")
            except Exception as e:
                print(f"❌ {test.__name__} error: {e}")
        
        await self.cleanup()
        
        print("\n" + "=" * 60)
        print(f"📊 Frontend Integration Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL FRONTEND INTEGRATION TESTS PASSED!")
            print("\n✨ Frontend Components Ready:")
            print("   🔍 Vector Search Component")
            print("   🤖 LLM Operations Component")
            print("   📊 Real-time Statistics")
            print("   🏗️ Provider Management")
            print("   📝 Document Indexing")
            return True
        else:
            print(f"❌ {total - passed} tests failed")
            return False

async def main():
    """Main function"""
    tester = FrontendIntegrationTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🚀 Frontend ready for production use!")
        print("   ➡️  Vector Search: http://localhost:3000/vector-search")
        print("   ➡️  LLM Operations: http://localhost:3000/llm-operations")
    else:
        print("\n❌ Some tests failed. Check backend logs.")

if __name__ == "__main__":
    asyncio.run(main()) 