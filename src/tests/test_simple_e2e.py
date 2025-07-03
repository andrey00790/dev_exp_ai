#!/usr/bin/env python3
"""
Simple E2E Test for AI Assistant
Tests basic functionality without authentication
"""

import asyncio
import json
import time
import httpx
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class SimpleE2ETester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = []
    
    async def test_health_check(self) -> Dict[str, Any]:
        """Test basic health check"""
        print("🏥 Testing health check...")
        
        try:
            response = await self.client.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data.get('status')}")
                return {"success": True, "data": data}
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_api_health(self) -> Dict[str, Any]:
        """Test API health endpoint"""
        print("🔧 Testing API health...")
        
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/health")
            
            if response.status_code == 200:
                data = response.json()
                components = data.get('components', {})
                print(f"✅ API health check passed")
                print(f"   Components: {list(components.keys())}")
                return {"success": True, "data": data}
            else:
                print(f"❌ API health check failed: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ API health check error: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_search_endpoint(self) -> Dict[str, Any]:
        """Test search functionality"""
        print("🔍 Testing search endpoint...")
        
        payload = {
            "query": "FastAPI web framework",
            "limit": 3
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/search",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                print(f"✅ Search successful: {len(results)} results")
                return {"success": True, "data": data, "results_count": len(results)}
            else:
                print(f"❌ Search failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error details: {error_data}")
                except:
                    pass
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Search error: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_generate_rfc_basic(self) -> Dict[str, Any]:
        """Test basic RFC generation"""
        print("📝 Testing RFC generation...")
        
        payload = {
            "task_type": "new_feature",
            "initial_request": "Create a simple API endpoint for user authentication"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/generate",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                session_id = data.get("session_id")
                questions = data.get("questions", [])
                print(f"✅ RFC generation started: session {session_id}")
                print(f"   Generated {len(questions)} questions")
                return {"success": True, "data": data, "session_id": session_id}
            else:
                print(f"❌ RFC generation failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error details: {error_data}")
                except:
                    pass
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ RFC generation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_vector_search(self) -> Dict[str, Any]:
        """Test vector search endpoint"""
        print("🎯 Testing vector search...")
        
        payload = {
            "query": "Python web development",
            "limit": 5
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/vector-search/search",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                print(f"✅ Vector search successful: {len(results)} results")
                return {"success": True, "data": data, "results_count": len(results)}
            else:
                print(f"❌ Vector search failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error details: {error_data}")
                except:
                    pass
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Vector search error: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_openapi_docs(self) -> Dict[str, Any]:
        """Test OpenAPI documentation"""
        print("📚 Testing OpenAPI docs...")
        
        try:
            response = await self.client.get(f"{self.base_url}/openapi.json")
            
            if response.status_code == 200:
                data = response.json()
                paths = data.get("paths", {})
                print(f"✅ OpenAPI docs accessible: {len(paths)} endpoints")
                return {"success": True, "endpoints_count": len(paths)}
            else:
                print(f"❌ OpenAPI docs failed: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ OpenAPI docs error: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_feedback_endpoint(self) -> Dict[str, Any]:
        """Test feedback collection"""
        print("💬 Testing feedback endpoint...")
        
        payload = {
            "target_id": "test_target",
            "context": "e2e_test",
            "feedback_type": "like",
            "rating": 5,
            "comment": "E2E test feedback"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/feedback",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Feedback submitted successfully")
                return {"success": True, "data": data}
            else:
                print(f"❌ Feedback failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error details: {error_data}")
                except:
                    pass
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Feedback error: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_e2e_tests(self) -> Dict[str, Any]:
        """Run all E2E tests"""
        print("🚀 Starting Simple E2E Tests")
        print("=" * 50)
        
        start_time = time.time()
        tests = [
            ("Health Check", self.test_health_check),
            ("API Health", self.test_api_health),
            ("OpenAPI Docs", self.test_openapi_docs),
            ("Search Endpoint", self.test_search_endpoint),
            ("Vector Search", self.test_vector_search),
            ("RFC Generation", self.test_generate_rfc_basic),
            ("Feedback Collection", self.test_feedback_endpoint),
        ]
        
        results = {}
        successful_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            result = await test_func()
            results[test_name] = result
            
            if result.get("success"):
                successful_tests += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
        
        total_time = time.time() - start_time
        success_rate = (successful_tests / total_tests) * 100
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 E2E TEST SUMMARY")
        print("=" * 50)
        print(f"✅ Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        print(f"⏱️  Total Time: {total_time:.2f}s")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        for test_name, result in results.items():
            status = "✅ PASS" if result.get("success") else "❌ FAIL"
            print(f"  {test_name}: {status}")
            if not result.get("success"):
                print(f"    Error: {result.get('error', 'Unknown')}")
        
        # Generate recommendations
        recommendations = []
        
        if not results.get("Health Check", {}).get("success"):
            recommendations.append("🚨 Critical: Health check failing - check server status")
        
        if not results.get("API Health", {}).get("success"):
            recommendations.append("🔧 API health issues - check component status")
        
        if not results.get("Search Endpoint", {}).get("success"):
            recommendations.append("🔍 Search functionality issues - check data sources")
        
        if not results.get("Vector Search", {}).get("success"):
            recommendations.append("🎯 Vector search issues - check Qdrant connection")
        
        if not results.get("RFC Generation", {}).get("success"):
            recommendations.append("📝 RFC generation issues - check LLM configuration")
        
        if success_rate < 70:
            recommendations.append("🚨 Overall system health is poor - immediate attention required")
        elif success_rate < 90:
            recommendations.append("⚠️ Some components need attention - investigate failures")
        else:
            recommendations.append("✅ System is healthy - all major components working")
        
        print("\n🔧 RECOMMENDATIONS:")
        for rec in recommendations:
            print(f"  {rec}")
        
        # Save results
        report = {
            "summary": {
                "success_rate": success_rate,
                "successful_tests": successful_tests,
                "total_tests": total_tests,
                "total_time": total_time
            },
            "detailed_results": results,
            "recommendations": recommendations,
            "timestamp": time.time()
        }
        
        with open("e2e_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved to: e2e_test_report.json")
        
        return report
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

async def main():
    """Main test runner"""
    tester = SimpleE2ETester(BASE_URL)
    
    try:
        report = await tester.run_e2e_tests()
        success_rate = report["summary"]["success_rate"]
        
        if success_rate >= 80:
            print(f"\n🎉 E2E TESTS PASSED: {success_rate:.1f}% success rate")
            return True
        else:
            print(f"\n🚨 E2E TESTS FAILED: {success_rate:.1f}% success rate")
            return False
    except Exception as e:
        print(f"❌ E2E test execution failed: {e}")
        return False
    finally:
        await tester.close()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 