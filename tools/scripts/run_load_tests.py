#!/usr/bin/env python3
"""
Load Test Runner for AI Assistant
Orchestrates comprehensive load testing scenarios
"""
import os
import sys
import subprocess
import asyncio
import yaml
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('load_test_results.log')
    ]
)
logger = logging.getLogger(__name__)

class LoadTestRunner:
    """Main load test runner orchestrator"""
    
    def __init__(self, config_path: str = None):
        self.project_root = Path(__file__).parent.parent
        self.config_path = config_path or self.project_root / "tests" / "performance" / "load_test_config.yaml"
        self.results_dir = self.project_root / "reports" / "load_tests"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Test execution tracking
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    def _load_config(self) -> dict:
        """Load load test configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            return self._get_default_config()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Default configuration if file not found"""
        return {
            "test_profiles": {
                "development": {
                    "health_check": {"concurrent_users": 10, "requests_per_user": 5},
                    "authentication": {"concurrent_users": 5, "requests_per_user": 3},
                    "websocket": {"concurrent_connections": 5, "messages_per_connection": 3},
                    "monitoring": {"concurrent_users": 3, "requests_per_user": 5},
                    "optimization": {"concurrent_users": 3, "requests_per_user": 3}
                }
            },
            "execution": {
                "base_url": "http://localhost:8000",
                "test_environment": "development"
            }
        }
    
    async def run_core_functionality_tests(self, profile: str = "development") -> dict:
        """Run core functionality load tests"""
        logger.info(f"🚀 Starting core functionality load tests with profile: {profile}")
        
        # Import test modules
        sys.path.append(str(self.project_root / "tests" / "performance"))
        
        try:
            from test_core_functionality_load import CoreFunctionalityLoadTester
            
            tester = CoreFunctionalityLoadTester()
            results = await tester.run_comprehensive_load_test()
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = self.results_dir / f"core_functionality_results_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"✅ Core functionality tests completed. Results saved to: {results_file}")
            return results
            
        except ImportError as e:
            logger.error(f"Failed to import test module: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error running core functionality tests: {e}")
            return {"error": str(e)}
    
    async def run_stress_tests(self, scenario: str = "light") -> dict:
        """Run stress and endurance tests"""
        logger.info(f"🔥 Starting stress tests with scenario: {scenario}")
        
        try:
            from test_stress_endurance import StressEnduranceTester
            
            tester = StressEnduranceTester()
            
            # Run different stress scenarios based on configuration
            if scenario == "light":
                escalating_result = await tester.run_escalating_load_test(max_users=50, escalation_steps=5, step_duration=20)
                sustained_result = await tester.run_sustained_load_test(concurrent_users=30, duration_minutes=2)
                spike_result = await tester.run_spike_load_test(baseline_users=10, spike_users=40, spike_duration=30)
            
            elif scenario == "moderate":
                escalating_result = await tester.run_escalating_load_test(max_users=100, escalation_steps=8, step_duration=30)
                sustained_result = await tester.run_sustained_load_test(concurrent_users=50, duration_minutes=5)
                spike_result = await tester.run_spike_load_test(baseline_users=20, spike_users=80, spike_duration=45)
            
            elif scenario == "heavy":
                escalating_result = await tester.run_escalating_load_test(max_users=200, escalation_steps=10, step_duration=45)
                sustained_result = await tester.run_sustained_load_test(concurrent_users=75, duration_minutes=10)
                spike_result = await tester.run_spike_load_test(baseline_users=30, spike_users=150, spike_duration=60)
            
            else:
                logger.warning(f"Unknown stress scenario: {scenario}, using light")
                escalating_result = await tester.run_escalating_load_test(max_users=50, escalation_steps=5, step_duration=20)
                sustained_result = await tester.run_sustained_load_test(concurrent_users=30, duration_minutes=2)
                spike_result = await tester.run_spike_load_test(baseline_users=10, spike_users=40, spike_duration=30)
            
            # Generate comprehensive report
            report = tester.generate_stress_test_report()
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = self.results_dir / f"stress_test_results_{scenario}_{timestamp}.json"
            report_file = self.results_dir / f"stress_test_report_{scenario}_{timestamp}.md"
            
            results_data = {
                "scenario": scenario,
                "timestamp": timestamp,
                "escalating_result": escalating_result.__dict__,
                "sustained_result": sustained_result.__dict__,
                "spike_result": spike_result.__dict__,
                "summary": {
                    "total_tests": 3,
                    "test_types": ["escalating", "sustained", "spike"]
                }
            }
            
            with open(results_file, 'w') as f:
                json.dump(results_data, f, indent=2, default=str)
            
            with open(report_file, 'w') as f:
                f.write(report)
            
            logger.info(f"✅ Stress tests completed. Results: {results_file}, Report: {report_file}")
            return results_data
            
        except ImportError as e:
            logger.error(f"Failed to import stress test module: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error running stress tests: {e}")
            return {"error": str(e)}
    
    def run_pytest_load_tests(self, test_markers: list = None) -> dict:
        """Run pytest-based load tests"""
        logger.info("🧪 Running pytest-based load tests")
        
        # Build pytest command
        pytest_cmd = [
            sys.executable, "-m", "pytest", 
            str(self.project_root / "tests" / "performance"),
            "-v", "--tb=short"
        ]
        
        # Add markers if specified
        if test_markers:
            for marker in test_markers:
                pytest_cmd.extend(["-m", marker])
        
        # Add output options
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        junit_file = self.results_dir / f"pytest_results_{timestamp}.xml"
        pytest_cmd.extend(["--junitxml", str(junit_file)])
        
        try:
            logger.info(f"Running command: {' '.join(pytest_cmd)}")
            
            result = subprocess.run(
                pytest_cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            # Save results
            results_data = {
                "command": " ".join(pytest_cmd),
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": timestamp
            }
            
            results_file = self.results_dir / f"pytest_execution_{timestamp}.json"
            with open(results_file, 'w') as f:
                json.dump(results_data, f, indent=2)
            
            if result.returncode == 0:
                logger.info(f"✅ Pytest load tests completed successfully")
            else:
                logger.warning(f"⚠️ Pytest load tests completed with issues (exit code: {result.returncode})")
            
            return results_data
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Pytest load tests timed out after 30 minutes")
            return {"error": "Test execution timed out"}
        except Exception as e:
            logger.error(f"❌ Error running pytest load tests: {e}")
            return {"error": str(e)}
    
    def generate_comprehensive_report(self, results: dict) -> str:
        """Generate comprehensive load test report"""
        report_lines = [
            "# 🚀 Comprehensive Load Test Report",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Test Duration**: {self.end_time - self.start_time if self.end_time and self.start_time else 'N/A'}",
            "",
            "## 📊 Executive Summary",
            ""
        ]
        
        # Analyze results
        total_tests_run = 0
        successful_tests = 0
        failed_tests = 0
        
        for test_type, test_results in results.items():
            if isinstance(test_results, dict) and "error" not in test_results:
                total_tests_run += 1
                successful_tests += 1
            elif isinstance(test_results, dict) and "error" in test_results:
                total_tests_run += 1
                failed_tests += 1
        
        success_rate = (successful_tests / total_tests_run * 100) if total_tests_run > 0 else 0
        
        report_lines.extend([
            f"- **Total Test Suites**: {total_tests_run}",
            f"- **Successful Suites**: {successful_tests}",
            f"- **Failed Suites**: {failed_tests}",
            f"- **Overall Success Rate**: {success_rate:.1f}%",
            "",
            "## 🎯 Detailed Results",
            ""
        ])
        
        # Core functionality results
        if "core_functionality" in results:
            core_results = results["core_functionality"]
            if "error" not in core_results:
                report_lines.extend([
                    "### Core Functionality Load Tests ✅",
                    f"- **Total Requests**: {core_results.get('test_summary', {}).get('total_requests', 'N/A'):,}",
                    f"- **Success Rate**: {core_results.get('test_summary', {}).get('overall_success_rate', 'N/A'):.1f}%",
                    f"- **Throughput**: {core_results.get('test_summary', {}).get('overall_rps', 'N/A'):.1f} RPS",
                    ""
                ])
            else:
                report_lines.extend([
                    "### Core Functionality Load Tests ❌",
                    f"- **Error**: {core_results['error']}",
                    ""
                ])
        
        # Stress test results
        if "stress_tests" in results:
            stress_results = results["stress_tests"]
            if "error" not in stress_results:
                report_lines.extend([
                    "### Stress & Endurance Tests ✅",
                    f"- **Scenario**: {stress_results.get('scenario', 'N/A')}",
                    f"- **Test Types**: {', '.join(stress_results.get('summary', {}).get('test_types', []))}",
                    ""
                ])
            else:
                report_lines.extend([
                    "### Stress & Endurance Tests ❌",
                    f"- **Error**: {stress_results['error']}",
                    ""
                ])
        
        # Pytest results
        if "pytest_results" in results:
            pytest_results = results["pytest_results"]
            if pytest_results.get("return_code") == 0:
                report_lines.extend([
                    "### Pytest Load Tests ✅",
                    "- All pytest-based load tests passed",
                    ""
                ])
            else:
                report_lines.extend([
                    "### Pytest Load Tests ⚠️",
                    f"- Exit code: {pytest_results.get('return_code', 'N/A')}",
                    "- Check detailed logs for issues",
                    ""
                ])
        
        # Recommendations
        report_lines.extend([
            "## 💡 Recommendations",
            ""
        ])
        
        if success_rate >= 90:
            report_lines.extend([
                "- System demonstrates excellent performance under load 🎉",
                "- Consider testing with higher load levels to find limits",
                "- Current configuration appears production-ready"
            ])
        elif success_rate >= 70:
            report_lines.extend([
                "- System shows good performance with some areas for improvement",
                "- Review failed tests and optimize bottlenecks",
                "- Consider implementing additional monitoring"
            ])
        else:
            report_lines.extend([
                "- System shows significant performance issues under load ⚠️",
                "- Immediate optimization required before production deployment",
                "- Review system architecture and resource allocation"
            ])
        
        report_lines.extend([
            "",
            "## 📁 Detailed Files",
            f"- **Results Directory**: `{self.results_dir}`",
            f"- **Configuration**: `{self.config_path}`",
            f"- **Logs**: `load_test_results.log`",
            "",
            "---",
            "*Report generated by Load Test Runner*"
        ])
        
        return "\n".join(report_lines)
    
    async def run_comprehensive_suite(self, profile: str = "development", stress_scenario: str = "light") -> dict:
        """Run comprehensive load test suite"""
        logger.info(f"🎯 Starting comprehensive load test suite (profile: {profile}, stress: {stress_scenario})")
        
        self.start_time = datetime.now()
        all_results = {}
        
        try:
            # 1. Core functionality tests
            logger.info("1️⃣ Running core functionality load tests...")
            core_results = await self.run_core_functionality_tests(profile)
            all_results["core_functionality"] = core_results
            
            # 2. Stress and endurance tests
            logger.info("2️⃣ Running stress and endurance tests...")
            stress_results = await self.run_stress_tests(stress_scenario)
            all_results["stress_tests"] = stress_results
            
            # 3. Pytest-based tests
            logger.info("3️⃣ Running pytest-based load tests...")
            pytest_results = self.run_pytest_load_tests()
            all_results["pytest_results"] = pytest_results
            
        except Exception as e:
            logger.error(f"❌ Error in comprehensive test suite: {e}")
            all_results["suite_error"] = str(e)
        
        finally:
            self.end_time = datetime.now()
        
        # Generate comprehensive report
        report = self.generate_comprehensive_report(all_results)
        
        # Save final report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"comprehensive_load_test_report_{timestamp}.md"
        results_file = self.results_dir / f"comprehensive_load_test_results_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        logger.info(f"🎉 Comprehensive load test suite completed!")
        logger.info(f"📊 Report: {report_file}")
        logger.info(f"📁 Results: {results_file}")
        
        # Print summary to console
        print("\n" + "="*80)
        print("🚀 COMPREHENSIVE LOAD TEST SUITE COMPLETED")
        print("="*80)
        print(report)
        print("="*80)
        
        return all_results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AI Assistant Load Test Runner")
    parser.add_argument("--profile", choices=["development", "staging", "production"], 
                       default="development", help="Load test profile")
    parser.add_argument("--stress", choices=["light", "moderate", "heavy"], 
                       default="light", help="Stress test scenario")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--core-only", action="store_true", help="Run only core functionality tests")
    parser.add_argument("--stress-only", action="store_true", help="Run only stress tests")
    parser.add_argument("--pytest-only", action="store_true", help="Run only pytest tests")
    
    args = parser.parse_args()
    
    # Create runner
    runner = LoadTestRunner(config_path=args.config)
    
    async def run_tests():
        if args.core_only:
            await runner.run_core_functionality_tests(args.profile)
        elif args.stress_only:
            await runner.run_stress_tests(args.stress)
        elif args.pytest_only:
            runner.run_pytest_load_tests()
        else:
            await runner.run_comprehensive_suite(args.profile, args.stress)
    
    # Run the selected tests
    try:
        asyncio.run(run_tests())
    except KeyboardInterrupt:
        logger.info("🛑 Load tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 