"""
ClickHouse DataSource Adapter for ETL Pipeline
Enhanced version with full ETL support including change detection and schema introspection
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

# Optional ClickHouse imports
try:
    import clickhouse_connect
    CLICKHOUSE_AVAILABLE = True
except ImportError:
    CLICKHOUSE_AVAILABLE = False
    clickhouse_connect = None

from dataclasses import dataclass

from ..datasource_interface import (
    DataSourceInterface,
    DataSourceConfig,
    ConnectionStatus,
    DataSourceSchema,
    QueryResult,
    ColumnInfo
)

logger = logging.getLogger(__name__)


@dataclass
class ClickHouseConnectionConfig:
    """ClickHouse connection configuration"""
    host: str
    port: int = 8123
    database: str = "default"
    username: str = "default"
    password: Optional[str] = None
    secure: bool = False
    verify: bool = True
    ca_cert: Optional[str] = None
    client_cert: Optional[str] = None
    client_cert_key: Optional[str] = None
    table_filter: Optional[str] = None  # Filter tables for sync
    sync_mode: str = "incremental"  # incremental or full
    last_modified_column: Optional[str] = "updated_at"  # Column for change detection
    batch_size: int = 10000  # ClickHouse handles large batches well
    timeout: int = 30
    settings: Optional[Dict[str, Any]] = None  # Custom ClickHouse settings


class ClickHouseDataSource(DataSourceInterface):
    """Enhanced ClickHouse DataSource with full ETL capabilities"""

    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        if not CLICKHOUSE_AVAILABLE:
            raise ImportError("clickhouse_connect package is required for ClickHouse datasource")
        self.client: Optional[clickhouse_connect.driver.Client] = None
        self.ch_config: ClickHouseConnectionConfig = self._parse_config(config.connection_params)
        self._last_sync_timestamp: Optional[datetime] = None

    def _parse_config(self, params: Dict[str, Any]) -> ClickHouseConnectionConfig:
        """Parse connection parameters into ClickHouse config"""
        # Handle URL format
        if 'url' in params:
            parsed = urlparse(params['url'])
            host = parsed.hostname or 'localhost'
            port = parsed.port or 8123
            database = parsed.path.lstrip('/') or 'default'
            username = parsed.username or 'default'
            password = parsed.password
            secure = parsed.scheme == 'https'
        else:
            host = params.get('host', 'localhost')
            port = params.get('port', 8123)
            database = params.get('database', 'default')
            username = params.get('username', 'default')
            password = params.get('password')
            secure = params.get('secure', False)

        return ClickHouseConnectionConfig(
            host=host,
            port=int(port),
            database=database,
            username=username,
            password=password,
            secure=secure,
            verify=params.get('verify', True),
            ca_cert=params.get('ca_cert'),
            client_cert=params.get('client_cert'),
            client_cert_key=params.get('client_cert_key'),
            table_filter=params.get('table_filter'),
            sync_mode=params.get('sync_mode', 'incremental'),
            last_modified_column=params.get('last_modified_column', 'updated_at'),
            batch_size=params.get('batch_size', 10000),
            timeout=params.get('timeout', 30),
            settings=params.get('settings', {})
        )

    async def connect(self) -> bool:
        """Establish connection to ClickHouse"""
        try:
            logger.info(f"Connecting to ClickHouse: {self.ch_config.host}:{self.ch_config.port}")
            
            # Prepare connection parameters
            connect_params = {
                'host': self.ch_config.host,
                'port': self.ch_config.port,
                'database': self.ch_config.database,
                'username': self.ch_config.username,
                'connect_timeout': self.ch_config.timeout,
                'send_receive_timeout': self.ch_config.timeout,
                'secure': self.ch_config.secure,
                'verify': self.ch_config.verify
            }
            
            # Add password if provided
            if self.ch_config.password:
                connect_params['password'] = self.ch_config.password
            
            # Add SSL certificates if provided
            if self.ch_config.ca_cert:
                connect_params['ca_cert'] = self.ch_config.ca_cert
            if self.ch_config.client_cert:
                connect_params['client_cert'] = self.ch_config.client_cert
            if self.ch_config.client_cert_key:
                connect_params['client_cert_key'] = self.ch_config.client_cert_key
            
            # Add custom settings
            if self.ch_config.settings:
                connect_params['settings'] = self.ch_config.settings
            
            # Create client connection
            self.client = await asyncio.to_thread(
                clickhouse_connect.get_client,
                **connect_params
            )
            
            # Test connection with a simple query
            await asyncio.to_thread(self.client.command, "SELECT 1")
            
            self._status = ConnectionStatus.CONNECTED
            logger.info(f"✅ Successfully connected to ClickHouse: {self.config.source_id}")
            return True
            
        except Exception as e:
            self._status = ConnectionStatus.ERROR
            logger.error(f"❌ Failed to connect to ClickHouse {self.config.source_id}: {e}")
            return False

    async def close(self) -> bool:
        """Close ClickHouse connection"""
        try:
            if self.client:
                await asyncio.to_thread(self.client.close)
                self.client = None
            
            self._status = ConnectionStatus.DISCONNECTED
            logger.info(f"✅ ClickHouse connection closed: {self.config.source_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error closing ClickHouse connection {self.config.source_id}: {e}")
            return False

    async def get_schema(self) -> DataSourceSchema:
        """Get schema information from ClickHouse"""
        if not self._is_connected():
            raise RuntimeError("Not connected to ClickHouse")

        try:
            tables = await self._discover_tables()
            schema = DataSourceSchema(
                source_id=self.config.source_id,
                tables=tables,
                total_tables=len(tables),
                discovered_at=datetime.now()
            )
            
            logger.info(f"📊 Discovered {len(tables)} tables in ClickHouse: {self.config.source_id}")
            return schema
            
        except Exception as e:
            logger.error(f"❌ Failed to get ClickHouse schema {self.config.source_id}: {e}")
            raise

    async def _discover_tables(self) -> List[Dict[str, Any]]:
        """Discover tables in ClickHouse database"""
        query = """
        SELECT name, engine, total_rows, total_bytes
        FROM system.tables 
        WHERE database = {database:String}
        AND name NOT LIKE '.%'
        """
        
        try:
            result = await self._execute_query(query, {'database': self.ch_config.database})
            
            tables = []
            for row in result.rows:
                table_name = row[0]
                engine = row[1]
                total_rows = row[2] if len(row) > 2 else 0
                total_bytes = row[3] if len(row) > 3 else 0
                
                # Apply table filter if specified
                if self.ch_config.table_filter and self.ch_config.table_filter not in table_name:
                    continue
                
                # Get column information
                columns = await self._get_table_columns(table_name)
                
                tables.append({
                    "name": table_name,
                    "type": "table",
                    "engine": engine,
                    "columns": columns,
                    "row_count": total_rows,
                    "size_bytes": total_bytes,
                    "metadata": {
                        "engine": engine,
                        "database": self.ch_config.database
                    }
                })
            
            return tables
            
        except Exception as e:
            logger.error(f"Failed to discover ClickHouse tables: {e}")
            return []

    async def _get_table_columns(self, table_name: str) -> List[ColumnInfo]:
        """Get column information for a ClickHouse table"""
        query = """
        SELECT name, type, default_kind, is_in_primary_key
        FROM system.columns 
        WHERE database = {database:String} AND table = {table:String}
        ORDER BY position
        """
        
        try:
            result = await self._execute_query(query, {
                'database': self.ch_config.database,
                'table': table_name
            })
            
            columns = []
            for row in result.rows:
                column_name = row[0]
                column_type = row[1]
                default_kind = row[2] if len(row) > 2 else None
                is_primary_key = bool(row[3]) if len(row) > 3 else False
                
                # ClickHouse nullable types are wrapped in Nullable()
                nullable = column_type.startswith('Nullable(')
                
                columns.append(ColumnInfo(
                    name=column_name,
                    type=column_type,
                    nullable=nullable,
                    primary_key=is_primary_key,
                    default=default_kind
                ))
            
            return columns
            
        except Exception as e:
            logger.warning(f"Failed to get columns for table {table_name}: {e}")
            return []

    async def query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute SQL query"""
        if not self._is_connected():
            raise RuntimeError("Not connected to ClickHouse")

        try:
            return await self._execute_query(sql, params or {})
        except Exception as e:
            logger.error(f"❌ Query failed in ClickHouse {self.config.source_id}: {e}")
            raise

    async def _execute_query(self, sql: str, params: Dict[str, Any]) -> QueryResult:
        """Execute query using ClickHouse client"""
        start_time = datetime.now()
        
        try:
            # Execute query with parameters
            result = await asyncio.to_thread(
                self.client.query,
                sql,
                parameters=params
            )
            
            # Extract data
            rows = []
            columns = []
            
            if hasattr(result, 'result_columns'):
                columns = [col.name for col in result.result_columns]
            
            if hasattr(result, 'result_rows'):
                for row in result.result_rows:
                    rows.append(list(row))
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return QueryResult(
                rows=rows,
                columns=columns,
                row_count=len(rows),
                execution_time=duration
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"ClickHouse query execution failed: {e}")
            raise

    async def stream(self, sql: str, params: Optional[Dict[str, Any]] = None, batch_size: int = 10000):
        """Stream query results in batches"""
        if not self._is_connected():
            raise RuntimeError("Not connected to ClickHouse")

        try:
            # ClickHouse supports streaming natively
            query_stream = await asyncio.to_thread(
                self.client.query_rows_stream,
                sql,
                parameters=params or {},
                settings={'max_block_size': batch_size}
            )
            
            batch = []
            async for row in query_stream:
                batch.append(list(row))
                
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
            
            # Yield remaining rows
            if batch:
                yield batch
                
        except Exception as e:
            logger.error(f"❌ ClickHouse stream query failed: {e}")
            raise

    async def fetch_changes(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch changed records since specified timestamp"""
        if not self._is_connected():
            raise RuntimeError("Not connected to ClickHouse")

        try:
            if since is None:
                since = self._last_sync_timestamp or datetime.now() - timedelta(days=1)

            logger.info(f"🔄 Fetching ClickHouse changes since {since}")
            
            tables = await self._discover_tables()
            all_changes = []
            
            for table in tables:
                table_name = table["name"]
                engine = table.get("engine", "")
                
                # Skip system and temporary tables
                if table_name.startswith('system.') or engine in ['Memory', 'Buffer']:
                    continue
                
                # Check if table has timestamp column for incremental sync
                if self.ch_config.sync_mode == "incremental":
                    timestamp_column = self._find_timestamp_column(table["columns"])
                    if timestamp_column:
                        changes = await self._fetch_table_changes(table_name, timestamp_column, since)
                        all_changes.extend(changes)
                        continue
                
                # For ClickHouse, we can also check for ReplacingMergeTree tables
                if "Replacing" in engine:
                    changes = await self._fetch_replacing_merge_tree_changes(table_name, since)
                    all_changes.extend(changes)
                    continue
                
                # Fall back to full table scan for tables without timestamp
                logger.info(f"📊 Full sync for table {table_name} (no timestamp column)")
                changes = await self._fetch_full_table(table_name)
                all_changes.extend(changes)
            
            self._last_sync_timestamp = datetime.now()
            logger.info(f"✅ Fetched {len(all_changes)} changes from ClickHouse")
            
            return all_changes
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch changes from ClickHouse: {e}")
            raise

    def _find_timestamp_column(self, columns: List[ColumnInfo]) -> Optional[str]:
        """Find timestamp column for change detection"""
        # First try configured column
        if self.ch_config.last_modified_column:
            for col in columns:
                if col.name == self.ch_config.last_modified_column:
                    return col.name
        
        # Try common timestamp column names and ClickHouse date/datetime types
        timestamp_columns = ['updated_at', 'modified_at', 'last_modified', 'timestamp', 'created_at', 'event_time']
        datetime_types = ['DateTime', 'DateTime64', 'Date', 'Date32']
        
        for col in columns:
            if col.name.lower() in [tc.lower() for tc in timestamp_columns]:
                # Check if it's a datetime type
                for dt_type in datetime_types:
                    if dt_type in col.type:
                        return col.name
        
        return None

    async def _fetch_table_changes(self, table_name: str, timestamp_column: str, since: datetime) -> List[Dict[str, Any]]:
        """Fetch changes from a specific table"""
        query = f"""
        SELECT * FROM `{self.ch_config.database}`.`{table_name}` 
        WHERE `{timestamp_column}` > {{since:DateTime}}
        ORDER BY `{timestamp_column}`
        """
        
        changes = []
        async for batch in self.stream(query, {'since': since}, self.ch_config.batch_size):
            for row in batch:
                changes.append({
                    "table": table_name,
                    "operation": "insert",  # ClickHouse is insert-only
                    "data": row,
                    "timestamp": datetime.now()
                })
        
        return changes

    async def _fetch_replacing_merge_tree_changes(self, table_name: str, since: datetime) -> List[Dict[str, Any]]:
        """Fetch changes from ReplacingMergeTree table"""
        # ReplacingMergeTree tables can have a version column
        query = f"""
        SELECT * FROM `{self.ch_config.database}`.`{table_name}` FINAL
        WHERE _timestamp > {{since:DateTime}}
        ORDER BY _timestamp
        """
        
        changes = []
        try:
            async for batch in self.stream(query, {'since': since}, self.ch_config.batch_size):
                for row in batch:
                    changes.append({
                        "table": table_name,
                        "operation": "upsert",
                        "data": row,
                        "timestamp": datetime.now()
                    })
        except Exception as e:
            # Fallback to regular query if FINAL is not supported
            logger.warning(f"Failed to query with FINAL, falling back to regular query: {e}")
            return await self._fetch_full_table(table_name)
        
        return changes

    async def _fetch_full_table(self, table_name: str) -> List[Dict[str, Any]]:
        """Fetch all records from a table"""
        query = f"SELECT * FROM `{self.ch_config.database}`.`{table_name}`"
        
        changes = []
        async for batch in self.stream(query, {}, self.ch_config.batch_size):
            for row in batch:
                changes.append({
                    "table": table_name,
                    "operation": "insert",
                    "data": row,
                    "timestamp": datetime.now()
                })
        
        return changes

    def _is_connected(self) -> bool:
        """Check if connection is active"""
        return self._status == ConnectionStatus.CONNECTED and self.client is not None

    async def test_connection(self) -> Tuple[bool, str]:
        """Test ClickHouse connection"""
        try:
            if not self._is_connected():
                return False, "Not connected"
            
            # Test with a simple query
            result = await asyncio.to_thread(self.client.command, "SELECT 1")
            if result == 1:
                return True, "Connection successful"
            else:
                return False, "Test query returned unexpected result"
                
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"

    async def get_health_info(self) -> Dict[str, Any]:
        """Get ClickHouse health information"""
        health_info = {
            "status": self._status.value,
            "source_id": self.config.source_id,
            "connection_config": {
                "host": self.ch_config.host,
                "port": self.ch_config.port,
                "database": self.ch_config.database,
                "username": self.ch_config.username,
                "secure": self.ch_config.secure
            },
            "last_sync": self._last_sync_timestamp.isoformat() if self._last_sync_timestamp else None
        }
        
        if self._is_connected():
            try:
                test_result, test_message = await self.test_connection()
                health_info.update({
                    "test_connection": test_result,
                    "test_message": test_message
                })
                
                # Get server info
                server_info = await asyncio.to_thread(self.client.command, "SELECT version()")
                health_info["server_version"] = server_info
                
                # Get database size info
                size_query = """
                SELECT sum(total_bytes) as total_size, sum(total_rows) as total_rows
                FROM system.tables 
                WHERE database = {database:String}
                """
                size_result = await self._execute_query(size_query, {'database': self.ch_config.database})
                if size_result.rows:
                    health_info.update({
                        "database_size_bytes": size_result.rows[0][0] or 0,
                        "total_rows": size_result.rows[0][1] or 0
                    })
                
            except Exception as e:
                health_info.update({
                    "test_connection": False,
                    "test_message": str(e)
                })
        
        return health_info

    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific table"""
        if not self._is_connected():
            raise RuntimeError("Not connected to ClickHouse")
        
        try:
            # Get table metadata
            table_query = """
            SELECT engine, total_rows, total_bytes, create_table_query
            FROM system.tables 
            WHERE database = {database:String} AND name = {table:String}
            """
            
            table_result = await self._execute_query(table_query, {
                'database': self.ch_config.database,
                'table': table_name
            })
            
            if not table_result.rows:
                raise ValueError(f"Table {table_name} not found")
            
            table_info = {
                "name": table_name,
                "database": self.ch_config.database,
                "engine": table_result.rows[0][0],
                "total_rows": table_result.rows[0][1],
                "total_bytes": table_result.rows[0][2],
                "create_query": table_result.rows[0][3] if len(table_result.rows[0]) > 3 else None,
                "columns": await self._get_table_columns(table_name)
            }
            
            return table_info
            
        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {e}")
            raise 