"""
🔥 Bug Hotspot Detection API - Phase 4B.3

FastAPI endpoints для системы обнаружения проблемных зон в коде.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.security.auth import get_current_user
from domain.monitoring.bug_hotspot_detection_engine import (
    BugHotspot, HotspotAnalysisReport, HotspotSeverity,
    get_hotspot_detection_engine)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/hotspots", tags=["Bug Hotspot Detection"])


class HotspotAnalysisRequest(BaseModel):
    """Запрос на анализ hotspot'ов"""

    code_content: str = Field(..., description="Исходный код для анализа")
    file_path: str = Field(default="", description="Путь к файлу")
    analysis_type: str = Field(default="comprehensive", description="Тип анализа")


class QuickHotspotCheckRequest(BaseModel):
    """Запрос на быструю проверку hotspot'ов"""

    code_content: str = Field(..., description="Исходный код для проверки")
    file_path: str = Field(default="", description="Путь к файлу")


@router.post("/analyze")
async def analyze_code_hotspots(
    request: HotspotAnalysisRequest, current_user: dict = Depends(get_current_user)
):
    """Анализ проблемных зон в коде"""
    try:
        logger.info(f"🔥 Запрос анализа hotspot'ов для: {request.file_path}")

        # Получение движка детектора
        engine = await get_hotspot_detection_engine()

        # Выполнение анализа
        report = await engine.analyze_code_hotspots(
            request.code_content, request.file_path
        )

        # Подсчет hotspot'ов по категориям
        severity_breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        category_breakdown = {}

        for hotspot in report.hotspots:
            # По критичности
            severity = hotspot.severity.value
            if severity in severity_breakdown:
                severity_breakdown[severity] += 1

            # По категориям
            category = hotspot.category.value
            category_breakdown[category] = category_breakdown.get(category, 0) + 1

        # Формирование ответа
        response_data = {
            "report_id": report.report_id,
            "target": report.target,
            "analysis_results": {
                "total_hotspots": report.total_hotspots,
                "critical_hotspots": report.critical_hotspots,
                "overall_risk_score": report.overall_risk_score,
                "severity_breakdown": severity_breakdown,
                "category_breakdown": category_breakdown,
            },
            "hotspots": [
                {
                    "hotspot_id": h.hotspot_id,
                    "category": h.category.value,
                    "severity": h.severity.value,
                    "title": h.title,
                    "description": h.description,
                    "location": h.location,
                    "risk_score": h.risk_score,
                    "confidence": h.confidence,
                    "recommendations": h.recommendations,
                }
                for h in report.hotspots
            ],
            "recommendations": report.recommendations,
            "analysis_duration": report.analysis_duration,
            "created_at": report.created_at.isoformat(),
        }

        logger.info(f"✅ Анализ завершен: найдено {report.total_hotspots} hotspot'ов")
        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error(f"❌ Ошибка анализа hotspot'ов: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-check")
async def quick_hotspot_check(
    request: QuickHotspotCheckRequest, current_user: dict = Depends(get_current_user)
):
    """Быстрая проверка проблемных зон"""
    try:
        logger.info(f"⚡ Быстрая проверка hotspot'ов: {request.file_path}")

        # Получение движка детектора
        engine = await get_hotspot_detection_engine()

        # Выполнение быстрой проверки
        result = await engine.quick_hotspot_check(
            request.code_content, request.file_path
        )

        logger.info(
            f"✅ Быстрая проверка завершена: {result['potential_issues']} потенциальных проблем"
        )
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"❌ Ошибка быстрой проверки: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_hotspot_detection_metrics(current_user: dict = Depends(get_current_user)):
    """Получение метрик детектора hotspot'ов"""
    try:
        engine = await get_hotspot_detection_engine()
        metrics = engine.get_detection_metrics()
        return JSONResponse(content=metrics)

    except Exception as e:
        logger.error(f"Ошибка получения метрик: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_hotspot_detection_status(current_user: dict = Depends(get_current_user)):
    """Получение статуса детектора hotspot'ов"""
    try:
        engine = await get_hotspot_detection_engine()
        metrics = engine.get_detection_metrics()

        return JSONResponse(
            content={
                "engine_status": "active",
                "system_health": "healthy",
                "analyses_performed": metrics["metrics"]["analyses_performed"],
                "hotspots_detected": metrics["metrics"]["hotspots_detected"],
                "avg_risk_score": metrics["metrics"]["avg_risk_score"],
                "capabilities": [
                    "complexity_analysis",
                    "code_smell_detection",
                    "anti_pattern_detection",
                    "performance_issue_detection",
                    "maintainability_analysis",
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
            "service": "bug_hotspot_detection",
        }
    )
