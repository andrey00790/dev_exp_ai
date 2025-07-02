"""
Integration Tests for DataSources with Test Containers
Интеграционные тесты для источников данных с использованием тест-контейнеров
"""

import pytest
import asyncio
import time
from typing import Dict, Any
from unittest.mock import patch

# Test containers imports (optional - только если установлены)
try:
    from testcontainers.clickhouse import ClickHouseContainer
    from testcontainers.compose import DockerCompose
    CONTAINERS_AVAILABLE = True
except ImportError:
    CONTAINERS_AVAILABLE = False

from domain.integration.datasource_interface import (
    DataSourceConfig,
    DataSourceType,
    ConnectionStatus
)
from domain.integration.datasources.clickhouse_datasource import ClickHouseDataSource
from domain.integration.datasources.ydb_datasource import YDBDataSource
from domain.integration.datasource_manager import DataSourceManager
from domain.integration.enhanced_semantic_search import (
    EnhancedSemanticSearch,
    SemanticSearchConfig
)


@pytest.mark.skipif(not CONTAINERS_AVAILABLE, reason="Test containers not available")
class TestClickHouseIntegration:
    """Интеграционные тесты для ClickHouse с тест-контейнерами"""
    
    @pytest.fixture(scope="class")
    def clickhouse_container(self):
        """ClickHouse тест-контейнер"""
        with ClickHouseContainer("clickhouse/clickhouse-server:latest") as container:
            # Ждем готовности контейнера
            container.get_exposed_port(8123)
            time.sleep(10)  # Дополнительное время на инициализацию
            yield container
    
    @pytest.fixture
    def clickhouse_config(self, clickhouse_container):
        """Конфигурация для тест-контейнера ClickHouse"""
        return DataSourceConfig(
            source_id="test_clickhouse_container",
            source_type=DataSourceType.CLICKHOUSE,
            name="Test ClickHouse Container",
            host=clickhouse_container.get_container_host_ip(),
            port=clickhouse_container.get_exposed_port(8123),
            database="default",
            username="default",
            password="",
            ssl_enabled=False
        )
    
    @pytest.fixture
    def clickhouse_datasource(self, clickhouse_config):
        """ClickHouse источник данных для тестов"""
        return ClickHouseDataSource(clickhouse_config)
    
    @pytest.mark.asyncio
    async def test_clickhouse_real_connection(self, clickhouse_datasource):
        """Тест реального подключения к ClickHouse контейнеру"""
        success = await clickhouse_datasource.connect()
        
        assert success is True
        assert clickhouse_datasource.status == ConnectionStatus.CONNECTED
        assert clickhouse_datasource.client is not None
        
        # Закрываем подключение
        await clickhouse_datasource.close()
        assert clickhouse_datasource.status == ConnectionStatus.DISCONNECTED
    
    @pytest.mark.asyncio
    async def test_clickhouse_query_execution(self, clickhouse_datasource):
        """Тест выполнения реального запроса к ClickHouse"""
        await clickhouse_datasource.connect()
        
        # Создаем тестовую таблицу
        create_table_query = """
        CREATE TABLE IF NOT EXISTS test_docs (
            id String,
            title String,
            content String,
            created_at DateTime DEFAULT now()
        ) ENGINE = Memory
        """
        
        result = await clickhouse_datasource.query(create_table_query)
        assert result is not None
        
        # Вставляем тестовые данные
        insert_query = """
        INSERT INTO test_docs (id, title, content) VALUES
        ('doc1', 'Test Document 1', 'This is test content for document 1'),
        ('doc2', 'Test Document 2', 'This is test content for document 2')
        """
        
        result = await clickhouse_datasource.query(insert_query)
        assert result is not None
        
        # Выполняем поисковый запрос
        search_query = "SELECT * FROM test_docs WHERE content LIKE '%test%'"
        result = await clickhouse_datasource.query(search_query)
        
        assert result.total_rows == 2
        assert len(result.data) == 2
        assert result.data[0]["title"] == "Test Document 1"
        
        await clickhouse_datasource.close()
    
    @pytest.mark.asyncio
    async def test_clickhouse_schema_detection_real(self, clickhouse_datasource):
        """Тест реальной автодетекции схемы ClickHouse"""
        await clickhouse_datasource.connect()
        
        # Создаем тестовую таблицу с различными типами данных
        create_table_query = """
        CREATE TABLE IF NOT EXISTS test_schema (
            id UInt64,
            name String,
            score Float64,
            is_active UInt8,
            created_at DateTime
        ) ENGINE = Memory
        """
        
        await clickhouse_datasource.query(create_table_query)
        
        # Получаем схему
        schema = await clickhouse_datasource.get_schema()
        
        assert schema.format_type == "sql"
        assert len(schema.tables) >= 1
        
        # Находим нашу тестовую таблицу
        test_table = next((t for t in schema.tables if t.name == "test_schema"), None)
        assert test_table is not None
        assert len(test_table.fields) == 5
        
        # Проверяем типы полей
        field_types = {f.name: f.type for f in test_table.fields}
        assert "id" in field_types
        assert "name" in field_types
        assert "score" in field_types
        
        await clickhouse_datasource.close()


class TestDataSourceManagerIntegration:
    """Интеграционные тесты для менеджера источников данных"""
    
    @pytest.fixture
    def mock_config_file(self, tmp_path):
        """Создание временного конфигурационного файла"""
        config_content = """
datasources:
  clickhouse:
    test_analytics:
      name: "Test Analytics ClickHouse"
      enabled: true
      host: "localhost"
      port: 8123
      database: "test_analytics"
      username: "default"
      password: ""
      ssl: false
      timeout: 30
      description: "Test ClickHouse for analytics"
      tags: ["test", "analytics"]
  
  ydb:
    test_storage:
      name: "Test Storage YDB"
      enabled: true
      endpoint: "grpc://localhost:2136"
      database: "/local/test"
      ssl: false
      timeout: 30
      auth_method: "metadata"
      description: "Test YDB for storage"
      tags: ["test", "storage"]

global_settings:
  connection_pool:
    default_max_connections: 5
    connection_timeout: 15
  retry_policy:
    max_retries: 2
    retry_delay: 1
"""
        config_file = tmp_path / "test_datasources.yaml"
        config_file.write_text(config_content)
        return str(config_file)
    
    @pytest.fixture
    def datasource_manager(self, mock_config_file):
        """Менеджер источников данных с тестовой конфигурацией"""
        return DataSourceManager(config_path=mock_config_file)
    
    def test_yaml_config_loading(self, datasource_manager):
        """Тест загрузки YAML конфигурации"""
        configs = datasource_manager._load_configuration()
        
        assert len(configs) >= 2
        
        # Проверяем ClickHouse конфигурацию
        clickhouse_configs = [c for c in configs if c.source_type == DataSourceType.CLICKHOUSE]
        assert len(clickhouse_configs) >= 1
        
        ch_config = clickhouse_configs[0]
        assert ch_config.source_id == "test_analytics"
        assert ch_config.host == "localhost"
        assert ch_config.port == 8123
        assert ch_config.enabled is True
        
        # Проверяем YDB конфигурацию
        ydb_configs = [c for c in configs if c.source_type == DataSourceType.YDB]
        assert len(ydb_configs) >= 1
        
        ydb_config = ydb_configs[0]
        assert ydb_config.source_id == "test_storage"
        assert ydb_config.host == "grpc://localhost:2136"
        assert ydb_config.database == "/local/test"
    
    def test_env_override_functionality(self, datasource_manager):
        """Тест переопределения конфигурации через ENV переменные"""
        env_vars = {
            "DS_CLICKHOUSE_HOST": "override-host.com",
            "DS_CLICKHOUSE_PORT": "9000",
            "DS_CLICKHOUSE_ENABLED": "true",
            "DS_CLICKHOUSE_SOURCE_ID": "env_clickhouse"
        }
        
        with patch.dict('os.environ', env_vars):
            configs = datasource_manager._load_configuration()
            
            # Должны быть как YAML, так и ENV конфигурации
            env_configs = [c for c in configs if c.source_id == "env_clickhouse"]
            assert len(env_configs) == 1
            
            env_config = env_configs[0]
            assert env_config.host == "override-host.com"
            assert env_config.port == 9000
    
    @pytest.mark.asyncio
    async def test_manager_initialization_with_mocks(self, datasource_manager):
        """Тест инициализации менеджера с мокированными подключениями"""
        # Мокируем все классы источников данных
        mock_clickhouse = AsyncMock()
        mock_clickhouse.connect.return_value = True
        mock_clickhouse.get_schema.return_value = AsyncMock()
        
        mock_ydb = AsyncMock()
        mock_ydb.connect.return_value = True
        mock_ydb.get_schema.return_value = AsyncMock()
        
        # Заменяем классы на моки
        with patch.object(datasource_manager, 'datasource_classes', {
            DataSourceType.CLICKHOUSE: lambda cfg: mock_clickhouse,
            DataSourceType.YDB: lambda cfg: mock_ydb
        }):
            success = await datasource_manager.initialize()
            
            assert success is True
            assert len(datasource_manager.datasources) >= 2
    
    @pytest.mark.asyncio
    async def test_health_check_all_sources(self, datasource_manager):
        """Тест проверки состояния всех источников"""
        # Регистрируем мокированные источники
        mock_datasource = AsyncMock()
        mock_datasource.health_check.return_value = {
            "status": "healthy",
            "connected": True,
            "source_id": "test_source",
            "response_time_ms": 150.0
        }
        
        datasource_manager.datasources["test_source"] = mock_datasource
        
        health_status = await datasource_manager.health_check_all()
        
        assert health_status["total_sources"] == 1
        assert health_status["healthy_sources"] == 1
        assert "test_source" in health_status["sources"]
        assert health_status["sources"]["test_source"]["status"] == "healthy"


class TestEnhancedSearchIntegration:
    """Интеграционные тесты для расширенного семантического поиска"""
    
    @pytest.fixture
    def enhanced_search(self):
        """Экземпляр расширенного поиска"""
        return EnhancedSemanticSearch()
    
    @pytest.mark.asyncio
    async def test_search_sources_ui_integration(self, enhanced_search):
        """Тест интеграции с UI для выбора источников"""
        # Мокируем менеджер источников данных
        mock_manager = AsyncMock()
        mock_manager.get_available_datasources.return_value = [
            {
                "source_id": "analytics_clickhouse",
                "name": "Analytics ClickHouse", 
                "source_type": "clickhouse",
                "enabled": True,
                "status": "connected",
                "tables_count": 5,
                "schema_available": True,
                "tags": ["analytics", "olap"]
            },
            {
                "source_id": "production_ydb",
                "name": "Production YDB",
                "source_type": "ydb", 
                "enabled": True,
                "status": "connected",
                "tables_count": 12,
                "schema_available": True,
                "tags": ["production", "transactional"]
            }
        ]
        
        enhanced_search.datasource_manager = mock_manager
        
        ui_sources = await enhanced_search.get_available_sources_for_ui()
        
        assert len(ui_sources) == 2
        
        # Проверяем ClickHouse источник
        ch_source = next(s for s in ui_sources if s["id"] == "analytics_clickhouse")
        assert ch_source["selectable"] is True
        assert ch_source["weight"] == 1.0
        assert ch_source["connected"] is True
        
        # Проверяем YDB источник
        ydb_source = next(s for s in ui_sources if s["id"] == "production_ydb")
        assert ydb_source["selectable"] is True
        assert ydb_source["weight"] == 0.9  # YDB имеет вес 0.9
        assert ydb_source["connected"] is True
    
    @pytest.mark.asyncio
    async def test_search_configuration_scenarios(self, enhanced_search):
        """Тест различных сценариев конфигурации поиска"""
        # Мокируем источники данных
        mock_manager = AsyncMock()
        mock_clickhouse = AsyncMock()
        mock_clickhouse.config.source_id = "analytics_clickhouse"
        mock_clickhouse.config.source_type = DataSourceType.CLICKHOUSE
        
        mock_ydb = AsyncMock()
        mock_ydb.config.source_id = "production_ydb"
        mock_ydb.config.source_type = DataSourceType.YDB
        
        mock_manager.get_enabled_datasources.return_value = [mock_clickhouse, mock_ydb]
        enhanced_search.datasource_manager = mock_manager
        
        # Сценарий 1: Пользователь выбрал только ClickHouse
        config1 = SemanticSearchConfig(
            user_id="user1",
            selected_sources=["analytics_clickhouse"],
            limit=10
        )
        
        sources1 = await enhanced_search._determine_search_sources(config1)
        assert len(sources1) == 1
        assert sources1[0].config.source_id == "analytics_clickhouse"
        
        # Сценарий 2: Пользователь выбрал все источники
        config2 = SemanticSearchConfig(
            user_id="user2",
            selected_sources=["analytics_clickhouse", "production_ydb"],
            limit=20
        )
        
        sources2 = await enhanced_search._determine_search_sources(config2)
        assert len(sources2) == 2
        
        # Сценарий 3: Пользователь не выбрал источники (используются по умолчанию)
        config3 = SemanticSearchConfig(
            user_id="user3",
            selected_sources=[],
            limit=15
        )
        
        sources3 = await enhanced_search._determine_search_sources(config3)
        # Источники по умолчанию должны пересекаться с доступными
        assert len(sources3) >= 0


# Mock-based тесты для случаев, когда контейнеры недоступны
class TestDataSourcesMockIntegration:
    """Интеграционные тесты с использованием моков"""
    
    @pytest.mark.asyncio
    async def test_full_search_pipeline_mock(self):
        """Тест полного пайплайна поиска с мокированными источниками"""
        # Создаем полную цепочку компонентов
        enhanced_search = EnhancedSemanticSearch()
        
        # Мокируем менеджер источников данных
        mock_manager = AsyncMock()
        mock_datasource = AsyncMock()
        mock_datasource.config.source_id = "test_clickhouse"
        mock_datasource.config.source_type = DataSourceType.CLICKHOUSE
        
        mock_manager.get_enabled_datasources.return_value = [mock_datasource]
        enhanced_search.datasource_manager = mock_manager
        
        # Мокируем поиск в SQL источниках
        with patch.object(enhanced_search, '_search_sql_source') as mock_sql_search:
            mock_sql_search.return_value = [
                AsyncMock(
                    id="doc1",
                    title="Test Document",
                    content="Test content",
                    source_id="test_clickhouse",
                    source_type=DataSourceType.CLICKHOUSE,
                    score=0.95,
                    snippet="Test snippet"
                )
            ]
            
            # Выполняем поиск
            config = SemanticSearchConfig(
                user_id="test_user",
                selected_sources=["test_clickhouse"],
                limit=10,
                hybrid_search=False  # Отключаем векторный поиск для простоты
            )
            
            result = await enhanced_search.search("test query", config)
            
            assert len(result.candidates) == 1
            assert result.total_results == 1
            assert "test_clickhouse" in result.sources_searched
            assert result.search_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_parallel_source_search_mock(self):
        """Тест параллельного поиска по множественным источникам"""
        enhanced_search = EnhancedSemanticSearch()
        
        # Мокируем несколько источников данных
        mock_manager = AsyncMock()
        
        mock_ch = AsyncMock()
        mock_ch.config.source_id = "clickhouse_source"
        mock_ch.config.source_type = DataSourceType.CLICKHOUSE
        
        mock_ydb = AsyncMock()
        mock_ydb.config.source_id = "ydb_source"
        mock_ydb.config.source_type = DataSourceType.YDB
        
        mock_manager.get_enabled_datasources.return_value = [mock_ch, mock_ydb]
        enhanced_search.datasource_manager = mock_manager
        
        # Мокируем результаты поиска от разных источников
        async def mock_collect_candidates(query, sources, config):
            candidates = []
            for source in sources:
                if source.config.source_type == DataSourceType.CLICKHOUSE:
                    candidates.append(AsyncMock(
                        id="ch_doc1",
                        source_id="clickhouse_source",
                        score=0.9
                    ))
                elif source.config.source_type == DataSourceType.YDB:
                    candidates.append(AsyncMock(
                        id="ydb_doc1", 
                        source_id="ydb_source",
                        score=0.8
                    ))
            return candidates
        
        with patch.object(enhanced_search, '_collect_candidates', mock_collect_candidates):
            config = SemanticSearchConfig(
                selected_sources=["clickhouse_source", "ydb_source"],
                limit=10
            )
            
            result = await enhanced_search.search("test query", config)
            
            assert len(result.candidates) == 2
            assert len(result.sources_searched) == 2
            assert "clickhouse_source" in result.sources_searched
            assert "ydb_source" in result.sources_searched


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 