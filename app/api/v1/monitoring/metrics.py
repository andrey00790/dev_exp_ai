"""
Prometheus Metrics API Endpoint
Предоставляет /metrics endpoint для Prometheus scraping
"""

import logging
from fastapi import APIRouter, Response
from app.monitoring.prometheus_metrics import get_metrics, get_metrics_content_type, metrics_collector

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Monitoring"])

@router.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus format for scraping
    """
    try:
        # Get metrics in Prometheus format
        metrics_text = get_metrics()
        content_type = get_metrics_content_type()
        
        return Response(
            content=metrics_text,
            media_type=content_type,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to generate Prometheus metrics: {e}")
        metrics_collector.record_error("metrics_export", "monitoring", "error")
        return Response(
            content="# Metrics generation failed\n",
            media_type="text/plain",
            status_code=500
        )

@router.get("/health/metrics")
async def metrics_health():
    """
    Health check for metrics system
    """
    try:
        # Simple health check - try to generate metrics
        metrics_text = get_metrics()
        metrics_count = len([line for line in metrics_text.split('\n') if line and not line.startswith('#')])
        
        return {
            "status": "healthy",
            "service": "prometheus_metrics",
            "metrics_count": metrics_count,
            "last_update": "real-time",
            "features": [
                "http_requests",
                "ai_operations", 
                "search_operations",
                "system_resources",
                "business_metrics"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Metrics health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "prometheus_metrics",
            "error": str(e)
        }

@router.post("/metrics/record/demo")
async def record_demo_metrics():
    """
    Demo endpoint to record sample metrics for testing
    """
    try:
        # Record sample metrics for demonstration
        metrics_collector.record_http_request("GET", "/demo", 200, 0.150, "demo_user")
        metrics_collector.record_ai_operation("chat", "gpt-4", 2.5, 150, 0.03, "success")
        metrics_collector.record_search_operation("semantic", "confluence", 1.2, 25)
        metrics_collector.record_user_session("login", "demo_user_123")
        metrics_collector.record_database_operation("select", 0.05)
        metrics_collector.record_cache_operation("get", "hit", "redis")
        metrics_collector.record_vector_operation("search", "confluence", 0.8, "success")
        
        logger.info("✅ Demo metrics recorded successfully")
        
        return {
            "status": "success",
            "message": "Demo metrics recorded",
            "metrics_recorded": [
                "http_request",
                "ai_operation",
                "search_operation", 
                "user_session",
                "database_operation",
                "cache_operation",
                "vector_operation"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to record demo metrics: {e}")
        return {
            "status": "error",
            "message": f"Failed to record demo metrics: {e}"
        } 