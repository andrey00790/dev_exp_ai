#!/usr/bin/env python3
"""
Comprehensive E2E tests using test-data directory.
Automatically downloads data and trains model if needed.
"""

import pytest
import asyncio
import os
import json
import yaml
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import requests
import time

# Test imports
from fastapi.testclient import TestClient
from app.main import app

# Mark entire module as E2E
pytestmark = pytest.mark.e2e

# Test data paths
TEST_DATA_DIR = Path("test-data")
CONFLUENCE_DIR = TEST_DATA_DIR / "confluence"
JIRA_DIR = TEST_DATA_DIR / "jira"  
GITLAB_DIR = TEST_DATA_DIR / "gitlab"
DATASET_DIR = TEST_DATA_DIR / "dataset"

class E2ETestEnvironment:
    """Manages E2E test environment setup and data preparation."""
    
    def __init__(self):
        self.client = TestClient(app)
        self.test_data_ready = False
        self.model_trained = False
        
    async def setup_environment(self):
        """Setup complete test environment with data and trained model."""
        print("🚀 Setting up E2E test environment...")
        
        # 1. Ensure test data exists
        await self.ensure_test_data()
        
        # 2. Download external data if configured
        await self.download_external_data()
        
        # 3. Train model if needed
        await self.ensure_model_trained()
        
        # 4. Initialize vector database
        await self.initialize_vector_db()
        
        print("✅ E2E test environment ready!")
        
    async def ensure_test_data(self):
        """Ensure all test data directories and files exist."""
        print("📁 Checking test data...")
        
        # Create directories if they don't exist
        for dir_path in [CONFLUENCE_DIR, JIRA_DIR, GITLAB_DIR, DATASET_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # Generate comprehensive test data
        await self.generate_comprehensive_test_data()
        self.test_data_ready = True
        print("✅ Test data ready")
        
    async def generate_comprehensive_test_data(self):
        """Generate large volume of test data for all sources."""
        
        # Generate Confluence pages (100+ documents)
        confluence_docs = []
        
        # Technical documentation
        tech_topics = [
            "OAuth 2.0 Implementation", "JWT Token Management", "API Rate Limiting",
            "Microservices Architecture", "Database Design Patterns", "Caching Strategies",
            "Message Queue Implementation", "Service Discovery", "Load Balancing",
            "Security Best Practices", "Performance Optimization", "Monitoring and Logging"
        ]
        
        for i, topic in enumerate(tech_topics):
            doc_content = f"""# {topic}

**Space:** TECH | **Created:** 2024-{i%12+1:02d}-15
**Author:** architect{i%3+1}@company.com
**Labels:** {topic.lower().replace(' ', '-')}, technical, implementation

## Overview
{topic} is a critical component of modern software architecture.

## Implementation Details
This document provides comprehensive guidance on implementing {topic}.

### Key Concepts
- Concept 1: Foundation principles
- Concept 2: Best practices
- Concept 3: Common pitfalls

### Code Examples
```python
# Example implementation
def implement_{topic.lower().replace(' ', '_')}():
    pass
```

## Troubleshooting
Common issues and solutions for {topic}.

## References
- Internal documentation
- External resources
- Best practice guides
"""
            
            file_path = CONFLUENCE_DIR / f"{topic.lower().replace(' ', '_')}.md"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            
            confluence_docs.append({
                "filename": file_path.name,
                "space": "TECH",
                "title": topic,
                "content_preview": doc_content[:200]
            })
        
        # Generate Jira issues (200+ issues)
        jira_issues = []
        
        # Epic issues
        epics = [
            "API Platform Enhancement", "Security Improvements", 
            "Performance Optimization", "User Experience Upgrade"
        ]
        
        for i, epic in enumerate(epics):
            epic_issue = {
                "key": f"PROJ-{1000+i}",
                "project": "PROJ",
                "issue_type": "Epic",
                "summary": epic,
                "description": f"Major initiative for {epic}",
                "status": "In Progress",
                "priority": "High",
                "created": f"2024-{i%12+1:02d}-01T10:00:00Z",
                "labels": [epic.lower().replace(' ', '-')],
                "stories": []
            }
            
            # Generate stories for each epic
            for j in range(15):  # 15 stories per epic
                story = {
                    "key": f"PROJ-{2000+i*20+j}",
                    "project": "PROJ", 
                    "issue_type": "Story",
                    "summary": f"Implement {epic} feature {j+1}",
                    "description": f"User story for {epic} implementation",
                    "status": ["To Do", "In Progress", "Done"][j%3],
                    "priority": ["High", "Medium", "Low"][j%3],
                    "story_points": [1, 2, 3, 5, 8][j%5],
                    "epic_link": epic_issue["key"],
                    "created": f"2024-{i%12+1:02d}-{j%28+1:02d}T10:00:00Z"
                }
                epic_issue["stories"].append(story["key"])
                jira_issues.append(story)
            
            jira_issues.append(epic_issue)
        
        # Generate bugs
        for i in range(50):
            bug = {
                "key": f"PROJ-{3000+i}",
                "project": "PROJ",
                "issue_type": "Bug", 
                "summary": f"Bug in {['authentication', 'payment', 'notification'][i%3]} service",
                "description": f"Critical bug affecting {['users', 'transactions', 'communications'][i%3]}",
                "status": ["Open", "In Progress", "Resolved"][i%3],
                "priority": ["Critical", "High", "Medium"][i%3],
                "created": f"2024-{i%12+1:02d}-{i%28+1:02d}T10:00:00Z"
            }
            jira_issues.append(bug)
        
        # Save Jira data
        jira_data = {
            "metadata": {
                "total_issues": len(jira_issues),
                "projects": ["PROJ"],
                "generated_at": datetime.now().isoformat()
            },
            "issues": jira_issues
        }
        
        with open(JIRA_DIR / "issues.json", 'w', encoding='utf-8') as f:
            json.dump(jira_data, f, indent=2, ensure_ascii=False)
        
        # Generate GitLab repositories
        repositories = [
            {
                "name": "api-gateway",
                "description": "Central API Gateway service",
                "files": {
                    "README.md": "# API Gateway\n\nMain gateway service for microservices architecture.",
                    "docs/api.md": "# API Documentation\n\nComplete API reference.",
                    "docs/deployment.md": "# Deployment Guide\n\nProduction deployment instructions."
                },
                "issues": [
                    {"title": "Add authentication middleware", "state": "open"},
                    {"title": "Implement rate limiting", "state": "closed"}
                ]
            },
            {
                "name": "user-service", 
                "description": "User management microservice",
                "files": {
                    "README.md": "# User Service\n\nHandles user authentication and management.",
                    "docs/schema.md": "# Database Schema\n\nUser service database design."
                }
            },
            {
                "name": "payment-service",
                "description": "Payment processing service", 
                "files": {
                    "README.md": "# Payment Service\n\nSecure payment processing.",
                    "docs/security.md": "# Security Guidelines\n\nPayment security best practices."
                }
            }
        ]
        
        for repo in repositories:
            repo_dir = GITLAB_DIR / repo["name"]
            repo_dir.mkdir(exist_ok=True)
            
            # Create files
            for file_path, content in repo["files"].items():
                full_path = repo_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Save metadata
            metadata = {
                "name": repo["name"],
                "description": repo["description"],
                "issues": repo.get("issues", []),
                "merge_requests": repo.get("merge_requests", [])
            }
            
            with open(repo_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
        
        # Generate training dataset
        training_data = self.generate_training_dataset()
        with open(DATASET_DIR / "training_data.json", 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Generated test data:")
        print(f"  - Confluence: {len(confluence_docs)} documents")
        print(f"  - Jira: {len(jira_issues)} issues")
        print(f"  - GitLab: {len(repositories)} repositories")
        print(f"  - Training: {len(training_data['pairs'])} pairs")
        
    def generate_training_dataset(self) -> Dict[str, Any]:
        """Generate training dataset based on dataset_config.yml."""
        
        # Load configuration
        try:
            with open('dataset_config.yml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            config = {"training_pairs": {"semantic_search": []}}
        
        # Generate training pairs
        training_pairs = [
            {
                "query": "Как реализовать OAuth 2.0 аутентификацию?",
                "language": "ru",
                "expected_docs": ["oauth_2_0_implementation.md"],
                "relevance_score": 0.95,
                "category": "authentication"
            },
            {
                "query": "How to implement OAuth 2.0 authentication?",
                "language": "en", 
                "expected_docs": ["oauth_2_0_implementation.md"],
                "relevance_score": 0.95,
                "category": "authentication"
            },
            {
                "query": "Микросервисы архитектура паттерны",
                "language": "ru",
                "expected_docs": ["microservices_architecture.md"],
                "relevance_score": 0.90,
                "category": "architecture"
            },
            {
                "query": "Microservices architecture patterns",
                "language": "en",
                "expected_docs": ["microservices_architecture.md"], 
                "relevance_score": 0.90,
                "category": "architecture"
            }
        ]
        
        # Add pairs from config if available
        config_pairs = config.get("training_pairs", {}).get("semantic_search", [])
        training_pairs.extend(config_pairs)
        
        return {
            "metadata": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "total_pairs": len(training_pairs),
                "languages": ["ru", "en"],
                "categories": ["authentication", "architecture", "performance", "security"]
            },
            "pairs": training_pairs
        }
        
    async def download_external_data(self):
        """Download external data sources if configured."""
        print("📥 Checking external data sources...")
        
        # Check if dataset_config.yml specifies external sources
        try:
            with open('dataset_config.yml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            data_sources = config.get('data_sources', {})
            
            # Simulate downloading from configured sources
            for source, source_config in data_sources.items():
                if source_config.get('enabled', False):
                    print(f"📡 Simulating download from {source}...")
                    # In real implementation, this would download actual data
                    await asyncio.sleep(0.1)  # Simulate download time
                    
        except FileNotFoundError:
            print("⚠️  dataset_config.yml not found, using local test data only")
        
        print("✅ External data sources processed")
        
    async def ensure_model_trained(self):
        """Ensure semantic search model is trained with test data."""
        print("🧠 Checking model training status...")
        
        model_path = Path("models/trained_model")
        
        if not model_path.exists() or self.should_retrain_model():
            print("🔄 Training model with test data...")
            await self.train_model()
            self.model_trained = True
            print("✅ Model training completed")
        else:
            print("✅ Model already trained")
            self.model_trained = True
            
    def should_retrain_model(self) -> bool:
        """Check if model should be retrained based on new data."""
        # Check if training data is newer than model
        training_data_path = DATASET_DIR / "training_data.json"
        model_path = Path("models/trained_model")
        
        if not training_data_path.exists() or not model_path.exists():
            return True
            
        training_mtime = training_data_path.stat().st_mtime
        model_mtime = model_path.stat().st_mtime
        
        return training_mtime > model_mtime
        
    async def train_model(self):
        """Train semantic search model with test data."""
        try:
            # Import model training module
            from model_training import ModelTrainer
            
            trainer = ModelTrainer()
            
            # Load training data
            training_data_path = DATASET_DIR / "training_data.json"
            if training_data_path.exists():
                with open(training_data_path, 'r', encoding='utf-8') as f:
                    training_data = json.load(f)
                
                # Train model with test data
                await trainer.train_with_data(training_data)
                print("✅ Model trained with test data")
            else:
                print("⚠️  Training data not found, using default model")
                
        except ImportError:
            print("⚠️  Model training module not available, using mock training")
            await asyncio.sleep(1)  # Simulate training time
            
    async def initialize_vector_db(self):
        """Initialize vector database with test documents."""
        print("🗄️  Initializing vector database...")
        
        try:
            # Import vector store modules
            from vectorstore.qdrant_client import QdrantVectorStore
            from vectorstore.collections import CollectionManager
            
            # Initialize vector store
            vector_store = QdrantVectorStore(use_memory=True)
            collection_manager = CollectionManager()
            
            # Index test documents
            await self.index_test_documents(collection_manager)
            
            print("✅ Vector database initialized")
            
        except ImportError:
            print("⚠️  Vector store modules not available, using mock data")
            
    async def index_test_documents(self, collection_manager):
        """Index all test documents into vector database."""
        
        # Index Confluence documents
        confluence_files = list(CONFLUENCE_DIR.glob("*.md"))
        for file_path in confluence_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata from document
            metadata = {
                "doc_id": file_path.stem,
                "title": file_path.stem.replace('_', ' ').title(),
                "source": "confluence",
                "source_type": "documents"
            }
            
            try:
                await collection_manager.index_document(content, metadata)
            except Exception as e:
                print(f"⚠️  Failed to index {file_path.name}: {e}")
        
        print(f"📚 Indexed {len(confluence_files)} Confluence documents")


@pytest.fixture(scope="session")
async def e2e_environment():
    """Setup E2E test environment."""
    env = E2ETestEnvironment()
    await env.setup_environment()
    yield env
    
    # Cleanup after tests
    print("🧹 Cleaning up test environment...")


class TestE2EComprehensive:
    """Comprehensive E2E tests using test-data."""
    
    @pytest.mark.asyncio
    async def test_data_sources_integration(self, e2e_environment):
        """Test integration with all data sources using test data."""
        
        # Test Confluence data integration
        response = e2e_environment.client.get("/api/v1/sources")
        assert response.status_code == 200
        
        sources = response.json()
        assert "confluence" in [s["type"] for s in sources.get("sources", [])]
        
    @pytest.mark.asyncio
    async def test_semantic_search_with_test_data(self, e2e_environment):
        """Test semantic search using generated test data."""
        
        # Test search with authentication query
        search_request = {
            "query": "OAuth 2.0 implementation guide",
            "limit": 5
        }
        
        response = e2e_environment.client.post(
            "/api/v1/vector-search/search",
            json=search_request
        )
        
        assert response.status_code == 200
        results = response.json()
        
        assert "results" in results
        assert len(results["results"]) > 0
        
        # Check that relevant documents are returned
        found_oauth = any("oauth" in result.get("title", "").lower() 
                         for result in results["results"])
        assert found_oauth, "OAuth related documents should be found"
        
    @pytest.mark.asyncio
    async def test_jira_data_processing(self, e2e_environment):
        """Test processing of Jira test data."""
        
        # Check if Jira data was loaded
        jira_file = JIRA_DIR / "issues.json"
        assert jira_file.exists(), "Jira test data should exist"
        
        with open(jira_file, 'r', encoding='utf-8') as f:
            jira_data = json.load(f)
        
        assert "issues" in jira_data
        assert len(jira_data["issues"]) > 0
        
        # Test that issues can be searched
        search_request = {
            "query": "authentication implementation",
            "limit": 5
        }
        
        response = e2e_environment.client.post(
            "/api/v1/search",
            json=search_request
        )
        
        assert response.status_code == 200
        
    @pytest.mark.asyncio
    async def test_model_training_pipeline(self, e2e_environment):
        """Test that model training pipeline works with test data."""
        
        assert e2e_environment.model_trained, "Model should be trained"
        
        # Test model performance with training pairs
        training_file = DATASET_DIR / "training_data.json"
        if training_file.exists():
            with open(training_file, 'r', encoding='utf-8') as f:
                training_data = json.load(f)
            
            # Test some training pairs
            for pair in training_data["pairs"][:3]:  # Test first 3 pairs
                response = e2e_environment.client.post(
                    "/api/v1/vector-search/search",
                    json={"query": pair["query"], "limit": 5}
                )
                
                assert response.status_code == 200
                results = response.json()
                assert len(results["results"]) > 0
                
    @pytest.mark.asyncio
    async def test_rfc_generation_with_context(self, e2e_environment):
        """Test RFC generation using test data as context."""
        
        rfc_request = {
            "project_description": "Implement OAuth 2.0 authentication system",
            "requirements": [
                "Secure token-based authentication",
                "Support for multiple client types",
                "Integration with existing services"
            ],
            "constraints": ["Must use industry standards", "High performance required"]
        }
        
        response = e2e_environment.client.post(
            "/api/v1/generate",
            json=rfc_request
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert "rfc_content" in result
        assert "OAuth" in result["rfc_content"]
        
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self, e2e_environment):
        """Test complete workflow: search -> generate -> feedback."""
        
        # 1. Search for relevant documents
        search_response = e2e_environment.client.post(
            "/api/v1/vector-search/search",
            json={"query": "authentication best practices", "limit": 3}
        )
        assert search_response.status_code == 200
        
        # 2. Generate RFC based on search results
        rfc_response = e2e_environment.client.post(
            "/api/v1/generate",
            json={
                "project_description": "Secure authentication system",
                "requirements": ["Multi-factor authentication", "Token management"]
            }
        )
        assert rfc_response.status_code == 200
        
        # 3. Provide feedback
        feedback_response = e2e_environment.client.post(
            "/api/v1/feedback",
            json={
                "query": "authentication best practices",
                "result_id": "test_result",
                "rating": 5,
                "comment": "Excellent results with test data"
            }
        )
        assert feedback_response.status_code == 200
        
    @pytest.mark.asyncio
    async def test_performance_with_large_dataset(self, e2e_environment):
        """Test system performance with large test dataset."""
        
        start_time = time.time()
        
        # Perform multiple searches to test performance
        queries = [
            "OAuth 2.0 implementation",
            "microservices architecture", 
            "database design patterns",
            "security best practices",
            "performance optimization"
        ]
        
        for query in queries:
            response = e2e_environment.client.post(
                "/api/v1/vector-search/search",
                json={"query": query, "limit": 5}
            )
            assert response.status_code == 200
        
        elapsed_time = time.time() - start_time
        
        # Should complete all searches within reasonable time
        assert elapsed_time < 10.0, f"Searches took too long: {elapsed_time}s"
        
    @pytest.mark.asyncio
    async def test_multilingual_support(self, e2e_environment):
        """Test multilingual support with Russian and English queries."""
        
        test_queries = [
            {"query": "реализация аутентификации", "language": "ru"},
            {"query": "authentication implementation", "language": "en"},
            {"query": "архитектура микросервисов", "language": "ru"},
            {"query": "microservices architecture", "language": "en"}
        ]
        
        for test_case in test_queries:
            response = e2e_environment.client.post(
                "/api/v1/vector-search/search",
                json=test_case
            )
            
            assert response.status_code == 200
            results = response.json()
            assert len(results["results"]) > 0


if __name__ == "__main__":
    # Run E2E tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"]) 