"""
Search models and data classes
"""

from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class SearchResult:
    """Результат поиска"""
    id: str
    title: str
    content: str
    source_type: str
    source_name: str
    url: str
    score: float
    highlights: List[str]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str 