"""
Database Optimizer for AI Assistant MVP
Task 2.1.2: Database Optimization Implementation

Features:
- AsyncPG connection pooling
- Query optimization and monitoring
- Database performance metrics
- Connection health monitoring
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import asyncpg
from asyncpg import Pool
import psutil
import os

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """
    High-performance database optimizer with connection pooling
    
    Features:
    - Connection pooling for PostgreSQL
    - Query performance monitoring
    - Health checks and metrics
    - Async operation optimization
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[Pool] = None
        self.query_stats = {}
        self.connection_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "failed_queries": 0,
            "avg_response_time": 0.0,
            "total_response_time": 0.0
        }
        
        # Performance thresholds
        self.slow_query_threshold = 0.1  # 100ms
        
    async def initialize_pool(self, min_size: int = 5, max_size: int = 20):
        """Initialize connection pool with optimal settings"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=min_size,
                max_size=max_size,
                max_queries=50000,
                max_inactive_connection_lifetime=300.0,
                timeout=30.0,
                command_timeout=60.0,
                server_settings={
                    'application_name': 'ai_assistant_mvp',
                    'jit': 'off'  # Disable JIT for faster startup on small queries
                }
            )
            logger.info(f"✅ Database pool initialized: {min_size}-{max_size} connections")
            
            # Test initial connection
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize database pool: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Get connection from pool with monitoring"""
        start_time = time.time()
        connection = None
        
        try:
            if not self.pool:
                await self.initialize_pool()
            
            connection = await self.pool.acquire()
            yield connection
            
        except Exception as e:
            self.connection_stats["failed_queries"] += 1
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                await self.pool.release(connection)
            
            # Track connection metrics
            response_time = time.time() - start_time
            self._update_stats(response_time)
    
    async def execute_query(self, query: str, *args, query_name: str = None) -> List[Dict]:
        """Execute query with performance monitoring"""
        start_time = time.time()
        query_id = query_name or query[:50]
        
        try:
            async with self.get_connection() as conn:
                # Execute query
                if args:
                    result = await conn.fetch(query, *args)
                else:
                    result = await conn.fetch(query)
                
                # Convert to list of dicts
                return [dict(row) for row in result]
                
        except Exception as e:
            logger.error(f"Query execution failed [{query_id}]: {e}")
            raise
        finally:
            # Track query performance
            execution_time = time.time() - start_time
            self._track_query_performance(query_id, execution_time)
    
    async def execute_query_one(self, query: str, *args, query_name: str = None) -> Optional[Dict]:
        """Execute query expecting single result"""
        start_time = time.time()
        query_id = query_name or query[:50]
        
        try:
            async with self.get_connection() as conn:
                if args:
                    result = await conn.fetchrow(query, *args)
                else:
                    result = await conn.fetchrow(query)
                
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Query execution failed [{query_id}]: {e}")
            raise
        finally:
            execution_time = time.time() - start_time
            self._track_query_performance(query_id, execution_time)
    
    async def execute_command(self, command: str, *args, query_name: str = None) -> str:
        """Execute command (INSERT, UPDATE, DELETE)"""
        start_time = time.time()
        query_id = query_name or command[:50]
        
        try:
            async with self.get_connection() as conn:
                if args:
                    result = await conn.execute(command, *args)
                else:
                    result = await conn.execute(command)
                
                return result
                
        except Exception as e:
            logger.error(f"Command execution failed [{query_id}]: {e}")
            raise
        finally:
            execution_time = time.time() - start_time
            self._track_query_performance(query_id, execution_time)
    
    async def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if not self.pool:
            return {"error": "Pool not initialized"}
        
        return {
            "pool_size": self.pool.get_size(),
            "pool_min_size": self.pool.get_min_size(),
            "pool_max_size": self.pool.get_max_size(),
            "pool_idle_connections": self.pool.get_idle_size(),
            "pool_active_connections": self.pool.get_size() - self.pool.get_idle_size()
        }
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        stats = {
            "connection_stats": self.connection_stats.copy(),
            "pool_stats": await self.get_pool_stats(),
            "query_stats": self.query_stats.copy(),
            "system_stats": self._get_system_stats()
        }
        
        # Get database size and performance metrics
        try:
            db_metrics = await self.execute_query("""
                SELECT 
                    pg_database_size(current_database()) as db_size,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle') as idle_connections
            """, query_name="database_metrics")
            
            if db_metrics:
                stats["database_metrics"] = db_metrics[0]
                stats["database_metrics"]["db_size_mb"] = stats["database_metrics"]["db_size"] / (1024 * 1024)
                
        except Exception as e:
            logger.warning(f"Could not fetch database metrics: {e}")
            stats["database_metrics"] = {"error": str(e)}
        
        return stats
    
    async def optimize_queries(self) -> Dict[str, Any]:
        """Analyze and optimize slow queries"""
        optimization_report = {
            "slow_queries": [],
            "recommendations": [],
            "indexes_suggested": []
        }
        
        # Find slow queries
        for query_id, stats in self.query_stats.items():
            if stats["avg_time"] > self.slow_query_threshold:
                optimization_report["slow_queries"].append({
                    "query": query_id,
                    "avg_time": stats["avg_time"],
                    "total_calls": stats["call_count"],
                    "total_time": stats["total_time"]
                })
        
        # Add optimization recommendations
        if optimization_report["slow_queries"]:
            optimization_report["recommendations"].extend([
                "Consider adding indexes for frequently queried columns",
                "Review query plans with EXPLAIN ANALYZE",
                "Consider query caching for repeated expensive operations",
                "Optimize WHERE clauses and JOIN conditions"
            ])
        
        # Check for missing indexes (common patterns)
        try:
            missing_indexes = await self.execute_query("""
                SELECT schemaname, tablename, attname, n_distinct, correlation
                FROM pg_stats
                WHERE schemaname = 'public'
                AND n_distinct > 100
                AND tablename IN ('users', 'user_budgets', 'llm_usage_logs', 'budget_alerts')
                ORDER BY n_distinct DESC
            """, query_name="index_analysis")
            
            for row in missing_indexes:
                if row['n_distinct'] > 500:  # High cardinality columns
                    optimization_report["indexes_suggested"].append({
                        "table": row['tablename'],
                        "column": row['attname'],
                        "reason": f"High cardinality ({row['n_distinct']} distinct values)"
                    })
                    
        except Exception as e:
            logger.warning(f"Could not analyze indexes: {e}")
        
        return optimization_report
    
    async def create_performance_indexes(self) -> List[str]:
        """Create performance-critical indexes"""
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
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_budget_alerts_user_type ON budget_alerts(user_id, alert_type)"
        ]
        
        for command in index_commands:
            try:
                await self.execute_command(command, query_name="create_index")
                indexes.append(command.split()[-1])  # Extract index name
                logger.info(f"✅ Created index: {command}")
            except Exception as e:
                logger.warning(f"Failed to create index: {e}")
        
        return indexes
    
    def _update_stats(self, response_time: float):
        """Update connection statistics"""
        self.connection_stats["total_queries"] += 1
        self.connection_stats["total_response_time"] += response_time
        self.connection_stats["avg_response_time"] = (
            self.connection_stats["total_response_time"] / 
            self.connection_stats["total_queries"]
        )
        
        if response_time > self.slow_query_threshold:
            self.connection_stats["slow_queries"] += 1
    
    def _track_query_performance(self, query_id: str, execution_time: float):
        """Track individual query performance"""
        if query_id not in self.query_stats:
            self.query_stats[query_id] = {
                "call_count": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "min_time": float('inf'),
                "max_time": 0.0
            }
        
        stats = self.query_stats[query_id]
        stats["call_count"] += 1
        stats["total_time"] += execution_time
        stats["avg_time"] = stats["total_time"] / stats["call_count"]
        stats["min_time"] = min(stats["min_time"], execution_time)
        stats["max_time"] = max(stats["max_time"], execution_time)
    
    def _get_system_stats(self) -> Dict[str, Any]:
        """Get system resource statistics"""
        try:
            process = psutil.Process(os.getpid())
            return {
                "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections())
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive database health check"""
        health = {
            "status": "unknown",
            "timestamp": time.time(),
            "checks": {}
        }
        
        try:
            # Test basic connectivity
            start_time = time.time()
            result = await self.execute_query_one("SELECT 1 as test", query_name="health_check")
            response_time = time.time() - start_time
            
            health["checks"]["connectivity"] = {
                "status": "ok" if result and result["test"] == 1 else "failed",
                "response_time": response_time
            }
            
            # Check pool health
            pool_stats = await self.get_pool_stats()
            health["checks"]["pool"] = {
                "status": "ok" if pool_stats.get("pool_size", 0) > 0 else "failed",
                "stats": pool_stats
            }
            
            # Overall status
            all_checks_ok = all(
                check["status"] == "ok" 
                for check in health["checks"].values()
            )
            health["status"] = "healthy" if all_checks_ok else "unhealthy"
            
        except Exception as e:
            health["status"] = "error"
            health["error"] = str(e)
            logger.error(f"Database health check failed: {e}")
        
        return health
    
    async def close(self):
        """Close database pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")

# Global database optimizer instance
db_optimizer = DatabaseOptimizer(
    database_url=os.getenv("DATABASE_URL", "postgresql://localhost/ai_assistant")
) 