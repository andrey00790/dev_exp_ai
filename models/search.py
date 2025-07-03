"""
Search models
Модели для поиска
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from models.shared.enums import SourceType, FileType, SyncStatus
from models.shared.types import JSON, OptionalStr, ListStr, DictAny, ListDict


class DataSource(BaseModel):
    """Источник данных"""
    id: str
    name: str
    type: SourceType
    enabled: bool
    config: DictAny
    last_sync: OptionalStr
    document_count: int


class DocumentMetadata(BaseModel):
    """Метаданные документа для поиска."""
    id: Optional[str] = None
    title: str
    url: OptionalStr = None           # Оригинальная ссылка
    source_id: str                      # ID источника
    source_type: SourceType
    author: OptionalStr = None
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    tags: ListStr = []
    file_type: Optional[FileType] = None
    file_size: Optional[int] = None     # В байтах
    content_hash: OptionalStr = None  # Для отслеживания изменений
    is_deleted: bool = False
    extra_metadata: DictAny = {} # Специфичная для источника информация
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SemanticSearchQuery(BaseModel):
    """Запрос семантического поиска"""
    query: str = Field(..., description="Поисковый запрос")
    limit: int = Field(10, description="Количество результатов", ge=1, le=100)
    sources: Optional[ListStr] = Field(None, description="Источники для поиска")
    filters: Optional[DictAny] = Field(None, description="Фильтры")


class SearchResult(BaseModel):
    """Результат поиска"""
    id: str
    title: str
    content: str
    source_type: str
    source_name: str
    url: OptionalStr
    score: float
    highlights: Optional[ListStr]
    metadata: Optional[DictAny]


class SemanticSearchResponse(BaseModel):
    """Ответ семантического поиска"""
    results: List[SearchResult]
    total_found: int
    query: str
    search_time_ms: int
    sources_searched: ListStr


class UploadFileRequest(BaseModel):
    """Запрос загрузки файла"""
    title: str
    description: OptionalStr = None
    tags: ListStr = []
    author: OptionalStr = None


class UploadFileResponse(BaseModel):
    """Ответ загрузки файла"""
    document_id: str
    title: str
    status: str
    message: str


class SyncTriggerRequest(BaseModel):
    """Запрос синхронизации"""
    sources: Optional[ListStr] = None
    full_sync: bool = False


class SyncResult(BaseModel):
    """Результат синхронизации"""
    source_id: str
    status: str
    documents_processed: int
    errors: ListStr = []


class SyncStatusResponse(BaseModel):
    """Статус синхронизации"""
    results: ListDict = []
    overall_status: str
    message: str


class ConfigureSourceRequest(BaseModel):
    """Запрос настройки источника"""
    source_type: SourceType
    name: str
    config: DictAny
    enabled: bool = True


class ConfigureSourceResponse(BaseModel):
    """Ответ настройки источника"""
    source: DataSource
    message: str
    connection_test_passed: bool


class SyncResult(BaseModel):
    """Результат синхронизации источника."""
    source_id: str
    source_name: str
    status: SyncStatus
    documents_processed: int = 0
    documents_added: int = 0
    documents_updated: int = 0
    documents_deleted: int = 0
    errors: ListStr = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None 