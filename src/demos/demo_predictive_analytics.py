"""
🔮 Predictive Analytics Engine Demo

Comprehensive demonstration of ML-powered predictive analytics capabilities.
Shows development time predictions, system status, and future capabilities.

Phase 4B - Advanced Intelligence Component Demo

Usage:
    python src/demos/demo_predictive_analytics.py
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from domain.core.predictive_analytics_engine import (
    get_analytics_engine,
    PredictiveAnalyticsEngine,
    PredictionType,
    PredictionConfidence
)

class PredictiveAnalyticsDemo:
    """Demo class for showcasing predictive analytics capabilities"""
    
    def __init__(self):
        self.engine = None
        self.demo_results = []
    
    async def setup(self):
        """Initialize the analytics engine"""
        print("🔮 Initializing Predictive Analytics Engine...")
        self.engine = await get_analytics_engine()
        print("✅ Engine initialized successfully!")
        print()
    
    async def run_all_demos(self):
        """Run all demonstration scenarios"""
        await self.setup()
        
        print("=" * 80)
        print("🔮 PREDICTIVE ANALYTICS ENGINE - COMPREHENSIVE DEMO")
        print("=" * 80)
        print()
        
        # Core functionality demos
        await self.demo_development_time_prediction()
        await self.demo_various_project_types()
        await self.demo_team_size_impact()
        await self.demo_complexity_analysis()
        
        # System capabilities
        await self.demo_engine_metrics()
        await self.demo_multiple_predictions()
        await self.demo_performance_testing()
        
        # Future capabilities preview
        await self.demo_future_capabilities()
        
        # Summary
        await self.show_demo_summary()
    
    async def demo_development_time_prediction(self):
        """Demonstrate basic development time prediction"""
        print("📊 DEVELOPMENT TIME PREDICTION DEMO")
        print("-" * 50)
        
        # Sample project data
        project_data = {
            'complexity': 0.7,
            'lines_of_code': 8000,
            'team': {
                'size': 3,
                'avg_experience_years': 4
            },
            'requirements': [
                'User authentication and authorization',
                'Real-time data dashboard', 
                'API integration with third-party services',
                'Automated report generation',
                'Mobile-responsive UI'
            ],
            'project_age_days': 5
        }
        
        print("Project Details:")
        print(f"  • Complexity Score: {project_data['complexity']}")
        print(f"  • Lines of Code: {project_data['lines_of_code']:,}")
        print(f"  • Team Size: {project_data['team']['size']}")
        print(f"  • Team Experience: {project_data['team']['avg_experience_years']} years avg")
        print(f"  • Requirements: {len(project_data['requirements'])}")
        print()
        
        print("🔮 Making prediction...")
        start_time = time.time()
        
        result = await self.engine.predict_development_time(project_data)
        
        prediction_time = (time.time() - start_time) * 1000
        
        print("✅ Prediction Results:")
        print(f"  • Predicted Development Time: {result.predicted_value} days")
        print(f"  • Confidence Level: {result.confidence.value} ({result.confidence_score:.2%})")
        print(f"  • Prediction Time: {prediction_time:.1f}ms")
        print()
        
        if result.recommendations:
            print("💡 Recommendations:")
            for i, rec in enumerate(result.recommendations, 1):
                print(f"  {i}. {rec}")
        print()
        
        self.demo_results.append({
            'type': 'development_time',
            'predicted_value': result.predicted_value,
            'confidence': result.confidence_score,
            'prediction_time_ms': prediction_time
        })
    
    async def demo_various_project_types(self):
        """Demonstrate predictions for different project types"""
        print("🎯 PROJECT TYPE COMPARISON DEMO")
        print("-" * 50)
        
        project_scenarios = [
            {
                'name': 'Simple CRUD App',
                'data': {
                    'complexity': 0.3,
                    'lines_of_code': 2000,
                    'team': {'size': 1, 'avg_experience_years': 3},
                    'requirements': ['Basic CRUD operations', 'Simple UI']
                }
            },
            {
                'name': 'E-commerce Platform',
                'data': {
                    'complexity': 0.8,
                    'lines_of_code': 25000,
                    'team': {'size': 5, 'avg_experience_years': 5},
                    'requirements': [
                        'User management', 'Product catalog', 
                        'Shopping cart', 'Payment integration',
                        'Order management', 'Admin dashboard'
                    ]
                }
            },
            {
                'name': 'Machine Learning Pipeline',
                'data': {
                    'complexity': 0.9,
                    'lines_of_code': 15000,
                    'team': {'size': 2, 'avg_experience_years': 6},
                    'requirements': [
                        'Data ingestion', 'Feature engineering',
                        'Model training', 'Model deployment',
                        'Monitoring dashboard'
                    ]
                }
            },
            {
                'name': 'Mobile App MVP',
                'data': {
                    'complexity': 0.5,
                    'lines_of_code': 8000,
                    'team': {'size': 2, 'avg_experience_years': 3},
                    'requirements': [
                        'User onboarding', 'Core functionality',
                        'Push notifications', 'Basic analytics'
                    ]
                }
            }
        ]
        
        print("Comparing different project types:\n")
        
        results_table = []
        
        for scenario in project_scenarios:
            result = await self.engine.predict_development_time(scenario['data'])
            
            results_table.append({
                'Project Type': scenario['name'],
                'Complexity': f"{scenario['data']['complexity']:.1f}",
                'Team Size': scenario['data']['team']['size'],
                'Predicted Days': result.predicted_value,
                'Confidence': f"{result.confidence_score:.1%}"
            })
            
            print(f"📋 {scenario['name']}:")
            print(f"    Predicted Time: {result.predicted_value} days")
            print(f"    Confidence: {result.confidence.value} ({result.confidence_score:.1%})")
            print()
        
        # Display summary table
        print("📊 Summary Comparison:")
        print("-" * 70)
        print(f"{'Project Type':<25} {'Complexity':<10} {'Team':<6} {'Days':<6} {'Confidence':<12}")
        print("-" * 70)
        
        for row in results_table:
            print(f"{row['Project Type']:<25} {row['Complexity']:<10} {row['Team Size']:<6} {row['Predicted Days']:<6} {row['Confidence']:<12}")
        
        print()
    
    async def demo_team_size_impact(self):
        """Demonstrate impact of team size on predictions"""
        print("👥 TEAM SIZE IMPACT ANALYSIS")
        print("-" * 50)
        
        base_project = {
            'complexity': 0.6,
            'lines_of_code': 10000,
            'requirements': ['Feature A', 'Feature B', 'Feature C', 'Feature D']
        }
        
        team_sizes = [1, 2, 3, 5, 8, 12]
        
        print("Analyzing impact of team size on development time:\n")
        
        for team_size in team_sizes:
            project_data = base_project.copy()
            project_data['team'] = {
                'size': team_size,
                'avg_experience_years': 4
            }
            
            result = await self.engine.predict_development_time(project_data)
            
            # Calculate efficiency (days per team member)
            efficiency = result.predicted_value / team_size
            
            print(f"Team Size {team_size:2d}: {result.predicted_value:2d} days "
                  f"(efficiency: {efficiency:.1f} days/person, "
                  f"confidence: {result.confidence_score:.1%})")
        
        print("\n💡 Insights:")
        print("  • Smaller teams often have higher efficiency per person")
        print("  • Larger teams may face coordination overhead")
        print("  • Optimal team size depends on project complexity")
        print()
    
    async def demo_complexity_analysis(self):
        """Demonstrate complexity impact on predictions"""
        print("🧩 COMPLEXITY IMPACT ANALYSIS")
        print("-" * 50)
        
        base_project = {
            'lines_of_code': 5000,
            'team': {'size': 3, 'avg_experience_years': 4},
            'requirements': ['Core functionality', 'Testing', 'Documentation']
        }
        
        complexity_levels = [0.1, 0.3, 0.5, 0.7, 0.9]
        complexity_names = ['Very Simple', 'Simple', 'Moderate', 'Complex', 'Very Complex']
        
        print("Analyzing impact of project complexity:\n")
        
        for complexity, name in zip(complexity_levels, complexity_names):
            project_data = base_project.copy()
            project_data['complexity'] = complexity
            
            result = await self.engine.predict_development_time(project_data)
            
            risk_indicator = "🟢" if complexity < 0.5 else "🟡" if complexity < 0.8 else "🔴"
            
            print(f"{risk_indicator} {name:12} (score: {complexity:.1f}): "
                  f"{result.predicted_value:2d} days "
                  f"(confidence: {result.confidence_score:.1%})")
        
        print("\n💡 Complexity Guidelines:")
        print("  🟢 Low complexity (0.1-0.4): Standard development practices")
        print("  🟡 Medium complexity (0.5-0.7): Extra planning and testing needed")
        print("  🔴 High complexity (0.8-1.0): Consider breaking into phases")
        print()
    
    async def demo_engine_metrics(self):
        """Demonstrate engine metrics and status"""
        print("📈 ENGINE METRICS & STATUS")
        print("-" * 50)
        
        # Display current metrics
        metrics = self.engine.metrics
        
        print("Current Engine Metrics:")
        print(f"  • Total Predictions Made: {metrics['predictions_made']}")
        print(f"  • Average Confidence: {metrics['average_confidence']:.1%}")
        
        # Engine status
        predictions_count = metrics['predictions_made']
        avg_confidence = metrics['average_confidence']
        
        if avg_confidence >= 0.8 and predictions_count >= 10:
            status = "🟢 Excellent"
        elif avg_confidence >= 0.7:
            status = "🟡 Good"
        elif avg_confidence >= 0.6:
            status = "🟠 Fair"
        else:
            status = "🔴 Needs Improvement"
        
        print(f"  • Engine Health: {status}")
        print(f"  • Supported Prediction Types: {len([pt for pt in PredictionType])}")
        print()
        
        # Available prediction types
        print("Available Prediction Types:")
        for pt in PredictionType:
            if pt == PredictionType.DEVELOPMENT_TIME:
                status = "✅ Implemented"
            else:
                status = "🔄 Coming Soon"
            print(f"  • {pt.value}: {status}")
        
        print()
    
    async def demo_multiple_predictions(self):
        """Demonstrate handling multiple predictions"""
        print("🔄 MULTIPLE PREDICTIONS DEMO")
        print("-" * 50)
        
        # Create multiple project scenarios
        projects = [
            {'name': 'Project Alpha', 'complexity': 0.4, 'team_size': 2},
            {'name': 'Project Beta', 'complexity': 0.6, 'team_size': 3},
            {'name': 'Project Gamma', 'complexity': 0.8, 'team_size': 4},
            {'name': 'Project Delta', 'complexity': 0.5, 'team_size': 2},
            {'name': 'Project Epsilon', 'complexity': 0.7, 'team_size': 5}
        ]
        
        print(f"Processing {len(projects)} projects simultaneously...\n")
        
        start_time = time.time()
        
        # Process all predictions
        results = []
        for project in projects:
            project_data = {
                'complexity': project['complexity'],
                'lines_of_code': 5000,
                'team': {'size': project['team_size'], 'avg_experience_years': 4},
                'requirements': ['Feature 1', 'Feature 2', 'Feature 3']
            }
            
            result = await self.engine.predict_development_time(project_data)
            results.append((project['name'], result))
        
        total_time = (time.time() - start_time) * 1000
        
        print("Results:")
        for project_name, result in results:
            print(f"  • {project_name}: {result.predicted_value} days "
                  f"({result.confidence.value})")
        
        print(f"\n⚡ Total Processing Time: {total_time:.1f}ms")
        print(f"📊 Average per Prediction: {total_time/len(projects):.1f}ms")
        print()
    
    async def demo_performance_testing(self):
        """Demonstrate performance characteristics"""
        print("⚡ PERFORMANCE TESTING")
        print("-" * 50)
        
        test_project = {
            'complexity': 0.6,
            'lines_of_code': 7500,
            'team': {'size': 3, 'avg_experience_years': 4},
            'requirements': ['Auth', 'Dashboard', 'API', 'Testing']
        }
        
        # Single prediction performance
        print("Single Prediction Performance:")
        times = []
        
        for i in range(5):
            start_time = time.time()
            result = await self.engine.predict_development_time(test_project)
            duration = (time.time() - start_time) * 1000
            times.append(duration)
            print(f"  Run {i+1}: {duration:.1f}ms")
        
        avg_time = sum(times) / len(times)
        print(f"  Average: {avg_time:.1f}ms")
        print()
        
        # Concurrent predictions
        print("Concurrent Predictions Test:")
        concurrent_count = 10
        
        start_time = time.time()
        
        tasks = [
            self.engine.predict_development_time(test_project)
            for _ in range(concurrent_count)
        ]
        
        concurrent_results = await asyncio.gather(*tasks)
        concurrent_time = (time.time() - start_time) * 1000
        
        print(f"  • {concurrent_count} concurrent predictions")
        print(f"  • Total time: {concurrent_time:.1f}ms")
        print(f"  • Average per prediction: {concurrent_time/concurrent_count:.1f}ms")
        print(f"  • Successful predictions: {len(concurrent_results)}")
        print()
    
    async def demo_future_capabilities(self):
        """Preview future capabilities"""
        print("🚀 FUTURE CAPABILITIES PREVIEW")
        print("-" * 50)
        
        future_features = [
            {
                'name': 'Bug Hotspot Detection',
                'description': 'ML-powered identification of code areas likely to contain bugs',
                'input': 'Code complexity metrics, change history, test coverage',
                'output': 'Risk probability score, recommended actions',
                'status': 'Phase 4B Development'
            },
            {
                'name': 'Team Performance Forecasting',
                'description': 'Predict team velocity and delivery capabilities',
                'input': 'Team composition, historical performance, collaboration metrics',
                'output': 'Velocity predictions, performance optimization suggestions',
                'status': 'Phase 4B Development'
            },
            {
                'name': 'Project Health Assessment',
                'description': 'Comprehensive project risk and health analysis',
                'input': 'Multiple project metrics, timeline data, quality indicators',
                'output': 'Health score, risk factors, mitigation strategies',
                'status': 'Phase 4B Planning'
            },
            {
                'name': 'Resource Allocation Optimization',
                'description': 'AI-powered resource allocation across multiple projects',
                'input': 'Team skills, project requirements, business priorities',
                'output': 'Optimal team assignments, capacity planning',
                'status': 'Phase 4B Planning'
            }
        ]
        
        for feature in future_features:
            print(f"🔮 {feature['name']}")
            print(f"    Description: {feature['description']}")
            print(f"    Input: {feature['input']}")
            print(f"    Output: {feature['output']}")
            print(f"    Status: {feature['status']}")
            print()
        
        print("💡 Coming in Phase 4B:")
        print("  • Advanced ML models with training capabilities")
        print("  • Historical data integration and learning")
        print("  • Real-time model performance monitoring")
        print("  • Custom prediction model configuration")
        print("  • Integration with project management tools")
        print()
    
    async def show_demo_summary(self):
        """Show comprehensive demo summary"""
        print("=" * 80)
        print("📊 DEMO SUMMARY")
        print("=" * 80)
        
        # Engine status after demo
        metrics = self.engine.metrics
        
        print("Engine Performance:")
        print(f"  • Total Predictions During Demo: {metrics['predictions_made']}")
        print(f"  • Average Confidence Level: {metrics['average_confidence']:.1%}")
        print()
        
        # Demo results analysis
        if self.demo_results:
            dev_time_results = [r for r in self.demo_results if r['type'] == 'development_time']
            if dev_time_results:
                avg_confidence = sum(r['confidence'] for r in dev_time_results) / len(dev_time_results)
                avg_time = sum(r['prediction_time_ms'] for r in dev_time_results) / len(dev_time_results)
                
                print("Demo Statistics:")
                print(f"  • Average Prediction Confidence: {avg_confidence:.1%}")
                print(f"  • Average Prediction Time: {avg_time:.1f}ms")
                print()
        
        print("Key Capabilities Demonstrated:")
        print("  ✅ Development time prediction with confidence scoring")
        print("  ✅ Multi-project analysis and comparison")
        print("  ✅ Team size impact analysis")
        print("  ✅ Complexity-based prediction adjustment")
        print("  ✅ Real-time performance metrics")
        print("  ✅ Concurrent prediction processing")
        print()
        
        print("Phase 4B Status:")
        print("  🎯 Predictive Analytics Engine: IMPLEMENTED")
        print("  🔄 Additional prediction types: IN DEVELOPMENT")
        print("  📈 Advanced ML models: PLANNED")
        print()
        
        print("Next Steps:")
        print("  1. Implement bug hotspot detection")
        print("  2. Add team performance forecasting")
        print("  3. Integrate historical data learning")
        print("  4. Deploy advanced security engine")
        print()
        
        print("✨ Predictive Analytics Engine Demo Completed Successfully!")
        print("=" * 80)

async def main():
    """Run the comprehensive predictive analytics demo"""
    demo = PredictiveAnalyticsDemo()
    
    try:
        await demo.run_all_demos()
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    else:
        print("\n🎉 Demo completed successfully!")

if __name__ == "__main__":
    # Run the demo
    print("Starting Predictive Analytics Engine Demo...")
    print("Press Ctrl+C to interrupt at any time.\n")
    
    asyncio.run(main()) 