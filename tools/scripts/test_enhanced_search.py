#!/usr/bin/env python3
"""
Quick test script for Enhanced Vector Search functionality.
This script validates that all components work together correctly.
"""

import asyncio
import sys
import os
from typing import List

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that all enhanced search components can be imported"""
    print("🔧 Testing imports...")
    
    try:
        from domain.integration.document_graph_builder import DocumentGraphBuilder, DocumentNode, DocumentRelation
        print("  ✅ DocumentGraphBuilder imported successfully")
        
        from domain.integration.dynamic_reranker import DynamicReranker, UserIntent, ContextualScore
        print("  ✅ DynamicReranker imported successfully")
        
        from domain.integration.enhanced_vector_search_service import EnhancedVectorSearchService
        print("  ✅ EnhancedVectorSearchService imported successfully")
        
        from domain.integration.search_models import SearchResult
        print("  ✅ SearchResult imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False

def test_document_classification():
    """Test document type classification"""
    print("\n🔍 Testing document classification...")
    
    try:
        from domain.integration.document_graph_builder import DocumentGraphBuilder
        
        builder = DocumentGraphBuilder()
        
        # Test code classification
        code_content = "def hello():\n    return 'world'\nimport os"
        doc_type = builder._classify_document_type(code_content)
        assert doc_type == "code", f"Expected 'code', got '{doc_type}'"
        print("  ✅ Code document classification works")
        
        # Test documentation classification
        doc_content = "# API Reference\n## Usage\nExample usage..."
        doc_type = builder._classify_document_type(doc_content)
        assert doc_type == "documentation", f"Expected 'documentation', got '{doc_type}'"
        print("  ✅ Documentation classification works")
        
        # Test configuration classification
        config_content = "FROM python:3.9\nRUN pip install fastapi"
        doc_type = builder._classify_document_type(config_content)
        assert doc_type == "config", f"Expected 'config', got '{doc_type}'"
        print("  ✅ Configuration classification works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Document classification test failed: {e}")
        return False

def test_language_detection():
    """Test programming language detection"""
    print("\n🌐 Testing language detection...")
    
    try:
        from domain.integration.document_graph_builder import DocumentGraphBuilder
        
        builder = DocumentGraphBuilder()
        
        # Test Python detection
        python_content = "def hello():\n    import os\n    return 'world'"
        language = builder._detect_language(python_content, "test.py")
        assert language == "python", f"Expected 'python', got '{language}'"
        print("  ✅ Python language detection works")
        
        # Test JavaScript detection
        js_content = "function hello() {\n    const x = 'world';\n    return x;\n}"
        language = builder._detect_language(js_content, "test.js")
        assert language == "javascript", f"Expected 'javascript', got '{language}'"
        print("  ✅ JavaScript language detection works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Language detection test failed: {e}")
        return False

def test_keyword_extraction():
    """Test keyword extraction from queries"""
    print("\n🔤 Testing keyword extraction...")
    
    try:
        from domain.integration.dynamic_reranker import DynamicReranker
        
        reranker = DynamicReranker()
        
        query = "How to implement Docker microservices deployment patterns"
        keywords = reranker._extract_keywords(query)
        
        expected_keywords = ["implement", "Docker", "microservices", "deployment", "patterns"]
        for keyword in expected_keywords:
            assert keyword in keywords, f"Keyword '{keyword}' not found in {keywords}"
        
        # Check that stop words are filtered out
        stop_words = ["how", "to"]
        for stop_word in stop_words:
            assert stop_word not in keywords, f"Stop word '{stop_word}' should not be in {keywords}"
        
        print("  ✅ Keyword extraction works correctly")
        return True
        
    except Exception as e:
        print(f"  ❌ Keyword extraction test failed: {e}")
        return False

def test_technical_level_detection():
    """Test technical level determination"""
    print("\n🎓 Testing technical level detection...")
    
    try:
        from domain.integration.dynamic_reranker import DynamicReranker
        
        reranker = DynamicReranker()
        
        # Test advanced query
        advanced_query = "Optimize microservices architecture performance patterns"
        level = reranker._determine_technical_level(advanced_query, {})
        assert level == "advanced", f"Expected 'advanced', got '{level}'"
        print("  ✅ Advanced level detection works")
        
        # Test beginner query
        beginner_query = "Introduction to basic Docker tutorial for beginners"
        level = reranker._determine_technical_level(beginner_query, {})
        assert level == "beginner", f"Expected 'beginner', got '{level}'"
        print("  ✅ Beginner level detection works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Technical level detection test failed: {e}")
        return False

async def test_async_components():
    """Test async components with mock data"""
    print("\n⚡ Testing async components...")
    
    try:
        from domain.integration.search_models import SearchResult
        from domain.integration.document_graph_builder import DocumentGraphBuilder
        
        # Create mock search results
        mock_results = [
            SearchResult(
                doc_id="test1",
                title="Test Document 1",
                content="def hello():\n    return 'world'\nimport os",
                score=0.9,
                source="test",
                source_type="code"
            ),
            SearchResult(
                doc_id="test2",
                title="Test Document 2",
                content="# Documentation\nThis is a test document",
                score=0.8,
                source="test",
                source_type="documentation"
            )
        ]
        
        # Test document node creation
        builder = DocumentGraphBuilder()
        node = await builder._create_document_node(mock_results[0])
        
        assert node.doc_id == "test1"
        assert node.document_type == "code"
        assert isinstance(node.importance_score, float)
        
        print("  ✅ Async document node creation works")
        return True
        
    except Exception as e:
        print(f"  ❌ Async components test failed: {e}")
        return False

def create_sample_search_results() -> List:
    """Create sample search results for testing"""
    from domain.integration.search_models import SearchResult
    
    return [
        SearchResult(
            doc_id="sample1",
            title="User Service Implementation",
            content="from fastapi import FastAPI\napp = FastAPI()\n\ndef create_user():\n    pass",
            score=0.9,
            source="gitlab/user-service",
            source_type="code",
            tags=["python", "fastapi", "api"]
        ),
        SearchResult(
            doc_id="sample2",
            title="Docker Configuration",
            content="FROM python:3.9\nRUN pip install fastapi\nCMD ['python', 'app.py']",
            score=0.8,
            source="gitlab/config",
            source_type="config",
            tags=["docker", "python"]
        ),
        SearchResult(
            doc_id="sample3",
            title="API Documentation",
            content="# User API\n## Endpoints\n- POST /users\n- GET /users/{id}",
            score=0.7,
            source="confluence/docs",
            source_type="documentation",
            tags=["api", "docs"]
        )
    ]

async def run_integration_test():
    """Run a basic integration test"""
    print("\n🔗 Running integration test...")
    
    try:
        from domain.integration.document_graph_builder import build_document_graph
        
        # Create sample data
        sample_results = create_sample_search_results()
        
        # Test graph building (will use fallback if embeddings service not available)
        document_graph = await build_document_graph(sample_results, include_semantic_analysis=False)
        
        assert len(document_graph) == len(sample_results)
        print(f"  ✅ Document graph built with {len(document_graph)} nodes")
        
        # Check that nodes have proper types
        for node in document_graph.values():
            assert node.document_type in ["code", "documentation", "config", "unknown"]
        
        print("  ✅ Document types properly classified")
        return True
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Enhanced Vector Search - Component Tests")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Document Classification", test_document_classification),
        ("Language Detection", test_language_detection),
        ("Keyword Extraction", test_keyword_extraction),
        ("Technical Level Detection", test_technical_level_detection),
        ("Async Components", test_async_components),
        ("Integration Test", run_integration_test)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced search components are working correctly.")
        print("\n📝 Next steps:")
        print("  1. Run the full demo: python src/demos/demo_enhanced_search.py")
        print("  2. Test the API endpoint: POST /api/v1/vector-search/search/enhanced")
        print("  3. Run unit tests: pytest tests/unit/test_enhanced_vector_search.py")
    else:
        print(f"⚠️  {total - passed} tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main()) 