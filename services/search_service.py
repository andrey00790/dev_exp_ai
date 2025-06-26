"""
Search Service
Сервис для семантического поиска
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
from abc import ABC, abstractmethod
from fastapi import UploadFile
from dataclasses import dataclass

# Импортируем backend сервис с полной функциональностью
try:
    from backend.search_service import SearchService as BackendSearchService, get_search_service as get_backend_search_service
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False

@dataclass
class SearchResult:
    """Результат поиска"""
    id: str
    title: str
    content: str
    source_type: str
    source_name: str
    url: str
    score: float
    highlights: List[str]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str

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


class SearchService(SearchServiceInterface):
    """Основной сервис поиска"""
    
    def __init__(self):
        self.backend_service = None
        self.embedding_model = None
        self.db_session = None
        self.initialized = False
        self.use_backend = BACKEND_AVAILABLE
    
    async def initialize(self):
        """Инициализация сервиса"""
        if self.use_backend:
            try:
                self.backend_service = await get_backend_search_service()
                self.initialized = True
                return
            except Exception as e:
                print(f"Failed to initialize backend service: {e}")
                self.use_backend = False
        
        # Fallback к mock реализации
        self.embedding_model = MockEmbeddingModel()
        self.initialized = True
    
    async def search_documents(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        search_type: str = "semantic",
        limit: int = 10,
        offset: int = 0,
        include_snippets: bool = True,
        filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Поиск документов"""
        
        if not self.initialized:
            await self.initialize()
        
        if self.use_backend and self.backend_service:
            # Используем backend сервис с полной функциональностью
            return await self.backend_service.search_documents(
                query=query,
                sources=sources,
                search_type=search_type,
                limit=limit,
                offset=offset,
                include_snippets=include_snippets,
                filters=filters,
                user_id=user_id
            )
        
        # Fallback mock реализация
        mock_results = [
            {
                "id": f"doc_{i}",
                "title": f"Document {i}: {query}",
                "content": f"This is content for document {i} matching query: {query}",
                "source_type": "confluence",
                "source_name": "main_confluence",
                "url": f"https://example.com/doc_{i}",
                "score": 0.9 - (i * 0.1),
                "highlights": [f"Highlight {i} for {query}"],
                "metadata": {"category": "documentation"},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            for i in range(min(limit, 5))
        ]
        
        return {
            "results": mock_results,
            "total_results": len(mock_results),
            "search_time_ms": 125.5,
            "query": query,
            "search_type": search_type
        }
    
    async def advanced_search(
        self,
        query: str,
        filters: Dict[str, Any],
        search_type: str = "semantic",
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "relevance",
        sort_order: str = "desc",
        include_snippets: bool = True,
        include_metadata: bool = True,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Расширенный поиск с детальными фильтрами"""
        
        if not self.initialized:
            await self.initialize()
        
        if self.use_backend and self.backend_service:
            return await self.backend_service.advanced_search(
                query=query,
                filters=filters,
                search_type=search_type,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_order=sort_order,
                include_snippets=include_snippets,
                include_metadata=include_metadata,
                user_id=user_id
            )
        
        # Fallback mock реализация для расширенного поиска
        results = []
        for i in range(min(limit, 3)):
            results.append({
                "id": f"advanced_doc_{i}",
                "title": f"Advanced Document {i}",
                "content": f"Advanced content for {query}",
                "source": {
                    "type": "confluence",
                    "name": "main_confluence",
                    "id": f"123{i}",
                    "url": f"https://example.com/advanced_{i}"
                },
                "hierarchy": {
                    "space_key": "TECH",
                    "project_key": None
                },
                "categorization": {
                    "document_type": "page",
                    "category": "documentation",
                    "tags": ["api", "documentation"]
                },
                "authorship": {
                    "author": "John Doe",
                    "author_email": "john@example.com"
                },
                "timestamps": {
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                "status": {
                    "quality_score": 0.9,
                    "relevance_score": 0.85
                },
                "score": 0.9 - (i * 0.1),
                "highlights": [f"Advanced highlight {i}"],
                "snippet": f"Advanced snippet for {query}..."
            })
        
        return {
            "results": results,
            "total_results": len(results),
            "search_time_ms": 150.0,
            "query": query,
            "search_type": search_type,
            "facets": {
                "source_types": [{"value": "confluence", "count": 3}],
                "document_types": [{"value": "page", "count": 3}],
                "categories": [{"value": "documentation", "count": 3}],
                "authors": [{"value": "John Doe", "count": 3}]
            }
        }
    
    async def semantic_search(self, query) -> List[Dict[str, Any]]:
        """Семантический поиск"""
        if not self.initialized:
            await self.initialize()
        
        # Используем search_documents для семантического поиска
        result = await self.search_documents(
            query=query, 
            search_type="semantic",
            limit=10
        )
        return result.get("results", [])
    
    async def get_searched_sources(self, query) -> List[str]:
        """Получить источники по которым производился поиск"""
        if not self.initialized:
            await self.initialize()
        
        if self.use_backend and self.backend_service:
            # Получаем статистику источников
            stats = await self.backend_service.get_source_statistics()
            sources = []
            
            # Собираем все доступные источники
            for space in stats.get("confluence_spaces", {}):
                sources.append(f"confluence_{space}")
            
            for project in stats.get("jira_projects", {}):
                sources.append(f"jira_{project}")
            
            for repo in stats.get("gitlab_repositories", {}):
                sources.append(f"gitlab_{repo}")
            
            return sources
        
        # Fallback
        return ["confluence", "jira", "gitlab"]
    
    async def upload_document(self, file, file_type, request) -> Dict[str, Any]:
        """Загрузка документа"""
        if not self.initialized:
            await self.initialize()
        
        # Простая реализация загрузки документа
        return {
            "document_id": "uploaded_doc_123",
            "title": getattr(request, 'title', getattr(file, 'filename', 'unknown')),
            "status": "uploaded",
            "message": "Document uploaded successfully"
        }
    
    async def get_search_suggestions(
        self,
        query: str,
        limit: int = 5,
        sources: Optional[List[str]] = None
    ) -> List[str]:
        """Получение предложений для поиска"""
        if not self.initialized:
            await self.initialize()
        
        if self.use_backend and self.backend_service:
            return await self.backend_service.get_search_suggestions(
                query=query,
                sources=sources,
                limit=limit
            )
        
        # Fallback
        return [
            f"{query} suggestion {i}"
            for i in range(1, limit + 1)
        ]
    
    async def get_source_statistics(self) -> Dict[str, Any]:
        """Получение статистики по источникам"""
        if not self.initialized:
            await self.initialize()
        
        if self.use_backend and self.backend_service:
            return await self.backend_service.get_source_statistics()
        
        # Fallback mock статистика
        return {
            "confluence_spaces": {"TECH": 15, "DOCS": 8},
            "jira_projects": {"PROJ": 25, "DEV": 12},
            "gitlab_repositories": {"api-service": 5, "frontend": 3},
            "content_types": {"page": 30, "issue": 37, "file": 8}
        }


class MockEmbeddingModel:
    """Mock модель для эмбеддингов"""
    
    async def encode(self, texts: List[str]) -> List[List[float]]:
        """Генерация mock эмбеддингов"""
        import random
        return [[random.random() for _ in range(384)] for _ in texts]


# Dependency для FastAPI
_search_service = None

async def get_search_service() -> SearchService:
    """Получение экземпляра сервиса поиска"""
    global _search_service
    
    if _search_service is None:
        _search_service = SearchService()
        await _search_service.initialize()
    
    return _search_service
