"""
🔥 Bug Hotspot Detection Engine - Phase 4B.3

Система интеллектуального обнаружения проблемных зон в коде.
"""

import ast
import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class HotspotSeverity(Enum):
    """Уровни критичности hotspot'ов"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class HotspotCategory(Enum):
    """Категории проблемных зон"""

    COMPLEXITY = "complexity"
    CODE_SMELL = "code_smell"
    ANTI_PATTERN = "anti_pattern"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"


class CodeMetricType(Enum):
    """Типы метрик кода"""

    CYCLOMATIC_COMPLEXITY = "cyclomatic_complexity"
    LINES_OF_CODE = "lines_of_code"
    FUNCTION_LENGTH = "function_length"
    PARAMETER_COUNT = "parameter_count"


@dataclass
class CodeMetric:
    """Метрика кода"""

    metric_type: CodeMetricType
    value: float
    threshold: float
    severity: HotspotSeverity
    location: str
    description: str


@dataclass
class BugHotspot:
    """Проблемная зона в коде"""

    hotspot_id: str = field(default_factory=lambda: str(uuid4()))
    category: HotspotCategory = HotspotCategory.COMPLEXITY
    severity: HotspotSeverity = HotspotSeverity.MEDIUM
    title: str = ""
    description: str = ""
    location: str = ""
    file_path: str = ""
    risk_score: float = 0.0
    confidence: float = 0.8
    recommendations: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class HotspotAnalysisReport:
    """Отчет по анализу hotspot'ов"""

    report_id: str = field(default_factory=lambda: str(uuid4()))
    target: str = ""
    total_hotspots: int = 0
    critical_hotspots: int = 0
    overall_risk_score: float = 0.0
    hotspots: List[BugHotspot] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    analysis_duration: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


class BugHotspotDetectionEngine:
    """Движок обнаружения проблемных зон в коде"""

    def __init__(self):
        # Метрики движка
        self.metrics = {
            "analyses_performed": 0,
            "hotspots_detected": 0,
            "critical_hotspots": 0,
            "avg_risk_score": 0.0,
        }

    async def analyze_code_hotspots(
        self, code: str, file_path: str = ""
    ) -> HotspotAnalysisReport:
        """Анализ hotspot'ов в коде"""
        analysis_start = datetime.now()

        logger.info(f"🔥 Начало анализа hotspot'ов для: {file_path}")

        report = HotspotAnalysisReport(target=file_path or "code_analysis")
        all_hotspots = []

        # Анализ сложности кода
        complexity_hotspots = await self._analyze_complexity(code, file_path)
        all_hotspots.extend(complexity_hotspots)

        # Обнаружение code smells
        smell_hotspots = await self._detect_code_smells(code, file_path)
        all_hotspots.extend(smell_hotspots)

        # Заполнение отчета
        report.hotspots = all_hotspots
        report.total_hotspots = len(all_hotspots)
        report.critical_hotspots = len(
            [h for h in all_hotspots if h.severity == HotspotSeverity.CRITICAL]
        )
        report.overall_risk_score = self._calculate_overall_risk_score(all_hotspots)
        report.recommendations = self._generate_recommendations(all_hotspots)

        analysis_duration = (datetime.now() - analysis_start).total_seconds()
        report.analysis_duration = analysis_duration

        self._update_metrics(report)

        logger.info(f"✅ Анализ завершен: найдено {len(all_hotspots)} hotspot'ов")
        return report

    async def _analyze_complexity(self, code: str, file_path: str) -> List[BugHotspot]:
        """Анализ сложности кода"""
        hotspots = []
        lines = code.split("\n")
        loc = len([line for line in lines if line.strip()])

        # Проверка размера файла
        if loc > 300:
            hotspots.append(
                BugHotspot(
                    category=HotspotCategory.COMPLEXITY,
                    severity=HotspotSeverity.HIGH,
                    title="Большой файл",
                    description=f"Файл содержит {loc} строк кода",
                    location=file_path,
                    file_path=file_path,
                    risk_score=8.0,
                    recommendations=[
                        "Разбейте большой файл на несколько меньших",
                        "Используйте принцип единой ответственности",
                    ],
                )
            )

        # Поиск сложных функций через regex
        function_pattern = r"def\s+(\w+)\s*\([^)]*\):"
        functions = re.finditer(function_pattern, code)

        for func_match in functions:
            func_name = func_match.group(1)
            if len(func_name) > 30:  # Длинное имя функции
                line_number = code[: func_match.start()].count("\n") + 1
                hotspots.append(
                    BugHotspot(
                        category=HotspotCategory.MAINTAINABILITY,
                        severity=HotspotSeverity.LOW,
                        title="Длинное имя функции",
                        description=f"Функция {func_name} имеет слишком длинное имя",
                        location=f"{file_path}:line {line_number}",
                        file_path=file_path,
                        risk_score=3.0,
                        recommendations=[
                            "Используйте более краткие, но описательные имена"
                        ],
                    )
                )

        return hotspots

    async def _detect_code_smells(self, code: str, file_path: str) -> List[BugHotspot]:
        """Обнаружение code smells"""
        hotspots = []

        # Подавление исключений
        except_pattern = r"except.*?:\s*\n\s*pass"
        except_matches = re.finditer(except_pattern, code, re.MULTILINE)

        for match in except_matches:
            line_number = code[: match.start()].count("\n") + 1
            hotspots.append(
                BugHotspot(
                    category=HotspotCategory.ANTI_PATTERN,
                    severity=HotspotSeverity.HIGH,
                    title="Подавление исключений",
                    description="Исключения подавляются без обработки",
                    location=f"{file_path}:line {line_number}",
                    file_path=file_path,
                    risk_score=7.0,
                    recommendations=[
                        "Добавьте логирование исключений",
                        "Обработайте исключение соответствующим образом",
                    ],
                )
            )

        # Магические числа
        magic_pattern = r"\b(?<![\w\.])\d{2,}\b(?![\w\.])"
        magic_matches = re.finditer(magic_pattern, code)
        magic_count = len(list(magic_matches))

        if magic_count > 5:
            hotspots.append(
                BugHotspot(
                    category=HotspotCategory.CODE_SMELL,
                    severity=HotspotSeverity.MEDIUM,
                    title="Магические числа",
                    description=f"Найдено {magic_count} магических чисел в коде",
                    location=file_path,
                    file_path=file_path,
                    risk_score=5.0,
                    recommendations=[
                        "Выделите числовые константы в именованные константы",
                        "Используйте enum для связанных числовых значений",
                    ],
                )
            )

        return hotspots

    def _calculate_overall_risk_score(self, hotspots: List[BugHotspot]) -> float:
        """Вычисление общего риск-скора"""
        if not hotspots:
            return 0.0

        total_score = sum(h.risk_score for h in hotspots)
        return round(total_score / len(hotspots), 2)

    def _generate_recommendations(self, hotspots: List[BugHotspot]) -> List[str]:
        """Генерация общих рекомендаций"""
        recommendations = []

        critical_count = len(
            [h for h in hotspots if h.severity == HotspotSeverity.CRITICAL]
        )
        high_count = len([h for h in hotspots if h.severity == HotspotSeverity.HIGH])

        if critical_count > 0:
            recommendations.append(
                f"🚨 КРИТИЧНО: Найдено {critical_count} критических проблем"
            )

        if high_count > 0:
            recommendations.append(
                f"⚠️ ВЫСОКИЙ ПРИОРИТЕТ: {high_count} проблем требуют внимания"
            )

        recommendations.extend(
            [
                "🔍 Регулярно проводите анализ качества кода",
                "📚 Обучите команду лучшим практикам разработки",
            ]
        )

        return recommendations[:5]

    def _update_metrics(self, report: HotspotAnalysisReport):
        """Обновление метрик движка"""
        self.metrics["analyses_performed"] += 1
        self.metrics["hotspots_detected"] += report.total_hotspots
        self.metrics["critical_hotspots"] += report.critical_hotspots

        # Обновление среднего риск-скора
        total_analyses = self.metrics["analyses_performed"]
        current_avg = self.metrics["avg_risk_score"]
        new_avg = (
            (current_avg * (total_analyses - 1)) + report.overall_risk_score
        ) / total_analyses
        self.metrics["avg_risk_score"] = round(new_avg, 2)

    async def quick_hotspot_check(
        self, code: str, file_path: str = ""
    ) -> Dict[str, Any]:
        """Быстрая проверка hotspot'ов"""
        start_time = datetime.now()

        lines = code.split("\n")
        loc = len([line for line in lines if line.strip()])

        potential_issues = 0
        if loc > 200:
            potential_issues += 1
        if len(re.findall(r"except.*?:\s*\n\s*pass", code)) > 0:
            potential_issues += 2

        risk_level = (
            "high"
            if potential_issues >= 3
            else "medium" if potential_issues >= 2 else "low"
        )
        duration = (datetime.now() - start_time).total_seconds()

        return {
            "file_path": file_path,
            "lines_of_code": loc,
            "potential_issues": potential_issues,
            "risk_level": risk_level,
            "scan_duration": duration,
            "timestamp": datetime.now().isoformat(),
        }

    def get_detection_metrics(self) -> Dict[str, Any]:
        """Получение метрик детектора"""
        return {
            "engine_status": "active",
            "metrics": self.metrics,
            "last_updated": datetime.now().isoformat(),
        }


# Глобальный экземпляр
_hotspot_detection_engine: Optional[BugHotspotDetectionEngine] = None


async def get_hotspot_detection_engine() -> BugHotspotDetectionEngine:
    """Получение глобального экземпляра детектора hotspot'ов"""
    global _hotspot_detection_engine
    if _hotspot_detection_engine is None:
        _hotspot_detection_engine = BugHotspotDetectionEngine()
    return _hotspot_detection_engine
