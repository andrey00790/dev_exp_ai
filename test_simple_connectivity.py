#!/usr/bin/env python3
"""
Simple E2E Connectivity Tests
Проверяет базовое подключение к запущенным сервисам
"""

import pytest
import requests
import redis
import psycopg2
from elasticsearch import Elasticsearch
import logging

logger = logging.getLogger(__name__)

class TestE2EConnectivity:
    """Тесты базового подключения к E2E сервисам."""
    
    def test_elasticsearch_connection(self):
        """Тест подключения к Elasticsearch."""
        try:
            es = Elasticsearch(["http://localhost:9200"])
            health = es.cluster.health()
            
            assert health["status"] in ["green", "yellow"]
            logger.info(f"✅ Elasticsearch: {health['status']} status")
            
        except Exception as e:
            pytest.fail(f"Elasticsearch connection failed: {e}")
    
    def test_redis_connection(self):
        """Тест подключения к Redis."""
        try:
            r = redis.Redis(host="localhost", port=6379, db=0)
            r.ping()
            
            # Тест записи/чтения
            r.set("test_key", "test_value")
            value = r.get("test_key")
            assert value.decode() == "test_value"
            
            logger.info("✅ Redis: Connection and operations successful")
            
        except Exception as e:
            pytest.fail(f"Redis connection failed: {e}")
    
    def test_postgres_connection(self):
        """Тест подключения к PostgreSQL."""
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="atlassian",
                user="atlassian",
                password="atlassian"
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            
            assert "PostgreSQL" in version[0]
            logger.info(f"✅ PostgreSQL: {version[0][:50]}...")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            pytest.fail(f"PostgreSQL connection failed: {e}")
    
    def test_jira_status(self):
        """Тест статуса Jira."""
        try:
            response = requests.get("http://localhost:8080/status", timeout=10)
            assert response.status_code == 200
            
            status = response.json()
            logger.info(f"✅ Jira: Status {status.get('state', 'UNKNOWN')}")
            
        except Exception as e:
            pytest.fail(f"Jira status check failed: {e}")
    
    def test_confluence_status(self):
        """Тест статуса Confluence."""
        try:
            response = requests.get("http://localhost:8090/status", timeout=10)
            assert response.status_code == 200
            
            status = response.json()
            logger.info(f"✅ Confluence: Status {status.get('state', 'UNKNOWN')}")
            
        except Exception as e:
            pytest.fail(f"Confluence status check failed: {e}")
    
    def test_all_services_summary(self):
        """Сводка по всем сервисам."""
        ready_services = []
        
        # Elasticsearch
        try:
            es = Elasticsearch(["http://localhost:9200"])
            health = es.cluster.health()
            if health["status"] in ["green", "yellow"]:
                ready_services.append("Elasticsearch")
        except:
            pass
        
        # Redis
        try:
            r = redis.Redis(host="localhost", port=6379, db=0)
            r.ping()
            ready_services.append("Redis")
        except:
            pass
        
        # PostgreSQL
        try:
            conn = psycopg2.connect(
                host="localhost", port=5432, database="atlassian",
                user="atlassian", password="atlassian"
            )
            conn.close()
            ready_services.append("PostgreSQL")
        except:
            pass
        
        # Jira
        try:
            response = requests.get("http://localhost:8080/status", timeout=5)
            if response.status_code == 200:
                ready_services.append("Jira")
        except:
            pass
        
        # Confluence
        try:
            response = requests.get("http://localhost:8090/status", timeout=5)
            if response.status_code == 200:
                ready_services.append("Confluence")
        except:
            pass
        
        # GitLab
        try:
            response = requests.get("http://localhost:8088/-/health", timeout=5)
            if response.status_code == 200:
                ready_services.append("GitLab")
        except:
            pass
        
        logger.info(f"🎯 Ready services: {len(ready_services)}/6")
        logger.info(f"✅ Services ready: {', '.join(ready_services)}")
        
        # Минимум 3 сервиса должны быть готовы для базовых тестов
        assert len(ready_services) >= 3, f"Not enough services ready: {ready_services}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 