"""
Smart Refactoring Engine - AI-powered code refactoring suggestions and automation.
Provides intelligent code improvements based on best practices and patterns.
"""

import ast
import asyncio
import difflib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.async_utils import AsyncTimeouts, async_retry, with_timeout

from .ai_code_analyzer import CodeAnalysisResult, CodeIssue, IssueSeverity

logger = logging.getLogger(__name__)


class RefactoringType(Enum):
    """Types of refactoring operations"""

    EXTRACT_METHOD = "extract_method"
    EXTRACT_VARIABLE = "extract_variable"
    INLINE_METHOD = "inline_method"
    RENAME_VARIABLE = "rename_variable"
    SPLIT_CLASS = "split_class"
    MERGE_CLASSES = "merge_classes"
    SIMPLIFY_CONDITION = "simplify_condition"
    REMOVE_DUPLICATION = "remove_duplication"
    OPTIMIZE_IMPORTS = "optimize_imports"
    ADD_TYPE_HINTS = "add_type_hints"
    CONVERT_TO_ASYNC = "convert_to_async"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"


class RefactoringComplexity(Enum):
    """Complexity levels for refactoring operations"""

    TRIVIAL = "trivial"  # Automated safe changes
    SIMPLE = "simple"  # Low risk, high confidence
    MODERATE = "moderate"  # Some risk, manual review recommended
    COMPLEX = "complex"  # High risk, careful analysis needed
    EXPERIMENTAL = "experimental"  # New patterns, requires testing


@dataclass
class RefactoringOperation:
    """A specific refactoring operation"""

    type: RefactoringType
    title: str
    description: str
    file_path: str
    line_start: int
    line_end: int
    original_code: str
    refactored_code: str
    benefits: List[str]
    risks: List[str]
    complexity: RefactoringComplexity
    confidence: float  # 0.0 to 1.0
    estimated_time: str  # "5 minutes", "30 minutes", etc.
    prerequisites: List[str]  # Required before applying
    side_effects: List[str]  # Potential impacts


@dataclass
class RefactoringPlan:
    """Complete refactoring plan for a file or project"""

    file_path: str
    operations: List[RefactoringOperation]
    execution_order: List[int]  # Indices of operations in optimal order
    total_estimated_time: str
    risk_assessment: str
    success_probability: float


class SmartRefactoringEngine:
    """
    AI-powered refactoring engine that analyzes code and suggests improvements.

    Features:
    - Automated detection of refactoring opportunities
    - Risk assessment and complexity analysis
    - Code generation for refactored versions
    - Dependency analysis and ordering
    - Performance impact estimation
    """

    def __init__(self):
        # Refactoring patterns and rules
        self.refactoring_patterns = {
            RefactoringType.EXTRACT_METHOD: {
                "min_lines": 5,
                "max_complexity": 15,
                "confidence_threshold": 0.7,
            },
            RefactoringType.EXTRACT_VARIABLE: {
                "min_expression_length": 20,
                "confidence_threshold": 0.8,
            },
            RefactoringType.SIMPLIFY_CONDITION: {
                "max_nesting": 3,
                "confidence_threshold": 0.9,
            },
        }

        # Performance optimization patterns
        self.performance_patterns = {
            "list_comprehension": {
                "pattern": r"for\s+\w+\s+in\s+.*?:\s*\w+\.append\(",
                "improvement": "Use list comprehension for better performance",
            },
            "string_join": {
                "pattern": r'\w+\s*\+=\s*["\']',
                "improvement": "Use str.join() for multiple string concatenations",
            },
            "set_membership": {
                "pattern": r"in\s+\[.*?\]",
                "improvement": "Use set() for membership testing",
            },
        }

        # Common variable naming improvements
        self.naming_improvements = {
            "temp": "temporary_value",
            "tmp": "temporary_data",
            "data": "processed_data",
            "result": "calculation_result",
            "x": "value",
            "i": "index",
            "j": "secondary_index",
        }

    @async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
    async def analyze_refactoring_opportunities(
        self,
        file_path: str,
        content: str,
        analysis_result: Optional[CodeAnalysisResult] = None,
    ) -> RefactoringPlan:
        """
        Analyze code and generate comprehensive refactoring plan.

        Args:
            file_path: Path to the file being analyzed
            content: File content
            analysis_result: Previous analysis result (optional)

        Returns:
            Complete refactoring plan with prioritized operations
        """
        try:
            return await with_timeout(
                self._analyze_refactoring_internal(file_path, content, analysis_result),
                AsyncTimeouts.ANALYTICS_AGGREGATION,
                f"Refactoring analysis timed out: {file_path}",
                {"file_path": file_path},
            )
        except Exception as e:
            logger.error(f"Refactoring analysis failed for {file_path}: {e}")
            return RefactoringPlan(
                file_path=file_path,
                operations=[],
                execution_order=[],
                total_estimated_time="Unknown",
                risk_assessment="Analysis failed",
                success_probability=0.0,
            )

    async def _analyze_refactoring_internal(
        self,
        file_path: str,
        content: str,
        analysis_result: Optional[CodeAnalysisResult],
    ) -> RefactoringPlan:
        """Internal refactoring analysis implementation"""

        logger.info(f"🔧 Analyzing refactoring opportunities for: {file_path}")

        operations = []

        # Detect language
        language = self._detect_language(file_path)

        if language == "python":
            # Python-specific refactoring opportunities
            operations.extend(
                await self._analyze_python_refactoring(content, file_path)
            )

        # Language-agnostic refactoring opportunities
        operations.extend(await self._analyze_generic_refactoring(content, file_path))

        # Performance optimization opportunities
        operations.extend(
            await self._analyze_performance_optimizations(content, file_path)
        )

        # Code quality improvements based on analysis result
        if analysis_result:
            operations.extend(
                await self._generate_quality_improvements(analysis_result, content)
            )

        # Filter and prioritize operations
        filtered_operations = self._filter_operations(operations)
        execution_order = self._determine_execution_order(filtered_operations)

        # Calculate overall metrics
        total_time = self._estimate_total_time(filtered_operations)
        risk_assessment = self._assess_overall_risk(filtered_operations)
        success_probability = self._calculate_success_probability(filtered_operations)

        logger.info(f"🎯 Found {len(filtered_operations)} refactoring opportunities")

        return RefactoringPlan(
            file_path=file_path,
            operations=filtered_operations,
            execution_order=execution_order,
            total_estimated_time=total_time,
            risk_assessment=risk_assessment,
            success_probability=success_probability,
        )

    async def _analyze_python_refactoring(
        self, content: str, file_path: str
    ) -> List[RefactoringOperation]:
        """Analyze Python-specific refactoring opportunities"""

        operations = []

        try:
            tree = ast.parse(content)

            # Find long methods that can be extracted
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = self._get_function_lines(node, content)

                    if (
                        len(func_lines)
                        > self.refactoring_patterns[RefactoringType.EXTRACT_METHOD][
                            "min_lines"
                        ]
                    ):
                        # Analyze if function can be split
                        sub_methods = self._identify_extractable_methods(node, content)

                        for method_info in sub_methods:
                            operations.append(
                                RefactoringOperation(
                                    type=RefactoringType.EXTRACT_METHOD,
                                    title=f"Extract method: {method_info['suggested_name']}",
                                    description=f"Extract {method_info['line_count']} lines from {node.name}()",
                                    file_path=file_path,
                                    line_start=method_info["start_line"],
                                    line_end=method_info["end_line"],
                                    original_code=method_info["original_code"],
                                    refactored_code=method_info["refactored_code"],
                                    benefits=[
                                        "Improved function readability",
                                        "Better code organization",
                                        "Easier unit testing",
                                        "Reduced function complexity",
                                    ],
                                    risks=[
                                        "May introduce additional function call overhead",
                                        "Requires careful variable scope management",
                                    ],
                                    complexity=RefactoringComplexity.SIMPLE,
                                    confidence=method_info["confidence"],
                                    estimated_time="15-30 minutes",
                                    prerequisites=[],
                                    side_effects=["Function signature changes"],
                                )
                            )

            # Find complex conditionals that can be simplified
            for node in ast.walk(tree):
                if isinstance(node, ast.If):
                    if self._is_complex_condition(node):
                        simplified = self._simplify_condition(node, content)

                        if simplified:
                            operations.append(
                                RefactoringOperation(
                                    type=RefactoringType.SIMPLIFY_CONDITION,
                                    title="Simplify complex condition",
                                    description="Replace complex boolean expression with clear variable",
                                    file_path=file_path,
                                    line_start=node.lineno,
                                    line_end=node.end_lineno or node.lineno,
                                    original_code=simplified["original"],
                                    refactored_code=simplified["refactored"],
                                    benefits=[
                                        "Improved code readability",
                                        "Easier debugging",
                                        "Self-documenting code",
                                    ],
                                    risks=["Minimal risk"],
                                    complexity=RefactoringComplexity.TRIVIAL,
                                    confidence=0.9,
                                    estimated_time="5 minutes",
                                    prerequisites=[],
                                    side_effects=[],
                                )
                            )

            # Find variables that need better names
            operations.extend(
                await self._suggest_variable_renames(tree, content, file_path)
            )

            # Find opportunities to add type hints
            operations.extend(await self._suggest_type_hints(tree, content, file_path))

        except SyntaxError as e:
            logger.warning(f"Could not parse Python file {file_path}: {e}")

        return operations

    async def _analyze_generic_refactoring(
        self, content: str, file_path: str
    ) -> List[RefactoringOperation]:
        """Analyze language-agnostic refactoring opportunities"""

        operations = []
        lines = content.split("\n")

        # Find code duplication
        duplicates = self._find_code_duplication(lines)

        for duplicate in duplicates:
            operations.append(
                RefactoringOperation(
                    type=RefactoringType.REMOVE_DUPLICATION,
                    title=f"Extract duplicated code ({duplicate['occurrences']} occurrences)",
                    description=f"Create reusable function for {duplicate['line_count']} duplicated lines",
                    file_path=file_path,
                    line_start=duplicate["first_occurrence"],
                    line_end=duplicate["first_occurrence"] + duplicate["line_count"],
                    original_code=duplicate["code"],
                    refactored_code=duplicate["suggested_refactoring"],
                    benefits=[
                        "Eliminates code duplication",
                        "Easier maintenance",
                        "Consistent behavior",
                        "Reduced file size",
                    ],
                    risks=[
                        "May affect performance if function is called frequently",
                        "Requires careful parameter design",
                    ],
                    complexity=RefactoringComplexity.MODERATE,
                    confidence=duplicate["confidence"],
                    estimated_time="20-45 minutes",
                    prerequisites=["Ensure all occurrences have same behavior"],
                    side_effects=["Creates new function dependency"],
                )
            )

        # Find long parameter lists
        long_param_functions = self._find_long_parameter_lists(content)

        for func_info in long_param_functions:
            operations.append(
                RefactoringOperation(
                    type=RefactoringType.EXTRACT_VARIABLE,
                    title=f"Simplify parameter list: {func_info['name']}",
                    description=f"Replace {func_info['param_count']} parameters with configuration object",
                    file_path=file_path,
                    line_start=func_info["line_number"],
                    line_end=func_info["line_number"],
                    original_code=func_info["original_signature"],
                    refactored_code=func_info["suggested_signature"],
                    benefits=[
                        "Simplified function calls",
                        "Better parameter organization",
                        "Easier to extend with new parameters",
                    ],
                    risks=[
                        "Breaking change for existing callers",
                        "May require configuration class creation",
                    ],
                    complexity=RefactoringComplexity.COMPLEX,
                    confidence=0.7,
                    estimated_time="1-2 hours",
                    prerequisites=["Analyze all function callers"],
                    side_effects=["API breaking change"],
                )
            )

        return operations

    async def _analyze_performance_optimizations(
        self, content: str, file_path: str
    ) -> List[RefactoringOperation]:
        """Analyze performance optimization opportunities"""

        operations = []

        # Check for performance anti-patterns
        for pattern_name, pattern_info in self.performance_patterns.items():
            matches = list(re.finditer(pattern_info["pattern"], content, re.MULTILINE))

            for match in matches:
                line_num = content[: match.start()].count("\n") + 1

                # Generate optimized code suggestion
                optimized_code = self._generate_performance_optimization(
                    match.group(0), pattern_name, content, match.start()
                )

                if optimized_code:
                    operations.append(
                        RefactoringOperation(
                            type=RefactoringType.PERFORMANCE_OPTIMIZATION,
                            title=f"Performance optimization: {pattern_name}",
                            description=pattern_info["improvement"],
                            file_path=file_path,
                            line_start=line_num,
                            line_end=line_num,
                            original_code=match.group(0),
                            refactored_code=optimized_code["suggestion"],
                            benefits=[
                                f"Performance improvement: {optimized_code['improvement']}",
                                "More efficient memory usage",
                                "Better algorithmic complexity",
                            ],
                            risks=[
                                "May affect code readability",
                                "Performance gain depends on data size",
                            ],
                            complexity=RefactoringComplexity.SIMPLE,
                            confidence=optimized_code["confidence"],
                            estimated_time="10-20 minutes",
                            prerequisites=["Profile to confirm performance benefit"],
                            side_effects=["Code style changes"],
                        )
                    )

        return operations

    async def _generate_quality_improvements(
        self, analysis_result: CodeAnalysisResult, content: str
    ) -> List[RefactoringOperation]:
        """Generate refactoring operations based on quality analysis"""

        operations = []

        for issue in analysis_result.issues:
            if issue.severity in [IssueSeverity.HIGH, IssueSeverity.CRITICAL]:
                # Generate specific refactoring for the issue
                refactoring = self._create_refactoring_for_issue(issue, content)

                if refactoring:
                    operations.append(refactoring)

        return operations

    def _identify_extractable_methods(
        self, func_node: ast.FunctionDef, content: str
    ) -> List[Dict[str, Any]]:
        """Identify parts of a function that can be extracted into separate methods"""

        extractable_methods = []

        # Simple heuristic: look for logical blocks (try/except, if statements, loops)
        for i, node in enumerate(func_node.body):
            if isinstance(node, (ast.Try, ast.If, ast.For, ast.While)):
                # Check if this block is substantial enough to extract
                block_lines = self._get_node_lines(node, content)

                if len(block_lines) >= 3:  # Minimum extractable size
                    method_name = self._suggest_method_name(node, content)

                    extractable_methods.append(
                        {
                            "suggested_name": method_name,
                            "start_line": node.lineno,
                            "end_line": node.end_lineno or node.lineno,
                            "line_count": len(block_lines),
                            "original_code": "\n".join(block_lines),
                            "refactored_code": self._generate_extracted_method(
                                method_name, block_lines
                            ),
                            "confidence": 0.8,
                        }
                    )

        return extractable_methods

    def _is_complex_condition(self, if_node: ast.If) -> bool:
        """Check if an if condition is complex enough to simplify"""

        # Count boolean operators and comparisons
        complexity = 0

        for node in ast.walk(if_node.test):
            if isinstance(node, ast.BoolOp):
                complexity += len(node.values)
            elif isinstance(node, ast.Compare):
                complexity += len(node.comparators)

        return complexity > 3  # Threshold for complexity

    def _simplify_condition(
        self, if_node: ast.If, content: str
    ) -> Optional[Dict[str, str]]:
        """Generate simplified version of complex condition"""

        lines = content.split("\n")
        original_line = (
            lines[if_node.lineno - 1] if if_node.lineno <= len(lines) else ""
        )

        # Extract the condition
        condition_match = re.search(r"if\s+(.+):", original_line)
        if not condition_match:
            return None

        condition = condition_match.group(1)

        # Generate descriptive variable name
        var_name = self._generate_condition_variable_name(condition)

        # Create refactored version
        refactored = f"{var_name} = {condition}\n    if {var_name}:"

        return {"original": original_line.strip(), "refactored": refactored}

    async def _suggest_variable_renames(
        self, tree: ast.AST, content: str, file_path: str
    ) -> List[RefactoringOperation]:
        """Suggest better variable names"""

        operations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                var_name = node.id

                # Check if variable name can be improved
                if var_name in self.naming_improvements:
                    suggested_name = self.naming_improvements[var_name]

                    operations.append(
                        RefactoringOperation(
                            type=RefactoringType.RENAME_VARIABLE,
                            title=f"Rename variable: {var_name} → {suggested_name}",
                            description=f"Improve variable name clarity",
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.lineno,
                            original_code=var_name,
                            refactored_code=suggested_name,
                            benefits=[
                                "Improved code readability",
                                "Self-documenting code",
                                "Better maintenance",
                            ],
                            risks=["Requires updating all references"],
                            complexity=RefactoringComplexity.SIMPLE,
                            confidence=0.9,
                            estimated_time="5-10 minutes",
                            prerequisites=["Check for name conflicts"],
                            side_effects=["Multiple file changes possible"],
                        )
                    )

        return operations

    async def _suggest_type_hints(
        self, tree: ast.AST, content: str, file_path: str
    ) -> List[RefactoringOperation]:
        """Suggest adding type hints to functions"""

        operations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function lacks type hints
                has_return_annotation = node.returns is not None
                has_arg_annotations = any(arg.annotation for arg in node.args.args)

                if not has_return_annotation or not has_arg_annotations:
                    # Generate type hint suggestions
                    suggested_hints = self._infer_type_hints(node, content)

                    if suggested_hints:
                        operations.append(
                            RefactoringOperation(
                                type=RefactoringType.ADD_TYPE_HINTS,
                                title=f"Add type hints: {node.name}()",
                                description="Add type annotations for better code clarity",
                                file_path=file_path,
                                line_start=node.lineno,
                                line_end=node.lineno,
                                original_code=self._get_function_signature(
                                    node, content
                                ),
                                refactored_code=suggested_hints["signature"],
                                benefits=[
                                    "Better IDE support",
                                    "Improved code documentation",
                                    "Early error detection",
                                    "Better refactoring support",
                                ],
                                risks=["May require import additions"],
                                complexity=RefactoringComplexity.SIMPLE,
                                confidence=suggested_hints["confidence"],
                                estimated_time="10-15 minutes",
                                prerequisites=["Verify type accuracy"],
                                side_effects=["May require typing imports"],
                            )
                        )

        return operations

    def _find_code_duplication(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Find duplicated code blocks"""

        duplicates = []
        min_duplicate_lines = 3

        # Simple duplication detection
        for i in range(len(lines) - min_duplicate_lines):
            for j in range(i + min_duplicate_lines, len(lines) - min_duplicate_lines):
                # Check for sequence of identical lines
                match_count = 0

                while (
                    i + match_count < len(lines)
                    and j + match_count < len(lines)
                    and lines[i + match_count].strip() == lines[j + match_count].strip()
                    and lines[i + match_count].strip() != ""
                ):
                    match_count += 1

                if match_count >= min_duplicate_lines:
                    duplicate_code = "\n".join(lines[i : i + match_count])

                    duplicates.append(
                        {
                            "first_occurrence": i + 1,
                            "line_count": match_count,
                            "occurrences": 2,  # Simplified - could count more
                            "code": duplicate_code,
                            "suggested_refactoring": self._generate_duplicate_refactoring(
                                duplicate_code
                            ),
                            "confidence": 0.8,
                        }
                    )

        return duplicates[:5]  # Limit to top 5 duplicates

    def _find_long_parameter_lists(self, content: str) -> List[Dict[str, Any]]:
        """Find functions with too many parameters"""

        long_param_functions = []

        # Find function definitions with many parameters
        pattern = r"def\s+(\w+)\s*\(([^)]+)\):"
        matches = re.finditer(pattern, content, re.MULTILINE)

        for match in matches:
            func_name = match.group(1)
            params = match.group(2)

            # Count parameters (simple count by commas)
            param_count = len([p for p in params.split(",") if p.strip()])

            if param_count > 5:  # Threshold for too many parameters
                line_num = content[: match.start()].count("\n") + 1

                long_param_functions.append(
                    {
                        "name": func_name,
                        "param_count": param_count,
                        "line_number": line_num,
                        "original_signature": match.group(0),
                        "suggested_signature": f"def {func_name}(config: {func_name.title()}Config):",
                    }
                )

        return long_param_functions

    def _generate_performance_optimization(
        self, original_code: str, pattern_name: str, full_content: str, position: int
    ) -> Optional[Dict[str, Any]]:
        """Generate performance-optimized code"""

        optimizations = {
            "list_comprehension": {
                "suggestion": "# Use list comprehension: result = [process(item) for item in items]",
                "improvement": "2-3x faster than append loop",
                "confidence": 0.9,
            },
            "string_join": {
                "suggestion": "# Use join: result = ''.join([str1, str2, str3])",
                "improvement": "O(n) instead of O(n²) for multiple concatenations",
                "confidence": 0.95,
            },
            "set_membership": {
                "suggestion": "# Use set: if item in {val1, val2, val3}:",
                "improvement": "O(1) lookup instead of O(n)",
                "confidence": 0.9,
            },
        }

        return optimizations.get(pattern_name)

    def _create_refactoring_for_issue(
        self, issue: CodeIssue, content: str
    ) -> Optional[RefactoringOperation]:
        """Create refactoring operation for a specific code issue"""

        # Map issue types to refactoring operations
        if issue.title == "Long Function":
            return RefactoringOperation(
                type=RefactoringType.EXTRACT_METHOD,
                title=f"Fix: {issue.title}",
                description=issue.description,
                file_path=issue.file_path,
                line_start=issue.line_number or 1,
                line_end=issue.line_number or 1,
                original_code="# Long function detected",
                refactored_code="# Split into smaller methods",
                benefits=["Addresses quality issue", "Improves maintainability"],
                risks=["Requires careful method extraction"],
                complexity=RefactoringComplexity.MODERATE,
                confidence=0.7,
                estimated_time="30-60 minutes",
                prerequisites=["Analyze function dependencies"],
                side_effects=["Function signature changes"],
            )

        return None

    def _filter_operations(
        self, operations: List[RefactoringOperation]
    ) -> List[RefactoringOperation]:
        """Filter and prioritize refactoring operations"""

        # Remove low-confidence operations
        filtered = [op for op in operations if op.confidence > 0.6]

        # Sort by impact and confidence
        filtered.sort(key=lambda op: (op.confidence, len(op.benefits)), reverse=True)

        # Limit to reasonable number
        return filtered[:20]

    def _determine_execution_order(
        self, operations: List[RefactoringOperation]
    ) -> List[int]:
        """Determine optimal execution order for operations"""

        # Simple ordering: trivial first, complex last
        complexity_order = {
            RefactoringComplexity.TRIVIAL: 0,
            RefactoringComplexity.SIMPLE: 1,
            RefactoringComplexity.MODERATE: 2,
            RefactoringComplexity.COMPLEX: 3,
            RefactoringComplexity.EXPERIMENTAL: 4,
        }

        indexed_ops = [(i, op) for i, op in enumerate(operations)]
        indexed_ops.sort(key=lambda x: complexity_order[x[1].complexity])

        return [i for i, _ in indexed_ops]

    def _estimate_total_time(self, operations: List[RefactoringOperation]) -> str:
        """Estimate total time for all operations"""

        if not operations:
            return "0 minutes"

        # Simple estimation based on operation count
        total_minutes = len(operations) * 20  # Average 20 minutes per operation

        if total_minutes < 60:
            return f"{total_minutes} minutes"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours}h {minutes}m"

    def _assess_overall_risk(self, operations: List[RefactoringOperation]) -> str:
        """Assess overall risk level"""

        if not operations:
            return "No risk"

        complex_count = len(
            [
                op
                for op in operations
                if op.complexity
                in [RefactoringComplexity.COMPLEX, RefactoringComplexity.EXPERIMENTAL]
            ]
        )

        if complex_count > len(operations) * 0.5:
            return "High risk - many complex operations"
        elif complex_count > 0:
            return "Medium risk - some complex operations"
        else:
            return "Low risk - mostly simple operations"

    def _calculate_success_probability(
        self, operations: List[RefactoringOperation]
    ) -> float:
        """Calculate probability of successful refactoring"""

        if not operations:
            return 1.0

        avg_confidence = sum(op.confidence for op in operations) / len(operations)

        # Adjust for complexity
        complex_penalty = (
            len(
                [
                    op
                    for op in operations
                    if op.complexity == RefactoringComplexity.COMPLEX
                ]
            )
            * 0.1
        )

        return max(0.0, min(1.0, avg_confidence - complex_penalty))

    # Helper methods
    def _detect_language(self, file_path: str) -> str:
        """Detect language from file path"""
        from pathlib import Path

        ext = Path(file_path).suffix.lower()
        return "python" if ext == ".py" else "unknown"

    def _get_function_lines(
        self, func_node: ast.FunctionDef, content: str
    ) -> List[str]:
        """Get lines of code for a function"""
        lines = content.split("\n")
        start = func_node.lineno - 1
        end = func_node.end_lineno or len(lines)
        return lines[start:end]

    def _get_node_lines(self, node: ast.AST, content: str) -> List[str]:
        """Get lines of code for an AST node"""
        lines = content.split("\n")
        start = node.lineno - 1
        end = node.end_lineno or node.lineno
        return lines[start:end]

    def _suggest_method_name(self, node: ast.AST, content: str) -> str:
        """Suggest a name for extracted method"""
        if isinstance(node, ast.Try):
            return "handle_exception"
        elif isinstance(node, ast.If):
            return "check_condition"
        elif isinstance(node, ast.For):
            return "process_items"
        elif isinstance(node, ast.While):
            return "process_loop"
        else:
            return "extracted_method"

    def _generate_extracted_method(self, method_name: str, lines: List[str]) -> str:
        """Generate code for extracted method"""
        indented_lines = ["    " + line for line in lines]
        return f"def {method_name}(self):\n" + "\n".join(indented_lines)

    def _generate_condition_variable_name(self, condition: str) -> str:
        """Generate descriptive variable name for condition"""
        # Simple heuristic based on condition content
        if "user" in condition.lower():
            return "is_valid_user"
        elif "file" in condition.lower():
            return "file_exists"
        elif "length" in condition.lower() or "len(" in condition:
            return "has_valid_length"
        else:
            return "condition_met"

    def _infer_type_hints(
        self, func_node: ast.FunctionDef, content: str
    ) -> Optional[Dict[str, Any]]:
        """Infer type hints for function"""
        # Simplified type inference
        return {
            "signature": f"def {func_node.name}(self, data: Any) -> Any:",
            "confidence": 0.6,
        }

    def _get_function_signature(self, func_node: ast.FunctionDef, content: str) -> str:
        """Get current function signature"""
        lines = content.split("\n")
        return (
            lines[func_node.lineno - 1].strip()
            if func_node.lineno <= len(lines)
            else ""
        )

    def _generate_duplicate_refactoring(self, duplicate_code: str) -> str:
        """Generate refactoring suggestion for duplicate code"""
        return f"def extracted_common_logic():\n{duplicate_code}"


# Convenience functions
async def analyze_refactoring_opportunities(
    file_path: str, content: str
) -> RefactoringPlan:
    """Analyze refactoring opportunities for a file"""
    engine = SmartRefactoringEngine()
    return await engine.analyze_refactoring_opportunities(file_path, content)


async def get_quick_refactoring_suggestions(file_path: str, content: str) -> List[str]:
    """Get quick refactoring suggestions"""
    plan = await analyze_refactoring_opportunities(file_path, content)

    suggestions = []
    for op in plan.operations[:5]:  # Top 5 suggestions
        suggestions.append(f"{op.title}: {op.description}")

    return suggestions


# Compatibility wrappers for old API
async def get_quick_suggestions(file_path: str, content: str) -> List[str]:
    """Compatibility wrapper for get_quick_suggestions (old API)"""
    return await get_quick_refactoring_suggestions(file_path, content)
