"""
Qdrant Vector Search API endpoints
"""

import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from adapters.vectorstore.collections import (CollectionType, DocumentMetadata,
                                     get_collection_manager)
from adapters.vectorstore.qdrant_client import get_qdrant_client

from infra.monitoring.metrics import record_semantic_search_metrics
from app.security.auth import get_current_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qdrant", tags=["Qdrant Vector Search"])


# Request/Response models
class DocumentIndexRequest(BaseModel):
    """Request model for document indexing."""

    text: str = Field(..., description="Document text content")
    doc_id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    source: str = Field(..., description="Document source system")
    collection_type: str = Field(default="documents", description="Collection type")
    author: Optional[str] = Field(None, description="Document author")
    content_type: Optional[str] = Field(None, description="Content MIME type")
    tags: Optional[List[str]] = Field(None, description="Document tags")
    url: Optional[str] = Field(None, description="Document URL")


class DocumentSearchRequest(BaseModel):
    """Request model for document search."""

    query: str = Field(..., description="Search query text")
    collection_types: Optional[List[str]] = Field(
        None, description="Collections to search"
    )
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")


class DocumentSearchResult(BaseModel):
    """Document search result."""

    id: str = Field(..., description="Document chunk ID")
    score: float = Field(..., description="Similarity score")
    doc_id: str = Field(..., description="Original document ID")
    title: str = Field(..., description="Document title")
    text: str = Field(..., description="Document text content")
    collection_type: str = Field(..., description="Collection type")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")


class SearchResponse(BaseModel):
    """Search response model."""

    results: List[DocumentSearchResult]
    total_results: int
    query: str
    search_time_ms: float
    collections_searched: List[str]


class IndexResponse(BaseModel):
    """Index response model."""

    success: bool
    doc_id: str
    message: str
    chunks_created: Optional[int] = None


class HealthResponse(BaseModel):
    """Qdrant health response model."""

    status: str
    connected: bool
    mode: str
    collections: Dict[str, Dict[str, Any]]


# API Endpoints


@router.get("/health", response_model=HealthResponse)
async def get_qdrant_health():
    """Get Qdrant health status and collection information."""
    try:
        client = get_qdrant_client()
        health = client.health_check()

        collection_manager = get_collection_manager()
        collections = collection_manager.get_collection_stats()

        return HealthResponse(
            status=health["status"],
            connected=health["connected"],
            mode=health.get("mode", "unknown"),
            collections=collections,
        )

    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.post("/collections/initialize")
async def initialize_collections(current_user=Depends(get_current_user)):
    """Initialize all Qdrant collections."""
    try:
        if not require_admin(current_user):
            raise HTTPException(status_code=403, detail="Admin access required")

        collection_manager = get_collection_manager()
        results = await collection_manager.initialize_collections()

        return {
            "success": True,
            "message": "Collections initialized",
            "results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Collection initialization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")


@router.post("/documents/index", response_model=IndexResponse)
async def index_document(
    request: DocumentIndexRequest, current_user=Depends(get_current_user)
):
    """Index a document in Qdrant vector store."""
    start_time = time.time()

    try:
        # Validate collection type
        try:
            collection_type = CollectionType(request.collection_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid collection type: {request.collection_type}",
            )

        # Create document metadata
        metadata = DocumentMetadata(
            doc_id=request.doc_id,
            title=request.title,
            source=request.source,
            source_type=collection_type,
            author=request.author,
            content_type=request.content_type,
            tags=request.tags,
            url=request.url,
        )

        # Index document
        collection_manager = get_collection_manager()
        success = await collection_manager.index_document(
            text=request.text, metadata=metadata, collection_type=collection_type
        )

        duration = time.time() - start_time

        # Record metrics
        record_semantic_search_metrics(
            endpoint="/qdrant/documents/index",
            duration=duration,
            results_count=1 if success else 0,
            relevance_score=1.0 if success else 0.0,
            status="success" if success else "failed",
            collection=request.collection_type,
            query_type="indexing",
        )

        if success:
            return IndexResponse(
                success=True,
                doc_id=request.doc_id,
                message="Document indexed successfully",
                chunks_created=1,  # Simplified, would need actual chunk count
            )
        else:
            raise HTTPException(status_code=500, detail="Document indexing failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document indexing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: DocumentSearchRequest):
    """Search documents using vector similarity."""
    start_time = time.time()

    try:
        # Parse collection types
        collection_types = None
        if request.collection_types:
            try:
                collection_types = [
                    CollectionType(ct.lower()) for ct in request.collection_types
                ]
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid collection type: {e}"
                )

        # Perform search
        collection_manager = get_collection_manager()
        results = await collection_manager.search_documents(
            query=request.query,
            collection_types=collection_types,
            limit=request.limit,
            filters=request.filters,
        )

        duration = time.time() - start_time
        search_time_ms = duration * 1000

        # Convert results to response format
        search_results = []
        collections_searched = set()

        for result in results:
            payload = result["payload"]
            collections_searched.add(result["collection_type"])

            search_results.append(
                DocumentSearchResult(
                    id=result["id"],
                    score=result["score"],
                    doc_id=payload.get(
                        "original_doc_id", payload.get("doc_id", "unknown")
                    ),
                    title=payload.get("title", "Untitled"),
                    text=payload.get("text", ""),
                    collection_type=result["collection_type"],
                    metadata={
                        "author": payload.get("author"),
                        "source": payload.get("source"),
                        "tags": payload.get("tags", []),
                        "content_type": payload.get("content_type"),
                        "chunk_index": payload.get("chunk_index"),
                        "total_chunks": payload.get("total_chunks"),
                    },
                )
            )

        # Record metrics
        avg_relevance = (
            sum(r.score for r in search_results) / len(search_results)
            if search_results
            else 0.0
        )
        record_semantic_search_metrics(
            endpoint="/qdrant/search",
            duration=duration,
            results_count=len(search_results),
            relevance_score=avg_relevance,
            status="success",
            query_type="semantic_search",
        )

        return SearchResponse(
            results=search_results,
            total_results=len(search_results),
            query=request.query,
            search_time_ms=search_time_ms,
            collections_searched=list(collections_searched),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    collection_type: str = Query(..., description="Collection type"),
    current_user=Depends(get_current_user),
):
    """Delete a document from vector store."""
    try:
        # Validate collection type
        try:
            coll_type = CollectionType(collection_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid collection type: {collection_type}"
            )

        # Delete document
        collection_manager = get_collection_manager()
        success = await collection_manager.delete_document(
            doc_id=doc_id, collection_type=coll_type
        )

        if success:
            return {
                "success": True,
                "message": f"Document {doc_id} deleted successfully",
            }
        else:
            raise HTTPException(
                status_code=404, detail="Document not found or deletion failed"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document deletion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@router.get("/collections/stats")
async def get_collection_stats():
    """Get statistics for all collections."""
    try:
        collection_manager = get_collection_manager()
        stats = collection_manager.get_collection_stats()

        return {"success": True, "collections": stats, "total_collections": len(stats)}

    except Exception as e:
        logger.error(f"Failed to get collection stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.post("/collections/{collection_type}/reindex")
async def reindex_collection(
    collection_type: str, current_user=Depends(get_current_user)
):
    """Reindex a specific collection."""
    try:
        if not require_admin(current_user):
            raise HTTPException(status_code=403, detail="Admin access required")

        # Validate collection type
        try:
            coll_type = CollectionType(collection_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid collection type: {collection_type}"
            )

        # Reindex collection
        collection_manager = get_collection_manager()
        success = await collection_manager.reindex_collection(coll_type)

        if success:
            return {
                "success": True,
                "message": f"Collection {collection_type} reindexed successfully",
            }
        else:
            raise HTTPException(status_code=500, detail="Reindexing failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Collection reindexing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reindexing failed: {str(e)}")


# Bulk operations


@router.post("/documents/bulk-index")
async def bulk_index_documents(
    documents: List[DocumentIndexRequest], current_user=Depends(get_current_user)
):
    """Bulk index multiple documents."""
    if len(documents) > 100:
        raise HTTPException(
            status_code=400, detail="Maximum 100 documents per bulk request"
        )

    start_time = time.time()
    results = []

    try:
        collection_manager = get_collection_manager()

        for doc_request in documents:
            try:
                # Validate collection type
                collection_type = CollectionType(doc_request.collection_type.lower())

                # Create metadata
                metadata = DocumentMetadata(
                    doc_id=doc_request.doc_id,
                    title=doc_request.title,
                    source=doc_request.source,
                    source_type=collection_type,
                    author=doc_request.author,
                    content_type=doc_request.content_type,
                    tags=doc_request.tags,
                    url=doc_request.url,
                )

                # Index document
                success = await collection_manager.index_document(
                    text=doc_request.text,
                    metadata=metadata,
                    collection_type=collection_type,
                )

                results.append(
                    {
                        "doc_id": doc_request.doc_id,
                        "success": success,
                        "message": (
                            "Indexed successfully" if success else "Indexing failed"
                        ),
                    }
                )

            except Exception as e:
                results.append(
                    {
                        "doc_id": doc_request.doc_id,
                        "success": False,
                        "message": f"Error: {str(e)}",
                    }
                )

        duration = time.time() - start_time
        successful_count = sum(1 for r in results if r["success"])

        # Record metrics
        record_semantic_search_metrics(
            endpoint="/qdrant/documents/bulk-index",
            duration=duration,
            results_count=successful_count,
            relevance_score=successful_count / len(documents) if documents else 0.0,
            status="success",
            query_type="bulk_indexing",
        )

        return {
            "success": True,
            "total_documents": len(documents),
            "successful": successful_count,
            "failed": len(documents) - successful_count,
            "results": results,
            "processing_time_ms": duration * 1000,
        }

    except Exception as e:
        logger.error(f"Bulk indexing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk indexing failed: {str(e)}")
