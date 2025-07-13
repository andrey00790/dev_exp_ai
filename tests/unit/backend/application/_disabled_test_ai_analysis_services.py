"""
Unit Tests for AI Analysis Application Services

Tests for application layer use cases with mocked dependencies.
Following hexagonal architecture testing principles.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from backend.domain.ai_analysis.entities import (
    AnalysisSession, AnalysisRequest, AnalysisResult, AIModel,
    AnalysisMetrics, AnalysisType, AnalysisStatus, Priority
)
from backend.application.ai_analysis.services import (
    AIAnalysisApplicationService, ModelManagementService
)
from backend.application.ai_analysis.ports import (
    AnalysisRepositoryPort, ModelRepositoryPort, AIProviderPort,
    MetricsRepositoryPort, EventPublisherPort
)


class TestAIAnalysisApplicationService:
    """Test AIAnalysisApplicationService with mocked dependencies"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        return {
            'analysis_repository': AsyncMock(spec=AnalysisRepositoryPort),
            'model_repository': AsyncMock(spec=ModelRepositoryPort),
            'metrics_repository': AsyncMock(spec=MetricsRepositoryPort),
            'ai_provider': AsyncMock(spec=AIProviderPort),
            'event_publisher': AsyncMock(spec=EventPublisherPort)
        }
    
    @pytest.fixture
    def ai_analysis_service(self, mock_repositories):
        """Create AIAnalysisApplicationService with mocked dependencies"""
        return AIAnalysisApplicationService(**mock_repositories)
    
    @pytest.fixture
    def sample_analysis_request(self):
        """Create sample analysis request for testing"""
        return AnalysisRequest(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            priority=Priority.MEDIUM,
            user_id="user_123",
            project_id="project_456"
        )
    
    @pytest.fixture
    def sample_ai_model(self):
        """Create sample AI model for testing"""
        return AIModel(
            id="model_123",
            name="CodeAnalyzer",
            version="1.0.0",
            model_type="transformer",
            capabilities={AnalysisType.CODE_ANALYSIS, AnalysisType.QUALITY_ANALYSIS}
        )
    
    @pytest.fixture
    def sample_analysis_result(self):
        """Create sample analysis result for testing"""
        return AnalysisResult(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            content="def hello(): pass",
            score=0.85,
            confidence=0.92,
            suggestions=["Add type hints", "Add docstring"],
            metadata={"language": "python", "complexity": "low"}
        )
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_start_analysis_success(self, ai_analysis_service, mock_repositories, 
                                         sample_analysis_request, sample_ai_model):
        """Test successful analysis start"""
        # Setup mocks
        mock_repositories['model_repository'].find_by_capability.return_value = sample_ai_model
        mock_repositories['analysis_repository'].save.return_value = None
        mock_repositories['event_publisher'].publish.return_value = None
        
        # Execute
        session = await ai_analysis_service.start_analysis(sample_analysis_request)
        
        # Verify
        assert session.request == sample_analysis_request
        assert session.status == AnalysisStatus.RUNNING
        assert session.started_at is not None
        
        # Verify repository calls
        mock_repositories['model_repository'].find_by_capability.assert_called_once_with(
            AnalysisType.CODE_ANALYSIS
        )
        mock_repositories['analysis_repository'].save.assert_called_once()
        mock_repositories['event_publisher'].publish.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_start_analysis_no_model_available_fails(self, ai_analysis_service, 
                                                          mock_repositories, sample_analysis_request):
        """Test analysis start fails when no model is available"""
        # Setup mocks
        mock_repositories['model_repository'].find_by_capability.return_value = None
        
        # Execute & Verify
        with pytest.raises(ValueError, match="No model available for analysis type"):
            await ai_analysis_service.start_analysis(sample_analysis_request)
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_start_analysis_inactive_model_fails(self, ai_analysis_service, 
                                                      mock_repositories, sample_analysis_request):
        """Test analysis start fails when model is inactive"""
        # Setup mocks
        inactive_model = AIModel(
            id="model_123",
            name="CodeAnalyzer",
            version="1.0.0",
            model_type="transformer",
            capabilities={AnalysisType.CODE_ANALYSIS},
            is_active=False
        )
        mock_repositories['model_repository'].find_by_capability.return_value = inactive_model
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Model is not active"):
            await ai_analysis_service.start_analysis(sample_analysis_request)
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_process_analysis_success(self, ai_analysis_service, mock_repositories, 
                                          sample_analysis_request, sample_ai_model, 
                                          sample_analysis_result):
        """Test successful analysis processing"""
        # Setup session
        session = AnalysisSession(
            id=str(uuid4()),
            request=sample_analysis_request
        )
        session.start_analysis()
        
        # Setup mocks
        mock_repositories['ai_provider'].analyze.return_value = sample_analysis_result
        mock_repositories['analysis_repository'].save.return_value = None
        mock_repositories['event_publisher'].publish.return_value = None
        
        # Execute
        result = await ai_analysis_service.process_analysis(session, sample_ai_model)
        
        # Verify
        assert result == sample_analysis_result
        assert len(session.results) == 1
        assert session.results[0] == sample_analysis_result
        assert session.status == AnalysisStatus.COMPLETED
        assert session.completed_at is not None
        
        # Verify repository calls
        mock_repositories['ai_provider'].analyze.assert_called_once_with(
            sample_analysis_request.content,
            sample_ai_model,
            sample_analysis_request.parameters
        )
        mock_repositories['analysis_repository'].save.assert_called()
        mock_repositories['event_publisher'].publish.assert_called()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_process_analysis_ai_provider_failure(self, ai_analysis_service, 
                                                       mock_repositories, sample_analysis_request, 
                                                       sample_ai_model):
        """Test analysis processing with AI provider failure"""
        # Setup session
        session = AnalysisSession(
            id=str(uuid4()),
            request=sample_analysis_request
        )
        session.start_analysis()
        
        # Setup mocks
        mock_repositories['ai_provider'].analyze.side_effect = Exception("AI provider error")
        mock_repositories['analysis_repository'].save.return_value = None
        mock_repositories['event_publisher'].publish.return_value = None
        
        # Execute & Verify
        with pytest.raises(Exception, match="AI provider error"):
            await ai_analysis_service.process_analysis(session, sample_ai_model)
        
        # Verify session was marked as failed
        assert session.status == AnalysisStatus.FAILED
        assert session.error_message == "AI provider error"
        assert session.completed_at is not None
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_analysis_by_id_success(self, ai_analysis_service, mock_repositories, 
                                            sample_analysis_request):
        """Test successful analysis retrieval by ID"""
        # Setup
        session = AnalysisSession(
            id="session_123",
            request=sample_analysis_request
        )
        mock_repositories['analysis_repository'].find_by_id.return_value = session
        
        # Execute
        result = await ai_analysis_service.get_analysis_by_id("session_123")
        
        # Verify
        assert result == session
        mock_repositories['analysis_repository'].find_by_id.assert_called_once_with("session_123")
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_analysis_by_id_not_found(self, ai_analysis_service, mock_repositories):
        """Test analysis retrieval by ID when not found"""
        # Setup
        mock_repositories['analysis_repository'].find_by_id.return_value = None
        
        # Execute
        result = await ai_analysis_service.get_analysis_by_id("nonexistent_id")
        
        # Verify
        assert result is None
        mock_repositories['analysis_repository'].find_by_id.assert_called_once_with("nonexistent_id")
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_analyses_by_user_success(self, ai_analysis_service, mock_repositories, 
                                              sample_analysis_request):
        """Test successful analysis retrieval by user"""
        # Setup
        session1 = AnalysisSession(id="session_1", request=sample_analysis_request)
        session2 = AnalysisSession(id="session_2", request=sample_analysis_request)
        mock_repositories['analysis_repository'].find_by_user_id.return_value = [session1, session2]
        
        # Execute
        results = await ai_analysis_service.get_analyses_by_user("user_123")
        
        # Verify
        assert len(results) == 2
        assert results[0] == session1
        assert results[1] == session2
        mock_repositories['analysis_repository'].find_by_user_id.assert_called_once_with("user_123")
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_analyses_by_user_empty(self, ai_analysis_service, mock_repositories):
        """Test analysis retrieval by user when empty"""
        # Setup
        mock_repositories['analysis_repository'].find_by_user_id.return_value = []
        
        # Execute
        results = await ai_analysis_service.get_analyses_by_user("user_123")
        
        # Verify
        assert len(results) == 0
        mock_repositories['analysis_repository'].find_by_user_id.assert_called_once_with("user_123")
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_cancel_analysis_success(self, ai_analysis_service, mock_repositories, 
                                         sample_analysis_request):
        """Test successful analysis cancellation"""
        # Setup
        session = AnalysisSession(
            id="session_123",
            request=sample_analysis_request
        )
        session.start_analysis()
        
        mock_repositories['analysis_repository'].find_by_id.return_value = session
        mock_repositories['analysis_repository'].save.return_value = None
        mock_repositories['event_publisher'].publish.return_value = None
        
        # Execute
        cancelled_session = await ai_analysis_service.cancel_analysis("session_123")
        
        # Verify
        assert cancelled_session.status == AnalysisStatus.CANCELLED
        assert cancelled_session.completed_at is not None
        mock_repositories['analysis_repository'].save.assert_called_once()
        mock_repositories['event_publisher'].publish.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_cancel_analysis_not_found(self, ai_analysis_service, mock_repositories):
        """Test analysis cancellation when session not found"""
        # Setup
        mock_repositories['analysis_repository'].find_by_id.return_value = None
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Analysis session not found"):
            await ai_analysis_service.cancel_analysis("nonexistent_id")
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_cancel_analysis_already_completed(self, ai_analysis_service, mock_repositories, 
                                                   sample_analysis_request):
        """Test analysis cancellation when already completed"""
        # Setup
        session = AnalysisSession(
            id="session_123",
            request=sample_analysis_request
        )
        session.start_analysis()
        session.complete_analysis()
        
        mock_repositories['analysis_repository'].find_by_id.return_value = session
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Cannot cancel analysis in completed status"):
            await ai_analysis_service.cancel_analysis("session_123")
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_analysis_metrics_success(self, ai_analysis_service, mock_repositories):
        """Test successful analysis metrics retrieval"""
        # Setup
        metrics = AnalysisMetrics(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            total_analyses=10,
            successful_analyses=8,
            failed_analyses=2
        )
        mock_repositories['metrics_repository'].find_by_analysis_type.return_value = metrics
        
        # Execute
        result = await ai_analysis_service.get_analysis_metrics(AnalysisType.CODE_ANALYSIS)
        
        # Verify
        assert result == metrics
        mock_repositories['metrics_repository'].find_by_analysis_type.assert_called_once_with(
            AnalysisType.CODE_ANALYSIS
        )
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_analysis_metrics_not_found(self, ai_analysis_service, mock_repositories):
        """Test analysis metrics retrieval when not found"""
        # Setup
        mock_repositories['metrics_repository'].find_by_analysis_type.return_value = None
        
        # Execute
        result = await ai_analysis_service.get_analysis_metrics(AnalysisType.CODE_ANALYSIS)
        
        # Verify
        assert result is None
        mock_repositories['metrics_repository'].find_by_analysis_type.assert_called_once_with(
            AnalysisType.CODE_ANALYSIS
        )
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_record_analysis_metrics_success(self, ai_analysis_service, mock_repositories, 
                                                 sample_analysis_request):
        """Test successful analysis metrics recording"""
        # Setup
        session = AnalysisSession(
            id="session_123",
            request=sample_analysis_request
        )
        session.start_analysis()
        session.complete_analysis()
        
        existing_metrics = AnalysisMetrics(
            id=str(uuid4()),
            analysis_type=AnalysisType.CODE_ANALYSIS,
            total_analyses=5,
            successful_analyses=4,
            failed_analyses=1
        )
        
        mock_repositories['metrics_repository'].find_by_analysis_type.return_value = existing_metrics
        mock_repositories['metrics_repository'].save.return_value = None
        
        # Execute
        await ai_analysis_service.record_analysis_metrics(session)
        
        # Verify
        assert existing_metrics.total_analyses == 6  # Incremented
        assert existing_metrics.successful_analyses == 5  # Incremented
        mock_repositories['metrics_repository'].save.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_record_analysis_metrics_create_new(self, ai_analysis_service, mock_repositories, 
                                                    sample_analysis_request):
        """Test analysis metrics recording when no existing metrics"""
        # Setup
        session = AnalysisSession(
            id="session_123",
            request=sample_analysis_request
        )
        session.start_analysis()
        session.complete_analysis()
        
        mock_repositories['metrics_repository'].find_by_analysis_type.return_value = None
        mock_repositories['metrics_repository'].save.return_value = None
        
        # Execute
        await ai_analysis_service.record_analysis_metrics(session)
        
        # Verify
        # Should create new metrics and save
        mock_repositories['metrics_repository'].save.assert_called_once()
        
        # Verify the metrics object that was saved
        saved_metrics = mock_repositories['metrics_repository'].save.call_args[0][0]
        assert saved_metrics.analysis_type == AnalysisType.CODE_ANALYSIS
        assert saved_metrics.total_analyses == 1
        assert saved_metrics.successful_analyses == 1
        assert saved_metrics.failed_analyses == 0


class TestModelManagementService:
    """Test ModelManagementService with mocked dependencies"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        return {
            'model_repository': AsyncMock(spec=ModelRepositoryPort),
            'event_publisher': AsyncMock(spec=EventPublisherPort)
        }
    
    @pytest.fixture
    def model_management_service(self, mock_repositories):
        """Create ModelManagementService with mocked dependencies"""
        return ModelManagementService(**mock_repositories)
    
    @pytest.fixture
    def sample_ai_model(self):
        """Create sample AI model for testing"""
        return AIModel(
            id="model_123",
            name="CodeAnalyzer",
            version="1.0.0",
            model_type="transformer",
            capabilities={AnalysisType.CODE_ANALYSIS, AnalysisType.QUALITY_ANALYSIS}
        )
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_create_model_success(self, model_management_service, mock_repositories):
        """Test successful model creation"""
        # Setup
        mock_repositories['model_repository'].save.return_value = None
        mock_repositories['event_publisher'].publish.return_value = None
        
        # Execute
        model = await model_management_service.create_model(
            name="CodeAnalyzer",
            version="1.0.0",
            model_type="transformer",
            capabilities={AnalysisType.CODE_ANALYSIS}
        )
        
        # Verify
        assert model.name == "CodeAnalyzer"
        assert model.version == "1.0.0"
        assert model.model_type == "transformer"
        assert AnalysisType.CODE_ANALYSIS in model.capabilities
        assert model.is_active == True
        
        # Verify repository calls
        mock_repositories['model_repository'].save.assert_called_once()
        mock_repositories['event_publisher'].publish.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_create_model_empty_name_fails(self, model_management_service, mock_repositories):
        """Test model creation fails with empty name"""
        # Execute & Verify
        with pytest.raises(ValueError, match="Model name cannot be empty"):
            await model_management_service.create_model(
                name="",
                version="1.0.0",
                model_type="transformer",
                capabilities={AnalysisType.CODE_ANALYSIS}
            )
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_create_model_empty_version_fails(self, model_management_service, mock_repositories):
        """Test model creation fails with empty version"""
        # Execute & Verify
        with pytest.raises(ValueError, match="Model version cannot be empty"):
            await model_management_service.create_model(
                name="CodeAnalyzer",
                version="",
                model_type="transformer",
                capabilities={AnalysisType.CODE_ANALYSIS}
            )
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_model_by_id_success(self, model_management_service, mock_repositories, 
                                         sample_ai_model):
        """Test successful model retrieval by ID"""
        # Setup
        mock_repositories['model_repository'].find_by_id.return_value = sample_ai_model
        
        # Execute
        result = await model_management_service.get_model_by_id("model_123")
        
        # Verify
        assert result == sample_ai_model
        mock_repositories['model_repository'].find_by_id.assert_called_once_with("model_123")
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_model_by_id_not_found(self, model_management_service, mock_repositories):
        """Test model retrieval by ID when not found"""
        # Setup
        mock_repositories['model_repository'].find_by_id.return_value = None
        
        # Execute
        result = await model_management_service.get_model_by_id("nonexistent_id")
        
        # Verify
        assert result is None
        mock_repositories['model_repository'].find_by_id.assert_called_once_with("nonexistent_id")
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_models_by_capability_success(self, model_management_service, 
                                                   mock_repositories, sample_ai_model):
        """Test successful model retrieval by capability"""
        # Setup
        mock_repositories['model_repository'].find_by_capability.return_value = [sample_ai_model]
        
        # Execute
        results = await model_management_service.get_models_by_capability(AnalysisType.CODE_ANALYSIS)
        
        # Verify
        assert len(results) == 1
        assert results[0] == sample_ai_model
        mock_repositories['model_repository'].find_by_capability.assert_called_once_with(
            AnalysisType.CODE_ANALYSIS
        )
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_models_by_capability_empty(self, model_management_service, mock_repositories):
        """Test model retrieval by capability when empty"""
        # Setup
        mock_repositories['model_repository'].find_by_capability.return_value = []
        
        # Execute
        results = await model_management_service.get_models_by_capability(AnalysisType.CODE_ANALYSIS)
        
        # Verify
        assert len(results) == 0
        mock_repositories['model_repository'].find_by_capability.assert_called_once_with(
            AnalysisType.CODE_ANALYSIS
        )
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_activate_model_success(self, model_management_service, mock_repositories, 
                                        sample_ai_model):
        """Test successful model activation"""
        # Setup
        sample_ai_model.is_active = False
        mock_repositories['model_repository'].find_by_id.return_value = sample_ai_model
        mock_repositories['model_repository'].save.return_value = None
        mock_repositories['event_publisher'].publish.return_value = None
        
        # Execute
        activated_model = await model_management_service.activate_model("model_123")
        
        # Verify
        assert activated_model.is_active == True
        mock_repositories['model_repository'].save.assert_called_once()
        mock_repositories['event_publisher'].publish.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_activate_model_not_found(self, model_management_service, mock_repositories):
        """Test model activation when not found"""
        # Setup
        mock_repositories['model_repository'].find_by_id.return_value = None
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Model not found"):
            await model_management_service.activate_model("nonexistent_id")
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_activate_model_already_active(self, model_management_service, mock_repositories, 
                                                sample_ai_model):
        """Test model activation when already active"""
        # Setup
        sample_ai_model.is_active = True
        mock_repositories['model_repository'].find_by_id.return_value = sample_ai_model
        
        # Execute
        activated_model = await model_management_service.activate_model("model_123")
        
        # Verify
        assert activated_model.is_active == True
        # Should not save or publish events if already active
        mock_repositories['model_repository'].save.assert_not_called()
        mock_repositories['event_publisher'].publish.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_deactivate_model_success(self, model_management_service, mock_repositories, 
                                          sample_ai_model):
        """Test successful model deactivation"""
        # Setup
        sample_ai_model.is_active = True
        mock_repositories['model_repository'].find_by_id.return_value = sample_ai_model
        mock_repositories['model_repository'].save.return_value = None
        mock_repositories['event_publisher'].publish.return_value = None
        
        # Execute
        deactivated_model = await model_management_service.deactivate_model("model_123")
        
        # Verify
        assert deactivated_model.is_active == False
        mock_repositories['model_repository'].save.assert_called_once()
        mock_repositories['event_publisher'].publish.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_deactivate_model_not_found(self, model_management_service, mock_repositories):
        """Test model deactivation when not found"""
        # Setup
        mock_repositories['model_repository'].find_by_id.return_value = None
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Model not found"):
            await model_management_service.deactivate_model("nonexistent_id")
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_deactivate_model_already_inactive(self, model_management_service, 
                                                    mock_repositories, sample_ai_model):
        """Test model deactivation when already inactive"""
        # Setup
        sample_ai_model.is_active = False
        mock_repositories['model_repository'].find_by_id.return_value = sample_ai_model
        
        # Execute
        deactivated_model = await model_management_service.deactivate_model("model_123")
        
        # Verify
        assert deactivated_model.is_active == False
        # Should not save or publish events if already inactive
        mock_repositories['model_repository'].save.assert_not_called()
        mock_repositories['event_publisher'].publish.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_delete_model_success(self, model_management_service, mock_repositories, 
                                      sample_ai_model):
        """Test successful model deletion"""
        # Setup
        mock_repositories['model_repository'].find_by_id.return_value = sample_ai_model
        mock_repositories['model_repository'].delete.return_value = True
        mock_repositories['event_publisher'].publish.return_value = None
        
        # Execute
        deleted = await model_management_service.delete_model("model_123")
        
        # Verify
        assert deleted == True
        mock_repositories['model_repository'].delete.assert_called_once_with("model_123")
        mock_repositories['event_publisher'].publish.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_delete_model_not_found(self, model_management_service, mock_repositories):
        """Test model deletion when not found"""
        # Setup
        mock_repositories['model_repository'].find_by_id.return_value = None
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Model not found"):
            await model_management_service.delete_model("nonexistent_id")
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_all_models_success(self, model_management_service, mock_repositories, 
                                        sample_ai_model):
        """Test successful retrieval of all models"""
        # Setup
        model1 = sample_ai_model
        model2 = AIModel(
            id="model_456",
            name="SecurityAnalyzer",
            version="2.0.0",
            model_type="neural_network",
            capabilities={AnalysisType.SECURITY_ANALYSIS}
        )
        mock_repositories['model_repository'].find_all.return_value = [model1, model2]
        
        # Execute
        results = await model_management_service.get_all_models()
        
        # Verify
        assert len(results) == 2
        assert results[0] == model1
        assert results[1] == model2
        mock_repositories['model_repository'].find_all.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_all_models_empty(self, model_management_service, mock_repositories):
        """Test retrieval of all models when empty"""
        # Setup
        mock_repositories['model_repository'].find_all.return_value = []
        
        # Execute
        results = await model_management_service.get_all_models()
        
        # Verify
        assert len(results) == 0
        mock_repositories['model_repository'].find_all.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_active_models_success(self, model_management_service, mock_repositories):
        """Test successful retrieval of active models"""
        # Setup
        active_model = AIModel(
            id="model_123",
            name="CodeAnalyzer",
            version="1.0.0",
            model_type="transformer",
            capabilities={AnalysisType.CODE_ANALYSIS},
            is_active=True
        )
        mock_repositories['model_repository'].find_active.return_value = [active_model]
        
        # Execute
        results = await model_management_service.get_active_models()
        
        # Verify
        assert len(results) == 1
        assert results[0] == active_model
        mock_repositories['model_repository'].find_active.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_active_models_empty(self, model_management_service, mock_repositories):
        """Test retrieval of active models when empty"""
        # Setup
        mock_repositories['model_repository'].find_active.return_value = []
        
        # Execute
        results = await model_management_service.get_active_models()
        
        # Verify
        assert len(results) == 0
        mock_repositories['model_repository'].find_active.assert_called_once() 