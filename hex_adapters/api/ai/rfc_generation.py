"""
RFC Generation API - Endpoints for generating RFC documents with architecture analysis.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.exceptions import APIException
from domain.rfc_generation.rfc_generator_service import (
    RFCGeneratorService, RFCRequest, RFCResult, generate_api_rfc,
    generate_architecture_rfc, generate_design_rfc)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rfc", tags=["RFC Generation"])


# Request/Response Models
class RFCGenerationRequest(BaseModel):
    """RFC generation request model"""

    title: str = Field(..., description="RFC title")
    description: str = Field(..., description="RFC description/problem statement")
    project_path: Optional[str] = Field(
        None, description="Path to project for analysis"
    )
    rfc_type: str = Field(
        "architecture", description="Type of RFC (architecture, design, process)"
    )
    include_diagrams: bool = Field(True, description="Include Mermaid diagrams")
    include_analysis: bool = Field(True, description="Include codebase analysis")
    author: str = Field("AI Assistant", description="RFC author")
    stakeholders: Optional[List[str]] = Field(None, description="List of stakeholders")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Microservices Architecture Migration",
                "description": "Migrate monolithic application to microservices architecture for better scalability",
                "project_path": "/Users/project/my-app",
                "rfc_type": "architecture",
                "include_diagrams": True,
                "include_analysis": True,
                "author": "John Doe",
                "stakeholders": ["Engineering Team", "Product Team"],
            }
        }


class ComponentInfo(BaseModel):
    """Component information"""

    name: str
    service_type: str
    files_count: int
    technology_stack: List[str]
    interfaces: List[str]


class ArchitectureAnalysisResponse(BaseModel):
    """Architecture analysis response"""

    components: List[ComponentInfo]
    dependencies_graph: Dict[str, List[str]]
    technology_inventory: Dict[str, int]
    metrics: Dict[str, Any]
    improvement_suggestions: List[str]


class RFCGenerationResponse(BaseModel):
    """RFC generation response model"""

    success: bool
    rfc_id: str
    title: str
    content: str
    diagrams: Dict[str, str] = Field(default_factory=dict)
    analysis: Optional[ArchitectureAnalysisResponse] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "rfc_id": "AUTO-abc123",
                "title": "Microservices Architecture Migration",
                "content": "# RFC-AUTO-abc123: Microservices Architecture Migration\n\n...",
                "diagrams": {
                    "architecture": "graph TD\n    API[API Service]\n    DB[Database]",
                    "deployment": "graph TD\n    LB[Load Balancer]\n    API[API Service]",
                },
                "metadata": {
                    "generated_at": "2024-01-15T10:30:00Z",
                    "components_analyzed": 5,
                    "diagram_count": 2,
                },
            }
        }


class QuickRFCRequest(BaseModel):
    """Quick RFC generation request"""

    title: str = Field(..., description="RFC title")
    description: str = Field(..., description="RFC description")
    rfc_type: str = Field("design", description="RFC type")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "API Rate Limiting Implementation",
                "description": "Implement rate limiting for public APIs to prevent abuse",
                "rfc_type": "design",
            }
        }


# Service Dependencies
async def get_rfc_service() -> RFCGeneratorService:
    """Get RFC generator service"""
    return RFCGeneratorService()


# API Endpoints
@router.post("/generate", response_model=RFCGenerationResponse)
async def generate_rfc(
    request: RFCGenerationRequest,
    background_tasks: BackgroundTasks,
    rfc_service: RFCGeneratorService = Depends(get_rfc_service),
) -> RFCGenerationResponse:
    """
    Generate comprehensive RFC document with architecture analysis and diagrams.

    This endpoint performs:
    - Codebase analysis (if project path provided)
    - Architecture diagram generation
    - RFC document creation with recommendations

    **Note**: Analysis can take 1-3 minutes for large codebases.
    """
    try:
        logger.info(f"🚀 RFC generation requested: {request.title}")

        # Validate project path if provided
        if request.project_path:
            import os

            if not os.path.exists(request.project_path):
                raise HTTPException(
                    status_code=400,
                    detail=f"Project path does not exist: {request.project_path}",
                )

        # Convert request to service model
        rfc_request = RFCRequest(
            title=request.title,
            description=request.description,
            project_path=request.project_path,
            rfc_type=request.rfc_type,
            include_diagrams=request.include_diagrams,
            author=request.author,
        )

        # Generate RFC
        generated_rfc = await rfc_service.generate_rfc(rfc_request)

        # Convert analysis to response model
        analysis_response = None
        if generated_rfc.analysis:
            analysis = generated_rfc.analysis

            components_info = [
                ComponentInfo(
                    name=comp.name,
                    service_type=comp.service_type,
                    files_count=len(comp.files),
                    technology_stack=comp.technology_stack,
                    interfaces=comp.interfaces,
                )
                for comp in analysis.components
            ]

            analysis_response = ArchitectureAnalysisResponse(
                components=components_info,
                dependencies_graph=analysis.dependencies_graph,
                technology_inventory=analysis.technology_inventory,
                metrics=analysis.metrics,
                improvement_suggestions=analysis.improvement_suggestions,
            )

        response = RFCGenerationResponse(
            success=True,
            rfc_id=generated_rfc.rfc_id,
            title=generated_rfc.title,
            content=generated_rfc.content,
            diagrams=generated_rfc.diagrams,
            analysis=analysis_response,
            metadata=generated_rfc.metadata,
        )

        logger.info(f"✅ RFC generated successfully: {generated_rfc.rfc_id}")
        return response

    except Exception as e:
        logger.error(f"RFC generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RFC generation failed: {str(e)}")


@router.post("/generate/quick", response_model=RFCGenerationResponse)
async def generate_quick_rfc(
    request: QuickRFCRequest,
    rfc_service: RFCGeneratorService = Depends(get_rfc_service),
) -> RFCGenerationResponse:
    """
    Generate quick RFC document without codebase analysis.

    This is a faster endpoint that creates RFC based on description only,
    without performing codebase analysis or diagram generation.
    """
    try:
        logger.info(f"⚡ Quick RFC generation: {request.title}")

        # Generate quick RFC
        generated_rfc = await generate_design_rfc(request.title, request.description)

        response = RFCGenerationResponse(
            success=True,
            rfc_id=generated_rfc.rfc_id,
            title=generated_rfc.title,
            content=generated_rfc.content,
            diagrams=generated_rfc.diagrams,
            analysis=None,
            metadata=generated_rfc.metadata,
        )

        logger.info(f"✅ Quick RFC generated: {generated_rfc.rfc_id}")
        return response

    except Exception as e:
        logger.error(f"Quick RFC generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Quick RFC generation failed: {str(e)}"
        )


@router.post("/generate/architecture", response_model=RFCGenerationResponse)
async def generate_architecture_rfc_endpoint(
    title: str,
    description: str,
    project_path: Optional[str] = None,
    author: str = "AI Assistant",
) -> RFCGenerationResponse:
    """
    Generate architecture-focused RFC with full codebase analysis.

    Convenience endpoint for architecture RFCs with sensible defaults.
    """
    try:
        logger.info(f"🏗️ Architecture RFC generation: {title}")

        # Validate project path if provided
        if project_path:
            import os

            if not os.path.exists(project_path):
                raise HTTPException(
                    status_code=400,
                    detail=f"Project path does not exist: {project_path}",
                )

        # Generate architecture RFC
        generated_rfc = await generate_architecture_rfc(
            title=title, description=description, project_path=project_path
        )

        # Convert analysis
        analysis_response = None
        if generated_rfc.analysis:
            analysis = generated_rfc.analysis

            components_info = [
                ComponentInfo(
                    name=comp.name,
                    service_type=comp.service_type,
                    files_count=len(comp.files),
                    technology_stack=comp.technology_stack,
                    interfaces=comp.interfaces,
                )
                for comp in analysis.components
            ]

            analysis_response = ArchitectureAnalysisResponse(
                components=components_info,
                dependencies_graph=analysis.dependencies_graph,
                technology_inventory=analysis.technology_inventory,
                metrics=analysis.metrics,
                improvement_suggestions=analysis.improvement_suggestions,
            )

        response = RFCGenerationResponse(
            success=True,
            rfc_id=generated_rfc.rfc_id,
            title=generated_rfc.title,
            content=generated_rfc.content,
            diagrams=generated_rfc.diagrams,
            analysis=analysis_response,
            metadata=generated_rfc.metadata,
        )

        logger.info(f"✅ Architecture RFC generated: {generated_rfc.rfc_id}")
        return response

    except Exception as e:
        logger.error(f"Architecture RFC generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Architecture RFC generation failed: {str(e)}"
        )


@router.get("/templates")
async def get_rfc_templates() -> Dict[str, Any]:
    """
    Get available RFC templates and their descriptions.
    """
    return {
        "templates": {
            "architecture": {
                "name": "Architecture RFC",
                "description": "For proposing system architecture changes",
                "includes_analysis": True,
                "includes_diagrams": True,
                "estimated_time": "2-5 minutes",
            },
            "design": {
                "name": "Design RFC",
                "description": "For design proposals and specifications",
                "includes_analysis": False,
                "includes_diagrams": False,
                "estimated_time": "30 seconds",
            },
            "process": {
                "name": "Process RFC",
                "description": "For proposing process changes",
                "includes_analysis": False,
                "includes_diagrams": False,
                "estimated_time": "30 seconds",
            },
            "api": {
                "name": "API RFC",
                "description": "For API design and changes",
                "includes_analysis": True,
                "includes_diagrams": True,
                "estimated_time": "1-2 minutes",
            },
        },
        "supported_diagram_types": [
            "architecture",
            "dependencies",
            "deployment",
            "sequence",
            "component",
        ],
        "analysis_capabilities": [
            "Component identification",
            "Technology stack detection",
            "Dependency mapping",
            "Quality issue detection",
            "Architecture pattern recognition",
            "Improvement recommendations",
        ],
    }


@router.get("/examples")
async def get_rfc_examples() -> Dict[str, Any]:
    """
    Get example RFC requests for different use cases.
    """
    return {
        "examples": {
            "microservices_migration": {
                "title": "Microservices Architecture Migration",
                "description": "Migrate our monolithic e-commerce application to microservices architecture to improve scalability and enable independent team development",
                "rfc_type": "architecture",
                "use_case": "Large application refactoring",
            },
            "api_rate_limiting": {
                "title": "API Rate Limiting Implementation",
                "description": "Implement comprehensive rate limiting across all public APIs to prevent abuse and ensure fair usage",
                "rfc_type": "design",
                "use_case": "Security and performance improvement",
            },
            "ci_cd_pipeline": {
                "title": "Automated CI/CD Pipeline Enhancement",
                "description": "Enhance our CI/CD pipeline with automated testing, security scanning, and blue-green deployments",
                "rfc_type": "process",
                "use_case": "DevOps improvement",
            },
            "graphql_migration": {
                "title": "REST to GraphQL API Migration",
                "description": "Migrate our REST APIs to GraphQL to improve client flexibility and reduce over-fetching",
                "rfc_type": "api",
                "use_case": "API modernization",
            },
        }
    }


# Health check endpoint
@router.get("/health")
async def rfc_service_health() -> Dict[str, Any]:
    """
    Check RFC generation service health.
    """
    try:
        # Quick service instantiation test
        service = RFCGeneratorService()

        return {
            "status": "healthy",
            "service": "RFC Generation",
            "version": "1.0.0",
            "capabilities": [
                "Architecture Analysis",
                "Mermaid Diagram Generation",
                "RFC Document Creation",
                "Quality Assessment",
            ],
            "timestamp": "2024-01-15T10:30:00Z",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-15T10:30:00Z",
        }
