"""
Search models for the AI Assistant
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Supported data source types"""
    CONFLUENCE = "confluence"
    JIRA = "jira"
    GITLAB = "gitlab"
    GITHUB = "github"
    LOCAL_FILES = "local_files"
    SHAREPOINT = "sharepoint"
    NOTION = "notion"
    SLACK = "slack"
    TEAMS = "teams"
    CUSTOM = "custom"


class FileType(str, Enum):
    """Supported file types for upload"""
    PDF = "pdf"
    TXT = "txt"
    DOC = "doc"
    DOCX = "docx"
    EPUB = "epub"
    MD = "md"
    MARKDOWN = "markdown"
    HTML = "html"
    RTF = "rtf"
    ODT = "odt"


class DataSource(BaseModel):
    """Data source configuration"""
    id: str
    name: str
    source_type: SourceType
    config: Dict[str, Any]
    enabled: bool = True
    last_sync: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    documents_count: int = 0
    status: str = "active"
    sync_schedule: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConfigureSourceRequest(BaseModel):
    """Request to configure a data source"""
    name: str = Field(..., description="Source name")
    source_type: SourceType = Field(..., description="Source type")
    config: Dict[str, Any] = Field(..., description="Source configuration")
    enabled: bool = Field(True, description="Enable source")
    sync_schedule: Optional[str] = Field(None, description="Sync schedule (cron format)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ConfigureSourceResponse(BaseModel):
    """Response for source configuration"""
    source: DataSource
    message: str = "Source configured successfully"
    connection_test_passed: bool = True


class SemanticSearchQuery(BaseModel):
    """Semantic search query"""
    query: str = Field(..., description="Search query", min_length=1, max_length=1000)
    sources: Optional[List[str]] = Field(None, description="Source filters")
    limit: int = Field(10, description="Results limit", ge=1, le=100)
    offset: int = Field(0, description="Results offset", ge=0)
    filters: Dict[str, Any] = Field(default_factory=dict, description="Additional filters")
    include_content: bool = Field(True, description="Include document content")
    include_metadata: bool = Field(True, description="Include document metadata")
    minimum_score: Optional[float] = Field(None, description="Minimum relevance score")
    search_type: str = Field("semantic", description="Search type: semantic, keyword, hybrid")


class SearchResultItem(BaseModel):
    """Individual search result"""
    id: str
    title: str
    content: str
    source_type: str
    source_name: str
    url: Optional[str] = None
    score: float
    highlights: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SemanticSearchResponse(BaseModel):
    """Semantic search response"""
    results: List[SearchResultItem]
    total_found: int
    query: str
    search_time_ms: int
    sources_searched: List[str]
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    pagination: Dict[str, Any] = Field(default_factory=dict)


class UploadFileRequest(BaseModel):
    """Request to upload a document"""
    title: str = Field(..., description="Document title")
    description: Optional[str] = Field(None, description="Document description")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    author: Optional[str] = Field(None, description="Document author")
    category: Optional[str] = Field(None, description="Document category")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class UploadFileResponse(BaseModel):
    """Response for file upload"""
    id: str
    title: str
    filename: str
    file_type: str
    size_bytes: int
    status: str = "uploaded"
    message: str = "File uploaded successfully"
    processing_time_ms: int
    indexed: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SyncTriggerRequest(BaseModel):
    """Request to trigger sync"""
    source_ids: Optional[List[str]] = Field(None, description="Specific sources to sync")
    full_sync: bool = Field(False, description="Perform full sync")
    force: bool = Field(False, description="Force sync even if recently synced")
    async_mode: bool = Field(True, description="Run sync asynchronously")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Sync filters")


class SyncResult(BaseModel):
    """Individual sync result"""
    source_id: str
    source_name: str
    status: str  # "completed", "failed", "in_progress"
    documents_processed: int
    documents_added: int
    documents_updated: int
    documents_deleted: int
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SyncStatusResponse(BaseModel):
    """Sync status response"""
    results: List[SyncResult]
    overall_status: str  # "completed", "failed", "in_progress"
    message: str = "Sync completed"
    total_documents_processed: int = 0
    start_time: datetime
    end_time: Optional[datetime] = None


__all__ = [
    "SourceType",
    "FileType",
    "DataSource",
    "ConfigureSourceRequest",
    "ConfigureSourceResponse",
    "SemanticSearchQuery",
    "SearchResultItem",
    "SemanticSearchResponse",
    "UploadFileRequest",
    "UploadFileResponse",
    "SyncTriggerRequest",
    "SyncResult",
    "SyncStatusResponse"
] 