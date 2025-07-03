"""
Интеграционные тесты для системы метаданных
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient


def test_metadata_fields_consistency():
    """Тест консистентности полей метаданных"""
    from models.document import Document, DocumentStatus, SourceType

    # Создаем документ с полными метаданными
    doc = Document(
        title="Test Document",
        content="Test content",
        source_type=SourceType.CONFLUENCE,
        source_name="main_confluence",
        source_id="123456",
        space_key="TECH",
        document_type="page",
        category="documentation",
        author="John Doe",
        tags=["api", "test"],
        quality_score=0.85,
        status=DocumentStatus.ACTIVE,
    )

    # Конвертируем в словарь
    doc_dict = doc.to_dict()

    # Проверяем структуру
    required_sections = [
        "source",
        "hierarchy",
        "categorization",
        "authorship",
        "timestamps",
        "status",
        "technical",
    ]

    for section in required_sections:
        assert section in doc_dict, f"Missing section: {section}"

    # Проверяем конкретные поля
    assert doc_dict["source"]["type"] == SourceType.CONFLUENCE
    assert doc_dict["source"]["name"] == "main_confluence"
    assert doc_dict["hierarchy"]["space_key"] == "TECH"
    assert doc_dict["categorization"]["category"] == "documentation"
    assert doc_dict["categorization"]["tags"] == ["api", "test"]
    assert doc_dict["authorship"]["author"] == "John Doe"
    assert doc_dict["status"]["quality_score"] == 0.85


def test_confluence_document_creation():
    """Тест создания документа из данных Confluence"""
    from models.document import Document

    page_data = {
        "id": "123456",
        "title": "API Documentation",
        "body": {"storage": {"value": "<p>This is API documentation</p>"}},
        "_links": {"webui": "/pages/123456"},
        "space": {"key": "TECH"},
        "history": {
            "createdBy": {"displayName": "John Doe", "email": "john@company.com"},
            "createdDate": "2024-01-15T10:00:00.000Z",
        },
        "version": {"when": "2024-01-15T12:00:00.000Z"},
        "metadata": {
            "labels": {"results": [{"name": "api"}, {"name": "documentation"}]}
        },
    }

    doc = Document.from_confluence_page(page_data, "main_confluence")

    # Проверяем основные поля
    assert doc.title == "API Documentation"
    assert doc.source_type == "confluence"
    assert doc.source_name == "main_confluence"
    assert doc.source_id == "123456"
    assert doc.space_key == "TECH"
    assert doc.document_type == "page"
    assert doc.category == "documentation"
    assert doc.author == "John Doe"
    assert doc.author_email == "john@company.com"

    # Проверяем метаданные
    assert doc.document_metadata is not None
    assert "confluence_space" in doc.document_metadata
    assert doc.document_metadata["confluence_space"]["key"] == "TECH"


def test_jira_document_creation():
    """Тест создания документа из задачи Jira"""
    from models.document import Document

    issue_data = {
        "key": "PROJ-123",
        "self": "https://company.atlassian.net/rest/api/2/issue/123",
        "fields": {
            "summary": "Implement user authentication",
            "description": "We need to implement OAuth2 authentication",
            "project": {"key": "PROJ"},
            "creator": {
                "displayName": "Jane Smith",
                "emailAddress": "jane@company.com",
            },
            "assignee": {"displayName": "Bob Johnson"},
            "priority": {"name": "High"},
            "status": {"name": "In Progress"},
            "issuetype": {"name": "Story"},
            "labels": ["authentication", "oauth2"],
            "created": "2024-01-15T09:00:00.000Z",
            "updated": "2024-01-15T11:00:00.000Z",
        },
    }

    doc = Document.from_jira_issue(issue_data, "main_jira")

    # Проверяем основные поля
    assert doc.title == "[PROJ-123] Implement user authentication"
    assert doc.source_type == "jira"
    assert doc.source_name == "main_jira"
    assert doc.source_id == "PROJ-123"
    assert doc.project_key == "PROJ"
    assert doc.document_type == "issue"
    assert doc.category == "requirements"
    assert doc.author == "Jane Smith"
    assert doc.assignee == "Bob Johnson"
    assert doc.priority == "High"
    assert doc.tags == ["authentication", "oauth2"]

    # Проверяем что URL правильно сформирован
    assert "https://company.atlassian.net/browse/PROJ-123" in doc.source_url

    # Проверяем контент
    assert "OAuth2 authentication" in doc.content


def test_gitlab_document_creation():
    """Тест создания документа из файла GitLab"""
    from models.document import Document

    file_data = {
        "file_path": "src/auth/README.md",
        "content": "# Authentication Module\n\nThis module handles authentication",
        "web_url": "https://gitlab.com/project/blob/main/src/auth/README.md",
        "size": 1024,
        "encoding": "utf-8",
        "ref": "main",
        "commit_id": "abc123",
        "blob_id": "def456",
        "last_commit_date": "2024-01-15T14:00:00.000Z",
    }

    project_data = {
        "id": 789,
        "name": "backend-service",
        "path_with_namespace": "company/backend-service",
    }

    doc = Document.from_gitlab_file(file_data, project_data, "main_gitlab")

    # Проверяем основные поля
    assert doc.title == "backend-service: src/auth/README.md"
    assert doc.source_type == "gitlab"
    assert doc.source_name == "main_gitlab"
    assert doc.source_id == "789:src/auth/README.md"
    assert doc.repository_name == "backend-service"
    assert doc.project_key == "company/backend-service"
    assert doc.document_type == "file"
    assert doc.category == "documentation"  # .md файл
    assert doc.file_extension == "md"
    assert doc.file_size == 1024
    assert doc.encoding == "utf-8"


def test_local_file_document_creation():
    """Тест создания документа из локального файла"""
    from models.document import Document

    file_metadata = {
        "size": 2048,
        "encoding": "utf-8",
        "created_time": 1705320000,  # timestamp
        "modified_time": 1705323600,
    }

    doc = Document.from_local_file(
        "/app/bootstrap/training_guide.pdf",
        "This is training content",
        "bootstrap",
        file_metadata,
    )

    # Проверяем основные поля
    assert doc.title == "training_guide.pdf"
    assert doc.source_type == "local_files"
    assert doc.source_name == "bootstrap"
    assert doc.source_id == "/app/bootstrap/training_guide.pdf"
    assert doc.source_url == "file:///app/bootstrap/training_guide.pdf"
    assert doc.document_type == "file"
    assert doc.category == "training_data"
    assert doc.file_extension == "pdf"
    assert doc.file_size == 2048
    assert doc.encoding == "utf-8"


def test_document_chunk_creation():
    """Тест создания чанков документов"""
    from models.document import DocumentChunk, SourceType

    chunk = DocumentChunk(
        document_id="doc123",
        chunk_index=0,
        content="This is a chunk of content",
        source_type=SourceType.CONFLUENCE,
        source_name="main_confluence",
        start_position=0,
        end_position=100,
        quality_score=0.8,
    )

    # Проверяем основные поля
    assert chunk.document_id == "doc123"
    assert chunk.chunk_index == 0
    assert chunk.content == "This is a chunk of content"
    assert chunk.source_type == SourceType.CONFLUENCE
    assert chunk.source_name == "main_confluence"
    assert chunk.start_position == 0
    assert chunk.end_position == 100
    assert chunk.quality_score == 0.8

    # Проверяем конвертацию в словарь
    chunk_dict = chunk.to_dict()
    assert chunk_dict["document_id"] == "doc123"
    assert chunk_dict["chunk_index"] == 0
    assert chunk_dict["source_type"] == SourceType.CONFLUENCE
    assert chunk_dict["position"]["start"] == 0
    assert chunk_dict["position"]["end"] == 100


def test_filter_application_to_documents():
    """Тест применения фильтров к документам"""
    from models.document import (Document, DocumentStatus, SearchFilter,
                                 SourceType)

    # Создаем тестовые документы
    doc1 = Document(
        title="Confluence Doc",
        content="Test content",
        source_type=SourceType.CONFLUENCE,
        source_name="main_confluence",
        source_id="123",
        category="documentation",
        status=DocumentStatus.ACTIVE,
    )

    doc2 = Document(
        title="Jira Issue",
        content="Issue content",
        source_type=SourceType.JIRA,
        source_name="main_jira",
        source_id="PROJ-123",
        category="requirements",
        status=DocumentStatus.ACTIVE,
    )

    # Создаем фильтр для Confluence документов
    confluence_filter = (
        SearchFilter()
        .by_source_type([SourceType.CONFLUENCE])
        .by_category(["documentation"])
        .build()
    )

    # Проверяем что фильтр соответствует первому документу
    assert doc1.source_type in confluence_filter["source_type"]
    assert doc1.category in confluence_filter["category"]

    # И не соответствует второму
    assert doc2.source_type not in confluence_filter["source_type"]

    # Создаем фильтр для всех документов
    all_filter = (
        SearchFilter()
        .by_source_type([SourceType.CONFLUENCE, SourceType.JIRA])
        .by_status([DocumentStatus.ACTIVE])
        .build()
    )

    # Проверяем что оба документа соответствуют
    assert doc1.source_type in all_filter["source_type"]
    assert doc2.source_type in all_filter["source_type"]


def test_metadata_serialization():
    """Тест сериализации метаданных"""
    from models.document import Document, SourceType

    # Создаем документ с комплексными метаданными
    doc = Document(
        title="Test Document",
        content="Test content",
        source_type=SourceType.CONFLUENCE,
        source_name="main_confluence",
        source_id="123456",
        tags=["api", "documentation", "test"],
        document_metadata={
            "confluence_space": {"key": "TECH", "name": "Technical Documentation"},
            "custom_fields": {"priority": "high", "team": "backend"},
            "nested_data": {"level1": {"level2": "value"}},
        },
    )

    # Конвертируем в словарь и обратно в JSON
    doc_dict = doc.to_dict()
    json_str = json.dumps(doc_dict, default=str)
    parsed_dict = json.loads(json_str)

    # Проверяем что метаданные сохранились
    assert "metadata" in parsed_dict
    assert "confluence_space" in parsed_dict["metadata"]
    assert parsed_dict["metadata"]["confluence_space"]["key"] == "TECH"
    assert parsed_dict["metadata"]["custom_fields"]["priority"] == "high"
    assert parsed_dict["metadata"]["nested_data"]["level1"]["level2"] == "value"


def test_timestamp_handling():
    """Тест обработки временных меток"""
    from models.document import Document, SourceType

    # Создаем документ с временными метками
    created_time = datetime(2024, 1, 10, 10, 0, 0)
    updated_time = datetime(2024, 1, 15, 14, 30, 0)

    doc = Document(
        title="Test Document",
        content="Test content",
        source_type=SourceType.CONFLUENCE,
        source_name="main_confluence",
        source_id="123456",
        created_at=created_time,
        updated_at=updated_time,
        source_created_at=created_time,
        source_updated_at=updated_time,
    )

    # Конвертируем в словарь
    doc_dict = doc.to_dict()

    # Проверяем что временные метки правильно сериализованы
    timestamps = doc_dict["timestamps"]
    assert timestamps["created_at"] == "2024-01-10T10:00:00"
    assert timestamps["updated_at"] == "2024-01-15T14:30:00"
    assert timestamps["source_created_at"] == "2024-01-10T10:00:00"
    assert timestamps["source_updated_at"] == "2024-01-15T14:30:00"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
