#!/usr/bin/env python3
"""
🚀 Enhanced RFC Generator with Mermaid Diagrams Demo
Демонстрация enhanced RFC generation с анализом архитектуры и автогенерацией диаграмм
Phase 2: Complete RFC Generation with diagrams and project analysis
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from domain.rfc_generation.rfc_generator_service import RFCGeneratorService, RFCRequest
from domain.rfc_generation.rfc_analyzer import analyze_project_architecture, quick_health_check
from domain.core.mermaid_diagram_generator import generate_all_diagrams

class EnhancedRFCGeneratorDemo:
    """Enhanced RFC Generator demonstration with real examples"""
    
    def __init__(self):
        self.rfc_generator = RFCGeneratorService()
        self.demo_project_path = "."  # Current project as demo
        
    async def run_demo(self):
        """Run complete Enhanced RFC Generator demonstration"""
        
        print("🚀 " + "="*80)
        print("   ENHANCED RFC GENERATOR WITH MERMAID DIAGRAMS - PHASE 2")
        print("   Complete RFC generation with architecture analysis & diagrams")
        print("="*84)
        
        # Demo scenarios
        scenarios = [
            self.demo_1_simple_rfc_with_diagrams,
            self.demo_2_full_project_analysis_rfc,
            self.demo_3_microservices_architecture_rfc,
            self.demo_4_api_gateway_design_rfc,
            self.demo_5_performance_optimization_rfc,
            self.demo_6_standalone_project_analysis
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n🎯 Demo {i}: {scenario.__name__.replace('demo_', '').replace('_', ' ').title()}")
            print("-" * 70)
            
            try:
                await scenario()
                print("✅ Demo completed successfully!\n")
                
                # Pause between demos
                if i < len(scenarios):
                    input("Press Enter to continue to next demo...")
                    
            except Exception as e:
                print(f"❌ Demo failed: {e}\n")
                import traceback
                traceback.print_exc()
        
        print("\n🎉 All Enhanced RFC Generator demos completed!")
        print("📁 Check generated RFCs in: /tmp/enhanced_rfc_outputs/")
    
    async def demo_1_simple_rfc_with_diagrams(self):
        """Demo 1: Simple RFC with automatic diagram generation"""
        
        print("📝 Generating RFC with automatic Mermaid diagrams...")
        
        request = RFCRequest(
            title="Enhanced API Rate Limiting with Redis",
            description="""
Implement comprehensive API rate limiting using Redis to protect services from abuse.

Current State:
- Basic in-memory rate limiting exists but not persistent
- No distributed rate limiting across instances
- Limited monitoring and alerting
- No graceful degradation strategies

Proposed Solution:
- Redis-based distributed rate limiting
- Token bucket algorithm with different tiers
- Real-time monitoring dashboard
- Automatic circuit breaker integration
- Graceful degradation under Redis failure

Technical Requirements:
- Sub-10ms latency impact
- Support for 100K+ requests/second
- Multi-tier rate limiting (user, API key, IP)
- Configurable limits via admin API
            """,
            rfc_type="architecture",
            include_diagrams=True,
            include_analysis=False,
            author="Platform Engineering",
            stakeholders=["API Team", "DevOps", "Security", "Product"],
            custom_sections={
                "Rate Limiting Algorithms": "Token bucket vs sliding window comparison",
                "Redis Architecture": "High availability setup with sentinel",
                "Monitoring Strategy": "Real-time metrics and alerting"
            }
        )
        
        # Generate RFC with diagrams
        rfc = await self.rfc_generator.generate_rfc(request)
        
        # Display results
        self._display_rfc_summary(rfc)
        
        # Save to file
        await self._save_rfc_to_file(rfc, "demo_1_api_rate_limiting_enhanced.md")
    
    async def demo_2_full_project_analysis_rfc(self):
        """Demo 2: RFC with complete project codebase analysis"""
        
        print("🏗️ Generating RFC with full project analysis...")
        
        # First, analyze current project
        print("  🔍 Analyzing current project architecture...")
        try:
            analysis = await analyze_project_architecture(self.demo_project_path)
            print(f"  📊 Analysis completed:")
            print(f"    - Components: {len(analysis.components)}")
            print(f"    - Technologies: {', '.join(list(analysis.technology_inventory.keys())[:5])}")
            print(f"    - Files analyzed: {analysis.metrics.get('total_files', 0)}")
            print(f"    - Recommendations: {len(analysis.improvement_suggestions)}")
        except Exception as e:
            print(f"  ⚠️ Analysis failed: {e}")
            analysis = None
        
        request = RFCRequest(
            title="AI Assistant Platform - Microservices Architecture Evolution",
            description="""
Transform the AI Assistant platform into a scalable microservices architecture.

Based on comprehensive codebase analysis, we need to address:

Current Architecture Challenges:
- Monolithic structure limiting independent deployment
- Tight coupling between AI services and web API
- Database connection pooling inefficiencies  
- Limited horizontal scaling capabilities
- Mixed concerns in single codebase

Proposed Microservices Architecture:
- Separate AI Processing Service (Python/FastAPI)
- Web API Gateway Service (Node.js/Express)
- Vector Search Service (Python/Elasticsearch)
- User Management Service (Python/PostgreSQL)
- Analytics & Monitoring Service (Go/InfluxDB)
- Real-time Communication Service (Node.js/WebSocket)

Goals:
- Independent service deployments
- Technology diversity where appropriate
- Improved fault isolation
- 10x scalability improvement
- Sub-200ms API response times
- 99.9% uptime SLA
            """,
            project_path=self.demo_project_path,
            rfc_type="architecture",
            include_diagrams=True,
            include_analysis=True,
            author="Chief Architect",
            stakeholders=["Engineering Leadership", "DevOps", "Product", "QA"],
            custom_sections={
                "Service Boundaries": "Domain-driven design with bounded contexts",
                "Data Architecture": "Database-per-service with event sourcing",
                "Communication Patterns": "Async messaging with Kafka + REST APIs",
                "Migration Strategy": "Strangler fig pattern with 6-month timeline",
                "Monitoring & Observability": "Distributed tracing with Jaeger"
            }
        )
        
        # Generate enhanced RFC with analysis
        rfc = await self.rfc_generator.generate_rfc(request)
        
        # Display results with analysis
        self._display_rfc_summary(rfc, show_analysis=True)
        
        # Save enhanced RFC
        await self._save_rfc_to_file(rfc, "demo_2_microservices_evolution.md")
    
    async def demo_3_microservices_architecture_rfc(self):
        """Demo 3: Complex microservices design RFC with multiple diagrams"""
        
        print("🔄 Generating comprehensive microservices architecture RFC...")
        
        request = RFCRequest(
            title="E-commerce Platform - Cloud-Native Microservices Architecture",
            description="""
Design a cloud-native e-commerce platform using microservices architecture.

Business Requirements:
- Support 1M+ active users
- Global deployment across multiple regions
- 99.99% uptime requirement
- Black Friday traffic spikes (100x normal load)
- Real-time inventory management
- Personalized recommendations
- Multi-payment gateway support

Core Services:
1. User Service - Authentication, profiles, preferences
2. Product Catalog Service - Product information, search, categories
3. Inventory Service - Stock management, reservations
4. Order Service - Order processing, state management
5. Payment Service - Payment processing, refunds
6. Notification Service - Email, SMS, push notifications
7. Recommendation Service - ML-based product recommendations
8. Analytics Service - User behavior, business metrics

Infrastructure:
- Kubernetes on AWS/GCP/Azure
- Service mesh (Istio) for communication
- Event-driven architecture with Kafka
- CQRS for read/write separation
- Distributed caching with Redis
- Multi-region database replication
            """,
            rfc_type="architecture",
            include_diagrams=True,
            include_analysis=False,
            author="Solution Architect",
            stakeholders=["Engineering", "DevOps", "Business", "Security", "Data Team"],
            custom_sections={
                "Service Mesh Configuration": "Istio setup for traffic management",
                "Event Sourcing Strategy": "Kafka event streams and projections",
                "Security Architecture": "Zero-trust with mutual TLS",
                "Disaster Recovery": "Multi-region failover strategy",
                "Performance Targets": "Latency and throughput SLAs"
            }
        )
        
        rfc = await self.rfc_generator.generate_rfc(request)
        
        self._display_rfc_summary(rfc)
        await self._save_rfc_to_file(rfc, "demo_3_ecommerce_microservices.md")
    
    async def demo_4_api_gateway_design_rfc(self):
        """Demo 4: API Gateway design with sequence diagrams"""
        
        print("🔌 Generating API Gateway design RFC...")
        
        request = RFCRequest(
            title="Enterprise API Gateway - Design & Implementation",
            description="""
Design and implement a comprehensive API Gateway for enterprise services.

Current Challenges:
- Direct service-to-service communication creating tight coupling
- No centralized authentication or rate limiting
- Difficult API versioning and deprecation
- Limited observability and monitoring
- Security concerns with direct service exposure

API Gateway Features:
- Centralized authentication (JWT, OAuth 2.0, API keys)
- Request/response transformation
- Rate limiting and throttling
- Circuit breaker pattern implementation
- API versioning and routing
- Request/response caching
- Comprehensive logging and metrics
- Load balancing and health checks
- Protocol translation (REST ↔ GraphQL ↔ gRPC)

Technical Implementation:
- Kong Gateway with custom plugins
- Redis for rate limiting and caching
- Prometheus for metrics collection
- Grafana for monitoring dashboards
- ELK stack for centralized logging
- Consul for service discovery
            """,
            rfc_type="api",
            include_diagrams=True,
            include_analysis=False,
            author="API Platform Team",
            stakeholders=["Backend Teams", "Frontend Teams", "DevOps", "Security"],
            custom_sections={
                "Authentication Flows": "JWT and OAuth 2.0 implementation details",
                "Rate Limiting Strategy": "Token bucket with Redis persistence",
                "Plugin Architecture": "Custom Kong plugins for business logic",
                "Monitoring & Alerting": "SLA monitoring and incident response"
            }
        )
        
        rfc = await self.rfc_generator.generate_rfc(request)
        
        self._display_rfc_summary(rfc)
        await self._save_rfc_to_file(rfc, "demo_4_api_gateway_design.md")
    
    async def demo_5_performance_optimization_rfc(self):
        """Demo 5: Performance optimization RFC with benchmarks"""
        
        print("⚡ Generating performance optimization RFC...")
        
        request = RFCRequest(
            title="Vector Search Performance Optimization - 10x Improvement",
            description="""
Optimize vector search performance to achieve 10x improvement in latency and throughput.

Current Performance Issues:
- Average search latency: 2.5 seconds (target: <250ms)
- Throughput: 50 RPS (target: 500+ RPS)
- Memory usage: 8GB for 1M vectors (target: <4GB)
- Cold start time: 30 seconds (target: <5 seconds)
- Search accuracy declining with large datasets

Root Cause Analysis:
- Inefficient vector similarity algorithms
- No index optimization or pruning
- Single-threaded search execution
- Poor memory layout and caching
- No result caching strategy

Optimization Strategy:
1. Algorithm Improvements:
   - HNSW (Hierarchical Navigable Small World) index
   - Product quantization for memory efficiency
   - Parallel search execution
   - Smart index partitioning

2. Infrastructure Optimizations:
   - GPU acceleration for similarity computation
   - In-memory caching with Redis
   - Connection pooling optimization
   - Async I/O improvements

3. Search Quality Enhancements:
   - Hybrid search (semantic + keyword)
   - Dynamic re-ranking based on user context
   - Query expansion and reformulation
   - A/B testing framework for relevance

Performance Targets:
- <250ms search latency (95th percentile)
- 500+ concurrent searches/second
- <4GB memory usage for 1M vectors
- 95%+ search accuracy maintained
- <5 second cold start time
            """,
            rfc_type="design",
            include_diagrams=True,
            include_analysis=False,
            author="Performance Engineering",
            stakeholders=["Search Team", "Data Science", "DevOps", "Product"],
            custom_sections={
                "Benchmarking Strategy": "Performance testing methodology",
                "Vector Index Optimization": "HNSW vs IVF-PQ comparison",
                "GPU Acceleration": "CUDA implementation for similarity search",
                "Caching Strategy": "Multi-level caching architecture"
            }
        )
        
        rfc = await self.rfc_generator.generate_rfc(request)
        
        self._display_rfc_summary(rfc)
        await self._save_rfc_to_file(rfc, "demo_5_performance_optimization.md")
    
    async def demo_6_standalone_project_analysis(self):
        """Demo 6: Standalone project analysis with comprehensive diagrams"""
        
        print("🔍 Running comprehensive project architecture analysis...")
        
        try:
            # Quick health check first
            print("  📊 Running health assessment...")
            health = await quick_health_check(self.demo_project_path)
            print(f"  🏥 Project Health Score: {health.get('health_score', 'Unknown')}/100")
            
            if health.get('health_score', 0) > 0:
                print(f"    - Components: {health.get('components_count', 0)}")
                print(f"    - Technologies: {', '.join(health.get('technologies', []))}")
                
                top_suggestions = health.get('top_suggestions', [])
                if top_suggestions:
                    print(f"    - Top Recommendations:")
                    for suggestion in top_suggestions[:3]:
                        print(f"      • {suggestion}")
            
            # Full detailed analysis
            print("  🔍 Running detailed architecture analysis...")
            analysis = await analyze_project_architecture(self.demo_project_path)
            
            # Generate comprehensive diagrams
            print("  📈 Generating comprehensive Mermaid diagrams...")
            diagrams = await generate_all_diagrams(analysis)
            
            # Display detailed analysis results
            self._display_comprehensive_analysis(analysis, diagrams)
            
            # Save detailed analysis report
            await self._save_analysis_report(analysis, diagrams, "demo_6_comprehensive_analysis.md")
            
        except Exception as e:
            print(f"  ❌ Analysis failed: {e}")
            print("  ℹ️ This might happen if running outside a proper Python project")
            
            # Show sample analysis for demo purposes
            await self._show_sample_analysis()
    
    async def _show_sample_analysis(self):
        """Show sample analysis for demo when real analysis fails"""
        
        print("  📋 Showing sample analysis results...")
        
        sample_analysis = {
            "components": [
                {"name": "api", "type": "api", "files": 25, "tech": ["fastapi", "pydantic"]},
                {"name": "services", "type": "service", "files": 30, "tech": ["python", "asyncio"]},
                {"name": "frontend", "type": "frontend", "files": 45, "tech": ["react", "typescript"]},
                {"name": "database", "type": "database", "files": 8, "tech": ["postgresql", "sqlalchemy"]}
            ],
            "technologies": ["Python", "FastAPI", "React", "TypeScript", "PostgreSQL", "Redis"],
            "recommendations": [
                "Consider implementing microservices architecture",
                "Add comprehensive API documentation",
                "Implement distributed caching strategy",
                "Add performance monitoring and alerting"
            ]
        }
        
        print(f"    📊 Sample Components: {len(sample_analysis['components'])}")
        for comp in sample_analysis['components']:
            print(f"      - {comp['name']} ({comp['type']}): {comp['files']} files")
        
        print(f"    🛠️ Technologies: {', '.join(sample_analysis['technologies'])}")
        print(f"    💡 Sample Recommendations:")
        for rec in sample_analysis['recommendations']:
            print(f"      • {rec}")
    
    def _display_rfc_summary(self, rfc, show_analysis=False):
        """Display RFC generation summary with enhanced details"""
        
        print(f"📄 RFC Generated:")
        print(f"  📋 Title: {rfc.title}")
        print(f"  🆔 RFC ID: {rfc.rfc_id}")
        print(f"  📏 Content: {len(rfc.content):,} characters ({len(rfc.content.split())} words)")
        print(f"  📑 Sections: {len(rfc.sections)}")
        
        # Display section details
        if rfc.sections:
            print(f"    Sections:")
            for section in rfc.sections[:5]:  # Show first 5 sections
                print(f"      - {section.title} ({len(section.content)} chars)")
            if len(rfc.sections) > 5:
                print(f"      ... and {len(rfc.sections) - 5} more sections")
        
        # Display diagram details
        if rfc.diagrams:
            print(f"  📊 Diagrams: {len(rfc.diagrams)}")
            for name, diagram in rfc.diagrams.items():
                diagram_title = name.replace('_', ' ').title()
                lines = len(diagram.split('\n'))
                print(f"    - {diagram_title} ({lines} lines)")
        
        # Display analysis details
        if show_analysis and rfc.analysis:
            print(f"  🔍 Architecture Analysis:")
            print(f"    - Components: {len(rfc.analysis.components)}")
            print(f"    - Technologies: {len(rfc.analysis.technology_inventory)}")
            print(f"    - Dependencies: {len(rfc.analysis.dependencies_graph)}")
            print(f"    - Recommendations: {len(rfc.analysis.improvement_suggestions)}")
            
            if rfc.analysis.improvement_suggestions:
                print(f"    Top Recommendations:")
                for suggestion in rfc.analysis.improvement_suggestions[:3]:
                    print(f"      • {suggestion}")
        
        # Display metadata
        print(f"  ⏱️ Generation Time: {rfc.metadata.get('generation_time', 'Unknown')}")
        print(f"  💰 Estimated Tokens: ~{len(rfc.content) // 4:,}")
        print(f"  👤 Author: {rfc.metadata.get('author', 'Unknown')}")
    
    def _display_comprehensive_analysis(self, analysis, diagrams):
        """Display comprehensive analysis results"""
        
        print(f"📊 Comprehensive Analysis Results:")
        print(f"  🏗️ Architecture Overview:")
        print(f"    - Total Components: {len(analysis.components)}")
        print(f"    - Total Files: {analysis.metrics.get('total_files', 0)}")
        print(f"    - Average Files per Component: {analysis.metrics.get('avg_files_per_component', 0)}")
        
        print(f"  📦 Components Detail:")
        for comp in analysis.components:
            tech_list = ', '.join(comp.technology_stack) if comp.technology_stack else 'Unknown'
            interfaces_count = len(comp.interfaces) if comp.interfaces else 0
            print(f"    - {comp.name} ({comp.service_type})")
            print(f"      • Files: {len(comp.files)}")
            print(f"      • Technologies: {tech_list}")
            print(f"      • Interfaces: {interfaces_count}")
        
        print(f"  🛠️ Technology Inventory:")
        for tech, count in analysis.technology_inventory.items():
            print(f"    - {tech}: {count} occurrences")
        
        print(f"  🔗 Dependencies:")
        for comp, deps in analysis.dependencies_graph.items():
            if deps:
                print(f"    - {comp} → {', '.join(deps)}")
        
        print(f"  💡 Architecture Recommendations:")
        for i, suggestion in enumerate(analysis.improvement_suggestions, 1):
            print(f"    {i}. {suggestion}")
        
        print(f"  📈 Generated Diagrams:")
        for name, diagram in diagrams.items():
            diagram_title = name.replace('_', ' ').title()
            complexity = "Simple" if len(diagram.split('\n')) < 20 else "Complex"
            print(f"    - {diagram_title} ({complexity})")
    
    async def _save_rfc_to_file(self, rfc, filename):
        """Save RFC to enhanced markdown file with metadata"""
        
        output_dir = Path("/tmp/enhanced_rfc_outputs")
        output_dir.mkdir(exist_ok=True)
        
        file_path = output_dir / filename
        
        # Create enhanced content with YAML frontmatter
        content = f"""---
title: "{rfc.title}"
rfc_id: "{rfc.rfc_id}"
author: "{rfc.metadata.get('author', 'Enhanced RFC Demo')}"
created: "{rfc.metadata.get('timestamp', 'Demo Generated')}"
rfc_type: "{rfc.metadata.get('rfc_type', 'architecture')}"
sections_count: {len(rfc.sections)}
diagrams_count: {len(rfc.diagrams)}
content_length: {len(rfc.content)}
has_analysis: {bool(rfc.analysis)}
stakeholders: {rfc.metadata.get('stakeholders', [])}
---

# {rfc.title}

> **Generated by Enhanced RFC Generator v2.0**  
> **RFC ID**: {rfc.rfc_id}  
> **Author**: {rfc.metadata.get('author', 'Demo User')}  
> **Type**: {rfc.metadata.get('rfc_type', 'architecture').title()}  

{rfc.content}
"""
        
        # Add diagrams section if present
        if rfc.diagrams:
            content += "\n\n---\n\n## 📊 Architecture Diagrams\n\n"
            content += "*Auto-generated Mermaid diagrams based on requirements and analysis*\n\n"
            
            for name, diagram_code in rfc.diagrams.items():
                diagram_title = name.replace('_', ' ').title()
                content += f"### {diagram_title}\n\n```mermaid\n{diagram_code}\n```\n\n"
        
        # Add analysis section if present
        if rfc.analysis:
            content += "\n\n---\n\n## 🔍 Project Analysis Summary\n\n"
            content += f"*Based on codebase analysis of: {rfc.analysis.metrics.get('project_path', 'Project')}*\n\n"
            
            content += f"### Architecture Overview\n\n"
            content += f"- **Components Analyzed**: {len(rfc.analysis.components)}\n"
            content += f"- **Total Files**: {rfc.analysis.metrics.get('total_files', 0)}\n"
            content += f"- **Technologies Detected**: {', '.join(rfc.analysis.technology_inventory.keys())}\n\n"
            
            if rfc.analysis.improvement_suggestions:
                content += f"### Key Recommendations\n\n"
                for i, suggestion in enumerate(rfc.analysis.improvement_suggestions, 1):
                    content += f"{i}. {suggestion}\n"
                content += "\n"
        
        # Add generation metadata
        content += "\n\n---\n\n## 📋 Generation Metadata\n\n"
        content += f"- **Generated**: {rfc.metadata.get('timestamp', 'Demo Session')}\n"
        content += f"- **Content Length**: {len(rfc.content):,} characters\n"
        content += f"- **Word Count**: ~{len(rfc.content.split())} words\n"
        content += f"- **Sections**: {len(rfc.sections)}\n"
        content += f"- **Diagrams**: {len(rfc.diagrams)}\n"
        content += f"- **Estimated Reading Time**: ~{len(rfc.content.split()) // 200} minutes\n"
        
        if rfc.analysis:
            content += f"- **Architecture Analysis**: ✅ Included\n"
            content += f"  - Components Analyzed: {len(rfc.analysis.components)}\n"
            content += f"  - Technologies Detected: {len(rfc.analysis.technology_inventory)}\n"
            content += f"  - Recommendations: {len(rfc.analysis.improvement_suggestions)}\n"
        else:
            content += f"- **Architecture Analysis**: ❌ Not performed\n"
        
        # Add enhancement features summary
        content += f"\n### Enhancement Features Used\n\n"
        content += f"- ✅ Professional RFC Template\n"
        content += f"- {'✅' if rfc.diagrams else '❌'} Automatic Mermaid Diagrams\n"
        content += f"- {'✅' if rfc.analysis else '❌'} Codebase Architecture Analysis\n"
        content += f"- ✅ Multi-section RFC Structure\n"
        content += f"- ✅ Stakeholder Integration\n"
        content += f"- ✅ Enhanced Metadata\n"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"💾 Enhanced RFC saved to: {file_path}")
        print(f"    📊 File size: {len(content.encode('utf-8')) / 1024:.1f} KB")
    
    async def _save_analysis_report(self, analysis, diagrams, filename):
        """Save comprehensive analysis report"""
        
        output_dir = Path("/tmp/enhanced_rfc_outputs")
        output_dir.mkdir(exist_ok=True)
        
        file_path = output_dir / filename
        
        # Create comprehensive analysis report
        content = f"""# 🔍 Comprehensive Project Architecture Analysis

> **Generated by Enhanced RFC Analyzer v2.0**  
> **Analysis Date**: {analysis.metrics.get('timestamp', 'Demo Session')}  
> **Project Path**: {analysis.metrics.get('project_path', self.demo_project_path)}  

## 📊 Executive Summary

- **Total Components**: {len(analysis.components)}
- **Total Files Analyzed**: {analysis.metrics.get('total_files', 0)}
- **Technologies Detected**: {len(analysis.technology_inventory)}
- **Architecture Recommendations**: {len(analysis.improvement_suggestions)}
- **Generated Diagrams**: {len(diagrams)}

## 🏗️ Component Architecture

"""
        
        for i, comp in enumerate(analysis.components, 1):
            content += f"""### {i}. {comp.name} ({comp.service_type.title()})

**Overview:**
- **Type**: {comp.service_type.title()} Service
- **Files**: {len(comp.files)} files
- **Technology Stack**: {', '.join(comp.technology_stack) if comp.technology_stack else 'Not detected'}
- **API Endpoints**: {len(comp.interfaces)} endpoints
- **Dependencies**: {', '.join(comp.dependencies) if comp.dependencies else 'None detected'}

**Key Files:**
"""
            # Show first few files
            for file in comp.files[:5]:
                content += f"- `{file}`\n"
            if len(comp.files) > 5:
                content += f"- ... and {len(comp.files) - 5} more files\n"
            
            if comp.interfaces:
                content += f"\n**API Interfaces:**\n"
                for interface in comp.interfaces[:5]:
                    content += f"- `{interface}`\n"
                if len(comp.interfaces) > 5:
                    content += f"- ... and {len(comp.interfaces) - 5} more endpoints\n"
            
            content += "\n"
        
        # Technology inventory
        content += "\n## 🛠️ Technology Stack Analysis\n\n"
        for tech, count in sorted(analysis.technology_inventory.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / max(analysis.technology_inventory.values())) * 100
            bar = "█" * min(int(percentage / 10), 10)
            content += f"- **{tech}**: {count} occurrences {bar}\n"
        
        # Dependencies analysis
        content += "\n## 🔗 Component Dependencies\n\n"
        if any(analysis.dependencies_graph.values()):
            content += "```\n"
            for comp, deps in analysis.dependencies_graph.items():
                if deps:
                    content += f"{comp} → {', '.join(deps)}\n"
            content += "```\n"
        else:
            content += "*No explicit dependencies detected between components.*\n"
        
        # Metrics summary
        content += f"\n## 📈 Project Metrics\n\n"
        for metric, value in analysis.metrics.items():
            if isinstance(value, dict):
                content += f"**{metric.replace('_', ' ').title()}:**\n"
                for k, v in value.items():
                    content += f"- {k}: {v}\n"
            else:
                content += f"- **{metric.replace('_', ' ').title()}**: {value}\n"
        
        # Recommendations
        content += "\n## 💡 Architecture Improvement Recommendations\n\n"
        if analysis.improvement_suggestions:
            for i, suggestion in enumerate(analysis.improvement_suggestions, 1):
                content += f"{i}. **{suggestion}**\n"
                content += f"   *Priority: Medium | Impact: High*\n\n"
        else:
            content += "*No specific recommendations generated.*\n"
        
        # Diagrams section
        if diagrams:
            content += "\n## 📈 Generated Architecture Diagrams\n\n"
            content += "*Auto-generated Mermaid diagrams based on codebase analysis*\n\n"
            
            for name, diagram_code in diagrams.items():
                diagram_title = name.replace('_', ' ').title()
                content += f"### {diagram_title}\n\n"
                content += f"```mermaid\n{diagram_code}\n```\n\n"
        
        # Analysis metadata
        content += "\n---\n\n## 📋 Analysis Metadata\n\n"
        content += f"- **Analysis Engine**: Enhanced RFC Analyzer v2.0\n"
        content += f"- **Analysis Duration**: {analysis.metrics.get('analysis_time', 'Unknown')}\n"
        content += f"- **Files Scanned**: {analysis.metrics.get('total_files', 0)}\n"
        content += f"- **Patterns Detected**: {len(analysis.technology_inventory)}\n"
        content += f"- **Diagrams Generated**: {len(diagrams)}\n"
        content += f"- **Report Size**: ~{len(content.split())} words\n"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"💾 Comprehensive analysis report saved to: {file_path}")
        print(f"    📊 Report size: {len(content.encode('utf-8')) / 1024:.1f} KB")

async def main():
    """Main demo runner"""
    demo = EnhancedRFCGeneratorDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main()) 