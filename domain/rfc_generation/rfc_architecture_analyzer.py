"""
RFC Architecture Analyzer - Intelligent codebase analysis for RFC generation.
Analyzes current architecture, identifies patterns, and suggests improvements.
"""

import ast
import asyncio
import json
import logging
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.async_utils import (AsyncTimeouts, async_retry, safe_gather,
                                  with_timeout)
from domain.integration.document_graph_builder import (DocumentGraphBuilder,
                                                       DocumentNode)
from domain.integration.enhanced_vector_search_service import enhanced_search

logger = logging.getLogger(__name__)


@dataclass
class CodeFile:
    """Represents a code file with metadata"""

    file_path: str
    language: str
    content: str
    lines_of_code: int
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    complexity_score: float = 0.0
    maintainability_index: float = 0.0


@dataclass
class ServiceComponent:
    """Represents a microservice or major component"""

    name: str
    service_type: str  # 'api', 'service', 'database', 'frontend', 'infrastructure'
    files: List[CodeFile] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)  # API endpoints, events, etc.
    technology_stack: List[str] = field(default_factory=list)
    deployment_config: Optional[str] = None
    health_check: Optional[str] = None


@dataclass
class ArchitecturePattern:
    """Detected architecture pattern"""

    pattern_type: str  # 'microservices', 'monolith', 'layered', 'event-driven'
    confidence: float
    evidence: List[str]
    components: List[str]


@dataclass
class QualityIssue:
    """Code quality or architecture issue"""

    severity: str  # 'critical', 'major', 'minor', 'info'
    category: str  # 'security', 'performance', 'maintainability', 'architecture'
    description: str
    location: str
    suggestion: str
    impact: str


@dataclass
class ArchitectureAnalysis:
    """Complete architecture analysis result"""

    components: List[ServiceComponent]
    patterns: List[ArchitecturePattern]
    quality_issues: List[QualityIssue]
    dependencies_graph: Dict[str, List[str]]
    technology_inventory: Dict[str, int]
    metrics: Dict[str, Any]
    improvement_suggestions: List[str]


class RFCArchitectureAnalyzer:
    """
    Analyzes codebase architecture for RFC generation.

    Capabilities:
    - Multi-language code analysis
    - Architecture pattern detection
    - Dependency graph construction
    - Quality assessment
    - Improvement recommendations
    """

    def __init__(self):
        self.graph_builder = DocumentGraphBuilder()

        # File patterns for different components
        self.component_patterns = {
            "api": [r".*api.*\.py$", r".*routes.*\.py$", r".*endpoints.*\.py$"],
            "service": [r".*service.*\.py$", r".*services/.*\.py$"],
            "model": [r".*model.*\.py$", r".*models/.*\.py$"],
            "database": [r".*db.*\.py$", r".*database.*\.py$", r"migrations/.*"],
            "config": [
                r".*config.*\.py$",
                r".*settings.*\.py$",
                r".*\.yml$",
                r".*\.yaml$",
            ],
            "frontend": [r".*\.tsx?$", r".*\.jsx?$", r".*\.vue$"],
            "infrastructure": [r".*docker.*", r".*k8s.*", r".*terraform.*"],
        }

        # Technology indicators
        self.tech_indicators = {
            "fastapi": ["fastapi", "FastAPI", "@app.", "APIRouter"],
            "django": ["django", "Django", "models.Model", "views.py"],
            "flask": ["flask", "Flask", "@app.route"],
            "react": ["React", "useState", "useEffect", "JSX"],
            "vue": ["Vue", "vue", "v-if", "v-for"],
            "docker": ["FROM ", "RUN ", "COPY ", "EXPOSE"],
            "kubernetes": ["apiVersion:", "kind:", "metadata:"],
            "postgresql": ["psycopg", "PostgreSQL", "POSTGRES"],
            "redis": ["redis", "Redis", "REDIS"],
            "nginx": ["nginx", "proxy_pass", "upstream"],
        }

        # Architecture pattern indicators
        self.pattern_indicators = {
            "microservices": [
                "multiple services",
                "api gateway",
                "service mesh",
                "docker-compose",
                "kubernetes",
                "independent deployment",
            ],
            "monolith": ["single deployment", "shared database", "single repository"],
            "layered": [
                "presentation layer",
                "business layer",
                "data layer",
                "controllers",
                "services",
                "repositories",
            ],
            "event_driven": ["events", "message queue", "pub/sub", "kafka", "rabbitmq"],
        }

    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def analyze_codebase(
        self,
        codebase_path: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> ArchitectureAnalysis:
        """
        Perform comprehensive codebase architecture analysis.

        Args:
            codebase_path: Path to codebase root
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude

        Returns:
            Complete architecture analysis
        """
        try:
            return await with_timeout(
                self._analyze_codebase_internal(
                    codebase_path, include_patterns, exclude_patterns
                ),
                AsyncTimeouts.ANALYTICS_AGGREGATION
                * 2,  # 120 seconds for comprehensive analysis
                f"Architecture analysis timed out for path: {codebase_path}",
                {"codebase_path": codebase_path},
            )
        except Exception as e:
            logger.error(f"Architecture analysis failed: {e}")
            # Return minimal analysis as fallback
            return ArchitectureAnalysis(
                components=[],
                patterns=[],
                quality_issues=[],
                dependencies_graph={},
                technology_inventory={},
                metrics={"error": str(e)},
                improvement_suggestions=["Analysis failed - manual review required"],
            )

    async def _analyze_codebase_internal(
        self,
        codebase_path: str,
        include_patterns: Optional[List[str]],
        exclude_patterns: Optional[List[str]],
    ) -> ArchitectureAnalysis:
        """Internal codebase analysis implementation"""

        logger.info(f"🔍 Starting architecture analysis for: {codebase_path}")

        # Step 1: Scan and categorize files
        code_files = await self._scan_codebase(
            codebase_path, include_patterns, exclude_patterns
        )
        logger.info(f"📁 Found {len(code_files)} code files")

        # Step 2: Analyze files concurrently
        analysis_tasks = [
            self._analyze_code_file(file_path, codebase_path)
            for file_path in code_files
        ]

        analyzed_files = await safe_gather(
            *analysis_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.ANALYTICS_QUERY,
            max_concurrency=20,
        )

        # Filter successful analyses
        valid_files = [file for file in analyzed_files if isinstance(file, CodeFile)]
        logger.info(f"📊 Successfully analyzed {len(valid_files)} files")

        # Step 3: Group files into components
        components = await self._identify_components(valid_files)
        logger.info(f"🏗️ Identified {len(components)} components")

        # Step 4: Build dependency graph
        dependencies_graph = await self._build_dependencies_graph(components)

        # Step 5: Detect architecture patterns
        patterns = await self._detect_architecture_patterns(components, valid_files)

        # Step 6: Assess quality and identify issues
        quality_issues = await self._assess_code_quality(valid_files, components)

        # Step 7: Generate metrics and technology inventory
        metrics = await self._calculate_metrics(valid_files, components)
        tech_inventory = self._build_technology_inventory(valid_files)

        # Step 8: Generate improvement suggestions
        suggestions = await self._generate_improvement_suggestions(
            components, patterns, quality_issues, metrics
        )

        logger.info(f"✅ Architecture analysis completed")

        return ArchitectureAnalysis(
            components=components,
            patterns=patterns,
            quality_issues=quality_issues,
            dependencies_graph=dependencies_graph,
            technology_inventory=tech_inventory,
            metrics=metrics,
            improvement_suggestions=suggestions,
        )

    async def _scan_codebase(
        self,
        codebase_path: str,
        include_patterns: Optional[List[str]],
        exclude_patterns: Optional[List[str]],
    ) -> List[str]:
        """Scan codebase and return relevant file paths"""

        code_files = []
        exclude_dirs = {
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            "venv",
            "dist",
            "build",
        }

        # Default include patterns for code files
        default_includes = [
            r".*\.py$",
            r".*\.js$",
            r".*\.ts$",
            r".*\.tsx$",
            r".*\.jsx$",
            r".*\.vue$",
            r".*\.java$",
            r".*\.go$",
            r".*\.rs$",
            r".*\.yml$",
            r".*\.yaml$",
            r".*\.json$",
            r".*Dockerfile.*",
            r".*docker-compose.*",
        ]

        include_regex = include_patterns or default_includes
        exclude_regex = exclude_patterns or [r".*test.*", r".*spec.*", r".*\.min\.js$"]

        for root, dirs, files in os.walk(codebase_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, codebase_path)

                # Check include patterns
                if any(re.match(pattern, relative_path) for pattern in include_regex):
                    # Check exclude patterns
                    if not any(
                        re.match(pattern, relative_path) for pattern in exclude_regex
                    ):
                        code_files.append(file_path)

        return code_files

    async def _analyze_code_file(self, file_path: str, codebase_root: str) -> CodeFile:
        """Analyze individual code file"""

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Detect language
            language = self._detect_file_language(file_path, content)

            # Calculate basic metrics
            lines_of_code = len([line for line in content.split("\n") if line.strip()])

            # Extract code elements based on language
            functions, classes, imports = [], [], []
            if language == "python":
                functions, classes, imports = await self._analyze_python_file(content)
            elif language in ["javascript", "typescript"]:
                functions, classes, imports = await self._analyze_js_ts_file(content)

            # Calculate complexity
            complexity_score = self._calculate_complexity(content, language)
            maintainability_index = self._calculate_maintainability(
                content, complexity_score
            )

            # Extract dependencies
            dependencies = self._extract_dependencies(imports, language)

            return CodeFile(
                file_path=os.path.relpath(file_path, codebase_root),
                language=language,
                content=content[:1000],  # Store first 1000 chars for analysis
                lines_of_code=lines_of_code,
                functions=functions,
                classes=classes,
                imports=imports,
                dependencies=dependencies,
                complexity_score=complexity_score,
                maintainability_index=maintainability_index,
            )

        except Exception as e:
            logger.warning(f"Failed to analyze file {file_path}: {e}")
            # Return basic file info
            return CodeFile(
                file_path=os.path.relpath(file_path, codebase_root),
                language="unknown",
                content="",
                lines_of_code=0,
            )

    def _detect_file_language(self, file_path: str, content: str) -> str:
        """Detect programming language from file extension and content"""

        ext = Path(file_path).suffix.lower()

        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".vue": "vue",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".json": "json",
        }

        if ext in extension_map:
            return extension_map[ext]

        # Content-based detection
        if "def " in content and "import " in content:
            return "python"
        elif "function " in content and ("const " in content or "let " in content):
            return "typescript" if ": " in content else "javascript"
        elif "FROM " in content and "RUN " in content:
            return "dockerfile"

        return "unknown"

    async def _analyze_python_file(
        self, content: str
    ) -> Tuple[List[str], List[str], List[str]]:
        """Analyze Python file for functions, classes, and imports"""

        functions, classes, imports = [], [], []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)

        except SyntaxError:
            # Fallback to regex if AST parsing fails
            functions = re.findall(r"def\s+(\w+)\s*\(", content)
            classes = re.findall(r"class\s+(\w+)\s*[:\(]", content)
            imports = re.findall(r"(?:from\s+(\S+)\s+import|import\s+(\S+))", content)
            imports = [imp[0] or imp[1] for imp in imports]

        return functions, classes, imports

    async def _analyze_js_ts_file(
        self, content: str
    ) -> Tuple[List[str], List[str], List[str]]:
        """Analyze JavaScript/TypeScript file"""

        # Extract functions
        functions = re.findall(
            r"(?:function\s+(\w+)|const\s+(\w+)\s*=.*(?:function|\())", content
        )
        functions = [f[0] or f[1] for f in functions if f[0] or f[1]]

        # Extract classes
        classes = re.findall(r"class\s+(\w+)", content)

        # Extract imports
        imports = re.findall(r'import.*from\s+[\'"]([^\'"]+)[\'"]', content)
        imports.extend(re.findall(r'require\([\'"]([^\'"]+)[\'"]\)', content))

        return functions, classes, imports

    def _calculate_complexity(self, content: str, language: str) -> float:
        """Calculate cyclomatic complexity"""

        complexity_indicators = {
            "python": [
                "if ",
                "elif ",
                "else:",
                "for ",
                "while ",
                "try:",
                "except:",
                "with ",
                "and ",
                "or ",
            ],
            "javascript": [
                "if ",
                "else ",
                "for ",
                "while ",
                "switch ",
                "case ",
                "&&",
                "||",
            ],
            "typescript": [
                "if ",
                "else ",
                "for ",
                "while ",
                "switch ",
                "case ",
                "&&",
                "||",
            ],
        }

        indicators = complexity_indicators.get(
            language, complexity_indicators["python"]
        )
        complexity = sum(content.count(indicator) for indicator in indicators)

        # Normalize by lines of code
        lines = len(content.split("\n"))
        return complexity / max(lines, 1) * 100

    def _calculate_maintainability(self, content: str, complexity: float) -> float:
        """Calculate maintainability index (simplified)"""

        lines = len(content.split("\n"))
        volume = len(content)  # Simplified volume calculation

        # Simplified maintainability index
        # MI = 171 - 5.2 * ln(V) - 0.23 * CC - 16.2 * ln(LOC)
        import math

        if volume <= 0 or lines <= 0:
            return 0.0

        mi = 171 - 5.2 * math.log(volume) - 0.23 * complexity - 16.2 * math.log(lines)
        return max(0, min(100, mi))  # Clamp between 0-100

    def _extract_dependencies(self, imports: List[str], language: str) -> List[str]:
        """Extract external dependencies from imports"""

        # Filter out standard library imports
        stdlib_modules = {
            "python": {
                "os",
                "sys",
                "json",
                "datetime",
                "typing",
                "asyncio",
                "logging",
                "re",
                "pathlib",
            },
            "javascript": {"fs", "path", "http", "https", "url", "util"},
            "typescript": {"fs", "path", "http", "https", "url", "util"},
        }

        std_modules = stdlib_modules.get(language, set())

        dependencies = []
        for imp in imports:
            # Get root module name
            root_module = imp.split(".")[0] if "." in imp else imp
            if root_module not in std_modules and not root_module.startswith("."):
                dependencies.append(root_module)

        return list(set(dependencies))  # Remove duplicates

    async def _identify_components(
        self, files: List[CodeFile]
    ) -> List[ServiceComponent]:
        """Group files into logical components/services"""

        components = []

        # Group files by directory structure
        component_files = defaultdict(list)

        for file in files:
            # Determine component from file path
            path_parts = Path(file.file_path).parts

            if len(path_parts) > 1:
                # Use first directory as component name
                component_name = path_parts[0]
            else:
                component_name = "root"

            component_files[component_name].append(file)

        # Create ServiceComponent objects
        for component_name, comp_files in component_files.items():
            service_type = self._determine_service_type(component_name, comp_files)

            # Aggregate component data
            all_dependencies = set()
            tech_stack = set()
            interfaces = []

            for file in comp_files:
                all_dependencies.update(file.dependencies)

                # Detect technology stack
                for tech, indicators in self.tech_indicators.items():
                    if any(indicator in file.content for indicator in indicators):
                        tech_stack.add(tech)

                # Extract API endpoints or interfaces
                if file.language == "python":
                    endpoints = re.findall(
                        r'@app\.(?:get|post|put|delete)\([\'"]([^\'"]+)[\'"]',
                        file.content,
                    )
                    interfaces.extend(endpoints)

            component = ServiceComponent(
                name=component_name,
                service_type=service_type,
                files=comp_files,
                dependencies=list(all_dependencies),
                interfaces=interfaces,
                technology_stack=list(tech_stack),
            )

            components.append(component)

        return components

    def _determine_service_type(
        self, component_name: str, files: List[CodeFile]
    ) -> str:
        """Determine the type of service/component"""

        name_lower = component_name.lower()

        # Check component name patterns
        if any(pattern in name_lower for pattern in ["api", "route", "endpoint"]):
            return "api"
        elif any(pattern in name_lower for pattern in ["service", "business", "logic"]):
            return "service"
        elif any(pattern in name_lower for pattern in ["model", "db", "database"]):
            return "database"
        elif any(
            pattern in name_lower for pattern in ["frontend", "ui", "web", "client"]
        ):
            return "frontend"
        elif any(pattern in name_lower for pattern in ["config", "deploy", "infra"]):
            return "infrastructure"

        # Check file patterns
        file_types = [file.language for file in files]
        if "dockerfile" in file_types or any("docker" in f.file_path for f in files):
            return "infrastructure"
        elif any(lang in file_types for lang in ["javascript", "typescript", "vue"]):
            return "frontend"
        elif "python" in file_types:
            # Check for API patterns in Python files
            has_api_patterns = any(
                any(
                    pattern in file.content
                    for pattern in ["@app.", "FastAPI", "APIRouter"]
                )
                for file in files
                if file.language == "python"
            )
            return "api" if has_api_patterns else "service"

        return "service"  # Default

    async def _build_dependencies_graph(
        self, components: List[ServiceComponent]
    ) -> Dict[str, List[str]]:
        """Build component dependency graph"""

        dependencies_graph = {}

        for component in components:
            component_deps = []

            # Find dependencies based on imports and references
            for dep in component.dependencies:
                # Check if dependency matches another component
                for other_component in components:
                    if other_component.name != component.name and (
                        dep.lower() in other_component.name.lower()
                        or any(dep in tech for tech in other_component.technology_stack)
                    ):
                        component_deps.append(other_component.name)

            dependencies_graph[component.name] = list(set(component_deps))

        return dependencies_graph

    async def _detect_architecture_patterns(
        self, components: List[ServiceComponent], files: List[CodeFile]
    ) -> List[ArchitecturePattern]:
        """Detect architecture patterns in the codebase"""

        patterns = []
        all_content = " ".join(file.content for file in files)

        for pattern_type, indicators in self.pattern_indicators.items():
            matches = sum(
                1
                for indicator in indicators
                if indicator.lower() in all_content.lower()
            )
            confidence = min(matches / len(indicators), 1.0)

            if confidence > 0.3:  # Threshold for pattern detection
                evidence = [
                    indicator
                    for indicator in indicators
                    if indicator.lower() in all_content.lower()
                ]
                component_names = [comp.name for comp in components]

                pattern = ArchitecturePattern(
                    pattern_type=pattern_type,
                    confidence=confidence,
                    evidence=evidence[:5],  # Limit evidence
                    components=component_names,
                )
                patterns.append(pattern)

        return sorted(patterns, key=lambda p: p.confidence, reverse=True)

    async def _assess_code_quality(
        self, files: List[CodeFile], components: List[ServiceComponent]
    ) -> List[QualityIssue]:
        """Assess code quality and identify issues"""

        issues = []

        # Check for high complexity files
        for file in files:
            if file.complexity_score > 15:  # High complexity threshold
                issues.append(
                    QualityIssue(
                        severity="major",
                        category="maintainability",
                        description=f"High cyclomatic complexity ({file.complexity_score:.1f})",
                        location=file.file_path,
                        suggestion="Consider refactoring into smaller functions",
                        impact="Difficult to test and maintain",
                    )
                )

            if file.maintainability_index < 20:  # Low maintainability
                issues.append(
                    QualityIssue(
                        severity="minor",
                        category="maintainability",
                        description=f"Low maintainability index ({file.maintainability_index:.1f})",
                        location=file.file_path,
                        suggestion="Improve code structure and reduce complexity",
                        impact="Higher maintenance costs",
                    )
                )

        # Check for large components
        for component in components:
            total_loc = sum(file.lines_of_code for file in component.files)
            if total_loc > 5000:  # Large component threshold
                issues.append(
                    QualityIssue(
                        severity="info",
                        category="architecture",
                        description=f"Large component with {total_loc} lines of code",
                        location=component.name,
                        suggestion="Consider splitting into smaller components",
                        impact="Reduced modularity and reusability",
                    )
                )

        # Check for missing documentation
        for file in files:
            if file.language == "python" and len(file.functions) > 5:
                if "def " in file.content and '"""' not in file.content:
                    issues.append(
                        QualityIssue(
                            severity="minor",
                            category="maintainability",
                            description="Missing function documentation",
                            location=file.file_path,
                            suggestion="Add docstrings to functions and classes",
                            impact="Reduced code understandability",
                        )
                    )

        return issues

    async def _calculate_metrics(
        self, files: List[CodeFile], components: List[ServiceComponent]
    ) -> Dict[str, Any]:
        """Calculate comprehensive codebase metrics"""

        total_files = len(files)
        total_loc = sum(file.lines_of_code for file in files)
        total_functions = sum(len(file.functions) for file in files)
        total_classes = sum(len(file.classes) for file in files)

        # Language distribution
        language_dist = Counter(file.language for file in files)

        # Complexity metrics
        avg_complexity = sum(file.complexity_score for file in files) / max(
            total_files, 1
        )
        avg_maintainability = sum(file.maintainability_index for file in files) / max(
            total_files, 1
        )

        # Component metrics
        component_sizes = [len(comp.files) for comp in components]
        avg_component_size = sum(component_sizes) / max(len(components), 1)

        return {
            "total_files": total_files,
            "total_lines_of_code": total_loc,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "total_components": len(components),
            "language_distribution": dict(language_dist),
            "average_complexity": round(avg_complexity, 2),
            "average_maintainability": round(avg_maintainability, 2),
            "average_component_size": round(avg_component_size, 2),
            "files_per_component": component_sizes,
        }

    def _build_technology_inventory(self, files: List[CodeFile]) -> Dict[str, int]:
        """Build inventory of technologies used"""

        tech_inventory = defaultdict(int)

        for file in files:
            for tech, indicators in self.tech_indicators.items():
                if any(indicator in file.content for indicator in indicators):
                    tech_inventory[tech] += 1

        return dict(tech_inventory)

    async def _generate_improvement_suggestions(
        self,
        components: List[ServiceComponent],
        patterns: List[ArchitecturePattern],
        quality_issues: List[QualityIssue],
        metrics: Dict[str, Any],
    ) -> List[str]:
        """Generate architecture improvement suggestions"""

        suggestions = []

        # Architecture-based suggestions
        if len(components) == 1 and metrics["total_lines_of_code"] > 10000:
            suggestions.append(
                "Consider splitting monolithic structure into microservices for better scalability and maintainability"
            )

        if metrics["average_complexity"] > 10:
            suggestions.append(
                "High average complexity detected - implement code review processes and refactoring initiatives"
            )

        if metrics["average_maintainability"] < 50:
            suggestions.append(
                "Low maintainability scores - prioritize technical debt reduction and code quality improvements"
            )

        # Pattern-based suggestions
        microservices_pattern = next(
            (p for p in patterns if p.pattern_type == "microservices"), None
        )
        if microservices_pattern and microservices_pattern.confidence > 0.7:
            suggestions.append(
                "Strong microservices pattern detected - consider implementing API gateway and service mesh for better management"
            )

        # Quality issue-based suggestions
        critical_issues = [
            issue for issue in quality_issues if issue.severity == "critical"
        ]
        if critical_issues:
            suggestions.append(
                f"Address {len(critical_issues)} critical quality issues immediately to prevent production risks"
            )

        # Technology diversity suggestions
        tech_count = len(set(metrics["language_distribution"].keys()))
        if tech_count > 5:
            suggestions.append(
                "High technology diversity detected - consider standardizing tech stack to reduce maintenance overhead"
            )

        # Component size suggestions
        if metrics["average_component_size"] > 20:
            suggestions.append(
                "Large components detected - consider breaking down into smaller, more focused modules"
            )

        return suggestions[:10]  # Limit to top 10 suggestions


# Convenience functions for external use
async def analyze_project_architecture(
    project_path: str,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> ArchitectureAnalysis:
    """
    Analyze project architecture from given path.

    Args:
        project_path: Path to project root
        include_patterns: File patterns to include
        exclude_patterns: File patterns to exclude

    Returns:
        Architecture analysis result
    """
    analyzer = RFCArchitectureAnalyzer()
    return await analyzer.analyze_codebase(
        project_path, include_patterns, exclude_patterns
    )


async def quick_architecture_assessment(project_path: str) -> Dict[str, Any]:
    """
    Quick architecture assessment for dashboard/summary view.

    Args:
        project_path: Path to project root

    Returns:
        Summary metrics and assessment
    """
    try:
        analysis = await analyze_project_architecture(project_path)

        return {
            "health_score": _calculate_health_score(analysis),
            "components_count": len(analysis.components),
            "quality_issues_count": len(analysis.quality_issues),
            "critical_issues_count": len(
                [i for i in analysis.quality_issues if i.severity == "critical"]
            ),
            "primary_pattern": (
                analysis.patterns[0].pattern_type if analysis.patterns else "unknown"
            ),
            "pattern_confidence": (
                analysis.patterns[0].confidence if analysis.patterns else 0
            ),
            "top_technologies": list(analysis.technology_inventory.keys())[:5],
            "total_loc": analysis.metrics.get("total_lines_of_code", 0),
            "average_complexity": analysis.metrics.get("average_complexity", 0),
            "improvement_priority": analysis.improvement_suggestions[:3],
        }
    except Exception as e:
        logger.error(f"Quick assessment failed: {e}")
        return {"error": str(e), "health_score": 0}


def _calculate_health_score(analysis: ArchitectureAnalysis) -> float:
    """Calculate overall architecture health score (0-100)"""

    base_score = 100

    # Penalize for quality issues
    critical_penalty = (
        len([i for i in analysis.quality_issues if i.severity == "critical"]) * 20
    )
    major_penalty = (
        len([i for i in analysis.quality_issues if i.severity == "major"]) * 10
    )
    minor_penalty = (
        len([i for i in analysis.quality_issues if i.severity == "minor"]) * 2
    )

    # Penalize for poor metrics
    complexity_penalty = max(0, (analysis.metrics.get("average_complexity", 0) - 5) * 2)
    maintainability_bonus = (
        analysis.metrics.get("average_maintainability", 50) - 50
    ) * 0.5

    final_score = (
        base_score
        - critical_penalty
        - major_penalty
        - minor_penalty
        - complexity_penalty
        + maintainability_bonus
    )

    return max(0, min(100, final_score))
