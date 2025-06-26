"""
Async Task Management API for AI Assistant MVP
Enhanced with standardized async patterns for enterprise reliability
Version: 2.1 Async Optimized

Endpoints:
- POST /async-tasks/submit - Submit background task
- GET /async-tasks/{task_id} - Get task status
- DELETE /async-tasks/{task_id} - Cancel task
- GET /async-tasks/user/tasks - Get user tasks
- GET /async-tasks/queue/stats - Get queue statistics
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum
import logging
import time

# Import standardized async patterns
from app.core.async_utils import (
    AsyncTimeouts, 
    with_timeout, 
    async_retry,
    safe_gather,
    create_background_task
)
from app.core.exceptions import AsyncTimeoutError, AsyncRetryError

from app.performance.async_processor import async_processor, TaskStatus, TaskPriority
from app.security.auth import get_current_user, require_admin
from app.models.user import User

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
@async_retry(max_attempts=2, delay=1.0, exceptions=(HTTPException,))
async def submit_async_task(
    task_request: TaskSubmissionRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Submit a task for background processing
    Enhanced with timeout protection and retry logic
    
    Supported task functions:
    - llm_generate_rfc: Generate RFC document using LLM
    - llm_enhance_document: Enhance document with LLM
    - process_data_sync: Synchronize data from external sources
    - send_budget_alert: Send budget alert notification
    - generate_analytics_report: Generate analytics report
    """
    try:
        # Calculate timeout based on task complexity
        timeout = _calculate_task_submission_timeout(task_request.task_func)
        
        # Execute task submission with timeout protection
        result = await with_timeout(
            _submit_task_internal(task_request, current_user),
            timeout,
            f"Task submission timed out (func: {task_request.task_func}, priority: {task_request.priority})",
            {
                "task_func": task_request.task_func,
                "priority": task_request.priority,
                "user_id": current_user.user_id,
                "has_args": bool(task_request.task_args)
            }
        )
        
        logger.info(f"✅ Task submitted by {current_user.email}: {result['task_id']} ({task_request.task_func})")
        
        return result
        
    except AsyncTimeoutError as e:
        logger.error(f"❌ Task submission timed out: {e}")
        raise HTTPException(
            status_code=504,
            detail="Task submission timed out: System overloaded. Please try again in a few moments."
        )
    except AsyncRetryError as e:
        logger.error(f"❌ Task submission failed after retries: {e}")
        raise HTTPException(status_code=500, detail=f"Task submission failed after retries: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error submitting task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit task: {str(e)}"
        )

@router.get("/{task_id}")
@async_retry(max_attempts=2, delay=0.5, exceptions=(HTTPException,))
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
) -> TaskStatusResponse:
    """
    Get status of a specific task
    Enhanced with timeout protection and concurrent permission checking
    
    Users can only view their own tasks unless they have admin access.
    """
    try:
        # Get task status with timeout protection
        task_data = await with_timeout(
            async_processor.get_task_status(task_id),
            AsyncTimeouts.DATABASE_QUERY,  # 10 seconds for status lookup
            f"Task status lookup timed out (task_id: {task_id})",
            {"task_id": task_id, "user_id": current_user.user_id}
        )
        
        if not task_data or "error" in task_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Concurrent permission check
        has_permission = await _check_task_permission(task_data, current_user)
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - you can only view your own tasks"
            )
        
        logger.info(f"✅ Task status retrieved: {task_id} for user {current_user.user_id}")
        
        return TaskStatusResponse(**task_data)
        
    except AsyncTimeoutError as e:
        logger.error(f"❌ Task status lookup timed out: {e}")
        raise HTTPException(
            status_code=504,
            detail="Task status lookup timed out: System overloaded"
        )
    except AsyncRetryError as e:
        logger.error(f"❌ Task status lookup failed after retries: {e}")
        raise HTTPException(status_code=500, detail=f"Status lookup failed after retries: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting task status {task_id}: {e}")
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
    Enhanced with timeout protection and concurrent stats collection
    
    Admin users get detailed statistics.
    """
    try:
        # Get queue stats with timeout protection
        stats = await with_timeout(
            async_processor.get_queue_stats(),
            AsyncTimeouts.DATABASE_QUERY * 1.5,  # 15 seconds for queue stats
            "Queue stats collection timed out",
            {"user_id": current_user.user_id}
        )
        
        # Basic stats for all users
        response_data = {
            "processor_type": stats.get("processor_type", "unknown"),
            "total_tasks": stats.get("total_tasks", 0),
            "pending_tasks": stats.get("pending_tasks", 0),
            "running_tasks": stats.get("running_tasks", 0),
            "completed_tasks": stats.get("completed_tasks", 0),
            "async_optimized": True
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
        
        logger.info(f"✅ Queue stats retrieved for user {current_user.user_id}")
        
        return QueueStatsResponse(**response_data)
        
    except AsyncTimeoutError as e:
        logger.warning(f"⚠️ Queue stats collection timed out: {e}")
        # Return basic stats on timeout
        return QueueStatsResponse(
            processor_type="timeout",
            total_tasks=0,
            pending_tasks=0,
            running_tasks=0,
            completed_tasks=0
        )
    except Exception as e:
        logger.error(f"❌ Error getting queue stats: {e}")
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

# Enhanced helper functions with async patterns

async def _submit_task_internal(
    task_request: TaskSubmissionRequest, 
    current_user: User
) -> Dict[str, Any]:
    """Internal task submission with concurrent validation"""
    
    # Concurrent validation and initialization
    validation_tasks = [
        _validate_task_function(task_request.task_func),
        _initialize_async_processor(),
        _parse_task_priority(task_request.priority)
    ]
    
    # Execute validations concurrently
    is_valid, processor_ready, priority = await safe_gather(
        *validation_tasks,
        return_exceptions=True,
        timeout=AsyncTimeouts.DATABASE_QUERY,  # 10 seconds for validation
        max_concurrency=3
    )
    
    # Handle validation results
    if isinstance(is_valid, Exception) or not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid task function: {task_request.task_func}"
        )
    
    if isinstance(processor_ready, Exception) or not processor_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task processor temporarily unavailable"
        )
    
    if isinstance(priority, Exception):
        priority = TaskPriority.NORMAL
    
    # Submit task with enhanced error handling
    task_id = await async_processor.submit_task(
        task_func=task_request.task_func,
        task_args=task_request.task_args,
        priority=priority,
        user_id=current_user.user_id,
        notification_callback=task_request.notification_callback
    )
    
    return {
        "status": "success",
        "message": "Task submitted successfully",
        "task_id": task_id,
        "task_func": task_request.task_func,
        "priority": task_request.priority,
        "estimated_processing_time": _get_estimated_time(task_request.task_func),
        "timeout_used": _calculate_task_submission_timeout(task_request.task_func),
        "async_optimized": True
    }

def _calculate_task_submission_timeout(task_func: str) -> float:
    """Calculate appropriate timeout for task submission"""
    base_timeout = AsyncTimeouts.BACKGROUND_TASK / 10  # 30 seconds for submission
    
    # Different task types have different submission complexity
    task_complexity = {
        "llm_generate_rfc": 1.5,  # More complex validation
        "llm_enhance_document": 1.2,
        "process_data_sync": 1.0,
        "send_budget_alert": 0.8,  # Simple task
        "generate_analytics_report": 1.3
    }
    
    multiplier = task_complexity.get(task_func, 1.0)
    return min(base_timeout * multiplier, 60.0)  # Cap at 1 minute

async def _validate_task_function(task_func: str) -> bool:
    """Validate task function concurrently"""
    valid_functions = [
        "llm_generate_rfc",
        "llm_enhance_document", 
        "process_data_sync",
        "send_budget_alert",
        "generate_analytics_report"
    ]
    return task_func in valid_functions

async def _initialize_async_processor() -> bool:
    """Initialize async processor if needed"""
    try:
        if not hasattr(async_processor, 'redis_client'):
            await async_processor.initialize()
        return True
    except Exception as e:
        logger.error(f"Failed to initialize async processor: {e}")
        return False

async def _parse_task_priority(priority_str: str) -> TaskPriority:
    """Parse task priority with fallback"""
    try:
        return TaskPriority[priority_str.upper()]
    except KeyError:
        return TaskPriority.NORMAL

async def _check_task_permission(task_data: Dict[str, Any], current_user: User) -> bool:
    """Check if user has permission to view task"""
    is_owner = task_data.get("user_id") == current_user.user_id
    is_admin = hasattr(current_user, 'scopes') and 'admin' in current_user.scopes
    return is_owner or is_admin 