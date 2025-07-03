#!/usr/bin/env python3
"""
Simple Load Test Script for AI Assistant
Uses correct endpoints that are available in the load test environment
"""

import asyncio
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

BASE_URL = "http://localhost:8000"


async def load_test_endpoint(
    endpoint: str, concurrent_users: int = 50, requests_per_user: int = 10
):
    """Test a specific endpoint with concurrent load"""
    print(
        f"🚀 Testing {endpoint} with {concurrent_users} users, {requests_per_user} req/user"
    )

    response_times = []
    successful_requests = 0
    failed_requests = 0
    start_time = time.time()

    async def user_simulation():
        """Simulate single user requests"""
        nonlocal successful_requests, failed_requests
        user_times = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for _ in range(requests_per_user):
                request_start = time.time()
                try:
                    if endpoint == "/api/v1/async-tasks/submit":
                        response = await client.post(
                            f"{BASE_URL}{endpoint}", json={"task": "test_task"}
                        )
                    else:
                        response = await client.get(f"{BASE_URL}{endpoint}")

                    response_time = time.time() - request_start
                    user_times.append(response_time)

                    if response.status_code in [200, 201]:
                        successful_requests += 1
                    else:
                        failed_requests += 1

                except Exception as e:
                    response_time = time.time() - request_start
                    user_times.append(response_time)
                    failed_requests += 1
                    print(f"Request failed: {e}")

                await asyncio.sleep(0.01)  # Small delay

        return user_times

    # Run concurrent user simulations
    tasks = [user_simulation() for _ in range(concurrent_users)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Aggregate results
    for result in results:
        if isinstance(result, list):
            response_times.extend(result)

    test_duration = time.time() - start_time
    total_requests = successful_requests + failed_requests

    # Calculate metrics
    if response_times:
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        p95_response_time = (
            statistics.quantiles(response_times, n=20)[18]
            if len(response_times) > 19
            else max_response_time
        )
    else:
        avg_response_time = min_response_time = max_response_time = (
            p95_response_time
        ) = 0.0

    success_rate = (
        (successful_requests / total_requests * 100) if total_requests > 0 else 0
    )
    requests_per_second = total_requests / test_duration if test_duration > 0 else 0

    print(f"✅ {endpoint}:")
    print(f"   • Total requests: {total_requests}")
    print(f"   • Success rate: {success_rate:.1f}%")
    print(f"   • Avg response time: {avg_response_time:.3f}s")
    print(f"   • P95 response time: {p95_response_time:.3f}s")
    print(f"   • Requests/sec: {requests_per_second:.1f}")
    print(f"   • Test duration: {test_duration:.2f}s")
    print()

    return {
        "endpoint": endpoint,
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "success_rate": success_rate,
        "avg_response_time": avg_response_time,
        "p95_response_time": p95_response_time,
        "requests_per_second": requests_per_second,
        "test_duration": test_duration,
    }


async def main():
    """Run comprehensive load tests"""
    print("🔧 Starting Simple Load Testing Suite...")
    print("=" * 60)

    # Define test endpoints that actually exist
    test_endpoints = [
        ("/health", 100, 20),  # high load health check
        ("/api/health", 75, 15),  # API health check
        ("/api/v1/health", 50, 10),  # V1 API health
        ("/api/v1/auth/budget/status", 40, 8),  # Budget status
        ("/api/v1/monitoring/metrics/current", 30, 6),  # Current metrics
        ("/api/v1/ws/stats", 25, 5),  # WebSocket stats
        ("/api/v1/async-tasks/submit", 20, 4),  # Async tasks
    ]

    results = []

    for endpoint, users, requests in test_endpoints:
        result = await load_test_endpoint(endpoint, users, requests)
        results.append(result)

    # Summary
    print("📊 LOAD TEST SUMMARY")
    print("=" * 60)

    total_requests = sum(r["total_requests"] for r in results)
    total_successful = sum(r["successful_requests"] for r in results)
    overall_success_rate = (
        (total_successful / total_requests * 100) if total_requests > 0 else 0
    )
    avg_rps = statistics.mean([r["requests_per_second"] for r in results])
    avg_response_time = statistics.mean([r["avg_response_time"] for r in results])

    print(f"• Total requests across all tests: {total_requests}")
    print(f"• Overall success rate: {overall_success_rate:.1f}%")
    print(f"• Average RPS: {avg_rps:.1f}")
    print(f"• Average response time: {avg_response_time:.3f}s")

    # Pass/Fail criteria
    if overall_success_rate >= 95.0 and avg_response_time <= 1.0:
        print("\n🎉 LOAD TESTS PASSED!")
    else:
        print(f"\n❌ LOAD TESTS FAILED!")
        if overall_success_rate < 95.0:
            print(f"   - Success rate too low: {overall_success_rate:.1f}% < 95.0%")
        if avg_response_time > 1.0:
            print(f"   - Response time too high: {avg_response_time:.3f}s > 1.0s")

    # Save results
    with open("simple_load_test_results.json", "w") as f:
        json.dump(
            {
                "timestamp": time.time(),
                "results": results,
                "summary": {
                    "total_requests": total_requests,
                    "total_successful": total_successful,
                    "overall_success_rate": overall_success_rate,
                    "avg_rps": avg_rps,
                    "avg_response_time": avg_response_time,
                },
            },
            f,
            indent=2,
        )

    print(f"\n💾 Results saved to: simple_load_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
