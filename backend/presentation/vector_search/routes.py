"""
Vector Search REST API Endpoints

FastAPI routes for semantic/vector search functionality using Qdrant.
"""

from typing import List, Optional, Dict, Any
import logging

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from backend.adapters.vector_search.qdrant_client import QdrantClient, VectorSearchResult, create_qdrant_client

logger = logging.getLogger(__name__)

# ============================================================================
# Request/Response Models
# ============================================================================

class VectorSearchRequest(BaseModel):
    """Request model for vector search"""
    query_vector: List[float] = Field(..., description="Query vector for similarity search")
    collection_name: str = Field(..., description="Name of the collection to search")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    filter: Optional[Dict[str, Any]] = Field(None, description="Optional filter conditions")
    with_vector: bool = Field(False, description="Include vectors in response")

class DocumentEmbedRequest(BaseModel):
    """Request model for document embedding"""
    text: str = Field(..., description="Text to embed")
    collection_name: str = Field(..., description="Collection to store the embedding")
    document_id: str = Field(..., description="Unique document identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class VectorSearchResponse(BaseModel):
    """Response model for vector search"""
    id: str
    score: float
    payload: Dict[str, Any]
    vector: Optional[List[float]] = None

class SearchResultsResponse(BaseModel):
    """Response model for search results"""
    results: List[VectorSearchResponse]
    total_count: int
    query_time_ms: float

class CollectionInfoResponse(BaseModel):
    """Response model for collection information"""
    name: str
    vector_size: int
    points_count: int
    distance: str
    status: str

class CreateCollectionRequest(BaseModel):
    """Request model for creating a collection"""
    name: str = Field(..., description="Collection name")
    vector_size: int = Field(..., ge=1, le=4096, description="Vector dimension size")
    distance: str = Field("Cosine", description="Distance metric (Cosine, Euclid, Dot)")

# ============================================================================
# Router
# ============================================================================

router = APIRouter(tags=["Vector Search"])

# ============================================================================
# Collection Management Endpoints
# ============================================================================

@router.get("/collections", response_model=List[str])
async def list_collections(
    qdrant_client: QdrantClient = Depends(create_qdrant_client)
):
    """List all available collections"""
    try:
        async with qdrant_client:
            collections = await qdrant_client.list_collections()
            return collections
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collections"
        )

@router.post("/collections", status_code=status.HTTP_201_CREATED)
async def create_collection(
    request: CreateCollectionRequest,
    qdrant_client: QdrantClient = Depends(create_qdrant_client)
):
    """Create a new vector collection"""
    try:
        async with qdrant_client:
            # Check if collection already exists
            if await qdrant_client.collection_exists(request.name):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Collection '{request.name}' already exists"
                )
            
            # Create collection
            success = await qdrant_client.create_collection(
                collection_name=request.name,
                vector_size=request.vector_size,
                distance=request.distance
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create collection"
                )
            
            return {"message": f"Collection '{request.name}' created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create collection"
        )

@router.get("/collections/{collection_name}", response_model=CollectionInfoResponse)
async def get_collection_info(
    collection_name: str,
    qdrant_client: QdrantClient = Depends(create_qdrant_client)
):
    """Get information about a specific collection"""
    try:
        async with qdrant_client:
            info = await qdrant_client.get_collection_info(collection_name)
            
            if not info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection '{collection_name}' not found"
                )
            
            return CollectionInfoResponse(
                name=collection_name,
                vector_size=info.get("config", {}).get("params", {}).get("vectors", {}).get("size", 0),
                points_count=info.get("points_count", 0),
                distance=info.get("config", {}).get("params", {}).get("vectors", {}).get("distance", "Unknown"),
                status=info.get("status", "Unknown")
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collection info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collection information"
        )

# ============================================================================
# Vector Search Endpoints  
# ============================================================================

@router.post("/search", response_model=SearchResultsResponse)
async def vector_search(
    request: VectorSearchRequest,
    qdrant_client: QdrantClient = Depends(create_qdrant_client)
):
    """Perform vector similarity search"""
    import time
    start_time = time.time()
    
    try:
        async with qdrant_client:
            # Check if collection exists
            if not await qdrant_client.collection_exists(request.collection_name):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection '{request.collection_name}' not found"
                )
            
            # Perform search
            results = await qdrant_client.search(
                collection_name=request.collection_name,
                query_vector=request.query_vector,
                limit=request.limit,
                filter=request.filter,
                with_vector=request.with_vector
            )
            
            # Convert to response format
            search_results = [
                VectorSearchResponse(
                    id=result.id,
                    score=result.score,
                    payload=result.payload,
                    vector=result.vector
                )
                for result in results
            ]
            
            query_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return SearchResultsResponse(
                results=search_results,
                total_count=len(search_results),
                query_time_ms=round(query_time, 2)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Vector search failed"
        )

@router.post("/collections/{collection_name}/embed")
async def embed_document(
    collection_name: str,
    request: DocumentEmbedRequest,
    qdrant_client: QdrantClient = Depends(create_qdrant_client)
):
    """Embed and store a document in the vector collection"""
    try:
        async with qdrant_client:
            # Check if collection exists
            if not await qdrant_client.collection_exists(collection_name):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection '{collection_name}' not found"
                )
            
            # TODO: Generate embeddings using your embedding model
            # For now, return a placeholder
            return {"message": "Document embedding endpoint ready - integration with embedding model needed"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document embedding failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document embedding failed"
        )

@router.delete("/collections/{collection_name}/points/{point_id}")
async def delete_vector_point(
    collection_name: str,
    point_id: str,
    qdrant_client: QdrantClient = Depends(create_qdrant_client)
):
    """Delete a specific vector point from collection"""
    try:
        async with qdrant_client:
            # Check if collection exists
            if not await qdrant_client.collection_exists(collection_name):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection '{collection_name}' not found"
                )
            
            # Delete point
            success = await qdrant_client.delete_points(collection_name, [point_id])
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete vector point"
                )
            
            return {"message": f"Point '{point_id}' deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete vector point: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete vector point"
        )

# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def vector_search_health(
    qdrant_client: QdrantClient = Depends(create_qdrant_client)
):
    """Health check for vector search service"""
    try:
        async with qdrant_client:
            is_healthy = await qdrant_client.health_check()
            
            if is_healthy:
                return {
                    "status": "healthy",
                    "qdrant": "connected",
                    "service": "vector_search"
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Qdrant service unavailable"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vector search health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector search service unavailable"
        )

# ============================================================================
# Router Factory
# ============================================================================

def create_vector_search_router() -> APIRouter:
    """Create vector search router"""
    return router 