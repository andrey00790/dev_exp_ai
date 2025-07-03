"""
Vectorstore module - Compatibility wrapper for adapters.vectorstore
"""

# Re-export everything from adapters.vectorstore for backward compatibility
from adapters.vectorstore.collections import CollectionManager, CollectionType, DocumentMetadata
from adapters.vectorstore.embeddings import OpenAIEmbeddings, EmbeddingResult, MockEmbeddingModel
from adapters.vectorstore.qdrant_client import QdrantClient

# Create aliases for backward compatibility
EmbeddingService = OpenAIEmbeddings

__all__ = [
    # From collections
    "CollectionManager", 
    "CollectionType",
    "DocumentMetadata",
    # From embeddings  
    "OpenAIEmbeddings",
    "EmbeddingResult", 
    "MockEmbeddingModel",
    "EmbeddingService",  # Alias
    # From qdrant_client
    "QdrantClient"
] 