"""
Services Compatibility Layer - Context7 Migration Pattern

Provides backward compatibility for old services.* imports during migration.
All new code should use domain.* imports directly.
"""

# Context7 pattern: Backward compatibility layer
import warnings

def _deprecated_import_warning(old_path: str, new_path: str):
    warnings.warn(
        f"Import from '{old_path}' is deprecated. Use '{new_path}' instead.",
        DeprecationWarning,
        stacklevel=3
    )

# AI Analysis Domain compatibility
try:
    from domain.ai_analysis.ai_code_analyzer import analyze_code_file as _analyze_code_file
    from domain.ai_analysis.smart_refactoring_engine import analyze_refactoring_opportunities as _analyze_refactoring
    
    def analyze_code_file(*args, **kwargs):
        _deprecated_import_warning("services.ai_code_analyzer", "domain.ai_analysis.ai_code_analyzer")
        return _analyze_code_file(*args, **kwargs)
        
    def analyze_refactoring_opportunities(*args, **kwargs):
        _deprecated_import_warning("services.smart_refactoring_engine", "domain.ai_analysis.smart_refactoring_engine")
        return _analyze_refactoring(*args, **kwargs)
        
except ImportError:
    pass

# Stub classes for compatibility - will be properly implemented
class DataSourceService:
    """Compatibility stub"""
    pass

class VectorSearchService:
    """Compatibility stub"""
    pass

class DocumentService:
    """Compatibility stub"""
    pass

class RFCGeneratorService:
    """Compatibility stub"""
    pass

class SecurityEngine:
    """Compatibility stub"""
    pass

class FeedbackService:
    """Compatibility stub"""
    pass

__all__ = [
    "analyze_code_file",
    "analyze_refactoring_opportunities", 
    "DataSourceService",
    "VectorSearchService",
    "DocumentService",
    "RFCGeneratorService",
    "SecurityEngine",
    "FeedbackService"
] 