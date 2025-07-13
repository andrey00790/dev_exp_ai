"""
Document models for the AI Assistant
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field
import uuid
import json


class SourceType(Enum):
    """Types of document sources"""
    CONFLUENCE = "confluence"
    JIRA = "jira"
    GITLAB = "gitlab"
    GITHUB = "github"
    LOCAL_FILES = "local_files"
    UPLOADED_FILES = "uploaded_files"


class DocumentStatus(Enum):
    """Document status"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class Document:
    """Document model with metadata"""
    title: str
    content: str
    source_type: SourceType
    source_name: str
    source_id: str
    id: str = None
    source_url: str = None
    space_key: str = None
    project_key: str = None
    document_type: str = None
    category: str = None
    author: str = None
    author_email: str = None
    assignee: str = None
    priority: str = None
    status: str = None
    tags: List[str] = None
    quality_score: float = 0.0
    repository_name: str = None
    file_extension: str = None
    file_size: int = None
    encoding: str = None
    source_created_at: datetime = None
    source_updated_at: datetime = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "source": {
                "type": self.source_type,
                "name": self.source_name,
                "id": self.source_id,
                "url": self.source_url
            },
            "hierarchy": {
                "space_key": self.space_key,
                "project_key": self.project_key
            },
            "categorization": {
                "category": self.category,
                "tags": self.tags,
                "document_type": self.document_type
            },
            "authorship": {
                "author": self.author,
                "author_email": self.author_email,
                "assignee": self.assignee
            },
            "timestamps": {
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
                "source_created_at": self.source_created_at.isoformat() if self.source_created_at else None,
                "source_updated_at": self.source_updated_at.isoformat() if self.source_updated_at else None
            },
            "status": {
                "quality_score": self.quality_score,
                "status": self.status,
                "priority": self.priority
            },
            "technical": {
                "file_extension": self.file_extension,
                "file_size": self.file_size,
                "encoding": self.encoding,
                "repository_name": self.repository_name
            }
        }
    
    @classmethod
    def from_confluence_page(cls, page_data: Dict[str, Any], source_name: str) -> 'Document':
        """Create document from Confluence page data"""
        return cls(
            title=page_data.get("title", ""),
            content=page_data.get("body", {}).get("storage", {}).get("value", ""),
            source_type=SourceType.CONFLUENCE,
            source_name=source_name,
            source_id=page_data.get("id", ""),
            source_url=page_data.get("_links", {}).get("webui", ""),
            space_key=page_data.get("space", {}).get("key", ""),
            document_type="page",
            category="documentation",
            author=page_data.get("history", {}).get("createdBy", {}).get("displayName", ""),
            author_email=page_data.get("history", {}).get("createdBy", {}).get("email", ""),
            tags=[label.get("name", "") for label in page_data.get("metadata", {}).get("labels", {}).get("results", [])],
            source_created_at=datetime.fromisoformat(page_data.get("history", {}).get("createdDate", "").replace('Z', '+00:00')) if page_data.get("history", {}).get("createdDate") else None,
            source_updated_at=datetime.fromisoformat(page_data.get("version", {}).get("when", "").replace('Z', '+00:00')) if page_data.get("version", {}).get("when") else None
        )
    
    @classmethod
    def from_jira_issue(cls, issue_data: Dict[str, Any], source_name: str) -> 'Document':
        """Create document from Jira issue data"""
        fields = issue_data.get("fields", {})
        
        # Build content from description and comments
        content_parts = []
        if fields.get("description"):
            content_parts.append(fields["description"])
        
        comments = fields.get("comment", {}).get("comments", [])
        for comment in comments:
            content_parts.append(f"Comment by {comment.get('author', {}).get('displayName', 'Unknown')}: {comment.get('body', '')}")
        
        return cls(
            title=f"[{issue_data.get('key', '')}] {fields.get('summary', '')}",
            content="\n\n".join(content_parts),
            source_type=SourceType.JIRA,
            source_name=source_name,
            source_id=issue_data.get("key", ""),
            source_url=issue_data.get("self", "").replace("/rest/api/2/issue/", "/browse/"),
            project_key=fields.get("project", {}).get("key", ""),
            document_type="issue",
            category="requirements",
            author=fields.get("creator", {}).get("displayName", ""),
            author_email=fields.get("creator", {}).get("emailAddress", ""),
            assignee=fields.get("assignee", {}).get("displayName", ""),
            priority=fields.get("priority", {}).get("name", ""),
            status=fields.get("status", {}).get("name", ""),
            tags=fields.get("labels", []),
            source_created_at=datetime.fromisoformat(fields.get("created", "").replace('Z', '+00:00')) if fields.get("created") else None,
            source_updated_at=datetime.fromisoformat(fields.get("updated", "").replace('Z', '+00:00')) if fields.get("updated") else None
        )
    
    @classmethod
    def from_gitlab_file(cls, file_data: Dict[str, Any], project_data: Dict[str, Any], source_name: str) -> 'Document':
        """Create document from GitLab file data"""
        file_path = file_data.get("file_path", "")
        file_extension = file_path.split('.')[-1] if '.' in file_path else ""
        
        return cls(
            title=f"{project_data.get('name', '')}: {file_path}",
            content=file_data.get("content", ""),
            source_type=SourceType.GITLAB,
            source_name=source_name,
            source_id=f"{project_data.get('id', '')}:{file_path}",
            source_url=file_data.get("web_url", ""),
            repository_name=project_data.get("name", ""),
            project_key=project_data.get("path_with_namespace", ""),
            document_type="file",
            category="documentation" if file_extension in ["md", "rst", "txt"] else "code",
            file_extension=file_extension,
            file_size=file_data.get("size", 0),
            encoding=file_data.get("encoding", ""),
            source_updated_at=datetime.fromisoformat(file_data.get("last_commit_date", "").replace('Z', '+00:00')) if file_data.get("last_commit_date") else None
        )
    
    @classmethod
    def from_local_file(cls, file_path: str, content: str, source_name: str, file_metadata: Dict[str, Any]) -> 'Document':
        """Create document from local file"""
        file_name = file_path.split('/')[-1]
        file_extension = file_name.split('.')[-1] if '.' in file_name else ""
        
        return cls(
            title=file_name,
            content=content,
            source_type=SourceType.LOCAL_FILES,
            source_name=source_name,
            source_id=file_path,
            source_url=f"file://{file_path}",
            document_type="file",
            category="training_data",
            file_extension=file_extension,
            file_size=file_metadata.get("size", 0),
            encoding=file_metadata.get("encoding", ""),
            source_created_at=datetime.fromtimestamp(file_metadata.get("created_time", 0), tz=timezone.utc) if file_metadata.get("created_time") else None,
            source_updated_at=datetime.fromtimestamp(file_metadata.get("modified_time", 0), tz=timezone.utc) if file_metadata.get("modified_time") else None
        )


@dataclass
class DocumentChunk:
    """Document chunk model"""
    document_id: str
    chunk_index: int
    content: str
    source_type: SourceType
    source_name: str
    start_position: int = 0
    end_position: int = 0
    quality_score: float = 0.0
    id: str = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "source_type": self.source_type,
            "source_name": self.source_name,
            "position": {
                "start": self.start_position,
                "end": self.end_position
            },
            "quality_score": self.quality_score,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class SearchFilter:
    """Search filter builder"""
    
    def __init__(self):
        self.filters = {}
    
    def by_source_type(self, source_types: List[str]) -> 'SearchFilter':
        """Filter by source type"""
        self.filters["source_type"] = source_types
        return self
    
    def by_source_name(self, source_names: List[str]) -> 'SearchFilter':
        """Filter by source name"""
        self.filters["source_name"] = source_names
        return self
    
    def by_project(self, project_keys: List[str]) -> 'SearchFilter':
        """Filter by project"""
        self.filters["project_key"] = project_keys
        return self
    
    def by_document_type(self, document_types: List[str]) -> 'SearchFilter':
        """Filter by document type"""
        self.filters["document_type"] = document_types
        return self
    
    def by_category(self, categories: List[str]) -> 'SearchFilter':
        """Filter by category"""
        self.filters["category"] = categories
        return self
    
    def by_file_extension(self, extensions: List[str]) -> 'SearchFilter':
        """Filter by file extension"""
        self.filters["file_extension"] = extensions
        return self
    
    def by_date_range(self, start_date: datetime, end_date: datetime, field: str = "updated_at") -> 'SearchFilter':
        """Filter by date range"""
        self.filters[f"{field}_range"] = (start_date, end_date)
        return self
    
    def by_quality_score(self, min_score: float) -> 'SearchFilter':
        """Filter by minimum quality score"""
        self.filters["min_quality_score"] = min_score
        return self
    
    def by_tags(self, tags: List[str]) -> 'SearchFilter':
        """Filter by tags"""
        self.filters["tags"] = tags
        return self
    
    def by_priority(self, priorities: List[str]) -> 'SearchFilter':
        """Filter by priority"""
        self.filters["priority"] = priorities
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the filters dictionary"""
        return self.filters.copy()


class CommonFilters:
    """Common predefined filters"""
    
    @classmethod
    def confluence_documentation(cls) -> SearchFilter:
        """Filter for Confluence documentation"""
        return SearchFilter().by_source_type(["confluence"]).by_category(["documentation"])
    
    @classmethod
    def jira_requirements(cls) -> SearchFilter:
        """Filter for Jira requirements"""
        return SearchFilter().by_source_type(["jira"]).by_category(["requirements"])
    
    @classmethod
    def gitlab_code(cls) -> SearchFilter:
        """Filter for GitLab code"""
        return SearchFilter().by_source_type(["gitlab"]).by_category(["code"])
    
    @classmethod
    def recent_updates(cls, days: int = 7) -> SearchFilter:
        """Filter for recent updates"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        return SearchFilter().by_date_range(start_date, end_date, "updated_at")
    
    @classmethod
    def high_quality_content(cls, min_score: float = 0.8) -> SearchFilter:
        """Filter for high quality content"""
        return SearchFilter().by_quality_score(min_score)
    
    @classmethod
    def by_project_context(cls, project_key: str) -> SearchFilter:
        """Filter by project context"""
        return SearchFilter().by_project([project_key])


__all__ = [
    "Document",
    "DocumentChunk", 
    "DocumentStatus",
    "SourceType",
    "SearchFilter",
    "CommonFilters"
]
