"""
📊 Team Performance Forecasting API - Phase 4B.4

FastAPI endpoints для системы прогнозирования производительности команды.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.security.auth import get_current_user
from domain.code_optimization.team_performance_forecasting_engine import (
    PerformanceMetric, TeamAnalysisReport, TeamMember, TeamMetricType,
    TeamPerformanceForecast, TeamRisk, get_team_performance_forecasting_engine)

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/v1/team-performance", tags=["Team Performance Forecasting"]
)


class TeamAnalysisRequest(BaseModel):
    """Запрос на анализ производительности команды"""

    team_id: str = Field(..., description="ID команды")
    historical_metrics: Dict[str, List[Dict]] = Field(
        default={}, description="Исторические метрики"
    )
    team_members: List[Dict] = Field(default=[], description="Члены команды")


class QuickAssessmentRequest(BaseModel):
    """Запрос на быструю оценку команды"""

    team_id: str = Field(..., description="ID команды")
    basic_metrics: Dict[str, float] = Field(..., description="Базовые метрики")


@router.post("/analyze")
async def analyze_team_performance(
    request: TeamAnalysisRequest, current_user: dict = Depends(get_current_user)
):
    """Комплексный анализ производительности команды"""
    try:
        logger.info(f"📊 Запрос анализа команды: {request.team_id}")

        # Получение движка прогнозирования
        engine = await get_team_performance_forecasting_engine()

        # Конвертация метрик
        converted_metrics = {}
        for metric_name, metric_list in request.historical_metrics.items():
            if metric_name in ["velocity", "quality", "bugs"]:
                converted_metrics[metric_name] = [
                    PerformanceMetric(
                        metric_type=(
                            TeamMetricType.VELOCITY
                            if metric_name == "velocity"
                            else TeamMetricType.QUALITY_SCORE
                        ),
                        value=m.get("value", 0.0),
                        timestamp=datetime.fromisoformat(
                            m.get("timestamp", datetime.now().isoformat())
                        ),
                        unit=m.get("unit", ""),
                    )
                    for m in metric_list
                ]

        # Конвертация членов команды
        team_members = []
        for member_data in request.team_members:
            member = TeamMember(
                name=member_data.get("name", ""),
                role=member_data.get("role", ""),
                experience_level=member_data.get("experience_level", ""),
                performance_score=member_data.get("performance_score", 0.0),
                availability=member_data.get("availability", 1.0),
            )
            team_members.append(member)

        # Выполнение анализа
        report = await engine.analyze_team_performance(
            request.team_id, converted_metrics, team_members
        )

        # Формирование ответа
        response_data = {
            "report_id": report.report_id,
            "team_id": report.team_id,
            "analysis_results": {
                "current_performance_score": report.current_performance_score,
                "performance_trend": report.performance_trend.value,
                "strengths": report.strengths,
                "weaknesses": report.weaknesses,
                "improvement_opportunities": report.improvement_opportunities,
            },
            "forecasts": [
                {
                    "forecast_id": f.forecast_id,
                    "forecast_period_days": f.forecast_period_days,
                    "predicted_velocity": f.predicted_velocity,
                    "predicted_quality_score": f.predicted_quality_score,
                    "predicted_bug_rate": f.predicted_bug_rate,
                    "confidence_level": f.confidence_level.value,
                    "risk_level": f.risk_level.value,
                    "trend": f.trend.value,
                    "recommendations": f.recommendations,
                    "risk_factors": f.risk_factors,
                }
                for f in report.forecasts
            ],
            "team_metrics": report.team_metrics,
            "analysis_duration": report.analysis_duration,
            "created_at": report.created_at.isoformat(),
        }

        logger.info(f"✅ Анализ команды завершен: {len(report.forecasts)} прогнозов")
        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error(f"❌ Ошибка анализа команды: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-assessment")
async def quick_team_assessment(
    request: QuickAssessmentRequest, current_user: dict = Depends(get_current_user)
):
    """Быстрая оценка производительности команды"""
    try:
        logger.info(f"⚡ Быстрая оценка команды: {request.team_id}")

        # Получение движка прогнозирования
        engine = await get_team_performance_forecasting_engine()

        # Выполнение быстрой оценки
        result = await engine.quick_team_assessment(
            request.team_id, request.basic_metrics
        )

        logger.info(f"✅ Быстрая оценка завершена: {result['performance_score']}/10")
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"❌ Ошибка быстрой оценки: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_forecasting_metrics(current_user: dict = Depends(get_current_user)):
    """Получение метрик движка прогнозирования"""
    try:
        engine = await get_team_performance_forecasting_engine()
        metrics = engine.get_forecasting_metrics()
        return JSONResponse(content=metrics)

    except Exception as e:
        logger.error(f"Ошибка получения метрик: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_forecasting_status(current_user: dict = Depends(get_current_user)):
    """Получение статуса движка прогнозирования"""
    try:
        engine = await get_team_performance_forecasting_engine()
        metrics = engine.get_forecasting_metrics()

        return JSONResponse(
            content={
                "engine_status": "active",
                "system_health": "healthy",
                "teams_analyzed": metrics["metrics"]["teams_analyzed"],
                "forecasts_generated": metrics["metrics"]["forecasts_generated"],
                "average_forecast_accuracy": metrics["metrics"][
                    "average_forecast_accuracy"
                ],
                "capabilities": [
                    "velocity_forecasting",
                    "performance_trend_analysis",
                    "risk_assessment",
                    "team_composition_analysis",
                    "improvement_recommendations",
                ],
                "last_updated": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Проверка здоровья системы"""
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "team_performance_forecasting",
        }
    )
