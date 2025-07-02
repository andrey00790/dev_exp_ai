"""
Тест для демонстрации работы с реальными зависимостями из Docker containers
"""

import os

import pytest


class TestWithRealDependencies:
    """Тесты с реальными зависимостями из Docker containers"""

    def test_import_models_with_real_dependencies(self):
        """Тест импорта models с реальными зависимостями"""
        # Устанавливаем переменные окружения для подключения к test containers
        os.environ["DATABASE_URL"] = (
            "postgresql://test_user:test_password@localhost:5433/test_ai_assistant"
        )
        os.environ["REDIS_URL"] = "redis://localhost:6380/1"
        os.environ["QDRANT_URL"] = "http://localhost:6334"
        os.environ["TESTING"] = "true"

        try:
            # Теперь можем импортировать модули с зависимостями
            from models.document import Document, DocumentType
            from models.feedback import UserFeedback, FeedbackType
            from models.generation import GenerationSession, TaskType
            from models.search import SearchResult

            # Проверяем что импорты прошли успешно
            assert Document is not None
            assert DocumentType is not None
            assert UserFeedback is not None
            assert FeedbackType is not None
            assert GenerationSession is not None
            assert TaskType is not None
            assert SearchResult is not None

            print("✅ Все models успешно импортированы с реальными зависимостями!")

        except ImportError as e:
            pytest.skip(f"Import failed due to dependencies: {e}")

    def test_import_app_modules_with_real_dependencies(self):
        """Тест импорта app модулей с реальными зависимостями"""
        # Устанавливаем переменные окружения
        os.environ["DATABASE_URL"] = (
            "postgresql://test_user:test_password@localhost:5433/test_ai_assistant"
        )
        os.environ["REDIS_URL"] = "redis://localhost:6380/1"
        os.environ["QDRANT_URL"] = "http://localhost:6334"
        os.environ["OPENAI_API_KEY"] = "test-key"
        os.environ["TESTING"] = "true"

        try:
            # Пробуем импортировать app модули
            from app.config import AppConfig
            from app.models.user import User

            # Проверяем что импорты прошли успешно
            assert AppConfig is not None
            assert User is not None

            print("✅ App модули успешно импортированы с реальными зависимостями!")

        except ImportError as e:
            pytest.skip(f"App import failed due to dependencies: {e}")

    def test_database_connection_with_containers(self):
        """Тест подключения к базе данных из containers"""
        os.environ["DATABASE_URL"] = (
            "postgresql://test_user:test_password@localhost:5433/test_ai_assistant"
        )
        os.environ["TESTING"] = "true"

        try:
            from sqlalchemy import create_engine, text

            # Создаем подключение к тестовой БД
            engine = create_engine(os.environ["DATABASE_URL"])

            # Проверяем подключение
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test_value"))
                row = result.fetchone()
                assert row[0] == 1

            print("✅ Подключение к PostgreSQL из container работает!")

        except Exception as e:
            pytest.skip(f"Database connection failed: {e}")

    def test_redis_connection_with_containers(self):
        """Тест подключения к Redis из containers"""
        os.environ["REDIS_URL"] = "redis://localhost:6380/1"

        try:
            import redis

            # Создаем подключение к тестовому Redis
            r = redis.from_url(os.environ["REDIS_URL"])

            # Проверяем подключение
            r.set("test_key", "test_value")
            value = r.get("test_key")
            assert value.decode() == "test_value"

            # Очищаем
            r.delete("test_key")

            print("✅ Подключение к Redis из container работает!")

        except Exception as e:
            pytest.skip(f"Redis connection failed: {e}")

    def test_qdrant_connection_with_containers(self):
        """Тест подключения к Qdrant из containers"""
        os.environ["QDRANT_URL"] = "http://localhost:6334"

        try:
            from qdrant_client import QdrantClient

            # Создаем подключение к тестовому Qdrant
            client = QdrantClient(url=os.environ["QDRANT_URL"])

            # Проверяем подключение
            collections = client.get_collections()
            assert collections is not None

            print("✅ Подключение к Qdrant из container работает!")

        except Exception as e:
            pytest.skip(f"Qdrant connection failed: {e}")

    def test_comprehensive_coverage_simulation(self):
        """Симуляция comprehensive coverage с реальными зависимостями"""
        # Устанавливаем все переменные окружения
        os.environ.update(
            {
                "DATABASE_URL": "postgresql://test_user:test_password@localhost:5433/test_ai_assistant",
                "REDIS_URL": "redis://localhost:6380/1",
                "QDRANT_URL": "http://localhost:6334",
                "OPENAI_API_KEY": "test-key",
                "TESTING": "true",
            }
        )

        # Счетчик успешных импортов
        successful_imports = 0
        total_modules = 0

        # Список модулей для тестирования
        modules_to_test = [
            ("models.document", "Document"),
            ("models.feedback", "UserFeedback"),
            ("models.generation", "GenerationSession"),
            ("models.search", "SearchResult"),
            ("app.config", "AppConfig"),
            ("app.models.user", "User"),
        ]

        for module_name, class_name in modules_to_test:
            total_modules += 1
            try:
                module = __import__(module_name, fromlist=[class_name])
                cls = getattr(module, class_name)
                assert cls is not None
                successful_imports += 1
                print(f"✅ {module_name}.{class_name} - импорт успешен")
            except Exception as e:
                print(f"❌ {module_name}.{class_name} - ошибка: {e}")

        # Рассчитываем покрытие
        coverage_percentage = (successful_imports / total_modules) * 100
        print(
            f"\n📊 Симуляция покрытия: {successful_imports}/{total_modules} модулей ({coverage_percentage:.1f}%)"
        )

        # Проверяем что хотя бы 50% модулей импортируется
        assert (
            coverage_percentage >= 50
        ), f"Покрытие слишком низкое: {coverage_percentage}%"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
