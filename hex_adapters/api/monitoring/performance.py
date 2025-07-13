"""
Performance Monitoring API for AI Assistant MVP
Task 2.1: Performance & Caching API Implementation

Endpoints:
- GET /performance/cache/stats - Cache statistics
- POST /performance/cache/clear - Clear cache patterns
- GET /performance/database/stats - Database performance metrics
- GET /performance/system/health - System health overview
"""

import logging
import os
import time
from typing import Any, Dict, Optional

import psutil
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.performance.cache_manager import cache_manager
from app.performance.database_optimizer import db_optimizer
from app.security.auth import get_current_user
from models.base import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/cache/stats")
async def get_cache_statistics(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get comprehensive cache statistics

    Requires authentication. Admin users get detailed stats.
    """
    try:
        # Initialize cache if needed
        if not cache_manager.connected:
            await cache_manager.initialize()

        stats = await cache_manager.get_stats()

        # Add system-level cache info
        stats["system_info"] = {
            "cache_manager_type": "redis" if cache_manager.use_redis else "memory",
            "timestamp": time.time(),
        }

        # Admin users get detailed statistics
        if hasattr(current_user, "scopes") and "admin" in current_user.scopes:
            stats["detailed_metrics"] = {
                "ttl_config": cache_manager.ttl_config,
                "redis_url_configured": (
                    cache_manager.redis_url
                    if cache_manager.redis_url
                    else "Not configured"
                ),
            }

        return {"status": "success", "data": stats, "timestamp": time.time()}

    except Exception as e:
        logger.error(f"Error fetching cache statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch cache statistics: {str(e)}",
        )


@router.post("/cache/clear")
async def clear_cache_pattern(
    pattern: str, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Clear cache entries matching pattern

    Requires admin access for security.
    """
    # Check admin permissions
    if not hasattr(current_user, "scopes") or "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for cache management",
        )

    try:
        if not cache_manager.connected:
            await cache_manager.initialize()

        cleared_count = await cache_manager.clear_pattern(pattern)

        logger.info(
            f"Cache cleared by user {current_user.email}: {cleared_count} keys matching '{pattern}'"
        )

        return {
            "status": "success",
            "message": f"Cleared {cleared_count} cache entries matching pattern '{pattern}'",
            "cleared_count": cleared_count,
            "pattern": pattern,
            "timestamp": time.time(),
        }

    except Exception as e:
        logger.error(f"Error clearing cache pattern '{pattern}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}",
        )


@router.get("/database/stats")
async def get_database_statistics(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get comprehensive database performance statistics

    Requires authentication. Admin users get detailed metrics.
    """
    try:
        # Initialize database pool if needed
        if not db_optimizer.pool:
            await db_optimizer.initialize_pool()

        stats = await db_optimizer.get_database_stats()

        # Admin users get optimization recommendations
        if hasattr(current_user, "scopes") and "admin" in current_user.scopes:
            optimization_report = await db_optimizer.optimize_queries()
            stats["optimization_report"] = optimization_report

        return {"status": "success", "data": stats, "timestamp": time.time()}

    except Exception as e:
        logger.error(f"Error fetching database statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch database statistics: {str(e)}",
        )


@router.post("/database/optimize")
async def optimize_database(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Create performance indexes and optimize database

    Requires admin access.
    """
    # Check admin permissions
    if not hasattr(current_user, "scopes") or "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for database optimization",
        )

    try:
        if not db_optimizer.pool:
            await db_optimizer.initialize_pool()

        # Create performance indexes
        created_indexes = await db_optimizer.create_performance_indexes()

        # Get optimization report
        optimization_report = await db_optimizer.optimize_queries()

        logger.info(
            f"Database optimization performed by user {current_user.email}: {len(created_indexes)} indexes created"
        )

        return {
            "status": "success",
            "message": f"Database optimization completed: {len(created_indexes)} indexes created",
            "created_indexes": created_indexes,
            "optimization_report": optimization_report,
            "timestamp": time.time(),
        }

    except Exception as e:
        logger.error(f"Error optimizing database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize database: {str(e)}",
        )


@router.get("/system/health")
async def get_system_health(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get comprehensive system health overview

    Includes cache, database, and system metrics.
    """
    try:
        health_report = {
            "overall_status": "unknown",
            "timestamp": time.time(),
            "components": {},
        }

        # Cache health
        try:
            if not cache_manager.connected:
                await cache_manager.initialize()
            cache_stats = await cache_manager.get_stats()
            health_report["components"]["cache"] = {
                "status": "healthy" if cache_manager.connected else "unhealthy",
                "type": "redis" if cache_manager.use_redis else "memory",
                "connected": cache_manager.connected,
            }
        except Exception as e:
            health_report["components"]["cache"] = {"status": "error", "error": str(e)}

        # Database health
        try:
            db_health = await db_optimizer.health_check()
            health_report["components"]["database"] = db_health
        except Exception as e:
            health_report["components"]["database"] = {
                "status": "error",
                "error": str(e),
            }

        # System health
        try:
            process = psutil.Process(os.getpid())
            system_info = {
                "status": "healthy",
                "memory_usage_mb": round(process.memory_info().rss / 1024 / 1024, 2),
                "cpu_percent": process.cpu_percent(),
                "open_files": len(process.open_files()),
                "uptime_seconds": time.time() - process.create_time(),
            }

            # Mark as unhealthy if resource usage is too high
            if system_info["memory_usage_mb"] > 1000 or system_info["cpu_percent"] > 80:
                system_info["status"] = "warning"

            health_report["components"]["system"] = system_info
        except Exception as e:
            health_report["components"]["system"] = {"status": "error", "error": str(e)}

        # Determine overall status
        component_statuses = [
            comp.get("status", "unknown")
            for comp in health_report["components"].values()
        ]

        if all(status == "healthy" for status in component_statuses):
            health_report["overall_status"] = "healthy"
        elif any(status == "error" for status in component_statuses):
            health_report["overall_status"] = "critical"
        elif any(status == "warning" for status in component_statuses):
            health_report["overall_status"] = "warning"
        else:
            health_report["overall_status"] = "degraded"

        return {"status": "success", "data": health_report}

    except Exception as e:
        logger.error(f"Error fetching system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch system health: {str(e)}",
        )


@router.get("/metrics/summary")
async def get_performance_summary(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get performance summary with key metrics

    Quick overview of system performance.
    """
    try:
        summary = {"timestamp": time.time(), "performance_score": 0, "metrics": {}}

        # Cache metrics
        if cache_manager.connected:
            cache_stats = await cache_manager.get_stats()
            summary["metrics"]["cache"] = {
                "type": cache_stats.get("cache_type", "unknown"),
                "hit_rate": cache_stats.get("hit_rate", 0),
                "connected": cache_stats.get("connected", False),
            }

        # Database metrics
        if db_optimizer.pool:
            db_stats = await db_optimizer.get_database_stats()
            summary["metrics"]["database"] = {
                "avg_response_time": db_stats["connection_stats"]["avg_response_time"],
                "total_queries": db_stats["connection_stats"]["total_queries"],
                "slow_queries": db_stats["connection_stats"]["slow_queries"],
                "pool_size": db_stats["pool_stats"]["pool_size"],
            }

        # System metrics
        process = psutil.Process(os.getpid())
        summary["metrics"]["system"] = {
            "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "cpu_percent": process.cpu_percent(),
            "uptime_hours": round((time.time() - process.create_time()) / 3600, 2),
        }

        # Calculate performance score (0-100)
        score = 100

        # Reduce score for poor metrics
        if summary["metrics"].get("cache", {}).get("hit_rate", 0) < 50:
            score -= 20
        if summary["metrics"].get("database", {}).get("avg_response_time", 0) > 0.1:
            score -= 15
        if summary["metrics"].get("system", {}).get("memory_mb", 0) > 500:
            score -= 10
        if summary["metrics"].get("system", {}).get("cpu_percent", 0) > 50:
            score -= 10

        summary["performance_score"] = max(0, score)
        summary["performance_grade"] = (
            "A"
            if score >= 90
            else (
                "B"
                if score >= 80
                else "C" if score >= 70 else "D" if score >= 60 else "F"
            )
        )

        return {"status": "success", "data": summary}

    except Exception as e:
        logger.error(f"Error generating performance summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate performance summary: {str(e)}",
        )
