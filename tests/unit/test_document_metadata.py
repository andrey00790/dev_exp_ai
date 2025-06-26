"""
Тесты для модели документов с метаданными
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import json

from models.document import (
    Document, DocumentChunk, SearchFilter, CommonFilters,
    SourceType, DocumentStatus
)


class TestDocument:
    """Тесты для модели Document"""
    
    def test_document_creation(self):
        """Тест создания документа"""
        doc = Document(
            title="Test Document",
            content="Test content",
            source_type=SourceType.CONFLUENCE,
            source_name="main_confluence",
            source_id="123456"
        )
        
        assert doc.title == "Test Document"
        assert doc.content == "Test content"
        assert doc.source_type == SourceType.CONFLUENCE
        assert doc.source_name == "main_confluence"
        assert doc.source_id == "123456"
    
    def test_document_to_dict(self):
        """Тест преобразования документа в словарь"""
        doc = Document(
            title="Test Document",
            content="Test content",
            source_type=SourceType.CONFLUENCE,
            source_name="main_confluence",
            source_id="123456",
            space_key="TECH",
            category="documentation",
            author="John Doe",
            tags=["api", "test"],
            quality_score=0.85,
            status=DocumentStatus.ACTIVE
        )
        
        doc_dict = doc.to_dict()
        
        assert doc_dict["title"] == "Test Document"
        assert doc_dict["source"]["type"] == SourceType.CONFLUENCE
        assert doc_dict["source"]["name"] == "main_confluence"
        assert doc_dict["hierarchy"]["space_key"] == "TECH"
        assert doc_dict["categorization"]["category"] == "documentation"
        assert doc_dict["categorization"]["tags"] == ["api", "test"]
        assert doc_dict["authorship"]["author"] == "John Doe"
        assert doc_dict["status"]["quality_score"] == 0.85
    
    def test_from_confluence_page(self):
        """Тест создания документа из страницы Confluence"""
        page_data = {
            "id": "123456",
            "title": "API Documentation",
            "body": {
                "storage": {
                    "value": "<p>This is API documentation</p>"
                }
            },
            "_links": {
                "webui": "/pages/123456"
            },
            "space": {
                "key": "TECH"
            },
            "history": {
                "createdBy": {
                    "displayName": "John Doe",
                    "email": "john@company.com"
                },
                "createdDate": "2024-01-15T10:00:00.000Z"
            },
            "version": {
                "when": "2024-01-15T12:00:00.000Z"
            },
            "metadata": {
                "labels": {
                    "results": [
                        {"name": "api"},
                        {"name": "documentation"}
                    ]
                }
            }
        }
        
        doc = Document.from_confluence_page(page_data, "main_confluence")
        
        assert doc.title == "API Documentation"
        assert doc.source_type == SourceType.CONFLUENCE
        assert doc.source_name == "main_confluence"
        assert doc.source_id == "123456"
        assert doc.source_url == "/pages/123456"
        assert doc.space_key == "TECH"
        assert doc.document_type == "page"
        assert doc.category == "documentation"
        assert doc.author == "John Doe"
        assert doc.author_email == "john@company.com"
        assert doc.source_created_at is not None
        assert doc.source_updated_at is not None
    
    def test_from_jira_issue(self):
        """Тест создания документа из задачи Jira"""
        issue_data = {
            "key": "PROJ-123",
            "self": "https://company.atlassian.net/rest/api/2/issue/123",
            "fields": {
                "summary": "Implement user authentication",
                "description": "We need to implement OAuth2 authentication",
                "project": {
                    "key": "PROJ"
                },
                "creator": {
                    "displayName": "Jane Smith",
                    "emailAddress": "jane@company.com"
                },
                "assignee": {
                    "displayName": "Bob Johnson"
                },
                "priority": {
                    "name": "High"
                },
                "status": {
                    "name": "In Progress"
                },
                "issuetype": {
                    "name": "Story"
                },
                "labels": ["authentication", "oauth2"],
                "created": "2024-01-15T09:00:00.000Z",
                "updated": "2024-01-15T11:00:00.000Z",
                "comment": {
                    "comments": [
                        {
                            "author": {
                                "displayName": "Alice Brown"
                            },
                            "body": "This is a comment"
                        }
                    ]
                }
            }
        }
        
        doc = Document.from_jira_issue(issue_data, "main_jira")
        
        assert doc.title == "[PROJ-123] Implement user authentication"
        assert doc.source_type == SourceType.JIRA
        assert doc.source_name == "main_jira"
        assert doc.source_id == "PROJ-123"
        assert "https://company.atlassian.net/browse/PROJ-123" in doc.source_url
        assert doc.project_key == "PROJ"
        assert doc.document_type == "issue"
        assert doc.category == "requirements"
        assert doc.author == "Jane Smith"
        assert doc.author_email == "jane@company.com"
        assert doc.assignee == "Bob Johnson"
        assert doc.priority == "High"
        assert doc.status == "In Progress"
        assert doc.tags == ["authentication", "oauth2"]
        assert "OAuth2 authentication" in doc.content
        assert "This is a comment" in doc.content
    
    def test_from_gitlab_file(self):
        """Тест создания документа из файла GitLab"""
        file_data = {
            "file_path": "src/auth/README.md",
            "content": "# Authentication Module\n\nThis module handles authentication",
            "web_url": "https://gitlab.com/project/blob/main/src/auth/README.md",
            "size": 1024,
            "encoding": "utf-8",
            "ref": "main",
            "commit_id": "abc123",
            "blob_id": "def456",
            "last_commit_date": "2024-01-15T14:00:00.000Z"
        }
        
        project_data = {
            "id": 789,
            "name": "backend-service",
            "path_with_namespace": "company/backend-service"
        }
        
        doc = Document.from_gitlab_file(file_data, project_data, "main_gitlab")
        
        assert doc.title == "backend-service: src/auth/README.md"
        assert doc.source_type == SourceType.GITLAB
        assert doc.source_name == "main_gitlab"
        assert doc.source_id == "789:src/auth/README.md"
        assert doc.source_url == "https://gitlab.com/project/blob/main/src/auth/README.md"
        assert doc.repository_name == "backend-service"
        assert doc.project_key == "company/backend-service"
        assert doc.document_type == "file"
        assert doc.category == "documentation"
        assert doc.file_extension == "md"
        assert doc.file_size == 1024
        assert doc.encoding == "utf-8"
        assert doc.source_updated_at is not None
    
    def test_from_local_file(self):
        """Тест создания документа из локального файла"""
        file_metadata = {
            "size": 2048,
            "encoding": "utf-8",
            "created_time": 1705320000,  # timestamp
            "modified_time": 1705323600
        }
        
        doc = Document.from_local_file(
            "/app/bootstrap/training_guide.pdf",
            "This is training content",
            "bootstrap",
            file_metadata
        )
        
        assert doc.title == "training_guide.pdf"
        assert doc.source_type == SourceType.LOCAL_FILES
        assert doc.source_name == "bootstrap"
        assert doc.source_id == "/app/bootstrap/training_guide.pdf"
        assert doc.source_url == "file:///app/bootstrap/training_guide.pdf"
        assert doc.document_type == "file"
        assert doc.category == "training_data"
        assert doc.file_extension == "pdf"
        assert doc.file_size == 2048
        assert doc.encoding == "utf-8"
        assert doc.source_created_at is not None
        assert doc.source_updated_at is not None


class TestDocumentChunk:
    """Тесты для модели DocumentChunk"""
    
    def test_chunk_creation(self):
        """Тест создания чанка документа"""
        chunk = DocumentChunk(
            document_id="doc123",
            chunk_index=0,
            content="This is a chunk of content",
            source_type=SourceType.CONFLUENCE,
            source_name="main_confluence",
            start_position=0,
            end_position=100,
            quality_score=0.8
        )
        
        assert chunk.document_id == "doc123"
        assert chunk.chunk_index == 0
        assert chunk.content == "This is a chunk of content"
        assert chunk.source_type == SourceType.CONFLUENCE
        assert chunk.source_name == "main_confluence"
        assert chunk.start_position == 0
        assert chunk.end_position == 100
        assert chunk.quality_score == 0.8
    
    def test_chunk_to_dict(self):
        """Тест преобразования чанка в словарь"""
        chunk = DocumentChunk(
            document_id="doc123",
            chunk_index=1,
            content="Another chunk",
            source_type=SourceType.JIRA,
            source_name="main_jira",
            start_position=100,
            end_position=200,
            quality_score=0.9
        )
        
        chunk_dict = chunk.to_dict()
        
        assert chunk_dict["document_id"] == "doc123"
        assert chunk_dict["chunk_index"] == 1
        assert chunk_dict["content"] == "Another chunk"
        assert chunk_dict["source_type"] == SourceType.JIRA
        assert chunk_dict["source_name"] == "main_jira"
        assert chunk_dict["position"]["start"] == 100
        assert chunk_dict["position"]["end"] == 200
        assert chunk_dict["quality_score"] == 0.9


class TestSearchFilter:
    """Тесты для SearchFilter"""
    
    def test_basic_filters(self):
        """Тест базовых фильтров"""
        filter_obj = SearchFilter()
        
        # Тест фильтра по типу источника
        filter_obj.by_source_type(["confluence", "jira"])
        assert filter_obj.filters["source_type"] == ["confluence", "jira"]
        
        # Тест фильтра по названию источника
        filter_obj.by_source_name(["main_confluence", "dev_jira"])
        assert filter_obj.filters["source_name"] == ["main_confluence", "dev_jira"]
        
        # Тест фильтра по проекту
        filter_obj.by_project(["PROJ", "TECH"])
        assert filter_obj.filters["project_key"] == ["PROJ", "TECH"]
    
    def test_content_filters(self):
        """Тест фильтров по контенту"""
        filter_obj = SearchFilter()
        
        filter_obj.by_document_type(["page", "issue"])
        filter_obj.by_category(["documentation", "code"])
        filter_obj.by_file_extension(["md", "py"])
        
        assert filter_obj.filters["document_type"] == ["page", "issue"]
        assert filter_obj.filters["category"] == ["documentation", "code"]
        assert filter_obj.filters["file_extension"] == ["md", "py"]
    
    def test_time_filters(self):
        """Тест временных фильтров"""
        filter_obj = SearchFilter()
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        filter_obj.by_date_range(start_date, end_date, "updated_at")
        
        assert filter_obj.filters["updated_at_range"] == (start_date, end_date)
    
    def test_quality_filters(self):
        """Тест фильтров по качеству"""
        filter_obj = SearchFilter()
        
        filter_obj.by_quality_score(0.7)
        filter_obj.by_tags(["api", "documentation"])
        filter_obj.by_priority(["high", "medium"])
        
        assert filter_obj.filters["min_quality_score"] == 0.7
        assert filter_obj.filters["tags"] == ["api", "documentation"]
        assert filter_obj.filters["priority"] == ["high", "medium"]
    
    def test_filter_chaining(self):
        """Тест цепочки фильтров"""
        filters = (SearchFilter()
                  .by_source_type(["confluence"])
                  .by_category(["documentation"])
                  .by_quality_score(0.8)
                  .build())
        
        assert filters["source_type"] == ["confluence"]
        assert filters["category"] == ["documentation"]
        assert filters["min_quality_score"] == 0.8


class TestCommonFilters:
    """Тесты для предопределенных фильтров"""
    
    def test_confluence_documentation(self):
        """Тест фильтра документации Confluence"""
        filters = CommonFilters.confluence_documentation().build()
        
        assert filters["source_type"] == ["confluence"]
        assert filters["category"] == ["documentation"]
    
    def test_jira_requirements(self):
        """Тест фильтра требований Jira"""
        filters = CommonFilters.jira_requirements().build()
        
        assert filters["source_type"] == ["jira"]
        assert filters["category"] == ["requirements"]
    
    def test_gitlab_code(self):
        """Тест фильтра кода GitLab"""
        filters = CommonFilters.gitlab_code().build()
        
        assert filters["source_type"] == ["gitlab"]
        assert filters["category"] == ["code"]
    
    def test_recent_updates(self):
        """Тест фильтра недавних обновлений"""
        filters = CommonFilters.recent_updates(7).build()
        
        assert "updated_at_range" in filters
        start_date, end_date = filters["updated_at_range"]
        
        # Проверяем что диапазон примерно 7 дней
        delta = end_date - start_date
        assert 6 <= delta.days <= 8
    
    def test_high_quality_content(self):
        """Тест фильтра высококачественного контента"""
        filters = CommonFilters.high_quality_content(0.8).build()
        
        assert filters["min_quality_score"] == 0.8
    
    def test_by_project_context(self):
        """Тест фильтра по контексту проекта"""
        filters = CommonFilters.by_project_context("PROJ").build()
        
        assert filters["project_key"] == ["PROJ"]


@pytest.fixture
def sample_document():
    """Фикстура для создания тестового документа"""
    return Document(
        title="Sample Document",
        content="This is sample content for testing",
        source_type=SourceType.CONFLUENCE,
        source_name="test_confluence",
        source_id="test123",
        space_key="TEST",
        category="documentation",
        author="Test User",
        tags=["test", "sample"],
        quality_score=0.85
    )


@pytest.fixture
def sample_chunk():
    """Фикстура для создания тестового чанка"""
    return DocumentChunk(
        document_id="doc123",
        chunk_index=0,
        content="Sample chunk content",
        source_type=SourceType.CONFLUENCE,
        source_name="test_confluence",
        start_position=0,
        end_position=50,
        quality_score=0.9
    )


class TestDocumentIntegration:
    """Интеграционные тесты для модели документов"""
    
    def test_document_with_chunks(self, sample_document, sample_chunk):
        """Тест документа с чанками"""
        # В реальной системе чанки связаны с документом через foreign key
        sample_chunk.document_id = sample_document.id
        
        assert sample_chunk.document_id == sample_document.id
        assert sample_chunk.source_type == sample_document.source_type
        assert sample_chunk.source_name == sample_document.source_name
    
    def test_document_metadata_consistency(self, sample_document):
        """Тест консистентности метаданных"""
        doc_dict = sample_document.to_dict()
        
        # Проверяем что все основные поля присутствуют
        required_sections = [
            "source", "hierarchy", "categorization", 
            "authorship", "timestamps", "status", "technical"
        ]
        
        for section in required_sections:
            assert section in doc_dict
        
        # Проверяем консистентность типов источников
        assert doc_dict["source"]["type"] in [e.value for e in SourceType]
    
    def test_search_filter_with_document(self, sample_document):
        """Тест применения фильтров к документу"""
        # Создаем фильтр который должен соответствовать документу
        matching_filter = (SearchFilter()
                          .by_source_type([sample_document.source_type])
                          .by_category([sample_document.category])
                          .build())
        
        # Проверяем что фильтр содержит правильные значения
        assert sample_document.source_type in matching_filter["source_type"]
        assert sample_document.category in matching_filter["category"]
        
        # Создаем фильтр который не должен соответствовать
        non_matching_filter = (SearchFilter()
                              .by_source_type(["jira"])
                              .by_category(["code"])
                              .build())
        
        assert sample_document.source_type not in non_matching_filter["source_type"]
        assert sample_document.category not in non_matching_filter["category"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 