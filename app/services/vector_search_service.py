"""
Vector Search Service
Handles vector-based semantic search operations
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
import numpy as np

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Vector search service for semantic search operations"""
    
    def __init__(self):
        self.embeddings_cache = {}
        self.documents = []
        self.initialized = False
        self.embedding_model = None
        
    async def initialize(self):
        """Initialize the vector search service"""
        if self.initialized:
            return
            
        # Mock initialization
        self.embedding_model = MockEmbeddingModel()
        self.initialized = True
        logger.info("VectorSearchService initialized")
    
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for given texts"""
        if not self.initialized:
            await self.initialize()
            
        embeddings = []
        for text in texts:
            # Check cache first
            if text in self.embeddings_cache:
                embeddings.append(self.embeddings_cache[text])
            else:
                # Generate mock embedding
                embedding = await self.embedding_model.encode(text)
                self.embeddings_cache[text] = embedding
                embeddings.append(embedding)
        
        return embeddings
    
    async def similarity_search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform similarity search using vector embeddings"""
        if not self.initialized:
            await self.initialize()
        
        # Create query embedding
        query_embedding = await self.embedding_model.encode(query)
        
        # Mock search results
        results = []
        for i in range(min(top_k, 5)):
            score = 0.95 - (i * 0.1)
            if score >= threshold:
                results.append({
                    "id": f"doc_{i}",
                    "content": f"Mock document {i} content for query: {query}",
                    "title": f"Document {i}",
                    "score": score,
                    "metadata": {
                        "source": "confluence",
                        "created_at": datetime.now().isoformat(),
                        "author": "Mock Author"
                    }
                })
        
        return results
    
    async def search(self, query: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Search method compatible with tests"""
        return await self.similarity_search(query, top_k=limit, **kwargs)
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """Add documents to the vector index"""
        if not self.initialized:
            await self.initialize()
        
        added_count = 0
        failed_count = 0
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            try:
                # Extract texts for embedding
                texts = [doc.get("content", "") for doc in batch]
                
                # Create embeddings
                embeddings = await self.create_embeddings(texts)
                
                # Store documents with embeddings
                for doc, embedding in zip(batch, embeddings):
                    doc["embedding"] = embedding
                    self.documents.append(doc)
                    added_count += 1
                
                # Simulate processing time
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to add batch: {e}")
                failed_count += len(batch)
        
        return {
            "added": added_count,
            "failed": failed_count,
            "total_documents": len(self.documents)
        }
    
    async def update_document(
        self,
        document_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update a document in the vector index"""
        if not self.initialized:
            await self.initialize()
        
        # Find and update document
        for i, doc in enumerate(self.documents):
            if doc.get("id") == document_id:
                # Update content and create new embedding
                doc["content"] = content
                doc["embedding"] = await self.embedding_model.encode(content)
                if metadata:
                    doc["metadata"].update(metadata)
                doc["updated_at"] = datetime.now().isoformat()
                return True
        
        return False
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from the vector index"""
        for i, doc in enumerate(self.documents):
            if doc.get("id") == document_id:
                del self.documents[i]
                return True
        return False
    
    async def get_document_count(self) -> int:
        """Get total number of documents in the index"""
        return len(self.documents)
    
    async def get_similar_documents(
        self,
        document_id: str,
        top_k: int = 5,
        threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Find documents similar to a given document"""
        if not self.initialized:
            await self.initialize()
        
        # Find the source document
        source_doc = None
        for doc in self.documents:
            if doc.get("id") == document_id:
                source_doc = doc
                break
        
        if not source_doc:
            return []
        
        # Mock similar documents
        similar_docs = []
        for i in range(min(top_k, 3)):
            score = 0.9 - (i * 0.1)
            if score >= threshold:
                similar_docs.append({
                    "id": f"similar_{i}",
                    "title": f"Similar Document {i}",
                    "content": f"Content similar to {source_doc.get('title', 'Unknown')}",
                    "score": score,
                    "metadata": {
                        "source": "confluence",
                        "similarity_type": "content"
                    }
                })
        
        return similar_docs
    
    async def cluster_documents(
        self,
        num_clusters: int = 10,
        min_cluster_size: int = 2
    ) -> Dict[str, Any]:
        """Cluster documents based on their embeddings"""
        if not self.initialized:
            await self.initialize()
        
        # Mock clustering results
        clusters = {}
        for i in range(num_clusters):
            cluster_docs = []
            for j in range(min_cluster_size + i):
                if len(self.documents) > j:
                    cluster_docs.append({
                        "id": f"cluster_{i}_doc_{j}",
                        "title": f"Cluster {i} Document {j}",
                        "distance_to_centroid": 0.1 + (j * 0.05)
                    })
            
            if cluster_docs:
                clusters[f"cluster_{i}"] = {
                    "documents": cluster_docs,
                    "centroid_topic": f"Topic {i}",
                    "size": len(cluster_docs)
                }
        
        return {
            "clusters": clusters,
            "total_clusters": len(clusters),
            "total_documents_clustered": sum(c["size"] for c in clusters.values())
        }
    
    async def get_search_statistics(self) -> Dict[str, Any]:
        """Get search service statistics"""
        return {
            "total_documents": len(self.documents),
            "embedding_cache_size": len(self.embeddings_cache),
            "initialized": self.initialized,
            "service_type": "vector_search",
            "supported_operations": [
                "similarity_search",
                "add_documents", 
                "update_document",
                "delete_document",
                "cluster_documents",
                "get_similar_documents"
            ]
        }


class MockEmbeddingModel:
    """Mock embedding model for testing"""
    
    def __init__(self):
        self.dimension = 384  # Common embedding dimension
    
    async def encode(self, text: str) -> List[float]:
        """Generate mock embedding for text"""
        # Simple hash-based mock embedding
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Convert to float values between -1 and 1
        embedding = []
        for i in range(0, min(len(hash_hex), self.dimension // 16)):
            chunk = hash_hex[i:i+2]
            value = int(chunk, 16) / 255.0 * 2 - 1  # Normalize to [-1, 1]
            embedding.append(value)
        
        # Pad to desired dimension
        while len(embedding) < self.dimension:
            embedding.append(0.0)
        
        return embedding[:self.dimension]


# Global service instance
_vector_search_service = None


async def get_vector_search_service() -> VectorSearchService:
    """Get vector search service instance"""
    global _vector_search_service
    if _vector_search_service is None:
        _vector_search_service = VectorSearchService()
        await _vector_search_service.initialize()
    return _vector_search_service


# Convenience functions
async def search_similar(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """Simple similarity search function"""
    service = await get_vector_search_service()
    return await service.similarity_search(query, top_k)


async def add_document(content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Add single document to vector index"""
    service = await get_vector_search_service()
    doc = {
        "id": f"doc_{int(time.time())}",
        "content": content,
        "metadata": metadata or {},
        "created_at": datetime.now().isoformat()
    }
    result = await service.add_documents([doc])
    return result["added"] > 0
