"""
RFC Generator Service - Creates comprehensive RFC documents with architecture analysis and diagrams.
Integrates with existing template service and document generation.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.async_utils import (AsyncTimeouts, async_retry, safe_gather,
                                  with_timeout)
from domain.core.mermaid_diagram_generator import (MermaidDiagramGenerator,
                                                   create_architecture_diagram,
                                                   create_dependency_diagram,
                                                   create_deployment_diagram,
                                                   generate_all_diagrams)
from domain.rfc_generation.rfc_analyzer import (ArchitectureAnalysis,
                                                RFCArchitectureAnalyzer,
                                                analyze_project_architecture)

logger = logging.getLogger(__name__)


@dataclass
class RFCRequest:
    """RFC generation request"""

    title: str
    description: str
    project_path: Optional[str] = None
    rfc_type: str = "architecture"  # 'architecture', 'design', 'process'
    include_diagrams: bool = True
    include_analysis: bool = True
    author: str = "AI Assistant"
    stakeholders: List[str] = None
    custom_sections: Dict[str, str] = None


@dataclass
class RFCSection:
    """RFC document section"""

    title: str
    content: str
    order: int
    section_type: str = "text"  # 'text', 'diagram', 'code', 'table'


@dataclass
class GeneratedRFC:
    """Complete generated RFC document"""

    title: str
    rfc_id: str
    content: str
    sections: List[RFCSection]
    diagrams: Dict[str, str]
    analysis: Optional[ArchitectureAnalysis]
    metadata: Dict[str, Any]


class RFCGeneratorService:
    """
    Comprehensive RFC generator with architecture analysis and diagram generation.

    Features:
    - Automated codebase analysis
    - Multi-type diagram generation
    - Template-based RFC creation
    - Architecture recommendations
    """

    def __init__(self):
        self.analyzer = RFCArchitectureAnalyzer()
        self.diagram_generator = MermaidDiagramGenerator()

        # RFC templates by type
        self.rfc_templates = {
            "architecture": self._get_architecture_template(),
            "design": self._get_design_template(),
            "process": self._get_process_template(),
            "api": self._get_api_template(),
        }

        # Section ordering
        self.section_order = {
            "summary": 1,
            "background": 2,
            "current_architecture": 3,
            "problem_statement": 4,
            "proposed_solution": 5,
            "architecture_overview": 6,
            "component_design": 7,
            "deployment_strategy": 8,
            "api_design": 9,
            "data_flow": 10,
            "security_considerations": 11,
            "performance_impact": 12,
            "implementation_plan": 13,
            "testing_strategy": 14,
            "rollback_plan": 15,
            "monitoring": 16,
            "alternatives_considered": 17,
            "risks_mitigation": 18,
            "conclusion": 19,
        }

    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def generate_rfc(self, request: RFCRequest) -> GeneratedRFC:
        """
        Generate comprehensive RFC document.

        Args:
            request: RFC generation request

        Returns:
            Complete RFC document with analysis and diagrams
        """
        try:
            return await with_timeout(
                self._generate_rfc_internal(request),
                AsyncTimeouts.ANALYTICS_AGGREGATION * 3,  # 180 seconds for full RFC
                f"RFC generation timed out for: {request.title}",
                {"title": request.title, "type": request.rfc_type},
            )
        except Exception as e:
            logger.error(f"RFC generation failed: {e}")
            # Return minimal RFC as fallback
            return GeneratedRFC(
                title=request.title,
                rfc_id=self._generate_rfc_id(request.title),
                content=f"# {request.title}\n\n**ERROR**: RFC generation failed - {str(e)}\n\nPlease review manually.",
                sections=[],
                diagrams={},
                analysis=None,
                metadata={"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()},
            )

    async def _generate_rfc_internal(self, request: RFCRequest) -> GeneratedRFC:
        """Internal RFC generation implementation"""

        logger.info(f"🚀 Generating RFC: {request.title}")

        # Step 1: Analyze architecture if project path provided
        analysis = None
        if request.project_path and request.include_analysis:
            try:
                analysis = await self.analyzer.analyze_codebase(request.project_path)
                logger.info(
                    f"📊 Architecture analysis completed: {len(analysis.components)} components"
                )
            except Exception as e:
                logger.warning(f"Architecture analysis failed: {e}")

        # Step 2: Generate diagrams if requested
        diagrams = {}
        if request.include_diagrams and analysis:
            try:
                diagrams = await self._generate_diagrams_for_rfc(analysis, request)
                logger.info(f"📈 Generated {len(diagrams)} diagrams")
            except Exception as e:
                logger.warning(f"Diagram generation failed: {e}")

        # Step 3: Create RFC sections
        sections = await self._create_rfc_sections(request, analysis, diagrams)
        logger.info(f"📝 Created {len(sections)} sections")

        # Step 4: Assemble final RFC document
        rfc_content = await self._assemble_rfc_document(request, sections, analysis)

        # Step 5: Generate metadata
        metadata = self._create_rfc_metadata(request, analysis, len(diagrams))

        rfc = GeneratedRFC(
            title=request.title,
            rfc_id=self._generate_rfc_id(request.title),
            content=rfc_content,
            sections=sections,
            diagrams=diagrams,
            analysis=analysis,
            metadata=metadata,
        )

        logger.info(f"✅ RFC generated successfully: {rfc.rfc_id}")
        return rfc

    async def _generate_diagrams_for_rfc(
        self, analysis: ArchitectureAnalysis, request: RFCRequest
    ) -> Dict[str, str]:
        """Generate all relevant diagrams for RFC"""

        # Create diagram generation tasks
        diagram_tasks = []

        # Always generate architecture overview
        diagram_tasks.append(
            (
                "architecture",
                create_architecture_diagram(analysis, "Current System Architecture"),
            )
        )

        # Generate dependency diagram if multiple components
        if len(analysis.components) > 1:
            diagram_tasks.append(
                (
                    "dependencies",
                    create_dependency_diagram(analysis, "Component Dependencies"),
                )
            )

        # Generate deployment diagram
        diagram_tasks.append(
            (
                "deployment",
                create_deployment_diagram(analysis, "Deployment Architecture"),
            )
        )

        # Generate component diagrams for key services
        api_components = [c for c in analysis.components if c.service_type == "api"]
        for i, component in enumerate(api_components[:2]):  # Limit to 2 API components
            diagram_tasks.append(
                (
                    f"component_api_{i}",
                    self.diagram_generator.generate_component_diagram(component),
                )
            )

        # Execute diagram generation concurrently
        diagram_results = await safe_gather(
            *[self._execute_diagram_task(name, task) for name, task in diagram_tasks],
            return_exceptions=True,
            timeout=AsyncTimeouts.ANALYTICS_QUERY,
            max_concurrency=5,
        )

        # Collect successful diagrams
        diagrams = {}
        for result in diagram_results:
            if isinstance(result, tuple) and len(result) == 2:
                name, diagram_code = result
                diagrams[name] = diagram_code

        return diagrams

    async def _execute_diagram_task(self, name: str, task) -> Tuple[str, str]:
        """Execute single diagram generation task"""
        try:
            if isinstance(task, str):
                # Already generated diagram code
                return name, task
            else:
                # Need to await the task
                diagram_code = await task if hasattr(task, "__await__") else task
                return name, diagram_code
        except Exception as e:
            logger.warning(f"Failed to generate diagram {name}: {e}")
            return name, f'graph TD\n    Error["Diagram generation failed: {str(e)}"]'

    async def _create_rfc_sections(
        self,
        request: RFCRequest,
        analysis: Optional[ArchitectureAnalysis],
        diagrams: Dict[str, str],
    ) -> List[RFCSection]:
        """Create all RFC sections based on template and analysis"""

        sections = []
        template = self.rfc_templates.get(
            request.rfc_type, self.rfc_templates["architecture"]
        )

        # 1. Executive Summary
        summary_content = await self._generate_summary_section(request, analysis)
        sections.append(
            RFCSection(
                "Executive Summary", summary_content, self.section_order["summary"]
            )
        )

        # 2. Background & Context
        background_content = await self._generate_background_section(request, analysis)
        sections.append(
            RFCSection(
                "Background", background_content, self.section_order["background"]
            )
        )

        # 3. Current Architecture (if analysis available)
        if analysis:
            current_arch_content = await self._generate_current_architecture_section(
                analysis
            )
            sections.append(
                RFCSection(
                    "Current Architecture",
                    current_arch_content,
                    self.section_order["current_architecture"],
                )
            )

        # 4. Problem Statement
        problem_content = await self._generate_problem_statement(request, analysis)
        sections.append(
            RFCSection(
                "Problem Statement",
                problem_content,
                self.section_order["problem_statement"],
            )
        )

        # 5. Proposed Solution
        solution_content = await self._generate_proposed_solution(request, analysis)
        sections.append(
            RFCSection(
                "Proposed Solution",
                solution_content,
                self.section_order["proposed_solution"],
            )
        )

        # 6. Architecture Overview (with diagram)
        if "architecture" in diagrams:
            arch_overview_content = self._create_architecture_overview_section(
                analysis, diagrams["architecture"]
            )
            sections.append(
                RFCSection(
                    "Architecture Overview",
                    arch_overview_content,
                    self.section_order["architecture_overview"],
                    "diagram",
                )
            )

        # 7. Component Design (with dependency diagram)
        if "dependencies" in diagrams:
            component_content = self._create_component_design_section(
                analysis, diagrams["dependencies"]
            )
            sections.append(
                RFCSection(
                    "Component Design",
                    component_content,
                    self.section_order["component_design"],
                    "diagram",
                )
            )

        # 8. Deployment Strategy (with deployment diagram)
        if "deployment" in diagrams:
            deployment_content = self._create_deployment_section(
                analysis, diagrams["deployment"]
            )
            sections.append(
                RFCSection(
                    "Deployment Strategy",
                    deployment_content,
                    self.section_order["deployment_strategy"],
                    "diagram",
                )
            )

        # 9. Implementation Plan
        impl_content = await self._generate_implementation_plan(request, analysis)
        sections.append(
            RFCSection(
                "Implementation Plan",
                impl_content,
                self.section_order["implementation_plan"],
            )
        )

        # 10. Testing Strategy
        testing_content = await self._generate_testing_strategy(analysis)
        sections.append(
            RFCSection(
                "Testing Strategy",
                testing_content,
                self.section_order["testing_strategy"],
            )
        )

        # 11. Risks & Mitigation
        risks_content = await self._generate_risks_section(analysis)
        sections.append(
            RFCSection(
                "Risks & Mitigation",
                risks_content,
                self.section_order["risks_mitigation"],
            )
        )

        # 12. Custom sections
        if request.custom_sections:
            for section_title, section_content in request.custom_sections.items():
                sections.append(
                    RFCSection(section_title, section_content, 20)
                )  # Add at end

        # Sort sections by order
        sections.sort(key=lambda s: s.order)
        return sections

    async def _generate_summary_section(
        self, request: RFCRequest, analysis: Optional[ArchitectureAnalysis]
    ) -> str:
        """Generate executive summary section"""

        content = [
            "## Executive Summary",
            "",
            f"This RFC proposes {request.description}",
            "",
        ]

        if analysis:
            content.extend(
                [
                    "### Current System Overview",
                    f"- **Components**: {len(analysis.components)} main components identified",
                    f"- **Technologies**: {', '.join(list(analysis.technology_inventory.keys())[:5])}",
                    f"- **Architecture Health**: {self._calculate_health_summary(analysis)}",
                    "",
                ]
            )

        content.extend(
            [
                "### Key Benefits",
                "- Improved system scalability and maintainability",
                "- Enhanced performance and reliability",
                "- Better developer experience and productivity",
                "- Reduced technical debt and operational overhead",
                "",
                "### Implementation Timeline",
                "- **Phase 1**: Design and planning (2 weeks)",
                "- **Phase 2**: Core implementation (4-6 weeks)",
                "- **Phase 3**: Testing and rollout (2 weeks)",
                "",
            ]
        )

        return "\n".join(content)

    async def _generate_background_section(
        self, request: RFCRequest, analysis: Optional[ArchitectureAnalysis]
    ) -> str:
        """Generate background section"""

        content = ["## Background", "", f"### Context", f"{request.description}", ""]

        if analysis and analysis.improvement_suggestions:
            content.extend(["### Current Challenges", ""])

            for suggestion in analysis.improvement_suggestions[:5]:
                content.append(f"- {suggestion}")

            content.append("")

        content.extend(
            [
                "### Business Drivers",
                "- Need for improved system performance and scalability",
                "- Requirements for better maintainability and developer productivity",
                "- Compliance and security requirements",
                "- Cost optimization and operational efficiency",
                "",
            ]
        )

        return "\n".join(content)

    async def _generate_current_architecture_section(
        self, analysis: ArchitectureAnalysis
    ) -> str:
        """Generate current architecture analysis section"""

        content = [
            "## Current Architecture Analysis",
            "",
            "### System Overview",
            f"The current system consists of {len(analysis.components)} main components:",
            "",
        ]

        # List components
        for component in analysis.components:
            tech_stack = (
                ", ".join(component.technology_stack)
                if component.technology_stack
                else "N/A"
            )
            content.extend(
                [
                    f"#### {component.name} ({component.service_type.title()})",
                    f"- **Technology Stack**: {tech_stack}",
                    f"- **Files**: {len(component.files)} files",
                    (
                        f"- **Interfaces**: {len(component.interfaces)} endpoints"
                        if component.interfaces
                        else ""
                    ),
                    "",
                ]
            )

        # Architecture patterns
        if analysis.patterns:
            content.extend(["### Detected Architecture Patterns", ""])

            for pattern in analysis.patterns[:3]:
                content.extend(
                    [
                        f"#### {pattern.pattern_type.title()} Pattern",
                        f"- **Confidence**: {pattern.confidence:.1%}",
                        f"- **Evidence**: {', '.join(pattern.evidence[:3])}",
                        "",
                    ]
                )

        # Metrics summary
        content.extend(
            [
                "### Key Metrics",
                f"- **Total Files**: {analysis.metrics.get('total_files', 0)}",
                f"- **Lines of Code**: {analysis.metrics.get('total_lines_of_code', 0):,}",
                f"- **Average Complexity**: {analysis.metrics.get('average_complexity', 0):.1f}",
                "",
            ]
        )

        return "\n".join(content)

    async def _generate_problem_statement(
        self, request: RFCRequest, analysis: Optional[ArchitectureAnalysis]
    ) -> str:
        """Generate problem statement section"""

        content = ["## Problem Statement", "", "### Primary Issues", ""]

        if analysis and analysis.quality_issues:
            # Group issues by severity
            critical_issues = [
                i for i in analysis.quality_issues if i.severity == "critical"
            ]
            major_issues = [i for i in analysis.quality_issues if i.severity == "major"]

            if critical_issues:
                content.extend(["#### Critical Issues", ""])
                for issue in critical_issues[:3]:
                    content.append(
                        f"- **{issue.category.title()}**: {issue.description} ({issue.location})"
                    )
                content.append("")

            if major_issues:
                content.extend(["#### Major Issues", ""])
                for issue in major_issues[:3]:
                    content.append(
                        f"- **{issue.category.title()}**: {issue.description}"
                    )
                content.append("")

        content.extend(
            [
                "### Impact Analysis",
                "- **Developer Productivity**: Current architecture slows down development cycles",
                "- **System Performance**: Scalability limitations under increasing load",
                "- **Maintenance Burden**: High technical debt requiring significant resources",
                "- **Risk Exposure**: Potential system failures and security vulnerabilities",
                "",
                "### Success Criteria",
                "- Improve system performance by 40%+",
                "- Reduce deployment time by 60%+",
                "- Decrease critical bugs by 50%+",
                "- Improve developer satisfaction scores",
                "",
            ]
        )

        return "\n".join(content)

    async def _generate_proposed_solution(
        self, request: RFCRequest, analysis: Optional[ArchitectureAnalysis]
    ) -> str:
        """Generate proposed solution section"""

        content = [
            "## Proposed Solution",
            "",
            "### Solution Overview",
            f"We propose to {request.description.lower()} by implementing the following key changes:",
            "",
            "### Key Components",
            "",
        ]

        if analysis:
            # Generate solution based on detected issues
            if len(analysis.components) == 1:
                content.extend(
                    [
                        "#### Microservices Architecture",
                        "- Break down monolithic structure into focused microservices",
                        "- Implement API gateway for service orchestration",
                        "- Enable independent scaling and deployment",
                        "",
                    ]
                )

            if analysis.technology_inventory.get("docker", 0) == 0:
                content.extend(
                    [
                        "#### Containerization Strategy",
                        "- Containerize all services using Docker",
                        "- Implement Kubernetes for orchestration",
                        "- Enable consistent deployment across environments",
                        "",
                    ]
                )

            if not any(
                "database" in comp.service_type.lower() for comp in analysis.components
            ):
                content.extend(
                    [
                        "#### Data Layer Improvements",
                        "- Implement robust database architecture",
                        "- Add caching layer with Redis",
                        "- Optimize data access patterns",
                        "",
                    ]
                )

        content.extend(
            [
                "### Technical Approach",
                "1. **Phase 1 - Foundation**: Set up core infrastructure and tooling",
                "2. **Phase 2 - Migration**: Gradually migrate existing components",
                "3. **Phase 3 - Optimization**: Performance tuning and monitoring",
                "",
                "### Benefits",
                "- **Scalability**: Support for 10x traffic growth",
                "- **Reliability**: 99.9% uptime with fault tolerance",
                "- **Maintainability**: Modular architecture for easier updates",
                "- **Performance**: Sub-100ms response times",
                "",
            ]
        )

        return "\n".join(content)

    def _create_architecture_overview_section(
        self, analysis: Optional[ArchitectureAnalysis], diagram: str
    ) -> str:
        """Create architecture overview with diagram"""

        content = [
            "## Architecture Overview",
            "",
            "The following diagram shows the high-level system architecture:",
            "",
            "```mermaid",
            diagram,
            "```",
            "",
        ]

        if analysis:
            content.extend(["### Component Breakdown", ""])

            # Group components by type
            component_types = {}
            for comp in analysis.components:
                if comp.service_type not in component_types:
                    component_types[comp.service_type] = []
                component_types[comp.service_type].append(comp)

            for service_type, components in component_types.items():
                content.extend([f"#### {service_type.title()} Layer", ""])
                for comp in components:
                    content.append(
                        f"- **{comp.name}**: {len(comp.files)} files, {', '.join(comp.technology_stack[:2])}"
                    )
                content.append("")

        return "\n".join(content)

    def _create_component_design_section(
        self, analysis: Optional[ArchitectureAnalysis], diagram: str
    ) -> str:
        """Create component design with dependency diagram"""

        content = [
            "## Component Design",
            "",
            "### Component Dependencies",
            "",
            "```mermaid",
            diagram,
            "```",
            "",
        ]

        if analysis:
            content.extend(["### Interface Contracts", ""])

            api_components = [c for c in analysis.components if c.interfaces]
            for component in api_components[:3]:  # Limit to 3 components
                content.extend([f"#### {component.name} API", ""])
                for interface in component.interfaces[:5]:  # Limit to 5 interfaces
                    content.append(f"- `{interface}`")
                content.append("")

        return "\n".join(content)

    def _create_deployment_section(
        self, analysis: Optional[ArchitectureAnalysis], diagram: str
    ) -> str:
        """Create deployment section with diagram"""

        content = [
            "## Deployment Strategy",
            "",
            "### Deployment Architecture",
            "",
            "```mermaid",
            diagram,
            "```",
            "",
            "### Deployment Process",
            "1. **Build Phase**: Automated CI/CD pipeline builds and tests all components",
            "2. **Staging Deployment**: Deploy to staging environment for integration testing",
            "3. **Production Deployment**: Blue-green deployment to production with rollback capability",
            "4. **Health Checks**: Automated monitoring and alerting post-deployment",
            "",
            "### Infrastructure Requirements",
            "",
        ]

        if analysis and analysis.technology_inventory:
            content.extend(["#### Technology Stack Requirements", ""])

            for tech, count in analysis.technology_inventory.items():
                if tech == "docker":
                    content.append(
                        "- **Container Runtime**: Docker with Kubernetes orchestration"
                    )
                elif tech == "postgresql":
                    content.append(
                        "- **Database**: PostgreSQL cluster with read replicas"
                    )
                elif tech == "redis":
                    content.append(
                        "- **Cache**: Redis cluster for session and data caching"
                    )
                elif tech == "fastapi":
                    content.append("- **API Framework**: FastAPI with async support")

            content.append("")

        content.extend(
            [
                "#### Resource Allocation",
                "- **CPU**: 2-4 cores per service instance",
                "- **Memory**: 4-8 GB per service instance",
                "- **Storage**: SSD storage with automated backups",
                "- **Network**: Load balancer with SSL termination",
                "",
            ]
        )

        return "\n".join(content)

    async def _generate_implementation_plan(
        self, request: RFCRequest, analysis: Optional[ArchitectureAnalysis]
    ) -> str:
        """Generate implementation plan section"""

        content = [
            "## Implementation Plan",
            "",
            "### Phase 1: Foundation (Weeks 1-2)",
            "- Set up development and deployment infrastructure",
            "- Implement CI/CD pipelines and monitoring",
            "- Create project structure and coding standards",
            "- Set up testing frameworks and quality gates",
            "",
            "### Phase 2: Core Implementation (Weeks 3-8)",
            "- Implement core services and APIs",
            "- Set up database schema and migrations",
            "- Develop authentication and authorization",
            "- Create integration tests and documentation",
            "",
            "### Phase 3: Integration & Testing (Weeks 9-10)",
            "- Integration testing across all components",
            "- Performance testing and optimization",
            "- Security testing and vulnerability assessment",
            "- User acceptance testing with stakeholders",
            "",
            "### Phase 4: Deployment & Monitoring (Weeks 11-12)",
            "- Production deployment with gradual rollout",
            "- Monitor system performance and stability",
            "- Address any post-deployment issues",
            "- Knowledge transfer and documentation handover",
            "",
            "### Resource Requirements",
            f"- **Team Size**: {self._estimate_team_size(analysis)} developers",
            "- **Duration**: 12 weeks total",
            "- **Budget**: Development and infrastructure costs",
            "",
            "### Key Milestones",
            "- **Week 2**: Infrastructure ready",
            "- **Week 6**: Core features implemented",
            "- **Week 10**: Testing completed",
            "- **Week 12**: Production deployment",
            "",
        ]

        return "\n".join(content)

    async def _generate_testing_strategy(
        self, analysis: Optional[ArchitectureAnalysis]
    ) -> str:
        """Generate testing strategy section"""

        content = [
            "## Testing Strategy",
            "",
            "### Testing Levels",
            "",
            "#### Unit Testing",
            "- Target: 90%+ code coverage",
            "- Framework: pytest for Python, Jest for JavaScript",
            "- Automated execution in CI/CD pipeline",
            "",
            "#### Integration Testing",
            "- API contract testing between services",
            "- Database integration testing",
            "- Third-party service integration testing",
            "",
            "#### End-to-End Testing",
            "- Critical user journey testing",
            "- Cross-browser and cross-device testing",
            "- Automated regression testing",
            "",
            "### Performance Testing",
            "- Load testing with expected traffic patterns",
            "- Stress testing to identify breaking points",
            "- Monitoring and alerting validation",
            "",
            "### Security Testing",
            "- Vulnerability scanning and penetration testing",
            "- Authentication and authorization testing",
            "- Data encryption and privacy compliance",
            "",
        ]

        if analysis:
            component_count = len(analysis.components)
            api_count = len([c for c in analysis.components if c.service_type == "api"])

            content.extend(
                [
                    "",
                    "### Test Automation Coverage",
                    f"- **Components to test**: {component_count} main components",
                    f"- **API endpoints**: {api_count} API services requiring testing",
                    "- **Test environments**: Development, staging, production",
                    "",
                ]
            )

        return "\n".join(content)

    async def _generate_risks_section(
        self, analysis: Optional[ArchitectureAnalysis]
    ) -> str:
        """Generate risks and mitigation section"""

        content = [
            "## Risks & Mitigation",
            "",
            "### Technical Risks",
            "",
            "#### High Risk",
            "- **Integration Complexity**: Multiple services may have integration challenges",
            "  - *Mitigation*: Comprehensive integration testing and API contracts",
            "",
            "- **Performance Degradation**: New architecture may initially impact performance",
            "  - *Mitigation*: Performance testing and gradual rollout strategy",
            "",
            "#### Medium Risk",
            "- **Data Migration Issues**: Existing data migration may face challenges",
            "  - *Mitigation*: Thorough migration testing and rollback procedures",
            "",
            "- **Third-party Dependencies**: External service dependencies may cause issues",
            "  - *Mitigation*: Fallback mechanisms and monitoring",
            "",
            "### Operational Risks",
            "",
            "#### Deployment Risk",
            "- **Risk**: Production deployment failures",
            "- **Mitigation**: Blue-green deployment with automated rollback",
            "",
            "#### Monitoring Gap",
            "- **Risk**: Insufficient monitoring during transition",
            "- **Mitigation**: Comprehensive monitoring and alerting setup",
            "",
            "### Business Risks",
            "",
            "#### Timeline Risk",
            "- **Risk**: Project delays affecting business objectives",
            "- **Mitigation**: Agile approach with regular milestone reviews",
            "",
            "#### Adoption Risk",
            "- **Risk**: Team resistance to new architecture",
            "- **Mitigation**: Training, documentation, and change management",
            "",
        ]

        if analysis and analysis.quality_issues:
            critical_issues = [
                i for i in analysis.quality_issues if i.severity == "critical"
            ]
            if critical_issues:
                content.extend(["", "### Architecture-Specific Risks", ""])

                for issue in critical_issues[:3]:
                    content.extend(
                        [
                            f"#### {issue.category.title()} Risk",
                            f"- **Issue**: {issue.description}",
                            f"- **Impact**: {issue.impact}",
                            f"- **Mitigation**: {issue.suggestion}",
                            "",
                        ]
                    )

        return "\n".join(content)

    async def _assemble_rfc_document(
        self,
        request: RFCRequest,
        sections: List[RFCSection],
        analysis: Optional[ArchitectureAnalysis],
    ) -> str:
        """Assemble final RFC document"""

        # RFC Header
        rfc_id = self._generate_rfc_id(request.title)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        header = [
            f"# RFC-{rfc_id}: {request.title}",
            "",
            f"**Author:** {request.author}",
            f"**Date:** {timestamp}",
            f"**Status:** Draft",
            f"**Type:** {request.rfc_type.title()}",
            "",
        ]

        if request.stakeholders:
            header.extend([f"**Stakeholders:** {', '.join(request.stakeholders)}", ""])

        # Table of Contents
        toc = ["## Table of Contents", ""]

        for section in sections:
            toc.append(
                f"- [{section.title}](#{section.title.lower().replace(' ', '-')})"
            )

        toc.extend(["", "---", ""])

        # Assemble all sections
        document_parts = header + toc

        for section in sections:
            document_parts.extend([section.content, "", "---", ""])

        # Footer
        footer = [
            "## Document Information",
            "",
            f"- **RFC ID**: RFC-{rfc_id}",
            f"- **Generated**: {datetime.now(timezone.utc).isoformat()}Z",
            f"- **Generator**: AI Assistant RFC Generator v1.0",
            "",
        ]

        if analysis:
            footer.extend(
                [
                    "### Analysis Summary",
                    f"- **Components Analyzed**: {len(analysis.components)}",
                    f"- **Technologies Detected**: {len(analysis.technology_inventory)}",
                    f"- **Quality Issues Found**: {len(analysis.quality_issues)}",
                    "",
                ]
            )

        document_parts.extend(footer)

        return "\n".join(document_parts)

    def _generate_rfc_id(self, title: str) -> str:
        """Generate RFC ID from title"""
        import hashlib
        import re

        # Create short hash from title
        title_hash = hashlib.md5(title.encode()).hexdigest()[:6]

        # Extract numbers or use hash
        numbers = re.findall(r"\d+", title)
        if numbers:
            return f"{numbers[0]}-{title_hash}"
        else:
            return f"AUTO-{title_hash}"

    def _create_rfc_metadata(
        self,
        request: RFCRequest,
        analysis: Optional[ArchitectureAnalysis],
        diagram_count: int,
    ) -> Dict[str, Any]:
        """Create RFC metadata"""

        metadata = {
            "rfc_type": request.rfc_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "author": request.author,
            "title": request.title,
            "description": request.description,
            "diagram_count": diagram_count,
            "include_analysis": request.include_analysis,
            "include_diagrams": request.include_diagrams,
        }

        if analysis:
            metadata.update(
                {
                    "components_analyzed": len(analysis.components),
                    "technologies_detected": list(analysis.technology_inventory.keys()),
                    "quality_issues_found": len(analysis.quality_issues),
                    "architecture_patterns": [
                        p.pattern_type for p in analysis.patterns
                    ],
                    "health_score": self._calculate_simple_health_score(analysis),
                }
            )

        if request.stakeholders:
            metadata["stakeholders"] = request.stakeholders

        return metadata

    def _calculate_health_summary(self, analysis: ArchitectureAnalysis) -> str:
        """Calculate health summary for display"""
        score = self._calculate_simple_health_score(analysis)

        if score >= 80:
            return f"Good ({score}/100)"
        elif score >= 60:
            return f"Fair ({score}/100)"
        else:
            return f"Needs Improvement ({score}/100)"

    def _calculate_simple_health_score(self, analysis: ArchitectureAnalysis) -> int:
        """Calculate simple health score"""
        base_score = 100

        # Penalize for critical issues
        critical_issues = len(
            [i for i in analysis.quality_issues if i.severity == "critical"]
        )
        major_issues = len(
            [i for i in analysis.quality_issues if i.severity == "major"]
        )

        score = base_score - (critical_issues * 20) - (major_issues * 10)

        # Bonus for good patterns
        if analysis.patterns:
            score += 10

        return max(0, min(100, score))

    def _estimate_team_size(self, analysis: Optional[ArchitectureAnalysis]) -> str:
        """Estimate required team size"""
        if not analysis:
            return "4-6"

        component_count = len(analysis.components)
        if component_count <= 3:
            return "3-4"
        elif component_count <= 6:
            return "5-7"
        else:
            return "8-10"

    def _get_architecture_template(self) -> Dict[str, str]:
        """Get architecture RFC template"""
        return {
            "summary": "Executive summary of the architectural changes",
            "background": "Context and motivation for the changes",
            "current_state": "Analysis of current architecture",
            "proposed_solution": "Detailed proposed architecture",
            "implementation": "Implementation strategy and timeline",
        }

    def _get_design_template(self) -> Dict[str, str]:
        """Get design RFC template"""
        return {
            "summary": "Design proposal summary",
            "requirements": "Functional and non-functional requirements",
            "design": "Detailed design specifications",
            "alternatives": "Alternative approaches considered",
        }

    def _get_process_template(self) -> Dict[str, str]:
        """Get process RFC template"""
        return {
            "summary": "Process change summary",
            "current_process": "Current process analysis",
            "proposed_process": "New process definition",
            "transition_plan": "Process transition strategy",
        }

    def _get_api_template(self) -> Dict[str, str]:
        """Get API RFC template"""
        return {
            "summary": "API design summary",
            "endpoints": "API endpoint specifications",
            "data_models": "Request/response schemas",
            "authentication": "API authentication and authorization",
        }


# Convenience functions
async def generate_architecture_rfc(
    title: str,
    description: str,
    project_path: Optional[str] = None,
    author: str = "AI Assistant",
) -> GeneratedRFC:
    """Generate architecture RFC with full analysis"""
    service = RFCGeneratorService()
    request = RFCRequest(
        title=title,
        description=description,
        project_path=project_path,
        rfc_type="architecture",
        include_diagrams=True,
        include_analysis=True,
        author=author,
    )
    return await service.generate_rfc(request)


async def generate_quick_rfc(title: str, description: str) -> GeneratedRFC:
    """Generate quick RFC without codebase analysis"""
    service = RFCGeneratorService()
    request = RFCRequest(
        title=title,
        description=description,
        rfc_type="design",
        include_diagrams=False,
        include_analysis=False,
    )
    return await service.generate_rfc(request)
