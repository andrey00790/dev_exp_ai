#!/usr/bin/env python3
"""
AI Code Analysis Demo - Interactive demonstration of intelligent code analysis features.

This demo showcases:
- 🔍 Code quality analysis with AI insights
- 🔧 Smart refactoring suggestions
- ⚡ Performance optimization recommendations
- 🛡️ Security vulnerability detection
- 📊 Project health assessment

Usage:
    python src/demos/demo_ai_code_analysis.py
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from domain.ai_analysis.ai_code_analyzer import analyze_code_file, analyze_project_structure
from domain.ai_analysis.smart_refactoring_engine import analyze_refactoring_opportunities
from domain.code_optimization.ai_performance_optimizer import analyze_file_performance

# Sample code for analysis
SAMPLE_PYTHON_CODE = '''
import re
import time
import requests

def process_data(data):
    # TODO: This function is too long and complex
    result = []
    for item in data:
        if item['type'] == 'user':
            for record in item['records']:
                if record['status'] == 'active':
                    user_data = requests.get(f"http://api.example.com/user/{record['id']}")
                    if user_data.status_code == 200:
                        result.append(user_data.json())
                        time.sleep(0.1)  # Rate limiting
    
    # String concatenation in loop
    report = ""
    for item in result:
        report += f"User: {item['name']}, Email: {item['email']}\\n"
    
    # Magic numbers
    if len(result) > 50:
        print("Too many results")
    
    # Inefficient membership testing
    active_users = ['alice', 'bob', 'charlie']
    for user in result:
        if user['name'] in active_users:
            print(f"Active user found: {user['name']}")
    
    return report

class DataProcessor:
    def __init__(self):
        self.password = "hardcoded_secret_123"  # Security issue
    
    def query_database(self, user_input):
        # SQL injection vulnerability
        query = f"SELECT * FROM users WHERE name = '{user_input}'"
        return self.execute_query(query)
    
    def execute_query(self, query):
        # Simulated database execution
        return []

def complex_algorithm(data):
    # Nested loops - O(n²) complexity
    results = []
    for i in range(len(data)):
        for j in range(len(data)):
            if data[i] != data[j]:
                results.append((data[i], data[j]))
    return results

# Function without type hints
def calculate_score(user_data, weights):
    score = 0
    for key, value in user_data.items():
        if key in weights:
            score += value * weights[key]
    return score
'''

class AICodeAnalysisDemo:
    """Interactive demo for AI Code Analysis features"""
    
    def __init__(self):
        self.sample_file_path = "demo_sample.py"
    
    async def run(self):
        """Run the interactive demo"""
        
        print("🤖 AI Code Analysis Demo")
        print("=" * 50)
        print("Welcome to the AI-powered code analysis demonstration!")
        print()
        
        while True:
            await self.show_menu()
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == '1':
                await self.demo_code_quality_analysis()
            elif choice == '2':
                await self.demo_refactoring_suggestions()
            elif choice == '3':
                await self.demo_performance_optimization()
            elif choice == '4':
                await self.demo_security_analysis()
            elif choice == '5':
                await self.demo_project_health()
            elif choice == '6':
                print("\n👋 Thanks for using AI Code Analysis Demo!")
                break
            else:
                print("\n❌ Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")
    
    async def show_menu(self):
        """Display the main menu"""
        
        print("\n" + "="*50)
        print("🔍 AI Code Analysis Features")
        print("="*50)
        print("1. 📊 Code Quality Analysis")
        print("2. 🔧 Smart Refactoring Suggestions") 
        print("3. ⚡ Performance Optimization")
        print("4. 🛡️ Security Vulnerability Detection")
        print("5. 🏥 Project Health Assessment")
        print("6. 🚪 Exit")
    
    async def demo_code_quality_analysis(self):
        """Demonstrate code quality analysis"""
        
        print("\n🔍 Code Quality Analysis Demo")
        print("-" * 40)
        
        print("Analyzing sample Python code for quality issues...")
        
        try:
            # Analyze the sample code
            result = await analyze_code_file(self.sample_file_path, SAMPLE_PYTHON_CODE)
            
            print(f"\n📋 Analysis Results for {result.file_path}")
            print(f"Language: {result.language}")
            print(f"Quality Score: {result.quality_score:.1f}/100")
            print(f"Maintainability Index: {result.maintainability_index:.1f}")
            
            # Show complexity metrics
            print(f"\n📊 Code Metrics:")
            metrics = result.metrics
            print(f"  • Total Lines: {metrics.get('total_lines', 0)}")
            print(f"  • Code Lines: {metrics.get('code_lines', 0)}")
            print(f"  • Comment Lines: {metrics.get('comment_lines', 0)}")
            print(f"  • Functions: {metrics.get('functions', 0)}")
            print(f"  • Classes: {metrics.get('classes', 0)}")
            print(f"  • Complexity: {metrics.get('complexity', 0)}")
            
            # Show issues found
            if result.issues:
                print(f"\n⚠️ Issues Found ({len(result.issues)}):")
                for i, issue in enumerate(result.issues[:5], 1):
                    print(f"  {i}. [{issue.severity.value.upper()}] {issue.title}")
                    print(f"     Line {issue.line_number}: {issue.description}")
                    if issue.suggestion:
                        print(f"     💡 Suggestion: {issue.suggestion}")
                    print()
                
                if len(result.issues) > 5:
                    print(f"     ... and {len(result.issues) - 5} more issues")
            else:
                print("\n✅ No quality issues found!")
            
            # Show AI insights
            if result.ai_insights:
                print(f"\n🤖 AI Insights:")
                insights = result.ai_insights
                if 'recommendations' in insights:
                    for rec in insights['recommendations']:
                        print(f"  • {rec}")
                
                if 'patterns' in insights:
                    print(f"\n🔍 Code Patterns Detected:")
                    for pattern in insights['patterns']:
                        print(f"  • {pattern}")
        
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
    
    async def demo_refactoring_suggestions(self):
        """Demonstrate refactoring suggestions"""
        
        print("\n🔧 Smart Refactoring Suggestions Demo")
        print("-" * 40)
        
        print("Analyzing code for refactoring opportunities...")
        
        try:
            plan = await analyze_refactoring_opportunities(self.sample_file_path, SAMPLE_PYTHON_CODE)
            
            print(f"\n📋 Refactoring Plan for {plan.file_path}")
            print(f"Total Operations: {len(plan.operations)}")
            print(f"Estimated Time: {plan.total_time}")
            print(f"Success Probability: {plan.success_probability:.1%}")
            
            if plan.operations:
                print(f"\n🔧 Refactoring Suggestions:")
                
                for i, op in enumerate(plan.operations[:5], 1):
                    print(f"\n{i}. {op.title}")
                    print(f"   Type: {op.type.value}")
                    print(f"   Description: {op.description}")
                    print(f"   Complexity: {op.complexity.value}")
                    print(f"   Confidence: {op.confidence:.1%}")
                    print(f"   Estimated Time: {op.estimated_time}")
                    
                    print(f"   📈 Benefits:")
                    for benefit in op.benefits:
                        print(f"     • {benefit}")
                    
                    if op.original_code:
                        print(f"   📝 Original: {op.original_code[:50]}...")
                    if op.refactored_code:
                        print(f"   ✨ Refactored: {op.refactored_code[:50]}...")
                
                if len(plan.operations) > 5:
                    print(f"\n... and {len(plan.operations) - 5} more suggestions")
            else:
                print("\n✅ No refactoring opportunities found!")
        
        except Exception as e:
            print(f"❌ Refactoring analysis failed: {e}")
    
    async def demo_performance_optimization(self):
        """Demonstrate performance optimization"""
        
        print("\n⚡ Performance Optimization Demo")
        print("-" * 40)
        
        print("Analyzing code for performance issues...")
        
        try:
            report = await analyze_file_performance(self.sample_file_path, SAMPLE_PYTHON_CODE)
            
            print(f"\n📋 Performance Report for {report.file_path}")
            print(f"Total Issues: {report.total_issues}")
            print(f"Critical Issues: {report.critical_issues}")
            print(f"Estimated Speedup: {report.estimated_speedup}")
            print(f"Priority: {report.priority}")
            
            if report.issues:
                print(f"\n⚡ Performance Issues Found:")
                
                for i, issue in enumerate(report.issues[:5], 1):
                    print(f"\n{i}. {issue.title}")
                    print(f"   Type: {issue.type.value}")
                    print(f"   Impact: {issue.impact_level.value}")
                    print(f"   Line {issue.line_number}: {issue.description}")
                    print(f"   Expected Improvement: {issue.expected_improvement}")
                    print(f"   Implementation Effort: {issue.effort}")
                    print(f"   Confidence: {issue.confidence:.1%}")
                    
                    if issue.current_code:
                        print(f"   📝 Current: {issue.current_code[:50]}...")
                    if issue.optimized_code:
                        print(f"   ⚡ Optimized: {issue.optimized_code[:50]}...")
                
                if len(report.issues) > 5:
                    print(f"\n... and {len(report.issues) - 5} more issues")
            else:
                print("\n✅ No performance issues found!")
        
        except Exception as e:
            print(f"❌ Performance analysis failed: {e}")
    
    async def demo_security_analysis(self):
        """Demonstrate security vulnerability detection"""
        
        print("\n🛡️ Security Analysis Demo")
        print("-" * 40)
        
        print("Scanning code for security vulnerabilities...")
        
        try:
            # Analyze for security issues specifically
            result = await analyze_code_file(self.sample_file_path, SAMPLE_PYTHON_CODE)
            
            # Filter security issues
            security_issues = [issue for issue in result.issues if issue.type.value == 'security']
            
            print(f"\n🔍 Security Scan Results")
            print(f"Security Issues Found: {len(security_issues)}")
            
            if security_issues:
                print(f"\n🚨 Security Vulnerabilities:")
                
                for i, issue in enumerate(security_issues, 1):
                    print(f"\n{i}. {issue.title}")
                    print(f"   Severity: {issue.severity.value.upper()}")
                    print(f"   Line {issue.line_number}: {issue.description}")
                    print(f"   💡 Suggestion: {issue.suggestion}")
                    
                    # Show affected code
                    if hasattr(issue, 'code_snippet') and issue.code_snippet:
                        print(f"   📝 Code: {issue.code_snippet}")
                
                print(f"\n⚠️ Recommendation: Address these security issues immediately!")
            else:
                print("\n✅ No security vulnerabilities detected!")
        
        except Exception as e:
            print(f"❌ Security analysis failed: {e}")
    
    async def demo_project_health(self):
        """Demonstrate project health assessment"""
        
        print("\n🏥 Project Health Assessment Demo")
        print("-" * 40)
        
        print("Analyzing project health (using current directory as sample)...")
        
        try:
            # Use current project directory
            project_path = str(Path.cwd())
            health_summary = await analyze_project_structure(project_path)
            
            if "error" in health_summary:
                print(f"❌ Project analysis failed: {health_summary['error']}")
                return
            
            print(f"\n📊 Project Health Summary")
            print(f"Project Path: {project_path}")
            print(f"Files Analyzed: {health_summary['files_analyzed']}")
            print(f"Average Quality Score: {health_summary['average_quality_score']}/100")
            print(f"Health Grade: {health_summary['health_grade']}")
            print(f"Total Issues: {health_summary['total_issues']}")
            
            if 'critical_issues' in health_summary:
                print(f"Critical Issues: {health_summary['critical_issues']}")
            if 'high_priority_issues' in health_summary:
                print(f"High Priority Issues: {health_summary['high_priority_issues']}")
            
            print(f"\n💡 Recommendations:")
            for recommendation in health_summary['recommendations']:
                print(f"  • {recommendation}")
            
            # Health grade explanation
            grade = health_summary['health_grade']
            if grade == 'A':
                print(f"\n🎉 Excellent! Your code quality is outstanding.")
            elif grade == 'B':
                print(f"\n👍 Good code quality with room for improvement.")
            elif grade == 'C':
                print(f"\n⚠️ Moderate code quality - consider addressing issues.")
            else:
                print(f"\n🚨 Code quality needs significant improvement.")
        
        except Exception as e:
            print(f"❌ Project health analysis failed: {e}")

async def main():
    """Main demo function"""
    
    demo = AICodeAnalysisDemo()
    await demo.run()

if __name__ == "__main__":
    # Run the demo
    asyncio.run(main()) 