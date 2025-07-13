"""
Search domain - handles all search functionality.
"""

from .search import router as search
from .search_advanced import router as search_advanced
from .vector_search import router as vector_search

__all__ = ["search", "search_advanced", "vector_search"]
