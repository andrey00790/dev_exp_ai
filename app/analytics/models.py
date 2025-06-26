"""
Analytics Database Models

Defines models for storing and analyzing various metrics including:
- Usage patterns and statistics
- Cost tracking and optimization
- Performance metrics
- User behavior analytics
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey, Text, Index
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

Base = declarative_base()


class MetricType(str, Enum):
    """Types of metrics we track"""
    USAGE = "usage"
    COST = "cost"
    PERFORMANCE = "performance"
    BEHAVIOR = "behavior"
    SECURITY = "security"
    ERROR = "error"


class AggregationPeriod(str, Enum):
    """Aggregation periods for metrics"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class UsageMetric(Base):
    """Usage metrics and statistics"""
    __tablename__ = "usage_metrics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Time and identification
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # Usage details
    feature = Column(String(100), nullable=False, index=True)  # search, generation, etc.
    action = Column(String(100), nullable=False, index=True)   # query, generate, upload, etc.
    resource = Column(String(200), nullable=True)             # specific resource used
    
    # Metrics
    count = Column(Integer, default=1, nullable=False)
    duration_ms = Column(Float, nullable=True)                # Duration in milliseconds
    bytes_processed = Column(Integer, nullable=True)          # Data size processed
    tokens_used = Column(Integer, nullable=True)              # LLM tokens consumed
    
    # Context
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    api_version = Column(String(20), nullable=True)
    
    # Status and extra data
    success = Column(Boolean, default=True, nullable=False)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_usage_metrics_timestamp_feature', 'timestamp', 'feature'),
        Index('ix_usage_metrics_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_usage_metrics_feature_success', 'feature', 'success'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "feature": self.feature,
            "action": self.action,
            "resource": self.resource,
            "count": self.count,
            "duration_ms": self.duration_ms,
            "bytes_processed": self.bytes_processed,
            "tokens_used": self.tokens_used,
            "success": self.success,
            "error_code": self.error_code,
            "extra_data": self.extra_data
        }


class CostMetric(Base):
    """Cost tracking and analysis"""
    __tablename__ = "cost_metrics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Time and identification
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    
    # Cost details
    service = Column(String(100), nullable=False, index=True)  # openai, anthropic, qdrant, etc.
    operation = Column(String(100), nullable=False)           # completion, embedding, search, etc.
    model = Column(String(100), nullable=True)                # gpt-4, claude-3, etc.
    
    # Usage metrics
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    requests_count = Column(Integer, default=1)
    
    # Cost calculations
    cost_per_token = Column(Float, nullable=True)
    input_cost = Column(Float, nullable=True)
    output_cost = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    
    # Context
    request_id = Column(String(255), nullable=True)
    feature_context = Column(String(100), nullable=True)
    
    # Budget tracking
    budget_category = Column(String(100), nullable=True)
    is_billable = Column(Boolean, default=True)
    
    # Extra data
    extra_data = Column(JSON, nullable=True)
    
    # Indexes for cost analysis
    __table_args__ = (
        Index('ix_cost_metrics_timestamp_service', 'timestamp', 'service'),
        Index('ix_cost_metrics_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_cost_metrics_org_timestamp', 'organization_id', 'timestamp'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "service": self.service,
            "operation": self.operation,
            "model": self.model,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "currency": self.currency,
            "is_billable": self.is_billable,
            "extra_data": self.extra_data
        }


class PerformanceMetric(Base):
    """Performance monitoring and analysis"""
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Time and identification
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Component identification
    component = Column(String(100), nullable=False, index=True)  # api, llm, database, etc.
    endpoint = Column(String(200), nullable=True, index=True)    # specific endpoint
    operation = Column(String(100), nullable=False)             # query, insert, generate, etc.
    
    # Performance metrics
    response_time_ms = Column(Float, nullable=False)
    cpu_usage_percent = Column(Float, nullable=True)
    memory_usage_mb = Column(Float, nullable=True)
    disk_io_mb = Column(Float, nullable=True)
    network_io_mb = Column(Float, nullable=True)
    
    # Request details
    request_size_bytes = Column(Integer, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)
    concurrent_requests = Column(Integer, nullable=True)
    
    # Status
    status_code = Column(Integer, nullable=True)
    success = Column(Boolean, default=True)
    error_type = Column(String(100), nullable=True)
    
    # Context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255), nullable=True)
    trace_id = Column(String(255), nullable=True)
    
    # Extra data
    extra_data = Column(JSON, nullable=True)
    
    # Indexes for performance analysis
    __table_args__ = (
        Index('ix_performance_metrics_timestamp_component', 'timestamp', 'component'),
        Index('ix_performance_metrics_endpoint_timestamp', 'endpoint', 'timestamp'),
        Index('ix_performance_metrics_success_timestamp', 'success', 'timestamp'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "component": self.component,
            "endpoint": self.endpoint,
            "operation": self.operation,
            "response_time_ms": self.response_time_ms,
            "cpu_usage_percent": self.cpu_usage_percent,
            "memory_usage_mb": self.memory_usage_mb,
            "success": self.success,
            "extra_data": self.extra_data
        }


class UserBehaviorMetric(Base):
    """User behavior analysis and patterns"""
    __tablename__ = "user_behavior_metrics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Time and identification
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    
    # Behavior tracking
    page_path = Column(String(500), nullable=True)
    event_type = Column(String(100), nullable=False, index=True)  # page_view, click, search, etc.
    event_name = Column(String(200), nullable=False)
    
    # Interaction details
    element_id = Column(String(200), nullable=True)
    element_text = Column(Text, nullable=True)
    click_coordinates = Column(JSON, nullable=True)  # {x: int, y: int}
    
    # Session context
    session_duration_ms = Column(Integer, nullable=True)
    page_view_duration_ms = Column(Integer, nullable=True)
    referrer = Column(String(500), nullable=True)
    
    # User context
    user_agent = Column(String(500), nullable=True)
    screen_resolution = Column(String(20), nullable=True)  # "1920x1080"
    browser = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    
    # Search and interaction
    search_query = Column(Text, nullable=True)
    search_results_count = Column(Integer, nullable=True)
    selected_result_position = Column(Integer, nullable=True)
    
    # Conversion tracking
    conversion_event = Column(String(100), nullable=True)
    conversion_value = Column(Float, nullable=True)
    
    # A/B testing
    experiment_id = Column(String(100), nullable=True)
    variant = Column(String(50), nullable=True)
    
    # Extra data
    extra_data = Column(JSON, nullable=True)
    
    # Indexes for behavior analysis
    __table_args__ = (
        Index('ix_behavior_metrics_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_behavior_metrics_session_timestamp', 'session_id', 'timestamp'),
        Index('ix_behavior_metrics_event_timestamp', 'event_type', 'timestamp'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "event_name": self.event_name,
            "page_path": self.page_path,
            "search_query": self.search_query,
            "device_type": self.device_type,
            "extra_data": self.extra_data
        }


class AggregatedMetric(Base):
    """Pre-aggregated metrics for fast dashboard queries"""
    __tablename__ = "aggregated_metrics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Time and aggregation
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)
    aggregation_period = Column(String(20), nullable=False, index=True)  # AggregationPeriod
    
    # Metric identification
    metric_type = Column(String(50), nullable=False, index=True)  # MetricType
    metric_name = Column(String(100), nullable=False, index=True)
    dimension = Column(String(100), nullable=True, index=True)    # user_id, feature, etc.
    dimension_value = Column(String(500), nullable=True)
    
    # Aggregated values
    count = Column(Integer, nullable=True)
    sum_value = Column(Float, nullable=True)
    avg_value = Column(Float, nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    
    # Additional statistics
    p50_value = Column(Float, nullable=True)  # Median
    p95_value = Column(Float, nullable=True)  # 95th percentile
    p99_value = Column(Float, nullable=True)  # 99th percentile
    
    # Extra data
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Unique constraint to prevent duplicates
    __table_args__ = (
        Index('ix_aggregated_unique', 'period_start', 'aggregation_period', 'metric_type', 'metric_name', 'dimension', 'dimension_value', unique=True),
        Index('ix_aggregated_period_type', 'aggregation_period', 'metric_type'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "aggregation_period": self.aggregation_period,
            "metric_type": self.metric_type,
            "metric_name": self.metric_name,
            "dimension": self.dimension,
            "dimension_value": self.dimension_value,
            "count": self.count,
            "sum_value": self.sum_value,
            "avg_value": self.avg_value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "p95_value": self.p95_value,
            "extra_data": self.extra_data
        }


class InsightReport(Base):
    """Generated insights and recommendations"""
    __tablename__ = "insight_reports"

    id = Column(Integer, primary_key=True, index=True)
    
    # Report identification
    report_type = Column(String(100), nullable=False, index=True)  # cost_optimization, performance, usage
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Insight data
    insights = Column(JSON, nullable=False)  # List of insights with scores
    recommendations = Column(JSON, nullable=True)  # List of actionable recommendations
    
    # Scoring and priority
    impact_score = Column(Float, nullable=True)  # 0-100
    confidence_score = Column(Float, nullable=True)  # 0-100
    priority = Column(String(20), nullable=True)  # high, medium, low
    
    # Context
    affected_users = Column(JSON, nullable=True)  # List of user IDs
    affected_features = Column(JSON, nullable=True)  # List of feature names
    
    # Status
    status = Column(String(50), default="active")  # active, archived, implemented
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Extra data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    extra_data = Column(JSON, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "report_type": self.report_type,
            "title": self.title,
            "description": self.description,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "insights": self.insights,
            "recommendations": self.recommendations,
            "impact_score": self.impact_score,
            "confidence_score": self.confidence_score,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "extra_data": self.extra_data
        } 