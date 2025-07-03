from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class BaseResponse(BaseModel):
    """Base response model."""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class DocumentType(str, Enum):
    """Document types supported by the system."""
    SRS = "srs"
    NFR = "nfr" 
    USE_CASE = "use_case"
    RFC = "rfc"
    ADR = "adr"
    DIAGRAM = "diagram"


class Document(BaseModel):
    """Document model."""
    id: Optional[str] = None
    title: str
    content: str
    doc_type: DocumentType
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SearchQuery(BaseModel):
    """Search query model."""
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=100)
    filters: Dict[str, Any] = {}


class SearchResult(BaseModel):
    """Search result model."""
    document: Document
    score: float = Field(..., ge=0.0, le=1.0)
    highlights: List[str] = []


class SearchResponse(BaseResponse):
    """Search response model."""
    results: List[SearchResult] = []
    total: int = 0
    query: str


class FeedbackType(str, Enum):
    """Feedback types."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class Feedback(BaseModel):
    """Feedback model."""
    id: Optional[str] = None
    query: str
    result_id: str
    feedback_type: FeedbackType
    comment: Optional[str] = None
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None


class GenerateRequest(BaseModel):
    """Document generation request."""
    doc_type: DocumentType
    title: str
    requirements: str
    context: Optional[str] = None
    template: Optional[str] = None


class GenerateResponse(BaseResponse):
    """Document generation response."""
    document: Optional[Document] = None 