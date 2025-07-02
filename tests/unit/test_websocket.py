"""
Unit tests for WebSocket functionality
"""

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import WebSocket
from fastapi.testclient import TestClient

from app.websocket import (ConnectionManager, broadcast_notification,
                           handle_websocket_connection,
                           send_notification_to_user)


class TestConnectionManager:
    """Test ConnectionManager class"""

    @pytest.fixture
    def manager(self):
        """Create a fresh ConnectionManager instance for each test"""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket"""
        websocket = Mock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.receive_text = AsyncMock()
        return websocket

    @pytest.mark.asyncio
    async def test_connect_user(self, manager, mock_websocket):
        """Test connecting a user"""
        user_id = "test_user"

        await manager.connect(mock_websocket, user_id)

        # Check that websocket was accepted
        mock_websocket.accept.assert_called_once()

        # Check that user was added to active connections
        assert user_id in manager.active_connections
        assert mock_websocket in manager.active_connections[user_id]
        assert manager.user_websockets[mock_websocket] == user_id

        # Check counts
        assert manager.get_user_connections_count(user_id) == 1
        assert manager.get_total_connections_count() == 1
        assert user_id in manager.get_connected_users()

    @pytest.mark.asyncio
    async def test_connect_multiple_users(self, manager, mock_websocket):
        """Test connecting multiple users"""
        # Create multiple mock websockets
        websocket1 = Mock(spec=WebSocket)
        websocket1.accept = AsyncMock()
        websocket1.send_text = AsyncMock()

        websocket2 = Mock(spec=WebSocket)
        websocket2.accept = AsyncMock()
        websocket2.send_text = AsyncMock()

        # Connect users
        await manager.connect(websocket1, "user1")
        await manager.connect(websocket2, "user2")

        # Check counts
        assert manager.get_total_connections_count() == 2
        assert len(manager.get_connected_users()) == 2
        assert "user1" in manager.get_connected_users()
        assert "user2" in manager.get_connected_users()

    @pytest.mark.asyncio
    async def test_connect_same_user_multiple_connections(self, manager):
        """Test same user with multiple connections"""
        websocket1 = Mock(spec=WebSocket)
        websocket1.accept = AsyncMock()
        websocket1.send_text = AsyncMock()

        websocket2 = Mock(spec=WebSocket)
        websocket2.accept = AsyncMock()
        websocket2.send_text = AsyncMock()

        user_id = "test_user"

        # Connect same user with two websockets
        await manager.connect(websocket1, user_id)
        await manager.connect(websocket2, user_id)

        # Check counts
        assert manager.get_user_connections_count(user_id) == 2
        assert manager.get_total_connections_count() == 2
        assert len(manager.get_connected_users()) == 1  # Same user

    @pytest.mark.asyncio
    async def test_disconnect_user(self, manager, mock_websocket):
        """Test disconnecting a user"""
        user_id = "test_user"

        # First connect
        await manager.connect(mock_websocket, user_id)
        assert manager.get_total_connections_count() == 1

        # Then disconnect
        await manager.disconnect(mock_websocket)

        # Check that user was removed
        assert user_id not in manager.active_connections
        assert mock_websocket not in manager.user_websockets
        assert manager.get_total_connections_count() == 0
        assert user_id not in manager.get_connected_users()

    @pytest.mark.asyncio
    async def test_send_personal_message(self, manager, mock_websocket):
        """Test sending personal message to user"""
        user_id = "test_user"
        message = {"type": "test", "content": "hello"}

        # Connect user
        await manager.connect(mock_websocket, user_id)

        # Send message
        await manager.send_personal_message(message, user_id)

        # Check that message was sent
        mock_websocket.send_text.assert_called_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_send_personal_message_to_nonexistent_user(self, manager):
        """Test sending message to user that doesn't exist"""
        message = {"type": "test", "content": "hello"}

        # This should not raise an exception
        await manager.send_personal_message(message, "nonexistent_user")

    @pytest.mark.asyncio
    async def test_broadcast_message(self, manager):
        """Test broadcasting message to all users"""
        # Create multiple mock websockets
        websocket1 = Mock(spec=WebSocket)
        websocket1.accept = AsyncMock()
        websocket1.send_text = AsyncMock()

        websocket2 = Mock(spec=WebSocket)
        websocket2.accept = AsyncMock()
        websocket2.send_text = AsyncMock()

        # Connect users
        await manager.connect(websocket1, "user1")
        await manager.connect(websocket2, "user2")

        message = {"type": "broadcast", "content": "hello everyone"}

        # Broadcast
        await manager.broadcast(message)

        # Check that both users received the message
        websocket1.send_text.assert_called_with(json.dumps(message))
        websocket2.send_text.assert_called_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_broadcast_with_exclusion(self, manager):
        """Test broadcasting with user exclusion"""
        # Create multiple mock websockets
        websocket1 = Mock(spec=WebSocket)
        websocket1.accept = AsyncMock()
        websocket1.send_text = AsyncMock()

        websocket2 = Mock(spec=WebSocket)
        websocket2.accept = AsyncMock()
        websocket2.send_text = AsyncMock()

        # Connect users
        await manager.connect(websocket1, "user1")
        await manager.connect(websocket2, "user2")

        message = {"type": "broadcast", "content": "hello everyone"}

        # Broadcast excluding user1
        await manager.broadcast(message, exclude_user="user1")

        # Check that only user2 received the message
        websocket1.send_text.assert_not_called()
        websocket2.send_text.assert_called_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_send_message_with_failed_connection(self, manager):
        """Test handling failed connections during message sending"""
        websocket1 = Mock(spec=WebSocket)
        websocket1.accept = AsyncMock()
        websocket1.send_text = AsyncMock(side_effect=Exception("Connection failed"))

        websocket2 = Mock(spec=WebSocket)
        websocket2.accept = AsyncMock()
        websocket2.send_text = AsyncMock()

        # Connect users
        await manager.connect(websocket1, "user1")
        await manager.connect(websocket2, "user2")

        assert manager.get_total_connections_count() == 2

        message = {"type": "test", "content": "hello"}

        # Broadcast - websocket1 should fail and be removed
        await manager.broadcast(message)

        # Check that failed connection was removed
        assert manager.get_total_connections_count() == 1
        assert "user1" not in manager.get_connected_users()
        assert "user2" in manager.get_connected_users()


class TestWebSocketHandlers:
    """Test WebSocket handler functions"""

    @pytest.mark.asyncio
    async def test_send_notification_to_user(self):
        """Test send_notification_to_user function"""
        with patch("app.websocket.manager") as mock_manager:
            mock_manager.send_personal_message = AsyncMock()

            user_id = "test_user"
            notification_type = "info"
            data = {"message": "test notification"}

            await send_notification_to_user(user_id, notification_type, data)

            # Check that manager.send_personal_message was called with correct structure
            mock_manager.send_personal_message.assert_called_once()
            call_args = mock_manager.send_personal_message.call_args[0]
            sent_message = call_args[0]
            sent_user_id = call_args[1]

            assert sent_user_id == user_id
            assert sent_message["type"] == "notification"
            assert sent_message["notification_type"] == notification_type
            assert sent_message["data"] == data
            assert "timestamp" in sent_message

    @pytest.mark.asyncio
    async def test_broadcast_notification(self):
        """Test broadcast_notification function"""
        with patch("app.websocket.manager") as mock_manager:
            mock_manager.broadcast = AsyncMock()

            notification_type = "system"
            data = {"message": "system maintenance"}
            exclude_user = "admin"

            await broadcast_notification(notification_type, data, exclude_user)

            # Check that manager.broadcast was called with correct structure
            mock_manager.broadcast.assert_called_once()
            call_args = mock_manager.broadcast.call_args[0]
            sent_message = call_args[0]
            sent_exclude_user = call_args[1]

            assert sent_exclude_user == exclude_user
            assert sent_message["type"] == "notification"
            assert sent_message["notification_type"] == notification_type
            assert sent_message["data"] == data
            assert "timestamp" in sent_message


class TestWebSocketConnection:
    """Test WebSocket connection handling"""

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket with all necessary methods"""
        websocket = Mock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.receive_text = AsyncMock()
        return websocket

    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self, mock_websocket):
        """Test ping-pong functionality"""
        # Setup receive_text to return ping, then raise WebSocketDisconnect
        mock_websocket.receive_text.side_effect = [
            json.dumps({"type": "ping"}),
            Exception("WebSocketDisconnect"),  # This will exit the loop
        ]

        with patch("app.websocket.manager") as mock_manager:
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = AsyncMock()
            mock_manager.get_total_connections_count.return_value = 1

            try:
                await handle_websocket_connection(mock_websocket, "test_user")
            except:
                pass  # Expected exception to exit

            # Check that pong was sent
            calls = mock_websocket.send_text.call_args_list
            pong_sent = False
            for call in calls:
                message = json.loads(call[0][0])
                if message.get("type") == "pong":
                    pong_sent = True
                    break

            assert pong_sent, "Pong message should be sent in response to ping"

    @pytest.mark.asyncio
    async def test_websocket_get_stats(self, mock_websocket):
        """Test get_stats functionality"""
        # Setup receive_text to return get_stats, then raise exception to exit
        mock_websocket.receive_text.side_effect = [
            json.dumps({"type": "get_stats"}),
            Exception("Exit"),
        ]

        with patch("app.websocket.manager") as mock_manager:
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = AsyncMock()
            mock_manager.get_total_connections_count.return_value = 5
            mock_manager.get_user_connections_count.return_value = 2
            mock_manager.get_connected_users.return_value = ["user1", "user2"]

            try:
                await handle_websocket_connection(mock_websocket, "test_user")
            except:
                pass  # Expected exception to exit

            # Check that stats were sent
            calls = mock_websocket.send_text.call_args_list
            stats_sent = False
            for call in calls:
                message = json.loads(call[0][0])
                if message.get("type") == "stats":
                    stats_sent = True
                    assert message["data"]["total_connections"] == 5
                    assert message["data"]["user_connections"] == 2
                    assert message["data"]["connected_users"] == ["user1", "user2"]
                    break

            assert stats_sent, "Stats message should be sent in response to get_stats"
