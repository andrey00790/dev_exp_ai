#!/usr/bin/env python3
"""
Simple Qdrant Integration Test with existing admin user
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
os.environ["QDRANT_USE_MEMORY"] = "true"
os.environ["PYTHONPATH"] = "/Users/a.kotenev/PycharmProjects/dev_exp_ai"

async def test_qdrant_with_admin():
    """Simple Qdrant test using admin user."""
    
    # Start app
    import subprocess
    app_process = subprocess.Popen([
        "python3", "app/main_production.py"
    ], env=dict(os.environ, PYTHONPATH="/Users/a.kotenev/PycharmProjects/dev_exp_ai"))
    
    try:
        print("⏳ Waiting for app to start...")
        await asyncio.sleep(8)
        
        base_url = "http://localhost:8000"
        
        print("\n🔑 Login with admin user...")
        
        # Login with admin
        login_data = {
            "email": "admin@example.com",
            "password": "admin"
        }
        
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
        
        token_data = response.json()
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        print("✅ Admin login successful")
        
        # Initialize collections
        print("\n📁 Initialize collections...")
        response = requests.post(f"{base_url}/api/v1/vector-search/collections/initialize", headers=headers)
        
        if response.status_code == 200:
            print("✅ Collections initialized")
        else:
            print(f"❌ Collection init failed: {response.text}")
        
        # Index a test document
        print("\n📝 Index test document...")
        doc_data = {
            "text": "Qdrant is a powerful vector database for AI applications. It supports semantic search, embeddings, and real-time vector operations.",
            "doc_id": "qdrant_test_001",
            "title": "Qdrant Vector Database",
            "source": "test",
            "source_type": "documents",
            "tags": ["qdrant", "vector", "database", "ai"]
        }
        
        response = requests.post(f"{base_url}/api/v1/vector-search/index", json=doc_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Document indexed: {result}")
        else:
            print(f"❌ Indexing failed: {response.text}")
        
        # Search documents
        print("\n🔍 Search documents...")
        search_data = {
            "query": "vector database semantic search AI",
            "limit": 5,
            "include_snippets": True
        }
        
        response = requests.post(f"{base_url}/api/v1/vector-search/search", json=search_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Search completed: {result['total_results']} results")
            
            for i, doc in enumerate(result['results'], 1):
                print(f"   {i}. {doc['title']} (score: {doc['score']:.4f})")
        else:
            print(f"❌ Search failed: {response.text}")
        
        # Get stats
        print("\n📊 Get system stats...")
        response = requests.get(f"{base_url}/api/v1/vector-search/stats", headers=headers)
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Stats retrieved:")
            print(f"   Status: {stats['status']}")
            print(f"   Collections: {stats['active_collections']}/{stats['total_collections']}")
            print(f"   Qdrant: {stats['qdrant_status']['status']} ({stats['qdrant_status'].get('mode', 'unknown')})")
        else:
            print(f"❌ Stats failed: {response.text}")
        
        print("\n🎉 Qdrant integration test completed successfully!")
        return True
        
    finally:
        print("\n🧹 Cleaning up...")
        app_process.terminate()
        await asyncio.sleep(2)
        if app_process.poll() is None:
            app_process.kill()

def main():
    """Run the simple test."""
    print("=" * 50)
    print("🚀 SIMPLE QDRANT INTEGRATION TEST")
    print("=" * 50)
    
    try:
        success = asyncio.run(test_qdrant_with_admin())
        
        if success:
            print("\n✅ TEST PASSED!")
            print("🎯 Qdrant integration working correctly")
        else:
            print("\n❌ TEST FAILED!")
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 