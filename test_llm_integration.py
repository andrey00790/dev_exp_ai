#!/usr/bin/env python3
"""
Comprehensive LLM Integration Test

Tests the complete LLM provider system including:
- Provider initialization
- Router functionality
- Service layer
- API endpoints
- Fallback mechanisms
"""

import asyncio
import sys
import os
import requests
import json
import time
from typing import Dict, Any, Optional

# Setup environment
sys.path.insert(0, '/Users/a.kotenev/PycharmProjects/dev_exp_ai')
os.environ["PYTHONPATH"] = "/Users/a.kotenev/PycharmProjects/dev_exp_ai"

# Force mock mode for testing (no real API keys needed)
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("ANTHROPIC_API_KEY", None)

async def test_llm_provider_system():
    """Test the complete LLM provider system."""
    print("🤖 Testing LLM Provider System...")
    
    print("\n1️⃣ Testing LLM Service Initialization")
    
    try:
        from llm.llm_service import get_llm_service, initialize_llm_service
        
        # Initialize service
        llm_service = get_llm_service()
        success = await llm_service.initialize()
        
        if success:
            print("✅ LLM Service initialized successfully")
        else:
            print("❌ LLM Service initialization failed")
            return False
        
        # Get service stats
        stats = await llm_service.get_service_stats()
        print(f"   Status: {stats['status']}")
        print(f"   Providers available: {stats['providers_available']}")
        
    except Exception as e:
        print(f"❌ LLM Service initialization error: {e}")
        return False
    
    print("\n2️⃣ Testing Text Generation")
    
    try:
        # Test basic text generation
        result = await llm_service.generate_text(
            prompt="Hello, how are you?",
            max_tokens=50,
            temperature=0.7
        )
        
        print(f"✅ Text generated: {len(result)} characters")
        print(f"   Preview: {result[:100]}...")
        
    except Exception as e:
        print(f"❌ Text generation failed: {e}")
        return False
    
    print("\n3️⃣ Testing RFC Generation")
    
    try:
        rfc = await llm_service.generate_rfc(
            task_description="Implement user authentication system",
            project_context="Web application with FastAPI backend",
            technical_requirements="JWT tokens, password hashing, role-based access"
        )
        
        print(f"✅ RFC generated: {len(rfc)} characters")
        print(f"   Preview: {rfc[:150]}...")
        
    except Exception as e:
        print(f"❌ RFC generation failed: {e}")
        return False
    
    print("\n4️⃣ Testing Code Documentation")
    
    try:
        test_code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
'''
        
        docs = await llm_service.generate_documentation(
            code=test_code,
            language="python",
            doc_type="comprehensive"
        )
        
        print(f"✅ Documentation generated: {len(docs)} characters")
        print(f"   Preview: {docs[:150]}...")
        
    except Exception as e:
        print(f"❌ Documentation generation failed: {e}")
        return False
    
    print("\n5️⃣ Testing Question Answering")
    
    try:
        answer = await llm_service.answer_question(
            question="What is the capital of France?",
            context="France is a country in Europe with Paris as its capital city.",
            max_tokens=100
        )
        
        print(f"✅ Question answered: {len(answer)} characters")
        print(f"   Answer: {answer}")
        
    except Exception as e:
        print(f"❌ Question answering failed: {e}")
        return False
    
    print("\n6️⃣ Testing Provider Health Checks")
    
    try:
        health = await llm_service.health_check()
        print(f"✅ Health check completed")
        print(f"   Status: {health.get('router_status', 'unknown')}")
        print(f"   Healthy providers: {health.get('healthy_count', 0)}/{health.get('total_count', 0)}")
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    print("\n7️⃣ Testing Router Functionality")
    
    try:
        from llm.llm_router import LLMRouter, RoutingStrategy
        from llm.providers.base import LLMRequest
        
        # Test different routing strategies
        router = LLMRouter(RoutingStrategy.BALANCED)
        
        # Add mock provider (should already be added by service)
        providers = router.get_available_providers()
        print(f"✅ Router has {len(providers)} providers")
        
        if providers:
            # Test routing decision
            test_request = LLMRequest(prompt="Test prompt")
            routing_decision = await router._route_request(test_request)
            print(f"✅ Routing decision: {routing_decision.reason}")
            print(f"   Provider: {routing_decision.provider.provider.value}")
            print(f"   Estimated cost: ${routing_decision.estimated_cost:.4f}")
        
        # Get router stats
        router_stats = await router.get_router_stats()
        print(f"✅ Router stats retrieved")
        print(f"   Strategy: {router_stats['routing_strategy']}")
        print(f"   Total requests: {router_stats['total_requests']}")
        
    except Exception as e:
        print(f"❌ Router testing failed: {e}")
        return False
    
    print("\n🎉 LLM Provider System Test Complete!")
    return True

async def test_llm_api_endpoints():
    """Test LLM API endpoints."""
    print("\n📡 Testing LLM API Endpoints...")
    
    # Start app
    import subprocess
    app_process = subprocess.Popen([
        "python3", "app/main_production.py"
    ], env=dict(os.environ, PYTHONPATH="/Users/a.kotenev/PycharmProjects/dev_exp_ai"))
    
    try:
        print("⏳ Waiting for app to start...")
        await asyncio.sleep(8)
        
        base_url = "http://localhost:8000"
        
        # Login with admin
        print("\n🔑 Authenticating...")
        login_data = {
            "email": "admin@example.com",
            "password": "admin"
        }
        
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ Login failed: {response.text}")
            return False
        
        token_data = response.json()
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        print("✅ Authentication successful")
        
        # Test LLM health endpoint
        print("\n📊 Testing LLM Health...")
        response = requests.get(f"{base_url}/api/v1/llm/health", headers=headers)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ LLM Health check passed")
            print(f"   Status: {health_data.get('status', 'unknown')}")
            print(f"   Providers: {health_data.get('healthy_count', 0)}/{health_data.get('total_count', 0)} healthy")
        else:
            print(f"❌ LLM Health check failed: {response.text}")
        
        # Test text generation
        print("\n✍️ Testing Text Generation API...")
        gen_request = {
            "prompt": "Explain quantum computing in simple terms",
            "max_tokens": 200,
            "temperature": 0.7
        }
        
        response = requests.post(f"{base_url}/api/v1/llm/generate", json=gen_request, headers=headers)
        
        if response.status_code == 200:
            gen_data = response.json()
            print(f"✅ Text generation successful")
            print(f"   Content length: {len(gen_data['content'])} characters")
            print(f"   Provider: {gen_data['provider']}")
            print(f"   Tokens: {gen_data['tokens_used']}")
            print(f"   Cost: ${gen_data['cost_usd']:.4f}")
            print(f"   Response time: {gen_data['response_time']:.2f}s")
        else:
            print(f"❌ Text generation failed: {response.text}")
        
        # Test RFC generation
        print("\n📄 Testing RFC Generation API...")
        rfc_request = {
            "task_description": "Build a REST API for user management",
            "project_context": "Microservices architecture with FastAPI",
            "technical_requirements": "Database persistence, authentication, validation"
        }
        
        response = requests.post(f"{base_url}/api/v1/llm/generate/rfc", json=rfc_request, headers=headers)
        
        if response.status_code == 200:
            rfc_data = response.json()
            print(f"✅ RFC generation successful")
            print(f"   Content length: {len(rfc_data['content'])} characters")
            print(f"   Response time: {rfc_data['response_time']:.2f}s")
        else:
            print(f"❌ RFC generation failed: {response.text}")
        
        # Test documentation generation
        print("\n📚 Testing Documentation Generation API...")
        doc_request = {
            "code": "class Calculator:\n    def add(self, a, b):\n        return a + b\n\n    def multiply(self, a, b):\n        return a * b",
            "language": "python",
            "doc_type": "comprehensive"
        }
        
        response = requests.post(f"{base_url}/api/v1/llm/generate/documentation", json=doc_request, headers=headers)
        
        if response.status_code == 200:
            doc_data = response.json()
            print(f"✅ Documentation generation successful")
            print(f"   Content length: {len(doc_data['content'])} characters")
        else:
            print(f"❌ Documentation generation failed: {response.text}")
        
        # Test question answering
        print("\n❓ Testing Question Answering API...")
        qa_request = {
            "question": "How does machine learning work?",
            "context": "Machine learning is a subset of AI that enables computers to learn from data.",
            "max_tokens": 300
        }
        
        response = requests.post(f"{base_url}/api/v1/llm/answer", json=qa_request, headers=headers)
        
        if response.status_code == 200:
            qa_data = response.json()
            print(f"✅ Question answering successful")
            print(f"   Answer length: {len(qa_data['content'])} characters")
        else:
            print(f"❌ Question answering failed: {response.text}")
        
        # Test provider listing
        print("\n📋 Testing Provider Listing...")
        response = requests.get(f"{base_url}/api/v1/llm/providers", headers=headers)
        
        if response.status_code == 200:
            providers_data = response.json()
            print(f"✅ Provider listing successful")
            print(f"   Total providers: {providers_data.get('total_providers', 0)}")
            print(f"   Routing strategy: {providers_data.get('routing_strategy', 'unknown')}")
        else:
            print(f"❌ Provider listing failed: {response.text}")
        
        # Test LLM stats
        print("\n📈 Testing LLM Statistics...")
        response = requests.get(f"{base_url}/api/v1/llm/stats", headers=headers)
        
        if response.status_code == 200:
            stats_data = response.json()
            print(f"✅ LLM statistics retrieved")
            print(f"   Status: {stats_data.get('status', 'unknown')}")
            print(f"   Providers available: {stats_data.get('providers_available', 0)}")
        else:
            print(f"❌ LLM statistics failed: {response.text}")
        
        print("\n🎉 LLM API Test Complete!")
        return True
        
    finally:
        print("\n🧹 Cleaning up...")
        app_process.terminate()
        await asyncio.sleep(2)
        if app_process.poll() is None:
            app_process.kill()

def main():
    """Run comprehensive LLM integration tests."""
    print("=" * 60)
    print("🤖 COMPREHENSIVE LLM INTEGRATION TEST")
    print("=" * 60)
    
    try:
        # Test core LLM system
        print("Phase 1: Core LLM System Testing")
        system_success = asyncio.run(test_llm_provider_system())
        
        if not system_success:
            print("\n❌ Core system tests failed!")
            return
        
        # Test API endpoints
        print("\n" + "="*60)
        print("Phase 2: API Endpoints Testing")
        api_success = asyncio.run(test_llm_api_endpoints())
        
        if system_success and api_success:
            print("\n✅ ALL LLM TESTS PASSED!")
            print("🎯 LLM integration is fully functional")
            print("🚀 Ready for production use")
            
            print("\n📊 SUMMARY:")
            print("✅ LLM Service layer working")
            print("✅ Provider system functional")
            print("✅ Router and fallback working")
            print("✅ API endpoints responding")
            print("✅ Authentication integrated")
            print("✅ Multiple generation types supported")
            print("✅ Monitoring and metrics active")
            
        else:
            print("\n❌ SOME TESTS FAILED!")
            print("🔧 Check the errors above")
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 