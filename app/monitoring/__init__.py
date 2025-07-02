"""
Monitoring module - Compatibility wrapper for infra.monitoring
"""

# Re-export everything from infra.monitoring for backward compatibility
from infra.monitoring.metrics import *
from infra.monitoring.apm import *
from infra.monitoring.middleware import *

__all__ = [
    # From metrics
    "MetricsCollector",
    "AlertManager", 
    "DashboardDataAggregator",
    "collect_metrics",
    "setup_metrics", 
    "get_metrics_handler",
    "metrics_middleware",
    "METRIC_TARGETS",
    "metrics",
    # From apm
    "APMTracker",
    "track_error",
    "track_request", 
    "get_apm_client",
    # From middleware
    "MonitoringMiddleware"
] 