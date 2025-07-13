"""
Enhanced Business Metrics System for AI Assistant MVP
Version: 8.0 Enterprise

Comprehensive business intelligence and KPI tracking system
that provides real-time insights into user engagement, feature adoption,
cost optimization, and revenue metrics.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import pandas as pd
from sqlalchemy import and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_async_session
from app.models.user import User
from app.models.analytics import AnalyticsEvent, BusinessMetric, KPITarget
from app.core.async_utils import async_retry, with_timeout

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of business metrics"""
    USER_ENGAGEMENT = "user_engagement"
    FEATURE_ADOPTION = "feature_adoption"
    REVENUE = "revenue"
    COST_OPTIMIZATION = "cost_optimization"
    PERFORMANCE = "performance"
    SATISFACTION = "satisfaction"
    PRODUCTIVITY = "productivity"


@dataclass
class BusinessKPI:
    """Business KPI definition"""
    name: str
    current_value: float
    target_value: float
    unit: str
    trend: str  # "up", "down", "stable"
    change_percent: float
    category: MetricType
    description: str
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserEngagementMetrics:
    """User engagement metrics"""
    daily_active_users: int
    monthly_active_users: int
    weekly_active_users: int
    session_duration_avg: float
    sessions_per_user: float
    retention_rate_7d: float
    retention_rate_30d: float
    bounce_rate: float
    feature_engagement_rate: Dict[str, float]
    time_to_first_value: float  # seconds


@dataclass
class FeatureAdoptionMetrics:
    """Feature adoption and usage metrics"""
    feature_usage_rates: Dict[str, float]
    feature_abandonment_rates: Dict[str, float]
    new_feature_adoption_speed: Dict[str, float]
    feature_stickiness: Dict[str, float]  # DAU/MAU ratio per feature
    power_user_features: List[str]
    underutilized_features: List[str]
    feature_conversion_rates: Dict[str, float]


@dataclass
class RevenueMetrics:
    """Revenue and cost metrics"""
    revenue_per_user: float
    cost_per_user: float
    profit_margin: float
    cost_optimization_savings: float
    ai_operation_costs: float
    infrastructure_costs: float
    roi_per_feature: Dict[str, float]
    cost_efficiency_trend: float


@dataclass
class ProductivityMetrics:
    """User productivity gains"""
    time_saved_per_user: float  # minutes per day
    documents_generated_rate: float
    search_success_rate: float
    rfc_completion_rate: float
    code_review_efficiency: float
    task_completion_speed: float
    productivity_score: float  # 0-100


class EnhancedBusinessMetricsCollector:
    """Enhanced business metrics collection and analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    @async_retry(max_attempts=3, delay=1.0)
    async def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive business metrics"""
        try:
            start_time = datetime.now(timezone.utc)
            
            # Collect metrics in parallel for better performance
            user_engagement, feature_adoption, revenue, productivity = await asyncio.gather(
                self.collect_user_engagement_metrics(),
                self.collect_feature_adoption_metrics(),
                self.collect_revenue_metrics(),
                self.collect_productivity_metrics(),
                return_exceptions=True
            )
            
            # Handle any exceptions
            if isinstance(user_engagement, Exception):
                self.logger.error(f"Error collecting user engagement metrics: {user_engagement}")
                user_engagement = UserEngagementMetrics(0, 0, 0, 0, 0, 0, 0, 0, {}, 0)
                
            if isinstance(feature_adoption, Exception):
                self.logger.error(f"Error collecting feature adoption metrics: {feature_adoption}")
                feature_adoption = FeatureAdoptionMetrics({}, {}, {}, {}, [], [], {})
                
            if isinstance(revenue, Exception):
                self.logger.error(f"Error collecting revenue metrics: {revenue}")
                revenue = RevenueMetrics(0, 0, 0, 0, 0, 0, {}, 0)
                
            if isinstance(productivity, Exception):
                self.logger.error(f"Error collecting productivity metrics: {productivity}")
                productivity = ProductivityMetrics(0, 0, 0, 0, 0, 0, 0)
            
            # Calculate derived KPIs
            kpis = await self.calculate_business_kpis(
                user_engagement, feature_adoption, revenue, productivity
            )
            
            collection_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            result = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "collection_time_seconds": collection_time,
                "user_engagement": user_engagement,
                "feature_adoption": feature_adoption,
                "revenue_metrics": revenue,
                "productivity_metrics": productivity,
                "business_kpis": kpis,
                "overall_health_score": await self.calculate_overall_health_score(kpis),
                "recommendations": await self.generate_recommendations(kpis)
            }
            
            # Cache the results
            self.metrics_cache = {
                "data": result,
                "timestamp": datetime.now(timezone.utc)
            }
            
            self.logger.info(f"✅ Business metrics collected successfully in {collection_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error collecting business metrics: {e}")
            raise

    async def collect_user_engagement_metrics(self) -> UserEngagementMetrics:
        """Collect detailed user engagement metrics"""
        async with get_async_session() as session:
            try:
                now = datetime.now(timezone.utc)
                
                # Calculate time periods
                day_ago = now - timedelta(days=1)
                week_ago = now - timedelta(days=7)
                month_ago = now - timedelta(days=30)
                
                # Daily Active Users
                dau_query = await session.execute(
                    text("""
                        SELECT COUNT(DISTINCT user_id) 
                        FROM analytics_events 
                        WHERE timestamp >= :day_ago
                    """),
                    {"day_ago": day_ago}
                )
                daily_active_users = dau_query.scalar() or 0
                
                # Weekly Active Users
                wau_query = await session.execute(
                    text("""
                        SELECT COUNT(DISTINCT user_id) 
                        FROM analytics_events 
                        WHERE timestamp >= :week_ago
                    """),
                    {"week_ago": week_ago}
                )
                weekly_active_users = wau_query.scalar() or 0
                
                # Monthly Active Users
                mau_query = await session.execute(
                    text("""
                        SELECT COUNT(DISTINCT user_id) 
                        FROM analytics_events 
                        WHERE timestamp >= :month_ago
                    """),
                    {"month_ago": month_ago}
                )
                monthly_active_users = mau_query.scalar() or 0
                
                # Session metrics
                session_metrics = await session.execute(
                    text("""
                        SELECT 
                            AVG(session_duration) as avg_duration,
                            AVG(sessions_per_day) as sessions_per_user
                        FROM (
                            SELECT 
                                user_id,
                                DATE(timestamp) as date,
                                COUNT(*) as sessions_per_day,
                                AVG(EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (PARTITION BY user_id ORDER BY timestamp)))) as session_duration
                            FROM analytics_events 
                            WHERE timestamp >= :week_ago
                            GROUP BY user_id, DATE(timestamp)
                        ) sessions
                    """),
                    {"week_ago": week_ago}
                )
                session_data = session_metrics.fetchone()
                session_duration_avg = float(session_data[0] or 0)
                sessions_per_user = float(session_data[1] or 0)
                
                # Retention rates
                retention_7d = await self.calculate_retention_rate(session, 7)
                retention_30d = await self.calculate_retention_rate(session, 30)
                
                # Bounce rate (sessions with only 1 event)
                bounce_rate_query = await session.execute(
                    text("""
                        SELECT 
                            CAST(SUM(CASE WHEN event_count = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100
                        FROM (
                            SELECT user_id, COUNT(*) as event_count
                            FROM analytics_events 
                            WHERE timestamp >= :day_ago
                            GROUP BY user_id
                        ) user_sessions
                    """),
                    {"day_ago": day_ago}
                )
                bounce_rate = float(bounce_rate_query.scalar() or 0)
                
                # Feature engagement rates
                feature_engagement = await self.calculate_feature_engagement_rates(session)
                
                # Time to first value
                ttfv_query = await session.execute(
                    text("""
                        SELECT AVG(
                            EXTRACT(EPOCH FROM (first_value_event.timestamp - user_creation.timestamp))
                        )
                        FROM users user_creation
                        JOIN (
                            SELECT user_id, MIN(timestamp) as timestamp
                            FROM analytics_events 
                            WHERE event_type IN ('search_success', 'rfc_generated', 'document_created')
                            GROUP BY user_id
                        ) first_value_event ON user_creation.user_id = first_value_event.user_id
                        WHERE user_creation.created_at >= :month_ago
                    """),
                    {"month_ago": month_ago}
                )
                time_to_first_value = float(ttfv_query.scalar() or 0)
                
                return UserEngagementMetrics(
                    daily_active_users=daily_active_users,
                    monthly_active_users=monthly_active_users,
                    weekly_active_users=weekly_active_users,
                    session_duration_avg=session_duration_avg,
                    sessions_per_user=sessions_per_user,
                    retention_rate_7d=retention_7d,
                    retention_rate_30d=retention_30d,
                    bounce_rate=bounce_rate,
                    feature_engagement_rate=feature_engagement,
                    time_to_first_value=time_to_first_value
                )
                
            except Exception as e:
                self.logger.error(f"Error collecting user engagement metrics: {e}")
                raise

    async def collect_feature_adoption_metrics(self) -> FeatureAdoptionMetrics:
        """Collect feature adoption and usage patterns"""
        async with get_async_session() as session:
            try:
                # Feature usage rates (last 30 days)
                usage_query = await session.execute(
                    text("""
                        SELECT 
                            feature_name,
                            COUNT(DISTINCT user_id)::FLOAT / (SELECT COUNT(DISTINCT user_id) FROM analytics_events WHERE timestamp >= NOW() - INTERVAL '30 days') * 100 as usage_rate
                        FROM analytics_events 
                        WHERE timestamp >= NOW() - INTERVAL '30 days'
                        AND feature_name IS NOT NULL
                        GROUP BY feature_name
                    """)
                )
                feature_usage_rates = {row[0]: float(row[1]) for row in usage_query.fetchall()}
                
                # Feature abandonment rates
                abandonment_query = await session.execute(
                    text("""
                        SELECT 
                            feature_name,
                            COUNT(*)::FLOAT / SUM(COUNT(*)) OVER () * 100 as abandonment_rate
                        FROM analytics_events 
                        WHERE event_type = 'feature_abandoned'
                        AND timestamp >= NOW() - INTERVAL '30 days'
                        GROUP BY feature_name
                    """)
                )
                feature_abandonment_rates = {row[0]: float(row[1]) for row in abandonment_query.fetchall()}
                
                # Feature stickiness (DAU/MAU ratio per feature)
                stickiness_query = await session.execute(
                    text("""
                        SELECT 
                            feature_name,
                            dau.daily_users::FLOAT / mau.monthly_users * 100 as stickiness
                        FROM (
                            SELECT 
                                feature_name,
                                COUNT(DISTINCT user_id) as daily_users
                            FROM analytics_events 
                            WHERE timestamp >= NOW() - INTERVAL '1 day'
                            GROUP BY feature_name
                        ) dau
                        JOIN (
                            SELECT 
                                feature_name,
                                COUNT(DISTINCT user_id) as monthly_users
                            FROM analytics_events 
                            WHERE timestamp >= NOW() - INTERVAL '30 days'
                            GROUP BY feature_name
                        ) mau ON dau.feature_name = mau.feature_name
                    """)
                )
                feature_stickiness = {row[0]: float(row[1]) for row in stickiness_query.fetchall()}
                
                # Identify power user features (top 20% usage)
                sorted_features = sorted(feature_usage_rates.items(), key=lambda x: x[1], reverse=True)
                power_user_features = [f[0] for f in sorted_features[:int(len(sorted_features) * 0.2)]]
                
                # Identify underutilized features (bottom 20% usage)
                underutilized_features = [f[0] for f in sorted_features[-int(len(sorted_features) * 0.2):]]
                
                # Feature conversion rates
                conversion_query = await session.execute(
                    text("""
                        SELECT 
                            feature_name,
                            COUNT(CASE WHEN event_type = 'feature_success' THEN 1 END)::FLOAT / 
                            COUNT(CASE WHEN event_type = 'feature_started' THEN 1 END) * 100 as conversion_rate
                        FROM analytics_events 
                        WHERE timestamp >= NOW() - INTERVAL '30 days'
                        AND event_type IN ('feature_started', 'feature_success')
                        GROUP BY feature_name
                    """)
                )
                feature_conversion_rates = {row[0]: float(row[1]) for row in conversion_query.fetchall()}
                
                # New feature adoption speed (time to 50% adoption)
                adoption_speed = await self.calculate_adoption_speed(session)
                
                return FeatureAdoptionMetrics(
                    feature_usage_rates=feature_usage_rates,
                    feature_abandonment_rates=feature_abandonment_rates,
                    new_feature_adoption_speed=adoption_speed,
                    feature_stickiness=feature_stickiness,
                    power_user_features=power_user_features,
                    underutilized_features=underutilized_features,
                    feature_conversion_rates=feature_conversion_rates
                )
                
            except Exception as e:
                self.logger.error(f"Error collecting feature adoption metrics: {e}")
                raise

    async def collect_revenue_metrics(self) -> RevenueMetrics:
        """Collect revenue and cost optimization metrics"""
        async with get_async_session() as session:
            try:
                # Revenue per user
                revenue_query = await session.execute(
                    text("""
                        SELECT 
                            SUM(revenue_amount) / COUNT(DISTINCT user_id) as revenue_per_user
                        FROM user_revenue 
                        WHERE created_at >= NOW() - INTERVAL '30 days'
                    """)
                )
                revenue_per_user = float(revenue_query.scalar() or 0)
                
                # Cost per user (AI operations + infrastructure)
                cost_query = await session.execute(
                    text("""
                        SELECT 
                            (SUM(ai_cost) + SUM(infrastructure_cost)) / COUNT(DISTINCT user_id) as cost_per_user
                        FROM user_costs 
                        WHERE created_at >= NOW() - INTERVAL '30 days'
                    """)
                )
                cost_per_user = float(cost_query.scalar() or 0)
                
                # Profit margin
                profit_margin = ((revenue_per_user - cost_per_user) / revenue_per_user * 100) if revenue_per_user > 0 else 0
                
                # AI operation costs
                ai_cost_query = await session.execute(
                    text("""
                        SELECT SUM(ai_cost) 
                        FROM user_costs 
                        WHERE created_at >= NOW() - INTERVAL '30 days'
                    """)
                )
                ai_operation_costs = float(ai_cost_query.scalar() or 0)
                
                # Infrastructure costs
                infra_cost_query = await session.execute(
                    text("""
                        SELECT SUM(infrastructure_cost) 
                        FROM user_costs 
                        WHERE created_at >= NOW() - INTERVAL '30 days'
                    """)
                )
                infrastructure_costs = float(infra_cost_query.scalar() or 0)
                
                # Cost optimization savings
                savings_query = await session.execute(
                    text("""
                        SELECT SUM(cost_savings) 
                        FROM cost_optimizations 
                        WHERE created_at >= NOW() - INTERVAL '30 days'
                    """)
                )
                cost_optimization_savings = float(savings_query.scalar() or 0)
                
                # ROI per feature
                roi_query = await session.execute(
                    text("""
                        SELECT 
                            feature_name,
                            (SUM(revenue_generated) - SUM(feature_cost)) / SUM(feature_cost) * 100 as roi
                        FROM feature_economics 
                        WHERE created_at >= NOW() - INTERVAL '30 days'
                        GROUP BY feature_name
                    """)
                )
                roi_per_feature = {row[0]: float(row[1]) for row in roi_query.fetchall()}
                
                # Cost efficiency trend (month over month)
                efficiency_query = await session.execute(
                    text("""
                        SELECT 
                            (current_month.efficiency - previous_month.efficiency) / previous_month.efficiency * 100 as trend
                        FROM (
                            SELECT AVG(cost_per_user) as efficiency
                            FROM user_costs 
                            WHERE created_at >= NOW() - INTERVAL '30 days'
                        ) current_month,
                        (
                            SELECT AVG(cost_per_user) as efficiency
                            FROM user_costs 
                            WHERE created_at >= NOW() - INTERVAL '60 days' 
                            AND created_at < NOW() - INTERVAL '30 days'
                        ) previous_month
                    """)
                )
                cost_efficiency_trend = float(efficiency_query.scalar() or 0)
                
                return RevenueMetrics(
                    revenue_per_user=revenue_per_user,
                    cost_per_user=cost_per_user,
                    profit_margin=profit_margin,
                    cost_optimization_savings=cost_optimization_savings,
                    ai_operation_costs=ai_operation_costs,
                    infrastructure_costs=infrastructure_costs,
                    roi_per_feature=roi_per_feature,
                    cost_efficiency_trend=cost_efficiency_trend
                )
                
            except Exception as e:
                self.logger.error(f"Error collecting revenue metrics: {e}")
                raise

    async def collect_productivity_metrics(self) -> ProductivityMetrics:
        """Collect user productivity and efficiency metrics"""
        async with get_async_session() as session:
            try:
                # Time saved per user (minutes per day)
                time_saved_query = await session.execute(
                    text("""
                        SELECT AVG(time_saved_minutes) 
                        FROM productivity_tracking 
                        WHERE created_at >= NOW() - INTERVAL '7 days'
                    """)
                )
                time_saved_per_user = float(time_saved_query.scalar() or 0)
                
                # Documents generated rate
                doc_rate_query = await session.execute(
                    text("""
                        SELECT 
                            COUNT(*)::FLOAT / COUNT(DISTINCT user_id) as docs_per_user
                        FROM analytics_events 
                        WHERE event_type = 'document_generated'
                        AND timestamp >= NOW() - INTERVAL '7 days'
                    """)
                )
                documents_generated_rate = float(doc_rate_query.scalar() or 0)
                
                # Search success rate
                search_success_query = await session.execute(
                    text("""
                        SELECT 
                            COUNT(CASE WHEN event_type = 'search_success' THEN 1 END)::FLOAT /
                            COUNT(CASE WHEN event_type = 'search_started' THEN 1 END) * 100
                        FROM analytics_events 
                        WHERE timestamp >= NOW() - INTERVAL '7 days'
                    """)
                )
                search_success_rate = float(search_success_query.scalar() or 0)
                
                # RFC completion rate
                rfc_completion_query = await session.execute(
                    text("""
                        SELECT 
                            COUNT(CASE WHEN event_type = 'rfc_completed' THEN 1 END)::FLOAT /
                            COUNT(CASE WHEN event_type = 'rfc_started' THEN 1 END) * 100
                        FROM analytics_events 
                        WHERE timestamp >= NOW() - INTERVAL '30 days'
                    """)
                )
                rfc_completion_rate = float(rfc_completion_query.scalar() or 0)
                
                # Code review efficiency
                code_review_query = await session.execute(
                    text("""
                        SELECT AVG(review_time_minutes) 
                        FROM code_reviews 
                        WHERE created_at >= NOW() - INTERVAL '7 days'
                    """)
                )
                code_review_efficiency = float(code_review_query.scalar() or 0)
                
                # Task completion speed
                task_speed_query = await session.execute(
                    text("""
                        SELECT AVG(completion_time_minutes) 
                        FROM task_completions 
                        WHERE created_at >= NOW() - INTERVAL '7 days'
                    """)
                )
                task_completion_speed = float(task_speed_query.scalar() or 0)
                
                # Overall productivity score (0-100)
                productivity_score = await self.calculate_productivity_score(
                    time_saved_per_user,
                    documents_generated_rate,
                    search_success_rate,
                    rfc_completion_rate,
                    code_review_efficiency
                )
                
                return ProductivityMetrics(
                    time_saved_per_user=time_saved_per_user,
                    documents_generated_rate=documents_generated_rate,
                    search_success_rate=search_success_rate,
                    rfc_completion_rate=rfc_completion_rate,
                    code_review_efficiency=code_review_efficiency,
                    task_completion_speed=task_completion_speed,
                    productivity_score=productivity_score
                )
                
            except Exception as e:
                self.logger.error(f"Error collecting productivity metrics: {e}")
                raise

    async def calculate_business_kpis(
        self,
        engagement: UserEngagementMetrics,
        adoption: FeatureAdoptionMetrics,
        revenue: RevenueMetrics,
        productivity: ProductivityMetrics
    ) -> List[BusinessKPI]:
        """Calculate high-level business KPIs"""
        kpis = []
        
        # User Growth KPI
        kpis.append(BusinessKPI(
            name="Monthly Active Users",
            current_value=engagement.monthly_active_users,
            target_value=engagement.monthly_active_users * 1.5,  # 50% growth target
            unit="users",
            trend="up" if engagement.monthly_active_users > engagement.weekly_active_users * 4 else "stable",
            change_percent=0.0,  # Calculate from historical data
            category=MetricType.USER_ENGAGEMENT,
            description="Total unique users active in the last 30 days"
        ))
        
        # User Stickiness KPI
        stickiness = (engagement.daily_active_users / engagement.monthly_active_users * 100) if engagement.monthly_active_users > 0 else 0
        kpis.append(BusinessKPI(
            name="User Stickiness (DAU/MAU)",
            current_value=stickiness,
            target_value=25.0,  # Industry benchmark
            unit="%",
            trend="up" if stickiness > 20 else "down",
            change_percent=0.0,
            category=MetricType.USER_ENGAGEMENT,
            description="Percentage of monthly users who are active daily"
        ))
        
        # Feature Adoption Rate KPI
        avg_adoption = np.mean(list(adoption.feature_usage_rates.values())) if adoption.feature_usage_rates else 0
        kpis.append(BusinessKPI(
            name="Average Feature Adoption Rate",
            current_value=avg_adoption,
            target_value=80.0,  # 80% target
            unit="%",
            trend="up" if avg_adoption > 70 else "stable",
            change_percent=0.0,
            category=MetricType.FEATURE_ADOPTION,
            description="Average percentage of users adopting features"
        ))
        
        # Revenue per User KPI
        kpis.append(BusinessKPI(
            name="Revenue per User",
            current_value=revenue.revenue_per_user,
            target_value=revenue.revenue_per_user * 2.0,  # 2x growth target
            unit="$",
            trend="up" if revenue.revenue_per_user > 0 else "stable",
            change_percent=0.0,
            category=MetricType.REVENUE,
            description="Average revenue generated per user per month"
        ))
        
        # Profit Margin KPI
        kpis.append(BusinessKPI(
            name="Profit Margin",
            current_value=revenue.profit_margin,
            target_value=40.0,  # 40% target margin
            unit="%",
            trend="up" if revenue.profit_margin > 30 else "down",
            change_percent=0.0,
            category=MetricType.REVENUE,
            description="Profit margin after all costs"
        ))
        
        # Productivity Score KPI
        kpis.append(BusinessKPI(
            name="User Productivity Score",
            current_value=productivity.productivity_score,
            target_value=85.0,  # 85% productivity target
            unit="score",
            trend="up" if productivity.productivity_score > 75 else "stable",
            change_percent=0.0,
            category=MetricType.PRODUCTIVITY,
            description="Overall user productivity improvement score"
        ))
        
        # Customer Satisfaction KPI (derived from retention)
        satisfaction_score = (engagement.retention_rate_30d + engagement.retention_rate_7d) / 2
        kpis.append(BusinessKPI(
            name="Customer Satisfaction Score",
            current_value=satisfaction_score,
            target_value=90.0,  # 90% satisfaction target
            unit="%",
            trend="up" if satisfaction_score > 80 else "stable",
            change_percent=0.0,
            category=MetricType.SATISFACTION,
            description="Derived satisfaction score from retention rates"
        ))
        
        return kpis

    async def calculate_overall_health_score(self, kpis: List[BusinessKPI]) -> float:
        """Calculate overall business health score (0-100)"""
        if not kpis:
            return 0.0
            
        scores = []
        for kpi in kpis:
            if kpi.target_value > 0:
                score = min(100, (kpi.current_value / kpi.target_value) * 100)
                scores.append(score)
                
        return np.mean(scores) if scores else 0.0

    async def generate_recommendations(self, kpis: List[BusinessKPI]) -> List[str]:
        """Generate actionable business recommendations"""
        recommendations = []
        
        for kpi in kpis:
            performance_ratio = kpi.current_value / kpi.target_value if kpi.target_value > 0 else 0
            
            if performance_ratio < 0.7:  # Below 70% of target
                if kpi.category == MetricType.USER_ENGAGEMENT:
                    recommendations.append(
                        f"🚨 {kpi.name} is at {performance_ratio:.1%} of target. "
                        "Consider improving onboarding flow and user experience."
                    )
                elif kpi.category == MetricType.FEATURE_ADOPTION:
                    recommendations.append(
                        f"📈 {kpi.name} needs attention at {performance_ratio:.1%} of target. "
                        "Focus on feature discovery and user education."
                    )
                elif kpi.category == MetricType.REVENUE:
                    recommendations.append(
                        f"💰 {kpi.name} is underperforming at {performance_ratio:.1%} of target. "
                        "Review pricing strategy and value proposition."
                    )
                elif kpi.category == MetricType.PRODUCTIVITY:
                    recommendations.append(
                        f"⚡ {kpi.name} below target at {performance_ratio:.1%}. "
                        "Optimize workflows and reduce friction points."
                    )
                    
        if not recommendations:
            recommendations.append("✅ All KPIs are performing well! Continue current strategies.")
            
        return recommendations

    # Helper methods
    async def calculate_retention_rate(self, session: AsyncSession, days: int) -> float:
        """Calculate user retention rate for specified days"""
        try:
            query = await session.execute(
                text(f"""
                    SELECT 
                        COUNT(returning_users.user_id)::FLOAT / COUNT(new_users.user_id) * 100
                    FROM (
                        SELECT DISTINCT user_id
                        FROM analytics_events 
                        WHERE timestamp >= NOW() - INTERVAL '{days + 7} days'
                        AND timestamp < NOW() - INTERVAL '{days} days'
                    ) new_users
                    LEFT JOIN (
                        SELECT DISTINCT user_id
                        FROM analytics_events 
                        WHERE timestamp >= NOW() - INTERVAL '{days} days'
                    ) returning_users ON new_users.user_id = returning_users.user_id
                """)
            )
            return float(query.scalar() or 0)
        except Exception:
            return 0.0

    async def calculate_feature_engagement_rates(self, session: AsyncSession) -> Dict[str, float]:
        """Calculate engagement rate for each feature"""
        try:
            query = await session.execute(
                text("""
                    SELECT 
                        feature_name,
                        COUNT(DISTINCT user_id)::FLOAT / (
                            SELECT COUNT(DISTINCT user_id) 
                            FROM analytics_events 
                            WHERE timestamp >= NOW() - INTERVAL '7 days'
                        ) * 100 as engagement_rate
                    FROM analytics_events 
                    WHERE timestamp >= NOW() - INTERVAL '7 days'
                    AND feature_name IS NOT NULL
                    GROUP BY feature_name
                """)
            )
            return {row[0]: float(row[1]) for row in query.fetchall()}
        except Exception:
            return {}

    async def calculate_adoption_speed(self, session: AsyncSession) -> Dict[str, float]:
        """Calculate time to 50% adoption for new features"""
        # Simplified calculation - in production, this would track feature rollout dates
        return {"new_feature_1": 7.0, "new_feature_2": 14.0}  # days to 50% adoption

    async def calculate_productivity_score(
        self,
        time_saved: float,
        doc_rate: float,
        search_success: float,
        rfc_completion: float,
        code_review_efficiency: float
    ) -> float:
        """Calculate overall productivity score"""
        # Weighted average of productivity indicators
        weights = {
            "time_saved": 0.3,
            "doc_rate": 0.2,
            "search_success": 0.2,
            "rfc_completion": 0.15,
            "code_review": 0.15
        }
        
        # Normalize values to 0-100 scale
        time_saved_norm = min(100, time_saved / 60 * 100)  # 60 minutes = 100%
        doc_rate_norm = min(100, doc_rate / 5 * 100)  # 5 docs per user = 100%
        search_success_norm = search_success  # Already percentage
        rfc_completion_norm = rfc_completion  # Already percentage
        code_review_norm = max(0, 100 - (code_review_efficiency / 60 * 100))  # Less time = better
        
        score = (
            time_saved_norm * weights["time_saved"] +
            doc_rate_norm * weights["doc_rate"] +
            search_success_norm * weights["search_success"] +
            rfc_completion_norm * weights["rfc_completion"] +
            code_review_norm * weights["code_review"]
        )
        
        return min(100, max(0, score))


# Global instance
enhanced_metrics_collector = EnhancedBusinessMetricsCollector()


async def get_real_time_business_dashboard() -> Dict[str, Any]:
    """Get real-time business dashboard data"""
    return await enhanced_metrics_collector.collect_all_metrics()


async def get_kpi_summary() -> List[BusinessKPI]:
    """Get summary of key business KPIs"""
    metrics = await enhanced_metrics_collector.collect_all_metrics()
    return metrics.get("business_kpis", [])


async def get_health_score() -> float:
    """Get overall business health score"""
    metrics = await enhanced_metrics_collector.collect_all_metrics()
    return metrics.get("overall_health_score", 0.0) 