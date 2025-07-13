"""
Database Optimizer for AI Assistant MVP
Enhanced with standardized async patterns for enterprise reliability
Version: 2.1 Async Optimized

Features:
- AsyncPG connection pooling with timeout protection
- Query optimization and monitoring with retry logic
- Database performance metrics with concurrent collection
- Connection health monitoring with enhanced error handling
"""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import asyncpg
import psutil
from asyncpg import Pool

# Import standardized async patterns
from app.core.async_utils import (AsyncTimeouts, async_retry,
                                  create_background_task, safe_gather,
                                  with_timeout)
from app.core.exceptions import AsyncRetryError, AsyncTimeoutError

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """
    High-performance database optimizer with connection pooling
    Enhanced with standardized async patterns for enterprise reliability

    Features:
    - Connection pooling for PostgreSQL with timeout protection
    - Query performance monitoring with retry logic
    - Health checks and metrics with concurrent collection
    - Async operation optimization with error recovery
    """

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[Pool] = None
        self.query_stats = {}
        self.connection_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "failed_queries": 0,
            "timeout_errors": 0,
            "retry_attempts": 0,
            "avg_response_time": 0.0,
            "total_response_time": 0.0,
        }

        # Performance thresholds
        self.slow_query_threshold = float(
            os.getenv("SLOW_QUERY_THRESHOLD", "0.1")
        )  # 100ms

    @async_retry(max_attempts=3, delay=2.0, exceptions=(asyncpg.PostgresError, OSError))
    async def initialize_pool(self, min_size: int = 5, max_size: int = 20):
        """
        Initialize connection pool with optimal settings
        Enhanced with timeout protection and retry logic
        """
        try:
            # Initialize pool with timeout protection
            self.pool = await with_timeout(
                self._create_pool_internal(min_size, max_size),
                AsyncTimeouts.DATABASE_TRANSACTION,  # 30 seconds for pool creation
                f"Database pool initialization timed out (min_size: {min_size}, max_size: {max_size})",
                {
                    "min_size": min_size,
                    "max_size": max_size,
                    "database_url_configured": bool(self.database_url),
                },
            )

            logger.info(
                f"✅ Database pool initialized: {min_size}-{max_size} connections"
            )

            # Test initial connection with timeout
            await with_timeout(
                self._test_initial_connection(),
                AsyncTimeouts.DATABASE_QUERY,  # 10 seconds for test connection
                "Initial database connection test timed out",
                {"operation": "test_initial_connection"},
            )

        except AsyncTimeoutError as e:
            self.connection_stats["timeout_errors"] += 1
            logger.error(f"❌ Database pool initialization timed out: {e}")
            raise
        except Exception as e:
            self.connection_stats["failed_queries"] += 1
            logger.error(f"❌ Failed to initialize database pool: {e}")
            raise

    async def _create_pool_internal(self, min_size: int, max_size: int) -> Pool:
        """Internal pool creation with enhanced configuration"""
        return await asyncpg.create_pool(
            self.database_url,
            min_size=min_size,
            max_size=max_size,
            max_queries=50000,
            max_inactive_connection_lifetime=300.0,
            timeout=30.0,
            command_timeout=60.0,
            server_settings={
                "application_name": "ai_assistant_mvp_optimizer",
                "jit": "off",  # Disable JIT for faster startup on small queries
            },
        )

    async def _test_initial_connection(self):
        """Test initial pool connection"""
        async with self.pool.acquire() as conn:
            await conn.execute("SELECT 1")

    @asynccontextmanager
    async def get_connection(self):
        """
        Get connection from pool with monitoring
        Enhanced with timeout protection and error tracking
        """
        start_time = time.time()
        connection = None

        try:
            if not self.pool:
                await self.initialize_pool()

            # Acquire connection with timeout protection
            connection = await with_timeout(
                self.pool.acquire(),
                AsyncTimeouts.DATABASE_QUERY,  # 10 seconds for connection acquisition
                "Database connection acquisition timed out",
                {"operation": "acquire_connection"},
            )

            yield connection

        except AsyncTimeoutError as e:
            self.connection_stats["timeout_errors"] += 1
            logger.error(f"❌ Database connection timeout: {e}")
            raise
        except Exception as e:
            self.connection_stats["failed_queries"] += 1
            logger.error(f"❌ Database connection error: {e}")
            raise
        finally:
            if connection:
                try:
                    await with_timeout(
                        self.pool.release(connection),
                        AsyncTimeouts.DATABASE_QUERY / 2,  # 5 seconds for release
                        "Connection release timed out",
                        {"operation": "release_connection"},
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Error releasing connection: {e}")

            # Track connection metrics
            response_time = time.time() - start_time
            self._update_stats(response_time)

    @async_retry(
        max_attempts=2, delay=1.0, exceptions=(asyncpg.PostgresError, AsyncTimeoutError)
    )
    async def execute_query(
        self, query: str, *args, query_name: str = None
    ) -> List[Dict]:
        """
        Execute query with performance monitoring
        Enhanced with timeout protection and retry logic
        """
        start_time = time.time()
        query_id = query_name or query[:50]

        try:
            # Calculate dynamic timeout based on query complexity
            timeout = self._calculate_query_timeout(query)

            # Execute query with timeout protection
            result = await with_timeout(
                self._execute_query_internal(query, args),
                timeout,
                f"Query execution timed out (query: {query_id})",
                {
                    "query_id": query_id,
                    "args_count": len(args),
                    "timeout_used": timeout,
                },
            )

            return result

        except AsyncTimeoutError as e:
            self.connection_stats["timeout_errors"] += 1
            logger.error(f"❌ Query execution timed out [{query_id}]: {e}")
            raise
        except Exception as e:
            self.connection_stats["failed_queries"] += 1
            logger.error(f"❌ Query execution failed [{query_id}]: {e}")
            raise
        finally:
            # Track query performance
            execution_time = time.time() - start_time
            self._track_query_performance(query_id, execution_time)

    async def _execute_query_internal(self, query: str, args: tuple) -> List[Dict]:
        """Internal query execution"""
        async with self.get_connection() as conn:
            # Execute query
            if args:
                result = await conn.fetch(query, *args)
            else:
                result = await conn.fetch(query)

            # Convert to list of dicts
            return [dict(row) for row in result]

    def _calculate_query_timeout(self, query: str) -> float:
        """Calculate dynamic timeout based on query complexity"""
        base_timeout = AsyncTimeouts.DATABASE_QUERY  # 10 seconds

        # Analyze query for complexity indicators
        query_lower = query.lower()
        multiplier = 1.0

        # Complex operations need more time
        if any(keyword in query_lower for keyword in ["join", "group by", "order by"]):
            multiplier *= 1.5
        if "create index" in query_lower:
            multiplier *= 3.0
        if any(keyword in query_lower for keyword in ["alter table", "create table"]):
            multiplier *= 2.0
        if "vacuum" in query_lower or "analyze" in query_lower:
            multiplier *= 4.0

        return min(base_timeout * multiplier, AsyncTimeouts.DATABASE_MIGRATION)

    @async_retry(
        max_attempts=2, delay=1.0, exceptions=(asyncpg.PostgresError, AsyncTimeoutError)
    )
    async def execute_query_one(
        self, query: str, *args, query_name: str = None
    ) -> Optional[Dict]:
        """
        Execute query expecting single result
        Enhanced with timeout protection and retry logic
        """
        start_time = time.time()
        query_id = query_name or query[:50]

        try:
            timeout = self._calculate_query_timeout(query)

            result = await with_timeout(
                self._execute_query_one_internal(query, args),
                timeout,
                f"Single query execution timed out (query: {query_id})",
                {
                    "query_id": query_id,
                    "args_count": len(args),
                    "timeout_used": timeout,
                },
            )

            return result

        except AsyncTimeoutError as e:
            self.connection_stats["timeout_errors"] += 1
            logger.error(f"❌ Single query execution timed out [{query_id}]: {e}")
            raise
        except Exception as e:
            self.connection_stats["failed_queries"] += 1
            logger.error(f"❌ Single query execution failed [{query_id}]: {e}")
            raise
        finally:
            execution_time = time.time() - start_time
            self._track_query_performance(query_id, execution_time)

    async def _execute_query_one_internal(
        self, query: str, args: tuple
    ) -> Optional[Dict]:
        """Internal single query execution"""
        async with self.get_connection() as conn:
            if args:
                result = await conn.fetchrow(query, *args)
            else:
                result = await conn.fetchrow(query)

            return dict(result) if result else None

    @async_retry(
        max_attempts=2, delay=1.0, exceptions=(asyncpg.PostgresError, AsyncTimeoutError)
    )
    async def execute_command(self, command: str, *args, query_name: str = None) -> str:
        """
        Execute command (INSERT, UPDATE, DELETE)
        Enhanced with timeout protection and retry logic
        """
        start_time = time.time()
        query_id = query_name or command[:50]

        try:
            timeout = self._calculate_query_timeout(command)

            result = await with_timeout(
                self._execute_command_internal(command, args),
                timeout,
                f"Command execution timed out (command: {query_id})",
                {
                    "query_id": query_id,
                    "args_count": len(args),
                    "timeout_used": timeout,
                },
            )

            return result

        except AsyncTimeoutError as e:
            self.connection_stats["timeout_errors"] += 1
            logger.error(f"❌ Command execution timed out [{query_id}]: {e}")
            raise
        except Exception as e:
            self.connection_stats["failed_queries"] += 1
            logger.error(f"❌ Command execution failed [{query_id}]: {e}")
            raise
        finally:
            execution_time = time.time() - start_time
            self._track_query_performance(query_id, execution_time)

    async def _execute_command_internal(self, command: str, args: tuple) -> str:
        """Internal command execution"""
        async with self.get_connection() as conn:
            if args:
                result = await conn.execute(command, *args)
            else:
                result = await conn.execute(command)

            return result

    async def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics
        Enhanced with timeout protection
        """
        try:
            if not self.pool:
                return {"error": "Pool not initialized"}

            return await with_timeout(
                self._get_pool_stats_internal(),
                AsyncTimeouts.DATABASE_QUERY / 2,  # 5 seconds for stats
                "Pool stats collection timed out",
                {"operation": "get_pool_stats"},
            )
        except AsyncTimeoutError as e:
            logger.warning(f"⚠️ Pool stats collection timed out: {e}")
            return {"error": f"Stats collection timed out: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ Error getting pool stats: {e}")
            return {"error": str(e)}

    async def _get_pool_stats_internal(self) -> Dict[str, Any]:
        """Internal pool stats collection"""
        return {
            "pool_size": self.pool.get_size(),
            "pool_min_size": self.pool.get_min_size(),
            "pool_max_size": self.pool.get_max_size(),
            "pool_idle_connections": self.pool.get_idle_size(),
            "pool_active_connections": self.pool.get_size() - self.pool.get_idle_size(),
            "async_patterns_enabled": True,
        }

    async def get_database_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics
        Enhanced with concurrent collection and timeout protection
        """
        try:
            # Collect stats concurrently
            stats_tasks = [
                self._get_connection_stats(),
                self.get_pool_stats(),
                self._get_query_stats(),
                self._get_database_metrics(),
                self._get_system_stats_async(),
            ]

            conn_stats, pool_stats, query_stats, db_metrics, sys_stats = (
                await safe_gather(
                    *stats_tasks,
                    return_exceptions=True,
                    timeout=AsyncTimeouts.DATABASE_QUERY
                    * 2,  # 20 seconds for comprehensive stats
                    max_concurrency=5,
                )
            )

            # Handle exceptions gracefully
            if isinstance(conn_stats, Exception):
                conn_stats = {"error": str(conn_stats)}
            if isinstance(pool_stats, Exception):
                pool_stats = {"error": str(pool_stats)}
            if isinstance(query_stats, Exception):
                query_stats = {"error": str(query_stats)}
            if isinstance(db_metrics, Exception):
                db_metrics = {"error": str(db_metrics)}
            if isinstance(sys_stats, Exception):
                sys_stats = {"error": str(sys_stats)}

            return {
                "connection_stats": conn_stats,
                "pool_stats": pool_stats,
                "query_stats": query_stats,
                "database_metrics": db_metrics,
                "system_stats": sys_stats,
                "async_optimized": True,
            }

        except Exception as e:
            logger.error(f"❌ Error collecting database stats: {e}")
            return {"error": str(e)}

    async def _get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return self.connection_stats.copy()

    async def _get_query_stats(self) -> Dict[str, Any]:
        """Get query statistics"""
        return self.query_stats.copy()

    async def _get_database_metrics(self) -> Dict[str, Any]:
        """Get database size and performance metrics"""
        try:
            db_metrics = await self.execute_query(
                """
                SELECT 
                    pg_database_size(current_database()) as db_size,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle') as idle_connections
            """,
                query_name="database_metrics",
            )

            if db_metrics:
                metrics = db_metrics[0]
                metrics["db_size_mb"] = metrics["db_size"] / (1024 * 1024)
                return metrics

            return {"error": "No metrics returned"}

        except Exception as e:
            logger.warning(f"⚠️ Could not fetch database metrics: {e}")
            return {"error": str(e)}

    async def _get_system_stats_async(self) -> Dict[str, Any]:
        """Get system resource statistics asynchronously"""
        try:
            return self._get_system_stats()
        except Exception as e:
            return {"error": str(e)}

    async def optimize_queries(self) -> Dict[str, Any]:
        """
        Analyze and optimize slow queries
        Enhanced with concurrent analysis and timeout protection
        """
        try:
            optimization_report = await with_timeout(
                self._optimize_queries_internal(),
                AsyncTimeouts.DATABASE_QUERY
                * 3,  # 30 seconds for optimization analysis
                "Query optimization analysis timed out",
                {"operation": "optimize_queries"},
            )

            return optimization_report

        except AsyncTimeoutError as e:
            logger.warning(f"⚠️ Query optimization timed out: {e}")
            return {
                "error": "Optimization analysis timed out",
                "timeout": True,
                "slow_queries": [],
                "recommendations": ["Retry optimization analysis with smaller dataset"],
            }
        except Exception as e:
            logger.error(f"❌ Query optimization failed: {e}")
            return {"error": str(e)}

    async def _optimize_queries_internal(self) -> Dict[str, Any]:
        """Internal query optimization analysis"""
        optimization_report = {
            "slow_queries": [],
            "recommendations": [],
            "indexes_suggested": [],
        }

        # Find slow queries
        for query_id, stats in self.query_stats.items():
            if stats["avg_time"] > self.slow_query_threshold:
                optimization_report["slow_queries"].append(
                    {
                        "query": query_id,
                        "avg_time": stats["avg_time"],
                        "total_calls": stats["call_count"],
                        "total_time": stats["total_time"],
                    }
                )

        # Add optimization recommendations
        if optimization_report["slow_queries"]:
            optimization_report["recommendations"].extend(
                [
                    "Consider adding indexes for frequently queried columns",
                    "Review query plans with EXPLAIN ANALYZE",
                    "Consider query caching for repeated expensive operations",
                    "Optimize WHERE clauses and JOIN conditions",
                ]
            )

        # Concurrent index analysis
        try:
            missing_indexes_task = self._analyze_missing_indexes()
            missing_indexes = await missing_indexes_task
            optimization_report["indexes_suggested"] = missing_indexes
        except Exception as e:
            logger.warning(f"⚠️ Index analysis failed: {e}")
            optimization_report["index_analysis_error"] = str(e)

        return optimization_report

    async def _analyze_missing_indexes(self) -> List[Dict[str, Any]]:
        """Analyze missing indexes"""
        try:
            missing_indexes = await self.execute_query(
                """
                SELECT schemaname, tablename, attname, n_distinct, correlation
                FROM pg_stats
                WHERE schemaname = 'public'
                AND n_distinct > 100
                AND tablename IN ('users', 'user_budgets', 'llm_usage_logs', 'budget_alerts')
                ORDER BY n_distinct DESC
            """,
                query_name="index_analysis",
            )

            suggestions = []
            for row in missing_indexes:
                if row["n_distinct"] > 500:  # High cardinality columns
                    suggestions.append(
                        {
                            "table": row["tablename"],
                            "column": row["attname"],
                            "reason": f"High cardinality ({row['n_distinct']} distinct values)",
                        }
                    )

            return suggestions

        except Exception as e:
            logger.warning(f"⚠️ Could not analyze indexes: {e}")
            return []

    @async_retry(max_attempts=2, delay=2.0, exceptions=(asyncpg.PostgresError,))
    async def create_performance_indexes(self) -> List[str]:
        """
        Create performance-critical indexes
        Enhanced with timeout protection and concurrent creation
        """
        try:
            return await with_timeout(
                self._create_performance_indexes_internal(),
                AsyncTimeouts.DATABASE_MIGRATION,  # 5 minutes for index creation
                "Performance index creation timed out",
                {"operation": "create_performance_indexes"},
            )
        except AsyncTimeoutError as e:
            logger.error(f"❌ Index creation timed out: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Index creation failed: {e}")
            return []

    async def _create_performance_indexes_internal(self) -> List[str]:
        """Internal performance index creation"""
        indexes = []

        index_commands = [
            # User-related indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users(created_at)",
            # Budget-related indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_budgets_user_id ON user_budgets(user_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_llm_usage_logs_user_id ON llm_usage_logs(user_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_llm_usage_logs_timestamp ON llm_usage_logs(timestamp)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_budget_alerts_user_id ON budget_alerts(user_id)",
            # Composite indexes for common queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_llm_usage_user_timestamp ON llm_usage_logs(user_id, timestamp)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_budget_alerts_user_type ON budget_alerts(user_id, alert_type)",
        ]

        # Create indexes with concurrent execution for better performance
        index_tasks = []
        for command in index_commands:
            task = self._create_single_index(command)
            index_tasks.append(task)

        # Execute index creation concurrently (limit to 3 to avoid overwhelming DB)
        results = await safe_gather(
            *index_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.DATABASE_MIGRATION,
            max_concurrency=3,
        )

        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"⚠️ Failed to create index: {result}")
            elif result:
                indexes.append(result)
                logger.info(f"✅ Created index: {result}")

        return indexes

    async def _create_single_index(self, command: str) -> Optional[str]:
        """Create a single index"""
        try:
            await self.execute_command(command, query_name="create_index")
            # Extract index name from command
            return command.split()[-1] if "idx_" in command else "unknown_index"
        except Exception as e:
            logger.warning(f"⚠️ Failed to create index: {e}")
            return None

    def _update_stats(self, response_time: float):
        """
        Update connection statistics
        Enhanced with additional metrics
        """
        self.connection_stats["total_queries"] += 1
        self.connection_stats["total_response_time"] += response_time
        self.connection_stats["avg_response_time"] = (
            self.connection_stats["total_response_time"]
            / self.connection_stats["total_queries"]
        )

        if response_time > self.slow_query_threshold:
            self.connection_stats["slow_queries"] += 1

    def _track_query_performance(self, query_id: str, execution_time: float):
        """
        Track individual query performance
        Enhanced with additional metrics
        """
        if query_id not in self.query_stats:
            self.query_stats[query_id] = {
                "call_count": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
                "last_executed": None,
            }

        stats = self.query_stats[query_id]
        stats["call_count"] += 1
        stats["total_time"] += execution_time
        stats["avg_time"] = stats["total_time"] / stats["call_count"]
        stats["min_time"] = min(stats["min_time"], execution_time)
        stats["max_time"] = max(stats["max_time"], execution_time)
        stats["last_executed"] = time.time()

    def _get_system_stats(self) -> Dict[str, Any]:
        """Get system resource statistics"""
        try:
            process = psutil.Process(os.getpid())
            return {
                "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections()),
            }
        except Exception as e:
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive database health check
        Enhanced with timeout protection and concurrent testing
        """
        health = {
            "status": "unknown",
            "timestamp": time.time(),
            "checks": {},
            "async_patterns_enabled": True,
        }

        try:
            # Execute health checks concurrently
            health_tasks = [
                self._test_connectivity(),
                self._test_pool_health(),
                self._test_query_performance(),
            ]

            connectivity, pool_health, query_perf = await safe_gather(
                *health_tasks,
                return_exceptions=True,
                timeout=AsyncTimeouts.DATABASE_QUERY * 2,  # 20 seconds for health check
                max_concurrency=3,
            )

            # Process results
            health["checks"]["connectivity"] = (
                connectivity
                if not isinstance(connectivity, Exception)
                else {"status": "failed", "error": str(connectivity)}
            )
            health["checks"]["pool"] = (
                pool_health
                if not isinstance(pool_health, Exception)
                else {"status": "failed", "error": str(pool_health)}
            )
            health["checks"]["query_performance"] = (
                query_perf
                if not isinstance(query_perf, Exception)
                else {"status": "failed", "error": str(query_perf)}
            )

            # Overall status
            all_checks_ok = all(
                check.get("status") == "ok"
                for check in health["checks"].values()
                if isinstance(check, dict)
            )
            health["status"] = "healthy" if all_checks_ok else "unhealthy"

        except Exception as e:
            health["status"] = "error"
            health["error"] = str(e)
            logger.error(f"❌ Database health check failed: {e}")

        return health

    async def _test_connectivity(self) -> Dict[str, Any]:
        """Test basic connectivity"""
        try:
            start_time = time.time()
            result = await self.execute_query_one(
                "SELECT 1 as test", query_name="health_check"
            )
            response_time = time.time() - start_time

            return {
                "status": "ok" if result and result["test"] == 1 else "failed",
                "response_time": response_time,
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def _test_pool_health(self) -> Dict[str, Any]:
        """Test connection pool health"""
        try:
            pool_stats = await self.get_pool_stats()
            return {
                "status": "ok" if pool_stats.get("pool_size", 0) > 0 else "failed",
                "stats": pool_stats,
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def _test_query_performance(self) -> Dict[str, Any]:
        """Test query performance"""
        try:
            start_time = time.time()
            await self.execute_query(
                "SELECT COUNT(*) FROM information_schema.tables",
                query_name="performance_test",
            )
            response_time = time.time() - start_time

            return {
                "status": (
                    "ok"
                    if response_time < self.slow_query_threshold * 5
                    else "degraded"
                ),
                "response_time": response_time,
                "threshold": self.slow_query_threshold * 5,
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def close(self) -> None:
        """Close database pool"""
        if self.pool:
            await self.pool.close()
            logger.info("✅ Database pool closed")

# Performance-optimized bulk operations to prevent N+1 queries
class BulkQueryOptimizer:
    """Optimized bulk database operations to prevent N+1 queries"""
    
    def __init__(self, database_optimizer: DatabaseOptimizer):
        self.db = database_optimizer
        
    @async_retry(max_attempts=2, delay=1.0, exceptions=(asyncpg.PostgresError, AsyncTimeoutError))
    async def bulk_fetch_with_relations(
        self, 
        base_query: str,
        relation_queries: Dict[str, str],
        join_key: str = "id",
        query_name: str = "bulk_fetch"
    ) -> List[Dict[str, Any]]:
        """
        Execute bulk fetch with relations to prevent N+1 queries
        
        Args:
            base_query: Main query to fetch base records
            relation_queries: Dict of relation_name -> SQL query to fetch related data  
            join_key: Key to join base and related records
            query_name: Name for query tracking
            
        Returns:
            List of records with relations populated
        """
        try:
            start_time = time.time()
            
            # Step 1: Fetch base records
            base_records = await self.db.execute_query(
                base_query, 
                query_name=f"{query_name}_base"
            )
            
            if not base_records:
                return []
            
            # Step 2: Extract join keys
            join_keys = [record[join_key] for record in base_records if join_key in record]
            
            if not join_keys:
                return base_records
            
            # Step 3: Fetch all relations in parallel
            relation_tasks = []
            for relation_name, relation_query in relation_queries.items():
                # Replace placeholder in query with actual IDs
                formatted_query = relation_query.format(
                    ids=','.join(f"'{key}'" for key in join_keys)
                )
                task = self.db.execute_query(
                    formatted_query,
                    query_name=f"{query_name}_{relation_name}"
                )
                relation_tasks.append((relation_name, task))
            
            # Execute all relation queries concurrently
            relation_results = await safe_gather(
                *[task for _, task in relation_tasks],
                return_exceptions=True,
                timeout=AsyncTimeouts.DATABASE_QUERY * 2,  # 20 seconds for bulk relations
                max_concurrency=5
            )
            
            # Step 4: Build lookup maps for fast joining
            relation_maps = {}
            for i, (relation_name, _) in enumerate(relation_tasks):
                if isinstance(relation_results[i], Exception):
                    logger.warning(f"⚠️ Failed to fetch relation {relation_name}: {relation_results[i]}")
                    relation_maps[relation_name] = {}
                    continue
                
                # Group related records by join key
                relation_map = {}
                for record in relation_results[i]:
                    key = record.get(join_key)
                    if key:
                        if key not in relation_map:
                            relation_map[key] = []
                        relation_map[key].append(record)
                
                relation_maps[relation_name] = relation_map
            
            # Step 5: Join base records with relations
            enhanced_records = []
            for base_record in base_records:
                enhanced_record = base_record.copy()
                record_key = base_record.get(join_key)
                
                # Add relations to record
                for relation_name, relation_map in relation_maps.items():
                    enhanced_record[relation_name] = relation_map.get(record_key, [])
                
                enhanced_records.append(enhanced_record)
            
            execution_time = time.time() - start_time
            logger.info(
                f"✅ Bulk fetch completed: {len(enhanced_records)} records with "
                f"{len(relation_queries)} relations in {execution_time:.2f}s"
            )
            
            return enhanced_records
            
        except Exception as e:
            logger.error(f"❌ Bulk fetch with relations failed: {e}")
            raise
    
    async def bulk_upsert(
        self,
        table_name: str,
        records: List[Dict[str, Any]],
        conflict_columns: List[str],
        update_columns: Optional[List[str]] = None,
        batch_size: int = 1000
    ) -> int:
        """
        Perform bulk upsert (INSERT ON CONFLICT UPDATE) operation
        
        Args:
            table_name: Target table name
            records: List of records to upsert
            conflict_columns: Columns to check for conflicts
            update_columns: Columns to update on conflict (defaults to all non-conflict columns)
            batch_size: Size of each batch for processing
            
        Returns:
            Number of affected rows
        """
        if not records:
            return 0
        
        try:
            total_affected = 0
            
            # Process in batches to avoid memory issues
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                # Generate column names and placeholders
                columns = list(batch[0].keys())
                if update_columns is None:
                    update_columns = [col for col in columns if col not in conflict_columns]
                
                placeholders = []
                values = []
                
                for record in batch:
                    row_placeholders = []
                    for col in columns:
                        values.append(record.get(col))
                        row_placeholders.append(f"${len(values)}")
                    placeholders.append(f"({','.join(row_placeholders)})")
                
                # Build upsert query
                conflict_clause = f"({','.join(conflict_columns)})"
                update_clause = ','.join([f"{col} = EXCLUDED.{col}" for col in update_columns])
                
                upsert_query = f"""
                    INSERT INTO {table_name} ({','.join(columns)})
                    VALUES {','.join(placeholders)}
                    ON CONFLICT {conflict_clause}
                    DO UPDATE SET {update_clause}
                """
                
                # Execute batch
                result = await self.db.execute_command(
                    upsert_query,
                    *values,
                    query_name=f"bulk_upsert_{table_name}_batch_{i//batch_size + 1}"
                )
                
                # Parse affected rows from result
                if "INSERT" in result:
                    # PostgreSQL returns "INSERT 0 affected_count"
                    affected = int(result.split()[-1]) if result.split()[-1].isdigit() else len(batch)
                else:
                    affected = len(batch)
                
                total_affected += affected
            
            logger.info(
                f"✅ Bulk upsert completed: {total_affected} rows affected in {table_name}"
            )
            return total_affected
            
        except Exception as e:
            logger.error(f"❌ Bulk upsert failed for {table_name}: {e}")
            raise
    
    async def bulk_select_in(
        self,
        query_template: str,
        in_values: List[Any],
        batch_size: int = 1000,
        query_name: str = "bulk_select_in"
    ) -> List[Dict[str, Any]]:
        """
        Execute SELECT with large IN clause efficiently using batches
        
        Args:
            query_template: SQL query template with {in_clause} placeholder
            in_values: List of values for IN clause
            batch_size: Size of each batch
            query_name: Name for query tracking
            
        Returns:
            Combined results from all batches
        """
        if not in_values:
            return []
        
        try:
            all_results = []
            
            # Process in batches to avoid large IN clauses
            for i in range(0, len(in_values), batch_size):
                batch_values = in_values[i:i + batch_size]
                
                # Create parameterized placeholders
                placeholders = []
                query_params = []
                
                for value in batch_values:
                    query_params.append(value)
                    placeholders.append(f"${len(query_params)}")
                
                in_clause = f"({','.join(placeholders)})"
                
                # Format query with IN clause
                batch_query = query_template.format(in_clause=in_clause)
                
                # Execute batch query
                batch_results = await self.db.execute_query(
                    batch_query,
                    *query_params,
                    query_name=f"{query_name}_batch_{i//batch_size + 1}"
                )
                
                all_results.extend(batch_results)
            
            logger.info(
                f"✅ Bulk SELECT IN completed: {len(all_results)} total results from {len(in_values)} values"
            )
            return all_results
            
        except Exception as e:
            logger.error(f"❌ Bulk SELECT IN failed: {e}")
            raise
    
    async def optimize_query_patterns(self, queries: List[str]) -> Dict[str, Any]:
        """
        Analyze query patterns and suggest optimizations to prevent N+1 queries
        
        Args:
            queries: List of executed queries to analyze
            
        Returns:
            Optimization suggestions and statistics
        """
        try:
            analysis = {
                "total_queries": len(queries),
                "unique_patterns": set(),
                "potential_n_plus_one": [],
                "optimization_suggestions": [],
                "pattern_frequency": {}
            }
            
            # Analyze query patterns
            for query in queries:
                # Normalize query by removing specific values
                normalized = self._normalize_query(query)
                analysis["unique_patterns"].add(normalized)
                
                # Count pattern frequency
                analysis["pattern_frequency"][normalized] = analysis["pattern_frequency"].get(normalized, 0) + 1
                
                # Detect potential N+1 patterns
                if self._is_potential_n_plus_one(query, queries):
                    analysis["potential_n_plus_one"].append(query)
            
            # Generate optimization suggestions
            for pattern, frequency in analysis["pattern_frequency"].items():
                if frequency > 10:  # Frequently executed patterns
                    if "SELECT" in pattern and "WHERE" in pattern and "=" in pattern:
                        analysis["optimization_suggestions"].append({
                            "pattern": pattern,
                            "frequency": frequency,
                            "suggestion": "Consider using bulk_select_in() for multiple similar queries",
                            "estimated_improvement": f"{frequency}x fewer queries"
                        })
            
            # Convert set to list for JSON serialization
            analysis["unique_patterns"] = list(analysis["unique_patterns"])
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Query pattern analysis failed: {e}")
            return {"error": str(e)}
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query by removing specific values for pattern analysis"""
        import re
        
        # Remove specific string values
        normalized = re.sub(r"'[^']*'", "'?'", query)
        
        # Remove specific numeric values  
        normalized = re.sub(r'\b\d+\b', '?', normalized)
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()
    
    def _is_potential_n_plus_one(self, query: str, all_queries: List[str]) -> bool:
        """Detect if query is part of potential N+1 pattern"""
        normalized = self._normalize_query(query)
        
        # Count similar queries
        similar_count = sum(1 for q in all_queries if self._normalize_query(q) == normalized)
        
        # If same pattern appears many times, it might be N+1
        return similar_count > 5 and "SELECT" in query and "WHERE" in query

# Global instance
_bulk_optimizer = None

async def get_bulk_optimizer() -> BulkQueryOptimizer:
    """Get global bulk query optimizer instance"""
    global _bulk_optimizer
    if _bulk_optimizer is None:
        # Assuming we have a global database optimizer
        from infra.database.session import get_database_optimizer
        db_optimizer = await get_database_optimizer()
        _bulk_optimizer = BulkQueryOptimizer(db_optimizer)
    return _bulk_optimizer
