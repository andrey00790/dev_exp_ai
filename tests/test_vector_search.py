"""
Tests for vector search functionality.
Tests Qdrant integration, embeddings, and search API endpoints.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

# Test imports
from vectorstore.qdrant_client import QdrantVectorStore, get_qdrant_client
from vectorstore.embeddings import OpenAIEmbeddings, get_embeddings_service, DocumentChunker
from vectorstore.collections import CollectionManager, get_collection_manager, DocumentMetadata, CollectionType
from services.vector_search_service import VectorSearchService, SearchRequest, get_vector_search_service

# API test imports
from fastapi.testclient import TestClient
from app.main import app

# Test fixtures and utilities

@pytest.fixture
def mock_embeddings():
    """Mock embeddings service for testing."""
    with patch('vectorstore.embeddings.OpenAIEmbeddings') as mock:
        mock_instance = Mock()
        mock_instance.embed_text = AsyncMock()
        mock_instance.embed_texts = AsyncMock()
        mock_instance.count_tokens.return_value = 100
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_qdrant():
    """Mock Qdrant client for testing."""
    with patch('vectorstore.qdrant_client.QdrantVectorStore') as mock:
        mock_instance = Mock()
        mock_instance.health_check.return_value = {"status": "healthy", "connected": True}
        mock_instance.collection_exists.return_value = True
        mock_instance.create_collection.return_value = True
        mock_instance.upsert_vectors.return_value = True
        mock_instance.search_vectors.return_value = []
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        "doc_id": "test_doc_1",
        "title": "Test Document",
        "text": "This is a test document with some content for semantic search testing.",
        "source": "test_source",
        "author": "Test Author",
        "tags": ["test", "document"]
    }

@pytest.fixture
def test_client():
    """Test client for API testing."""
    return TestClient(app)

# Unit Tests

class TestQdrantClient:
    """Test Qdrant vector store client."""
    
    def test_qdrant_initialization(self):
        """Test Qdrant client initialization."""
        client = QdrantVectorStore(use_memory=True)
        assert client.use_memory is True
        assert client.host == "localhost"
        assert client.port == 6333
    
    def test_health_check_success(self):
        """Test successful health check."""
        client = QdrantVectorStore(use_memory=True)
        health = client.health_check()
        
        assert health["status"] == "healthy"
        assert health["connected"] is True
        assert health["mode"] == "memory"
    
    def test_collection_operations(self):
        """Test collection create/delete operations."""
        client = QdrantVectorStore(use_memory=True)
        
        # Test create collection
        result = client.create_collection("test_collection")
        assert result is True
        
        # Test collection exists
        exists = client.collection_exists("test_collection")
        assert exists is True
        
        # Test delete collection
        result = client.delete_collection("test_collection")
        assert result is True
    
    def test_vector_operations(self):
        """Test vector upsert and search operations."""
        client = QdrantVectorStore(use_memory=True)
        
        # Create collection first
        client.create_collection("test_vectors")
        
        # Test vector upsert
        vectors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        payloads = [{"text": "doc1"}, {"text": "doc2"}]
        ids = ["1", "2"]
        
        result = client.upsert_vectors(
            collection_name="test_vectors",
            vectors=vectors,
            payloads=payloads,
            ids=ids
        )
        
        assert result is True
        
        # Test vector search
        query_vector = [0.1, 0.2, 0.3]
        results = client.search_vectors(
            collection_name="test_vectors",
            query_vector=query_vector,
            limit=5
        )
        
        # Results should be a list (may be empty for in-memory)
        assert isinstance(results, list)

class TestEmbeddings:
    """Test OpenAI embeddings service."""
    
    def test_token_counting(self):
        """Test token counting functionality."""
        embeddings = OpenAIEmbeddings()
        
        text = "This is a test sentence."
        token_count = embeddings.count_tokens(text)
        
        assert isinstance(token_count, int)
        assert token_count > 0
    
    def test_text_splitting(self):
        """Test text splitting by tokens."""
        embeddings = OpenAIEmbeddings()
        
        long_text = "This is a very long text. " * 100
        chunks = embeddings.split_text_by_tokens(long_text, max_tokens=50)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 1
        
        # Each chunk should be under token limit
        for chunk in chunks:
            token_count = embeddings.count_tokens(chunk)
            assert token_count <= 60  # Small buffer for safety
    
    @pytest.mark.asyncio
    async def test_mock_embedding(self):
        """Test mock embedding generation."""
        embeddings = OpenAIEmbeddings()  # No API key, should use mock
        
        text = "Test document for embedding"
        result = await embeddings.embed_text(text)
        
        assert result is not None
        assert result.text == text
        assert len(result.vector) == 1536  # OpenAI ada-002 size
        assert isinstance(result.cost_estimate, float)
        assert result.token_count > 0
    
    @pytest.mark.asyncio
    async def test_batch_embedding(self):
        """Test batch embedding generation."""
        embeddings = OpenAIEmbeddings()
        
        texts = ["First document", "Second document", "Third document"]
        results = await embeddings.embed_texts(texts)
        
        assert len(results) == len(texts)
        
        for i, result in enumerate(results):
            assert result.text == texts[i]
            assert len(result.vector) == 1536

class TestDocumentChunker:
    """Test document chunking functionality."""
    
    def test_chunking_basic(self):
        """Test basic document chunking."""
        chunker = DocumentChunker(chunk_size=50, overlap=10)
        
        text = "This is a test document. " * 10
        metadata = {"doc_id": "test_1", "title": "Test"}
        
        chunks = chunker.chunk_document(text, metadata)
        
        assert len(chunks) > 1
        
        for chunk in chunks:
            assert "text" in chunk
            assert "chunk_id" in chunk
            assert "doc_id" in chunk
            assert chunk["doc_id"] == "test_1"
            assert len(chunk["text"]) <= 60  # Some buffer
    
    def test_chunking_empty_text(self):
        """Test chunking with empty text."""
        chunker = DocumentChunker()
        
        chunks = chunker.chunk_document("", {"doc_id": "empty"})
        assert chunks == []
        
        chunks = chunker.chunk_document("   ", {"doc_id": "whitespace"})
        assert chunks == []
    
    def test_chunking_short_text(self):
        """Test chunking with text shorter than chunk size."""
        chunker = DocumentChunker(chunk_size=1000, overlap=100)
        
        text = "Short text."
        chunks = chunker.chunk_document(text)
        
        assert len(chunks) == 1
        assert chunks[0]["text"] == text

class TestCollectionManager:
    """Test collection management functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self, mock_qdrant, mock_embeddings):
        """Set up mocks for collection manager tests."""
        self.mock_qdrant = mock_qdrant
        self.mock_embeddings = mock_embeddings
    
    @pytest.mark.asyncio
    async def test_collection_initialization(self):
        """Test collection initialization."""
        with patch('vectorstore.collections.get_qdrant_client') as mock_get_client:
            mock_get_client.return_value = self.mock_qdrant
            
            manager = CollectionManager()
            results = await manager.initialize_collections()
            
            assert isinstance(results, dict)
            assert len(results) == len(CollectionType)
    
    @pytest.mark.asyncio
    async def test_document_indexing(self):
        """Test document indexing process."""
        # Mock embedding result
        from vectorstore.embeddings import EmbeddingResult
        mock_embedding = EmbeddingResult(
            text="test text",
            vector=[0.1] * 1536,
            token_count=10,
            cost_estimate=0.001
        )
        self.mock_embeddings.embed_texts.return_value = [mock_embedding]
        
        with patch('vectorstore.collections.get_qdrant_client') as mock_get_client, \
             patch('vectorstore.collections.get_embeddings_service') as mock_get_embeddings:
            
            mock_get_client.return_value = self.mock_qdrant
            mock_get_embeddings.return_value = self.mock_embeddings
            
            manager = CollectionManager()
            
            metadata = DocumentMetadata(
                doc_id="test_doc",
                title="Test Document",
                source="test",
                source_type=CollectionType.DOCUMENTS
            )
            
            result = await manager.index_document(
                text="This is test content for indexing.",
                metadata=metadata
            )
            
            assert result is True
            self.mock_embeddings.embed_texts.assert_called_once()
            self.mock_qdrant.upsert_vectors.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_document_search(self):
        """Test document search functionality."""
        # Mock embedding result
        from vectorstore.embeddings import EmbeddingResult
        mock_embedding = EmbeddingResult(
            text="search query",
            vector=[0.1] * 1536,
            token_count=5,
            cost_estimate=0.001
        )
        self.mock_embeddings.embed_text.return_value = mock_embedding
        
        # Mock search results
        mock_search_results = [
            {
                "id": "test_doc_0",
                "score": 0.85,
                "payload": {
                    "doc_id": "test_doc",
                    "title": "Test Document",
                    "text": "Test content",
                    "source": "test",
                    "source_type": "documents"
                }
            }
        ]
        self.mock_qdrant.search_vectors.return_value = mock_search_results
        
        with patch('vectorstore.collections.get_qdrant_client') as mock_get_client, \
             patch('vectorstore.collections.get_embeddings_service') as mock_get_embeddings:
            
            mock_get_client.return_value = self.mock_qdrant
            mock_get_embeddings.return_value = self.mock_embeddings
            
            manager = CollectionManager()
            
            results = await manager.search_documents(
                query="test search",
                collection_types=[CollectionType.DOCUMENTS],
                limit=10
            )
            
            assert len(results) == 1
            assert results[0]["id"] == "test_doc_0"
            assert results[0]["score"] == 0.85

class TestVectorSearchService:
    """Test vector search service."""
    
    @pytest.fixture(autouse=True)
    def setup_service(self, mock_qdrant, mock_embeddings):
        """Set up search service with mocks."""
        with patch('services.vector_search_service.get_collection_manager') as mock_get_manager, \
             patch('services.vector_search_service.get_embeddings_service') as mock_get_embeddings:
            
            mock_manager = Mock()
            mock_manager.search_documents = AsyncMock()
            mock_manager.index_document = AsyncMock()
            mock_manager.delete_document = AsyncMock()
            mock_manager.get_collection_stats.return_value = {"test": "stats"}
            mock_manager.qdrant.health_check.return_value = {"status": "healthy"}
            
            mock_get_manager.return_value = mock_manager
            mock_get_embeddings.return_value = mock_embeddings
            
            self.service = VectorSearchService()
            self.mock_manager = mock_manager
            self.mock_embeddings = mock_embeddings
    
    @pytest.mark.asyncio
    async def test_search_functionality(self):
        """Test search functionality."""
        # Mock search results
        mock_results = [{
            "id": "doc1",
            "score": 0.9,
            "payload": {
                "doc_id": "doc1",
                "title": "Test Doc",
                "text": "Test content",
                "source": "test",
                "source_type": "documents"
            }
        }]
        self.mock_manager.search_documents.return_value = mock_results
        
        request = SearchRequest(
            query="test query",
            limit=10
        )
        
        results = await self.service.search(request)
        
        assert len(results) == 1
        assert results[0].doc_id == "doc1"
        assert results[0].title == "Test Doc"
        assert results[0].score == 0.9
    
    @pytest.mark.asyncio
    async def test_document_indexing(self):
        """Test document indexing."""
        self.mock_manager.index_document.return_value = True
        
        result = await self.service.index_document(
            text="Test document content",
            doc_id="test_doc",
            title="Test Document",
            source="test_source"
        )
        
        assert result is True
        self.mock_manager.index_document.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_document_deletion(self):
        """Test document deletion."""
        self.mock_manager.delete_document.return_value = True
        
        result = await self.service.delete_document("test_doc")
        
        assert result is True
        self.mock_manager.delete_document.assert_called_once_with(
            doc_id="test_doc",
            collection_type=CollectionType.DOCUMENTS
        )
    
    def test_search_stats(self):
        """Test search statistics."""
        stats = self.service.get_search_stats()
        
        assert "status" in stats
        assert "active_collections" in stats
        assert "qdrant_status" in stats

# Integration Tests

class TestVectorSearchAPI:
    """Test vector search API endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup_api_tests(self):
        """Set up API test environment."""
        # Mock authentication
        with patch('app.security.auth.get_current_user') as mock_auth:
            mock_auth.return_value = {"user_id": "test_user", "username": "test"}
            self.test_client = TestClient(app)
    
    @patch('services.vector_search_service.get_vector_search_service')
    def test_search_endpoint(self, mock_get_service):
        """Test search API endpoint."""
        # Mock service
        mock_service = Mock()
        mock_service.search = AsyncMock()
        mock_service.search.return_value = []
        mock_get_service.return_value = mock_service
        
        response = self.test_client.post(
            "/api/v1/vector-search/search",
            json={
                "query": "test search",
                "limit": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert data["query"] == "test search"
    
    @patch('services.vector_search_service.get_vector_search_service')
    def test_index_endpoint(self, mock_get_service):
        """Test document indexing endpoint."""
        mock_service = Mock()
        mock_service.index_document = AsyncMock()
        mock_service.index_document.return_value = True
        mock_get_service.return_value = mock_service
        
        response = self.test_client.post(
            "/api/v1/vector-search/index",
            json={
                "text": "Test document content",
                "doc_id": "test_doc_1",
                "title": "Test Document",
                "source": "test"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["doc_id"] == "test_doc_1"
    
    @patch('services.vector_search_service.get_vector_search_service')
    def test_delete_endpoint(self, mock_get_service):
        """Test document deletion endpoint."""
        mock_service = Mock()
        mock_service.delete_document = AsyncMock()
        mock_service.delete_document.return_value = True
        mock_get_service.return_value = mock_service
        
        response = self.test_client.delete("/api/v1/vector-search/documents/test_doc")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["doc_id"] == "test_doc"
    
    @patch('services.vector_search_service.get_vector_search_service')
    def test_stats_endpoint(self, mock_get_service):
        """Test statistics endpoint."""
        mock_service = Mock()
        mock_service.get_search_stats.return_value = {
            "status": "healthy",
            "active_collections": 3,
            "total_collections": 6,
            "collections": {},
            "embeddings_service": {"model": "text-embedding-ada-002"},
            "qdrant_status": {"status": "healthy"}
        }
        mock_get_service.return_value = mock_service
        
        response = self.test_client.get("/api/v1/vector-search/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["active_collections"] == 3
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.test_client.get("/api/v1/vector-search/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["service"] == "vector_search"

# Performance Tests

class TestVectorSearchPerformance:
    """Test vector search performance."""
    
    @pytest.mark.asyncio
    async def test_search_response_time(self):
        """Test that search responds within acceptable time."""
        import time
        
        service = VectorSearchService()
        
        # Mock for fast response
        with patch.object(service, 'collection_manager') as mock_manager:
            mock_manager.search_documents = AsyncMock()
            mock_manager.search_documents.return_value = []
            
            start_time = time.time()
            
            request = SearchRequest(query="performance test")
            await service.search(request)
            
            elapsed = time.time() - start_time
            
            # Should respond within 2 seconds as per AGENTS.md requirement
            assert elapsed < 2.0
    
    @pytest.mark.asyncio
    async def test_indexing_performance(self):
        """Test document indexing performance."""
        import time
        
        service = VectorSearchService()
        
        # Mock for performance test
        with patch.object(service, 'collection_manager') as mock_manager:
            mock_manager.index_document = AsyncMock()
            mock_manager.index_document.return_value = True
            
            start_time = time.time()
            
            await service.index_document(
                text="Performance test document content",
                doc_id="perf_test",
                title="Performance Test",
                source="test"
            )
            
            elapsed = time.time() - start_time
            
            # Indexing should be reasonably fast
            assert elapsed < 5.0

# Error Handling Tests

class TestVectorSearchErrors:
    """Test error handling in vector search."""
    
    @pytest.mark.asyncio
    async def test_search_with_invalid_query(self):
        """Test search with invalid query."""
        service = VectorSearchService()
        
        # Empty query
        request = SearchRequest(query="")
        results = await service.search(request)
        
        # Should handle gracefully and return empty results
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_embedding_service_failure(self):
        """Test handling of embedding service failures."""
        service = VectorSearchService()
        
        with patch.object(service, 'embeddings') as mock_embeddings:
            mock_embeddings.embed_text = AsyncMock()
            mock_embeddings.embed_text.return_value = None  # Simulate failure
            
            request = SearchRequest(query="test")
            results = await service.search(request)
            
            # Should handle failure gracefully
            assert isinstance(results, list)
            assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_qdrant_connection_failure(self):
        """Test handling of Qdrant connection failures."""
        service = VectorSearchService()
        
        with patch.object(service, 'collection_manager') as mock_manager:
            mock_manager.search_documents = AsyncMock()
            mock_manager.search_documents.side_effect = Exception("Connection failed")
            
            request = SearchRequest(query="test")
            results = await service.search(request)
            
            # Should handle connection failure gracefully
            assert isinstance(results, list)
            assert len(results) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 