"""
AI Analytics API
Endpoints for advanced analytics, predictive modeling, and insights
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from infra.database.session import get_db
from app.models.user import User
from infra.monitoring.metrics import metrics
from app.security.auth import get_current_user
from app.services.ai_analytics_service import (AnalyticsType, CostInsight,
                                               MetricType, PredictiveModel,
                                               TrendAnalysis, UsagePattern,
                                               ai_analytics_service)

router = APIRouter(prefix="/ai-analytics", tags=["AI Analytics"])

# ============================================================================
# Request/Response Models
# ============================================================================


class AnalyticsDataRequest(BaseModel):
    """Request for collecting analytics data"""

    metric_type: str = Field(..., description="Type of metric")
    value: float = Field(..., description="Metric value")
    model_type: str = Field(..., description="Model type")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

    class Config:
        schema_extra = {
            "example": {
                "metric_type": "latency",
                "value": 850.5,
                "model_type": "code_review",
                "context": {"user_type": "premium", "request_size": "large"},
            }
        }


class TrendAnalysisRequest(BaseModel):
    """Request for trend analysis"""

    metric_type: str = Field(..., description="Metric to analyze")
    model_type: Optional[str] = Field(None, description="Specific model type")
    time_range_days: int = Field(30, description="Time range in days", ge=1, le=90)

    class Config:
        schema_extra = {
            "example": {
                "metric_type": "latency",
                "model_type": "code_review",
                "time_range_days": 30,
            }
        }


class PredictiveModelRequest(BaseModel):
    """Request for predictive modeling"""

    metric_type: str = Field(..., description="Metric to predict")
    model_type: str = Field(..., description="Model type")
    forecast_days: int = Field(7, description="Forecast period in days", ge=1, le=30)

    class Config:
        schema_extra = {
            "example": {
                "metric_type": "latency",
                "model_type": "code_review",
                "forecast_days": 7,
            }
        }


class TrendAnalysisResponse(BaseModel):
    """Response for trend analysis"""

    metric_type: str
    trend_direction: str
    trend_strength: float
    change_percent: float
    confidence: float
    forecast_points: List[Dict[str, Any]]
    insights: List[str]
    analysis_timestamp: str


class UsagePatternResponse(BaseModel):
    """Response for usage pattern analysis"""

    pattern_id: str
    pattern_type: str
    frequency: int
    peak_hours: List[int]
    model_preferences: Dict[str, float]
    user_segments: Dict[str, int]
    seasonal_trends: Dict[str, float]
    recommendations: List[str]
    analysis_timestamp: str


class CostInsightResponse(BaseModel):
    """Response for cost insights"""

    insight_id: str
    cost_driver: str
    current_cost: float
    potential_savings: float
    savings_percent: float
    optimization_actions: List[str]
    impact_level: str
    implementation_effort: str


class PredictiveModelResponse(BaseModel):
    """Response for predictive model"""

    model_id: str
    metric_type: str
    model_type: str
    accuracy: float
    predictions: List[Dict[str, Any]]
    feature_importance: Dict[str, float]
    model_insights: List[str]
    created_timestamp: str


class DashboardAnalyticsResponse(BaseModel):
    """Response for dashboard analytics"""

    summary: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    model_usage: Dict[str, int]
    user_activity_distribution: Dict[str, int]
    top_insights: List[str]
    last_updated: str


# ============================================================================
# Helper Functions
# ============================================================================


def parse_metric_type(metric_type_str: str) -> MetricType:
    """Parse metric type from string"""
    try:
        return MetricType(metric_type_str)
    except ValueError:
        valid_types = [t.value for t in MetricType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric_type '{metric_type_str}'. Valid types: {valid_types}",
        )


def trend_analysis_to_response(analysis: TrendAnalysis) -> TrendAnalysisResponse:
    """Convert TrendAnalysis to API response"""
    return TrendAnalysisResponse(
        metric_type=analysis.metric_type.value,
        trend_direction=analysis.trend_direction,
        trend_strength=analysis.trend_strength,
        change_percent=analysis.change_percent,
        confidence=analysis.confidence,
        forecast_points=[
            {
                "timestamp": point[0].isoformat(),
                "value": point[1],
                "confidence": analysis.confidence,
            }
            for point in analysis.forecast_points
        ],
        insights=analysis.insights,
        analysis_timestamp=datetime.utcnow().isoformat(),
    )


def usage_pattern_to_response(pattern: UsagePattern) -> UsagePatternResponse:
    """Convert UsagePattern to API response"""
    return UsagePatternResponse(
        pattern_id=pattern.pattern_id,
        pattern_type=pattern.pattern_type,
        frequency=pattern.frequency,
        peak_hours=pattern.peak_hours,
        model_preferences=pattern.model_preferences,
        user_segments=pattern.user_segments,
        seasonal_trends=pattern.seasonal_trends,
        recommendations=pattern.recommendations,
        analysis_timestamp=datetime.utcnow().isoformat(),
    )


def cost_insight_to_response(insight: CostInsight) -> CostInsightResponse:
    """Convert CostInsight to API response"""
    return CostInsightResponse(
        insight_id=insight.insight_id,
        cost_driver=insight.cost_driver,
        current_cost=insight.current_cost,
        potential_savings=insight.potential_savings,
        savings_percent=insight.savings_percent,
        optimization_actions=insight.optimization_actions,
        impact_level=insight.impact_level,
        implementation_effort=insight.implementation_effort,
    )


def predictive_model_to_response(model: PredictiveModel) -> PredictiveModelResponse:
    """Convert PredictiveModel to API response"""
    return PredictiveModelResponse(
        model_id=model.model_id,
        metric_type=model.metric_type.value,
        model_type=model.model_type,
        accuracy=model.accuracy,
        predictions=[
            {"timestamp": pred[0].isoformat(), "value": pred[1], "confidence": pred[2]}
            for pred in model.predictions
        ],
        feature_importance=model.feature_importance,
        model_insights=model.model_insights,
        created_timestamp=datetime.utcnow().isoformat(),
    )


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/collect-data")
async def collect_analytics_data(
    request: AnalyticsDataRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Collect analytics data point
    """
    try:
        metric_type = parse_metric_type(request.metric_type)

        await ai_analytics_service.collect_analytics_data(
            metric_type=metric_type,
            value=request.value,
            model_type=request.model_type,
            user_id=str(current_user.id),
            context=request.context,
        )

        return {
            "status": "success",
            "message": "Analytics data collected successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data collection failed: {str(e)}")


@router.get("/dashboard", response_model=DashboardAnalyticsResponse)
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics for dashboard
    """
    try:
        dashboard_data = await ai_analytics_service.get_dashboard_analytics()

        return DashboardAnalyticsResponse(**dashboard_data)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Dashboard analytics failed: {str(e)}"
        )


@router.post("/trends", response_model=TrendAnalysisResponse)
async def analyze_performance_trends(
    request: TrendAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyze performance trends for specific metrics
    """
    try:
        metric_type = parse_metric_type(request.metric_type)

        trend_analysis = await ai_analytics_service.analyze_performance_trends(
            metric_type=metric_type,
            model_type=request.model_type,
            time_range_days=request.time_range_days,
        )

        return trend_analysis_to_response(trend_analysis)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@router.get("/usage-patterns")
async def analyze_usage_patterns(
    time_range_days: int = Query(30, description="Time range in days", ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyze AI usage patterns
    """
    try:
        patterns = await ai_analytics_service.analyze_usage_patterns(
            time_range_days=time_range_days
        )

        return {
            "patterns": [usage_pattern_to_response(pattern) for pattern in patterns],
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "total_patterns": len(patterns),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Usage pattern analysis failed: {str(e)}"
        )


@router.get("/cost-insights")
async def get_cost_optimization_insights(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get cost optimization insights
    """
    try:
        insights = await ai_analytics_service.analyze_cost_optimization()

        # Calculate total potential savings
        total_savings = sum(insight.potential_savings for insight in insights)
        avg_savings_percent = (
            sum(insight.savings_percent for insight in insights) / len(insights)
            if insights
            else 0
        )

        return {
            "insights": [cost_insight_to_response(insight) for insight in insights],
            "summary": {
                "total_insights": len(insights),
                "total_potential_savings": total_savings,
                "average_savings_percent": avg_savings_percent,
                "high_impact_insights": len(
                    [i for i in insights if i.impact_level == "high"]
                ),
                "easy_implementation": len(
                    [i for i in insights if i.implementation_effort == "easy"]
                ),
            },
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Cost insights analysis failed: {str(e)}"
        )


@router.post("/predictive-model", response_model=PredictiveModelResponse)
async def build_predictive_model(
    request: PredictiveModelRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Build predictive model for performance metrics
    """
    try:
        metric_type = parse_metric_type(request.metric_type)

        predictive_model = await ai_analytics_service.build_predictive_model(
            metric_type=metric_type,
            model_type=request.model_type,
            forecast_days=request.forecast_days,
        )

        return predictive_model_to_response(predictive_model)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Predictive modeling failed: {str(e)}"
        )


@router.get("/history")
async def get_analytics_history(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get analytics processing history
    """
    try:
        history = ai_analytics_service.get_analytics_history()

        return {
            "history": history,
            "total_analyses": len(history),
            "last_updated": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"History retrieval failed: {str(e)}"
        )


@router.get("/metrics-overview")
async def get_metrics_overview(current_user: User = Depends(get_current_user)):
    """
    Get overview of available metrics and models
    """
    return {
        "available_metrics": [
            {
                "type": metric.value,
                "name": metric.value.replace("_", " ").title(),
                "description": f"Analytics for {metric.value.replace('_', ' ')}",
            }
            for metric in MetricType
        ],
        "analytics_types": [
            {
                "type": analytics.value,
                "name": analytics.value.replace("_", " ").title(),
                "description": f"Analysis of {analytics.value.replace('_', ' ')}",
            }
            for analytics in AnalyticsType
        ],
        "supported_models": [
            "code_review",
            "semantic_search",
            "rfc_generation",
            "multimodal_search",
        ],
    }


@router.get("/real-time-metrics")
async def get_real_time_metrics(
    limit: int = Query(100, description="Number of recent data points", ge=1, le=1000),
    current_user: User = Depends(get_current_user),
):
    """
    Get real-time analytics metrics
    """
    try:
        # Get recent data points
        recent_data = ai_analytics_service.data_points[-limit:]

        metrics_data = []
        for dp in recent_data:
            metrics_data.append(
                {
                    "timestamp": dp.timestamp.isoformat(),
                    "metric_type": dp.metric_type.value,
                    "value": dp.value,
                    "model_type": dp.model_type,
                    "user_id": dp.user_id,
                    "context": dp.context,
                }
            )

        return {
            "metrics": metrics_data,
            "total_points": len(metrics_data),
            "time_range": {
                "start": recent_data[0].timestamp.isoformat() if recent_data else None,
                "end": recent_data[-1].timestamp.isoformat() if recent_data else None,
            },
            "last_updated": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Real-time metrics failed: {str(e)}"
        )


@router.post("/batch-analysis")
async def run_batch_analysis(
    background_tasks: BackgroundTasks,
    time_range_days: int = Query(
        30, description="Time range for analysis", ge=1, le=90
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run comprehensive batch analysis
    """
    try:
        analysis_id = f"batch_{int(datetime.utcnow().timestamp())}"

        # Schedule background analysis
        async def run_analysis():
            # Usage patterns
            await ai_analytics_service.analyze_usage_patterns(time_range_days)

            # Cost insights
            await ai_analytics_service.analyze_cost_optimization()

            # Trend analysis for key metrics
            for metric_type in [
                MetricType.LATENCY,
                MetricType.ACCURACY,
                MetricType.COST,
            ]:
                await ai_analytics_service.analyze_performance_trends(
                    metric_type=metric_type, time_range_days=time_range_days
                )

        background_tasks.add_task(run_analysis)

        return {
            "analysis_id": analysis_id,
            "status": "started",
            "message": "Batch analysis started in background",
            "estimated_completion": (
                datetime.utcnow() + timedelta(minutes=5)
            ).isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@router.get("/health")
async def ai_analytics_health():
    """Health check for AI analytics service"""
    try:
        data_points_count = len(ai_analytics_service.data_points)
        patterns_count = len(ai_analytics_service.usage_patterns)
        insights_count = len(ai_analytics_service.cost_insights)
        models_count = len(ai_analytics_service.predictive_models)

        return {
            "status": "healthy",
            "service": "ai_analytics",
            "features": {
                "usage_pattern_analysis": "active",
                "performance_trend_analysis": "active",
                "cost_optimization_insights": "active",
                "predictive_modeling": "active",
                "real_time_metrics": "active",
                "dashboard_analytics": "active",
            },
            "data_summary": {
                "total_data_points": data_points_count,
                "usage_patterns": patterns_count,
                "cost_insights": insights_count,
                "predictive_models": models_count,
            },
            "available_metrics": [metric.value for metric in MetricType],
            "analytics_types": [analytics.value for analytics in AnalyticsType],
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
