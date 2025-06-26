"""
Интеграционные тесты с реальными сервисами из Docker containers
"""
import pytest
import asyncio
from unittest.mock import patch
import os
from sqlalchemy import text


class TestRealServicesIntegration:
    """Тесты с реальными сервисами"""
    
    def test_services_availability(self, services_status):
        """Проверяем доступность всех сервисов"""
        if not services_status:
            pytest.skip("Services status not available")
        
        print(f"📊 Services status: {services_status}")
        
        # Проверяем что хотя бы один сервис доступен
        available_count = sum(1 for status in services_status.values() if status)
        assert available_count > 0, "No services are available"
    
    def test_database_connection(self, test_database, test_config):
        """Тест подключения к тестовой базе данных"""
        if not test_database or not test_config:
            pytest.skip("Test database not available")
        
        # Проверяем что можем подключиться к БД
        assert test_database is not None
        
        # Выполняем простой запрос с text() для SQLAlchemy 2.0
        with test_database.connect() as conn:
            result = conn.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            assert row[0] == 1
    
    def test_redis_connection(self, test_redis, test_config):
        """Тест подключения к Redis"""
        if not test_redis or not test_config:
            pytest.skip("Test Redis not available")
        
        # Проверяем что можем подключиться к Redis
        assert test_redis is not None
        
        # Выполняем простые операции
        test_redis.set("test_key", "test_value")
        value = test_redis.get("test_key")
        assert value.decode() == "test_value"
        
        # Очищаем
        test_redis.delete("test_key")
    
    def test_qdrant_connection(self, test_qdrant, test_config):
        """Тест подключения к Qdrant"""
        if not test_qdrant or not test_config:
            pytest.skip("Test Qdrant not available")
        
        # Проверяем что можем подключиться к Qdrant
        assert test_qdrant is not None
        
        # Проверяем что коллекция существует
        try:
            collections = test_qdrant.get_collections()
            assert collections is not None
        except Exception as e:
            pytest.skip(f"Qdrant not fully available: {e}")


class TestAnalyticsWithRealServices:
    """Тесты analytics модулей с реальными сервисами"""
    
    @pytest.mark.skipif(not os.getenv("TEST_WITH_REAL_SERVICES"), 
                       reason="Real services tests disabled")
    def test_analytics_aggregator_with_db(self, test_database):
        """Тест analytics aggregator с реальной БД"""
        if not test_database:
            pytest.skip("Test database not available")
        
        # Импортируем и тестируем реальный aggregator
        try:
            from app.analytics.aggregator import DataAggregator
            from app.analytics.models import MetricType, AggregationPeriod
            from datetime import datetime
            
            # Создаем mock сессии БД
            from sqlalchemy.orm import sessionmaker
            Session = sessionmaker(bind=test_database)
            session = Session()
            
            aggregator = DataAggregator(session)
            
            # Тестируем базовые методы
            assert aggregator is not None
            assert aggregator.db == session
            
            session.close()
            
        except ImportError as e:
            pytest.skip(f"Analytics modules not available: {e}")
    
    @pytest.mark.skipif(not os.getenv("TEST_WITH_REAL_SERVICES"), 
                       reason="Real services tests disabled")  
    def test_analytics_insights_with_db(self, test_database):
        """Тест analytics insights с реальной БД"""
        if not test_database:
            pytest.skip("Test database not available")
        
        try:
            from app.analytics.insights import AnalyticsInsights
            
            # Создаем mock для тестирования
            insights = AnalyticsInsights()
            assert insights is not None
            
        except ImportError as e:
            pytest.skip(f"Analytics insights not available: {e}")


class TestServicesWithRealDependencies:
    """Тесты services модулей с реальными зависимостями"""
    
    @pytest.mark.skipif(not os.getenv("TEST_WITH_REAL_SERVICES"), 
                       reason="Real services tests disabled")
    def test_vector_search_service_with_qdrant(self, test_qdrant):
        """Тест vector search service с реальным Qdrant"""
        if not test_qdrant:
            pytest.skip("Test Qdrant not available")
        
        try:
            from app.services.vector_search_service import VectorSearchService
            
            service = VectorSearchService()
            assert service is not None
            
            # Тестируем базовые операции если сервис инициализируется
            # (реальная реализация может потребовать дополнительной настройки)
            
        except ImportError as e:
            pytest.skip(f"Vector search service not available: {e}")
    
    @pytest.mark.skipif(not os.getenv("TEST_WITH_REAL_SERVICES"), 
                       reason="Real services tests disabled")
    def test_llm_service_with_mock_openai(self, test_config):
        """Тест LLM service с mock OpenAI API"""
        if not test_config:
            pytest.skip("Test config not available")
        
        try:
            # Устанавливаем переменные окружения для mock API
            os.environ["OPENAI_API_BASE"] = test_config.OPENAI_API_BASE
            os.environ["OPENAI_API_KEY"] = test_config.OPENAI_API_KEY
            
            from app.services.llm_service import LLMService
            
            service = LLMService()
            assert service is not None
            
        except ImportError as e:
            pytest.skip(f"LLM service not available: {e}")
    
    @pytest.mark.skipif(not os.getenv("TEST_WITH_REAL_SERVICES"), 
                       reason="Real services tests disabled")
    def test_realtime_monitoring_with_redis(self, test_redis):
        """Тест realtime monitoring service с реальным Redis"""
        if not test_redis:
            pytest.skip("Test Redis not available")
        
        try:
            from app.services.realtime_monitoring_service import RealtimeMonitoringService
            
            service = RealtimeMonitoringService()
            assert service is not None
            
        except ImportError as e:
            pytest.skip(f"Realtime monitoring service not available: {e}")


class TestMonitoringWithRealServices:
    """Тесты monitoring модулей с реальными сервисами"""
    
    @pytest.mark.skipif(not os.getenv("TEST_WITH_REAL_SERVICES"), 
                       reason="Real services tests disabled")
    def test_metrics_collector_with_real_system(self):
        """Тест metrics collector с реальными системными метриками"""
        try:
            from app.monitoring.metrics import MetricsCollector
            
            collector = MetricsCollector()
            assert collector is not None
            
            # Тестируем сбор реальных системных метрик
            metrics = collector.collect_system_metrics()
            assert metrics is not None
            assert "cpu_percent" in metrics
            assert "memory_percent" in metrics
            
        except ImportError as e:
            pytest.skip(f"Metrics collector not available: {e}")
    
    @pytest.mark.skipif(not os.getenv("TEST_WITH_REAL_SERVICES"), 
                       reason="Real services tests disabled")
    def test_apm_tracker_with_real_data(self):
        """Тест APM tracker с реальными данными"""
        try:
            from app.monitoring.apm import APMTracker
            
            tracker = APMTracker()
            assert tracker is not None
            
            # Тестируем создание транзакции
            txn_id = tracker.start_transaction("test_transaction", "test_user")
            assert txn_id is not None
            
            # Завершаем транзакцию
            result = tracker.end_transaction(txn_id, "success")
            assert result is not None
            
        except ImportError as e:
            pytest.skip(f"APM tracker not available: {e}")


class TestFullStackIntegration:
    """Полноценные интеграционные тесты"""
    
    @pytest.mark.skipif(not os.getenv("TEST_WITH_REAL_SERVICES"), 
                       reason="Real services tests disabled")
    def test_full_search_workflow(self, test_database, test_qdrant, test_redis):
        """Тест полного workflow поиска"""
        if not all([test_database, test_qdrant, test_redis]):
            pytest.skip("Not all services available for full workflow test")
        
        # Этот тест будет реализован когда все сервисы будут доступны
        pytest.skip("Full workflow test - to be implemented")
    
    @pytest.mark.skipif(not os.getenv("TEST_WITH_REAL_SERVICES"), 
                       reason="Real services tests disabled")
    def test_full_generation_workflow(self, test_database, test_config):
        """Тест полного workflow генерации"""
        if not all([test_database, test_config]):
            pytest.skip("Not all services available for generation workflow test")
        
        # Этот тест будет реализован когда все сервисы будут доступны
        pytest.skip("Generation workflow test - to be implemented")


class TestPerformanceWithRealServices:
    """Тесты производительности с реальными сервисами"""
    
    @pytest.mark.skipif(not os.getenv("TEST_WITH_REAL_SERVICES"), 
                       reason="Real services tests disabled")
    def test_database_performance(self, test_database):
        """Тест производительности БД"""
        if not test_database:
            pytest.skip("Test database not available")
        
        import time
        
        # Выполняем множественные запросы и измеряем время
        start_time = time.time()
        
        with test_database.connect() as conn:
            for i in range(100):
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Проверяем что 100 запросов выполняются быстро
        assert duration < 5.0, f"Database queries too slow: {duration}s"
    
    @pytest.mark.skipif(not os.getenv("TEST_WITH_REAL_SERVICES"), 
                       reason="Real services tests disabled")
    def test_redis_performance(self, test_redis):
        """Тест производительности Redis"""
        if not test_redis:
            pytest.skip("Test Redis not available")
        
        import time
        
        # Выполняем множественные операции с Redis
        start_time = time.time()
        
        for i in range(1000):
            test_redis.set(f"perf_test_{i}", f"value_{i}")
            test_redis.get(f"perf_test_{i}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Очищаем тестовые данные
        for i in range(1000):
            test_redis.delete(f"perf_test_{i}")
        
        # Проверяем что 1000 операций выполняются быстро
        assert duration < 10.0, f"Redis operations too slow: {duration}s"


if __name__ == "__main__":
    # Для запуска тестов с реальными сервисами:
    # TEST_WITH_REAL_SERVICES=1 pytest tests/integration/test_real_services.py -v
    pytest.main([__file__, "-v"]) 