"""
Async Processing System for AI Assistant MVP
Task 2.2: Scalability & Load Handling - Background Tasks

Features:
- LLM request queuing with Redis Queue
- Background task processing
- WebSocket notifications for completion
- Progress tracking for long-running tasks
- Task status management
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from enum import Enum
import traceback

# Redis queue imports with fallback
try:
    import aioredis
    from rq import Queue, Worker, Connection
    import redis
    REDIS_QUEUE_AVAILABLE = True
except ImportError:
    REDIS_QUEUE_AVAILABLE = False

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class AsyncTaskProcessor:
    """
    Asynchronous task processor with Redis Queue backend
    
    Supports:
    - LLM request queuing
    - Background task execution
    - Progress tracking
    - WebSocket notifications
    - Task scheduling and prioritization
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.task_queue = None
        self.running_tasks = {}
        self.task_results = {}
        self.notification_callbacks = {}
        self.use_redis = REDIS_QUEUE_AVAILABLE
        
        # In-memory fallback for development
        self.memory_queue = []
        self.memory_tasks = {}
        
    async def initialize(self):
        """Initialize async task processor"""
        if self.use_redis:
            try:
                # Setup Redis connection
                self.redis_client = redis.from_url(self.redis_url)
                
                # Test connection
                self.redis_client.ping()
                
                # Initialize RQ queues
                self.task_queue = Queue('ai_assistant_tasks', connection=self.redis_client)
                self.llm_queue = Queue('llm_requests', connection=self.redis_client)
                self.notification_queue = Queue('notifications', connection=self.redis_client)
                
                logger.info("✅ Redis Queue task processor initialized")
                
            except Exception as e:
                logger.warning(f"⚠️ Redis Queue unavailable, using memory fallback: {e}")
                self.use_redis = False
        
        if not self.use_redis:
            logger.info("📝 Using in-memory task processor")
    
    async def submit_task(
        self, 
        task_func: str, 
        task_args: Dict[str, Any] = None, 
        priority: TaskPriority = TaskPriority.NORMAL,
        user_id: str = None,
        notification_callback: str = None
    ) -> str:
        """
        Submit a task for background processing
        
        Args:
            task_func: Function name to execute
            task_args: Arguments for the function
            priority: Task priority level
            user_id: User ID for tracking
            notification_callback: WebSocket callback for notifications
            
        Returns:
            Task ID for tracking
        """
        task_id = str(uuid.uuid4())
        task_args = task_args or {}
        
        task_data = {
            "task_id": task_id,
            "task_func": task_func,
            "task_args": task_args,
            "priority": priority.value,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "status": TaskStatus.PENDING.value,
            "progress": 0,
            "notification_callback": notification_callback
        }
        
        try:
            if self.use_redis:
                # Submit to Redis Queue
                if task_func.startswith("llm_"):
                    job = self.llm_queue.enqueue(
                        self._execute_task,
                        task_data,
                        job_timeout='30m',
                        result_ttl=3600  # Keep results for 1 hour
                    )
                    task_data["job_id"] = job.id
                else:
                    job = self.task_queue.enqueue(
                        self._execute_task,
                        task_data,
                        job_timeout='10m',
                        result_ttl=1800  # Keep results for 30 minutes
                    )
                    task_data["job_id"] = job.id
                
                # Store task metadata
                await self._store_task_metadata(task_id, task_data)
                
            else:
                # Memory fallback
                task_data["job_id"] = task_id
                self.memory_queue.append(task_data)
                self.memory_tasks[task_id] = task_data
                
                # Process immediately in memory mode (for development)
                asyncio.create_task(self._process_memory_task(task_data))
            
            logger.info(f"Task submitted: {task_id} ({task_func}) for user {user_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to submit task {task_id}: {e}")
            raise
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get current status of a task"""
        try:
            if self.use_redis:
                # Get from Redis
                task_data = await self._get_task_metadata(task_id)
                if task_data:
                    # Check if job is still running
                    job_id = task_data.get("job_id")
                    if job_id:
                        from rq import job
                        try:
                            job_obj = job.Job.fetch(job_id, connection=self.redis_client)
                            task_data["status"] = job_obj.get_status()
                            if job_obj.result:
                                task_data["result"] = job_obj.result
                        except Exception:
                            pass  # Job might be expired
                    
                    return task_data
            else:
                # Memory fallback
                return self.memory_tasks.get(task_id, {"error": "Task not found"})
                
        except Exception as e:
            logger.error(f"Error getting task status {task_id}: {e}")
            return {"error": str(e)}
        
        return {"error": "Task not found"}
    
    async def cancel_task(self, task_id: str, user_id: str = None) -> bool:
        """Cancel a pending or running task"""
        try:
            task_data = await self.get_task_status(task_id)
            
            # Check permissions
            if user_id and task_data.get("user_id") != user_id:
                logger.warning(f"User {user_id} attempted to cancel task {task_id} owned by {task_data.get('user_id')}")
                return False
            
            if self.use_redis:
                job_id = task_data.get("job_id")
                if job_id:
                    from rq import job
                    try:
                        job_obj = job.Job.fetch(job_id, connection=self.redis_client)
                        job_obj.cancel()
                        
                        # Update task status
                        task_data["status"] = TaskStatus.CANCELLED.value
                        task_data["cancelled_at"] = datetime.now().isoformat()
                        await self._store_task_metadata(task_id, task_data)
                        
                        logger.info(f"Task cancelled: {task_id}")
                        return True
                    except Exception as e:
                        logger.error(f"Failed to cancel Redis job {job_id}: {e}")
            else:
                # Memory fallback
                if task_id in self.memory_tasks:
                    self.memory_tasks[task_id]["status"] = TaskStatus.CANCELLED.value
                    self.memory_tasks[task_id]["cancelled_at"] = datetime.now().isoformat()
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return False
    
    async def get_user_tasks(self, user_id: str, status: TaskStatus = None) -> List[Dict[str, Any]]:
        """Get all tasks for a user"""
        user_tasks = []
        
        try:
            if self.use_redis:
                # Search Redis for user tasks (this is simplified - in production would use proper indexing)
                task_keys = await self._get_user_task_keys(user_id)
                for task_key in task_keys:
                    task_data = await self._get_task_metadata(task_key)
                    if task_data and (not status or task_data.get("status") == status.value):
                        user_tasks.append(task_data)
            else:
                # Memory fallback
                for task_data in self.memory_tasks.values():
                    if task_data.get("user_id") == user_id:
                        if not status or task_data.get("status") == status.value:
                            user_tasks.append(task_data)
            
            # Sort by creation time (newest first)
            user_tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting user tasks for {user_id}: {e}")
        
        return user_tasks
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = {
            "processor_type": "redis" if self.use_redis else "memory",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if self.use_redis:
                # Redis Queue stats
                stats.update({
                    "task_queue_size": len(self.task_queue),
                    "llm_queue_size": len(self.llm_queue),
                    "notification_queue_size": len(self.notification_queue),
                    "total_jobs_processed": self.task_queue.count,
                    "failed_jobs": len(self.task_queue.failed_job_registry),
                    "started_jobs": len(self.task_queue.started_job_registry)
                })
            else:
                # Memory stats
                total_tasks = len(self.memory_tasks)
                pending_tasks = len([t for t in self.memory_tasks.values() if t.get("status") == TaskStatus.PENDING.value])
                running_tasks = len([t for t in self.memory_tasks.values() if t.get("status") == TaskStatus.RUNNING.value])
                completed_tasks = len([t for t in self.memory_tasks.values() if t.get("status") == TaskStatus.COMPLETED.value])
                
                stats.update({
                    "memory_queue_size": len(self.memory_queue),
                    "total_tasks": total_tasks,
                    "pending_tasks": pending_tasks,
                    "running_tasks": running_tasks,
                    "completed_tasks": completed_tasks
                })
                
        except Exception as e:
            stats["error"] = str(e)
            logger.error(f"Error getting queue stats: {e}")
        
        return stats
    
    def _execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task (runs in worker process)"""
        task_id = task_data["task_id"]
        task_func = task_data["task_func"]
        task_args = task_data["task_args"]
        
        try:
            # Update status to running
            task_data["status"] = TaskStatus.RUNNING.value
            task_data["started_at"] = datetime.now().isoformat()
            
            # Execute the specific task function
            if task_func == "llm_generate_rfc":
                result = self._execute_llm_rfc_generation(task_args)
            elif task_func == "llm_enhance_document":
                result = self._execute_llm_document_enhancement(task_args)
            elif task_func == "process_data_sync":
                result = self._execute_data_sync(task_args)
            elif task_func == "send_budget_alert":
                result = self._execute_budget_alert(task_args)
            elif task_func == "generate_analytics_report":
                result = self._execute_analytics_report(task_args)
            else:
                raise ValueError(f"Unknown task function: {task_func}")
            
            # Update status to completed
            task_data["status"] = TaskStatus.COMPLETED.value
            task_data["completed_at"] = datetime.now().isoformat()
            task_data["result"] = result
            task_data["progress"] = 100
            
            logger.info(f"Task completed: {task_id}")
            return task_data
            
        except Exception as e:
            # Update status to failed
            task_data["status"] = TaskStatus.FAILED.value
            task_data["failed_at"] = datetime.now().isoformat()
            task_data["error"] = str(e)
            task_data["traceback"] = traceback.format_exc()
            
            logger.error(f"Task failed: {task_id} - {e}")
            return task_data
    
    async def _process_memory_task(self, task_data: Dict[str, Any]):
        """Process task in memory mode (for development)"""
        try:
            result = self._execute_task(task_data)
            self.memory_tasks[task_data["task_id"]] = result
        except Exception as e:
            logger.error(f"Memory task processing failed: {e}")
    
    def _execute_llm_rfc_generation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LLM RFC generation task"""
        # Mock implementation - in production would call actual LLM service
        time.sleep(2)  # Simulate processing time
        
        return {
            "rfc_content": f"Generated RFC for: {args.get('topic', 'Unknown')}",
            "word_count": 1500,
            "processing_time": 2.0,
            "llm_provider": "openai",
            "model": "gpt-4"
        }
    
    def _execute_llm_document_enhancement(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LLM document enhancement task"""
        # Mock implementation
        time.sleep(1.5)
        
        return {
            "enhanced_content": f"Enhanced document: {args.get('document_id', 'Unknown')}",
            "improvements": ["Grammar fixes", "Style improvements", "Structure optimization"],
            "processing_time": 1.5,
            "llm_provider": "anthropic",
            "model": "claude-3-sonnet"
        }
    
    def _execute_data_sync(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data synchronization task"""
        # Mock implementation
        time.sleep(1.0)
        
        return {
            "synced_records": 150,
            "source": args.get("source", "confluence"),
            "sync_time": datetime.now().isoformat(),
            "processing_time": 1.0
        }
    
    def _execute_budget_alert(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute budget alert sending task"""
        # Mock implementation
        time.sleep(0.5)
        
        return {
            "alert_sent": True,
            "recipient": args.get("user_email", "unknown"),
            "alert_type": args.get("alert_type", "budget_warning"),
            "processing_time": 0.5
        }
    
    def _execute_analytics_report(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analytics report generation task"""
        # Mock implementation
        time.sleep(3.0)
        
        return {
            "report_generated": True,
            "report_type": args.get("report_type", "usage_summary"),
            "data_points": 500,
            "charts_generated": 5,
            "processing_time": 3.0
        }
    
    async def _store_task_metadata(self, task_id: str, task_data: Dict[str, Any]):
        """Store task metadata in Redis"""
        if self.use_redis:
            try:
                redis_client = aioredis.from_url(self.redis_url)
                await redis_client.setex(
                    f"ai_assistant:task:{task_id}",
                    3600,  # 1 hour TTL
                    json.dumps(task_data, default=str)
                )
                await redis_client.close()
            except Exception as e:
                logger.error(f"Failed to store task metadata: {e}")
    
    async def _get_task_metadata(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task metadata from Redis"""
        if self.use_redis:
            try:
                redis_client = aioredis.from_url(self.redis_url)
                data = await redis_client.get(f"ai_assistant:task:{task_id}")
                await redis_client.close()
                
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Failed to get task metadata: {e}")
        
        return None
    
    async def _get_user_task_keys(self, user_id: str) -> List[str]:
        """Get task keys for a user (simplified implementation)"""
        # In production, would use proper Redis indexing
        return []
    
    async def cleanup_completed_tasks(self, older_than_hours: int = 24):
        """Clean up completed tasks older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        cleaned_count = 0
        
        try:
            if self.use_redis:
                # Redis cleanup would be more complex in production
                pass
            else:
                # Memory cleanup
                tasks_to_remove = []
                for task_id, task_data in self.memory_tasks.items():
                    completed_at = task_data.get("completed_at")
                    if completed_at:
                        task_time = datetime.fromisoformat(completed_at)
                        if task_time < cutoff_time:
                            tasks_to_remove.append(task_id)
                
                for task_id in tasks_to_remove:
                    del self.memory_tasks[task_id]
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} completed tasks older than {older_than_hours} hours")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up tasks: {e}")
            return 0

# Global async task processor instance
async_processor = AsyncTaskProcessor() 