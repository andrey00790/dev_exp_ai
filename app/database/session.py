"""
Database session management
Enhanced with standardized async patterns for enterprise reliability
Version: 2.1 Async Optimized
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Generator, AsyncGenerator, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import QueuePool

# Import standardized async patterns
from app.core.async_utils import (
    AsyncTimeouts, 
    with_timeout, 
    async_retry,
    safe_gather,
    create_background_task
)
from app.core.exceptions import AsyncTimeoutError, AsyncRetryError

logger = logging.getLogger(__name__)

# Database URLs from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://ai_user:ai_password@localhost:5432/ai_assistant"
)

# Convert to async URL if not already
ASYNC_DATABASE_URL = os.getenv(
    "ASYNC_DATABASE_URL",
    DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://") if "asyncpg" not in DATABASE_URL else DATABASE_URL
)

# Enhanced engine configuration with connection pooling
ENGINE_CONFIG = {
    "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
    "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),  # 1 hour
    "pool_pre_ping": True,
    "echo": os.getenv("DB_ECHO", "false").lower() == "true"
}

# Create sync engine with enhanced configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    **ENGINE_CONFIG
)

# Create async engine with enhanced configuration
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    poolclass=QueuePool,
    **ENGINE_CONFIG
)

# Create session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# Create Base class for models
Base = declarative_base()

# Connection health monitoring
connection_stats = {
    "sync_connections": 0,
    "async_connections": 0,
    "failed_connections": 0,
    "timeout_errors": 0,
    "total_queries": 0
}


# Enhanced session management with timeout protection
def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get sync database session
    Enhanced with connection monitoring
    """
    db = None
    try:
        db = SessionLocal()
        connection_stats["sync_connections"] += 1
        yield db
    except Exception as e:
        connection_stats["failed_connections"] += 1
        logger.error(f"❌ Sync database session error: {e}")
        if db:
            db.rollback()
        raise
    finally:
        if db:
            db.close()


@asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions
    Enhanced with timeout protection and retry logic
    """
    session = None
    try:
        # Create session with timeout protection
        session = await with_timeout(
            _create_async_session(),
            AsyncTimeouts.DATABASE_QUERY,  # 10 seconds for session creation
            "Database session creation timed out",
            {"operation": "create_async_session"}
        )
        
        connection_stats["async_connections"] += 1
        yield session
        
        # Commit with timeout protection
        await with_timeout(
            session.commit(),
            AsyncTimeouts.DATABASE_TRANSACTION,  # 30 seconds for commit
            "Database commit timed out",
            {"operation": "session_commit"}
        )
        
    except AsyncTimeoutError as e:
        connection_stats["timeout_errors"] += 1
        logger.error(f"❌ Database session timeout: {e}")
        if session:
            await session.rollback()
        raise
    except Exception as e:
        connection_stats["failed_connections"] += 1
        logger.error(f"❌ Async database session error: {e}")
        if session:
            await session.rollback()
        raise
    finally:
        if session:
            await session.close()


async def _create_async_session() -> AsyncSession:
    """Internal async session creation"""
    return AsyncSessionLocal()


@async_retry(max_attempts=3, delay=1.0, exceptions=(Exception,))
async def get_async_db_session() -> AsyncSession:
    """
    Get async database session for direct use
    Enhanced with retry logic and timeout protection
    """
    try:
        session = await with_timeout(
            _create_async_session(),
            AsyncTimeouts.DATABASE_QUERY,
            "Async session creation timed out",
            {"operation": "direct_async_session"}
        )
        
        connection_stats["async_connections"] += 1
        return session
        
    except AsyncTimeoutError as e:
        connection_stats["timeout_errors"] += 1
        logger.error(f"❌ Async session creation timeout: {e}")
        raise
    except Exception as e:
        connection_stats["failed_connections"] += 1
        logger.error(f"❌ Async session creation failed: {e}")
        raise


def get_db_session() -> Session:
    """
    Get sync database session for direct use
    Enhanced with connection monitoring
    """
    try:
        session = SessionLocal()
        connection_stats["sync_connections"] += 1
        return session
    except Exception as e:
        connection_stats["failed_connections"] += 1
        logger.error(f"❌ Sync session creation failed: {e}")
        raise


@async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
async def create_tables():
    """
    Create all database tables
    Enhanced with async patterns and timeout protection
    """
    try:
        # Create tables with timeout protection
        await with_timeout(
            _create_tables_internal(),
            AsyncTimeouts.DATABASE_MIGRATION,  # 5 minutes for table creation
            "Database table creation timed out",
            {"operation": "create_tables"}
        )
        
        logger.info("✅ Database tables created successfully")
        
    except AsyncTimeoutError as e:
        logger.error(f"❌ Table creation timed out: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Table creation failed: {e}")
        raise


async def _create_tables_internal():
    """Internal table creation with async engine"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def create_tables_sync():
    """
    Create all database tables (sync version)
    Enhanced with error handling
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully (sync)")
    except Exception as e:
        logger.error(f"❌ Sync table creation failed: {e}")
        raise


def get_engine():
    """
    Get sync database engine
    """
    return engine


def get_async_engine():
    """
    Get async database engine
    """
    return async_engine


async def init_database():
    """
    Initialize database with tables
    Enhanced with async patterns
    """
    try:
        await create_tables()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


def init_database_sync():
    """
    Initialize database with tables (sync version)
    """
    try:
        create_tables_sync()
        logger.info("✅ Database initialized successfully (sync)")
    except Exception as e:
        logger.error(f"❌ Sync database initialization failed: {e}")
        raise


async def close_db_session_async(session: AsyncSession):
    """
    Close async database session
    Enhanced with timeout protection
    """
    try:
        if session:
            await with_timeout(
                session.close(),
                AsyncTimeouts.DATABASE_QUERY,
                "Session close timed out",
                {"operation": "close_async_session"}
            )
    except Exception as e:
        logger.error(f"❌ Error closing async session: {e}")


def close_db_session(session: Session):
    """
    Close sync database session
    Enhanced with error handling
    """
    try:
        if session:
            session.close()
    except Exception as e:
        logger.error(f"❌ Error closing sync session: {e}")


async def get_database_stats() -> dict:
    """
    Get comprehensive database statistics
    Enhanced with concurrent stats collection
    """
    try:
        # Collect stats concurrently
        stats_tasks = [
            _get_connection_pool_stats(),
            _get_engine_stats(),
            _get_connection_stats()
        ]
        
        pool_stats, engine_stats, conn_stats = await safe_gather(
            *stats_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.DATABASE_QUERY,
            max_concurrency=3
        )
        
        # Handle exceptions gracefully
        if isinstance(pool_stats, Exception):
            pool_stats = {"error": str(pool_stats)}
        if isinstance(engine_stats, Exception):
            engine_stats = {"error": str(engine_stats)}
        if isinstance(conn_stats, Exception):
            conn_stats = {"error": str(conn_stats)}
        
        return {
            "pool_stats": pool_stats,
            "engine_stats": engine_stats,
            "connection_stats": conn_stats,
            "database_url_configured": bool(DATABASE_URL),
            "async_url_configured": bool(ASYNC_DATABASE_URL),
            "async_patterns_enabled": True
        }
        
    except Exception as e:
        logger.error(f"❌ Error collecting database stats: {e}")
        return {"error": str(e)}


async def _get_connection_pool_stats() -> dict:
    """Get connection pool statistics"""
    try:
        pool = async_engine.pool
        return {
            "async_pool_size": pool.size(),
            "async_pool_checked_in": pool.checkedin(),
            "async_pool_checked_out": pool.checkedout(),
            "async_pool_overflow": pool.overflow(),
            "async_pool_invalid": pool.invalid(),
            "sync_pool_size": engine.pool.size(),
            "sync_pool_checked_in": engine.pool.checkedin(),
            "sync_pool_checked_out": engine.pool.checkedout()
        }
    except Exception as e:
        return {"error": str(e)}


async def _get_engine_stats() -> dict:
    """Get engine statistics"""
    return {
        "sync_engine_echo": engine.echo,
        "async_engine_echo": async_engine.echo,
        "pool_size": ENGINE_CONFIG["pool_size"],
        "max_overflow": ENGINE_CONFIG["max_overflow"],
        "pool_timeout": ENGINE_CONFIG["pool_timeout"],
        "pool_recycle": ENGINE_CONFIG["pool_recycle"]
    }


async def _get_connection_stats() -> dict:
    """Get connection statistics"""
    return connection_stats.copy()


async def health_check() -> dict:
    """
    Database health check
    Enhanced with async patterns and comprehensive testing
    """
    health = {
        "status": "unknown",
        "sync_database": {"status": "unknown"},
        "async_database": {"status": "unknown"},
        "connection_pools": {"status": "unknown"},
        "errors": []
    }
    
    try:
        # Test sync database with timeout protection
        sync_test = await with_timeout(
            _test_sync_database(),
            AsyncTimeouts.DATABASE_QUERY,
            "Sync database test timed out",
            {"test": "sync_database"}
        )
        health["sync_database"] = sync_test
        
        # Test async database with timeout protection
        async_test = await with_timeout(
            _test_async_database(),
            AsyncTimeouts.DATABASE_QUERY,
            "Async database test timed out", 
            {"test": "async_database"}
        )
        health["async_database"] = async_test
        
        # Test connection pools
        pool_test = await _test_connection_pools()
        health["connection_pools"] = pool_test
        
        # Determine overall status
        all_healthy = (
            sync_test.get("status") == "healthy" and
            async_test.get("status") == "healthy" and
            pool_test.get("status") == "healthy"
        )
        
        health["status"] = "healthy" if all_healthy else "degraded"
        
    except AsyncTimeoutError as e:
        health["status"] = "timeout"
        health["errors"].append(f"Health check timed out: {str(e)}")
    except Exception as e:
        health["status"] = "unhealthy"
        health["errors"].append(f"Health check failed: {str(e)}")
    
    return health


async def _test_sync_database() -> dict:
    """Test sync database connectivity"""
    try:
        with get_db() as db:
            result = db.execute("SELECT 1 as test").fetchone()
            return {
                "status": "healthy",
                "test_query": result[0] if result else None
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def _test_async_database() -> dict:
    """Test async database connectivity"""
    try:
        async with get_async_db() as db:
            result = await db.execute("SELECT 1 as test")
            row = result.fetchone()
            return {
                "status": "healthy", 
                "test_query": row[0] if row else None
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def _test_connection_pools() -> dict:
    """Test connection pool health"""
    try:
        stats = await _get_connection_pool_stats()
        
        # Check if pools are functional
        async_healthy = stats.get("async_pool_size", 0) > 0
        sync_healthy = stats.get("sync_pool_size", 0) > 0
        
        return {
            "status": "healthy" if (async_healthy and sync_healthy) else "degraded",
            "async_pool_healthy": async_healthy,
            "sync_pool_healthy": sync_healthy,
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def cleanup_database():
    """
    Cleanup database connections
    Enhanced with timeout protection
    """
    try:
        # Close async engine
        cleanup_tasks = [
            _cleanup_async_engine(),
            _cleanup_sync_engine()
        ]
        
        await safe_gather(
            *cleanup_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.DATABASE_QUERY * 2,  # 20 seconds for cleanup
            max_concurrency=2
        )
        
        logger.info("✅ Database connections cleaned up successfully")
        
    except Exception as e:
        logger.error(f"❌ Database cleanup failed: {e}")


async def _cleanup_async_engine():
    """Cleanup async engine"""
    if async_engine:
        await async_engine.dispose()


async def _cleanup_sync_engine():
    """Cleanup sync engine"""
    if engine:
        engine.dispose()


# Event listeners for connection monitoring
@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Monitor sync connections"""
    connection_stats["total_queries"] += 1


@event.listens_for(async_engine.sync_engine, "connect")
def receive_async_connect(dbapi_connection, connection_record):
    """Monitor async connections"""
    connection_stats["total_queries"] += 1


# Backward compatibility functions
async def get_async_session() -> AsyncSession:
    """Backward compatibility for async session"""
    return await get_async_db_session()


# Database dependency for FastAPI (async)
async def get_async_db_dependency() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database sessions"""
    async with get_async_db() as session:
        yield session 