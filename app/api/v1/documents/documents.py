from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from domain.integration.document_service import (DocumentServiceInterface,
                                                 InMemoryDocumentService)
from models.base import BaseResponse, Document, SearchQuery, SearchResponse

router = APIRouter()

# Global instance for consistency in tests
_document_service_instance = None


# Dependency for document service
def get_document_service() -> DocumentServiceInterface:
    """Get document service instance."""
    global _document_service_instance
    if _document_service_instance is None:
        _document_service_instance = InMemoryDocumentService()
    return _document_service_instance


@router.post(
    "/documents",
    response_model=Document,
    status_code=status.HTTP_201_CREATED,
    summary="Create Document",
    description="Create a new document",
)
async def create_document(
    document: Document,
    service: DocumentServiceInterface = Depends(get_document_service),
) -> Document:
    """Create a new document."""
    try:
        return await service.create_document(document)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}",
        )


@router.get(
    "/documents/{document_id}",
    response_model=Document,
    summary="Get Document",
    description="Get document by ID",
)
async def get_document(
    document_id: str, service: DocumentServiceInterface = Depends(get_document_service)
) -> Document:
    """Get document by ID."""
    document = await service.get_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found",
        )
    return document


@router.post(
    "/documents/search",
    response_model=SearchResponse,
    summary="Search Documents",
    description="Search documents by query",
)
async def search_documents(
    query: SearchQuery,
    service: DocumentServiceInterface = Depends(get_document_service),
) -> SearchResponse:
    """Search documents."""
    try:
        results = await service.search_documents(query)
        return SearchResponse(results=results, total=len(results), query=query.query)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.put(
    "/documents/{document_id}",
    response_model=Document,
    summary="Update Document",
    description="Update document by ID",
)
async def update_document(
    document_id: str,
    document: Document,
    service: DocumentServiceInterface = Depends(get_document_service),
) -> Document:
    """Update document."""
    updated_document = await service.update_document(document_id, document)
    if not updated_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found",
        )
    return updated_document


@router.delete(
    "/documents/{document_id}",
    response_model=BaseResponse,
    summary="Delete Document",
    description="Delete document by ID",
)
async def delete_document(
    document_id: str, service: DocumentServiceInterface = Depends(get_document_service)
) -> BaseResponse:
    """Delete document."""
    success = await service.delete_document(document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found",
        )
    return BaseResponse(message=f"Document {document_id} deleted successfully")


@router.get(
    "/documents",
    response_model=List[Document],
    summary="List Documents",
    description="Get all documents (for development)",
)
async def list_documents(
    service: DocumentServiceInterface = Depends(get_document_service),
) -> List[Document]:
    """List all documents (development endpoint)."""
    # This is a simple implementation for development
    # In production, this should be paginated
    if hasattr(service, "_documents"):
        return list(service._documents.values())
    return []
