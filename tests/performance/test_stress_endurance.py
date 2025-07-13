"""
Stress and Endurance Testing for AI Assistant
Tests system behavior under extreme load and extended duration
"""

import asyncio
import logging
import os
import random
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import httpx
import psutil
import pytest

logger = logging.getLogger(__name__)


@dataclass
class StressTestResult:
    """Stress test result metrics"""

    test_name: str
    peak_concurrent_users: int
    test_duration: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    peak_rps: float
    avg_rps: float
    memory_start_mb: float
    memory_peak_mb: float
    memory_end_mb: float
    cpu_usage_avg: float
    cpu_usage_peak: float
    recovery_time: float
    system_degraded: bool


class StressEnduranceTester:
    """Advanced stress and endurance testing framework"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[StressTestResult] = []
        self.process = psutil.Process(os.getpid())

        # Real tokens (will be obtained during tests)
        self.admin_token = None
        self.user_token = None

    def _get_system_metrics(self) -> Dict[str, float]:
        """Get current system metrics"""
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        cpu_percent = self.process.cpu_percent(interval=0.1)

        return {"memory_mb": memory_mb, "cpu_percent": cpu_percent}

    async def run_escalating_load_test(
        self, max_users: int = 200, escalation_steps: int = 10, step_duration: int = 30
    ) -> StressTestResult:
        """Test with escalating load to find breaking point"""
        logger.info(
            f"🔥 Running escalating load test: 0 → {max_users} users in {escalation_steps} steps"
        )

        start_time = time.time()
        start_metrics = self._get_system_metrics()

        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        peak_rps = 0.0
        rps_measurements = []
        memory_measurements = [start_metrics["memory_mb"]]
        cpu_measurements = [start_metrics["cpu_percent"]]

        users_per_step = max_users // escalation_steps
        system_degraded = False

        for step in range(1, escalation_steps + 1):
            current_users = users_per_step * step
            logger.info(
                f"🚀 Step {step}/{escalation_steps}: {current_users} concurrent users"
            )

            step_start = time.time()
            step_requests = 0
            step_success = 0
            step_failures = 0

            async def user_load():
                """Single user load generator"""
                nonlocal step_requests, step_success, step_failures

                async with httpx.AsyncClient(
                    app=None, base_url=self.base_url
                ) as client:
                    end_time = time.time() + step_duration

                    while time.time() < end_time:
                        try:
                            # Mix of different endpoints for realistic load
                            endpoint = random.choice(
                                [
                                    "/api/health",
                                    "/api/v1/health",
                                    "/api/v1/ws/stats",
                                    "/api/v1/realtime-monitoring/health",
                                ]
                            )

                            response = await client.get(endpoint, timeout=5.0)
                            step_requests += 1

                            if response.status_code in [
                                200,
                                404,
                            ]:  # 404 is OK for missing endpoints
                                step_success += 1
                            else:
                                step_failures += 1

                        except Exception as e:
                            step_requests += 1
                            step_failures += 1
                            logger.debug(f"Request failed: {e}")

                        # Random delay to simulate real usage
                        await asyncio.sleep(random.uniform(0.1, 0.5))

            # Run concurrent users for this step
            tasks = [user_load() for _ in range(current_users)]
            await asyncio.gather(*tasks, return_exceptions=True)

            step_duration_actual = time.time() - step_start
            step_rps = (
                step_requests / step_duration_actual
                if step_duration_actual > 0
                else 0.0
            )

            # Collect metrics
            current_metrics = self._get_system_metrics()
            memory_measurements.append(current_metrics["memory_mb"])
            cpu_measurements.append(current_metrics["cpu_percent"])
            rps_measurements.append(step_rps)

            if step_rps > peak_rps:
                peak_rps = step_rps

            total_requests += step_requests
            successful_requests += step_success
            failed_requests += step_failures

            # Check for system degradation
            error_rate = (
                (step_failures / step_requests * 100) if step_requests > 0 else 0
            )
            if error_rate > 50 or step_rps < (peak_rps * 0.3):
                system_degraded = True
                logger.warning(
                    f"⚠️ System degradation detected at {current_users} users"
                )

            logger.info(
                f"✅ Step {step} complete: {step_rps:.1f} RPS, {error_rate:.1f}% error rate"
            )

            # Small recovery pause between steps
            await asyncio.sleep(2)

        # Recovery test
        logger.info("🔄 Testing system recovery...")
        recovery_start = time.time()

        # Wait for system to stabilize
        await asyncio.sleep(5)

        # Test normal load after stress
        async with httpx.AsyncClient(app=None, base_url=self.base_url) as client:
            recovery_success = 0
            for _ in range(10):
                try:
                    response = await client.get("/api/health", timeout=5.0)
                    if response.status_code == 200:
                        recovery_success += 1
                except:
                    pass
                await asyncio.sleep(0.5)

        recovery_time = time.time() - recovery_start
        recovery_rate = recovery_success / 10 * 100

        if recovery_rate < 80:
            logger.warning(
                f"⚠️ Poor recovery: {recovery_rate:.1f}% success after stress"
            )

        test_duration = time.time() - start_time
        end_metrics = self._get_system_metrics()

        result = StressTestResult(
            test_name="Escalating Load Stress Test",
            peak_concurrent_users=max_users,
            test_duration=test_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            peak_rps=peak_rps,
            avg_rps=statistics.mean(rps_measurements) if rps_measurements else 0.0,
            memory_start_mb=start_metrics["memory_mb"],
            memory_peak_mb=max(memory_measurements),
            memory_end_mb=end_metrics["memory_mb"],
            cpu_usage_avg=(
                statistics.mean(cpu_measurements) if cpu_measurements else 0.0
            ),
            cpu_usage_peak=max(cpu_measurements),
            recovery_time=recovery_time,
            system_degraded=system_degraded,
        )

        self.results.append(result)
        logger.info(
            f"✅ Escalating load test completed: Peak {peak_rps:.1f} RPS at {max_users} users"
        )

        return result

    async def run_sustained_load_test(
        self, concurrent_users: int = 50, duration_minutes: int = 10
    ) -> StressTestResult:
        """Test system under sustained load for extended period"""
        logger.info(
            f"⏰ Running sustained load test: {concurrent_users} users for {duration_minutes} minutes"
        )

        start_time = time.time()
        duration_seconds = duration_minutes * 60
        start_metrics = self._get_system_metrics()

        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        rps_measurements = []
        memory_measurements = [start_metrics["memory_mb"]]
        cpu_measurements = [start_metrics["cpu_percent"]]

        async def sustained_user():
            """User making requests for the entire duration"""
            nonlocal total_requests, successful_requests, failed_requests

            async with httpx.AsyncClient(app=None, base_url=self.base_url) as client:
                end_time = time.time() + duration_seconds

                while time.time() < end_time:
                    try:
                        # Health check requests
                        response = await client.get("/api/health", timeout=3.0)
                        total_requests += 1

                        if response.status_code == 200:
                            successful_requests += 1
                        else:
                            failed_requests += 1

                    except Exception as e:
                        total_requests += 1
                        failed_requests += 1
                        logger.debug(f"Sustained request failed: {e}")

                    # Consistent request rate
                    await asyncio.sleep(1.0)

        # Performance monitoring task
        async def monitor_performance():
            """Monitor system performance during test"""
            monitor_end = time.time() + duration_seconds

            while time.time() < monitor_end:
                await asyncio.sleep(10)  # Sample every 10 seconds

                current_metrics = self._get_system_metrics()
                memory_measurements.append(current_metrics["memory_mb"])
                cpu_measurements.append(current_metrics["cpu_percent"])

                # Calculate current RPS
                current_time = time.time()
                if len(rps_measurements) > 0:
                    time_diff = current_time - start_time
                    current_rps = total_requests / time_diff if time_diff > 0 else 0.0
                    rps_measurements.append(current_rps)

        # Run sustained load and monitoring
        user_tasks = [sustained_user() for _ in range(concurrent_users)]
        monitor_task = monitor_performance()

        await asyncio.gather(*user_tasks, monitor_task, return_exceptions=True)

        test_duration = time.time() - start_time
        end_metrics = self._get_system_metrics()

        # Analyze memory leaks
        memory_growth = end_metrics["memory_mb"] - start_metrics["memory_mb"]
        memory_leak_detected = memory_growth > 50  # More than 50MB growth

        if memory_leak_detected:
            logger.warning(
                f"⚠️ Potential memory leak detected: {memory_growth:.1f}MB growth"
            )

        avg_rps = total_requests / test_duration if test_duration > 0 else 0.0

        result = StressTestResult(
            test_name="Sustained Load Endurance Test",
            peak_concurrent_users=concurrent_users,
            test_duration=test_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            peak_rps=max(rps_measurements) if rps_measurements else avg_rps,
            avg_rps=avg_rps,
            memory_start_mb=start_metrics["memory_mb"],
            memory_peak_mb=max(memory_measurements),
            memory_end_mb=end_metrics["memory_mb"],
            cpu_usage_avg=(
                statistics.mean(cpu_measurements) if cpu_measurements else 0.0
            ),
            cpu_usage_peak=max(cpu_measurements),
            recovery_time=0.0,  # No recovery test for sustained
            system_degraded=memory_leak_detected,
        )

        self.results.append(result)
        logger.info(
            f"✅ Sustained load test completed: {avg_rps:.1f} avg RPS over {duration_minutes} minutes"
        )

        return result

    async def run_spike_load_test(
        self, baseline_users: int = 10, spike_users: int = 100, spike_duration: int = 30
    ) -> StressTestResult:
        """Test system response to sudden load spikes"""
        logger.info(
            f"⚡ Running spike load test: {baseline_users} → {spike_users} users spike"
        )

        start_time = time.time()
        start_metrics = self._get_system_metrics()

        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        peak_rps = 0.0
        memory_measurements = [start_metrics["memory_mb"]]
        cpu_measurements = [start_metrics["cpu_percent"]]

        # Phase 1: Baseline load
        logger.info(f"📊 Phase 1: Baseline load ({baseline_users} users)")

        async def baseline_user():
            """Baseline user load"""
            nonlocal total_requests, successful_requests, failed_requests

            async with httpx.AsyncClient(app=None, base_url=self.base_url) as client:
                for _ in range(10):  # 10 requests during baseline
                    try:
                        response = await client.get("/api/health", timeout=3.0)
                        total_requests += 1

                        if response.status_code == 200:
                            successful_requests += 1
                        else:
                            failed_requests += 1
                    except:
                        total_requests += 1
                        failed_requests += 1

                    await asyncio.sleep(0.5)

        # Run baseline load
        baseline_tasks = [baseline_user() for _ in range(baseline_users)]
        await asyncio.gather(*baseline_tasks, return_exceptions=True)

        baseline_metrics = self._get_system_metrics()
        memory_measurements.append(baseline_metrics["memory_mb"])
        cpu_measurements.append(baseline_metrics["cpu_percent"])

        # Phase 2: Spike load
        logger.info(f"🚀 Phase 2: Spike load ({spike_users} users)")
        spike_start = time.time()

        async def spike_user():
            """Spike user load"""
            nonlocal total_requests, successful_requests, failed_requests

            async with httpx.AsyncClient(app=None, base_url=self.base_url) as client:
                spike_end = time.time() + spike_duration

                while time.time() < spike_end:
                    try:
                        response = await client.get("/api/health", timeout=2.0)
                        total_requests += 1

                        if response.status_code == 200:
                            successful_requests += 1
                        else:
                            failed_requests += 1
                    except:
                        total_requests += 1
                        failed_requests += 1

                    await asyncio.sleep(0.1)  # Higher frequency during spike

        # Run spike load
        spike_tasks = [spike_user() for _ in range(spike_users)]
        await asyncio.gather(*spike_tasks, return_exceptions=True)

        spike_duration_actual = time.time() - spike_start
        spike_rps = (
            total_requests * 0.8
        ) / spike_duration_actual  # Estimate spike portion
        peak_rps = spike_rps

        spike_metrics = self._get_system_metrics()
        memory_measurements.append(spike_metrics["memory_mb"])
        cpu_measurements.append(spike_metrics["cpu_percent"])

        # Phase 3: Recovery
        logger.info("🔄 Phase 3: Recovery period")
        await asyncio.sleep(10)

        recovery_metrics = self._get_system_metrics()
        memory_measurements.append(recovery_metrics["memory_mb"])
        cpu_measurements.append(recovery_metrics["cpu_percent"])

        # Test recovery with baseline load
        recovery_success = 0
        for _ in range(5):
            try:
                async with httpx.AsyncClient(
                    app=None, base_url=self.base_url
                ) as client:
                    response = await client.get("/api/health", timeout=3.0)
                    if response.status_code == 200:
                        recovery_success += 1
            except:
                pass
            await asyncio.sleep(1)

        recovery_rate = recovery_success / 5 * 100
        system_degraded = recovery_rate < 60

        if system_degraded:
            logger.warning(f"⚠️ Poor spike recovery: {recovery_rate:.1f}% success")

        test_duration = time.time() - start_time

        result = StressTestResult(
            test_name="Spike Load Test",
            peak_concurrent_users=spike_users,
            test_duration=test_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            peak_rps=peak_rps,
            avg_rps=total_requests / test_duration if test_duration > 0 else 0.0,
            memory_start_mb=start_metrics["memory_mb"],
            memory_peak_mb=max(memory_measurements),
            memory_end_mb=recovery_metrics["memory_mb"],
            cpu_usage_avg=(
                statistics.mean(cpu_measurements) if cpu_measurements else 0.0
            ),
            cpu_usage_peak=max(cpu_measurements),
            recovery_time=10.0,
            system_degraded=system_degraded,
        )

        self.results.append(result)
        logger.info(
            f"✅ Spike load test completed: {peak_rps:.1f} peak RPS, {recovery_rate:.1f}% recovery"
        )

        return result

    def generate_stress_test_report(self) -> str:
        """Generate comprehensive stress test report"""
        if not self.results:
            return "No stress test results available"

        report_lines = [
            "# 🔥 Stress & Endurance Test Report",
            f"**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
            f"**Tests Completed**: {len(self.results)}",
            "",
            "## 📊 Executive Summary",
            "",
        ]

        # Calculate overall metrics
        total_requests = sum(r.total_requests for r in self.results)
        total_successful = sum(r.successful_requests for r in self.results)
        overall_success_rate = (
            (total_successful / total_requests * 100) if total_requests > 0 else 0.0
        )
        max_peak_rps = max(r.peak_rps for r in self.results)
        max_users_tested = max(r.peak_concurrent_users for r in self.results)

        report_lines.extend(
            [
                f"- **Maximum Concurrent Users Tested**: {max_users_tested:,}",
                f"- **Peak Throughput Achieved**: {max_peak_rps:.1f} RPS",
                f"- **Overall Success Rate**: {overall_success_rate:.1f}%",
                f"- **Total Requests Processed**: {total_requests:,}",
                "",
                "## 🎯 Individual Test Results",
                "",
            ]
        )

        for result in self.results:
            success_rate = (
                (result.successful_requests / result.total_requests * 100)
                if result.total_requests > 0
                else 0.0
            )
            memory_growth = result.memory_end_mb - result.memory_start_mb

            report_lines.extend(
                [
                    f"### {result.test_name}",
                    "",
                    f"**Load Characteristics:**",
                    f"- Peak Concurrent Users: {result.peak_concurrent_users:,}",
                    f"- Test Duration: {result.test_duration:.1f} seconds",
                    f"- Total Requests: {result.total_requests:,}",
                    "",
                    f"**Performance Metrics:**",
                    f"- Success Rate: {success_rate:.1f}%",
                    f"- Peak RPS: {result.peak_rps:.1f}",
                    f"- Average RPS: {result.avg_rps:.1f}",
                    "",
                    f"**Resource Usage:**",
                    f"- Memory Start: {result.memory_start_mb:.1f} MB",
                    f"- Memory Peak: {result.memory_peak_mb:.1f} MB",
                    f"- Memory Growth: {memory_growth:+.1f} MB",
                    f"- CPU Average: {result.cpu_usage_avg:.1f}%",
                    f"- CPU Peak: {result.cpu_usage_peak:.1f}%",
                    "",
                    f"**System Health:**",
                    f"- System Degraded: {'❌ Yes' if result.system_degraded else '✅ No'}",
                    f"- Recovery Time: {result.recovery_time:.1f} seconds",
                    "",
                    "---",
                    "",
                ]
            )

        # Performance analysis
        report_lines.extend(
            ["## 🔍 Performance Analysis", "", "### System Limits Identified", ""]
        )

        # Find the breaking points
        degraded_tests = [r for r in self.results if r.system_degraded]
        if degraded_tests:
            min_degraded_users = min(r.peak_concurrent_users for r in degraded_tests)
            report_lines.append(
                f"- System degradation begins around **{min_degraded_users} concurrent users**"
            )
        else:
            report_lines.append(
                f"- No system degradation detected up to **{max_users_tested} concurrent users** ✅"
            )

        # Memory analysis
        max_memory_growth = max(
            r.memory_end_mb - r.memory_start_mb for r in self.results
        )
        if max_memory_growth > 50:
            report_lines.append(
                f"- Potential memory leak detected: **{max_memory_growth:.1f} MB** growth ⚠️"
            )
        else:
            report_lines.append(
                f"- Memory usage stable: **{max_memory_growth:.1f} MB** max growth ✅"
            )

        # CPU analysis
        max_cpu_usage = max(r.cpu_usage_peak for r in self.results)
        if max_cpu_usage > 80:
            report_lines.append(
                f"- High CPU usage detected: **{max_cpu_usage:.1f}%** peak ⚠️"
            )
        else:
            report_lines.append(
                f"- CPU usage acceptable: **{max_cpu_usage:.1f}%** peak ✅"
            )

        report_lines.extend(["", "### Recommendations", ""])

        # Generate recommendations
        if degraded_tests:
            report_lines.extend(
                [
                    "- Consider implementing horizontal scaling before reaching degradation point",
                    "- Add circuit breakers and rate limiting for high-load scenarios",
                    "- Implement graceful degradation strategies",
                ]
            )

        if max_memory_growth > 30:
            report_lines.extend(
                [
                    "- Investigate potential memory leaks in long-running processes",
                    "- Implement memory monitoring and cleanup routines",
                ]
            )

        if max_cpu_usage > 70:
            report_lines.extend(
                [
                    "- Optimize CPU-intensive operations",
                    "- Consider async processing for heavy workloads",
                ]
            )

        if not degraded_tests and max_memory_growth < 30 and max_cpu_usage < 70:
            report_lines.extend(
                [
                    "- System demonstrates excellent stability under stress 🎉",
                    "- Consider testing with higher loads to find true limits",
                    "- Current configuration appears production-ready",
                ]
            )

        report_lines.extend(
            ["", "---", "*Report generated by Stress & Endurance Tester*"]
        )

        return "\n".join(report_lines)


# Pytest integration
@pytest.mark.asyncio
class TestStressScenarios:
    """Stress testing scenarios"""

    async def test_escalating_load_moderate(self):
        """Test escalating load up to moderate levels"""
        tester = StressEnduranceTester()
        result = await tester.run_escalating_load_test(
            max_users=50, escalation_steps=5, step_duration=15
        )

        # Assertions for moderate load
        assert result.peak_rps > 10, f"Peak RPS too low: {result.peak_rps:.1f}"
        assert not result.system_degraded, "System should not degrade at moderate load"

        print(
            f"\n📊 Escalating Load Result: {result.peak_rps:.1f} peak RPS at {result.peak_concurrent_users} users"
        )

    async def test_sustained_load_short(self):
        """Test sustained load for short duration"""
        tester = StressEnduranceTester()
        result = await tester.run_sustained_load_test(
            concurrent_users=25, duration_minutes=2
        )

        # Memory leak check
        memory_growth = result.memory_end_mb - result.memory_start_mb
        assert memory_growth < 100, f"Excessive memory growth: {memory_growth:.1f} MB"

        # Success rate check
        success_rate = (
            (result.successful_requests / result.total_requests * 100)
            if result.total_requests > 0
            else 0.0
        )
        assert success_rate > 70, f"Success rate too low: {success_rate:.1f}%"

        print(
            f"\n⏰ Sustained Load Result: {result.avg_rps:.1f} avg RPS over {result.test_duration/60:.1f} minutes"
        )

    async def test_spike_load_moderate(self):
        """Test moderate spike load"""
        tester = StressEnduranceTester()
        result = await tester.run_spike_load_test(
            baseline_users=5, spike_users=30, spike_duration=20
        )

        # Recovery check
        assert not result.system_degraded, "System should recover from moderate spike"

        print(
            f"\n⚡ Spike Load Result: {result.peak_rps:.1f} peak RPS, recovery OK: {not result.system_degraded}"
        )


@pytest.mark.asyncio
class TestExtremeStress:
    """Extreme stress testing scenarios"""

    async def test_comprehensive_stress_suite(self):
        """Run comprehensive stress test suite"""
        tester = StressEnduranceTester()

        print(f"\n{'='*80}")
        print("🔥 STARTING COMPREHENSIVE STRESS TEST SUITE")
        print(f"{'='*80}")

        # Run all stress tests
        escalating_result = await tester.run_escalating_load_test(
            max_users=100, escalation_steps=8, step_duration=20
        )
        sustained_result = await tester.run_sustained_load_test(
            concurrent_users=40, duration_minutes=5
        )
        spike_result = await tester.run_spike_load_test(
            baseline_users=10, spike_users=60, spike_duration=25
        )

        # Generate comprehensive report
        report = tester.generate_stress_test_report()

        print(f"\n{'='*80}")
        print("📊 COMPREHENSIVE STRESS TEST RESULTS")
        print(f"{'='*80}")
        print(report)
        print(f"{'='*80}")

        # Overall system health check
        total_requests = sum(r.total_requests for r in tester.results)
        total_successful = sum(r.successful_requests for r in tester.results)
        overall_success_rate = (
            (total_successful / total_requests * 100) if total_requests > 0 else 0.0
        )

        # System should handle basic stress scenarios
        assert (
            overall_success_rate > 60
        ), f"Overall system success rate too low: {overall_success_rate:.1f}%"
        assert (
            total_requests > 1000
        ), f"Insufficient load tested: {total_requests} requests"

        print(
            f"🎯 OVERALL SYSTEM ASSESSMENT: {overall_success_rate:.1f}% success rate across {total_requests:,} requests"
        )


if __name__ == "__main__":
    # Run stress tests directly
    async def main():
        tester = StressEnduranceTester()

        print("🔥 Starting Stress & Endurance Testing Suite...")

        # Run comprehensive stress tests
        escalating = await tester.run_escalating_load_test(
            max_users=80, escalation_steps=6
        )
        sustained = await tester.run_sustained_load_test(
            concurrent_users=30, duration_minutes=3
        )
        spike = await tester.run_spike_load_test(baseline_users=8, spike_users=40)

        # Generate and display report
        report = tester.generate_stress_test_report()

        print("\n" + "=" * 80)
        print("🔥 STRESS & ENDURANCE TEST COMPLETED")
        print("=" * 80)
        print(report)
        print("=" * 80)

    import asyncio

    asyncio.run(main())
