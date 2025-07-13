"""
Enhanced Generation Service with RFC Generator integration.

This module provides comprehensive generation capabilities including:
- RFC generation with architecture analysis
- Technical documentation generation
- Architecture design documents
"""

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from app.core.async_utils import (AsyncTimeouts, async_retry, safe_gather,
                                  with_timeout)
from domain.rfc_generation.rfc_analyzer import (analyze_project_architecture,
                                                quick_health_check)

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from domain.rfc_generation.rfc_generator_service import (GeneratedRFC,
                                                             RFCGeneratorService,
                                                             RFCRequest)

logger = logging.getLogger(__name__)


class GenerationServiceInterface(ABC):
    """Interface for generation services"""

    @abstractmethod
    async def generate_rfc(self, **kwargs) -> Dict[str, Any]:
        """Generate RFC document"""
        pass

    @abstractmethod
    async def generate_architecture(self, **kwargs) -> Dict[str, Any]:
        """Generate architecture document"""
        pass

    @abstractmethod
    async def generate_documentation(self, **kwargs) -> Dict[str, Any]:
        """Generate documentation"""
        pass


class EnhancedGenerationService(GenerationServiceInterface):
    """
    Enhanced generation service with RFC Generator and Mermaid diagrams.

    Features:
    - Full RFC generation with architecture analysis
    - Automatic Mermaid diagram generation
    - Project codebase analysis
    - Multi-source context gathering
    """

    def __init__(self):
        # Import at runtime to avoid circular import
        from domain.rfc_generation.rfc_generator_service import RFCGeneratorService
        
        self.rfc_generator = RFCGeneratorService()
        self.cost_tracker = {"total_tokens": 0, "total_cost": 0.0}

    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def generate_rfc(self, **kwargs) -> Dict[str, Any]:
        """
        Generate comprehensive RFC with diagrams and architecture analysis.

        Args:
            task_description: Main RFC description
            project_context: Optional project context
            technical_requirements: Technical requirements
            stakeholders: List of stakeholders
            priority: Priority level
            template_type: RFC template type
            context_data: Additional context from sources
            user_id: User identifier
            project_path: Optional path to analyze codebase

        Returns:
            Generated RFC with metadata
        """
        try:
            # Import at runtime to avoid circular import
            from domain.rfc_generation.rfc_generator_service import RFCRequest
            
            # Extract parameters
            task_description = kwargs.get("task_description", "")
            project_context = kwargs.get("project_context")
            technical_requirements = kwargs.get("technical_requirements")
            stakeholders = kwargs.get("stakeholders", [])
            priority = kwargs.get("priority", "medium")
            template_type = kwargs.get("template_type", "architecture")
            context_data = kwargs.get("context_data", [])
            user_id = kwargs.get("user_id", "anonymous")
            project_path = kwargs.get("project_path")

            logger.info(
                f"🚀 Starting enhanced RFC generation: {task_description[:50]}..."
            )

            # Step 1: Analyze project if path provided
            project_analysis = None
            if project_path:
                try:
                    project_analysis = await analyze_project_architecture(project_path)
                    logger.info(
                        f"📊 Project analysis completed: {len(project_analysis.components)} components"
                    )
                except Exception as e:
                    logger.warning(f"Project analysis failed: {e}")

            # Step 2: Create RFC request
            rfc_request = RFCRequest(
                title=self._generate_rfc_title(task_description),
                description=task_description,
                project_path=project_path,
                rfc_type=template_type,
                include_diagrams=True,
                include_analysis=bool(project_path),
                author=f"AI Assistant (User: {user_id})",
                stakeholders=stakeholders,
                custom_sections=self._create_custom_sections_from_context(context_data),
            )

            # Step 3: Generate RFC with diagrams
            generated_rfc = await self.rfc_generator.generate_rfc(rfc_request)

            # Step 4: Process and enhance content
            enhanced_content = await self._enhance_rfc_content(
                generated_rfc, context_data, project_analysis
            )

            # Step 5: Calculate metrics
            tokens_used = self._estimate_tokens_used(generated_rfc.content)
            cost_estimate = tokens_used * 0.002 / 1000  # Rough estimate

            # Update tracking
            self.cost_tracker["total_tokens"] += tokens_used
            self.cost_tracker["total_cost"] += cost_estimate

            result = {
                "task_id": generated_rfc.rfc_id,
                "status": "completed",
                "content": enhanced_content,
                "rfc_data": {
                    "title": generated_rfc.title,
                    "sections": [
                        {
                            "title": section.title,
                            "content": section.content,
                            "order": section.order,
                            "type": section.section_type,
                        }
                        for section in generated_rfc.sections
                    ],
                    "diagrams": generated_rfc.diagrams,
                    "analysis": (
                        generated_rfc.analysis.__dict__
                        if generated_rfc.analysis
                        else None
                    ),
                },
                "metadata": generated_rfc.metadata,
                "tokens_used": tokens_used,
                "cost_estimate": cost_estimate,
                "project_analysis": (
                    project_analysis.__dict__ if project_analysis else None
                ),
            }

            logger.info(f"✅ RFC generation completed: {generated_rfc.rfc_id}")
            return result

        except Exception as e:
            logger.error(f"RFC generation failed: {e}")
            return {
                "task_id": str(uuid.uuid4()),
                "status": "error",
                "content": f"# RFC Generation Failed\n\n**Error**: {str(e)}\n\nPlease try again with simplified requirements.",
                "error": str(e),
                "tokens_used": 0,
                "cost_estimate": 0.0,
            }

    async def generate_architecture(self, **kwargs) -> Dict[str, Any]:
        """
        Generate architecture document with comprehensive analysis.

        Args:
            system_name: Name of the system
            system_description: System description
            requirements: List of requirements
            constraints: List of constraints
            architecture_type: Type of architecture
            include_diagrams: Whether to include diagrams
            context_data: Additional context
            architectural_patterns: Detected patterns
            user_id: User identifier

        Returns:
            Generated architecture document
        """
        try:
            # Import at runtime to avoid circular import
            from domain.rfc_generation.rfc_generator_service import RFCRequest
            
            system_name = kwargs.get("system_name", "System")
            system_description = kwargs.get("system_description", "")
            requirements = kwargs.get("requirements", [])
            constraints = kwargs.get("constraints", [])
            architecture_type = kwargs.get("architecture_type", "microservices")
            include_diagrams = kwargs.get("include_diagrams", True)
            context_data = kwargs.get("context_data", [])
            patterns = kwargs.get("architectural_patterns", [])
            user_id = kwargs.get("user_id", "anonymous")

            logger.info(f"🏗️ Generating architecture document: {system_name}")

            # Create architecture-focused RFC request
            task_description = f"""
Design architecture for {system_name}.

**System Description**: {system_description}

**Requirements**:
{chr(10).join(f"- {req}" for req in requirements)}

**Architecture Type**: {architecture_type}

**Constraints**:
{chr(10).join(f"- {constraint}" for constraint in (constraints or []))}

**Detected Patterns**:
{chr(10).join(f"- {pattern.get('pattern', 'Unknown')}" for pattern in patterns)}
            """

            rfc_request = RFCRequest(
                title=f"{system_name} - Architecture Design",
                description=task_description,
                rfc_type="architecture",
                include_diagrams=include_diagrams,
                include_analysis=True,
                author=f"AI Assistant (User: {user_id})",
                custom_sections={
                    "Architecture Patterns": self._format_patterns_section(patterns),
                    "Requirements Analysis": self._format_requirements_section(
                        requirements
                    ),
                    "Constraints & Considerations": self._format_constraints_section(
                        constraints or []
                    ),
                },
            )

            # Generate architecture RFC
            generated_rfc = await self.rfc_generator.generate_rfc(rfc_request)

            # Enhanced architecture content
            enhanced_content = await self._enhance_architecture_content(
                generated_rfc, architecture_type, patterns, context_data
            )

            tokens_used = self._estimate_tokens_used(generated_rfc.content)
            cost_estimate = tokens_used * 0.002 / 1000

            result = {
                "task_id": generated_rfc.rfc_id,
                "status": "completed",
                "content": enhanced_content,
                "architecture_data": {
                    "system_name": system_name,
                    "architecture_type": architecture_type,
                    "diagrams": generated_rfc.diagrams,
                    "patterns_used": patterns,
                    "requirements_covered": len(requirements),
                },
                "metadata": generated_rfc.metadata,
                "tokens_used": tokens_used,
                "cost_estimate": cost_estimate,
            }

            logger.info(f"✅ Architecture generation completed: {system_name}")
            return result

        except Exception as e:
            logger.error(f"Architecture generation failed: {e}")
            return {
                "task_id": str(uuid.uuid4()),
                "status": "error",
                "content": f"# Architecture Generation Failed\n\n**Error**: {str(e)}",
                "error": str(e),
                "tokens_used": 0,
                "cost_estimate": 0.0,
            }

    async def generate_documentation(self, **kwargs) -> Dict[str, Any]:
        """
        Generate comprehensive documentation.

        Args:
            doc_type: Type of documentation
            title: Document title
            content_outline: Content structure
            target_audience: Target audience
            detail_level: Level of detail
            include_examples: Include examples
            context_data: Additional context
            user_id: User identifier

        Returns:
            Generated documentation
        """
        try:
            # Import at runtime to avoid circular import
            from domain.rfc_generation.rfc_generator_service import RFCRequest
            
            doc_type = kwargs.get("doc_type", "technical_spec")
            title = kwargs.get("title", "Documentation")
            content_outline = kwargs.get("content_outline", [])
            target_audience = kwargs.get("target_audience", "developers")
            detail_level = kwargs.get("detail_level", "detailed")
            include_examples = kwargs.get("include_examples", True)
            context_data = kwargs.get("context_data", [])
            user_id = kwargs.get("user_id", "anonymous")

            logger.info(f"📝 Generating documentation: {title} ({doc_type})")

            # Create documentation-focused description
            task_description = f"""
Create {doc_type} documentation for {title}.

**Target Audience**: {target_audience}
**Detail Level**: {detail_level}
**Include Examples**: {include_examples}

**Content Outline**:
{chr(10).join(f"- {item}" for item in content_outline)}

**Documentation Type Specific Requirements**:
{self._get_doc_type_requirements(doc_type)}
            """

            # Determine RFC type based on doc type
            rfc_type = "design" if doc_type in ["api", "technical_spec"] else "process"

            rfc_request = RFCRequest(
                title=title,
                description=task_description,
                rfc_type=rfc_type,
                include_diagrams=doc_type in ["technical_spec", "api"],
                include_analysis=False,
                author=f"AI Assistant (User: {user_id})",
                custom_sections=self._create_doc_custom_sections(
                    doc_type, content_outline
                ),
            )

            # Generate documentation RFC
            generated_rfc = await self.rfc_generator.generate_rfc(rfc_request)

            # Format for documentation style
            doc_content = await self._format_as_documentation(
                generated_rfc, doc_type, target_audience, include_examples
            )

            tokens_used = self._estimate_tokens_used(generated_rfc.content)
            cost_estimate = tokens_used * 0.002 / 1000

            result = {
                "task_id": generated_rfc.rfc_id,
                "status": "completed",
                "content": doc_content,
                "documentation_data": {
                    "doc_type": doc_type,
                    "target_audience": target_audience,
                    "detail_level": detail_level,
                    "sections_count": len(generated_rfc.sections),
                    "includes_examples": include_examples,
                },
                "metadata": generated_rfc.metadata,
                "tokens_used": tokens_used,
                "cost_estimate": cost_estimate,
            }

            logger.info(f"✅ Documentation generation completed: {title}")
            return result

        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            return {
                "task_id": str(uuid.uuid4()),
                "status": "error",
                "content": f"# Documentation Generation Failed\n\n**Error**: {str(e)}",
                "error": str(e),
                "tokens_used": 0,
                "cost_estimate": 0.0,
            }

    # Helper methods

    def _generate_rfc_title(self, description: str) -> str:
        """Generate RFC title from description"""
        # Extract first meaningful sentence
        sentences = description.split(".")
        if sentences:
            title = sentences[0].strip()
            if len(title) > 60:
                title = title[:60] + "..."
            return f"RFC: {title}"
        return "RFC: System Enhancement"

    def _create_custom_sections_from_context(
        self, context_data: List[Dict]
    ) -> Dict[str, str]:
        """Create custom sections from context data"""
        sections = {}

        if context_data:
            # Group context by source
            confluence_data = [
                c for c in context_data if c.get("source") == "confluence"
            ]
            gitlab_data = [c for c in context_data if c.get("source") == "gitlab"]

            if confluence_data:
                sections["Related Documentation"] = self._format_confluence_references(
                    confluence_data
                )

            if gitlab_data:
                sections["Code References"] = self._format_gitlab_references(
                    gitlab_data
                )

        return sections

    def _format_confluence_references(self, data: List[Dict]) -> str:
        """Format Confluence references"""
        content = ["### Existing Documentation\n"]
        for item in data[:5]:  # Limit to 5 items
            title = item.get("title", "Unknown")
            content.append(f"- **{title}**: {item.get('summary', 'No summary')}")
        return "\n".join(content)

    def _format_gitlab_references(self, data: List[Dict]) -> str:
        """Format GitLab references"""
        content = ["### Related Code\n"]
        for item in data[:5]:  # Limit to 5 items
            title = item.get("title", "Unknown")
            content.append(f"- **{title}**: {item.get('summary', 'No summary')}")
        return "\n".join(content)

    async def _enhance_rfc_content(
        self,
        rfc,  # GeneratedRFC type - avoiding annotation due to circular import
        context_data: List[Dict],
        project_analysis: Optional[Any],
    ) -> str:
        """Enhance RFC content with additional formatting and diagrams"""

        content_parts = []

        # Add YAML frontmatter
        content_parts.append(
            f"""---
title: "{rfc.title}"
rfc_id: "{rfc.rfc_id}"
author: "{rfc.metadata.get('author', 'AI Assistant')}"
created: "{datetime.now(timezone.utc).isoformat()}"
status: "draft"
version: "1.0"
---

"""
        )

        # Add main content
        content_parts.append(rfc.content)

        # Add diagrams section if present
        if rfc.diagrams:
            content_parts.append("\n\n## 📊 Architecture Diagrams\n")

            for diagram_name, diagram_code in rfc.diagrams.items():
                diagram_title = diagram_name.replace("_", " ").title()
                content_parts.append(f"\n### {diagram_title}\n")
                content_parts.append(f"```mermaid\n{diagram_code}\n```\n")

        # Add project analysis if available
        if project_analysis and hasattr(project_analysis, "components"):
            content_parts.append(f"\n\n## 🔍 Project Analysis Summary\n")
            content_parts.append(
                f"- **Components**: {len(project_analysis.components)}"
            )
            content_parts.append(
                f"- **Technologies**: {', '.join(project_analysis.technology_inventory.keys())}"
            )
            if project_analysis.improvement_suggestions:
                content_parts.append(f"\n**Key Recommendations**:")
                for suggestion in project_analysis.improvement_suggestions[:3]:
                    content_parts.append(f"- {suggestion}")

        return "".join(content_parts)

    def _estimate_tokens_used(self, content: str) -> int:
        """Rough token estimation"""
        # Approximate: 1 token ≈ 4 characters
        return len(content) // 4

    def _format_patterns_section(self, patterns: List[Dict]) -> str:
        """Format architectural patterns section"""
        if not patterns:
            return "No specific patterns detected."

        content = ["### Detected Architectural Patterns\n"]
        for pattern in patterns:
            name = pattern.get("pattern", "Unknown")
            relevance = pattern.get("relevance", 0)
            content.append(f"- **{name}** (Relevance: {relevance:.1%})")

        return "\n".join(content)

    def _format_requirements_section(self, requirements: List[str]) -> str:
        """Format requirements section"""
        if not requirements:
            return "No specific requirements provided."

        content = ["### Requirements\n"]
        for i, req in enumerate(requirements, 1):
            content.append(f"{i}. {req}")

        return "\n".join(content)

    def _format_constraints_section(self, constraints: List[str]) -> str:
        """Format constraints section"""
        if not constraints:
            return "No specific constraints identified."

        content = ["### Constraints & Considerations\n"]
        for constraint in constraints:
            content.append(f"- {constraint}")

        return "\n".join(content)

    async def _enhance_architecture_content(
        self,
        rfc,  # GeneratedRFC type - avoiding annotation due to circular import
        architecture_type: str,
        patterns: List[Dict],
        context_data: List[Dict],
    ) -> str:
        """Enhance architecture content with additional sections"""

        content_parts = []

        # Add YAML frontmatter
        content_parts.append(
            f"""---
title: "{rfc.title}"
architecture_type: "{architecture_type}"
rfc_id: "{rfc.rfc_id}"
created: "{datetime.now(timezone.utc).isoformat()}"
status: "draft"
version: "1.0"
---

"""
        )

        # Add main content
        content_parts.append(rfc.content)

        return "".join(content_parts)

    def _get_doc_type_requirements(self, doc_type: str) -> str:
        """Get documentation type specific requirements"""
        requirements = {
            "api": "Include endpoints, parameters, responses, examples",
            "technical_spec": "Include architecture, data models, interfaces",
            "user_guide": "Include step-by-step instructions, screenshots",
            "developer_guide": "Include setup, configuration, code examples",
        }
        return requirements.get(doc_type, "General documentation requirements")

    def _create_doc_custom_sections(
        self, doc_type: str, outline: List[str]
    ) -> Dict[str, str]:
        """Create custom sections for documentation"""
        sections = {}

        if outline:
            sections["Content Structure"] = "\n".join(
                f"- {item}" for item in outline
            )

        # Add type-specific sections
        if doc_type == "api":
            sections["API Standards"] = "Follow RESTful principles and OpenAPI 3.0 specification"
        elif doc_type == "technical_spec":
            sections[
                "Technical Requirements"
            ] = "Include performance, security, and scalability considerations"

        return sections

    async def _format_as_documentation(
        self,
        rfc,  # GeneratedRFC type - avoiding annotation due to circular import
        doc_type: str,
        target_audience: str,
        include_examples: bool,
    ) -> str:
        """Format RFC as documentation style"""

        content_parts = []

        # Add documentation header
        content_parts.append(
            f"""# {rfc.title}

**Document Type**: {doc_type.replace('_', ' ').title()}
**Target Audience**: {target_audience.title()}
**Last Updated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

---

"""
        )

        # Add main content (formatted for documentation)
        doc_content = rfc.content.replace("# RFC:", "#").replace("## Abstract", "## Overview")

        content_parts.append(doc_content)

        if include_examples and rfc.diagrams:
            content_parts.append("\n\n## Examples & Diagrams\n")
            for diagram_name, diagram_code in rfc.diagrams.items():
                diagram_title = diagram_name.replace("_", " ").title()
                content_parts.append(f"\n### {diagram_title}\n")
                content_parts.append(f"```mermaid\n{diagram_code}\n```\n")

        return "".join(content_parts)


class MockGenerationService(GenerationServiceInterface):
    """Mock generation service for testing"""

    async def generate_rfc(self, **kwargs) -> Dict[str, Any]:
        return {
            "task_id": str(uuid.uuid4()),
            "status": "completed",
            "content": "# Mock RFC\n\nThis is a mock RFC for testing.",
            "tokens_used": 100,
            "cost_estimate": 0.01,
        }

    async def generate_architecture(self, **kwargs) -> Dict[str, Any]:
        return {
            "task_id": str(uuid.uuid4()),
            "status": "completed", 
            "content": "# Mock Architecture\n\nThis is a mock architecture document.",
            "tokens_used": 100,
            "cost_estimate": 0.01,
        }

    async def generate_documentation(self, **kwargs) -> Dict[str, Any]:
        return {
            "task_id": str(uuid.uuid4()),
            "status": "completed",
            "content": "# Mock Documentation\n\nThis is mock documentation.",
            "tokens_used": 100,
            "cost_estimate": 0.01,
        }


def get_generation_service() -> GenerationServiceInterface:
    """Get generation service instance"""
    return EnhancedGenerationService()


# Alias for backward compatibility
GenerationService = EnhancedGenerationService
