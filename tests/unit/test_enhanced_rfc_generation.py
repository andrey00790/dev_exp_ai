"""
Unit tests for Enhanced RFC Generation functionality
Tests RFC Generator Service, Mermaid Diagram Generator, and RFC Analyzer
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from domain.core.generation_service import EnhancedGenerationService
from domain.core.mermaid_diagram_generator import (DiagramConfig,
                                                   MermaidDiagramGenerator)
from domain.rfc_generation.rfc_analyzer import (ArchitectureAnalysis,
                                                ComponentAnalysis,
                                                RFCArchitectureAnalyzer)
from domain.rfc_generation.rfc_generator_service import (GeneratedRFC,
                                                         RFCGeneratorService,
                                                         RFCRequest)


class TestRFCGeneratorService:
    """Test RFC Generator Service"""

    @pytest.fixture
    def rfc_service(self):
        return RFCGeneratorService()

    @pytest.fixture
    def sample_rfc_request(self):
        return RFCRequest(
            title="Test API Rate Limiting",
            description="Implement rate limiting for API endpoints",
            rfc_type="architecture",
            include_diagrams=True,
            include_analysis=False,
            author="Test User",
        )

    @pytest.mark.asyncio
    async def test_generate_simple_rfc(self, rfc_service, sample_rfc_request):
        """Test simple RFC generation without analysis"""

        # Mock the analyzer to avoid file system operations
        with patch.object(rfc_service, "analyzer") as mock_analyzer:
            mock_analyzer.analyze_codebase.return_value = None

            rfc = await rfc_service.generate_rfc(sample_rfc_request)

            assert isinstance(rfc, GeneratedRFC)
            assert rfc.title == sample_rfc_request.title
            assert len(rfc.content) > 0
            assert len(rfc.sections) > 0
            assert rfc.rfc_id is not None

    @pytest.mark.asyncio
    async def test_generate_rfc_with_analysis(self, rfc_service):
        """Test RFC generation with codebase analysis"""

        request = RFCRequest(
            title="Test RFC with Analysis",
            description="Test RFC generation with project analysis",
            project_path="/test/path",
            rfc_type="architecture",
            include_diagrams=True,
            include_analysis=True,
            author="Test User",
        )

        # Mock analysis result
        mock_analysis = ArchitectureAnalysis(
            components=[
                ComponentAnalysis(
                    name="api",
                    service_type="api",
                    files=["app.py"],
                    dependencies=["database"],
                    technology_stack=["fastapi"],
                    interfaces=["/health"],
                )
            ],
            dependencies_graph={"api": ["database"]},
            technology_inventory={"fastapi": 1},
            metrics={"total_files": 1},
            improvement_suggestions=["Add caching"],
        )

        with patch.object(
            rfc_service.analyzer, "analyze_codebase", return_value=mock_analysis
        ):
            rfc = await rfc_service.generate_rfc(request)

            assert rfc.analysis is not None
            assert len(rfc.analysis.components) == 1
            assert "fastapi" in rfc.analysis.technology_inventory

    @pytest.mark.asyncio
    async def test_generate_rfc_with_diagrams(self, rfc_service, sample_rfc_request):
        """Test RFC generation with diagram generation"""

        # Mock diagram generation
        mock_diagrams = {
            "architecture": "graph TD\n    A[API] --> B[Database]",
            "deployment": "graph TD\n    C[Load Balancer] --> D[API Server]",
        }

        with patch.object(
            rfc_service, "_generate_diagrams_for_rfc", return_value=mock_diagrams
        ):
            rfc = await rfc_service.generate_rfc(sample_rfc_request)

            assert len(rfc.diagrams) == 2
            assert "architecture" in rfc.diagrams
            assert "deployment" in rfc.diagrams

    def test_generate_rfc_id(self, rfc_service):
        """Test RFC ID generation"""

        title = "Test RFC Title"
        rfc_id = rfc_service._generate_rfc_id(title)

        assert rfc_id.startswith("RFC-")
        assert len(rfc_id) > 10  # Should have timestamp

    def test_calculate_health_summary(self, rfc_service):
        """Test health score calculation"""

        mock_analysis = ArchitectureAnalysis(
            components=[
                ComponentAnalysis("api", "api", ["app.py"], [], ["fastapi"], []),
                ComponentAnalysis("db", "database", ["db.py"], [], ["postgresql"], []),
            ],
            dependencies_graph={"api": ["db"]},
            technology_inventory={"fastapi": 1, "postgresql": 1},
            metrics={"total_files": 2},
            improvement_suggestions=["Add monitoring"],
        )

        health = rfc_service._calculate_health_summary(mock_analysis)
        assert isinstance(health, str)
        assert len(health) > 0


class TestRFCArchitectureAnalyzer:
    """Test RFC Architecture Analyzer"""

    @pytest.fixture
    def analyzer(self):
        return RFCArchitectureAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_codebase_nonexistent_path(self, analyzer):
        """Test analysis with non-existent path"""

        analysis = await analyzer.analyze_codebase("/nonexistent/path")

        # Should return empty analysis rather than failing
        assert isinstance(analysis, ArchitectureAnalysis)
        assert len(analysis.components) == 0

    def test_determine_service_type(self, analyzer):
        """Test service type determination"""

        # Test API service
        api_type = analyzer._determine_service_type(
            "api_service", ["routes.py", "handlers.py"]
        )
        assert api_type == "api"

        # Test frontend service
        frontend_type = analyzer._determine_service_type(
            "frontend", ["app.tsx", "components.js"]
        )
        assert frontend_type == "frontend"

        # Test generic service
        service_type = analyzer._determine_service_type("user_service", ["user.py"])
        assert service_type == "service"

    def test_detect_technologies(self, analyzer):
        """Test technology detection"""

        # Mock file content
        sample_files = ["app.py"]
        sample_content = "from fastapi import FastAPI\nimport redis"

        with patch("builtins.open", mock_open(read_data=sample_content)):
            with patch("os.path.join", return_value="/test/app.py"):
                technologies = analyzer._detect_technologies(sample_files, "/test")

                assert "fastapi" in technologies
                assert "redis" in technologies


class TestMermaidDiagramGenerator:
    """Test Mermaid Diagram Generator"""

    @pytest.fixture
    def generator(self):
        return MermaidDiagramGenerator()

    @pytest.fixture
    def sample_analysis(self):
        return ArchitectureAnalysis(
            components=[
                ComponentAnalysis(
                    name="api_service",
                    service_type="api",
                    files=["app.py", "routes.py"],
                    dependencies=["database_service"],
                    technology_stack=["fastapi", "python"],
                    interfaces=["/health", "/api/v1/users"],
                ),
                ComponentAnalysis(
                    name="database_service",
                    service_type="database",
                    files=["models.py"],
                    dependencies=[],
                    technology_stack=["postgresql", "sqlalchemy"],
                    interfaces=[],
                ),
            ],
            dependencies_graph={
                "api_service": ["database_service"],
                "database_service": [],
            },
            technology_inventory={"fastapi": 2, "postgresql": 1},
            metrics={"total_files": 3},
            improvement_suggestions=["Add caching layer"],
        )

    def test_generate_architecture_diagram(self, generator, sample_analysis):
        """Test architecture diagram generation"""

        diagram = generator.generate_architecture_diagram(sample_analysis)

        assert "graph TD" in diagram
        assert "api_service" in diagram
        assert "database_service" in diagram
        assert "-->" in diagram  # Should have connections

    def test_generate_dependency_graph(self, generator, sample_analysis):
        """Test dependency graph generation"""

        diagram = generator.generate_dependency_graph(sample_analysis)

        assert "flowchart" in diagram
        assert "api_service" in diagram
        assert "database_service" in diagram

    def test_generate_deployment_diagram(self, generator, sample_analysis):
        """Test deployment diagram generation"""

        diagram = generator.generate_deployment_diagram(sample_analysis)

        assert "graph" in diagram
        assert "Load Balancer" in diagram or "Internet" in diagram
        assert "subgraph" in diagram  # Should have layered structure

    def test_generate_api_sequence_diagram(self, generator, sample_analysis):
        """Test API sequence diagram generation"""

        diagram = generator.generate_api_sequence_diagram(sample_analysis)

        assert "sequenceDiagram" in diagram
        assert "participant" in diagram
        assert "Client" in diagram

    def test_generate_component_diagram(self, generator, sample_analysis):
        """Test component diagram generation"""

        component = sample_analysis.components[0]  # API service
        diagram = generator.generate_component_diagram(component)

        assert "graph TD" in diagram
        assert component.name in diagram
        assert "subgraph" in diagram  # Should have sections

    def test_sanitize_id(self, generator):
        """Test ID sanitization for Mermaid"""

        # Test with special characters
        sanitized = generator._sanitize_id("api-service.v2")
        assert sanitized == "api_service_v2"

        # Test with spaces
        sanitized = generator._sanitize_id("user management service")
        assert sanitized == "user_management_service"

    def test_get_service_icon(self, generator):
        """Test service icon retrieval"""

        api_icon = generator._get_service_icon("api")
        assert api_icon == "🔌"

        database_icon = generator._get_service_icon("database")
        assert database_icon == "🗄️"

        unknown_icon = generator._get_service_icon("unknown")
        assert unknown_icon == "📦"


class TestEnhancedGenerationService:
    """Test Enhanced Generation Service"""

    @pytest.fixture
    def service(self):
        return EnhancedGenerationService()

    @pytest.mark.asyncio
    async def test_generate_rfc(self, service):
        """Test RFC generation through service"""

        # Mock the RFC generator
        with patch.object(service.rfc_generator, "generate_rfc") as mock_generate:
            mock_rfc = GeneratedRFC(
                title="Test RFC",
                rfc_id="RFC-123",
                content="# Test RFC Content",
                sections=[],
                diagrams={"arch": "graph TD\n    A --> B"},
                analysis=None,
                metadata={"author": "Test"},
            )
            mock_generate.return_value = mock_rfc

            result = await service.generate_rfc(
                task_description="Test RFC generation",
                template_type="architecture",
                user_id="test_user",
            )

            assert result["status"] == "completed"
            assert result["task_id"] == "RFC-123"
            assert "rfc_data" in result
            assert "tokens_used" in result

    @pytest.mark.asyncio
    async def test_generate_architecture(self, service):
        """Test architecture generation"""

        with patch.object(service.rfc_generator, "generate_rfc") as mock_generate:
            mock_rfc = GeneratedRFC(
                title="Architecture Design",
                rfc_id="RFC-ARCH-123",
                content="# Architecture Document",
                sections=[],
                diagrams={"deployment": "graph TD\n    LB --> API"},
                analysis=None,
                metadata={"author": "Architect"},
            )
            mock_generate.return_value = mock_rfc

            result = await service.generate_architecture(
                system_name="Test System",
                system_description="Test system description",
                requirements=["High availability", "Scalability"],
                architecture_type="microservices",
                user_id="test_user",
            )

            assert result["status"] == "completed"
            assert "architecture_data" in result
            assert result["architecture_data"]["system_name"] == "Test System"

    @pytest.mark.asyncio
    async def test_generate_documentation(self, service):
        """Test documentation generation"""

        with patch.object(service.rfc_generator, "generate_rfc") as mock_generate:
            mock_rfc = GeneratedRFC(
                title="API Documentation",
                rfc_id="RFC-DOC-123",
                content="# API Documentation",
                sections=[],
                diagrams={},
                analysis=None,
                metadata={"author": "Tech Writer"},
            )
            mock_generate.return_value = mock_rfc

            result = await service.generate_documentation(
                doc_type="api",
                title="API Documentation",
                target_audience="developers",
                user_id="test_user",
            )

            assert result["status"] == "completed"
            assert "documentation_data" in result
            assert result["documentation_data"]["doc_type"] == "api"

    def test_generate_rfc_title(self, service):
        """Test RFC title generation"""

        description = "Implement comprehensive API rate limiting system."
        title = service._generate_rfc_title(description)

        assert title.startswith("RFC:")
        assert "rate limiting" in title.lower()

    def test_estimate_tokens_used(self, service):
        """Test token estimation"""

        content = "This is a test content with some words."
        tokens = service._estimate_tokens_used(content)

        assert tokens > 0
        assert tokens == len(content) // 4


class TestIntegration:
    """Integration tests for RFC generation flow"""

    @pytest.mark.asyncio
    async def test_full_rfc_generation_flow(self):
        """Test complete RFC generation flow"""

        service = EnhancedGenerationService()

        # Mock all external dependencies
        with patch.object(
            service.rfc_generator.analyzer, "analyze_codebase"
        ) as mock_analyze, patch.object(
            service.rfc_generator.diagram_generator, "generate_architecture_diagram"
        ) as mock_diagram:

            # Setup mocks
            mock_analyze.return_value = None  # No analysis
            mock_diagram.return_value = "graph TD\n    A --> B"

            result = await service.generate_rfc(
                task_description="Implement microservices architecture",
                template_type="architecture",
                include_diagrams=True,
                user_id="integration_test",
            )

            # Verify result structure
            assert result["status"] == "completed"
            assert "content" in result
            assert "rfc_data" in result
            assert "metadata" in result
            assert result["tokens_used"] > 0


# Helper function for mocking file operations
def mock_open(read_data=""):
    """Create a mock for open() function"""
    from unittest.mock import mock_open as _mock_open

    return _mock_open(read_data=read_data)


# Pytest configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
