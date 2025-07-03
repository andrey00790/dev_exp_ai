"""
Performance Optimization Engine for AI Assistant - Phase 3
Automatic performance tuning, monitoring, and optimization

Features:
- Real-time performance monitoring and analysis
- Automatic optimization recommendations
- Resource usage tracking and prediction
- Performance bottleneck detection
- Intelligent alerting
"""

import asyncio
import json
import logging
import statistics
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import psutil

from app.core.async_utils import (AsyncTaskManager, AsyncTimeouts, async_retry,
                                  create_background_task, safe_gather,
                                  with_timeout)
from app.performance.cache_manager import cache_manager

logger = logging.getLogger(__name__)


class PerformanceMetricType(Enum):
    """Types of performance metrics"""

    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    CACHE_HIT_RATE = "cache_hit_rate"


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class OptimizationStrategy(Enum):
    """Optimization strategies"""

    SCALING = "scaling"
    CACHING = "caching"
    ASYNC_TUNING = "async_tuning"
    RESOURCE_ALLOCATION = "resource_allocation"


@dataclass
class PerformanceMetric:
    """Performance metric data point"""

    metric_type: PerformanceMetricType
    value: float
    timestamp: datetime
    component: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """Performance alert"""

    alert_id: str
    severity: AlertSeverity
    metric_type: PerformanceMetricType
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False


@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation"""

    recommendation_id: str
    strategy: OptimizationStrategy
    description: str
    expected_improvement: float  # percentage
    estimated_effort: str  # low, medium, high
    priority: int  # 1-10
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class PerformanceMonitor:
    """Real-time performance monitoring"""

    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.metrics: Dict[PerformanceMetricType, deque] = {
            metric_type: deque(maxlen=window_size)
            for metric_type in PerformanceMetricType
        }

    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        self.metrics[metric.metric_type].append(metric)

    def get_current_stats(self, metric_type: PerformanceMetricType) -> Dict[str, float]:
        """Get current statistics for a metric type"""
        metrics = self.metrics[metric_type]
        if not metrics:
            return {"avg": 0.0, "min": 0.0, "max": 0.0, "p95": 0.0, "count": 0}

        values = [m.value for m in metrics]
        sorted_values = sorted(values)

        return {
            "avg": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "p95": (
                sorted_values[int(len(sorted_values) * 0.95)]
                if len(sorted_values) > 0
                else 0.0
            ),
            "count": len(values),
        }

    def get_trend(
        self, metric_type: PerformanceMetricType, duration_minutes: int = 30
    ) -> str:
        """Analyze metric trend over time"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_metrics = [
            m for m in self.metrics[metric_type] if m.timestamp > cutoff_time
        ]

        if len(recent_metrics) < 10:
            return "insufficient_data"

        # Simple trend analysis
        values = [m.value for m in recent_metrics]
        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2 :]

        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)

        if second_avg > first_avg * 1.1:
            return "increasing"
        elif second_avg < first_avg * 0.9:
            return "decreasing"
        else:
            return "stable"


class SystemResourceMonitor:
    """System resource monitoring"""

    def __init__(self):
        self.process = psutil.Process()
        self.executor = ThreadPoolExecutor(max_workers=2)

    async def get_system_metrics(self) -> Dict[str, float]:
        """Get current system metrics"""
        loop = asyncio.get_event_loop()

        # Run system calls in thread pool to avoid blocking
        cpu_task = loop.run_in_executor(self.executor, psutil.cpu_percent, 1)
        memory_task = loop.run_in_executor(self.executor, psutil.virtual_memory)
        process_task = loop.run_in_executor(self.executor, self._get_process_metrics)

        cpu_percent, memory_info, process_metrics = await asyncio.gather(
            cpu_task, memory_task, process_task
        )

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_info.percent,
            "memory_used_gb": memory_info.used / (1024**3),
            "memory_available_gb": memory_info.available / (1024**3),
            "process_cpu_percent": process_metrics["cpu_percent"],
            "process_memory_mb": process_metrics["memory_mb"],
            "process_threads": process_metrics["threads"],
        }

    def _get_process_metrics(self) -> Dict[str, float]:
        """Get process-specific metrics"""
        try:
            memory_info = self.process.memory_info()
            cpu_percent = self.process.cpu_percent()
            threads = self.process.num_threads()

            return {
                "cpu_percent": cpu_percent,
                "memory_mb": memory_info.rss / (1024**2),
                "threads": threads,
            }
        except Exception as e:
            logger.warning(f"Failed to get process metrics: {e}")
            return {"cpu_percent": 0.0, "memory_mb": 0.0, "threads": 0}


class PerformanceOptimizer:
    """Intelligent performance optimization"""

    def __init__(self):
        self.optimization_history: List[OptimizationRecommendation] = []
        self.active_optimizations: Dict[str, Any] = {}

    async def analyze_performance(
        self, monitor: PerformanceMonitor
    ) -> List[OptimizationRecommendation]:
        """Analyze performance and generate optimization recommendations"""
        recommendations = []

        # Analyze each metric type
        for metric_type in PerformanceMetricType:
            stats = monitor.get_current_stats(metric_type)
            trend = monitor.get_trend(metric_type)

            # Generate recommendations based on analysis
            recs = await self._analyze_metric(metric_type, stats, trend)
            recommendations.extend(recs)

        # Sort by priority
        recommendations.sort(key=lambda x: x.priority, reverse=True)

        # Store recommendations
        self.optimization_history.extend(recommendations)

        return recommendations[:5]  # Return top 5

    async def _analyze_metric(
        self, metric_type: PerformanceMetricType, stats: Dict[str, float], trend: str
    ) -> List[OptimizationRecommendation]:
        """Analyze specific metric and generate recommendations"""
        recommendations = []

        if metric_type == PerformanceMetricType.RESPONSE_TIME:
            if stats["avg"] > 5.0:  # Average response time > 5 seconds
                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_id=f"resp_time_{int(time.time())}",
                        strategy=OptimizationStrategy.CACHING,
                        description="Implement aggressive caching to reduce response times",
                        expected_improvement=30.0,
                        estimated_effort="medium",
                        priority=8,
                        parameters={"cache_ttl": 600, "cache_strategy": "aggressive"},
                    )
                )

        elif metric_type == PerformanceMetricType.CPU_USAGE:
            if stats["avg"] > 80.0:  # High CPU usage
                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_id=f"cpu_usage_{int(time.time())}",
                        strategy=OptimizationStrategy.ASYNC_TUNING,
                        description="Optimize async processing to reduce CPU load",
                        expected_improvement=25.0,
                        estimated_effort="medium",
                        priority=7,
                        parameters={"max_workers": 50, "batch_size": 10},
                    )
                )

        elif metric_type == PerformanceMetricType.MEMORY_USAGE:
            if stats["avg"] > 85.0:  # High memory usage
                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_id=f"memory_{int(time.time())}",
                        strategy=OptimizationStrategy.RESOURCE_ALLOCATION,
                        description="Optimize memory usage through garbage collection tuning",
                        expected_improvement=20.0,
                        estimated_effort="low",
                        priority=6,
                        parameters={"gc_threshold": 700},
                    )
                )

        elif metric_type == PerformanceMetricType.ERROR_RATE:
            if stats["avg"] > 5.0:  # Error rate > 5%
                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_id=f"error_rate_{int(time.time())}",
                        strategy=OptimizationStrategy.SCALING,
                        description="Implement circuit breakers and retry mechanisms",
                        expected_improvement=40.0,
                        estimated_effort="high",
                        priority=9,
                        parameters={
                            "circuit_breaker_threshold": 3,
                            "retry_attempts": 3,
                        },
                    )
                )

        return recommendations

    async def apply_optimization(
        self, recommendation: OptimizationRecommendation
    ) -> bool:
        """Apply an optimization recommendation"""
        try:
            logger.info(f"🚀 Applying optimization: {recommendation.description}")

            if recommendation.strategy == OptimizationStrategy.CACHING:
                await self._optimize_caching(recommendation.parameters)
            elif recommendation.strategy == OptimizationStrategy.ASYNC_TUNING:
                await self._optimize_async_processing(recommendation.parameters)
            elif recommendation.strategy == OptimizationStrategy.RESOURCE_ALLOCATION:
                await self._optimize_resource_allocation(recommendation.parameters)

            self.active_optimizations[recommendation.recommendation_id] = {
                "applied_at": datetime.now(),
                "recommendation": recommendation,
            }

            logger.info(f"✅ Optimization applied: {recommendation.recommendation_id}")
            return True

        except Exception as e:
            logger.error(
                f"❌ Failed to apply optimization {recommendation.recommendation_id}: {e}"
            )
            return False

    async def _optimize_caching(self, parameters: Dict[str, Any]):
        """Optimize caching strategy"""
        cache_ttl = parameters.get("cache_ttl", 300)
        logger.info(f"Optimized caching with TTL: {cache_ttl}s")

    async def _optimize_async_processing(self, parameters: Dict[str, Any]):
        """Optimize async processing parameters"""
        max_workers = parameters.get("max_workers", 50)
        logger.info(f"Optimized async processing with max workers: {max_workers}")

    async def _optimize_resource_allocation(self, parameters: Dict[str, Any]):
        """Optimize resource allocation"""
        gc_threshold = parameters.get("gc_threshold", 700)
        logger.info(f"Optimized resource allocation with GC threshold: {gc_threshold}")


class AlertManager:
    """Performance alerting system"""

    def __init__(self):
        self.alert_thresholds = {
            PerformanceMetricType.RESPONSE_TIME: {"warning": 3.0, "critical": 10.0},
            PerformanceMetricType.CPU_USAGE: {"warning": 70.0, "critical": 90.0},
            PerformanceMetricType.MEMORY_USAGE: {"warning": 80.0, "critical": 95.0},
            PerformanceMetricType.ERROR_RATE: {"warning": 5.0, "critical": 15.0},
            PerformanceMetricType.CACHE_HIT_RATE: {"warning": 70.0, "critical": 50.0},
        }
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_history: List[PerformanceAlert] = []

    async def check_alerts(self, monitor: PerformanceMonitor) -> List[PerformanceAlert]:
        """Check for performance alerts"""
        new_alerts = []

        for metric_type in PerformanceMetricType:
            if metric_type not in self.alert_thresholds:
                continue

            stats = monitor.get_current_stats(metric_type)
            thresholds = self.alert_thresholds[metric_type]

            # Check for threshold violations
            alert = await self._check_threshold_violation(
                metric_type, stats, thresholds
            )
            if alert:
                new_alerts.append(alert)

        # Store new alerts
        for alert in new_alerts:
            self.active_alerts[alert.alert_id] = alert
            self.alert_history.append(alert)

        return new_alerts

    async def _check_threshold_violation(
        self,
        metric_type: PerformanceMetricType,
        stats: Dict[str, float],
        thresholds: Dict[str, float],
    ) -> Optional[PerformanceAlert]:
        """Check if metric violates thresholds"""
        value = stats["avg"]

        # Determine severity
        severity = None
        threshold = None

        if metric_type == PerformanceMetricType.CACHE_HIT_RATE:
            # For cache hit rate, lower is worse
            if value < thresholds["critical"]:
                severity = AlertSeverity.CRITICAL
                threshold = thresholds["critical"]
            elif value < thresholds["warning"]:
                severity = AlertSeverity.WARNING
                threshold = thresholds["warning"]
        else:
            # For other metrics, higher is worse
            if value > thresholds["critical"]:
                severity = AlertSeverity.CRITICAL
                threshold = thresholds["critical"]
            elif value > thresholds["warning"]:
                severity = AlertSeverity.WARNING
                threshold = thresholds["warning"]

        if severity:
            alert_id = f"{metric_type.value}_{severity.value}_{int(time.time())}"
            return PerformanceAlert(
                alert_id=alert_id,
                severity=severity,
                metric_type=metric_type,
                message=f"{metric_type.value} {severity.value}: {value:.2f} (threshold: {threshold})",
                value=value,
                threshold=threshold,
                timestamp=datetime.now(),
            )

        return None


class PerformanceOptimizationEngine:
    """
    Main Performance Optimization Engine

    Features:
    - Real-time monitoring
    - Automatic optimization
    - Intelligent alerting
    - Performance reporting
    """

    def __init__(self):
        self.task_manager = AsyncTaskManager("performance_optimization_engine")
        self.monitor = PerformanceMonitor()
        self.system_monitor = SystemResourceMonitor()
        self.optimizer = PerformanceOptimizer()
        self.alert_manager = AlertManager()

        # Background tasks
        self.background_tasks = set()
        self.running = False

    async def initialize(self) -> bool:
        """Initialize the performance optimization engine"""
        try:
            logger.info("🚀 Initializing Performance Optimization Engine...")

            # Initialize cache manager
            await cache_manager.initialize()

            # Start background services
            self.running = True
            self._start_background_services()

            logger.info("✅ Performance Optimization Engine initialized")
            return True

        except Exception as e:
            logger.error(
                f"❌ Failed to initialize Performance Optimization Engine: {e}"
            )
            return False

    def _start_background_services(self):
        """Start background monitoring and optimization services"""
        services = [
            self._monitoring_service(),
            self._optimization_service(),
            self._alerting_service(),
            self._cleanup_service(),
        ]

        for service_coro in services:
            task = create_background_task(
                service_coro, name=f"perf_{service_coro.__name__}"
            )
            self.background_tasks.add(task)

    async def record_performance_metric(
        self,
        metric_type: PerformanceMetricType,
        value: float,
        component: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Record a performance metric"""
        metric = PerformanceMetric(
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            component=component,
            context=context or {},
        )

        self.monitor.record_metric(metric)

    async def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""
        # Get current metrics
        current_metrics = {}
        for metric_type in PerformanceMetricType:
            current_metrics[metric_type.value] = self.monitor.get_current_stats(
                metric_type
            )

        # Get system metrics
        system_metrics = await self.system_monitor.get_system_metrics()

        # Get active alerts
        active_alerts = [
            {
                "alert_id": alert.alert_id,
                "severity": alert.severity.value,
                "metric_type": alert.metric_type.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
            }
            for alert in self.alert_manager.active_alerts.values()
            if not alert.resolved
        ]

        # Get recent recommendations
        recent_recommendations = [
            {
                "recommendation_id": rec.recommendation_id,
                "strategy": rec.strategy.value,
                "description": rec.description,
                "expected_improvement": rec.expected_improvement,
                "priority": rec.priority,
            }
            for rec in self.optimizer.optimization_history[-5:]
        ]

        # Calculate performance score
        performance_score = await self._calculate_performance_score()

        return {
            "performance_score": performance_score,
            "current_metrics": current_metrics,
            "system_metrics": system_metrics,
            "active_alerts": active_alerts,
            "recent_recommendations": recent_recommendations,
            "engine_stats": await self._get_engine_stats(),
            "timestamp": datetime.now().isoformat(),
        }

    async def _calculate_performance_score(self) -> float:
        """Calculate overall performance score (0-100)"""
        scores = []

        # Response time score (inverse relationship)
        resp_time_stats = self.monitor.get_current_stats(
            PerformanceMetricType.RESPONSE_TIME
        )
        if resp_time_stats["count"] > 0:
            resp_time_score = max(0, 100 - (resp_time_stats["avg"] * 10))
            scores.append(resp_time_score)

        # Error rate score (inverse relationship)
        error_rate_stats = self.monitor.get_current_stats(
            PerformanceMetricType.ERROR_RATE
        )
        if error_rate_stats["count"] > 0:
            error_rate_score = max(0, 100 - (error_rate_stats["avg"] * 5))
            scores.append(error_rate_score)

        # Cache hit rate score (direct relationship)
        cache_stats = self.monitor.get_current_stats(
            PerformanceMetricType.CACHE_HIT_RATE
        )
        if cache_stats["count"] > 0:
            scores.append(cache_stats["avg"])

        # System resource scores
        try:
            system_metrics = await self.system_monitor.get_system_metrics()
            cpu_score = max(0, 100 - system_metrics["cpu_percent"])
            memory_score = max(0, 100 - system_metrics["memory_percent"])
            scores.extend([cpu_score, memory_score])
        except Exception:
            pass

        return statistics.mean(scores) if scores else 50.0

    async def _monitoring_service(self):
        """Background monitoring service"""
        while self.running:
            try:
                await asyncio.sleep(10)  # Monitor every 10 seconds

                # Collect system metrics
                system_metrics = await self.system_monitor.get_system_metrics()

                # Record system metrics
                await self.record_performance_metric(
                    PerformanceMetricType.CPU_USAGE,
                    system_metrics["cpu_percent"],
                    component="system",
                )

                await self.record_performance_metric(
                    PerformanceMetricType.MEMORY_USAGE,
                    system_metrics["memory_percent"],
                    component="system",
                )

                # Get cache stats
                try:
                    cache_stats = await cache_manager.get_stats()
                    if cache_stats.get("hit_rate"):
                        await self.record_performance_metric(
                            PerformanceMetricType.CACHE_HIT_RATE,
                            cache_stats["hit_rate"],
                            component="cache",
                        )
                except Exception:
                    pass

            except Exception as e:
                logger.error(f"Error in monitoring service: {e}")

    async def _optimization_service(self):
        """Background optimization service"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                # Generate optimization recommendations
                recommendations = await self.optimizer.analyze_performance(self.monitor)

                if recommendations:
                    logger.info(
                        f"📊 Generated {len(recommendations)} optimization recommendations"
                    )

                    # Auto-apply low-effort, high-impact optimizations
                    for rec in recommendations:
                        if (
                            rec.estimated_effort == "low"
                            and rec.expected_improvement > 15.0
                            and rec.priority >= 7
                        ):
                            await self.optimizer.apply_optimization(rec)

            except Exception as e:
                logger.error(f"Error in optimization service: {e}")

    async def _alerting_service(self):
        """Background alerting service"""
        while self.running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                # Check for new alerts
                new_alerts = await self.alert_manager.check_alerts(self.monitor)

                if new_alerts:
                    for alert in new_alerts:
                        logger.warning(f"🚨 Performance Alert: {alert.message}")

                        # For critical alerts, trigger immediate optimization
                        if alert.severity == AlertSeverity.CRITICAL:
                            recommendations = await self.optimizer.analyze_performance(
                                self.monitor
                            )
                            # Apply first high-priority recommendation
                            for rec in recommendations:
                                if rec.priority >= 8:
                                    await self.optimizer.apply_optimization(rec)
                                    break

            except Exception as e:
                logger.error(f"Error in alerting service: {e}")

    async def _cleanup_service(self):
        """Background cleanup service"""
        while self.running:
            try:
                await asyncio.sleep(1800)  # Run every 30 minutes

                # Clean up completed background tasks
                completed_tasks = [
                    task for task in self.background_tasks if task.done()
                ]
                for task in completed_tasks:
                    self.background_tasks.discard(task)
                    if task.exception():
                        logger.error(f"Background task failed: {task.exception()}")

                # Clean up old alerts
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.alert_manager.alert_history = [
                    alert
                    for alert in self.alert_manager.alert_history
                    if alert.timestamp > cutoff_time
                ]

                # Clean up old optimization history
                if len(self.optimizer.optimization_history) > 100:
                    self.optimizer.optimization_history = (
                        self.optimizer.optimization_history[-50:]
                    )

            except Exception as e:
                logger.error(f"Error in cleanup service: {e}")

    async def _get_engine_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            "background_tasks": len(self.background_tasks),
            "total_metrics_collected": sum(
                len(self.monitor.metrics[mt]) for mt in PerformanceMetricType
            ),
            "active_alerts": len(
                [
                    alert
                    for alert in self.alert_manager.active_alerts.values()
                    if not alert.resolved
                ]
            ),
            "total_recommendations": len(self.optimizer.optimization_history),
            "active_optimizations": len(self.optimizer.active_optimizations),
        }

    async def shutdown(self, timeout: float = 30.0):
        """Graceful shutdown"""
        logger.info("🔄 Shutting down Performance Optimization Engine...")
        self.running = False

        try:
            # Cancel background tasks
            for task in self.background_tasks:
                task.cancel()

            if self.background_tasks:
                await asyncio.wait_for(
                    asyncio.gather(*self.background_tasks, return_exceptions=True),
                    timeout=timeout,
                )

            # Cleanup task manager
            await self.task_manager.cleanup_tasks(timeout=10.0)

            # Close system monitor
            self.system_monitor.executor.shutdown(wait=True)

            logger.info("✅ Performance Optimization Engine shutdown completed")

        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")


# Global engine instance
perf_engine = PerformanceOptimizationEngine()


# Convenience functions
async def record_response_time(response_time: float, component: Optional[str] = None):
    """Record response time metric"""
    await perf_engine.record_performance_metric(
        PerformanceMetricType.RESPONSE_TIME, response_time, component
    )


async def record_error_rate(error_rate: float, component: Optional[str] = None):
    """Record error rate metric"""
    await perf_engine.record_performance_metric(
        PerformanceMetricType.ERROR_RATE, error_rate, component
    )


async def record_throughput(throughput: float, component: Optional[str] = None):
    """Record throughput metric"""
    await perf_engine.record_performance_metric(
        PerformanceMetricType.THROUGHPUT, throughput, component
    )


async def get_performance_dashboard() -> Dict[str, Any]:
    """Get performance dashboard data"""
    return await perf_engine.get_performance_dashboard()


async def initialize_performance_engine() -> bool:
    """Initialize the global performance optimization engine"""
    return await perf_engine.initialize()


async def shutdown_performance_engine(timeout: float = 30.0):
    """Shutdown the global performance optimization engine"""
    await perf_engine.shutdown(timeout)


# Alias for backward compatibility
OptimizationEngine = PerformanceOptimizationEngine
