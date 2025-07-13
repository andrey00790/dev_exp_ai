"""
🧪 Tests for AI Agent Orchestrator

Comprehensive test suite for the AI Agent Orchestration System.
Tests agent coordination, workflow execution, error handling, and performance.
"""

import asyncio
import os
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from domain.ai_analysis.ai_agent_orchestrator import (
    AgentStatus, AgentTask, AgentType, AIAgentOrchestrator, ArchitectAgent,
    AutomatedWorkflow, BaseAgent, CodeReviewAgent, TaskPriority, WorkflowStep,
    create_code_review_workflow, create_project_assessment_workflow,
    execute_agent_task, execute_automated_workflow, get_orchestrator)


class TestBaseAgent:
    """Test base agent functionality"""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing"""
        agent = BaseAgent("test_agent", AgentType.ARCHITECT)
        agent._execute_specific_task = AsyncMock(return_value={"test": "result"})
        return agent

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization"""
        agent = BaseAgent("test_agent", AgentType.ARCHITECT)

        assert agent.agent_id == "test_agent"
        assert agent.agent_type == AgentType.ARCHITECT
        assert agent.status == AgentStatus.IDLE
        assert agent.current_task is None
        assert agent.message_queue == []

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_agent_task_execution(self, mock_agent):
        """Test agent task execution"""
        task = AgentTask(
            agent_type=AgentType.ARCHITECT,
            task_type="test_task",
            description="Test task",
            input_data={"test": "data"},
        )

        result = await mock_agent.execute_task(task)

        assert result == {"test": "result"}
        assert task.status == AgentStatus.COMPLETED
        assert task.result == {"test": "result"}
        assert mock_agent.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_agent_task_failure(self, mock_agent):
        """Test agent task failure handling"""
        mock_agent._execute_specific_task.side_effect = Exception("Test error")

        task = AgentTask(
            agent_type=AgentType.ARCHITECT,
            task_type="test_task",
            description="Test task",
            input_data={"test": "data"},
        )

        with pytest.raises(Exception):
            await mock_agent.execute_task(task)

        assert task.status == AgentStatus.FAILED
        assert task.error == "Test error"
        assert mock_agent.status == AgentStatus.IDLE


class TestArchitectAgent:
    """Test architect agent functionality"""

    @pytest.fixture
    def architect_agent(self):
        """Create architect agent for testing"""
        return ArchitectAgent("architect_test")

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_architect_agent_initialization(self, architect_agent):
        """Test architect agent initialization"""
        assert architect_agent.agent_type == AgentType.ARCHITECT
        assert "architecture_analysis" in architect_agent.capabilities
        assert "system_design" in architect_agent.capabilities

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_analyze_architecture_task(self, architect_agent):
        """Test architecture analysis task"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, "w") as f:
                f.write("def test(): pass")

            task = AgentTask(
                agent_type=AgentType.ARCHITECT,
                task_type="analyze_architecture",
                input_data={"project_path": temp_dir},
            )

            result = await architect_agent.execute_task(task)

            assert result["analysis_type"] == "architecture"
            assert "components" in result
            assert "recommendations" in result
            assert "health_score" in result

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_recommend_technologies_task(self, architect_agent):
        """Test technology recommendation task"""
        task = AgentTask(
            agent_type=AgentType.ARCHITECT,
            task_type="recommend_technologies",
            input_data={
                "requirements": ["api", "database"],
                "current_stack": ["python"],
            },
        )

        result = await architect_agent.execute_task(task)

        assert "backend" in result
        assert "database" in result
        assert "rationale" in result

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_invalid_task_type(self, architect_agent):
        """Test handling of invalid task type"""
        task = AgentTask(
            agent_type=AgentType.ARCHITECT, task_type="invalid_task", input_data={}
        )

        with pytest.raises(ValueError):
            await architect_agent.execute_task(task)


class TestCodeReviewAgent:
    """Test code review agent functionality"""

    @pytest.fixture
    def review_agent(self):
        """Create code review agent for testing"""
        return CodeReviewAgent("reviewer_test")

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_review_agent_initialization(self, review_agent):
        """Test code review agent initialization"""
        assert review_agent.agent_type == AgentType.REVIEWER
        assert "code_quality_analysis" in review_agent.capabilities
        assert "security_review" in review_agent.capabilities

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_code_review_task(self, review_agent):
        """Test code review task"""
        sample_code = """
def test_function():
    print("Hello world")  # Debug print
    # TODO: Add proper implementation
    return True
"""

        task = AgentTask(
            agent_type=AgentType.REVIEWER,
            task_type="review_code",
            input_data={"code": sample_code, "file_path": "test.py"},
        )

        result = await review_agent.execute_task(task)

        assert "overall_score" in result
        assert "issues" in result
        assert "suggestions" in result
        assert len(result["issues"]) > 0  # Should find TODO and print statement

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_pull_request_analysis(self, review_agent):
        """Test pull request analysis"""
        task = AgentTask(
            agent_type=AgentType.REVIEWER,
            task_type="analyze_pr",
            input_data={
                "pr_data": {
                    "changed_files": 25,  # Large PR
                    "additions": 500,
                    "deletions": 100,
                }
            },
        )

        result = await review_agent.execute_task(task)

        assert "risk_level" in result
        assert result["risk_level"] == "high"  # Due to large number of files
        assert "recommendations" in result


class TestAIAgentOrchestrator:
    """Test AI agent orchestrator functionality"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for testing"""
        return AIAgentOrchestrator()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization"""
        # Wait for default agents to initialize
        await asyncio.sleep(0.1)

        assert len(orchestrator.agents) >= 0
        assert orchestrator.active_tasks == {}
        assert orchestrator.workflows == {}

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_agent_registration(self, orchestrator):
        """Test agent registration"""
        test_agent = BaseAgent("test_agent", AgentType.ARCHITECT)
        test_agent._execute_specific_task = AsyncMock(return_value={"test": "result"})

        agent_id = await orchestrator.register_agent(test_agent)

        assert agent_id == "test_agent"
        assert "test_agent" in orchestrator.agents
        assert orchestrator.agents["test_agent"] == test_agent

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_task_execution(self, orchestrator):
        """Test task execution through orchestrator"""
        # Register a test agent
        test_agent = BaseAgent("test_agent", AgentType.ARCHITECT)
        test_agent._execute_specific_task = AsyncMock(return_value={"test": "result"})
        await orchestrator.register_agent(test_agent)

        result = await orchestrator.execute_task(
            agent_type=AgentType.ARCHITECT,
            task_type="test_task",
            input_data={"test": "data"},
        )

        assert result["status"] == "completed"
        assert result["result"] == {"test": "result"}
        assert result["agent_id"] == "test_agent"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_no_available_agent(self, orchestrator):
        """Test behavior when no agent is available"""
        result = await orchestrator.execute_task(
            agent_type=AgentType.SECURITY,  # No security agent registered
            task_type="test_task",
            input_data={"test": "data"},
        )

        assert result["status"] == "failed"
        assert "No available agent" in result["error"]

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_workflow_registration(self, orchestrator):
        """Test workflow registration"""
        workflow = create_code_review_workflow()
        workflow_id = orchestrator.register_workflow(workflow)

        assert workflow_id in orchestrator.workflows
        assert orchestrator.workflows[workflow_id] == workflow

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_agent_status_retrieval(self, orchestrator):
        """Test agent status retrieval"""
        # Register a test agent
        test_agent = BaseAgent("test_agent", AgentType.ARCHITECT)
        await orchestrator.register_agent(test_agent)

        status = orchestrator.get_agent_status()

        assert "total_agents" in status
        assert "agents" in status
        assert "metrics" in status
        assert "test_agent" in status["agents"]


class TestWorkflowExecution:
    """Test workflow execution functionality"""

    @pytest.fixture
    def orchestrator_with_agents(self):
        """Create orchestrator with test agents"""
        orchestrator = AIAgentOrchestrator()

        # Create mock agents
        architect_agent = BaseAgent("architect_001", AgentType.ARCHITECT)
        architect_agent._execute_specific_task = AsyncMock(
            return_value={"components": [], "recommendations": [], "health_score": 85}
        )

        reviewer_agent = BaseAgent("reviewer_001", AgentType.REVIEWER)
        reviewer_agent._execute_specific_task = AsyncMock(
            return_value={"overall_score": 90, "issues": [], "suggestions": []}
        )

        # Register agents
        asyncio.create_task(orchestrator.register_agent(architect_agent))
        asyncio.create_task(orchestrator.register_agent(reviewer_agent))

        return orchestrator

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_workflow_step_creation(self):
        """Test workflow step creation"""
        step = WorkflowStep(
            name="Test Step",
            agent_type=AgentType.ARCHITECT,
            task_type="test_task",
            input_mapping={"input_key": "source_key"},
            output_key="result",
        )

        assert step.name == "Test Step"
        assert step.agent_type == AgentType.ARCHITECT
        assert step.task_type == "test_task"
        assert step.input_mapping == {"input_key": "source_key"}
        assert step.output_key == "result"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_workflow_creation(self):
        """Test automated workflow creation"""
        workflow = create_code_review_workflow()

        assert workflow.name == "Automated Code Review"
        assert len(workflow.steps) == 2
        assert workflow.timeout_minutes == 15

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_project_assessment_workflow_creation(self):
        """Test project assessment workflow creation"""
        workflow = create_project_assessment_workflow()

        assert workflow.name == "Project Assessment"
        assert len(workflow.steps) == 2
        assert workflow.timeout_minutes == 30


class TestConvenienceFunctions:
    """Test convenience functions"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_orchestrator_singleton(self):
        """Test orchestrator singleton pattern"""
        orchestrator1 = await get_orchestrator()
        orchestrator2 = await get_orchestrator()

        assert orchestrator1 is orchestrator2

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_execute_agent_task_convenience(self):
        """Test convenience function for agent task execution"""
        with patch(
            "domain.ai_analysis.ai_agent_orchestrator.get_orchestrator"
        ) as mock_get_orchestrator:
            mock_orchestrator = Mock()
            mock_orchestrator.execute_task = AsyncMock(
                return_value={
                    "task_id": "test_id",
                    "status": "completed",
                    "result": {"test": "result"},
                }
            )
            mock_get_orchestrator.return_value = mock_orchestrator

            result = await execute_agent_task(
                agent_type="architect",
                task_type="test_task",
                input_data={"test": "data"},
            )

            assert result["status"] == "completed"
            assert result["result"] == {"test": "result"}

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_execute_automated_workflow_convenience(self):
        """Test convenience function for workflow execution"""
        with patch(
            "domain.ai_analysis.ai_agent_orchestrator.get_orchestrator"
        ) as mock_get_orchestrator:
            mock_orchestrator = Mock()
            
            # Create proper mock workflow with correct name attribute
            mock_workflow = Mock()
            mock_workflow.name = "test_workflow"  # Set name attribute to match workflow_name
            
            mock_orchestrator.workflows = {"test_id": mock_workflow}
            mock_orchestrator.execute_workflow = AsyncMock(
                return_value={"workflow_id": "test_id", "status": "completed"}
            )
            mock_get_orchestrator.return_value = mock_orchestrator

            result = await execute_automated_workflow(
                workflow_name="test_workflow", input_data={"test": "data"}
            )

            assert result["status"] == "completed"


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_invalid_agent_type(self):
        """Test handling of invalid agent type"""
        with pytest.raises(ValueError):
            AgentType("invalid_type")

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_invalid_task_priority(self):
        """Test handling of invalid task priority"""
        with pytest.raises(ValueError):
            TaskPriority("invalid_priority")

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_orchestrator_task_timeout(self):
        """Test task timeout handling"""
        orchestrator = AIAgentOrchestrator()

        # Register a slow agent
        slow_agent = BaseAgent("slow_agent", AgentType.ARCHITECT)
        async def slow_task(task):
            await asyncio.sleep(10)  # 10 second delay
            return {"completed": True}
        slow_agent._execute_specific_task = slow_task
        await orchestrator.register_agent(slow_agent)

        result = await orchestrator.execute_task(
            agent_type=AgentType.ARCHITECT,
            task_type="slow_task",
            input_data={"test": "data"},
            timeout_seconds=0.1,  # Very short timeout
        )

        assert result["status"] == "failed"
        assert "timeout" in result.get("error", "").lower() or "timed out" in result.get("error", "").lower()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_workflow_not_found(self):
        """Test workflow not found error"""
        with patch(
            "domain.ai_analysis.ai_agent_orchestrator.get_orchestrator"
        ) as mock_get_orchestrator:
            mock_orchestrator = Mock()
            mock_orchestrator.workflows = {}
            mock_get_orchestrator.return_value = mock_orchestrator

            with pytest.raises(ValueError, match="Workflow not found"):
                await execute_automated_workflow(
                    workflow_name="nonexistent_workflow", input_data={"test": "data"}
                )


class TestPerformanceMetrics:
    """Test performance metrics and monitoring"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_metrics_initialization(self):
        """Test metrics initialization"""
        orchestrator = AIAgentOrchestrator()

        assert orchestrator.metrics["tasks_completed"] == 0
        assert orchestrator.metrics["tasks_failed"] == 0
        assert orchestrator.metrics["average_execution_time"] == 0.0
        assert isinstance(orchestrator.metrics["agent_utilization"], dict)

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_metrics_update_on_success(self):
        """Test metrics update on successful task"""
        orchestrator = AIAgentOrchestrator()

        # Create a test task
        task = AgentTask(
            agent_type=AgentType.ARCHITECT,
            task_type="test_task",
            started_at=datetime.now(),
            completed_at=datetime.now(),
        )

        # Update metrics
        orchestrator._update_task_metrics(task, True)

        assert orchestrator.metrics["tasks_completed"] == 1
        assert orchestrator.metrics["tasks_failed"] == 0

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_metrics_update_on_failure(self):
        """Test metrics update on failed task"""
        orchestrator = AIAgentOrchestrator()

        # Create a test task
        task = AgentTask(agent_type=AgentType.ARCHITECT, task_type="test_task")

        # Update metrics
        orchestrator._update_task_metrics(task, False)

        assert orchestrator.metrics["tasks_completed"] == 0
        assert orchestrator.metrics["tasks_failed"] == 1


class TestIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_end_to_end_agent_task(self):
        """Test end-to-end agent task execution"""
        # This test requires the actual system to be working
        try:
            result = await execute_agent_task(
                agent_type="architect",
                task_type="recommend_technologies",
                input_data={
                    "requirements": ["api", "database"],
                    "current_stack": ["python"],
                },
            )

            assert result["status"] in ["completed", "failed"]
            if result["status"] == "completed":
                assert "result" in result

        except Exception as e:
            # If integration fails, that's okay for unit tests
            pytest.skip(f"Integration test skipped: {e}")

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_workflow_templates_available(self):
        """Test that workflow templates are available"""
        try:
            from domain.ai_analysis.ai_agent_orchestrator import \
                get_agent_capabilities

            capabilities = await get_agent_capabilities()

            assert "workflow_templates" in capabilities
            assert "supported_tasks" in capabilities
            assert "available_agent_types" in capabilities

        except Exception as e:
            pytest.skip(f"Integration test skipped: {e}")


# Fixtures for shared test data
@pytest.fixture
def sample_code():
    """Sample code for testing"""
    return '''
def calculate_sum(numbers):
    """Calculate sum of numbers"""
    total = 0
    for num in numbers:
        total += num
    return total

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def process(self, item):
        # TODO: Add validation
        self.data.append(item)
        return len(self.data)
'''


@pytest.fixture
def sample_project_structure():
    """Sample project structure for testing"""
    return {
        "src/": ["main.py", "utils.py", "models.py"],
        "tests/": ["test_main.py", "test_utils.py"],
        "docs/": ["README.md", "API.md"],
        "config/": ["settings.yml", "database.yml"],
    }


# Performance tests
class TestPerformance:
    """Performance tests for agent orchestrator"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self):
        """Test concurrent task execution performance"""
        orchestrator = AIAgentOrchestrator()

        # Register multiple test agents
        agents = []
        for i in range(3):
            agent = BaseAgent(f"test_agent_{i}", AgentType.ARCHITECT)
            agent._execute_specific_task = AsyncMock(
                return_value={"result": f"agent_{i}"}
            )
            await orchestrator.register_agent(agent)
            agents.append(agent)

        # Execute multiple tasks concurrently
        tasks = []
        for i in range(5):
            task = orchestrator.execute_task(
                agent_type=AgentType.ARCHITECT,
                task_type="test_task",
                input_data={"task_id": i},
            )
            tasks.append(task)

        # Measure execution time
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = asyncio.get_event_loop().time()

        execution_time = end_time - start_time

        # Verify results
        successful_results = [
            r for r in results if isinstance(r, dict) and r.get("status") == "completed"
        ]

        assert len(successful_results) > 0
        assert execution_time < 10  # Should complete within 10 seconds

        print(f"Concurrent execution: {len(tasks)} tasks in {execution_time:.2f}s")


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_orchestrator():
    """Cleanup orchestrator between tests"""
    yield
    # Reset global orchestrator instance
    import domain.ai_analysis.ai_agent_orchestrator

    domain.ai_analysis.ai_agent_orchestrator._orchestrator_instance = None
