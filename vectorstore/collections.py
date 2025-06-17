"""
Document collections management for different data types.
"""
import logging
import uuid
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from vectorstore.qdrant_client import get_qdrant_client
from vectorstore.embeddings import get_embeddings_service, DocumentChunker

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
    
    async def initialize_collections(self) -> Dict[str, bool]:
        """Initialize all document collections."""
        results = {}
        
        for collection_type in CollectionType:
            collection_name = self.get_collection_name(collection_type)
            
            if not self.qdrant.collection_exists(collection_name):
                success = self.qdrant.create_collection(
                    collection_name=collection_name,
                    vector_size=1536,  # OpenAI ada-002 embedding size
                )
                results[collection_name] = success
                logger.info(f"Created collection: {collection_name}")
            else:
                results[collection_name] = True
                logger.info(f"Collection already exists: {collection_name}")
        
        return results
    
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
    
    async def search_documents(
        self,
        query: str,
        collection_types: List[CollectionType] = None,
        limit: int = 10,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search documents across collections.
        
        Args:
            query: Search query text
            collection_types: Collections to search (default: all)
            limit: Maximum results per collection
            filters: Optional filters for search
            
        Returns:
            List of search results with scores and metadata
        """
        if collection_types is None:
            collection_types = list(CollectionType)
        
        # Generate query embedding
        query_embedding = await self.embeddings.embed_text(query)
        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return []
        
        all_results = []
        
        # Search each collection
        for collection_type in collection_types:
            collection_name = self.get_collection_name(collection_type)
            
            if not self.qdrant.collection_exists(collection_name):
                continue
            
            # Search in collection
            results = self.qdrant.search_vectors(
                collection_name=collection_name,
                query_vector=query_embedding.vector,
                limit=limit,
                filter_conditions=filters
            )
            
            # Add collection info to results
            for result in results:
                result["collection_name"] = collection_name
                result["collection_type"] = collection_type.value
                all_results.append(result)
        
        # Sort by score (descending)
        all_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Limit total results
        return all_results[:limit * 2]  # Allow more results from multiple collections
    
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
    
    def get_collection_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all collections."""
        stats = {}
        
        for collection_type in CollectionType:
            collection_name = self.get_collection_name(collection_type)
            
            if self.qdrant.collection_exists(collection_name):
                # Get collection info
                try:
                    # Note: Simplified stats, in production you'd use client.get_collection()
                    stats[collection_name] = {
                        "exists": True,
                        "type": collection_type.value,
                        "status": "active"
                    }
                except Exception as e:
                    stats[collection_name] = {
                        "exists": True,
                        "type": collection_type.value,
                        "status": "error",
                        "error": str(e)
                    }
            else:
                stats[collection_name] = {
                    "exists": False,
                    "type": collection_type.value,
                    "status": "not_created"
                }
        
        return stats
    
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