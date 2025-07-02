"""
Insights Engine

Generates automated insights and recommendations based on analytics data.
Provides cost optimization, performance improvements, and usage pattern insights.
"""

import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from .models import (AggregatedMetric, AggregationPeriod, CostMetric,
                     InsightReport, MetricType, PerformanceMetric, UsageMetric,
                     UserBehaviorMetric)

logger = logging.getLogger(__name__)


@dataclass
class Insight:
    """Individual insight with scoring"""

    title: str
    description: str
    impact_score: float  # 0-100
    confidence_score: float  # 0-100
    category: str
    recommendation: Optional[str] = None
    affected_metrics: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class InsightsEngine:
    """
    Generates automated insights and recommendations
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    # ==================== COST OPTIMIZATION INSIGHTS ====================

    async def get_cost_optimization_insights(
        self,
        start_date: datetime,
        end_date: datetime,
        organization_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Generate cost optimization insights"""
        insights = []

        try:
            # High-cost services analysis
            high_cost_insights = await self._analyze_high_cost_services(
                start_date, end_date, organization_id
            )
            insights.extend(high_cost_insights)

            # Unused capacity analysis
            unused_capacity_insights = await self._analyze_unused_capacity(
                start_date, end_date, organization_id
            )
            insights.extend(unused_capacity_insights)

            # Token efficiency analysis
            token_efficiency_insights = await self._analyze_token_efficiency(
                start_date, end_date, organization_id
            )
            insights.extend(token_efficiency_insights)

            # Cost trend analysis
            cost_trend_insights = await self._analyze_cost_trends(
                start_date, end_date, organization_id
            )
            insights.extend(cost_trend_insights)

            return [insight.__dict__ for insight in insights]

        except Exception as e:
            logger.error(f"Failed to generate cost optimization insights: {e}")
            return []

    async def _analyze_high_cost_services(
        self, start_date: datetime, end_date: datetime, organization_id: Optional[int]
    ) -> List[Insight]:
        """Analyze services with disproportionately high costs"""
        insights = []

        try:
            # Get cost by service
            query = self.db.query(
                CostMetric.service,
                func.sum(CostMetric.total_cost).label("total_cost"),
                func.count(CostMetric.id).label("request_count"),
                func.avg(CostMetric.total_cost).label("avg_cost_per_request"),
            ).filter(
                and_(
                    CostMetric.timestamp >= start_date,
                    CostMetric.timestamp <= end_date,
                    CostMetric.is_billable == True,
                )
            )

            if organization_id:
                query = query.filter(CostMetric.organization_id == organization_id)

            results = (
                query.group_by(CostMetric.service).order_by(desc("total_cost")).all()
            )

            if not results:
                return insights

            total_cost = sum(result.total_cost for result in results)

            for result in results:
                cost_percentage = (result.total_cost / total_cost) * 100

                # Flag services consuming >40% of total cost
                if cost_percentage > 40:
                    insights.append(
                        Insight(
                            title=f"High Cost Service: {result.service}",
                            description=f"{result.service} accounts for {cost_percentage:.1f}% of total costs (${result.total_cost:.2f})",
                            impact_score=min(cost_percentage * 2, 100),
                            confidence_score=95,
                            category="cost_optimization",
                            recommendation=f"Review usage patterns for {result.service}. Consider optimizing requests or switching to more cost-effective models.",
                            affected_metrics=["total_cost", "cost_per_request"],
                            metadata={
                                "service": result.service,
                                "total_cost": float(result.total_cost),
                                "cost_percentage": cost_percentage,
                                "avg_cost_per_request": float(
                                    result.avg_cost_per_request
                                ),
                            },
                        )
                    )

                # Flag services with high cost per request
                if result.avg_cost_per_request > 0.5:  # $0.50 per request threshold
                    insights.append(
                        Insight(
                            title=f"High Per-Request Cost: {result.service}",
                            description=f"Average cost per request for {result.service} is ${result.avg_cost_per_request:.3f}",
                            impact_score=min(result.avg_cost_per_request * 100, 100),
                            confidence_score=85,
                            category="cost_optimization",
                            recommendation=f"Optimize request patterns or consider batch processing for {result.service}.",
                            metadata={
                                "service": result.service,
                                "avg_cost_per_request": float(
                                    result.avg_cost_per_request
                                ),
                                "request_count": result.request_count,
                            },
                        )
                    )

            return insights

        except Exception as e:
            logger.error(f"Failed to analyze high cost services: {e}")
            return []

    async def _analyze_unused_capacity(
        self, start_date: datetime, end_date: datetime, organization_id: Optional[int]
    ) -> List[Insight]:
        """Analyze unused or underutilized capacity"""
        insights = []

        try:
            # Analyze low-usage periods
            daily_usage = (
                self.db.query(
                    func.date(UsageMetric.timestamp).label("date"),
                    func.count(UsageMetric.id).label("daily_requests"),
                )
                .filter(
                    and_(
                        UsageMetric.timestamp >= start_date,
                        UsageMetric.timestamp <= end_date,
                    )
                )
                .group_by(func.date(UsageMetric.timestamp))
                .all()
            )

            if len(daily_usage) > 7:  # Need at least a week of data
                request_counts = [day.daily_requests for day in daily_usage]
                avg_daily_requests = statistics.mean(request_counts)
                std_daily_requests = (
                    statistics.stdev(request_counts) if len(request_counts) > 1 else 0
                )

                low_usage_days = [
                    day
                    for day in daily_usage
                    if day.daily_requests < (avg_daily_requests - std_daily_requests)
                ]

                if len(low_usage_days) > len(daily_usage) * 0.3:  # >30% low usage days
                    unused_percentage = (len(low_usage_days) / len(daily_usage)) * 100

                    insights.append(
                        Insight(
                            title="Significant Unused Capacity Detected",
                            description=f"{unused_percentage:.1f}% of days show below-average usage patterns",
                            impact_score=min(unused_percentage * 1.5, 100),
                            confidence_score=80,
                            category="cost_optimization",
                            recommendation="Consider implementing auto-scaling or usage-based pricing to optimize costs during low-usage periods.",
                            metadata={
                                "unused_percentage": unused_percentage,
                                "avg_daily_requests": avg_daily_requests,
                                "low_usage_days": len(low_usage_days),
                                "total_days": len(daily_usage),
                            },
                        )
                    )

            return insights

        except Exception as e:
            logger.error(f"Failed to analyze unused capacity: {e}")
            return []

    async def _analyze_token_efficiency(
        self, start_date: datetime, end_date: datetime, organization_id: Optional[int]
    ) -> List[Insight]:
        """Analyze token usage efficiency"""
        insights = []

        try:
            # Analyze token usage patterns
            token_analysis = (
                self.db.query(
                    CostMetric.service,
                    CostMetric.model,
                    func.avg(CostMetric.input_tokens).label("avg_input_tokens"),
                    func.avg(CostMetric.output_tokens).label("avg_output_tokens"),
                    func.avg(CostMetric.total_cost / CostMetric.total_tokens).label(
                        "cost_per_token"
                    ),
                )
                .filter(
                    and_(
                        CostMetric.timestamp >= start_date,
                        CostMetric.timestamp <= end_date,
                        CostMetric.total_tokens > 0,
                    )
                )
                .group_by(CostMetric.service, CostMetric.model)
                .all()
            )

            for result in token_analysis:
                # Flag high input-to-output ratios (inefficient prompts)
                if result.avg_input_tokens and result.avg_output_tokens:
                    input_output_ratio = (
                        result.avg_input_tokens / result.avg_output_tokens
                    )

                    if (
                        input_output_ratio > 5
                    ):  # >5:1 ratio suggests inefficient prompts
                        insights.append(
                            Insight(
                                title=f"Inefficient Token Usage: {result.service}",
                                description=f"High input-to-output token ratio ({input_output_ratio:.1f}:1) detected",
                                impact_score=min(input_output_ratio * 10, 100),
                                confidence_score=75,
                                category="cost_optimization",
                                recommendation="Optimize prompt engineering to reduce input tokens while maintaining output quality.",
                                metadata={
                                    "service": result.service,
                                    "model": result.model,
                                    "input_output_ratio": input_output_ratio,
                                    "avg_input_tokens": float(result.avg_input_tokens),
                                    "avg_output_tokens": float(
                                        result.avg_output_tokens
                                    ),
                                },
                            )
                        )

            return insights

        except Exception as e:
            logger.error(f"Failed to analyze token efficiency: {e}")
            return []

    async def _analyze_cost_trends(
        self, start_date: datetime, end_date: datetime, organization_id: Optional[int]
    ) -> List[Insight]:
        """Analyze cost trends and predict future costs"""
        insights = []

        try:
            # Get daily cost trends
            daily_costs = (
                self.db.query(
                    func.date(CostMetric.timestamp).label("date"),
                    func.sum(CostMetric.total_cost).label("daily_cost"),
                )
                .filter(
                    and_(
                        CostMetric.timestamp >= start_date,
                        CostMetric.timestamp <= end_date,
                        CostMetric.is_billable == True,
                    )
                )
                .group_by(func.date(CostMetric.timestamp))
                .order_by("date")
                .all()
            )

            if len(daily_costs) >= 7:  # Need at least a week of data
                costs = [float(day.daily_cost) for day in daily_costs]

                # Calculate trend
                if len(costs) > 1:
                    # Simple linear trend calculation
                    x_values = list(range(len(costs)))
                    slope = self._calculate_slope(x_values, costs)

                    # Significant upward trend
                    if slope > 0.1:  # $0.10 increase per day
                        monthly_increase = slope * 30
                        current_monthly = (
                            sum(costs[-7:]) * 30 / 7
                        )  # Estimate based on last week

                        insights.append(
                            Insight(
                                title="Rising Cost Trend Detected",
                                description=f"Costs are increasing by approximately ${slope:.2f} per day",
                                impact_score=min(
                                    monthly_increase / current_monthly * 100, 100
                                ),
                                confidence_score=70,
                                category="cost_optimization",
                                recommendation=f"Monitor usage patterns closely. Projected monthly increase: ${monthly_increase:.2f}",
                                metadata={
                                    "daily_increase": slope,
                                    "projected_monthly_increase": monthly_increase,
                                    "current_monthly_estimate": current_monthly,
                                },
                            )
                        )

            return insights

        except Exception as e:
            logger.error(f"Failed to analyze cost trends: {e}")
            return []

    # ==================== PERFORMANCE INSIGHTS ====================

    async def get_performance_insights(
        self, start_date: datetime, end_date: datetime, component: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate performance optimization insights"""
        insights = []

        try:
            # Slow endpoint analysis
            slow_endpoint_insights = await self._analyze_slow_endpoints(
                start_date, end_date, component
            )
            insights.extend(slow_endpoint_insights)

            # Error rate analysis
            error_rate_insights = await self._analyze_error_rates(
                start_date, end_date, component
            )
            insights.extend(error_rate_insights)

            # Resource usage analysis
            resource_insights = await self._analyze_resource_usage(
                start_date, end_date, component
            )
            insights.extend(resource_insights)

            return [insight.__dict__ for insight in insights]

        except Exception as e:
            logger.error(f"Failed to generate performance insights: {e}")
            return []

    async def _analyze_slow_endpoints(
        self, start_date: datetime, end_date: datetime, component: Optional[str]
    ) -> List[Insight]:
        """Analyze endpoints with poor performance"""
        insights = []

        try:
            query = self.db.query(
                PerformanceMetric.endpoint,
                func.avg(PerformanceMetric.response_time_ms).label("avg_response_time"),
                func.max(PerformanceMetric.response_time_ms).label("max_response_time"),
                func.count(PerformanceMetric.id).label("request_count"),
            ).filter(
                and_(
                    PerformanceMetric.timestamp >= start_date,
                    PerformanceMetric.timestamp <= end_date,
                    PerformanceMetric.endpoint.isnot(None),
                    PerformanceMetric.success == True,
                )
            )

            if component:
                query = query.filter(PerformanceMetric.component == component)

            results = (
                query.group_by(PerformanceMetric.endpoint)
                .having(func.count(PerformanceMetric.id) >= 10)
                .order_by(desc("avg_response_time"))
                .limit(10)
                .all()
            )

            # Calculate overall average for comparison
            overall_avg = (
                self.db.query(func.avg(PerformanceMetric.response_time_ms))
                .filter(
                    and_(
                        PerformanceMetric.timestamp >= start_date,
                        PerformanceMetric.timestamp <= end_date,
                        PerformanceMetric.success == True,
                    )
                )
                .scalar()
                or 0
            )

            for result in results:
                if result.avg_response_time > overall_avg * 2:  # 2x slower than average
                    slowness_factor = result.avg_response_time / overall_avg

                    insights.append(
                        Insight(
                            title=f"Slow Endpoint: {result.endpoint}",
                            description=f"Average response time of {result.avg_response_time:.0f}ms is {slowness_factor:.1f}x slower than average",
                            impact_score=min(slowness_factor * 20, 100),
                            confidence_score=85,
                            category="performance",
                            recommendation="Investigate database queries, optimize algorithms, or consider caching for this endpoint.",
                            metadata={
                                "endpoint": result.endpoint,
                                "avg_response_time_ms": float(result.avg_response_time),
                                "max_response_time_ms": float(result.max_response_time),
                                "request_count": result.request_count,
                                "slowness_factor": slowness_factor,
                            },
                        )
                    )

            return insights

        except Exception as e:
            logger.error(f"Failed to analyze slow endpoints: {e}")
            return []

    async def _analyze_error_rates(
        self, start_date: datetime, end_date: datetime, component: Optional[str]
    ) -> List[Insight]:
        """Analyze components with high error rates"""
        insights = []

        try:
            query = self.db.query(
                PerformanceMetric.component,
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

            results = (
                query.group_by(PerformanceMetric.component)
                .having(func.count(PerformanceMetric.id) >= 10)
                .all()
            )

            for result in results:
                error_rate = (result.error_count / result.total_requests) * 100

                if error_rate > 5:  # >5% error rate
                    insights.append(
                        Insight(
                            title=f"High Error Rate: {result.component}",
                            description=f"Error rate of {error_rate:.1f}% detected ({result.error_count}/{result.total_requests} requests)",
                            impact_score=min(error_rate * 5, 100),
                            confidence_score=90,
                            category="performance",
                            recommendation="Investigate error logs and implement better error handling or monitoring.",
                            metadata={
                                "component": result.component,
                                "error_rate_percent": error_rate,
                                "error_count": result.error_count,
                                "total_requests": result.total_requests,
                            },
                        )
                    )

            return insights

        except Exception as e:
            logger.error(f"Failed to analyze error rates: {e}")
            return []

    async def _analyze_resource_usage(
        self, start_date: datetime, end_date: datetime, component: Optional[str]
    ) -> List[Insight]:
        """Analyze resource usage patterns"""
        insights = []

        try:
            query = self.db.query(
                PerformanceMetric.component,
                func.avg(PerformanceMetric.cpu_usage_percent).label("avg_cpu"),
                func.max(PerformanceMetric.cpu_usage_percent).label("max_cpu"),
                func.avg(PerformanceMetric.memory_usage_mb).label("avg_memory"),
                func.max(PerformanceMetric.memory_usage_mb).label("max_memory"),
            ).filter(
                and_(
                    PerformanceMetric.timestamp >= start_date,
                    PerformanceMetric.timestamp <= end_date,
                    PerformanceMetric.cpu_usage_percent.isnot(None),
                )
            )

            if component:
                query = query.filter(PerformanceMetric.component == component)

            results = query.group_by(PerformanceMetric.component).all()

            for result in results:
                # High CPU usage
                if result.avg_cpu and result.avg_cpu > 80:
                    insights.append(
                        Insight(
                            title=f"High CPU Usage: {result.component}",
                            description=f"Average CPU usage of {result.avg_cpu:.1f}% (max: {result.max_cpu:.1f}%)",
                            impact_score=min(result.avg_cpu, 100),
                            confidence_score=85,
                            category="performance",
                            recommendation="Consider optimizing algorithms, adding more CPU resources, or implementing load balancing.",
                            metadata={
                                "component": result.component,
                                "avg_cpu_percent": float(result.avg_cpu),
                                "max_cpu_percent": float(result.max_cpu or 0),
                            },
                        )
                    )

                # High memory usage
                if result.avg_memory and result.avg_memory > 1000:  # >1GB average
                    insights.append(
                        Insight(
                            title=f"High Memory Usage: {result.component}",
                            description=f"Average memory usage of {result.avg_memory:.0f}MB (max: {result.max_memory:.0f}MB)",
                            impact_score=min(
                                result.avg_memory / 50, 100
                            ),  # Scale to 100
                            confidence_score=85,
                            category="performance",
                            recommendation="Investigate memory leaks, optimize data structures, or increase available memory.",
                            metadata={
                                "component": result.component,
                                "avg_memory_mb": float(result.avg_memory),
                                "max_memory_mb": float(result.max_memory or 0),
                            },
                        )
                    )

            return insights

        except Exception as e:
            logger.error(f"Failed to analyze resource usage: {e}")
            return []

    # ==================== HELPER METHODS ====================

    def _calculate_slope(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate linear regression slope"""
        try:
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x_squared = sum(x * x for x in x_values)

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x_squared - sum_x * sum_x)
            return slope

        except (ZeroDivisionError, ValueError):
            return 0.0
