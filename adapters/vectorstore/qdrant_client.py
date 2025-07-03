"""
Qdrant vector database client and connection management.
"""
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import ResponseHandlingException
import os

logger = logging.getLogger(__name__)

class QdrantVectorStore:
    """Qdrant vector database client with connection management."""
    
    def __init__(self, host: str = "localhost", port: int = 6333, use_memory: bool = False):
        """
        Initialize Qdrant client.
        
        Args:
            host: Qdrant server host
            port: Qdrant server port  
            use_memory: Use in-memory storage for development
        """
        self.host = host
        self.port = port
        self.use_memory = use_memory
        self._client = None
        self._connected = False
        
    @property
    def client(self) -> QdrantClient:
        """Get or create Qdrant client."""
        if self._client is None:
            self._connect()
        return self._client
    
    def _connect(self) -> None:
        """Establish connection to Qdrant."""
        try:
            if self.use_memory:
                # In-memory client for development
                self._client = QdrantClient(":memory:")
                logger.info("Connected to Qdrant in-memory mode")
            else:
                # Real Qdrant server
                self._client = QdrantClient(
                    host=self.host,
                    port=self.port,
                    timeout=30
                )
                logger.info(f"Connected to Qdrant at {self.host}:{self.port}")
            
            self._connected = True
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            # Fallback to in-memory for development
            self._client = QdrantClient(":memory:")
            self.use_memory = True
            self._connected = True
            logger.warning("Fallback to in-memory Qdrant client")
    
    def health_check(self) -> Dict[str, Any]:
        """Check Qdrant health status."""
        try:
            if not self._connected:
                self._connect()
            
            # For in-memory mode, always return healthy
            if self.use_memory:
                return {
                    "status": "healthy",
                    "connected": True,
                    "mode": "memory",
                    "cluster_info": None
                }
            
            # For server mode, try to get collections to test connection
            collections = self.client.get_collections()
            
            return {
                "status": "healthy",
                "connected": True,
                "mode": "server",
                "collections_count": len(collections.collections) if collections else 0
            }
            
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return {
                "status": "unhealthy", 
                "connected": False,
                "error": str(e)
            }
    
    def create_collection(
        self,
        collection_name: str,
        vector_size: int = 1536,  # OpenAI embedding size
        distance: models.Distance = models.Distance.COSINE
    ) -> bool:
        """
        Create a new collection.
        
        Args:
            collection_name: Name of the collection
            vector_size: Size of vectors (default: OpenAI embedding size)
            distance: Distance metric for similarity search
            
        Returns:
            True if created successfully
        """
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=distance
                )
            )
            logger.info(f"Created collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists."""
        try:
            collections = self.client.get_collections()
            return any(c.name == collection_name for c in collections.collections)
        except Exception as e:
            logger.error(f"Failed to check collection existence: {e}")
            return False
    
    def upsert_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        Insert or update vectors in collection.
        
        Args:
            collection_name: Target collection
            vectors: List of vector embeddings
            payloads: Metadata for each vector
            ids: Optional custom IDs for vectors
            
        Returns:
            True if successful
        """
        try:
            if ids is None:
                ids = list(range(len(vectors)))
            
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=str(id_),
                        vector=vector,
                        payload=payload
                    )
                    for id_, vector, payload in zip(ids, vectors, payloads)
                ]
            )
            
            logger.info(f"Upserted {len(vectors)} vectors to {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {e}")
            return False
    
    def search_vectors(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        filter_conditions: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            collection_name: Collection to search in
            query_vector: Query embedding vector
            limit: Maximum number of results
            filter_conditions: Optional payload filters
            
        Returns:
            List of search results with scores and payloads
        """
        try:
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=models.Filter(**filter_conditions) if filter_conditions else None
            )
            
            results = []
            for result in search_result:
                results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })
            
            logger.info(f"Found {len(results)} similar vectors in {collection_name}")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

# Global instance
_qdrant_instance = None

def get_qdrant_client() -> QdrantVectorStore:
    """Get global Qdrant client instance."""
    global _qdrant_instance
    if _qdrant_instance is None:
        # Try to connect to real Qdrant, fallback to memory
        use_memory = os.getenv("QDRANT_USE_MEMORY", "false").lower() == "true"
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        
        _qdrant_instance = QdrantVectorStore(host=host, port=port, use_memory=use_memory)
    
    return _qdrant_instance 