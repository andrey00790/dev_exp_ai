"""
Documents domain - handles document management and data sources.
"""

from .data_sources import router as data_sources
from .documentation import router as documentation
from .documents import router as documents

__all__ = ["data_sources", "documentation", "documents"]
