#!/usr/bin/env python3
"""
Generate comprehensive test data for E2E testing.
Creates realistic test data for Confluence, Jira, GitLab, and training datasets.
"""

import os
import json
import yaml
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

# Create test-data directory structure
TEST_DATA_DIR = "test-data"
CONFLUENCE_DIR = os.path.join(TEST_DATA_DIR, "confluence")
JIRA_DIR = os.path.join(TEST_DATA_DIR, "jira")
GITLAB_DIR = os.path.join(TEST_DATA_DIR, "gitlab")
DATASET_DIR = os.path.join(TEST_DATA_DIR, "dataset")

def create_directories():
    """Create all necessary directories."""
    for dir_path in [CONFLUENCE_DIR, JIRA_DIR, GITLAB_DIR, DATASET_DIR]:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")

def generate_confluence_data():
    """Generate comprehensive Confluence test data."""
    print("Generating Confluence test data...")
    
    # Technical documentation
    confluence_docs = [
        {
            "filename": "tech_space_oauth2_guide.md",
            "space": "TECH",
            "title": "OAuth 2.0 Implementation Guide",
            "content": """# OAuth 2.0 Implementation Guide

**Space:** TECH | **Created:** 2024-01-15 | **Author:** system.architect@company.com  
**Labels:** oauth2, authentication, security, api

## Overview
OAuth 2.0 authorization framework enables secure API access through token-based authentication.

## Implementation Steps
1. Register application with authorization server
2. Redirect user to authorization endpoint
3. Exchange authorization code for access token
4. Use access token to access protected resources

## Security Best Practices
- Use PKCE for all public clients
- Implement proper state validation
- Store tokens securely (httpOnly cookies)
- Use short-lived access tokens with refresh tokens

## Code Examples

### Python Implementation
```python
import requests
from urllib.parse import urlencode

class OAuth2Client:
    def __init__(self, client_id, client_secret, auth_url, token_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.token_url = token_url
    
    def get_authorization_url(self, scope, state):
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'scope': scope,
            'state': state,
            'redirect_uri': 'https://example.com/callback'
        }
        return f"{self.auth_url}?{urlencode(params)}"
```

## Testing
Unit tests should cover authorization flow, token validation, and error handling.
"""
        },
        {
            "filename": "arch_space_microservices_patterns.md",
            "space": "ARCH",
            "title": "Microservices Architecture Patterns",
            "content": """# Microservices Architecture Patterns

**Space:** ARCH | **Created:** 2024-02-20 | **Author:** chief.architect@company.com  
**Labels:** microservices, architecture, patterns, scalability

## Service Decomposition Patterns

### 1. Database per Service
Each microservice has its own database to ensure loose coupling.

### 2. API Gateway Pattern
Single entry point for all client requests, handles routing, authentication, rate limiting.

### 3. Circuit Breaker Pattern
Prevents cascade failures by monitoring service calls and failing fast.

## Communication Patterns

### Synchronous Communication
- REST APIs
- GraphQL
- gRPC

### Asynchronous Communication
- Message queues (RabbitMQ, Apache Kafka)
- Event sourcing
- Pub/Sub patterns

## Data Management Patterns

### Saga Pattern
Manages distributed transactions across multiple services.

### CQRS (Command Query Responsibility Segregation)
Separates read and write operations for better performance.

## Implementation Guidelines

```yaml
# docker-compose.yml example
version: '3.8'
services:
  api-gateway:
    image: nginx:alpine
    ports:
      - "80:80"
  
  user-service:
    image: user-service:latest
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/users
  
  order-service:
    image: order-service:latest
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/orders
```

## Monitoring and Observability
- Distributed tracing (Jaeger, Zipkin)
- Centralized logging (ELK stack)
- Metrics collection (Prometheus, Grafana)
"""
        },
        {
            "filename": "dev_space_api_documentation.md",
            "space": "DEV",
            "title": "REST API Development Guidelines",
            "content": """# REST API Development Guidelines

**Space:** DEV | **Created:** 2024-03-10 | **Author:** lead.developer@company.com  
**Labels:** api, rest, development, standards

## API Design Principles

### 1. RESTful Resource Design
- Use nouns for resource names
- Use HTTP methods appropriately (GET, POST, PUT, DELETE)
- Implement proper status codes

### 2. URL Structure
```
GET    /api/v1/users          # Get all users
GET    /api/v1/users/{id}     # Get specific user
POST   /api/v1/users          # Create new user
PUT    /api/v1/users/{id}     # Update user
DELETE /api/v1/users/{id}     # Delete user
```

### 3. Request/Response Format
```json
{
  "status": "success",
  "data": {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com"
  },
  "metadata": {
    "timestamp": "2024-06-10T10:30:00Z",
    "version": "1.0"
  }
}
```

## Authentication & Authorization
- Use Bearer tokens for API authentication
- Implement role-based access control (RBAC)
- Validate all input parameters

## Error Handling
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": {
      "field": "email",
      "value": "invalid-email"
    }
  }
}
```

## Rate Limiting
- Implement per-user rate limits
- Use sliding window algorithm
- Return appropriate headers (X-RateLimit-*)

## Testing Strategy
- Unit tests for business logic
- Integration tests for API endpoints
- Contract testing for API consumers
"""
        },
        {
            "filename": "testspace_qa_procedures.md",
            "space": "TESTSPACE",
            "title": "QA Testing Procedures",
            "content": """# QA Testing Procedures

**Space:** TESTSPACE | **Created:** 2024-04-05 | **Author:** qa.lead@company.com  
**Labels:** qa, testing, procedures, quality

## Testing Pyramid

### Unit Tests (70%)
- Test individual components in isolation
- Mock external dependencies
- Fast execution (< 1 second per test)

### Integration Tests (20%)
- Test component interactions
- Use test databases and services
- Medium execution time (1-10 seconds)

### E2E Tests (10%)
- Test complete user workflows
- Use production-like environment
- Slower execution (10+ seconds)

## Test Data Management

### Test Data Generation
```python
import faker
from datetime import datetime

fake = faker.Faker()

def generate_user_data(count=100):
    users = []
    for _ in range(count):
        user = {
            'id': fake.uuid4(),
            'name': fake.name(),
            'email': fake.email(),
            'created_at': fake.date_time_between(start_date='-1y', end_date='now')
        }
        users.append(user)
    return users
```

### Test Environment Setup
- Isolated test databases
- Mock external services
- Reproducible test data

## Automation Strategy
- Continuous integration pipeline
- Automated test execution on PR
- Test result reporting and analysis

## Performance Testing
- Load testing with realistic data volumes
- Stress testing to find breaking points
- Monitor response times and resource usage
"""
        }
    ]
    
    for doc in confluence_docs:
        filepath = os.path.join(CONFLUENCE_DIR, doc["filename"])
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(doc["content"])
        print(f"Created Confluence doc: {doc['filename']}")

def generate_jira_data():
    """Generate comprehensive Jira test data."""
    print("Generating Jira test data...")
    
    # Generate various Jira issues
    jira_issues = []
    
    # Epic issues
    for i in range(5):
        epic = {
            "key": f"API-{1000 + i}",
            "project": "API",
            "issue_type": "Epic",
            "summary": f"API Enhancement Epic {i+1}",
            "description": f"Major API enhancement initiative for Q{i%4+1} 2024",
            "status": random.choice(["In Progress", "Done", "To Do"]),
            "priority": random.choice(["High", "Medium", "Low"]),
            "reporter": "epic.owner@company.com",
            "assignee": "tech.lead@company.com",
            "labels": ["api", "enhancement", "epic"],
            "components": ["API Gateway", "Authentication"],
            "created": (datetime.now() - timedelta(days=random.randint(30, 180))).isoformat(),
            "updated": datetime.now().isoformat(),
            "comments": [
                {
                    "author": "tech.lead@company.com",
                    "body": "Breaking down epic into smaller stories",
                    "created": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
                }
            ]
        }
        jira_issues.append(epic)
    
    # Story issues
    for i in range(20):
        story = {
            "key": f"API-{2000 + i}",
            "project": "API",
            "issue_type": "Story",
            "summary": f"Implement {random.choice(['OAuth 2.0', 'Rate Limiting', 'Caching', 'Monitoring'])} Feature",
            "description": f"As a developer, I want to implement {random.choice(['secure authentication', 'performance optimization', 'error handling', 'logging'])} so that the API is more robust.",
            "status": random.choice(["To Do", "In Progress", "Code Review", "Done"]),
            "priority": random.choice(["High", "Medium", "Low"]),
            "story_points": random.choice([1, 2, 3, 5, 8]),
            "reporter": "product.owner@company.com",
            "assignee": f"developer{random.randint(1,5)}@company.com",
            "labels": ["story", "development", "api"],
            "epic_link": f"API-{1000 + random.randint(0, 4)}",
            "created": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
            "updated": datetime.now().isoformat(),
            "comments": [
                {
                    "author": "developer1@company.com",
                    "body": "Working on implementation, should be ready for review tomorrow",
                    "created": (datetime.now() - timedelta(days=random.randint(1, 10))).isoformat()
                },
                {
                    "author": "tech.lead@company.com", 
                    "body": "Please make sure to add unit tests",
                    "created": (datetime.now() - timedelta(days=random.randint(1, 5))).isoformat()
                }
            ]
        }
        jira_issues.append(story)
    
    # Bug issues
    for i in range(15):
        bug = {
            "key": f"API-{3000 + i}",
            "project": "API",
            "issue_type": "Bug",
            "summary": f"{random.choice(['Memory leak', 'Authentication failure', 'Timeout error', 'Data corruption'])} in {random.choice(['user service', 'payment service', 'notification service'])}",
            "description": f"Bug found in production affecting {random.choice(['user login', 'payment processing', 'email notifications'])}. Needs immediate attention.",
            "status": random.choice(["Open", "In Progress", "Resolved", "Closed"]),
            "priority": random.choice(["Critical", "High", "Medium"]),
            "severity": random.choice(["Blocker", "Major", "Minor"]),
            "reporter": "qa.tester@company.com",
            "assignee": f"developer{random.randint(1,5)}@company.com",
            "labels": ["bug", "production", "urgent"],
            "environment": random.choice(["production", "staging", "development"]),
            "created": (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat(),
            "updated": datetime.now().isoformat(),
            "comments": [
                {
                    "author": "qa.tester@company.com",
                    "body": "Bug reproduced in staging environment",
                    "created": (datetime.now() - timedelta(days=random.randint(1, 7))).isoformat()
                },
                {
                    "author": "developer2@company.com",
                    "body": "Root cause identified, working on fix",
                    "created": (datetime.now() - timedelta(days=random.randint(1, 3))).isoformat()
                }
            ]
        }
        jira_issues.append(bug)
    
    # Save all Jira issues
    jira_data = {
        "issues": jira_issues,
        "projects": [
            {
                "key": "API",
                "name": "API Development",
                "description": "API development and maintenance project"
            },
            {
                "key": "ARCH", 
                "name": "Architecture",
                "description": "System architecture and design decisions"
            }
        ]
    }
    
    jira_filepath = os.path.join(JIRA_DIR, "jira_issues.json")
    with open(jira_filepath, 'w', encoding='utf-8') as f:
        json.dump(jira_data, f, indent=2, ensure_ascii=False)
    print(f"Created Jira data: {len(jira_issues)} issues")

def generate_gitlab_data():
    """Generate comprehensive GitLab test data."""
    print("Generating GitLab test data...")
    
    # Generate GitLab repositories
    repositories = [
        {
            "name": "api-gateway",
            "description": "Main API Gateway service",
            "default_branch": "main",
            "visibility": "internal",
            "README.md": """# API Gateway Service

Central API Gateway for microservices architecture.

## Features
- Request routing
- Authentication & authorization  
- Rate limiting
- Request/response transformation
- Monitoring & analytics

## Quick Start
```bash
docker-compose up -d
```

## Configuration
See `config/gateway.yml` for detailed configuration options.

## API Documentation
Available at `/api/docs` when running locally.
""",
            "docs/deployment.md": """# Deployment Guide

## Development Environment
```bash
docker-compose up -d
```

## Production Environment
```bash
helm install api-gateway ./helm/api-gateway
```

## Environment Variables
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection for caching
- `JWT_SECRET`: Secret for JWT token validation
""",
            "issues": [
                {
                    "iid": 1,
                    "title": "Add rate limiting per user",
                    "description": "Implement per-user rate limiting to prevent abuse",
                    "state": "opened",
                    "labels": ["enhancement", "security"],
                    "author": "developer1@company.com"
                },
                {
                    "iid": 2, 
                    "title": "Performance optimization for routing",
                    "description": "Optimize request routing performance for high load",
                    "state": "closed",
                    "labels": ["performance", "optimization"],
                    "author": "developer2@company.com"
                }
            ],
            "merge_requests": [
                {
                    "iid": 1,
                    "title": "feat: Add health check endpoint",
                    "description": "Add comprehensive health check endpoint for monitoring",
                    "state": "merged",
                    "source_branch": "feature/health-check",
                    "target_branch": "main",
                    "author": "developer1@company.com"
                }
            ]
        },
        {
            "name": "auth-service",
            "description": "Authentication and authorization microservice",
            "default_branch": "main",
            "visibility": "internal",
            "README.md": """# Authentication Service

Handles user authentication and authorization.

## Features
- OAuth 2.0 / OpenID Connect
- JWT token management
- User management
- Role-based access control (RBAC)

## Tech Stack
- FastAPI (Python)
- PostgreSQL
- Redis
- Docker

## Development
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
""",
            "docs/api.md": """# Authentication API

## Endpoints

### POST /auth/login
Authenticate user and return access token.

### POST /auth/refresh
Refresh access token using refresh token.

### GET /auth/user
Get current user information.

### POST /auth/logout
Invalidate user session.
""",
            "issues": [
                {
                    "iid": 3,
                    "title": "Implement OAuth 2.0 PKCE flow",
                    "description": "Add PKCE support for mobile applications",
                    "state": "opened",
                    "labels": ["enhancement", "oauth", "mobile"],
                    "author": "security.engineer@company.com"
                }
            ],
            "merge_requests": [
                {
                    "iid": 2,
                    "title": "fix: Token expiration validation",
                    "description": "Fix token expiration validation logic",
                    "state": "merged",
                    "source_branch": "bugfix/token-validation",
                    "target_branch": "main",
                    "author": "developer3@company.com"
                }
            ]
        },
        {
            "name": "microservices-demo",
            "description": "Demo application showcasing microservices patterns",
            "default_branch": "main",
            "visibility": "public",
            "README.md": """# Microservices Demo

Demonstration of microservices architecture patterns and best practices.

## Services
- User Service
- Order Service  
- Payment Service
- Notification Service
- API Gateway

## Architecture Patterns
- Database per service
- Event-driven communication
- Circuit breaker
- Distributed tracing

## Getting Started
```bash
docker-compose up -d
```

Visit http://localhost:8080 for the demo application.
""",
            "docs/architecture.md": """# Architecture Overview

## Service Dependencies
```
API Gateway -> User Service
            -> Order Service -> Payment Service
                            -> Notification Service
```

## Communication Patterns
- Synchronous: REST APIs for real-time operations
- Asynchronous: Event bus for eventual consistency

## Data Management
Each service has its own database to ensure loose coupling.
""",
            "issues": [
                {
                    "iid": 4,
                    "title": "Add distributed tracing",
                    "description": "Implement distributed tracing with Jaeger",
                    "state": "opened", 
                    "labels": ["observability", "tracing"],
                    "author": "devops.engineer@company.com"
                },
                {
                    "iid": 5,
                    "title": "Implement saga pattern for orders",
                    "description": "Use saga pattern for distributed order transactions",
                    "state": "opened",
                    "labels": ["pattern", "distributed-transactions"],
                    "author": "architect@company.com"
                }
            ]
        }
    ]
    
    # Save each repository data
    for repo in repositories:
        repo_dir = os.path.join(GITLAB_DIR, repo["name"])
        os.makedirs(repo_dir, exist_ok=True)
        
        # Save README and docs
        for filename, content in repo.items():
            if filename.endswith('.md'):
                filepath = os.path.join(repo_dir, filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        # Save metadata
        metadata = {
            "name": repo["name"],
            "description": repo["description"], 
            "default_branch": repo["default_branch"],
            "visibility": repo["visibility"],
            "issues": repo["issues"],
            "merge_requests": repo.get("merge_requests", [])
        }
        
        metadata_filepath = os.path.join(repo_dir, "gitlab_metadata.json")
        with open(metadata_filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"Created GitLab data: {len(repositories)} repositories")

def generate_training_dataset():
    """Generate training dataset based on dataset_config.yml."""
    print("Generating training dataset...")
    
    # Load dataset configuration
    try:
        with open('dataset_config.yml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("dataset_config.yml not found, using default configuration")
        config = {
            "synthetic_data": {
                "technical_docs": [
                    {"category": "authentication", "language": "ru", "count": 50},
                    {"category": "authentication", "language": "en", "count": 50},
                    {"category": "microservices", "language": "ru", "count": 40},
                    {"category": "microservices", "language": "en", "count": 40}
                ]
            },
            "training_pairs": {
                "semantic_search": [
                    {
                        "query": "Как реализовать OAuth 2.0 аутентификацию?",
                        "language": "ru",
                        "expected_docs": ["oauth2_guide_ru.md"],
                        "relevance_scores": [0.95]
                    },
                    {
                        "query": "How to implement OAuth 2.0 authentication?", 
                        "language": "en",
                        "expected_docs": ["oauth2_guide_en.md"],
                        "relevance_scores": [0.95]
                    }
                ]
            }
        }
    
    # Generate synthetic documents
    synthetic_docs = []
    templates = {
        "authentication": {
            "ru": [
                "Руководство по аутентификации",
                "Безопасность API и методы аутентификации",
                "Реализация OAuth 2.0 в микросервисах",
                "JWT токены: лучшие практики",
                "Двухфакторная аутентификация"
            ],
            "en": [
                "Authentication Guide",
                "API Security and Authentication Methods", 
                "Implementing OAuth 2.0 in Microservices",
                "JWT Tokens: Best Practices",
                "Two-Factor Authentication"
            ]
        },
        "microservices": {
            "ru": [
                "Архитектура микросервисов",
                "Паттерны проектирования микросервисов",
                "Мониторинг распределенных систем",
                "Service Mesh и Istio",
                "Развертывание микросервисов с Docker"
            ],
            "en": [
                "Microservices Architecture",
                "Microservices Design Patterns",
                "Monitoring Distributed Systems", 
                "Service Mesh and Istio",
                "Deploying Microservices with Docker"
            ]
        }
    }
    
    # Generate training pairs
    training_pairs = []
    for pair in config.get("training_pairs", {}).get("semantic_search", []):
        training_pairs.append({
            "query": pair["query"],
            "language": pair["language"],
            "expected_docs": pair["expected_docs"],
            "relevance_scores": pair["relevance_scores"],
            "id": str(uuid.uuid4())
        })
    
    # Save training dataset
    dataset = {
        "metadata": {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "total_documents": len(synthetic_docs),
            "languages": ["ru", "en"],
            "categories": ["authentication", "microservices"]
        },
        "documents": synthetic_docs,
        "training_pairs": training_pairs
    }
    
    dataset_filepath = os.path.join(DATASET_DIR, "training_dataset.json")
    with open(dataset_filepath, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    # Save embedding evaluation data
    evaluation_data = {
        "queries": [
            {"text": "OAuth 2.0 implementation", "language": "en", "category": "authentication"},
            {"text": "Реализация OAuth 2.0", "language": "ru", "category": "authentication"},
            {"text": "microservices patterns", "language": "en", "category": "microservices"},
            {"text": "паттерны микросервисов", "language": "ru", "category": "microservices"}
        ],
        "expected_similarities": [
            {"query1": 0, "query2": 1, "similarity": 0.9},  # Same topic, different languages
            {"query1": 2, "query2": 3, "similarity": 0.9}   # Same topic, different languages
        ]
    }
    
    eval_filepath = os.path.join(DATASET_DIR, "evaluation_data.json")
    with open(eval_filepath, 'w', encoding='utf-8') as f:
        json.dump(evaluation_data, f, indent=2, ensure_ascii=False)
    
    print(f"Created training dataset with {len(training_pairs)} training pairs")

def create_data_summary():
    """Create summary of all generated test data."""
    summary = {
        "generated_at": datetime.now().isoformat(),
        "test_data_structure": {
            "confluence": {
                "spaces": ["TECH", "ARCH", "DEV", "TESTSPACE"],
                "documents": 4,
                "content_types": ["technical_guides", "architecture_docs", "qa_procedures"]
            },
            "jira": {
                "projects": ["API", "ARCH"],
                "issues": 40,
                "issue_types": ["Epic", "Story", "Bug"]
            },
            "gitlab": {
                "repositories": 3,
                "files": ["README.md", "docs/*.md"],
                "issues": 5,
                "merge_requests": 3
            },
            "dataset": {
                "training_pairs": "variable",
                "evaluation_queries": 4,
                "languages": ["ru", "en"]
            }
        },
        "usage": {
            "e2e_tests": "Use this data for comprehensive E2E testing",
            "model_training": "Training dataset for semantic search improvement",
            "integration_testing": "Test data source integrations"
        }
    }
    
    summary_filepath = os.path.join(TEST_DATA_DIR, "data_summary.json")
    with open(summary_filepath, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"Created data summary: {summary_filepath}")

def main():
    """Generate all test data."""
    print("🚀 Generating comprehensive test data for E2E testing...")
    print("=" * 60)
    
    create_directories()
    generate_confluence_data()
    generate_jira_data() 
    generate_gitlab_data()
    generate_training_dataset()
    create_data_summary()
    
    print("=" * 60)
    print("✅ Test data generation completed!")
    print(f"📁 All data saved in: {TEST_DATA_DIR}/")
    print("🔍 Check data_summary.json for overview")

if __name__ == "__main__":
    main() 