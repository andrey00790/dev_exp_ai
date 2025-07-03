"""
Quick test script for RFC Generator components.
Tests all components individually to ensure they work correctly.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_architecture_analyzer():
    """Test the architecture analyzer component"""
    
    print("🔍 Testing Architecture Analyzer...")
    
    try:
        from domain.rfc_generation.rfc_analyzer import RFCArchitectureAnalyzer, quick_health_check
        
        # Test quick health check
        current_path = str(project_root)
        health = await quick_health_check(current_path)
        
        print(f"✅ Quick health check passed:")
        print(f"   Health Score: {health.get('health_score', 0)}")
        print(f"   Components: {health.get('components_count', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Architecture analyzer test failed: {e}")
        return False

async def test_diagram_generator():
    """Test the Mermaid diagram generator"""
    
    print("\n📊 Testing Mermaid Diagram Generator...")
    
    try:
        from domain.core.mermaid_diagram_generator import MermaidDiagramGenerator
        from domain.rfc_generation.rfc_analyzer import ComponentAnalysis, ArchitectureAnalysis
        
        # Create test data
        test_component = ComponentAnalysis(
            name="test_api",
            service_type="api",
            files=["api.py", "models.py"],
            dependencies=["database"],
            technology_stack=["fastapi", "postgresql"],
            interfaces=["/api/test", "/api/health"]
        )
        
        test_analysis = ArchitectureAnalysis(
            components=[test_component],
            patterns=[],
            quality_issues=[],
            dependencies_graph={"test_api": ["database"]},
            technology_inventory={"fastapi": 1, "postgresql": 1},
            metrics={"total_files": 2},
            improvement_suggestions=["Add monitoring"]
        )
        
        # Test diagram generation
        generator = MermaidDiagramGenerator()
        diagram = generator.generate_architecture_diagram(test_analysis)
        
        print(f"✅ Diagram generation passed:")
        print(f"   Diagram length: {len(diagram)} characters")
        print(f"   Preview: {diagram[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Diagram generator test failed: {e}")
        return False

async def test_rfc_service():
    """Test the RFC service"""
    
    print("\n📝 Testing RFC Service...")
    
    try:
        from services.rfc_service import RFCGeneratorService, RFCRequest
        
        # Create test request
        request = RFCRequest(
            title="Test RFC",
            description="Test RFC generation without analysis",
            rfc_type="design",
            include_diagrams=False,
            include_analysis=False
        )
        
        # Test RFC generation
        service = RFCGeneratorService()
        rfc = await service.generate_rfc(request)
        
        print(f"✅ RFC service test passed:")
        print(f"   RFC ID: {rfc.rfc_id}")
        print(f"   Content length: {len(rfc.content)} characters")
        print(f"   Title: {rfc.title}")
        
        return True
        
    except Exception as e:
        print(f"❌ RFC service test failed: {e}")
        return False

async def test_full_integration():
    """Test full integration with all components"""
    
    print("\n🚀 Testing Full Integration...")
    
    try:
        from services.rfc_service import generate_design_rfc
        
        # Test quick RFC generation
        rfc = await generate_design_rfc(
            title="Integration Test RFC",
            description="Testing full integration of RFC generation components"
        )
        
        print(f"✅ Full integration test passed:")
        print(f"   RFC ID: {rfc.rfc_id}")
        print(f"   Has content: {'✅' if rfc.content else '❌'}")
        print(f"   Has metadata: {'✅' if rfc.metadata else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Full integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    
    print("🧪 RFC GENERATOR COMPONENT TESTS")
    print("=" * 50)
    
    tests = [
        ("Architecture Analyzer", test_architecture_analyzer),
        ("Diagram Generator", test_diagram_generator),
        ("RFC Service", test_rfc_service),
        ("Full Integration", test_full_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("📋 TEST SUMMARY")
    print(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! RFC Generator is ready to use.")
        print("\n🚀 Next steps:")
        print("   • Run the demo: python src/demos/demo_rfc_generator.py")
        print("   • Start the API: uvicorn app.main:app --reload")
        print("   • Test endpoints: http://localhost:8000/docs")
    else:
        print("⚠️ Some tests failed. Please check the error messages above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main()) 