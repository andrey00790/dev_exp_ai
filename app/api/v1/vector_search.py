"""
Vector search API endpoints for semantic document search.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
from services.vector_search_service import (
    get_vector_search_service, 
    VectorSearchService,
    SearchRequest,
    SearchResult
)
from vectorstore.collections import CollectionType
from app.security.auth import get_current_user
from app.security.rate_limiter import rate_limit_search as rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vector-search", tags=["Vector Search"])

# Pydantic models for API

class SearchRequestModel(BaseModel):
    """Search request model."""
    query: str = Field(..., description="Search query text", min_length=1, max_length=1000)
    collections: Optional[List[str]] = Field(None, description="Collections to search in")
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional search filters")
    include_snippets: bool = Field(True, description="Include text highlights in results")
    hybrid_search: bool = Field(True, description="Enable hybrid search (semantic + keyword)")

class SearchResultModel(BaseModel):
    """Search result model."""
    doc_id: str
    title: str
    content: str
    score: float
    source: str
    source_type: str
    url: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[str] = None
    tags: Optional[List[str]] = None
    collection_name: Optional[str] = None
    chunk_index: Optional[int] = None
    highlights: Optional[List[str]] = None

class SearchResponseModel(BaseModel):
    """Search response model."""
    query: str
    results: List[SearchResultModel]
    total_results: int
    search_time_ms: float
    collections_searched: List[str]

class IndexDocumentRequest(BaseModel):
    """Document indexing request."""
    text: str = Field(..., description="Document text content", min_length=1)
    doc_id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    source: str = Field(..., description="Document source/origin")
    source_type: str = Field("documents", description="Type of source")
    author: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    url: Optional[str] = None
    tags: Optional[List[str]] = None
    content_type: Optional[str] = None
    file_path: Optional[str] = None

class IndexDocumentResponse(BaseModel):
    """Document indexing response."""
    success: bool
    doc_id: str
    message: str

class DeleteDocumentResponse(BaseModel):
    """Document deletion response."""
    success: bool
    doc_id: str
    message: str

class SearchStatsResponse(BaseModel):
    """Search service statistics."""
    status: str
    active_collections: int
    total_collections: int
    collections: Dict[str, Any]
    embeddings_service: Dict[str, Any]
    qdrant_status: Dict[str, Any]

# API Endpoints

@router.post("/search", response_model=SearchResponseModel)

async def search_documents(
    request: SearchRequestModel,
    current_user: dict = Depends(get_current_user),
    search_service: VectorSearchService = Depends(get_vector_search_service)
):
    """
    Perform semantic search across document collections.
    
    Supports:
    - Semantic vector search using OpenAI embeddings
    - Hybrid search combining semantic and keyword matching  
    - Multi-collection search across different data sources
    - Advanced filtering and result highlighting
    """
    try:
        import time
        start_time = time.time()
        
        # Create search request
        search_request = SearchRequest(
            query=request.query,
            collections=request.collections,
            limit=request.limit,
            filters=request.filters,
            include_snippets=request.include_snippets,
            hybrid_search=request.hybrid_search
        )
        
        # Perform search
        results = await search_service.search(search_request)
        
        # Calculate search time
        search_time_ms = (time.time() - start_time) * 1000
        
        # Convert results to response model
        result_models = [
            SearchResultModel(
                doc_id=result.doc_id,
                title=result.title,
                content=result.content,
                score=result.score,
                source=result.source,
                source_type=result.source_type,
                url=result.url,
                author=result.author,
                created_at=result.created_at,
                tags=result.tags,
                collection_name=result.collection_name,
                chunk_index=result.chunk_index,
                highlights=result.highlights
            )
            for result in results
        ]
        
        # Determine which collections were searched
        collections_searched = request.collections or [col.value for col in CollectionType]
        
        return SearchResponseModel(
            query=request.query,
            results=result_models,
            total_results=len(result_models),
            search_time_ms=search_time_ms,
            collections_searched=collections_searched
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/index", response_model=IndexDocumentResponse)

async def index_document(
    request: IndexDocumentRequest,
    current_user: dict = Depends(get_current_user),
    search_service: VectorSearchService = Depends(get_vector_search_service)
):
    """
    Index a document for semantic search.
    
    The document will be:
    - Split into chunks for better search relevance
    - Converted to embeddings using OpenAI
    - Stored in the appropriate collection based on source_type
    """
    try:
        # Index the document
        success = await search_service.index_document(
            text=request.text,
            doc_id=request.doc_id,
            title=request.title,
            source=request.source,
            source_type=request.source_type,
            author=request.author,
            created_at=request.created_at,
            updated_at=request.updated_at,
            url=request.url,
            tags=request.tags,
            content_type=request.content_type,
            file_path=request.file_path
        )
        
        if success:
            return IndexDocumentResponse(
                success=True,
                doc_id=request.doc_id,
                message="Document indexed successfully"
            )
        else:
            return IndexDocumentResponse(
                success=False,
                doc_id=request.doc_id,
                message="Document indexing failed"
            )
            
    except Exception as e:
        logger.error(f"Document indexing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@router.delete("/documents/{doc_id}", response_model=DeleteDocumentResponse)

async def delete_document(
    doc_id: str,
    source_type: str = Query("documents", description="Collection type"),
    current_user: dict = Depends(get_current_user),
    search_service: VectorSearchService = Depends(get_vector_search_service)
):
    """
    Delete a document from the search index.
    
    This will remove all chunks of the document from the specified collection.
    """
    try:
        success = await search_service.delete_document(
            doc_id=doc_id,
            source_type=source_type
        )
        
        if success:
            return DeleteDocumentResponse(
                success=True,
                doc_id=doc_id,
                message="Document deleted successfully"
            )
        else:
            return DeleteDocumentResponse(
                success=False,
                doc_id=doc_id,
                message="Document not found or deletion failed"
            )
            
    except Exception as e:
        logger.error(f"Document deletion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

@router.get("/similar/{doc_id}", response_model=List[SearchResultModel])

async def get_similar_documents(
    doc_id: str,
    source_type: str = Query("documents", description="Collection type"),
    limit: int = Query(5, description="Maximum number of results", ge=1, le=20),
    current_user: dict = Depends(get_current_user),
    search_service: VectorSearchService = Depends(get_vector_search_service)
):
    """
    Find documents similar to the given document.
    
    Uses the document content to find semantically similar documents
    in the same or related collections.
    """
    try:
        results = await search_service.get_similar_documents(
            doc_id=doc_id,
            source_type=source_type,
            limit=limit
        )
        
        return [
            SearchResultModel(
                doc_id=result.doc_id,
                title=result.title,
                content=result.content,
                score=result.score,
                source=result.source,
                source_type=result.source_type,
                url=result.url,
                author=result.author,
                created_at=result.created_at,
                tags=result.tags,
                collection_name=result.collection_name,
                chunk_index=result.chunk_index,
                highlights=result.highlights
            )
            for result in results
        ]
        
    except Exception as e:
        logger.error(f"Similar documents search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Similar search failed: {str(e)}")

@router.get("/stats", response_model=SearchStatsResponse)
async def get_search_stats(
    current_user: dict = Depends(get_current_user),
    search_service: VectorSearchService = Depends(get_vector_search_service)
):
    """
    Get search service statistics and health information.
    
    Includes:
    - Collection status and counts
    - Qdrant connection status
    - Embeddings service configuration
    """
    try:
        stats = search_service.get_search_stats()
        
        return SearchStatsResponse(
            status=stats["status"],
            active_collections=stats["active_collections"],
            total_collections=stats["total_collections"],
            collections=stats["collections"],
            embeddings_service=stats["embeddings_service"],
            qdrant_status=stats["qdrant_status"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get search stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

@router.post("/collections/initialize")

async def initialize_collections(
    current_user: dict = Depends(get_current_user),
    search_service: VectorSearchService = Depends(get_vector_search_service)
):
    """
    Initialize all document collections.
    
    Creates Qdrant collections for all supported data source types.
    This is typically done once during system setup.
    """
    try:
        results = await search_service.collection_manager.initialize_collections()
        
        return {
            "success": True,
            "message": "Collections initialized",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Collection initialization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")

@router.post("/upload-file")

async def upload_and_index_file(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    current_user: dict = Depends(get_current_user),
    search_service: VectorSearchService = Depends(get_vector_search_service)
):
    """
    Upload and index a file for search.
    
    Supported formats: TXT, PDF, DOC, DOCX, MD
    The file will be processed, chunked, and indexed for semantic search.
    """
    try:
        # Validate file type
        allowed_types = {
            "text/plain": ".txt",
            "application/pdf": ".pdf", 
            "application/msword": ".doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "text/markdown": ".md"
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Read file content
        content = await file.read()
        
        # For now, handle text files directly
        # In production, you'd use document parsers for PDF, DOC, etc.
        if file.content_type == "text/plain" or file.content_type == "text/markdown":
            text_content = content.decode('utf-8')
        else:
            # Mock processing for other file types
            text_content = f"[Processed content from {file.filename}]\n\n" + \
                          content.decode('utf-8', errors='ignore')[:1000] + "..."
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Generate document ID
        doc_id = f"upload_{file.filename}_{hash(text_content) % 1000000}"
        
        # Index document
        success = await search_service.index_document(
            text=text_content,
            doc_id=doc_id,
            title=title or file.filename,
            source=f"uploaded_file:{file.filename}",
            source_type="uploaded_files",
            tags=tag_list,
            content_type=file.content_type,
            file_path=file.filename
        )
        
        return {
            "success": success,
            "doc_id": doc_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": len(content),
            "message": "File uploaded and indexed successfully" if success else "File upload failed"
        }
        
    except Exception as e:
        logger.error(f"File upload and indexing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/collections", response_model=Dict[str, Any])
async def list_collections(
    current_user: dict = Depends(get_current_user),
    search_service: VectorSearchService = Depends(get_vector_search_service)
):
    """
    List all available document collections and their status.
    """
    try:
        stats = search_service.collection_manager.get_collection_stats()
        
        return {
            "collections": stats,
            "total_collections": len(stats),
            "available_types": [col.value for col in CollectionType]
        }
        
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(status_code=500, detail=f"Collection listing failed: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Vector search service health check."""
    try:
        search_service = get_vector_search_service()
        stats = search_service.get_search_stats()
        
        return {
            "status": "healthy" if stats["status"] == "healthy" else "degraded",
            "timestamp": "2024-01-01T00:00:00Z",  # Replace with actual timestamp
            "service": "vector_search",
            "version": "1.0.0"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "vector_search"
        } 