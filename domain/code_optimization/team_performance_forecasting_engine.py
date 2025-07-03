"""
📊 Team Performance Forecasting Engine - Phase 4B.4

Система интеллектуального прогнозирования производительности команды разработки.
"""

import asyncio
import logging
import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


class TeamMetricType(Enum):
    """Типы метрик команды"""

    VELOCITY = "velocity"
    CYCLE_TIME = "cycle_time"
    QUALITY_SCORE = "quality_score"
    BUG_RATE = "bug_rate"


class PerformanceTrend(Enum):
    """Тренды производительности"""

    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


class ForecastAccuracy(Enum):
    """Уровни точности прогноза"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


class TeamRisk(Enum):
    """Уровни риска для команды"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


@dataclass
class TeamMember:
    """Информация о члене команды"""

    member_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    role: str = ""
    experience_level: str = ""
    performance_score: float = 0.0
    availability: float = 1.0


@dataclass
class PerformanceMetric:
    """Метрика производительности"""

    metric_type: TeamMetricType
    value: float
    timestamp: datetime
    unit: str = ""


@dataclass
class TeamPerformanceForecast:
    """Прогноз производительности команды"""

    forecast_id: str = field(default_factory=lambda: str(uuid4()))
    team_id: str = ""
    forecast_period_days: int = 30
    predicted_velocity: float = 0.0
    predicted_quality_score: float = 0.0
    predicted_bug_rate: float = 0.0
    confidence_level: ForecastAccuracy = ForecastAccuracy.MEDIUM
    risk_level: TeamRisk = TeamRisk.MEDIUM
    trend: PerformanceTrend = PerformanceTrend.STABLE
    recommendations: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TeamAnalysisReport:
    """Отчет по анализу команды"""

    report_id: str = field(default_factory=lambda: str(uuid4()))
    team_id: str = ""
    current_performance_score: float = 0.0
    performance_trend: PerformanceTrend = PerformanceTrend.STABLE
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    improvement_opportunities: List[str] = field(default_factory=list)
    forecasts: List[TeamPerformanceForecast] = field(default_factory=list)
    team_metrics: Dict[str, float] = field(default_factory=dict)
    analysis_duration: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


class VelocityAnalyzer:
    """Анализатор скорости разработки команды"""

    async def analyze_velocity_trends(
        self, velocity_data: List[PerformanceMetric]
    ) -> Dict[str, Any]:
        """Анализ трендов скорости разработки"""
        if len(velocity_data) < 3:
            return {
                "trend": PerformanceTrend.STABLE,
                "average_velocity": 0.0,
                "velocity_variance": 0.0,
                "confidence": ForecastAccuracy.UNCERTAIN,
            }

        # Сортировка по времени
        sorted_data = sorted(velocity_data, key=lambda x: x.timestamp)
        velocities = [metric.value for metric in sorted_data]

        # Вычисление статистик
        avg_velocity = statistics.mean(velocities)
        velocity_variance = (
            statistics.variance(velocities) if len(velocities) > 1 else 0
        )

        # Анализ тренда
        trend = self._calculate_trend(velocities)
        confidence = self._calculate_confidence(velocities, velocity_variance)

        return {
            "trend": trend,
            "average_velocity": avg_velocity,
            "velocity_variance": velocity_variance,
            "confidence": confidence,
            "velocity_stability": self._calculate_stability(velocities),
        }

    async def predict_future_velocity(
        self, historical_data: List[PerformanceMetric], periods_ahead: int = 3
    ) -> Dict[str, Any]:
        """Прогнозирование будущей скорости"""
        if len(historical_data) < 3:
            return {
                "predicted_velocity": 0.0,
                "confidence": ForecastAccuracy.UNCERTAIN,
                "prediction_range": (0.0, 0.0),
            }

        velocities = [
            metric.value
            for metric in sorted(historical_data, key=lambda x: x.timestamp)
        ]

        # Простой линейный тренд
        predicted_velocity = self._linear_trend_prediction(velocities, periods_ahead)

        # Расчет доверительного интервала
        variance = statistics.variance(velocities) if len(velocities) > 1 else 0
        std_dev = math.sqrt(variance)

        prediction_range = (
            max(0, predicted_velocity - 2 * std_dev),
            predicted_velocity + 2 * std_dev,
        )

        confidence = self._calculate_confidence(velocities, variance)

        return {
            "predicted_velocity": predicted_velocity,
            "confidence": confidence,
            "prediction_range": prediction_range,
            "trend_direction": self._calculate_trend(velocities),
        }

    def _calculate_trend(self, values: List[float]) -> PerformanceTrend:
        """Вычисление тренда"""
        if len(values) < 3:
            return PerformanceTrend.STABLE

        recent_values = values[-min(6, len(values)) :]

        # Простая линейная регрессия
        n = len(recent_values)
        x = list(range(n))
        y = recent_values

        # Коэффициент наклона
        if n > 1:
            slope = (n * sum(i * y[i] for i in range(n)) - sum(x) * sum(y)) / (
                n * sum(i * i for i in range(n)) - sum(x) ** 2
            )
        else:
            slope = 0

        # Определение тренда
        if slope > 0.1:
            return PerformanceTrend.IMPROVING
        elif slope < -0.1:
            return PerformanceTrend.DECLINING
        else:
            # Проверяем волатильность
            variance = (
                statistics.variance(recent_values) if len(recent_values) > 1 else 0
            )
            avg = statistics.mean(recent_values)
            cv = (math.sqrt(variance) / avg) if avg > 0 else 0

            if cv > 0.3:
                return PerformanceTrend.VOLATILE
            else:
                return PerformanceTrend.STABLE

    def _calculate_confidence(
        self, values: List[float], variance: float
    ) -> ForecastAccuracy:
        """Вычисление уверенности прогноза"""
        if len(values) < 3:
            return ForecastAccuracy.UNCERTAIN

        avg = statistics.mean(values)
        cv = (math.sqrt(variance) / avg) if avg > 0 else 1

        if cv < 0.1:
            return ForecastAccuracy.HIGH
        elif cv < 0.25:
            return ForecastAccuracy.MEDIUM
        elif cv < 0.5:
            return ForecastAccuracy.LOW
        else:
            return ForecastAccuracy.UNCERTAIN

    def _calculate_stability(self, values: List[float]) -> float:
        """Вычисление стабильности (0-1)"""
        if len(values) < 2:
            return 1.0

        variance = statistics.variance(values)
        avg = statistics.mean(values)
        cv = (math.sqrt(variance) / avg) if avg > 0 else 1

        return max(0, 1 - cv)

    def _linear_trend_prediction(
        self, values: List[float], periods_ahead: int
    ) -> float:
        """Простое прогнозирование на основе линейного тренда"""
        if len(values) < 2:
            return values[0] if values else 0.0

        n = len(values)
        x = list(range(n))
        y = values

        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return y_mean

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        future_x = n + periods_ahead - 1
        prediction = slope * future_x + intercept

        return max(0, prediction)


class TeamPerformanceForecastingEngine:
    """Движок прогнозирования производительности команды"""

    def __init__(self):
        self.velocity_analyzer = VelocityAnalyzer()

        # Метрики движка
        self.metrics = {
            "forecasts_generated": 0,
            "teams_analyzed": 0,
            "average_forecast_accuracy": 0.0,
            "total_recommendations": 0,
        }

    async def analyze_team_performance(
        self,
        team_id: str,
        historical_metrics: Dict[str, List[PerformanceMetric]],
        team_members: List[TeamMember] = None,
    ) -> TeamAnalysisReport:
        """Комплексный анализ производительности команды"""
        analysis_start = datetime.now()

        try:
            logger.info(f"📊 Начало анализа команды: {team_id}")

            report = TeamAnalysisReport(team_id=team_id)

            # Анализ скорости разработки
            velocity_analysis = await self.velocity_analyzer.analyze_velocity_trends(
                historical_metrics.get("velocity", [])
            )

            # Генерация прогнозов
            forecasts = await self._generate_forecasts(team_id, historical_metrics)

            # Простой расчет производительности
            current_performance = self._calculate_current_performance(velocity_analysis)

            # Заполнение отчета
            report.current_performance_score = current_performance
            report.performance_trend = velocity_analysis.get(
                "trend", PerformanceTrend.STABLE
            )
            report.forecasts = forecasts
            report.team_metrics = {
                "average_velocity": velocity_analysis.get("average_velocity", 0.0),
                "velocity_stability": velocity_analysis.get("velocity_stability", 0.0),
            }

            # Рекомендации
            report.improvement_opportunities = [
                "Регулярно отслеживайте метрики производительности команды",
                "Проводите ретроспективы для выявления возможностей улучшения",
            ]

            analysis_duration = (datetime.now() - analysis_start).total_seconds()
            report.analysis_duration = analysis_duration

            # Обновление метрик
            self.metrics["teams_analyzed"] += 1
            self.metrics["forecasts_generated"] += len(forecasts)

            logger.info(
                f"✅ Анализ команды завершен: {len(forecasts)} прогнозов сгенерировано"
            )
            return report

        except Exception as e:
            logger.error(f"❌ Ошибка анализа команды: {e}")
            raise

    def _calculate_current_performance(self, velocity_analysis: Dict) -> float:
        """Расчет текущей производительности (0-10)"""
        velocity_score = min(10, velocity_analysis.get("average_velocity", 0) / 10)
        return min(10.0, max(0.0, velocity_score))

    async def _generate_forecasts(
        self, team_id: str, historical_metrics: Dict[str, List[PerformanceMetric]]
    ) -> List[TeamPerformanceForecast]:
        """Генерация прогнозов"""
        forecasts = []

        # Прогноз на разные периоды
        forecast_periods = [7, 14, 30]

        for period in forecast_periods:
            forecast = TeamPerformanceForecast(
                team_id=team_id, forecast_period_days=period
            )

            # Прогноз скорости
            velocity_data = historical_metrics.get("velocity", [])
            if velocity_data:
                velocity_forecast = (
                    await self.velocity_analyzer.predict_future_velocity(
                        velocity_data, periods_ahead=period // 7
                    )
                )
                forecast.predicted_velocity = velocity_forecast.get(
                    "predicted_velocity", 0.0
                )
                forecast.confidence_level = velocity_forecast.get(
                    "confidence", ForecastAccuracy.MEDIUM
                )

            # Простые прогнозы качества
            forecast.predicted_quality_score = 7.5  # Средняя оценка
            forecast.predicted_bug_rate = 2.0  # Низкая частота багов

            # Оценка рисков
            forecast.risk_level = self._assess_risk_level(forecast)
            forecast.recommendations = self._generate_forecast_recommendations(forecast)

            forecasts.append(forecast)

        return forecasts

    def _assess_risk_level(self, forecast: TeamPerformanceForecast) -> TeamRisk:
        """Оценка уровня риска"""
        risk_score = 0

        if forecast.predicted_velocity < 5:
            risk_score += 2

        if forecast.predicted_quality_score < 6.0:
            risk_score += 3

        if forecast.confidence_level == ForecastAccuracy.UNCERTAIN:
            risk_score += 2

        # Определение уровня риска
        if risk_score >= 6:
            return TeamRisk.CRITICAL
        elif risk_score >= 4:
            return TeamRisk.HIGH
        elif risk_score >= 2:
            return TeamRisk.MEDIUM
        elif risk_score >= 1:
            return TeamRisk.LOW
        else:
            return TeamRisk.MINIMAL

    def _generate_forecast_recommendations(
        self, forecast: TeamPerformanceForecast
    ) -> List[str]:
        """Генерация рекомендаций для прогноза"""
        recommendations = []

        if forecast.risk_level in [TeamRisk.CRITICAL, TeamRisk.HIGH]:
            recommendations.append("Требуется немедленное внимание руководства")

        if forecast.predicted_velocity < 5:
            recommendations.append("Рассмотрите упрощение задач или увеличение команды")

        recommendations.append("Отслеживайте ключевые метрики производительности")

        return recommendations

    async def quick_team_assessment(
        self, team_id: str, basic_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Быстрая оценка команды"""
        start_time = datetime.now()

        velocity = basic_metrics.get("velocity", 0.0)
        quality = basic_metrics.get("quality_score", 7.0)

        # Расчет общей оценки
        performance_score = min(10, velocity / 10) * 0.6 + quality * 0.4

        # Определение уровня риска
        if performance_score >= 8.0:
            risk_level = TeamRisk.MINIMAL
        elif performance_score >= 6.5:
            risk_level = TeamRisk.LOW
        elif performance_score >= 5.0:
            risk_level = TeamRisk.MEDIUM
        else:
            risk_level = TeamRisk.HIGH

        duration = (datetime.now() - start_time).total_seconds()

        return {
            "team_id": team_id,
            "performance_score": round(performance_score, 2),
            "risk_level": risk_level.value,
            "quick_recommendations": [
                "Проведите полный анализ для детальных рекомендаций",
                "Отслеживайте ключевые метрики команды",
            ],
            "assessment_duration": duration,
            "timestamp": datetime.now().isoformat(),
        }

    def get_forecasting_metrics(self) -> Dict[str, Any]:
        """Получение метрик движка прогнозирования"""
        return {
            "engine_status": "active",
            "metrics": self.metrics,
            "capabilities": {
                "velocity_forecasting": True,
                "risk_assessment": True,
                "team_analysis": True,
            },
            "last_updated": datetime.now().isoformat(),
        }


# Глобальный экземпляр
_forecasting_engine: Optional[TeamPerformanceForecastingEngine] = None


async def get_team_performance_forecasting_engine() -> TeamPerformanceForecastingEngine:
    """Получение глобального экземпляра движка прогнозирования"""
    global _forecasting_engine
    if _forecasting_engine is None:
        _forecasting_engine = TeamPerformanceForecastingEngine()
    return _forecasting_engine
