"""
Unit Tests for AI Analysis Domain Entities

Tests for pure domain entities without external dependencies.
Following hexagonal architecture testing principles.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock
from uuid import uuid4

from backend.domain.ai_analysis.entities import (
    AnalysisSession, AnalysisRequest, AnalysisResult, AIModel,
    AnalysisMetrics, AnalysisType, AnalysisStatus, Priority
)


class TestAnalysisRequest:
    """Test AnalysisRequest entity"""
    
    def test_create_analysis_request_success(self):
        """Test successful analysis request creation"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            parameters={"language": "python", "complexity": "medium"},
            priority=Priority.MEDIUM,
            user_id="user_123"
        )
        
        assert request.id is not None
        assert request.analysis_type == AnalysisType.CODE_ANALYSIS
        assert request.content == "def hello(): pass"
        assert request.priority == Priority.MEDIUM
        assert request.user_id == "user_123"
        assert isinstance(request.created_at, datetime)
    
    def test_create_analysis_request_empty_content_fails(self):
        """Test analysis request creation fails with empty content"""
        with pytest.raises(ValueError, match="Content cannot be empty"):
            AnalysisRequest(
                id=str(uuid4()),
                analysis_type=AnalysisType.CODE_ANALYSIS,
                content="",
                parameters={},
                priority=Priority.MEDIUM,
                user_id="user_123"
            )
    
    def test_create_analysis_request_whitespace_content_fails(self):
        """Test analysis request creation fails with whitespace-only content"""
        with pytest.raises(ValueError, match="Content cannot be empty"):
            AnalysisRequest(
                id=str(uuid4()),
                analysis_type=AnalysisType.CODE_ANALYSIS,
                content="   ",
                parameters={},
                priority=Priority.MEDIUM,
                user_id="user_123"
            )
    
    def test_create_analysis_request_auto_id_generation(self):
        """Test analysis request auto-generates ID if not provided"""
        request = AnalysisRequest(
            id="",  # Empty ID should be auto-generated
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            priority=Priority.MEDIUM,
        )
        
        assert request.id is not None
        assert request.id != ""
        assert len(request.id) > 0
    
    def test_create_analysis_request_default_priority(self):
        """Test analysis request uses default priority"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass"
        )
        
        assert request.priority == Priority.MEDIUM


class TestAnalysisResult:
    """Test AnalysisResult entity"""
    
    def test_create_analysis_result_success(self):
        """Test successful analysis result creation"""
        result = AnalysisResult(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            score=0.85,
            confidence=0.92,
            suggestions=["Add type hints", "Add docstring"],
            metadata={"language": "python", "complexity": "low"}
        )
        
        assert result.id is not None
        assert result.analysis_type == AnalysisType.CODE_ANALYSIS
        assert result.content == "def hello(): pass"
        assert result.score == 0.85
        assert result.confidence == 0.92
        assert "Add type hints" in result.suggestions
        assert result.metadata["language"] == "python"
        assert isinstance(result.created_at, datetime)
    
    def test_create_analysis_result_auto_id_generation(self):
        """Test analysis result auto-generates ID if not provided"""
        result = AnalysisResult(
            id="",  # Empty ID should be auto-generated
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            score=0.85,
            confidence=0.92
        )
        
        assert result.id is not None
        assert result.id != ""
        assert len(result.id) > 0
    
    def test_create_analysis_result_invalid_score_fails(self):
        """Test analysis result creation fails with invalid score"""
        with pytest.raises(ValueError, match="Score must be between 0.0 and 1.0"):
            AnalysisResult(
                id=str(uuid4()),
                analysis_type=AnalysisType.CODE_ANALYSIS,
                content="def hello(): pass",
                score=1.5,  # Invalid score
                confidence=0.92
            )
    
    def test_create_analysis_result_negative_score_fails(self):
        """Test analysis result creation fails with negative score"""
        with pytest.raises(ValueError, match="Score must be between 0.0 and 1.0"):
            AnalysisResult(
                id=str(uuid4()),
                analysis_type=AnalysisType.CODE_ANALYSIS,
                content="def hello(): pass",
                score=-0.1,  # Negative score
                confidence=0.92
            )
    
    def test_create_analysis_result_invalid_confidence_fails(self):
        """Test analysis result creation fails with invalid confidence"""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            AnalysisResult(
                id=str(uuid4()),
                analysis_type=AnalysisType.CODE_ANALYSIS,
                content="def hello(): pass",
                score=0.85,
                confidence=1.5  # Invalid confidence
            )
    
    def test_create_analysis_result_negative_confidence_fails(self):
        """Test analysis result creation fails with negative confidence"""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            AnalysisResult(
                id=str(uuid4()),
                analysis_type=AnalysisType.CODE_ANALYSIS,
                content="def hello(): pass",
                score=0.85,
                confidence=-0.1  # Negative confidence
            )


class TestAIModel:
    """Test AIModel entity"""
    
    def test_create_ai_model_success(self):
        """Test successful AI model creation"""
        model = AIModel(
            id="model_123",
            name="CodeAnalyzer",
            version="1.0.0",
            model_type="transformer",
            capabilities={AnalysisType.CODE_ANALYSIS, AnalysisType.QUALITY_ANALYSIS},
            parameters={"max_tokens": 1000, "temperature": 0.7}
        )
        
        assert model.id == "model_123"
        assert model.name == "CodeAnalyzer"
        assert model.version == "1.0.0"
        assert model.model_type == "transformer"
        assert AnalysisType.CODE_ANALYSIS in model.capabilities
        assert AnalysisType.QUALITY_ANALYSIS in model.capabilities
        assert model.parameters["max_tokens"] == 1000
        assert model.is_active == True
        assert isinstance(model.created_at, datetime)
    
    def test_create_ai_model_empty_name_fails(self):
        """Test AI model creation fails with empty name"""
        with pytest.raises(ValueError, match="Model name cannot be empty"):
            AIModel(
                id="model_123",
                name="",
                version="1.0.0",
                model_type="transformer"
            )
    
    def test_create_ai_model_whitespace_name_fails(self):
        """Test AI model creation fails with whitespace-only name"""
        with pytest.raises(ValueError, match="Model name cannot be empty"):
            AIModel(
                id="model_123",
                name="   ",
                version="1.0.0",
                model_type="transformer"
            )
    
    def test_create_ai_model_empty_version_fails(self):
        """Test AI model creation fails with empty version"""
        with pytest.raises(ValueError, match="Model version cannot be empty"):
            AIModel(
                id="model_123",
                name="TestModel",
                version="",
                model_type="transformer"
            )
    
    def test_create_ai_model_whitespace_version_fails(self):
        """Test AI model creation fails with whitespace-only version"""
        with pytest.raises(ValueError, match="Model version cannot be empty"):
            AIModel(
                id="model_123",
                name="TestModel",
                version="   ",
                model_type="transformer"
            )
    
    def test_create_ai_model_auto_id_generation(self):
        """Test AI model auto-generates ID if not provided"""
        model = AIModel(
            id="",  # Empty ID should be auto-generated
            name="TestModel",
            version="1.0.0",
            model_type="transformer"
        )
        
        assert model.id is not None
        assert model.id != ""
        assert len(model.id) > 0
    
    def test_can_analyze(self):
        """Test analysis capability check"""
        model = AIModel(
            id="model_123",
            name="CodeAnalyzer",
            version="1.0.0",
            model_type="transformer",
            capabilities={AnalysisType.CODE_ANALYSIS, AnalysisType.QUALITY_ANALYSIS}
        )
        
        assert model.can_analyze(AnalysisType.CODE_ANALYSIS) == True
        assert model.can_analyze(AnalysisType.QUALITY_ANALYSIS) == True
        assert model.can_analyze(AnalysisType.SECURITY_ANALYSIS) == False
    
    def test_activate_deactivate(self):
        """Test model activation/deactivation"""
        model = AIModel(
            id="model_123",
            name="CodeAnalyzer",
            version="1.0.0",
            model_type="transformer"
        )
        
        # Initially active
        assert model.is_active == True
        
        # Deactivate
        model.deactivate()
        assert model.is_active == False
        
        # Activate again
        model.activate()
        assert model.is_active == True


class TestAnalysisSession:
    """Test AnalysisSession entity (aggregate root)"""
    
    def test_create_analysis_session_success(self):
        """Test successful analysis session creation"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            priority=Priority.MEDIUM,
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        assert session.id is not None
        assert session.request == request
        assert session.status == AnalysisStatus.PENDING
        assert session.results == []
        assert session.error_message is None
        assert session.started_at is None
        assert session.completed_at is None
        assert isinstance(session.created_at, datetime)
    
    def test_create_analysis_session_auto_id_generation(self):
        """Test analysis session auto-generates ID if not provided"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id="",  # Empty ID should be auto-generated
            request=request
        )
        
        assert session.id is not None
        assert session.id != ""
        assert len(session.id) > 0
    
    def test_start_analysis_success(self):
        """Test successful analysis session start"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        session.start_analysis()
        
        assert session.status == AnalysisStatus.RUNNING
        assert session.started_at is not None
        assert session.updated_at is not None
        assert session.is_running() == True
    
    def test_start_analysis_wrong_status_fails(self):
        """Test analysis session start fails with wrong status"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        session.start_analysis()  # First start
        
        with pytest.raises(ValueError, match="Cannot start analysis in running status"):
            session.start_analysis()  # Second start should fail
    
    def test_add_result_success(self):
        """Test successful result addition"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        session.start_analysis()
        
        result = AnalysisResult(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            score=0.85,
            confidence=0.92
        )
        
        session.add_result(result)
        
        assert len(session.results) == 1
        assert session.results[0] == result
        assert session.updated_at is not None
    
    def test_add_result_wrong_status_fails(self):
        """Test result addition fails with wrong status"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        result = AnalysisResult(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            score=0.85,
            confidence=0.92
        )
        
        with pytest.raises(ValueError, match="Cannot add result in pending status"):
            session.add_result(result)  # Should fail - not running
    
    def test_complete_analysis_success(self):
        """Test successful analysis completion"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        session.start_analysis()
        session.complete_analysis()
        
        assert session.status == AnalysisStatus.COMPLETED
        assert session.completed_at is not None
        assert session.updated_at is not None
        assert session.is_completed() == True
    
    def test_complete_analysis_wrong_status_fails(self):
        """Test analysis completion fails with wrong status"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        with pytest.raises(ValueError, match="Cannot complete analysis in pending status"):
            session.complete_analysis()  # Should fail - not running
    
    def test_fail_analysis_success(self):
        """Test successful analysis failure"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        session.start_analysis()
        session.fail_analysis("Analysis failed due to timeout")
        
        assert session.status == AnalysisStatus.FAILED
        assert session.error_message == "Analysis failed due to timeout"
        assert session.completed_at is not None
        assert session.updated_at is not None
        assert session.is_failed() == True
    
    def test_fail_completed_analysis_fails(self):
        """Test failing completed analysis fails"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        session.start_analysis()
        session.complete_analysis()
        
        with pytest.raises(ValueError, match="Cannot fail completed analysis"):
            session.fail_analysis("This should fail")
    
    def test_cancel_analysis_success(self):
        """Test successful analysis cancellation"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        session.start_analysis()
        session.cancel_analysis()
        
        assert session.status == AnalysisStatus.CANCELLED
        assert session.completed_at is not None
        assert session.updated_at is not None
    
    def test_cancel_completed_analysis_fails(self):
        """Test cancelling completed analysis fails"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        session.start_analysis()
        session.complete_analysis()
        
        with pytest.raises(ValueError, match="Cannot cancel analysis in completed status"):
            session.cancel_analysis()
    
    def test_get_best_result_success(self):
        """Test getting best result"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        session.start_analysis()
        
        result1 = AnalysisResult(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            score=0.75,
            confidence=0.9
        )
        
        result2 = AnalysisResult(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            score=0.85,
            confidence=0.95
        )
        
        session.add_result(result1)
        session.add_result(result2)
        
        best_result = session.get_best_result()
        assert best_result == result2  # Higher score * confidence
    
    def test_get_best_result_empty_returns_none(self):
        """Test getting best result with no results returns None"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        best_result = session.get_best_result()
        assert best_result is None
    
    def test_get_average_score_success(self):
        """Test getting average score"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        session.start_analysis()
        
        result1 = AnalysisResult(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            score=0.8,
            confidence=0.9
        )
        
        result2 = AnalysisResult(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            score=0.6,
            confidence=0.95
        )
        
        session.add_result(result1)
        session.add_result(result2)
        
        avg_score = session.get_average_score()
        assert avg_score == 0.7  # (0.8 + 0.6) / 2
    
    def test_get_average_score_empty_returns_zero(self):
        """Test getting average score with no results returns zero"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        avg_score = session.get_average_score()
        assert avg_score == 0.0
    
    def test_get_duration_success(self):
        """Test getting analysis duration"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        session.start_analysis()
        
        # Mock the started_at time to be 5 seconds ago
        session.started_at = datetime.now(timezone.utc) - timedelta(seconds=5)
        session.complete_analysis()
        
        duration = session.get_duration()
        assert duration is not None
        assert duration >= 5.0  # Should be at least 5 seconds
    
    def test_get_duration_not_started_returns_none(self):
        """Test getting duration when analysis not started returns None"""
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        duration = session.get_duration()
        assert duration is None


class TestAnalysisMetrics:
    """Test AnalysisMetrics entity"""
    
    def test_create_analysis_metrics_success(self):
        """Test successful analysis metrics creation"""
        metrics = AnalysisMetrics(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            total_analyses=10,
            successful_analyses=8,
            failed_analyses=2,
            average_duration=5.5,
            average_score=0.85,
            average_confidence=0.92
        )
        
        assert metrics.id is not None
        assert metrics.analysis_type == AnalysisType.CODE_ANALYSIS
        assert metrics.total_analyses == 10
        assert metrics.successful_analyses == 8
        assert metrics.failed_analyses == 2
        assert metrics.average_duration == 5.5
        assert metrics.average_score == 0.85
        assert metrics.average_confidence == 0.92
        assert isinstance(metrics.created_at, datetime)
    
    def test_create_analysis_metrics_auto_id_generation(self):
        """Test analysis metrics auto-generates ID if not provided"""
        metrics = AnalysisMetrics(
            id="",  # Empty ID should be auto-generated
            analysis_type=AnalysisType.CODE_ANALYSIS
        )
        
        assert metrics.id is not None
        assert metrics.id != ""
        assert len(metrics.id) > 0
    
    def test_record_successful_analysis(self):
        """Test recording successful analysis"""
        metrics = AnalysisMetrics(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS
        )
        
        # Create a completed session
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        session.start_analysis()
        session.started_at = datetime.now(timezone.utc) - timedelta(seconds=5)
        
        result = AnalysisResult(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            score=0.85,
            confidence=0.92
        )
        
        session.add_result(result)
        session.complete_analysis()
        
        # Record the analysis
        metrics.record_analysis(session)
        
        assert metrics.total_analyses == 1
        assert metrics.successful_analyses == 1
        assert metrics.failed_analyses == 0
        assert metrics.average_duration > 0
        assert metrics.average_score == 0.85
        assert metrics.average_confidence == 0.92
        assert metrics.updated_at is not None
    
    def test_record_failed_analysis(self):
        """Test recording failed analysis"""
        metrics = AnalysisMetrics(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS
        )
        
        # Create a failed session
        request = AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            user_id="user_123"
        )
        
        session = AnalysisSession(
            id=str(uuid4()),
            request=request
        )
        
        session.start_analysis()
        session.fail_analysis("Test failure")
        
        # Record the analysis
        metrics.record_analysis(session)
        
        assert metrics.total_analyses == 1
        assert metrics.successful_analyses == 0
        assert metrics.failed_analyses == 1
        assert metrics.updated_at is not None
    
    def test_get_success_rate(self):
        """Test getting success rate"""
        metrics = AnalysisMetrics(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            total_analyses=10,
            successful_analyses=8,
            failed_analyses=2
        )
        
        success_rate = metrics.get_success_rate()
        assert success_rate == 0.8  # 8/10
    
    def test_get_success_rate_zero_total(self):
        """Test getting success rate with zero total analyses"""
        metrics = AnalysisMetrics(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            total_analyses=0,
            successful_analyses=0,
            failed_analyses=0
        )
        
        success_rate = metrics.get_success_rate()
        assert success_rate == 0.0
    
    def test_get_failure_rate(self):
        """Test getting failure rate"""
        metrics = AnalysisMetrics(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            total_analyses=10,
            successful_analyses=8,
            failed_analyses=2
        )
        
        failure_rate = metrics.get_failure_rate()
        assert failure_rate == 0.2  # 2/10
    
    def test_get_failure_rate_zero_total(self):
        """Test getting failure rate with zero total analyses"""
        metrics = AnalysisMetrics(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            total_analyses=0,
            successful_analyses=0,
            failed_analyses=0
        )
        
        failure_rate = metrics.get_failure_rate()
        assert failure_rate == 0.0 