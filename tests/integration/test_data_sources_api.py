#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_data_sources_api.py

Интеграционные тесты для API источников данных.
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
import tempfile
import json
from pathlib import Path
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from app.main import app


@pytest.fixture
def temp_bootstrap_dir():
    """Временная папка с тестовыми bootstrap материалами"""
    with tempfile.TemporaryDirectory() as temp_dir:
        bootstrap_path = Path(temp_dir) / "bootstrap"
        bootstrap_path.mkdir()
        
        # Создаем тестовые файлы и метаданные
        academic_dir = bootstrap_path / "academic"
        academic_dir.mkdir()
        
        # Тестовый текстовый файл
        test_file = academic_dir / "test_academic_resource.txt"
        test_file.write_text("This is a test academic resource about system design.")
        
        # Метаданные для файла
        metadata_file = academic_dir / "test_academic_resource.json"
        metadata = {
            "name": "Test Academic Resource",
            "category": "academic",
            "role": "All",
            "url": "https://example.com/test-resource",
            "downloaded_at": "2025-06-22T19:00:00",
            "file_path": str(test_file),
            "file_size": test_file.stat().st_size,
            "url_type": "webpage",
            "strategy": "webpage"
        }
        metadata_file.write_text(json.dumps(metadata, indent=2))
        
        # Статистика загрузки
        stats_file = bootstrap_path / "download_stats.json"
        stats = {
            "total": 1,
            "downloaded": 1,
            "skipped": 0,
            "failed": 0,
            "sources": {
                "academic": {"count": 1, "downloaded": 1}
            }
        }
        stats_file.write_text(json.dumps(stats, indent=2))
        
        yield str(bootstrap_path)


class TestDataSourcesAPI:
    """Тесты API источников данных"""
    
    @pytest.fixture
    def client(self):
        """Фикстура клиента FastAPI"""
        return TestClient(app)
    
    @pytest.fixture
    async def async_client(self):
        """Фикстура асинхронного клиента"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    def test_get_data_sources(self, client):
        """Тест получения списка источников данных"""
        response = client.get("/api/v1/data-sources/sources")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Проверяем что есть bootstrap источник
        bootstrap_sources = [s for s in data if s["source_type"] == "bootstrap"]
        assert len(bootstrap_sources) > 0
        
        # Проверяем структуру данных
        for source in data:
            assert "source_type" in source
            assert "enabled" in source
            assert "priority" in source
            assert isinstance(source["enabled"], bool)
            assert isinstance(source["priority"], int)
    
    def test_get_data_sources_filtered(self, client):
        """Тест фильтрации источников по типу"""
        # Фильтруем только bootstrap источники
        response = client.get("/api/v1/data-sources/sources?source_type=bootstrap")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Все источники должны быть bootstrap
        for source in data:
            assert source["source_type"] == "bootstrap"
    
    def test_get_source_filters(self, client):
        """Тест получения доступных фильтров"""
        response = client.get("/api/v1/data-sources/filters")
        assert response.status_code == 200
        
        data = response.json()
        assert "source_types" in data
        assert "categories" in data
        assert "roles" in data
        
        assert isinstance(data["source_types"], list)
        assert isinstance(data["categories"], list)
        assert isinstance(data["roles"], list)
        
        # Проверяем что bootstrap есть в типах источников
        assert "bootstrap" in data["source_types"]
    
    def test_discover_sources(self, client, temp_bootstrap_dir):
        """Тест автообнаружения источников"""
        response = client.get(f"/api/v1/data-sources/discover?bootstrap_dir={temp_bootstrap_dir}")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_sources" in data
        assert "sources_by_type" in data
        assert "sources_by_category" in data
        assert "discovered_sources" in data
        
        assert data["total_sources"] > 0
        assert "bootstrap" in data["sources_by_type"]
        assert "academic" in data["sources_by_category"]
        
        # Проверяем структуру обнаруженных источников
        sources = data["discovered_sources"]
        assert len(sources) > 0
        
        for source in sources:
            assert "name" in source
            assert "category" in source
            assert source["category"] == "academic"
    
    def test_discover_sources_with_filter(self, client, temp_bootstrap_dir):
        """Тест автообнаружения с фильтрацией"""
        response = client.get(f"/api/v1/data-sources/discover?bootstrap_dir={temp_bootstrap_dir}&category=academic")
        assert response.status_code == 200
        
        data = response.json()
        sources = data["discovered_sources"]
        
        # Все источники должны быть academic категории
        for source in sources:
            assert source["category"] == "academic"
    
    def test_get_bootstrap_stats(self, client, temp_bootstrap_dir):
        """Тест получения статистики bootstrap материалов"""
        response = client.get(f"/api/v1/data-sources/bootstrap/stats?bootstrap_dir={temp_bootstrap_dir}")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_files" in data
        assert "total_size_mb" in data
        assert "categories" in data
        assert "last_updated" in data
        
        assert data["total_files"] > 0
        assert data["total_size_mb"] >= 0  # Может быть 0.0 для очень маленьких файлов
        assert "academic" in data["categories"]
        assert data["categories"]["academic"] > 0
    
    def test_get_bootstrap_stats_nonexistent_dir(self, client):
        """Тест статистики для несуществующей папки"""
        response = client.get("/api/v1/data-sources/bootstrap/stats?bootstrap_dir=/nonexistent/path")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "не найдена" in data["detail"]
    
    def test_health_check(self, client):
        """Тест проверки здоровья модуля"""
        response = client.get("/api/v1/data-sources/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "sources_registered" in data
        assert "timestamp" in data
        
        assert data["status"] in ["healthy", "unhealthy"]
        assert isinstance(data["sources_registered"], int)
    
    def test_trigger_ingestion_unsupported_type(self, client):
        """Тест запуска ingestion для неподдерживаемого типа"""
        response = client.post("/api/v1/data-sources/ingest/unsupported_type")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "не поддерживается" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_async_discover_sources(self, temp_bootstrap_dir):
        """Асинхронный тест автообнаружения источников"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/data-sources/discover?bootstrap_dir={temp_bootstrap_dir}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["total_sources"] > 0
            assert "discovered_sources" in data
    
    def test_api_error_handling(self, client):
        """Тест обработки ошибок API"""
        # Тест с некорректным параметром
        response = client.get("/api/v1/data-sources/discover?bootstrap_dir=")
        # API должен обрабатывать пустой путь gracefully
        assert response.status_code in [200, 404, 500]
    
    def test_api_parameter_validation(self, client):
        """Тест валидации параметров API"""
        # Тест булевого параметра
        response = client.get("/api/v1/data-sources/sources?enabled_only=true")
        assert response.status_code == 200
        
        response = client.get("/api/v1/data-sources/sources?enabled_only=false")
        assert response.status_code == 200
        
        # Тест фильтрации по типу источника
        response = client.get("/api/v1/data-sources/sources?source_type=bootstrap")
        assert response.status_code == 200
        
        response = client.get("/api/v1/data-sources/sources?source_type=confluence")
        assert response.status_code == 200


@pytest.mark.integration
class TestDataSourcesIntegration:
    """Интеграционные тесты с реальными данными"""
    
    @pytest.fixture
    def client(self):
        """Фикстура клиента FastAPI"""
        return TestClient(app)
    
    def test_integration_with_real_bootstrap_data(self, client):
        """Тест интеграции с реальными bootstrap данными"""
        # Используем реальную папку bootstrap если она есть
        bootstrap_path = Path("local/bootstrap")
        if not bootstrap_path.exists():
            pytest.skip("Реальная папка bootstrap не найдена")
        
        response = client.get(f"/api/v1/data-sources/bootstrap/stats?bootstrap_dir={bootstrap_path}")
        assert response.status_code == 200
        
        data = response.json()
        if data["total_files"] > 0:
            assert data["total_size_mb"] > 0
            assert len(data["categories"]) > 0
    
    def test_api_performance(self, client, temp_bootstrap_dir):
        """Тест производительности API"""
        import time
        
        start_time = time.time()
        response = client.get(f"/api/v1/data-sources/discover?bootstrap_dir={temp_bootstrap_dir}")
        end_time = time.time()
        
        assert response.status_code == 200
        
        # API должен отвечать быстро (менее 5 секунд)
        assert (end_time - start_time) < 5.0
    
    def test_concurrent_requests(self, client, temp_bootstrap_dir):
        """Тест конкурентных запросов к API"""
        import concurrent.futures
        import threading
        
        def make_request():
            response = client.get(f"/api/v1/data-sources/discover?bootstrap_dir={temp_bootstrap_dir}")
            return response.status_code == 200
        
        # Делаем несколько конкурентных запросов
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request) for _ in range(3)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Все запросы должны быть успешными
        assert all(results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 