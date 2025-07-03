"""
WebSocket Notification System for AI Assistant MVP
Task 2.2: Scalability & Load Handling - Real-time Notifications

Features:
- Real-time task status updates via WebSocket
- User-specific notification channels
- Connection management and cleanup
- Message queuing for offline users
- Performance monitoring integration
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import websockets
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Notification type enumeration"""

    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    BUDGET_ALERT = "budget_alert"
    SYSTEM_ALERT = "system_alert"
    PERFORMANCE_ALERT = "performance_alert"


class WebSocketManager:
    """
    WebSocket connection manager for real-time notifications

    Features:
    - User-specific connection tracking
    - Message broadcasting
    - Connection health monitoring
    - Offline message queuing
    """

    def __init__(self):
        # Active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}

        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

        # Offline message queue (user_id -> messages)
        self.offline_messages: Dict[str, List[Dict[str, Any]]] = {}

        # Connection statistics
        self.connection_stats = {
            "total_connections": 0,
            "current_connections": 0,
            "messages_sent": 0,
            "messages_failed": 0,
            "connection_errors": 0,
        }

        # Message history for debugging (limited to last 100 messages)
        self.message_history: List[Dict[str, Any]] = []

    async def connect(
        self, websocket: WebSocket, user_id: str, connection_info: Dict[str, Any] = None
    ):
        """Connect a WebSocket for a user"""
        try:
            await websocket.accept()

            # Add to active connections
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()

            self.active_connections[user_id].add(websocket)

            # Store connection metadata
            self.connection_metadata[websocket] = {
                "user_id": user_id,
                "connected_at": datetime.now().isoformat(),
                "last_ping": time.time(),
                "message_count": 0,
                "connection_info": connection_info or {},
            }

            # Update stats
            self.connection_stats["total_connections"] += 1
            self.connection_stats["current_connections"] += 1

            logger.info(f"WebSocket connected for user {user_id}")

            # Send any queued offline messages
            await self._send_offline_messages(user_id, websocket)

            # Send connection confirmation
            await self._send_to_websocket(
                websocket,
                {
                    "type": "connection_established",
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat(),
                    "queued_messages": len(self.offline_messages.get(user_id, [])),
                },
            )

        except Exception as e:
            logger.error(f"Error connecting WebSocket for user {user_id}: {e}")
            self.connection_stats["connection_errors"] += 1
            raise

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket"""
        try:
            metadata = self.connection_metadata.get(websocket, {})
            user_id = metadata.get("user_id")

            if user_id and user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)

                # Remove user entry if no more connections
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

            # Remove metadata
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]

            # Update stats
            self.connection_stats["current_connections"] -= 1

            logger.info(f"WebSocket disconnected for user {user_id}")

        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {e}")

    async def send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        data: Dict[str, Any],
        priority: str = "normal",
    ):
        """
        Send notification to a specific user

        Args:
            user_id: Target user ID
            notification_type: Type of notification
            data: Notification data
            priority: Message priority (low, normal, high, urgent)
        """
        message = {
            "type": notification_type.value,
            "data": data,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
            "message_id": str(uuid.uuid4()),
        }

        # Add to message history
        self._add_to_history(user_id, message)

        # Try to send to active connections
        if user_id in self.active_connections:
            active_connections = list(self.active_connections[user_id])
            sent_count = 0

            for websocket in active_connections:
                try:
                    await self._send_to_websocket(websocket, message)
                    sent_count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to send message to WebSocket for user {user_id}: {e}"
                    )
                    # Remove failed connection
                    await self.disconnect(websocket)

            if sent_count > 0:
                logger.debug(
                    f"Notification sent to {sent_count} connections for user {user_id}"
                )
                return True

        # Queue message if user is offline
        await self._queue_offline_message(user_id, message)
        logger.debug(f"Notification queued for offline user {user_id}")
        return False

    async def broadcast_system_notification(
        self,
        notification_type: NotificationType,
        data: Dict[str, Any],
        target_users: Optional[List[str]] = None,
    ):
        """
        Broadcast notification to all connected users or specific users

        Args:
            notification_type: Type of notification
            data: Notification data
            target_users: Optional list of specific user IDs to target
        """
        message = {
            "type": notification_type.value,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "message_id": str(uuid.uuid4()),
            "broadcast": True,
        }

        # Determine target users
        if target_users:
            users_to_notify = target_users
        else:
            users_to_notify = list(self.active_connections.keys())

        sent_count = 0
        failed_count = 0

        for user_id in users_to_notify:
            try:
                success = await self.send_notification(
                    user_id, notification_type, data, priority="high"
                )
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to user {user_id}: {e}")
                failed_count += 1

        logger.info(
            f"Broadcast sent: {sent_count} successful, {failed_count} failed/queued"
        )
        return {"sent": sent_count, "failed": failed_count}

    async def send_task_notification(
        self,
        user_id: str,
        task_id: str,
        task_status: str,
        task_data: Dict[str, Any] = None,
    ):
        """
        Send task-specific notification

        Args:
            user_id: User ID who owns the task
            task_id: Task ID
            task_status: Current task status
            task_data: Additional task data
        """
        # Map task status to notification type
        status_mapping = {
            "running": NotificationType.TASK_STARTED,
            "completed": NotificationType.TASK_COMPLETED,
            "failed": NotificationType.TASK_FAILED,
            "cancelled": NotificationType.TASK_CANCELLED,
        }

        notification_type = status_mapping.get(
            task_status, NotificationType.TASK_PROGRESS
        )

        notification_data = {
            "task_id": task_id,
            "status": task_status,
            "task_data": task_data or {},
        }

        await self.send_notification(
            user_id=user_id,
            notification_type=notification_type,
            data=notification_data,
            priority="normal" if task_status in ["running", "progress"] else "high",
        )

    async def send_budget_alert(
        self, user_id: str, alert_type: str, budget_data: Dict[str, Any]
    ):
        """
        Send budget alert notification

        Args:
            user_id: User ID to alert
            alert_type: Type of budget alert
            budget_data: Budget information
        """
        notification_data = {
            "alert_type": alert_type,
            "budget_info": budget_data,
            "action_required": alert_type in ["budget_exceeded", "budget_warning_95"],
        }

        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.BUDGET_ALERT,
            data=notification_data,
            priority="urgent" if alert_type == "budget_exceeded" else "high",
        )

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        active_users = len(self.active_connections)
        total_active_connections = sum(
            len(connections) for connections in self.active_connections.values()
        )

        # Calculate average connections per user
        avg_connections_per_user = total_active_connections / max(active_users, 1)

        # Get connection details for admin
        connection_details = []
        for user_id, connections in self.active_connections.items():
            for websocket in connections:
                metadata = self.connection_metadata.get(websocket, {})
                connection_details.append(
                    {
                        "user_id": user_id,
                        "connected_at": metadata.get("connected_at"),
                        "message_count": metadata.get("message_count", 0),
                        "last_ping": metadata.get("last_ping", 0),
                    }
                )

        return {
            "active_users": active_users,
            "total_active_connections": total_active_connections,
            "avg_connections_per_user": round(avg_connections_per_user, 2),
            "connection_stats": self.connection_stats,
            "queued_messages": {
                user_id: len(messages)
                for user_id, messages in self.offline_messages.items()
            },
            "connection_details": connection_details,
            "recent_messages": len(self.message_history),
            "timestamp": datetime.now().isoformat(),
        }

    async def cleanup_offline_messages(self, max_age_hours: int = 24):
        """Clean up old offline messages"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        cleaned_count = 0

        for user_id in list(self.offline_messages.keys()):
            messages = self.offline_messages[user_id]

            # Filter out old messages
            fresh_messages = []
            for message in messages:
                try:
                    message_time = datetime.fromisoformat(
                        message["timestamp"]
                    ).timestamp()
                    if message_time > cutoff_time:
                        fresh_messages.append(message)
                    else:
                        cleaned_count += 1
                except Exception:
                    cleaned_count += 1  # Remove malformed messages

            if fresh_messages:
                self.offline_messages[user_id] = fresh_messages
            else:
                del self.offline_messages[user_id]

        logger.info(
            f"Cleaned up {cleaned_count} offline messages older than {max_age_hours} hours"
        )
        return cleaned_count

    async def _send_to_websocket(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message, default=str))

            # Update metadata
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["message_count"] += 1
                self.connection_metadata[websocket]["last_ping"] = time.time()

            # Update stats
            self.connection_stats["messages_sent"] += 1

        except Exception as e:
            self.connection_stats["messages_failed"] += 1
            raise

    async def _send_offline_messages(self, user_id: str, websocket: WebSocket):
        """Send queued offline messages to newly connected user"""
        if user_id in self.offline_messages:
            messages = self.offline_messages[user_id]

            for message in messages:
                try:
                    await self._send_to_websocket(websocket, message)
                except Exception as e:
                    logger.warning(f"Failed to send offline message to {user_id}: {e}")

            # Clear offline messages after sending
            del self.offline_messages[user_id]
            logger.info(f"Sent {len(messages)} offline messages to user {user_id}")

    async def _queue_offline_message(self, user_id: str, message: Dict[str, Any]):
        """Queue message for offline user"""
        if user_id not in self.offline_messages:
            self.offline_messages[user_id] = []

        self.offline_messages[user_id].append(message)

        # Limit queue size per user (keep only last 50 messages)
        if len(self.offline_messages[user_id]) > 50:
            self.offline_messages[user_id] = self.offline_messages[user_id][-50:]

    def _add_to_history(self, user_id: str, message: Dict[str, Any]):
        """Add message to history for debugging"""
        history_entry = {
            "user_id": user_id,
            "message": message,
            "sent_at": datetime.now().isoformat(),
        }

        self.message_history.append(history_entry)

        # Keep only last 100 messages
        if len(self.message_history) > 100:
            self.message_history = self.message_history[-100:]


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


# WebSocket connection handler
async def handle_websocket_connection(websocket: WebSocket):
    """
    Handle WebSocket connection lifecycle

    Expected connection format:
    ws://localhost:8000/ws?token=<jwt_token>&user_id=<user_id>
    """
    user_id = None

    try:
        # Extract user_id from query parameters or headers
        query_params = websocket.query_params
        user_id = query_params.get("user_id")
        token = query_params.get("token")

        if not user_id or not token:
            await websocket.close(code=4000, reason="Missing user_id or token")
            return

        # TODO: Validate JWT token here
        # For now, we'll accept any token for development

        # Connection info
        connection_info = {
            "user_agent": websocket.headers.get("user-agent"),
            "client_ip": websocket.client.host if websocket.client else "unknown",
        }

        # Connect user
        await websocket_manager.connect(websocket, user_id, connection_info)

        # Handle incoming messages
        while True:
            try:
                # Wait for incoming messages (ping/pong, etc.)
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(
                        json.dumps(
                            {"type": "pong", "timestamp": datetime.now().isoformat()}
                        )
                    )
                elif message.get("type") == "subscribe":
                    # Handle subscription to specific notification types
                    pass

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from WebSocket user {user_id}")
            except Exception as e:
                logger.error(
                    f"Error handling WebSocket message from user {user_id}: {e}"
                )
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error for user {user_id}: {e}")
    finally:
        # Cleanup connection
        await websocket_manager.disconnect(websocket)
