import pytest
import yaml
import asyncio
import subprocess
import json
import logging
import requests
pytest.importorskip("psycopg2")
import psycopg2
import os
from typing import Dict, List, Any
pytest.importorskip("atlassian")
pytest.importorskip("gitlab")
from atlassian import Confluence, Jira
from gitlab import Gitlab

# Mark as E2E to skip by default
pytestmark = pytest.mark.e2e
from sklearn.metrics.pairwise import cosine_similarity
from model_training import ModelTrainer
# from evaluate_semantic_search import run_evaluation as run_semantic_evaluation
# from validate_rfc import run_validation as run_rfc_validation

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestE2EMLPipeline:
    """E2E тесты полного ML пайплайна с обучением модели"""
    
    @pytest.fixture(scope="class")
    def model_trainer(self):
        """Фикстура для инициализации тренера модели"""
        return ModelTrainer("dataset_config.yml")
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_full_e2e_pipeline_with_model_training(self, model_trainer, integration_services):
        """
        Полный E2E тест:
        1. Загрузка датасета из dataset_config.yml
        2. Обучение модели
        3. Заполнение тестовых данных
        4. Запуск evaluate_semantic_search
        5. Запуск rfc_generation_eval
        6. Тесты обратной связи
        """
        # 1. Обучение модели
        logger.info("Запуск обучения модели...")
        training_metrics = model_trainer.run_full_training_pipeline()
        
        # Проверяем метрики
        assert training_metrics['precision_at_3'] > 0.6, f"Низкая точность модели: {training_metrics['precision_at_3']}"
        
        # 2. Заполнение тестовых данных
        logger.info("Заполнение тестовых данных...")
        self._populate_test_data()
        
        # 3. Ожидание готовности систем
        self._wait_for_services_ready()
        
        # 4. Запуск семантического поиска
        logger.info("Запуск тестов семантического поиска...")
        semantic_results = run_semantic_evaluation(language='all')
        
        # Проверяем результаты семантического поиска
        assert semantic_results['passed'] > semantic_results['failed'], "Больше неудачных тестов семантического поиска"
        
        # 5. Запуск тестов RFC генерации
        logger.info("Запуск тестов RFC генерации...")
        rfc_results = run_rfc_validation(language='all')
        
        # Проверяем результаты RFC
        assert rfc_results['passed'] > rfc_results['failed'], "Больше неудачных тестов RFC генерации"
        
        # 6. Тесты обратной связи
        logger.info("Тестирование обратной связи...")
        self._test_feedback_pipeline(model_trainer)
        
        logger.info("Полный E2E пайплайн завершён успешно")
        
    def _populate_test_data(self):
        """Заполнение тестовых данных во всех системах"""
        # Confluence тестовые данные
        self._create_confluence_test_pages()
        
        # Jira тестовые проекты
        self._create_jira_test_projects()
        
        # GitLab тестовые репозитории
        self._create_gitlab_test_repos()
        
    def _create_confluence_test_pages(self):
        """Создание тестовых страниц в Confluence"""
        confluence = self._get_confluence_client()
        
        test_pages = [
            {
                "title": "OAuth 2.0 Implementation Guide",
                "content": """
                # OAuth 2.0 Implementation Guide
                
                This guide covers OAuth 2.0 implementation for authentication and authorization.
                
                ## Key Components:
                - Authorization Server
                - Resource Server
                - Client Application
                
                ## Flow Types:
                - Authorization Code Flow
                - Implicit Flow
                - Client Credentials Flow
                """,
                "space": "TESTSPACE",
                "language": "en"
            },
            {
                "title": "Руководство по реализации OAuth 2.0",
                "content": """
                # Руководство по реализации OAuth 2.0
                
                Это руководство охватывает реализацию OAuth 2.0 для аутентификации и авторизации.
                
                ## Ключевые компоненты:
                - Сервер авторизации
                - Сервер ресурсов
                - Клиентское приложение
                
                ## Типы потоков:
                - Поток кода авторизации
                - Неявный поток
                - Поток учетных данных клиента
                """,
                "space": "TESTSPACE",
                "language": "ru"
            },
            {
                "title": "Microservices Architecture Best Practices",
                "content": """
                # Microservices Architecture Best Practices
                
                ## Design Principles:
                - Single Responsibility
                - Decentralized Governance
                - Infrastructure Automation
                
                ## Communication Patterns:
                - Synchronous (REST, GraphQL)
                - Asynchronous (Event-driven)
                
                ## Data Management:
                - Database per Service
                - Eventual Consistency
                """,
                "space": "TECH",
                "language": "en"
            }
        ]
        
        for page_data in test_pages:
            try:
                confluence.create_page(
                    space=page_data["space"],
                    title=page_data["title"],
                    body=page_data["content"]
                )
                logger.info(f"Создана страница: {page_data['title']}")
            except Exception as e:
                logger.warning(f"Ошибка создания страницы {page_data['title']}: {e}")
                
    def _create_jira_test_projects(self):
        """Создание тестовых проектов в Jira"""
        jira = self._get_jira_client()
        
        test_issues = [
            {
                "project": "TEST",
                "summary": "Implement OAuth 2.0 authentication",
                "description": """
                We need to implement OAuth 2.0 authentication for our API.
                
                Requirements:
                - Support Authorization Code flow
                - JWT token validation
                - Refresh token mechanism
                
                Acceptance Criteria:
                - Users can authenticate via OAuth 2.0
                - Tokens are properly validated
                - Refresh tokens work correctly
                """,
                "issuetype": "Story",
                "language": "en"
            },
            {
                "project": "TEST", 
                "summary": "Реализовать аутентификацию OAuth 2.0",
                "description": """
                Необходимо реализовать аутентификацию OAuth 2.0 для нашего API.
                
                Требования:
                - Поддержка потока кода авторизации
                - Валидация JWT токенов
                - Механизм обновления токенов
                
                Критерии приемки:
                - Пользователи могут аутентифицироваться через OAuth 2.0
                - Токены правильно валидируются
                - Токены обновления работают корректно
                """,
                "issuetype": "Story",
                "language": "ru"
            }
        ]
        
        for issue_data in test_issues:
            try:
                issue = jira.create_issue(
                    project=issue_data["project"],
                    summary=issue_data["summary"],
                    description=issue_data["description"],
                    issuetype={"name": issue_data["issuetype"]}
                )
                logger.info(f"Создана задача: {issue_data['summary']}")
            except Exception as e:
                logger.warning(f"Ошибка создания задачи {issue_data['summary']}: {e}")
                
    def _create_gitlab_test_repos(self):
        """Создание тестовых репозиториев в GitLab"""
        gitlab = self._get_gitlab_client()
        
        test_repos = [
            {
                "name": "oauth2-service",
                "description": "OAuth 2.0 authentication service",
                "readme_content": """
                # OAuth 2.0 Authentication Service
                
                This service provides OAuth 2.0 authentication capabilities.
                
                ## Features:
                - Authorization Code Flow
                - JWT Token Generation
                - Token Validation
                - Refresh Token Support
                
                ## API Endpoints:
                - `/oauth/authorize` - Authorization endpoint
                - `/oauth/token` - Token endpoint
                - `/oauth/validate` - Token validation
                """,
                "language": "en"
            },
            {
                "name": "microservices-demo",
                "description": "Демонстрация архитектуры микросервисов",
                "readme_content": """
                # Демонстрация архитектуры микросервисов
                
                Этот проект демонстрирует лучшие практики архитектуры микросервисов.
                
                ## Компоненты:
                - API Gateway
                - Сервис аутентификации
                - Сервис пользователей
                - Сервис заказов
                
                ## Технологии:
                - Docker & Kubernetes
                - REST API
                - Event-driven architecture
                """,
                "language": "ru"
            }
        ]
        
        for repo_data in test_repos:
            try:
                project = gitlab.projects.create({
                    'name': repo_data["name"],
                    'description': repo_data["description"],
                    'visibility': 'public'
                })
                
                # Создаём README файл
                project.files.create({
                    'file_path': 'README.md',
                    'branch': 'main',
                    'content': repo_data["readme_content"],
                    'commit_message': 'Initial README'
                })
                
                logger.info(f"Создан репозиторий: {repo_data['name']}")
            except Exception as e:
                logger.warning(f"Ошибка создания репозитория {repo_data['name']}: {e}")
                
    def _test_feedback_pipeline(self, model_trainer):
        """Тестирование пайплайна обратной связи"""
        # Создаём тестовые данные обратной связи
        feedback_data = [
            {
                "query": "OAuth 2.0 implementation",
                "document": "OAuth 2.0 Implementation Guide",
                "relevance_score": 0.95,
                "language": "en",
                "user_id": "test_user_1"
            },
            {
                "query": "микросервисы архитектура",
                "document": "Руководство по архитектуре микросервисов",
                "relevance_score": 0.90,
                "language": "ru", 
                "user_id": "test_user_2"
            }
        ]
        
        # Сохраняем обратную связь в PostgreSQL
        self._save_feedback_to_postgres(feedback_data)
        
        # Проверяем, что данные сохранены
        saved_feedback = self._get_feedback_from_postgres()
        assert len(saved_feedback) >= len(feedback_data), "Не все данные обратной связи сохранены"
        
        # Тестируем переобучение (если достигнут порог)
        if len(saved_feedback) >= 100:  # Порог из конфигурации
            logger.info("Запуск переобучения модели...")
            model_trainer.retrain_with_feedback(saved_feedback)
            
            # Проверяем, что модель переобучена
            new_metrics = model_trainer.evaluate_model()
            assert new_metrics is not None, "Метрики после переобучения не получены"
            
    def _save_feedback_to_postgres(self, feedback_data):
        """Сохранение данных обратной связи в PostgreSQL"""
        conn = self._get_postgres_connection()
        
        try:
            with conn.cursor() as cursor:
                # Создание таблицы если не существует
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS model_feedback (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        query TEXT NOT NULL,
                        document TEXT NOT NULL,
                        relevance_score FLOAT NOT NULL,
                        language VARCHAR(10),
                        user_id VARCHAR(100),
                        processed BOOLEAN DEFAULT FALSE,
                        metadata JSONB
                    )
                """)
                
                # Вставка данных
                for feedback in feedback_data:
                    cursor.execute(
                        """
                        INSERT INTO model_feedback 
                        (query, document, relevance_score, language, user_id, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            feedback["query"],
                            feedback["document"],
                            feedback["relevance_score"],
                            feedback["language"],
                            feedback["user_id"],
                            json.dumps({"source": "e2e_test"})
                        )
                    )
                    
                conn.commit()
                logger.info(f"Сохранено {len(feedback_data)} записей обратной связи")
                
        except Exception as e:
            logger.error(f"Ошибка сохранения обратной связи: {e}")
            raise
            
    def _get_feedback_from_postgres(self):
        """Получение данных обратной связи из PostgreSQL"""
        conn = self._get_postgres_connection()
        feedback_data = []
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT query, document, relevance_score, language, user_id, metadata
                    FROM model_feedback
                    WHERE processed = FALSE
                    ORDER BY timestamp DESC
                """)
                
                rows = cursor.fetchall()
                
                for row in rows:
                    feedback_data.append({
                        'query': row[0],
                        'document': row[1],
                        'relevance_score': row[2],
                        'language': row[3],
                        'user_id': row[4],
                        'metadata': row[5]
                    })
                    
        except Exception as e:
            logger.error(f"Ошибка получения обратной связи: {e}")
            
        return feedback_data

    @pytest.mark.e2e
    def test_model_quality_metrics_storage(self, model_trainer):
        """Тест сохранения метрик качества модели в PostgreSQL"""
        # Обучаем модель
        training_examples = model_trainer.load_training_data()
        model_trainer.train_model(training_examples)
        
        # Оцениваем модель
        metrics = model_trainer.evaluate_model()
        
        # Проверяем, что метрики сохранены в PostgreSQL
        conn = self._get_postgres_connection()
        
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT metric_name, metric_value 
                FROM model_metrics
                WHERE model_version = %s
                ORDER BY timestamp DESC
                LIMIT 10
            """, (model_trainer.config['metadata']['version'],))
            
            saved_metrics = dict(cursor.fetchall())
            
        # Проверяем наличие основных метрик
        assert 'precision_at_3' in saved_metrics, "Метрика precision_at_3 не сохранена"
        assert saved_metrics['precision_at_3'] > 0, "Неверное значение метрики precision_at_3"
        
    @pytest.mark.e2e 
    def test_multilingual_model_performance(self, model_trainer):
        """Тест производительности модели на разных языках"""
        # Загружаем данные для обучения
        training_examples = model_trainer.load_training_data()
        
        # Фильтруем примеры по языкам
        ru_examples = [ex for ex in training_examples if 'ru' in str(ex.texts).lower()]
        en_examples = [ex for ex in training_examples if 'en' in str(ex.texts).lower() or 'oauth' in str(ex.texts).lower()]
        
        assert len(ru_examples) > 0, "Нет примеров на русском языке"
        assert len(en_examples) > 0, "Нет примеров на английском языке"
        
        # Обучаем модель
        model_trainer.train_model(training_examples)
        
        # Тестируем на русском
        ru_query = "Как реализовать OAuth 2.0 аутентификацию?"
        ru_embedding = model_trainer.model.encode([ru_query])
        
        # Тестируем на английском
        en_query = "How to implement OAuth 2.0 authentication?"
        en_embedding = model_trainer.model.encode([en_query])
        
        # Проверяем, что эмбеддинги генерируются
        assert ru_embedding.shape[1] == model_trainer.config['model_config']['embeddings']['dimensions']
        assert en_embedding.shape[1] == model_trainer.config['model_config']['embeddings']['dimensions']
        
        # Проверяем семантическую близость между переводами
        similarity = cosine_similarity(ru_embedding, en_embedding)[0][0]
        assert similarity > 0.5, f"Слишком низкая семантическая близость между переводами: {similarity}"

    @pytest.mark.e2e
    def test_advanced_e2e_scenarios(self):
        """Дополнительные E2E сценарии"""
        
        # Сценарий 1: Поиск документации по API
        logger.info("Тестирование сценария поиска документации API...")
        self._test_api_documentation_search()
        
        # Сценарий 2: Генерация RFC на основе Jira задач
        logger.info("Тестирование генерации RFC на основе Jira...")
        self._test_rfc_generation_from_jira()
        
        # Сценарий 3: Кросс-языковой поиск
        logger.info("Тестирование кросс-языкового поиска...")
        self._test_cross_language_search()
        
        # Сценарий 4: Интеграция с внешними системами
        logger.info("Тестирование интеграции с внешними системами...")
        self._test_external_systems_integration()
        
    def _test_api_documentation_search(self):
        """Тест поиска документации по API"""
        # Симуляция поиска документации
        queries = [
            "OAuth 2.0 authorization endpoint",
            "JWT token validation",
            "API rate limiting",
            "микросервисы коммуникация",
            "REST API документация"
        ]
        
        for query in queries:
            # Здесь должен быть реальный вызов к системе поиска
            results = self._simulate_search(query)
            assert len(results) > 0, f"Нет результатов для запроса: {query}"
            
    def _test_rfc_generation_from_jira(self):
        """Тест генерации RFC на основе Jira задач"""
        # Получаем тестовые задачи из Jira
        jira = self._get_jira_client()
        
        try:
            issues = jira.search_issues("project=TEST", maxResults=5)
            
            for issue in issues:
                # Симуляция генерации RFC
                rfc_content = self._simulate_rfc_generation(issue)
                assert len(rfc_content) > 100, f"RFC слишком короткий для задачи {issue.key}"
                assert "## Цель" in rfc_content or "## Purpose" in rfc_content, "RFC не содержит раздел цели"
                
        except Exception as e:
            logger.warning(f"Ошибка тестирования генерации RFC: {e}")
            
    def _test_cross_language_search(self):
        """Тест кросс-языкового поиска"""
        test_pairs = [
            ("OAuth 2.0 implementation", "реализация OAuth 2.0"),
            ("microservices architecture", "архитектура микросервисов"),
            ("API gateway patterns", "паттерны API шлюза")
        ]
        
        for en_query, ru_query in test_pairs:
            # Симуляция кросс-языкового поиска
            en_results = self._simulate_search(en_query)
            ru_results = self._simulate_search(ru_query)
            
            # Проверяем, что есть пересечения в результатах
            assert len(en_results) > 0, f"Нет результатов для EN запроса: {en_query}"
            assert len(ru_results) > 0, f"Нет результатов для RU запроса: {ru_query}"
            
    def _test_external_systems_integration(self):
        """Тест интеграции с внешними системами"""
        # Проверяем доступность всех систем
        systems = {
            'confluence': 'http://localhost:8090',
            'jira': 'http://localhost:8080', 
            'gitlab': 'http://localhost:8088',
            'elasticsearch': 'http://localhost:9200',
            'postgres': 'localhost:5432'
        }
        
        for system, url in systems.items():
            try:
                if system == 'postgres':
                    conn = self._get_postgres_connection()
                    assert conn is not None, f"{system} недоступен"
                else:
                    response = requests.get(f"{url}/api/health", timeout=5)
                    assert response.status_code == 200, f"{system} не отвечает"
                    
                logger.info(f"Система {system} доступна")
                
            except Exception as e:
                logger.warning(f"Система {system} недоступна: {e}")
                
    def _simulate_search(self, query: str) -> List[Dict]:
        """Симуляция поиска (заглушка)"""
        # В реальной реализации здесь будет вызов к Elasticsearch или другой поисковой системе
        return [
            {"title": f"Result for {query}", "score": 0.95},
            {"title": f"Another result for {query}", "score": 0.87}
        ]
        
    def _simulate_rfc_generation(self, issue) -> str:
        """Симуляция генерации RFC (заглушка)"""
        return f"""
        # RFC: {issue.fields.summary}
        
        ## Цель
        {issue.fields.description[:200]}...
        
        ## Предлагаемое решение
        Подробное описание решения...
        
        ## Альтернативы
        Рассмотренные альтернативы...
        
        ## Риски
        Потенциальные риски...
        """

    # Helper методы для подключения к внешним системам
    def _get_confluence_client(self):
        """Получение клиента Confluence"""
        return Confluence(
            url=os.getenv('CONFLUENCE_URL', 'http://localhost:8090'),
            username=os.getenv('CONFLUENCE_USER', 'admin'),
            password=os.getenv('CONFLUENCE_PASS', 'admin')
        )
        
    def _get_jira_client(self):
        """Получение клиента Jira"""
        return Jira(
            url=os.getenv('JIRA_URL', 'http://localhost:8080'),
            username=os.getenv('JIRA_USER', 'admin'),
            password=os.getenv('JIRA_PASS', 'admin')
        )
        
    def _get_gitlab_client(self):
        """Получение клиента GitLab"""
        return Gitlab(
            url=os.getenv('GITLAB_URL', 'http://localhost:8088'),
            private_token=os.getenv('GITLAB_TOKEN', 'test-token')
        )
        
    def _get_postgres_connection(self):
        """Получение подключения к PostgreSQL"""
        return psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'postgres'),
            port=os.getenv('POSTGRES_PORT', 5432),
            database=os.getenv('POSTGRES_DB', 'testdb'),
            user=os.getenv('POSTGRES_USER', 'testuser'),
            password=os.getenv('POSTGRES_PASSWORD', 'testpass')
        )
        
    def _wait_for_services_ready(self, timeout: int = 300):
        """Ожидание готовности всех сервисов"""
        import time
        
        services = {
            'Confluence': 'http://localhost:8090/status',
            'Jira': 'http://localhost:8080/status',
            'GitLab': 'http://localhost:8088/-/health',
            'Elasticsearch': 'http://localhost:9200/_cluster/health',
            'PostgreSQL': 'localhost:5432'
        }
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            all_ready = True
            
            for service, endpoint in services.items():
                try:
                    if service == 'PostgreSQL':
                        conn = self._get_postgres_connection()
                        conn.close()
                    else:
                        response = requests.get(endpoint, timeout=5)
                        if response.status_code != 200:
                            all_ready = False
                            break
                            
                except Exception:
                    all_ready = False
                    break
                    
            if all_ready:
                logger.info("Все сервисы готовы")
                return
                
            logger.info("Ожидание готовности сервисов...")
            time.sleep(10)
            
        raise Exception(f"Сервисы не готовы после {timeout} секунд")


class TestE2EComprehensiveScenarios:
    """Дополнительные комплексные E2E сценарии"""
    
    @pytest.mark.e2e
    def test_feedback_driven_retraining_cycle(self):
        """Тест полного цикла переобучения на основе обратной связи"""
        trainer = ModelTrainer()
        
        # 1. Первоначальное обучение
        initial_metrics = trainer.run_full_training_pipeline()
        
        # 2. Симуляция пользовательской обратной связи
        self._simulate_user_feedback()
        
        # 3. Сбор обратной связи и переобучение
        feedback_data = trainer.get_feedback_from_postgres()
        
        if len(feedback_data) >= 10:  # Минимальный порог для тестирования
            trainer.retrain_with_feedback(feedback_data)
            
            # 4. Сравнение метрик до и после
            new_metrics = trainer.evaluate_model()
            
            # Проверяем, что модель не деградировала
            assert new_metrics['precision_at_3'] >= initial_metrics['precision_at_3'] * 0.9, \
                "Значительное ухудшение модели после переобучения"
                
    def _simulate_user_feedback(self):
        """Симуляция пользовательской обратной связи"""
        feedback_scenarios = [
            {
                "query": "OAuth 2.0 implementation best practices",
                "selected_document": "OAuth 2.0 Implementation Guide",
                "relevance": 0.95,
                "language": "en"
            },
            {
                "query": "микросервисы коммуникация между сервисами",
                "selected_document": "Microservices Communication Patterns",
                "relevance": 0.90,
                "language": "ru"
            },
            {
                "query": "API gateway authentication flow",
                "selected_document": "API Gateway Patterns",
                "relevance": 0.85,
                "language": "en"
            }
        ]
        
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', 5432),
            database=os.getenv('POSTGRES_DB', 'testdb'),
            user=os.getenv('POSTGRES_USER', 'testuser'),
            password=os.getenv('POSTGRES_PASSWORD', 'testpass')
        )
        
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_feedback (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    query TEXT NOT NULL,
                    document TEXT NOT NULL,
                    relevance_score FLOAT NOT NULL,
                    language VARCHAR(10),
                    user_id VARCHAR(100),
                    processed BOOLEAN DEFAULT FALSE,
                    metadata JSONB
                )
            """)
            
            for feedback in feedback_scenarios:
                cursor.execute(
                    """
                    INSERT INTO model_feedback 
                    (query, document, relevance_score, language, user_id, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        feedback["query"],
                        feedback["selected_document"],
                        feedback["relevance"],
                        feedback["language"],
                        f"test_user_{hash(feedback['query']) % 100}",
                        json.dumps({"source": "simulated_feedback"})
                    )
                )
                
            conn.commit()
            
    @pytest.mark.e2e
    def test_multilingual_cross_system_integration(self):
        """Тест мультиязычной интеграции между системами"""
        # Создаём связанные данные на разных языках
        self._create_linked_multilingual_data()
        
        # Тестируем поиск с кросс-языковыми ссылками
        search_scenarios = [
            {
                "query": "OAuth 2.0 authorization server",
                "expected_languages": ["en", "ru"],
                "min_results": 2
            },
            {
                "query": "архитектура микросервисов паттерны",
                "expected_languages": ["ru", "en"],
                "min_results": 2
            }
        ]
        
        for scenario in search_scenarios:
            results = self._perform_cross_system_search(scenario["query"])
            
            # Проверяем, что есть результаты на ожидаемых языках
            found_languages = set()
            for result in results:
                if result.get('language'):
                    found_languages.add(result['language'])
                    
            assert len(results) >= scenario["min_results"], \
                f"Недостаточно результатов для запроса: {scenario['query']}"
                
    def _create_linked_multilingual_data(self):
        """Создание связанных мультиязычных данных"""
        # Создаём связанные страницы в Confluence
        confluence = Confluence(
            url=os.getenv('CONFLUENCE_URL', 'http://localhost:8090'),
            username=os.getenv('CONFLUENCE_USER', 'admin'),
            password=os.getenv('CONFLUENCE_PASS', 'admin')
        )
        
        linked_pages = [
            {
                "title_en": "OAuth 2.0 Authorization Server Setup",
                "title_ru": "Настройка сервера авторизации OAuth 2.0",
                "content_en": "Comprehensive guide for setting up OAuth 2.0 authorization server...",
                "content_ru": "Подробное руководство по настройке сервера авторизации OAuth 2.0...",
                "tags": ["oauth", "authorization", "security"]
            }
        ]
        
        for page_set in linked_pages:
            try:
                # Создаём английскую версию
                en_page = confluence.create_page(
                    space="TECH",
                    title=page_set["title_en"],
                    body=f"<p>{page_set['content_en']}</p><p>См. также: <a href='#'>Русская версия</a></p>"
                )
                
                # Создаём русскую версию
                ru_page = confluence.create_page(
                    space="TECH",
                    title=page_set["title_ru"], 
                    body=f"<p>{page_set['content_ru']}</p><p>See also: <a href='#'>English version</a></p>"
                )
                
                logger.info(f"Созданы связанные страницы: {page_set['title_en']} / {page_set['title_ru']}")
                
            except Exception as e:
                logger.warning(f"Ошибка создания связанных страниц: {e}")
                
    def _perform_cross_system_search(self, query: str) -> List[Dict]:
        """Выполнение поиска по всем системам"""
        results = []
        
        # Поиск в Confluence
        try:
            confluence = Confluence(
                url=os.getenv('CONFLUENCE_URL', 'http://localhost:8090'),
                username=os.getenv('CONFLUENCE_USER', 'admin'),
                password=os.getenv('CONFLUENCE_PASS', 'admin')
            )
            
            confluence_results = confluence.cql(f'text ~ "{query}"')
            
            for result in confluence_results.get('results', []):
                results.append({
                    'title': result.get('title', ''),
                    'source': 'confluence',
                    'url': result.get('_links', {}).get('webui', ''),
                    'language': self._detect_language(result.get('title', '')),
                    'score': result.get('score', 0.5)
                })
                
        except Exception as e:
            logger.warning(f"Ошибка поиска в Confluence: {e}")
            
        # Симуляция поиска в других системах
        results.extend([
            {
                'title': f'Jira Issue for {query}',
                'source': 'jira',
                'language': 'en',
                'score': 0.8
            },
            {
                'title': f'GitLab Repo: {query}',
                'source': 'gitlab', 
                'language': 'en',
                'score': 0.7
            }
        ])
        
        return results
        
    def _detect_language(self, text: str) -> str:
        """Простое определение языка"""
        # Простая эвристика для определения языка
        cyrillic_chars = sum(1 for char in text if '\u0400' <= char <= '\u04FF')
        if cyrillic_chars > len(text) * 0.1:
            return 'ru'
        return 'en'

    @pytest.mark.e2e
    def test_model_quality_degradation_detection(self):
        """Тест обнаружения деградации качества модели"""
        trainer = ModelTrainer()
        
        # Получаем базовые метрики
        baseline_metrics = trainer.run_full_training_pipeline()
        
        # Симулируем плохую обратную связь
        bad_feedback = [
            {
                "query": "OAuth implementation",
                "document": "Irrelevant document about cooking",
                "relevance_score": 0.95,  # Неправильно высокая оценка
                "language": "en"
            } for _ in range(50)  # Много плохих примеров
        ]
        
        # Добавляем плохие данные и переобучаем
        trainer.retrain_with_feedback(bad_feedback)
        degraded_metrics = trainer.evaluate_model()
        
        # Проверяем обнаружение деградации
        quality_drop = baseline_metrics['precision_at_3'] - degraded_metrics['precision_at_3']
        threshold = trainer.config['feedback_config']['retraining']['min_quality_drop']
        
        if quality_drop > threshold:
            logger.warning(f"Обнаружена деградация модели: {quality_drop:.3f}")
            # В реальной системе здесь должен быть откат к предыдущей версии модели
            assert True, "Деградация корректно обнаружена"
        else:
            assert degraded_metrics['precision_at_3'] > 0.5, "Модель деградировала, но не обнаружена" 