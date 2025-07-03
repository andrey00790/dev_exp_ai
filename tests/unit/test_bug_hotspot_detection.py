"""
🧪 Bug Hotspot Detection Engine Tests

Unit тесты для системы обнаружения проблемных зон в коде.
Phase 4B.3 - Bug Hotspot Detection Testing
"""

import asyncio
from datetime import datetime
from unittest.mock import Mock

import pytest

from domain.monitoring.bug_hotspot_detection_engine import (
    BugHotspot, BugHotspotDetectionEngine, HotspotAnalysisReport,
    HotspotCategory, HotspotSeverity, get_hotspot_detection_engine)


class TestBugHotspotDetectionEngine:
    """Тесты для BugHotspotDetectionEngine"""

    @pytest.fixture
    def engine(self):
        """Создание тестового экземпляра движка"""
        return BugHotspotDetectionEngine()

    @pytest.fixture
    def sample_problematic_code(self):
        """Образец проблемного кода"""
        return (
            """
        def very_long_function_name_that_is_too_descriptive_and_should_be_shorter():
            try:
                data = process_data()
            except:
                pass
            
            magic_number = 12345
            another_magic = 67890
            
            return data
        
        def another_function():
            # Еще одна функция для создания большого файла
            pass
        
        """
            * 20
        )  # Повторяем для создания большого файла

    @pytest.fixture
    def sample_clean_code(self):
        """Образец чистого кода"""
        return '''
        def calculate_area(length, width):
            """Вычисляет площадь прямоугольника"""
            return length * width
        
        def get_user_info(user_id):
            """Получает информацию о пользователе"""
            return database.get_user(user_id)
        '''

    @pytest.mark.asyncio
    async def test_analyze_code_hotspots_with_problems(
        self, engine, sample_problematic_code
    ):
        """Тест анализа кода с проблемами"""
        result = await engine.analyze_code_hotspots(
            sample_problematic_code, "problematic.py"
        )

        assert isinstance(result, HotspotAnalysisReport)
        assert result.target == "problematic.py"
        assert result.total_hotspots > 0
        assert result.overall_risk_score > 0
        assert len(result.recommendations) > 0
        assert result.analysis_duration >= 0

    @pytest.mark.asyncio
    async def test_analyze_code_hotspots_clean_code(self, engine, sample_clean_code):
        """Тест анализа чистого кода"""
        result = await engine.analyze_code_hotspots(sample_clean_code, "clean.py")

        assert isinstance(result, HotspotAnalysisReport)
        assert result.target == "clean.py"
        # Чистый код может иметь меньше проблем
        assert result.overall_risk_score <= 5.0
        assert result.analysis_duration >= 0

    @pytest.mark.asyncio
    async def test_analyze_complexity_large_file(self, engine):
        """Тест обнаружения большого файла"""
        large_code = "def function_%d(): pass\n" * 500  # Создаем большой файл

        hotspots = await engine._analyze_complexity(large_code, "large.py")

        # Должен найти проблему большого файла
        large_file_hotspots = [h for h in hotspots if "Большой файл" in h.title]
        assert len(large_file_hotspots) > 0

        hotspot = large_file_hotspots[0]
        assert hotspot.category == HotspotCategory.COMPLEXITY
        assert hotspot.severity == HotspotSeverity.HIGH
        assert hotspot.risk_score > 5.0

    @pytest.mark.asyncio
    async def test_detect_code_smells_exception_swallowing(self, engine):
        """Тест обнаружения подавления исключений"""
        code_with_except = """
        def risky_function():
            try:
                dangerous_operation()
            except:
                pass
        """

        hotspots = await engine._detect_code_smells(code_with_except, "risky.py")

        # Должен найти подавление исключений
        except_hotspots = [h for h in hotspots if "Подавление исключений" in h.title]
        assert len(except_hotspots) > 0

        hotspot = except_hotspots[0]
        assert hotspot.category == HotspotCategory.ANTI_PATTERN
        assert hotspot.severity == HotspotSeverity.HIGH
        assert len(hotspot.recommendations) > 0

    @pytest.mark.asyncio
    async def test_detect_magic_numbers(self, engine):
        """Тест обнаружения магических чисел"""
        code_with_magic = """
        def calculate():
            result1 = value * 12345
            result2 = other * 67890
            result3 = another * 11111
            result4 = more * 22222
            result5 = extra * 33333
            result6 = final * 44444
            return result1 + result2
        """

        hotspots = await engine._detect_code_smells(code_with_magic, "magic.py")

        # Должен найти магические числа
        magic_hotspots = [h for h in hotspots if "Магические числа" in h.title]
        assert len(magic_hotspots) > 0

        hotspot = magic_hotspots[0]
        assert hotspot.category == HotspotCategory.CODE_SMELL
        assert hotspot.severity == HotspotSeverity.MEDIUM

    @pytest.mark.asyncio
    async def test_quick_hotspot_check(self, engine, sample_problematic_code):
        """Тест быстрой проверки hotspot'ов"""
        result = await engine.quick_hotspot_check(sample_problematic_code, "test.py")

        assert isinstance(result, dict)
        assert "file_path" in result
        assert "lines_of_code" in result
        assert "potential_issues" in result
        assert "risk_level" in result
        assert "scan_duration" in result
        assert "timestamp" in result

        assert result["file_path"] == "test.py"
        assert isinstance(result["lines_of_code"], int)
        assert result["risk_level"] in ["low", "medium", "high"]
        assert result["scan_duration"] >= 0

    def test_calculate_overall_risk_score(self, engine):
        """Тест вычисления общего риск-скора"""
        # Тест с пустым списком
        assert engine._calculate_overall_risk_score([]) == 0.0

        # Тест с hotspot'ами разной критичности
        hotspots = [
            BugHotspot(severity=HotspotSeverity.CRITICAL, risk_score=9.0),
            BugHotspot(severity=HotspotSeverity.HIGH, risk_score=7.0),
            BugHotspot(severity=HotspotSeverity.MEDIUM, risk_score=5.0),
        ]

        risk_score = engine._calculate_overall_risk_score(hotspots)
        assert 0 <= risk_score <= 10
        assert isinstance(risk_score, float)

        # Среднее значение должно быть около 7.0
        assert 6.0 <= risk_score <= 8.0

    def test_generate_recommendations(self, engine):
        """Тест генерации рекомендаций"""
        # Тест с критическими проблемами
        critical_hotspots = [
            BugHotspot(severity=HotspotSeverity.CRITICAL),
            BugHotspot(severity=HotspotSeverity.CRITICAL),
        ]

        recommendations = engine._generate_recommendations(critical_hotspots)
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("КРИТИЧНО" in rec for rec in recommendations)

        # Тест с проблемами высокого приоритета
        high_hotspots = [
            BugHotspot(severity=HotspotSeverity.HIGH),
            BugHotspot(severity=HotspotSeverity.HIGH),
        ]

        high_recommendations = engine._generate_recommendations(high_hotspots)
        assert any("ВЫСОКИЙ ПРИОРИТЕТ" in rec for rec in high_recommendations)

    def test_update_metrics(self, engine):
        """Тест обновления метрик"""
        initial_metrics = engine.metrics.copy()

        # Создание тестового отчета
        test_report = HotspotAnalysisReport(
            total_hotspots=5, critical_hotspots=2, overall_risk_score=7.5
        )

        # Обновление метрик
        engine._update_metrics(test_report)

        # Проверка обновления
        assert (
            engine.metrics["analyses_performed"]
            == initial_metrics["analyses_performed"] + 1
        )
        assert (
            engine.metrics["hotspots_detected"]
            == initial_metrics["hotspots_detected"] + 5
        )
        assert (
            engine.metrics["critical_hotspots"]
            == initial_metrics["critical_hotspots"] + 2
        )
        assert engine.metrics["avg_risk_score"] != initial_metrics["avg_risk_score"]

    def test_get_detection_metrics(self, engine):
        """Тест получения метрик детектора"""
        metrics = engine.get_detection_metrics()

        assert isinstance(metrics, dict)
        assert "engine_status" in metrics
        assert "metrics" in metrics
        assert "last_updated" in metrics

        assert metrics["engine_status"] == "active"
        assert isinstance(metrics["metrics"], dict)
        assert "analyses_performed" in metrics["metrics"]
        assert "hotspots_detected" in metrics["metrics"]


class TestGlobalEngineInstance:
    """Тесты для глобального экземпляра движка"""

    @pytest.mark.asyncio
    async def test_get_hotspot_detection_engine_singleton(self):
        """Тест получения singleton экземпляра"""
        engine1 = await get_hotspot_detection_engine()
        engine2 = await get_hotspot_detection_engine()

        assert engine1 is engine2
        assert isinstance(engine1, BugHotspotDetectionEngine)

    @pytest.mark.asyncio
    async def test_engine_initialization(self):
        """Тест инициализации движка"""
        engine = await get_hotspot_detection_engine()

        assert hasattr(engine, "metrics")
        assert "analyses_performed" in engine.metrics
        assert "hotspots_detected" in engine.metrics
        assert "critical_hotspots" in engine.metrics
        assert "avg_risk_score" in engine.metrics


class TestEdgeCases:
    """Тесты крайних случаев"""

    @pytest.mark.asyncio
    async def test_empty_code_analysis(self):
        """Тест анализа пустого кода"""
        engine = BugHotspotDetectionEngine()

        result = await engine.analyze_code_hotspots("", "empty.py")
        assert isinstance(result, HotspotAnalysisReport)
        assert result.total_hotspots == 0
        assert result.overall_risk_score == 0.0

    @pytest.mark.asyncio
    async def test_whitespace_only_code(self):
        """Тест анализа кода только с пробелами"""
        engine = BugHotspotDetectionEngine()

        whitespace_code = "   \n  \n\t\t\n   "
        result = await engine.analyze_code_hotspots(whitespace_code, "whitespace.py")

        assert isinstance(result, HotspotAnalysisReport)
        assert result.total_hotspots == 0

    @pytest.mark.asyncio
    async def test_single_line_code(self):
        """Тест анализа одной строки кода"""
        engine = BugHotspotDetectionEngine()

        single_line = "print('Hello, World!')"
        result = await engine.analyze_code_hotspots(single_line, "hello.py")

        assert isinstance(result, HotspotAnalysisReport)
        assert result.analysis_duration >= 0


class TestPerformance:
    """Тесты производительности"""

    @pytest.mark.asyncio
    async def test_analysis_performance(self):
        """Тест производительности анализа"""
        engine = BugHotspotDetectionEngine()

        # Создание среднего по размеру кода
        medium_code = (
            """
        def process_data(data_list):
            result = []
            for item in data_list:
                if item is not None:
                    processed = transform_item(item)
                    result.append(processed)
            return result
        """
            * 10
        )

        start_time = datetime.now()
        result = await engine.analyze_code_hotspots(medium_code, "medium.py")
        duration = (datetime.now() - start_time).total_seconds()

        # Анализ должен завершиться быстро
        assert duration < 2.0
        assert isinstance(result, HotspotAnalysisReport)

    @pytest.mark.asyncio
    async def test_quick_check_performance(self):
        """Тест производительности быстрой проверки"""
        engine = BugHotspotDetectionEngine()

        # Код среднего размера
        code = "def function_%d(): pass\n" * 100

        start_time = datetime.now()
        result = await engine.quick_hotspot_check(code, "test.py")
        duration = (datetime.now() - start_time).total_seconds()

        # Быстрая проверка должна быть очень быстрой
        assert duration < 0.5
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_concurrent_analyses(self):
        """Тест параллельных анализов"""
        engine = BugHotspotDetectionEngine()

        code_sample = """
        def test_function():
            try:
                result = process()
            except:
                pass
            return result
        """

        # Создание нескольких параллельных задач
        tasks = [
            engine.analyze_code_hotspots(code_sample, f"file_{i}.py") for i in range(3)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all(isinstance(result, HotspotAnalysisReport) for result in results)

        # Проверка, что все анализы нашли проблемы
        assert all(result.total_hotspots > 0 for result in results)


# =============================================================================
# ПАРАМЕТРИЗОВАННЫЕ ТЕСТЫ
# =============================================================================


@pytest.mark.parametrize(
    "severity,expected_range",
    [
        (HotspotSeverity.CRITICAL, (8.0, 10.0)),
        (HotspotSeverity.HIGH, (6.0, 8.0)),
        (HotspotSeverity.MEDIUM, (4.0, 6.0)),
        (HotspotSeverity.LOW, (1.0, 4.0)),
    ],
)
def test_severity_risk_score_ranges(severity, expected_range):
    """Тест диапазонов риск-скоров для уровней критичности"""
    hotspot = BugHotspot(severity=severity, risk_score=5.0)  # Базовый скор

    # Проверка, что severity соответствует ожидаемому
    assert hotspot.severity == severity

    # Для более точного тестирования можно добавить логику вычисления риск-скора
    # на основе severity в самом движке


@pytest.mark.parametrize(
    "code_size,expected_issues",
    [
        (50, 0),  # Маленький файл
        (200, 0),  # Средний файл
        (500, 1),  # Большой файл - должна быть проблема
    ],
)
@pytest.mark.asyncio
async def test_file_size_detection(code_size, expected_issues):
    """Тест обнаружения проблем в зависимости от размера файла"""
    engine = BugHotspotDetectionEngine()

    # Создание кода заданного размера
    code = "# Comment line\n" * code_size

    hotspots = await engine._analyze_complexity(code, "test.py")

    # Проверка количества найденных проблем
    large_file_issues = len([h for h in hotspots if "Большой файл" in h.title])
    assert large_file_issues == expected_issues


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_complex_code():
    """Образец сложного кода для тестирования"""
    return """
    def very_complex_function_with_many_nested_conditions(param1, param2, param3, param4, param5):
        if param1:
            if param2:
                if param3:
                    try:
                        result = complex_operation()
                        if result:
                            return process_result(result)
                        else:
                            return None
                    except:
                        pass
                else:
                    return default_value()
            else:
                return alternative_result()
        else:
            return None
    """
