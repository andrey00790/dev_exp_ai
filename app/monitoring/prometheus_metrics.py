"""
Prometheus Metrics for AI Assistant MVP
Комплексные бизнес-метрики для enterprise monitoring
"""

import time
import logging
from typing import Dict, Any, Optional, List
from prometheus_client import (
    Counter, Histogram, Gauge, Info, Enum, 
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from functools import wraps
import psutil
import asyncio

logger = logging.getLogger(__name__)

# Создаем собственный registry для изоляции метрик
REGISTRY = CollectorRegistry()

# ============================================================================
# Core Application Metrics
# ============================================================================

# HTTP Request Metrics
http_requests_total = Counter(
    'ai_assistant_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status', 'user_type'],
    registry=REGISTRY
)

http_request_duration_seconds = Histogram(
    'ai_assistant_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
    registry=REGISTRY
)

# ============================================================================
# Business Metrics
# ============================================================================

# User Activity Metrics
active_users_total = Gauge(
    'ai_assistant_active_users_total',
    'Number of active users',
    ['time_window'],  # 1m, 5m, 15m, 1h, 24h
    registry=REGISTRY
)

user_sessions_total = Counter(
    'ai_assistant_user_sessions_total',
    'Total user sessions',
    ['session_type'],  # login, logout, refresh
    registry=REGISTRY
)

# AI Operations Metrics
ai_requests_total = Counter(
    'ai_assistant_ai_requests_total',
    'Total AI requests',
    ['operation_type', 'model', 'status'],  # operation: chat, search, rfc, analysis
    registry=REGISTRY
)

ai_request_duration_seconds = Histogram(
    'ai_assistant_ai_request_duration_seconds',
    'AI request duration in seconds',
    ['operation_type', 'model'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
    registry=REGISTRY
)

ai_tokens_used_total = Counter(
    'ai_assistant_ai_tokens_used_total',
    'Total AI tokens used',
    ['model', 'operation_type'],
    registry=REGISTRY
)

ai_cost_usd_total = Counter(
    'ai_assistant_ai_cost_usd_total',
    'Total AI cost in USD',
    ['model', 'operation_type'],
    registry=REGISTRY
)

# Search Metrics
search_requests_total = Counter(
    'ai_assistant_search_requests_total',
    'Total search requests',
    ['search_type', 'source'],  # search_type: semantic, vector, hybrid
    registry=REGISTRY
)

search_duration_seconds = Histogram(
    'ai_assistant_search_duration_seconds',
    'Search duration in seconds',
    ['search_type', 'source'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
    registry=REGISTRY
)

search_results_count = Histogram(
    'ai_assistant_search_results_count',
    'Number of search results returned',
    ['search_type'],
    buckets=[0, 1, 5, 10, 25, 50, 100, 250, 500],
    registry=REGISTRY
)

# Document Operations
documents_processed_total = Counter(
    'ai_assistant_documents_processed_total',
    'Total documents processed',
    ['operation', 'source', 'status'],  # operation: index, update, delete
    registry=REGISTRY
)

document_processing_duration_seconds = Histogram(
    'ai_assistant_document_processing_duration_seconds',
    'Document processing duration in seconds',
    ['operation', 'source'],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0],
    registry=REGISTRY
)

# ============================================================================
# System Performance Metrics
# ============================================================================

# Database Metrics
database_connections_active = Gauge(
    'ai_assistant_database_connections_active',
    'Number of active database connections',
    registry=REGISTRY
)

database_query_duration_seconds = Histogram(
    'ai_assistant_database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],  # select, insert, update, delete
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=REGISTRY
)

# Cache Metrics
cache_operations_total = Counter(
    'ai_assistant_cache_operations_total',
    'Total cache operations',
    ['operation', 'status'],  # operation: get, set, delete; status: hit, miss, error
    registry=REGISTRY
)

cache_hit_ratio = Gauge(
    'ai_assistant_cache_hit_ratio',
    'Cache hit ratio (0-1)',
    ['cache_type'],  # redis, local
    registry=REGISTRY
)

# Vector Database Metrics
vector_operations_total = Counter(
    'ai_assistant_vector_operations_total',
    'Total vector database operations',
    ['operation', 'collection', 'status'],  # operation: search, upsert, delete
    registry=REGISTRY
)

vector_search_duration_seconds = Histogram(
    'ai_assistant_vector_search_duration_seconds',
    'Vector search duration in seconds',
    ['collection'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
    registry=REGISTRY
)

# ============================================================================
# System Resource Metrics
# ============================================================================

# Application Info
app_info = Info(
    'ai_assistant_app_info',
    'Application information',
    registry=REGISTRY
)

# System Resources
system_cpu_usage_percent = Gauge(
    'ai_assistant_system_cpu_usage_percent',
    'System CPU usage percentage',
    registry=REGISTRY
)

system_memory_usage_bytes = Gauge(
    'ai_assistant_system_memory_usage_bytes',
    'System memory usage in bytes',
    ['type'],  # total, available, used
    registry=REGISTRY
)

system_disk_usage_bytes = Gauge(
    'ai_assistant_system_disk_usage_bytes',
    'System disk usage in bytes',
    ['type'],  # total, used, free
    registry=REGISTRY
)

# Application Health
app_health_status = Enum(
    'ai_assistant_app_health_status',
    'Application health status',
    states=['healthy', 'degraded', 'unhealthy'],
    registry=REGISTRY
)

app_uptime_seconds = Gauge(
    'ai_assistant_app_uptime_seconds',
    'Application uptime in seconds',
    registry=REGISTRY
)

# Error Tracking
errors_total = Counter(
    'ai_assistant_errors_total',
    'Total application errors',
    ['error_type', 'component', 'severity'],
    registry=REGISTRY
)

# ============================================================================
# Metrics Collection and Utilities
# ============================================================================

class MetricsCollector:
    """Centralized metrics collector for business operations"""
    
    def __init__(self):
        self.start_time = time.time()
        self._active_users_cache = {}
        self._last_system_update = 0
        
    def record_http_request(self, method: str, endpoint: str, status: int, 
                           duration: float, user_type: str = "anonymous"):
        """Record HTTP request metrics"""
        http_requests_total.labels(
            method=method, 
            endpoint=endpoint, 
            status=str(status),
            user_type=user_type
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_ai_operation(self, operation_type: str, model: str, 
                           duration: float, tokens_used: int = 0, 
                           cost_usd: float = 0.0, status: str = "success"):
        """Record AI operation metrics"""
        ai_requests_total.labels(
            operation_type=operation_type,
            model=model,
            status=status
        ).inc()
        
        ai_request_duration_seconds.labels(
            operation_type=operation_type,
            model=model
        ).observe(duration)
        
        if tokens_used > 0:
            ai_tokens_used_total.labels(
                model=model,
                operation_type=operation_type
            ).inc(tokens_used)
        
        if cost_usd > 0:
            ai_cost_usd_total.labels(
                model=model,
                operation_type=operation_type
            ).inc(cost_usd)
    
    def record_search_operation(self, search_type: str, source: str, 
                               duration: float, results_count: int):
        """Record search operation metrics"""
        search_requests_total.labels(
            search_type=search_type,
            source=source
        ).inc()
        
        search_duration_seconds.labels(
            search_type=search_type,
            source=source
        ).observe(duration)
        
        search_results_count.labels(
            search_type=search_type
        ).observe(results_count)
    
    def record_user_session(self, session_type: str, user_id: str = ""):
        """Record user session metrics"""
        user_sessions_total.labels(session_type=session_type).inc()
        
        # Update active users (simplified tracking)
        if session_type == "login" and user_id:
            self._active_users_cache[user_id] = time.time()
            self._update_active_users_metrics()
    
    def record_database_operation(self, operation: str, duration: float):
        """Record database operation metrics"""
        database_query_duration_seconds.labels(operation=operation).observe(duration)
    
    def record_cache_operation(self, operation: str, status: str, cache_type: str = "redis"):
        """Record cache operation metrics"""
        cache_operations_total.labels(operation=operation, status=status).inc()
    
    def record_vector_operation(self, operation: str, collection: str, 
                               duration: float, status: str = "success"):
        """Record vector database operation metrics"""
        vector_operations_total.labels(
            operation=operation,
            collection=collection,
            status=status
        ).inc()
        
        if operation == "search":
            vector_search_duration_seconds.labels(collection=collection).observe(duration)
    
    def record_error(self, error_type: str, component: str, severity: str = "error"):
        """Record application error"""
        errors_total.labels(
            error_type=error_type,
            component=component,
            severity=severity
        ).inc()
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        try:
            # CPU Usage
            cpu_percent = psutil.cpu_percent(interval=1)
            system_cpu_usage_percent.set(cpu_percent)
            
            # Memory Usage
            memory = psutil.virtual_memory()
            system_memory_usage_bytes.labels(type="total").set(memory.total)
            system_memory_usage_bytes.labels(type="available").set(memory.available)
            system_memory_usage_bytes.labels(type="used").set(memory.used)
            
            # Disk Usage
            disk = psutil.disk_usage('/')
            system_disk_usage_bytes.labels(type="total").set(disk.total)
            system_disk_usage_bytes.labels(type="used").set(disk.used)
            system_disk_usage_bytes.labels(type="free").set(disk.free)
            
            # App Uptime
            uptime = time.time() - self.start_time
            app_uptime_seconds.set(uptime)
            
            self._last_system_update = time.time()
            
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
            self.record_error("system_metrics", "monitoring", "warning")
    
    def _update_active_users_metrics(self):
        """Update active users metrics with time windows"""
        current_time = time.time()
        
        # Clean old users and count active users for different time windows
        time_windows = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "1h": 3600,
            "24h": 86400
        }
        
        for window, seconds in time_windows.items():
            active_count = sum(
                1 for last_seen in self._active_users_cache.values()
                if current_time - last_seen <= seconds
            )
            active_users_total.labels(time_window=window).set(active_count)
    
    def set_app_info(self, version: str, environment: str, build_date: str):
        """Set application information"""
        app_info.info({
            'version': version,
            'environment': environment,
            'build_date': build_date,
            'python_version': '3.11+',
            'framework': 'FastAPI'
        })
    
    def set_health_status(self, status: str):
        """Set application health status"""
        if status in ['healthy', 'degraded', 'unhealthy']:
            app_health_status.state(status)

# ============================================================================
# Decorators for Automatic Metrics Collection
# ============================================================================

# Global metrics collector instance
metrics_collector = MetricsCollector()

def track_http_requests():
    """Decorator to automatically track HTTP requests"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 200
            user_type = "authenticated"  # Default
            
            try:
                # Extract request info
                request = None
                for arg in args:
                    if hasattr(arg, 'method') and hasattr(arg, 'url'):
                        request = arg
                        break
                
                result = await func(*args, **kwargs)
                return result
                
            except Exception as e:
                status = getattr(e, 'status_code', 500)
                raise
            finally:
                duration = time.time() - start_time
                
                if request:
                    method = request.method
                    endpoint = request.url.path
                    metrics_collector.record_http_request(method, endpoint, status, duration, user_type)
        
        return wrapper
    return decorator

def track_ai_operations(operation_type: str, model: str = "default"):
    """Decorator to automatically track AI operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # Extract metrics from result if available
                tokens_used = getattr(result, 'tokens_used', 0)
                cost_usd = getattr(result, 'cost_usd', 0.0)
                
                duration = time.time() - start_time
                metrics_collector.record_ai_operation(
                    operation_type, model, duration, tokens_used, cost_usd, "success"
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                metrics_collector.record_ai_operation(
                    operation_type, model, duration, 0, 0.0, "error"
                )
                raise
        
        return wrapper
    return decorator

def track_database_operations(operation: str):
    """Decorator to automatically track database operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                metrics_collector.record_database_operation(operation, duration)
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                metrics_collector.record_database_operation(f"{operation}_error", duration)
                raise
        
        return wrapper
    return decorator

# ============================================================================
# Metrics Export
# ============================================================================

def get_metrics() -> str:
    """Get Prometheus metrics in text format"""
    # Update system metrics before export
    metrics_collector.update_system_metrics()
    return generate_latest(REGISTRY).decode('utf-8')

def get_metrics_content_type() -> str:
    """Get content type for metrics"""
    return CONTENT_TYPE_LATEST

# ============================================================================
# Background Tasks
# ============================================================================

async def start_metrics_collection():
    """Start background metrics collection"""
    try:
        # Set initial app info
        metrics_collector.set_app_info(
            version="8.0.0",
            environment="production",
            build_date="2024-12-28"
        )
        
        # Set initial health status
        metrics_collector.set_health_status("healthy")
        
        logger.info("✅ Prometheus metrics collection started")
        
        # Background task to update system metrics every 30 seconds
        while True:
            await asyncio.sleep(30)
            metrics_collector.update_system_metrics()
            
    except Exception as e:
        logger.error(f"❌ Metrics collection error: {e}")
        metrics_collector.record_error("metrics_collection", "monitoring", "critical") 