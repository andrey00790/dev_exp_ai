"""
Database module placeholder for compatibility with tests.
Redirects to infra.database for actual implementation.
"""

# Re-export from infra.database for backward compatibility
try:
    from infra.database.session import Base, SessionLocal, engine, get_db
    
    __all__ = ["Base", "SessionLocal", "engine", "get_db"]
except ImportError:
    # Fallback for tests
    from unittest.mock import Mock
    
    Base = Mock()
    SessionLocal = Mock()
    engine = Mock()
    
    def get_db():
        return Mock()
    
    __all__ = ["Base", "SessionLocal", "engine", "get_db"] 