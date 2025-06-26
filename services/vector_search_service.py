"""
Vector search service for semantic document search.
Implements hybrid search with relevance scoring.

Enhanced with standardized async patterns for enterprise reliability.
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio
from vectorstore.collections import get_collection_manager, CollectionType, DocumentMetadata
from vectorstore.embeddings import get_embeddings_service

# Import standardized async patterns
from app.core.async_utils import (
    AsyncTimeouts, 
    with_timeout, 
    async_retry,
    safe_gather,
    create_background_task
)
from app.core.exceptions import AsyncTimeoutError, AsyncRetryError

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Structured search result."""
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

@dataclass
class SearchRequest:
    """Search request parameters."""
    query: str
    collections: Optional[List[str]] = None
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None
    include_snippets: bool = True
    hybrid_search: bool = True

class VectorSearchService:
    """Service for semantic document search with advanced features."""
    
    def __init__(self):
        """Initialize search service."""
        self.collection_manager = get_collection_manager()
        self.embeddings = get_embeddings_service()
    
    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def search(self, request: SearchRequest) -> List[SearchResult]:
        """
        Perform semantic search across document collections.
        Enhanced with timeout protection and retry logic.
        
        Args:
            request: Search request parameters
            
        Returns:
            List of search results ordered by relevance
            
        Raises:
            AsyncTimeoutError: If search times out
            AsyncRetryError: If search fails after retries
        """
        try:
            # Calculate timeout based on search complexity
            timeout = self._calculate_search_timeout(request)
            
            return await with_timeout(
                self._search_internal(request),
                timeout,
                f"Vector search timed out (query: '{request.query[:50]}...', collections: {request.collections}, limit: {request.limit})",
                {
                    "query_length": len(request.query),
                    "collections_count": len(request.collections) if request.collections else "all",
                    "limit": request.limit,
                    "hybrid_search": request.hybrid_search
                }
            )
            
        except AsyncTimeoutError as e:
            logger.error(f"❌ Vector search timed out: {e}")
            raise
        except AsyncRetryError as e:
            logger.error(f"❌ Vector search failed after retries: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}")
            return []
    
    async def _search_internal(self, request: SearchRequest) -> List[SearchResult]:
        """Internal search method without timeout wrapper"""
        # Determine collections to search
        collection_types = self._parse_collections(request.collections)
        
        logger.info(f"🔍 Searching {len(collection_types)} collections for: '{request.query[:100]}...'")
        
        # Perform vector search with enhanced error handling
        raw_results = await self.collection_manager.search_documents(
            query=request.query,
            collection_types=collection_types,
            limit=request.limit,
            filters=request.filters
        )
        
        # Process and enhance results
        search_results = self._process_search_results(
            raw_results=raw_results,
            query=request.query,
            include_snippets=request.include_snippets
        )
        
        # Apply hybrid search if enabled
        if request.hybrid_search:
            search_results = self._apply_hybrid_scoring(
                results=search_results,
                query=request.query
            )
        
        # Sort by final score and limit
        search_results.sort(key=lambda x: x.score, reverse=True)
        final_results = search_results[:request.limit]
        
        logger.info(f"✅ Search completed: {len(final_results)} results found")
        return final_results
    
    def _calculate_search_timeout(self, request: SearchRequest) -> float:
        """Calculate appropriate timeout based on search complexity"""
        base_timeout = AsyncTimeouts.VECTOR_SEARCH  # 15 seconds
        
        # Add extra time for complex searches
        extra_time = 0
        
        # More collections = more time
        if request.collections:
            extra_time += len(request.collections) * 2  # 2s per collection
        else:
            extra_time += 10  # 10s for all collections
        
        # Large result sets need more time
        if request.limit > 50:
            extra_time += (request.limit - 50) / 10  # 1s per extra 10 results
        
        # Hybrid search adds processing time
        if request.hybrid_search:
            extra_time += 5  # 5s for hybrid processing
        
        return min(base_timeout + extra_time, 60.0)  # Cap at 1 minute
    
    def _parse_collections(self, collections: Optional[List[str]]) -> List[CollectionType]:
        """Parse collection names to CollectionType enum."""
        if not collections:
            return list(CollectionType)
        
        parsed_collections = []
        for col_name in collections:
            try:
                if col_name.startswith("docs_"):
                    col_type = CollectionType(col_name.replace("docs_", ""))
                else:
                    col_type = CollectionType(col_name)
                parsed_collections.append(col_type)
            except ValueError:
                logger.warning(f"Unknown collection type: {col_name}")
        
        return parsed_collections or list(CollectionType)
    
    def _process_search_results(
        self,
        raw_results: List[Dict[str, Any]],
        query: str,
        include_snippets: bool = True
    ) -> List[SearchResult]:
        """Process raw search results into structured format."""
        results = []
        
        for raw_result in raw_results:
            payload = raw_result.get("payload", {})
            
            # Extract content and create snippet
            content = payload.get("text", "")
            highlights = []
            
            if include_snippets and content:
                highlights = self._generate_highlights(content, query)
            
            # Create search result
            result = SearchResult(
                doc_id=payload.get("doc_id", ""),
                title=payload.get("title", "Untitled"),
                content=content,
                score=raw_result.get("score", 0.0),
                source=payload.get("source", ""),
                source_type=payload.get("source_type", ""),
                url=payload.get("url"),
                author=payload.get("author"),
                created_at=payload.get("created_at"),
                tags=payload.get("tags", []),
                collection_name=raw_result.get("collection_name"),
                chunk_index=payload.get("chunk_index"),
                highlights=highlights
            )
            
            results.append(result)
        
        return results
    
    def _generate_highlights(self, content: str, query: str, max_highlights: int = 3) -> List[str]:
        """Generate text highlights for search query."""
        if not content or not query:
            return []
        
        highlights = []
        query_terms = query.lower().split()
        content_lower = content.lower()
        
        # Find sentences containing query terms
        sentences = content.split('. ')
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check if sentence contains any query terms
            if any(term in sentence_lower for term in query_terms):
                # Limit sentence length
                if len(sentence) > 200:
                    # Find position of first query term
                    first_pos = len(sentence)
                    for term in query_terms:
                        if term in sentence_lower:
                            pos = sentence_lower.find(term)
                            if pos < first_pos:
                                first_pos = pos
                    
                    # Extract snippet around the term
                    start = max(0, first_pos - 100)
                    end = min(len(sentence), first_pos + 100)
                    snippet = "..." + sentence[start:end] + "..."
                    highlights.append(snippet)
                else:
                    highlights.append(sentence)
                
                if len(highlights) >= max_highlights:
                    break
        
        return highlights
    
    def _apply_hybrid_scoring(
        self,
        results: List[SearchResult],
        query: str
    ) -> List[SearchResult]:
        """Apply hybrid scoring combining semantic and keyword matching."""
        query_terms = set(query.lower().split())
        
        for result in results:
            # Original semantic score (0-1)
            semantic_score = result.score
            
            # Keyword matching score
            content_terms = set(result.content.lower().split())
            title_terms = set(result.title.lower().split())
            
            # Calculate keyword overlap
            content_overlap = len(query_terms.intersection(content_terms))
            title_overlap = len(query_terms.intersection(title_terms))
            
            # Keyword score (normalized)
            keyword_score = (content_overlap + title_overlap * 2) / (len(query_terms) * 3)
            keyword_score = min(keyword_score, 1.0)  # Cap at 1.0
            
            # Combine scores (weighted)
            hybrid_score = (semantic_score * 0.7) + (keyword_score * 0.3)
            
            # Bonus for exact phrase matches
            if query.lower() in result.content.lower():
                hybrid_score *= 1.1
            if query.lower() in result.title.lower():
                hybrid_score *= 1.2
            
            # Update result score
            result.score = min(hybrid_score, 1.0)
        
        return results
    
    @async_retry(max_attempts=2, delay=2.0, exceptions=(Exception,))
    async def index_document(
        self,
        text: str,
        doc_id: str,
        title: str,
        source: str,
        source_type: str = "documents",
        **metadata
    ) -> bool:
        """
        Index a single document.
        Enhanced with timeout protection and retry logic.
        
        Args:
            text: Document text content
            doc_id: Unique document identifier
            title: Document title
            source: Document source/origin
            source_type: Type of source (documents, confluence, etc.)
            **metadata: Additional metadata
            
        Returns:
            True if successful
            
        Raises:
            AsyncTimeoutError: If indexing times out
        """
        try:
            # Validate input
            if not text.strip():
                raise ValueError(f"Document text cannot be empty for doc_id: {doc_id}")
            
            if len(text) > 1000000:  # 1MB limit
                raise ValueError(f"Document too large ({len(text)} chars). Maximum 1,000,000 characters.")
            
            # Calculate timeout based on document size
            timeout = self._calculate_indexing_timeout(text)
            
            return await with_timeout(
                self._index_document_internal(text, doc_id, title, source, source_type, **metadata),
                timeout,
                f"Document indexing timed out (doc_id: {doc_id}, size: {len(text)} chars)",
                {
                    "doc_id": doc_id,
                    "text_length": len(text),
                    "source_type": source_type,
                    "has_metadata": bool(metadata)
                }
            )
            
        except (AsyncTimeoutError, ValueError) as e:
            logger.error(f"❌ Document indexing failed for {doc_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Document indexing failed for {doc_id}: {e}")
            return False
    
    async def _index_document_internal(
        self, text: str, doc_id: str, title: str, source: str, source_type: str, **metadata
    ) -> bool:
        """Internal indexing method without timeout wrapper"""
        # Parse collection type
        collection_type = CollectionType(source_type)
        
        # Create metadata object
        doc_metadata = DocumentMetadata(
            doc_id=doc_id,
            title=title,
            source=source,
            source_type=collection_type,
            author=metadata.get("author"),
            created_at=metadata.get("created_at"),
            updated_at=metadata.get("updated_at"),
            url=metadata.get("url"),
            tags=metadata.get("tags"),
            content_type=metadata.get("content_type"),
            file_path=metadata.get("file_path")
        )
        
        logger.info(f"🔄 Indexing document: {doc_id} ({len(text)} chars)")
        
        # Index document
        success = await self.collection_manager.index_document(
            text=text,
            metadata=doc_metadata,
            collection_type=collection_type
        )
        
        if success:
            logger.info(f"✅ Successfully indexed document: {doc_id}")
        else:
            logger.error(f"❌ Failed to index document: {doc_id}")
        
        return success
    
    def _calculate_indexing_timeout(self, text: str) -> float:
        """Calculate appropriate timeout based on document size"""
        base_timeout = AsyncTimeouts.EMBEDDING_GENERATION  # 30 seconds
        
        # Add extra time for large documents (rough estimate: 1000 chars/second processing)
        if len(text) > 10000:
            extra_time = (len(text) - 10000) / 1000  # 1 second per extra 1000 chars
            return min(base_timeout + extra_time, 300.0)  # Cap at 5 minutes
        
        return base_timeout
    
    async def delete_document(self, doc_id: str, source_type: str = "documents") -> bool:
        """
        Delete document from index.
        
        Args:
            doc_id: Document ID to delete
            source_type: Collection type
            
        Returns:
            True if successful
        """
        try:
            collection_type = CollectionType(source_type)
            success = await self.collection_manager.delete_document(
                doc_id=doc_id,
                collection_type=collection_type
            )
            
            if success:
                logger.info(f"Successfully deleted document: {doc_id}")
            else:
                logger.warning(f"Document not found or deletion failed: {doc_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Document deletion failed for {doc_id}: {e}")
            return False
    
    @async_retry(max_attempts=2, delay=1.5, exceptions=(Exception,))
    async def get_similar_documents(
        self,
        doc_id: str,
        source_type: str = "documents",
        limit: int = 5
    ) -> List[SearchResult]:
        """
        Find documents similar to the given document.
        Enhanced with timeout protection and better error handling.
        
        Args:
            doc_id: Reference document ID
            source_type: Collection type
            limit: Maximum number of results
            
        Returns:
            List of similar documents
            
        Raises:
            AsyncTimeoutError: If similarity search times out
        """
        try:
            return await with_timeout(
                self._get_similar_documents_internal(doc_id, source_type, limit),
                AsyncTimeouts.VECTOR_SEARCH * 1.5,  # 22.5 seconds for similarity search
                f"Similar documents search timed out (doc_id: {doc_id}, source_type: {source_type}, limit: {limit})",
                {"doc_id": doc_id, "source_type": source_type, "limit": limit}
            )
            
        except AsyncTimeoutError as e:
            logger.error(f"❌ Similar documents search timed out: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Similar documents search failed for {doc_id}: {e}")
            return []
    
    async def _get_similar_documents_internal(
        self, doc_id: str, source_type: str, limit: int
    ) -> List[SearchResult]:
        """Internal similar documents search method"""
        logger.info(f"🔍 Finding similar documents for: {doc_id}")
        
        # First, find the document content
        collection_type = CollectionType(source_type)
        collection_name = self.collection_manager.get_collection_name(collection_type)
        
        # Search for the document chunks with timeout
        dummy_vector = [0.0] * 1536
        
        # Use timeout for the vector search operation
        results = await with_timeout(
            asyncio.to_thread(
                self.collection_manager.qdrant.search_vectors,
                collection_name=collection_name,
                query_vector=dummy_vector,
                limit=1,
                filter_conditions={"doc_id": doc_id}
            ),
            AsyncTimeouts.DATABASE_QUERY,  # 10 seconds for document lookup
            f"Document lookup timed out for doc_id: {doc_id}"
        )
        
        if not results:
            logger.warning(f"⚠️ Document not found: {doc_id}")
            return []
        
        # Use the document content as query
        doc_content = results[0]["payload"].get("text", "")
        if not doc_content:
            logger.warning(f"⚠️ Document has no content: {doc_id}")
            return []
        
        # Search for similar documents using enhanced search
        search_request = SearchRequest(
            query=doc_content[:500],  # Use first 500 chars as query
            collections=[source_type],
            limit=limit + 1,  # +1 to account for self-match
            include_snippets=False,
            hybrid_search=True  # Use hybrid search for better results
        )
        
        similar_results = await self.search(search_request)
        
        # Filter out the original document
        filtered_results = [
            result for result in similar_results 
            if result.doc_id != doc_id
        ]
        
        final_results = filtered_results[:limit]
        logger.info(f"✅ Found {len(final_results)} similar documents for: {doc_id}")
        
        return final_results
    
    async def get_search_stats(self) -> Dict[str, Any]:
        """
        Get search service statistics.
        Enhanced with timeout protection and async operations.
        """
        try:
            logger.info("🔄 Collecting vector search service statistics...")
            
            # Collect stats with timeout protection
            stats_data = await with_timeout(
                self._collect_stats_internal(),
                AsyncTimeouts.DATABASE_QUERY * 2,  # 20 seconds for stats collection
                "Search stats collection timed out"
            )
            
            logger.info("✅ Search stats collected successfully")
            return stats_data
            
        except AsyncTimeoutError as e:
            logger.warning(f"⚠️ Search stats collection timed out: {e}")
            return {
                "status": "timeout",
                "error": f"Stats collection timed out: {e}",
                "partial_data": True
            }
        except Exception as e:
            logger.error(f"❌ Failed to get search stats: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _collect_stats_internal(self) -> Dict[str, Any]:
        """Internal stats collection method"""
        # Get collection stats with timeout
        collection_stats = await with_timeout(
            asyncio.to_thread(self.collection_manager.get_collection_stats),
            AsyncTimeouts.DATABASE_QUERY,  # 10 seconds for collection stats
            "Collection stats collection timed out"
        )
        
        # Get Qdrant health check with timeout
        qdrant_status = await with_timeout(
            asyncio.to_thread(self.collection_manager.qdrant.health_check),
            AsyncTimeouts.HTTP_REQUEST,  # 30 seconds for health check
            "Qdrant health check timed out"
        )
        
        # Count active collections
        active_collections = sum(
            1 for stats in collection_stats.values() 
            if stats.get("exists", False)
        )
        
        return {
            "status": "healthy",
            "active_collections": active_collections,
            "total_collections": len(collection_stats),
            "collections": collection_stats,
            "embeddings_service": {
                "model": self.embeddings.model,
                "max_tokens": self.embeddings.max_tokens,
                "status": "healthy"
            },
            "qdrant_status": qdrant_status,
            "async_patterns_enabled": True,
            "timeout_protection": "enabled"
        }

# Global search service instance
_search_service = None

def get_vector_search_service() -> VectorSearchService:
    """Get global vector search service instance."""
    global _search_service
    if _search_service is None:
        _search_service = VectorSearchService()
    return _search_service 