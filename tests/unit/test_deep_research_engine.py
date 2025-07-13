"""
Unit tests for Deep Research Engine

Comprehensive test suite covering:
- Research session creation and management
- Step execution and planning
- WebSocket communication
- Error handling and edge cases
- Performance metrics
- Adaptive planning
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from domain.core.deep_research_engine import (DeepResearchEngine,
                                              ResearchSession, ResearchStatus,
                                              ResearchStep, ResearchStepType,
                                              StepStatus,
                                              get_deep_research_engine)


class TestDeepResearchEngine:
    """Test cases for DeepResearchEngine"""

    @pytest.fixture
    def engine(self):
        """Create a DeepResearchEngine instance for testing"""
        engine = DeepResearchEngine()
        return engine

    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service for testing"""
        mock_service = AsyncMock()
        mock_service.generate_response = AsyncMock(return_value="Generated response")
        return mock_service

    @pytest.fixture
    def sample_query(self):
        """Sample research query for testing"""
        return "What are the best practices for microservices architecture?"

    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Test engine initialization"""
        assert engine.llm_service is not None
        assert engine.active_sessions == {}
        assert engine.metrics["total_sessions"] == 0
        assert engine.config["max_concurrent_sessions"] == 10

    @pytest.mark.asyncio
    async def test_start_research_basic(self, engine, sample_query):
        """Test basic research session creation"""
        session = await engine.start_research(
            query=sample_query, user_id="test_user", max_steps=5
        )

        assert session.session_id is not None
        assert session.original_query == sample_query
        assert session.user_id == "test_user"
        assert session.max_steps == 5
        assert session.status == ResearchStatus.CREATED
        assert session.session_id in engine.active_sessions
        assert engine.metrics["total_sessions"] == 1

    @pytest.mark.asyncio
    async def test_start_research_with_defaults(self, engine, sample_query):
        """Test research session creation with default parameters"""
        session = await engine.start_research(query=sample_query)

        assert session.user_id == ""
        assert session.max_steps == engine.config["default_max_steps"]

    @pytest.mark.asyncio
    async def test_start_research_max_sessions_limit(self, engine, sample_query):
        """Test max concurrent sessions limit"""
        # Fill up to the limit
        for i in range(engine.config["max_concurrent_sessions"]):
            await engine.start_research(query=f"Query {i}", user_id=f"user_{i}")

        # This should raise an exception
        with pytest.raises(
            Exception, match="Превышен лимит одновременных исследований"
        ):
            await engine.start_research(query="One too many", user_id="overflow_user")

    @patch("domain.core.deep_research_engine.LLMGenerationService")
    @pytest.mark.asyncio
    async def test_extract_research_goal_success(
        self, mock_llm_class, engine, sample_query
    ):
        """Test successful research goal extraction"""
        mock_llm = AsyncMock()
        mock_llm.generate_response = AsyncMock(
            return_value="Analyze microservices best practices"
        )
        mock_llm_class.return_value = mock_llm
        engine.llm_service = mock_llm

        goal = await engine._extract_research_goal(sample_query)

        assert goal == "Analyze microservices best practices"
        mock_llm.generate_response.assert_called_once()

    @patch("domain.core.deep_research_engine.LLMGenerationService")
    @pytest.mark.asyncio
    async def test_extract_research_goal_fallback(
        self, mock_llm_class, engine, sample_query
    ):
        """Test research goal extraction fallback"""
        mock_llm = AsyncMock()
        mock_llm.generate_response = AsyncMock(side_effect=Exception("LLM error"))
        mock_llm_class.return_value = mock_llm
        engine.llm_service = mock_llm

        goal = await engine._extract_research_goal(sample_query)

        assert goal == f"Провести углубленный анализ запроса: {sample_query}"

    @pytest.mark.asyncio
    async def test_plan_research_steps_basic(self, engine):
        """Test basic research step planning"""
        session = ResearchSession(
            original_query="Test query", research_goal="Test goal", max_steps=5
        )

        with patch.object(engine, "llm_service") as mock_llm:
            mock_llm.generate_response = AsyncMock(return_value="Planning response")

            steps = await engine._plan_research_steps(session)

            assert len(steps) <= session.max_steps
            assert all(isinstance(step, ResearchStep) for step in steps)
            assert steps[0].step_type == ResearchStepType.INITIAL_ANALYSIS
            assert steps[-1].step_type == ResearchStepType.FINAL_SUMMARY

    @pytest.mark.asyncio
    async def test_plan_research_steps_fallback(self, engine):
        """Test research step planning fallback"""
        session = ResearchSession(
            original_query="Test query", research_goal="Test goal", max_steps=3
        )

        with patch.object(engine, "llm_service") as mock_llm:
            mock_llm.generate_response = AsyncMock(
                side_effect=Exception("Planning error")
            )

            steps = await engine._plan_research_steps(session)

            # Should return basic fallback plan
            assert len(steps) == 3
            assert steps[0].step_type == ResearchStepType.INITIAL_ANALYSIS
            assert steps[1].step_type == ResearchStepType.CONTEXT_GATHERING
            assert steps[2].step_type == ResearchStepType.FINAL_SUMMARY

    @pytest.mark.asyncio
    async def test_calculate_step_confidence(self, engine):
        """Test step confidence calculation"""
        # High confidence step with sources and result
        step_high = ResearchStep(
            result="A very detailed and comprehensive result that demonstrates thorough analysis",
            sources=[
                {"score": 0.9, "title": "High quality source"},
                {"score": 0.8, "title": "Good source"},
            ],
        )
        confidence_high = engine._calculate_step_confidence(step_high)
        assert 0.8 <= confidence_high <= 1.0

        # Low confidence step with no sources
        step_low = ResearchStep(result="Short result", sources=[])
        confidence_low = engine._calculate_step_confidence(step_low)
        assert 0.3 <= confidence_low <= 0.7

    @pytest.mark.asyncio
    async def test_get_session_status_existing(self, engine, sample_query):
        """Test getting status of existing session"""
        session = await engine.start_research(query=sample_query)

        status = await engine.get_session_status(session.session_id)

        assert status is not None
        assert status["session_id"] == session.session_id
        assert status["status"] == ResearchStatus.CREATED.value
        assert "current_step" in status
        assert "total_steps" in status
        assert "progress" in status

    @pytest.mark.asyncio
    async def test_get_session_status_nonexistent(self, engine):
        """Test getting status of non-existent session"""
        status = await engine.get_session_status("non_existent_id")
        assert status is None

    @pytest.mark.asyncio
    async def test_cancel_research_existing(self, engine, sample_query):
        """Test cancelling existing research session"""
        session = await engine.start_research(query=sample_query)

        success = await engine.cancel_research(session.session_id)

        assert success is True
        updated_session = engine.active_sessions[session.session_id]
        assert updated_session.status == ResearchStatus.CANCELLED
        assert updated_session.completed_at is not None

    @pytest.mark.asyncio
    async def test_cancel_research_nonexistent(self, engine):
        """Test cancelling non-existent research session"""
        success = await engine.cancel_research("non_existent_id")
        assert success is False

    @pytest.mark.asyncio
    async def test_get_engine_status(self, engine):
        """Test getting engine status"""
        status = await engine.get_engine_status()

        assert status["engine_status"] == "active"
        assert "active_sessions" in status
        assert "metrics" in status
        assert "configuration" in status
        assert "last_updated" in status

        # Check configuration values
        config = status["configuration"]
        assert (
            config["max_concurrent_sessions"]
            == engine.config["max_concurrent_sessions"]
        )
        assert config["default_max_steps"] == engine.config["default_max_steps"]

    @pytest.mark.asyncio
    async def test_update_metrics(self, engine):
        """Test metrics updating"""
        # Create a completed session
        session = ResearchSession(
            status=ResearchStatus.COMPLETED,
            duration=10.5,
            steps=[ResearchStep(), ResearchStep()],
        )

        initial_completed = engine.metrics["completed_sessions"]
        engine._update_metrics(session)

        assert engine.metrics["completed_sessions"] == initial_completed + 1
        assert engine.metrics["success_rate"] > 0

    @pytest.mark.asyncio
    async def test_build_step_context(self, engine):
        """Test building context for research step"""
        session = ResearchSession(
            original_query="Test query", research_goal="Test goal"
        )

        # Add some completed steps
        completed_step = ResearchStep(
            title="Previous step", result="Previous result", status=StepStatus.COMPLETED
        )
        session.steps = [completed_step]

        current_step = ResearchStep(
            title="Current step",
            sources=[
                {"title": "Source 1", "content": "Content 1"},
                {"title": "Source 2", "content": "Content 2"},
            ],
        )

        context = engine._build_step_context(current_step, session)

        assert "Test query" in context
        assert "Test goal" in context
        assert "Current step" in context
        assert "Previous step" in context
        assert "Source 1" in context

    @pytest.mark.asyncio
    async def test_build_step_prompt(self, engine):
        """Test building prompt for research step"""
        step = ResearchStep(step_type=ResearchStepType.DEEP_ANALYSIS)
        context = "Test context information"

        prompt = engine._build_step_prompt(step, context)

        assert "углубленный анализ" in prompt.lower()
        assert context in prompt
        assert "конкретным и обоснованным" in prompt

    @pytest.mark.asyncio
    async def test_suggest_next_steps_success(self, engine):
        """Test successful next steps suggestion"""
        step = ResearchStep(
            result="Analysis shows need for security review and performance testing"
        )
        session = ResearchSession()

        with patch.object(engine, "llm_service") as mock_llm:
            mock_llm.generate_response = AsyncMock(
                return_value="1. Conduct security audit\n2. Perform load testing\n3. Review deployment process"
            )

            suggestions = await engine._suggest_next_steps(step, session)

            assert len(suggestions) <= 3
            assert all(isinstance(s, str) for s in suggestions)

    @pytest.mark.asyncio
    async def test_suggest_next_steps_fallback(self, engine):
        """Test next steps suggestion fallback"""
        step = ResearchStep(result="Test result")
        session = ResearchSession()

        with patch.object(engine, "llm_service") as mock_llm:
            mock_llm.generate_response = AsyncMock(
                side_effect=Exception("Generation error")
            )

            suggestions = await engine._suggest_next_steps(step, session)

            assert len(suggestions) == 2
            assert "углубленный анализ" in suggestions[0]
            assert "дополнительные источники" in suggestions[1]

    @pytest.mark.asyncio
    async def test_adapt_next_steps_low_confidence(self, engine):
        """Test adaptive step planning for low confidence"""
        session = ResearchSession(max_steps=5)
        current_step = ResearchStep(confidence=0.3)  # Low confidence
        next_step = ResearchStep()

        session.steps = [current_step, next_step]

        await engine._adapt_next_steps(session, 0)

        # Should have inserted a validation step
        assert len(session.steps) == 3
        assert session.steps[1].step_type == ResearchStepType.VALIDATION

    @pytest.mark.asyncio
    async def test_adapt_next_steps_high_confidence(self, engine):
        """Test adaptive step planning for high confidence"""
        session = ResearchSession(max_steps=5)
        current_step = ResearchStep(confidence=0.9)  # High confidence
        next_step = ResearchStep()

        session.steps = [current_step, next_step]
        initial_length = len(session.steps)

        await engine._adapt_next_steps(session, 0)

        # Should not have inserted additional steps
        assert len(session.steps) == initial_length

    @pytest.mark.asyncio
    async def test_is_research_complete_high_confidence(self, engine):
        """Test research completion check with high confidence"""
        session = ResearchSession(max_steps=5)
        step = ResearchStep(
            confidence=0.9,
            result="Very detailed comprehensive result with lots of information and thorough analysis",
        )

        is_complete = await engine._is_research_complete(session, step)
        assert is_complete is True

    @pytest.mark.asyncio
    async def test_is_research_complete_many_steps(self, engine):
        """Test research completion check with many completed steps"""
        session = ResearchSession(max_steps=5)

        # Add completed steps
        for i in range(4):  # 80% of max_steps
            step = ResearchStep(status=StepStatus.COMPLETED, confidence=0.8)
            session.steps.append(step)

        last_step = ResearchStep(confidence=0.7)

        is_complete = await engine._is_research_complete(session, last_step)
        assert is_complete is True

    @pytest.mark.asyncio
    async def test_is_research_complete_not_ready(self, engine):
        """Test research completion check when not ready"""
        session = ResearchSession(max_steps=5)
        step = ResearchStep(confidence=0.4, result="Short result")

        is_complete = await engine._is_research_complete(session, step)
        assert is_complete is False


class TestResearchModels:
    """Test cases for research data models"""

    def test_research_step_creation(self):
        """Test ResearchStep creation with defaults"""
        step = ResearchStep()

        assert step.step_id is not None
        assert step.step_type == ResearchStepType.INITIAL_ANALYSIS
        assert step.status == StepStatus.PENDING
        assert step.confidence == 0.0
        assert step.sources == []
        assert isinstance(step.created_at, datetime)

    def test_research_session_creation(self):
        """Test ResearchSession creation with defaults"""
        session = ResearchSession()

        assert session.session_id is not None
        assert session.status == ResearchStatus.CREATED
        assert session.current_step == 0
        assert session.max_steps == 7
        assert session.steps == []
        assert isinstance(session.created_at, datetime)

    def test_research_step_types(self):
        """Test all research step types are accessible"""
        types = [
            ResearchStepType.INITIAL_ANALYSIS,
            ResearchStepType.CONTEXT_GATHERING,
            ResearchStepType.DEEP_ANALYSIS,
            ResearchStepType.SYNTHESIS,
            ResearchStepType.VALIDATION,
            ResearchStepType.FINAL_SUMMARY,
        ]

        for step_type in types:
            step = ResearchStep(step_type=step_type)
            assert step.step_type == step_type

    def test_research_statuses(self):
        """Test all research statuses are accessible"""
        statuses = [
            ResearchStatus.CREATED,
            ResearchStatus.IN_PROGRESS,
            ResearchStatus.COMPLETED,
            ResearchStatus.FAILED,
            ResearchStatus.CANCELLED,
        ]

        for status in statuses:
            session = ResearchSession(status=status)
            assert session.status == status


class TestGlobalEngine:
    """Test cases for global engine instance"""

    @pytest.mark.asyncio
    async def test_get_deep_research_engine_singleton(self):
        """Test that get_deep_research_engine returns singleton"""
        engine1 = await get_deep_research_engine()
        engine2 = await get_deep_research_engine()

        assert engine1 is engine2
        assert isinstance(engine1, DeepResearchEngine)

    @pytest.mark.asyncio
    async def test_global_engine_initialization(self):
        """Test global engine is properly initialized"""
        engine = await get_deep_research_engine()

        assert engine.active_sessions == {}
        assert engine.metrics["total_sessions"] >= 0
        assert engine.config["max_concurrent_sessions"] > 0


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_empty_query(self):
        """Test handling of empty query"""
        engine = DeepResearchEngine()

        # Empty query should still create a session
        session = await engine.start_research(query="")
        assert session.original_query == ""

    @pytest.mark.asyncio
    async def test_very_long_query(self):
        """Test handling of very long query"""
        engine = DeepResearchEngine()
        long_query = "x" * 10000  # Very long query

        session = await engine.start_research(query=long_query)
        assert session.original_query == long_query

    @pytest.mark.asyncio
    async def test_zero_max_steps(self):
        """Test handling of zero max steps"""
        engine = DeepResearchEngine()

        session = await engine.start_research(query="Test query", max_steps=0)
        assert session.max_steps == 0

    @pytest.mark.asyncio
    async def test_negative_max_steps(self):
        """Test handling of negative max steps"""
        engine = DeepResearchEngine()

        session = await engine.start_research(query="Test query", max_steps=-1)
        assert session.max_steps == -1  # Should accept whatever is passed


@pytest.mark.asyncio
class TestPerformance:
    """Performance-related test cases"""

    @pytest.mark.asyncio
    async def test_concurrent_sessions_creation(self):
        """Test creating multiple sessions concurrently"""
        engine = DeepResearchEngine()

        # Create tasks for concurrent session creation
        tasks = []
        for i in range(5):
            task = engine.start_research(query=f"Query {i}", user_id=f"user_{i}")
            tasks.append(task)

        # Execute all tasks concurrently
        sessions = await asyncio.gather(*tasks)

        assert len(sessions) == 5
        assert len(set(s.session_id for s in sessions)) == 5  # All unique IDs
        assert engine.metrics["total_sessions"] == 5

    @pytest.mark.asyncio
    async def test_session_cleanup_performance(self):
        """Test that session data doesn't accumulate indefinitely"""
        engine = DeepResearchEngine()

        # Create many sessions
        for i in range(20):
            await engine.start_research(query=f"Query {i}", user_id=f"user_{i}")

        assert len(engine.active_sessions) <= engine.config["max_concurrent_sessions"]


if __name__ == "__main__":
    pytest.main([__file__])
