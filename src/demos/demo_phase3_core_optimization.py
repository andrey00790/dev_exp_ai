"""
Phase 3 Core Logic Improvements Demo Script
Comprehensive demonstration of enhanced async patterns, repository integration, and performance optimization

Features tested:
- Core Logic Engine with circuit breakers and adaptive timeouts
- Smart Repository Integration with multi-source data
- Performance Optimization Engine with real-time monitoring
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime

# Phase 3 imports
from domain.core.core_logic_engine import (
    initialize_core_engine, execute_intelligently, TaskType, get_core_engine_stats
)
from domain.integration.smart_repository_integration import (
    initialize_smart_repository, register_git_repository, 
    search_repositories, get_repository_stats, DataSourceType
)
from domain.code_optimization.performance_optimization_engine import (
    initialize_performance_engine, record_response_time, record_error_rate,
    get_performance_dashboard
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase3Demo:
    """Phase 3 Core Logic Improvements Demo"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
    
    async def run_complete_demo(self):
        """Run complete Phase 3 demonstration"""
        logger.info("🚀 Starting Phase 3 Core Logic Improvements Demo")
        self.start_time = datetime.now()
        
        try:
            # Step 1: Initialize all engines
            await self.demo_initialization()
            
            # Step 2: Core Logic Engine demo
            await self.demo_core_logic()
            
            # Step 3: Repository Integration demo
            await self.demo_repository()
            
            # Step 4: Performance Optimization demo
            await self.demo_performance()
            
            # Step 5: Generate report
            await self.generate_report()
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
        
        logger.info("✅ Phase 3 Demo completed")
    
    async def demo_initialization(self):
        """Demonstrate engine initialization"""
        logger.info("\n" + "="*50)
        logger.info("🔧 STEP 1: Engine Initialization")
        logger.info("="*50)
        
        # Initialize Core Logic Engine
        logger.info("📦 Initializing Core Logic Engine...")
        core_success = await initialize_core_engine()
        logger.info(f"✅ Core Logic Engine: {'Success' if core_success else 'Failed'}")
        
        # Initialize Smart Repository Integration
        logger.info("📚 Initializing Smart Repository Integration...")
        repo_success = await initialize_smart_repository()
        logger.info(f"✅ Repository Integration: {'Success' if repo_success else 'Failed'}")
        
        # Initialize Performance Optimization Engine
        logger.info("📊 Initializing Performance Optimization Engine...")
        perf_success = await initialize_performance_engine()
        logger.info(f"✅ Performance Engine: {'Success' if perf_success else 'Failed'}")
        
        self.results["initialization"] = {
            "core_engine": core_success,
            "repository_integration": repo_success,
            "performance_optimization": perf_success,
            "overall_success": all([core_success, repo_success, perf_success])
        }
        
        if all([core_success, repo_success, perf_success]):
            logger.info("🎉 All engines initialized successfully!")
        else:
            logger.warning("⚠️ Some engines failed to initialize")
    
    async def demo_core_logic(self):
        """Demonstrate Core Logic Engine features"""
        logger.info("\n" + "="*50)
        logger.info("🧠 STEP 2: Core Logic Engine Demo")
        logger.info("="*50)
        
        # Test intelligent execution
        logger.info("🔌 Testing intelligent execution patterns...")
        
        async def test_function():
            await asyncio.sleep(0.1)
            return {"status": "success", "data": f"executed_at_{datetime.now().isoformat()}"}
        
        # Test with different configurations
        start_time = time.time()
        result = await execute_intelligently(
            test_function,
            task_type=TaskType.IO_BOUND,
            enable_circuit_breaker=True,
            enable_coalescing=True,
            enable_adaptive_timeout=True
        )
        execution_time = time.time() - start_time
        
        logger.info(f"✅ Intelligent execution completed in {execution_time:.3f}s")
        logger.info(f"📊 Result: {result}")
        
        # Test request coalescing
        logger.info("🔄 Testing Request Coalescing...")
        
        async def coalesced_function():
            await asyncio.sleep(0.2)
            return {"coalesced": True, "timestamp": datetime.now().isoformat()}
        
        # Execute same function multiple times concurrently
        coalescing_tasks = [
            execute_intelligently(coalesced_function, enable_coalescing=True) 
            for _ in range(3)
        ]
        
        coalescing_start = time.time()
        coalescing_results = await asyncio.gather(*coalescing_tasks)
        coalescing_time = time.time() - coalescing_start
        
        logger.info(f"✅ Coalescing test completed in {coalescing_time:.3f}s")
        logger.info(f"📊 Unique responses: {len(set(str(r) for r in coalescing_results))}/3")
        
        # Get engine stats
        core_stats = await get_core_engine_stats()
        logger.info(f"📊 Engine State: {core_stats.get('engine_state', 'unknown')}")
        
        self.results["core_logic_engine"] = {
            "intelligent_execution": "success",
            "request_coalescing": "success",
            "engine_state": core_stats.get('engine_state', 'unknown'),
            "execution_time": execution_time,
            "coalescing_time": coalescing_time
        }
    
    async def demo_repository(self):
        """Demonstrate Smart Repository Integration"""
        logger.info("\n" + "="*50)
        logger.info("📚 STEP 3: Repository Integration Demo")
        logger.info("="*50)
        
        # Register demo repository
        logger.info("📁 Registering Git repository...")
        git_success = await register_git_repository(
            source_id="demo_git_repo",
            repo_url="https://github.com/example/demo-repo",
            name="Demo Git Repository"
        )
        logger.info(f"✅ Git repository registration: {'Success' if git_success else 'Failed'}")
        
        # Wait for initialization
        await asyncio.sleep(1)
        
        # Perform search
        logger.info("🔍 Searching repositories...")
        search_start = time.time()
        search_results = await search_repositories(
            query="documentation",
            source_types=[DataSourceType.GIT_REPOSITORY],
            limit=5
        )
        search_time = time.time() - search_start
        
        logger.info(f"✅ Search completed in {search_time:.3f}s")
        logger.info(f"📊 Found {len(search_results)} results")
        
        # Get repository stats
        repo_stats = await get_repository_stats()
        logger.info(f"📊 Total Sources: {repo_stats.get('total_sources', 0)}")
        logger.info(f"📈 Active Sources: {repo_stats.get('active_sources', 0)}")
        
        self.results["repository_integration"] = {
            "git_registration": git_success,
            "search_results": len(search_results),
            "total_sources": repo_stats.get('total_sources', 0),
            "active_sources": repo_stats.get('active_sources', 0),
            "search_time": search_time
        }
    
    async def demo_performance(self):
        """Demonstrate Performance Optimization Engine"""
        logger.info("\n" + "="*50)
        logger.info("📊 STEP 4: Performance Optimization Demo")
        logger.info("="*50)
        
        # Record sample performance metrics
        logger.info("📈 Recording performance metrics...")
        
        # Simulate response times
        for i in range(5):
            response_time = random.uniform(0.1, 1.0)
            await record_response_time(response_time, component="demo_api")
            await asyncio.sleep(0.1)
        
        # Simulate error rates
        for i in range(3):
            error_rate = random.uniform(0.0, 5.0)
            await record_error_rate(error_rate, component="demo_service")
            await asyncio.sleep(0.1)
        
        logger.info("✅ Performance metrics recorded")
        
        # Get performance dashboard
        logger.info("📊 Retrieving performance dashboard...")
        dashboard_start = time.time()
        dashboard = await get_performance_dashboard()
        dashboard_time = time.time() - dashboard_start
        
        logger.info(f"✅ Dashboard retrieved in {dashboard_time:.3f}s")
        logger.info(f"🎯 Performance Score: {dashboard.get('performance_score', 0):.1f}/100")
        logger.info(f"🚨 Active Alerts: {len(dashboard.get('active_alerts', []))}")
        
        # Display system metrics
        system_metrics = dashboard.get('system_metrics', {})
        logger.info(f"💻 CPU Usage: {system_metrics.get('cpu_percent', 0):.1f}%")
        logger.info(f"💾 Memory Usage: {system_metrics.get('memory_percent', 0):.1f}%")
        
        self.results["performance_optimization"] = {
            "metrics_recorded": 8,  # 5 response times + 3 error rates
            "performance_score": dashboard.get('performance_score', 0),
            "active_alerts": len(dashboard.get('active_alerts', [])),
            "cpu_usage": system_metrics.get('cpu_percent', 0),
            "memory_usage": system_metrics.get('memory_percent', 0),
            "dashboard_time": dashboard_time
        }
    
    async def generate_report(self):
        """Generate comprehensive demo report"""
        logger.info("\n" + "="*50)
        logger.info("📋 STEP 5: Demo Report Generation")
        logger.info("="*50)
        
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Collect final statistics
        final_core_stats = await get_core_engine_stats()
        final_repo_stats = await get_repository_stats()
        final_perf_stats = await get_performance_dashboard()
        
        report = {
            "demo_summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration": total_duration
            },
            "component_results": self.results,
            "final_states": {
                "core_engine_state": final_core_stats.get("engine_state", "unknown"),
                "repository_sources": final_repo_stats.get("total_sources", 0),
                "performance_score": final_perf_stats.get("performance_score", 0)
            }
        }
        
        # Display report summary
        logger.info("📊 PHASE 3 DEMO REPORT")
        logger.info(f"⏱️ Total Duration: {total_duration:.2f} seconds")
        logger.info(f"🎯 Performance Score: {final_perf_stats.get('performance_score', 0):.1f}/100")
        logger.info(f"🔧 Core Engine: {final_core_stats.get('engine_state', 'unknown')}")
        logger.info(f"📚 Repository Sources: {final_repo_stats.get('total_sources', 0)}")
        
        # Save report
        report_filename = f"phase3_demo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"📁 Report saved to: {report_filename}")
        except Exception as e:
            logger.warning(f"⚠️ Could not save report: {e}")

async def demo_intelligent_execution():
    """Quick demo of intelligent execution patterns"""
    logger.info("\n🧠 Quick Intelligent Execution Demo")
    
    async def cpu_task():
        await asyncio.sleep(0.1)
        return {"type": "cpu", "result": sum(i**2 for i in range(100))}
    
    async def io_task():
        await asyncio.sleep(0.2)
        return {"type": "io", "result": "file_data"}
    
    async def network_task():
        await asyncio.sleep(0.15)
        return {"type": "network", "result": "api_response"}
    
    # Test different task types
    tasks = [
        (cpu_task, TaskType.CPU_INTENSIVE),
        (io_task, TaskType.IO_BOUND),
        (network_task, TaskType.NETWORK_HEAVY)
    ]
    
    for task_func, task_type in tasks:
        start_time = time.time()
        result = await execute_intelligently(
            task_func,
            task_type=task_type,
            enable_circuit_breaker=True,
            enable_adaptive_timeout=True
        )
        execution_time = time.time() - start_time
        logger.info(f"✅ {task_type.value}: {execution_time:.3f}s - {result['result']}")

async def main():
    """Main demo execution"""
    print("\n" + "="*70)
    print("🚀 AI ASSISTANT PHASE 3: CORE LOGIC IMPROVEMENTS DEMO")
    print("="*70)
    print("Testing: Enhanced Async Patterns, Repository Integration, Performance Optimization")
    print("="*70)
    
    demo = Phase3Demo()
    await demo.run_complete_demo()
    
    # Additional intelligent execution demo
    await demo_intelligent_execution()
    
    print("\n" + "="*70)
    print("✅ PHASE 3 DEMO COMPLETED")
    print("="*70)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        logging.exception("Demo error details:") 