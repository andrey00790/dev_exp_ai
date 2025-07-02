"""
Search models and data classes
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SearchResult:
    """Результат поиска"""

    # Primary fields
    id: str = ""
    title: str = ""
    content: str = ""
    source_type: str = ""
    source_name: str = ""
    url: str = ""
    score: float = 0.0
    highlights: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    
    # Additional fields for compatibility with tests
    doc_id: Optional[str] = None
    source: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    collection_name: Optional[str] = None
    chunk_index: Optional[int] = None
    
    def __post_init__(self):
        """Post-processing after initialization"""
        # Use doc_id as id if provided
        if self.doc_id and not self.id:
            self.id = self.doc_id
        
        # Use source as source_name if provided
        if self.source and not self.source_name:
            self.source_name = self.source
