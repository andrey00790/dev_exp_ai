"""
Data Aggregation Engine
Enhanced with standardized async patterns for enterprise reliability
Version: 2.1 Async Optimized

Handles efficient aggregation of metrics data for fast dashboard queries.
Implements time-based aggregation with multiple periods and dimensions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, select, text
from sqlalchemy.orm import Session

# Import standardized async patterns
from app.core.async_utils import (AsyncTimeouts, async_retry,
                                  create_background_task, safe_gather,
                                  with_timeout)
from app.core.exceptions import AsyncRetryError, AsyncTimeoutError

from .models import (AggregatedMetric, AggregationPeriod, CostMetric,
                     MetricType, PerformanceMetric, UsageMetric,
                     UserBehaviorMetric)

logger = logging.getLogger(__name__)


class DataAggregator:
    """
    Handles data aggregation for analytics dashboard
    Enhanced with standardized async patterns for enterprise reliability
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        # Removed manual ThreadPoolExecutor - using standardized async patterns
        self.aggregation_stats = {
            "total_aggregations": 0,
            "successful_aggregations": 0,
            "failed_aggregations": 0,
            "timeout_errors": 0,
            "avg_aggregation_time": 0.0,
        }

    # ==================== MAIN AGGREGATION METHODS ====================

    @async_retry(max_attempts=3, delay=2.0, exceptions=(Exception,))
    async def update_aggregations(self, metric_type: MetricType, timestamp: datetime):
        """
        Update aggregations for a new metric
        Enhanced with timeout protection and retry logic
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Update aggregations with timeout protection
            await with_timeout(
                self._update_aggregations_internal(metric_type, timestamp),
                AsyncTimeouts.ANALYTICS_AGGREGATION,  # 60 seconds for aggregation
                f"Aggregation update timed out for {metric_type.value}",
                {
                    "metric_type": metric_type.value,
                    "timestamp": timestamp.isoformat(),
                    "operation": "update_aggregations",
                },
            )

            # Update stats
            self.aggregation_stats["total_aggregations"] += 1
            self.aggregation_stats["successful_aggregations"] += 1

        except AsyncTimeoutError as e:
            self.aggregation_stats["timeout_errors"] += 1
            logger.error(f"❌ Aggregation timeout for {metric_type.value}: {e}")
            raise
        except Exception as e:
            self.aggregation_stats["failed_aggregations"] += 1
            logger.error(
                f"❌ Failed to update aggregations for {metric_type.value}: {e}"
            )
            raise
        finally:
            # Track aggregation performance
            duration = asyncio.get_event_loop().time() - start_time
            self._update_aggregation_stats(duration)

    async def _update_aggregations_internal(
        self, metric_type: MetricType, timestamp: datetime
    ):
        """Internal aggregation update with concurrent period processing"""
        # Determine which periods need updating
        periods_to_update = self._get_periods_for_timestamp(timestamp)

        # Update each period concurrently with controlled concurrency
        aggregation_tasks = [
            self._update_period_aggregation(metric_type, timestamp, period)
            for period in periods_to_update
        ]

        # Execute aggregations concurrently (max 3 to avoid DB overload)
        results = await safe_gather(
            *aggregation_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.ANALYTICS_AGGREGATION,
            max_concurrency=3,
        )

        # Check for any failures
        failed_periods = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_periods.append(periods_to_update[i])
                logger.warning(
                    f"⚠️ Failed to aggregate {periods_to_update[i]}: {result}"
                )

        if failed_periods:
            logger.warning(f"⚠️ Some aggregations failed: {failed_periods}")

    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def get_aggregated_metrics(
        self,
        metric_type: MetricType,
        start_date: datetime,
        end_date: datetime,
        aggregation_period: AggregationPeriod,
        dimension: Optional[str] = None,
        dimension_value: Optional[str] = None,
        metric_names: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated metrics for the specified parameters
        Enhanced with timeout protection and concurrent query optimization
        """
        try:
            # Calculate timeout based on date range complexity
            timeout = self._calculate_query_timeout(
                start_date, end_date, aggregation_period
            )

            return await with_timeout(
                self._get_aggregated_metrics_internal(
                    metric_type,
                    start_date,
                    end_date,
                    aggregation_period,
                    dimension,
                    dimension_value,
                    metric_names,
                ),
                timeout,
                f"Aggregated metrics query timed out (type: {metric_type.value}, period: {aggregation_period.value})",
                {
                    "metric_type": metric_type.value,
                    "aggregation_period": aggregation_period.value,
                    "date_range_days": (end_date - start_date).days,
                    "dimension": dimension,
                    "timeout_used": timeout,
                },
            )

        except AsyncTimeoutError as e:
            logger.error(f"❌ Aggregated metrics query timed out: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Failed to get aggregated metrics: {e}")
            return []

    async def _get_aggregated_metrics_internal(
        self,
        metric_type: MetricType,
        start_date: datetime,
        end_date: datetime,
        aggregation_period: AggregationPeriod,
        dimension: Optional[str],
        dimension_value: Optional[str],
        metric_names: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        """Internal aggregated metrics query"""
        query = self.db.query(AggregatedMetric).filter(
            and_(
                AggregatedMetric.metric_type == metric_type,
                AggregatedMetric.aggregation_period == aggregation_period,
                AggregatedMetric.period_start >= start_date,
                AggregatedMetric.period_start <= end_date,
            )
        )

        if dimension:
            query = query.filter(AggregatedMetric.dimension == dimension)

        if dimension_value:
            query = query.filter(AggregatedMetric.dimension_value == dimension_value)

        if metric_names:
            query = query.filter(AggregatedMetric.metric_name.in_(metric_names))

        results = query.order_by(AggregatedMetric.period_start).all()

        return [result.to_dict() for result in results]

    def _calculate_query_timeout(
        self,
        start_date: datetime,
        end_date: datetime,
        aggregation_period: AggregationPeriod,
    ) -> float:
        """Calculate dynamic timeout based on query complexity"""
        base_timeout = AsyncTimeouts.ANALYTICS_QUERY  # 30 seconds

        # Calculate date range complexity
        date_range_days = (end_date - start_date).days

        # Adjust timeout based on complexity
        multiplier = 1.0
        if date_range_days > 365:  # More than a year
            multiplier *= 3.0
        elif date_range_days > 90:  # More than 3 months
            multiplier *= 2.0
        elif date_range_days > 30:  # More than a month
            multiplier *= 1.5

        # Hourly aggregations are more complex
        if aggregation_period == AggregationPeriod.HOURLY:
            multiplier *= 1.5

        return min(base_timeout * multiplier, AsyncTimeouts.ANALYTICS_AGGREGATION)

    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def get_time_series_data(
        self,
        metric_type: MetricType,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        aggregation_period: AggregationPeriod,
        dimension: Optional[str] = None,
        dimension_value: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get time series data for charts
        Enhanced with timeout protection and concurrent optimization
        """
        try:
            timeout = self._calculate_query_timeout(
                start_date, end_date, aggregation_period
            )

            return await with_timeout(
                self._get_time_series_data_internal(
                    metric_type,
                    metric_name,
                    start_date,
                    end_date,
                    aggregation_period,
                    dimension,
                    dimension_value,
                ),
                timeout,
                f"Time series query timed out (metric: {metric_name}, period: {aggregation_period.value})",
                {
                    "metric_type": metric_type.value,
                    "metric_name": metric_name,
                    "aggregation_period": aggregation_period.value,
                    "timeout_used": timeout,
                },
            )

        except AsyncTimeoutError as e:
            logger.error(f"❌ Time series query timed out: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Failed to get time series data: {e}")
            return []

    async def _get_time_series_data_internal(
        self,
        metric_type: MetricType,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        aggregation_period: AggregationPeriod,
        dimension: Optional[str],
        dimension_value: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Internal time series data query"""
        query = self.db.query(
            AggregatedMetric.period_start,
            AggregatedMetric.sum_value,
            AggregatedMetric.avg_value,
            AggregatedMetric.count,
            AggregatedMetric.dimension_value,
        ).filter(
            and_(
                AggregatedMetric.metric_type == metric_type,
                AggregatedMetric.metric_name == metric_name,
                AggregatedMetric.aggregation_period == aggregation_period,
                AggregatedMetric.period_start >= start_date,
                AggregatedMetric.period_start <= end_date,
            )
        )

        if dimension:
            query = query.filter(AggregatedMetric.dimension == dimension)

        if dimension_value:
            query = query.filter(AggregatedMetric.dimension_value == dimension_value)

        results = query.order_by(AggregatedMetric.period_start).all()

        return [
            {
                "timestamp": result.period_start.isoformat(),
                "value": float(result.sum_value) if result.sum_value else 0,
                "average": float(result.avg_value) if result.avg_value else 0,
                "count": result.count or 0,
                "dimension_value": result.dimension_value,
            }
            for result in results
        ]

    # ==================== PERIOD AGGREGATION ====================

    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def _update_period_aggregation(
        self, metric_type: MetricType, timestamp: datetime, period: AggregationPeriod
    ):
        """
        Update aggregation for a specific period
        Enhanced with timeout protection and concurrent sub-aggregation
        """
        try:
            period_start, period_end = self._get_period_bounds(timestamp, period)

            # Execute period aggregation with timeout protection
            await with_timeout(
                self._execute_period_aggregation(
                    metric_type, period_start, period_end, period
                ),
                AsyncTimeouts.ANALYTICS_AGGREGATION / 2,  # 30 seconds for single period
                f"Period aggregation timed out ({metric_type.value}, {period.value})",
                {
                    "metric_type": metric_type.value,
                    "period": period.value,
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                },
            )

        except AsyncTimeoutError as e:
            logger.error(f"❌ Period aggregation timed out for {period.value}: {e}")
            raise
        except Exception as e:
            logger.error(
                f"❌ Failed to update {period.value} aggregation for {metric_type.value}: {e}"
            )
            raise

    async def _execute_period_aggregation(
        self,
        metric_type: MetricType,
        period_start: datetime,
        period_end: datetime,
        period: AggregationPeriod,
    ):
        """Execute the actual period aggregation based on metric type"""
        if metric_type == MetricType.USAGE:
            await self._aggregate_usage_metrics(period_start, period_end, period)
        elif metric_type == MetricType.COST:
            await self._aggregate_cost_metrics(period_start, period_end, period)
        elif metric_type == MetricType.PERFORMANCE:
            await self._aggregate_performance_metrics(period_start, period_end, period)
        elif metric_type == MetricType.BEHAVIOR:
            await self._aggregate_behavior_metrics(period_start, period_end, period)

    async def _aggregate_usage_metrics(
        self, period_start: datetime, period_end: datetime, period: AggregationPeriod
    ):
        """
        Aggregate usage metrics for the period
        Enhanced with concurrent sub-aggregations
        """
        try:
            # Execute feature and user aggregations concurrently
            aggregation_tasks = [
                self._aggregate_usage_by_feature(period_start, period_end, period),
                self._aggregate_usage_by_user(period_start, period_end, period),
            ]

            await safe_gather(
                *aggregation_tasks,
                return_exceptions=True,
                timeout=AsyncTimeouts.ANALYTICS_QUERY,
                max_concurrency=2,
            )

        except Exception as e:
            logger.error(f"❌ Failed to aggregate usage metrics: {e}")
            raise

    async def _aggregate_usage_by_feature(
        self, period_start: datetime, period_end: datetime, period: AggregationPeriod
    ):
        """Aggregate usage metrics by feature"""
        feature_query = (
            self.db.query(
                UsageMetric.feature,
                func.count(UsageMetric.id).label("count"),
                func.sum(UsageMetric.tokens_used).label("total_tokens"),
                func.avg(UsageMetric.duration_ms).label("avg_duration"),
                func.max(UsageMetric.duration_ms).label("max_duration"),
                func.sum(UsageMetric.bytes_processed).label("total_bytes"),
            )
            .filter(
                and_(
                    UsageMetric.timestamp >= period_start,
                    UsageMetric.timestamp < period_end,
                )
            )
            .group_by(UsageMetric.feature)
        )

        for result in feature_query.all():
            await self._upsert_aggregated_metric(
                metric_type=MetricType.USAGE,
                metric_name="usage_count",
                period_start=period_start,
                period_end=period_end,
                aggregation_period=period,
                dimension="feature",
                dimension_value=result.feature,
                count=result.count,
                sum_value=float(result.total_tokens or 0),
                avg_value=float(result.avg_duration or 0),
                max_value=float(result.max_duration or 0),
                metadata={"total_bytes": result.total_bytes or 0},
            )

    async def _aggregate_usage_by_user(
        self, period_start: datetime, period_end: datetime, period: AggregationPeriod
    ):
        """Aggregate usage metrics by user"""
        user_query = (
            self.db.query(
                UsageMetric.user_id,
                func.count(UsageMetric.id).label("count"),
                func.sum(UsageMetric.tokens_used).label("total_tokens"),
                func.count(func.distinct(UsageMetric.session_id)).label(
                    "session_count"
                ),
            )
            .filter(
                and_(
                    UsageMetric.timestamp >= period_start,
                    UsageMetric.timestamp < period_end,
                    UsageMetric.user_id.isnot(None),
                )
            )
            .group_by(UsageMetric.user_id)
        )

        for result in user_query.all():
            await self._upsert_aggregated_metric(
                metric_type=MetricType.USAGE,
                metric_name="user_activity",
                period_start=period_start,
                period_end=period_end,
                aggregation_period=period,
                dimension="user_id",
                dimension_value=str(result.user_id),
                count=result.count,
                sum_value=float(result.total_tokens or 0),
                metadata={"session_count": result.session_count or 0},
            )

    async def _aggregate_cost_metrics(
        self, period_start: datetime, period_end: datetime, period: AggregationPeriod
    ):
        """
        Aggregate cost metrics for the period
        Enhanced with concurrent sub-aggregations
        """
        try:
            # Execute service and organization aggregations concurrently
            aggregation_tasks = [
                self._aggregate_cost_by_service(period_start, period_end, period),
                self._aggregate_cost_by_organization(period_start, period_end, period),
            ]

            await safe_gather(
                *aggregation_tasks,
                return_exceptions=True,
                timeout=AsyncTimeouts.ANALYTICS_QUERY,
                max_concurrency=2,
            )

        except Exception as e:
            logger.error(f"❌ Failed to aggregate cost metrics: {e}")
            raise

    async def _aggregate_cost_by_service(
        self, period_start: datetime, period_end: datetime, period: AggregationPeriod
    ):
        """Aggregate cost metrics by service"""
        service_query = (
            self.db.query(
                CostMetric.service,
                func.count(CostMetric.id).label("count"),
                func.sum(CostMetric.total_cost).label("total_cost"),
                func.avg(CostMetric.total_cost).label("avg_cost"),
                func.max(CostMetric.total_cost).label("max_cost"),
                func.sum(CostMetric.total_tokens).label("total_tokens"),
            )
            .filter(
                and_(
                    CostMetric.timestamp >= period_start,
                    CostMetric.timestamp < period_end,
                    CostMetric.is_billable == True,
                )
            )
            .group_by(CostMetric.service)
        )

        for result in service_query.all():
            await self._upsert_aggregated_metric(
                metric_type=MetricType.COST,
                metric_name="total_cost",
                period_start=period_start,
                period_end=period_end,
                aggregation_period=period,
                dimension="service",
                dimension_value=result.service,
                count=result.count,
                sum_value=float(result.total_cost),
                avg_value=float(result.avg_cost),
                max_value=float(result.max_cost),
                metadata={"total_tokens": result.total_tokens or 0},
            )

    async def _aggregate_cost_by_organization(
        self, period_start: datetime, period_end: datetime, period: AggregationPeriod
    ):
        """Aggregate cost metrics by organization"""
        org_query = (
            self.db.query(
                CostMetric.organization_id,
                func.count(CostMetric.id).label("count"),
                func.sum(CostMetric.total_cost).label("total_cost"),
                func.avg(CostMetric.total_cost).label("avg_cost"),
            )
            .filter(
                and_(
                    CostMetric.timestamp >= period_start,
                    CostMetric.timestamp < period_end,
                    CostMetric.is_billable == True,
                    CostMetric.organization_id.isnot(None),
                )
            )
            .group_by(CostMetric.organization_id)
        )

        for result in org_query.all():
            await self._upsert_aggregated_metric(
                metric_type=MetricType.COST,
                metric_name="organization_cost",
                period_start=period_start,
                period_end=period_end,
                aggregation_period=period,
                dimension="organization_id",
                dimension_value=str(result.organization_id),
                count=result.count,
                sum_value=float(result.total_cost),
                avg_value=float(result.avg_cost),
            )

    async def _aggregate_performance_metrics(
        self, period_start: datetime, period_end: datetime, period: AggregationPeriod
    ):
        """
        Aggregate performance metrics for the period
        Enhanced with concurrent sub-aggregations
        """
        try:
            # Execute component and endpoint aggregations concurrently
            aggregation_tasks = [
                self._aggregate_performance_by_component(
                    period_start, period_end, period
                ),
                self._aggregate_performance_by_endpoint(
                    period_start, period_end, period
                ),
            ]

            await safe_gather(
                *aggregation_tasks,
                return_exceptions=True,
                timeout=AsyncTimeouts.ANALYTICS_QUERY,
                max_concurrency=2,
            )

        except Exception as e:
            logger.error(f"❌ Failed to aggregate performance metrics: {e}")
            raise

    async def _aggregate_performance_by_component(
        self, period_start: datetime, period_end: datetime, period: AggregationPeriod
    ):
        """Aggregate performance metrics by component"""
        component_query = (
            self.db.query(
                PerformanceMetric.component,
                func.count(PerformanceMetric.id).label("count"),
                func.avg(PerformanceMetric.response_time_ms).label("avg_response_time"),
                func.percentile_cont(0.5)
                .within_group(PerformanceMetric.response_time_ms)
                .label("p50_response_time"),
                func.percentile_cont(0.95)
                .within_group(PerformanceMetric.response_time_ms)
                .label("p95_response_time"),
                func.max(PerformanceMetric.response_time_ms).label("max_response_time"),
                func.avg(PerformanceMetric.cpu_usage_percent).label("avg_cpu"),
                func.avg(PerformanceMetric.memory_usage_mb).label("avg_memory"),
                func.sum(
                    func.case([(PerformanceMetric.success == False, 1)], else_=0)
                ).label("error_count"),
            )
            .filter(
                and_(
                    PerformanceMetric.timestamp >= period_start,
                    PerformanceMetric.timestamp < period_end,
                )
            )
            .group_by(PerformanceMetric.component)
        )

        for result in component_query.all():
            error_rate = (
                (result.error_count / result.count * 100) if result.count > 0 else 0
            )

            await self._upsert_aggregated_metric(
                metric_type=MetricType.PERFORMANCE,
                metric_name="response_time_ms",
                period_start=period_start,
                period_end=period_end,
                aggregation_period=period,
                dimension="component",
                dimension_value=result.component,
                count=result.count,
                avg_value=float(result.avg_response_time),
                p50_value=(
                    float(result.p50_response_time)
                    if result.p50_response_time
                    else None
                ),
                p95_value=(
                    float(result.p95_response_time)
                    if result.p95_response_time
                    else None
                ),
                max_value=float(result.max_response_time),
                metadata={
                    "avg_cpu_percent": (
                        float(result.avg_cpu) if result.avg_cpu else None
                    ),
                    "avg_memory_mb": (
                        float(result.avg_memory) if result.avg_memory else None
                    ),
                    "error_count": result.error_count,
                    "error_rate_percent": round(error_rate, 2),
                },
            )

    async def _aggregate_performance_by_endpoint(
        self, period_start: datetime, period_end: datetime, period: AggregationPeriod
    ):
        """Aggregate performance metrics by endpoint"""
        endpoint_query = (
            self.db.query(
                PerformanceMetric.endpoint,
                func.count(PerformanceMetric.id).label("count"),
                func.avg(PerformanceMetric.response_time_ms).label("avg_response_time"),
                func.max(PerformanceMetric.response_time_ms).label("max_response_time"),
            )
            .filter(
                and_(
                    PerformanceMetric.timestamp >= period_start,
                    PerformanceMetric.timestamp < period_end,
                    PerformanceMetric.endpoint.isnot(None),
                )
            )
            .group_by(PerformanceMetric.endpoint)
        )

        for result in endpoint_query.all():
            await self._upsert_aggregated_metric(
                metric_type=MetricType.PERFORMANCE,
                metric_name="endpoint_performance",
                period_start=period_start,
                period_end=period_end,
                aggregation_period=period,
                dimension="endpoint",
                dimension_value=result.endpoint,
                count=result.count,
                avg_value=float(result.avg_response_time),
                max_value=float(result.max_response_time),
            )

    async def _aggregate_behavior_metrics(
        self, period_start: datetime, period_end: datetime, period: AggregationPeriod
    ):
        """
        Aggregate user behavior metrics for the period
        Enhanced with concurrent sub-aggregations
        """
        try:
            # Execute event and page aggregations concurrently
            aggregation_tasks = [
                self._aggregate_behavior_by_event(period_start, period_end, period),
                self._aggregate_behavior_by_page(period_start, period_end, period),
            ]

            await safe_gather(
                *aggregation_tasks,
                return_exceptions=True,
                timeout=AsyncTimeouts.ANALYTICS_QUERY,
                max_concurrency=2,
            )

        except Exception as e:
            logger.error(f"❌ Failed to aggregate behavior metrics: {e}")
            raise

    async def _aggregate_behavior_by_event(
        self, period_start: datetime, period_end: datetime, period: AggregationPeriod
    ):
        """Aggregate behavior metrics by event type"""
        event_query = (
            self.db.query(
                UserBehaviorMetric.event_type,
                func.count(UserBehaviorMetric.id).label("count"),
                func.count(func.distinct(UserBehaviorMetric.user_id)).label(
                    "unique_users"
                ),
                func.count(func.distinct(UserBehaviorMetric.session_id)).label(
                    "unique_sessions"
                ),
                func.avg(UserBehaviorMetric.page_view_duration_ms).label(
                    "avg_duration"
                ),
            )
            .filter(
                and_(
                    UserBehaviorMetric.timestamp >= period_start,
                    UserBehaviorMetric.timestamp < period_end,
                )
            )
            .group_by(UserBehaviorMetric.event_type)
        )

        for result in event_query.all():
            await self._upsert_aggregated_metric(
                metric_type=MetricType.BEHAVIOR,
                metric_name="event_count",
                period_start=period_start,
                period_end=period_end,
                aggregation_period=period,
                dimension="event_type",
                dimension_value=result.event_type,
                count=result.count,
                avg_value=float(result.avg_duration) if result.avg_duration else None,
                metadata={
                    "unique_users": result.unique_users,
                    "unique_sessions": result.unique_sessions,
                },
            )

    async def _aggregate_behavior_by_page(
        self, period_start: datetime, period_end: datetime, period: AggregationPeriod
    ):
        """Aggregate behavior metrics by page path"""
        page_query = (
            self.db.query(
                UserBehaviorMetric.page_path,
                func.count(UserBehaviorMetric.id).label("count"),
                func.count(func.distinct(UserBehaviorMetric.user_id)).label(
                    "unique_users"
                ),
                func.avg(UserBehaviorMetric.page_view_duration_ms).label(
                    "avg_duration"
                ),
            )
            .filter(
                and_(
                    UserBehaviorMetric.timestamp >= period_start,
                    UserBehaviorMetric.timestamp < period_end,
                    UserBehaviorMetric.page_path.isnot(None),
                )
            )
            .group_by(UserBehaviorMetric.page_path)
        )

        for result in page_query.all():
            await self._upsert_aggregated_metric(
                metric_type=MetricType.BEHAVIOR,
                metric_name="page_views",
                period_start=period_start,
                period_end=period_end,
                aggregation_period=period,
                dimension="page_path",
                dimension_value=result.page_path,
                count=result.count,
                avg_value=float(result.avg_duration) if result.avg_duration else None,
                metadata={"unique_users": result.unique_users},
            )

    # ==================== HELPER METHODS ====================

    @async_retry(max_attempts=2, delay=0.5, exceptions=(Exception,))
    async def _upsert_aggregated_metric(
        self,
        metric_type: MetricType,
        metric_name: str,
        period_start: datetime,
        period_end: datetime,
        aggregation_period: AggregationPeriod,
        dimension: Optional[str] = None,
        dimension_value: Optional[str] = None,
        count: Optional[int] = None,
        sum_value: Optional[float] = None,
        avg_value: Optional[float] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        p50_value: Optional[float] = None,
        p95_value: Optional[float] = None,
        p99_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Insert or update aggregated metric
        Enhanced with timeout protection and retry logic
        """
        try:
            # Upsert operation with timeout protection
            await with_timeout(
                self._execute_upsert(
                    metric_type,
                    metric_name,
                    period_start,
                    period_end,
                    aggregation_period,
                    dimension,
                    dimension_value,
                    count,
                    sum_value,
                    avg_value,
                    min_value,
                    max_value,
                    p50_value,
                    p95_value,
                    p99_value,
                    metadata,
                ),
                AsyncTimeouts.DATABASE_QUERY,  # 10 seconds for upsert
                f"Upsert timeout for metric {metric_name}",
                {
                    "metric_type": metric_type.value,
                    "metric_name": metric_name,
                    "aggregation_period": aggregation_period.value,
                },
            )

        except AsyncTimeoutError as e:
            logger.error(f"❌ Upsert timeout for {metric_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to upsert aggregated metric {metric_name}: {e}")
            raise

    async def _execute_upsert(
        self,
        metric_type: MetricType,
        metric_name: str,
        period_start: datetime,
        period_end: datetime,
        aggregation_period: AggregationPeriod,
        dimension: Optional[str],
        dimension_value: Optional[str],
        count: Optional[int],
        sum_value: Optional[float],
        avg_value: Optional[float],
        min_value: Optional[float],
        max_value: Optional[float],
        p50_value: Optional[float],
        p95_value: Optional[float],
        p99_value: Optional[float],
        metadata: Optional[Dict[str, Any]],
    ):
        """Execute the actual upsert operation"""
        # Check if record exists
        existing = (
            self.db.query(AggregatedMetric)
            .filter(
                and_(
                    AggregatedMetric.period_start == period_start,
                    AggregatedMetric.aggregation_period == aggregation_period,
                    AggregatedMetric.metric_type == metric_type,
                    AggregatedMetric.metric_name == metric_name,
                    AggregatedMetric.dimension == dimension,
                    AggregatedMetric.dimension_value == dimension_value,
                )
            )
            .first()
        )

        if existing:
            # Update existing record
            existing.period_end = period_end
            existing.count = count
            existing.sum_value = sum_value
            existing.avg_value = avg_value
            existing.min_value = min_value
            existing.max_value = max_value
            existing.p50_value = p50_value
            existing.p95_value = p95_value
            existing.p99_value = p99_value
            existing.metadata = metadata
        else:
            # Create new record
            new_metric = AggregatedMetric(
                period_start=period_start,
                period_end=period_end,
                aggregation_period=aggregation_period,
                metric_type=metric_type,
                metric_name=metric_name,
                dimension=dimension,
                dimension_value=dimension_value,
                count=count,
                sum_value=sum_value,
                avg_value=avg_value,
                min_value=min_value,
                max_value=max_value,
                p50_value=p50_value,
                p95_value=p95_value,
                p99_value=p99_value,
                metadata=metadata,
            )
            self.db.add(new_metric)

        self.db.commit()

    def _update_aggregation_stats(self, duration: float):
        """Update aggregation performance statistics"""
        total = self.aggregation_stats["total_aggregations"]
        if total > 0:
            current_avg = self.aggregation_stats["avg_aggregation_time"]
            self.aggregation_stats["avg_aggregation_time"] = (
                current_avg * (total - 1) + duration
            ) / total

    async def get_aggregation_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive aggregation statistics
        Enhanced with performance metrics
        """
        stats = self.aggregation_stats.copy()

        # Calculate success rate
        total = stats["total_aggregations"]
        if total > 0:
            stats["success_rate"] = (stats["successful_aggregations"] / total) * 100
            stats["failure_rate"] = (stats["failed_aggregations"] / total) * 100
            stats["timeout_rate"] = (stats["timeout_errors"] / total) * 100
        else:
            stats["success_rate"] = 0.0
            stats["failure_rate"] = 0.0
            stats["timeout_rate"] = 0.0

        stats["async_patterns_enabled"] = True
        return stats

    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive aggregation health check
        Enhanced with timeout protection
        """
        health = {
            "status": "unknown",
            "aggregation_engine": {"status": "unknown"},
            "database_connectivity": {"status": "unknown"},
            "performance_metrics": {},
            "errors": [],
        }

        try:
            # Test database connectivity with timeout
            db_test = await with_timeout(
                self._test_database_connectivity(),
                AsyncTimeouts.DATABASE_QUERY,
                "Database connectivity test timed out",
                {"test": "aggregation_health_check"},
            )
            health["database_connectivity"] = db_test

            # Test aggregation engine
            engine_test = await self._test_aggregation_engine()
            health["aggregation_engine"] = engine_test

            # Get performance metrics
            health["performance_metrics"] = await self.get_aggregation_stats()

            # Overall health determination
            all_healthy = (
                db_test.get("status") == "healthy"
                and engine_test.get("status") == "healthy"
            )
            health["status"] = "healthy" if all_healthy else "degraded"

        except AsyncTimeoutError as e:
            health["status"] = "timeout"
            health["errors"].append(f"Health check timed out: {str(e)}")
        except Exception as e:
            health["status"] = "unhealthy"
            health["errors"].append(f"Health check failed: {str(e)}")

        return health

    async def _test_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity for aggregation"""
        try:
            # Simple query to test connectivity
            result = self.db.query(AggregatedMetric).limit(1).first()
            return {
                "status": "healthy",
                "connectivity": True,
                "test_query_success": True,
            }
        except Exception as e:
            return {"status": "unhealthy", "connectivity": False, "error": str(e)}

    async def _test_aggregation_engine(self) -> Dict[str, Any]:
        """Test aggregation engine functionality"""
        try:
            stats = await self.get_aggregation_stats()
            return {
                "status": "healthy",
                "total_aggregations": stats["total_aggregations"],
                "success_rate": stats["success_rate"],
                "avg_processing_time": stats["avg_aggregation_time"],
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def _get_periods_for_timestamp(
        self, timestamp: datetime
    ) -> List[AggregationPeriod]:
        """Determine which aggregation periods need updating for a timestamp"""
        return [
            AggregationPeriod.HOURLY,
            AggregationPeriod.DAILY,
            AggregationPeriod.WEEKLY,
            AggregationPeriod.MONTHLY,
        ]

    def _get_period_bounds(
        self, timestamp: datetime, period: AggregationPeriod
    ) -> Tuple[datetime, datetime]:
        """Get start and end bounds for an aggregation period"""
        if period == AggregationPeriod.HOURLY:
            period_start = timestamp.replace(minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(hours=1)
        elif period == AggregationPeriod.DAILY:
            period_start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
        elif period == AggregationPeriod.WEEKLY:
            days_since_monday = timestamp.weekday()
            period_start = timestamp.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(days=days_since_monday)
            period_end = period_start + timedelta(weeks=1)
        elif period == AggregationPeriod.MONTHLY:
            period_start = timestamp.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)
        else:
            # Default to daily
            period_start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)

        return period_start, period_end
