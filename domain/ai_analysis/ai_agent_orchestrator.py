"""
🤖 AI Agent Orchestration System

Intelligent orchestration of multiple AI agents for complex task automation.
This system coordinates specialized agents to handle multi-step workflows,
from code review automation to intelligent project planning.

Phase 4A - Foundation Component
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import uuid4

from app.core.async_utils import (AsyncTimeouts, async_retry, safe_gather,
                                  with_timeout)
from app.core.exceptions import ServiceError
from domain.integration.enhanced_vector_search_service import \
    EnhancedVectorSearchService
from domain.rfc_generation.rfc_generator_service import RFCGeneratorService

from ..core.core_logic_engine import CoreLogicEngine

logger = logging.getLogger(__name__)

# =============================================================================
# AGENT TYPES AND COMMUNICATION
# =============================================================================


class AgentType(Enum):
    """Types of specialized AI agents"""

    ARCHITECT = "architect"  # Architecture analysis and design
    REVIEWER = "reviewer"  # Code review and quality assessment
    SECURITY = "security"  # Security analysis and recommendations
    PERFORMANCE = "performance"  # Performance optimization
    DOCUMENTATION = "documentation"  # Documentation generation
    PLANNER = "planner"  # Project planning and estimation
    QUALITY = "quality"  # Quality assurance and testing
    DEPLOYMENT = "deployment"  # Deployment and infrastructure


class AgentStatus(Enum):
    """Agent execution status"""

    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TaskPriority(Enum):
    """Task priority levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class AgentMessage:
    """Inter-agent communication message"""

    id: str = field(default_factory=lambda: str(uuid4()))
    sender: str = ""
    recipient: str = ""
    message_type: str = "request"  # request, response, notification, error
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None


@dataclass
class AgentTask:
    """Task for agent execution"""

    id: str = field(default_factory=lambda: str(uuid4()))
    agent_type: AgentType = AgentType.ARCHITECT
    task_type: str = "analysis"
    description: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.MEDIUM
    timeout_seconds: int = 300
    retry_count: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: AgentStatus = AgentStatus.IDLE
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class WorkflowStep:
    """Single step in a workflow"""

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    agent_type: AgentType = AgentType.ARCHITECT
    task_type: str = "analysis"
    input_mapping: Dict[str, str] = field(
        default_factory=dict
    )  # Maps from previous steps
    output_key: str = "result"
    depends_on: List[str] = field(default_factory=list)
    parallel: bool = False
    optional: bool = False


@dataclass
class AutomatedWorkflow:
    """Complete automated workflow definition"""

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    timeout_minutes: int = 30
    retry_policy: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# SPECIALIZED AGENTS
# =============================================================================


class BaseAgent:
    """Base class for all specialized agents"""

    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.status = AgentStatus.IDLE
        self.current_task: Optional[AgentTask] = None
        self.message_queue: List[AgentMessage] = []
        self.capabilities = []

        # Initialize core services
        self.core_engine = CoreLogicEngine()
        self.search_service = EnhancedVectorSearchService()

    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a task and return results"""
        try:
            self.status = AgentStatus.WORKING
            self.current_task = task
            task.started_at = datetime.now()

            logger.info(f"🤖 Agent {self.agent_id} executing task: {task.description}")

            # Execute the specific agent logic
            result = await self._execute_specific_task(task)

            task.status = AgentStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result

            self.status = AgentStatus.IDLE
            self.current_task = None

            return result

        except Exception as e:
            logger.error(f"❌ Agent {self.agent_id} task failed: {e}")
            task.status = AgentStatus.FAILED
            task.error = str(e)
            self.status = AgentStatus.IDLE
            raise

    async def _execute_specific_task(self, task: AgentTask) -> Dict[str, Any]:
        """Override in specialized agents"""
        raise NotImplementedError("Subclasses must implement _execute_specific_task")

    async def send_message(
        self, recipient: str, message_type: str, content: Dict[str, Any]
    ) -> str:
        """Send message to another agent"""
        message = AgentMessage(
            sender=self.agent_id,
            recipient=recipient,
            message_type=message_type,
            content=content,
        )
        # In real implementation, this would go through the orchestrator
        return message.id


class ArchitectAgent(BaseAgent):
    """Specialized agent for architecture analysis and design"""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentType.ARCHITECT)
        self.capabilities = [
            "architecture_analysis",
            "system_design",
            "technology_recommendations",
            "scalability_assessment",
        ]
        self.rfc_service = RFCGeneratorService()

    async def _execute_specific_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute architecture-specific tasks"""

        if task.task_type == "analyze_architecture":
            return await self._analyze_architecture(task.input_data)
        elif task.task_type == "design_system":
            return await self._design_system(task.input_data)
        elif task.task_type == "recommend_technologies":
            return await self._recommend_technologies(task.input_data)
        else:
            raise ValueError(f"Unknown task type: {task.task_type}")

    @async_retry(max_attempts=2, delay=1.0)
    async def _analyze_architecture(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze system architecture"""
        project_path = input_data.get("project_path", ".")

        try:
            # Use existing RFC architecture analyzer
            from domain.rfc_generation.rfc_architecture_analyzer import \
                RFCArchitectureAnalyzer

            analyzer = RFCArchitectureAnalyzer()

            analysis = await analyzer.analyze_codebase(project_path)

            return {
                "analysis_type": "architecture",
                "components": [
                    {
                        "name": comp.name,
                        "type": comp.service_type,
                        "files_count": len(comp.files),
                        "technologies": comp.technology_stack,
                    }
                    for comp in analysis.components
                ],
                "patterns": [
                    {
                        "type": pattern.pattern_type,
                        "confidence": pattern.confidence,
                        "evidence": pattern.evidence[:3],
                    }
                    for pattern in analysis.patterns
                ],
                "recommendations": analysis.improvement_suggestions[:5],
                "metrics": analysis.metrics,
                "health_score": self._calculate_architecture_health(analysis),
            }

        except Exception as e:
            logger.error(f"Architecture analysis failed: {e}")
            return {
                "analysis_type": "architecture",
                "error": str(e),
                "components": [],
                "recommendations": ["Manual architecture review recommended"],
            }

    def _calculate_architecture_health(self, analysis) -> float:
        """Calculate overall architecture health score"""
        base_score = 70.0

        # Adjust based on patterns found
        pattern_bonus = len(analysis.patterns) * 5

        # Adjust based on component organization
        if len(analysis.components) > 3:
            organization_bonus = 10
        else:
            organization_bonus = -5

        # Adjust based on tech diversity
        tech_count = len(analysis.technology_inventory)
        if 3 <= tech_count <= 8:
            tech_bonus = 10
        elif tech_count > 8:
            tech_bonus = -5
        else:
            tech_bonus = 0

        health_score = base_score + pattern_bonus + organization_bonus + tech_bonus
        return min(100.0, max(0.0, health_score))

    async def _design_system(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Design system architecture"""
        requirements = input_data.get("requirements", [])
        constraints = input_data.get("constraints", {})

        # Simplified system design logic
        design = {
            "architecture_type": (
                "microservices" if len(requirements) > 5 else "monolithic"
            ),
            "components": [],
            "data_flow": [],
            "deployment_strategy": "containerized",
            "scalability_considerations": [],
            "security_measures": [],
        }

        # Add components based on requirements
        for req in requirements:
            if "api" in req.lower():
                design["components"].append(
                    {
                        "name": "API Gateway",
                        "type": "service",
                        "responsibility": "API management and routing",
                    }
                )
            if "database" in req.lower():
                design["components"].append(
                    {
                        "name": "Database Layer",
                        "type": "data",
                        "responsibility": "Data persistence and management",
                    }
                )

        return design

    async def _recommend_technologies(
        self, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recommend technologies based on requirements"""
        requirements = input_data.get("requirements", [])
        current_stack = input_data.get("current_stack", [])

        recommendations = {
            "backend": [],
            "frontend": [],
            "database": [],
            "infrastructure": [],
            "rationale": {},
        }

        # Simple recommendation logic
        if "python" in str(current_stack).lower():
            recommendations["backend"].append("FastAPI")
            recommendations["rationale"][
                "FastAPI"
            ] = "High performance, type hints, async support"

        if "react" in str(current_stack).lower():
            recommendations["frontend"].append("TypeScript")
            recommendations["rationale"][
                "TypeScript"
            ] = "Type safety, better developer experience"

        recommendations["database"].append("PostgreSQL")
        recommendations["rationale"][
            "PostgreSQL"
        ] = "ACID compliance, JSON support, mature ecosystem"

        return recommendations


class CodeReviewAgent(BaseAgent):
    """Specialized agent for code review and quality assessment"""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, AgentType.REVIEWER)
        self.capabilities = [
            "code_quality_analysis",
            "security_review",
            "performance_review",
            "best_practices_check",
        ]

    async def _execute_specific_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute code review tasks"""

        if task.task_type == "review_code":
            return await self._review_code(task.input_data)
        elif task.task_type == "analyze_pr":
            return await self._analyze_pull_request(task.input_data)
        else:
            raise ValueError(f"Unknown task type: {task.task_type}")

    async def _review_code(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive code review"""
        code_content = input_data.get("code", "")
        file_path = input_data.get("file_path", "")

        review = {
            "overall_score": 85,  # Placeholder
            "issues": [],
            "suggestions": [],
            "security_concerns": [],
            "performance_issues": [],
            "best_practices": [],
        }

        # Simplified code analysis
        if len(code_content) > 1000:
            review["suggestions"].append(
                "Consider breaking this file into smaller modules"
            )

        if "TODO" in code_content:
            review["issues"].append(
                "TODOs found - consider addressing or creating tickets"
            )

        if "print(" in code_content and file_path.endswith(".py"):
            review["issues"].append(
                "Debug print statements found - consider using logging"
            )

        return review

    async def _analyze_pull_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a pull request"""
        pr_data = input_data.get("pr_data", {})

        analysis = {
            "summary": "Pull request analysis completed",
            "risk_level": "medium",
            "recommendations": [],
            "approval_status": "needs_review",
        }

        # Simplified PR analysis
        changed_files = pr_data.get("changed_files", 0)
        if changed_files > 20:
            analysis["risk_level"] = "high"
            analysis["recommendations"].append(
                "Large PR - consider breaking into smaller changes"
            )

        return analysis


# =============================================================================
# ORCHESTRATOR
# =============================================================================


class AIAgentOrchestrator:
    """
    Main orchestrator for AI agents collaboration.

    Manages agent lifecycle, task distribution, and workflow execution.
    Provides intelligent coordination of multiple specialized agents.
    """

    def __init__(self):
        """Initialize the orchestrator with empty state"""
        self.agents: Dict[str, BaseAgent] = {}
        self.active_tasks: Dict[str, AgentTask] = {}
        self.workflows: Dict[str, AutomatedWorkflow] = {}
        self.message_bus: List[AgentMessage] = []

        # Initialize core services
        self.core_engine = CoreLogicEngine()

        # Performance metrics
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "average_execution_time": 0.0,
            "agent_utilization": {},
            "workflow_success_rate": 0.0,
        }

        # Flag to track if default agents are initialized
        self._default_agents_initialized = False

    async def _ensure_default_agents_initialized(self):
        """Ensure default agents are initialized (lazy initialization)"""
        if not self._default_agents_initialized:
            await self._initialize_default_agents()
            self._default_agents_initialized = True

    async def _initialize_default_agents(self):
        """Initialize standard set of agents"""
        try:
            await self.register_agent(ArchitectAgent("architect_001"))
            await self.register_agent(CodeReviewAgent("reviewer_001"))

            logger.info("🚀 Default AI agents initialized")
        except Exception as e:
            logger.error(f"Failed to initialize default agents: {e}")

    async def register_agent(self, agent: BaseAgent) -> str:
        """Register a new agent with the orchestrator"""
        agent_id = agent.agent_id
        self.agents[agent_id] = agent
        self.metrics["agent_utilization"][agent_id] = 0.0

        logger.info(f"🤖 Registered agent: {agent_id} ({agent.agent_type.value})")
        return agent_id

    async def execute_task(
        self,
        agent_type: AgentType,
        task_type: str,
        input_data: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        timeout_seconds: int = 300,
    ) -> Dict[str, Any]:
        """Execute a single task with specified agent type"""

        # Ensure default agents are initialized
        await self._ensure_default_agents_initialized()

        task = AgentTask(
            agent_type=agent_type,
            task_type=task_type,
            description=f"{agent_type.value} task: {task_type}",
            input_data=input_data,
            priority=priority,
            timeout_seconds=timeout_seconds,
        )

        try:
            # Find available agent of the requested type
            available_agent = await self._find_available_agent(agent_type)
            if not available_agent:
                raise ServiceError(f"No available agent of type {agent_type.value}")

            # Execute task with timeout
            result = await with_timeout(
                available_agent.execute_task(task),
                timeout_seconds,
                f"Task execution timed out: {task.id}",
            )

            # Update metrics
            self._update_task_metrics(task, True)

            return {
                "task_id": task.id,
                "status": "completed",
                "result": result,
                "execution_time": (
                    (task.completed_at - task.started_at).total_seconds()
                    if task.completed_at
                    else 0
                ),
                "agent_id": available_agent.agent_id,
            }

        except Exception as e:
            logger.error(f"❌ Task execution failed: {e}")
            self._update_task_metrics(task, False)

            return {
                "task_id": task.id,
                "status": "failed",
                "error": str(e),
                "agent_type": agent_type.value,
            }

    async def execute_workflow(
        self, workflow_id: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a complete automated workflow"""

        # Ensure default agents are initialized
        await self._ensure_default_agents_initialized()

        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow = self.workflows[workflow_id]

        logger.info(f"🔄 Starting workflow: {workflow.name}")

        try:
            # Execute workflow steps
            workflow_result = await self._execute_workflow_steps(workflow, input_data)

            logger.info(f"✅ Workflow completed: {workflow.name}")
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "result": workflow_result,
                "execution_summary": {
                    "total_steps": len(workflow.steps),
                    "completed_steps": len(
                        [
                            s
                            for s in workflow_result.get("step_results", {})
                            if workflow_result["step_results"][s].get("status")
                            == "completed"
                        ]
                    ),
                },
            }

        except Exception as e:
            logger.error(f"❌ Workflow failed: {workflow.name} - {e}")
            return {"workflow_id": workflow_id, "status": "failed", "error": str(e)}

    async def _execute_workflow_steps(
        self, workflow: AutomatedWorkflow, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute all steps in a workflow"""

        step_results = {}
        workflow_context = {"input": input_data}

        # Build dependency graph
        dependency_map = {}
        for step in workflow.steps:
            dependency_map[step.id] = step.depends_on

        # Execute steps in dependency order
        completed_steps = set()

        while len(completed_steps) < len(workflow.steps):
            # Find steps ready to execute
            ready_steps = []
            for step in workflow.steps:
                if step.id not in completed_steps:
                    # Check if all dependencies are completed
                    if all(dep_id in completed_steps for dep_id in step.depends_on):
                        ready_steps.append(step)

            if not ready_steps:
                raise ServiceError("Workflow deadlock detected - circular dependencies")

            # Execute ready steps (in parallel if marked)
            parallel_steps = [s for s in ready_steps if s.parallel]
            sequential_steps = [s for s in ready_steps if not s.parallel]

            # Execute parallel steps
            if parallel_steps:
                parallel_tasks = [
                    self._execute_workflow_step(step, workflow_context, step_results)
                    for step in parallel_steps
                ]

                parallel_results = await safe_gather(
                    *parallel_tasks, return_exceptions=True
                )

                for step, result in zip(parallel_steps, parallel_results):
                    if isinstance(result, Exception):
                        if not step.optional:
                            raise result
                        step_results[step.id] = {
                            "status": "failed",
                            "error": str(result),
                        }
                    else:
                        step_results[step.id] = result
                    completed_steps.add(step.id)

            # Execute sequential steps
            for step in sequential_steps:
                try:
                    result = await self._execute_workflow_step(
                        step, workflow_context, step_results
                    )
                    step_results[step.id] = result
                    completed_steps.add(step.id)
                except Exception as e:
                    if not step.optional:
                        raise
                    step_results[step.id] = {"status": "failed", "error": str(e)}
                    completed_steps.add(step.id)

        return {"step_results": step_results, "final_context": workflow_context}

    async def _execute_workflow_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
        previous_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single workflow step"""

        # Prepare step input from context and previous results
        step_input = {}

        # Map inputs from previous steps
        for input_key, source_path in step.input_mapping.items():
            if "." in source_path:
                # Navigate nested structure
                parts = source_path.split(".")
                value = context
                for part in parts:
                    if part in previous_results:
                        value = previous_results[part]
                    elif isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        value = None
                        break
                step_input[input_key] = value
            else:
                # Direct mapping
                if source_path in previous_results:
                    step_input[input_key] = previous_results[source_path].get("result")
                elif source_path in context:
                    step_input[input_key] = context[source_path]

        # Execute the step
        result = await self.execute_task(
            agent_type=step.agent_type, task_type=step.task_type, input_data=step_input
        )

        # Update context with step result
        if step.output_key and result.get("result"):
            context[step.output_key] = result["result"]

        return result

    async def _find_available_agent(self, agent_type: AgentType) -> Optional[BaseAgent]:
        """Find an available agent of the specified type"""
        for agent in self.agents.values():
            if agent.agent_type == agent_type and agent.status == AgentStatus.IDLE:
                return agent
        return None

    def _update_task_metrics(self, task: AgentTask, success: bool):
        """Update performance metrics"""
        if success:
            self.metrics["tasks_completed"] += 1
        else:
            self.metrics["tasks_failed"] += 1

        # Update average execution time
        if task.started_at and task.completed_at:
            execution_time = (task.completed_at - task.started_at).total_seconds()
            current_avg = self.metrics["average_execution_time"]
            total_tasks = self.metrics["tasks_completed"] + self.metrics["tasks_failed"]

            self.metrics["average_execution_time"] = (
                current_avg * (total_tasks - 1) + execution_time
            ) / total_tasks

    def register_workflow(self, workflow: AutomatedWorkflow) -> str:
        """Register a new automated workflow"""
        self.workflows[workflow.id] = workflow
        logger.info(f"📋 Registered workflow: {workflow.name}")
        return workflow.id

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current status of all agents"""
        return {
            "total_agents": len(self.agents),
            "agents": {
                agent_id: {
                    "type": agent.agent_type.value,
                    "status": agent.status.value,
                    "capabilities": agent.capabilities,
                    "current_task": (
                        agent.current_task.id if agent.current_task else None
                    ),
                }
                for agent_id, agent in self.agents.items()
            },
            "metrics": self.metrics,
        }

    def get_workflow_templates(self) -> Dict[str, Any]:
        """Get available workflow templates"""
        return {
            "code_review_workflow": {
                "name": "Automated Code Review",
                "description": "Complete code review with architecture, security, and performance analysis",
                "steps": [
                    "architecture_analysis",
                    "code_review",
                    "security_check",
                    "performance_analysis",
                ],
            },
            "project_assessment_workflow": {
                "name": "Project Health Assessment",
                "description": "Comprehensive project assessment including technical debt analysis",
                "steps": [
                    "architecture_analysis",
                    "code_quality_check",
                    "security_audit",
                    "performance_review",
                ],
            },
            "rfc_generation_workflow": {
                "name": "RFC Generation with Analysis",
                "description": "Generate RFC with full codebase analysis and recommendations",
                "steps": [
                    "architecture_analysis",
                    "requirement_analysis",
                    "rfc_generation",
                    "review",
                ],
            },
        }


# =============================================================================
# PREDEFINED WORKFLOWS
# =============================================================================


def create_code_review_workflow() -> AutomatedWorkflow:
    """Create automated code review workflow"""

    steps = [
        WorkflowStep(
            id="architecture_analysis",
            name="Architecture Analysis",
            agent_type=AgentType.ARCHITECT,
            task_type="analyze_architecture",
            input_mapping={"project_path": "input.project_path"},
            output_key="architecture_analysis",
        ),
        WorkflowStep(
            id="code_review",
            name="Code Quality Review",
            agent_type=AgentType.REVIEWER,
            task_type="review_code",
            input_mapping={
                "code": "input.code",
                "file_path": "input.file_path",
                "architecture_context": "architecture_analysis",
            },
            depends_on=["architecture_analysis"],
            output_key="code_review",
        ),
    ]

    return AutomatedWorkflow(
        name="Automated Code Review",
        description="Complete code review with architecture context",
        steps=steps,
        input_schema={
            "required": ["project_path", "code", "file_path"],
            "optional": ["review_depth", "focus_areas"],
        },
        timeout_minutes=15,
    )


def create_project_assessment_workflow() -> AutomatedWorkflow:
    """Create comprehensive project assessment workflow"""

    steps = [
        WorkflowStep(
            id="architecture_analysis",
            name="Architecture Analysis",
            agent_type=AgentType.ARCHITECT,
            task_type="analyze_architecture",
            input_mapping={"project_path": "input.project_path"},
            output_key="architecture_analysis",
            parallel=True,
        ),
        WorkflowStep(
            id="technology_recommendations",
            name="Technology Recommendations",
            agent_type=AgentType.ARCHITECT,
            task_type="recommend_technologies",
            input_mapping={
                "requirements": "input.requirements",
                "current_stack": "architecture_analysis.technologies",
            },
            depends_on=["architecture_analysis"],
            output_key="tech_recommendations",
        ),
    ]

    return AutomatedWorkflow(
        name="Project Assessment",
        description="Comprehensive project health and technology assessment",
        steps=steps,
        input_schema={
            "required": ["project_path"],
            "optional": ["requirements", "assessment_depth"],
        },
        timeout_minutes=30,
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global orchestrator instance
_orchestrator_instance: Optional[AIAgentOrchestrator] = None


async def get_orchestrator() -> AIAgentOrchestrator:
    """Get or create global orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AIAgentOrchestrator()

        # Register default workflows
        code_review_workflow = create_code_review_workflow()
        _orchestrator_instance.register_workflow(code_review_workflow)

        project_assessment_workflow = create_project_assessment_workflow()
        _orchestrator_instance.register_workflow(project_assessment_workflow)

    return _orchestrator_instance


async def execute_agent_task(
    agent_type: str,
    task_type: str,
    input_data: Dict[str, Any],
    priority: str = "medium",
) -> Dict[str, Any]:
    """Convenience function to execute a single agent task"""
    orchestrator = await get_orchestrator()

    agent_type_enum = AgentType(agent_type)
    priority_enum = TaskPriority(priority)

    return await orchestrator.execute_task(
        agent_type=agent_type_enum,
        task_type=task_type,
        input_data=input_data,
        priority=priority_enum,
    )


async def execute_automated_workflow(
    workflow_name: str, input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Convenience function to execute a predefined workflow"""
    orchestrator = await get_orchestrator()

    # Find workflow by name
    workflow_id = None
    for wf_id, workflow in orchestrator.workflows.items():
        if workflow.name.lower().replace(" ", "_") == workflow_name.lower():
            workflow_id = wf_id
            break

    if not workflow_id:
        raise ValueError(f"Workflow not found: {workflow_name}")

    return await orchestrator.execute_workflow(workflow_id, input_data)


async def get_agent_capabilities() -> Dict[str, Any]:
    """Get information about available agents and their capabilities"""
    orchestrator = await get_orchestrator()

    return {
        "available_agent_types": [agent_type.value for agent_type in AgentType],
        "active_agents": orchestrator.get_agent_status(),
        "workflow_templates": orchestrator.get_workflow_templates(),
        "supported_tasks": {
            "architect": [
                "analyze_architecture",
                "design_system",
                "recommend_technologies",
            ],
            "reviewer": ["review_code", "analyze_pr"],
            "security": ["security_scan", "vulnerability_assessment"],
            "performance": ["performance_analysis", "optimization_recommendations"],
        },
    }
