"""
AI Assistant MVP - Application Performance Monitoring (APM)
OpenTelemetry integration for distributed tracing and metrics
"""

import os
import logging
import time
from functools import wraps
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.semantic_conventions.resource import ResourceAttributes

logger = logging.getLogger(__name__)

class APMManager:
    """Manages Application Performance Monitoring setup and instrumentation."""
    
    def __init__(self, service_name: str = "ai-assistant-mvp", environment: str = "production"):
        self.service_name = service_name
        self.environment = environment
        self.tracer = None
        self.meter = None
        self._initialized = False
        
        # Custom metrics
        self.request_counter = None
        self.request_duration = None
        self.error_counter = None
        self.active_requests = None
        self.llm_request_counter = None
        self.llm_token_counter = None
        self.cache_hit_counter = None
        self.database_query_duration = None
        
    def initialize(self) -> None:
        """Initialize OpenTelemetry tracing and metrics."""
        if self._initialized:
            logger.warning("APM already initialized")
            return
            
        try:
            # Create resource
            resource = Resource.create({
                ResourceAttributes.SERVICE_NAME: self.service_name,
                ResourceAttributes.SERVICE_VERSION: "2.1.0",
                ResourceAttributes.DEPLOYMENT_ENVIRONMENT: self.environment,
                ResourceAttributes.SERVICE_NAMESPACE: "ai-assistant",
                ResourceAttributes.SERVICE_INSTANCE_ID: os.getenv("HOSTNAME", "unknown"),
            })
            
            # Setup tracing
            self._setup_tracing(resource)
            
            # Setup metrics
            self._setup_metrics(resource)
            
            # Auto-instrument common libraries
            self._setup_auto_instrumentation()
            
            self._initialized = True
            logger.info(f"APM initialized for service: {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize APM: {e}")
            raise
    
    def _setup_tracing(self, resource: Resource) -> None:
        """Setup distributed tracing with Jaeger."""
        # Configure tracer provider
        trace.set_tracer_provider(TracerProvider(resource=resource))
        
        # Setup Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=os.getenv("JAEGER_AGENT_HOST", "localhost"),
            agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
            collector_endpoint=os.getenv("JAEGER_ENDPOINT", "http://localhost:14268/api/traces"),
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(
            jaeger_exporter,
            max_queue_size=2048,
            max_export_batch_size=512,
            export_timeout_millis=30000,
            schedule_delay_millis=5000,
        )
        
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        # Get tracer
        self.tracer = trace.get_tracer(__name__)
        
        logger.info("Distributed tracing configured with Jaeger")
    
    def _setup_metrics(self, resource: Resource) -> None:
        """Setup metrics collection with Prometheus."""
        # Configure metric reader
        prometheus_reader = PrometheusMetricReader()
        
        # Configure meter provider
        metrics.set_meter_provider(
            MeterProvider(
                resource=resource,
                metric_readers=[prometheus_reader]
            )
        )
        
        # Get meter
        self.meter = metrics.get_meter(__name__)
        
        # Create custom metrics
        self._create_custom_metrics()
        
        logger.info("Metrics collection configured with Prometheus")
    
    def _create_custom_metrics(self) -> None:
        """Create application-specific metrics."""
        # HTTP Request metrics
        self.request_counter = self.meter.create_counter(
            name="http_requests_total",
            description="Total HTTP requests",
            unit="1"
        )
        
        self.request_duration = self.meter.create_histogram(
            name="http_request_duration_seconds",
            description="HTTP request duration",
            unit="s"
        )
        
        self.error_counter = self.meter.create_counter(
            name="http_errors_total",
            description="Total HTTP errors",
            unit="1"
        )
        
        self.active_requests = self.meter.create_up_down_counter(
            name="http_requests_active",
            description="Active HTTP requests",
            unit="1"
        )
        
        # LLM-specific metrics
        self.llm_request_counter = self.meter.create_counter(
            name="llm_requests_total",
            description="Total LLM requests",
            unit="1"
        )
        
        self.llm_token_counter = self.meter.create_counter(
            name="llm_tokens_total",
            description="Total LLM tokens used",
            unit="1"
        )
        
        # Cache metrics
        self.cache_hit_counter = self.meter.create_counter(
            name="cache_operations_total",
            description="Total cache operations",
            unit="1"
        )
        
        # Database metrics
        self.database_query_duration = self.meter.create_histogram(
            name="database_query_duration_seconds",
            description="Database query duration",
            unit="s"
        )
        
        logger.info("Custom application metrics created")
    
    def _setup_auto_instrumentation(self) -> None:
        """Setup automatic instrumentation for common libraries."""
        try:
            # FastAPI instrumentation
            FastAPIInstrumentor.instrument()
            
            # HTTP requests instrumentation
            RequestsInstrumentor().instrument()
            
            # Database instrumentation
            Psycopg2Instrumentor().instrument()
            
            # Redis instrumentation  
            RedisInstrumentor().instrument()
            
            logger.info("Auto-instrumentation configured")
            
        except Exception as e:
            logger.warning(f"Some auto-instrumentation failed: {e}")
    
    # Decorators for custom instrumentation
    def trace_function(self, name: Optional[str] = None):
        """Decorator to trace function calls."""
        def decorator(func: Callable) -> Callable:
            span_name = name or f"{func.__module__}.{func.__name__}"
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.tracer.start_as_current_span(span_name) as span:
                    try:
                        # Add function parameters as attributes
                        span.set_attribute("function.name", func.__name__)
                        span.set_attribute("function.module", func.__module__)
                        
                        result = await func(*args, **kwargs)
                        span.set_attribute("function.result.success", True)
                        return result
                    except Exception as e:
                        span.set_attribute("function.result.success", False)
                        span.set_attribute("function.error.type", type(e).__name__)
                        span.set_attribute("function.error.message", str(e))
                        raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.tracer.start_as_current_span(span_name) as span:
                    try:
                        # Add function parameters as attributes
                        span.set_attribute("function.name", func.__name__)
                        span.set_attribute("function.module", func.__module__)
                        
                        result = func(*args, **kwargs)
                        span.set_attribute("function.result.success", True)
                        return result
                    except Exception as e:
                        span.set_attribute("function.result.success", False)
                        span.set_attribute("function.error.type", type(e).__name__)
                        span.set_attribute("function.error.message", str(e))
                        raise
            
            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
                
        return decorator
    
    def record_http_request(self, method: str, path: str, status_code: int, duration: float) -> None:
        """Record HTTP request metrics."""
        if not self._initialized:
            return
            
        attributes = {
            "method": method,
            "path": path,
            "status_code": str(status_code),
            "status_class": f"{status_code // 100}xx"
        }
        
        # Increment request counter
        self.request_counter.add(1, attributes)
        
        # Record request duration
        self.request_duration.record(duration, attributes)
        
        # Increment error counter for errors
        if status_code >= 400:
            self.error_counter.add(1, attributes)
    
    def record_llm_request(self, provider: str, model: str, tokens_used: int, duration: float, success: bool) -> None:
        """Record LLM request metrics."""
        if not self._initialized:
            return
            
        attributes = {
            "provider": provider,
            "model": model,
            "success": str(success)
        }
        
        # Increment LLM request counter
        self.llm_request_counter.add(1, attributes)
        
        # Record tokens used
        self.llm_token_counter.add(tokens_used, attributes)
    
    def record_cache_operation(self, operation: str, hit: bool) -> None:
        """Record cache operation metrics."""
        if not self._initialized:
            return
            
        attributes = {
            "operation": operation,
            "result": "hit" if hit else "miss"
        }
        
        self.cache_hit_counter.add(1, attributes)
    
    def record_database_query(self, query_type: str, duration: float, success: bool) -> None:
        """Record database query metrics."""
        if not self._initialized:
            return
            
        attributes = {
            "query_type": query_type,
            "success": str(success)
        }
        
        self.database_query_duration.record(duration, attributes)
    
    @contextmanager
    def trace_operation(self, operation_name: str, **attributes):
        """Context manager for tracing operations."""
        if not self._initialized:
            yield
            return
            
        with self.tracer.start_as_current_span(operation_name) as span:
            # Add custom attributes
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
            
            start_time = time.time()
            try:
                yield span
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                raise
            finally:
                duration = time.time() - start_time
                span.set_attribute("duration", duration)
    
    @contextmanager
    def active_request_tracking(self):
        """Track active requests."""
        if not self._initialized:
            yield
            return
            
        self.active_requests.add(1)
        try:
            yield
        finally:
            self.active_requests.add(-1)

# Global APM instance
apm_manager = APMManager()

# Convenience functions
def initialize_apm(service_name: str = "ai-assistant-mvp", environment: str = "production") -> None:
    """Initialize APM with configuration."""
    apm_manager.service_name = service_name
    apm_manager.environment = environment
    apm_manager.initialize()

def trace(name: Optional[str] = None):
    """Decorator for tracing functions."""
    return apm_manager.trace_function(name)

def record_http_metrics(method: str, path: str, status_code: int, duration: float) -> None:
    """Record HTTP request metrics."""
    apm_manager.record_http_request(method, path, status_code, duration)

def record_llm_metrics(provider: str, model: str, tokens_used: int, duration: float, success: bool) -> None:
    """Record LLM request metrics."""
    apm_manager.record_llm_request(provider, model, tokens_used, duration, success)

def trace_operation(operation_name: str, **attributes):
    """Context manager for tracing operations."""
    return apm_manager.trace_operation(operation_name, **attributes)

def active_request_context():
    """Context manager for tracking active requests."""
    return apm_manager.active_request_tracking() 