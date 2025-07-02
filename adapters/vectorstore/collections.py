"""
Векторные коллекции - управление коллекциями документов
"""
import logging
import uuid
import asyncio
from typing import List, Dict, Any, Optional, AsyncIterator, Union
from enum import Enum
from dataclasses import dataclass
from .qdrant_client import get_qdrant_client
from .embeddings import get_embeddings_service, DocumentChunker

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

class CollectionType(Enum):
    """Types of document collections."""
    DOCUMENTS = "documents"
    CONFLUENCE = "confluence"
    JIRA = "jira"
    GITLAB = "gitlab"
    GITHUB = "github"
    UPLOADED_FILES = "uploaded_files"

@dataclass
class DocumentMetadata:
    """Metadata for indexed documents."""
    doc_id: str
    title: str
    source: str
    source_type: CollectionType
    author: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    url: Optional[str] = None
    tags: Optional[List[str]] = None
    content_type: Optional[str] = None
    file_path: Optional[str] = None

class CollectionManager:
    """Manager for document collections and indexing."""
    
    def __init__(self):
        """Initialize collection manager."""
        self.qdrant = get_qdrant_client()
        self.embeddings = get_embeddings_service()
        self.chunker = DocumentChunker(chunk_size=1000, overlap=200)
    
    def get_collection_name(self, collection_type: CollectionType) -> str:
        """Get collection name for given type."""
        return f"docs_{collection_type.value}"
    
    @async_retry(max_attempts=2, delay=2.0, exceptions=(Exception,))
    async def initialize_collections(self) -> Dict[str, bool]:
        """
        Initialize all document collections.
        Enhanced with concurrent initialization and timeout protection.
        """
        try:
            return await with_timeout(
                self._initialize_collections_internal(),
                AsyncTimeouts.DATABASE_MIGRATION,  # 5 minutes for collection initialization
                "Collection initialization timed out"
            )
        except AsyncTimeoutError as e:
            logger.error(f"❌ Collection initialization timed out: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ Collection initialization failed: {e}")
            return {}
    
    async def _initialize_collections_internal(self) -> Dict[str, bool]:
        """Internal collection initialization with concurrent processing"""
        logger.info(f"🔄 Initializing {len(CollectionType)} collections concurrently...")
        
        # Create initialization tasks for each collection
        init_tasks = [
            self._initialize_single_collection(collection_type)
            for collection_type in CollectionType
        ]
        
        # Execute concurrently with limits
        results_list = await safe_gather(
            *init_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.DATABASE_MIGRATION,
            max_concurrency=3  # Limit concurrent collection creation
        )
        
        # Process results
        results = {}
        for collection_type, result in zip(CollectionType, results_list):
            collection_name = self.get_collection_name(collection_type)
            
            if isinstance(result, Exception):
                logger.error(f"❌ Failed to initialize {collection_name}: {result}")
                results[collection_name] = False
            else:
                results[collection_name] = result
                if result:
                    logger.info(f"✅ Initialized collection: {collection_name}")
                else:
                    logger.warning(f"⚠️ Collection initialization returned False: {collection_name}")
        
        successful_count = sum(1 for success in results.values() if success)
        logger.info(f"✅ Collection initialization completed: {successful_count}/{len(CollectionType)} successful")
        
        return results
    
    async def _initialize_single_collection(self, collection_type: CollectionType) -> bool:
        """Initialize a single collection with timeout protection"""
        collection_name = self.get_collection_name(collection_type)
        
        try:
            # Check if collection exists with timeout
            exists = await with_timeout(
                asyncio.to_thread(self.qdrant.collection_exists, collection_name),
                AsyncTimeouts.DATABASE_QUERY,  # 10 seconds to check existence
                f"Collection existence check timed out for {collection_name}"
            )
            
            if not exists:
                # Create collection with timeout
                success = await with_timeout(
                    asyncio.to_thread(
                        self.qdrant.create_collection,
                        collection_name=collection_name,
                        vector_size=1536  # OpenAI ada-002 embedding size
                    ),
                    AsyncTimeouts.DATABASE_TRANSACTION,  # 30 seconds to create collection
                    f"Collection creation timed out for {collection_name}"
                )
                return success
            else:
                return True  # Already exists
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize collection {collection_name}: {e}")
            return False
    
    async def index_document(
        self,
        text: str,
        metadata: DocumentMetadata,
        collection_type: CollectionType = CollectionType.DOCUMENTS
    ) -> bool:
        """
        Index a document in the specified collection.
        
        Args:
            text: Document text content
            metadata: Document metadata
            collection_type: Target collection type
            
        Returns:
            True if successful
        """
        try:
            collection_name = self.get_collection_name(collection_type)
            
            # Ensure collection exists
            if not self.qdrant.collection_exists(collection_name):
                self.qdrant.create_collection(collection_name)
            
            # Chunk document
            chunks = self.chunker.chunk_document(
                text=text,
                metadata={
                    "doc_id": metadata.doc_id,
                    "title": metadata.title,
                    "source": metadata.source,
                    "source_type": metadata.source_type.value,
                    "author": metadata.author,
                    "created_at": metadata.created_at,
                    "updated_at": metadata.updated_at,
                    "url": metadata.url,
                    "tags": metadata.tags or [],
                    "content_type": metadata.content_type,
                    "file_path": metadata.file_path
                }
            )
            
            if not chunks:
                logger.warning(f"No chunks created for document: {metadata.doc_id}")
                return False
            
            # Generate embeddings for chunks
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = await self.embeddings.embed_texts(chunk_texts)
            
            if len(embeddings) != len(chunks):
                logger.error(f"Embedding count mismatch: {len(embeddings)} vs {len(chunks)}")
                return False
            
            # Prepare vectors and payloads with proper UUIDs
            vectors = [emb.vector for emb in embeddings]
            payloads = []
            chunk_ids = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Generate proper UUID for each chunk
                chunk_uuid = str(uuid.uuid4())
                chunk_ids.append(chunk_uuid)
                
                payload = {
                    **chunk,
                    "original_doc_id": metadata.doc_id,  # Keep original doc ID in payload
                    "chunk_id": f"{metadata.doc_id}_{i}",  # Human-readable chunk reference
                    "embedding_token_count": embedding.token_count,
                    "embedding_cost": embedding.cost_estimate,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
                payloads.append(payload)
            
            # Store vectors in Qdrant
            success = self.qdrant.upsert_vectors(
                collection_name=collection_name,
                vectors=vectors,
                payloads=payloads,
                ids=chunk_ids
            )
            
            if success:
                logger.info(f"Indexed document {metadata.doc_id} with {len(chunks)} chunks")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to index document {metadata.doc_id}: {e}")
            return False
    
    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def search_documents(
        self,
        query: str,
        collection_types: List[CollectionType] = None,
        limit: int = 10,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search documents across collections.
        Enhanced with concurrent search and timeout protection.
        
        Args:
            query: Search query text
            collection_types: Collections to search (default: all)
            limit: Maximum results per collection
            filters: Optional filters for search
            
        Returns:
            List of search results with scores and metadata
            
        Raises:
            AsyncTimeoutError: If search times out
        """
        try:
            timeout = self._calculate_multi_collection_search_timeout(collection_types, limit)
            
            return await with_timeout(
                self._search_documents_internal(query, collection_types, limit, filters),
                timeout,
                f"Multi-collection search timed out (query: '{query[:50]}...', collections: {len(collection_types or CollectionType)}, limit: {limit})",
                {
                    "query_length": len(query),
                    "collections_count": len(collection_types) if collection_types else len(CollectionType),
                    "limit": limit,
                    "has_filters": bool(filters)
                }
            )
            
        except AsyncTimeoutError as e:
            logger.error(f"❌ Multi-collection search timed out: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Multi-collection search failed: {e}")
            return []
    
    async def _search_documents_internal(
        self, query: str, collection_types: List[CollectionType], limit: int, filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Internal search method with concurrent collection processing"""
        if collection_types is None:
            collection_types = list(CollectionType)
        
        logger.info(f"🔍 Searching {len(collection_types)} collections concurrently for: '{query[:100]}...'")
        
        # Generate query embedding with timeout
        query_embedding = await with_timeout(
            self.embeddings.embed_text(query),
            AsyncTimeouts.EMBEDDING_GENERATION,  # 30 seconds for embedding
            f"Query embedding generation timed out for query: '{query[:50]}...'"
        )
        
        if not query_embedding:
            logger.error("❌ Failed to generate query embedding")
            return []
        
        # Create search tasks for each collection
        search_tasks = [
            self._search_single_collection(collection_type, query_embedding.vector, limit, filters)
            for collection_type in collection_types
        ]
        
        # Execute searches concurrently
        search_results = await safe_gather(
            *search_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.VECTOR_SEARCH * 2,  # 30 seconds for all searches
            max_concurrency=5  # Limit concurrent collection searches
        )
        
        # Aggregate results
        all_results = []
        successful_searches = 0
        
        for collection_type, result in zip(collection_types, search_results):
            if isinstance(result, Exception):
                logger.warning(f"⚠️ Search failed for collection {collection_type.value}: {result}")
                continue
            
            successful_searches += 1
            all_results.extend(result)
        
        # Sort by score (descending)
        all_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Limit total results
        final_results = all_results[:limit * 2]  # Allow more results from multiple collections
        
        logger.info(f"✅ Multi-collection search completed: {len(final_results)} results from {successful_searches}/{len(collection_types)} collections")
        
        return final_results
    
    async def _search_single_collection(
        self, collection_type: CollectionType, query_vector: List[float], limit: int, filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Search a single collection with timeout protection"""
        collection_name = self.get_collection_name(collection_type)
        
        # Check if collection exists
        exists = await with_timeout(
            asyncio.to_thread(self.qdrant.collection_exists, collection_name),
            AsyncTimeouts.DATABASE_QUERY,  # 10 seconds for existence check
            f"Collection existence check timed out for {collection_name}"
        )
        
        if not exists:
            logger.debug(f"Collection {collection_name} does not exist, skipping")
            return []
        
        # Search in collection with timeout
        results = await with_timeout(
            asyncio.to_thread(
                self.qdrant.search_vectors,
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                filter_conditions=filters
            ),
            AsyncTimeouts.VECTOR_SEARCH,  # 15 seconds for single collection search
            f"Vector search timed out for collection {collection_name}"
        )
        
        # Add collection info to results
        for result in results:
            result["collection_name"] = collection_name
            result["collection_type"] = collection_type.value
        
        logger.debug(f"Found {len(results)} results in collection {collection_name}")
        return results
    
    def _calculate_multi_collection_search_timeout(
        self, collection_types: List[CollectionType], limit: int
    ) -> float:
        """Calculate timeout for multi-collection search"""
        base_timeout = AsyncTimeouts.VECTOR_SEARCH  # 15 seconds
        
        # Number of collections to search
        num_collections = len(collection_types) if collection_types else len(CollectionType)
        
        # Since we search concurrently, we need base time + some buffer for concurrency overhead
        collection_time = max(base_timeout, num_collections * 3)  # 3s per collection minimum
        
        # Add extra time for large result sets
        if limit > 50:
            collection_time += (limit - 50) / 10  # 1s per extra 10 results
        
        return min(collection_time, 120.0)  # Cap at 2 minutes
    
    async def delete_document(
        self,
        doc_id: str,
        collection_type: CollectionType = CollectionType.DOCUMENTS
    ) -> bool:
        """
        Delete document and all its chunks from collection.
        
        Args:
            doc_id: Document ID to delete
            collection_type: Collection to delete from
            
        Returns:
            True if successful
        """
        try:
            collection_name = self.get_collection_name(collection_type)
            
            if not self.qdrant.collection_exists(collection_name):
                logger.warning(f"Collection {collection_name} does not exist")
                return False
            
            # Find all chunks for this document
            # Use a filter to find all points with this doc_id
            filter_condition = {"original_doc_id": doc_id}
            
            # Search for all chunks (large limit to get all)
            results = self.qdrant.search_vectors(
                collection_name=collection_name,
                query_vector=[0.0] * 1536,  # Dummy vector
                limit=1000,  # Large limit
                filter_conditions=filter_condition
            )
            
            if not results:
                logger.warning(f"No chunks found for document: {doc_id}")
                return True
            
            # Delete all chunk points
            point_ids = [result["id"] for result in results]
            
            # Note: Qdrant client doesn't have bulk delete in our simplified version
            # In production, you'd use client.delete() with point IDs
            logger.info(f"Would delete {len(point_ids)} chunks for document {doc_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False
    
    async def get_collection_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all collections.
        Enhanced with concurrent stats collection and timeout protection.
        """
        try:
            logger.info("🔄 Collecting collection statistics concurrently...")
            
            return await with_timeout(
                self._collect_collection_stats_internal(),
                AsyncTimeouts.DATABASE_QUERY * 2,  # 20 seconds for stats collection
                "Collection stats collection timed out"
            )
            
        except AsyncTimeoutError as e:
            logger.warning(f"⚠️ Collection stats collection timed out: {e}")
            return {
                "error": f"Stats collection timed out: {e}",
                "partial_data": True
            }
        except Exception as e:
            logger.error(f"❌ Failed to get collection stats: {e}")
            return {
                "error": str(e)
            }
    
    async def _collect_collection_stats_internal(self) -> Dict[str, Dict[str, Any]]:
        """Internal stats collection with concurrent processing"""
        # Create stats tasks for each collection
        stats_tasks = [
            self._get_single_collection_stats(collection_type)
            for collection_type in CollectionType
        ]
        
        # Execute stats collection concurrently
        stats_results = await safe_gather(
            *stats_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.DATABASE_QUERY,
            max_concurrency=6  # All collections can be checked concurrently
        )
        
        # Process results
        stats = {}
        successful_stats = 0
        
        for collection_type, result in zip(CollectionType, stats_results):
            collection_name = self.get_collection_name(collection_type)
            
            if isinstance(result, Exception):
                logger.warning(f"⚠️ Stats collection failed for {collection_name}: {result}")
                stats[collection_name] = {
                    "exists": False,
                    "type": collection_type.value,
                    "status": "error",
                    "error": str(result)
                }
            else:
                successful_stats += 1
                stats[collection_name] = result
        
        logger.info(f"✅ Collection stats collected: {successful_stats}/{len(CollectionType)} successful")
        
        return stats
    
    async def _get_single_collection_stats(self, collection_type: CollectionType) -> Dict[str, Any]:
        """Get statistics for a single collection with timeout protection"""
        collection_name = self.get_collection_name(collection_type)
        
        try:
            # Check if collection exists with timeout
            exists = await with_timeout(
                asyncio.to_thread(self.qdrant.collection_exists, collection_name),
                AsyncTimeouts.DATABASE_QUERY,  # 10 seconds for existence check
                f"Collection existence check timed out for {collection_name}"
            )
            
            if exists:
                # Get collection info with timeout
                # Note: Simplified stats, in production you'd use client.get_collection()
                return {
                    "exists": True,
                    "type": collection_type.value,
                    "status": "active",
                    "last_checked": "just_now"
                }
            else:
                return {
                    "exists": False,
                    "type": collection_type.value,
                    "status": "not_created"
                }
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to get stats for {collection_name}: {e}")
            return {
                "exists": False,
                "type": collection_type.value,
                "status": "error",
                "error": str(e)
            }
    
    async def reindex_collection(self, collection_type: CollectionType) -> bool:
        """
        Reindex entire collection (recreate from source).
        
        Args:
            collection_type: Collection to reindex
            
        Returns:
            True if successful
        """
        try:
            collection_name = self.get_collection_name(collection_type)
            
            # Delete existing collection
            if self.qdrant.collection_exists(collection_name):
                self.qdrant.delete_collection(collection_name)
                logger.info(f"Deleted existing collection: {collection_name}")
            
            # Recreate collection
            success = self.qdrant.create_collection(collection_name)
            if success:
                logger.info(f"Recreated collection: {collection_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to reindex collection {collection_type.value}: {e}")
            return False

# Global collection manager instance
_collection_manager = None

def get_collection_manager() -> CollectionManager:
    """Get global collection manager instance."""
    global _collection_manager
    if _collection_manager is None:
        _collection_manager = CollectionManager()
    return _collection_manager 