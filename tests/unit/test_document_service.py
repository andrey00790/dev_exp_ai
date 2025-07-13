from datetime import datetime

import pytest

from domain.integration.document_service import InMemoryDocumentService
from models.base import Document, DocumentType, SearchQuery


@pytest.fixture
def document_service():
    """Fixture for document service."""
    return InMemoryDocumentService()


@pytest.fixture
def sample_document():
    """Fixture for sample document."""
    return Document(
        title="Test Document",
        content="This is a test document for unit testing.",
        doc_type=DocumentType.SRS,
        tags=["test", "unit"],
        metadata={"author": "test_user"},
    )


class TestInMemoryDocumentService:
    """Test cases for InMemoryDocumentService."""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_create_document(self, document_service, sample_document):
        """Test document creation."""
        created_doc = await document_service.create_document(sample_document)

        assert created_doc.id is not None
        assert created_doc.title == sample_document.title
        assert created_doc.content == sample_document.content
        assert created_doc.doc_type == sample_document.doc_type
        assert created_doc.created_at is not None
        assert created_doc.updated_at is not None

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_document(self, document_service, sample_document):
        """Test document retrieval."""
        created_doc = await document_service.create_document(sample_document)
        retrieved_doc = await document_service.get_document(created_doc.id)

        assert retrieved_doc is not None
        assert retrieved_doc.id == created_doc.id
        assert retrieved_doc.title == created_doc.title

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self, document_service):
        """Test retrieval of non-existent document."""
        retrieved_doc = await document_service.get_document("nonexistent-id")
        assert retrieved_doc is None

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_search_documents(self, document_service, sample_document):
        """Test document search."""
        await document_service.create_document(sample_document)

        # Create another document
        another_doc = Document(
            title="Another Document",
            content="This is another document.",
            doc_type=DocumentType.NFR,
            tags=["another"],
        )
        await document_service.create_document(another_doc)

        # Search by title
        query = SearchQuery(query="test", limit=10)
        results = await document_service.search_documents(query)

        assert len(results) == 1
        assert results[0].document.title == sample_document.title
        assert results[0].score > 0
        assert len(results[0].highlights) > 0

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_search_with_filters(self, document_service, sample_document):
        """Test document search with filters."""
        await document_service.create_document(sample_document)

        # Search with document type filter
        query = SearchQuery(query="document", filters={"doc_type": DocumentType.SRS})
        results = await document_service.search_documents(query)

        assert len(results) == 1
        assert results[0].document.doc_type == DocumentType.SRS

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_update_document(self, document_service, sample_document):
        """Test document update."""
        created_doc = await document_service.create_document(sample_document)

        # Update the document
        updated_content = "Updated content"
        created_doc.content = updated_content

        updated_doc = await document_service.update_document(
            created_doc.id, created_doc
        )

        assert updated_doc is not None
        assert updated_doc.content == updated_content
        assert updated_doc.updated_at > updated_doc.created_at

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_update_nonexistent_document(self, document_service, sample_document):
        """Test update of non-existent document."""
        updated_doc = await document_service.update_document(
            "nonexistent-id", sample_document
        )
        assert updated_doc is None

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_delete_document(self, document_service, sample_document):
        """Test document deletion."""
        created_doc = await document_service.create_document(sample_document)

        # Delete the document
        success = await document_service.delete_document(created_doc.id)
        assert success is True

        # Verify it's deleted
        retrieved_doc = await document_service.get_document(created_doc.id)
        assert retrieved_doc is None

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self, document_service):
        """Test deletion of non-existent document."""
        success = await document_service.delete_document("nonexistent-id")
        assert success is False
