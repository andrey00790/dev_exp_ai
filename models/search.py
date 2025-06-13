from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class SourceType(str, Enum):
    """Типы источников данных."""
    CONFLUENCE = "confluence"
    JIRA = "jira"
    GITLAB = "gitlab"
    UPLOADED_FILE = "uploaded_file"
    MANUAL = "manual"
    SLACK = "slack"                     # Планируется
    NOTION = "notion"                   # Планируется
    GITHUB = "github"                   # Планируется


class FileType(str, Enum):
    """Типы загружаемых файлов."""
    PDF = "pdf"
    TXT = "txt"
    EPUB = "epub"
    DOC = "doc"
    DOCX = "docx"
    MD = "md"


class DataSource(BaseModel):
    """Источник данных."""
    id: Optional[str] = None
    name: str                           # Название источника
    source_type: SourceType
    is_enabled: bool = True
    config: Dict[str, Any] = {}         # Конфигурация (URL, токены и т.д.)
    last_sync: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DocumentMetadata(BaseModel):
    """Метаданные документа для поиска."""
    id: Optional[str] = None
    title: str
    url: Optional[str] = None           # Оригинальная ссылка
    source_id: str                      # ID источника
    source_type: SourceType
    author: Optional[str] = None
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    tags: List[str] = []
    file_type: Optional[FileType] = None
    file_size: Optional[int] = None     # В байтах
    content_hash: Optional[str] = None  # Для отслеживания изменений
    is_deleted: bool = False
    extra_metadata: Dict[str, Any] = {} # Специфичная для источника информация
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SemanticSearchQuery(BaseModel):
    """Запрос семантического поиска."""
    query: str = Field(..., min_length=1, max_length=1000)
    sources: List[str] = []             # ID источников для поиска (пустой = все)
    source_types: List[SourceType] = [] # Типы источников для поиска
    limit: int = Field(default=10, ge=1, le=100)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)  # Минимальная релевантность
    filters: Dict[str, Any] = {}        # Дополнительные фильтры
    include_content: bool = False       # Включать ли полный контент


class SemanticSearchResult(BaseModel):
    """Результат семантического поиска."""
    document_id: str
    title: str
    snippet: str                        # Релевантный фрагмент
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    source_type: SourceType
    source_name: str
    url: Optional[str] = None
    author: Optional[str] = None
    created_date: Optional[datetime] = None
    full_content: Optional[str] = None  # Если include_content=True
    highlights: List[str] = []          # Подсвеченные фрагменты


class SemanticSearchResponse(BaseModel):
    """Ответ на семантический поиск."""
    results: List[SemanticSearchResult]
    total_found: int
    query: str
    search_time_ms: int
    sources_searched: List[str]


class UploadFileRequest(BaseModel):
    """Запрос на загрузку файла."""
    title: Optional[str] = None         # Если не указан, берется из имени файла
    description: Optional[str] = None
    tags: List[str] = []
    author: Optional[str] = None


class UploadFileResponse(BaseModel):
    """Ответ на загрузку файла."""
    document_id: str
    title: str
    file_type: FileType
    file_size: int
    processing_status: str              # "uploaded", "processing", "completed", "failed"
    message: str


class SyncStatus(str, Enum):
    """Статусы синхронизации."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SyncResult(BaseModel):
    """Результат синхронизации источника."""
    source_id: str
    source_name: str
    status: SyncStatus
    documents_processed: int = 0
    documents_added: int = 0
    documents_updated: int = 0
    documents_deleted: int = 0
    errors: List[str] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class SyncTriggerRequest(BaseModel):
    """Запрос на запуск синхронизации."""
    source_ids: List[str] = []          # Пустой = все источники
    force_full_sync: bool = False       # Полная пересинхронизация


class SyncStatusResponse(BaseModel):
    """Статус синхронизации."""
    results: List[SyncResult]
    overall_status: SyncStatus
    message: str


class ConfigureSourceRequest(BaseModel):
    """Запрос на настройку источника."""
    name: str
    source_type: SourceType
    is_enabled: bool = True
    config: Dict[str, Any]              # URL, токены, параметры


class ConfigureSourceResponse(BaseModel):
    """Ответ на настройку источника."""
    source: DataSource
    message: str
    connection_test_passed: bool = False 