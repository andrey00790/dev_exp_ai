"""
Advanced Analytics Module

Provides comprehensive analytics capabilities including:
- Usage analytics and metrics
- Cost optimization insights
- Performance monitoring
- User behavior analysis
- Report generation
"""

from .aggregator import DataAggregator
from .insights import InsightsEngine
from .models import (CostMetric, PerformanceMetric, UsageMetric,
                     UserBehaviorMetric)
from .service import AnalyticsService

__all__ = [
    "UsageMetric",
    "CostMetric",
    "PerformanceMetric",
    "UserBehaviorMetric",
    "AnalyticsService",
    "DataAggregator",
    "InsightsEngine",
]
