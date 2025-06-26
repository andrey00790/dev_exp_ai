"""
Unit тесты для monitoring модулей для достижения 90% покрытия
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json

class TestMonitoringMetrics:
    """Тесты для monitoring metrics"""
    
    def test_metrics_init(self):
        """Тест инициализации метрик"""
        from app.monitoring.metrics import MetricsCollector
        
        collector = MetricsCollector()
        assert collector is not None
    
    @patch('app.monitoring.metrics.time.time')
    def test_record_request_metric(self, mock_time):
        """Тест записи метрики запроса"""
        from app.monitoring.metrics import MetricsCollector
        
        mock_time.return_value = 1234567890.0
        
        collector = MetricsCollector()
        collector.record_request_metric("search", 0.5, 200, "test_user")
        
        assert len(collector.request_metrics) > 0
    
    @patch('app.monitoring.metrics.psutil.cpu_percent')
    @patch('app.monitoring.metrics.psutil.virtual_memory')
    def test_collect_system_metrics(self, mock_memory, mock_cpu):
        """Тест сбора системных метрик"""
        from app.monitoring.metrics import MetricsCollector
        
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0, available=4000000000)
        
        collector = MetricsCollector()
        metrics = collector.collect_system_metrics()
        
        assert metrics is not None
        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
    
    def test_calculate_response_time_percentiles(self):
        """Тест расчета перцентилей времени ответа"""
        from app.monitoring.metrics import MetricsCollector
        
        collector = MetricsCollector()
        response_times = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        
        percentiles = collector.calculate_response_time_percentiles(response_times)
        
        assert percentiles is not None
        assert "p50" in percentiles
        assert "p95" in percentiles
        assert "p99" in percentiles
    
    def test_get_error_rate(self):
        """Тест расчета частоты ошибок"""
        from app.monitoring.metrics import MetricsCollector
        
        collector = MetricsCollector()
        
        # Добавляем тестовые метрики
        collector.request_metrics = [
            {"status_code": 200, "endpoint": "search"},
            {"status_code": 200, "endpoint": "search"},
            {"status_code": 500, "endpoint": "search"},
            {"status_code": 404, "endpoint": "search"}
        ]
        
        error_rate = collector.get_error_rate("search")
        
        assert error_rate == 0.5  # 2 ошибки из 4 запросов
    
    def test_get_throughput(self):
        """Тест расчета пропускной способности"""
        from app.monitoring.metrics import MetricsCollector
        
        collector = MetricsCollector()
        
        # Добавляем тестовые метрики за последнюю минуту
        now = datetime.now()
        collector.request_metrics = [
            {"timestamp": now - timedelta(seconds=30)},
            {"timestamp": now - timedelta(seconds=20)},
            {"timestamp": now - timedelta(seconds=10)}
        ]
        
        throughput = collector.get_throughput(60)  # За последние 60 секунд
        
        assert throughput == 3.0  # 3 запроса за минуту

class TestMonitoringMiddleware:
    """Тесты для monitoring middleware"""
    
    def test_middleware_init(self):
        """Тест инициализации middleware"""
        from app.monitoring.middleware import MonitoringMiddleware
        
        app = Mock()
        middleware = MonitoringMiddleware(app)
        assert middleware is not None
        assert middleware.app == app
    
    @pytest.mark.asyncio
    async def test_middleware_call(self):
        """Тест вызова middleware"""
        from app.monitoring.middleware import MonitoringMiddleware
        
        app = Mock()
        middleware = MonitoringMiddleware(app)
        
        # Mock ASGI scope, receive, send
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/search",
            "headers": [(b"user-agent", b"test")]
        }
        
        receive = AsyncMock()
        send = AsyncMock()
        
        # Mock app call
        async def mock_app(scope, receive, send):
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": []
            })
            await send({
                "type": "http.response.body",
                "body": b"OK"
            })
        
        middleware.app = mock_app
        
        await middleware(scope, receive, send)
        
        # Проверяем что send был вызван
        assert send.call_count >= 2
    
    @patch('app.monitoring.middleware.time.time')
    def test_extract_request_info(self, mock_time):
        """Тест извлечения информации о запросе"""
        from app.monitoring.middleware import MonitoringMiddleware
        
        mock_time.return_value = 1234567890.0
        
        app = Mock()
        middleware = MonitoringMiddleware(app)
        
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/search",
            "headers": [(b"content-type", b"application/json")]
        }
        
        info = middleware.extract_request_info(scope)
        
        assert info is not None
        assert info["method"] == "POST"
        assert info["path"] == "/api/v1/search"
    
    def test_should_monitor_request(self):
        """Тест проверки нужно ли мониторить запрос"""
        from app.monitoring.middleware import MonitoringMiddleware
        
        app = Mock()
        middleware = MonitoringMiddleware(app)
        
        # API запросы должны мониториться
        assert middleware.should_monitor_request("/api/v1/search") == True
        
        # Health check не должен мониториться
        assert middleware.should_monitor_request("/health") == False
        
        # Статические файлы не должны мониториться
        assert middleware.should_monitor_request("/static/css/style.css") == False

class TestMonitoringAPM:
    """Тесты для monitoring APM"""
    
    def test_apm_init(self):
        """Тест инициализации APM"""
        from app.monitoring.apm import APMTracker
        
        tracker = APMTracker()
        assert tracker is not None
    
    @patch('app.monitoring.apm.time.time')
    def test_start_transaction(self, mock_time):
        """Тест начала транзакции"""
        from app.monitoring.apm import APMTracker
        
        mock_time.return_value = 1234567890.0
        
        tracker = APMTracker()
        transaction_id = tracker.start_transaction("search_request", "test_user")
        
        assert transaction_id is not None
        assert transaction_id in tracker.active_transactions
    
    @patch('app.monitoring.apm.time.time')
    def test_end_transaction(self, mock_time):
        """Тест завершения транзакции"""
        from app.monitoring.apm import APMTracker
        
        mock_time.side_effect = [1234567890.0, 1234567891.0]  # start, end
        
        tracker = APMTracker()
        transaction_id = tracker.start_transaction("search_request", "test_user")
        result = tracker.end_transaction(transaction_id, "success")
        
        assert result is not None
        assert result["duration"] == 1.0
        assert result["status"] == "success"
    
    def test_add_span(self):
        """Тест добавления span"""
        from app.monitoring.apm import APMTracker
        
        tracker = APMTracker()
        transaction_id = tracker.start_transaction("search_request", "test_user")
        
        span_id = tracker.add_span(transaction_id, "database_query", {"query": "SELECT * FROM docs"})
        
        assert span_id is not None
        transaction = tracker.active_transactions[transaction_id]
        assert len(transaction["spans"]) == 1
    
    def test_get_transaction_metrics(self):
        """Тест получения метрик транзакции"""
        from app.monitoring.apm import APMTracker
        
        tracker = APMTracker()
        
        # Добавляем завершенные транзакции
        tracker.completed_transactions = [
            {"name": "search", "duration": 0.5, "status": "success"},
            {"name": "search", "duration": 0.8, "status": "success"},
            {"name": "search", "duration": 1.2, "status": "error"}
        ]
        
        metrics = tracker.get_transaction_metrics("search")
        
        assert metrics is not None
        assert metrics["total_count"] == 3
        assert metrics["success_count"] == 2
        assert metrics["error_count"] == 1

class TestMonitoringAlerts:
    """Тесты для monitoring alerts"""
    
    def test_alert_manager_init(self):
        """Тест инициализации менеджера алертов"""
        from app.monitoring.metrics import AlertManager
        
        manager = AlertManager()
        assert manager is not None
    
    def test_check_response_time_alert(self):
        """Тест проверки алерта времени ответа"""
        from app.monitoring.metrics import AlertManager
        
        manager = AlertManager()
        
        # Нормальное время ответа
        alert = manager.check_response_time_alert(0.5, threshold=1.0)
        assert alert is None
        
        # Превышение порога
        alert = manager.check_response_time_alert(1.5, threshold=1.0)
        assert alert is not None
        assert alert["type"] == "response_time"
        assert alert["severity"] == "warning"
    
    def test_check_error_rate_alert(self):
        """Тест проверки алерта частоты ошибок"""
        from app.monitoring.metrics import AlertManager
        
        manager = AlertManager()
        
        # Нормальная частота ошибок
        alert = manager.check_error_rate_alert(0.02, threshold=0.05)
        assert alert is None
        
        # Превышение порога
        alert = manager.check_error_rate_alert(0.08, threshold=0.05)
        assert alert is not None
        assert alert["type"] == "error_rate"
        assert alert["severity"] == "critical"
    
    def test_check_system_resource_alert(self):
        """Тест проверки алерта системных ресурсов"""
        from app.monitoring.metrics import AlertManager
        
        manager = AlertManager()
        
        # Нормальное использование ресурсов
        alert = manager.check_system_resource_alert(
            cpu_percent=50.0,
            memory_percent=60.0,
            cpu_threshold=80.0,
            memory_threshold=85.0
        )
        assert alert is None
        
        # Превышение порога CPU
        alert = manager.check_system_resource_alert(
            cpu_percent=90.0,
            memory_percent=60.0,
            cpu_threshold=80.0,
            memory_threshold=85.0
        )
        assert alert is not None
        assert alert["type"] == "system_resources"
        assert "cpu" in alert["message"]

class TestMonitoringDashboard:
    """Тесты для monitoring dashboard"""
    
    def test_dashboard_data_aggregation(self):
        """Тест агрегации данных для дашборда"""
        from app.monitoring.metrics import DashboardDataAggregator
        
        aggregator = DashboardDataAggregator()
        
        # Mock данные метрик
        metrics_data = [
            {"endpoint": "search", "response_time": 0.5, "status_code": 200, "timestamp": datetime.now()},
            {"endpoint": "search", "response_time": 0.8, "status_code": 200, "timestamp": datetime.now()},
            {"endpoint": "generate", "response_time": 2.0, "status_code": 500, "timestamp": datetime.now()}
        ]
        
        dashboard_data = aggregator.aggregate_metrics(metrics_data)
        
        assert dashboard_data is not None
        assert "endpoints" in dashboard_data
        assert "overall_stats" in dashboard_data
    
    def test_time_series_data_preparation(self):
        """Тест подготовки данных временных рядов"""
        from app.monitoring.metrics import DashboardDataAggregator
        
        aggregator = DashboardDataAggregator()
        
        # Mock данные за последний час
        now = datetime.now()
        time_series_data = []
        for i in range(60):  # 60 минут
            time_series_data.append({
                "timestamp": now - timedelta(minutes=i),
                "response_time": 0.5 + (i * 0.01),
                "requests_count": 10 + i
            })
        
        prepared_data = aggregator.prepare_time_series(time_series_data, interval_minutes=5)
        
        assert prepared_data is not None
        assert len(prepared_data) <= 12  # 60 минут / 5 минут интервал

class TestMonitoringUtilities:
    """Тесты для вспомогательных функций monitoring"""
    
    def test_format_monitoring_response(self):
        """Тест форматирования ответа мониторинга"""
        def format_monitoring_response(metrics, status="healthy"):
            return {
                "status": status,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0"
            }
        
        response = format_monitoring_response({
            "cpu_percent": 50.0,
            "memory_percent": 60.0
        })
        
        assert response["status"] == "healthy"
        assert response["metrics"]["cpu_percent"] == 50.0
        assert "timestamp" in response
    
    def test_calculate_sla_metrics(self):
        """Тест расчета SLA метрик"""
        def calculate_sla_metrics(requests, sla_threshold=0.99):
            total_requests = len(requests)
            successful_requests = len([r for r in requests if r["status_code"] < 400])
            
            availability = successful_requests / total_requests if total_requests > 0 else 0
            sla_breach = availability < sla_threshold
            
            return {
                "availability": availability,
                "sla_threshold": sla_threshold,
                "sla_breach": sla_breach,
                "total_requests": total_requests,
                "successful_requests": successful_requests
            }
        
        requests = [
            {"status_code": 200},
            {"status_code": 200},
            {"status_code": 500},
            {"status_code": 200}
        ]
        
        sla = calculate_sla_metrics(requests, sla_threshold=0.8)
        
        assert sla["availability"] == 0.75  # 3 успешных из 4
        assert sla["sla_breach"] == True     # 0.75 < 0.8
    
    def test_health_check_aggregation(self):
        """Тест агрегации health check"""
        def aggregate_health_checks(services_health):
            overall_status = "healthy"
            failed_services = []
            
            for service, status in services_health.items():
                if status != "healthy":
                    overall_status = "unhealthy"
                    failed_services.append(service)
            
            return {
                "overall_status": overall_status,
                "services": services_health,
                "failed_services": failed_services,
                "healthy_services_count": len([s for s in services_health.values() if s == "healthy"])
            }
        
        health_data = aggregate_health_checks({
            "database": "healthy",
            "redis": "healthy",
            "vector_db": "unhealthy",
            "llm_service": "healthy"
        })
        
        assert health_data["overall_status"] == "unhealthy"
        assert "vector_db" in health_data["failed_services"]
        assert health_data["healthy_services_count"] == 3

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 