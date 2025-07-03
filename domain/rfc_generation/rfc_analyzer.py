"""
RFC Architecture Analyzer - Analyzes codebase for RFC generation.
"""

import asyncio
import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.async_utils import AsyncTimeouts, async_retry, with_timeout

logger = logging.getLogger(__name__)


@dataclass
class ComponentAnalysis:
    """Analysis of a component/service"""

    name: str
    service_type: str
    files: List[str]
    dependencies: List[str]
    technology_stack: List[str]
    interfaces: List[str]


@dataclass
class ArchitectureAnalysis:
    """Complete architecture analysis"""

    components: List[ComponentAnalysis]
    dependencies_graph: Dict[str, List[str]]
    technology_inventory: Dict[str, int]
    metrics: Dict[str, Any]
    improvement_suggestions: List[str]


class RFCArchitectureAnalyzer:
    """Analyzes codebase architecture for RFC generation"""

    def __init__(self):
        self.tech_indicators = {
            "fastapi": ["fastapi", "FastAPI", "@app.", "APIRouter"],
            "react": ["React", "useState", "useEffect"],
            "docker": ["FROM ", "RUN ", "COPY ", "EXPOSE"],
            "postgresql": ["psycopg", "PostgreSQL", "POSTGRES"],
            "redis": ["redis", "Redis"],
        }

    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def analyze_codebase(self, codebase_path: str) -> ArchitectureAnalysis:
        """Analyze codebase architecture"""
        try:
            return await with_timeout(
                self._analyze_internal(codebase_path),
                AsyncTimeouts.ANALYTICS_AGGREGATION,
                f"Architecture analysis timed out: {codebase_path}",
                {"path": codebase_path},
            )
        except Exception as e:
            logger.error(f"Architecture analysis failed: {e}")
            return ArchitectureAnalysis(
                components=[],
                dependencies_graph={},
                technology_inventory={},
                metrics={"error": str(e)},
                improvement_suggestions=["Analysis failed - manual review required"],
            )

    async def _analyze_internal(self, codebase_path: str) -> ArchitectureAnalysis:
        """Internal analysis implementation"""

        logger.info(f"🔍 Analyzing codebase: {codebase_path}")

        # Scan files
        files = self._scan_files(codebase_path)
        logger.info(f"📁 Found {len(files)} files")

        # Group into components
        components = self._identify_components(files, codebase_path)

        # Build dependency graph
        deps_graph = self._build_dependency_graph(components)

        # Technology inventory
        tech_inventory = self._build_tech_inventory(files, codebase_path)

        # Calculate metrics
        metrics = self._calculate_metrics(files, components)

        # Generate suggestions
        suggestions = self._generate_suggestions(components, metrics)

        logger.info(f"✅ Analysis completed: {len(components)} components found")

        return ArchitectureAnalysis(
            components=components,
            dependencies_graph=deps_graph,
            technology_inventory=tech_inventory,
            metrics=metrics,
            improvement_suggestions=suggestions,
        )

    def _scan_files(self, codebase_path: str) -> List[str]:
        """Scan for relevant files"""
        files = []
        exclude_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"}

        patterns = [r".*\.py$", r".*\.js$", r".*\.ts$", r".*\.tsx$", r".*\.yml$"]

        for root, dirs, filenames in os.walk(codebase_path):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for filename in filenames:
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, codebase_path)

                if any(re.match(pattern, relative_path) for pattern in patterns):
                    files.append(file_path)

        return files[:50]  # Limit for performance

    def _identify_components(
        self, files: List[str], codebase_path: str
    ) -> List[ComponentAnalysis]:
        """Group files into components"""
        components = []
        component_files = defaultdict(list)

        for file_path in files:
            relative_path = os.path.relpath(file_path, codebase_path)
            parts = Path(relative_path).parts

            # Use first directory as component name
            component_name = parts[0] if len(parts) > 1 else "root"
            component_files[component_name].append(relative_path)

        for comp_name, comp_files in component_files.items():
            # Determine service type
            service_type = self._determine_service_type(comp_name, comp_files)

            # Find technologies
            tech_stack = self._detect_technologies(comp_files, codebase_path)

            # Extract interfaces (simplified)
            interfaces = self._extract_interfaces(comp_files, codebase_path)

            component = ComponentAnalysis(
                name=comp_name,
                service_type=service_type,
                files=comp_files,
                dependencies=[],  # Will be filled later
                technology_stack=tech_stack,
                interfaces=interfaces,
            )

            components.append(component)

        return components

    def _determine_service_type(self, name: str, files: List[str]) -> str:
        """Determine component service type"""
        name_lower = name.lower()

        if any(pattern in name_lower for pattern in ["api", "route", "endpoint"]):
            return "api"
        elif any(pattern in name_lower for pattern in ["frontend", "ui", "web"]):
            return "frontend"
        elif any(pattern in name_lower for pattern in ["service", "business"]):
            return "service"
        elif any(pattern in name_lower for pattern in ["config", "deploy"]):
            return "infrastructure"

        # Check file types
        if any(".ts" in f or ".js" in f for f in files):
            return "frontend"
        elif any(".py" in f for f in files):
            return "service"

        return "service"

    def _detect_technologies(self, files: List[str], codebase_path: str) -> List[str]:
        """Detect technologies used in component"""
        technologies = set()

        for file_path in files[:10]:  # Limit for performance
            try:
                full_path = os.path.join(codebase_path, file_path)
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                for tech, indicators in self.tech_indicators.items():
                    if any(indicator in content for indicator in indicators):
                        technologies.add(tech)
            except:
                continue

        return list(technologies)

    def _extract_interfaces(self, files: List[str], codebase_path: str) -> List[str]:
        """Extract API interfaces/endpoints"""
        interfaces = []

        for file_path in files[:5]:  # Limit for performance
            try:
                full_path = os.path.join(codebase_path, file_path)
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Extract FastAPI endpoints
                endpoints = re.findall(
                    r'@app\.(?:get|post|put|delete)\([\'"]([^\'"]+)[\'"]', content
                )
                interfaces.extend(endpoints)

            except:
                continue

        return list(set(interfaces))[:10]  # Limit and deduplicate

    def _build_dependency_graph(
        self, components: List[ComponentAnalysis]
    ) -> Dict[str, List[str]]:
        """Build simple dependency graph"""
        graph = {}

        for component in components:
            deps = []
            for other_comp in components:
                if other_comp.name != component.name:
                    # Simple heuristic: check if component name mentioned in files
                    if any(
                        other_comp.name.lower() in file.lower()
                        for file in component.files
                    ):
                        deps.append(other_comp.name)

            graph[component.name] = deps

        return graph

    def _build_tech_inventory(
        self, files: List[str], codebase_path: str
    ) -> Dict[str, int]:
        """Build technology inventory"""
        inventory = defaultdict(int)

        for file_path in files[:20]:  # Limit for performance
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                for tech, indicators in self.tech_indicators.items():
                    if any(indicator in content for indicator in indicators):
                        inventory[tech] += 1
            except:
                continue

        return dict(inventory)

    def _calculate_metrics(
        self, files: List[str], components: List[ComponentAnalysis]
    ) -> Dict[str, Any]:
        """Calculate basic metrics"""

        total_files = len(files)
        total_components = len(components)

        # File distribution by extension
        extensions = defaultdict(int)
        for file_path in files:
            ext = Path(file_path).suffix
            extensions[ext] += 1

        return {
            "total_files": total_files,
            "total_components": total_components,
            "file_extensions": dict(extensions),
            "avg_files_per_component": round(total_files / max(total_components, 1), 2),
        }

    def _generate_suggestions(
        self, components: List[ComponentAnalysis], metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate improvement suggestions"""

        suggestions = []

        if len(components) == 1:
            suggestions.append(
                "Consider splitting monolithic structure into microservices"
            )

        if metrics["total_files"] > 100:
            suggestions.append(
                "Large codebase detected - implement modular architecture"
            )

        # Check for missing documentation
        doc_files = [
            f
            for comp in components
            for f in comp.files
            if "readme" in f.lower() or ".md" in f.lower()
        ]
        if len(doc_files) < len(components):
            suggestions.append("Add documentation for each component")

        # Check for testing
        test_files = [
            f for comp in components for f in comp.files if "test" in f.lower()
        ]
        if len(test_files) < len(components):
            suggestions.append("Implement comprehensive testing strategy")

        return suggestions[:5]


# Convenience functions
async def analyze_project_architecture(project_path: str) -> ArchitectureAnalysis:
    """Analyze project architecture"""
    analyzer = RFCArchitectureAnalyzer()
    return await analyzer.analyze_codebase(project_path)


async def quick_health_check(project_path: str) -> Dict[str, Any]:
    """Quick architecture health check"""
    try:
        analysis = await analyze_project_architecture(project_path)

        # Calculate simple health score
        base_score = 100
        if len(analysis.components) == 1:  # Monolith penalty
            base_score -= 20
        if analysis.metrics["total_files"] > 100:  # Large codebase penalty
            base_score -= 10
        if not analysis.technology_inventory:  # No tech detected penalty
            base_score -= 30

        health_score = max(0, base_score)

        return {
            "health_score": health_score,
            "components_count": len(analysis.components),
            "total_files": analysis.metrics["total_files"],
            "technologies": list(analysis.technology_inventory.keys()),
            "top_suggestions": analysis.improvement_suggestions[:3],
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"error": str(e), "health_score": 0}
