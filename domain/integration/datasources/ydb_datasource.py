"""
YDB DataSource Adapter for ETL Pipeline
Enhanced version with full ETL support including change detection and schema introspection
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import ydb
import ydb.iam
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
class YDBConnectionConfig:
    """YDB connection configuration"""
    endpoint: str
    database: str
    auth_method: str = "env"  # env, token, static, service_account, metadata, anonymous
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    service_account_key_file: Optional[str] = None
    table_filter: Optional[str] = None  # Filter tables for sync
    sync_mode: str = "incremental"  # incremental or full
    last_modified_column: Optional[str] = "updated_at"  # Column for change detection
    batch_size: int = 1000
    timeout: int = 30


class YDBDataSource(DataSourceInterface):
    """Enhanced YDB DataSource with full ETL capabilities"""

    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.driver: Optional[ydb.Driver] = None
        self.session_pool: Optional[ydb.QuerySessionPool] = None
        self.ydb_config: YDBConnectionConfig = self._parse_config(config.connection_params)
        self._last_sync_timestamp: Optional[datetime] = None

    def _parse_config(self, params: Dict[str, Any]) -> YDBConnectionConfig:
        """Parse connection parameters into YDB config"""
        return YDBConnectionConfig(
            endpoint=params.get('endpoint', ''),
            database=params.get('database', ''),
            auth_method=params.get('auth_method', 'env'),
            token=params.get('token'),
            username=params.get('username'),
            password=params.get('password'),
            service_account_key_file=params.get('service_account_key_file'),
            table_filter=params.get('table_filter'),
            sync_mode=params.get('sync_mode', 'incremental'),
            last_modified_column=params.get('last_modified_column', 'updated_at'),
            batch_size=params.get('batch_size', 1000),
            timeout=params.get('timeout', 30)
        )

    async def connect(self) -> bool:
        """Establish connection to YDB"""
        try:
            logger.info(f"Connecting to YDB: {self.ydb_config.endpoint}")
            
            # Prepare credentials based on auth method
            credentials = self._get_credentials()
            
            # Create driver configuration
            if self.ydb_config.endpoint.startswith('grpc://') or self.ydb_config.endpoint.startswith('grpcs://'):
                # Using connection string
                self.driver = ydb.Driver(
                    connection_string=f"{self.ydb_config.endpoint}{self.ydb_config.database}",
                    credentials=credentials
                )
            else:
                # Using separate endpoint and database
                driver_config = ydb.DriverConfig(
                    endpoint=self.ydb_config.endpoint,
                    database=self.ydb_config.database
                )
                self.driver = ydb.Driver(driver_config=driver_config, credentials=credentials)
            
            # Wait for driver to be ready
            await asyncio.wait_for(
                asyncio.to_thread(self.driver.wait),
                timeout=self.ydb_config.timeout
            )
            
            # Create session pool
            self.session_pool = ydb.QuerySessionPool(self.driver)
            
            self._status = ConnectionStatus.CONNECTED
            logger.info(f"✅ Successfully connected to YDB: {self.config.source_id}")
            return True
            
        except Exception as e:
            self._status = ConnectionStatus.ERROR
            logger.error(f"❌ Failed to connect to YDB {self.config.source_id}: {e}")
            return False

    def _get_credentials(self):
        """Get YDB credentials based on auth method"""
        auth_method = self.ydb_config.auth_method.lower()
        
        if auth_method == "env":
            return ydb.credentials_from_env_variables()
        elif auth_method == "token":
            if not self.ydb_config.token:
                raise ValueError("Token is required for token auth method")
            return ydb.credentials.AccessTokenCredentials(self.ydb_config.token)
        elif auth_method == "static":
            if not self.ydb_config.username or not self.ydb_config.password:
                raise ValueError("Username and password are required for static auth")
            return ydb.StaticCredentials.from_user_password(
                self.ydb_config.username, 
                self.ydb_config.password
            )
        elif auth_method == "service_account":
            if not self.ydb_config.service_account_key_file:
                raise ValueError("Service account key file is required")
            return ydb.iam.ServiceAccountCredentials.from_file(
                self.ydb_config.service_account_key_file
            )
        elif auth_method == "metadata":
            return ydb.iam.MetadataUrlCredentials()
        elif auth_method == "anonymous":
            return ydb.credentials.AnonymousCredentials()
        else:
            raise ValueError(f"Unsupported auth method: {auth_method}")

    async def close(self) -> bool:
        """Close YDB connection"""
        try:
            if self.session_pool:
                await asyncio.to_thread(self.session_pool.close)
                self.session_pool = None
                
            if self.driver:
                await asyncio.to_thread(self.driver.close)
                self.driver = None
            
            self._status = ConnectionStatus.DISCONNECTED
            logger.info(f"✅ YDB connection closed: {self.config.source_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error closing YDB connection {self.config.source_id}: {e}")
            return False

    async def get_schema(self) -> DataSourceSchema:
        """Get schema information from YDB"""
        if not self._is_connected():
            raise RuntimeError("Not connected to YDB")

        try:
            tables = await self._discover_tables()
            schema = DataSourceSchema(
                source_id=self.config.source_id,
                tables=tables,
                total_tables=len(tables),
                discovered_at=datetime.now()
            )
            
            logger.info(f"📊 Discovered {len(tables)} tables in YDB: {self.config.source_id}")
            return schema
            
        except Exception as e:
            logger.error(f"❌ Failed to get YDB schema {self.config.source_id}: {e}")
            raise

    async def _discover_tables(self) -> List[Dict[str, Any]]:
        """Discover tables in YDB database"""
        query = """
        SELECT table_name, table_type 
        FROM information_schema.tables 
        WHERE table_schema = ?
        """
        
        try:
            result = await self._execute_query(query, [self.ydb_config.database])
            
            tables = []
            for row in result.rows:
                table_name = row[0]
                table_type = row[1]
                
                # Apply table filter if specified
                if self.ydb_config.table_filter and self.ydb_config.table_filter not in table_name:
                    continue
                
                # Get column information
                columns = await self._get_table_columns(table_name)
                
                tables.append({
                    "name": table_name,
                    "type": table_type,
                    "columns": columns,
                    "row_count": await self._get_table_row_count(table_name)
                })
            
            return tables
            
        except Exception as e:
            logger.warning(f"Failed to discover tables, falling back to manual discovery: {e}")
            return await self._manual_table_discovery()

    async def _manual_table_discovery(self) -> List[Dict[str, Any]]:
        """Manual table discovery when information_schema is not available"""
        # For YDB, we might need to use SHOW TABLES or similar
        try:
            result = await self._execute_query("SHOW TABLES", [])
            tables = []
            
            for row in result.rows:
                table_name = row[0]
                
                if self.ydb_config.table_filter and self.ydb_config.table_filter not in table_name:
                    continue
                
                columns = await self._get_table_columns(table_name)
                
                tables.append({
                    "name": table_name,
                    "type": "table",
                    "columns": columns,
                    "row_count": await self._get_table_row_count(table_name)
                })
            
            return tables
            
        except Exception as e:
            logger.error(f"Manual table discovery failed: {e}")
            return []

    async def _get_table_columns(self, table_name: str) -> List[ColumnInfo]:
        """Get column information for a table"""
        query = f"DESCRIBE TABLE `{table_name}`"
        
        try:
            result = await self._execute_query(query, [])
            columns = []
            
            for row in result.rows:
                columns.append(ColumnInfo(
                    name=row[0],
                    type=row[1],
                    nullable=row[2] == "YES",
                    primary_key=row[3] == "YES" if len(row) > 3 else False
                ))
            
            return columns
            
        except Exception as e:
            logger.warning(f"Failed to get columns for table {table_name}: {e}")
            return []

    async def _get_table_row_count(self, table_name: str) -> int:
        """Get row count for a table"""
        try:
            result = await self._execute_query(f"SELECT COUNT(*) FROM `{table_name}`", [])
            return result.rows[0][0] if result.rows else 0
        except Exception as e:
            logger.warning(f"Failed to get row count for {table_name}: {e}")
            return 0

    async def query(self, sql: str, params: Optional[List[Any]] = None) -> QueryResult:
        """Execute SQL query"""
        if not self._is_connected():
            raise RuntimeError("Not connected to YDB")

        try:
            return await self._execute_query(sql, params or [])
        except Exception as e:
            logger.error(f"❌ Query failed in YDB {self.config.source_id}: {e}")
            raise

    async def _execute_query(self, sql: str, params: List[Any]) -> QueryResult:
        """Execute query using session pool"""
        start_time = datetime.now()
        
        def execute_in_session(session):
            return session.transaction().execute(
                sql,
                parameters=params,
                commit_tx=True
            )
        
        try:
            result = await asyncio.to_thread(
                self.session_pool.retry_operation_sync,
                execute_in_session
            )
            
            # Convert result to QueryResult
            rows = []
            columns = []
            
            if hasattr(result, 'result_sets') and result.result_sets:
                result_set = result.result_sets[0]
                
                # Extract column names
                if hasattr(result_set, 'columns'):
                    columns = [col.name for col in result_set.columns]
                
                # Extract rows
                for row in result_set.rows:
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
            logger.error(f"Query execution failed: {e}")
            raise

    async def stream(self, sql: str, params: Optional[List[Any]] = None, batch_size: int = 1000):
        """Stream query results in batches"""
        if not self._is_connected():
            raise RuntimeError("Not connected to YDB")

        offset = 0
        while True:
            # Add LIMIT and OFFSET to the query
            paginated_sql = f"{sql} LIMIT {batch_size} OFFSET {offset}"
            
            try:
                result = await self._execute_query(paginated_sql, params or [])
                
                if not result.rows:
                    break
                
                yield result.rows
                
                if len(result.rows) < batch_size:
                    break
                
                offset += batch_size
                
            except Exception as e:
                logger.error(f"❌ Stream query failed: {e}")
                break

    async def fetch_changes(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch changed records since specified timestamp"""
        if not self._is_connected():
            raise RuntimeError("Not connected to YDB")

        try:
            if since is None:
                since = self._last_sync_timestamp or datetime.now() - timedelta(days=1)

            logger.info(f"🔄 Fetching YDB changes since {since}")
            
            tables = await self._discover_tables()
            all_changes = []
            
            for table in tables:
                table_name = table["name"]
                
                # Check if table has timestamp column for incremental sync
                if self.ydb_config.sync_mode == "incremental":
                    timestamp_column = self._find_timestamp_column(table["columns"])
                    if timestamp_column:
                        changes = await self._fetch_table_changes(table_name, timestamp_column, since)
                        all_changes.extend(changes)
                        continue
                
                # Fall back to full table scan for tables without timestamp
                logger.info(f"📊 Full sync for table {table_name} (no timestamp column)")
                changes = await self._fetch_full_table(table_name)
                all_changes.extend(changes)
            
            self._last_sync_timestamp = datetime.now()
            logger.info(f"✅ Fetched {len(all_changes)} changes from YDB")
            
            return all_changes
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch changes from YDB: {e}")
            raise

    def _find_timestamp_column(self, columns: List[ColumnInfo]) -> Optional[str]:
        """Find timestamp column for change detection"""
        # First try configured column
        if self.ydb_config.last_modified_column:
            for col in columns:
                if col.name == self.ydb_config.last_modified_column:
                    return col.name
        
        # Try common timestamp column names
        timestamp_columns = ['updated_at', 'modified_at', 'last_modified', 'timestamp', 'created_at']
        for col in columns:
            if col.name.lower() in timestamp_columns and 'timestamp' in col.type.lower():
                return col.name
        
        return None

    async def _fetch_table_changes(self, table_name: str, timestamp_column: str, since: datetime) -> List[Dict[str, Any]]:
        """Fetch changes from a specific table"""
        query = f"""
        SELECT * FROM `{table_name}` 
        WHERE `{timestamp_column}` > ?
        ORDER BY `{timestamp_column}`
        """
        
        changes = []
        async for batch in self.stream(query, [since], self.ydb_config.batch_size):
            for row in batch:
                changes.append({
                    "table": table_name,
                    "operation": "upsert",  # YDB doesn't distinguish insert/update
                    "data": row,
                    "timestamp": datetime.now()
                })
        
        return changes

    async def _fetch_full_table(self, table_name: str) -> List[Dict[str, Any]]:
        """Fetch all records from a table"""
        query = f"SELECT * FROM `{table_name}`"
        
        changes = []
        async for batch in self.stream(query, [], self.ydb_config.batch_size):
            for row in batch:
                changes.append({
                    "table": table_name,
                    "operation": "upsert",
                    "data": row,
                    "timestamp": datetime.now()
                })
        
        return changes

    def _is_connected(self) -> bool:
        """Check if connection is active"""
        return (
            self._status == ConnectionStatus.CONNECTED and 
            self.driver is not None and 
            self.session_pool is not None
        )

    async def test_connection(self) -> Tuple[bool, str]:
        """Test YDB connection"""
        try:
            if not self._is_connected():
                return False, "Not connected"
            
            # Simple test query
            result = await self._execute_query("SELECT 1 as test", [])
            if result.rows and result.rows[0][0] == 1:
                return True, "Connection successful"
            else:
                return False, "Test query failed"
                
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"

    async def get_health_info(self) -> Dict[str, Any]:
        """Get YDB health information"""
        health_info = {
            "status": self._status.value,
            "source_id": self.config.source_id,
            "connection_config": {
                "endpoint": self.ydb_config.endpoint,
                "database": self.ydb_config.database,
                "auth_method": self.ydb_config.auth_method
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
            except Exception as e:
                health_info.update({
                    "test_connection": False,
                    "test_message": str(e)
                })
        
        return health_info 