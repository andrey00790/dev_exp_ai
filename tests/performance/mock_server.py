#!/usr/bin/env python3
"""
Mock HTTP Server for Load Testing
Simulates AI Assistant API endpoints for performance testing
"""
import asyncio
import json
import logging
import random
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)


class MockAPIHandler(BaseHTTPRequestHandler):
    """Mock API request handler"""

    def log_message(self, format, *args):
        """Suppress default HTTP server logging"""
        pass

    def _send_json_response(self, data: dict, status_code: int = 200):
        """Send JSON response"""
        response_body = json.dumps(data)
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response_body.encode("utf-8"))

    def _simulate_processing_time(self, min_ms: int = 10, max_ms: int = 100):
        """Simulate realistic processing time"""
        delay = random.uniform(min_ms, max_ms) / 1000
        time.sleep(delay)

    def do_GET(self):
        """Handle GET requests"""
        path = urlparse(self.path).path
        query = parse_qs(urlparse(self.path).query)

        try:
            if path == "/api/health" or path == "/health":
                self._handle_health_check()

            elif path == "/api/v1/health":
                self._handle_v1_health_check()

            elif path == "/api/v1/auth/verify":
                self._handle_auth_verify()

            elif path == "/api/v1/auth/budget/status":
                self._handle_budget_status()

            elif path == "/api/v1/ws/stats":
                self._handle_websocket_stats()

            elif path.startswith("/api/v1/monitoring/"):
                self._handle_monitoring_endpoints(path)

            elif path.startswith("/api/v1/realtime-monitoring/"):
                self._handle_realtime_monitoring(path)

            elif path == "/api/v1/optimization/history":
                self._handle_optimization_history()

            else:
                self._send_json_response({"error": "Not found"}, 404)

        except Exception as e:
            logger.error(f"Error handling GET {path}: {e}")
            self._send_json_response({"error": "Internal server error"}, 500)

    def do_POST(self):
        """Handle POST requests"""
        path = urlparse(self.path).path

        try:
            # Read request body
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                request_body = self.rfile.read(content_length)
                try:
                    request_data = json.loads(request_body.decode("utf-8"))
                except json.JSONDecodeError:
                    request_data = {}
            else:
                request_data = {}

            if path == "/api/v1/auth/login":
                self._handle_auth_login(request_data)

            elif path == "/api/v1/async-tasks/submit":
                self._handle_task_submission(request_data)

            elif path.startswith("/api/v1/optimization/"):
                self._handle_optimization_endpoints(path, request_data)

            else:
                self._send_json_response({"error": "Not found"}, 404)

        except Exception as e:
            logger.error(f"Error handling POST {path}: {e}")
            self._send_json_response({"error": "Internal server error"}, 500)

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"
        )
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    # Mock endpoint handlers

    def _handle_health_check(self):
        """Handle health check requests"""
        self._simulate_processing_time(5, 50)

        # Occasionally return error to simulate realistic conditions
        if random.random() < 0.05:  # 5% error rate
            self._send_json_response(
                {"status": "unhealthy", "error": "Service temporarily unavailable"}, 503
            )
        else:
            self._send_json_response(
                {
                    "status": "healthy",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "version": "1.0.0",
                    "uptime": random.randint(3600, 86400),
                }
            )

    def _handle_v1_health_check(self):
        """Handle v1 health check"""
        self._simulate_processing_time(10, 80)

        if random.random() < 0.03:  # 3% error rate
            self._send_json_response({"error": "Health check failed"}, 500)
        else:
            self._send_json_response(
                {
                    "status": "ok",
                    "checks": {
                        "database": "connected",
                        "redis": "connected",
                        "external_api": "available",
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

    def _handle_auth_login(self, request_data):
        """Handle authentication login"""
        self._simulate_processing_time(100, 300)

        email = request_data.get("email", request_data.get("username", ""))
        password = request_data.get("password", "")

        # Simple mock authentication
        if email and password:
            if random.random() < 0.1:  # 10% login failure rate
                self._send_json_response({"error": "Invalid credentials"}, 401)
            else:
                self._send_json_response(
                    {
                        "access_token": f"mock_token_{random.randint(10000, 99999)}",
                        "token_type": "bearer",
                        "expires_in": 3600,
                        "user_id": f"user_{random.randint(1000, 9999)}",
                    }
                )
        else:
            self._send_json_response({"error": "Missing email or password"}, 400)

    def _handle_auth_verify(self):
        """Handle token verification"""
        self._simulate_processing_time(20, 100)

        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            if random.random() < 0.05:  # 5% token invalid
                self._send_json_response({"error": "Invalid token"}, 401)
            else:
                self._send_json_response(
                    {
                        "valid": True,
                        "user_id": f"user_{random.randint(1000, 9999)}",
                        "expires_at": (datetime.now(timezone.utc).timestamp() + 3600),
                    }
                )
        else:
            self._send_json_response({"error": "Missing authorization header"}, 401)

    def _handle_budget_status(self):
        """Handle budget status requests"""
        self._simulate_processing_time(50, 200)

        self._send_json_response(
            {
                "current_usage": round(random.uniform(10.0, 95.0), 2),
                "budget_limit": 100.0,
                "remaining": round(random.uniform(5.0, 90.0), 2),
                "period": "monthly",
                "reset_date": "2024-01-01T00:00:00Z",
            }
        )

    def _handle_websocket_stats(self):
        """Handle WebSocket statistics"""
        self._simulate_processing_time(30, 150)

        self._send_json_response(
            {
                "active_connections": random.randint(5, 100),
                "total_connections": random.randint(1000, 10000),
                "messages_sent": random.randint(50000, 500000),
                "messages_received": random.randint(48000, 490000),
                "average_response_time": round(random.uniform(0.1, 2.0), 3),
            }
        )

    def _handle_monitoring_endpoints(self, path):
        """Handle monitoring endpoints"""
        self._simulate_processing_time(100, 500)

        if "current" in path:
            self._send_json_response(
                {
                    "cpu_usage": round(random.uniform(10.0, 80.0), 1),
                    "memory_usage": round(random.uniform(200.0, 800.0), 1),
                    "disk_usage": round(random.uniform(20.0, 70.0), 1),
                    "network_io": {
                        "bytes_sent": random.randint(1000000, 10000000),
                        "bytes_recv": random.randint(2000000, 20000000),
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

        elif "history" in path:
            # Generate mock historical data
            history = []
            for i in range(24):  # 24 hours of data
                history.append(
                    {
                        "timestamp": (datetime.now(timezone.utc).timestamp() - (i * 3600)),
                        "cpu_usage": round(random.uniform(15.0, 75.0), 1),
                        "memory_usage": round(random.uniform(250.0, 750.0), 1),
                    }
                )

            self._send_json_response({"history": history})

        elif "performance" in path:
            self._send_json_response(
                {
                    "avg_response_time": round(random.uniform(0.1, 1.0), 3),
                    "requests_per_second": round(random.uniform(50.0, 500.0), 1),
                    "error_rate": round(random.uniform(0.1, 5.0), 2),
                    "active_users": random.randint(10, 200),
                }
            )

        else:
            self._send_json_response({"message": "Monitoring endpoint"})

    def _handle_realtime_monitoring(self, path):
        """Handle real-time monitoring"""
        self._simulate_processing_time(50, 200)

        if "health" in path:
            self._send_json_response(
                {
                    "status": "healthy" if random.random() > 0.1 else "degraded",
                    "services": {
                        "api": "healthy",
                        "database": "healthy" if random.random() > 0.05 else "slow",
                        "cache": "healthy",
                        "queue": "healthy",
                    },
                }
            )
        else:
            self._send_json_response({"message": "Real-time monitoring"})

    def _handle_task_submission(self, request_data):
        """Handle async task submission"""
        self._simulate_processing_time(200, 600)

        task_func = request_data.get("task_func", "unknown")
        priority = request_data.get("priority", "normal")

        if random.random() < 0.15:  # 15% task rejection
            self._send_json_response({"error": "Task queue full"}, 503)
        else:
            self._send_json_response(
                {
                    "task_id": f"task_{random.randint(100000, 999999)}",
                    "status": "queued",
                    "priority": priority,
                    "estimated_completion": datetime.now(timezone.utc).timestamp()
                    + random.randint(30, 300),
                }
            )

    def _handle_optimization_endpoints(self, path, request_data):
        """Handle optimization endpoints"""
        self._simulate_processing_time(300, 1000)

        if "benchmark" in path:
            component = request_data.get("component", "unknown")
            self._send_json_response(
                {
                    "benchmark_id": f"bench_{random.randint(10000, 99999)}",
                    "component": component,
                    "status": "running",
                    "estimated_duration": random.randint(60, 300),
                }
            )

        elif "optimize" in path:
            component = request_data.get("component", "unknown")
            self._send_json_response(
                {
                    "optimization_id": f"opt_{random.randint(10000, 99999)}",
                    "component": component,
                    "status": "started",
                    "estimated_completion": datetime.now(timezone.utc).timestamp()
                    + random.randint(120, 600),
                }
            )

        else:
            self._send_json_response({"message": "Optimization endpoint"})

    def _handle_optimization_history(self):
        """Handle optimization history"""
        self._simulate_processing_time(100, 300)

        history = []
        for i in range(10):
            history.append(
                {
                    "id": f"opt_{random.randint(10000, 99999)}",
                    "component": random.choice(
                        ["search", "analytics", "auth", "monitoring"]
                    ),
                    "type": random.choice(
                        ["cache_tuning", "query_optimization", "performance_boost"]
                    ),
                    "status": random.choice(["completed", "failed", "running"]),
                    "improvement": f"{random.randint(5, 50)}%",
                    "timestamp": datetime.now(timezone.utc).timestamp() - (i * 3600),
                }
            )

        self._send_json_response({"history": history})


class MockServer:
    """Mock server controller"""

    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.running = False

    def start(self):
        """Start the mock server"""
        try:
            self.server = HTTPServer((self.host, self.port), MockAPIHandler)
            self.server_thread = threading.Thread(
                target=self.server.serve_forever, daemon=True
            )
            self.server_thread.start()
            self.running = True

            print(f"🚀 Mock server started at http://{self.host}:{self.port}")
            print("Available endpoints:")
            print("  GET  /api/health")
            print("  GET  /api/v1/health")
            print("  POST /api/v1/auth/login")
            print("  GET  /api/v1/auth/verify")
            print("  GET  /api/v1/auth/budget/status")
            print("  GET  /api/v1/ws/stats")
            print("  GET  /api/v1/monitoring/metrics/current")
            print("  GET  /api/v1/monitoring/metrics/history")
            print("  GET  /api/v1/monitoring/performance/summary")
            print("  GET  /api/v1/realtime-monitoring/health")
            print("  POST /api/v1/async-tasks/submit")
            print("  POST /api/v1/optimization/benchmark")
            print("  POST /api/v1/optimization/optimize")
            print("  GET  /api/v1/optimization/history")

        except Exception as e:
            print(f"❌ Failed to start mock server: {e}")

    def stop(self):
        """Stop the mock server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.running = False
            print("🛑 Mock server stopped")

    def is_running(self):
        """Check if server is running"""
        return self.running and self.server_thread and self.server_thread.is_alive()


def main():
    """Main function to run the mock server"""
    import argparse

    parser = argparse.ArgumentParser(description="Mock HTTP Server for Load Testing")
    parser.add_argument(
        "--host", default="localhost", help="Server host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Server port (default: 8000)"
    )

    args = parser.parse_args()

    server = MockServer(args.host, args.port)

    try:
        server.start()

        if server.is_running():
            print("\n🎯 Server is ready for load testing!")
            print("Press Ctrl+C to stop the server")

            # Keep the main thread alive
            while server.is_running():
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        server.stop()
    except Exception as e:
        print(f"❌ Server error: {e}")
        server.stop()


if __name__ == "__main__":
    main()
