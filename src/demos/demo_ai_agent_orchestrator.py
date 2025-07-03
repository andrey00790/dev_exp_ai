#!/usr/bin/env python3
"""
🤖 AI Agent Orchestrator Demo

Демонстрация возможностей AI Agent Orchestration System.
Показывает координацию нескольких AI агентов для автоматизации сложных задач.

Usage:
    python src/demos/demo_ai_agent_orchestrator.py
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
import json
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from domain.ai_analysis.ai_agent_orchestrator import (
    AIAgentOrchestrator,
    get_orchestrator,
    execute_agent_task,
    execute_automated_workflow,
    get_agent_capabilities,
    AgentType,
    TaskPriority,
    create_code_review_workflow,
    create_project_assessment_workflow
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIAgentOrchestratorDemo:
    """Comprehensive demo of AI Agent Orchestration capabilities"""
    
    def __init__(self):
        self.demo_project_path = os.getcwd()
        self.orchestrator = None
        
    async def run_all_demos(self):
        """Run all demo scenarios"""
        print("🚀 AI Agent Orchestrator Demo")
        print("=" * 50)
        
        demos = [
            ("System Initialization", self.demo_1_system_initialization),
            ("Single Agent Tasks", self.demo_2_single_agent_tasks),
            ("Multi-Agent Workflow", self.demo_3_multi_agent_workflow),
            ("Custom Workflow Creation", self.demo_4_custom_workflow),
            ("Performance Monitoring", self.demo_5_performance_monitoring),
            ("Advanced Scenarios", self.demo_6_advanced_scenarios)
        ]
        
        for demo_name, demo_func in demos:
            print(f"\n🎯 {demo_name}")
            print("-" * 30)
            
            try:
                start_time = time.time()
                await demo_func()
                duration = time.time() - start_time
                print(f"✅ {demo_name} completed in {duration:.2f}s")
            except Exception as e:
                print(f"❌ {demo_name} failed: {e}")
                logger.exception(f"Demo failed: {demo_name}")
    
    async def demo_1_system_initialization(self):
        """Demo 1: System initialization and agent status"""
        
        print("🔧 Initializing AI Agent Orchestrator...")
        
        # Get orchestrator instance
        self.orchestrator = await get_orchestrator()
        
        # Check agent status
        status = self.orchestrator.get_agent_status()
        print(f"  📊 System Status:")
        print(f"    - Total Agents: {status['total_agents']}")
        print(f"    - Active Agents: {len([a for a in status['agents'].values() if a['status'] == 'idle'])}")
        
        # Show agent capabilities
        capabilities = await get_agent_capabilities()
        print(f"  🎯 Available Agent Types:")
        for agent_type in capabilities['available_agent_types']:
            print(f"    - {agent_type}")
        
        print(f"  📋 Workflow Templates:")
        for template_name, template_info in capabilities['workflow_templates'].items():
            print(f"    - {template_name}: {template_info['description']}")
        
        print("✅ System initialized successfully")
    
    async def demo_2_single_agent_tasks(self):
        """Demo 2: Execute single agent tasks"""
        
        print("🔍 Testing individual agent capabilities...")
        
        # Test Architect Agent
        print("  🏗️ Testing Architect Agent...")
        try:
            result = await execute_agent_task(
                agent_type="architect",
                task_type="analyze_architecture",
                input_data={"project_path": self.demo_project_path}
            )
            
            if result["status"] == "completed":
                analysis = result["result"]
                print(f"    ✅ Architecture Analysis:")
                print(f"      - Components: {len(analysis.get('components', []))}")
                print(f"      - Health Score: {analysis.get('health_score', 0):.1f}/100")
                print(f"      - Recommendations: {len(analysis.get('recommendations', []))}")
                
                # Show top recommendation
                if analysis.get('recommendations'):
                    print(f"      - Top Recommendation: {analysis['recommendations'][0]}")
            else:
                print(f"    ❌ Architecture analysis failed: {result.get('error')}")
        except Exception as e:
            print(f"    ⚠️ Architect agent test failed: {e}")
        
        # Test Code Review Agent
        print("  📝 Testing Code Review Agent...")
        try:
            sample_code = '''
def process_data(data):
    # TODO: Add validation
    print("Processing data...")
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
'''
            
            result = await execute_agent_task(
                agent_type="reviewer",
                task_type="review_code",
                input_data={
                    "code": sample_code,
                    "file_path": "sample.py"
                }
            )
            
            if result["status"] == "completed":
                review = result["result"]
                print(f"    ✅ Code Review:")
                print(f"      - Overall Score: {review.get('overall_score', 0)}/100")
                print(f"      - Issues Found: {len(review.get('issues', []))}")
                print(f"      - Suggestions: {len(review.get('suggestions', []))}")
                
                # Show first issue if any
                if review.get('issues'):
                    print(f"      - First Issue: {review['issues'][0]}")
            else:
                print(f"    ❌ Code review failed: {result.get('error')}")
        except Exception as e:
            print(f"    ⚠️ Code review agent test failed: {e}")
    
    async def demo_3_multi_agent_workflow(self):
        """Demo 3: Execute multi-agent automated workflows"""
        
        print("🔄 Testing automated workflows...")
        
        # Test Project Assessment Workflow
        print("  📊 Running Project Assessment Workflow...")
        try:
            result = await execute_automated_workflow(
                workflow_name="project_assessment",
                input_data={
                    "project_path": self.demo_project_path,
                    "requirements": ["scalability", "security", "performance"]
                }
            )
            
            if result["status"] == "completed":
                summary = result["execution_summary"]
                print(f"    ✅ Workflow Completed:")
                print(f"      - Total Steps: {summary.get('total_steps', 0)}")
                print(f"      - Completed Steps: {summary.get('completed_steps', 0)}")
                
                # Show step results summary
                if result.get("result", {}).get("step_results"):
                    successful_steps = len([
                        s for s in result["result"]["step_results"].values() 
                        if s.get("status") == "completed"
                    ])
                    print(f"      - Successful Steps: {successful_steps}")
            else:
                print(f"    ❌ Workflow failed: {result.get('error')}")
        except Exception as e:
            print(f"    ⚠️ Project assessment workflow failed: {e}")
        
        # Test Code Review Workflow
        print("  🔍 Running Automated Code Review Workflow...")
        try:
            result = await execute_automated_workflow(
                workflow_name="automated_code_review",
                input_data={
                    "project_path": self.demo_project_path,
                    "code": "def hello(): print('Hello World')",
                    "file_path": "hello.py"
                }
            )
            
            if result["status"] == "completed":
                print(f"    ✅ Code Review Workflow:")
                print(f"      - Status: {result['status']}")
                print(f"      - Workflow ID: {result['workflow_id']}")
            else:
                print(f"    ❌ Code review workflow failed: {result.get('error')}")
        except Exception as e:
            print(f"    ⚠️ Code review workflow failed: {e}")
    
    async def demo_4_custom_workflow(self):
        """Demo 4: Create and execute custom workflows"""
        
        print("🛠️ Creating custom workflow...")
        
        try:
            from domain.ai_analysis.ai_agent_orchestrator import AutomatedWorkflow, WorkflowStep, AgentType
            
            # Create custom workflow for comprehensive project analysis
            custom_steps = [
                WorkflowStep(
                    id="architecture_analysis", 
                    name="Architecture Analysis",
                    agent_type=AgentType.ARCHITECT,
                    task_type="analyze_architecture",
                    input_mapping={"project_path": "input.project_path"},
                    output_key="architecture"
                ),
                WorkflowStep(
                    id="tech_recommendations",
                    name="Technology Recommendations", 
                    agent_type=AgentType.ARCHITECT,
                    task_type="recommend_technologies",
                    input_mapping={
                        "requirements": "input.requirements",
                        "current_stack": "architecture.technologies"
                    },
                    depends_on=["architecture_analysis"],
                    output_key="recommendations"
                )
            ]
            
            custom_workflow = AutomatedWorkflow(
                name="Custom Project Analysis",
                description="Custom workflow for comprehensive project analysis",
                steps=custom_steps,
                input_schema={
                    "required": ["project_path"],
                    "optional": ["requirements"]
                },
                timeout_minutes=20
            )
            
            # Register custom workflow
            workflow_id = self.orchestrator.register_workflow(custom_workflow)
            print(f"  ✅ Custom workflow registered: {workflow_id}")
            
            # Execute custom workflow
            print("  🚀 Executing custom workflow...")
            result = await self.orchestrator.execute_workflow(
                workflow_id,
                {
                    "project_path": self.demo_project_path,
                    "requirements": ["performance", "scalability"]
                }
            )
            
            if result["status"] == "completed":
                print(f"    ✅ Custom workflow executed successfully")
                print(f"      - Workflow ID: {workflow_id}")
                print(f"      - Steps completed: {result['execution_summary'].get('completed_steps', 0)}")
            else:
                print(f"    ❌ Custom workflow failed: {result.get('error')}")
                
        except Exception as e:
            print(f"    ⚠️ Custom workflow creation failed: {e}")
    
    async def demo_5_performance_monitoring(self):
        """Demo 5: Performance monitoring and metrics"""
        
        print("📈 Performance monitoring and metrics...")
        
        try:
            # Get current metrics
            status = self.orchestrator.get_agent_status()
            metrics = status["metrics"]
            
            print(f"  📊 System Metrics:")
            print(f"    - Tasks Completed: {metrics['tasks_completed']}")
            print(f"    - Tasks Failed: {metrics['tasks_failed']}")
            print(f"    - Average Execution Time: {metrics['average_execution_time']:.2f}s")
            
            # Calculate success rate
            total_tasks = metrics['tasks_completed'] + metrics['tasks_failed']
            if total_tasks > 0:
                success_rate = (metrics['tasks_completed'] / total_tasks) * 100
                print(f"    - Success Rate: {success_rate:.1f}%")
            
            # Agent utilization
            print(f"  🤖 Agent Utilization:")
            for agent_id, utilization in metrics.get("agent_utilization", {}).items():
                print(f"    - {agent_id}: {utilization:.1f}%")
            
            # System health assessment
            if total_tasks > 0:
                if success_rate >= 95:
                    health = "🟢 Excellent"
                elif success_rate >= 85:
                    health = "🟡 Good"
                elif success_rate >= 70:
                    health = "🟠 Fair"
                else:
                    health = "🔴 Needs Attention"
                
                print(f"  🏥 System Health: {health}")
            
        except Exception as e:
            print(f"    ⚠️ Performance monitoring failed: {e}")
    
    async def demo_6_advanced_scenarios(self):
        """Demo 6: Advanced scenarios and edge cases"""
        
        print("🎯 Advanced scenarios and capabilities...")
        
        # Parallel task execution
        print("  ⚡ Testing parallel task execution...")
        try:
            tasks = []
            
            # Create multiple tasks to run in parallel
            for i in range(3):
                task = execute_agent_task(
                    agent_type="architect",
                    task_type="recommend_technologies",
                    input_data={
                        "requirements": [f"requirement_{i}"],
                        "current_stack": ["python", "fastapi"]
                    },
                    priority="medium"
                )
                tasks.append(task)
            
            # Execute tasks in parallel
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            parallel_time = time.time() - start_time
            
            successful_tasks = len([r for r in results if isinstance(r, dict) and r.get("status") == "completed"])
            print(f"    ✅ Parallel Execution:")
            print(f"      - Tasks: {len(tasks)}")
            print(f"      - Successful: {successful_tasks}")
            print(f"      - Total Time: {parallel_time:.2f}s")
            print(f"      - Avg Time per Task: {parallel_time/len(tasks):.2f}s")
            
        except Exception as e:
            print(f"    ⚠️ Parallel execution test failed: {e}")
        
        # Error handling and recovery
        print("  🛡️ Testing error handling...")
        try:
            # Test with invalid input
            result = await execute_agent_task(
                agent_type="architect",
                task_type="invalid_task_type",  # This should fail
                input_data={"invalid": "data"}
            )
            
            if result["status"] == "failed":
                print(f"    ✅ Error handling working correctly")
                print(f"      - Error caught: {result.get('error', 'Unknown error')[:50]}...")
            else:
                print(f"    ⚠️ Expected failure but got success")
                
        except Exception as e:
            print(f"    ✅ Exception properly handled: {str(e)[:50]}...")
        
        # Load testing (simplified)
        print("  📈 Simple load testing...")
        try:
            load_tasks = []
            num_tasks = 5
            
            for i in range(num_tasks):
                task = execute_agent_task(
                    agent_type="reviewer",
                    task_type="review_code",
                    input_data={
                        "code": f"def function_{i}(): return {i}",
                        "file_path": f"test_{i}.py"
                    }
                )
                load_tasks.append(task)
            
            start_time = time.time()
            load_results = await asyncio.gather(*load_tasks, return_exceptions=True)
            load_time = time.time() - start_time
            
            successful_load_tasks = len([
                r for r in load_results 
                if isinstance(r, dict) and r.get("status") == "completed"
            ])
            
            print(f"    ✅ Load Test Results:")
            print(f"      - Concurrent Tasks: {num_tasks}")
            print(f"      - Successful: {successful_load_tasks}")
            print(f"      - Total Time: {load_time:.2f}s")
            print(f"      - Throughput: {successful_load_tasks/load_time:.2f} tasks/sec")
            
        except Exception as e:
            print(f"    ⚠️ Load testing failed: {e}")
    
    def print_summary(self):
        """Print demo summary and next steps"""
        print("\n" + "=" * 50)
        print("📊 AI Agent Orchestrator Demo Summary")
        print("=" * 50)
        
        print("✅ Demonstrated Capabilities:")
        print("  🤖 Multi-agent coordination")
        print("  🔄 Automated workflow execution")
        print("  🛠️ Custom workflow creation")
        print("  📈 Performance monitoring")
        print("  ⚡ Parallel task execution")
        print("  🛡️ Error handling and recovery")
        
        print("\n🚀 Next Steps:")
        print("  1. Integrate with existing Phase 1-3 components")
        print("  2. Add more specialized agent types")
        print("  3. Implement advanced workflow patterns")
        print("  4. Add machine learning for workflow optimization")
        print("  5. Create web UI for workflow management")
        
        print("\n📚 API Endpoints Available:")
        print("  • GET  /api/v1/ai-agents/status")
        print("  • GET  /api/v1/ai-agents/capabilities")
        print("  • POST /api/v1/ai-agents/execute-task")
        print("  • POST /api/v1/ai-agents/execute-workflow")
        print("  • POST /api/v1/ai-agents/create-workflow")
        print("  • GET  /api/v1/ai-agents/workflows")
        print("  • POST /api/v1/ai-agents/analyze-architecture")
        print("  • POST /api/v1/ai-agents/review-code")
        
        print(f"\n🎯 Phase 4A: AI Agent Orchestration - COMPLETE")
        print(f"   Ready for production deployment! 🚀")

async def main():
    """Main demo function"""
    demo = AIAgentOrchestratorDemo()
    
    try:
        await demo.run_all_demos()
        demo.print_summary()
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        logger.exception("Demo failed")

if __name__ == "__main__":
    # Run the demo
    print("🚀 Starting AI Agent Orchestrator Demo...")
    asyncio.run(main()) 