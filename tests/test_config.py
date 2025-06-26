"""
Конфигурация для тестового окружения с Docker containers
"""
import os
from typing import Optional


class TestConfig:
    """Конфигурация для тестов"""
    
    # Database
    TEST_DATABASE_URL = os.getenv(
        "TEST_DATABASE_URL", 
        "postgresql://test_user:test_password@localhost:5433/test_ai_assistant"
    )
    
    # Redis
    TEST_REDIS_URL = os.getenv(
        "TEST_REDIS_URL",
        "redis://localhost:6379/1"
    )
    
    # Qdrant
    QDRANT_URL = os.getenv(
        "QDRANT_URL",
        "http://localhost:6334"
    )
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
    
    # Mock OpenAI
    OPENAI_API_BASE = os.getenv(
        "OPENAI_API_BASE",
        "http://localhost:8081/v1"
    )
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "test-key-mock")
    
    # Elasticsearch
    ELASTICSEARCH_URL = os.getenv(
        "ELASTICSEARCH_URL",
        "http://localhost:9201"
    )
    
    # Test environment
    TESTING = True
    ENVIRONMENT = "test"
    LOG_LEVEL = "INFO"


def get_test_config() -> TestConfig:
    """Получить тестовую конфигурацию"""
    return TestConfig()


def is_docker_available() -> bool:
    """Проверить доступность Docker"""
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


def wait_for_service(url: str, timeout: int = 60) -> bool:
    """Ждать готовности сервиса"""
    import time
    import requests
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def setup_test_database():
    """Настроить тестовую базу данных"""
    from sqlalchemy import create_engine
    from app.database.session import Base
    
    config = get_test_config()
    engine = create_engine(config.TEST_DATABASE_URL)
    
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    return engine


def setup_test_qdrant():
    """Настроить тестовую Qdrant"""
    from qdrant_client import QdrantClient
    
    config = get_test_config()
    client = QdrantClient(
        url=config.QDRANT_URL,
        api_key=config.QDRANT_API_KEY if config.QDRANT_API_KEY else None
    )
    
    # Создаем тестовую коллекцию
    try:
        client.create_collection(
            collection_name="test_documents",
            vectors_config={
                "size": 1536,
                "distance": "Cosine"
            }
        )
    except Exception:
        # Коллекция уже существует
        pass
    
    return client


def setup_test_redis():
    """Настроить тестовый Redis"""
    import redis
    
    config = get_test_config()
    client = redis.from_url(config.TEST_REDIS_URL)
    
    # Очищаем тестовую базу
    client.flushdb()
    
    return client


def cleanup_test_environment():
    """Очистить тестовое окружение"""
    try:
        # Очищаем Redis
        redis_client = setup_test_redis()
        redis_client.flushdb()
        
        # Очищаем Qdrant
        qdrant_client = setup_test_qdrant()
        try:
            qdrant_client.delete_collection("test_documents")
        except Exception:
            pass
            
    except Exception as e:
        print(f"Warning: Could not cleanup test environment: {e}")


# Проверка доступности сервисов
def check_test_services():
    """Проверить доступность тестовых сервисов"""
    config = get_test_config()
    
    services = {
        "PostgreSQL": f"http://localhost:5433",  # Для проверки порта
        "Redis": f"http://localhost:6379",
        "Qdrant": f"{config.QDRANT_URL}/health",
        "OpenAI Mock": f"{config.OPENAI_API_BASE.replace('/v1', '')}/__admin/health",
        "Elasticsearch": f"{config.ELASTICSEARCH_URL}/_cluster/health"
    }
    
    available_services = {}
    
    for service, url in services.items():
        try:
            if service in ["PostgreSQL", "Redis"]:
                # Для DB сервисов проверяем по-другому
                available_services[service] = True
            else:
                import requests
                response = requests.get(url, timeout=5)
                available_services[service] = response.status_code == 200
        except Exception:
            available_services[service] = False
    
    return available_services 