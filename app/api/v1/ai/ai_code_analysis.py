"""
AI Code Analysis API - Endpoints for intelligent code analysis, refactoring, and optimization.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from starlette.status import (HTTP_200_OK, HTTP_400_BAD_REQUEST,
                              HTTP_404_NOT_FOUND)

from app.core.async_utils import AsyncTimeouts, safe_gather, with_timeout
from app.core.exceptions import APIError, ValidationError
from domain.ai_analysis.ai_code_analyzer import (CodeAnalysisRequest,
                                                 CodeAnalysisResult,
                                                 analyze_code_file,
                                                 analyze_project_structure,
                                                 get_analysis_summary)
from domain.ai_analysis.smart_refactoring_engine import (
    RefactoringPlan, analyze_refactoring_opportunities, get_quick_suggestions)
from domain.code_optimization.ai_performance_optimizer import (
    PerformanceAnalysisRequest, analyze_file_performance,
    get_performance_summary)
from services.performance_optimizer import (ImpactLevel, OptimizationType,
                                            PerformanceIssue,
                                            PerformanceReport,
                                            get_optimization_suggestions)

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response Models
class CodeAnalysisRequest(BaseModel):
    """Request for code analysis"""

    file_path: str = Field(..., description="Path to the file to analyze")
    content: str = Field(..., description="File content to analyze")
    analysis_types: Optional[List[str]] = Field(
        default=None, description="Types of analysis to perform"
    )
    include_refactoring: bool = Field(
        default=True, description="Include refactoring suggestions"
    )
    include_performance: bool = Field(
        default=True, description="Include performance analysis"
    )


class ProjectAnalysisRequest(BaseModel):
    """Request for project-wide analysis"""

    project_path: str = Field(..., description="Path to the project directory")
    file_patterns: Optional[List[str]] = Field(
        default=None, description="File patterns to analyze"
    )
    max_files: int = Field(default=20, description="Maximum number of files to analyze")


class CodeIssueResponse(BaseModel):
    """Code issue response"""

    type: str
    severity: str
    title: str
    description: str
    file_path: str
    line_number: Optional[int]
    suggestion: Optional[str]
    tags: List[str]


class RefactoringResponse(BaseModel):
    """Refactoring suggestion response"""

    type: str
    title: str
    description: str
    file_path: str
    line_number: int
    original_code: str
    refactored_code: str
    benefits: List[str]
    complexity: str
    confidence: float
    estimated_time: str


class PerformanceIssueResponse(BaseModel):
    """Performance issue response"""

    type: str
    title: str
    description: str
    file_path: str
    line_number: int
    current_code: str
    optimized_code: str
    expected_improvement: str
    impact_level: str
    confidence: float
    effort: str


class CodeAnalysisResponse(BaseModel):
    """Complete code analysis response"""

    file_path: str
    language: str
    quality_score: float
    issues: List[CodeIssueResponse]
    refactoring_suggestions: List[RefactoringResponse]
    performance_issues: List[PerformanceIssueResponse]
    ai_insights: Dict[str, Any]
    analysis_summary: Dict[str, Any]


class ProjectHealthResponse(BaseModel):
    """Project health analysis response"""

    project_path: str
    files_analyzed: int
    average_quality_score: float
    health_grade: str
    total_issues: int
    critical_issues: int
    high_priority_issues: int
    total_refactoring_opportunities: int
    total_performance_issues: int
    recommendations: List[str]
    file_summaries: List[Dict[str, Any]]


@router.post(
    "/analyze/file", response_model=CodeAnalysisResponse, status_code=HTTP_200_OK
)
async def analyze_code_file_endpoint(
    request: CodeAnalysisRequest, background_tasks: BackgroundTasks
) -> CodeAnalysisResponse:
    """
    Analyze a single code file with AI insights.

    Provides:
    - Code quality analysis
    - Security vulnerability detection
    - Refactoring suggestions
    - Performance optimization opportunities
    - AI-powered insights and recommendations
    """
    try:
        logger.info(f"🔍 Starting AI code analysis for: {request.file_path}")

        # Parse analysis types
        analysis_types = None
        if request.analysis_types:
            analysis_types = [AnalysisType(t) for t in request.analysis_types]

        # Run parallel analysis
        analysis_tasks = [
            analyze_code_file(request.file_path, request.content, analysis_types)
        ]

        if request.include_refactoring:
            analysis_tasks.append(
                analyze_refactoring_opportunities(request.file_path, request.content)
            )

        if request.include_performance:
            analysis_tasks.append(
                analyze_file_performance(request.file_path, request.content)
            )

        # Execute all analysis tasks concurrently
        results = await safe_gather(
            *analysis_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.ANALYTICS_AGGREGATION,
            max_concurrency=3,
        )

        # Extract results
        code_analysis = results[0] if not isinstance(results[0], Exception) else None
        refactoring_plan = (
            results[1]
            if len(results) > 1 and not isinstance(results[1], Exception)
            else None
        )
        performance_report = (
            results[2]
            if len(results) > 2 and not isinstance(results[2], Exception)
            else None
        )

        if not code_analysis:
            raise APIError(
                message="Code analysis failed",
                details={"error": str(results[0]) if results else "Unknown error"},
                status_code=HTTP_400_BAD_REQUEST,
            )

        # Convert to response format
        response = CodeAnalysisResponse(
            file_path=code_analysis.file_path,
            language=code_analysis.language,
            quality_score=code_analysis.quality_score,
            issues=[
                CodeIssueResponse(
                    type=issue.type.value,
                    severity=issue.severity.value,
                    title=issue.title,
                    description=issue.description,
                    file_path=issue.file_path,
                    line_number=issue.line_number,
                    suggestion=issue.suggestion,
                    tags=issue.tags,
                )
                for issue in code_analysis.issues
            ],
            refactoring_suggestions=[
                RefactoringResponse(
                    type=op.type.value,
                    title=op.title,
                    description=op.description,
                    file_path=op.file_path,
                    line_number=op.line_number,
                    original_code=op.original_code,
                    refactored_code=op.refactored_code,
                    benefits=op.benefits,
                    complexity=op.complexity.value,
                    confidence=op.confidence,
                    estimated_time=op.estimated_time,
                )
                for op in (refactoring_plan.operations if refactoring_plan else [])
            ],
            performance_issues=[
                PerformanceIssueResponse(
                    type=issue.type.value,
                    title=issue.title,
                    description=issue.description,
                    file_path=issue.file_path,
                    line_number=issue.line_number,
                    current_code=issue.current_code,
                    optimized_code=issue.optimized_code,
                    expected_improvement=issue.expected_improvement,
                    impact_level=issue.impact_level.value,
                    confidence=issue.confidence,
                    effort=issue.effort,
                )
                for issue in (performance_report.issues if performance_report else [])
            ],
            ai_insights=code_analysis.ai_insights,
            analysis_summary={
                "quality_grade": _get_quality_grade(code_analysis.quality_score),
                "total_issues": len(code_analysis.issues),
                "refactoring_opportunities": (
                    len(refactoring_plan.operations) if refactoring_plan else 0
                ),
                "performance_optimizations": (
                    len(performance_report.issues) if performance_report else 0
                ),
                "estimated_refactoring_time": (
                    refactoring_plan.total_time if refactoring_plan else "N/A"
                ),
                "estimated_performance_gain": (
                    performance_report.estimated_speedup
                    if performance_report
                    else "N/A"
                ),
            },
        )

        logger.info(f"✅ Code analysis completed for: {request.file_path}")
        return response

    except Exception as e:
        logger.error(f"Code analysis failed: {e}")
        raise APIError(
            message="Failed to analyze code file",
            details={"error": str(e), "file_path": request.file_path},
            status_code=HTTP_400_BAD_REQUEST,
        )


@router.post(
    "/analyze/project", response_model=ProjectHealthResponse, status_code=HTTP_200_OK
)
async def analyze_project_health_endpoint(
    request: ProjectAnalysisRequest, background_tasks: BackgroundTasks
) -> ProjectHealthResponse:
    """
    Analyze project-wide code health and quality.

    Provides comprehensive analysis across multiple files:
    - Overall code quality metrics
    - Security and performance issues
    - Refactoring opportunities
    - Project health recommendations
    """
    try:
        logger.info(f"🏗️ Starting project analysis: {request.project_path}")

        # Get project health summary
        health_summary = await analyze_project_health(request.project_path)

        if "error" in health_summary:
            raise APIError(
                message="Project analysis failed",
                details=health_summary,
                status_code=HTTP_400_BAD_REQUEST,
            )

        # TODO: Add detailed file analysis for project
        # This would iterate through files and collect detailed metrics

        response = ProjectHealthResponse(
            project_path=request.project_path,
            files_analyzed=health_summary["files_analyzed"],
            average_quality_score=health_summary["average_quality_score"],
            health_grade=health_summary["health_grade"],
            total_issues=health_summary["total_issues"],
            critical_issues=health_summary.get("critical_issues", 0),
            high_priority_issues=health_summary.get("high_priority_issues", 0),
            total_refactoring_opportunities=0,  # TODO: Calculate from detailed analysis
            total_performance_issues=0,  # TODO: Calculate from detailed analysis
            recommendations=health_summary["recommendations"],
            file_summaries=[],  # TODO: Add individual file summaries
        )

        logger.info(f"✅ Project analysis completed: {request.project_path}")
        return response

    except Exception as e:
        logger.error(f"Project analysis failed: {e}")
        raise APIError(
            message="Failed to analyze project",
            details={"error": str(e), "project_path": request.project_path},
            status_code=HTTP_400_BAD_REQUEST,
        )


@router.get(
    "/suggestions/refactoring/{file_path:path}",
    response_model=List[str],
    status_code=HTTP_200_OK,
)
async def get_refactoring_suggestions_endpoint(
    file_path: str, content: str = Query(..., description="File content to analyze")
) -> List[str]:
    """
    Get quick refactoring suggestions for a file.

    Returns top 5 refactoring suggestions with brief descriptions.
    """
    try:
        suggestions = await get_quick_suggestions(file_path, content)
        return suggestions

    except Exception as e:
        logger.error(f"Failed to get refactoring suggestions: {e}")
        raise APIError(
            message="Failed to get refactoring suggestions",
            details={"error": str(e), "file_path": file_path},
            status_code=HTTP_400_BAD_REQUEST,
        )


@router.get(
    "/suggestions/performance/{file_path:path}",
    response_model=List[str],
    status_code=HTTP_200_OK,
)
async def get_performance_suggestions_endpoint(
    file_path: str, content: str = Query(..., description="File content to analyze")
) -> List[str]:
    """
    Get quick performance optimization suggestions for a file.

    Returns top 5 performance improvements with expected gains.
    """
    try:
        suggestions = await get_optimization_suggestions(file_path, content)
        return suggestions

    except Exception as e:
        logger.error(f"Failed to get performance suggestions: {e}")
        raise APIError(
            message="Failed to get performance suggestions",
            details={"error": str(e), "file_path": file_path},
            status_code=HTTP_400_BAD_REQUEST,
        )


@router.get("/health", status_code=HTTP_200_OK)
async def health_check():
    """Health check for AI code analysis service."""
    return {
        "status": "healthy",
        "service": "ai_code_analysis",
        "features": [
            "code_quality_analysis",
            "security_vulnerability_detection",
            "refactoring_suggestions",
            "performance_optimization",
            "ai_insights",
        ],
    }


@router.get(
    "/analysis-types", response_model=Dict[str, List[str]], status_code=HTTP_200_OK
)
async def get_analysis_types():
    """Get available analysis types and their descriptions."""
    return {
        "quality_analysis": [
            "function_length_check",
            "magic_number_detection",
            "todo_comment_tracking",
            "code_complexity_analysis",
        ],
        "security_analysis": [
            "sql_injection_detection",
            "hardcoded_secrets_detection",
            "unsafe_eval_detection",
        ],
        "performance_analysis": [
            "nested_loop_detection",
            "string_concatenation_optimization",
            "list_membership_optimization",
            "blocking_io_detection",
            "database_query_optimization",
        ],
        "refactoring_suggestions": [
            "extract_method",
            "simplify_condition",
            "remove_duplication",
            "improve_naming",
            "add_type_hints",
        ],
    }


# Helper functions
def _get_quality_grade(score: float) -> str:
    """Convert quality score to letter grade"""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def _calculate_priority_score(issues: List[CodeIssue]) -> int:
    """Calculate priority score based on issues"""
    score = 0
    for issue in issues:
        if issue.severity == IssueSeverity.CRITICAL:
            score += 10
        elif issue.severity == IssueSeverity.HIGH:
            score += 5
        elif issue.severity == IssueSeverity.MEDIUM:
            score += 2
        else:
            score += 1
    return score
