"""
Упрощенные тесты для основной функциональности документов
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch

import pytest


def test_source_type_enum():
    """Тест перечисления типов источников"""
    from models.document import SourceType

    assert SourceType.CONFLUENCE == "confluence"
    assert SourceType.JIRA == "jira"
    assert SourceType.GITLAB == "gitlab"
    assert SourceType.LOCAL_FILES == "local_files"


def test_document_status_enum():
    """Тест перечисления статусов документов"""
    from models.document import DocumentStatus

    assert DocumentStatus.ACTIVE == "active"
    assert DocumentStatus.ARCHIVED == "archived"
    assert DocumentStatus.DELETED == "deleted"
    assert DocumentStatus.PROCESSING == "processing"
    assert DocumentStatus.ERROR == "error"


def test_search_filter_basic():
    """Тест базовой функциональности SearchFilter"""
    from models.document import SearchFilter

    filter_obj = SearchFilter()

    # Тест добавления фильтров
    filter_obj.by_source_type(["confluence", "jira"])
    filter_obj.by_category(["documentation"])

    filters = filter_obj.build()

    assert filters["source_type"] == ["confluence", "jira"]
    assert filters["category"] == ["documentation"]


def test_search_filter_chaining():
    """Тест цепочки фильтров"""
    from models.document import SearchFilter

    filters = (
        SearchFilter()
        .by_source_type(["confluence"])
        .by_category(["documentation"])
        .by_quality_score(0.8)
        .build()
    )

    assert filters["source_type"] == ["confluence"]
    assert filters["category"] == ["documentation"]
    assert filters["min_quality_score"] == 0.8


def test_common_filters():
    """Тест предопределенных фильтров"""
    from models.document import CommonFilters

    # Тест фильтра документации Confluence
    confluence_filters = CommonFilters.confluence_documentation().build()
    assert confluence_filters["source_type"] == ["confluence"]
    assert confluence_filters["category"] == ["documentation"]

    # Тест фильтра требований Jira
    jira_filters = CommonFilters.jira_requirements().build()
    assert jira_filters["source_type"] == ["jira"]
    assert jira_filters["category"] == ["requirements"]

    # Тест фильтра кода GitLab
    gitlab_filters = CommonFilters.gitlab_code().build()
    assert gitlab_filters["source_type"] == ["gitlab"]
    assert gitlab_filters["category"] == ["code"]


def test_time_filter():
    """Тест временного фильтра"""
    from datetime import datetime, timedelta

    from models.document import SearchFilter

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)

    filter_obj = SearchFilter()
    filter_obj.by_date_range(start_date, end_date, "updated_at")

    filters = filter_obj.build()
    assert filters["updated_at_range"] == (start_date, end_date)


def test_recent_updates_filter():
    """Тест фильтра недавних обновлений"""
    from models.document import CommonFilters

    filters = CommonFilters.recent_updates(7).build()

    assert "updated_at_range" in filters
    start_date, end_date = filters["updated_at_range"]

    # Проверяем что диапазон примерно 7 дней
    delta = end_date - start_date
    assert 6 <= delta.days <= 8


def test_high_quality_filter():
    """Тест фильтра высококачественного контента"""
    from models.document import CommonFilters

    filters = CommonFilters.high_quality_content(0.8).build()
    assert filters["min_quality_score"] == 0.8


def test_project_context_filter():
    """Тест фильтра по контексту проекта"""
    from models.document import CommonFilters

    filters = CommonFilters.by_project_context("PROJ").build()
    assert filters["project_key"] == ["PROJ"]


def test_multiple_filters():
    """Тест комбинации множественных фильтров"""
    from models.document import SearchFilter

    filter_obj = SearchFilter()

    # Добавляем разные типы фильтров
    filter_obj.by_source_type(["confluence", "jira"])
    filter_obj.by_document_type(["page", "issue"])
    filter_obj.by_author(["John Doe", "Jane Smith"])
    filter_obj.by_tags(["api", "documentation"])
    filter_obj.by_priority(["high", "medium"])
    filter_obj.by_language(["en", "ru"])
    filter_obj.by_file_extension(["md", "py"])

    filters = filter_obj.build()

    # Проверяем все фильтры
    assert filters["source_type"] == ["confluence", "jira"]
    assert filters["document_type"] == ["page", "issue"]
    assert filters["author"] == ["John Doe", "Jane Smith"]
    assert filters["tags"] == ["api", "documentation"]
    assert filters["priority"] == ["high", "medium"]
    assert filters["language"] == ["en", "ru"]
    assert filters["file_extension"] == ["md", "py"]


def test_empty_filter():
    """Тест пустого фильтра"""
    from models.document import SearchFilter

    filter_obj = SearchFilter()
    filters = filter_obj.build()

    assert filters == {}


def test_documentation_sources_filter():
    """Тест фильтра источников документации"""
    from models.document import CommonFilters

    filters = CommonFilters.documentation_sources().build()

    assert "confluence" in filters["source_type"]
    assert "gitlab" in filters["source_type"]
    assert filters["category"] == ["documentation"]


def test_code_and_architecture_filter():
    """Тест фильтра кода и архитектуры"""
    from models.document import CommonFilters

    filters = CommonFilters.code_and_architecture().build()

    expected_categories = ["code", "architecture", "documentation"]
    assert filters["category"] == expected_categories


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
