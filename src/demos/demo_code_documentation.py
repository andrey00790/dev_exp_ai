#!/usr/bin/env python3
"""
Demo script for testing Code Documentation Generation API
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

# Sample Python code
SAMPLE_CODE = '''from fastapi import FastAPI, HTTPException
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI(title="User Management API", version="1.0.0")

class User(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    age: int

users_db = []

@app.get("/users", response_model=List[User])
async def get_users():
    """Get all users from the database."""
    return users_db

@app.post("/users", response_model=User)
async def create_user(user: User):
    """Create a new user."""
    user.id = len(users_db) + 1
    users_db.append(user)
    return user
'''

def test_documentation_generation():
    """Test documentation generation API."""
    
    print("🚀 Testing Code Documentation Generation")
    print("=" * 50)
    
    # Test different documentation types
    doc_types = ["readme", "api_docs", "technical_spec"]
    
    for doc_type in doc_types:
        print(f"\n📝 Testing {doc_type} generation...")
        
        request_data = {
            "documentation_type": doc_type,
            "code_input": SAMPLE_CODE,
            "target_audience": "developers",
            "detail_level": "detailed"
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/v1/documentation/generate",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {doc_type} generation successful!")
                print(f"Title: {result['documentation']['title']}")
                print("Generated content (preview):")
                print("-" * 30)
                content = result['documentation']['full_content']
                print(content[:300] + "..." if len(content) > 300 else content)
                print("-" * 30)
            else:
                print(f"❌ {doc_type} generation failed: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Error testing {doc_type}: {str(e)}")

def test_code_analysis():
    """Test code analysis API."""
    
    print("\n🔍 Testing Code Analysis")
    print("=" * 50)
    
    request_data = {
        "code_input": SAMPLE_CODE,
        "analysis_depth": "standard"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/documentation/analyze",
            json=request_data,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Code analysis successful!")
            print(f"Functions found: {len(result.get('functions', []))}")
            print(f"Classes found: {len(result.get('classes', []))}")
            print(f"Dependencies: {len(result.get('dependencies', []))}")
        else:
            print(f"❌ Code analysis failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error in code analysis: {str(e)}")

if __name__ == "__main__":
    # Check server availability
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running!")
            test_code_analysis()
            test_documentation_generation()
            
            print("\n🎉 All tests completed!")
            print("\n📖 GUI Access:")
            print("Open http://localhost:3000/code-docs in your browser")
        else:
            print("❌ Server not responding properly")
    except:
        print("❌ Server is not available. Please start the backend server:")
        print("python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
