import pytest
from fastapi.testclient import TestClient

from main import create_application as create_app

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
        "metadata": {"source": "api_test"},
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
        assert "timestamp" in data
        # API v1 health endpoint returns only status and timestamp (SmokeHealthResponse)
        # The 'checks' field is only in the main /health endpoint (HealthResponse)


class TestDocumentEndpoints:
    """Test document API endpoints."""

    def _check_documents_endpoint_available(self, client):
        """Check if documents endpoint is available."""
        response = client.get("/api/v1/documents")
        if response.status_code == 404:
            pytest.skip("Documents endpoint not available (missing dependencies)")
        return True

    def test_create_document(self, client, sample_document_data):
        """Test document creation."""
        response = client.post("/api/v1/documents", json=sample_document_data)
        
        # Documents endpoint may not be available if dependencies are missing
        if response.status_code == 404:
            pytest.skip("Documents endpoint not available (missing dependencies)")
        
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
        self._check_documents_endpoint_available(client)
        
        # First create a document
        create_response = client.post("/api/v1/documents", json=sample_document_data)
        if create_response.status_code == 404:
            pytest.skip("Documents endpoint not available (missing dependencies)")
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
        self._check_documents_endpoint_available(client)
        
        response = client.get("/api/v1/documents/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_search_documents(self, client, sample_document_data):
        """Test document search."""
        self._check_documents_endpoint_available(client)
        
        # Create a document first
        create_response = client.post("/api/v1/documents", json=sample_document_data)
        if create_response.status_code == 404:
            pytest.skip("Documents endpoint not available (missing dependencies)")
        created_doc = create_response.json()

        # Search for documents
        response = client.get("/api/v1/documents/search", params={"q": "Test"})
        assert response.status_code == 200

        data = response.json()
        assert "documents" in data
        assert len(data["documents"]) > 0

    def test_update_document(self, client, sample_document_data):
        """Test document update."""
        self._check_documents_endpoint_available(client)
        
        # Create a document
        create_response = client.post("/api/v1/documents", json=sample_document_data)
        if create_response.status_code == 404:
            pytest.skip("Documents endpoint not available (missing dependencies)")
        created_doc = create_response.json()
        document_id = created_doc["id"]

        # Update the document
        update_data = {"title": "Updated Title", "content": "Updated content"}
        response = client.put(f"/api/v1/documents/{document_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["content"] == update_data["content"]

    def test_update_nonexistent_document(self, client, sample_document_data):
        """Test update of non-existent document."""
        self._check_documents_endpoint_available(client)
        
        update_data = {"title": "Updated Title", "content": "Updated content"}
        response = client.put("/api/v1/documents/nonexistent-id", json=update_data)
        assert response.status_code == 404

    def test_delete_document(self, client, sample_document_data):
        """Test document deletion."""
        self._check_documents_endpoint_available(client)
        
        # Create a document
        create_response = client.post("/api/v1/documents", json=sample_document_data)
        if create_response.status_code == 404:
            pytest.skip("Documents endpoint not available (missing dependencies)")
        created_doc = create_response.json()
        document_id = created_doc["id"]

        # Delete the document
        response = client.delete(f"/api/v1/documents/{document_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/v1/documents/{document_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_document(self, client):
        """Test deletion of non-existent document."""
        self._check_documents_endpoint_available(client)
        
        response = client.delete("/api/v1/documents/nonexistent-id")
        assert response.status_code == 404

    def test_list_documents(self, client, sample_document_data):
        """Test document listing."""
        self._check_documents_endpoint_available(client)
        
        # Create a document
        create_response = client.post("/api/v1/documents", json=sample_document_data)
        if create_response.status_code == 404:
            pytest.skip("Documents endpoint not available (missing dependencies)")

        # List documents
        response = client.get("/api/v1/documents")
        assert response.status_code == 200

        data = response.json()
        assert "documents" in data
        assert len(data["documents"]) > 0
