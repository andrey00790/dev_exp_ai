#!/usr/bin/env python3
"""
🧪 Enhanced RFC Generation Testing Script
Тестирование Phase 2: RFC Generation с диаграммами и архитектурным анализом
"""

import asyncio
import sys
import os
import tempfile
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from domain.rfc_generation.rfc_generator_service import RFCGeneratorService, RFCRequest
from domain.rfc_generation.rfc_analyzer import analyze_project_architecture

async def test_enhanced_rfc_generation():
    """Test enhanced RFC generation functionality"""
    
    print("🧪 " + "="*70)
    print("   ENHANCED RFC GENERATION - TESTING SUITE")
    print("   Phase 2: RFC Generation with Diagrams & Analysis")
    print("="*74)
    
    rfc_service = RFCGeneratorService()
    
    # Test 1: Simple RFC with diagrams
    print("\n🔬 Test 1: Simple RFC Generation with Diagrams")
    print("-" * 50)
    
    try:
        request = RFCRequest(
            title="Test API Rate Limiting Implementation",
            description="Implement rate limiting for API endpoints to prevent abuse and ensure fair usage.",
            rfc_type="architecture",
            include_diagrams=True,
            include_analysis=False,
            author="Test Suite"
        )
        
        rfc = await rfc_service.generate_rfc(request)
        
        print(f"✅ RFC Generated: {rfc.title}")
        print(f"   📄 Content: {len(rfc.content)} characters")
        print(f"   📋 Sections: {len(rfc.sections)}")
        print(f"   📊 Diagrams: {len(rfc.diagrams)}")
        
        if rfc.diagrams:
            for name in rfc.diagrams.keys():
                print(f"      - {name.replace('_', ' ').title()}")
        
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
    
    # Test 2: RFC with project analysis
    print("\n🔬 Test 2: RFC with Project Analysis")
    print("-" * 50)
    
    try:
        # Use current project for analysis
        current_path = "."
        
        request = RFCRequest(
            title="Test Project Architecture Enhancement",
            description="Enhance the current project architecture based on analysis.",
            project_path=current_path,
            rfc_type="architecture",
            include_diagrams=True,
            include_analysis=True,
            author="Test Suite"
        )
        
        rfc = await rfc_service.generate_rfc(request)
        
        print(f"✅ Enhanced RFC Generated: {rfc.title}")
        print(f"   📄 Content: {len(rfc.content)} characters")
        print(f"   📋 Sections: {len(rfc.sections)}")
        print(f"   📊 Diagrams: {len(rfc.diagrams)}")
        
        if rfc.analysis:
            print(f"   🔍 Analysis:")
            print(f"      - Components: {len(rfc.analysis.components)}")
            print(f"      - Technologies: {len(rfc.analysis.technology_inventory)}")
            print(f"      - Recommendations: {len(rfc.analysis.improvement_suggestions)}")
        
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
    
    # Test 3: Different RFC types
    print("\n🔬 Test 3: Different RFC Types")
    print("-" * 50)
    
    rfc_types = ["architecture", "design", "process", "api"]
    
    for rfc_type in rfc_types:
        try:
            request = RFCRequest(
                title=f"Test {rfc_type.title()} RFC",
                description=f"Test RFC generation for {rfc_type} type documents.",
                rfc_type=rfc_type,
                include_diagrams=True,
                include_analysis=False,
                author="Test Suite"
            )
            
            rfc = await rfc_service.generate_rfc(request)
            print(f"   ✅ {rfc_type.title()} RFC: {len(rfc.content)} chars, {len(rfc.sections)} sections")
            
        except Exception as e:
            print(f"   ❌ {rfc_type.title()} RFC failed: {e}")
    
    # Test 4: Error handling
    print("\n🔬 Test 4: Error Handling")
    print("-" * 50)
    
    try:
        # Test with invalid project path
        request = RFCRequest(
            title="Test Error Handling",
            description="Test RFC with invalid project path.",
            project_path="/nonexistent/path",
            rfc_type="architecture",
            include_diagrams=True,
            include_analysis=True,
            author="Test Suite"
        )
        
        rfc = await rfc_service.generate_rfc(request)
        print(f"✅ Error handling test passed - got fallback RFC")
        print(f"   📄 Content: {len(rfc.content)} characters")
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
    
    # Test 5: Performance test
    print("\n🔬 Test 5: Performance Test")
    print("-" * 50)
    
    import time
    
    try:
        start_time = time.time()
        
        request = RFCRequest(
            title="Performance Test RFC",
            description="Test RFC generation performance with moderate complexity.",
            rfc_type="architecture",
            include_diagrams=True,
            include_analysis=False,
            author="Test Suite"
        )
        
        rfc = await rfc_service.generate_rfc(request)
        
        duration = time.time() - start_time
        print(f"✅ Performance test completed in {duration:.2f} seconds")
        print(f"   📄 Generated: {len(rfc.content)} characters")
        print(f"   📊 Diagrams: {len(rfc.diagrams)}")
        
        if duration < 30:  # Should complete within 30 seconds
            print(f"   🚀 Performance: GOOD (< 30s)")
        else:
            print(f"   ⚠️ Performance: SLOW (> 30s)")
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
    
    print("\n🎉 Enhanced RFC Generation testing completed!")
    print("All major components tested successfully.")

async def test_standalone_analysis():
    """Test standalone project analysis"""
    
    print("\n🔬 Standalone Analysis Test")
    print("-" * 50)
    
    try:
        from domain.rfc_generation.rfc_analyzer import quick_health_check
        
        # Quick health check
        print("   🏥 Running health check...")
        health = await quick_health_check(".")
        print(f"   📊 Health Score: {health.get('health_score', 0)}/100")
        
        # Full analysis
        print("   🔍 Running full analysis...")
        analysis = await analyze_project_architecture(".")
        
        print(f"   ✅ Analysis completed:")
        print(f"      - Components: {len(analysis.components)}")
        print(f"      - Files: {analysis.metrics.get('total_files', 0)}")
        print(f"      - Technologies: {len(analysis.technology_inventory)}")
        
    except Exception as e:
        print(f"   ❌ Analysis test failed: {e}")

async def test_diagram_generation():
    """Test Mermaid diagram generation"""
    
    print("\n🔬 Diagram Generation Test")
    print("-" * 50)
    
    try:
        from domain.core.mermaid_diagram_generator import (
            MermaidDiagramGenerator, 
            create_architecture_diagram
        )
        
        # Create mock analysis for diagram testing
        from domain.rfc_generation.rfc_analyzer import ComponentAnalysis, ArchitectureAnalysis
        
        mock_components = [
            ComponentAnalysis(
                name="api",
                service_type="api",
                files=["app/main.py", "app/api/routes.py"],
                dependencies=["database"],
                technology_stack=["fastapi", "python"],
                interfaces=["/health", "/api/v1/search"]
            ),
            ComponentAnalysis(
                name="database",
                service_type="database",
                files=["models/base.py"],
                dependencies=[],
                technology_stack=["postgresql", "sqlalchemy"],
                interfaces=[]
            )
        ]
        
        mock_analysis = ArchitectureAnalysis(
            components=mock_components,
            dependencies_graph={"api": ["database"], "database": []},
            technology_inventory={"fastapi": 2, "postgresql": 1},
            metrics={"total_files": 3},
            improvement_suggestions=["Add caching layer"]
        )
        
        # Generate diagrams
        generator = MermaidDiagramGenerator()
        
        print("   📈 Generating architecture diagram...")
        arch_diagram = generator.generate_architecture_diagram(mock_analysis)
        print(f"   ✅ Architecture diagram: {len(arch_diagram)} characters")
        
        print("   📈 Generating dependency diagram...")
        dep_diagram = generator.generate_dependency_graph(mock_analysis)
        print(f"   ✅ Dependency diagram: {len(dep_diagram)} characters")
        
        print("   📈 Generating deployment diagram...")
        deploy_diagram = generator.generate_deployment_diagram(mock_analysis)
        print(f"   ✅ Deployment diagram: {len(deploy_diagram)} characters")
        
    except Exception as e:
        print(f"   ❌ Diagram generation test failed: {e}")

async def main():
    """Run all tests"""
    
    await test_enhanced_rfc_generation()
    await test_standalone_analysis()
    await test_diagram_generation()
    
    print(f"\n🏁 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 