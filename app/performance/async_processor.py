"""
Async Processing System for AI Assistant MVP
Enhanced with standardized async patterns for enterprise reliability
Version: 2.1 Async Optimized

Features:
- LLM request queuing with Redis Queue
- Background task processing with timeout protection
- WebSocket notifications for completion
- Progress tracking for long-running tasks
- Task status management with retry logic
"""

import asyncio
import json
import logging
import time
import traceback
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# Import standardized async patterns
from app.core.async_utils import (AsyncTimeouts, async_retry,
                                  create_background_task, safe_gather,
                                  with_timeout)
from app.core.exceptions import AsyncRetryError, AsyncTimeoutError

# Redis queue imports with fallback
try:
    import redis
    from rq import Connection, Queue, Worker

    # Skip aioredis for now due to TimeoutError conflict
    # import aioredis
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

    @async_retry(max_attempts=3, delay=2.0, exceptions=(Exception,))
    async def initialize(self):
        """
        Initialize async task processor
        Enhanced with timeout protection and retry logic
        """
        if self.use_redis:
            try:
                # Initialize Redis with timeout protection
                await with_timeout(
                    self._initialize_redis_internal(),
                    AsyncTimeouts.DATABASE_TRANSACTION,  # 30 seconds for Redis setup
                    "Redis initialization timed out",
                    {"redis_url": self.redis_url},
                )

                logger.info("✅ Redis Queue task processor initialized")

            except AsyncTimeoutError as e:
                logger.warning(f"⚠️ Redis initialization timed out: {e}")
                self.use_redis = False
            except Exception as e:
                logger.warning(f"⚠️ Redis Queue unavailable, using memory fallback: {e}")
                self.use_redis = False

        if not self.use_redis:
            logger.info("📝 Using in-memory task processor")

    async def _initialize_redis_internal(self):
        """Internal Redis initialization with connection pooling"""
        # Setup Redis connection
        self.redis_client = redis.from_url(self.redis_url)

        # Test connection
        self.redis_client.ping()

        # Initialize RQ queues concurrently
        queue_tasks = [
            self._create_redis_queue("ai_assistant_tasks"),
            self._create_redis_queue("llm_requests"),
            self._create_redis_queue("notifications"),
        ]

        task_queue, llm_queue, notification_queue = await safe_gather(
            *queue_tasks,
            return_exceptions=False,
            timeout=AsyncTimeouts.DATABASE_QUERY,
            max_concurrency=3,
        )

        self.task_queue = task_queue
        self.llm_queue = llm_queue
        self.notification_queue = notification_queue

    async def _create_redis_queue(self, queue_name: str):
        """Create Redis queue with error handling"""
        try:
            return Queue(queue_name, connection=self.redis_client)
        except Exception as e:
            logger.error(f"Failed to create queue {queue_name}: {e}")
            raise

    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def submit_task(
        self,
        task_func: str,
        task_args: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        user_id: str = None,
        notification_callback: str = None,
    ) -> str:
        """
        Submit a task for background processing
        Enhanced with timeout protection and concurrent processing

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
            "notification_callback": notification_callback,
        }

        try:
            # Execute task submission with timeout protection
            timeout = _calculate_submission_timeout(task_func)

            await with_timeout(
                self._submit_task_internal(task_data, task_func),
                timeout,
                f"Task submission timed out (func: {task_func}, priority: {priority})",
                {
                    "task_id": task_id,
                    "task_func": task_func,
                    "user_id": user_id,
                    "priority": priority.value,
                },
            )

            logger.info(
                f"✅ Task submitted: {task_id} ({task_func}) for user {user_id}"
            )
            return task_id

        except AsyncTimeoutError as e:
            logger.error(f"❌ Task submission timed out: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to submit task {task_id}: {e}")
            raise

    async def _submit_task_internal(self, task_data: Dict[str, Any], task_func: str):
        """Internal task submission with concurrent processing"""
        task_id = task_data["task_id"]

        if self.use_redis:
            # Submit to Redis Queue with concurrent metadata storage
            if task_func.startswith("llm_"):
                job = self.llm_queue.enqueue(
                    self._execute_task,
                    task_data,
                    job_timeout="30m",
                    result_ttl=3600,  # Keep results for 1 hour
                )
                task_data["job_id"] = job.id
            else:
                job = self.task_queue.enqueue(
                    self._execute_task,
                    task_data,
                    job_timeout="10m",
                    result_ttl=1800,  # Keep results for 30 minutes
                )
                task_data["job_id"] = job.id

            # Store task metadata in background
            create_background_task(
                self._store_task_metadata(task_id, task_data),
                name=f"store_metadata_{task_id}",
            )

        else:
            # Memory fallback with enhanced processing
            task_data["job_id"] = task_id
            self.memory_queue.append(task_data)
            self.memory_tasks[task_id] = task_data

            # Process immediately in memory mode (for development)
            create_background_task(
                self._process_memory_task(task_data), name=f"process_memory_{task_id}"
            )


def _calculate_submission_timeout(task_func: str) -> float:
    """Calculate timeout for task submission based on complexity"""
    base_timeout = AsyncTimeouts.BACKGROUND_TASK / 10  # 30 seconds

    # Task complexity multipliers
    complexity_multipliers = {
        "llm_generate_rfc": 1.5,
        "llm_enhance_document": 1.2,
        "generate_analytics_report": 1.3,
        "process_data_sync": 1.0,
        "send_budget_alert": 0.8,
    }

    multiplier = complexity_multipliers.get(task_func, 1.0)
    return min(base_timeout * multiplier, 60.0)  # Cap at 1 minute

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
                            job_obj = job.Job.fetch(
                                job_id, connection=self.redis_client
                            )
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
                logger.warning(
                    f"User {user_id} attempted to cancel task {task_id} owned by {task_data.get('user_id')}"
                )
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
                    self.memory_tasks[task_id][
                        "cancelled_at"
                    ] = datetime.now().isoformat()
                    return True

            return False

        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return False

    async def get_user_tasks(
        self, user_id: str, status: TaskStatus = None
    ) -> List[Dict[str, Any]]:
        """Get all tasks for a user"""
        user_tasks = []

        try:
            if self.use_redis:
                # Search Redis for user tasks (this is simplified - in production would use proper indexing)
                task_keys = await self._get_user_task_keys(user_id)
                for task_key in task_keys:
                    task_data = await self._get_task_metadata(task_key)
                    if task_data and (
                        not status or task_data.get("status") == status.value
                    ):
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
        """
        Get queue statistics
        Enhanced with timeout protection and concurrent stats collection
        """
        stats = {
            "processor_type": "redis" if self.use_redis else "memory",
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Collect stats with timeout protection
            if self.use_redis:
                redis_stats = await with_timeout(
                    self._collect_redis_stats(),
                    AsyncTimeouts.DATABASE_QUERY,  # 10 seconds for Redis stats
                    "Redis stats collection timed out",
                    {"processor_type": "redis"},
                )
                stats.update(redis_stats)
            else:
                memory_stats = await with_timeout(
                    self._collect_memory_stats(),
                    AsyncTimeouts.DATABASE_QUERY / 2,  # 5 seconds for memory stats
                    "Memory stats collection timed out",
                    {"processor_type": "memory"},
                )
                stats.update(memory_stats)

        except AsyncTimeoutError as e:
            stats["error"] = f"Stats collection timed out: {str(e)}"
            logger.warning(f"⚠️ Queue stats collection timed out: {e}")
        except Exception as e:
            stats["error"] = str(e)
            logger.error(f"❌ Error getting queue stats: {e}")

        return stats

    async def _collect_redis_stats(self) -> Dict[str, Any]:
        """Collect Redis queue statistics concurrently"""

        # Collect Redis stats concurrently
        stats_tasks = [
            self._get_queue_size(self.task_queue, "task"),
            self._get_queue_size(self.llm_queue, "llm"),
            self._get_queue_size(self.notification_queue, "notification"),
            self._get_queue_count(self.task_queue),
            self._get_failed_jobs_count(self.task_queue),
            self._get_started_jobs_count(self.task_queue),
        ]

        results = await safe_gather(
            *stats_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.DATABASE_QUERY / 2,
            max_concurrency=6,
        )

        # Process results with error handling
        task_size, llm_size, notif_size, total_count, failed_count, started_count = (
            results
        )

        return {
            "task_queue_size": task_size if not isinstance(task_size, Exception) else 0,
            "llm_queue_size": llm_size if not isinstance(llm_size, Exception) else 0,
            "notification_queue_size": (
                notif_size if not isinstance(notif_size, Exception) else 0
            ),
            "total_jobs_processed": (
                total_count if not isinstance(total_count, Exception) else 0
            ),
            "failed_jobs": (
                failed_count if not isinstance(failed_count, Exception) else 0
            ),
            "started_jobs": (
                started_count if not isinstance(started_count, Exception) else 0
            ),
        }

    async def _collect_memory_stats(self) -> Dict[str, Any]:
        """Collect memory queue statistics concurrently"""

        # Collect memory stats concurrently
        stats_tasks = [
            self._count_memory_tasks_by_status(TaskStatus.PENDING),
            self._count_memory_tasks_by_status(TaskStatus.RUNNING),
            self._count_memory_tasks_by_status(TaskStatus.COMPLETED),
            self._count_memory_tasks_by_status(TaskStatus.FAILED),
        ]

        pending, running, completed, failed = await safe_gather(
            *stats_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.DATABASE_QUERY / 4,
            max_concurrency=4,
        )

        # Handle exceptions
        pending = pending if not isinstance(pending, Exception) else 0
        running = running if not isinstance(running, Exception) else 0
        completed = completed if not isinstance(completed, Exception) else 0
        failed = failed if not isinstance(failed, Exception) else 0

        total_tasks = len(self.memory_tasks)

        return {
            "memory_queue_size": len(self.memory_queue),
            "total_tasks": total_tasks,
            "pending_tasks": pending,
            "running_tasks": running,
            "completed_tasks": completed,
            "failed_tasks": failed,
        }

    async def _get_queue_size(self, queue, queue_type: str) -> int:
        """Get queue size with error handling"""
        try:
            return len(queue)
        except Exception as e:
            logger.warning(f"Failed to get {queue_type} queue size: {e}")
            return 0

    async def _get_queue_count(self, queue) -> int:
        """Get queue processed count"""
        try:
            return queue.count
        except Exception as e:
            logger.warning(f"Failed to get queue count: {e}")
            return 0

    async def _get_failed_jobs_count(self, queue) -> int:
        """Get failed jobs count"""
        try:
            return len(queue.failed_job_registry)
        except Exception as e:
            logger.warning(f"Failed to get failed jobs count: {e}")
            return 0

    async def _get_started_jobs_count(self, queue) -> int:
        """Get started jobs count"""
        try:
            return len(queue.started_job_registry)
        except Exception as e:
            logger.warning(f"Failed to get started jobs count: {e}")
            return 0

    async def _count_memory_tasks_by_status(self, status: TaskStatus) -> int:
        """Count memory tasks by status"""
        try:
            return len(
                [
                    t
                    for t in self.memory_tasks.values()
                    if t.get("status") == status.value
                ]
            )
        except Exception as e:
            logger.warning(f"Failed to count tasks by status {status}: {e}")
            return 0

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
            "model": "gpt-4",
        }

    def _execute_llm_document_enhancement(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LLM document enhancement task"""
        # Mock implementation
        time.sleep(1.5)

        return {
            "enhanced_content": f"Enhanced document: {args.get('document_id', 'Unknown')}",
            "improvements": [
                "Grammar fixes",
                "Style improvements",
                "Structure optimization",
            ],
            "processing_time": 1.5,
            "llm_provider": "anthropic",
            "model": "claude-3-sonnet",
        }

    def _execute_data_sync(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data synchronization task"""
        # Mock implementation
        time.sleep(1.0)

        return {
            "synced_records": 150,
            "source": args.get("source", "confluence"),
            "sync_time": datetime.now().isoformat(),
            "processing_time": 1.0,
        }

    def _execute_budget_alert(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute budget alert sending task"""
        # Mock implementation
        time.sleep(0.5)

        return {
            "alert_sent": True,
            "recipient": args.get("user_email", "unknown"),
            "alert_type": args.get("alert_type", "budget_warning"),
            "processing_time": 0.5,
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
            "processing_time": 3.0,
        }

    async def _store_task_metadata(self, task_id: str, task_data: Dict[str, Any]):
        """Store task metadata in Redis"""
        if self.use_redis:
            try:
                # Use synchronous Redis client for metadata storage
                self.redis_client.setex(
                    f"ai_assistant:task:{task_id}",
                    3600,  # 1 hour TTL
                    json.dumps(task_data, default=str),
                )
            except Exception as e:
                logger.error(f"Failed to store task metadata: {e}")

    async def _get_task_metadata(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task metadata from Redis"""
        if self.use_redis:
            try:
                # Use synchronous Redis client for metadata retrieval
                data = self.redis_client.get(f"ai_assistant:task:{task_id}")

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

            logger.info(
                f"Cleaned up {cleaned_count} completed tasks older than {older_than_hours} hours"
            )
            return cleaned_count

        except Exception as e:
            logger.error(f"Error cleaning up tasks: {e}")
            return 0


# Global async task processor instance
async_processor = AsyncTaskProcessor()
