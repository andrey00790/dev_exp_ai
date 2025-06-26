"""
Test endpoints for E2E testing without authentication.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["Test Endpoints"])

# Models for test endpoints

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

# Test endpoints

@router.post("/vector-search", response_model=TestSearchResponse)
async def test_vector_search(request: TestSearchRequest):
    """
    Test vector search endpoint without authentication.
    Returns mock data for E2E testing.
    """
    try:
        # Mock search results for testing
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
        
        # Limit results based on request
        limited_results = mock_results[:request.limit]
        
        return TestSearchResponse(
            query=request.query,
            results=limited_results,
            total_results=len(limited_results),
            search_time_ms=45.5
        )
        
    except Exception as e:
        logger.error(f"Test vector search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test search failed: {str(e)}")

@router.post("/feedback", response_model=TestFeedbackResponse)
async def test_feedback_submission(request: TestFeedbackRequest):
    """
    Test feedback submission endpoint without authentication.
    Returns mock response for E2E testing.
    """
    try:
        # Validate feedback type
        valid_types = ["like", "dislike", "report"]
        if request.feedback_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid feedback type. Must be one of: {valid_types}"
            )
        
        # Generate mock feedback ID
        feedback_id = f"test_feedback_{request.target_id}_{request.feedback_type}_{hash(str(datetime.now())) % 10000}"
        
        return TestFeedbackResponse(
            success=True,
            message=f"Test feedback '{request.feedback_type}' recorded successfully",
            feedback_id=feedback_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test feedback submission failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test feedback failed: {str(e)}")

@router.get("/health")
async def test_health_check():
    """Test health check endpoint."""
    return {
        "status": "healthy",
        "service": "test_endpoints",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@router.get("/mock-data")
async def get_mock_data():
    """Get mock data for testing purposes."""
    return {
        "documents": [
            {
                "id": "mock_doc_1",
                "title": "Sample Document 1",
                "content": "This is a sample document for testing purposes.",
                "source": "confluence",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "mock_doc_2", 
                "title": "Sample Document 2",
                "content": "This is another sample document with different content.",
                "source": "gitlab",
                "created_at": "2024-01-02T00:00:00Z"
            }
        ],
        "search_queries": [
            "API documentation",
            "authentication guide",
            "deployment process",
            "troubleshooting"
        ],
        "feedback_types": ["like", "dislike", "report"]
    }

@router.post("/simulate-error")
async def simulate_error(error_type: str = "generic"):
    """Simulate different types of errors for testing error handling."""
    if error_type == "404":
        raise HTTPException(status_code=404, detail="Test resource not found")
    elif error_type == "500":
        raise HTTPException(status_code=500, detail="Test internal server error")
    elif error_type == "400":
        raise HTTPException(status_code=400, detail="Test bad request")
    elif error_type == "timeout":
        import asyncio
        await asyncio.sleep(10)  # Simulate timeout
        return {"message": "This should timeout"}
    else:
        raise HTTPException(status_code=500, detail="Generic test error")

@router.get("/stats")
async def get_test_stats():
    """Get test statistics and metrics."""
    return {
        "test_endpoints_active": True,
        "mock_documents_count": 2,
        "supported_operations": [
            "vector_search",
            "feedback_submission", 
            "health_check",
            "error_simulation"
        ],
        "last_updated": datetime.now().isoformat(),
        "performance": {
            "avg_response_time_ms": 25.5,
            "success_rate": 0.98,
            "total_requests": 1000
        }
    } 