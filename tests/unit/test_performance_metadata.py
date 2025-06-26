"""
Тесты производительности для системы метаданных
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock
from models.document import Document, SearchFilter, CommonFilters, SourceType, DocumentStatus


class TestMetadataPerformance:
    """Тесты производительности метаданных"""
    
    def test_document_creation_performance(self):
        """Тест производительности создания документов"""
        start_time = time.time()
        
        documents = []
        for i in range(1000):
            doc = Document(
                title=f"Test Document {i}",
                content=f"Test content for document {i}",
                source_type=SourceType.CONFLUENCE,
                source_name="main_confluence",
                source_id=f"doc_{i}",
                space_key="TECH",
                document_type="page",
                category="documentation",
                author=f"Author {i % 10}",
                tags=[f"tag_{i % 5}", f"category_{i % 3}"],
                quality_score=0.5 + (i % 50) / 100,
                status=DocumentStatus.ACTIVE
            )
            documents.append(doc)
        
        creation_time = time.time() - start_time
        
        # Проверяем что создание 1000 документов занимает разумное время
        assert creation_time < 2.0, f"Создание 1000 документов заняло {creation_time:.2f}s"
        assert len(documents) == 1000
        
        print(f"Создание 1000 документов: {creation_time:.3f}s ({creation_time/1000*1000:.1f}ms на документ)")
    
    def test_document_serialization_performance(self):
        """Тест производительности сериализации документов"""
        # Создаем документы с полными метаданными
        documents = []
        for i in range(100):
            doc = Document(
                title=f"Complex Document {i}",
                content=f"Complex content for document {i} with lots of metadata",
                source_type=SourceType.CONFLUENCE,
                source_name="main_confluence",
                source_id=f"complex_doc_{i}",
                space_key="TECH",
                document_type="page",
                category="documentation",
                author=f"Author {i}",
                tags=[f"tag_{j}" for j in range(10)],  # 10 тегов
                quality_score=0.8,
                document_metadata={
                    "confluence_space": {"key": "TECH", "name": "Technical"},
                    "custom_fields": {f"field_{j}": f"value_{j}" for j in range(20)},
                    "nested_data": {"level1": {"level2": {"level3": "deep_value"}}}
                },
                status=DocumentStatus.ACTIVE
            )
            documents.append(doc)
        
        # Тестируем сериализацию
        start_time = time.time()
        serialized_docs = []
        for doc in documents:
            serialized_docs.append(doc.to_dict())
        
        serialization_time = time.time() - start_time
        
        assert serialization_time < 1.0, f"Сериализация 100 документов заняла {serialization_time:.2f}s"
        assert len(serialized_docs) == 100
        
        # Проверяем что метаданные сериализованы
        assert "metadata" in serialized_docs[0]
        assert "confluence_space" in serialized_docs[0]["metadata"]
        
        print(f"Сериализация 100 сложных документов: {serialization_time:.3f}s ({serialization_time/100*1000:.1f}ms на документ)")
    
    def test_filter_building_performance(self):
        """Тест производительности построения фильтров"""
        start_time = time.time()
        
        filters = []
        for i in range(1000):
            filter_obj = (SearchFilter()
                         .by_source_type([f"source_{i % 5}"])
                         .by_category([f"category_{i % 3}"])
                         .by_author([f"author_{i % 10}"])
                         .by_tags([f"tag_{j}" for j in range(i % 5 + 1)])
                         .by_quality_score(0.5 + (i % 50) / 100)
                         .by_date_range(
                             datetime.now() - timedelta(days=30),
                             datetime.now(),
                             "updated_at"
                         ))
            filters.append(filter_obj.build())
        
        building_time = time.time() - start_time
        
        assert building_time < 1.0, f"Построение 1000 фильтров заняло {building_time:.2f}s"
        assert len(filters) == 1000
        
        # Проверяем что фильтры построены правильно
        assert "source_type" in filters[0]
        assert "category" in filters[0]
        assert "updated_at_range" in filters[0]
        
        print(f"Построение 1000 сложных фильтров: {building_time:.3f}s ({building_time/1000*1000:.1f}ms на фильтр)")
    
    def test_common_filters_performance(self):
        """Тест производительности предопределенных фильтров"""
        start_time = time.time()
        
        # Создаем множество предопределенных фильтров
        filter_types = [
            CommonFilters.confluence_documentation,
            CommonFilters.jira_requirements,
            CommonFilters.gitlab_code,
            lambda: CommonFilters.recent_updates(7),
            lambda: CommonFilters.high_quality_content(0.8),
            lambda: CommonFilters.by_project_context("PROJ"),
            CommonFilters.documentation_sources,
            CommonFilters.code_and_architecture
        ]
        
        filters = []
        for i in range(1000):
            filter_func = filter_types[i % len(filter_types)]
            filters.append(filter_func().build())
        
        building_time = time.time() - start_time
        
        assert building_time < 0.5, f"Построение 1000 предопределенных фильтров заняло {building_time:.2f}s"
        assert len(filters) == 1000
        
        print(f"Построение 1000 предопределенных фильтров: {building_time:.3f}s ({building_time/1000*1000:.1f}ms на фильтр)")
    
    def test_document_factory_methods_performance(self):
        """Тест производительности фабричных методов"""
        # Подготавливаем тестовые данные
        confluence_data = {
            "id": "123456",
            "title": "Test Page",
            "body": {"storage": {"value": "<p>Test content</p>"}},
            "_links": {"webui": "/pages/123456"},
            "space": {"key": "TECH"},
            "history": {
                "createdBy": {"displayName": "John Doe", "email": "john@company.com"},
                "createdDate": "2024-01-15T10:00:00.000Z"
            },
            "version": {"when": "2024-01-15T12:00:00.000Z"},
            "metadata": {"labels": {"results": [{"name": "api"}]}}
        }
        
        jira_data = {
            "key": "PROJ-123",
            "self": "https://company.atlassian.net/rest/api/2/issue/123",
            "fields": {
                "summary": "Test Issue",
                "description": "Test description",
                "project": {"key": "PROJ"},
                "creator": {"displayName": "Jane Smith", "emailAddress": "jane@company.com"},
                "created": "2024-01-15T09:00:00.000Z",
                "updated": "2024-01-15T11:00:00.000Z"
            }
        }
        
        gitlab_file_data = {
            "file_path": "README.md",
            "content": "# Test Project",
            "web_url": "https://gitlab.com/project/blob/main/README.md",
            "size": 1024,
            "encoding": "utf-8",
            "last_commit_date": "2024-01-15T14:00:00.000Z"
        }
        
        gitlab_project_data = {
            "id": 789,
            "name": "test-project",
            "path_with_namespace": "company/test-project"
        }
        
        # Тестируем производительность фабричных методов
        start_time = time.time()
        
        documents = []
        for i in range(100):
            # Confluence документ
            confluence_doc = Document.from_confluence_page(confluence_data, f"confluence_{i}")
            documents.append(confluence_doc)
            
            # Jira документ
            jira_doc = Document.from_jira_issue(jira_data, f"jira_{i}")
            documents.append(jira_doc)
            
            # GitLab документ
            gitlab_doc = Document.from_gitlab_file(gitlab_file_data, gitlab_project_data, f"gitlab_{i}")
            documents.append(gitlab_doc)
        
        factory_time = time.time() - start_time
        
        assert factory_time < 1.0, f"Создание 300 документов через фабричные методы заняло {factory_time:.2f}s"
        assert len(documents) == 300
        
        # Проверяем что документы созданы правильно
        confluence_docs = [d for d in documents if d.source_type == SourceType.CONFLUENCE]
        jira_docs = [d for d in documents if d.source_type == SourceType.JIRA]
        gitlab_docs = [d for d in documents if d.source_type == SourceType.GITLAB]
        
        assert len(confluence_docs) == 100
        assert len(jira_docs) == 100
        assert len(gitlab_docs) == 100
        
        print(f"Создание 300 документов через фабричные методы: {factory_time:.3f}s ({factory_time/300*1000:.1f}ms на документ)")
    
    def test_large_metadata_handling(self):
        """Тест обработки больших объемов метаданных"""
        start_time = time.time()
        
        # Создаем документ с очень большими метаданными
        large_metadata = {
            "large_array": [f"item_{i}" for i in range(1000)],
            "large_dict": {f"key_{i}": f"value_{i}" for i in range(1000)},
            "nested_structure": {
                f"level1_{i}": {
                    f"level2_{j}": {
                        f"level3_{k}": f"value_{i}_{j}_{k}"
                        for k in range(10)
                    }
                    for j in range(10)
                }
                for i in range(10)
            }
        }
        
        doc = Document(
            title="Large Metadata Document",
            content="Document with large metadata",
            source_type=SourceType.CONFLUENCE,
            source_name="main_confluence",
            source_id="large_doc",
            document_metadata=large_metadata,
            status=DocumentStatus.ACTIVE
        )
        
        # Тестируем сериализацию
        serialized = doc.to_dict()
        
        handling_time = time.time() - start_time
        
        assert handling_time < 1.0, f"Обработка больших метаданных заняла {handling_time:.2f}s"
        assert "metadata" in serialized
        assert len(serialized["metadata"]["large_array"]) == 1000
        assert len(serialized["metadata"]["large_dict"]) == 1000
        
        print(f"Обработка больших метаданных: {handling_time:.3f}s")
    
    def test_filter_combination_performance(self):
        """Тест производительности комбинирования фильтров"""
        start_time = time.time()
        
        # Создаем базовые фильтры
        base_filters = [
            SearchFilter().by_source_type(["confluence"]),
            SearchFilter().by_category(["documentation"]),
            SearchFilter().by_author(["John Doe"]),
            SearchFilter().by_quality_score(0.8),
            SearchFilter().by_tags(["api", "test"])
        ]
        
        # Комбинируем фильтры в различных вариациях
        combined_filters = []
        for i in range(100):
            combined_filter = SearchFilter()
            
            # Добавляем случайную комбинацию базовых фильтров
            for j, base_filter in enumerate(base_filters):
                if i % (j + 2) == 0:  # Псевдослучайное добавление
                    base_dict = base_filter.build()
                    for key, value in base_dict.items():
                        if key not in combined_filter.filters:
                            combined_filter.filters[key] = value
            
            combined_filters.append(combined_filter.build())
        
        combination_time = time.time() - start_time
        
        assert combination_time < 0.5, f"Комбинирование 100 фильтров заняло {combination_time:.2f}s"
        assert len(combined_filters) == 100
        
        print(f"Комбинирование 100 сложных фильтров: {combination_time:.3f}s ({combination_time/100*1000:.1f}ms на комбинацию)")


class TestMemoryUsage:
    """Тесты использования памяти"""
    
    def test_document_memory_efficiency(self):
        """Тест эффективности использования памяти документами"""
        import sys
        
        # Создаем документы и измеряем память
        documents = []
        for i in range(1000):
            doc = Document(
                title=f"Memory Test Document {i}",
                content=f"Content for memory test {i}" * 10,  # ~250 символов
                source_type=SourceType.CONFLUENCE,
                source_name="main_confluence",
                source_id=f"mem_doc_{i}",
                tags=[f"tag_{j}" for j in range(5)],
                document_metadata={"test": f"metadata_{i}"},
                status=DocumentStatus.ACTIVE
            )
            documents.append(doc)
        
        # Приблизительная оценка размера одного документа
        # (это очень грубая оценка, но дает представление)
        estimated_size_per_doc = sys.getsizeof(documents[0])
        total_estimated_size = estimated_size_per_doc * len(documents)
        
        # Проверяем что размер разумный (менее 1MB для 1000 документов)
        assert total_estimated_size < 1024 * 1024, f"1000 документов занимают {total_estimated_size} байт"
        
        print(f"Приблизительный размер 1000 документов: {total_estimated_size/1024:.1f}KB ({estimated_size_per_doc}B на документ)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s для показа print statements 