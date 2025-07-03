#!/usr/bin/env python3
"""
🚀 RFC Generator with Mermaid Diagrams Demo
Демонстрация enhanced RFC generation с анализом архитектуры и автогенерацией диаграмм
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

class RFCGeneratorDemo:
    """RFC Generator demonstration with real examples"""
    
    def __init__(self):
        self.rfc_generator = RFCGeneratorService()
        self.demo_project_path = "."  # Current project as demo
        
    async def run_demo(self):
        """Run complete RFC Generator demonstration"""
        
        print("🚀 " + "="*80)
        print("   RFC GENERATOR WITH MERMAID DIAGRAMS - PHASE 2 DEMO")
        print("   Enhanced RFC generation with architecture analysis")
        print("="*84)
        
        # Demo scenarios
        scenarios = [
            self.demo_1_simple_rfc,
            self.demo_2_architecture_rfc_with_analysis,
            self.demo_3_microservices_migration_rfc,
            self.demo_4_api_design_rfc,
            self.demo_5_project_analysis_only
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n🎯 Demo {i}: {scenario.__name__.replace('demo_', '').replace('_', ' ').title()}")
            print("-" * 60)
            
            try:
                await scenario()
                print("✅ Demo completed successfully!\n")
                
                # Pause between demos
                if i < len(scenarios):
                    input("Press Enter to continue to next demo...")
                    
            except Exception as e:
                print(f"❌ Demo failed: {e}\n")
        
        print("\n🎉 All RFC Generator demos completed!")
        print("Check generated RFCs in: /tmp/rfc_demo_outputs/")
    
    async def demo_1_simple_rfc(self):
        """Demo 1: Simple RFC generation without codebase analysis"""
        
        print("📝 Generating simple RFC for API rate limiting feature...")
        
        request = RFCRequest(
            title="API Rate Limiting Implementation",
            description="""
Implement comprehensive API rate limiting to protect our services from abuse and ensure fair usage.

Current situation:
- No rate limiting exists
- Occasional service overload during peak times
- Need to protect against DDoS and abuse

Requirements:
- Rate limiting per user/API key
- Different limits for different endpoints
- Graceful degradation under load
- Monitoring and alerting
            """,
            rfc_type="architecture",
            include_diagrams=True,
            include_analysis=False,  # No codebase analysis
            author="Demo User",
            stakeholders=["API Team", "DevOps", "Product"],
        )
        
        # Generate RFC
        rfc = await self.rfc_generator.generate_rfc(request)
        
        # Display results
        self._display_rfc_summary(rfc)
        
        # Save to file
        await self._save_rfc_to_file(rfc, "demo_1_simple_rfc.md")
    
    async def demo_2_architecture_rfc_with_analysis(self):
        """Demo 2: RFC with full project architecture analysis"""
        
        print("🏗️ Generating RFC with full codebase analysis...")
        
        # First, analyze current project
        print("  🔍 Analyzing current project architecture...")
        try:
            analysis = await analyze_project_architecture(self.demo_project_path)
            print(f"  📊 Found {len(analysis.components)} components")
            print(f"  🛠️ Technologies: {', '.join(analysis.technology_inventory.keys())}")
        except Exception as e:
            print(f"  ⚠️ Analysis failed: {e}, using sample data")
            analysis = None
        
        request = RFCRequest(
            title="AI Assistant Microservices Architecture Enhancement",
            description="""
Enhance the AI Assistant architecture to improve scalability, maintainability, and performance.

Based on current codebase analysis, we need to:
- Improve service separation and boundaries
- Implement better async patterns  
- Add comprehensive monitoring
- Enhance security and authentication
- Optimize database connections and caching

The goal is to prepare the system for 10x user growth while maintaining sub-200ms response times.
            """,
            project_path=self.demo_project_path,
            rfc_type="architecture",
            include_diagrams=True,
            include_analysis=True,
            author="Senior Architect",
            stakeholders=["Engineering Team", "DevOps", "CTO", "Product"],
            custom_sections={
                "Migration Strategy": "Phased migration approach with zero-downtime deployment",
                "Performance Goals": "Target: <200ms API response, 99.9% uptime, 10x user capacity"
            }
        )
        
        # Generate enhanced RFC
        rfc = await self.rfc_generator.generate_rfc(request)
        
        # Display results with analysis
        self._display_rfc_summary(rfc, show_analysis=True)
        
        # Save enhanced RFC
        await self._save_rfc_to_file(rfc, "demo_2_architecture_rfc.md")
    
    async def demo_3_microservices_migration_rfc(self):
        """Demo 3: Complex microservices migration RFC"""
        
        print("🔄 Generating microservices migration RFC...")
        
        request = RFCRequest(
            title="Monolith to Microservices Migration Strategy",
            description="""
Plan and execute migration from current monolithic architecture to microservices.

Migration goals:
- Independent deployability of services
- Technology diversity (Python, Node.js, Go)
- Improved fault isolation
- Team autonomy and ownership
- Horizontal scalability

Phases:
1. Service identification and boundary definition
2. Data decomposition and distributed data management
3. API contracts and service mesh implementation
4. Migration execution with strangler fig pattern
5. Monitoring and observability setup
            """,
            rfc_type="architecture",
            include_diagrams=True,
            include_analysis=False,
            author="Platform Team",
            stakeholders=["All Engineering Teams", "DevOps", "CTO", "Data Team"],
            custom_sections={
                "Service Boundaries": "Domain-driven design approach with bounded contexts",
                "Data Strategy": "Database-per-service with event sourcing for consistency",
                "Timeline": "6-month migration plan with milestone-based approach"
            }
        )
        
        rfc = await self.rfc_generator.generate_rfc(request)
        
        self._display_rfc_summary(rfc)
        await self._save_rfc_to_file(rfc, "demo_3_microservices_migration.md")
    
    async def demo_4_api_design_rfc(self):
        """Demo 4: API design RFC with OpenAPI integration"""
        
        print("🔌 Generating API design RFC...")
        
        request = RFCRequest(
            title="Enhanced Vector Search API v2.0",
            description="""
Design next generation vector search API with improved performance and capabilities.

New features:
- Hybrid search (semantic + keyword)
- Real-time indexing
- Multi-modal search (text, images, code)
- Advanced filtering and faceting
- Batch operations
- WebSocket streaming for large results

Technical requirements:
- <100ms search latency for 95th percentile
- Support for 1M+ documents
- Horizontal scaling capability
- OpenAPI 3.0 specification
- Comprehensive test coverage
            """,
            rfc_type="api",
            include_diagrams=True,
            include_analysis=False,
            author="API Team Lead",
            stakeholders=["Frontend Team", "Data Science", "DevOps", "QA"],
            custom_sections={
                "API Specification": "OpenAPI 3.0 with detailed schemas and examples",
                "Performance Benchmarks": "Latency and throughput requirements",
                "Security Considerations": "Authentication, rate limiting, input validation"
            }
        )
        
        rfc = await self.rfc_generator.generate_rfc(request)
        
        self._display_rfc_summary(rfc)
        await self._save_rfc_to_file(rfc, "demo_4_api_design.md")
    
    async def demo_5_project_analysis_only(self):
        """Demo 5: Standalone project analysis with diagrams"""
        
        print("🔍 Running standalone project architecture analysis...")
        
        try:
            # Quick health check
            print("  📊 Running quick health check...")
            health = await quick_health_check(self.demo_project_path)
            print(f"  🏥 Health Score: {health.get('health_score', 'Unknown')}/100")
            
            # Full analysis
            print("  🔍 Running full architecture analysis...")
            analysis = await analyze_project_architecture(self.demo_project_path)
            
            # Generate diagrams
            print("  📈 Generating Mermaid diagrams...")
            diagrams = await generate_all_diagrams(analysis)
            
            # Display analysis results
            self._display_analysis_summary(analysis, diagrams)
            
            # Save analysis report
            await self._save_analysis_report(analysis, diagrams, "demo_5_project_analysis.md")
            
        except Exception as e:
            print(f"  ❌ Analysis failed: {e}")
            print("  ℹ️ This is expected if running outside a proper codebase")
    
    def _display_rfc_summary(self, rfc, show_analysis=False):
        """Display RFC generation summary"""
        
        print(f"📄 RFC Generated: {rfc.title}")
        print(f"🆔 RFC ID: {rfc.rfc_id}")
        print(f"📏 Content Length: {len(rfc.content):,} characters")
        print(f"📋 Sections: {len(rfc.sections)}")
        
        if rfc.diagrams:
            print(f"📊 Diagrams Generated: {len(rfc.diagrams)}")
            for name in rfc.diagrams.keys():
                print(f"  - {name.replace('_', ' ').title()}")
        
        if show_analysis and rfc.analysis:
            print(f"🔍 Architecture Analysis:")
            print(f"  - Components: {len(rfc.analysis.components)}")
            print(f"  - Technologies: {len(rfc.analysis.technology_inventory)}")
            print(f"  - Recommendations: {len(rfc.analysis.improvement_suggestions)}")
        
        print(f"💰 Estimated Tokens: ~{len(rfc.content) // 4:,}")
    
    def _display_analysis_summary(self, analysis, diagrams):
        """Display analysis summary"""
        
        print(f"📊 Analysis Results:")
        print(f"  🏗️ Components: {len(analysis.components)}")
        for comp in analysis.components:
            print(f"    - {comp.name} ({comp.service_type}): {len(comp.files)} files")
        
        print(f"  🛠️ Technologies:")
        for tech, count in analysis.technology_inventory.items():
            print(f"    - {tech}: {count} occurrences")
        
        print(f"  💡 Recommendations: {len(analysis.improvement_suggestions)}")
        for suggestion in analysis.improvement_suggestions[:3]:
            print(f"    - {suggestion}")
        
        print(f"  📈 Diagrams: {len(diagrams)}")
        for name in diagrams.keys():
            print(f"    - {name.replace('_', ' ').title()}")
    
    async def _save_rfc_to_file(self, rfc, filename):
        """Save RFC to markdown file"""
        
        output_dir = Path("/tmp/rfc_demo_outputs")
        output_dir.mkdir(exist_ok=True)
        
        file_path = output_dir / filename
        
        # Create enhanced content with metadata
        content = f"""---
title: "{rfc.title}"
rfc_id: "{rfc.rfc_id}"
author: "{rfc.metadata.get('author', 'Demo User')}"
generated: "{rfc.metadata.get('timestamp', 'Unknown')}"
diagrams_count: {len(rfc.diagrams)}
sections_count: {len(rfc.sections)}
---

{rfc.content}
"""
        
        # Add diagrams section
        if rfc.diagrams:
            content += "\n\n## 📊 Generated Diagrams\n\n"
            for name, diagram_code in rfc.diagrams.items():
                diagram_title = name.replace('_', ' ').title()
                content += f"### {diagram_title}\n\n```mermaid\n{diagram_code}\n```\n\n"
        
        # Add metadata section
        content += f"\n\n## 📋 Generation Metadata\n\n"
        content += f"- **Generated**: {rfc.metadata.get('timestamp', 'Unknown')}\n"
        content += f"- **Content Length**: {len(rfc.content):,} characters\n"
        content += f"- **Sections**: {len(rfc.sections)}\n"
        content += f"- **Diagrams**: {len(rfc.diagrams)}\n"
        if rfc.analysis:
            content += f"- **Components Analyzed**: {len(rfc.analysis.components)}\n"
            content += f"- **Technologies Detected**: {len(rfc.analysis.technology_inventory)}\n"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"💾 RFC saved to: {file_path}")
    
    async def _save_analysis_report(self, analysis, diagrams, filename):
        """Save analysis report to file"""
        
        output_dir = Path("/tmp/rfc_demo_outputs")
        output_dir.mkdir(exist_ok=True)
        
        file_path = output_dir / filename
        
        # Create analysis report
        content = f"""# Project Architecture Analysis Report

## 📊 Analysis Overview

- **Total Components**: {len(analysis.components)}
- **Total Files**: {analysis.metrics.get('total_files', 0)}
- **Analysis Date**: {analysis.metrics.get('timestamp', 'Unknown')}

## 🏗️ Components

"""
        
        for comp in analysis.components:
            content += f"""### {comp.name} ({comp.service_type.title()})

- **Files**: {len(comp.files)}
- **Technology Stack**: {', '.join(comp.technology_stack) if comp.technology_stack else 'Unknown'}
- **Interfaces**: {len(comp.interfaces)} endpoints
- **Dependencies**: {', '.join(comp.dependencies) if comp.dependencies else 'None'}

"""
        
        # Technology inventory
        content += "\n## 🛠️ Technology Inventory\n\n"
        for tech, count in analysis.technology_inventory.items():
            content += f"- **{tech}**: {count} occurrences\n"
        
        # Dependencies graph
        content += "\n## 🔗 Dependencies Graph\n\n"
        for comp, deps in analysis.dependencies_graph.items():
            if deps:
                content += f"- **{comp}** → {', '.join(deps)}\n"
        
        # Recommendations
        content += "\n## 💡 Improvement Recommendations\n\n"
        for i, suggestion in enumerate(analysis.improvement_suggestions, 1):
            content += f"{i}. {suggestion}\n"
        
        # Diagrams
        if diagrams:
            content += "\n## 📈 Generated Diagrams\n\n"
            for name, diagram_code in diagrams.items():
                diagram_title = name.replace('_', ' ').title()
                content += f"### {diagram_title}\n\n```mermaid\n{diagram_code}\n```\n\n"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"💾 Analysis report saved to: {file_path}")

async def main():
    """Main demo runner"""
    demo = RFCGeneratorDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main()) 