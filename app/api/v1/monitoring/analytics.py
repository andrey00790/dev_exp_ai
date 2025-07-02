"""
Analytics API Endpoints

Provides comprehensive analytics endpoints for:
- Usage analytics and metrics
- Cost tracking and optimization
- Performance monitoring
- User behavior analysis
- Insights and recommendations
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from app.analytics.models import AggregationPeriod, MetricType
from app.analytics.service import AnalyticsService
from infra.database import get_db
from app.models.users import User
from app.security.auth import get_current_user, require_admin

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ==================== REQUEST/RESPONSE MODELS ====================


class MetricRecordRequest(BaseModel):
    """Base model for recording metrics"""

    metadata: Optional[Dict[str, Any]] = None


class UsageMetricRequest(MetricRecordRequest):
    """Request model for recording usage metrics"""

    feature: str = Field(
        ..., description="Feature being used (search, generation, etc.)"
    )
    action: str = Field(..., description="Specific action performed")
    resource: Optional[str] = Field(None, description="Resource accessed")
    duration_ms: Optional[float] = Field(None, description="Duration in milliseconds")
    bytes_processed: Optional[int] = Field(None, description="Bytes processed")
    tokens_used: Optional[int] = Field(None, description="LLM tokens consumed")
    success: bool = Field(True, description="Whether operation succeeded")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class CostMetricRequest(MetricRecordRequest):
    """Request model for recording cost metrics"""

    service: str = Field(..., description="Service used (openai, anthropic, etc.)")
    operation: str = Field(..., description="Operation performed")
    total_cost: float = Field(..., ge=0, description="Total cost in USD")
    model: Optional[str] = Field(None, description="Model used")
    input_tokens: Optional[int] = Field(None, ge=0, description="Input tokens")
    output_tokens: Optional[int] = Field(None, ge=0, description="Output tokens")
    currency: str = Field("USD", description="Currency code")
    is_billable: bool = Field(True, description="Whether cost is billable")


class PerformanceMetricRequest(MetricRecordRequest):
    """Request model for recording performance metrics"""

    component: str = Field(..., description="Component being measured")
    operation: str = Field(..., description="Operation performed")
    response_time_ms: float = Field(
        ..., ge=0, description="Response time in milliseconds"
    )
    endpoint: Optional[str] = Field(None, description="API endpoint")
    success: bool = Field(True, description="Whether operation succeeded")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    cpu_usage_percent: Optional[float] = Field(
        None, ge=0, le=100, description="CPU usage %"
    )
    memory_usage_mb: Optional[float] = Field(
        None, ge=0, description="Memory usage in MB"
    )


class UserBehaviorRequest(MetricRecordRequest):
    """Request model for recording user behavior"""

    event_type: str = Field(
        ..., description="Type of event (click, view, search, etc.)"
    )
    event_name: str = Field(..., description="Specific event name")
    page_path: Optional[str] = Field(None, description="Page path")
    search_query: Optional[str] = Field(None, description="Search query if applicable")
    element_id: Optional[str] = Field(None, description="UI element ID")
    device_type: Optional[str] = Field(None, description="Device type")


class DashboardTimeRange(str, Enum):
    """Predefined time ranges for dashboards"""

    LAST_HOUR = "last_hour"
    LAST_24_HOURS = "last_24_hours"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    CUSTOM = "custom"


class DashboardRequest(BaseModel):
    """Request model for dashboard data"""

    time_range: DashboardTimeRange = Field(
        DashboardTimeRange.LAST_7_DAYS, description="Time range"
    )
    start_date: Optional[datetime] = Field(None, description="Custom start date")
    end_date: Optional[datetime] = Field(None, description="Custom end date")
    aggregation: AggregationPeriod = Field(
        AggregationPeriod.DAILY, description="Aggregation period"
    )
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    organization_id: Optional[int] = Field(None, description="Filter by organization")
    component: Optional[str] = Field(None, description="Filter by component")

    @validator("end_date")
    def validate_custom_range(cls, v, values):
        if values.get("time_range") == DashboardTimeRange.CUSTOM:
            if not values.get("start_date") or not v:
                raise ValueError(
                    "start_date and end_date required for custom time range"
                )
        return v


class MetricResponse(BaseModel):
    """Response model for metric recording"""

    id: int
    timestamp: datetime
    success: bool = True
    message: str = "Metric recorded successfully"


class DashboardResponse(BaseModel):
    """Response model for dashboard data"""

    period: Dict[str, Any]
    data: Dict[str, Any]
    generated_at: datetime


# ==================== HELPER FUNCTIONS ====================


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Get analytics service instance"""
    return AnalyticsService(db)


def parse_time_range(
    time_range: DashboardTimeRange,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
) -> tuple[datetime, datetime]:
    """Parse time range into start and end dates"""
    now = datetime.utcnow()

    if time_range == DashboardTimeRange.CUSTOM:
        if not start_date or not end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date and end_date required for custom range",
            )
        return start_date, end_date
    elif time_range == DashboardTimeRange.LAST_HOUR:
        return now - timedelta(hours=1), now
    elif time_range == DashboardTimeRange.LAST_24_HOURS:
        return now - timedelta(days=1), now
    elif time_range == DashboardTimeRange.LAST_7_DAYS:
        return now - timedelta(days=7), now
    elif time_range == DashboardTimeRange.LAST_30_DAYS:
        return now - timedelta(days=30), now
    elif time_range == DashboardTimeRange.LAST_90_DAYS:
        return now - timedelta(days=90), now
    else:
        raise HTTPException(status_code=400, detail="Invalid time range")


# ==================== METRICS RECORDING ENDPOINTS ====================


@router.post("/metrics/usage", response_model=MetricResponse)
async def record_usage_metric(
    request: UsageMetricRequest,
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """Record a usage metric"""
    try:
        metric = await analytics.record_usage_metric(
            feature=request.feature,
            action=request.action,
            user_id=current_user.id,
            resource=request.resource,
            duration_ms=request.duration_ms,
            bytes_processed=request.bytes_processed,
            tokens_used=request.tokens_used,
            success=request.success,
            error_code=request.error_code,
            error_message=request.error_message,
            metadata=request.metadata,
        )

        return MetricResponse(
            id=metric.id,
            timestamp=metric.timestamp,
            success=True,
            message="Usage metric recorded successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/cost", response_model=MetricResponse)
async def record_cost_metric(
    request: CostMetricRequest,
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """Record a cost metric"""
    try:
        metric = await analytics.record_cost_metric(
            service=request.service,
            operation=request.operation,
            total_cost=request.total_cost,
            user_id=current_user.id,
            model=request.model,
            input_tokens=request.input_tokens,
            output_tokens=request.output_tokens,
            currency=request.currency,
            is_billable=request.is_billable,
            metadata=request.metadata,
        )

        return MetricResponse(
            id=metric.id,
            timestamp=metric.timestamp,
            success=True,
            message="Cost metric recorded successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/performance", response_model=MetricResponse)
async def record_performance_metric(
    request: PerformanceMetricRequest,
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """Record a performance metric"""
    try:
        metric = await analytics.record_performance_metric(
            component=request.component,
            operation=request.operation,
            response_time_ms=request.response_time_ms,
            endpoint=request.endpoint,
            success=request.success,
            status_code=request.status_code,
            user_id=current_user.id,
            cpu_usage_percent=request.cpu_usage_percent,
            memory_usage_mb=request.memory_usage_mb,
            metadata=request.metadata,
        )

        return MetricResponse(
            id=metric.id,
            timestamp=metric.timestamp,
            success=True,
            message="Performance metric recorded successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/behavior", response_model=MetricResponse)
async def record_user_behavior(
    request: UserBehaviorRequest,
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """Record user behavior metric"""
    try:
        # Generate session ID if not provided
        import uuid

        session_id = str(uuid.uuid4())

        metric = await analytics.record_user_behavior(
            user_id=current_user.id,
            session_id=session_id,
            event_type=request.event_type,
            event_name=request.event_name,
            page_path=request.page_path,
            search_query=request.search_query,
            metadata=request.metadata,
            element_id=request.element_id,
            device_type=request.device_type,
        )

        return MetricResponse(
            id=metric.id,
            timestamp=metric.timestamp,
            success=True,
            message="User behavior recorded successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== DASHBOARD ENDPOINTS ====================


@router.post("/dashboard/usage", response_model=DashboardResponse)
async def get_usage_dashboard(
    request: DashboardRequest,
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """Get usage analytics dashboard"""
    try:
        start_date, end_date = parse_time_range(
            request.time_range, request.start_date, request.end_date
        )

        # Non-admin users can only see their own data
        user_id = request.user_id if current_user.is_admin else current_user.id

        dashboard_data = await analytics.get_usage_dashboard(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            aggregation=request.aggregation,
        )

        return DashboardResponse(
            period=dashboard_data["period"],
            data=dashboard_data,
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dashboard/cost", response_model=DashboardResponse)
async def get_cost_dashboard(
    request: DashboardRequest,
    current_user: User = Depends(require_admin),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """Get cost analytics dashboard (admin only)"""
    try:
        start_date, end_date = parse_time_range(
            request.time_range, request.start_date, request.end_date
        )

        dashboard_data = await analytics.get_cost_dashboard(
            start_date=start_date,
            end_date=end_date,
            organization_id=request.organization_id,
            aggregation=request.aggregation,
        )

        return DashboardResponse(
            period=dashboard_data["period"],
            data=dashboard_data,
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dashboard/performance", response_model=DashboardResponse)
async def get_performance_dashboard(
    request: DashboardRequest,
    current_user: User = Depends(require_admin),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """Get performance analytics dashboard (admin only)"""
    try:
        start_date, end_date = parse_time_range(
            request.time_range, request.start_date, request.end_date
        )

        dashboard_data = await analytics.get_performance_dashboard(
            start_date=start_date,
            end_date=end_date,
            component=request.component,
            aggregation=request.aggregation,
        )

        return DashboardResponse(
            period=dashboard_data["period"],
            data=dashboard_data,
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INSIGHTS ENDPOINTS ====================


@router.get("/insights/cost")
async def get_cost_insights(
    time_range: DashboardTimeRange = Query(DashboardTimeRange.LAST_30_DAYS),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    organization_id: Optional[int] = Query(None),
    current_user: User = Depends(require_admin),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """Get cost optimization insights (admin only)"""
    try:
        start_date, end_date = parse_time_range(time_range, start_date, end_date)

        insights = await analytics.insights_engine.get_cost_optimization_insights(
            start_date=start_date, end_date=end_date, organization_id=organization_id
        )

        return {
            "insights": insights,
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/performance")
async def get_performance_insights(
    time_range: DashboardTimeRange = Query(DashboardTimeRange.LAST_7_DAYS),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    component: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """Get performance optimization insights (admin only)"""
    try:
        start_date, end_date = parse_time_range(time_range, start_date, end_date)

        insights = await analytics.insights_engine.get_performance_insights(
            start_date=start_date, end_date=end_date, component=component
        )

        return {
            "insights": insights,
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== AGGREGATION ENDPOINTS ====================


@router.get("/aggregated/{metric_type}")
async def get_aggregated_metrics(
    metric_type: MetricType,
    time_range: DashboardTimeRange = Query(DashboardTimeRange.LAST_7_DAYS),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    aggregation: AggregationPeriod = Query(AggregationPeriod.DAILY),
    dimension: Optional[str] = Query(None),
    dimension_value: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """Get aggregated metrics data"""
    try:
        start_date, end_date = parse_time_range(time_range, start_date, end_date)

        # Restrict access for non-admin users
        if not current_user.is_admin and metric_type in [
            MetricType.COST,
            MetricType.PERFORMANCE,
        ]:
            raise HTTPException(
                status_code=403, detail="Admin access required for this metric type"
            )

        aggregated_data = await analytics.aggregator.get_aggregated_metrics(
            metric_type=metric_type,
            start_date=start_date,
            end_date=end_date,
            aggregation_period=aggregation,
            dimension=dimension,
            dimension_value=dimension_value,
        )

        return {
            "metric_type": metric_type,
            "aggregation_period": aggregation,
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "data": aggregated_data,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/time-series/{metric_type}/{metric_name}")
async def get_time_series_data(
    metric_type: MetricType,
    metric_name: str,
    time_range: DashboardTimeRange = Query(DashboardTimeRange.LAST_7_DAYS),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    aggregation: AggregationPeriod = Query(AggregationPeriod.DAILY),
    dimension: Optional[str] = Query(None),
    dimension_value: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """Get time series data for charts"""
    try:
        start_date, end_date = parse_time_range(time_range, start_date, end_date)

        # Restrict access for non-admin users
        if not current_user.is_admin and metric_type in [
            MetricType.COST,
            MetricType.PERFORMANCE,
        ]:
            raise HTTPException(
                status_code=403, detail="Admin access required for this metric type"
            )

        time_series_data = await analytics.aggregator.get_time_series_data(
            metric_type=metric_type,
            metric_name=metric_name,
            start_date=start_date,
            end_date=end_date,
            aggregation_period=aggregation,
            dimension=dimension,
            dimension_value=dimension_value,
        )

        return {
            "metric_type": metric_type,
            "metric_name": metric_name,
            "aggregation_period": aggregation,
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "data": time_series_data,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SYSTEM ENDPOINTS ====================


@router.get("/health")
async def analytics_health():
    """Analytics service health check"""
    return {
        "status": "healthy",
        "service": "analytics",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "metrics_collection",
            "dashboard_data",
            "insights_generation",
            "cost_tracking",
            "performance_monitoring",
            "user_behavior_analysis",
        ],
    }


@router.post("/aggregate/trigger")
async def trigger_aggregation(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """Manually trigger data aggregation (admin only)"""
    try:

        async def run_aggregation():
            """Background task to run aggregation"""
            now = datetime.utcnow()
            for metric_type in MetricType:
                await analytics.aggregator.update_aggregations(metric_type, now)

        background_tasks.add_task(run_aggregation)

        return {
            "status": "triggered",
            "message": "Data aggregation started in background",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
