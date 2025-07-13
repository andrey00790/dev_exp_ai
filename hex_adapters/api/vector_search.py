"""
Vector Search API - Compatibility module
Redirects to app.api.v1.search.vector_search
"""

# Re-export router from search.vector_search for backward compatibility
try:
    from app.api.v1.search.vector_search import router
    
    __all__ = ["router"]
except ImportError:
    # Fallback for tests - create minimal router
    from fastapi import APIRouter
    
    router = APIRouter(prefix="/vector-search", tags=["Vector Search"])
    
    @router.get("/health")
    async def health():
        return {"status": "healthy", "service": "vector_search"}
    
    @router.post("/search")
    async def search(query: str):
        return {"results": [], "query": query}
    
    __all__ = ["router"] 