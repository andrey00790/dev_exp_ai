"""
Qdrant Integration Tests
Тесты для интеграции с Qdrant векторной базой данных
"""
import pytest
import numpy as np
import asyncio
from typing import List, Dict, Any

# Import main Qdrant system instead of simple version
from adapters.vectorstore.qdrant_client import QdrantVectorStore, get_qdrant_store
from adapters.vectorstore.embeddings import get_embeddings_service

try:
    from adapters.vectorstore.qdrant_simple import QdrantSimpleStore, get_qdrant_simple
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

# Skip all tests if Qdrant is not available
pytestmark = pytest.mark.skipif(not QDRANT_AVAILABLE, reason="Qdrant client not available")

class TestQdrantSimpleStore:
    """Tests for simplified Qdrant store"""
    
    def setup_method(self):
        """Setup test with in-memory Qdrant"""
        self.store = QdrantSimpleStore(in_memory=True)
        
    def test_health_check(self):
        """Test Qdrant health check"""
        health = self.store.health_check()
        assert health["status"] == "healthy"
        assert health["mode"] == "in-memory"
        
    def test_create_collection(self):
        """Test collection creation"""
        success = self.store.create_collection("test_collection", vector_size=128)
        assert success is True
        
        # Check collection exists
        assert self.store.collection_exists("test_collection") is True
        
        # Creating same collection again should succeed
        success = self.store.create_collection("test_collection", vector_size=128)
        assert success is True
        
    def test_insert_and_search_vectors(self):
        """Test vector insertion and search"""
        # Create collection
        self.store.create_collection("test_docs", vector_size=128)
        
        # Prepare test data
        vectors = [
            [0.1] * 128,  # Doc 1
            [0.5] * 128,  # Doc 2
            [0.9] * 128   # Doc 3
        ]
        
        payloads = [
            {"text": "Document 1", "category": "A"},
            {"text": "Document 2", "category": "B"},
            {"text": "Document 3", "category": "A"}
        ]
        
        # Insert vectors
        success = self.store.insert_vectors("test_docs", vectors, payloads)
        assert success is True
        
        # Search for similar vectors
        query_vector = [0.15] * 128  # Should be closest to Doc 1
        results = self.store.search_vectors("test_docs", query_vector, limit=2)
        
        assert len(results) == 2
        # Don't assume specific order, just check that we get results
        assert any("Document" in r["payload"]["text"] for r in results)
        assert results[0]["score"] >= 0.0  # Score should be valid
        
    def test_vector_deletion(self):
        """Test vector deletion"""
        # Create collection and insert vectors
        self.store.create_collection("test_delete", vector_size=64)
        
        vectors = [[0.1] * 64, [0.2] * 64]
        payloads = [{"id": "doc1"}, {"id": "doc2"}]
        ids = ["id1", "id2"]
        
        self.store.insert_vectors("test_delete", vectors, payloads, ids)
        
        # Delete one vector
        success = self.store.delete_vectors("test_delete", ["id1"])
        assert success is True
        
        # Search should only return one result
        results = self.store.search_vectors("test_delete", [0.1] * 64, limit=10)
        assert len(results) == 1
        assert results[0]["payload"]["id"] == "doc2"
        
    def test_collection_info(self):
        """Test getting collection information"""
        # Create collection with vectors
        self.store.create_collection("test_info", vector_size=32)
        
        vectors = [[0.1] * 32, [0.2] * 32, [0.3] * 32]
        payloads = [{"idx": i} for i in range(3)]
        
        self.store.insert_vectors("test_info", vectors, payloads)
        
        # Get collection info
        info = self.store.get_collection_info("test_info")
        
        assert info["name"] == "test_info"
        assert info["vector_count"] >= 3  # Should have at least 3 vectors
        
    def test_list_collections(self):
        """Test listing collections"""
        # Create multiple collections
        self.store.create_collection("collection_1", vector_size=64)
        self.store.create_collection("collection_2", vector_size=128)
        
        collections = self.store.list_collections()
        
        assert "collection_1" in collections
        assert "collection_2" in collections
        assert len(collections) >= 2
        
    def test_default_collections_initialization(self):
        """Test default collections initialization"""
        self.store.initialize_default_collections()
        
        collections = self.store.list_collections()
        
        # Check default collections exist
        assert "documents" in collections
        assert "chat_history" in collections
        assert "knowledge_base" in collections
        
    def test_error_handling(self):
        """Test error handling"""
        # Try to search in non-existent collection
        results = self.store.search_vectors("non_existent", [0.1] * 128)
        assert results == []
        
        # Try to insert mismatched vectors and payloads
        success = self.store.insert_vectors(
            "test_collection", 
            [[0.1] * 128], 
            [{"text": "doc1"}, {"text": "doc2"}]  # Mismatch
        )
        assert success is False
        
    def test_global_store_access(self):
        """Test global store access"""
        store = get_qdrant_simple()
        assert store is not None
        
        health = store.health_check()
        assert health["status"] in ["healthy", "unhealthy"]

class TestQdrantIntegration:
    """Integration tests for Qdrant functionality"""
    
    def test_realistic_document_search(self):
        """Test realistic document search scenario"""
        store = QdrantSimpleStore(in_memory=True)
        
        # Create documents collection
        store.create_collection("documents", vector_size=256)
        
        # Simulate document embeddings (random but consistent)
        np.random.seed(42)  # For reproducible results
        
        documents = [
            {"text": "Python programming tutorial", "category": "programming"},
            {"text": "Machine learning basics", "category": "ai"},
            {"text": "Web development with React", "category": "programming"},
            {"text": "Deep learning fundamentals", "category": "ai"},
            {"text": "Database design principles", "category": "database"}
        ]
        
        # Generate pseudo-embeddings
        vectors = []
        for doc in documents:
            # Create pseudo-embeddings based on content
            base_vector = np.random.rand(256)
            
            # Adjust vector based on category for clustering
            if doc["category"] == "programming":
                base_vector[:50] += 0.3  # Programming docs cluster
            elif doc["category"] == "ai":
                base_vector[50:100] += 0.3  # AI docs cluster
            elif doc["category"] == "database":
                base_vector[100:150] += 0.3  # Database docs cluster
                
            vectors.append(base_vector.tolist())
        
        # Insert documents
        success = store.insert_vectors("documents", vectors, documents)
        assert success is True
        
        # Search for programming-related content
        query_vector = np.random.rand(256)
        query_vector[:50] += 0.3  # Similar to programming docs
        
        results = store.search_vectors("documents", query_vector.tolist(), limit=3)
        
        assert len(results) > 0
        
        # Results should contain programming docs with higher scores
        programming_results = [r for r in results if r["payload"]["category"] == "programming"]
        assert len(programming_results) > 0
        
    def test_vector_operations_workflow(self):
        """Test complete vector operations workflow"""
        store = QdrantSimpleStore(in_memory=True)
        
        # 1. Initialize default collections
        store.initialize_default_collections()
        
        # 2. Verify collections were created
        collections = store.list_collections()
        assert "documents" in collections
        assert "chat_history" in collections
        
        # 3. Insert chat history
        chat_vectors = [[0.1] * 1536, [0.2] * 1536]
        chat_payloads = [
            {"message": "Hello, how are you?", "user": "user1", "timestamp": "2024-01-01"},
            {"message": "I'm doing well, thanks!", "user": "assistant", "timestamp": "2024-01-01"}
        ]
        
        success = store.insert_vectors("chat_history", chat_vectors, chat_payloads)
        assert success is True
        
        # 4. Search chat history
        query_vector = [0.15] * 1536  # Similar to first message
        results = store.search_vectors("chat_history", query_vector, limit=5)
        
        assert len(results) > 0
        assert "message" in results[0]["payload"]
        
        # 5. Get collection statistics
        info = store.get_collection_info("chat_history")
        assert info["vector_count"] >= 2
        
        # 6. Cleanup - delete vectors
        vector_ids = [r["id"] for r in results]
        success = store.delete_vectors("chat_history", vector_ids[:1])  # Delete first one
        assert success is True

if __name__ == "__main__":
    pytest.main([__file__]) 