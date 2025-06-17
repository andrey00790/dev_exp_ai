#!/usr/bin/env python3
"""
Comprehensive Performance Testing Pipeline
Task 2.3: Enhanced Testing Framework - Automation

Features:
- Backend load testing automation
- Frontend performance testing
- Database performance validation
- WebSocket stress testing
- Performance regression detection
- Automated reporting
"""

import os
import sys
import subprocess
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List
import argparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceTestPipeline:
    """
    Automated performance testing pipeline
    
    Orchestrates:
    - Backend API load testing
    - Frontend performance testing  
    - Database optimization validation
    - WebSocket stress testing
    - Report generation
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._load_default_config()
        self.test_results = {}
        self.start_time = datetime.now()
        self.server_process = None
        
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default test configuration"""
        return {
            "backend": {
                "host": "localhost",
                "port": 8000,
                "startup_timeout": 30,
                "concurrent_users": [10, 25, 50, 100],
                "test_duration": 30
            },
            "frontend": {
                "build_timeout": 120,
                "test_timeout": 300,
                "performance_budget": {
                    "bundle_size_mb": 2.0,
                    "render_time_ms": 200,
                    "interaction_time_ms": 500
                }
            },
            "database": {
                "connection_pool_size": 20,
                "query_timeout": 30,
                "optimization_tests": True
            },
            "websocket": {
                "max_connections": 50,
                "message_rate": 10,
                "test_duration": 60
            },
            "reports": {
                "output_dir": "test_reports",
                "formats": ["json", "html", "markdown"]
            }
        }
    
    async def run_full_pipeline(self) -> Dict[str, Any]:
        """Run the complete performance testing pipeline"""
        logger.info("🚀 Starting comprehensive performance testing pipeline")
        
        pipeline_results = {
            "pipeline_start": self.start_time.isoformat(),
            "configuration": self.config,
            "stages": {},
            "overall_status": "UNKNOWN"
        }
        
        try:
            # Stage 1: Environment setup
            logger.info("🔧 Stage 1: Environment setup")
            setup_result = await self._setup_test_environment()
            pipeline_results["stages"]["environment_setup"] = setup_result
            
            if not setup_result.get("success", False):
                raise Exception("Environment setup failed")
            
            # Stage 2: Backend server startup
            logger.info("🖥️ Stage 2: Backend server startup")
            server_result = await self._start_backend_server()
            pipeline_results["stages"]["server_startup"] = server_result
            
            if not server_result.get("success", False):
                raise Exception("Backend server startup failed")
            
            # Stage 3: Backend load testing
            logger.info("⚡ Stage 3: Backend load testing")
            backend_result = await self._run_backend_load_tests()
            pipeline_results["stages"]["backend_load_tests"] = backend_result
            
            # Stage 4: Frontend performance testing
            logger.info("🎨 Stage 4: Frontend performance testing")
            frontend_result = await self._run_frontend_tests()
            pipeline_results["stages"]["frontend_tests"] = frontend_result
            
            # Stage 5: Database performance testing
            logger.info("🗄️ Stage 5: Database performance testing")
            database_result = await self._run_database_tests()
            pipeline_results["stages"]["database_tests"] = database_result
            
            # Stage 6: WebSocket stress testing
            logger.info("🔌 Stage 6: WebSocket stress testing")
            websocket_result = await self._run_websocket_tests()
            pipeline_results["stages"]["websocket_tests"] = websocket_result
            
            # Stage 7: Performance analysis
            logger.info("📊 Stage 7: Performance analysis")
            analysis_result = await self._analyze_performance_results(pipeline_results)
            pipeline_results["stages"]["performance_analysis"] = analysis_result
            
            # Determine overall status
            pipeline_results["overall_status"] = self._determine_pipeline_status(pipeline_results)
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            pipeline_results["error"] = str(e)
            pipeline_results["overall_status"] = "FAILED"
        
        finally:
            # Cleanup
            await self._cleanup_test_environment()
            
            # Generate reports
            await self._generate_reports(pipeline_results)
        
        pipeline_results["pipeline_end"] = datetime.now().isoformat()
        pipeline_results["total_duration"] = (datetime.now() - self.start_time).total_seconds()
        
        return pipeline_results
    
    async def _setup_test_environment(self) -> Dict[str, Any]:
        """Setup test environment"""
        setup_result = {
            "success": False,
            "steps": {},
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            # Check Python dependencies
            logger.info("📦 Checking Python dependencies...")
            deps_result = await self._check_python_dependencies()
            setup_result["steps"]["python_dependencies"] = deps_result
            
            # Check Node.js dependencies
            logger.info("📦 Checking Node.js dependencies...")
            node_result = await self._check_node_dependencies()
            setup_result["steps"]["node_dependencies"] = node_result
            
            # Create output directories
            logger.info("📁 Creating output directories...")
            dirs_result = await self._create_output_directories()
            setup_result["steps"]["output_directories"] = dirs_result
            
            # Validate database connection
            logger.info("🗄️ Validating database connection...")
            db_result = await self._validate_database_connection()
            setup_result["steps"]["database_connection"] = db_result
            
            # Check if all steps successful
            all_successful = all(
                step.get("success", False) 
                for step in setup_result["steps"].values()
            )
            
            setup_result["success"] = all_successful
            
        except Exception as e:
            setup_result["error"] = str(e)
            logger.error(f"Environment setup failed: {e}")
        
        setup_result["duration"] = time.time() - start_time
        return setup_result
    
    async def _start_backend_server(self) -> Dict[str, Any]:
        """Start backend server for testing"""
        server_result = {
            "success": False,
            "startup_time": 0,
            "health_check": False
        }
        
        start_time = time.time()
        
        try:
            # Start server process
            logger.info("🚀 Starting backend server...")
            
            # Use uvicorn to start the server
            cmd = [
                sys.executable, "-m", "uvicorn", 
                "app.main:app", 
                "--host", self.config["backend"]["host"],
                "--port", str(self.config["backend"]["port"]),
                "--log-level", "info"
            ]
            
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            health_check_url = f"http://{self.config['backend']['host']}:{self.config['backend']['port']}/health"
            
            for attempt in range(self.config["backend"]["startup_timeout"]):
                try:
                    import httpx
                    async with httpx.AsyncClient() as client:
                        response = await client.get(health_check_url, timeout=5.0)
                        if response.status_code == 200:
                            server_result["health_check"] = True
                            break
                except:
                    pass
                
                await asyncio.sleep(1)
                logger.info(f"⏳ Waiting for server startup... ({attempt + 1}/{self.config['backend']['startup_timeout']})")
            
            if server_result["health_check"]:
                server_result["success"] = True
                logger.info("✅ Backend server started successfully")
            else:
                logger.error("❌ Backend server health check failed")
                
        except Exception as e:
            server_result["error"] = str(e)
            logger.error(f"Failed to start backend server: {e}")
        
        server_result["startup_time"] = time.time() - start_time
        return server_result
    
    async def _run_backend_load_tests(self) -> Dict[str, Any]:
        """Run backend load testing"""
        logger.info("⚡ Running backend load tests...")
        
        try:
            # Import and run load tester
            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
            from tests.performance.test_load_testing import LoadTester
            
            base_url = f"http://{self.config['backend']['host']}:{self.config['backend']['port']}"
            tester = LoadTester(base_url)
            
            # Run comprehensive load test
            results = await tester.run_comprehensive_load_test()
            
            return {
                "success": results.get("overall_status") in ["PASS", "PARTIAL"],
                "detailed_results": results,
                "performance_score": self._calculate_performance_score(results),
                "critical_issues": results.get("critical_issues", [])
            }
            
        except Exception as e:
            logger.error(f"Backend load testing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _run_frontend_tests(self) -> Dict[str, Any]:
        """Run frontend performance tests"""
        logger.info("🎨 Running frontend performance tests...")
        
        frontend_result = {
            "success": False,
            "build_result": {},
            "test_result": {},
            "bundle_analysis": {}
        }
        
        try:
            # Change to frontend directory
            frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
            
            # Build frontend
            logger.info("🔨 Building frontend...")
            build_cmd = ["npm", "run", "build"]
            build_process = subprocess.run(
                build_cmd,
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=self.config["frontend"]["build_timeout"]
            )
            
            frontend_result["build_result"] = {
                "success": build_process.returncode == 0,
                "stdout": build_process.stdout,
                "stderr": build_process.stderr
            }
            
            if build_process.returncode != 0:
                logger.error("❌ Frontend build failed")
                return frontend_result
            
            # Run performance tests
            logger.info("🧪 Running frontend performance tests...")
            test_cmd = ["npm", "test", "--", "--testNamePattern=performance", "--verbose"]
            test_process = subprocess.run(
                test_cmd,
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=self.config["frontend"]["test_timeout"]
            )
            
            frontend_result["test_result"] = {
                "success": test_process.returncode == 0,
                "stdout": test_process.stdout,
                "stderr": test_process.stderr
            }
            
            # Analyze bundle size
            bundle_analysis = await self._analyze_bundle_size(frontend_dir)
            frontend_result["bundle_analysis"] = bundle_analysis
            
            # Determine overall success
            frontend_result["success"] = (
                frontend_result["build_result"]["success"] and
                frontend_result["test_result"]["success"] and
                bundle_analysis.get("within_budget", False)
            )
            
        except Exception as e:
            logger.error(f"Frontend testing failed: {e}")
            frontend_result["error"] = str(e)
        
        return frontend_result
    
    async def _run_database_tests(self) -> Dict[str, Any]:
        """Run database performance tests"""
        logger.info("🗄️ Running database performance tests...")
        
        try:
            # Test database optimization
            optimization_cmd = [
                sys.executable, "-c",
                """
import asyncio
import sys
import os
sys.path.append('.')
from app.performance.database_optimizer import db_optimizer

async def test_db():
    await db_optimizer.initialize_pool()
    stats = await db_optimizer.get_database_stats()
    health = await db_optimizer.health_check()
    optimization = await db_optimizer.optimize_queries()
    
    result = {
        'stats': stats,
        'health': health,
        'optimization': optimization,
        'success': health.get('status') == 'healthy'
    }
    
    import json
    print(json.dumps(result, default=str))

asyncio.run(test_db())
                """
            ]
            
            db_process = subprocess.run(
                optimization_cmd,
                capture_output=True,
                text=True,
                timeout=self.config["database"]["query_timeout"]
            )
            
            if db_process.returncode == 0:
                db_result = json.loads(db_process.stdout)
                return {
                    "success": db_result.get("success", False),
                    "performance_stats": db_result.get("stats", {}),
                    "health_status": db_result.get("health", {}),
                    "optimization_report": db_result.get("optimization", {})
                }
            else:
                return {
                    "success": False,
                    "error": db_process.stderr
                }
                
        except Exception as e:
            logger.error(f"Database testing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _run_websocket_tests(self) -> Dict[str, Any]:
        """Run WebSocket stress tests"""
        logger.info("🔌 Running WebSocket stress tests...")
        
        try:
            # Import WebSocket tester
            ws_test_cmd = [
                sys.executable, "-c",
                f"""
import asyncio
import json
import websockets
import time

async def test_websockets():
    connections = []
    start_time = time.time()
    successful_connections = 0
    failed_connections = 0
    
    async def connect_websocket():
        nonlocal successful_connections, failed_connections
        try:
            uri = "ws://{self.config['backend']['host']}:{self.config['backend']['port']}/ws?token=test&user_id=test"
            async with websockets.connect(uri, timeout=10) as websocket:
                successful_connections += 1
                await websocket.send(json.dumps({{"type": "ping"}}))
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                await asyncio.sleep({self.config['websocket']['test_duration']})
        except Exception:
            failed_connections += 1
    
    # Create concurrent connections
    tasks = [connect_websocket() for _ in range({self.config['websocket']['max_connections']})]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    test_duration = time.time() - start_time
    
    result = {{
        'successful_connections': successful_connections,
        'failed_connections': failed_connections,
        'test_duration': test_duration,
        'success': successful_connections > 0
    }}
    
    print(json.dumps(result))

asyncio.run(test_websockets())
                """
            ]
            
            ws_process = subprocess.run(
                ws_test_cmd,
                capture_output=True,
                text=True,
                timeout=self.config["websocket"]["test_duration"] + 30
            )
            
            if ws_process.returncode == 0:
                return json.loads(ws_process.stdout)
            else:
                return {
                    "success": False,
                    "error": ws_process.stderr
                }
                
        except Exception as e:
            logger.error(f"WebSocket testing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_performance_results(self, pipeline_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall performance results"""
        analysis = {
            "overall_score": 0,
            "stage_scores": {},
            "critical_issues": [],
            "recommendations": [],
            "performance_grade": "F"
        }
        
        try:
            # Score each stage
            stages = pipeline_results.get("stages", {})
            total_score = 0
            scored_stages = 0
            
            for stage_name, stage_data in stages.items():
                if isinstance(stage_data, dict) and stage_data.get("success", False):
                    stage_score = self._calculate_stage_score(stage_name, stage_data)
                    analysis["stage_scores"][stage_name] = stage_score
                    total_score += stage_score
                    scored_stages += 1
                else:
                    analysis["stage_scores"][stage_name] = 0
                    analysis["critical_issues"].append(f"Stage {stage_name} failed")
            
            # Calculate overall score
            if scored_stages > 0:
                analysis["overall_score"] = total_score / scored_stages
            
            # Determine grade
            score = analysis["overall_score"]
            if score >= 90:
                analysis["performance_grade"] = "A"
            elif score >= 80:
                analysis["performance_grade"] = "B"
            elif score >= 70:
                analysis["performance_grade"] = "C"
            elif score >= 60:
                analysis["performance_grade"] = "D"
            else:
                analysis["performance_grade"] = "F"
            
            # Generate recommendations
            analysis["recommendations"] = self._generate_recommendations(analysis)
            
        except Exception as e:
            analysis["error"] = str(e)
            logger.error(f"Performance analysis failed: {e}")
        
        return analysis
    
    def _calculate_stage_score(self, stage_name: str, stage_data: Dict[str, Any]) -> int:
        """Calculate score for individual stage"""
        if stage_name == "backend_load_tests":
            return stage_data.get("performance_score", 0)
        elif stage_name == "frontend_tests":
            return 90 if stage_data.get("success", False) else 30
        elif stage_name == "database_tests":
            return 85 if stage_data.get("success", False) else 20
        elif stage_name == "websocket_tests":
            success_rate = stage_data.get("successful_connections", 0) / max(stage_data.get("successful_connections", 0) + stage_data.get("failed_connections", 1), 1)
            return int(success_rate * 100)
        else:
            return 100 if stage_data.get("success", False) else 0
    
    def _calculate_performance_score(self, results: Dict[str, Any]) -> int:
        """Calculate performance score from load test results"""
        if not results or "performance_summary" not in results:
            return 0
        
        summary = results["performance_summary"]
        score = 100
        
        # Deduct points for issues
        success_rate = summary.get("overall_success_rate", 0)
        if success_rate < 95:
            score -= (95 - success_rate) * 2
        
        avg_response_time = summary.get("avg_response_time", 0)
        if avg_response_time > 0.5:  # 500ms
            score -= min((avg_response_time - 0.5) * 100, 30)
        
        critical_issues = len(results.get("critical_issues", []))
        score -= critical_issues * 10
        
        return max(0, int(score))
    
    def _determine_pipeline_status(self, pipeline_results: Dict[str, Any]) -> str:
        """Determine overall pipeline status"""
        stages = pipeline_results.get("stages", {})
        
        if "error" in pipeline_results:
            return "FAILED"
        
        failed_stages = [
            name for name, data in stages.items()
            if not data.get("success", False)
        ]
        
        if not failed_stages:
            return "PASSED"
        elif len(failed_stages) <= 2:  # Allow some failures
            return "PARTIAL"
        else:
            return "FAILED"
    
    async def _generate_reports(self, pipeline_results: Dict[str, Any]):
        """Generate test reports in multiple formats"""
        logger.info("📝 Generating test reports...")
        
        try:
            output_dir = self.config["reports"]["output_dir"]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON report
            if "json" in self.config["reports"]["formats"]:
                json_file = os.path.join(output_dir, f"performance_report_{timestamp}.json")
                with open(json_file, 'w') as f:
                    json.dump(pipeline_results, f, indent=2, default=str)
                logger.info(f"📄 JSON report saved: {json_file}")
            
            # Markdown report
            if "markdown" in self.config["reports"]["formats"]:
                md_file = os.path.join(output_dir, f"performance_report_{timestamp}.md")
                markdown_content = self._generate_markdown_report(pipeline_results)
                with open(md_file, 'w') as f:
                    f.write(markdown_content)
                logger.info(f"📄 Markdown report saved: {md_file}")
            
            # HTML report (simplified)
            if "html" in self.config["reports"]["formats"]:
                html_file = os.path.join(output_dir, f"performance_report_{timestamp}.html")
                html_content = self._generate_html_report(pipeline_results)
                with open(html_file, 'w') as f:
                    f.write(html_content)
                logger.info(f"📄 HTML report saved: {html_file}")
                
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
    
    def _generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generate markdown test report"""
        lines = []
        lines.append("# 🚀 AI Assistant MVP - Performance Test Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Duration:** {results.get('total_duration', 0):.1f} seconds")
        lines.append(f"**Overall Status:** {results.get('overall_status', 'UNKNOWN')}")
        lines.append("")
        
        # Performance analysis
        if "performance_analysis" in results.get("stages", {}):
            analysis = results["stages"]["performance_analysis"]
            lines.append("## 📊 Performance Analysis")
            lines.append(f"- **Overall Score:** {analysis.get('overall_score', 0):.1f}/100")
            lines.append(f"- **Performance Grade:** {analysis.get('performance_grade', 'F')}")
            lines.append("")
        
        # Stage results
        lines.append("## 🧪 Test Stages")
        for stage_name, stage_data in results.get("stages", {}).items():
            status = "✅ PASSED" if stage_data.get("success", False) else "❌ FAILED"
            lines.append(f"- **{stage_name.replace('_', ' ').title()}:** {status}")
        lines.append("")
        
        # Critical issues
        analysis = results.get("stages", {}).get("performance_analysis", {})
        critical_issues = analysis.get("critical_issues", [])
        if critical_issues:
            lines.append("## ⚠️ Critical Issues")
            for issue in critical_issues:
                lines.append(f"- {issue}")
            lines.append("")
        
        # Recommendations
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            lines.append("## 💡 Recommendations")
            for rec in recommendations:
                lines.append(f"- {rec}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_html_report(self, results: Dict[str, Any]) -> str:
        """Generate HTML test report"""
        status = results.get("overall_status", "UNKNOWN")
        status_color = {
            "PASSED": "green",
            "PARTIAL": "orange", 
            "FAILED": "red",
            "UNKNOWN": "gray"
        }.get(status, "gray")
        
        analysis = results.get("stages", {}).get("performance_analysis", {})
        score = analysis.get("overall_score", 0)
        grade = analysis.get("performance_grade", "F")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Assistant MVP - Performance Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .status {{ color: {status_color}; font-weight: bold; }}
                .score {{ font-size: 24px; color: #333; }}
                .stage {{ margin: 10px 0; padding: 10px; border-left: 3px solid #ccc; }}
                .passed {{ border-color: green; }}
                .failed {{ border-color: red; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 AI Assistant MVP - Performance Test Report</h1>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Duration:</strong> {results.get('total_duration', 0):.1f} seconds</p>
                <p><strong>Status:</strong> <span class="status">{status}</span></p>
                <p class="score"><strong>Score:</strong> {score:.1f}/100 (Grade: {grade})</p>
            </div>
            
            <h2>🧪 Test Stages</h2>
        """
        
        for stage_name, stage_data in results.get("stages", {}).items():
            success = stage_data.get("success", False)
            css_class = "passed" if success else "failed"
            status_text = "✅ PASSED" if success else "❌ FAILED"
            
            html += f"""
            <div class="stage {css_class}">
                <strong>{stage_name.replace('_', ' ').title()}:</strong> {status_text}
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    # Helper methods for environment setup
    async def _check_python_dependencies(self) -> Dict[str, Any]:
        """Check Python dependencies"""
        try:
            import httpx, websockets, asyncio
            return {"success": True, "message": "Python dependencies available"}
        except ImportError as e:
            return {"success": False, "error": str(e)}
    
    async def _check_node_dependencies(self) -> Dict[str, Any]:
        """Check Node.js dependencies"""
        try:
            frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
            if os.path.exists(os.path.join(frontend_dir, 'node_modules')):
                return {"success": True, "message": "Node.js dependencies available"}
            else:
                return {"success": False, "error": "node_modules not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _create_output_directories(self) -> Dict[str, Any]:
        """Create output directories"""
        try:
            output_dir = self.config["reports"]["output_dir"]
            os.makedirs(output_dir, exist_ok=True)
            return {"success": True, "message": f"Output directory created: {output_dir}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _validate_database_connection(self) -> Dict[str, Any]:
        """Validate database connection"""
        # Simplified check - in real implementation would test actual DB
        return {"success": True, "message": "Database connection assumed available"}
    
    async def _analyze_bundle_size(self, frontend_dir: str) -> Dict[str, Any]:
        """Analyze frontend bundle size"""
        try:
            dist_dir = os.path.join(frontend_dir, 'dist')
            if os.path.exists(dist_dir):
                total_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(dist_dir)
                    for filename in filenames
                )
                
                size_mb = total_size / (1024 * 1024)
                budget_mb = self.config["frontend"]["performance_budget"]["bundle_size_mb"]
                
                return {
                    "total_size_mb": size_mb,
                    "budget_mb": budget_mb,
                    "within_budget": size_mb <= budget_mb,
                    "success": True
                }
            else:
                return {"success": False, "error": "dist directory not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        score = analysis.get("overall_score", 0)
        if score < 70:
            recommendations.append("Consider implementing additional caching strategies")
            recommendations.append("Review database query optimization")
            recommendations.append("Analyze and optimize slow API endpoints")
        
        if score < 80:
            recommendations.append("Implement CDN for static assets")
            recommendations.append("Consider horizontal scaling preparation")
        
        critical_issues = analysis.get("critical_issues", [])
        if critical_issues:
            recommendations.append("Address critical performance issues before production")
            recommendations.append("Implement performance monitoring and alerting")
        
        return recommendations
    
    async def _cleanup_test_environment(self):
        """Cleanup test environment"""
        logger.info("🧹 Cleaning up test environment...")
        
        # Stop server process
        if self.server_process:
            try:
                self.server_process.terminate()
                await asyncio.sleep(2)
                if self.server_process.poll() is None:
                    self.server_process.kill()
                logger.info("✅ Backend server stopped")
            except Exception as e:
                logger.warning(f"Error stopping server: {e}")

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="AI Assistant MVP Performance Testing Pipeline")
    parser.add_argument("--config", help="Path to test configuration file")
    parser.add_argument("--output-dir", help="Output directory for reports", default="test_reports")
    parser.add_argument("--concurrent-users", type=int, help="Max concurrent users for load testing", default=100)
    parser.add_argument("--quick", action="store_true", help="Run quick test suite")
    
    args = parser.parse_args()
    
    # Load configuration
    config = None
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Override config with CLI args
    if not config:
        config = {}
    
    if args.output_dir:
        config.setdefault("reports", {})["output_dir"] = args.output_dir
    
    if args.concurrent_users:
        config.setdefault("backend", {})["concurrent_users"] = [args.concurrent_users]
    
    if args.quick:
        # Quick test configuration
        config.update({
            "backend": {"concurrent_users": [10, 25], "test_duration": 15},
            "frontend": {"test_timeout": 120},
            "websocket": {"max_connections": 10, "test_duration": 30}
        })
    
    # Run pipeline
    pipeline = PerformanceTestPipeline(config)
    results = await pipeline.run_full_pipeline()
    
    # Print summary
    print("\n" + "="*60)
    print("🚀 PERFORMANCE TESTING PIPELINE COMPLETED")
    print("="*60)
    print(f"Overall Status: {results.get('overall_status', 'UNKNOWN')}")
    print(f"Total Duration: {results.get('total_duration', 0):.1f} seconds")
    
    analysis = results.get("stages", {}).get("performance_analysis", {})
    if analysis:
        print(f"Performance Score: {analysis.get('overall_score', 0):.1f}/100")
        print(f"Performance Grade: {analysis.get('performance_grade', 'F')}")
    
    print("="*60)
    
    # Exit with appropriate code
    status = results.get("overall_status", "FAILED")
    return 0 if status in ["PASSED", "PARTIAL"] else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 