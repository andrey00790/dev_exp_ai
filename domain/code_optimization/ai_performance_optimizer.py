"""
AI Performance Optimizer - Intelligent performance analysis and optimization suggestions.
"""

import ast
import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from app.core.async_utils import AsyncTimeouts, async_retry, with_timeout

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """Types of performance optimizations"""

    ALGORITHM = "algorithm"
    DATABASE = "database"
    CACHING = "caching"
    ASYNC_IO = "async_io"
    MEMORY = "memory"
    CPU = "cpu"
    NETWORKING = "networking"


class ImpactLevel(Enum):
    """Performance impact levels"""

    CRITICAL = "critical"  # >50% improvement
    HIGH = "high"  # 20-50% improvement
    MEDIUM = "medium"  # 5-20% improvement
    LOW = "low"  # <5% improvement


@dataclass
class PerformanceIssue:
    """Performance issue detected"""

    type: OptimizationType
    title: str
    description: str
    file_path: str
    line_number: int
    current_code: str
    optimized_code: str
    expected_improvement: str
    impact_level: ImpactLevel
    confidence: float
    implementation_effort: str
    prerequisites: List[str]


@dataclass
class PerformanceProfile:
    """Performance profile for code"""

    file_path: str
    total_issues: int
    critical_issues: int
    estimated_speedup: str
    memory_savings: str
    optimization_priority: str
    issues: List[PerformanceIssue]


class AIPerformanceOptimizer:
    """AI-powered performance optimizer"""

    def __init__(self):
        # Performance anti-patterns
        self.anti_patterns = {
            "nested_loops": {
                "pattern": r"for\s+.*?:\s*.*?for\s+.*?:",
                "severity": ImpactLevel.HIGH,
                "improvement": "50-80% with algorithm optimization",
            },
            "inefficient_string_concat": {
                "pattern": r'(\w+\s*\+=\s*["\'].*?["\'])',
                "severity": ImpactLevel.MEDIUM,
                "improvement": "200-500% with join() method",
            },
            "list_in_loop": {
                "pattern": r"in\s+\[.*?\].*?for",
                "severity": ImpactLevel.MEDIUM,
                "improvement": "10-50x with set conversion",
            },
            "repeated_regex": {
                "pattern": r're\.(search|match|findall)\s*\(["\'].*?["\']',
                "severity": ImpactLevel.MEDIUM,
                "improvement": "30-70% with compiled regex",
            },
            "blocking_io": {
                "pattern": r"(requests\.|urllib\.|time\.sleep|open\()",
                "severity": ImpactLevel.HIGH,
                "improvement": "90%+ with async/await",
            },
            "database_n_plus_one": {
                "pattern": r"for\s+.*?:\s*.*?\.(get|filter|query)",
                "severity": ImpactLevel.CRITICAL,
                "improvement": "95%+ with bulk operations",
            },
            "unnecessary_list_copy": {
                "pattern": r"list\(\w+\)",
                "severity": ImpactLevel.LOW,
                "improvement": "10-30% memory reduction",
            },
        }

        # Optimization templates
        self.optimization_templates = {
            "list_comprehension": {
                "original": "result = []\nfor item in items:\n    result.append(process(item))",
                "optimized": "result = [process(item) for item in items]",
                "improvement": "2-3x faster",
            },
            "generator_expression": {
                "original": "sum([x*x for x in range(1000)])",
                "optimized": "sum(x*x for x in range(1000))",
                "improvement": "Memory efficient",
            },
            "set_membership": {
                "original": "if item in [a, b, c, d]:",
                "optimized": "if item in {a, b, c, d}:",
                "improvement": "O(1) vs O(n) lookup",
            },
        }

    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def analyze_performance(
        self, file_path: str, content: str
    ) -> PerformanceProfile:
        """Analyze performance issues and generate optimization suggestions"""
        try:
            return await with_timeout(
                self._analyze_performance_internal(file_path, content),
                AsyncTimeouts.ANALYTICS_AGGREGATION,
                f"Performance analysis timed out: {file_path}",
                {"file_path": file_path},
            )
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return PerformanceProfile(
                file_path=file_path,
                total_issues=0,
                critical_issues=0,
                estimated_speedup="Unknown",
                memory_savings="Unknown",
                optimization_priority="Low",
                issues=[],
            )

    async def _analyze_performance_internal(
        self, file_path: str, content: str
    ) -> PerformanceProfile:
        """Internal performance analysis implementation"""

        logger.info(f"⚡ Analyzing performance for: {file_path}")

        issues = []

        # Detect anti-patterns
        issues.extend(await self._detect_anti_patterns(content, file_path))

        # Analyze algorithmic complexity
        issues.extend(await self._analyze_complexity(content, file_path))

        # Check database operations
        issues.extend(await self._analyze_database_operations(content, file_path))

        # Analyze memory usage patterns
        issues.extend(await self._analyze_memory_patterns(content, file_path))

        # Check async/await usage
        issues.extend(await self._analyze_async_patterns(content, file_path))

        # Calculate metrics
        total_issues = len(issues)
        critical_issues = len(
            [i for i in issues if i.impact_level == ImpactLevel.CRITICAL]
        )

        estimated_speedup = self._calculate_speedup_estimate(issues)
        memory_savings = self._calculate_memory_savings(issues)
        priority = self._determine_priority(issues)

        logger.info(
            f"🎯 Found {total_issues} performance issues ({critical_issues} critical)"
        )

        return PerformanceProfile(
            file_path=file_path,
            total_issues=total_issues,
            critical_issues=critical_issues,
            estimated_speedup=estimated_speedup,
            memory_savings=memory_savings,
            optimization_priority=priority,
            issues=sorted(
                issues, key=lambda x: (x.impact_level.value, x.confidence), reverse=True
            ),
        )

    async def _detect_anti_patterns(
        self, content: str, file_path: str
    ) -> List[PerformanceIssue]:
        """Detect performance anti-patterns"""

        issues = []

        for pattern_name, pattern_info in self.anti_patterns.items():
            matches = list(
                re.finditer(pattern_info["pattern"], content, re.MULTILINE | re.DOTALL)
            )

            for match in matches:
                line_num = content[: match.start()].count("\n") + 1

                # Generate specific optimization for this pattern
                optimization = self._generate_optimization(
                    pattern_name, match.group(0), content, match.start()
                )

                if optimization:
                    issues.append(
                        PerformanceIssue(
                            type=self._get_optimization_type(pattern_name),
                            title=f"Performance Issue: {pattern_name.replace('_', ' ').title()}",
                            description=optimization["description"],
                            file_path=file_path,
                            line_number=line_num,
                            current_code=match.group(0).strip(),
                            optimized_code=optimization["optimized_code"],
                            expected_improvement=pattern_info["improvement"],
                            impact_level=pattern_info["severity"],
                            confidence=optimization["confidence"],
                            implementation_effort=optimization["effort"],
                            prerequisites=optimization.get("prerequisites", []),
                        )
                    )

        return issues

    async def _analyze_complexity(
        self, content: str, file_path: str
    ) -> List[PerformanceIssue]:
        """Analyze algorithmic complexity issues"""

        issues = []

        if file_path.endswith(".py"):
            try:
                tree = ast.parse(content)

                # Find nested loops (potential O(n²) or worse)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        complexity_issues = self._analyze_function_complexity(
                            node, content
                        )
                        issues.extend(complexity_issues)

            except SyntaxError:
                logger.warning(
                    f"Could not parse file for complexity analysis: {file_path}"
                )

        return issues

    async def _analyze_database_operations(
        self, content: str, file_path: str
    ) -> List[PerformanceIssue]:
        """Analyze database operation patterns"""

        issues = []

        # Check for N+1 query problems
        n_plus_one_pattern = r"for\s+\w+\s+in\s+.*?:\s*.*?\.(get|filter|objects\.get)"
        matches = list(
            re.finditer(n_plus_one_pattern, content, re.MULTILINE | re.DOTALL)
        )

        for match in matches:
            line_num = content[: match.start()].count("\n") + 1

            issues.append(
                PerformanceIssue(
                    type=OptimizationType.DATABASE,
                    title="N+1 Query Problem",
                    description="Multiple database queries in loop - use select_related() or prefetch_related()",
                    file_path=file_path,
                    line_number=line_num,
                    current_code=match.group(0).strip(),
                    optimized_code="# Use bulk query with select_related() or prefetch_related()",
                    expected_improvement="90-99% query reduction",
                    impact_level=ImpactLevel.CRITICAL,
                    confidence=0.8,
                    implementation_effort="Medium",
                    prerequisites=["Django ORM or similar framework"],
                )
            )

        # Check for missing indexes
        filter_patterns = [r"\.filter\(\w+__\w+=", r"\.get\(\w+=", r"WHERE\s+\w+\s*="]

        for pattern in filter_patterns:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))

            for match in matches:
                line_num = content[: match.start()].count("\n") + 1

                issues.append(
                    PerformanceIssue(
                        type=OptimizationType.DATABASE,
                        title="Potential Missing Index",
                        description="Query on field that may benefit from database index",
                        file_path=file_path,
                        line_number=line_num,
                        current_code=match.group(0),
                        optimized_code="# Add database index: db_index=True or Index()",
                        expected_improvement="10-1000x query speed",
                        impact_level=ImpactLevel.HIGH,
                        confidence=0.6,
                        implementation_effort="Low",
                        prerequisites=["Database access for index creation"],
                    )
                )

        return issues

    async def _analyze_memory_patterns(
        self, content: str, file_path: str
    ) -> List[PerformanceIssue]:
        """Analyze memory usage patterns"""

        issues = []

        # Check for large list creations that could be generators
        large_list_patterns = [
            r"\[.*?for.*?in.*?range\(\d{4,}\)",  # Large range in list comprehension
            r"list\(range\(\d{4,}\)\)",  # Large range to list
        ]

        for pattern in large_list_patterns:
            matches = list(re.finditer(pattern, content))

            for match in matches:
                line_num = content[: match.start()].count("\n") + 1

                issues.append(
                    PerformanceIssue(
                        type=OptimizationType.MEMORY,
                        title="Memory Optimization: Use Generator",
                        description="Large list creation - consider using generator for memory efficiency",
                        file_path=file_path,
                        line_number=line_num,
                        current_code=match.group(0),
                        optimized_code=self._convert_to_generator(match.group(0)),
                        expected_improvement="90%+ memory reduction",
                        impact_level=ImpactLevel.MEDIUM,
                        confidence=0.9,
                        implementation_effort="Low",
                        prerequisites=[],
                    )
                )

        # Check for unnecessary copying
        copy_patterns = [r"list\(\w+\)", r"dict\(\w+\)", r"\w+\.copy\(\)"]

        for pattern in copy_patterns:
            matches = list(re.finditer(pattern, content))

            for match in matches:
                line_num = content[: match.start()].count("\n") + 1

                issues.append(
                    PerformanceIssue(
                        type=OptimizationType.MEMORY,
                        title="Unnecessary Copy Operation",
                        description="Consider if copy is needed - direct reference may be sufficient",
                        file_path=file_path,
                        line_number=line_num,
                        current_code=match.group(0),
                        optimized_code="# Use direct reference if modification not needed",
                        expected_improvement="Memory allocation reduction",
                        impact_level=ImpactLevel.LOW,
                        confidence=0.7,
                        implementation_effort="Low",
                        prerequisites=["Verify no side effects"],
                    )
                )

        return issues

    async def _analyze_async_patterns(
        self, content: str, file_path: str
    ) -> List[PerformanceIssue]:
        """Analyze async/await usage patterns"""

        issues = []

        # Check for blocking I/O in async functions
        if "async def" in content:
            blocking_patterns = [
                r"requests\.(get|post|put|delete)",
                r"time\.sleep\(",
                r"open\(",
                r"input\(",
            ]

            for pattern in blocking_patterns:
                matches = list(re.finditer(pattern, content))

                for match in matches:
                    line_num = content[: match.start()].count("\n") + 1

                    # Check if we're inside an async function
                    if self._is_in_async_function(content, match.start()):
                        issues.append(
                            PerformanceIssue(
                                type=OptimizationType.ASYNC_IO,
                                title="Blocking I/O in Async Function",
                                description="Use async alternative to avoid blocking event loop",
                                file_path=file_path,
                                line_number=line_num,
                                current_code=match.group(0),
                                optimized_code=self._get_async_alternative(
                                    match.group(0)
                                ),
                                expected_improvement="Prevents event loop blocking",
                                impact_level=ImpactLevel.HIGH,
                                confidence=0.9,
                                implementation_effort="Medium",
                                prerequisites=[
                                    "Async library (aiohttp, aiofiles, etc.)"
                                ],
                            )
                        )

        # Check for missing await keywords
        async_calls = re.finditer(r"(\w+)\s*\(\s*\)", content)
        for match in async_calls:
            if self._might_be_async_call(match.group(1)):
                line_num = content[: match.start()].count("\n") + 1

                issues.append(
                    PerformanceIssue(
                        type=OptimizationType.ASYNC_IO,
                        title="Missing await keyword",
                        description="Async function call may need await keyword",
                        file_path=file_path,
                        line_number=line_num,
                        current_code=match.group(0),
                        optimized_code=f"await {match.group(0)}",
                        expected_improvement="Proper async execution",
                        impact_level=ImpactLevel.MEDIUM,
                        confidence=0.6,
                        implementation_effort="Low",
                        prerequisites=["Verify function is async"],
                    )
                )

        return issues

    def _analyze_function_complexity(
        self, func_node: ast.FunctionDef, content: str
    ) -> List[PerformanceIssue]:
        """Analyze complexity of individual function"""

        issues = []

        # Count nested loops
        loop_depth = self._calculate_loop_depth(func_node)

        if loop_depth > 2:  # More than 2 levels of nesting
            issues.append(
                PerformanceIssue(
                    type=OptimizationType.ALGORITHM,
                    title=f"High Algorithmic Complexity: {func_node.name}()",
                    description=f"Function has {loop_depth} levels of nested loops - O(n^{loop_depth}) complexity",
                    file_path="",  # Will be set by caller
                    line_number=func_node.lineno,
                    current_code=f"def {func_node.name}(...): # {loop_depth} nested loops",
                    optimized_code="# Consider algorithm optimization, caching, or data structure changes",
                    expected_improvement=f"Potential O(n^{loop_depth-1}) or better reduction",
                    impact_level=(
                        ImpactLevel.CRITICAL if loop_depth > 3 else ImpactLevel.HIGH
                    ),
                    confidence=0.9,
                    implementation_effort="High",
                    prerequisites=["Algorithm analysis and redesign"],
                )
            )

        return issues

    def _calculate_loop_depth(self, node: ast.AST) -> int:
        """Calculate maximum loop nesting depth"""

        max_depth = 0

        def visit_node(node, depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, depth)

            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.For, ast.While)):
                    visit_node(child, depth + 1)
                else:
                    visit_node(child, depth)

        visit_node(node)
        return max_depth

    def _generate_optimization(
        self, pattern_name: str, matched_code: str, full_content: str, position: int
    ) -> Optional[Dict[str, Any]]:
        """Generate specific optimization for detected pattern"""

        optimizations = {
            "nested_loops": {
                "description": "Nested loops detected - consider algorithmic optimization",
                "optimized_code": "# Use dictionary lookup, set operations, or different algorithm",
                "confidence": 0.8,
                "effort": "High",
                "prerequisites": ["Algorithm analysis", "Data structure redesign"],
            },
            "inefficient_string_concat": {
                "description": "String concatenation in loop - use join() for better performance",
                "optimized_code": "result = ''.join(string_parts)",
                "confidence": 0.95,
                "effort": "Low",
            },
            "list_in_loop": {
                "description": "List membership testing in loop - convert to set for O(1) lookup",
                "optimized_code": "item_set = set(items)\nif item in item_set:",
                "confidence": 0.9,
                "effort": "Low",
            },
            "repeated_regex": {
                "description": "Regex compilation in loop - compile once outside loop",
                "optimized_code": 'pattern = re.compile(r"...")\npattern.search(text)',
                "confidence": 0.85,
                "effort": "Low",
            },
            "blocking_io": {
                "description": "Blocking I/O operation - use async alternative",
                "optimized_code": "async with aiohttp.ClientSession() as session:\n    await session.get(url)",
                "confidence": 0.9,
                "effort": "Medium",
                "prerequisites": ["Async library installation"],
            },
            "database_n_plus_one": {
                "description": "N+1 query problem - use bulk operations",
                "optimized_code": 'queryset.select_related("field").prefetch_related("related")',
                "confidence": 0.85,
                "effort": "Medium",
            },
            "unnecessary_list_copy": {
                "description": "Unnecessary list copy - use original if no modifications needed",
                "optimized_code": "# Use original list directly if no modifications",
                "confidence": 0.7,
                "effort": "Low",
            },
        }

        return optimizations.get(pattern_name)

    def _get_optimization_type(self, pattern_name: str) -> OptimizationType:
        """Get optimization type for pattern"""

        type_mapping = {
            "nested_loops": OptimizationType.ALGORITHM,
            "inefficient_string_concat": OptimizationType.ALGORITHM,
            "list_in_loop": OptimizationType.ALGORITHM,
            "repeated_regex": OptimizationType.CPU,
            "blocking_io": OptimizationType.ASYNC_IO,
            "database_n_plus_one": OptimizationType.DATABASE,
            "unnecessary_list_copy": OptimizationType.MEMORY,
        }

        return type_mapping.get(pattern_name, OptimizationType.ALGORITHM)

    def _convert_to_generator(self, list_expression: str) -> str:
        """Convert list expression to generator"""

        if list_expression.startswith("[") and list_expression.endswith("]"):
            return f"({list_expression[1:-1]})"
        elif list_expression.startswith("list("):
            inner = list_expression[5:-1]
            return f"({inner})" if "range(" in inner else f"iter({inner})"

        return f"# Convert to generator: {list_expression}"

    def _is_in_async_function(self, content: str, position: int) -> bool:
        """Check if position is inside an async function"""

        # Find the most recent function definition before this position
        content_before = content[:position]

        # Look for async def patterns
        async_matches = list(re.finditer(r"async\s+def\s+\w+", content_before))
        regular_matches = list(re.finditer(r"^def\s+\w+", content_before, re.MULTILINE))

        if not async_matches:
            return False

        # Get the most recent function definition
        last_async = async_matches[-1] if async_matches else None
        last_regular = regular_matches[-1] if regular_matches else None

        # If the most recent function is async, we're likely in an async function
        if last_async and (
            not last_regular or last_async.start() > last_regular.start()
        ):
            return True

        return False

    def _get_async_alternative(self, blocking_code: str) -> str:
        """Get async alternative for blocking operation"""

        alternatives = {
            "requests.get": "async with aiohttp.ClientSession() as session:\n    await session.get",
            "requests.post": "async with aiohttp.ClientSession() as session:\n    await session.post",
            "time.sleep": "await asyncio.sleep",
            "open(": "async with aiofiles.open",
            "input(": "# Use async input alternative or queue",
        }

        for pattern, replacement in alternatives.items():
            if pattern in blocking_code:
                return replacement

        return f"# Async alternative for: {blocking_code}"

    def _might_be_async_call(self, function_name: str) -> bool:
        """Check if function name suggests it might be async"""

        async_indicators = [
            "fetch",
            "get",
            "post",
            "put",
            "delete",
            "send",
            "receive",
            "connect",
            "disconnect",
            "read",
            "write",
            "save",
            "load",
            "process",
            "execute",
            "run",
        ]

        return any(indicator in function_name.lower() for indicator in async_indicators)

    def _calculate_speedup_estimate(self, issues: List[PerformanceIssue]) -> str:
        """Calculate estimated speedup from optimizations"""

        if not issues:
            return "No optimizations identified"

        critical_count = len(
            [i for i in issues if i.impact_level == ImpactLevel.CRITICAL]
        )
        high_count = len([i for i in issues if i.impact_level == ImpactLevel.HIGH])

        if critical_count > 0:
            return f"10-100x potential speedup ({critical_count} critical issues)"
        elif high_count > 2:
            return f"2-10x potential speedup ({high_count} high-impact issues)"
        else:
            return "10-50% potential improvement"

    def _calculate_memory_savings(self, issues: List[PerformanceIssue]) -> str:
        """Calculate estimated memory savings"""

        memory_issues = [i for i in issues if i.type == OptimizationType.MEMORY]

        if not memory_issues:
            return "No memory optimizations identified"

        if len(memory_issues) > 3:
            return "50-90% memory reduction possible"
        else:
            return "10-30% memory savings possible"

    def _determine_priority(self, issues: List[PerformanceIssue]) -> str:
        """Determine optimization priority"""

        critical_count = len(
            [i for i in issues if i.impact_level == ImpactLevel.CRITICAL]
        )
        high_count = len([i for i in issues if i.impact_level == ImpactLevel.HIGH])

        if critical_count > 0:
            return "Critical - Immediate optimization needed"
        elif high_count > 2:
            return "High - Significant performance gains available"
        elif len(issues) > 5:
            return "Medium - Multiple small optimizations"
        else:
            return "Low - Minor improvements available"


# Convenience functions
async def analyze_performance_issues(
    file_path: str, content: str
) -> PerformanceProfile:
    """Analyze performance issues in code file"""
    optimizer = AIPerformanceOptimizer()
    return await optimizer.analyze_performance(file_path, content)


async def get_top_performance_issues(
    file_path: str, content: str, limit: int = 5
) -> List[PerformanceIssue]:
    """Get top performance issues"""
    profile = await analyze_performance_issues(file_path, content)
    return profile.issues[:limit]


async def get_performance_summary(file_path: str, content: str) -> Dict[str, Any]:
    """Get performance analysis summary"""
    optimizer = AIPerformanceOptimizer()
    profile = await optimizer.analyze_performance(file_path, content)

    return {
        "file_path": file_path,
        "total_issues": profile.total_issues,
        "critical_issues": profile.critical_issues,
        "estimated_speedup": profile.estimated_speedup,
        "memory_savings": profile.memory_savings,
        "optimization_priority": profile.optimization_priority,
        "top_issues": [
            {
                "type": issue.type.value,
                "title": issue.title,
                "impact": issue.impact_level.value,
                "confidence": issue.confidence,
            }
            for issue in profile.issues[:3]
        ],
    }


# Alias for backward compatibility
async def analyze_file_performance(file_path: str, content: str) -> PerformanceProfile:
    """Analyze file performance (alias for analyze_performance_issues)"""
    return await analyze_performance_issues(file_path, content)
