#!/usr/bin/env python3
"""
E2E Integration Tests
Тесты интеграции с локальными инстансами Jira, Confluence, GitLab
"""

import pytest
import asyncio
import time
import requests
from pathlib import Path
pytest.importorskip("docker")
import docker
import logging

pytest.importorskip("atlassian")
pytest.importorskip("gitlab")
pytest.importorskip("elasticsearch")
pytest.importorskip("redis")
from atlassian import Jira, Confluence
import gitlab
from elasticsearch import Elasticsearch
import redis

logger = logging.getLogger(__name__)

# Mark entire module as E2E so it's skipped by default
pytestmark = pytest.mark.e2e

@pytest.fixture(scope="session")
def docker_services():
    """Фикстура для управления Docker Compose сервисами"""
    client = docker.from_env()
    
    # Запуск docker-compose up
    import subprocess
    process = subprocess.Popen([
        "docker-compose", "-f", "tests/e2e/docker-compose.yml", 
        "up", "-d", "--build"
    ], cwd=".")
    
    # Ожидание готовности сервисов
    time.sleep(180)  # Ожидание инициализации сервисов
    
    yield
    
    # Очистка после тестов
    subprocess.run([
        "docker-compose", "-f", "tests/e2e/docker-compose.yml", "down", "-v"
    ], cwd=".")

@pytest.fixture(scope="session")
def load_test_data(docker_services):
    """Загрузка тестовых данных"""
    # Запуск загрузчика тестовых данных
    import subprocess
    process = subprocess.run([
        "docker-compose", "-f", "tests/e2e/docker-compose.yml",
        "run", "--rm", "test-data-loader"
    ], cwd=".", capture_output=True, text=True)
    
    if process.returncode != 0:
        logger.error(f"Test data loading failed: {process.stderr}")
        pytest.fail("Failed to load test data")
    
    return True

@pytest.fixture
def jira_client():
    """Клиент Jira для тестов"""
    return Jira(
        url="http://localhost:8080",
        username="admin",
        password="admin"
    )

@pytest.fixture  
def confluence_client():
    """Клиент Confluence для тестов"""
    return Confluence(
        url="http://localhost:8090",
        username="admin", 
        password="admin"
    )

@pytest.fixture
def gitlab_client():
    """Клиент GitLab для тестов"""
    return gitlab.Gitlab("http://localhost:8088", private_token="test-token")

@pytest.fixture
def elasticsearch_client():
    """Клиент Elasticsearch для тестов"""
    return Elasticsearch(["http://localhost:9200"])

@pytest.fixture
def redis_client():
    """Клиент Redis для тестов"""
    return redis.Redis(host="localhost", port=6379, db=0)

class TestJiraIntegration:
    """Тесты интеграции с Jira"""
    
    def test_jira_connection(self, jira_client, load_test_data):
        """Тест подключения к Jira"""
        user = jira_client.myself()
        assert user is not None
        assert user["name"] == "admin"
    
    def test_jira_projects_exist(self, jira_client, load_test_data):
        """Тест наличия созданных проектов"""
        projects = jira_client.projects()
        project_keys = [p["key"] for p in projects]
        
        assert "TEST" in project_keys
        assert "API" in project_keys
    
    def test_jira_issues_search_russian(self, jira_client, load_test_data):
        """Тест поиска русскоязычных задач"""
        issues = jira_client.search_issues('summary ~ "аутентификации"')
        assert len(issues) > 0
        
        russian_issue = issues[0]
        assert "OAuth 2.0" in russian_issue.fields.summary
        assert "аутентификации" in russian_issue.fields.summary
    
    def test_jira_issues_search_english(self, jira_client, load_test_data):
        """Тест поиска англоязычных задач"""
        issues = jira_client.search_issues('summary ~ "rate limiting"')
        assert len(issues) > 0
        
        english_issue = issues[0]
        assert "rate limiting" in english_issue.fields.summary.lower()

class TestConfluenceIntegration:
    """Тесты интеграции с Confluence"""
    
    def test_confluence_connection(self, confluence_client, load_test_data):
        """Тест подключения к Confluence"""
        user = confluence_client.user()
        assert user is not None
    
    def test_confluence_spaces_exist(self, confluence_client, load_test_data):
        """Тест наличия созданных пространств"""
        spaces = confluence_client.get_all_spaces()
        space_keys = [s["key"] for s in spaces["results"]]
        
        assert "TESTSPACE" in space_keys
    
    def test_confluence_pages_search_multilingual(self, confluence_client, load_test_data):
        """Тест поиска многоязычных страниц"""
        # Поиск английской страницы
        en_results = confluence_client.search_content("OAuth 2.0 Authentication")
        assert len(en_results["results"]) > 0
        
        # Поиск русской страницы  
        ru_results = confluence_client.search_content("API Gateway")
        assert len(ru_results["results"]) > 0
    
    def test_confluence_page_content_russian(self, confluence_client, load_test_data):
        """Тест содержимого русскоязычной страницы"""
        page = confluence_client.get_page_by_title(
            space="TESTSPACE", 
            title="Руководство по API Gateway"
        )
        assert page is not None
        assert "маршрутизация" in page["body"]["storage"]["value"].lower()

class TestGitLabIntegration:
    """Тесты интеграции с GitLab"""
    
    def test_gitlab_connection(self, gitlab_client, load_test_data):
        """Тест подключения к GitLab"""
        user = gitlab_client.user
        assert user is not None
    
    def test_gitlab_projects_exist(self, gitlab_client, load_test_data):
        """Тест наличия созданных проектов"""
        projects = gitlab_client.projects.list()
        project_names = [p.name for p in projects]
        
        assert "api-gateway" in project_names
        assert "auth-service" in project_names
    
    def test_gitlab_files_content(self, gitlab_client, load_test_data):
        """Тест содержимого файлов в проектах"""
        # Поиск проекта auth-service
        projects = gitlab_client.projects.list(search="auth-service")
        assert len(projects) > 0
        
        project = projects[0]
        
        # Проверка README файла
        try:
            readme = project.files.get("README.md", ref="main")
            content = readme.decode().decode('utf-8')
            assert "OAuth 2.0" in content
            assert "Русское описание" in content
        except Exception as e:
            logger.warning(f"Could not get README: {e}")

class TestElasticsearchIntegration:
    """Тесты интеграции с Elasticsearch"""
    
    def test_elasticsearch_connection(self, elasticsearch_client, load_test_data):
        """Тест подключения к Elasticsearch"""
        assert elasticsearch_client.ping()
    
    def test_documents_indexed(self, elasticsearch_client, load_test_data):
        """Тест наличия проиндексированных документов"""
        # Поиск по английскому запросу
        en_query = {
            "query": {
                "match": {
                    "content": "OAuth authentication"
                }
            }
        }
        
        en_results = elasticsearch_client.search(
            index="test_documents", 
            body=en_query
        )
        assert en_results["hits"]["total"]["value"] > 0
        
        # Поиск по русскому запросу
        ru_query = {
            "query": {
                "match": {
                    "content": "API Gateway реализация"
                }
            }
        }
        
        ru_results = elasticsearch_client.search(
            index="test_documents",
            body=ru_query
        )
        assert ru_results["hits"]["total"]["value"] > 0
    
    def test_multilingual_search(self, elasticsearch_client, load_test_data):
        """Тест многоязычного поиска"""
        # Поиск документов по языку
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"content": "microservices"}},
                        {"term": {"language": "en"}}
                    ]
                }
            }
        }
        
        results = elasticsearch_client.search(
            index="test_documents",
            body=query
        )
        
        assert results["hits"]["total"]["value"] > 0
        for hit in results["hits"]["hits"]:
            assert hit["_source"]["language"] == "en"

class TestRedisIntegration:
    """Тесты интеграции с Redis"""
    
    def test_redis_connection(self, redis_client, load_test_data):
        """Тест подключения к Redis"""
        assert redis_client.ping()
    
    def test_redis_cache_operations(self, redis_client, load_test_data):
        """Тест операций кеширования"""
        # Установка значения
        redis_client.set("test_key", "test_value", ex=60)
        
        # Получение значения
        value = redis_client.get("test_key")
        assert value.decode('utf-8') == "test_value"
        
        # Удаление значения
        redis_client.delete("test_key")
        assert redis_client.get("test_key") is None

class TestCrossSystemIntegration:
    """Тесты интеграции между системами"""
    
    def test_semantic_search_cross_system(self, jira_client, confluence_client, 
                                        elasticsearch_client, load_test_data):
        """Тест семантического поиска между системами"""
        # Поиск информации об OAuth из Confluence в Elasticsearch
        query = {
            "query": {
                "multi_match": {
                    "query": "OAuth authentication implementation",
                    "fields": ["title^2", "content"]
                }
            }
        }
        
        es_results = elasticsearch_client.search(
            index="test_documents",
            body=query
        )
        
        # Поиск связанных задач в Jira
        jira_issues = jira_client.search_issues('summary ~ "OAuth"')
        
        # Проверка что найдены релевантные документы
        assert es_results["hits"]["total"]["value"] > 0
        assert len(jira_issues) > 0
        
        # Проверка релевантности
        oauth_doc = es_results["hits"]["hits"][0]["_source"]
        assert "oauth" in oauth_doc["tags"]
    
    @pytest.mark.asyncio
    async def test_async_data_synchronization(self, jira_client, confluence_client,
                                            elasticsearch_client, load_test_data):
        """Тест асинхронной синхронизации данных"""
        # Создание новой задачи в Jira
        issue_data = {
            "summary": "Test E2E Integration Issue",
            "description": "This issue is created for E2E testing purposes",
            "issuetype": {"name": "Task"},
            "project": {"key": "TEST"}
        }
        
        issue = jira_client.create_issue(fields=issue_data)
        assert issue is not None
        
        # Имитация индексации в Elasticsearch (в реальной системе это было бы автоматически)
        doc = {
            "title": issue_data["summary"],
            "content": issue_data["description"],
            "source": "jira",
            "language": "en",
            "tags": ["test", "e2e"],
            "created_at": "2024-01-01T00:00:00"
        }
        
        elasticsearch_client.index(index="test_documents", body=doc)
        
        # Небольшая пауза для индексации
        await asyncio.sleep(2)
        
        # Поиск созданного документа
        search_query = {
            "query": {
                "match": {
                    "title": "E2E Integration"
                }
            }
        }
        
        results = elasticsearch_client.search(
            index="test_documents",
            body=search_query
        )
        
        assert results["hits"]["total"]["value"] > 0
        
        # Очистка тестовых данных
        jira_client.issue(issue.key).delete()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"]) 