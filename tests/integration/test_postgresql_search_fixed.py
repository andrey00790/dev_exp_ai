#!/usr/bin/env python3
"""
Интеграционные тесты для полнотекстового поиска в PostgreSQL
"""

import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import time
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

pytestmark = pytest.mark.integration

class PostgreSQLSearch:
    """Класс для работы с поиском в PostgreSQL"""
    
    def __init__(self, connection_params: Dict[str, Any]):
        self.connection_params = connection_params
        self._connection = None
    
    def _get_connection(self):
        """Получение подключения к базе данных"""
        if not self._connection or self._connection.closed:
            self._connection = psycopg2.connect(**self.connection_params)
            self._connection.autocommit = True
        return self._connection
    
    def index_document(self, document_id: str, user_id: int, title: str, content: str, metadata: Dict = None) -> bool:
        """Индексация документа для поиска"""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO search_data.search_index (document_id, user_id, title, content, metadata)
                    VALUES (%s::uuid, %s, %s, %s, %s)
                    ON CONFLICT (document_id) 
                    DO UPDATE SET 
                        title = EXCLUDED.title,
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                """, (document_id, user_id, title, content, json.dumps(metadata or {})))
                
                return True
        except Exception as e:
            print(f"Error indexing document: {e}")
            return False
    
    def search(self, user_id: int, query: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Поиск документов"""
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Записываем запрос в историю
                start_time = time.time()
                
                cursor.execute("""
                    SELECT document_id, title, content, metadata,
                           ts_rank(search_vector, plainto_tsquery('english', %s)) as rank
                    FROM search_data.search_index
                    WHERE user_id = %s
                    AND search_vector @@ plainto_tsquery('english', %s)
                    ORDER BY rank DESC
                    LIMIT %s OFFSET %s
                """, (query, user_id, query, limit, offset))
                
                results = cursor.fetchall()
                execution_time = int((time.time() - start_time) * 1000)
                
                # Записываем в историю поиска
                cursor.execute("""
                    INSERT INTO search_data.search_history (user_id, query_text, results_count, execution_time_ms)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, query, len(results), execution_time))
                
                return [dict(result) for result in results]
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    def search_by_title(self, user_id: int, title_query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Поиск по заголовку"""
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT document_id, title, content, metadata,
                           ts_rank(to_tsvector('english', title), plainto_tsquery('english', %s)) as rank
                    FROM search_data.search_index
                    WHERE user_id = %s
                    AND to_tsvector('english', title) @@ plainto_tsquery('english', %s)
                    ORDER BY rank DESC
                    LIMIT %s
                """, (title_query, user_id, title_query, limit))
                
                return [dict(result) for result in cursor.fetchall()]
        except Exception as e:
            print(f"Error searching by title: {e}")
            return []
    
    def get_search_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение истории поиска"""
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT query_text, results_count, execution_time_ms, created_at
                    FROM search_data.search_history
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (user_id, limit))
                
                return [dict(result) for result in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting search history: {e}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """Удаление документа из индекса"""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM search_data.search_index
                    WHERE document_id = %s::uuid
                """, (document_id,))
                
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
    
    def get_stats(self, user_id: int) -> Dict[str, Any]:
        """Получение статистики поиска"""
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Общая статистика
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_documents
                    FROM search_data.search_index
                    WHERE user_id = %s
                """, (user_id,))
                
                stats = dict(cursor.fetchone() or {})
                
                # Статистика поиска
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_searches,
                        AVG(execution_time_ms) as avg_execution_time,
                        MAX(execution_time_ms) as max_execution_time
                    FROM search_data.search_history
                    WHERE user_id = %s
                """, (user_id,))
                
                search_stats = dict(cursor.fetchone() or {})
                stats.update(search_stats)
                
                return stats
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
    
    def close(self):
        """Закрытие подключения"""
        if self._connection and not self._connection.closed:
            self._connection.close()


class TestPostgreSQLSearch:
    """Тесты полнотекстового поиска в PostgreSQL"""
    
    @pytest.fixture(scope="class")
    def search_client(self):
        """Клиент для работы с поиском"""
        connection_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5433')),
            'database': os.getenv('POSTGRES_DB', 'testdb'),
            'user': os.getenv('POSTGRES_USER', 'testuser'),
            'password': os.getenv('POSTGRES_PASSWORD', 'testpass')
        }
        
        search = PostgreSQLSearch(connection_params)
        
        # Очищаем индекс перед тестами
        conn = search._get_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM search_data.search_index")
            cursor.execute("DELETE FROM search_data.search_history")
        
        yield search
        
        # Очищаем индекс после тестов
        conn = search._get_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM search_data.search_index")
            cursor.execute("DELETE FROM search_data.search_history")
        
        search.close()
    
    def test_index_and_search_document(self, search_client):
        """Тест индексации и поиска документа"""
        doc_id = str(uuid.uuid4())
        
        # Индексируем документ
        assert search_client.index_document(
            document_id=doc_id,
            user_id=1,
            title="Integration Testing Guide",
            content="This is a comprehensive guide for integration testing with PostgreSQL and Python",
            metadata={"type": "guide", "author": "test_user"}
        ) is True
        
        # Ищем по содержимому
        results = search_client.search(user_id=1, query="integration testing")
        assert len(results) == 1
        assert results[0]['document_id'] == doc_id
        assert results[0]['title'] == "Integration Testing Guide"
        assert results[0]['rank'] > 0
        
        # Ищем по заголовку
        results = search_client.search(user_id=1, query="guide")
        assert len(results) == 1
        assert results[0]['document_id'] == doc_id
    
    def test_search_multiple_documents(self, search_client):
        """Тест поиска среди нескольких документов"""
        # Индексируем несколько документов
        documents = [
            {
                "document_id": str(uuid.uuid4()),
                "title": "Python Testing Best Practices",
                "content": "Best practices for testing Python applications with pytest and mock",
                "metadata": {"language": "python"}
            },
            {
                "document_id": str(uuid.uuid4()), 
                "title": "Database Integration Testing",
                "content": "How to test database integrations effectively using PostgreSQL",
                "metadata": {"database": "postgresql"}
            },
            {
                "document_id": str(uuid.uuid4()),
                "title": "API Testing Guide",
                "content": "Complete guide for testing REST APIs with FastAPI and pytest",
                "metadata": {"api": "fastapi"}
            }
        ]
        
        for doc in documents:
            assert search_client.index_document(
                document_id=doc["document_id"],
                user_id=1,
                title=doc["title"],
                content=doc["content"],
                metadata=doc["metadata"]
            ) is True
        
        # Поиск по общему термину
        results = search_client.search(user_id=1, query="testing")
        assert len(results) == 3
        
        # Поиск по специфичному термину
        results = search_client.search(user_id=1, query="postgresql")
        assert len(results) == 1
        assert results[0]['document_id'] == documents[1]["document_id"]
        
        # Поиск по API
        results = search_client.search(user_id=1, query="fastapi")
        assert len(results) == 1
        assert results[0]['document_id'] == documents[2]["document_id"]
    
    def test_search_ranking(self, search_client):
        """Тест ранжирования результатов поиска"""
        high_rel_id = str(uuid.uuid4())
        low_rel_id = str(uuid.uuid4())
        
        # Индексируем документы с разной релевантностью
        search_client.index_document(
            document_id=high_rel_id,
            user_id=1,
            title="PostgreSQL PostgreSQL PostgreSQL",
            content="PostgreSQL is the best database for PostgreSQL applications with PostgreSQL features",
            metadata={}
        )
        
        search_client.index_document(
            document_id=low_rel_id,
            user_id=1,
            title="Database Guide",
            content="This guide covers various databases including PostgreSQL among others",
            metadata={}
        )
        
        # Поиск должен вернуть документы в порядке релевантности
        results = search_client.search(user_id=1, query="postgresql")
        assert len(results) == 2
        
        # Первый результат должен быть более релевантным
        assert results[0]['document_id'] == high_rel_id
        assert results[0]['rank'] > results[1]['rank']
    
    def test_search_by_title(self, search_client):
        """Тест поиска по заголовку"""
        doc_id = str(uuid.uuid4())
        
        search_client.index_document(
            document_id=doc_id,
            user_id=1,
            title="Unique Title for Testing",
            content="This document has a unique title but common content",
            metadata={}
        )
        
        # Поиск по заголовку
        results = search_client.search_by_title(user_id=1, title_query="unique title")
        assert len(results) == 1
        assert results[0]['document_id'] == doc_id
        assert results[0]['rank'] > 0
    
    def test_search_user_isolation(self, search_client):
        """Тест изоляции поиска между пользователями"""
        user1_doc_id = str(uuid.uuid4())
        user2_doc_id = str(uuid.uuid4())
        
        # Индексируем документы для разных пользователей
        search_client.index_document(
            document_id=user1_doc_id,
            user_id=1,
            title="User 1 Document",
            content="This document belongs to user 1",
            metadata={}
        )
        
        search_client.index_document(
            document_id=user2_doc_id,
            user_id=2,
            title="User 2 Document", 
            content="This document belongs to user 2",
            metadata={}
        )
        
        # Пользователь 1 должен видеть только свои документы
        results = search_client.search(user_id=1, query="document")
        user1_docs = [r['document_id'] for r in results]
        assert user1_doc_id in user1_docs
        assert user2_doc_id not in user1_docs
        
        # Пользователь 2 должен видеть только свои документы
        results = search_client.search(user_id=2, query="document")
        user2_docs = [r['document_id'] for r in results]
        assert user2_doc_id in user2_docs
        assert user1_doc_id not in user2_docs
    
    def test_search_history(self, search_client):
        """Тест истории поиска"""
        doc_id = str(uuid.uuid4())
        
        # Индексируем документ
        search_client.index_document(
            document_id=doc_id,
            user_id=1,
            title="History Test Document",
            content="Document for testing search history functionality",
            metadata={}
        )
        
        # Выполняем несколько поисков
        search_client.search(user_id=1, query="history")
        search_client.search(user_id=1, query="test")
        search_client.search(user_id=1, query="document")
        
        # Проверяем историю поиска
        history = search_client.get_search_history(user_id=1, limit=5)
        assert len(history) >= 3
        
        # Проверяем что запросы записались
        queries = [h['query_text'] for h in history]
        assert "history" in queries
        assert "test" in queries
        assert "document" in queries
        
        # Проверяем что есть время выполнения
        for entry in history:
            assert entry['execution_time_ms'] >= 0
            assert entry['results_count'] >= 0
    
    def test_document_update(self, search_client):
        """Тест обновления документа в индексе"""
        doc_id = str(uuid.uuid4())
        
        # Индексируем документ
        search_client.index_document(
            document_id=doc_id,
            user_id=1,
            title="Original Title",
            content="Original content for testing updates",
            metadata={"version": 1}
        )
        
        # Проверяем что документ найден
        results = search_client.search(user_id=1, query="original")
        assert len(results) == 1
        assert results[0]['title'] == "Original Title"
        
        # Обновляем документ
        search_client.index_document(
            document_id=doc_id,
            user_id=1,
            title="Updated Title",
            content="Updated content for testing modifications",
            metadata={"version": 2}
        )
        
        # Проверяем что документ обновился
        results = search_client.search(user_id=1, query="updated")
        assert len(results) == 1
        assert results[0]['title'] == "Updated Title"
        
        # Старый контент не должен находиться
        results = search_client.search(user_id=1, query="original")
        assert len(results) == 0
    
    def test_document_deletion(self, search_client):
        """Тест удаления документа из индекса"""
        doc_id = str(uuid.uuid4())
        
        # Индексируем документ
        search_client.index_document(
            document_id=doc_id,
            user_id=1,
            title="Document to Delete",
            content="This document will be deleted from the search index",
            metadata={}
        )
        
        # Проверяем что документ найден
        results = search_client.search(user_id=1, query="delete")
        assert len(results) == 1
        
        # Удаляем документ
        assert search_client.delete_document(doc_id) is True
        
        # Проверяем что документ не найден
        results = search_client.search(user_id=1, query="delete")
        assert len(results) == 0
    
    def test_search_stats(self, search_client):
        """Тест статистики поиска"""
        # Индексируем несколько документов
        for i in range(3):
            search_client.index_document(
                document_id=str(uuid.uuid4()),
                user_id=1,
                title=f"Stats Document {i}",
                content=f"Content for statistics testing document {i}",
                metadata={"index": i}
            )
        
        # Выполняем поиски
        search_client.search(user_id=1, query="stats")
        search_client.search(user_id=1, query="document")
        
        # Получаем статистику
        stats = search_client.get_stats(user_id=1)
        
        assert stats['total_searches'] >= 2
        assert stats['avg_execution_time'] >= 0
        assert stats['max_execution_time'] >= 0
    
    def test_search_performance(self, search_client):
        """Тест производительности поиска"""
        doc_ids = []
        
        # Индексируем много документов
        for i in range(50):
            doc_id = str(uuid.uuid4())
            doc_ids.append(doc_id)
            search_client.index_document(
                document_id=doc_id,
                user_id=1,
                title=f"Performance Test Document {i}",
                content=f"This is document number {i} for performance testing with various keywords",
                metadata={"number": i}
            )
        
        # Тест скорости поиска
        start_time = time.time()
        results = search_client.search(user_id=1, query="performance testing")
        search_time = time.time() - start_time
        
        # Проверяем что поиск быстрый и находит документы
        assert len(results) > 0
        assert search_time < 1.0, f"Поиск занял {search_time:.2f}s (ожидалось < 1s)"
        
        # Очистка
        for doc_id in doc_ids:
            search_client.delete_document(doc_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 