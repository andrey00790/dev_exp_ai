#!/usr/bin/env python3
"""
Minimal test server for E2E testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
from datetime import datetime

app = FastAPI(
    title="AI Assistant MVP - Test Server",
    description="Minimal test server for E2E testing",
    version="2.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test models
class TestSearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)

class TestSearchResult(BaseModel):
    doc_id: str
    title: str
    content: str
    score: float
    source: str

class TestSearchResponse(BaseModel):
    query: str
    results: List[TestSearchResult]
    total_results: int
    search_time_ms: float

class TestFeedbackRequest(BaseModel):
    target_id: str
    feedback_type: str = Field(..., description="like, dislike, or report")
    comment: Optional[str] = None

class TestFeedbackResponse(BaseModel):
    success: bool
    message: str
    feedback_id: str

# Health endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "version": "2.1.0", 
        "timestamp": "2025-06-17"
    }

@app.get("/api/v1/health")
async def api_health_check():
    """API health check"""
    return {
        "status": "healthy",
        "version": "2.1.0",
        "timestamp": "2025-06-17",
        "components": {
            "api": "healthy",
            "auth": "healthy",
            "search": "healthy",
            "generation": "healthy",
            "vector_search": "healthy",
            "websocket": "healthy"
        }
    }

# Test endpoints
@app.get("/api/v1/test/health")
async def test_health():
    """Test endpoints health"""
    return {
        "status": "healthy",
        "service": "test_endpoints",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.post("/api/v1/test/vector-search", response_model=TestSearchResponse)
async def test_vector_search(request: TestSearchRequest):
    """Test vector search"""
    mock_results = [
        TestSearchResult(
            doc_id="test_doc_1",
            title=f"Test Result for '{request.query}'",
            content=f"This is a mock search result for the query '{request.query}'. It demonstrates the search functionality.",
            score=0.95,
            source="test_confluence"
        ),
        TestSearchResult(
            doc_id="test_doc_2",
            title="Another Test Document", 
            content="This is another mock document that would match your search query in a real scenario.",
            score=0.87,
            source="test_gitlab"
        )
    ]
    
    limited_results = mock_results[:request.limit]
    
    return TestSearchResponse(
        query=request.query,
        results=limited_results,
        total_results=len(limited_results),
        search_time_ms=45.5
    )

@app.post("/api/v1/test/feedback", response_model=TestFeedbackResponse)
async def test_feedback(request: TestFeedbackRequest):
    """Test feedback submission"""
    valid_types = ["like", "dislike", "report"]
    if request.feedback_type not in valid_types:
        return TestFeedbackResponse(
            success=False,
            message=f"Invalid feedback type. Must be one of: {valid_types}",
            feedback_id=""
        )
    
    feedback_id = f"test_feedback_{request.target_id}_{request.feedback_type}_{hash(str(datetime.now())) % 10000}"
    
    return TestFeedbackResponse(
        success=True,
        message=f"Test feedback '{request.feedback_type}' recorded successfully",
        feedback_id=feedback_id
    )

# Search endpoint
@app.post("/api/v1/search")
async def search():
    """Basic search endpoint"""
    return {
        "results": [
            {"id": "1", "title": "Test Result 1", "content": "Mock content 1"},
            {"id": "2", "title": "Test Result 2", "content": "Mock content 2"}
        ],
        "total": 2,
        "query": "test"
    }

# RFC generation endpoint
@app.post("/api/v1/generate/rfc")
async def generate_rfc():
    """RFC generation endpoint"""
    return {
        "content": "# Test RFC\n\nThis is a mock RFC generated for testing purposes.",
        "status": "success",
        "tokens_used": 50
    }

if __name__ == "__main__":
    print("🚀 Starting Test Server...")
    uvicorn.run(
        "test_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 