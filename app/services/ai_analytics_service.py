"""
AI Analytics Service
Advanced analytics, predictive modeling, and performance insights
"""

import asyncio
import json
import logging
import statistics
import time
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class AnalyticsType(Enum):
    """Types of AI analytics"""

    USAGE_PATTERNS = "usage_patterns"
    PERFORMANCE_TRENDS = "performance_trends"
    COST_ANALYSIS = "cost_analysis"
    QUALITY_METRICS = "quality_metrics"
    PREDICTIVE_MODELING = "predictive_modeling"


class MetricType(Enum):
    """Metric types for analytics"""

    LATENCY = "latency"
    ACCURACY = "accuracy"
    COST = "cost"
    THROUGHPUT = "throughput"
    QUALITY_SCORE = "quality_score"
    ERROR_RATE = "error_rate"
    USER_SATISFACTION = "user_satisfaction"


@dataclass
class AnalyticsDataPoint:
    """Single analytics data point"""

    timestamp: datetime
    metric_type: MetricType
    value: float
    model_type: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class TrendAnalysis:
    """Trend analysis result"""

    metric_type: MetricType
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0-1
    change_percent: float
    confidence: float
    forecast_points: List[Tuple[datetime, float]]
    insights: List[str]


@dataclass
class UsagePattern:
    """Usage pattern analysis"""

    pattern_id: str
    pattern_type: str
    frequency: int
    peak_hours: List[int]
    model_preferences: Dict[str, float]
    user_segments: Dict[str, int]
    seasonal_trends: Dict[str, float]
    recommendations: List[str]


@dataclass
class CostInsight:
    """Cost optimization insight"""

    insight_id: str
    cost_driver: str
    current_cost: float
    potential_savings: float
    savings_percent: float
    optimization_actions: List[str]
    impact_level: str  # "high", "medium", "low"
    implementation_effort: str  # "easy", "moderate", "complex"


@dataclass
class PredictiveModel:
    """Predictive model result"""

    model_id: str
    metric_type: MetricType
    model_type: str
    accuracy: float
    predictions: List[Tuple[datetime, float, float]]  # timestamp, value, confidence
    feature_importance: Dict[str, float]
    model_insights: List[str]


class AIAnalyticsService:
    """Service for AI analytics and insights"""

    def __init__(self):
        self.data_points: List[AnalyticsDataPoint] = []
        self.usage_patterns: List[UsagePattern] = []
        self.cost_insights: List[CostInsight] = []
        self.predictive_models: Dict[str, PredictiveModel] = {}

        # Initialize with sample data
        self._initialize_sample_data()

    def _initialize_sample_data(self):
        """Initialize with sample analytics data"""
        now = datetime.utcnow()

        # Generate sample data points for the last 30 days
        for days_back in range(30):
            for hour in range(24):
                timestamp = now - timedelta(days=days_back, hours=hour)

                # Add latency data points
                self.data_points.append(
                    AnalyticsDataPoint(
                        timestamp=timestamp,
                        metric_type=MetricType.LATENCY,
                        value=800
                        + np.random.normal(0, 100),  # Base latency with variation
                        model_type="code_review",
                        user_id=f"user_{np.random.randint(1, 100)}",
                    )
                )

                # Add accuracy data points
                self.data_points.append(
                    AnalyticsDataPoint(
                        timestamp=timestamp,
                        metric_type=MetricType.ACCURACY,
                        value=0.85 + np.random.normal(0, 0.05),
                        model_type="semantic_search",
                        user_id=f"user_{np.random.randint(1, 100)}",
                    )
                )

                # Add cost data points
                self.data_points.append(
                    AnalyticsDataPoint(
                        timestamp=timestamp,
                        metric_type=MetricType.COST,
                        value=0.02 + np.random.normal(0, 0.005),
                        model_type="rfc_generation",
                        user_id=f"user_{np.random.randint(1, 100)}",
                    )
                )

    async def collect_analytics_data(
        self,
        metric_type: MetricType,
        value: float,
        model_type: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Collect analytics data point"""
        data_point = AnalyticsDataPoint(
            timestamp=datetime.utcnow(),
            metric_type=metric_type,
            value=value,
            model_type=model_type,
            user_id=user_id,
            context=context,
        )

        self.data_points.append(data_point)

        # Keep only last 10000 data points to manage memory
        if len(self.data_points) > 10000:
            self.data_points = self.data_points[-10000:]

        logger.info(
            f"Collected analytics data: {metric_type.value} = {value} for {model_type}"
        )

    async def analyze_usage_patterns(
        self, time_range_days: int = 30
    ) -> List[UsagePattern]:
        """Analyze AI usage patterns"""

        logger.info(f"Analyzing usage patterns for last {time_range_days} days")

        cutoff_time = datetime.utcnow() - timedelta(days=time_range_days)
        recent_data = [dp for dp in self.data_points if dp.timestamp >= cutoff_time]

        patterns = []

        # Pattern 1: Peak Usage Hours
        hourly_usage = defaultdict(int)
        for dp in recent_data:
            hour = dp.timestamp.hour
            hourly_usage[hour] += 1

        peak_hours = sorted(
            hourly_usage.keys(), key=lambda h: hourly_usage[h], reverse=True
        )[:3]

        # Pattern 2: Model Preferences
        model_usage = defaultdict(int)
        for dp in recent_data:
            model_usage[dp.model_type] += 1

        total_usage = sum(model_usage.values())
        model_preferences = (
            {model: count / total_usage for model, count in model_usage.items()}
            if total_usage > 0
            else {}
        )

        # Pattern 3: User Segments
        user_segments = defaultdict(int)
        user_activity = defaultdict(int)
        for dp in recent_data:
            if dp.user_id:
                user_activity[dp.user_id] += 1

        for user_id, activity in user_activity.items():
            if activity >= 50:
                user_segments["heavy_users"] += 1
            elif activity >= 10:
                user_segments["regular_users"] += 1
            else:
                user_segments["light_users"] += 1

        # Create usage pattern
        pattern = UsagePattern(
            pattern_id=str(uuid.uuid4()),
            pattern_type="general_usage",
            frequency=len(recent_data),
            peak_hours=peak_hours,
            model_preferences=model_preferences,
            user_segments=dict(user_segments),
            seasonal_trends=self._analyze_seasonal_trends(recent_data),
            recommendations=self._generate_usage_recommendations(
                peak_hours, model_preferences, user_segments
            ),
        )

        patterns.append(pattern)
        self.usage_patterns = patterns

        return patterns

    def _analyze_seasonal_trends(
        self, data_points: List[AnalyticsDataPoint]
    ) -> Dict[str, float]:
        """Analyze seasonal trends in usage"""
        daily_usage = defaultdict(int)

        for dp in data_points:
            day_of_week = dp.timestamp.strftime("%A")
            daily_usage[day_of_week] += 1

        total = sum(daily_usage.values())
        if total == 0:
            return {}

        return {day: count / total for day, count in daily_usage.items()}

    def _generate_usage_recommendations(
        self,
        peak_hours: List[int],
        model_preferences: Dict[str, float],
        user_segments: Dict[str, int],
    ) -> List[str]:
        """Generate usage pattern recommendations"""
        recommendations = []

        # Peak hours recommendations
        if peak_hours:
            recommendations.append(
                f"Peak usage hours are {', '.join(map(str, peak_hours))}. "
                "Consider scaling resources during these times."
            )

        # Model preference recommendations
        if model_preferences:
            most_used = max(model_preferences.items(), key=lambda x: x[1])
            recommendations.append(
                f"Most used model is {most_used[0]} ({most_used[1]:.1%}). "
                "Focus optimization efforts on this model."
            )

        # User segment recommendations
        heavy_users = user_segments.get("heavy_users", 0)
        if heavy_users > 0:
            recommendations.append(
                f"{heavy_users} heavy users detected. "
                "Consider premium features or dedicated support."
            )

        return recommendations

    async def analyze_performance_trends(
        self,
        metric_type: MetricType,
        model_type: Optional[str] = None,
        time_range_days: int = 30,
    ) -> TrendAnalysis:
        """Analyze performance trends"""

        logger.info(
            f"Analyzing {metric_type.value} trends for {model_type or 'all models'}"
        )

        cutoff_time = datetime.utcnow() - timedelta(days=time_range_days)

        # Filter data points
        filtered_data = [
            dp
            for dp in self.data_points
            if dp.timestamp >= cutoff_time
            and dp.metric_type == metric_type
            and (model_type is None or dp.model_type == model_type)
        ]

        if len(filtered_data) < 2:
            return TrendAnalysis(
                metric_type=metric_type,
                trend_direction="insufficient_data",
                trend_strength=0.0,
                change_percent=0.0,
                confidence=0.0,
                forecast_points=[],
                insights=["Insufficient data for trend analysis"],
            )

        # Sort by timestamp
        filtered_data.sort(key=lambda dp: dp.timestamp)

        # Calculate trend
        values = [dp.value for dp in filtered_data]
        timestamps = [dp.timestamp for dp in filtered_data]

        # Simple linear regression for trend
        n = len(values)
        x_vals = list(range(n))

        # Calculate slope
        x_mean = statistics.mean(x_vals)
        y_mean = statistics.mean(values)

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, values))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)

        slope = numerator / denominator if denominator != 0 else 0

        # Determine trend direction and strength
        if abs(slope) < 0.01:
            trend_direction = "stable"
            trend_strength = 0.1
        elif slope > 0:
            trend_direction = "increasing"
            trend_strength = min(abs(slope) * 100, 1.0)
        else:
            trend_direction = "decreasing"
            trend_strength = min(abs(slope) * 100, 1.0)

        # Calculate change percent
        if len(values) >= 2:
            change_percent = (
                ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0
            )
        else:
            change_percent = 0

        # Generate forecast
        forecast_points = self._generate_forecast(
            timestamps, values, 7
        )  # 7 days forecast

        # Generate insights
        insights = self._generate_trend_insights(
            metric_type, trend_direction, change_percent, trend_strength
        )

        return TrendAnalysis(
            metric_type=metric_type,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            change_percent=change_percent,
            confidence=min(0.5 + trend_strength, 0.95),
            forecast_points=forecast_points,
            insights=insights,
        )

    def _generate_forecast(
        self, timestamps: List[datetime], values: List[float], forecast_days: int
    ) -> List[Tuple[datetime, float]]:
        """Generate simple forecast points"""
        if len(values) < 2:
            return []

        # Simple moving average forecast
        recent_values = values[-min(7, len(values)) :]
        avg_value = statistics.mean(recent_values)

        forecast_points = []
        last_timestamp = timestamps[-1]

        for i in range(1, forecast_days + 1):
            forecast_time = last_timestamp + timedelta(days=i)
            # Add some noise to make it realistic
            noise = np.random.normal(0, statistics.stdev(recent_values) * 0.1)
            forecast_value = avg_value + noise
            forecast_points.append((forecast_time, forecast_value))

        return forecast_points

    def _generate_trend_insights(
        self,
        metric_type: MetricType,
        trend_direction: str,
        change_percent: float,
        trend_strength: float,
    ) -> List[str]:
        """Generate insights based on trend analysis"""
        insights = []

        if trend_direction == "increasing":
            if metric_type in [
                MetricType.LATENCY,
                MetricType.COST,
                MetricType.ERROR_RATE,
            ]:
                insights.append(
                    f"{metric_type.value} is increasing by {change_percent:.1f}% - this needs attention"
                )
                if change_percent > 20:
                    insights.append("Consider immediate optimization measures")
            else:
                insights.append(
                    f"{metric_type.value} is improving by {change_percent:.1f}%"
                )

        elif trend_direction == "decreasing":
            if metric_type in [
                MetricType.ACCURACY,
                MetricType.QUALITY_SCORE,
                MetricType.USER_SATISFACTION,
            ]:
                insights.append(
                    f"{metric_type.value} is declining by {abs(change_percent):.1f}% - investigate causes"
                )
                if abs(change_percent) > 15:
                    insights.append(
                        "Quality degradation detected - immediate review needed"
                    )
            else:
                insights.append(
                    f"{metric_type.value} is improving by {abs(change_percent):.1f}%"
                )

        else:
            insights.append(f"{metric_type.value} is stable with minimal variation")

        if trend_strength > 0.7:
            insights.append("Strong trend detected - high confidence in predictions")
        elif trend_strength > 0.3:
            insights.append("Moderate trend - monitor for continuation")
        else:
            insights.append("Weak trend - data may be noisy")

        return insights

    async def analyze_cost_optimization(self) -> List[CostInsight]:
        """Analyze cost optimization opportunities"""

        logger.info("Analyzing cost optimization opportunities")

        insights = []

        # Insight 1: High-cost models
        cost_data = [dp for dp in self.data_points if dp.metric_type == MetricType.COST]
        if cost_data:
            model_costs = defaultdict(list)
            for dp in cost_data:
                model_costs[dp.model_type].append(dp.value)

            for model, costs in model_costs.items():
                avg_cost = statistics.mean(costs)
                if avg_cost > 0.025:  # Threshold for high cost
                    potential_savings = avg_cost * 0.3  # 30% potential savings

                    insights.append(
                        CostInsight(
                            insight_id=str(uuid.uuid4()),
                            cost_driver=f"High-cost model: {model}",
                            current_cost=avg_cost,
                            potential_savings=potential_savings,
                            savings_percent=30.0,
                            optimization_actions=[
                                "Implement request batching",
                                "Enable intelligent caching",
                                "Consider model compression",
                                "Optimize prompt engineering",
                            ],
                            impact_level="high",
                            implementation_effort="moderate",
                        )
                    )

        # Insight 2: Usage inefficiency
        usage_data = [dp for dp in self.data_points[-1000:]]  # Last 1000 requests
        if usage_data:
            model_usage = defaultdict(int)
            for dp in usage_data:
                model_usage[dp.model_type] += 1

            total_requests = len(usage_data)
            for model, count in model_usage.items():
                usage_percent = (count / total_requests) * 100
                if usage_percent < 10:  # Low usage model
                    insights.append(
                        CostInsight(
                            insight_id=str(uuid.uuid4()),
                            cost_driver=f"Underutilized model: {model}",
                            current_cost=0.02,  # Estimated
                            potential_savings=0.015,
                            savings_percent=75.0,
                            optimization_actions=[
                                "Consider consolidating with similar models",
                                "Implement on-demand loading",
                                "Review model necessity",
                            ],
                            impact_level="medium",
                            implementation_effort="easy",
                        )
                    )

        # Insight 3: Peak time optimization
        current_hour = datetime.utcnow().hour
        peak_hours = [9, 10, 11, 14, 15, 16]  # Business hours
        if current_hour in peak_hours:
            insights.append(
                CostInsight(
                    insight_id=str(uuid.uuid4()),
                    cost_driver="Peak time resource usage",
                    current_cost=0.05,  # Estimated peak cost
                    potential_savings=0.02,
                    savings_percent=40.0,
                    optimization_actions=[
                        "Implement auto-scaling",
                        "Use spot instances during off-peak",
                        "Cache frequent requests",
                        "Load balance across regions",
                    ],
                    impact_level="high",
                    implementation_effort="complex",
                )
            )

        self.cost_insights = insights
        return insights

    async def build_predictive_model(
        self, metric_type: MetricType, model_type: str, forecast_days: int = 7
    ) -> PredictiveModel:
        """Build predictive model for performance metrics"""

        logger.info(
            f"Building predictive model for {metric_type.value} on {model_type}"
        )

        # Filter relevant data
        relevant_data = [
            dp
            for dp in self.data_points
            if dp.metric_type == metric_type and dp.model_type == model_type
        ]

        if len(relevant_data) < 10:
            return PredictiveModel(
                model_id=str(uuid.uuid4()),
                metric_type=metric_type,
                model_type=model_type,
                accuracy=0.0,
                predictions=[],
                feature_importance={},
                model_insights=["Insufficient data for modeling"],
            )

        # Sort by timestamp
        relevant_data.sort(key=lambda dp: dp.timestamp)

        # Simple time series prediction using moving average
        values = [dp.value for dp in relevant_data]
        timestamps = [dp.timestamp for dp in relevant_data]

        # Calculate model accuracy using historical data
        predictions_vs_actual = []
        window_size = min(5, len(values) // 2)

        for i in range(window_size, len(values) - 1):
            historical = values[i - window_size : i]
            predicted = statistics.mean(historical)
            actual = values[i]
            predictions_vs_actual.append(
                abs(predicted - actual) / actual if actual != 0 else 0
            )

        accuracy = (
            1 - statistics.mean(predictions_vs_actual) if predictions_vs_actual else 0.5
        )
        accuracy = max(0.0, min(1.0, accuracy))

        # Generate future predictions
        recent_values = values[-window_size:]
        base_prediction = statistics.mean(recent_values)
        std_dev = statistics.stdev(recent_values) if len(recent_values) > 1 else 0.1

        predictions = []
        last_timestamp = timestamps[-1]

        for i in range(1, forecast_days + 1):
            future_time = last_timestamp + timedelta(days=i)

            # Add trend and noise
            trend_factor = 1 + (i * 0.01)  # Small upward trend
            noise = np.random.normal(0, std_dev * 0.2)
            predicted_value = base_prediction * trend_factor + noise
            confidence = max(
                0.1, accuracy - (i * 0.1)
            )  # Decreasing confidence over time

            predictions.append((future_time, predicted_value, confidence))

        # Feature importance (simulated)
        feature_importance = {
            "time_of_day": 0.3,
            "day_of_week": 0.2,
            "recent_usage": 0.25,
            "model_load": 0.15,
            "seasonal_factors": 0.1,
        }

        # Generate insights
        model_insights = [
            f"Model accuracy: {accuracy:.1%}",
            f"Based on {len(relevant_data)} historical data points",
            f"Prediction confidence decreases over time",
            "Consider retraining with more recent data for better accuracy",
        ]

        if accuracy > 0.8:
            model_insights.append("High accuracy model - reliable for decision making")
        elif accuracy > 0.6:
            model_insights.append("Moderate accuracy - use with caution")
        else:
            model_insights.append(
                "Low accuracy - collect more data before relying on predictions"
            )

        predictive_model = PredictiveModel(
            model_id=str(uuid.uuid4()),
            metric_type=metric_type,
            model_type=model_type,
            accuracy=accuracy,
            predictions=predictions,
            feature_importance=feature_importance,
            model_insights=model_insights,
        )

        self.predictive_models[f"{metric_type.value}_{model_type}"] = predictive_model

        return predictive_model

    async def get_dashboard_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics for dashboard"""

        logger.info("Generating dashboard analytics")

        # Recent performance metrics
        recent_data = [
            dp
            for dp in self.data_points
            if dp.timestamp >= datetime.utcnow() - timedelta(days=7)
        ]

        # Calculate aggregated metrics
        metrics_by_type = defaultdict(list)
        for dp in recent_data:
            metrics_by_type[dp.metric_type.value].append(dp.value)

        aggregated_metrics = {}
        for metric_type, values in metrics_by_type.items():
            if values:
                aggregated_metrics[metric_type] = {
                    "avg": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0,
                    "count": len(values),
                }

        # Usage statistics
        model_usage = defaultdict(int)
        user_activity = defaultdict(int)

        for dp in recent_data:
            model_usage[dp.model_type] += 1
            if dp.user_id:
                user_activity[dp.user_id] += 1

        # Top insights
        top_insights = []
        if self.cost_insights:
            high_impact_insights = [
                insight
                for insight in self.cost_insights
                if insight.impact_level == "high"
            ]
            top_insights.extend(
                [
                    f"Potential savings: ${insight.potential_savings:.3f} ({insight.savings_percent:.1f}%)"
                    for insight in high_impact_insights[:3]
                ]
            )

        return {
            "summary": {
                "total_requests": len(recent_data),
                "active_models": len(model_usage),
                "active_users": len(user_activity),
                "data_points_collected": len(self.data_points),
            },
            "performance_metrics": aggregated_metrics,
            "model_usage": dict(model_usage),
            "user_activity_distribution": {
                "heavy_users": len([u for u in user_activity.values() if u >= 20]),
                "regular_users": len(
                    [u for u in user_activity.values() if 5 <= u < 20]
                ),
                "light_users": len([u for u in user_activity.values() if u < 5]),
            },
            "top_insights": top_insights,
            "last_updated": datetime.utcnow().isoformat(),
        }

    def get_analytics_history(self) -> List[Dict[str, Any]]:
        """Get analytics processing history"""

        return [
            {
                "analysis_type": "usage_patterns",
                "patterns_found": len(self.usage_patterns),
                "last_analysis": datetime.utcnow().isoformat(),
            },
            {
                "analysis_type": "cost_insights",
                "insights_generated": len(self.cost_insights),
                "total_potential_savings": sum(
                    insight.potential_savings for insight in self.cost_insights
                ),
                "last_analysis": datetime.utcnow().isoformat(),
            },
            {
                "analysis_type": "predictive_models",
                "models_trained": len(self.predictive_models),
                "last_training": datetime.utcnow().isoformat(),
            },
        ]


# Global instance
ai_analytics_service = AIAnalyticsService()
