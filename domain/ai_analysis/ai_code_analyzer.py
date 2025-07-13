"""
AI Code Analyzer - Advanced code analysis with LLM-powered insights.
Provides intelligent code analysis, refactoring suggestions, and optimization recommendations.
"""

import ast
import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.async_utils import (AsyncTimeouts, async_retry, safe_gather,
                                  with_timeout)

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of code analysis"""

    QUALITY = "quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"


class IssueSeverity(Enum):
    """Severity levels for issues"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis"""

    type: AnalysisType
    severity: IssueSeverity
    title: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None
    fix_code: Optional[str] = None
    confidence: float = 0.8
    tags: List[str] = field(default_factory=list)


@dataclass
class RefactoringSuggestion:
    """Refactoring suggestion with AI-generated improvements"""

    title: str
    description: str
    file_path: str
    original_code: str
    refactored_code: str
    benefits: List[str]
    complexity_reduction: float
    confidence: float
    estimated_effort: str  # "low", "medium", "high"


@dataclass
class PerformanceOptimization:
    """Performance optimization suggestion"""

    title: str
    description: str
    file_path: str
    optimization_type: str  # "algorithm", "database", "caching", "async"
    current_code: str
    optimized_code: str
    expected_improvement: str
    impact_assessment: Dict[str, Any]
    implementation_notes: List[str]


@dataclass
class SecurityVulnerability:
    """Security vulnerability detection"""

    cve_type: str
    severity: IssueSeverity
    title: str
    description: str
    file_path: str
    vulnerable_code: str
    secure_alternative: str
    mitigation_steps: List[str]
    references: List[str]


@dataclass
class CodeAnalysisResult:
    """Complete code analysis result"""

    file_path: str
    language: str
    analysis_timestamp: str
    quality_score: float  # 0-100
    maintainability_index: float
    complexity_metrics: Dict[str, Any]
    issues: List[CodeIssue]
    refactoring_suggestions: List[RefactoringSuggestion]
    performance_optimizations: List[PerformanceOptimization]
    security_vulnerabilities: List[SecurityVulnerability]
    documentation_gaps: List[str]
    ai_insights: Dict[str, Any]


class AICodeAnalyzer:
    """
    AI-powered code analyzer with advanced insights and recommendations.

    Features:
    - Deep code quality analysis with LLM insights
    - Automated refactoring suggestions
    - Performance optimization recommendations
    - Security vulnerability detection
    - Documentation gap analysis
    """

    def __init__(self):
        # Quality patterns for different issues
        self.quality_patterns = {
            "long_function": {
                "pattern": r"def\s+\w+\([^)]*\):.*?(?=\ndef|\nclass|\Z)",
                "threshold": 50,  # lines
                "severity": IssueSeverity.MEDIUM,
            },
            "complex_function": {
                "pattern": r"if\s+.*?:|for\s+.*?:|while\s+.*?:|try\s*:",
                "threshold": 10,  # complexity points
                "severity": IssueSeverity.HIGH,
            },
            "magic_numbers": {
                "pattern": r"\b\d{2,}\b(?!\s*[)\]])",
                "severity": IssueSeverity.LOW,
            },
            "todo_comments": {
                "pattern": r"#\s*(TODO|FIXME|HACK|XXX)",
                "severity": IssueSeverity.INFO,
            },
        }

        # Security vulnerability patterns
        self.security_patterns = {
            "sql_injection": {
                "pattern": r'(execute|query)\s*\(\s*["\'].*%.*["\']',
                "severity": IssueSeverity.CRITICAL,
            },
            "hardcoded_secrets": {
                "pattern": r'(password|secret|key|token)\s*=\s*["\'][^"\']{8,}["\']',
                "severity": IssueSeverity.HIGH,
            },
            "eval_usage": {"pattern": r"\beval\s*\(", "severity": IssueSeverity.HIGH},
            "pickle_usage": {
                "pattern": r"pickle\.loads?\s*\(",
                "severity": IssueSeverity.MEDIUM,
            },
        }

        # Performance anti-patterns
        self.performance_patterns = {
            "nested_loops": {
                "pattern": r"for\s+.*?:.*?\n.*?for\s+.*?:",
                "severity": IssueSeverity.MEDIUM,
            },
            "inefficient_string_concat": {
                "pattern": r'\w+\s*\+=\s*["\'].*?["\']',
                "severity": IssueSeverity.LOW,
            },
            "blocking_io": {
                "pattern": r"(requests\.|urllib\.|time\.sleep)",
                "severity": IssueSeverity.MEDIUM,
            },
        }

    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def analyze_file(
        self,
        file_path: str,
        content: str,
        analysis_types: Optional[List[AnalysisType]] = None,
    ) -> CodeAnalysisResult:
        """
        Perform comprehensive AI-powered code analysis.

        Args:
            file_path: Path to the file being analyzed
            content: File content to analyze
            analysis_types: Types of analysis to perform (default: all)

        Returns:
            Complete analysis result with insights and recommendations
        """
        try:
            return await with_timeout(
                self._analyze_file_internal(file_path, content, analysis_types),
                AsyncTimeouts.ANALYTICS_AGGREGATION,
                f"Code analysis timed out for: {file_path}",
                {"file_path": file_path, "content_length": len(content)},
            )
        except Exception as e:
            logger.error(f"Code analysis failed for {file_path}: {e}")
            return self._create_minimal_result(file_path, content, str(e))

    async def _analyze_file_internal(
        self, file_path: str, content: str, analysis_types: Optional[List[AnalysisType]]
    ) -> CodeAnalysisResult:
        """Internal analysis implementation"""

        if analysis_types is None:
            analysis_types = list(AnalysisType)

        logger.info(
            f"🔍 Analyzing {file_path} with {len(analysis_types)} analysis types"
        )

        # Detect language
        language = self._detect_language(file_path, content)

        # Parallel analysis tasks
        analysis_tasks = []

        if AnalysisType.QUALITY in analysis_types:
            analysis_tasks.append(self._analyze_quality(content, file_path))

        if AnalysisType.SECURITY in analysis_types:
            analysis_tasks.append(self._analyze_security(content, file_path))

        if AnalysisType.PERFORMANCE in analysis_types:
            analysis_tasks.append(self._analyze_performance(content, file_path))

        if AnalysisType.REFACTORING in analysis_types:
            analysis_tasks.append(
                self._suggest_refactoring(content, file_path, language)
            )

        if AnalysisType.DOCUMENTATION in analysis_types:
            analysis_tasks.append(
                self._analyze_documentation(content, file_path, language)
            )

        # Execute analysis tasks concurrently
        results = await safe_gather(
            *analysis_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.ANALYTICS_QUERY,
            max_concurrency=5,
        )

        # Process results
        issues = []
        refactoring_suggestions = []
        performance_optimizations = []
        security_vulnerabilities = []
        documentation_gaps = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Analysis task {i} failed: {result}")
                continue

            # Extract results based on analysis type
            if analysis_types[i] == AnalysisType.QUALITY and isinstance(result, list):
                issues.extend(result)
            elif analysis_types[i] == AnalysisType.SECURITY and isinstance(
                result, list
            ):
                security_vulnerabilities.extend(result)
            elif analysis_types[i] == AnalysisType.PERFORMANCE and isinstance(
                result, list
            ):
                performance_optimizations.extend(result)
            elif analysis_types[i] == AnalysisType.REFACTORING and isinstance(
                result, list
            ):
                refactoring_suggestions.extend(result)
            elif analysis_types[i] == AnalysisType.DOCUMENTATION and isinstance(
                result, list
            ):
                documentation_gaps.extend(result)

        # Calculate metrics
        complexity_metrics = await self._calculate_complexity_metrics(content, language)
        quality_score = self._calculate_quality_score(issues, complexity_metrics)
        maintainability_index = self._calculate_maintainability_index(
            complexity_metrics, issues
        )

        # Generate AI insights
        ai_insights = await self._generate_ai_insights(
            file_path,
            content,
            issues,
            refactoring_suggestions,
            performance_optimizations,
        )

        from datetime import datetime, timezone

        return CodeAnalysisResult(
            file_path=file_path,
            language=language,
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            quality_score=quality_score,
            maintainability_index=maintainability_index,
            complexity_metrics=complexity_metrics,
            issues=issues,
            refactoring_suggestions=refactoring_suggestions,
            performance_optimizations=performance_optimizations,
            security_vulnerabilities=security_vulnerabilities,
            documentation_gaps=documentation_gaps,
            ai_insights=ai_insights,
        )

    async def _analyze_quality(self, content: str, file_path: str) -> List[CodeIssue]:
        """Analyze code quality issues"""

        issues = []
        lines = content.split("\n")

        # Check function length
        current_function = None
        function_start = 0

        for i, line in enumerate(lines):
            if line.strip().startswith("def "):
                if current_function:
                    # Check previous function length
                    function_length = i - function_start
                    if (
                        function_length
                        > self.quality_patterns["long_function"]["threshold"]
                    ):
                        issues.append(
                            CodeIssue(
                                type=AnalysisType.QUALITY,
                                severity=self.quality_patterns["long_function"][
                                    "severity"
                                ],
                                title="Long Function",
                                description=f"Function '{current_function}' is {function_length} lines long (recommended: <50)",
                                file_path=file_path,
                                line_number=function_start + 1,
                                suggestion="Consider breaking this function into smaller, more focused functions",
                                tags=["function-length", "maintainability"],
                            )
                        )

                current_function = line.strip().split("(")[0].replace("def ", "")
                function_start = i

        # Check for magic numbers
        for i, line in enumerate(lines):
            magic_numbers = re.findall(
                self.quality_patterns["magic_numbers"]["pattern"], line
            )
            for number in magic_numbers:
                if number not in ["0", "1", "100"]:  # Common acceptable numbers
                    issues.append(
                        CodeIssue(
                            type=AnalysisType.QUALITY,
                            severity=self.quality_patterns["magic_numbers"]["severity"],
                            title="Magic Number",
                            description=f"Magic number '{number}' found in code",
                            file_path=file_path,
                            line_number=i + 1,
                            code_snippet=line.strip(),
                            suggestion=f"Consider defining '{number}' as a named constant",
                            tags=["magic-numbers", "constants"],
                        )
                    )

        # Check for TODO comments
        for i, line in enumerate(lines):
            todos = re.findall(self.quality_patterns["todo_comments"]["pattern"], line)
            for todo_type in todos:
                issues.append(
                    CodeIssue(
                        type=AnalysisType.QUALITY,
                        severity=self.quality_patterns["todo_comments"]["severity"],
                        title=f"{todo_type} Comment",
                        description=f"Unresolved {todo_type} comment found",
                        file_path=file_path,
                        line_number=i + 1,
                        code_snippet=line.strip(),
                        suggestion=f"Address this {todo_type} or create a proper issue tracker entry",
                        tags=["todo", "technical-debt"],
                    )
                )

        return issues

    async def _analyze_security(
        self, content: str, file_path: str
    ) -> List[SecurityVulnerability]:
        """Analyze security vulnerabilities"""

        vulnerabilities = []
        lines = content.split("\n")

        # Check for SQL injection patterns
        for i, line in enumerate(lines):
            if re.search(self.security_patterns["sql_injection"]["pattern"], line):
                vulnerabilities.append(
                    SecurityVulnerability(
                        cve_type="SQL Injection",
                        severity=self.security_patterns["sql_injection"]["severity"],
                        title="Potential SQL Injection",
                        description="SQL query construction using string formatting",
                        file_path=file_path,
                        vulnerable_code=line.strip(),
                        secure_alternative="Use parameterized queries or ORM methods",
                        mitigation_steps=[
                            "Replace string formatting with parameterized queries",
                            "Use SQLAlchemy or similar ORM for query construction",
                            "Validate and sanitize all user inputs",
                        ],
                        references=[
                            "https://owasp.org/www-community/attacks/SQL_Injection",
                            "https://docs.sqlalchemy.org/en/14/core/tutorial.html#using-textual-sql",
                        ],
                    )
                )

        # Check for hardcoded secrets
        for i, line in enumerate(lines):
            if re.search(
                self.security_patterns["hardcoded_secrets"]["pattern"],
                line,
                re.IGNORECASE,
            ):
                vulnerabilities.append(
                    SecurityVulnerability(
                        cve_type="Hardcoded Credentials",
                        severity=self.security_patterns["hardcoded_secrets"][
                            "severity"
                        ],
                        title="Hardcoded Secret",
                        description="Potential hardcoded password, key, or token",
                        file_path=file_path,
                        vulnerable_code=line.strip(),
                        secure_alternative="Use environment variables or secure configuration",
                        mitigation_steps=[
                            "Move secrets to environment variables",
                            "Use secure secret management (e.g., HashiCorp Vault)",
                            "Implement proper secret rotation",
                        ],
                        references=[
                            "https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_password"
                        ],
                    )
                )

        # Check for dangerous eval usage
        for i, line in enumerate(lines):
            if re.search(self.security_patterns["eval_usage"]["pattern"], line):
                vulnerabilities.append(
                    SecurityVulnerability(
                        cve_type="Code Injection",
                        severity=self.security_patterns["eval_usage"]["severity"],
                        title="Dangerous eval() Usage",
                        description="Use of eval() function can lead to code injection",
                        file_path=file_path,
                        vulnerable_code=line.strip(),
                        secure_alternative="Use ast.literal_eval() for safe evaluation or alternative parsing",
                        mitigation_steps=[
                            "Replace eval() with ast.literal_eval() for literals",
                            "Use json.loads() for JSON data",
                            "Implement proper input validation and parsing",
                        ],
                        references=[
                            "https://docs.python.org/3/library/ast.html#ast.literal_eval"
                        ],
                    )
                )

        return vulnerabilities

    async def _analyze_performance(
        self, content: str, file_path: str
    ) -> List[PerformanceOptimization]:
        """Analyze performance optimization opportunities"""

        optimizations = []
        lines = content.split("\n")

        # Check for nested loops
        nested_loop_pattern = re.compile(r"for\s+.*?:.*?\n.*?for\s+.*?:", re.DOTALL)
        matches = nested_loop_pattern.finditer(content)

        for match in matches:
            line_num = content[: match.start()].count("\n") + 1
            optimizations.append(
                PerformanceOptimization(
                    title="Nested Loop Optimization",
                    description="Nested loops detected - potential O(n²) complexity",
                    file_path=file_path,
                    optimization_type="algorithm",
                    current_code=match.group(0),
                    optimized_code="# Consider using list comprehensions, set operations, or algorithmic improvements",
                    expected_improvement="Potential O(n) complexity reduction",
                    impact_assessment={
                        "complexity_reduction": "high",
                        "memory_impact": "low",
                        "readability_impact": "medium",
                    },
                    implementation_notes=[
                        "Analyze if inner loop can be replaced with set operations",
                        "Consider using dictionary lookups instead of nested iteration",
                        "Evaluate if data structure changes can eliminate nesting",
                    ],
                )
            )

        # Check for inefficient string concatenation
        for i, line in enumerate(lines):
            if re.search(
                self.performance_patterns["inefficient_string_concat"]["pattern"], line
            ):
                optimizations.append(
                    PerformanceOptimization(
                        title="String Concatenation Optimization",
                        description="Inefficient string concatenation in loop",
                        file_path=file_path,
                        optimization_type="algorithm",
                        current_code=line.strip(),
                        optimized_code="# Use list.append() and ''.join() for multiple concatenations",
                        expected_improvement="O(n) instead of O(n²) for multiple concatenations",
                        impact_assessment={
                            "complexity_reduction": "medium",
                            "memory_impact": "medium",
                            "readability_impact": "low",
                        },
                        implementation_notes=[
                            "Collect strings in a list and use ''.join() at the end",
                            "Use f-strings for single concatenations",
                            "Consider using StringIO for complex string building",
                        ],
                    )
                )

        # Check for blocking I/O operations
        for i, line in enumerate(lines):
            if re.search(self.performance_patterns["blocking_io"]["pattern"], line):
                optimizations.append(
                    PerformanceOptimization(
                        title="Async I/O Optimization",
                        description="Blocking I/O operation detected",
                        file_path=file_path,
                        optimization_type="async",
                        current_code=line.strip(),
                        optimized_code="# Use async/await with aiohttp or asyncio for I/O operations",
                        expected_improvement="Non-blocking execution and better concurrency",
                        impact_assessment={
                            "complexity_reduction": "high",
                            "memory_impact": "low",
                            "readability_impact": "medium",
                        },
                        implementation_notes=[
                            "Replace requests with aiohttp for HTTP calls",
                            "Use asyncio.sleep() instead of time.sleep()",
                            "Implement proper async context managers",
                        ],
                    )
                )

        return optimizations

    async def _suggest_refactoring(
        self, content: str, file_path: str, language: str
    ) -> List[RefactoringSuggestion]:
        """Generate AI-powered refactoring suggestions"""

        suggestions = []

        if language == "python":
            # Analyze Python-specific refactoring opportunities
            try:
                tree = ast.parse(content)

                # Find large functions that could be refactored
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        function_complexity = self._calculate_function_complexity(node)

                        if function_complexity > 15:  # High complexity threshold
                            suggestions.append(
                                RefactoringSuggestion(
                                    title=f"Refactor Complex Function: {node.name}",
                                    description=f"Function '{node.name}' has high complexity ({function_complexity})",
                                    file_path=file_path,
                                    original_code=f"def {node.name}(...): # {function_complexity} complexity points",
                                    refactored_code="# Split into smaller functions with single responsibilities",
                                    benefits=[
                                        "Improved readability and maintainability",
                                        "Easier testing and debugging",
                                        "Better code reusability",
                                        "Reduced cognitive load",
                                    ],
                                    complexity_reduction=0.6,  # Estimated 60% complexity reduction
                                    confidence=0.8,
                                    estimated_effort="medium",
                                )
                            )

                # Find classes with too many methods (God objects)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        method_count = len(
                            [n for n in node.body if isinstance(n, ast.FunctionDef)]
                        )

                        if method_count > 20:  # Too many methods
                            suggestions.append(
                                RefactoringSuggestion(
                                    title=f"Decompose Large Class: {node.name}",
                                    description=f"Class '{node.name}' has {method_count} methods (recommended: <20)",
                                    file_path=file_path,
                                    original_code=f"class {node.name}: # {method_count} methods",
                                    refactored_code="# Split into focused classes with single responsibilities",
                                    benefits=[
                                        "Better separation of concerns",
                                        "Easier testing and mocking",
                                        "Improved code organization",
                                        "Better adherence to SOLID principles",
                                    ],
                                    complexity_reduction=0.7,
                                    confidence=0.9,
                                    estimated_effort="high",
                                )
                            )

            except SyntaxError:
                # If AST parsing fails, provide generic suggestions
                pass

        # Generic refactoring suggestions based on content analysis
        lines = content.split("\n")

        # Check for code duplication
        line_counts = {}
        for line in lines:
            stripped = line.strip()
            if len(stripped) > 10:  # Ignore short lines
                line_counts[stripped] = line_counts.get(stripped, 0) + 1

        duplicated_lines = {
            line: count for line, count in line_counts.items() if count > 2
        }

        if duplicated_lines:
            suggestions.append(
                RefactoringSuggestion(
                    title="Extract Common Code",
                    description=f"Found {len(duplicated_lines)} duplicated code patterns",
                    file_path=file_path,
                    original_code=f"# {len(duplicated_lines)} duplicated patterns found",
                    refactored_code="# Extract common code into functions or constants",
                    benefits=[
                        "Reduced code duplication",
                        "Easier maintenance and updates",
                        "Better code consistency",
                        "DRY principle compliance",
                    ],
                    complexity_reduction=0.4,
                    confidence=0.7,
                    estimated_effort="low",
                )
            )

        return suggestions

    async def _analyze_documentation(
        self, content: str, file_path: str, language: str
    ) -> List[str]:
        """Analyze documentation gaps"""

        gaps = []

        if language == "python":
            try:
                tree = ast.parse(content)

                # Check for functions without docstrings
                undocumented_functions = []

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check if function has docstring
                        if not (
                            node.body
                            and isinstance(node.body[0], ast.Expr)
                            and isinstance(node.body[0].value, ast.Constant)
                            and isinstance(node.body[0].value.value, str)
                        ):
                            undocumented_functions.append(node.name)

                if undocumented_functions:
                    gaps.append(
                        f"Missing docstrings for {len(undocumented_functions)} functions: {', '.join(undocumented_functions[:5])}"
                    )

                # Check for classes without docstrings
                undocumented_classes = []

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if not (
                            node.body
                            and isinstance(node.body[0], ast.Expr)
                            and isinstance(node.body[0].value, ast.Constant)
                            and isinstance(node.body[0].value.value, str)
                        ):
                            undocumented_classes.append(node.name)

                if undocumented_classes:
                    gaps.append(
                        f"Missing docstrings for {len(undocumented_classes)} classes: {', '.join(undocumented_classes)}"
                    )

            except SyntaxError:
                gaps.append(
                    "File contains syntax errors - unable to analyze documentation"
                )

        # Check for missing type hints
        if (
            language == "python"
            and "from typing import" not in content
            and "->" not in content
        ):
            gaps.append(
                "Missing type hints - consider adding type annotations for better code clarity"
            )

        # Check for missing README or documentation files
        if file_path.endswith("__init__.py") and len(content.strip()) == 0:
            gaps.append("Empty __init__.py - consider adding module documentation")

        return gaps

    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function"""

        complexity = 1  # Base complexity

        for node in ast.walk(func_node):
            if isinstance(
                node,
                (
                    ast.If,
                    ast.While,
                    ast.For,
                    ast.AsyncFor,
                    ast.ExceptHandler,
                    ast.With,
                    ast.AsyncWith,
                ),
            ):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    async def _calculate_complexity_metrics(
        self, content: str, language: str
    ) -> Dict[str, Any]:
        """Calculate various complexity metrics"""

        lines = content.split("\n")

        metrics = {
            "total_lines": len(lines),
            "code_lines": len(
                [
                    line
                    for line in lines
                    if line.strip() and not line.strip().startswith("#")
                ]
            ),
            "comment_lines": len(
                [line for line in lines if line.strip().startswith("#")]
            ),
            "blank_lines": len([line for line in lines if not line.strip()]),
            "cyclomatic_complexity": 0,
            "function_count": 0,
            "class_count": 0,
            "import_count": 0,
        }

        if language == "python":
            try:
                tree = ast.parse(content)

                # Count functions and classes
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        metrics["function_count"] += 1
                        metrics[
                            "cyclomatic_complexity"
                        ] += self._calculate_function_complexity(node)
                    elif isinstance(node, ast.ClassDef):
                        metrics["class_count"] += 1
                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        metrics["import_count"] += 1

            except SyntaxError:
                # Fallback to regex-based counting
                metrics["function_count"] = len(
                    re.findall(r"^\s*def\s+", content, re.MULTILINE)
                )
                metrics["class_count"] = len(
                    re.findall(r"^\s*class\s+", content, re.MULTILINE)
                )
                metrics["import_count"] = len(
                    re.findall(r"^\s*(?:import|from)\s+", content, re.MULTILINE)
                )

        return metrics

    def _calculate_quality_score(
        self, issues: List[CodeIssue], metrics: Dict[str, Any]
    ) -> float:
        """Calculate overall quality score (0-100)"""

        base_score = 100

        # Penalize for issues
        for issue in issues:
            if issue.severity == IssueSeverity.CRITICAL:
                base_score -= 20
            elif issue.severity == IssueSeverity.HIGH:
                base_score -= 10
            elif issue.severity == IssueSeverity.MEDIUM:
                base_score -= 5
            elif issue.severity == IssueSeverity.LOW:
                base_score -= 2

        # Penalize for high complexity
        if metrics.get("cyclomatic_complexity", 0) > 50:
            base_score -= (metrics["cyclomatic_complexity"] - 50) * 0.5

        # Bonus for good documentation ratio
        comment_ratio = metrics.get("comment_lines", 0) / max(
            metrics.get("code_lines", 1), 1
        )
        if comment_ratio > 0.1:  # At least 10% comments
            base_score += min(comment_ratio * 50, 10)  # Max 10 bonus points

        return max(0, min(100, base_score))

    def _calculate_maintainability_index(
        self, metrics: Dict[str, Any], issues: List[CodeIssue]
    ) -> float:
        """Calculate maintainability index"""

        # Simplified maintainability index calculation
        volume = metrics.get("code_lines", 0)
        complexity = metrics.get("cyclomatic_complexity", 1)

        if volume <= 0:
            return 0

        # Base formula: 171 - 5.2 * ln(V) - 0.23 * CC - 16.2 * ln(LOC)
        import math

        base_mi = 171 - 5.2 * math.log(volume + 1) - 0.23 * complexity

        # Adjust for issues
        issue_penalty = (
            len(
                [
                    i
                    for i in issues
                    if i.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]
                ]
            )
            * 5
        )

        return max(0, min(100, base_mi - issue_penalty))

    async def _generate_ai_insights(
        self,
        file_path: str,
        content: str,
        issues: List[CodeIssue],
        refactoring_suggestions: List[RefactoringSuggestion],
        performance_optimizations: List[PerformanceOptimization],
    ) -> Dict[str, Any]:
        """Generate AI-powered insights and recommendations"""

        # This would integrate with LLM for deeper insights
        # For now, provide rule-based insights

        insights = {
            "summary": f"Analyzed {len(content.split())} lines of code",
            "key_recommendations": [],
            "architectural_suggestions": [],
            "best_practices": [],
            "learning_resources": [],
        }

        # Key recommendations based on analysis
        if len(issues) > 10:
            insights["key_recommendations"].append(
                "High number of issues detected - prioritize addressing critical and high severity issues first"
            )

        if len(refactoring_suggestions) > 3:
            insights["key_recommendations"].append(
                "Multiple refactoring opportunities identified - consider implementing them in phases"
            )

        if len(performance_optimizations) > 2:
            insights["key_recommendations"].append(
                "Performance optimization opportunities found - profile code to validate impact before implementing"
            )

        # Architectural suggestions
        function_count = len(re.findall(r"def\s+\w+", content))
        if function_count > 50:
            insights["architectural_suggestions"].append(
                "Large number of functions in single file - consider splitting into multiple modules"
            )

        # Best practices
        if "async def" in content and "await" not in content:
            insights["best_practices"].append(
                "Async functions detected without await - ensure proper async/await usage"
            )

        if "try:" in content and "except:" in content:
            insights["best_practices"].append(
                "Generic exception handling found - use specific exception types when possible"
            )

        return insights

    def _detect_language(self, file_path: str, content: str) -> str:
        """Detect programming language"""

        ext = Path(file_path).suffix.lower()

        if ext == ".py":
            return "python"
        elif ext in [".js", ".jsx"]:
            return "javascript"
        elif ext in [".ts", ".tsx"]:
            return "typescript"
        elif ext in [".java"]:
            return "java"
        elif ext in [".go"]:
            return "go"
        else:
            return "unknown"

    def _create_minimal_result(
        self, file_path: str, content: str, error: str
    ) -> CodeAnalysisResult:
        """Create minimal result when analysis fails"""

        from datetime import datetime, timezone

        return CodeAnalysisResult(
            file_path=file_path,
            language=self._detect_language(file_path, content),
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            quality_score=50.0,  # Default score
            maintainability_index=50.0,
            complexity_metrics={
                "total_lines": len(content.split("\n")),
                "error": error,
            },
            issues=[],
            refactoring_suggestions=[],
            performance_optimizations=[],
            security_vulnerabilities=[],
            documentation_gaps=[],
            ai_insights={"error": error, "status": "analysis_failed"},
        )


# Convenience functions
async def analyze_code_file(
    file_path: str, content: str, analysis_types: Optional[List[AnalysisType]] = None
) -> CodeAnalysisResult:
    """Analyze a single code file with AI insights"""
    analyzer = AICodeAnalyzer()
    return await analyzer.analyze_file(file_path, content, analysis_types)


async def analyze_project_quality(
    project_path: str, file_patterns: Optional[List[str]] = None
) -> Dict[str, CodeAnalysisResult]:
    """Analyze code quality for an entire project"""

    import glob
    import os

    if file_patterns is None:
        file_patterns = ["**/*.py", "**/*.js", "**/*.ts"]

    analyzer = AICodeAnalyzer()
    results = {}

    for pattern in file_patterns:
        files = glob.glob(os.path.join(project_path, pattern), recursive=True)

        for file_path in files[:20]:  # Limit for performance
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                relative_path = os.path.relpath(file_path, project_path)
                result = await analyzer.analyze_file(relative_path, content)
                results[relative_path] = result

            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")

    return results


async def get_project_health_summary(project_path: str) -> Dict[str, Any]:
    """Get high-level project health summary"""

    results = await analyze_project_quality(project_path)

    total_files = len(results)
    if total_files == 0:
        return {"error": "No files analyzed"}

    avg_quality = sum(r.quality_score for r in results.values()) / total_files
    total_issues = sum(len(r.issues) for r in results.values())
    total_vulnerabilities = sum(
        len(r.security_vulnerabilities) for r in results.values()
    )
    total_optimizations = sum(
        len(r.performance_optimizations) for r in results.values()
    )

    return {
        "files_analyzed": total_files,
        "average_quality_score": round(avg_quality, 1),
        "total_issues": total_issues,
        "security_vulnerabilities": total_vulnerabilities,
        "performance_optimizations": total_optimizations,
        "health_grade": (
            "A"
            if avg_quality >= 80
            else "B" if avg_quality >= 60 else "C" if avg_quality >= 40 else "D"
        ),
        "recommendations": [
            f"Address {total_issues} code quality issues",
            f"Review {total_vulnerabilities} security vulnerabilities",
            f"Consider {total_optimizations} performance optimizations",
        ],
    }
