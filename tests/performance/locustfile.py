#!/usr/bin/env python3
"""
Locust Load Testing Configuration for AI Assistant
"""

from locust import HttpUser, task, between
import random
import json


class AIAssistantUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a simulated user starts"""
        # Health check on start
        self.client.get("/health")
    
    @task(5)
    def health_check(self):
        """Basic health check - most frequent task"""
        self.client.get("/health")
    
    @task(3)
    def api_health_check(self):
        """API health check"""
        self.client.get("/api/health")
    
    @task(3)
    def api_v1_health_check(self):
        """API v1 health check"""
        self.client.get("/api/v1/health")
    
    @task(2)
    def monitoring_metrics(self):
        """Get current metrics"""
        self.client.get("/api/v1/monitoring/metrics/current")
    
    @task(2)
    def monitoring_performance(self):
        """Get performance summary"""
        self.client.get("/api/v1/monitoring/performance/summary")
    
    @task(1)
    def auth_budget_status(self):
        """Check auth budget status"""
        self.client.get("/api/v1/auth/budget/status")
    
    @task(1)
    def websocket_stats(self):
        """Get WebSocket statistics"""
        self.client.get("/api/v1/ws/stats")
    
    @task(1)
    def realtime_monitoring(self):
        """Realtime monitoring health"""
        self.client.get("/api/v1/realtime-monitoring/health")
    
    @task(1)
    def optimization_history(self):
        """Get optimization history"""
        self.client.get("/api/v1/optimization/history")
    
    # POST endpoints for more realistic load
    @task(1)
    def auth_login_attempt(self):
        """Simulate login attempt"""
        payload = {
            "username": f"user_{random.randint(1, 100)}",
            "password": "test_password"
        }
        self.client.post("/api/v1/auth/login", json=payload)
    
    @task(1)
    def submit_async_task(self):
        """Submit async task"""
        payload = {
            "task_type": "analysis",
            "priority": random.choice(["normal", "high", "low"]),
            "data": {"test": "data"}
        }
        self.client.post("/api/v1/async-tasks/submit", json=payload)
    
    @task(1)
    def optimization_benchmark(self):
        """Start optimization benchmark"""
        payload = {
            "component": random.choice(["search", "cache", "database"]),
            "duration": 60
        }
        self.client.post("/api/v1/optimization/benchmark", json=payload)


class AdminUser(HttpUser):
    """Admin user with different usage patterns"""
    wait_time = between(2, 5)
    weight = 1  # Less frequent than regular users
    
    @task(3)
    def monitoring_metrics_history(self):
        """Admin checking metrics history"""
        self.client.get("/api/v1/monitoring/metrics/history")
    
    @task(2)
    def system_optimization(self):
        """Admin triggering system optimization"""
        payload = {
            "optimization_type": "performance",
            "target": "all_systems"
        }
        self.client.post("/api/v1/optimization/optimize", json=payload)
    
    @task(1)
    def health_check(self):
        """Admin health check"""
        self.client.get("/health")


class HighLoadUser(HttpUser):
    """User simulating high load scenarios"""
    wait_time = between(0.1, 1)  # Very frequent requests
    weight = 2  # More frequent than admin users
    
    @task(10)
    def rapid_health_checks(self):
        """Rapid health checks"""
        self.client.get("/health")
    
    @task(5)
    def rapid_api_calls(self):
        """Rapid API calls"""
        endpoints = [
            "/api/health",
            "/api/v1/health", 
            "/api/v1/monitoring/metrics/current"
        ]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint)
    
    @task(1)
    def stress_auth_budget(self):
        """Stress test auth budget"""
        self.client.get("/api/v1/auth/budget/status")


# Custom test scenarios
class BurstLoadUser(HttpUser):
    """Simulates burst load patterns"""
    wait_time = between(0, 0.5)  # Very short wait times
    
    def on_start(self):
        # Burst of requests on start
        for _ in range(10):
            self.client.get("/health")
    
    @task
    def burst_requests(self):
        """Burst pattern requests"""
        # Make 3-5 requests in quick succession
        for _ in range(random.randint(3, 5)):
            self.client.get("/api/health")
            self.client.get("/api/v1/health")


# Load test configuration
if __name__ == "__main__":
    # This allows running locust directly with this file
    import subprocess
    import sys
    
    # Start locust with web UI
    cmd = [
        "locust",
        "-f", __file__,
        "--host", "http://localhost:8000",
        "--web-host", "0.0.0.0",
        "--web-port", "8089"
    ]
    
    subprocess.run(cmd) 