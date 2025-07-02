import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from models.base import Document, DocumentType, SearchQuery, SearchResult


class DocumentServiceInterface(ABC):
    """Interface for document services."""

    @abstractmethod
    async def create_document(self, document: Document) -> Document:
        """Create a new document."""
        pass

    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        pass

    @abstractmethod
    async def search_documents(self, query: SearchQuery) -> List[SearchResult]:
        """Search documents."""
        pass

    @abstractmethod
    async def update_document(
        self, document_id: str, document: Document
    ) -> Optional[Document]:
        """Update document."""
        pass

    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """Delete document."""
        pass


class InMemoryDocumentService(DocumentServiceInterface):
    """In-memory implementation for development and testing."""

    def __init__(self):
        self._documents: dict[str, Document] = {}

    async def create_document(self, document: Document) -> Document:
        """Create a new document."""
        if not document.id:
            document.id = str(uuid.uuid4())

        document.created_at = datetime.now()
        document.updated_at = datetime.now()

        self._documents[document.id] = document
        return document

    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        return self._documents.get(document_id)

    async def search_documents(self, query: SearchQuery) -> List[SearchResult]:
        """Search documents using simple text matching."""
        results = []
        search_term = query.query.lower()

        for doc in self._documents.values():
            score = 0.0
            highlights = []

            # Simple scoring based on title and content matches
            if search_term in doc.title.lower():
                score += 0.5
                highlights.append(f"Title: {doc.title}")

            if search_term in doc.content.lower():
                score += 0.3
                # Extract snippet with search term
                content_lower = doc.content.lower()
                pos = content_lower.find(search_term)
                if pos >= 0:
                    start = max(0, pos - 50)
                    end = min(len(doc.content), pos + 50)
                    snippet = doc.content[start:end]
                    highlights.append(f"...{snippet}...")

            # Filter by document type if specified
            if "doc_type" in query.filters:
                if doc.doc_type != query.filters["doc_type"]:
                    continue

            if score > 0:
                results.append(
                    SearchResult(
                        document=doc, score=min(score, 1.0), highlights=highlights
                    )
                )

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)

        # Apply limit
        return results[: query.limit]

    async def update_document(
        self, document_id: str, document: Document
    ) -> Optional[Document]:
        """Update document."""
        if document_id not in self._documents:
            return None

        document.id = document_id
        document.updated_at = datetime.now()
        if not document.created_at:
            document.created_at = self._documents[document_id].created_at

        self._documents[document_id] = document
        return document

    async def delete_document(self, document_id: str) -> bool:
        """Delete document."""
        if document_id in self._documents:
            del self._documents[document_id]
            return True
        return False
