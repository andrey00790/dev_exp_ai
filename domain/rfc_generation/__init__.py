"""
RFC Generation Domain - Architecture documentation and RFC creation.
"""

from .rfc_architecture_analyzer import RFCArchitectureAnalyzer as ArchitectureAnalyzer
# RFC generation exports
from .rfc_generator_service import (RFCGeneratorService,
                                    generate_architecture_rfc)

__all__ = ["RFCGeneratorService", "generate_architecture_rfc", "ArchitectureAnalyzer"]
