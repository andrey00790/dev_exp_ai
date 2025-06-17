"""
Async Task Management API for AI Assistant MVP
Task 2.2: Scalability & Load Handling - Background Task API

Endpoints:
- POST /async-tasks/submit - Submit background task
- GET /async-tasks/{task_id} - Get task status
- DELETE /async-tasks/{task_id} - Cancel task
- GET /async-tasks/user/{user_id} - Get user tasks
- GET /async-tasks/queue/stats - Get queue statistics
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum
import logging

from app.performance.async_processor import async_processor, TaskStatus, TaskPriority
from app.security.auth import get_current_user, require_admin
from models.base import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/async-tasks", tags=["Async Tasks"])

class TaskSubmissionRequest(BaseModel):
    """Task submission request model"""
    task_func: str = Field(description="Function name to execute")
    task_args: Dict[str, Any] = Field(default_factory=dict, description="Function arguments")
    priority: str = Field(default="normal", description="Task priority: low, normal, high, urgent")
    notification_callback: Optional[str] = Field(None, description="WebSocket callback for notifications")

class TaskStatusResponse(BaseModel):
    """Task status response model"""
    task_id: str
    status: str
    progress: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    failed_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class QueueStatsResponse(BaseModel):
    """Queue statistics response model"""
    processor_type: str
    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: Optional[int] = None

@router.post("/submit")
async def submit_async_task(
    task_request: TaskSubmissionRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Submit a task for background processing
    
    Supported task functions:
    - llm_generate_rfc: Generate RFC document using LLM
    - llm_enhance_document: Enhance document with LLM
    - process_data_sync: Synchronize data from external sources
    - send_budget_alert: Send budget alert notification
    - generate_analytics_report: Generate analytics report
    """
    try:
        # Initialize async processor if needed
        if not hasattr(async_processor, 'redis_client'):
            await async_processor.initialize()
        
        # Validate task function
        valid_functions = [
            "llm_generate_rfc",
            "llm_enhance_document", 
            "process_data_sync",
            "send_budget_alert",
            "generate_analytics_report"
        ]
        
        if task_request.task_func not in valid_functions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid task function. Supported: {valid_functions}"
            )
        
        # Parse priority
        try:
            priority = TaskPriority[task_request.priority.upper()]
        except KeyError:
            priority = TaskPriority.NORMAL
        
        # Submit task
        task_id = await async_processor.submit_task(
            task_func=task_request.task_func,
            task_args=task_request.task_args,
            priority=priority,
            user_id=current_user.user_id,
            notification_callback=task_request.notification_callback
        )
        
        logger.info(f"Task submitted by {current_user.email}: {task_id} ({task_request.task_func})")
        
        return {
            "status": "success",
            "message": "Task submitted successfully",
            "task_id": task_id,
            "task_func": task_request.task_func,
            "priority": task_request.priority,
            "estimated_processing_time": _get_estimated_time(task_request.task_func)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit task: {str(e)}"
        )

@router.get("/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
) -> TaskStatusResponse:
    """
    Get status of a specific task
    
    Users can only view their own tasks unless they have admin access.
    """
    try:
        task_data = await async_processor.get_task_status(task_id)
        
        if not task_data or "error" in task_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Check permissions - users can only see their own tasks
        if (task_data.get("user_id") != current_user.user_id and 
            not (hasattr(current_user, 'scopes') and 'admin' in current_user.scopes)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - you can only view your own tasks"
            )
        
        return TaskStatusResponse(**task_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )

@router.delete("/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Cancel a pending or running task
    
    Users can only cancel their own tasks unless they have admin access.
    """
    try:
        # Check if task exists and get ownership
        task_data = await async_processor.get_task_status(task_id)
        
        if not task_data or "error" in task_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Check permissions
        is_owner = task_data.get("user_id") == current_user.user_id
        is_admin = hasattr(current_user, 'scopes') and 'admin' in current_user.scopes
        
        if not is_owner and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - you can only cancel your own tasks"
            )
        
        # Check if task can be cancelled
        current_status = task_data.get("status")
        if current_status in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel task with status: {current_status}"
            )
        
        # Cancel the task
        success = await async_processor.cancel_task(task_id, current_user.user_id)
        
        if success:
            logger.info(f"Task cancelled by {current_user.email}: {task_id}")
            return {
                "status": "success",
                "message": "Task cancelled successfully",
                "task_id": task_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel task"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}"
        )

@router.get("/user/tasks")
async def get_user_tasks(
    status_filter: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all tasks for the current user
    
    Args:
        status_filter: Filter by task status (pending, running, completed, failed, cancelled)
        limit: Maximum number of tasks to return (default: 50, max: 200)
    """
    try:
        if limit > 200:
            limit = 200
        
        # Parse status filter
        status_enum = None
        if status_filter:
            try:
                status_enum = TaskStatus[status_filter.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter. Valid values: {[s.value for s in TaskStatus]}"
                )
        
        # Get user tasks
        user_tasks = await async_processor.get_user_tasks(current_user.user_id, status_enum)
        
        # Apply limit
        limited_tasks = user_tasks[:limit]
        
        # Calculate statistics
        total_tasks = len(user_tasks)
        status_counts = {}
        for task in user_tasks:
            task_status = task.get("status", "unknown")
            status_counts[task_status] = status_counts.get(task_status, 0) + 1
        
        return {
            "status": "success",
            "user_id": current_user.user_id,
            "total_tasks": total_tasks,
            "returned_tasks": len(limited_tasks),
            "status_filter": status_filter,
            "status_counts": status_counts,
            "tasks": limited_tasks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user tasks for {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user tasks: {str(e)}"
        )

@router.get("/queue/stats")
async def get_queue_stats(
    current_user: User = Depends(get_current_user)
) -> QueueStatsResponse:
    """
    Get queue statistics
    
    Admin users get detailed statistics.
    """
    try:
        stats = await async_processor.get_queue_stats()
        
        # Basic stats for all users
        response_data = {
            "processor_type": stats.get("processor_type", "unknown"),
            "total_tasks": stats.get("total_tasks", 0),
            "pending_tasks": stats.get("pending_tasks", 0),
            "running_tasks": stats.get("running_tasks", 0),
            "completed_tasks": stats.get("completed_tasks", 0)
        }
        
        # Detailed stats for admin users
        if hasattr(current_user, 'scopes') and 'admin' in current_user.scopes:
            response_data.update({
                "failed_tasks": stats.get("failed_jobs", 0),
                "queue_details": {
                    "task_queue_size": stats.get("task_queue_size", 0),
                    "llm_queue_size": stats.get("llm_queue_size", 0),
                    "notification_queue_size": stats.get("notification_queue_size", 0)
                },
                "performance_metrics": {
                    "total_jobs_processed": stats.get("total_jobs_processed", 0),
                    "timestamp": stats.get("timestamp")
                }
            })
        
        return QueueStatsResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue statistics: {str(e)}"
        )

@router.post("/cleanup", dependencies=[Depends(require_admin)])
async def cleanup_completed_tasks(
    older_than_hours: int = 24,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Clean up completed tasks older than specified hours (admin only)
    
    Args:
        older_than_hours: Remove completed tasks older than this many hours (default: 24)
    """
    try:
        if older_than_hours < 1 or older_than_hours > 168:  # Max 1 week
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="older_than_hours must be between 1 and 168 (1 week)"
            )
        
        cleaned_count = await async_processor.cleanup_completed_tasks(older_than_hours)
        
        logger.info(f"Task cleanup performed by admin {current_user.email}: {cleaned_count} tasks removed")
        
        return {
            "status": "success",
            "message": f"Cleaned up {cleaned_count} completed tasks",
            "cleaned_count": cleaned_count,
            "older_than_hours": older_than_hours,
            "performed_by": current_user.user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup tasks: {str(e)}"
        )

@router.get("/examples")
async def get_task_examples(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get examples of available task functions and their arguments
    
    Helps users understand how to submit different types of tasks.
    """
    examples = {
        "llm_generate_rfc": {
            "description": "Generate RFC document using LLM",
            "estimated_time": "2-5 minutes",
            "example_args": {
                "topic": "API Gateway Design",
                "sections": ["Abstract", "Motivation", "Specification", "Implementation"],
                "target_length": 2000,
                "template": "technical_rfc"
            }
        },
        "llm_enhance_document": {
            "description": "Enhance document with LLM improvements",
            "estimated_time": "1-3 minutes", 
            "example_args": {
                "document_id": "doc_123",
                "enhancement_type": "grammar_and_style",
                "target_audience": "technical",
                "preserve_structure": True
            }
        },
        "process_data_sync": {
            "description": "Synchronize data from external sources",
            "estimated_time": "30 seconds - 2 minutes",
            "example_args": {
                "source": "confluence",
                "sync_type": "incremental",
                "since_timestamp": "2025-06-16T00:00:00Z",
                "categories": ["documentation", "specs"]
            }
        },
        "send_budget_alert": {
            "description": "Send budget alert notification",
            "estimated_time": "10-30 seconds",
            "example_args": {
                "user_email": "user@example.com",
                "alert_type": "budget_warning_80",
                "current_usage": 85.50,
                "budget_limit": 100.00
            }
        },
        "generate_analytics_report": {
            "description": "Generate comprehensive analytics report",
            "estimated_time": "2-5 minutes",
            "example_args": {
                "report_type": "usage_summary",
                "date_range": "last_30_days",
                "include_charts": True,
                "format": "json"
            }
        }
    }
    
    return {
        "status": "success",
        "available_tasks": len(examples),
        "priority_levels": ["low", "normal", "high", "urgent"],
        "task_examples": examples
    }

def _get_estimated_time(task_func: str) -> str:
    """Get estimated processing time for a task function"""
    time_estimates = {
        "llm_generate_rfc": "2-5 minutes",
        "llm_enhance_document": "1-3 minutes",
        "process_data_sync": "30 seconds - 2 minutes", 
        "send_budget_alert": "10-30 seconds",
        "generate_analytics_report": "2-5 minutes"
    }
    
    return time_estimates.get(task_func, "1-2 minutes") 