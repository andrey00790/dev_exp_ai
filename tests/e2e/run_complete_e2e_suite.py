#!/usr/bin/env python3
"""
Complete E2E Test Suite Runner
Executes all E2E tests and generates final production readiness report
"""

import asyncio
import time
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Import all E2E test modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_complete_workflow_e2e import CompleteWorkflowE2ETester
from test_frontend_backend_e2e import FrontendBackendE2ETester
from test_system_load_e2e import SystemLoadE2ETester

class CompleteE2ETestSuite:
    """Complete E2E test suite for AI Assistant MVP"""
    
    def __init__(self, backend_url: str = "http://localhost:8000", frontend_url: str = "http://localhost:3000"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    async def run_complete_e2e_suite(self):
        """Run the complete E2E test suite"""
        self.start_time = time.time()
        
        print("🚀 AI ASSISTANT MVP - COMPLETE E2E TEST SUITE")
        print("=" * 100)
        print(f"Backend URL: {self.backend_url}")
        print(f"Frontend URL: {self.frontend_url}")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)
        
        # Test Suite 1: Complete Workflow Tests
        print("\n📋 TEST SUITE 1: COMPLETE WORKFLOW TESTS")
        print("-" * 60)
        workflow_tester = CompleteWorkflowE2ETester(self.backend_url)
        workflow_success = await workflow_tester.run_complete_e2e_tests()
        self.test_results["workflow_tests"] = {
            "success": workflow_success,
            "results": workflow_tester.test_results,
            "duration": time.time() - self.start_time
        }
        
        # Test Suite 2: Frontend-Backend Integration Tests
        print("\n🌐 TEST SUITE 2: FRONTEND-BACKEND INTEGRATION TESTS")
        print("-" * 60)
        frontend_backend_start = time.time()
        frontend_backend_tester = FrontendBackendE2ETester(self.backend_url, self.frontend_url)
        frontend_backend_success = await frontend_backend_tester.run_frontend_backend_e2e_tests()
        self.test_results["frontend_backend_tests"] = {
            "success": frontend_backend_success,
            "duration": time.time() - frontend_backend_start
        }
        
        # Test Suite 3: System Load Tests  
        print("\n🔥 TEST SUITE 3: SYSTEM LOAD TESTS")
        print("-" * 60)
        load_test_start = time.time()
        load_tester = SystemLoadE2ETester(self.backend_url)
        load_test_success = await load_tester.run_system_load_tests()
        self.test_results["load_tests"] = {
            "success": load_test_success,
            "results": load_tester.results,
            "duration": time.time() - load_test_start
        }
        
        self.end_time = time.time()
        
        # Generate final report
        await self.generate_final_report()
        
        # Determine overall success
        overall_success = (
            workflow_success and 
            frontend_backend_success and 
            load_test_success
        )
        
        return overall_success
    
    async def check_system_readiness(self):
        """Check if the system is ready for E2E testing"""
        print("🔍 Checking System Readiness...")
        
        import aiohttp
        
        # Check backend
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.backend_url}/health") as response:
                    if response.status == 200:
                        print("✅ Backend is running and healthy")
                        backend_ready = True
                    else:
                        print(f"❌ Backend health check failed: {response.status}")
                        backend_ready = False
        except Exception as e:
            print(f"❌ Backend is not accessible: {e}")
            backend_ready = False
        
        # Check frontend (optional)
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.frontend_url) as response:
                    if response.status == 200:
                        print("✅ Frontend is running")
                        frontend_ready = True
                    else:
                        print(f"⚠️ Frontend may not be running: {response.status}")
                        frontend_ready = False
        except Exception as e:
            print(f"⚠️ Frontend is not accessible (optional): {e}")
            frontend_ready = False
        
        # Check authentication
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/v1/auth/login",
                    json={"email": "admin@example.com", "password": "admin"}
                ) as response:
                    if response.status == 200:
                        print("✅ Authentication system working")
                        auth_ready = True
                    else:
                        print(f"❌ Authentication failed: {response.status}")
                        auth_ready = False
        except Exception as e:
            print(f"❌ Authentication check failed: {e}")
            auth_ready = False
        
        system_ready = backend_ready and auth_ready
        
        if system_ready:
            print("✅ System is ready for E2E testing")
        else:
            print("❌ System is not ready for E2E testing")
            print("\n🔧 Prerequisites:")
            print("   1. Start backend: export PYTHONPATH=$PWD:$PYTHONPATH && python3 app/main_production.py")
            print("   2. Start frontend (optional): cd frontend && npm run dev")
            print("   3. Ensure admin user exists: admin@example.com / admin")
        
        return system_ready
    
    async def generate_final_report(self):
        """Generate comprehensive final E2E test report"""
        print("\n" + "=" * 100)
        print("📊 FINAL E2E TEST REPORT - AI ASSISTANT MVP")
        print("=" * 100)
        
        total_duration = self.end_time - self.start_time
        
        # Executive Summary
        print("📋 EXECUTIVE SUMMARY")
        print("-" * 50)
        
        workflow_success = self.test_results["workflow_tests"]["success"]
        frontend_backend_success = self.test_results["frontend_backend_tests"]["success"]
        load_test_success = self.test_results["load_tests"]["success"]
        
        overall_success = workflow_success and frontend_backend_success and load_test_success
        
        print(f"Overall Status: {'🎉 PRODUCTION READY' if overall_success else '⚠️ NEEDS ATTENTION'}")
        print(f"Total Test Duration: {total_duration:.2f} seconds")
        print(f"Test Completion Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test Suite Results
        print(f"\n📊 TEST SUITE RESULTS")
        print("-" * 50)
        
        suite_results = [
            ("Complete Workflow Tests", workflow_success, self.test_results["workflow_tests"]["duration"]),
            ("Frontend-Backend Integration", frontend_backend_success, self.test_results["frontend_backend_tests"]["duration"]),
            ("System Load Tests", load_test_success, self.test_results["load_tests"]["duration"])
        ]
        
        for suite_name, success, duration in suite_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {suite_name} ({duration:.2f}s)")
        
        # Detailed Workflow Results
        if "results" in self.test_results["workflow_tests"]:
            print(f"\n🔍 WORKFLOW TEST DETAILS")
            print("-" * 50)
            
            workflow_results = self.test_results["workflow_tests"]["results"]
            for result in workflow_results:
                status = "✅" if result.status == "PASSED" else "❌"
                print(f"{status} {result.name} ({result.duration:.2f}s)")
                
                # Show key details
                if result.details:
                    for key, value in result.details.items():
                        if not key.startswith("error"):
                            print(f"      {key}: {value}")
        
        # Load Test Performance Summary
        if "results" in self.test_results["load_tests"]:
            print(f"\n⚡ LOAD TEST PERFORMANCE SUMMARY")
            print("-" * 50)
            
            load_results = self.test_results["load_tests"]["results"]
            if load_results:
                total_requests = sum(r.total_requests for r in load_results)
                total_successful = sum(r.successful_requests for r in load_results)
                avg_response_time = sum(r.avg_response_time for r in load_results) / len(load_results)
                avg_rps = sum(r.requests_per_second for r in load_results) / len(load_results)
                
                print(f"Total Requests Processed: {total_requests:,}")
                print(f"Success Rate: {(total_successful/total_requests*100):.2f}%")
                print(f"Average Response Time: {avg_response_time*1000:.1f}ms")
                print(f"Average Requests/Second: {avg_rps:.2f}")
                
                # Performance classification
                if avg_response_time < 0.5 and avg_rps > 100:
                    perf_grade = "🏆 EXCELLENT"
                elif avg_response_time < 1.0 and avg_rps > 50:
                    perf_grade = "🥈 GOOD"
                elif avg_response_time < 2.0 and avg_rps > 20:
                    perf_grade = "🥉 ACCEPTABLE"
                else:
                    perf_grade = "⚠️ NEEDS IMPROVEMENT"
                
                print(f"Performance Grade: {perf_grade}")
        
        # System Capabilities Summary
        print(f"\n🎯 VALIDATED SYSTEM CAPABILITIES")
        print("-" * 50)
        
        capabilities = [
            ("🔐 JWT Authentication & Authorization", workflow_success),
            ("🔍 Vector Search with Qdrant", workflow_success),
            ("🤖 LLM Operations (Multi-provider)", workflow_success),
            ("💾 Cache System (Redis + Local)", workflow_success),
            ("🌐 Frontend-Backend Integration", frontend_backend_success),
            ("⚡ High-Performance Under Load", load_test_success),
            ("🔒 Security & Error Handling", workflow_success and frontend_backend_success),
            ("📊 Monitoring & Health Checks", workflow_success)
        ]
        
        for capability, validated in capabilities:
            status = "✅" if validated else "❌"
            print(f"{status} {capability}")
        
        # Production Readiness Checklist
        print(f"\n✅ PRODUCTION READINESS CHECKLIST")
        print("-" * 50)
        
        checklist = [
            ("Authentication System", workflow_success),
            ("Vector Search Functionality", workflow_success),
            ("LLM Integration", workflow_success),
            ("Cache Layer", workflow_success),
            ("API Response Consistency", frontend_backend_success),
            ("Error Handling", frontend_backend_success),
            ("Performance Under Load", load_test_success),
            ("Security Validation", workflow_success),
            ("Health Monitoring", workflow_success)
        ]
        
        passed_checks = sum(1 for _, status in checklist if status)
        total_checks = len(checklist)
        
        for check_name, status in checklist:
            icon = "✅" if status else "❌"
            print(f"{icon} {check_name}")
        
        readiness_percentage = (passed_checks / total_checks) * 100
        
        print(f"\n📈 PRODUCTION READINESS: {readiness_percentage:.1f}% ({passed_checks}/{total_checks})")
        
        # Final Recommendation
        print(f"\n🎯 FINAL RECOMMENDATION")
        print("-" * 50)
        
        if overall_success:
            print("🎉 SYSTEM IS PRODUCTION READY!")
            print("\n✨ The AI Assistant MVP has passed all critical E2E tests:")
            print("   🚀 Deploy immediately to production")
            print("   📊 All systems operational and performing well")
            print("   🔒 Security and reliability validated")
            print("   ⚡ Performance meets production requirements")
            
            print(f"\n🌟 DEPLOYMENT COMMANDS:")
            print("   Backend: export PYTHONPATH=$PWD:$PYTHONPATH && python3 app/main_production.py")
            print("   Frontend: cd frontend && npm run build && npm run preview")
            print("   Docker: docker-compose -f docker-compose.prod.yml up")
            
        elif readiness_percentage >= 80:
            print("⚠️ SYSTEM IS MOSTLY READY - Minor Issues Detected")
            print("\n🔧 Address the following before production deployment:")
            failed_checks = [name for name, status in checklist if not status]
            for check in failed_checks:
                print(f"   ❌ {check}")
            print("\n📋 Recommended actions:")
            print("   1. Fix failing test suites")
            print("   2. Re-run E2E tests to validate fixes")
            print("   3. Deploy to staging environment first")
            
        else:
            print("❌ SYSTEM NOT READY FOR PRODUCTION")
            print("\n🚨 Critical issues detected:")
            failed_checks = [name for name, status in checklist if not status]
            for check in failed_checks:
                print(f"   ❌ {check}")
            print("\n🔧 Required actions:")
            print("   1. Fix all failing systems")
            print("   2. Conduct thorough testing")
            print("   3. Re-run complete E2E suite")
            print("   4. Consider additional development time")
        
        # Save detailed report
        await self.save_detailed_report()
        
        print("\n" + "=" * 100)
        
        return overall_success
    
    async def save_detailed_report(self):
        """Save detailed JSON report"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": self.end_time - self.start_time,
            "backend_url": self.backend_url,
            "frontend_url": self.frontend_url,
            "test_results": {}
        }
        
        # Convert test results to serializable format
        for suite_name, suite_data in self.test_results.items():
            report_data["test_results"][suite_name] = {
                "success": suite_data["success"],
                "duration": suite_data["duration"]
            }
            
            if "results" in suite_data and suite_data["results"]:
                report_data["test_results"][suite_name]["details"] = []
                
                for result in suite_data["results"]:
                    if hasattr(result, 'name'):  # Workflow test result
                        report_data["test_results"][suite_name]["details"].append({
                            "name": result.name,
                            "status": result.status,
                            "duration": result.duration,
                            "details": result.details
                        })
                    elif hasattr(result, 'test_name'):  # Load test result
                        report_data["test_results"][suite_name]["details"].append({
                            "test_name": result.test_name,
                            "total_requests": result.total_requests,
                            "successful_requests": result.successful_requests,
                            "avg_response_time": result.avg_response_time,
                            "requests_per_second": result.requests_per_second,
                            "error_rate": result.error_rate
                        })
        
        # Save to file
        report_filename = f"e2e_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_filename}")

async def main():
    """Main E2E test suite runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run complete E2E test suite for AI Assistant MVP')
    parser.add_argument('--backend-url', default='http://localhost:8000', help='Backend URL')
    parser.add_argument('--frontend-url', default='http://localhost:3000', help='Frontend URL')
    parser.add_argument('--skip-readiness-check', action='store_true', help='Skip system readiness check')
    
    args = parser.parse_args()
    
    suite = CompleteE2ETestSuite(args.backend_url, args.frontend_url)
    
    # Check system readiness
    if not args.skip_readiness_check:
        if not await suite.check_system_readiness():
            print("\n❌ System readiness check failed. Exiting.")
            return False
    
    # Run complete test suite
    success = await suite.run_complete_e2e_suite()
    
    if success:
        print("\n🚀🚀🚀 ALL E2E TESTS PASSED - SYSTEM IS PRODUCTION READY! 🚀🚀🚀")
        return True
    else:
        print("\n❌ E2E tests failed. System needs attention before production deployment.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 