"""
Integration Domain - Data sources, search, and document management.
"""

# Integration exports
from .data_source_service import DataSourceService
from .document_service import DocumentServiceInterface as DocumentService
from .enhanced_vector_search_service import VectorSearchService

__all__ = ["DataSourceService", "VectorSearchService", "DocumentService"]
