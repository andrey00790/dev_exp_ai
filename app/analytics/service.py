"""
Analytics Service
Enhanced with standardized async patterns for enterprise reliability
Version: 2.1 Async Optimized

Provides comprehensive analytics capabilities including:
- Metrics collection and storage with timeout protection
- Real-time analytics processing with concurrent operations
- Dashboard data preparation with retry logic
- Insights generation with enhanced error handling
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session

# Import standardized async patterns
from app.core.async_utils import (AsyncTimeouts, async_retry,
                                  create_background_task, safe_gather,
                                  with_timeout)
from app.core.exceptions import AsyncRetryError, AsyncTimeoutError

from .aggregator import DataAggregator
from .insights import InsightsEngine
from .models import (AggregatedMetric, AggregationPeriod, CostMetric,
                     InsightReport, MetricType, PerformanceMetric, UsageMetric,
                     UserBehaviorMetric)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Main analytics service that coordinates all analytics operations
    Enhanced with standardized async patterns for enterprise reliability
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.aggregator = DataAggregator(db_session)
        self.insights_engine = InsightsEngine(db_session)
        # Removed manual ThreadPoolExecutor - using standardized async patterns
        self.service_stats = {
            "metrics_recorded": 0,
            "dashboards_generated": 0,
            "errors": 0,
            "timeout_errors": 0,
            "avg_response_time": 0.0,
        }

    # ==================== METRICS COLLECTION ====================

    @async_retry(max_attempts=2, delay=0.5, exceptions=(Exception,))
    async def record_usage_metric(
        self,
        feature: str,
        action: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        resource: Optional[str] = None,
        duration_ms: Optional[float] = None,
        bytes_processed: Optional[int] = None,
        tokens_used: Optional[int] = None,
        success: bool = True,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> UsageMetric:
        """
        Record a usage metric
        Enhanced with timeout protection and retry logic
        """
        try:
            # Record metric with timeout protection
            metric = await with_timeout(
                self._record_usage_metric_internal(
                    feature,
                    action,
                    user_id,
                    session_id,
                    resource,
                    duration_ms,
                    bytes_processed,
                    tokens_used,
                    success,
                    error_code,
                    error_message,
                    metadata,
                    **kwargs,
                ),
                AsyncTimeouts.DATABASE_TRANSACTION,  # 30 seconds for metric recording
                f"Usage metric recording timed out (feature: {feature}, action: {action})",
                {
                    "feature": feature,
                    "action": action,
                    "user_id": user_id,
                    "operation": "record_usage_metric",
                },
            )

            # Update service stats
            self.service_stats["metrics_recorded"] += 1

            # Trigger background aggregation (don't wait for it)
            create_background_task(
                self._update_aggregations(MetricType.USAGE, metric.timestamp),
                f"usage_aggregation_{metric.id}",
            )

            logger.info(
                f"✅ Usage metric recorded: {feature}/{action} for user {user_id}"
            )
            return metric

        except AsyncTimeoutError as e:
            self.service_stats["timeout_errors"] += 1
            logger.error(f"❌ Usage metric recording timed out: {e}")
            raise HTTPException(
                status_code=408, detail=f"Usage metric recording timed out: {str(e)}"
            )
        except Exception as e:
            self.service_stats["errors"] += 1
            self.db.rollback()
            logger.error(f"❌ Failed to record usage metric: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to record usage metric: {e}"
            )

    async def _record_usage_metric_internal(
        self,
        feature: str,
        action: str,
        user_id: Optional[int],
        session_id: Optional[str],
        resource: Optional[str],
        duration_ms: Optional[float],
        bytes_processed: Optional[int],
        tokens_used: Optional[int],
        success: bool,
        error_code: Optional[str],
        error_message: Optional[str],
        metadata: Optional[Dict[str, Any]],
        **kwargs,
    ) -> UsageMetric:
        """Internal usage metric recording"""
        metric = UsageMetric(
            user_id=user_id,
            session_id=session_id,
            feature=feature,
            action=action,
            resource=resource,
            duration_ms=duration_ms,
            bytes_processed=bytes_processed,
            tokens_used=tokens_used,
            success=success,
            error_code=error_code,
            error_message=error_message,
            metadata=metadata,
            user_agent=kwargs.get("user_agent"),
            ip_address=kwargs.get("ip_address"),
            api_version=kwargs.get("api_version"),
        )

        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    @async_retry(max_attempts=2, delay=0.5, exceptions=(Exception,))
    async def record_cost_metric(
        self,
        service: str,
        operation: str,
        total_cost: float,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        model: Optional[str] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        currency: str = "USD",
        is_billable: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> CostMetric:
        """
        Record a cost metric
        Enhanced with timeout protection and retry logic
        """
        try:
            # Record cost metric with timeout protection
            metric = await with_timeout(
                self._record_cost_metric_internal(
                    service,
                    operation,
                    total_cost,
                    user_id,
                    organization_id,
                    model,
                    input_tokens,
                    output_tokens,
                    currency,
                    is_billable,
                    metadata,
                    **kwargs,
                ),
                AsyncTimeouts.DATABASE_TRANSACTION,
                f"Cost metric recording timed out (service: {service}, operation: {operation})",
                {
                    "service": service,
                    "operation": operation,
                    "total_cost": total_cost,
                    "operation_type": "record_cost_metric",
                },
            )

            # Update service stats
            self.service_stats["metrics_recorded"] += 1

            # Trigger background aggregation
            create_background_task(
                self._update_aggregations(MetricType.COST, metric.timestamp),
                f"cost_aggregation_{metric.id}",
            )

            logger.info(
                f"✅ Cost metric recorded: {service}/{operation} = ${total_cost}"
            )
            return metric

        except AsyncTimeoutError as e:
            self.service_stats["timeout_errors"] += 1
            logger.error(f"❌ Cost metric recording timed out: {e}")
            raise HTTPException(
                status_code=408, detail=f"Cost metric recording timed out: {str(e)}"
            )
        except Exception as e:
            self.service_stats["errors"] += 1
            self.db.rollback()
            logger.error(f"❌ Failed to record cost metric: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to record cost metric: {e}"
            )

    async def _record_cost_metric_internal(
        self,
        service: str,
        operation: str,
        total_cost: float,
        user_id: Optional[int],
        organization_id: Optional[int],
        model: Optional[str],
        input_tokens: Optional[int],
        output_tokens: Optional[int],
        currency: str,
        is_billable: bool,
        metadata: Optional[Dict[str, Any]],
        **kwargs,
    ) -> CostMetric:
        """Internal cost metric recording"""
        metric = CostMetric(
            user_id=user_id,
            organization_id=organization_id,
            service=service,
            operation=operation,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=(
                (input_tokens or 0) + (output_tokens or 0)
                if input_tokens or output_tokens
                else None
            ),
            total_cost=total_cost,
            currency=currency,
            is_billable=is_billable,
            metadata=metadata,
            request_id=kwargs.get("request_id"),
            feature_context=kwargs.get("feature_context"),
            budget_category=kwargs.get("budget_category"),
        )

        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    async def record_performance_metric(
        self,
        component: str,
        operation: str,
        response_time_ms: float,
        endpoint: Optional[str] = None,
        success: bool = True,
        status_code: Optional[int] = None,
        user_id: Optional[int] = None,
        cpu_usage_percent: Optional[float] = None,
        memory_usage_mb: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> PerformanceMetric:
        """Record a performance metric"""
        try:
            metric = PerformanceMetric(
                component=component,
                endpoint=endpoint,
                operation=operation,
                response_time_ms=response_time_ms,
                cpu_usage_percent=cpu_usage_percent,
                memory_usage_mb=memory_usage_mb,
                status_code=status_code,
                success=success,
                user_id=user_id,
                metadata=metadata,
                disk_io_mb=kwargs.get("disk_io_mb"),
                network_io_mb=kwargs.get("network_io_mb"),
                request_size_bytes=kwargs.get("request_size_bytes"),
                response_size_bytes=kwargs.get("response_size_bytes"),
                concurrent_requests=kwargs.get("concurrent_requests"),
                session_id=kwargs.get("session_id"),
                trace_id=kwargs.get("trace_id"),
                error_type=kwargs.get("error_type"),
            )

            self.db.add(metric)
            self.db.commit()
            self.db.refresh(metric)

            # Trigger async aggregation
            asyncio.create_task(
                self._update_aggregations(MetricType.PERFORMANCE, metric.timestamp)
            )

            logger.debug(
                f"Performance metric recorded: {component}/{operation} = {response_time_ms}ms"
            )
            return metric

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to record performance metric: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to record performance metric: {e}"
            )

    async def record_user_behavior(
        self,
        user_id: int,
        session_id: str,
        event_type: str,
        event_name: str,
        page_path: Optional[str] = None,
        search_query: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> UserBehaviorMetric:
        """Record user behavior metric"""
        try:
            metric = UserBehaviorMetric(
                user_id=user_id,
                session_id=session_id,
                event_type=event_type,
                event_name=event_name,
                page_path=page_path,
                search_query=search_query,
                metadata=metadata,
                element_id=kwargs.get("element_id"),
                element_text=kwargs.get("element_text"),
                click_coordinates=kwargs.get("click_coordinates"),
                session_duration_ms=kwargs.get("session_duration_ms"),
                page_view_duration_ms=kwargs.get("page_view_duration_ms"),
                referrer=kwargs.get("referrer"),
                user_agent=kwargs.get("user_agent"),
                screen_resolution=kwargs.get("screen_resolution"),
                browser=kwargs.get("browser"),
                device_type=kwargs.get("device_type"),
                search_results_count=kwargs.get("search_results_count"),
                selected_result_position=kwargs.get("selected_result_position"),
                conversion_event=kwargs.get("conversion_event"),
                conversion_value=kwargs.get("conversion_value"),
                experiment_id=kwargs.get("experiment_id"),
                variant=kwargs.get("variant"),
            )

            self.db.add(metric)
            self.db.commit()
            self.db.refresh(metric)

            # Trigger async aggregation
            asyncio.create_task(
                self._update_aggregations(MetricType.BEHAVIOR, metric.timestamp)
            )

            logger.debug(
                f"User behavior recorded: {event_type}/{event_name} for user {user_id}"
            )
            return metric

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to record user behavior: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to record user behavior: {e}"
            )

    # ==================== DASHBOARD DATA ====================

    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def get_usage_dashboard(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int] = None,
        aggregation: AggregationPeriod = AggregationPeriod.DAILY,
    ) -> Dict[str, Any]:
        """
        Get usage analytics dashboard data
        Enhanced with concurrent data collection and timeout protection
        """
        try:
            # Calculate timeout based on date range complexity
            timeout = self._calculate_dashboard_timeout(start_date, end_date)

            return await with_timeout(
                self._get_usage_dashboard_internal(
                    start_date, end_date, user_id, aggregation
                ),
                timeout,
                f"Usage dashboard generation timed out (range: {(end_date - start_date).days} days)",
                {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "user_id": user_id,
                    "aggregation": aggregation.value,
                    "timeout_used": timeout,
                },
            )

        except AsyncTimeoutError as e:
            self.service_stats["timeout_errors"] += 1
            logger.error(f"❌ Usage dashboard generation timed out: {e}")
            raise HTTPException(
                status_code=408,
                detail=f"Usage dashboard generation timed out: {str(e)}",
            )
        except Exception as e:
            self.service_stats["errors"] += 1
            logger.error(f"❌ Failed to get usage dashboard: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get usage dashboard: {e}"
            )

    async def _get_usage_dashboard_internal(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int],
        aggregation: AggregationPeriod,
    ) -> Dict[str, Any]:
        """Internal usage dashboard generation with concurrent data collection"""
        # Collect all dashboard data concurrently
        dashboard_tasks = [
            self.aggregator.get_aggregated_metrics(
                metric_type=MetricType.USAGE,
                start_date=start_date,
                end_date=end_date,
                aggregation_period=aggregation,
                dimension="feature" if not user_id else "user_id",
                dimension_value=str(user_id) if user_id else None,
            ),
            self._get_top_features(start_date, end_date, user_id),
            self._get_usage_trends(start_date, end_date, user_id, aggregation),
            self._get_error_analytics(start_date, end_date, user_id),
        ]

        # Execute all tasks concurrently (max 4 concurrent operations)
        usage_data, top_features, usage_trends, error_analytics = await safe_gather(
            *dashboard_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.ANALYTICS_QUERY,
            max_concurrency=4,
        )

        # Handle any exceptions gracefully
        if isinstance(usage_data, Exception):
            logger.warning(f"⚠️ Usage data collection failed: {usage_data}")
            usage_data = []
        if isinstance(top_features, Exception):
            logger.warning(f"⚠️ Top features collection failed: {top_features}")
            top_features = []
        if isinstance(usage_trends, Exception):
            logger.warning(f"⚠️ Usage trends collection failed: {usage_trends}")
            usage_trends = []
        if isinstance(error_analytics, Exception):
            logger.warning(f"⚠️ Error analytics collection failed: {error_analytics}")
            error_analytics = {
                "error_rate_percent": 0,
                "total_errors": 0,
                "error_breakdown": [],
            }

        # Update service stats
        self.service_stats["dashboards_generated"] += 1

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "aggregation": aggregation.value,
            },
            "usage_data": usage_data,
            "top_features": top_features,
            "usage_trends": usage_trends,
            "error_analytics": error_analytics,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "async_optimized": True,
        }

    def _calculate_dashboard_timeout(
        self, start_date: datetime, end_date: datetime
    ) -> float:
        """Calculate dynamic timeout for dashboard generation based on date range"""
        base_timeout = AsyncTimeouts.ANALYTICS_QUERY  # 30 seconds
        date_range_days = (end_date - start_date).days

        # Adjust timeout based on date range complexity
        if date_range_days > 365:  # More than a year
            multiplier = 3.0
        elif date_range_days > 90:  # More than 3 months
            multiplier = 2.0
        elif date_range_days > 30:  # More than a month
            multiplier = 1.5
        else:
            multiplier = 1.0

        return min(base_timeout * multiplier, AsyncTimeouts.ANALYTICS_AGGREGATION)

    async def get_cost_dashboard(
        self,
        start_date: datetime,
        end_date: datetime,
        organization_id: Optional[int] = None,
        aggregation: AggregationPeriod = AggregationPeriod.DAILY,
    ) -> Dict[str, Any]:
        """Get cost analytics dashboard data"""
        try:
            # Get aggregated cost metrics
            cost_data = await self.aggregator.get_aggregated_metrics(
                metric_type=MetricType.COST,
                start_date=start_date,
                end_date=end_date,
                aggregation_period=aggregation,
                dimension="service",
            )

            # Get cost breakdown by service
            cost_by_service = await self._get_cost_by_service(
                start_date, end_date, organization_id
            )

            # Get cost trends
            cost_trends = await self._get_cost_trends(
                start_date, end_date, organization_id, aggregation
            )

            # Get cost optimization opportunities
            optimization_opportunities = (
                await self.insights_engine.get_cost_optimization_insights(
                    start_date, end_date, organization_id
                )
            )

            # Calculate total costs
            total_cost = await self._calculate_total_cost(
                start_date, end_date, organization_id
            )

            return {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "aggregation": aggregation,
                },
                "total_cost": total_cost,
                "cost_data": cost_data,
                "cost_by_service": cost_by_service,
                "cost_trends": cost_trends,
                "optimization_opportunities": optimization_opportunities,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get cost dashboard: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get cost dashboard: {e}"
            )

    async def get_performance_dashboard(
        self,
        start_date: datetime,
        end_date: datetime,
        component: Optional[str] = None,
        aggregation: AggregationPeriod = AggregationPeriod.HOURLY,
    ) -> Dict[str, Any]:
        """Get performance analytics dashboard data"""
        try:
            # Get aggregated performance metrics
            performance_data = await self.aggregator.get_aggregated_metrics(
                metric_type=MetricType.PERFORMANCE,
                start_date=start_date,
                end_date=end_date,
                aggregation_period=aggregation,
                dimension="component" if not component else "endpoint",
                dimension_value=component,
            )

            # Get response time trends
            response_time_trends = await self._get_response_time_trends(
                start_date, end_date, component, aggregation
            )

            # Get slowest endpoints
            slowest_endpoints = await self._get_slowest_endpoints(
                start_date, end_date, component
            )

            # Get error rates
            error_rates = await self._get_error_rates(start_date, end_date, component)

            # Get performance insights
            performance_insights = await self.insights_engine.get_performance_insights(
                start_date, end_date, component
            )

            return {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "aggregation": aggregation,
                },
                "performance_data": performance_data,
                "response_time_trends": response_time_trends,
                "slowest_endpoints": slowest_endpoints,
                "error_rates": error_rates,
                "performance_insights": performance_insights,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get performance dashboard: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get performance dashboard: {e}"
            )

    # ==================== HELPER METHODS ====================

    async def _update_aggregations(self, metric_type: MetricType, timestamp: datetime):
        """
        Update aggregations for new metrics
        Enhanced with timeout protection
        """
        try:
            await with_timeout(
                self.aggregator.update_aggregations(metric_type, timestamp),
                AsyncTimeouts.ANALYTICS_AGGREGATION,
                f"Aggregation update timed out for {metric_type.value}",
                {"metric_type": metric_type.value, "timestamp": timestamp.isoformat()},
            )
        except AsyncTimeoutError as e:
            logger.warning(f"⚠️ Aggregation update timed out: {e}")
        except Exception as e:
            logger.error(f"❌ Failed to update aggregations: {e}")

    async def get_service_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive analytics service statistics
        Enhanced with performance metrics
        """
        try:
            # Get stats from sub-components concurrently
            stats_tasks = [
                self.aggregator.get_aggregation_stats(),
                (
                    self.insights_engine.get_insights_stats()
                    if hasattr(self.insights_engine, "get_insights_stats")
                    else self._get_default_insights_stats()
                ),
            ]

            aggregator_stats, insights_stats = await safe_gather(
                *stats_tasks,
                return_exceptions=True,
                timeout=AsyncTimeouts.ANALYTICS_QUERY / 2,  # 15 seconds for stats
                max_concurrency=2,
            )

            # Handle exceptions gracefully
            if isinstance(aggregator_stats, Exception):
                aggregator_stats = {"error": str(aggregator_stats)}
            if isinstance(insights_stats, Exception):
                insights_stats = {"error": str(insights_stats)}

            service_stats = self.service_stats.copy()

            # Calculate success rate
            total_operations = (
                service_stats["metrics_recorded"]
                + service_stats["dashboards_generated"]
                + service_stats["errors"]
            )

            if total_operations > 0:
                service_stats["success_rate"] = (
                    (
                        service_stats["metrics_recorded"]
                        + service_stats["dashboards_generated"]
                    )
                    / total_operations
                    * 100
                )
                service_stats["error_rate"] = (
                    service_stats["errors"] / total_operations * 100
                )
                service_stats["timeout_rate"] = (
                    service_stats["timeout_errors"] / total_operations * 100
                )
            else:
                service_stats["success_rate"] = 0.0
                service_stats["error_rate"] = 0.0
                service_stats["timeout_rate"] = 0.0

            return {
                "service_stats": service_stats,
                "aggregator_stats": aggregator_stats,
                "insights_stats": insights_stats,
                "async_patterns_enabled": True,
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Error collecting service stats: {e}")
            return {"error": str(e)}

    async def _get_default_insights_stats(self) -> Dict[str, Any]:
        """Default insights stats if insights engine doesn't have stats method"""
        return {
            "insights_generated": 0,
            "cost_insights": 0,
            "performance_insights": 0,
            "status": "available",
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive analytics service health check
        Enhanced with component testing and timeout protection
        """
        health = {
            "status": "unknown",
            "service_layer": {"status": "unknown"},
            "aggregator": {"status": "unknown"},
            "insights_engine": {"status": "unknown"},
            "database": {"status": "unknown"},
            "performance_metrics": {},
            "errors": [],
        }

        try:
            # Test all components concurrently
            health_tasks = [
                self._test_service_layer(),
                self.aggregator.health_check(),
                self._test_insights_engine(),
                self._test_database_connectivity(),
            ]

            service_test, aggregator_test, insights_test, db_test = await safe_gather(
                *health_tasks,
                return_exceptions=True,
                timeout=AsyncTimeouts.ANALYTICS_QUERY,
                max_concurrency=4,
            )

            # Process results
            health["service_layer"] = (
                service_test
                if not isinstance(service_test, Exception)
                else {"status": "failed", "error": str(service_test)}
            )
            health["aggregator"] = (
                aggregator_test
                if not isinstance(aggregator_test, Exception)
                else {"status": "failed", "error": str(aggregator_test)}
            )
            health["insights_engine"] = (
                insights_test
                if not isinstance(insights_test, Exception)
                else {"status": "failed", "error": str(insights_test)}
            )
            health["database"] = (
                db_test
                if not isinstance(db_test, Exception)
                else {"status": "failed", "error": str(db_test)}
            )

            # Get performance metrics
            health["performance_metrics"] = await self.get_service_stats()

            # Determine overall health
            all_healthy = all(
                component.get("status") == "healthy"
                for component in [
                    health["service_layer"],
                    health["aggregator"],
                    health["insights_engine"],
                    health["database"],
                ]
                if isinstance(component, dict)
            )

            health["status"] = "healthy" if all_healthy else "degraded"

        except Exception as e:
            health["status"] = "unhealthy"
            health["errors"].append(f"Health check failed: {str(e)}")

        return health

    async def _test_service_layer(self) -> Dict[str, Any]:
        """Test analytics service layer functionality"""
        try:
            stats = await self.get_service_stats()
            return {
                "status": "healthy",
                "metrics_recorded": stats["service_stats"]["metrics_recorded"],
                "dashboards_generated": stats["service_stats"]["dashboards_generated"],
                "async_patterns": True,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def _test_insights_engine(self) -> Dict[str, Any]:
        """Test insights engine functionality"""
        try:
            # Simple test - try to access insights engine
            if hasattr(self.insights_engine, "health_check"):
                return await self.insights_engine.health_check()
            else:
                return {
                    "status": "healthy",
                    "engine_available": True,
                    "test": "basic_access",
                }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def _test_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity for analytics"""
        try:
            # Simple query to test connectivity
            result = self.db.query(UsageMetric).limit(1).first()
            return {
                "status": "healthy",
                "connectivity": True,
                "test_query_success": True,
            }
        except Exception as e:
            return {"status": "unhealthy", "connectivity": False, "error": str(e)}

    async def _get_top_features(
        self, start_date: datetime, end_date: datetime, user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get top used features"""
        query = self.db.query(
            UsageMetric.feature,
            func.count(UsageMetric.id).label("usage_count"),
            func.sum(UsageMetric.tokens_used).label("total_tokens"),
            func.avg(UsageMetric.duration_ms).label("avg_duration"),
        ).filter(
            and_(
                UsageMetric.timestamp >= start_date,
                UsageMetric.timestamp <= end_date,
                UsageMetric.success == True,
            )
        )

        if user_id:
            query = query.filter(UsageMetric.user_id == user_id)

        results = (
            query.group_by(UsageMetric.feature)
            .order_by(desc("usage_count"))
            .limit(10)
            .all()
        )

        return [
            {
                "feature": result.feature,
                "usage_count": result.usage_count,
                "total_tokens": result.total_tokens or 0,
                "avg_duration_ms": (
                    float(result.avg_duration) if result.avg_duration else 0
                ),
            }
            for result in results
        ]

    async def _get_usage_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int],
        aggregation: AggregationPeriod,
    ) -> List[Dict[str, Any]]:
        """Get usage trends over time"""
        # This would use aggregated data for efficiency
        return await self.aggregator.get_time_series_data(
            metric_type=MetricType.USAGE,
            metric_name="usage_count",
            start_date=start_date,
            end_date=end_date,
            aggregation_period=aggregation,
            dimension="user_id" if user_id else None,
            dimension_value=str(user_id) if user_id else None,
        )

    async def _get_error_analytics(
        self, start_date: datetime, end_date: datetime, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get error analytics"""
        query = self.db.query(
            UsageMetric.error_code, func.count(UsageMetric.id).label("error_count")
        ).filter(
            and_(
                UsageMetric.timestamp >= start_date,
                UsageMetric.timestamp <= end_date,
                UsageMetric.success == False,
                UsageMetric.error_code.isnot(None),
            )
        )

        if user_id:
            query = query.filter(UsageMetric.user_id == user_id)

        error_counts = (
            query.group_by(UsageMetric.error_code)
            .order_by(desc("error_count"))
            .limit(10)
            .all()
        )

        total_requests = (
            self.db.query(func.count(UsageMetric.id))
            .filter(
                and_(
                    UsageMetric.timestamp >= start_date,
                    UsageMetric.timestamp <= end_date,
                    UsageMetric.user_id == user_id if user_id else True,
                )
            )
            .scalar()
        )

        total_errors = sum(error.error_count for error in error_counts)
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

        return {
            "error_rate_percent": round(error_rate, 2),
            "total_errors": total_errors,
            "total_requests": total_requests,
            "top_errors": [
                {
                    "error_code": error.error_code,
                    "count": error.error_count,
                    "percentage": (
                        round(error.error_count / total_errors * 100, 2)
                        if total_errors > 0
                        else 0
                    ),
                }
                for error in error_counts
            ],
        }

    async def _get_cost_by_service(
        self,
        start_date: datetime,
        end_date: datetime,
        organization_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get cost breakdown by service"""
        query = self.db.query(
            CostMetric.service,
            func.sum(CostMetric.total_cost).label("total_cost"),
            func.count(CostMetric.id).label("request_count"),
            func.sum(CostMetric.total_tokens).label("total_tokens"),
        ).filter(
            and_(
                CostMetric.timestamp >= start_date,
                CostMetric.timestamp <= end_date,
                CostMetric.is_billable == True,
            )
        )

        if organization_id:
            query = query.filter(CostMetric.organization_id == organization_id)

        results = query.group_by(CostMetric.service).order_by(desc("total_cost")).all()

        return [
            {
                "service": result.service,
                "total_cost": float(result.total_cost),
                "request_count": result.request_count,
                "total_tokens": result.total_tokens or 0,
            }
            for result in results
        ]

    async def _get_cost_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        organization_id: Optional[int],
        aggregation: AggregationPeriod,
    ) -> List[Dict[str, Any]]:
        """Get cost trends over time"""
        return await self.aggregator.get_time_series_data(
            metric_type=MetricType.COST,
            metric_name="total_cost",
            start_date=start_date,
            end_date=end_date,
            aggregation_period=aggregation,
            dimension="organization_id" if organization_id else None,
            dimension_value=str(organization_id) if organization_id else None,
        )

    async def _calculate_total_cost(
        self,
        start_date: datetime,
        end_date: datetime,
        organization_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Calculate total costs for the period"""
        query = self.db.query(
            func.sum(CostMetric.total_cost).label("total"),
            func.avg(CostMetric.total_cost).label("average"),
            func.count(CostMetric.id).label("transactions"),
        ).filter(
            and_(
                CostMetric.timestamp >= start_date,
                CostMetric.timestamp <= end_date,
                CostMetric.is_billable == True,
            )
        )

        if organization_id:
            query = query.filter(CostMetric.organization_id == organization_id)

        result = query.first()

        return {
            "total_cost": float(result.total) if result.total else 0.0,
            "average_per_transaction": float(result.average) if result.average else 0.0,
            "total_transactions": result.transactions or 0,
        }

    async def _get_response_time_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        component: Optional[str],
        aggregation: AggregationPeriod,
    ) -> List[Dict[str, Any]]:
        """Get response time trends"""
        return await self.aggregator.get_time_series_data(
            metric_type=MetricType.PERFORMANCE,
            metric_name="response_time_ms",
            start_date=start_date,
            end_date=end_date,
            aggregation_period=aggregation,
            dimension="component" if component else None,
            dimension_value=component,
        )

    async def _get_slowest_endpoints(
        self, start_date: datetime, end_date: datetime, component: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get slowest endpoints"""
        query = self.db.query(
            PerformanceMetric.endpoint,
            func.avg(PerformanceMetric.response_time_ms).label("avg_response_time"),
            func.max(PerformanceMetric.response_time_ms).label("max_response_time"),
            func.count(PerformanceMetric.id).label("request_count"),
        ).filter(
            and_(
                PerformanceMetric.timestamp >= start_date,
                PerformanceMetric.timestamp <= end_date,
                PerformanceMetric.success == True,
                PerformanceMetric.endpoint.isnot(None),
            )
        )

        if component:
            query = query.filter(PerformanceMetric.component == component)

        results = (
            query.group_by(PerformanceMetric.endpoint)
            .order_by(desc("avg_response_time"))
            .limit(10)
            .all()
        )

        return [
            {
                "endpoint": result.endpoint,
                "avg_response_time_ms": float(result.avg_response_time),
                "max_response_time_ms": float(result.max_response_time),
                "request_count": result.request_count,
            }
            for result in results
        ]

    async def _get_error_rates(
        self, start_date: datetime, end_date: datetime, component: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get error rates for performance metrics"""
        query = self.db.query(
            func.count(PerformanceMetric.id).label("total_requests"),
            func.sum(
                func.case([(PerformanceMetric.success == False, 1)], else_=0)
            ).label("error_count"),
        ).filter(
            and_(
                PerformanceMetric.timestamp >= start_date,
                PerformanceMetric.timestamp <= end_date,
            )
        )

        if component:
            query = query.filter(PerformanceMetric.component == component)

        result = query.first()

        total_requests = result.total_requests or 0
        error_count = result.error_count or 0
        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0

        return {
            "error_rate_percent": round(error_rate, 2),
            "total_errors": error_count,
            "total_requests": total_requests,
        }
