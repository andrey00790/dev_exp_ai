#!/usr/bin/env python3
"""
Интеграционные тесты для Qdrant векторного поиска
"""

import pytest
import requests
import json
import time
import os
import numpy as np
from typing import Dict, Any, List, Optional
import uuid

pytestmark = pytest.mark.integration

class QdrantClient:
    """Клиент для работы с Qdrant"""
    
    def __init__(self, url: str):
        self.url = url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья Qdrant"""
        try:
            response = self.session.get(f"{self.url}/")
            response.raise_for_status()
            data = response.json()
            # Qdrant возвращает {"title": "qdrant - vector search engine", "version": "1.7.4"}
            if "title" in data and "qdrant" in data["title"]:
                return {"status": "ok", "version": data.get("version")}
            return {"status": "unhealthy", "error": "Invalid response"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def create_collection(self, collection_name: str, vector_size: int = 1536) -> bool:
        """Создание коллекции"""
        try:
            payload = {
                "vectors": {
                    "size": vector_size,
                    "distance": "Cosine"
                }
            }
            
            response = self.session.put(
                f"{self.url}/collections/{collection_name}",
                json=payload
            )
            
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error creating collection: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Удаление коллекции"""
        try:
            response = self.session.delete(f"{self.url}/collections/{collection_name}")
            return response.status_code in [200, 404]  # 404 если уже не существует
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """Список коллекций"""
        try:
            response = self.session.get(f"{self.url}/collections")
            response.raise_for_status()
            data = response.json()
            return [col["name"] for col in data.get("result", {}).get("collections", [])]
        except Exception as e:
            print(f"Error listing collections: {e}")
            return []
    
    def upsert_points(self, collection_name: str, points: List[Dict[str, Any]]) -> bool:
        """Добавление/обновление точек"""
        try:
            payload = {"points": points}
            
            response = self.session.put(
                f"{self.url}/collections/{collection_name}/points",
                json=payload
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"Error upserting points: {e}")
            return False
    
    def search_points(self, collection_name: str, vector: List[float], limit: int = 10, 
                     filter_conditions: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Поиск похожих точек"""
        try:
            payload = {
                "vector": vector,
                "limit": limit,
                "with_payload": True,
                "with_vector": False
            }
            
            if filter_conditions:
                payload["filter"] = filter_conditions
            
            response = self.session.post(
                f"{self.url}/collections/{collection_name}/points/search",
                json=payload
            )
            
            if response.status_code == 200:
                return response.json().get("result", [])
            return []
        except Exception as e:
            print(f"Error searching points: {e}")
            return []
    
    def get_point(self, collection_name: str, point_id: str) -> Optional[Dict[str, Any]]:
        """Получение точки по ID"""
        try:
            response = self.session.get(
                f"{self.url}/collections/{collection_name}/points/{point_id}"
            )
            
            if response.status_code == 200:
                return response.json().get("result")
            return None
        except Exception as e:
            print(f"Error getting point: {e}")
            return None
    
    def delete_points(self, collection_name: str, point_ids: List[str]) -> bool:
        """Удаление точек"""
        try:
            payload = {"points": point_ids}
            
            response = self.session.post(
                f"{self.url}/collections/{collection_name}/points/delete",
                json=payload
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"Error deleting points: {e}")
            return False
    
    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Информация о коллекции"""
        try:
            response = self.session.get(f"{self.url}/collections/{collection_name}")
            
            if response.status_code == 200:
                return response.json().get("result")
            return None
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return None


def generate_random_vector(size: int = 1536) -> List[float]:
    """Генерация случайного вектора"""
    return np.random.random(size).tolist()


class TestQdrantIntegration:
    """Интеграционные тесты Qdrant"""
    
    @pytest.fixture(scope="class")
    def qdrant_client(self):
        """Клиент Qdrant"""
        url = f"http://{os.getenv('QDRANT_HOST', 'localhost')}:{os.getenv('QDRANT_PORT', '6334')}"
        client = QdrantClient(url)
        
        # Проверяем подключение
        health = client.health_check()
        if health.get("status") != "ok":
            pytest.skip(f"Qdrant не доступен: {health}")
        
        yield client
    
    @pytest.fixture
    def test_collection(self, qdrant_client):
        """Тестовая коллекция"""
        collection_name = f"test_collection_{uuid.uuid4().hex[:8]}"
        
        # Создаем коллекцию
        assert qdrant_client.create_collection(collection_name) is True
        
        yield collection_name
        
        # Удаляем коллекцию после теста
        qdrant_client.delete_collection(collection_name)
    
    def test_qdrant_health_check(self, qdrant_client):
        """Тест проверки здоровья Qdrant"""
        health = qdrant_client.health_check()
        assert health.get("status") == "ok"
    
    def test_create_and_delete_collection(self, qdrant_client):
        """Тест создания и удаления коллекции"""
        collection_name = f"temp_collection_{uuid.uuid4().hex[:8]}"
        
        # Создаем коллекцию
        assert qdrant_client.create_collection(collection_name) is True
        
        # Проверяем что коллекция создалась
        collections = qdrant_client.list_collections()
        assert collection_name in collections
        
        # Получаем информацию о коллекции
        info = qdrant_client.get_collection_info(collection_name)
        assert info is not None
        assert info["config"]["params"]["vectors"]["size"] == 1536
        assert info["config"]["params"]["vectors"]["distance"] == "Cosine"
        
        # Удаляем коллекцию
        assert qdrant_client.delete_collection(collection_name) is True
        
        # Проверяем что коллекция удалилась
        collections = qdrant_client.list_collections()
        assert collection_name not in collections
    
    def test_upsert_and_get_points(self, qdrant_client, test_collection):
        """Тест добавления и получения точек"""
        # Подготавливаем точки
        points = [
            {
                "id": "point1",
                "vector": generate_random_vector(),
                "payload": {
                    "title": "Test Document 1",
                    "content": "This is the first test document",
                    "user_id": 1,
                    "doc_type": "test"
                }
            },
            {
                "id": "point2", 
                "vector": generate_random_vector(),
                "payload": {
                    "title": "Test Document 2",
                    "content": "This is the second test document",
                    "user_id": 1,
                    "doc_type": "test"
                }
            }
        ]
        
        # Добавляем точки
        assert qdrant_client.upsert_points(test_collection, points) is True
        
        # Ждем индексации
        time.sleep(1)
        
        # Получаем точки
        point1 = qdrant_client.get_point(test_collection, "point1")
        assert point1 is not None
        assert point1["payload"]["title"] == "Test Document 1"
        assert point1["payload"]["user_id"] == 1
        
        point2 = qdrant_client.get_point(test_collection, "point2")
        assert point2 is not None
        assert point2["payload"]["title"] == "Test Document 2"
    
    def test_vector_search(self, qdrant_client, test_collection):
        """Тест векторного поиска"""
        # Создаем точки с известными векторами
        base_vector = [0.1] * 1536
        similar_vector = [0.11] * 1536  # Похожий вектор
        different_vector = [0.9] * 1536  # Отличающийся вектор
        
        points = [
            {
                "id": "base_doc",
                "vector": base_vector,
                "payload": {"title": "Base Document", "category": "base"}
            },
            {
                "id": "similar_doc",
                "vector": similar_vector,
                "payload": {"title": "Similar Document", "category": "similar"}
            },
            {
                "id": "different_doc",
                "vector": different_vector,
                "payload": {"title": "Different Document", "category": "different"}
            }
        ]
        
        # Добавляем точки
        assert qdrant_client.upsert_points(test_collection, points) is True
        time.sleep(1)
        
        # Ищем похожие на base_vector
        results = qdrant_client.search_points(test_collection, base_vector, limit=3)
        
        assert len(results) == 3
        
        # Проверяем порядок по релевантности
        assert results[0]["id"] == "base_doc"  # Самый похожий (идентичный)
        assert results[1]["id"] == "similar_doc"  # Второй по похожести
        assert results[2]["id"] == "different_doc"  # Наименее похожий
        
        # Проверяем что скоры убывают
        assert results[0]["score"] >= results[1]["score"]
        assert results[1]["score"] >= results[2]["score"]
    
    def test_filtered_search(self, qdrant_client, test_collection):
        """Тест поиска с фильтрами"""
        # Создаем точки с разными пользователями
        points = [
            {
                "id": "user1_doc1",
                "vector": generate_random_vector(),
                "payload": {"title": "User 1 Doc 1", "user_id": 1, "category": "work"}
            },
            {
                "id": "user1_doc2",
                "vector": generate_random_vector(),
                "payload": {"title": "User 1 Doc 2", "user_id": 1, "category": "personal"}
            },
            {
                "id": "user2_doc1",
                "vector": generate_random_vector(),
                "payload": {"title": "User 2 Doc 1", "user_id": 2, "category": "work"}
            }
        ]
        
        assert qdrant_client.upsert_points(test_collection, points) is True
        time.sleep(1)
        
        # Поиск только для пользователя 1
        filter_user1 = {
            "must": [
                {"key": "user_id", "match": {"value": 1}}
            ]
        }
        
        results = qdrant_client.search_points(
            test_collection, 
            generate_random_vector(), 
            limit=10,
            filter_conditions=filter_user1
        )
        
        assert len(results) == 2
        for result in results:
            assert result["payload"]["user_id"] == 1
        
        # Поиск по категории "work"
        filter_work = {
            "must": [
                {"key": "category", "match": {"value": "work"}}
            ]
        }
        
        results = qdrant_client.search_points(
            test_collection,
            generate_random_vector(),
            limit=10,
            filter_conditions=filter_work
        )
        
        assert len(results) == 2
        for result in results:
            assert result["payload"]["category"] == "work"
    
    def test_update_points(self, qdrant_client, test_collection):
        """Тест обновления точек"""
        # Создаем точку
        original_point = {
            "id": "update_test",
            "vector": generate_random_vector(),
            "payload": {"title": "Original Title", "version": 1}
        }
        
        assert qdrant_client.upsert_points(test_collection, [original_point]) is True
        time.sleep(1)
        
        # Проверяем исходную точку
        point = qdrant_client.get_point(test_collection, "update_test")
        assert point["payload"]["title"] == "Original Title"
        assert point["payload"]["version"] == 1
        
        # Обновляем точку
        updated_point = {
            "id": "update_test",
            "vector": generate_random_vector(),
            "payload": {"title": "Updated Title", "version": 2}
        }
        
        assert qdrant_client.upsert_points(test_collection, [updated_point]) is True
        time.sleep(1)
        
        # Проверяем обновленную точку
        point = qdrant_client.get_point(test_collection, "update_test")
        assert point["payload"]["title"] == "Updated Title"
        assert point["payload"]["version"] == 2
    
    def test_delete_points(self, qdrant_client, test_collection):
        """Тест удаления точек"""
        # Создаем точки
        points = [
            {
                "id": "delete_test1",
                "vector": generate_random_vector(),
                "payload": {"title": "Delete Test 1"}
            },
            {
                "id": "delete_test2",
                "vector": generate_random_vector(),
                "payload": {"title": "Delete Test 2"}
            },
            {
                "id": "keep_test",
                "vector": generate_random_vector(),
                "payload": {"title": "Keep Test"}
            }
        ]
        
        assert qdrant_client.upsert_points(test_collection, points) is True
        time.sleep(1)
        
        # Проверяем что все точки существуют
        assert qdrant_client.get_point(test_collection, "delete_test1") is not None
        assert qdrant_client.get_point(test_collection, "delete_test2") is not None
        assert qdrant_client.get_point(test_collection, "keep_test") is not None
        
        # Удаляем две точки
        assert qdrant_client.delete_points(test_collection, ["delete_test1", "delete_test2"]) is True
        time.sleep(1)
        
        # Проверяем результат удаления
        assert qdrant_client.get_point(test_collection, "delete_test1") is None
        assert qdrant_client.get_point(test_collection, "delete_test2") is None
        assert qdrant_client.get_point(test_collection, "keep_test") is not None
    
    def test_large_batch_operations(self, qdrant_client, test_collection):
        """Тест операций с большими батчами"""
        # Создаем много точек
        batch_size = 100
        points = []
        
        for i in range(batch_size):
            points.append({
                "id": f"batch_point_{i}",
                "vector": generate_random_vector(),
                "payload": {
                    "title": f"Batch Document {i}",
                    "index": i,
                    "batch": "large_test"
                }
            })
        
        # Добавляем батч
        start_time = time.time()
        assert qdrant_client.upsert_points(test_collection, points) is True
        upsert_time = time.time() - start_time
        
        time.sleep(2)  # Ждем индексации
        
        # Проверяем что все точки добавились
        info = qdrant_client.get_collection_info(test_collection)
        assert info["points_count"] >= batch_size
        
        # Тест поиска в большой коллекции
        start_time = time.time()
        results = qdrant_client.search_points(test_collection, generate_random_vector(), limit=10)
        search_time = time.time() - start_time
        
        assert len(results) == 10
        
        # Проверяем производительность
        assert upsert_time < 10.0, f"Добавление {batch_size} точек заняло {upsert_time:.2f}s"
        assert search_time < 1.0, f"Поиск занял {search_time:.2f}s"
        
        # Удаляем батч
        point_ids = [f"batch_point_{i}" for i in range(batch_size)]
        assert qdrant_client.delete_points(test_collection, point_ids) is True
    
    def test_collection_statistics(self, qdrant_client, test_collection):
        """Тест статистики коллекции"""
        # Добавляем несколько точек
        points = [
            {
                "id": f"stats_point_{i}",
                "vector": generate_random_vector(),
                "payload": {"index": i, "type": "stats_test"}
            }
            for i in range(10)
        ]
        
        assert qdrant_client.upsert_points(test_collection, points) is True
        time.sleep(1)
        
        # Получаем информацию о коллекции
        info = qdrant_client.get_collection_info(test_collection)
        
        assert info is not None
        assert info["points_count"] >= 10
        assert info["status"] == "green"
        assert "vectors_count" in info
        
        # Проверяем конфигурацию
        config = info["config"]
        assert config["params"]["vectors"]["size"] == 1536
        assert config["params"]["vectors"]["distance"] == "Cosine"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 