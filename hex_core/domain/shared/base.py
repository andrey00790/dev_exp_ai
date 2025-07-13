"""
Base models for the AI Assistant
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel
import uuid


class DocumentType(Enum):
    """Document types"""
    PAGE = "page"
    ISSUE = "issue"
    FILE = "file"
    COMMENT = "comment"
    ATTACHMENT = "attachment"
    WIKI = "wiki"
    ARTICLE = "article"
    SPECIFICATION = "specification"
    TUTORIAL = "tutorial"
    API_DOC = "api_doc"
    CODE = "code"
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    DISCUSSION = "discussion"
    MEETING_NOTES = "meeting_notes"
    DECISION = "decision"
    TASK = "task"
    BUG = "bug"
    FEATURE = "feature"
    EPIC = "epic"
    STORY = "story"
    TRAINING_DATA = "training_data"
    KNOWLEDGE_BASE = "knowledge_base"
    FAQ = "faq"
    GUIDE = "guide"
    MANUAL = "manual"
    POLICY = "policy"
    PROCEDURE = "procedure"
    TEMPLATE = "template"
    EXAMPLE = "example"
    REFERENCE = "reference"
    CHANGELOG = "changelog"
    ROADMAP = "roadmap"
    ARCHITECTURE = "architecture"
    DIAGRAM = "diagram"
    SCHEMA = "schema"
    CONFIG = "config"
    SCRIPT = "script"
    REPORT = "report"
    ANALYSIS = "analysis"
    RESEARCH = "research"
    PROPOSAL = "proposal"
    PRESENTATION = "presentation"
    DOCUMENT = "document"
    OTHER = "other"


class Priority(Enum):
    """Priority levels"""
    LOWEST = "lowest"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    HIGHEST = "highest"
    CRITICAL = "critical"


class Status(Enum):
    """Document status"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


@dataclass
class Document:
    """Base document model"""
    id: str
    title: str
    content: str
    document_type: DocumentType
    source: str
    source_id: str
    source_url: Optional[str] = None
    author: Optional[str] = None
    author_email: Optional[str] = None
    assignee: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_created_at: Optional[datetime] = None
    source_updated_at: Optional[datetime] = None
    quality_score: float = 0.0
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "document_type": self.document_type.value if isinstance(self.document_type, DocumentType) else self.document_type,
            "source": self.source,
            "source_id": self.source_id,
            "source_url": self.source_url,
            "author": self.author,
            "author_email": self.author_email,
            "assignee": self.assignee,
            "priority": self.priority.value if isinstance(self.priority, Priority) else self.priority,
            "status": self.status.value if isinstance(self.status, Status) else self.status,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "source_created_at": self.source_created_at.isoformat() if self.source_created_at else None,
            "source_updated_at": self.source_updated_at.isoformat() if self.source_updated_at else None,
            "quality_score": self.quality_score,
            "embedding": self.embedding
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Create from dictionary"""
        # Convert string enums back to enum instances
        document_type = data.get("document_type")
        if isinstance(document_type, str):
            document_type = DocumentType(document_type)
        
        priority = data.get("priority")
        if isinstance(priority, str):
            priority = Priority(priority)
        
        status = data.get("status")
        if isinstance(status, str):
            status = Status(status)
        
        # Convert date strings back to datetime
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        
        source_created_at = data.get("source_created_at")
        if isinstance(source_created_at, str):
            source_created_at = datetime.fromisoformat(source_created_at.replace('Z', '+00:00'))
        
        source_updated_at = data.get("source_updated_at")
        if isinstance(source_updated_at, str):
            source_updated_at = datetime.fromisoformat(source_updated_at.replace('Z', '+00:00'))
        
        return cls(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            document_type=document_type,
            source=data["source"],
            source_id=data["source_id"],
            source_url=data.get("source_url"),
            author=data.get("author"),
            author_email=data.get("author_email"),
            assignee=data.get("assignee"),
            priority=priority,
            status=status,
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            created_at=created_at,
            updated_at=updated_at,
            source_created_at=source_created_at,
            source_updated_at=source_updated_at,
            quality_score=data.get("quality_score", 0.0),
            embedding=data.get("embedding")
        )


@dataclass
class SearchQuery:
    """Search query model"""
    query: str
    filters: Dict[str, Any] = field(default_factory=dict)
    limit: int = 10
    offset: int = 0
    sort_by: Optional[str] = None
    sort_order: str = "desc"
    include_content: bool = True
    include_metadata: bool = True
    minimum_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "query": self.query,
            "filters": self.filters,
            "limit": self.limit,
            "offset": self.offset,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
            "include_content": self.include_content,
            "include_metadata": self.include_metadata,
            "minimum_score": self.minimum_score
        }


@dataclass
class SearchResult:
    """Search result model"""
    document: Document
    score: float
    highlights: List[str] = field(default_factory=list)
    explanation: Optional[str] = None
    rank: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "document": self.document.to_dict(),
            "score": self.score,
            "highlights": self.highlights,
            "explanation": self.explanation,
            "rank": self.rank
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchResult':
        """Create from dictionary"""
        return cls(
            document=Document.from_dict(data["document"]),
            score=data["score"],
            highlights=data.get("highlights", []),
            explanation=data.get("explanation"),
            rank=data.get("rank")
        )


@dataclass
class SearchResponse:
    """Search response model"""
    query: SearchQuery
    results: List[SearchResult]
    total_count: int
    took_ms: int
    has_more: bool = False
    facets: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "query": self.query.to_dict(),
            "results": [result.to_dict() for result in self.results],
            "total_count": self.total_count,
            "took_ms": self.took_ms,
            "has_more": self.has_more,
            "facets": self.facets
        }


# Pydantic models for API
class DocumentRequest(BaseModel):
    """Document request model"""
    title: str
    content: str
    document_type: str
    source: str
    source_id: str
    source_url: Optional[str] = None
    author: Optional[str] = None
    author_email: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class DocumentResponse(BaseModel):
    """Document response model"""
    id: str
    title: str
    content: str
    document_type: str
    source: str
    source_id: str
    source_url: Optional[str] = None
    author: Optional[str] = None
    author_email: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    created_at: str
    updated_at: str
    quality_score: float = 0.0


class SearchRequest(BaseModel):
    """Search request model"""
    query: str
    filters: Dict[str, Any] = {}
    limit: int = 10
    offset: int = 0
    sort_by: Optional[str] = None
    sort_order: str = "desc"
    include_content: bool = True
    include_metadata: bool = True
    minimum_score: Optional[float] = None


class SearchResultResponse(BaseModel):
    """Search result response model"""
    document: DocumentResponse
    score: float
    highlights: List[str] = []
    explanation: Optional[str] = None
    rank: Optional[int] = None


class SearchResponseModel(BaseModel):
    """Search response model"""
    query: SearchRequest
    results: List[SearchResultResponse]
    total_count: int
    took_ms: int
    has_more: bool = False
    facets: Dict[str, Any] = {}


class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: str = "OK"
    data: Optional[Any] = None
    error: Optional[str] = None


__all__ = [
    "Document",
    "DocumentType",
    "Priority",
    "Status",
    "SearchQuery",
    "SearchResult",
    "SearchResponse",
    "DocumentRequest",
    "DocumentResponse",
    "SearchRequest",
    "SearchResultResponse",
    "SearchResponseModel",
    "BaseResponse"
] 