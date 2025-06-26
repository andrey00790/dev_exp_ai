#!/usr/bin/env python3
"""
Финальная версия интеграционных тестов для Qdrant
"""

import pytest
import requests
import json
import time
import os
import numpy as np
from typing import Dict, Any, List, Optional, Union
import uuid

pytestmark = pytest.mark.integration

class QdrantClient:
    """Клиент для работы с Qdrant"""
    
    def __init__(self, url: str, timeout: int = 5):
        self.url = url.rstrip('/')
        self.session = requests.Session()
        self.timeout = timeout
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def health_check(self) -> Dict[str, Any]:
        try:
            response = self.session.get(f"{self.url}/", timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            if "title" in data and "qdrant" in data["title"]:
                return {"status": "ok", "version": data.get("version")}
            return {"status": "unhealthy", "error": "Invalid response"}
        except requests.exceptions.Timeout:
            return {"status": "unhealthy", "error": "Timeout"}
        except requests.exceptions.ConnectionError:
            return {"status": "unhealthy", "error": "Connection refused"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def create_collection(self, collection_name: str, vector_size: int = 1536) -> bool:
        try:
            payload = {"vectors": {"size": vector_size, "distance": "Cosine"}}
            response = self.session.put(f"{self.url}/collections/{collection_name}", json=payload, timeout=self.timeout)
            return response.status_code in [200, 201]
        except:
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        try:
            response = self.session.delete(f"{self.url}/collections/{collection_name}", timeout=self.timeout)
            return response.status_code in [200, 404]
        except:
            return False
    
    def list_collections(self) -> List[str]:
        try:
            response = self.session.get(f"{self.url}/collections", timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return [col["name"] for col in data.get("result", {}).get("collections", [])]
        except:
            return []
    
    def upsert_points(self, collection_name: str, points: List[Dict[str, Any]]) -> bool:
        try:
            if not points:
                return True
            payload = {"points": points}
            response = self.session.put(f"{self.url}/collections/{collection_name}/points", json=payload, timeout=self.timeout)
            return response.status_code in [200, 202]
        except:
            return False
    
    def search_points(self, collection_name: str, vector: List[float], limit: int = 10, filter_conditions: Optional[Dict] = None) -> List[Dict[str, Any]]:
        try:
            payload = {"vector": vector, "limit": limit, "with_payload": True, "with_vector": False}
            if filter_conditions:
                payload["filter"] = filter_conditions
            response = self.session.post(f"{self.url}/collections/{collection_name}/points/search", json=payload, timeout=self.timeout)
            if response.status_code == 200:
                return response.json().get("result", [])
            return []
        except:
            return []
    
    def get_point(self, collection_name: str, point_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        try:
            response = self.session.get(f"{self.url}/collections/{collection_name}/points/{point_id}", timeout=self.timeout)
            if response.status_code == 200:
                return response.json().get("result")
            return None
        except:
            return None
    
    def delete_points(self, collection_name: str, point_ids: List[Union[str, int]]) -> bool:
        try:
            payload = {"points": point_ids}
            response = self.session.post(f"{self.url}/collections/{collection_name}/points/delete", json=payload, timeout=self.timeout)
            return response.status_code == 200
        except:
            return False
    
    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.session.get(f"{self.url}/collections/{collection_name}", timeout=self.timeout)
            if response.status_code == 200:
                return response.json().get("result")
            return None
        except:
            return None


def generate_random_vector(size: int = 4) -> List[float]:
    return np.random.random(size).tolist()


class TestQdrantIntegration:
    
    @pytest.fixture(scope="class")
    def qdrant_client(self):
        url = f"http://{os.getenv('QDRANT_HOST', 'localhost')}:{os.getenv('QDRANT_PORT', '6333')}"
        client = QdrantClient(url, timeout=10)
        health = client.health_check()
        if health.get("status") != "ok":
            pytest.skip(f"Qdrant не доступен: {health}")
        yield client
    
    @pytest.fixture
    def test_collection(self, qdrant_client):
        collection_name = f"test_collection_{uuid.uuid4().hex[:8]}"
        try:
            result = qdrant_client.create_collection(collection_name, vector_size=4)
            if not result:
                pytest.skip(f"Не удалось создать коллекцию {collection_name}")
            time.sleep(2)
        except Exception as e:
            pytest.skip(f"Ошибка создания коллекции: {e}")
        yield collection_name
        try:
            qdrant_client.delete_collection(collection_name)
        except:
            pass
    
    def test_qdrant_health_check(self, qdrant_client):
        health = qdrant_client.health_check()
        assert health.get("status") == "ok"
    
    def test_create_and_delete_collection(self, qdrant_client):
        collection_name = f"temp_collection_{uuid.uuid4().hex[:8]}"
        assert qdrant_client.create_collection(collection_name, vector_size=4) is True
        collections = qdrant_client.list_collections()
        assert collection_name in collections
        info = qdrant_client.get_collection_info(collection_name)
        assert info is not None
        assert info["config"]["params"]["vectors"]["size"] == 4
        assert qdrant_client.delete_collection(collection_name) is True
        collections = qdrant_client.list_collections()
        assert collection_name not in collections
    
    def test_upsert_and_get_points(self, qdrant_client, test_collection):
        points = [
            {"id": 1, "vector": generate_random_vector(), "payload": {"title": "Test Doc 1", "user_id": 1}},
            {"id": 2, "vector": generate_random_vector(), "payload": {"title": "Test Doc 2", "user_id": 1}}
        ]
        assert qdrant_client.upsert_points(test_collection, points) is True
        time.sleep(1)
        point1 = qdrant_client.get_point(test_collection, 1)
        assert point1 is not None
        assert point1["payload"]["title"] == "Test Doc 1"
        point2 = qdrant_client.get_point(test_collection, 2)
        assert point2 is not None
        assert point2["payload"]["title"] == "Test Doc 2"
    
    def test_vector_search(self, qdrant_client, test_collection):
        # Простой тест векторного поиска без жёстких требований к скорам
        points = [
            {"id": 101, "vector": [0.1, 0.2, 0.3, 0.4], "payload": {"title": "Doc 1"}},
            {"id": 102, "vector": [0.2, 0.3, 0.4, 0.5], "payload": {"title": "Doc 2"}},
            {"id": 103, "vector": [0.9, 0.8, 0.7, 0.6], "payload": {"title": "Doc 3"}}
        ]
        assert qdrant_client.upsert_points(test_collection, points) is True
        time.sleep(1)
        
        results = qdrant_client.search_points(test_collection, [0.1, 0.2, 0.3, 0.4], limit=3)
        assert len(results) == 3
        
        # Проверяем что все ID присутствуют
        result_ids = [result["id"] for result in results]
        assert 101 in result_ids
        assert 102 in result_ids
        assert 103 in result_ids
        
        # Проверяем что все имеют положительные скоры
        for result in results:
            assert result["score"] > 0
    
    def test_filtered_search(self, qdrant_client, test_collection):
        points = [
            {"id": 201, "vector": generate_random_vector(), "payload": {"user_id": 1, "category": "work"}},
            {"id": 202, "vector": generate_random_vector(), "payload": {"user_id": 1, "category": "personal"}},
            {"id": 203, "vector": generate_random_vector(), "payload": {"user_id": 2, "category": "work"}}
        ]
        assert qdrant_client.upsert_points(test_collection, points) is True
        time.sleep(1)
        
        filter_user1 = {"must": [{"key": "user_id", "match": {"value": 1}}]}
        results = qdrant_client.search_points(test_collection, generate_random_vector(), limit=10, filter_conditions=filter_user1)
        assert len(results) == 2
        for result in results:
            assert result["payload"]["user_id"] == 1
    
    def test_update_points(self, qdrant_client, test_collection):
        original_point = {"id": 301, "vector": generate_random_vector(), "payload": {"title": "Original", "version": 1}}
        assert qdrant_client.upsert_points(test_collection, [original_point]) is True
        time.sleep(1)
        
        point = qdrant_client.get_point(test_collection, 301)
        assert point["payload"]["title"] == "Original"
        
        updated_point = {"id": 301, "vector": generate_random_vector(), "payload": {"title": "Updated", "version": 2}}
        assert qdrant_client.upsert_points(test_collection, [updated_point]) is True
        time.sleep(1)
        
        point = qdrant_client.get_point(test_collection, 301)
        assert point["payload"]["title"] == "Updated"
    
    def test_delete_points(self, qdrant_client, test_collection):
        points = [
            {"id": 401, "vector": generate_random_vector(), "payload": {"title": "Delete 1"}},
            {"id": 402, "vector": generate_random_vector(), "payload": {"title": "Delete 2"}},
            {"id": 403, "vector": generate_random_vector(), "payload": {"title": "Keep"}}
        ]
        assert qdrant_client.upsert_points(test_collection, points) is True
        time.sleep(1)
        
        assert qdrant_client.get_point(test_collection, 401) is not None
        assert qdrant_client.delete_points(test_collection, [401, 402]) is True
        time.sleep(1)
        
        assert qdrant_client.get_point(test_collection, 401) is None
        assert qdrant_client.get_point(test_collection, 403) is not None
    
    def test_large_batch_operations(self, qdrant_client, test_collection):
        batch_size = 30
        points = []
        for i in range(batch_size):
            points.append({"id": 500 + i, "vector": generate_random_vector(), "payload": {"index": i}})
        
        start_time = time.time()
        assert qdrant_client.upsert_points(test_collection, points) is True
        upsert_time = time.time() - start_time
        time.sleep(2)
        
        info = qdrant_client.get_collection_info(test_collection)
        assert info["points_count"] >= batch_size
        
        results = qdrant_client.search_points(test_collection, generate_random_vector(), limit=10)
        assert len(results) == 10
        assert upsert_time < 10.0
    
    def test_collection_statistics(self, qdrant_client, test_collection):
        points = [{"id": 600 + i, "vector": generate_random_vector(), "payload": {"index": i}} for i in range(10)]
        assert qdrant_client.upsert_points(test_collection, points) is True
        time.sleep(1)
        
        info = qdrant_client.get_collection_info(test_collection)
        assert info is not None
        assert info["points_count"] >= 10
        assert info["status"] == "green"
        assert info["config"]["params"]["vectors"]["size"] == 4
