"""
Unified DataSource Interface
Единый интерфейс для всех источников данных
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Типы источников данных"""
    POSTGRESQL = "postgresql"
    CLICKHOUSE = "clickhouse"
    YDB = "ydb"
    CONFLUENCE = "confluence"
    JIRA = "jira"
    GITLAB = "gitlab"
    LOCAL_FILES = "local_files"
    S3 = "s3"
    ELASTICSEARCH = "elasticsearch"


class ConnectionStatus(Enum):
    """Статусы подключения"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class DataSourceConfig:
    """Конфигурация источника данных"""
    source_id: str
    source_type: DataSourceType
    name: str
    enabled: bool = True
    
    # Connection parameters
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Advanced parameters
    ssl_enabled: bool = False
    ssl_verify: bool = True
    timeout_seconds: int = 30
    max_connections: int = 10
    
    # Additional parameters from environment or config
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class SchemaField:
    """Описание поля схемы"""
    name: str
    type: str
    nullable: bool = True
    description: Optional[str] = None
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TableSchema:
    """Схема таблицы/коллекции"""
    name: str
    fields: List[SchemaField]
    primary_keys: List[str] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataSourceSchema:
    """Схема источника данных"""
    source_id: str
    format_type: str  # 'sql', 'json', 'parquet', 'proto', etc.
    tables: List[TableSchema] = field(default_factory=list)
    schema_path: Optional[str] = None  # Путь к файлу схемы для JSON/Parquet/Proto
    detected_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryResult:
    """Результат выполнения запроса"""
    data: List[Dict[str, Any]]
    total_rows: int
    affected_rows: int = 0
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataSourceInterface(ABC):
    """
    Единый интерфейс для всех источников данных
    
    Методы:
    - connect, close: управление соединением
    - get_schema: автодетекция схемы данных  
    - query: выполнение запросов
    - stream: потоковое чтение данных
    """
    
    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.status = ConnectionStatus.DISCONNECTED
        self.connection = None
        self.schema: Optional[DataSourceSchema] = None
        
    @abstractmethod
    async def connect(self) -> bool:
        """
        Установить соединение с источником данных
        
        Returns:
            True если соединение успешно установлено
        """
        pass
    
    @abstractmethod
    async def close(self) -> bool:
        """
        Закрыть соединение с источником данных
        
        Returns:
            True если соединение успешно закрыто
        """
        pass
    
    @abstractmethod
    async def get_schema(self) -> DataSourceSchema:
        """
        Получить схему данных с автодетекцией
        
        Для SQL БД: получить структуру таблиц {column -> type}
        Для NoSQL/файлов: сохранить формат и путь к схеме
        
        Returns:
            Схема источника данных
        """
        pass
    
    @abstractmethod
    async def query(self, query_text: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """
        Выполнить запрос к источнику данных
        
        Args:
            query_text: Текст запроса (SQL, JSON path, etc.)
            params: Параметры запроса
            
        Returns:
            Результат выполнения запроса
        """
        pass
    
    @abstractmethod
    async def stream(self, query_text: str, batch_size: int = 1000) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """
        Потоковое чтение данных из источника
        
        Args:
            query_text: Текст запроса
            batch_size: Размер батча для чтения
            
        Yields:
            Батчи данных
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Проверка состояния источника данных
        
        Returns:
            Информация о состоянии
        """
        try:
            if self.status != ConnectionStatus.CONNECTED:
                await self.connect()
            
            # Простой запрос для проверки
            result = await self.query("SELECT 1", {})
            
            return {
                "status": "healthy",
                "connected": True,
                "source_id": self.config.source_id,
                "source_type": self.config.source_type.value,
                "response_time_ms": result.execution_time_ms,
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed for {self.config.source_id}: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "source_id": self.config.source_id,
                "source_type": self.config.source_type.value,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Получить информацию о подключении (без чувствительных данных)
        
        Returns:
            Безопасная информация о подключении
        """
        return {
            "source_id": self.config.source_id,
            "source_type": self.config.source_type.value,
            "name": self.config.name,
            "status": self.status.value,
            "host": self.config.host,
            "port": self.config.port,
            "database": self.config.database,
            "ssl_enabled": self.config.ssl_enabled,
            "timeout_seconds": self.config.timeout_seconds,
            "enabled": self.config.enabled,
            "description": self.config.description,
            "tags": self.config.tags
        } 