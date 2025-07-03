"""
Core Optimization API Endpoints for AI Assistant - Phase 3
Enhanced async patterns, repository integration, and performance optimization

Features:
- Core Logic Engine management and statistics
- Smart Repository Integration control
- Performance Optimization monitoring
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

# Security
from app.security.auth import get_current_user
from domain.code_optimization.performance_optimization_engine import (
    PerformanceMetricType, get_performance_dashboard,
    initialize_performance_engine, perf_engine, record_response_time)
# Phase 3 imports
from domain.core.core_logic_engine import (TaskType, core_engine,
                                           execute_intelligently,
                                           get_core_engine_stats,
                                           initialize_core_engine)
from domain.integration.smart_repository_integration import (
    DataSourceConfig, DataSourceType, SyncStrategy, get_repository_stats,
    initialize_smart_repository, search_repositories, smart_repo,
    sync_all_sources)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/core-optimization", tags=["Core Optimization"])


# Request/Response Models
class EngineInitRequest(BaseModel):
    """Request to initialize core engines"""

    engines: List[str] = Field(default=["core", "repository", "performance"])
    force_reinit: bool = Field(default=False)


class RepositorySourceRequest(BaseModel):
    """Request to register a repository source"""

    source_id: str
    source_type: str
    name: str
    connection_params: Dict[str, Any]
    sync_strategy: str = "smart_adaptive"
    enabled: bool = True


class SearchRepositoriesRequest(BaseModel):
    """Request to search repositories"""

    query: str
    source_types: Optional[List[str]] = None
    limit: int = Field(default=50, ge=1, le=200)


class PerformanceMetricRequest(BaseModel):
    """Request to record performance metric"""

    metric_type: str
    value: float
    component: Optional[str] = None


class IntelligentExecutionRequest(BaseModel):
    """Request for intelligent function execution"""

    function_name: str
    task_type: str = "mixed_workload"
    enable_circuit_breaker: bool = True
    enable_coalescing: bool = True
    enable_adaptive_timeout: bool = True


# Core Engine Endpoints
@router.post("/engines/initialize")
async def initialize_engines(
    request: EngineInitRequest, current_user=Depends(get_current_user)
):
    """Initialize core optimization engines"""
    try:
        logger.info(f"🚀 Initializing engines: {request.engines}")

        initialization_results = {}

        if "core" in request.engines:
            result = await initialize_core_engine()
            initialization_results["core_engine"] = result

        if "repository" in request.engines:
            result = await initialize_smart_repository()
            initialization_results["repository_integration"] = result

        if "performance" in request.engines:
            result = await initialize_performance_engine()
            initialization_results["performance_optimization"] = result

        success_count = sum(1 for result in initialization_results.values() if result)

        return {
            "status": "success" if success_count == len(request.engines) else "partial",
            "message": f"Initialized {success_count}/{len(request.engines)} engines",
            "results": initialization_results,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Engine initialization failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Engine initialization failed: {str(e)}"
        )


@router.get("/engines/stats")
async def get_engines_stats(current_user=Depends(get_current_user)):
    """Get comprehensive statistics for all engines"""
    try:
        # Collect stats from all engines concurrently
        stats_tasks = [
            get_core_engine_stats(),
            get_repository_stats(),
            get_performance_dashboard(),
        ]

        core_stats, repo_stats, perf_stats = await asyncio.gather(
            *stats_tasks, return_exceptions=True
        )

        # Handle exceptions gracefully
        if isinstance(core_stats, Exception):
            core_stats = {"error": str(core_stats)}
        if isinstance(repo_stats, Exception):
            repo_stats = {"error": str(repo_stats)}
        if isinstance(perf_stats, Exception):
            perf_stats = {"error": str(perf_stats)}

        return {
            "core_engine": core_stats,
            "repository_integration": repo_stats,
            "performance_optimization": perf_stats,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Failed to get engine stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get engine stats: {str(e)}"
        )


@router.get("/engines/health")
async def check_engines_health(current_user=Depends(get_current_user)):
    """Check health status of all engines"""
    try:
        health_status = {
            "core_engine": {"status": "unknown"},
            "repository_integration": {"status": "unknown"},
            "performance_optimization": {"status": "unknown"},
        }

        # Check core engine
        try:
            core_stats = await get_core_engine_stats()
            health_status["core_engine"] = {
                "status": (
                    "healthy"
                    if core_stats.get("engine_state") == "healthy"
                    else "degraded"
                ),
                "state": core_stats.get("engine_state", "unknown"),
                "active_tasks": core_stats.get("concurrency", {}).get(
                    "active_tasks", 0
                ),
            }
        except Exception as e:
            health_status["core_engine"]["status"] = "error"
            health_status["core_engine"]["error"] = str(e)

        # Check repository integration
        try:
            repo_stats = await get_repository_stats()
            health_status["repository_integration"] = {
                "status": (
                    "healthy" if repo_stats.get("active_sources", 0) > 0 else "inactive"
                ),
                "total_sources": repo_stats.get("total_sources", 0),
                "active_sources": repo_stats.get("active_sources", 0),
            }
        except Exception as e:
            health_status["repository_integration"]["status"] = "error"
            health_status["repository_integration"]["error"] = str(e)

        # Check performance optimization
        try:
            perf_stats = await get_performance_dashboard()
            health_status["performance_optimization"] = {
                "status": (
                    "healthy"
                    if perf_stats.get("performance_score", 0) > 70
                    else "degraded"
                ),
                "performance_score": perf_stats.get("performance_score", 0),
                "active_alerts": len(perf_stats.get("active_alerts", [])),
            }
        except Exception as e:
            health_status["performance_optimization"]["status"] = "error"
            health_status["performance_optimization"]["error"] = str(e)

        # Overall health
        engine_statuses = [engine["status"] for engine in health_status.values()]
        overall_status = "healthy"
        if "error" in engine_statuses:
            overall_status = "error"
        elif "degraded" in engine_statuses:
            overall_status = "degraded"
        elif "inactive" in engine_statuses:
            overall_status = "inactive"

        return {
            "overall_status": overall_status,
            "engines": health_status,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# Repository Integration Endpoints
@router.post("/repository/sources")
async def register_repository_source(
    request: RepositorySourceRequest, current_user=Depends(get_current_user)
):
    """Register a new repository data source"""
    try:
        logger.info(f"📚 Registering repository source: {request.source_id}")

        # Map string to enum
        source_type_map = {
            "git_repository": DataSourceType.GIT_REPOSITORY,
            "confluence": DataSourceType.CONFLUENCE,
            "jira": DataSourceType.JIRA,
            "database": DataSourceType.DATABASE,
            "rest_api": DataSourceType.REST_API,
            "file_system": DataSourceType.FILE_SYSTEM,
        }

        sync_strategy_map = {
            "real_time": SyncStrategy.REAL_TIME,
            "batch_hourly": SyncStrategy.BATCH_HOURLY,
            "batch_daily": SyncStrategy.BATCH_DAILY,
            "on_demand": SyncStrategy.ON_DEMAND,
            "smart_adaptive": SyncStrategy.SMART_ADAPTIVE,
        }

        source_type = source_type_map.get(request.source_type)
        if not source_type:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported source type: {request.source_type}",
            )

        sync_strategy = sync_strategy_map.get(
            request.sync_strategy, SyncStrategy.SMART_ADAPTIVE
        )

        # Create data source configuration
        config = DataSourceConfig(
            source_id=request.source_id,
            source_type=source_type,
            name=request.name,
            connection_params=request.connection_params,
            sync_strategy=sync_strategy,
            enabled=request.enabled,
        )

        # Register the source
        success = await smart_repo.register_data_source(config)

        if success:
            return {
                "status": "success",
                "message": f"Repository source {request.source_id} registered successfully",
                "source_id": request.source_id,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to register repository source {request.source_id}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to register repository source: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to register repository source: {str(e)}"
        )


@router.post("/repository/search")
async def search_repository_sources(
    request: SearchRepositoriesRequest, current_user=Depends(get_current_user)
):
    """Search across registered repository sources"""
    try:
        logger.info(f"🔍 Searching repositories: '{request.query}'")

        # Map string types to enums if provided
        source_types = None
        if request.source_types:
            type_map = {
                "git_repository": DataSourceType.GIT_REPOSITORY,
                "confluence": DataSourceType.CONFLUENCE,
                "jira": DataSourceType.JIRA,
                "database": DataSourceType.DATABASE,
                "rest_api": DataSourceType.REST_API,
                "file_system": DataSourceType.FILE_SYSTEM,
            }
            source_types = [
                type_map[st] for st in request.source_types if st in type_map
            ]

        # Perform search
        results = await search_repositories(
            query=request.query, source_types=source_types, limit=request.limit
        )

        # Convert results to serializable format
        serialized_results = []
        for result in results:
            serialized_results.append(
                {
                    "record_id": result.record_id,
                    "source_id": result.source_id,
                    "title": result.title,
                    "content": (
                        result.content[:500] + "..."
                        if len(result.content) > 500
                        else result.content
                    ),
                    "content_type": result.content_type,
                    "tags": result.tags,
                    "metadata": result.metadata,
                    "created_at": result.created_at.isoformat(),
                    "updated_at": result.updated_at.isoformat(),
                }
            )

        return {
            "status": "success",
            "query": request.query,
            "results_count": len(serialized_results),
            "results": serialized_results,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Repository search failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Repository search failed: {str(e)}"
        )


@router.post("/repository/sync-all")
async def sync_all_repository_sources(current_user=Depends(get_current_user)):
    """Sync all registered repository sources"""
    try:
        logger.info("🔄 Syncing all repository sources")

        sync_results = await sync_all_sources()

        # Process results
        total_sources = len(sync_results)
        successful_syncs = sum(1 for result in sync_results.values() if result.success)
        total_records = sum(
            result.records_processed for result in sync_results.values()
        )

        serialized_results = {}
        for source_id, result in sync_results.items():
            serialized_results[source_id] = {
                "success": result.success,
                "records_processed": result.records_processed,
                "errors": result.errors,
                "duration": result.duration,
                "sync_timestamp": result.sync_timestamp.isoformat(),
            }

        return {
            "status": "success",
            "summary": {
                "total_sources": total_sources,
                "successful_syncs": successful_syncs,
                "failed_syncs": total_sources - successful_syncs,
                "total_records_processed": total_records,
            },
            "results": serialized_results,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Repository sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Repository sync failed: {str(e)}")


# Performance Optimization Endpoints
@router.get("/performance/dashboard")
async def get_performance_optimization_dashboard(
    current_user=Depends(get_current_user),
):
    """Get comprehensive performance optimization dashboard"""
    try:
        dashboard_data = await get_performance_dashboard()
        return {"status": "success", "dashboard": dashboard_data}

    except Exception as e:
        logger.error(f"❌ Failed to get performance dashboard: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance dashboard: {str(e)}"
        )


@router.post("/performance/metrics")
async def record_performance_metric_endpoint(
    request: PerformanceMetricRequest, current_user=Depends(get_current_user)
):
    """Record a performance metric"""
    try:
        # Map string to enum
        metric_type_map = {
            "response_time": PerformanceMetricType.RESPONSE_TIME,
            "throughput": PerformanceMetricType.THROUGHPUT,
            "error_rate": PerformanceMetricType.ERROR_RATE,
            "cpu_usage": PerformanceMetricType.CPU_USAGE,
            "memory_usage": PerformanceMetricType.MEMORY_USAGE,
            "cache_hit_rate": PerformanceMetricType.CACHE_HIT_RATE,
        }

        metric_type = metric_type_map.get(request.metric_type)
        if not metric_type:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported metric type: {request.metric_type}",
            )

        await perf_engine.record_performance_metric(
            metric_type=metric_type, value=request.value, component=request.component
        )

        return {
            "status": "success",
            "message": "Performance metric recorded",
            "metric": {
                "type": request.metric_type,
                "value": request.value,
                "component": request.component,
            },
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to record performance metric: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to record performance metric: {str(e)}"
        )


# Intelligent Execution Endpoint
@router.post("/execute/intelligent")
async def execute_function_intelligently(
    request: IntelligentExecutionRequest, current_user=Depends(get_current_user)
):
    """Execute a function with intelligent optimization patterns"""
    try:
        logger.info(f"🧠 Executing function intelligently: {request.function_name}")

        # Map string to enum
        task_type_map = {
            "cpu_intensive": TaskType.CPU_INTENSIVE,
            "io_bound": TaskType.IO_BOUND,
            "memory_intensive": TaskType.MEMORY_INTENSIVE,
            "network_heavy": TaskType.NETWORK_HEAVY,
            "mixed_workload": TaskType.MIXED_WORKLOAD,
        }

        task_type = task_type_map.get(request.task_type, TaskType.MIXED_WORKLOAD)

        # Demo function
        async def demo_function():
            await asyncio.sleep(0.1)  # Simulate work
            return {"result": f"Function {request.function_name} executed successfully"}

        start_time = datetime.now()

        # Execute with intelligent patterns
        result = await execute_intelligently(
            demo_function,
            task_type=task_type,
            enable_circuit_breaker=request.enable_circuit_breaker,
            enable_coalescing=request.enable_coalescing,
            enable_adaptive_timeout=request.enable_adaptive_timeout,
            user_id=current_user.user_id if hasattr(current_user, "user_id") else None,
        )

        execution_time = (datetime.now() - start_time).total_seconds()

        # Record performance metric
        await record_response_time(execution_time, component=request.function_name)

        return {
            "status": "success",
            "function_name": request.function_name,
            "result": result,
            "execution_metadata": {
                "task_type": request.task_type,
                "execution_time": execution_time,
                "circuit_breaker_enabled": request.enable_circuit_breaker,
                "coalescing_enabled": request.enable_coalescing,
                "adaptive_timeout_enabled": request.enable_adaptive_timeout,
            },
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Intelligent execution failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Intelligent execution failed: {str(e)}"
        )


# Quick stats endpoint for dashboard
@router.get("/quick-stats")
async def get_quick_optimization_stats(current_user=Depends(get_current_user)):
    """Get quick optimization statistics for dashboard"""
    try:
        # Get essential stats quickly
        stats_tasks = [
            get_core_engine_stats(),
            get_repository_stats(),
            get_performance_dashboard(),
        ]

        results = await asyncio.gather(*stats_tasks, return_exceptions=True)
        core_stats, repo_stats, perf_stats = results

        # Extract key metrics
        quick_stats = {
            "core_engine": {
                "state": (
                    core_stats.get("engine_state", "unknown")
                    if not isinstance(core_stats, Exception)
                    else "error"
                ),
                "active_tasks": (
                    core_stats.get("concurrency", {}).get("active_tasks", 0)
                    if not isinstance(core_stats, Exception)
                    else 0
                ),
                "error_rate": (
                    core_stats.get("metrics", {}).get("error_rate", 0)
                    if not isinstance(core_stats, Exception)
                    else 0
                ),
            },
            "repository": {
                "total_sources": (
                    repo_stats.get("total_sources", 0)
                    if not isinstance(repo_stats, Exception)
                    else 0
                ),
                "active_sources": (
                    repo_stats.get("active_sources", 0)
                    if not isinstance(repo_stats, Exception)
                    else 0
                ),
                "total_records": (
                    repo_stats.get("total_records", 0)
                    if not isinstance(repo_stats, Exception)
                    else 0
                ),
            },
            "performance": {
                "score": (
                    perf_stats.get("performance_score", 0)
                    if not isinstance(perf_stats, Exception)
                    else 0
                ),
                "active_alerts": (
                    len(perf_stats.get("active_alerts", []))
                    if not isinstance(perf_stats, Exception)
                    else 0
                ),
                "cpu_usage": (
                    perf_stats.get("system_metrics", {}).get("cpu_percent", 0)
                    if not isinstance(perf_stats, Exception)
                    else 0
                ),
                "memory_usage": (
                    perf_stats.get("system_metrics", {}).get("memory_percent", 0)
                    if not isinstance(perf_stats, Exception)
                    else 0
                ),
            },
        }

        return {
            "status": "success",
            "quick_stats": quick_stats,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Failed to get quick stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get quick stats: {str(e)}"
        )
