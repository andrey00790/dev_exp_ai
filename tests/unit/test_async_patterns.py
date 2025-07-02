"""
Comprehensive tests for standardized async patterns
Tests the new async utilities, timeout handling, retry logic, and resource management
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.async_utils import (AsyncTaskManager, AsyncTimeouts,
                                  async_resource_manager, async_retry,
                                  create_background_task, create_task,
                                  safe_gather, with_timeout)
from app.core.exceptions import (AsyncResourceError, AsyncRetryError,
                                 AsyncTimeoutError)
from app.core.http_client import StandardHttpClient, http_client_context


class TestAsyncTimeouts:
    """Test timeout configurations"""

    def test_timeout_constants(self):
        """Test that timeout constants are properly defined"""
        assert AsyncTimeouts.HTTP_REQUEST == 30.0
        assert AsyncTimeouts.WEBSOCKET_MESSAGE == 5.0
        assert AsyncTimeouts.CACHE_GET == 2.0
        assert AsyncTimeouts.LLM_REQUEST == 60.0
        assert AsyncTimeouts.DATABASE_QUERY == 10.0


class TestWithTimeout:
    """Test the with_timeout utility function"""

    @pytest.mark.asyncio
    async def test_successful_operation(self):
        """Test that successful operations work normally"""

        async def quick_operation():
            await asyncio.sleep(0.1)
            return "success"

        result = await with_timeout(quick_operation(), 1.0)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_timeout_operation(self):
        """Test that slow operations timeout correctly"""

        async def slow_operation():
            await asyncio.sleep(2.0)
            return "should not reach here"

        with pytest.raises(AsyncTimeoutError) as exc_info:
            await with_timeout(slow_operation(), 0.5)

        assert "timed out after 0.5s" in str(exc_info.value)
        assert exc_info.value.timeout_duration == 0.5

    @pytest.mark.asyncio
    async def test_custom_timeout_message(self):
        """Test custom timeout messages"""

        async def slow_operation():
            await asyncio.sleep(1.0)

        with pytest.raises(AsyncTimeoutError) as exc_info:
            await with_timeout(
                slow_operation(),
                0.1,
                "Custom operation timed out",
                {"operation": "test"},
            )

        assert "Custom operation timed out" in str(exc_info.value)
        assert exc_info.value.operation_context == {"operation": "test"}


class TestSafeGather:
    """Test the safe_gather utility function"""

    @pytest.mark.asyncio
    async def test_successful_gather(self):
        """Test gathering successful operations"""

        async def operation(value):
            await asyncio.sleep(0.1)
            return value * 2

        results = await safe_gather(operation(1), operation(2), operation(3))

        assert results == [2, 4, 6]

    @pytest.mark.asyncio
    async def test_gather_with_exceptions(self):
        """Test gathering with some operations failing"""

        async def good_operation(value):
            return value * 2

        async def bad_operation():
            raise ValueError("Test error")

        results = await safe_gather(
            good_operation(1),
            bad_operation(),
            good_operation(3),
            return_exceptions=True,
        )

        assert results[0] == 2
        assert isinstance(results[1], ValueError)
        assert results[2] == 6

    @pytest.mark.asyncio
    async def test_gather_with_concurrency_limit(self):
        """Test concurrency limiting in gather"""
        call_times = []

        async def timed_operation(value):
            call_times.append(time.time())
            await asyncio.sleep(0.1)
            return value

        start_time = time.time()
        results = await safe_gather(
            timed_operation(1),
            timed_operation(2),
            timed_operation(3),
            timed_operation(4),
            max_concurrency=2,
        )
        total_time = time.time() - start_time

        assert results == [1, 2, 3, 4]
        # With concurrency limit of 2, should take roughly 2 batches
        assert total_time >= 0.2  # At least 2 batches of 0.1s each


class TestAsyncResourceManager:
    """Test async resource management"""

    @pytest.mark.asyncio
    async def test_successful_resource_management(self):
        """Test normal resource creation and cleanup"""
        resource_created = False
        resource_cleaned = False

        async def create_resource():
            nonlocal resource_created
            resource_created = True
            return "test_resource"

        async def cleanup_resource(resource):
            nonlocal resource_cleaned
            resource_cleaned = True
            assert resource == "test_resource"

        async with async_resource_manager(create_resource, cleanup_resource, "test"):
            assert resource_created
            assert not resource_cleaned

        assert resource_cleaned

    @pytest.mark.asyncio
    async def test_resource_creation_failure(self):
        """Test handling of resource creation failures"""

        async def failing_create():
            raise ValueError("Creation failed")

        with pytest.raises(AsyncResourceError) as exc_info:
            async with async_resource_manager(failing_create, None, "failing_test"):
                pass

        assert "Failed to create resource" in str(exc_info.value)
        assert exc_info.value.resource_type == "failing_test"


class TestAsyncRetry:
    """Test async retry decorator"""

    @pytest.mark.asyncio
    async def test_successful_retry(self):
        """Test that successful operations work without retry"""
        call_count = 0

        @async_retry(max_attempts=3, delay=0.1)
        async def stable_operation():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await stable_operation()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_with_eventual_success(self):
        """Test retry mechanism with eventual success"""
        call_count = 0

        @async_retry(max_attempts=3, delay=0.01)
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count} failed")
            return "success"

        result = await flaky_operation()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhaustion(self):
        """Test retry exhaustion handling"""
        call_count = 0

        @async_retry(max_attempts=2, delay=0.01)
        async def always_failing():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Attempt {call_count}")

        with pytest.raises(AsyncRetryError) as exc_info:
            await always_failing()

        assert call_count == 2
        assert exc_info.value.attempts_made == 2
        assert exc_info.value.max_attempts == 2


class TestAsyncTaskManager:
    """Test async task management"""

    @pytest.mark.asyncio
    async def test_task_creation_and_tracking(self):
        """Test basic task creation and tracking"""
        manager = AsyncTaskManager("test_manager")

        async def test_task():
            await asyncio.sleep(0.1)
            return "task_result"

        result = await manager.create_task(test_task(), "test_task")
        assert result == "task_result"

        stats = manager.get_task_stats()
        assert stats["manager_name"] == "test_manager"
        assert stats["total_tasks"] == 0  # Task should be cleaned up

    @pytest.mark.asyncio
    async def test_background_task_creation(self):
        """Test background task creation"""
        manager = AsyncTaskManager("bg_test")
        results = []

        async def background_work(value):
            await asyncio.sleep(0.1)
            results.append(value)

        task = manager.create_background_task(background_work("test"), "bg_task")

        # Wait for background task to complete
        await asyncio.sleep(0.2)

        assert results == ["test"]
        assert task.done()

    @pytest.mark.asyncio
    async def test_task_cleanup(self):
        """Test task cleanup functionality"""
        manager = AsyncTaskManager("cleanup_test")

        async def long_running_task():
            await asyncio.sleep(10.0)  # This should be cancelled

        # Start background task
        task = manager.create_background_task(long_running_task(), "long_task")

        # Verify task is running
        stats = manager.get_task_stats()
        assert stats["active_tasks"] == 1

        # Cleanup tasks
        await manager.cleanup_tasks(timeout=1.0)

        # Verify task is cancelled
        assert task.cancelled()
        final_stats = manager.get_task_stats()
        assert final_stats["active_tasks"] == 0


class TestHttpClient:
    """Test standardized HTTP client"""

    @pytest.mark.asyncio
    async def test_http_client_context_manager(self):
        """Test HTTP client context manager usage"""
        async with http_client_context() as client:
            assert isinstance(client, StandardHttpClient)
            assert client.default_timeout == AsyncTimeouts.HTTP_REQUEST

        # Client should be closed after context exit
        assert client._session is None or client._session.closed

    def test_http_client_factory(self):
        """Test HTTP client factory function"""
        from app.core import (api_client, http_client_factory,
                              internal_service_client)

        # Test basic factory
        client = http_client_factory("https://api.example.com", timeout=10.0)
        assert client.base_url == "https://api.example.com"
        assert client.default_timeout == 10.0

        # Test API client
        api_client_instance = api_client("https://api.example.com", "test-key")
        assert "Authorization" in api_client_instance.default_headers

        # Test internal service client
        service_client = internal_service_client(
            "test-service", "http://localhost:8080"
        )
        assert service_client.default_headers["X-Service-Name"] == "test-service"


class TestIntegrationAsyncPatterns:
    """Integration tests for async patterns"""

    @pytest.mark.asyncio
    async def test_cache_manager_async_patterns(self):
        """Test that cache manager uses new async patterns"""
        from app.performance.cache_manager import (cache_manager, get_cache,
                                                   set_cache)

        # Initialize cache manager
        await cache_manager.initialize()

        try:
            # Test set with timeout
            result = await set_cache("test_async_key", "test_value", ttl=5)
            assert result is True

            # Test get with timeout
            value = await get_cache("test_async_key")
            assert value == "test_value"

            # Test stats
            stats = await cache_manager.get_stats()
            assert "hit_rate" in stats
            assert stats["cache_type"] in ["redis+local", "local"]

        finally:
            await cache_manager.close()

    @pytest.mark.asyncio
    async def test_websocket_async_patterns(self):
        """Test that WebSocket handlers use new async patterns"""
        from app.websocket import (handle_websocket_message,
                                   send_websocket_error,
                                   send_websocket_heartbeat)

        # Mock WebSocket for testing
        mock_websocket = AsyncMock()

        # Test message handling
        test_message = {"type": "ping"}
        await handle_websocket_message(mock_websocket, "test_user", test_message)

        # Verify pong response was sent
        mock_websocket.send_text.assert_called_once()
        sent_data = mock_websocket.send_text.call_args[0][0]
        response = eval(sent_data)  # Simple eval for test - in real code use json.loads
        assert response["type"] == "pong"

        # Test error sending
        mock_websocket.reset_mock()
        await send_websocket_error(mock_websocket, "Test error")

        mock_websocket.send_text.assert_called_once()
        error_data = mock_websocket.send_text.call_args[0][0]
        error_response = eval(error_data)
        assert error_response["type"] == "error"
        assert error_response["message"] == "Test error"


# Performance benchmarks
class TestAsyncPerformance:
    """Performance tests to ensure async utilities don't add significant overhead"""

    @pytest.mark.asyncio
    async def test_with_timeout_overhead(self):
        """Test that with_timeout doesn't add significant overhead"""

        async def simple_operation():
            # Add small delay to make timing more reliable
            await asyncio.sleep(0.001)  # 1ms
            return "result"

        # Warm up
        for _ in range(10):
            await simple_operation()
            await with_timeout(simple_operation(), 10.0)

        # Measure direct operation
        start_time = time.time()
        for _ in range(50):  # Reduced iterations for more precise timing
            await simple_operation()
        direct_time = time.time() - start_time

        # Measure with timeout
        start_time = time.time()
        for _ in range(50):
            await with_timeout(simple_operation(), 10.0)
        timeout_time = time.time() - start_time

        # Overhead should be reasonable (less than 200% to account for variability)
        # and direct_time should be at least 50ms (50 * 1ms)
        if direct_time < 0.01:  # Less than 10ms total - timing too unreliable
            pytest.skip("Timing too unreliable for overhead measurement")

        overhead = (timeout_time - direct_time) / direct_time
        assert (
            overhead < 2.0
        ), f"Timeout overhead too high: {overhead:.2%} (direct: {direct_time:.3f}s, timeout: {timeout_time:.3f}s)"

    @pytest.mark.asyncio
    async def test_async_retry_overhead(self):
        """Test async retry decorator overhead"""
        call_count = 0

        @async_retry(max_attempts=1, delay=0.0)
        async def test_operation():
            nonlocal call_count
            call_count += 1
            return call_count

        # Should have minimal overhead for successful operations
        start_time = time.time()
        for _ in range(50):
            await test_operation()
        total_time = time.time() - start_time

        # Should complete quickly (less than 1 second for 50 operations)
        assert total_time < 1.0, f"Retry decorator too slow: {total_time:.2f}s"


if __name__ == "__main__":
    # Run basic smoke tests
    import sys

    async def run_smoke_tests():
        """Run basic smoke tests to verify async patterns work"""
        print("🧪 Running async patterns smoke tests...")

        # Test basic timeout functionality
        try:

            async def quick_test():
                return "OK"

            result = await with_timeout(quick_test(), 1.0)
            print(f"✅ with_timeout: {result}")
        except Exception as e:
            print(f"❌ with_timeout failed: {e}")
            return False

        # Test task manager
        try:
            manager = AsyncTaskManager("smoke_test")

            async def test_task():
                await asyncio.sleep(0.01)
                return "task_ok"

            result = await manager.create_task(test_task())
            await manager.cleanup_tasks()
            print(f"✅ AsyncTaskManager: {result}")
        except Exception as e:
            print(f"❌ AsyncTaskManager failed: {e}")
            return False

        # Test HTTP client factory
        try:
            from app.core import http_client_factory

            client = http_client_factory("https://httpbin.org")
            print(f"✅ HTTP client: {client.base_url}")
        except Exception as e:
            print(f"❌ HTTP client failed: {e}")
            return False

        print("🎉 All smoke tests passed!")
        return True

    if asyncio.run(run_smoke_tests()):
        sys.exit(0)
    else:
        sys.exit(1)
