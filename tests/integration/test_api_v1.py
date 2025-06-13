import pytest
from fastapi.testclient import TestClient
from app.main import create_app

pytestmark = pytest.mark.integration
from models.base import DocumentType


@pytest.fixture
def client():
    """Test client fixture."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "title": "Test API Document",
        "content": "This is a test document for API testing.",
        "doc_type": "srs",
        "tags": ["test", "api"],
        "metadata": {"source": "api_test"}
    }


class TestHealthEndpoints:
    """Test health endpoints."""
    
    def test_health_endpoint(self, client):
        """Test basic health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "uptime" in data
        assert "environment" in data
    
    def test_health_v1_endpoint(self, client):
        """Test API v1 health endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "checks" in data
        assert data["checks"]["api"] == "healthy"


class TestDocumentEndpoints:
    """Test document API endpoints."""
    
    def test_create_document(self, client, sample_document_data):
        """Test document creation."""
        response = client.post("/api/v1/documents", json=sample_document_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["title"] == sample_document_data["title"]
        assert data["content"] == sample_document_data["content"]
        assert data["doc_type"] == sample_document_data["doc_type"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_get_document(self, client, sample_document_data):
        """Test document retrieval."""
        # First create a document
        create_response = client.post("/api/v1/documents", json=sample_document_data)
        created_doc = create_response.json()
        document_id = created_doc["id"]
        
        # Then retrieve it
        response = client.get(f"/api/v1/documents/{document_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == document_id
        assert data["title"] == sample_document_data["title"]
    
    def test_get_nonexistent_document(self, client):
        """Test retrieval of non-existent document."""
        response = client.get("/api/v1/documents/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_search_documents(self, client, sample_document_data):
        """Test document search."""
        # Create a document first
        client.post("/api/v1/documents", json=sample_document_data)
        
        # Search for it
        search_query = {
            "query": "test",
            "limit": 10
        }
        response = client.post("/api/v1/documents/search", json=search_query)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["query"] == search_query["query"]
        assert data["total"] >= 1
        assert len(data["results"]) >= 1
        assert data["results"][0]["score"] > 0
    
    def test_update_document(self, client, sample_document_data):
        """Test document update."""
        # Create a document first
        create_response = client.post("/api/v1/documents", json=sample_document_data)
        created_doc = create_response.json()
        document_id = created_doc["id"]
        
        # Update it
        updated_data = sample_document_data.copy()
        updated_data["title"] = "Updated Test Document"
        updated_data["content"] = "Updated content for testing."
        
        response = client.put(f"/api/v1/documents/{document_id}", json=updated_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == updated_data["title"]
        assert data["content"] == updated_data["content"]
    
    def test_update_nonexistent_document(self, client, sample_document_data):
        """Test update of non-existent document."""
        response = client.put("/api/v1/documents/nonexistent-id", json=sample_document_data)
        assert response.status_code == 404
    
    def test_delete_document(self, client, sample_document_data):
        """Test document deletion."""
        # Create a document first
        create_response = client.post("/api/v1/documents", json=sample_document_data)
        created_doc = create_response.json()
        document_id = created_doc["id"]
        
        # Delete it
        response = client.delete(f"/api/v1/documents/{document_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"]
        
        # Verify it's deleted
        get_response = client.get(f"/api/v1/documents/{document_id}")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_document(self, client):
        """Test deletion of non-existent document."""
        response = client.delete("/api/v1/documents/nonexistent-id")
        assert response.status_code == 404
    
    def test_list_documents(self, client, sample_document_data):
        """Test document listing."""
        # Create a document first
        client.post("/api/v1/documents", json=sample_document_data)
        
        # List documents
        response = client.get("/api/v1/documents")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1 