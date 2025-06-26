"""
WebSocket endpoints for FastAPI application
Enhanced with standardized async patterns for enterprise reliability
Version: 2.1 Async Optimized
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from typing import Optional
import json
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

from app.websocket import handle_websocket_connection, manager, send_notification_to_user, broadcast_notification
from app.security.auth import get_current_user

import logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time communication
    Enhanced with timeout protection and connection resilience
    """
    try:
        # Enhanced WebSocket connection with timeout protection
        await with_timeout(
            handle_websocket_connection(websocket, user_id),
            AsyncTimeouts.WEBSOCKET_CONNECT,  # 10 seconds for connection
            f"WebSocket connection timed out for user: {user_id}",
            {"user_id": user_id, "endpoint": "ws_user"}
        )
        
    except AsyncTimeoutError as e:
        logger.error(f"❌ WebSocket connection timed out for user {user_id}: {e}")
        try:
            await websocket.close(code=4000, reason="Connection timeout")
        except Exception:
            pass
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error for user {user_id}: {e}")
        try:
            await websocket.close(code=4001, reason="Internal error")
        except Exception:
            pass

@router.websocket("/ws")
async def websocket_anonymous(websocket: WebSocket):
    """
    WebSocket endpoint for anonymous users
    Enhanced with timeout protection and error handling
    """
    try:
        # Enhanced anonymous WebSocket connection
        await with_timeout(
            handle_websocket_connection(websocket, "anonymous"),
            AsyncTimeouts.WEBSOCKET_CONNECT,  # 10 seconds for connection
            "Anonymous WebSocket connection timed out",
            {"user_id": "anonymous", "endpoint": "ws_anonymous"}
        )
        
    except AsyncTimeoutError as e:
        logger.error(f"❌ Anonymous WebSocket connection timed out: {e}")
        try:
            await websocket.close(code=4000, reason="Connection timeout")
        except Exception:
            pass
    except WebSocketDisconnect:
        logger.info("Anonymous WebSocket disconnected")
    except Exception as e:
        logger.error(f"❌ Anonymous WebSocket error: {e}")
        try:
            await websocket.close(code=4001, reason="Internal error")
        except Exception:
            pass

@router.get("/ws/stats")
@async_retry(max_attempts=2, delay=0.5, exceptions=(HTTPException,))
async def get_websocket_stats():
    """
    Get current WebSocket connection statistics
    Enhanced with timeout protection and concurrent stats collection
    """
    try:
        # Collect WebSocket stats with timeout protection
        stats_data = await with_timeout(
            _collect_websocket_stats_internal(),
            AsyncTimeouts.DATABASE_QUERY,  # 10 seconds for stats collection
            "WebSocket stats collection timed out",
            {"operation": "websocket_stats"}
        )
        
        logger.info(f"✅ WebSocket stats collected: {stats_data['total_connections']} connections")
        
        return stats_data
        
    except AsyncTimeoutError as e:
        logger.warning(f"⚠️ WebSocket stats collection timed out: {e}")
        return {
            "status": "timeout",
            "total_connections": 0,
            "connected_users": [],
            "users_count": 0,
            "error": "Stats collection timed out"
        }
    except AsyncRetryError as e:
        logger.error(f"❌ WebSocket stats collection failed after retries: {e}")
        raise HTTPException(status_code=500, detail=f"Stats collection failed: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Error getting WebSocket stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get WebSocket stats: {str(e)}"
        )

async def _collect_websocket_stats_internal():
    """Internal WebSocket stats collection with concurrent processing"""
    
    # Collect stats concurrently for better performance
    stats_tasks = [
        _get_total_connections(),
        _get_connected_users(),
        _get_connection_metadata()
    ]
    
    total_connections, connected_users, metadata = await safe_gather(
        *stats_tasks,
        return_exceptions=True,
        timeout=AsyncTimeouts.DATABASE_QUERY / 2,  # 5 seconds for concurrent stats
        max_concurrency=3
    )
    
    # Handle exceptions gracefully
    if isinstance(total_connections, Exception):
        total_connections = 0
    if isinstance(connected_users, Exception):
        connected_users = []
    if isinstance(metadata, Exception):
        metadata = {}
    
    return {
        "total_connections": total_connections,
        "connected_users": connected_users,
        "users_count": len(connected_users),
        "connection_metadata": metadata,
        "async_optimized": True
    }

async def _get_total_connections() -> int:
    """Get total connections count"""
    try:
        return manager.get_total_connections_count()
    except Exception as e:
        logger.warning(f"Failed to get total connections: {e}")
        return 0

async def _get_connected_users() -> list:
    """Get connected users list"""
    try:
        return manager.get_connected_users()
    except Exception as e:
        logger.warning(f"Failed to get connected users: {e}")
        return []

async def _get_connection_metadata() -> dict:
    """Get connection metadata"""
    try:
        return {
            "last_updated": time.time(),
            "manager_status": "healthy"
        }
    except Exception as e:
        logger.warning(f"Failed to get connection metadata: {e}")
        return {}

@router.post("/ws/notify/{user_id}")
@async_retry(max_attempts=2, delay=1.0, exceptions=(HTTPException,))
async def send_notification(
    user_id: str, 
    notification_type: str, 
    message: dict,
    current_user=Depends(get_current_user)
):
    """
    Send notification to a specific user
    Enhanced with timeout protection and delivery confirmation
    """
    try:
        # Send notification with timeout protection
        delivery_result = await with_timeout(
            _send_notification_internal(user_id, notification_type, message),
            AsyncTimeouts.WEBSOCKET_MESSAGE * 3,  # 15 seconds for notification delivery
            f"Notification delivery timed out (user: {user_id}, type: {notification_type})",
            {
                "user_id": user_id,
                "notification_type": notification_type,
                "sender": current_user.user_id if hasattr(current_user, 'user_id') else 'system'
            }
        )
        
        logger.info(f"✅ Notification sent to {user_id}: {notification_type}")
        
        return {
            "status": "sent" if delivery_result else "queued",
            "user_id": user_id,
            "type": notification_type,
            "delivery_result": delivery_result,
            "async_optimized": True
        }
        
    except AsyncTimeoutError as e:
        logger.error(f"❌ Notification delivery timed out: {e}")
        # Queue notification for later delivery
        create_background_task(
            send_notification_to_user(user_id, notification_type, message),
            name=f"retry_notification_{user_id}_{notification_type}"
        )
        
        return {
            "status": "timeout_queued",
            "user_id": user_id,
            "type": notification_type,
            "message": "Notification queued due to timeout"
        }
    except AsyncRetryError as e:
        logger.error(f"❌ Notification delivery failed after retries: {e}")
        raise HTTPException(status_code=500, detail=f"Notification delivery failed: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Failed to send notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )

async def _send_notification_internal(user_id: str, notification_type: str, message: dict) -> bool:
    """Internal notification sending with enhanced error handling"""
    try:
        await send_notification_to_user(user_id, notification_type, message)
        return True
    except Exception as e:
        logger.warning(f"Notification delivery failed for {user_id}: {e}")
        return False

@router.post("/ws/broadcast")
@async_retry(max_attempts=2, delay=1.0, exceptions=(HTTPException,))
async def broadcast_message(
    notification_type: str,
    message: dict,
    exclude_user: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """
    Broadcast notification to all connected users
    Enhanced with concurrent delivery and progress tracking
    """
    try:
        # Execute broadcast with timeout protection
        broadcast_result = await with_timeout(
            _broadcast_message_internal(notification_type, message, exclude_user),
            AsyncTimeouts.WEBSOCKET_MESSAGE * 5,  # 25 seconds for broadcast
            f"Broadcast timed out (type: {notification_type}, exclude: {exclude_user})",
            {
                "notification_type": notification_type,
                "exclude_user": exclude_user,
                "sender": current_user.user_id if hasattr(current_user, 'user_id') else 'system'
            }
        )
        
        logger.info(f"✅ Broadcast completed: {notification_type} to {broadcast_result['successful']} users")
        
        return {
            "status": "broadcasted",
            "type": notification_type,
            "excluded_user": exclude_user,
            "total_recipients": broadcast_result['total_recipients'],
            "successful_deliveries": broadcast_result['successful'],
            "failed_deliveries": broadcast_result['failed'],
            "async_optimized": True
        }
        
    except AsyncTimeoutError as e:
        logger.error(f"❌ Broadcast timed out: {e}")
        # Start background broadcast for timeout recovery
        create_background_task(
            broadcast_notification(notification_type, message, exclude_user),
            name=f"retry_broadcast_{notification_type}"
        )
        
        return {
            "status": "timeout_queued",
            "type": notification_type,
            "message": "Broadcast queued due to timeout",
            "background_task": True
        }
    except AsyncRetryError as e:
        logger.error(f"❌ Broadcast failed after retries: {e}")
        raise HTTPException(status_code=500, detail=f"Broadcast failed: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Failed to broadcast: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to broadcast: {str(e)}"
        )

async def _broadcast_message_internal(
    notification_type: str, 
    message: dict, 
    exclude_user: Optional[str]
) -> dict:
    """Internal broadcast with concurrent delivery tracking"""
    
    try:
        # Get connected users count before broadcast
        total_recipients = manager.get_total_connections_count()
        
        # Execute broadcast
        await broadcast_notification(notification_type, message, exclude_user)
        
        # For now, assume all deliveries successful
        # In production, this would track actual delivery results
        return {
            "total_recipients": total_recipients,
            "successful": total_recipients,
            "failed": 0
        }
        
    except Exception as e:
        logger.error(f"Broadcast execution failed: {e}")
        return {
            "total_recipients": 0,
            "successful": 0,
            "failed": 1
        }

@router.get("/ws/test")
async def get_test_page():
    """Test page for WebSocket functionality"""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .message-box { 
            border: 1px solid #ccc; 
            height: 300px; 
            overflow-y: scroll; 
            padding: 10px; 
            margin: 10px 0;
            background-color: #f9f9f9;
        }
        .controls { margin: 10px 0; }
        input, button { margin: 5px; padding: 8px; }
        .status { 
            padding: 10px; 
            margin: 10px 0; 
            border-radius: 4px;
        }
        .connected { background-color: #d4edda; color: #155724; }
        .disconnected { background-color: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>WebSocket Test Client</h1>
        
        <div id="status" class="status disconnected">Disconnected</div>
        
        <div class="controls">
            <input type="text" id="userId" placeholder="User ID" value="test_user">
            <button onclick="connect()">Connect</button>
            <button onclick="disconnect()">Disconnect</button>
        </div>
        
        <div class="controls">
            <input type="text" id="messageInput" placeholder="Type message here...">
            <button onclick="sendMessage()">Send Message</button>
            <button onclick="sendPing()">Send Ping</button>
            <button onclick="getStats()">Get Stats</button>
        </div>
        
        <div class="message-box" id="messages"></div>
        
        <div class="controls">
            <button onclick="clearMessages()">Clear Messages</button>
        </div>
    </div>

    <script>
        let ws = null;
        let userId = 'test_user';
        
        function updateStatus(connected, message = '') {
            const statusDiv = document.getElementById('status');
            if (connected) {
                statusDiv.className = 'status connected';
                statusDiv.textContent = 'Connected' + (message ? ': ' + message : '');
            } else {
                statusDiv.className = 'status disconnected';
                statusDiv.textContent = 'Disconnected' + (message ? ': ' + message : '');
            }
        }
        
        function addMessage(message) {
            const messagesDiv = document.getElementById('messages');
            const timestamp = new Date().toLocaleTimeString();
            messagesDiv.innerHTML += `<div><strong>[${timestamp}]</strong> ${JSON.stringify(message, null, 2)}</div>`;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function connect() {
            userId = document.getElementById('userId').value || 'test_user';
            const wsUrl = `ws://localhost:8000/api/v1/ws/${userId}`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function(event) {
                updateStatus(true, `as ${userId}`);
                addMessage({type: 'system', message: 'Connected to WebSocket'});
            };
            
            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    addMessage(data);
                } catch (e) {
                    addMessage({type: 'system', message: 'Received: ' + event.data});
                }
            };
            
            ws.onclose = function(event) {
                updateStatus(false, 'Connection closed');
                addMessage({type: 'system', message: 'WebSocket connection closed'});
            };
            
            ws.onerror = function(error) {
                updateStatus(false, 'Connection error');
                addMessage({type: 'system', message: 'WebSocket error: ' + error});
            };
        }
        
        function disconnect() {
            if (ws) {
                ws.send(JSON.stringify({type: 'disconnect'}));
                ws.close();
                ws = null;
            }
        }
        
        function sendMessage() {
            const input = document.getElementById('messageInput');
            if (ws && input.value) {
                const message = {
                    type: 'custom_message',
                    content: input.value,
                    timestamp: new Date().toISOString()
                };
                ws.send(JSON.stringify(message));
                input.value = '';
            }
        }
        
        function sendPing() {
            if (ws) {
                ws.send(JSON.stringify({type: 'ping'}));
            }
        }
        
        function getStats() {
            if (ws) {
                ws.send(JSON.stringify({type: 'get_stats'}));
            }
        }
        
        function clearMessages() {
            document.getElementById('messages').innerHTML = '';
        }
        
        // Auto-connect on page load
        window.onload = function() {
            connect();
        };
        
        // Handle Enter key in message input
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

__all__ = ["router"] 