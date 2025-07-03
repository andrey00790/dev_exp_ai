"""
🧪 Predictive Analytics Engine Tests

Unit tests for the predictive analytics engine and API endpoints.
Phase 4B - Advanced Intelligence Component Testing
"""

import asyncio
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest

from domain.core.predictive_analytics_engine import (PredictionConfidence,
                                                     PredictionResult,
                                                     PredictionType,
                                                     PredictiveAnalyticsEngine,
                                                     get_analytics_engine)


class TestPredictiveAnalyticsEngine:
    """Test suite for PredictiveAnalyticsEngine"""

    @pytest.fixture
    def engine(self):
        """Create a test engine instance"""
        return PredictiveAnalyticsEngine()

    @pytest.fixture
    def sample_project_data(self):
        """Sample project data for testing"""
        return {
            "complexity": 0.7,
            "lines_of_code": 5000,
            "team": {"size": 3, "avg_experience_years": 4},
            "requirements": [
                "User authentication",
                "Data visualization",
                "API integration",
            ],
            "project_age_days": 15,
        }

    @pytest.mark.asyncio
    async def test_predict_development_time_basic(self, engine, sample_project_data):
        """Test basic development time prediction"""
        result = await engine.predict_development_time(sample_project_data)

        assert isinstance(result, PredictionResult)
        assert result.prediction_type == PredictionType.DEVELOPMENT_TIME
        assert isinstance(result.predicted_value, int)
        assert result.predicted_value > 0
        assert result.confidence in [conf for conf in PredictionConfidence]
        assert 0.0 <= result.confidence_score <= 1.0
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_predict_development_time_simple_project(self, engine):
        """Test prediction for a simple project"""
        simple_project = {
            "complexity": 0.2,
            "lines_of_code": 1000,
            "team": {"size": 1, "avg_experience_years": 5},
            "requirements": ["Simple CRUD"],
        }

        result = await engine.predict_development_time(simple_project)

        assert result.predicted_value <= 10  # Should be reasonable for simple project
        assert result.confidence_score >= 0.5

    @pytest.mark.asyncio
    async def test_predict_development_time_complex_project(self, engine):
        """Test prediction for a complex project"""
        complex_project = {
            "complexity": 0.9,
            "lines_of_code": 50000,
            "team": {"size": 1, "avg_experience_years": 2},
            "requirements": [f"Requirement {i}" for i in range(15)],
        }

        result = await engine.predict_development_time(complex_project)

        assert result.predicted_value >= 5  # Should be higher for complex project
        assert len(result.recommendations) > 0

    def test_extract_features_basic(self, engine):
        """Test feature extraction from project data"""
        project_data = {
            "complexity": 0.5,
            "lines_of_code": 2000,
            "team": {"size": 2, "avg_experience_years": 3},
        }

        features = engine._extract_features(project_data)

        assert isinstance(features, dict)
        assert "complexity" in features
        assert "team_size" in features
        assert "loc" in features
        assert features["complexity"] == 0.5
        assert features["team_size"] == 2
        assert features["loc"] == 2000

    def test_extract_features_missing_data(self, engine):
        """Test feature extraction with missing data"""
        incomplete_data = {"complexity": 0.3}

        features = engine._extract_features(incomplete_data)

        assert isinstance(features, dict)
        assert "complexity" in features
        assert "team_size" in features  # Should have default
        assert "loc" in features  # Should have default
        assert features["team_size"] == 1  # Default value
        assert features["loc"] == 100  # Default value

    def test_update_metrics(self, engine):
        """Test metrics updating"""
        initial_predictions = engine.metrics["predictions_made"]
        initial_confidence = engine.metrics["average_confidence"]

        # Create a mock result
        mock_result = Mock()
        mock_result.confidence_score = 0.8

        engine._update_metrics(mock_result)

        assert engine.metrics["predictions_made"] == initial_predictions + 1
        assert engine.metrics["average_confidence"] != initial_confidence

    @pytest.mark.asyncio
    async def test_multiple_predictions_metrics(self, engine, sample_project_data):
        """Test metrics after multiple predictions"""
        initial_count = engine.metrics["predictions_made"]

        # Make multiple predictions
        for i in range(3):
            await engine.predict_development_time(sample_project_data)

        assert engine.metrics["predictions_made"] == initial_count + 3
        assert engine.metrics["average_confidence"] > 0


class TestPredictionResult:
    """Test suite for PredictionResult"""

    def test_prediction_result_creation(self):
        """Test creating a prediction result"""
        result = PredictionResult(
            prediction_type=PredictionType.DEVELOPMENT_TIME,
            predicted_value=7,
            confidence=PredictionConfidence.HIGH,
            confidence_score=0.85,
            recommendations=["Test recommendation"],
        )

        assert result.prediction_type == PredictionType.DEVELOPMENT_TIME
        assert result.predicted_value == 7
        assert result.confidence == PredictionConfidence.HIGH
        assert result.confidence_score == 0.85
        assert len(result.recommendations) == 1
        assert result.prediction_id is not None
        assert isinstance(result.created_at, datetime)

    def test_prediction_result_defaults(self):
        """Test prediction result with default values"""
        result = PredictionResult()

        assert result.prediction_type == PredictionType.DEVELOPMENT_TIME
        assert result.confidence == PredictionConfidence.MEDIUM
        assert result.confidence_score == 0.0
        assert len(result.recommendations) == 0
        assert result.prediction_id is not None


class TestPredictionTypes:
    """Test suite for prediction types and enums"""

    def test_prediction_type_enum(self):
        """Test PredictionType enum values"""
        assert PredictionType.DEVELOPMENT_TIME.value == "development_time"
        assert PredictionType.BUG_HOTSPOTS.value == "bug_hotspots"
        assert PredictionType.TEAM_PERFORMANCE.value == "team_performance"
        assert PredictionType.PROJECT_HEALTH.value == "project_health"

    def test_prediction_confidence_enum(self):
        """Test PredictionConfidence enum values"""
        assert PredictionConfidence.VERY_HIGH.value == "very_high"
        assert PredictionConfidence.HIGH.value == "high"
        assert PredictionConfidence.MEDIUM.value == "medium"
        assert PredictionConfidence.LOW.value == "low"


class TestGlobalEngineInstance:
    """Test suite for global engine instance management"""

    @pytest.mark.asyncio
    async def test_get_analytics_engine_singleton(self):
        """Test that get_analytics_engine returns the same instance"""
        engine1 = await get_analytics_engine()
        engine2 = await get_analytics_engine()

        assert engine1 is engine2
        assert isinstance(engine1, PredictiveAnalyticsEngine)

    @pytest.mark.asyncio
    async def test_engine_initialization(self):
        """Test engine initialization"""
        engine = await get_analytics_engine()

        assert hasattr(engine, "metrics")
        assert "predictions_made" in engine.metrics
        assert "average_confidence" in engine.metrics
        assert engine.metrics["predictions_made"] >= 0
        assert 0.0 <= engine.metrics["average_confidence"] <= 1.0


class TestEdgeCases:
    """Test suite for edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_empty_project_data(self):
        """Test prediction with empty project data"""
        engine = PredictiveAnalyticsEngine()

        result = await engine.predict_development_time({})

        assert isinstance(result, PredictionResult)
        assert result.predicted_value > 0  # Should still provide a prediction

    @pytest.mark.asyncio
    async def test_negative_values_handling(self):
        """Test handling of negative values in input"""
        engine = PredictiveAnalyticsEngine()

        project_data = {
            "complexity": -0.5,  # Negative complexity
            "lines_of_code": -100,  # Negative LOC
            "team": {"size": -1},  # Negative team size
        }

        result = await engine.predict_development_time(project_data)

        assert isinstance(result, PredictionResult)
        assert result.predicted_value > 0

    @pytest.mark.asyncio
    async def test_extremely_large_values(self):
        """Test handling of extremely large values"""
        engine = PredictiveAnalyticsEngine()

        project_data = {
            "complexity": 100.0,  # Very high complexity
            "lines_of_code": 1000000,  # Very large codebase
            "team": {"size": 100},  # Very large team
        }

        result = await engine.predict_development_time(project_data)

        assert isinstance(result, PredictionResult)
        assert result.predicted_value > 0


class TestPerformance:
    """Test suite for performance characteristics"""

    @pytest.mark.asyncio
    async def test_prediction_performance(self, sample_project_data):
        """Test prediction performance"""
        engine = PredictiveAnalyticsEngine()

        start_time = datetime.now()
        result = await engine.predict_development_time(sample_project_data)
        end_time = datetime.now()

        duration = (end_time - start_time).total_seconds()

        assert duration < 1.0  # Should complete within 1 second
        assert isinstance(result, PredictionResult)

    @pytest.mark.asyncio
    async def test_concurrent_predictions(self, sample_project_data):
        """Test concurrent prediction handling"""
        engine = PredictiveAnalyticsEngine()

        # Create multiple concurrent prediction tasks
        tasks = [engine.predict_development_time(sample_project_data) for _ in range(5)]

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(isinstance(result, PredictionResult) for result in results)
        assert all(result.predicted_value > 0 for result in results)


class TestIntegration:
    """Integration tests for the complete system"""

    @pytest.mark.asyncio
    async def test_end_to_end_prediction_flow(self, sample_project_data):
        """Test complete prediction flow from data to result"""
        engine = await get_analytics_engine()

        # Initial metrics
        initial_predictions = engine.metrics["predictions_made"]

        # Make prediction
        result = await engine.predict_development_time(sample_project_data)

        # Verify result
        assert isinstance(result, PredictionResult)
        assert result.prediction_type == PredictionType.DEVELOPMENT_TIME
        assert result.predicted_value > 0
        assert result.confidence_score > 0
        assert len(result.recommendations) > 0

        # Verify metrics updated
        assert engine.metrics["predictions_made"] == initial_predictions + 1
        assert engine.metrics["average_confidence"] > 0

    @pytest.mark.asyncio
    async def test_multiple_prediction_types_future(self):
        """Test framework for future prediction types"""
        engine = PredictiveAnalyticsEngine()

        # Test that enum supports future prediction types
        prediction_types = [pt for pt in PredictionType]

        assert PredictionType.DEVELOPMENT_TIME in prediction_types
        assert PredictionType.BUG_HOTSPOTS in prediction_types
        assert PredictionType.TEAM_PERFORMANCE in prediction_types
        assert PredictionType.PROJECT_HEALTH in prediction_types


# =============================================================================
# FIXTURES AND UTILITIES
# =============================================================================


@pytest.fixture
def sample_project_data():
    """Sample project data for testing"""
    return {
        "complexity": 0.6,
        "lines_of_code": 3000,
        "team": {"size": 2, "avg_experience_years": 3},
        "requirements": ["User management", "Data processing", "Report generation"],
        "project_age_days": 10,
    }


@pytest.fixture
def mock_engine():
    """Create a mock engine for testing"""
    engine = Mock(spec=PredictiveAnalyticsEngine)
    engine.metrics = {"predictions_made": 0, "average_confidence": 0.0}
    return engine


# =============================================================================
# PARAMETRIZED TESTS
# =============================================================================


@pytest.mark.parametrize(
    "complexity,expected_range",
    [
        (0.1, (5, 10)),  # Low complexity
        (0.5, (5, 15)),  # Medium complexity
        (0.9, (7, 20)),  # High complexity
    ],
)
@pytest.mark.asyncio
async def test_complexity_impact_on_prediction(complexity, expected_range):
    """Test that complexity appropriately impacts predictions"""
    engine = PredictiveAnalyticsEngine()

    project_data = {
        "complexity": complexity,
        "lines_of_code": 2000,
        "team": {"size": 2, "avg_experience_years": 3},
    }

    result = await engine.predict_development_time(project_data)

    assert expected_range[0] <= result.predicted_value <= expected_range[1]


@pytest.mark.parametrize(
    "team_size,expected_impact",
    [
        (1, "higher"),  # Solo developer
        (3, "moderate"),  # Small team
        (8, "lower"),  # Large team
    ],
)
@pytest.mark.asyncio
async def test_team_size_impact(team_size, expected_impact):
    """Test team size impact on predictions"""
    engine = PredictiveAnalyticsEngine()

    project_data = {
        "complexity": 0.5,
        "lines_of_code": 3000,
        "team": {"size": team_size, "avg_experience_years": 3},
    }

    result = await engine.predict_development_time(project_data)

    # Basic validation that prediction is reasonable
    assert result.predicted_value > 0
    assert result.confidence_score > 0
