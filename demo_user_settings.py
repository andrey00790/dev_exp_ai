#!/usr/bin/env python3
"""
Demo script for testing User Settings API
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

def test_user_settings():
    """Тестирует API настроек пользователя."""
    
    print("🔧 Testing User Settings API")
    print("=" * 50)
    
    # Test GET current settings
    print("\n📖 Testing GET /api/v1/users/current/settings")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/users/current/settings")
        
        if response.status_code == 200:
            settings = response.json()
            print("✅ Current settings retrieved:")
            print(f"  Data sources: {len(settings['data_sources'])}")
            for ds in settings['data_sources']:
                print(f"    - {ds['source_type']}: Search={ds['is_enabled_semantic_search']}")
            print(f"  Preferences: {settings['preferences']}")
        else:
            print(f"❌ Failed to get settings: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test PUT update settings
    print("\n🔄 Testing PUT /api/v1/users/current/settings")
    try:
        update_data = {
            "data_sources": [
                {
                    "source_type": "jira",
                    "source_name": "default",
                    "is_enabled_semantic_search": True,
                    "is_enabled_architecture_generation": True
                },
                {
                    "source_type": "user_files",
                    "source_name": "default",
                    "is_enabled_semantic_search": True,
                    "is_enabled_architecture_generation": True
                }
            ],
            "preferences": {
                "language": "ru",
                "theme": "dark"
            }
        }
        
        response = requests.put(
            f"{API_BASE_URL}/api/v1/users/current/settings",
            json=update_data
        )
        
        if response.status_code == 200:
            print("✅ Settings updated successfully!")
        else:
            print(f"❌ Failed to update settings: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running!")
            test_user_settings()
            print("\n🎉 Test completed!")
            print("📖 GUI: http://localhost:3000/settings")
        else:
            print("❌ Server not responding")
    except:
        print("❌ Server not available")
