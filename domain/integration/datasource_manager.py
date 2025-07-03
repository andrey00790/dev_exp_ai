"""
DataSource Manager

Manages all data sources and provides unified interface for data access.
"""

import os
import yaml
from typing import Dict, List, Optional, Any, Type, AsyncIterator
from datetime import datetime
import asyncio
import logging

from .datasource_interface import (
    DataSourceInterface,
    DataSourceConfig,
    DataSourceType,
    DataSourceSchema
)

# Conditional imports to handle missing optional dependencies
try:
    from .datasources.clickhouse_datasource import ClickHouseDataSource
except ImportError:
    ClickHouseDataSource = None

try:
    from .datasources.ydb_datasource import YDBDataSource
except ImportError:
    YDBDataSource = None

logger = logging.getLogger(__name__)


class DataSourceManager:
    """
    Менеджер источников данных
    
    Возможности:
    - Динамическая конфигурация через config.yaml и ENV переменные
    - Автоматическая регистрация и подключение к источникам
    - Управление жизненным циклом подключений
    - Балансировка нагрузки между источниками
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/datasources.yaml"
        self.datasources: Dict[str, DataSourceInterface] = {}
        self.schemas: Dict[str, DataSourceSchema] = {}
        
        # Регистрируем доступные типы источников
        self.datasource_classes: Dict[DataSourceType, Type[DataSourceInterface]] = {
            DataSourceType.CLICKHOUSE: ClickHouseDataSource,
            DataSourceType.YDB: YDBDataSource,
        }
        
    async def initialize(self) -> bool:
        """Инициализация менеджера источников данных"""
        try:
            logger.info("🚀 Initializing DataSource Manager...")
            
            # Загружаем конфигурацию
            configs = self._load_configuration()
            
            # Регистрируем и подключаем источники
            success_count = 0
            for config in configs:
                try:
                    if await self.register_datasource(config):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Failed to register datasource {config.source_id}: {e}")
            
            logger.info(f"✅ DataSource Manager initialized: {success_count}/{len(configs)} sources")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize DataSource Manager: {e}")
            return False
    
    def _load_configuration(self) -> List[DataSourceConfig]:
        """Загрузка конфигурации источников данных"""
        configs = []
        
        # Загрузка из YAML файла
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    yaml_config = yaml.safe_load(f)
                    configs.extend(self._parse_yaml_config(yaml_config))
            except Exception as e:
                logger.warning(f"Failed to load YAML config: {e}")
        
        # Загрузка из переменных окружения
        env_configs = self._load_env_configuration()
        configs.extend(env_configs)
        
        return configs
    
    def _parse_yaml_config(self, yaml_config: Dict[str, Any]) -> List[DataSourceConfig]:
        """Парсинг YAML конфигурации"""
        configs = []
        
        datasources_config = yaml_config.get("datasources", {})
        
        # ClickHouse источники
        for source_id, source_config in datasources_config.get("clickhouse", {}).items():
            config = DataSourceConfig(
                source_id=source_id,
                source_type=DataSourceType.CLICKHOUSE,
                name=source_config.get("name", source_id),
                enabled=source_config.get("enabled", True),
                host=source_config.get("host"),
                port=source_config.get("port", 8123),
                database=source_config.get("database", "default"),
                username=source_config.get("username", "default"),
                password=source_config.get("password", ""),
                ssl_enabled=source_config.get("ssl", False),
                timeout_seconds=source_config.get("timeout", 30),
                max_connections=source_config.get("max_connections", 10),
                extra_params=source_config.get("extra_params", {}),
                description=source_config.get("description"),
                tags=source_config.get("tags", [])
            )
            configs.append(config)
        
        # YDB источники
        for source_id, source_config in datasources_config.get("ydb", {}).items():
            config = DataSourceConfig(
                source_id=source_id,
                source_type=DataSourceType.YDB,
                name=source_config.get("name", source_id),
                enabled=source_config.get("enabled", True),
                host=source_config.get("endpoint"),
                port=source_config.get("port", 2135),
                database=source_config.get("database"),
                ssl_enabled=source_config.get("ssl", True),
                timeout_seconds=source_config.get("timeout", 30),
                extra_params={
                    "auth_method": source_config.get("auth_method", "metadata"),
                    "service_account_key_file": source_config.get("service_account_key_file"),
                    "oauth_token": source_config.get("oauth_token"),
                    **source_config.get("extra_params", {})
                },
                description=source_config.get("description"),
                tags=source_config.get("tags", [])
            )
            configs.append(config)
        
        return configs
    
    def _load_env_configuration(self) -> List[DataSourceConfig]:
        """Загрузка конфигурации из переменных окружения"""
        configs = []
        
        # Поиск переменных с префиксом DS_
        env_prefixes = ["DS_CLICKHOUSE_", "DS_YDB_"]
        
        for prefix in env_prefixes:
            source_type = DataSourceType.CLICKHOUSE if "CLICKHOUSE" in prefix else DataSourceType.YDB
            
            # Извлекаем все переменные с данным префиксом
            source_vars = {}
            for key, value in os.environ.items():
                if key.startswith(prefix):
                    param_name = key[len(prefix):].lower()
                    source_vars[param_name] = value
            
            if not source_vars:
                continue
            
            # Создаем конфигурацию из ENV переменных
            source_id = source_vars.get("source_id", f"env_{source_type.value}")
            
            if source_type == DataSourceType.CLICKHOUSE:
                config = DataSourceConfig(
                    source_id=source_id,
                    source_type=source_type,
                    name=source_vars.get("name", source_id),
                    enabled=source_vars.get("enabled", "true").lower() == "true",
                    host=source_vars.get("host"),
                    port=int(source_vars.get("port", "8123")),
                    database=source_vars.get("database", "default"),
                    username=source_vars.get("username", "default"),
                    password=source_vars.get("password", ""),
                    ssl_enabled=source_vars.get("ssl", "false").lower() == "true",
                    timeout_seconds=int(source_vars.get("timeout", "30")),
                    description=source_vars.get("description")
                )
            else:  # YDB
                config = DataSourceConfig(
                    source_id=source_id,
                    source_type=source_type,
                    name=source_vars.get("name", source_id),
                    enabled=source_vars.get("enabled", "true").lower() == "true",
                    host=source_vars.get("endpoint"),
                    port=int(source_vars.get("port", "2135")),
                    database=source_vars.get("database"),
                    ssl_enabled=source_vars.get("ssl", "true").lower() == "true",
                    timeout_seconds=int(source_vars.get("timeout", "30")),
                    extra_params={
                        "auth_method": source_vars.get("auth_method", "metadata"),
                        "service_account_key_file": source_vars.get("service_account_key_file"),
                        "oauth_token": source_vars.get("oauth_token")
                    },
                    description=source_vars.get("description")
                )
            
            configs.append(config)
        
        return configs
    
    async def register_datasource(self, config: DataSourceConfig) -> bool:
        """Регистрация нового источника данных"""
        try:
            if not config.enabled:
                logger.info(f"Datasource {config.source_id} is disabled, skipping")
                return False
            
            # Получаем класс для типа источника
            datasource_class = self.datasource_classes.get(config.source_type)
            if not datasource_class:
                logger.error(f"Unsupported datasource type: {config.source_type}")
                return False
            
            # Создаем экземпляр источника данных
            datasource = datasource_class(config)
            
            # Подключаемся
            if await datasource.connect():
                self.datasources[config.source_id] = datasource
                
                # Автодетекция схемы
                try:
                    schema = await datasource.get_schema()
                    self.schemas[config.source_id] = schema
                    logger.info(f"✅ Schema detected for {config.source_id}: {len(schema.tables)} tables")
                except Exception as e:
                    logger.warning(f"Schema detection failed for {config.source_id}: {e}")
                
                logger.info(f"✅ Registered datasource: {config.source_id}")
                return True
            else:
                logger.error(f"❌ Failed to connect datasource: {config.source_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to register datasource {config.source_id}: {e}")
            return False
    
    async def get_datasource(self, source_id: str) -> Optional[DataSourceInterface]:
        """Получение источника данных по ID"""
        return self.datasources.get(source_id)
    
    async def get_enabled_datasources(self, source_types: Optional[List[DataSourceType]] = None) -> List[DataSourceInterface]:
        """Получение списка активных источников данных"""
        datasources = []
        
        for source_id, datasource in self.datasources.items():
            if source_types and datasource.config.source_type not in source_types:
                continue
            
            if datasource.config.enabled:
                datasources.append(datasource)
        
        return datasources
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Проверка состояния всех источников данных"""
        results = {}
        
        tasks = []
        for source_id, datasource in self.datasources.items():
            tasks.append(datasource.health_check())
        
        if tasks:
            health_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, (source_id, datasource) in enumerate(self.datasources.items()):
                result = health_results[i]
                if isinstance(result, Exception):
                    results[source_id] = {
                        "status": "error",
                        "error": str(result),
                        "source_type": datasource.config.source_type.value
                    }
                else:
                    results[source_id] = result
        
        return {
            "total_sources": len(self.datasources),
            "healthy_sources": sum(1 for r in results.values() if r.get("status") == "healthy"),
            "sources": results,
            "check_time": datetime.now().isoformat()
        }
    
    async def close_all(self) -> bool:
        """Закрытие всех подключений"""
        try:
            tasks = []
            for datasource in self.datasources.values():
                tasks.append(datasource.close())
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
            self.datasources.clear()
            self.schemas.clear()
            
            logger.info("✅ All datasources closed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to close datasources: {e}")
            return False
    
    def get_available_datasources(self) -> List[Dict[str, Any]]:
        """Получение списка доступных источников для UI"""
        sources = []
        
        for source_id, datasource in self.datasources.items():
            info = datasource.get_connection_info()
            schema = self.schemas.get(source_id)
            
            info.update({
                "schema_available": schema is not None,
                "tables_count": len(schema.tables) if schema else 0,
                "last_schema_detection": schema.detected_at.isoformat() if schema and schema.detected_at else None
            })
            
            sources.append(info)
        
        return sources


# Глобальный экземпляр менеджера
_datasource_manager: Optional[DataSourceManager] = None


async def get_datasource_manager() -> DataSourceManager:
    """Получение глобального экземпляра менеджера источников данных"""
    global _datasource_manager
    if _datasource_manager is None:
        _datasource_manager = DataSourceManager()
        await _datasource_manager.initialize()
    return _datasource_manager


async def initialize_datasource_manager(config_path: Optional[str] = None) -> DataSourceManager:
    """Инициализация менеджера источников данных"""
    global _datasource_manager
    _datasource_manager = DataSourceManager(config_path)
    await _datasource_manager.initialize()
    return _datasource_manager 