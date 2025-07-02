"""
🤖 AI Agent Orchestration API

FastAPI endpoints for managing and executing AI agent workflows.
Provides REST API access to the AI Agent Orchestration System.

Endpoints:
- Agent management and status
- Task execution
- Workflow orchestration
- Monitoring and metrics
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.exceptions import ServiceError
from app.security.auth import get_current_user
from domain.ai_analysis.ai_agent_orchestrator import (
    AgentType, AutomatedWorkflow, TaskPriority, WorkflowStep,
    execute_agent_task, execute_automated_workflow, get_agent_capabilities,
    get_orchestrator)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ai-agents", tags=["AI Agents"])

# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class AgentTaskRequest(BaseModel):
    """Request model for agent task execution"""

    agent_type: str = Field(
        ..., description="Type of agent (architect, reviewer, security, etc.)"
    )
    task_type: str = Field(..., description="Specific task type")
    input_data: Dict[str, Any] = Field(..., description="Input data for the task")
    priority: str = Field(
        default="medium", description="Task priority (critical, high, medium, low)"
    )
    timeout_seconds: int = Field(default=300, description="Task timeout in seconds")
    description: Optional[str] = Field(
        None, description="Human-readable task description"
    )


class WorkflowExecutionRequest(BaseModel):
    """Request model for workflow execution"""

    workflow_name: str = Field(..., description="Name of the workflow to execute")
    input_data: Dict[str, Any] = Field(..., description="Input data for the workflow")
    timeout_minutes: int = Field(default=30, description="Workflow timeout in minutes")


class WorkflowDefinitionRequest(BaseModel):
    """Request model for creating custom workflows"""

    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="Workflow description")
    steps: List[Dict[str, Any]] = Field(..., description="Workflow steps configuration")
    input_schema: Dict[str, Any] = Field(
        default_factory=dict, description="Input schema definition"
    )
    timeout_minutes: int = Field(default=30, description="Workflow timeout in minutes")


class AgentTaskResponse(BaseModel):
    """Response model for agent task execution"""

    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float
    agent_id: str
    agent_type: str


class WorkflowExecutionResponse(BaseModel):
    """Response model for workflow execution"""

    workflow_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_summary: Dict[str, Any]


class AgentStatusResponse(BaseModel):
    """Response model for agent status"""

    total_agents: int
    agents: Dict[str, Any]
    metrics: Dict[str, Any]
    system_health: str


# =============================================================================
# AGENT MANAGEMENT ENDPOINTS
# =============================================================================


@router.get("/status", response_model=AgentStatusResponse)
async def get_agents_status(current_user: dict = Depends(get_current_user)):
    """
    Get current status of all AI agents.

    Returns information about active agents, their capabilities,
    current tasks, and system metrics.
    """
    try:
        orchestrator = await get_orchestrator()
        status = orchestrator.get_agent_status()

        # Calculate system health
        total_tasks = (
            status["metrics"]["tasks_completed"] + status["metrics"]["tasks_failed"]
        )
        success_rate = status["metrics"]["tasks_completed"] / max(total_tasks, 1) * 100

        if success_rate >= 95:
            system_health = "excellent"
        elif success_rate >= 85:
            system_health = "good"
        elif success_rate >= 70:
            system_health = "fair"
        else:
            system_health = "poor"

        return AgentStatusResponse(
            total_agents=status["total_agents"],
            agents=status["agents"],
            metrics=status["metrics"],
            system_health=system_health,
        )

    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent status: {str(e)}"
        )


@router.get("/capabilities")
async def get_agents_capabilities(current_user: dict = Depends(get_current_user)):
    """
    Get information about available agents and their capabilities.

    Returns:
    - Available agent types
    - Supported task types
    - Workflow templates
    - Current system capacity
    """
    try:
        capabilities = await get_agent_capabilities()
        return JSONResponse(content=capabilities)

    except Exception as e:
        logger.error(f"Failed to get agent capabilities: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get capabilities: {str(e)}"
        )


@router.get("/metrics")
async def get_agent_metrics(current_user: dict = Depends(get_current_user)):
    """
    Get detailed performance metrics for the agent system.

    Returns execution statistics, performance trends, and optimization insights.
    """
    try:
        orchestrator = await get_orchestrator()
        status = orchestrator.get_agent_status()
        metrics = status["metrics"]

        # Enhanced metrics calculation
        total_tasks = metrics["tasks_completed"] + metrics["tasks_failed"]
        success_rate = (metrics["tasks_completed"] / max(total_tasks, 1)) * 100

        enhanced_metrics = {
            "execution_statistics": {
                "total_tasks_executed": total_tasks,
                "successful_tasks": metrics["tasks_completed"],
                "failed_tasks": metrics["tasks_failed"],
                "success_rate_percentage": round(success_rate, 2),
                "average_execution_time_seconds": round(
                    metrics["average_execution_time"], 2
                ),
            },
            "agent_utilization": metrics["agent_utilization"],
            "system_performance": {
                "health_status": (
                    "excellent"
                    if success_rate >= 95
                    else "good" if success_rate >= 85 else "needs_attention"
                ),
                "recommendation": (
                    "System performing optimally"
                    if success_rate >= 95
                    else "Consider reviewing failed tasks"
                ),
            },
            "timestamp": datetime.now().isoformat(),
        }

        return JSONResponse(content=enhanced_metrics)

    except Exception as e:
        logger.error(f"Failed to get agent metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


# =============================================================================
# TASK EXECUTION ENDPOINTS
# =============================================================================


@router.post("/execute-task", response_model=AgentTaskResponse)
async def execute_single_task(
    request: AgentTaskRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Execute a single task with a specialized AI agent.

    Available agent types:
    - architect: Architecture analysis and design
    - reviewer: Code review and quality assessment
    - security: Security analysis and recommendations
    - performance: Performance optimization
    - documentation: Documentation generation
    - planner: Project planning and estimation
    """
    try:
        logger.info(
            f"🚀 Executing agent task: {request.agent_type} - {request.task_type}"
        )

        # Validate agent type
        try:
            agent_type_enum = AgentType(request.agent_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent type: {request.agent_type}. Available types: {[t.value for t in AgentType]}",
            )

        # Validate priority
        try:
            priority_enum = TaskPriority(request.priority)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid priority: {request.priority}. Available priorities: {[p.value for p in TaskPriority]}",
            )

        # Execute task
        result = await execute_agent_task(
            agent_type=request.agent_type,
            task_type=request.task_type,
            input_data=request.input_data,
            priority=request.priority,
        )

        # Log successful execution
        logger.info(
            f"✅ Task completed: {result['task_id']} in {result.get('execution_time', 0):.2f}s"
        )

        return AgentTaskResponse(
            task_id=result["task_id"],
            status=result["status"],
            result=result.get("result"),
            error=result.get("error"),
            execution_time=result.get("execution_time", 0),
            agent_id=result.get("agent_id", "unknown"),
            agent_type=request.agent_type,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Task execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")


@router.post("/execute-workflow", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    request: WorkflowExecutionRequest, current_user: dict = Depends(get_current_user)
):
    """
    Execute a complete automated workflow.

    Available workflows:
    - automated_code_review: Complete code review with multiple agents
    - project_assessment: Comprehensive project health assessment
    - rfc_generation_with_analysis: RFC generation with full analysis

    Custom workflows can be created via the /create-workflow endpoint.
    """
    try:
        logger.info(f"🔄 Executing workflow: {request.workflow_name}")

        # Execute workflow
        result = await execute_automated_workflow(
            workflow_name=request.workflow_name, input_data=request.input_data
        )

        logger.info(f"✅ Workflow completed: {request.workflow_name}")

        return WorkflowExecutionResponse(
            workflow_id=result["workflow_id"],
            status=result["status"],
            result=result.get("result"),
            error=result.get("error"),
            execution_summary=result.get("execution_summary", {}),
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Workflow execution failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Workflow execution failed: {str(e)}"
        )


# =============================================================================
# WORKFLOW MANAGEMENT ENDPOINTS
# =============================================================================


@router.get("/workflows")
async def get_available_workflows(current_user: dict = Depends(get_current_user)):
    """
    Get list of available workflows and their descriptions.

    Returns both built-in and custom workflows with their
    input requirements and expected outputs.
    """
    try:
        orchestrator = await get_orchestrator()
        workflows = orchestrator.get_workflow_templates()

        # Add registered workflows
        registered_workflows = {}
        for workflow_id, workflow in orchestrator.workflows.items():
            registered_workflows[workflow_id] = {
                "name": workflow.name,
                "description": workflow.description,
                "steps": len(workflow.steps),
                "timeout_minutes": workflow.timeout_minutes,
                "input_schema": workflow.input_schema,
            }

        return JSONResponse(
            content={
                "workflow_templates": workflows,
                "registered_workflows": registered_workflows,
                "total_workflows": len(workflows) + len(registered_workflows),
            }
        )

    except Exception as e:
        logger.error(f"Failed to get workflows: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get workflows: {str(e)}"
        )


@router.post("/create-workflow")
async def create_custom_workflow(
    request: WorkflowDefinitionRequest, current_user: dict = Depends(get_current_user)
):
    """
    Create a custom automated workflow.

    Allows users to define multi-step workflows that coordinate
    multiple AI agents to accomplish complex tasks.
    """
    try:
        logger.info(f"🏗️ Creating custom workflow: {request.name}")

        # Convert request to workflow object
        steps = []
        for step_data in request.steps:
            step = WorkflowStep(
                name=step_data.get("name", ""),
                agent_type=AgentType(step_data["agent_type"]),
                task_type=step_data["task_type"],
                input_mapping=step_data.get("input_mapping", {}),
                output_key=step_data.get("output_key", "result"),
                depends_on=step_data.get("depends_on", []),
                parallel=step_data.get("parallel", False),
                optional=step_data.get("optional", False),
            )
            steps.append(step)

        workflow = AutomatedWorkflow(
            name=request.name,
            description=request.description,
            steps=steps,
            input_schema=request.input_schema,
            timeout_minutes=request.timeout_minutes,
        )

        # Register workflow
        orchestrator = await get_orchestrator()
        workflow_id = orchestrator.register_workflow(workflow)

        logger.info(f"✅ Created workflow: {request.name} (ID: {workflow_id})")

        return JSONResponse(
            content={
                "workflow_id": workflow_id,
                "name": request.name,
                "status": "created",
                "steps_count": len(steps),
                "message": f"Workflow '{request.name}' created successfully",
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid workflow definition: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create workflow: {str(e)}"
        )


# =============================================================================
# SPECIALIZED TASK ENDPOINTS
# =============================================================================


@router.post("/analyze-architecture")
async def analyze_project_architecture(
    project_path: str,
    include_recommendations: bool = True,
    current_user: dict = Depends(get_current_user),
):
    """
    Analyze project architecture using the Architect agent.

    Provides comprehensive analysis of codebase structure,
    patterns, and architectural recommendations.
    """
    try:
        result = await execute_agent_task(
            agent_type="architect",
            task_type="analyze_architecture",
            input_data={"project_path": project_path},
        )

        if result["status"] == "completed" and result["result"]:
            analysis = result["result"]

            # Enhanced response with actionable insights
            response = {
                "project_path": project_path,
                "analysis": analysis,
                "summary": {
                    "components_found": len(analysis.get("components", [])),
                    "architecture_patterns": len(analysis.get("patterns", [])),
                    "health_score": analysis.get("health_score", 0),
                    "recommendations_count": len(analysis.get("recommendations", [])),
                },
                "execution_time": result["execution_time"],
                "timestamp": datetime.now().isoformat(),
            }

            if include_recommendations and analysis.get("recommendations"):
                response["top_recommendations"] = analysis["recommendations"][:3]

            return JSONResponse(content=response)
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Architecture analysis failed"),
            )

    except Exception as e:
        logger.error(f"Architecture analysis failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Architecture analysis failed: {str(e)}"
        )


@router.post("/review-code")
async def review_code_with_ai(
    code: str,
    file_path: str = "",
    review_focus: List[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Perform AI-powered code review.

    Uses specialized reviewer agent to analyze code quality,
    security issues, performance concerns, and best practices.
    """
    try:
        input_data = {"code": code, "file_path": file_path}

        if review_focus:
            input_data["focus_areas"] = review_focus

        result = await execute_agent_task(
            agent_type="reviewer", task_type="review_code", input_data=input_data
        )

        if result["status"] == "completed":
            return JSONResponse(
                content={
                    "review_result": result["result"],
                    "file_path": file_path,
                    "execution_time": result["execution_time"],
                    "agent_id": result["agent_id"],
                }
            )
        else:
            raise HTTPException(
                status_code=500, detail=result.get("error", "Code review failed")
            )

    except Exception as e:
        logger.error(f"Code review failed: {e}")
        raise HTTPException(status_code=500, detail=f"Code review failed: {str(e)}")


@router.post("/quick-workflow")
async def execute_quick_workflow(
    workflow_type: str,
    project_path: str,
    additional_params: Dict[str, Any] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Execute common workflows with simplified parameters.

    Supported workflow types:
    - project_health_check: Quick project assessment
    - code_review_batch: Review multiple files
    - architecture_review: Focus on architecture patterns
    """
    try:
        # Prepare input data based on workflow type
        if workflow_type == "project_health_check":
            workflow_name = "project_assessment"
            input_data = {"project_path": project_path, "assessment_depth": "standard"}
        elif workflow_type == "architecture_review":
            workflow_name = "automated_code_review"
            input_data = {"project_path": project_path, "focus": "architecture"}
        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown workflow type: {workflow_type}"
            )

        # Add additional parameters
        if additional_params:
            input_data.update(additional_params)

        # Execute workflow
        result = await execute_automated_workflow(workflow_name, input_data)

        return JSONResponse(
            content={
                "workflow_type": workflow_type,
                "result": result,
                "quick_summary": {
                    "status": result["status"],
                    "execution_time": result.get("execution_time", 0),
                    "key_findings": result.get("result", {}).get(
                        "summary", "Analysis completed"
                    ),
                },
            }
        )

    except Exception as e:
        logger.error(f"Quick workflow failed: {e}")
        raise HTTPException(status_code=500, detail=f"Quick workflow failed: {str(e)}")


# =============================================================================
# HEALTH AND MONITORING
# =============================================================================


@router.get("/health")
async def health_check():
    """
    Health check endpoint for AI Agent system.

    Returns system status and basic health metrics.
    """
    try:
        orchestrator = await get_orchestrator()
        status = orchestrator.get_agent_status()

        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "agents_active": len(
                [a for a in status["agents"].values() if a["status"] != "failed"]
            ),
            "total_agents": status["total_agents"],
            "system_ready": True,
        }

        return JSONResponse(content=health_status)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )
