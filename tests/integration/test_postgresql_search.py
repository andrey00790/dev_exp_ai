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
                # Удаляем существующий документ если есть
                cursor.execute("""
                    DELETE FROM search_data.search_index WHERE document_id = %s::uuid
                """, (document_id,))
                
                # Добавляем новый документ
                cursor.execute("""
                    INSERT INTO search_data.search_index (document_id, user_id, title, content, metadata)
                    VALUES (%s::uuid, %s, %s, %s, %s)
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
    
    def close(self):
        """Закрытие подключения"""
        if self._connection and not self._connection.closed:
            self._connection.close()


class TestPostgreSQLSearch:
    """Тесты полнотекстового поиска в PostgreSQL"""
    
    @pytest.fixture(scope="function")
    def search_client(self):
        """Клиент для работы с поиском"""
        connection_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB', 'ai_assistant'),
            'user': os.getenv('POSTGRES_USER', 'ai_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'ai_password_dev')
        }
        
        search = PostgreSQLSearch(connection_params)
        
        # Очищаем индекс перед каждым тестом
        conn = search._get_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM search_data.search_index")
            cursor.execute("DELETE FROM search_data.search_history")
        
        yield search
        
        # Очищаем индекс после каждого теста
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
    
    def test_search_performance(self, search_client):
        """Тест производительности поиска"""
        doc_ids = []
        
        # Индексируем много документов
        for i in range(20):  # Уменьшаем количество для быстроты
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