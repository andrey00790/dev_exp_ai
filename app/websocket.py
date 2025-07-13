"""
WebSocket connection handler for real-time notifications
Updated with standardized async patterns
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed

from app.core.async_utils import AsyncTimeouts, with_timeout
from app.core.exceptions import AsyncTimeoutError

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_websockets: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, user_id: str = "anonymous"):
        """Add a new WebSocket connection"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        self.user_websockets[websocket] = user_id

        logger.info(
            f"WebSocket connected for user {user_id}. Total connections: {len(self.user_websockets)}"
        )

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.user_websockets:
            user_id = self.user_websockets[websocket]

            # Remove from user's connections
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

            # Remove from websocket mapping
            del self.user_websockets[websocket]

            logger.info(
                f"WebSocket disconnected for user {user_id}. Total connections: {len(self.user_websockets)}"
            )

    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to all connections of a specific user"""
        if user_id in self.active_connections:
            disconnected_websockets = []

            for websocket in self.active_connections[user_id].copy():
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send message to user {user_id}: {e}")
                    disconnected_websockets.append(websocket)

            # Clean up failed connections
            for websocket in disconnected_websockets:
                await self.disconnect(websocket)

    async def broadcast(self, message: dict, exclude_user: Optional[str] = None):
        """Send message to all connected users"""
        disconnected_websockets = []

        for websocket, user_id in self.user_websockets.copy().items():
            if exclude_user and user_id == exclude_user:
                continue

            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to broadcast to user {user_id}: {e}")
                disconnected_websockets.append(websocket)

        # Clean up failed connections
        for websocket in disconnected_websockets:
            await self.disconnect(websocket)

    def get_user_connections_count(self, user_id: str) -> int:
        """Get number of active connections for a user"""
        return len(self.active_connections.get(user_id, set()))

    def get_total_connections_count(self) -> int:
        """Get total number of active connections"""
        return len(self.user_websockets)

    def get_connected_users(self) -> List[str]:
        """Get list of all connected users"""
        return list(self.active_connections.keys())


# Create manager instance
manager = ConnectionManager()


async def handle_websocket_connection(websocket: WebSocket, user_id: str = "anonymous"):
    """Handle WebSocket connection lifecycle"""
    await manager.connect(websocket, user_id)

    # Send initial connection status message
    await websocket.send_text(
        json.dumps(
            {
                "type": "connection_status",
                "data": {
                    "status": "connected",
                    "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "total_connections": manager.get_total_connections_count(),
                },
            }
        )
    )

    try:
        while True:
            try:
                # Use standardized timeout for WebSocket messages
                data = await with_timeout(
                    websocket.receive_text(),
                    AsyncTimeouts.WEBSOCKET_MESSAGE,
                    f"WebSocket message timeout for user {user_id}",
                )

                try:
                    message = json.loads(data)
                    await handle_websocket_message(websocket, user_id, message)

                    # Check for disconnect message
                    if message.get("type") == "disconnect":
                        break

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from user {user_id}")
                    await send_websocket_error(websocket, "Invalid JSON format")

            except AsyncTimeoutError:
                # Send periodic heartbeat on timeout
                await send_websocket_heartbeat(websocket)
                continue

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except ConnectionClosed:
        logger.info(f"WebSocket connection closed for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        await manager.disconnect(websocket)
        logger.info(f"WebSocket cleanup completed for user {user_id}")


# Utility functions for sending notifications
async def send_notification_to_user(user_id: str, notification_type: str, data: dict):
    """Send a notification to a specific user"""
    message = {
        "type": "notification",
        "notification_type": notification_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await manager.send_personal_message(message, user_id)


async def broadcast_notification(
    notification_type: str, data: dict, exclude_user: Optional[str] = None
):
    """Broadcast a notification to all connected users"""
    message = {
        "type": "notification",
        "notification_type": notification_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await manager.broadcast(message, exclude_user)


async def handle_websocket_message(
    websocket: WebSocket, user_id: str, message: Dict[str, Any]
) -> None:
    """Handle individual WebSocket message with standardized patterns"""
    message_type = message.get("type")

    if message_type == "ping":
        await websocket.send_text(
            json.dumps({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})
        )
    elif message_type == "disconnect":
        logger.info(f"Received disconnect request from user {user_id}")
        # This will be handled by the main loop
    elif message_type == "get_stats":
        await websocket.send_text(
            json.dumps(
                {
                    "type": "stats",
                    "data": {
                        "total_connections": manager.get_total_connections_count(),
                        "user_connections": manager.get_user_connections_count(user_id),
                        "connected_users": manager.get_connected_users(),
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        )
    else:
        # Echo unknown messages back with info
        await websocket.send_text(
            json.dumps(
                {
                    "type": "echo",
                    "original_message": message,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        )


async def send_websocket_error(websocket: WebSocket, error_message: str) -> None:
    """Send standardized error message via WebSocket"""
    await websocket.send_text(
        json.dumps(
            {
                "type": "error",
                "message": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    )


async def send_websocket_heartbeat(websocket: WebSocket) -> None:
    """Send standardized heartbeat message"""
    await websocket.send_text(
        json.dumps({"type": "heartbeat", "timestamp": datetime.now(timezone.utc).isoformat()})
    )


__all__ = [
    "handle_websocket_connection",
    "manager",
    "ConnectionManager",
    "send_notification_to_user",
    "broadcast_notification",
    "handle_websocket_message",
    "send_websocket_error",
    "send_websocket_heartbeat",
]
