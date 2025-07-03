"""
Tests for monitoring metrics module.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from app.monitoring.metrics import (METRIC_TARGETS, get_metrics_handler,
                                    initialize_app_info,
                                    record_code_documentation_metrics,
                                    record_rfc_generation_metrics,
                                    record_semantic_search_metrics,
                                    record_user_experience_metrics,
                                    update_business_metrics,
                                    update_feature_adoption_rates,
                                    update_system_metrics)


class TestMetricsRecording:
    """Test metrics recording functions."""

    def test_record_semantic_search_metrics(self):
        """Test semantic search metrics recording."""
        # This should not raise any exceptions
        record_semantic_search_metrics(
            endpoint="/api/v1/search",
            duration=0.5,
            results_count=10,
            relevance_score=0.85,
            status="success",
            language="ru",
            collection="documents",
            query_type="semantic",
            cache_hit=True,
        )

    def test_record_rfc_generation_metrics(self):
        """Test RFC generation metrics recording."""
        record_rfc_generation_metrics(
            endpoint="/api/v1/generate",
            task_type="system_design",
            duration=25.0,
            quality_score=4.2,
            completeness_percent=95.0,
            tokens_used=5000,
            status="success",
            template="standard",
            llm_provider="openai",
            model="gpt-4",
        )

    def test_record_code_documentation_metrics(self):
        """Test code documentation metrics recording."""
        record_code_documentation_metrics(
            endpoint="/api/v1/documentation",
            doc_type="api",
            language="python",
            duration=45.0,
            coverage_percent=92.0,
            lines_processed=1500,
            status="success",
        )

    def test_record_user_experience_metrics(self):
        """Test user experience metrics recording."""
        record_user_experience_metrics(
            feature="semantic_search",
            satisfaction_score=4.5,
            session_duration_seconds=1200.0,
            user_type="premium",
        )

    def test_update_business_metrics(self):
        """Test business metrics update."""
        update_business_metrics(
            feature="rfc_generation",
            time_savings_percent=75.0,
            quality_improvement_percent=60.0,
        )

    def test_update_system_metrics(self):
        """Test system metrics update."""
        update_system_metrics(
            uptime_percent=99.8,
            component_error_rates={
                "semantic_search": 1.2,
                "rfc_generation": 0.8,
                "code_documentation": 0.5,
            },
            daily_active_users=150,
            weekly_active_users=800,
            monthly_active_users=2500,
        )

    def test_update_feature_adoption_rates(self):
        """Test feature adoption rates update."""
        update_feature_adoption_rates(
            {
                "semantic_search": 85.0,
                "rfc_generation": 70.0,
                "code_documentation": 60.0,
            }
        )


class TestMetricsHandlers:
    """Test metrics handlers and utilities."""

    def test_get_metrics_handler(self):
        """Test metrics handler creation."""
        handler = get_metrics_handler()
        assert callable(handler)

        result = handler()
        assert "content" in result
        assert "media_type" in result
        assert result["media_type"] == "text/plain; version=0.0.4; charset=utf-8"

    @patch("infra.monitoring.metrics.logger")
    def test_initialize_app_info(self, mock_logger):
        """Test app info initialization."""
        initialize_app_info("1.0.0", "test")

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "version: 1.0.0" in call_args
        assert "env: test" in call_args


class TestMetricTargets:
    """Test metric targets configuration."""

    def test_metric_targets_exist(self):
        """Test that metric targets are defined."""
        assert isinstance(METRIC_TARGETS, dict)
        assert len(METRIC_TARGETS) > 0

        # Check some key targets
        assert "semantic_search_response_time_p95" in METRIC_TARGETS
        assert "rfc_generation_duration_avg" in METRIC_TARGETS
        assert "code_documentation_duration_avg" in METRIC_TARGETS
        assert "user_satisfaction_avg" in METRIC_TARGETS
        assert "system_uptime_min" in METRIC_TARGETS

    def test_metric_targets_values(self):
        """Test metric target values are reasonable."""
        # Response times should be positive
        assert METRIC_TARGETS["semantic_search_response_time_p95"] > 0
        assert METRIC_TARGETS["rfc_generation_duration_avg"] > 0
        assert METRIC_TARGETS["code_documentation_duration_avg"] > 0

        # Scores should be in reasonable ranges
        assert 0 <= METRIC_TARGETS["rfc_generation_quality_score_avg"] <= 5
        assert 0 <= METRIC_TARGETS["user_satisfaction_avg"] <= 5

        # Percentages should be 0-100
        assert 0 <= METRIC_TARGETS["system_uptime_min"] <= 100
        assert 0 <= METRIC_TARGETS["error_rate_max"] <= 100


@pytest.mark.asyncio
class TestMetricsMiddleware:
    """Test metrics middleware."""

    @patch("app.monitoring.metrics.time.time")
    @patch("infra.monitoring.metrics.logger")
    async def test_metrics_middleware_success(self, mock_logger, mock_time):
        """Test metrics middleware with successful request."""
        from app.monitoring.metrics import metrics_middleware

        # Mock time progression
        mock_time.side_effect = [1000.0, 1001.5]  # 1.5 second duration

        # Mock request and response
        mock_request = MagicMock()
        mock_request.url.path = "/api/v1/search"

        mock_response = MagicMock()

        async def mock_call_next(request):
            return mock_response

        result = await metrics_middleware(mock_request, mock_call_next)

        assert result == mock_response
        mock_logger.error.assert_not_called()

    @patch("infra.monitoring.metrics.logger")
    async def test_metrics_middleware_error(self, mock_logger):
        """Test metrics middleware with error."""
        from app.monitoring.metrics import metrics_middleware

        # Mock request
        mock_request = MagicMock()
        mock_request.url.path = "/api/v1/generate"

        async def mock_call_next(request):
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await metrics_middleware(mock_request, mock_call_next)

        mock_logger.error.assert_called_once()
        assert "Request failed" in mock_logger.error.call_args[0][0]
