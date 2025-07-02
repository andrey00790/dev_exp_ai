"""
Domain module compatibility layer
Redirects app.domain imports to the root domain module
"""

# Re-export from root domain module for backward compatibility
try:
    import domain
    import sys
    
    # Make domain module available as app.domain
    sys.modules['app.domain'] = domain
    
    # Re-export commonly used components
    from domain.integration.vector_search_service import VectorSearchService
    
    __all__ = ["VectorSearchService"]
    
except ImportError:
    # Fallback for tests
    from unittest.mock import Mock
    
    VectorSearchService = Mock
    
    __all__ = ["VectorSearchService"] 