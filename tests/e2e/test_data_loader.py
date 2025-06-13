#!/usr/bin/env python3
"""
E2E Test Data Loader
Загружает тестовые данные в Jira, Confluence, GitLab для интеграционных тестов
"""

import json
import time
import logging
from typing import Dict, List
import requests
from pathlib import Path
import pytest

pytest.importorskip("atlassian")
pytest.importorskip("gitlab")
from atlassian import Jira, Confluence
import gitlab

pytestmark = pytest.mark.e2e
pytest.importorskip("psycopg2")
import psycopg2
pytest.importorskip("elasticsearch")
from elasticsearch import Elasticsearch
import redis
from faker import Faker
import yaml

fake = Faker(['en_US', 'ru_RU'])

class E2EDataLoader:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # URLs сервисов
        self.jira_url = "http://localhost:8080"
        self.confluence_url = "http://localhost:8090"
        self.gitlab_url = "http://localhost:8088"
        
        # Credentials
        self.admin_user = "admin"
        self.admin_pass = "admin"
        
        # Подключения к базам данных и сервисам
        self.postgres_conn = None
        self.es_client = None
        self.redis_client = None
        
    def wait_for_services(self):
        """Ожидание готовности всех сервисов"""
        services = [
            (self.jira_url + "/status", "Jira"),
            (self.confluence_url + "/status", "Confluence"), 
            (self.gitlab_url + "/-/health", "GitLab")
        ]
        
        for url, name in services:
            self.logger.info(f"Waiting for {name}...")
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        self.logger.info(f"{name} is ready!")
                        break
                except requests.RequestException:
                    if attempt == max_attempts - 1:
                        raise Exception(f"{name} not ready after {max_attempts} attempts")
                    time.sleep(30)
    
    def setup_connections(self):
        """Настройка подключений к сервисам"""
        # PostgreSQL
        self.postgres_conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="atlassian",
            user="atlassian", 
            password="atlassian"
        )
        
        # Elasticsearch
        self.es_client = Elasticsearch(["http://localhost:9200"])
        
        # Redis
        self.redis_client = redis.Redis(host="localhost", port=6379, db=0)
        
        self.logger.info("All service connections established")
    
    def load_jira_data(self):
        """Загрузка тестовых данных в Jira"""
        self.logger.info("Loading Jira test data...")
        
        jira = Jira(
            url=self.jira_url,
            username=self.admin_user,
            password=self.admin_pass
        )
        
        # Создание проектов
        projects_data = [
            {
                "key": "TEST",
                "name": "Test Project",
                "description": "Тестовый проект для E2E тестов",
                "lead": self.admin_user,
                "projectTypeKey": "software"
            },
            {
                "key": "API",
                "name": "API Development",
                "description": "API Development project with Russian documentation",
                "lead": self.admin_user, 
                "projectTypeKey": "software"
            }
        ]
        
        for project_data in projects_data:
            try:
                project = jira.create_project(project_data)
                self.logger.info(f"Created Jira project: {project_data['key']}")
                
                # Создание задач в проекте
                self._create_jira_issues(jira, project_data['key'])
                
            except Exception as e:
                self.logger.warning(f"Project {project_data['key']} might already exist: {e}")
    
    def _create_jira_issues(self, jira, project_key):
        """Создание тестовых задач в Jira"""
        issues_data = [
            {
                "summary": "Реализация OAuth 2.0 аутентификации",
                "description": "Необходимо реализовать OAuth 2.0 для REST API с поддержкой refresh токенов",
                "issuetype": {"name": "Story"},
                "project": {"key": project_key}
            },
            {
                "summary": "API rate limiting implementation", 
                "description": "Implement rate limiting for API endpoints to prevent abuse",
                "issuetype": {"name": "Task"},
                "project": {"key": project_key}
            },
            {
                "summary": "Микросервисы архитектура документация",
                "description": "Создать техническую документацию по архитектуре микросервисов",
                "issuetype": {"name": "Task"},
                "project": {"key": project_key}
            }
        ]
        
        for issue_data in issues_data:
            try:
                issue = jira.create_issue(fields=issue_data)
                self.logger.info(f"Created Jira issue: {issue_data['summary']}")
            except Exception as e:
                self.logger.warning(f"Failed to create issue: {e}")
    
    def load_confluence_data(self):
        """Загрузка тестовых данных в Confluence"""
        self.logger.info("Loading Confluence test data...")
        
        confluence = Confluence(
            url=self.confluence_url,
            username=self.admin_user,
            password=self.admin_pass
        )
        
        # Создание пространства
        space_data = {
            "key": "TESTSPACE",
            "name": "Test Knowledge Base",
            "description": "Тестовая база знаний для E2E тестов"
        }
        
        try:
            space = confluence.create_space(
                space_data["key"],
                space_data["name"], 
                space_data["description"]
            )
            self.logger.info(f"Created Confluence space: {space_data['key']}")
            
            # Создание страниц
            self._create_confluence_pages(confluence, space_data["key"])
            
        except Exception as e:
            self.logger.warning(f"Space might already exist: {e}")
    
    def _create_confluence_pages(self, confluence, space_key):
        """Создание тестовых страниц в Confluence"""
        pages_data = [
            {
                "title": "OAuth 2.0 Authentication Guide",
                "content": """
                <h1>OAuth 2.0 Implementation Guide</h1>
                <p>This guide covers implementation of OAuth 2.0 authentication for REST APIs.</p>
                <h2>Key Components</h2>
                <ul>
                <li>Authorization Server</li>
                <li>Resource Server</li>
                <li>Client Application</li>
                </ul>
                """
            },
            {
                "title": "Руководство по API Gateway",
                "content": """
                <h1>API Gateway Implementation</h1>
                <p>Руководство по реализации API Gateway с ограничением скорости запросов.</p>
                <h2>Основные функции</h2>
                <ul>
                <li>Маршрутизация запросов</li>
                <li>Аутентификация и авторизация</li>
                <li>Rate limiting</li>
                <li>Мониторинг и логирование</li>
                </ul>
                """
            },
            {
                "title": "Microservices Architecture Patterns",
                "content": """
                <h1>Microservices Design Patterns</h1>
                <p>Collection of proven patterns for microservices architecture.</p>
                <h2>Patterns Covered</h2>
                <ul>
                <li>Circuit Breaker</li>
                <li>Saga Pattern</li>
                <li>API Gateway</li>
                <li>Service Discovery</li>
                </ul>
                """
            }
        ]
        
        for page_data in pages_data:
            try:
                page = confluence.create_page(
                    space=space_key,
                    title=page_data["title"],
                    body=page_data["content"]
                )
                self.logger.info(f"Created Confluence page: {page_data['title']}")
            except Exception as e:
                self.logger.warning(f"Failed to create page: {e}")
    
    def load_gitlab_data(self):
        """Загрузка тестовых данных в GitLab"""
        self.logger.info("Loading GitLab test data...")
        
        gl = gitlab.Gitlab(self.gitlab_url, private_token="test-token")
        
        # Создание проектов
        projects_data = [
            {
                "name": "api-gateway",
                "description": "API Gateway service implementation",
                "visibility": "internal"
            },
            {
                "name": "auth-service", 
                "description": "Authentication microservice with OAuth 2.0",
                "visibility": "internal"
            }
        ]
        
        for project_data in projects_data:
            try:
                project = gl.projects.create(project_data)
                self.logger.info(f"Created GitLab project: {project_data['name']}")
                
                # Создание файлов в проекте
                self._create_gitlab_files(project, project_data['name'])
                
            except Exception as e:
                self.logger.warning(f"Project might already exist: {e}")
    
    def _create_gitlab_files(self, project, project_name):
        """Создание тестовых файлов в GitLab проекте"""
        if project_name == "api-gateway":
            files_data = [
                {
                    "file_path": "README.md",
                    "content": """# API Gateway Service

API Gateway implementation with rate limiting and authentication.

## Features
- Request routing
- Rate limiting  
- Authentication/Authorization
- Monitoring and logging
""",
                    "commit_message": "Add README"
                },
                {
                    "file_path": "docs/architecture.md", 
                    "content": """# Architecture Overview

This document describes the API Gateway architecture.

## Components
- Load Balancer
- Gateway Service
- Backend Services
""",
                    "commit_message": "Add architecture documentation"
                }
            ]
        else:
            files_data = [
                {
                    "file_path": "README.md",
                    "content": """# Authentication Service

OAuth 2.0 authentication microservice.

## Русское описание
Сервис аутентификации с поддержкой OAuth 2.0.

## Features
- OAuth 2.0 flows
- JWT tokens
- Refresh tokens
""",
                    "commit_message": "Initial commit"
                }
            ]
        
        for file_data in files_data:
            try:
                project.files.create(file_data)
                self.logger.info(f"Created file: {file_data['file_path']}")
            except Exception as e:
                self.logger.warning(f"Failed to create file: {e}")
    
    def index_documents_to_elasticsearch(self):
        """Индексация документов в Elasticsearch для семантического поиска"""
        self.logger.info("Indexing documents to Elasticsearch...")
        
        # Создание индекса
        index_name = "test_documents"
        if not self.es_client.indices.exists(index=index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "title": {"type": "text", "analyzer": "standard"},
                        "content": {"type": "text", "analyzer": "standard"},
                        "source": {"type": "keyword"},
                        "language": {"type": "keyword"},
                        "tags": {"type": "keyword"},
                        "created_at": {"type": "date"}
                    }
                }
            }
            self.es_client.indices.create(index=index_name, body=mapping)
            
        # Тестовые документы для индексации
        documents = [
            {
                "title": "OAuth 2.0 Authentication Guide",
                "content": "OAuth 2.0 implementation REST API authentication authorization tokens",
                "source": "confluence",
                "language": "en",
                "tags": ["oauth", "authentication", "api"]
            },
            {
                "title": "Руководство по API Gateway", 
                "content": "API Gateway реализация ограничение скорости маршрутизация аутентификация",
                "source": "confluence",
                "language": "ru", 
                "tags": ["api-gateway", "rate-limiting", "routing"]
            },
            {
                "title": "Microservices Architecture Patterns",
                "content": "Circuit Breaker Saga API Gateway Service Discovery microservices patterns",
                "source": "confluence",
                "language": "en",
                "tags": ["microservices", "patterns", "architecture"]
            }
        ]
        
        for i, doc in enumerate(documents):
            doc["created_at"] = "2024-01-01T00:00:00"
            self.es_client.index(index=index_name, id=i+1, body=doc)
            
        self.logger.info(f"Indexed {len(documents)} documents to Elasticsearch")
    
    def run(self):
        """Запуск загрузки всех тестовых данных"""
        try:
            self.logger.info("Starting E2E test data loading...")
            
            self.wait_for_services()
            self.setup_connections()
            
            self.load_jira_data()
            self.load_confluence_data() 
            self.load_gitlab_data()
            self.index_documents_to_elasticsearch()
            
            self.logger.info("E2E test data loading completed successfully!")
            
        except Exception as e:
            self.logger.error(f"Test data loading failed: {e}")
            raise
        finally:
            if self.postgres_conn:
                self.postgres_conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loader = E2EDataLoader()
    loader.run() 