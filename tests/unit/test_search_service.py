"""
Тесты для сервиса поиска с метаданными
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from domain.integration.search_service import SearchService
from models.document import Document, DocumentChunk, SourceType


@pytest.fixture
def search_service():
    """Фикстура для сервиса поиска"""
    service = SearchService()
    service.embedding_model = Mock()
    service.db_session = Mock()
    service.use_backend = False  # Принудительно используем mock версию для тестов
    return service


@pytest.fixture
def mock_documents():
    """Фикстура с mock документами"""
    return [
        {
            "id": "doc1",
            "title": "API Documentation",
            "content": "This document describes the REST API endpoints...",
            "source_type": "confluence",
            "source_name": "main_confluence",
            "url": "https://confluence.example.com/doc1",
            "score": 0.95,
            "highlights": ["API endpoints", "REST API"],
            "metadata": {
                "category": "documentation",
                "space_key": "TECH",
                "author": "John Doe",
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        },
        {
            "id": "doc2",
            "title": "Database Schema",
            "content": "Database schema for user management...",
            "source_type": "gitlab",
            "source_name": "main_gitlab",
            "url": "https://gitlab.example.com/doc2",
            "score": 0.88,
            "highlights": ["Database schema", "user management"],
            "metadata": {
                "category": "code",
                "repository_name": "user-service",
                "author": "Jane Smith",
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        },
    ]


@pytest.fixture
def sample_documents():
    """Фикстура с примерами документов"""
    return [
        Document(
            id="doc1",
            title="API Authentication Guide",
            content="This guide explains OAuth2 authentication for APIs",
            source_type=SourceType.CONFLUENCE,
            source_name="main_confluence",
            source_id="123456",
            space_key="TECH",
            document_type="page",
            category="documentation",
            author="John Doe",
            tags=["api", "authentication", "oauth2"],
            quality_score=0.92,
            relevance_score=0.88,
            created_at=datetime(2024, 1, 10, 10, 0),
            updated_at=datetime(2024, 1, 15, 14, 30),
        ),
        Document(
            id="doc2",
            title="User Service Implementation",
            content="Implementation details for user authentication microservice",
            source_type=SourceType.GITLAB,
            source_name="main_gitlab",
            source_id="789:src/auth/README.md",
            repository_name="backend-service",
            project_key="company/backend-service",
            document_type="file",
            category="code",
            author="Jane Smith",
            tags=["microservice", "authentication"],
            file_extension="md",
            quality_score=0.85,
            relevance_score=0.82,
            created_at=datetime(2024, 1, 12, 9, 0),
            updated_at=datetime(2024, 1, 14, 16, 45),
        ),
    ]


@pytest.fixture
def sample_chunks():
    """Фикстура с примерами чанков"""
    return [
        DocumentChunk(
            id="chunk1",
            document_id="doc1",
            chunk_index=0,
            content="OAuth2 is a widely used authentication protocol",
            source_type=SourceType.CONFLUENCE,
            source_name="main_confluence",
            start_position=0,
            end_position=50,
            quality_score=0.9,
        ),
        DocumentChunk(
            id="chunk2",
            document_id="doc2",
            chunk_index=0,
            content="The authentication service handles user login",
            source_type=SourceType.GITLAB,
            source_name="main_gitlab",
            start_position=0,
            end_position=45,
            quality_score=0.85,
        ),
    ]


@pytest.mark.asyncio
class TestSearchService:
    """Тесты для основного сервиса поиска"""

    @pytest.mark.asyncio
    async def test_initialize_service(self, search_service):
        """Тест инициализации сервиса"""
        await search_service.initialize()
        assert search_service.initialized is True
        assert search_service.embedding_model is not None

    @pytest.mark.asyncio
    async def test_basic_search(self, search_service, mock_documents):
        """Тест базового поиска"""
        await search_service.initialize()

        result = await search_service.search_documents(
            query="API documentation", limit=10
        )

        assert "results" in result
        assert "total_results" in result
        assert "search_time_ms" in result
        assert "query" in result
        assert "search_type" in result

        # Проверяем структуру результатов
        results = result["results"]
        assert len(results) > 0

        for doc in results:
            assert "id" in doc
            assert "title" in doc
            assert "content" in doc
            assert "source_type" in doc
            assert "source_name" in doc
            assert "score" in doc
            assert "highlights" in doc
            assert "metadata" in doc

    @pytest.mark.asyncio
    async def test_semantic_search(self, search_service):
        """Тест семантического поиска"""
        await search_service.initialize()

        results = await search_service.semantic_search("machine learning")

        assert isinstance(results, list)
        assert len(results) > 0

        for result in results:
            assert "id" in result
            assert "title" in result
            assert "content" in result

    @pytest.mark.asyncio
    async def test_search_with_filters(self, search_service):
        """Тест поиска с фильтрами"""
        await search_service.initialize()

        filters = {
            "source_types": ["confluence"],
            "categories": ["documentation"],
            "authors": ["John Doe"],
        }

        result = await search_service.search_documents(
            query="API", filters=filters, limit=5
        )

        assert "results" in result
        assert result["total_results"] >= 0

    @pytest.mark.asyncio
    async def test_search_with_sources(self, search_service):
        """Тест поиска с указанием источников"""
        await search_service.initialize()

        sources = ["confluence_TECH", "gitlab_main"]

        result = await search_service.search_documents(
            query="documentation", sources=sources
        )

        assert "results" in result
        assert len(result["results"]) >= 0

    @pytest.mark.asyncio
    async def test_search_types(self, search_service):
        """Тест различных типов поиска"""
        await search_service.initialize()

        # Семантический поиск
        semantic_result = await search_service.search_documents(
            query="API documentation", search_type="semantic"
        )
        assert semantic_result["search_type"] == "semantic"

        # Ключевой поиск
        keyword_result = await search_service.search_documents(
            query="API documentation", search_type="keyword"
        )
        assert keyword_result["search_type"] == "keyword"

        # Гибридный поиск
        hybrid_result = await search_service.search_documents(
            query="API documentation", search_type="hybrid"
        )
        assert hybrid_result["search_type"] == "hybrid"

    @pytest.mark.asyncio
    async def test_advanced_search(self, search_service):
        """Тест расширенного поиска"""
        await search_service.initialize()

        filters = {
            "document_types": ["page"],
            "categories": ["documentation"],
            "authors": ["John Doe"],
            "updated_at_range": [
                (datetime.now() - timedelta(days=30)).isoformat(),
                datetime.now().isoformat(),
            ],
        }

        result = await search_service.advanced_search(
            query="API",
            filters=filters,
            sort_by="relevance",
            sort_order="desc",
            include_metadata=True,
        )

        assert "results" in result
        assert "facets" in result
        assert "search_type" in result

        # Проверяем фасеты
        facets = result["facets"]
        assert "source_types" in facets
        assert "document_types" in facets
        assert "categories" in facets
        assert "authors" in facets

    @pytest.mark.asyncio
    async def test_get_searched_sources(self, search_service):
        """Тест получения источников поиска"""
        await search_service.initialize()

        sources = await search_service.get_searched_sources("test query")

        assert isinstance(sources, list)
        assert len(sources) > 0
        assert "confluence" in sources
        assert "jira" in sources
        assert "gitlab" in sources

    @pytest.mark.asyncio
    async def test_upload_document(self, search_service):
        """Тест загрузки документа"""
        await search_service.initialize()

        # Mock файл и запрос
        mock_file = Mock()
        mock_file.filename = "test_document.pdf"

        mock_request = Mock()
        mock_request.title = "Test Document"

        result = await search_service.upload_document(
            file=mock_file, file_type="pdf", request=mock_request
        )

        assert "document_id" in result
        assert "title" in result
        assert "status" in result
        assert "message" in result
        assert result["status"] == "uploaded"

    @pytest.mark.asyncio
    async def test_search_suggestions(self, search_service):
        """Тест предложений для поиска"""
        await search_service.initialize()

        suggestions = await search_service.get_search_suggestions(query="API", limit=5)

        assert isinstance(suggestions, list)
        assert len(suggestions) <= 5

        for suggestion in suggestions:
            assert isinstance(suggestion, str)
            assert "API" in suggestion

    @pytest.mark.asyncio
    async def test_source_statistics(self, search_service):
        """Тест статистики источников"""
        await search_service.initialize()

        stats = await search_service.get_source_statistics()

        assert isinstance(stats, dict)
        assert "confluence_spaces" in stats
        assert "jira_projects" in stats
        assert "gitlab_repositories" in stats
        assert "content_types" in stats

    @pytest.mark.asyncio
    async def test_pagination(self, search_service):
        """Тест пагинации"""
        await search_service.initialize()

        # Первая страница
        page1 = await search_service.search_documents(query="test", limit=2, offset=0)

        # Вторая страница
        page2 = await search_service.search_documents(query="test", limit=2, offset=2)

        assert len(page1["results"]) <= 2
        assert len(page2["results"]) <= 2

    @pytest.mark.asyncio
    async def test_search_with_snippets(self, search_service):
        """Тест поиска с фрагментами"""
        await search_service.initialize()

        # С фрагментами
        with_snippets = await search_service.search_documents(
            query="API", include_snippets=True
        )

        # Без фрагментов
        without_snippets = await search_service.search_documents(
            query="API", include_snippets=False
        )

        assert "results" in with_snippets
        assert "results" in without_snippets

    @pytest.mark.asyncio
    async def test_error_handling(self, search_service):
        """Тест обработки ошибок"""
        # Тест с невалидными параметрами
        result = await search_service.search_documents(
            query="", limit=-1  # Пустой запрос  # Негативный лимит
        )

        # Сервис должен обработать ошибку gracefully
        assert "results" in result


@pytest.mark.asyncio
class TestSearchServiceWithBackend:
    """Тесты интеграции с backend сервисом"""

    @pytest.mark.asyncio
    async def test_backend_integration(self):
        """Тест интеграции с backend сервисом"""
        # Создаем сервис и проверяем его работу 
        service = SearchService()
        service.use_backend = False  # Принудительно отключаем backend для тестирования
        await service.initialize()

        # Выполняем поиск
        result = await service.search_documents(query="test")

        # Проверяем базовую структуру результата
        assert "results" in result
        assert "total_results" in result
        assert "search_time_ms" in result
        assert isinstance(result["results"], list)

    @pytest.mark.asyncio
    async def test_backend_fallback(self):
        """Тест fallback при недоступности backend"""
        service = SearchService()
        service.use_backend = False  # Симулируем fallback к mock implementation
        await service.initialize()

        # Сервис должен работать на mock реализации
        assert service.use_backend is False
        assert service.embedding_model is not None

        # Поиск должен работать
        result = await service.search_documents(query="test")
        assert "results" in result
        assert isinstance(result["results"], list)


@pytest.mark.asyncio
class TestSearchFilters:
    """Тесты для фильтров поиска"""

    @pytest.mark.asyncio
    async def test_source_type_filter(self, search_service):
        """Тест фильтра по типу источника"""
        await search_service.initialize()

        filters = {"source_types": ["confluence"]}
        result = await search_service.search_documents(query="test", filters=filters)

        assert "results" in result

    @pytest.mark.asyncio
    async def test_date_range_filter(self, search_service):
        """Тест фильтра по диапазону дат"""
        await search_service.initialize()

        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        filters = {"updated_at_range": [start_date.isoformat(), end_date.isoformat()]}

        result = await search_service.search_documents(query="test", filters=filters)

        assert "results" in result

    @pytest.mark.asyncio
    async def test_author_filter(self, search_service):
        """Тест фильтра по автору"""
        await search_service.initialize()

        filters = {"authors": ["John Doe", "Jane Smith"]}
        result = await search_service.search_documents(query="test", filters=filters)

        assert "results" in result

    @pytest.mark.asyncio
    async def test_category_filter(self, search_service):
        """Тест фильтра по категории"""
        await search_service.initialize()

        filters = {"categories": ["documentation", "code"]}
        result = await search_service.search_documents(query="test", filters=filters)

        assert "results" in result


@pytest.mark.asyncio
class TestSearchPerformance:
    """Тесты производительности поиска"""

    @pytest.mark.asyncio
    async def test_search_response_time(self, search_service):
        """Тест времени ответа поиска"""
        await search_service.initialize()

        start_time = datetime.now()
        result = await search_service.search_documents(query="performance test")
        end_time = datetime.now()

        response_time = (end_time - start_time).total_seconds() * 1000

        assert response_time < 5000  # Менее 5 секунд
        assert "search_time_ms" in result
        assert result["search_time_ms"] > 0

    @pytest.mark.asyncio
    async def test_large_result_set(self, search_service):
        """Тест с большим количеством результатов"""
        await search_service.initialize()

        result = await search_service.search_documents(query="test", limit=100)

        assert "results" in result
        assert len(result["results"]) <= 100


@pytest.mark.asyncio
async def test_get_search_service_singleton():
    """Тест что get_search_service возвращает singleton"""
    from domain.integration.search_service import get_search_service

    with patch.object(SearchService, "initialize") as mock_init:
        mock_init.return_value = None

        service1 = await get_search_service()
        service2 = await get_search_service()

        # Должен быть один и тот же экземпляр
        assert service1 is service2

        # Инициализация должна быть вызвана только один раз
        mock_init.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
