"""
RFC Quality Enhancement Service
Улучшает качество генерации RFC документов с помощью AI анализа и оптимизации
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re
import json
from pathlib import Path

from models.generation import GeneratedRFC
from services.learning_pipeline_service import get_learning_service
from llm.llm_loader import load_llm

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """Метрики качества RFC документа."""
    structure_score: float  # 0.0-1.0
    completeness_score: float  # 0.0-1.0
    technical_depth_score: float  # 0.0-1.0
    clarity_score: float  # 0.0-1.0
    overall_score: float  # 0.0-1.0
    improvement_suggestions: List[str]
    missing_sections: List[str]
    weak_areas: List[str]

@dataclass
class EnhancementResult:
    """Результат улучшения RFC."""
    original_rfc: GeneratedRFC
    enhanced_rfc: GeneratedRFC
    quality_improvement: float  # Насколько улучшилось качество
    changes_made: List[str]
    metrics_before: QualityMetrics
    metrics_after: QualityMetrics

class RFCQualityEnhancer:
    """Сервис для улучшения качества RFC документов."""
    
    def __init__(self):
        """Инициализация сервиса."""
        self.llm = load_llm()
        self.learning_service = get_learning_service()
        
        # Шаблоны для анализа качества
        self.quality_patterns = {
            "technical_indicators": [
                "API", "database", "architecture", "scalability", "performance",
                "security", "authentication", "authorization", "encryption",
                "monitoring", "logging", "metrics", "SLA", "SLO", "error handling"
            ],
            "structure_indicators": [
                "## ", "### ", "#### ", "```", "- ", "1. ", "* "
            ],
            "quality_indicators": [
                "best practices", "trade-offs", "alternatives", "risks",
                "mitigation", "testing", "validation", "deployment"
            ]
        }
        
        # Минимальные требования к RFC
        self.min_requirements = {
            "min_sections": 8,
            "min_words_per_section": 100,
            "required_sections": [
                "Problem Statement", "Requirements", "Architecture", 
                "Implementation", "Security", "Monitoring"
            ],
            "min_technical_terms": 10
        }
        
        logger.info("RFCQualityEnhancer initialized")

    def analyze_rfc_quality(self, content: str, title: str = "") -> QualityMetrics:
        """Анализирует качество RFC документа."""
        logger.info(f"Analyzing RFC quality for: {title}")
        
        if not content:
            return QualityMetrics(
                structure_score=0.0,
                completeness_score=0.0,
                technical_depth_score=0.0,
                clarity_score=0.0,
                overall_score=0.0,
                improvement_suggestions=["Content is empty"],
                missing_sections=self.min_requirements["required_sections"],
                weak_areas=["All areas"]
            )
        
        # 1. Анализ структуры
        structure_score = self._analyze_structure(content)
        
        # 2. Анализ полноты
        completeness_score = self._analyze_completeness(content)
        
        # 3. Анализ технической глубины
        technical_depth_score = self._analyze_technical_depth(content)
        
        # 4. Анализ ясности (упрощенный)
        clarity_score = self._analyze_clarity(content)
        
        # 5. Общий счет
        overall_score = (
            structure_score * 0.25 +
            completeness_score * 0.30 +
            technical_depth_score * 0.25 +
            clarity_score * 0.20
        )
        
        # 6. Генерация рекомендаций
        improvement_suggestions = self._generate_improvement_suggestions(
            content, structure_score, completeness_score, 
            technical_depth_score, clarity_score
        )
        
        # 7. Поиск недостающих секций
        missing_sections = self._find_missing_sections(content)
        
        # 8. Определение слабых мест
        weak_areas = self._identify_weak_areas(
            structure_score, completeness_score, 
            technical_depth_score, clarity_score
        )
        
        metrics = QualityMetrics(
            structure_score=structure_score,
            completeness_score=completeness_score,
            technical_depth_score=technical_depth_score,
            clarity_score=clarity_score,
            overall_score=overall_score,
            improvement_suggestions=improvement_suggestions,
            missing_sections=missing_sections,
            weak_areas=weak_areas
        )
        
        logger.info(f"RFC quality analysis completed. Overall score: {overall_score:.2f}")
        return metrics

    def _analyze_structure(self, content: str) -> float:
        """Анализирует структуру документа."""
        if not content:
            return 0.0
        
        score = 0.0
        
        # Проверяем наличие заголовков разных уровней
        h2_count = len(re.findall(r'^## ', content, re.MULTILINE))
        h3_count = len(re.findall(r'^### ', content, re.MULTILINE))
        
        # Баллы за структуру
        if h2_count >= 6:  # Минимум 6 основных секций
            score += 0.4
        elif h2_count >= 4:
            score += 0.2
        
        if h3_count >= 10:  # Подсекции для детализации
            score += 0.3
        elif h3_count >= 5:
            score += 0.15
        
        # Проверяем наличие списков и кода
        lists_count = len(re.findall(r'^- ', content, re.MULTILINE))
        code_blocks = len(re.findall(r'```', content))
        
        if lists_count >= 10:
            score += 0.2
        elif lists_count >= 5:
            score += 0.1
        
        if code_blocks >= 4:
            score += 0.1
        
        return min(1.0, score)

    def _analyze_completeness(self, content: str) -> float:
        """Анализирует полноту документа."""
        if not content:
            return 0.0
        
        score = 0.0
        
        # Проверяем наличие обязательных секций
        required_found = 0
        for required_section in self.min_requirements["required_sections"]:
            if required_section.lower() in content.lower():
                required_found += 1
        
        score += (required_found / len(self.min_requirements["required_sections"])) * 0.5
        
        # Проверяем длину контента
        word_count = len(content.split())
        if word_count >= 2000:
            score += 0.3
        elif word_count >= 1000:
            score += 0.2
        elif word_count >= 500:
            score += 0.1
        
        # Проверяем разнообразие контента
        if "```" in content:  # Есть примеры кода
            score += 0.1
        if len(re.findall(r'^- ', content, re.MULTILINE)) >= 5:  # Есть списки
            score += 0.1
        
        return min(1.0, score)

    def _analyze_technical_depth(self, content: str) -> float:
        """Анализирует техническую глубину документа."""
        if not content:
            return 0.0
        
        content_lower = content.lower()
        
        # Подсчитываем технические термины
        technical_terms_found = 0
        for term in self.quality_patterns["technical_indicators"]:
            if term.lower() in content_lower:
                technical_terms_found += 1
        
        # Подсчитываем индикаторы качества
        quality_indicators_found = 0
        for indicator in self.quality_patterns["quality_indicators"]:
            if indicator.lower() in content_lower:
                quality_indicators_found += 1
        
        # Рассчитываем счет
        technical_score = min(1.0, technical_terms_found / len(self.quality_patterns["technical_indicators"]))
        quality_score = min(1.0, quality_indicators_found / len(self.quality_patterns["quality_indicators"]))
        
        return (technical_score * 0.6 + quality_score * 0.4)

    def _analyze_clarity(self, content: str) -> float:
        """Анализирует ясность документа (упрощенная версия)."""
        if not content:
            return 0.0
        
        score = 0.0
        
        # Проверяем среднюю длину предложений
        sentences = re.split(r'[.!?]+', content)
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if 10 <= avg_sentence_length <= 25:  # Оптимальная длина
                score += 0.3
            elif avg_sentence_length <= 35:
                score += 0.2
        
        # Проверяем использование заголовков
        if len(re.findall(r'^#+', content, re.MULTILINE)) >= 5:
            score += 0.3
        
        # Проверяем наличие примеров
        if "example" in content.lower() or "например" in content.lower():
            score += 0.2
        
        # Проверяем наличие объяснений
        if "because" in content.lower() or "потому что" in content.lower():
            score += 0.2
        
        return min(1.0, score)

    def _generate_improvement_suggestions(
        self, 
        content: str, 
        structure_score: float,
        completeness_score: float,
        technical_depth_score: float,
        clarity_score: float
    ) -> List[str]:
        """Генерирует рекомендации по улучшению."""
        suggestions = []
        
        if structure_score < 0.7:
            suggestions.append("Улучшить структуру документа: добавить больше заголовков и подразделов")
            suggestions.append("Добавить списки и примеры кода для лучшей читаемости")
        
        if completeness_score < 0.7:
            suggestions.append("Расширить содержание: добавить больше деталей в каждую секцию")
            suggestions.append("Добавить недостающие обязательные секции")
        
        if technical_depth_score < 0.7:
            suggestions.append("Углубить техническое содержание: добавить больше технических деталей")
            suggestions.append("Включить рассмотрение альтернатив и компромиссов")
        
        if clarity_score < 0.7:
            suggestions.append("Улучшить ясность изложения: упростить сложные предложения")
            suggestions.append("Добавить определения технических терминов")
        
        return suggestions

    def _find_missing_sections(self, content: str) -> List[str]:
        """Находит недостающие секции."""
        missing = []
        content_lower = content.lower()
        
        for required_section in self.min_requirements["required_sections"]:
            if required_section.lower() not in content_lower:
                missing.append(required_section)
        
        return missing

    def _identify_weak_areas(
        self,
        structure_score: float,
        completeness_score: float,
        technical_depth_score: float,
        clarity_score: float
    ) -> List[str]:
        """Определяет слабые области документа."""
        weak_areas = []
        threshold = 0.6
        
        if structure_score < threshold:
            weak_areas.append("Структура документа")
        if completeness_score < threshold:
            weak_areas.append("Полнота содержания")
        if technical_depth_score < threshold:
            weak_areas.append("Техническая глубина")
        if clarity_score < threshold:
            weak_areas.append("Ясность изложения")
        
        return weak_areas

    async def enhance_rfc(self, rfc: GeneratedRFC) -> EnhancementResult:
        """Улучшает RFC документ."""
        logger.info(f"Enhancing RFC: {rfc.title}")
        
        # 1. Анализируем текущее качество
        metrics_before = await self.analyze_rfc_quality(rfc.full_content, rfc.title)
        
        # 2. Если качество уже высокое, возвращаем оригинал
        if metrics_before.overall_score >= 0.85:
            logger.info("RFC quality is already high, no enhancement needed")
            return EnhancementResult(
                original_rfc=rfc,
                enhanced_rfc=rfc,
                quality_improvement=0.0,
                changes_made=["No changes needed - quality already high"],
                metrics_before=metrics_before,
                metrics_after=metrics_before
            )
        
        # 3. Генерируем улучшенную версию
        enhanced_content = await self._generate_enhanced_content(
            rfc, metrics_before
        )
        
        # 4. Создаем улучшенный RFC
        enhanced_rfc = GeneratedRFC(
            id=rfc.id + "_enhanced",
            session_id=rfc.session_id,
            title=rfc.title,
            summary=rfc.summary,
            sections=rfc.sections,
            full_content=enhanced_content,
            metadata={
                **rfc.metadata,
                "enhanced": True,
                "enhancement_date": datetime.now().isoformat(),
                "original_quality_score": metrics_before.overall_score
            },
            sources_used=rfc.sources_used + ["Quality Enhancement AI"],
            created_at=datetime.now()
        )
        
        # 5. Анализируем качество после улучшения
        metrics_after = await self.analyze_rfc_quality(enhanced_content, rfc.title)
        
        # 6. Определяем изменения
        changes_made = self._identify_changes_made(metrics_before, metrics_after)
        
        quality_improvement = metrics_after.overall_score - metrics_before.overall_score
        
        logger.info(f"RFC enhancement completed. Quality improved by: {quality_improvement:.2f}")
        
        return EnhancementResult(
            original_rfc=rfc,
            enhanced_rfc=enhanced_rfc,
            quality_improvement=quality_improvement,
            changes_made=changes_made,
            metrics_before=metrics_before,
            metrics_after=metrics_after
        )

    async def _generate_enhanced_content(
        self, 
        rfc: GeneratedRFC, 
        metrics: QualityMetrics
    ) -> str:
        """Генерирует улучшенное содержание RFC."""
        
        enhancement_prompt = f"""
Улучши этот RFC документ на основе анализа качества.

Оригинальный RFC:
Заголовок: {rfc.title}
Содержание: {rfc.full_content}

Анализ качества:
- Общий счет: {metrics.overall_score:.2f}
- Структура: {metrics.structure_score:.2f}
- Полнота: {metrics.completeness_score:.2f}
- Техническая глубина: {metrics.technical_depth_score:.2f}
- Ясность: {metrics.clarity_score:.2f}

Рекомендации по улучшению:
{chr(10).join(f"- {suggestion}" for suggestion in metrics.improvement_suggestions)}

Недостающие секции:
{chr(10).join(f"- {section}" for section in metrics.missing_sections)}

Слабые области:
{chr(10).join(f"- {area}" for area in metrics.weak_areas)}

Создай улучшенную версию RFC, которая:
1. Исправляет выявленные недостатки
2. Добавляет недостающие секции
3. Углубляет техническое содержание
4. Улучшает структуру и ясность

Верни только улучшенный RFC в формате Markdown:
"""
        
        try:
            enhanced_content = await self.llm.generate(enhancement_prompt)
            return enhanced_content
        except Exception as e:
            logger.error(f"Failed to generate enhanced content: {e}")
            return rfc.full_content or ""

    def _identify_changes_made(
        self, 
        metrics_before: QualityMetrics, 
        metrics_after: QualityMetrics
    ) -> List[str]:
        """Определяет какие изменения были сделаны."""
        changes = []
        
        if metrics_after.structure_score > metrics_before.structure_score + 0.1:
            changes.append("Улучшена структура документа")
        
        if metrics_after.completeness_score > metrics_before.completeness_score + 0.1:
            changes.append("Расширено содержание")
        
        if metrics_after.technical_depth_score > metrics_before.technical_depth_score + 0.1:
            changes.append("Углублена техническая детализация")
        
        if metrics_after.clarity_score > metrics_before.clarity_score + 0.1:
            changes.append("Улучшена ясность изложения")
        
        if len(metrics_after.missing_sections) < len(metrics_before.missing_sections):
            changes.append("Добавлены недостающие секции")
        
        if not changes:
            changes.append("Выполнены общие улучшения качества")
        
        return changes

# Глобальный экземпляр сервиса
_quality_enhancer = None

def get_rfc_quality_enhancer() -> RFCQualityEnhancer:
    """Получить глобальный экземпляр сервиса улучшения качества RFC."""
    global _quality_enhancer
    if _quality_enhancer is None:
        _quality_enhancer = RFCQualityEnhancer()
    return _quality_enhancer 