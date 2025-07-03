"""
Mermaid Diagram Generator - Creates architectural diagrams for RFC documentation.
Inspired by deepwiki-open diagram generation patterns.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from domain.rfc_generation.rfc_analyzer import (ArchitectureAnalysis,
                                                ComponentAnalysis)

logger = logging.getLogger(__name__)


class DiagramType(Enum):
    """Supported diagram types"""

    ARCHITECTURE = "architecture"
    DEPENDENCY_GRAPH = "dependency_graph"
    DEPLOYMENT = "deployment"
    SEQUENCE = "sequence"
    FLOWCHART = "flowchart"
    COMPONENT = "component"


@dataclass
class DiagramConfig:
    """Configuration for diagram generation"""

    title: str
    direction: str = "TD"  # TD, LR, RL, BT
    theme: str = "default"
    show_icons: bool = True
    max_nodes: int = 20
    group_by_type: bool = True


class MermaidDiagramGenerator:
    """
    Generates Mermaid diagrams for architecture visualization.

    Supports:
    - Architecture overview diagrams
    - Component dependency graphs
    - Deployment diagrams
    - Sequence diagrams for API flows
    """

    def __init__(self):
        # Service type styling
        self.service_styles = {
            "api": {"color": "#FF6B6B", "icon": "🔌"},
            "frontend": {"color": "#4ECDC4", "icon": "🎨"},
            "service": {"color": "#45B7D1", "icon": "⚙️"},
            "database": {"color": "#96CEB4", "icon": "🗄️"},
            "infrastructure": {"color": "#FCEA2B", "icon": "🏗️"},
            "message_queue": {"color": "#FF8A65", "icon": "📬"},
        }

        # Technology icons
        self.tech_icons = {
            "fastapi": "🚀",
            "react": "⚛️",
            "docker": "🐳",
            "postgresql": "🐘",
            "redis": "🔴",
            "nginx": "🌐",
            "kubernetes": "☸️",
        }

    def generate_architecture_diagram(
        self, analysis: ArchitectureAnalysis, config: Optional[DiagramConfig] = None
    ) -> str:
        """
        Generate high-level architecture diagram.

        Args:
            analysis: Architecture analysis result
            config: Diagram configuration

        Returns:
            Mermaid diagram code
        """
        if not config:
            config = DiagramConfig(
                title="System Architecture", direction="TD", show_icons=True
            )

        # Start with graph definition
        lines = ["graph TD", f"    %% {config.title}", ""]

        # Add component nodes
        for component in analysis.components:
            node_id = self._sanitize_id(component.name)

            # Create node with styling
            icon = self._get_service_icon(component.service_type)
            tech_stack = " & ".join(component.technology_stack[:2])  # Show top 2 techs

            if config.show_icons:
                label = f"{icon} {component.name}<br/><small>{tech_stack}</small>"
            else:
                label = f"{component.name}<br/><small>{tech_stack}</small>"

            lines.append(f'    {node_id}["{label}"]')

        lines.append("")

        # Add dependencies
        for component_name, dependencies in analysis.dependencies_graph.items():
            source_id = self._sanitize_id(component_name)

            for dep in dependencies:
                target_id = self._sanitize_id(dep)
                lines.append(f"    {source_id} --> {target_id}")

        lines.append("")

        # Add styling
        lines.extend(self._generate_component_styles(analysis.components))

        return "\n".join(lines)

    def generate_dependency_graph(
        self, analysis: ArchitectureAnalysis, config: Optional[DiagramConfig] = None
    ) -> str:
        """
        Generate detailed dependency graph.

        Args:
            analysis: Architecture analysis result
            config: Diagram configuration

        Returns:
            Mermaid flowchart showing dependencies
        """
        if not config:
            config = DiagramConfig(title="Component Dependencies", direction="LR")

        lines = [f"flowchart {config.direction}", f"    %% {config.title}", ""]

        # Group components by type if requested
        if config.group_by_type:
            grouped_components = self._group_components_by_type(analysis.components)

            for service_type, components in grouped_components.items():
                if not components:
                    continue

                # Create subgraph for each service type
                subgraph_id = f"sg_{service_type}"
                icon = self._get_service_icon(service_type)

                lines.extend(
                    [
                        f"    subgraph {subgraph_id} [{icon} {service_type.title()} Layer]",
                        f"        direction {config.direction}",
                    ]
                )

                # Add components to subgraph
                for component in components:
                    node_id = self._sanitize_id(component.name)
                    label = self._create_component_label(component, config.show_icons)
                    lines.append(f"        {node_id}[{label}]")

                lines.append("    end")
                lines.append("")
        else:
            # Simple flat structure
            for component in analysis.components:
                node_id = self._sanitize_id(component.name)
                label = self._create_component_label(component, config.show_icons)
                lines.append(f"    {node_id}[{label}]")

            lines.append("")

        # Add dependency arrows
        for component_name, dependencies in analysis.dependencies_graph.items():
            source_id = self._sanitize_id(component_name)

            for dep in dependencies:
                target_id = self._sanitize_id(dep)
                # Use different arrow styles for different relationship types
                lines.append(f"    {source_id} --> {target_id}")

        lines.append("")

        # Add styling
        lines.extend(self._generate_dependency_styles(analysis.components))

        return "\n".join(lines)

    def generate_deployment_diagram(
        self, analysis: ArchitectureAnalysis, config: Optional[DiagramConfig] = None
    ) -> str:
        """
        Generate deployment architecture diagram.

        Args:
            analysis: Architecture analysis result
            config: Diagram configuration

        Returns:
            Mermaid diagram showing deployment structure
        """
        if not config:
            config = DiagramConfig(title="Deployment Architecture", direction="TD")

        lines = [f"graph {config.direction}", f"    %% {config.title}", ""]

        # Internet/Load Balancer layer
        lines.extend(
            [
                "    Internet([🌐 Internet])",
                "    LB[🔀 Load Balancer]",
                "    Internet --> LB",
                "",
            ]
        )

        # API Gateway if detected
        has_api_gateway = any(
            "gateway" in comp.name.lower() for comp in analysis.components
        )
        if (
            has_api_gateway
            or len([c for c in analysis.components if c.service_type == "api"]) > 1
        ):
            lines.extend(["    Gateway[🚪 API Gateway]", "    LB --> Gateway", ""])
            gateway_target = "Gateway"
        else:
            gateway_target = "LB"

        # Application services
        app_components = [
            c
            for c in analysis.components
            if c.service_type in ["api", "service", "frontend"]
        ]

        if app_components:
            lines.append("    subgraph AppLayer [🏗️ Application Layer]")

            for component in app_components:
                node_id = self._sanitize_id(component.name)
                icon = self._get_service_icon(component.service_type)

                # Add replicas indicator for scalable services
                if component.service_type in ["api", "service"]:
                    label = f"{icon} {component.name}<br/><small>Replicas: 2-5</small>"
                else:
                    label = f"{icon} {component.name}"

                lines.append(f'        {node_id}["{label}"]')

                # Connect from gateway/LB
                if component.service_type == "api":
                    lines.append(f"    {gateway_target} --> {node_id}")

            lines.extend(["    end", ""])

        # Data layer
        data_components = [
            c for c in analysis.components if c.service_type == "database"
        ]
        storage_techs = [
            tech
            for tech in analysis.technology_inventory.keys()
            if tech in ["postgresql", "redis", "mongodb"]
        ]

        if data_components or storage_techs:
            lines.append("    subgraph DataLayer [🗄️ Data Layer]")

            # Add detected databases
            for tech in storage_techs:
                tech_id = self._sanitize_id(tech)
                icon = self.tech_icons.get(tech, "🗄️")
                lines.append(f'        {tech_id}["{icon} {tech.title()}"]')

            # Add database components
            for component in data_components:
                node_id = self._sanitize_id(component.name)
                icon = self._get_service_icon(component.service_type)
                lines.append(f'        {node_id}["{icon} {component.name}"]')

            lines.extend(["    end", ""])

            # Connect app services to databases
            for app_comp in app_components:
                if app_comp.service_type in ["api", "service"]:
                    app_id = self._sanitize_id(app_comp.name)
                    for tech in storage_techs:
                        tech_id = self._sanitize_id(tech)
                        lines.append(f"    {app_id} --> {tech_id}")

        # Infrastructure layer
        infra_components = [
            c for c in analysis.components if c.service_type == "infrastructure"
        ]
        has_containerization = "docker" in analysis.technology_inventory

        if infra_components or has_containerization:
            lines.append("    subgraph InfraLayer [🏗️ Infrastructure Layer]")

            if has_containerization:
                lines.append("        Docker[🐳 Docker Containers]")

            if "kubernetes" in analysis.technology_inventory:
                lines.append("        K8s[☸️ Kubernetes Cluster]")
                lines.append("        Docker --> K8s")

            for component in infra_components:
                node_id = self._sanitize_id(component.name)
                icon = self._get_service_icon(component.service_type)
                lines.append(f'        {node_id}["{icon} {component.name}"]')

            lines.extend(["    end", ""])

        # Add styling
        lines.extend(
            [
                "",
                "    %% Styling",
                "    classDef appService fill:#e1f5fe",
                "    classDef dataService fill:#f3e5f5",
                "    classDef infraService fill:#fff3e0",
                "    classDef external fill:#ffebee",
            ]
        )

        return "\n".join(lines)

    def generate_api_sequence_diagram(
        self,
        analysis: ArchitectureAnalysis,
        api_flow: str = "User Authentication",
        config: Optional[DiagramConfig] = None,
    ) -> str:
        """
        Generate sequence diagram for API flow.

        Args:
            analysis: Architecture analysis result
            api_flow: Name of the API flow to diagram
            config: Diagram configuration

        Returns:
            Mermaid sequence diagram
        """
        if not config:
            config = DiagramConfig(title=f"API Flow: {api_flow}")

        lines = ["sequenceDiagram", f"    title {config.title}", ""]

        # Define participants
        participants = ["Client"]

        # Add API components as participants
        api_components = [c for c in analysis.components if c.service_type == "api"]
        service_components = [
            c for c in analysis.components if c.service_type == "service"
        ]

        for component in api_components + service_components:
            participants.append(component.name)

        # Add database if present
        if any(c.service_type == "database" for c in analysis.components):
            participants.append("Database")

        # Define participants
        for participant in participants:
            lines.append(
                f"    participant {self._sanitize_id(participant)} as {participant}"
            )

        lines.append("")

        # Generate sample flow based on detected components
        if api_components:
            api_comp = api_components[0]
            api_id = self._sanitize_id(api_comp.name)

            lines.extend(
                [
                    f"    Client->>+{api_id}: POST /auth/login",
                    f"    {api_id}->>+{api_id}: Validate request",
                ]
            )

            if service_components:
                service_comp = service_components[0]
                service_id = self._sanitize_id(service_comp.name)
                lines.extend(
                    [
                        f"    {api_id}->>+{service_id}: Authenticate user",
                        f"    {service_id}->>+Database: Query user credentials",
                        f"    Database-->>-{service_id}: User data",
                        f"    {service_id}-->>-{api_id}: Authentication result",
                    ]
                )

            lines.extend(
                [
                    f"    {api_id}->>+{api_id}: Generate JWT token",
                    f"    {api_id}-->>-Client: 200 OK + JWT token",
                ]
            )

        return "\n".join(lines)

    def generate_component_diagram(
        self, component, config: Optional[DiagramConfig] = None
    ) -> str:
        """
        Generate detailed component diagram.

        Args:
            component: Component to diagram (ServiceComponent)
            config: Diagram configuration

        Returns:
            Mermaid component diagram
        """
        if not config:
            config = DiagramConfig(title=f"Component: {component.name}")

        lines = ["graph TD", f"    %% {config.title}", ""]

        # Main component
        comp_id = self._sanitize_id(component.name)
        icon = self._get_service_icon(component.service_type)

        lines.append(f'    {comp_id}["{icon} {component.name}"]')
        lines.append("")

        # Add interfaces
        if component.interfaces:
            lines.append("    subgraph Interfaces [📡 API Endpoints]")
            for i, interface in enumerate(component.interfaces[:5]):  # Limit to 5
                interface_id = f"int_{i}"
                lines.append(f'        {interface_id}["{interface}"]')
                lines.append(f"        {comp_id} --> {interface_id}")
            lines.append("    end")
            lines.append("")

        # Add technology stack
        if component.technology_stack:
            lines.append("    subgraph TechStack [🛠️ Technology Stack]")
            for i, tech in enumerate(component.technology_stack):
                tech_id = f"tech_{i}"
                icon = self.tech_icons.get(tech, "🔧")
                lines.append(f'        {tech_id}["{icon} {tech}"]')
            lines.append("    end")
            lines.append("")

        # Add files structure
        if component.files:
            lines.append("    subgraph Files [📁 Key Files]")
            # Handle both old string format and new CodeFile format
            key_files = []
            for f in component.files:
                if hasattr(f, 'file_path'):  # CodeFile object
                    file_path = f.file_path
                else:  # String (legacy)
                    file_path = f
                
                if not any(skip in file_path for skip in ["test", "__pycache__", ".pyc"]):
                    key_files.append(file_path)
            
            # Limit to 5 files
            key_files = key_files[:5]

            for i, file_path in enumerate(key_files):
                file_id = f"file_{i}"
                file_name = file_path.split("/")[-1]  # Get filename only
                lines.append(f'        {file_id}["{file_name}"]')
            lines.append("    end")
            lines.append("")

        return "\n".join(lines)

    def _sanitize_id(self, name: str) -> str:
        """Sanitize name for use as Mermaid node ID"""
        # Replace special characters with underscores
        import re

        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        return sanitized.strip("_")

    def _get_service_icon(self, service_type: str) -> str:
        """Get icon for service type"""
        return self.service_styles.get(service_type, {}).get("icon", "📦")

    def _create_component_label(
        self, component, show_icons: bool = True
    ) -> str:
        """Create label for component node"""
        icon = self._get_service_icon(component.service_type) if show_icons else ""

        # Add technology indicators
        tech_indicators = []
        for tech in component.technology_stack[:2]:  # Show max 2 technologies
            tech_icon = self.tech_icons.get(tech, "")
            if tech_icon:
                tech_indicators.append(tech_icon)

        tech_str = "".join(tech_indicators)

        if show_icons:
            return f'"{icon} {component.name}<br/><small>{tech_str}</small>"'
        else:
            return f'"{component.name}<br/><small>{" ".join(component.technology_stack[:2])}</small>"'

    def _group_components_by_type(
        self, components
    ) -> Dict[str, List]:
        """Group components by service type"""
        grouped = {}
        for component in components:
            service_type = component.service_type
            if service_type not in grouped:
                grouped[service_type] = []
            grouped[service_type].append(component)

        return grouped

    def _generate_component_styles(
        self, components
    ) -> List[str]:
        """Generate styling for components"""
        styles = ["    %% Component Styling"]

        for component in components:
            node_id = self._sanitize_id(component.name)
            color = self.service_styles.get(component.service_type, {}).get(
                "color", "#DDDDDD"
            )
            styles.append(f"    style {node_id} fill:{color}")

        return styles

    def _generate_dependency_styles(
        self, components
    ) -> List[str]:
        """Generate styling for dependency graph"""
        styles = ["    %% Dependency Styling"]

        # Define style classes
        styles.extend(
            [
                "    classDef api fill:#FF6B6B,stroke:#333,stroke-width:2px",
                "    classDef frontend fill:#4ECDC4,stroke:#333,stroke-width:2px",
                "    classDef service fill:#45B7D1,stroke:#333,stroke-width:2px",
                "    classDef database fill:#96CEB4,stroke:#333,stroke-width:2px",
                "    classDef infrastructure fill:#FCEA2B,stroke:#333,stroke-width:2px",
            ]
        )

        # Apply classes to nodes
        for component in components:
            node_id = self._sanitize_id(component.name)
            styles.append(f"    class {node_id} {component.service_type}")

        return styles


# Convenience functions
def create_architecture_diagram(
    analysis: ArchitectureAnalysis, title: str = "System Architecture"
) -> str:
    """Create architecture overview diagram"""
    generator = MermaidDiagramGenerator()
    config = DiagramConfig(title=title, direction="TD", show_icons=True)
    return generator.generate_architecture_diagram(analysis, config)


def create_dependency_diagram(
    analysis: ArchitectureAnalysis, title: str = "Component Dependencies"
) -> str:
    """Create component dependency diagram"""
    generator = MermaidDiagramGenerator()
    config = DiagramConfig(title=title, direction="LR", group_by_type=True)
    return generator.generate_dependency_graph(analysis, config)


def create_deployment_diagram(
    analysis: ArchitectureAnalysis, title: str = "Deployment Architecture"
) -> str:
    """Create deployment architecture diagram"""
    generator = MermaidDiagramGenerator()
    config = DiagramConfig(title=title, direction="TD")
    return generator.generate_deployment_diagram(analysis, config)


def create_api_flow_diagram(
    analysis: ArchitectureAnalysis, flow_name: str = "API Authentication Flow"
) -> str:
    """Create API sequence diagram"""
    generator = MermaidDiagramGenerator()
    config = DiagramConfig(title=flow_name)
    return generator.generate_api_sequence_diagram(analysis, flow_name, config)


def generate_all_diagrams(analysis: ArchitectureAnalysis) -> Dict[str, str]:
    """Generate all standard diagrams for an architecture"""

    diagrams = {
        "architecture": create_architecture_diagram(analysis),
        "dependencies": create_dependency_diagram(analysis),
        "deployment": create_deployment_diagram(analysis),
        "api_flow": create_api_flow_diagram(analysis),
    }

    # Add component-specific diagrams for key components
    key_components = [
        c for c in analysis.components if c.service_type in ["api", "service"]
    ][:3]

    generator = MermaidDiagramGenerator()
    for component in key_components:
        comp_key = f"component_{component.name.lower()}"
        diagrams[comp_key] = generator.generate_component_diagram(component)

    return diagrams
