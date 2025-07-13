"""
Vector Search Service для AI Assistant MVP
Высокоуровневый сервис для работы с векторным поиском
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio
import numpy as np

try:
    from adapters.vectorstore.qdrant_client import QdrantVectorStore, get_qdrant_store
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

from app.core.exceptions import ServiceError

logger = logging.getLogger(__name__)

class VectorSearchError(ServiceError):
    """Vector search service error"""
    pass

class DocumentEmbedding:
    """Document with embedding representation"""
    
    def __init__(self, doc_id: str, content: str, embedding: List[float],
                 metadata: Optional[Dict[str, Any]] = None):
        self.doc_id = doc_id
        self.content = content
        self.embedding = embedding
        self.metadata = metadata or {}

class SearchResult:
    """Search result with score and metadata"""
    
    def __init__(self, doc_id: str, content: str, score: float,
                 metadata: Optional[Dict[str, Any]] = None):
        self.doc_id = doc_id
        self.content = content
        self.score = score
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata
        }

class VectorSearchService:
    """High-level vector search service"""
    
    def __init__(self):
        self.store: Optional[QdrantVectorStore] = None
        self.default_collection = "documents"
        self.vector_dimension = 1536  # OpenAI embeddings default
        
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize vector search service"""
        try:
            if not QDRANT_AVAILABLE:
                raise VectorSearchError("Qdrant client not available")
            
            # Get Qdrant configuration
            qdrant_config = config.get('qdrant', {})
            host = qdrant_config.get('host', 'localhost')
            port = qdrant_config.get('port', 6333)
            
            # Initialize Qdrant store
            self.store = QdrantVectorStore(host=host, port=port)
            
            # Test connection
            health = await self.store.health_check()
            if health["status"] != "healthy":
                raise VectorSearchError(f"Qdrant connection failed: {health.get('error', 'Unknown')}")
            
            # Initialize default collections
            await self.store.initialize_default_collections()
            
            # Update configuration
            self.default_collection = config.get('default_collection', 'documents')
            self.vector_dimension = config.get('vector_dimension', 1536)
            
            logger.info(f"🔍 Vector search service initialized with Qdrant at {host}:{port}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector search service: {e}")
            raise VectorSearchError(f"Vector search initialization failed: {e}")
    
    async def add_document(self, doc_id: str, content: str, embedding: List[float],
                          metadata: Optional[Dict[str, Any]] = None,
                          collection: Optional[str] = None) -> bool:
        """Add document with embedding to vector store"""
        try:
            if not self.store:
                raise VectorSearchError("Vector search service not initialized")
            
            target_collection = collection or self.default_collection
            
            # Ensure collection exists
            if not self.store.collection_exists(target_collection):
                self.store.create_collection(target_collection, vector_size=len(embedding))
            
            # Prepare payload
            payload = {
                "doc_id": doc_id,
                "content": content,
                "metadata": metadata or {}
            }
            
            # Insert vector
            success = self.store.insert_vectors(
                collection_name=target_collection,
                vectors=[embedding],
                payloads=[payload],
                ids=[doc_id]
            )
            
            if success:
                logger.info(f"✅ Added document {doc_id} to {target_collection}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to add document {doc_id}: {e}")
            return False
    
    async def add_documents_batch(self, documents: List[DocumentEmbedding],
                                 collection: Optional[str] = None) -> int:
        """Add multiple documents in batch"""
        try:
            if not self.store:
                raise VectorSearchError("Vector search service not initialized")
            
            if not documents:
                return 0
            
            target_collection = collection or self.default_collection
            
            # Ensure collection exists
            if not self.store.collection_exists(target_collection):
                vector_size = len(documents[0].embedding)
                self.store.create_collection(target_collection, vector_size=vector_size)
            
            # Prepare batch data
            vectors = [doc.embedding for doc in documents]
            payloads = []
            ids = []
            
            for doc in documents:
                payload = {
                    "doc_id": doc.doc_id,
                    "content": doc.content,
                    "metadata": doc.metadata
                }
                payloads.append(payload)
                ids.append(doc.doc_id)
            
            # Insert batch
            success = self.store.insert_vectors(
                collection_name=target_collection,
                vectors=vectors,
                payloads=payloads,
                ids=ids
            )
            
            if success:
                logger.info(f"✅ Added {len(documents)} documents to {target_collection}")
                return len(documents)
            else:
                return 0
                
        except Exception as e:
            logger.error(f"❌ Failed to add batch documents: {e}")
            return 0
    
    async def search_similar(self, query_embedding: List[float],
                           limit: int = 10,
                           score_threshold: Optional[float] = None,
                           collection: Optional[str] = None) -> List[SearchResult]:
        """Search for similar documents"""
        try:
            if not self.store:
                raise VectorSearchError("Vector search service not initialized")
            
            target_collection = collection or self.default_collection
            
            # Perform search
            results = self.store.search_vectors(
                collection_name=target_collection,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Convert to SearchResult objects
            search_results = []
            for result in results:
                payload = result["payload"]
                search_result = SearchResult(
                    doc_id=payload.get("doc_id", result["id"]),
                    content=payload.get("content", ""),
                    score=result["score"],
                    metadata=payload.get("metadata", {})
                )
                search_results.append(search_result)
            
            logger.info(f"🔍 Found {len(search_results)} similar documents in {target_collection}")
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    async def search_by_text(self, query_text: str, embedding_function,
                           limit: int = 10,
                           score_threshold: Optional[float] = None,
                           collection: Optional[str] = None) -> List[SearchResult]:
        """Search by text query (requires embedding function)"""
        try:
            # Generate embedding for query text
            if asyncio.iscoroutinefunction(embedding_function):
                query_embedding = await embedding_function(query_text)
            else:
                query_embedding = embedding_function(query_text)
            
            # Search using embedding
            return await self.search_similar(
                query_embedding=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                collection=collection
            )
            
        except Exception as e:
            logger.error(f"❌ Text search failed: {e}")
            return []
    
    async def delete_document(self, doc_id: str,
                            collection: Optional[str] = None) -> bool:
        """Delete document from vector store"""
        try:
            if not self.store:
                raise VectorSearchError("Vector search service not initialized")
            
            target_collection = collection or self.default_collection
            
            success = self.store.delete_vectors(
                collection_name=target_collection,
                ids=[doc_id]
            )
            
            if success:
                logger.info(f"🗑️ Deleted document {doc_id} from {target_collection}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to delete document {doc_id}: {e}")
            return False
    
    async def get_collection_stats(self, collection: Optional[str] = None) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            if not self.store:
                return {"error": "Service not initialized"}
            
            target_collection = collection or self.default_collection
            
            if not self.store.collection_exists(target_collection):
                return {"error": f"Collection {target_collection} does not exist"}
            
            info = self.store.get_collection_info(target_collection)
            
            return {
                "collection": target_collection,
                "document_count": info.get("vector_count", 0),
                "status": info.get("status", "unknown"),
                "config": info.get("config", "")
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get collection stats: {e}")
            return {"error": str(e)}
    
    async def list_collections(self) -> List[str]:
        """List all available collections"""
        try:
            if not self.store:
                return []
            
            return self.store.list_collections()
            
        except Exception as e:
            logger.error(f"❌ Failed to list collections: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for vector search service"""
        try:
            if not self.store:
                return {
                    "status": "unhealthy",
                    "error": "Service not initialized"
                }
            
            # Get Qdrant health
            qdrant_health = self.store.health_check()
            
            # Get collections info
            collections = self.store.list_collections()
            
            return {
                "status": "healthy" if qdrant_health["status"] == "healthy" else "degraded",
                "qdrant": qdrant_health,
                "collections": len(collections),
                "default_collection": self.default_collection,
                "vector_dimension": self.vector_dimension
            }
            
        except Exception as e:
            logger.error(f"❌ Vector search health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Global service instance
vector_search_service = VectorSearchService()

# Convenience functions
async def search_documents(query_embedding: List[float], **kwargs) -> List[SearchResult]:
    """Convenience function for document search"""
    return await vector_search_service.search_similar(query_embedding, **kwargs)

async def add_document_to_search(doc_id: str, content: str, embedding: List[float], **kwargs) -> bool:
    """Convenience function to add document"""
    return await vector_search_service.add_document(doc_id, content, embedding, **kwargs)

async def get_search_stats() -> Dict[str, Any]:
    """Convenience function to get search statistics"""
    return await vector_search_service.get_collection_stats()
