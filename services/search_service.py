from abc import ABC, abstractmethod
from typing import List, Optional
from fastapi import UploadFile

from models.search import (
    SemanticSearchQuery, SemanticSearchResult, UploadFileRequest, 
    UploadFileResponse, FileType
)


class SearchServiceInterface(ABC):
    """Interface for semantic search service."""
    
    @abstractmethod
    async def semantic_search(self, query: SemanticSearchQuery) -> List[SemanticSearchResult]:
        """Выполняет семантический поиск."""
        pass
    
    @abstractmethod
    async def get_searched_sources(self, query: SemanticSearchQuery) -> List[str]:
        """Возвращает список источников, по которым производился поиск."""
        pass
    
    @abstractmethod
    async def upload_document(
        self, 
        file: UploadFile, 
        file_type: FileType, 
        request: UploadFileRequest
    ) -> UploadFileResponse:
        """Загружает и индексирует документ."""
        pass


class MockSearchService(SearchServiceInterface):
    """Mock implementation for development."""
    
    async def semantic_search(self, query: SemanticSearchQuery) -> List[SemanticSearchResult]:
        """Mock семантический поиск."""
        from models.search import SourceType
        
        # Возвращаем mock результаты
        return [
            SemanticSearchResult(
                document_id="doc_1",
                title="Архитектурный гайд по микросервисам",
                snippet=f"Найден релевантный контент по запросу '{query.query}': описание принципов проектирования микросервисной архитектуры...",
                relevance_score=0.95,
                source_type=SourceType.CONFLUENCE,
                source_name="Confluence - Architecture",
                url="https://confluence.company.com/pages/123",
                author="Senior Architect",
                highlights=[f"Ключевые слова: {query.query}", "микросервисы", "архитектура"]
            ),
            SemanticSearchResult(
                document_id="doc_2", 
                title="RFC: Дизайн API Gateway",
                snippet="Документ описывает подходы к проектированию API Gateway для обработки запросов к микросервисам.",
                relevance_score=0.87,
                source_type=SourceType.GITLAB,
                source_name="GitLab - RFC Repository", 
                url="https://gitlab.company.com/rfcs/api-gateway",
                author="Platform Team",
                highlights=["API Gateway", "маршрутизация", "нагрузка"]
            )
        ]
    
    async def get_searched_sources(self, query: SemanticSearchQuery) -> List[str]:
        """Возвращает mock список источников."""
        return ["confluence-main", "gitlab-rfcs", "uploaded-docs"]
    
    async def upload_document(
        self, 
        file: UploadFile, 
        file_type: FileType, 
        request: UploadFileRequest
    ) -> UploadFileResponse:
        """Mock загрузка документа."""
        import uuid
        
        # Симулируем обработку файла
        file_content = await file.read()
        
        return UploadFileResponse(
            document_id=str(uuid.uuid4()),
            title=request.title,
            file_type=file_type,
            file_size=len(file_content),
            processing_status="completed",
            message="Документ успешно загружен и проиндексирован"
        )


# Global instance
_search_service_instance = None

def get_search_service() -> SearchServiceInterface:
    """Dependency injection для search service."""
    global _search_service_instance
    if _search_service_instance is None:
        _search_service_instance = MockSearchService()
    return _search_service_instance 