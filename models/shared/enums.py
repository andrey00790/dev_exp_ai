"""
Unified enums for AI Assistant

This module contains all shared enums used across the application.
Consolidates previously duplicated enum definitions.
"""

from enum import Enum


class SourceType(str, Enum):
    """Unified source types enum
    
    Consolidates all source types from models/search.py, models/document.py, 
    and models/data_source.py into a single definition.
    """
    # Core source types
    BOOTSTRAP = "bootstrap"              # Local training materials
    CONFLUENCE = "confluence"            # Corporate documentation  
    JIRA = "jira"                       # Issues and tickets
    GITLAB = "gitlab"                   # Source code repositories
    GITHUB = "github"                   # GitHub repositories
    
    # File-based sources
    LOCAL_FILES = "local_files"         # Local file uploads
    USER_UPLOAD = "user_upload"         # User uploaded files
    API_IMPORT = "api_import"           # API imported content
    
    # Enterprise sources
    CORPORATE = "corporate"             # Internal corporate materials


class FeedbackType(str, Enum):
    """User feedback types"""
    LIKE = "like"                       # Positive feedback (👍)
    DISLIKE = "dislike"                 # Negative feedback (👎)
    REPORT = "report"                   # Content report/complaint
    POSITIVE = "positive"               # General positive feedback
    NEGATIVE = "negative"               # General negative feedback
    NEUTRAL = "neutral"                 # Neutral feedback


class DocumentStatus(str, Enum):
    """Document processing and lifecycle status"""
    ACTIVE = "active"                   # Document is active and searchable
    ARCHIVED = "archived"               # Document is archived
    DELETED = "deleted"                 # Document is marked for deletion
    PROCESSING = "processing"           # Document is being processed
    ERROR = "error"                     # Error during processing


class ProcessingStatus(str, Enum):
    """Source processing status"""
    PENDING = "pending"                 # Waiting for processing
    PROCESSING = "processing"           # Currently being processed
    COMPLETED = "completed"             # Processing completed successfully
    FAILED = "failed"                   # Processing failed
    CANCELLED = "cancelled"             # Processing was cancelled
    SKIPPED = "skipped"                 # Processing was skipped


class FileType(str, Enum):
    """Supported file types for upload and processing"""
    PDF = "pdf"
    TXT = "txt"
    EPUB = "epub"
    DOC = "doc"
    DOCX = "docx"
    MD = "md"
    HTML = "html"
    JSON = "json"
    CSV = "csv"


class SyncStatus(str, Enum):
    """Synchronization status for data sources"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """AI task generation types"""
    NEW_FEATURE = "new_feature"         # Designing new functionality
    MODIFY_EXISTING = "modify_existing" # Modifying existing features
    ANALYZE_CURRENT = "analyze_current" # Analyzing current functionality


class QuestionType(str, Enum):
    """AI question types"""
    TEXT = "text"                       # Text response required
    CHOICE = "choice"                   # Single choice from options
    MULTIPLE_CHOICE = "multiple_choice" # Multiple choice selection
    BOOLEAN = "boolean"                 # Yes/No question
    NUMBER = "number"                   # Numeric response


class ContentType(str, Enum):
    """Content types for categorization"""
    DOCUMENT = "document"               # Documents (PDF, TXT, MD)
    CODE = "code"                      # Source code
    WEBPAGE = "webpage"                # Web pages
    REPOSITORY = "repository"          # Git repositories
    ISSUE = "issue"                    # Issues/tickets
    COMMENT = "comment"                # Comments
    EDUCATIONAL = "educational"        # Educational materials


class CodeLanguage(str, Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    PHP = "php"
    RUBY = "ruby"
    KOTLIN = "kotlin"
    SWIFT = "swift"
    OTHER = "other"


# Legacy aliases for backward compatibility  
# These will be deprecated in future versions
# Note: Cannot inherit from Enum in Python, so using direct assignment
LegacySourceType = SourceType  # Deprecated: Use SourceType instead
LegacyFeedbackType = FeedbackType  # Deprecated: Use FeedbackType instead 