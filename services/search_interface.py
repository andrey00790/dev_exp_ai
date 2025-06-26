"""
Search Service Interface
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from fastapi import UploadFile


class SearchServiceInterface(ABC):
    """Interface for search service"""
    
    @abstractmethod
    async def semantic_search(self, query) -> List[Dict[str, Any]]:
        """Perform semantic search"""
        pass
    
    @abstractmethod
    async def get_searched_sources(self, query) -> List[str]:
        """Get sources that were searched"""
        pass
    
    @abstractmethod
    async def upload_document(self, file: UploadFile, file_type, request) -> Dict[str, Any]:
        """Upload and process document"""
        pass
    
    @abstractmethod
    async def search_documents(self, **kwargs) -> Dict[str, Any]:
        """Search documents with parameters"""
        pass 