"""
Document model with comprehensive metadata for source tracking
Модель документа с полными метаданными для отслеживания источников
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid

from models.shared.enums import SourceType, DocumentStatus
from models.shared.types import DictAny, OptionalStr, ListStr

Base = declarative_base()


class Document(Base):
    """Основная модель документа с метаданными"""
    __tablename__ = "documents"
    
    # Основные поля
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text)  # Краткое содержание
    
    # Метаданные источника
    source_type = Column(String, nullable=False, index=True)  # confluence, jira, gitlab, etc.
    source_name = Column(String, nullable=False, index=True)  # main_confluence, dev_jira, etc.
    source_id = Column(String, nullable=False, index=True)    # ID в исходной системе
    source_url = Column(String)  # Прямая ссылка на документ
    
    # Иерархия и связи
    parent_id = Column(String)  # ID родительского документа
    project_key = Column(String, index=True)  # Ключ проекта (для Jira/GitLab)
    space_key = Column(String, index=True)    # Ключ пространства (для Confluence)
    repository_name = Column(String, index=True)  # Название репозитория (для GitLab)
    
    # Категоризация
    document_type = Column(String, index=True)  # page, issue, merge_request, file, etc.
    category = Column(String, index=True)       # documentation, code, requirements, etc.
    tags = Column(JSON)  # Список тегов
    labels = Column(JSON)  # Метки из исходной системы
    
    # Авторство и версионность
    author = Column(String, index=True)
    author_email = Column(String)
    created_by = Column(String)
    updated_by = Column(String)
    assignee = Column(String)  # Для задач Jira
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    source_created_at = Column(DateTime, index=True)  # Время создания в исходной системе
    source_updated_at = Column(DateTime, index=True)  # Время обновления в исходной системе
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    
    # Статус и качество
    status = Column(String, default=DocumentStatus.ACTIVE, index=True)
    priority = Column(String, index=True)  # high, medium, low
    quality_score = Column(Float, default=0.0)  # Оценка качества контента
    relevance_score = Column(Float, default=0.0)  # Релевантность для поиска
    
    # Технические метаданные
    language = Column(String, default="en", index=True)
    content_length = Column(Integer)
    word_count = Column(Integer)
    file_extension = Column(String)  # Для файлов
    file_size = Column(Integer)      # Размер файла в байтах
    encoding = Column(String)        # Кодировка файла
    
    # Дополнительные метаданные (JSON)
    document_metadata = Column(JSON)  # Изменено с metadata на document_metadata
    
    # Индексы для поиска
    search_vector = Column(Text)  # Для полнотекстового поиска
    embedding_vector = Column(JSON)  # Векторное представление
    
    def to_dict(self) -> DictAny:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "source": {
                "type": self.source_type,
                "name": self.source_name,
                "id": self.source_id,
                "url": self.source_url
            },
            "hierarchy": {
                "parent_id": self.parent_id,
                "project_key": self.project_key,
                "space_key": self.space_key,
                "repository_name": self.repository_name
            },
            "categorization": {
                "document_type": self.document_type,
                "category": self.category,
                "tags": self.tags or [],
                "labels": self.labels or []
            },
            "authorship": {
                "author": self.author,
                "author_email": self.author_email,
                "created_by": self.created_by,
                "updated_by": self.updated_by,
                "assignee": self.assignee
            },
            "timestamps": {
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
                "source_created_at": self.source_created_at.isoformat() if self.source_created_at else None,
                "source_updated_at": self.source_updated_at.isoformat() if self.source_updated_at else None,
                "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None
            },
            "status": {
                "status": self.status,
                "priority": self.priority,
                "quality_score": self.quality_score,
                "relevance_score": self.relevance_score
            },
            "technical": {
                "language": self.language,
                "content_length": self.content_length,
                "word_count": self.word_count,
                "file_extension": self.file_extension,
                "file_size": self.file_size,
                "encoding": self.encoding
            },
            "metadata": self.document_metadata or {}  # Возвращаем как metadata для обратной совместимости
        }
    
    @classmethod
    def from_confluence_page(cls, page_data: DictAny, source_name: str) -> 'Document':
        """Создание документа из страницы Confluence"""
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
            source_created_at=datetime.fromisoformat(page_data.get("history", {}).get("createdDate", "").replace("Z", "+00:00")) if page_data.get("history", {}).get("createdDate") else None,
            source_updated_at=datetime.fromisoformat(page_data.get("version", {}).get("when", "").replace("Z", "+00:00")) if page_data.get("version", {}).get("when") else None,
            labels=page_data.get("metadata", {}).get("labels", {}).get("results", []),
            document_metadata={
                "confluence_space": page_data.get("space", {}),
                "confluence_version": page_data.get("version", {}),
                "confluence_ancestors": page_data.get("ancestors", [])
            }
        )
    
    @classmethod
    def from_jira_issue(cls, issue_data: DictAny, source_name: str) -> 'Document':
        """Создание документа из задачи Jira"""
        fields = issue_data.get("fields", {})
        
        # Объединение описания и комментариев
        content_parts = []
        if fields.get("description"):
            content_parts.append(f"Description: {fields['description']}")
        
        # Добавление комментариев если есть
        if fields.get("comment", {}).get("comments"):
            comments = [f"Comment by {c.get('author', {}).get('displayName', 'Unknown')}: {c.get('body', '')}" 
                       for c in fields["comment"]["comments"]]
            content_parts.extend(comments)
        
        content = "\n\n".join(content_parts)
        
        return cls(
            title=f"[{issue_data.get('key', '')}] {fields.get('summary', '')}",
            content=content,
            source_type=SourceType.JIRA,
            source_name=source_name,
            source_id=issue_data.get("key", ""),
            source_url=f"{issue_data.get('self', '').split('/rest/')[0]}/browse/{issue_data.get('key', '')}",
            project_key=fields.get("project", {}).get("key", ""),
            document_type="issue",
            category="requirements",
            author=fields.get("creator", {}).get("displayName", ""),
            author_email=fields.get("creator", {}).get("emailAddress", ""),
            assignee=fields.get("assignee", {}).get("displayName", ""),
            priority=fields.get("priority", {}).get("name", ""),
            source_created_at=datetime.fromisoformat(fields.get("created", "").replace("Z", "+00:00")) if fields.get("created") else None,
            source_updated_at=datetime.fromisoformat(fields.get("updated", "").replace("Z", "+00:00")) if fields.get("updated") else None,
            status=fields.get("status", {}).get("name", ""),
            labels=[label for label in fields.get("labels", [])],
            tags=fields.get("labels", []),
            document_metadata={
                "jira_issue_type": fields.get("issuetype", {}),
                "jira_status": fields.get("status", {}),
                "jira_priority": fields.get("priority", {}),
                "jira_components": fields.get("components", []),
                "jira_fix_versions": fields.get("fixVersions", []),
                "jira_affects_versions": fields.get("versions", [])
            }
        )
    
    @classmethod
    def from_gitlab_file(cls, file_data: DictAny, project_data: DictAny, source_name: str) -> 'Document':
        """Создание документа из файла GitLab"""
        return cls(
            title=f"{project_data.get('name', '')}: {file_data.get('file_path', '')}",
            content=file_data.get("content", ""),
            source_type=SourceType.GITLAB,
            source_name=source_name,
            source_id=f"{project_data.get('id', '')}:{file_data.get('file_path', '')}",
            source_url=file_data.get("web_url", ""),
            repository_name=project_data.get("name", ""),
            project_key=project_data.get("path_with_namespace", ""),
            document_type="file",
            category="code" if file_data.get("file_path", "").endswith(('.py', '.js', '.java', '.cpp')) else "documentation",
            file_extension=file_data.get("file_path", "").split(".")[-1] if "." in file_data.get("file_path", "") else "",
            file_size=file_data.get("size", 0),
            encoding=file_data.get("encoding", ""),
            source_updated_at=datetime.fromisoformat(file_data.get("last_commit_date", "").replace("Z", "+00:00")) if file_data.get("last_commit_date") else None,
            document_metadata={
                "gitlab_project": project_data,
                "gitlab_branch": file_data.get("ref", "main"),
                "gitlab_commit_id": file_data.get("commit_id", ""),
                "gitlab_blob_id": file_data.get("blob_id", "")
            }
        )
    
    @classmethod
    def from_local_file(cls, file_path: str, content: str, source_name: str, file_metadata: DictAny) -> 'Document':
        """Создание документа из локального файла"""
        import os
        
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        
        return cls(
            title=filename,
            content=content,
            source_type=SourceType.LOCAL_FILES,
            source_name=source_name,
            source_id=file_path,
            source_url=f"file://{file_path}",
            document_type="file",
            category="training_data",
            file_extension=file_ext.lstrip("."),
            file_size=file_metadata.get("size", 0),
            encoding=file_metadata.get("encoding", "utf-8"),
            source_created_at=datetime.fromtimestamp(file_metadata.get("created_time", 0)) if file_metadata.get("created_time") else None,
            source_updated_at=datetime.fromtimestamp(file_metadata.get("modified_time", 0)) if file_metadata.get("modified_time") else None,
            document_metadata={
                "file_path": file_path,
                "file_stats": file_metadata
            }
        )


class DocumentChunk(Base):
    """Чанки документов для векторного поиска"""
    __tablename__ = "document_chunks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    
    # Наследуем метаданные от родительского документа
    source_type = Column(String, nullable=False, index=True)
    source_name = Column(String, nullable=False, index=True)
    
    # Позиция в документе
    start_position = Column(Integer)
    end_position = Column(Integer)
    
    # Векторное представление
    embedding_vector = Column(JSON)
    
    # Качество чанка
    quality_score = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> DictAny:
        """Преобразование в словарь"""
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
    """Класс для построения фильтров поиска по метаданным"""
    
    def __init__(self):
        self.filters = {}
    
    def by_source_type(self, source_types: ListStr) -> 'SearchFilter':
        """Фильтр по типу источника"""
        self.filters['source_type'] = source_types
        return self
    
    def by_source_name(self, source_names: ListStr) -> 'SearchFilter':
        """Фильтр по названию источника"""
        self.filters['source_name'] = source_names
        return self
    
    def by_project(self, project_keys: ListStr) -> 'SearchFilter':
        """Фильтр по проекту"""
        self.filters['project_key'] = project_keys
        return self
    
    def by_space(self, space_keys: ListStr) -> 'SearchFilter':
        """Фильтр по пространству Confluence"""
        self.filters['space_key'] = space_keys
        return self
    
    def by_repository(self, repo_names: ListStr) -> 'SearchFilter':
        """Фильтр по репозиторию GitLab"""
        self.filters['repository_name'] = repo_names
        return self
    
    def by_document_type(self, doc_types: ListStr) -> 'SearchFilter':
        """Фильтр по типу документа"""
        self.filters['document_type'] = doc_types
        return self
    
    def by_category(self, categories: ListStr) -> 'SearchFilter':
        """Фильтр по категории"""
        self.filters['category'] = categories
        return self
    
    def by_author(self, authors: ListStr) -> 'SearchFilter':
        """Фильтр по автору"""
        self.filters['author'] = authors
        return self
    
    def by_date_range(self, start_date: datetime, end_date: datetime, field: str = 'updated_at') -> 'SearchFilter':
        """Фильтр по диапазону дат"""
        self.filters[f'{field}_range'] = (start_date, end_date)
        return self
    
    def by_tags(self, tags: ListStr) -> 'SearchFilter':
        """Фильтр по тегам"""
        self.filters['tags'] = tags
        return self
    
    def by_priority(self, priorities: ListStr) -> 'SearchFilter':
        """Фильтр по приоритету"""
        self.filters['priority'] = priorities
        return self
    
    def by_status(self, statuses: ListStr) -> 'SearchFilter':
        """Фильтр по статусу"""
        self.filters['status'] = statuses
        return self
    
    def by_language(self, languages: ListStr) -> 'SearchFilter':
        """Фильтр по языку"""
        self.filters['language'] = languages
        return self
    
    def by_file_extension(self, extensions: ListStr) -> 'SearchFilter':
        """Фильтр по расширению файла"""
        self.filters['file_extension'] = extensions
        return self
    
    def by_quality_score(self, min_score: float) -> 'SearchFilter':
        """Фильтр по минимальной оценке качества"""
        self.filters['min_quality_score'] = min_score
        return self
    
    def build(self) -> DictAny:
        """Построение финального фильтра"""
        return self.filters


# Предопределенные фильтры для удобства
class CommonFilters:
    """Часто используемые фильтры"""
    
    @staticmethod
    def confluence_documentation() -> SearchFilter:
        """Документация из Confluence"""
        return SearchFilter().by_source_type(['confluence']).by_category(['documentation'])
    
    @staticmethod
    def jira_requirements() -> SearchFilter:
        """Требования из Jira"""
        return SearchFilter().by_source_type(['jira']).by_category(['requirements'])
    
    @staticmethod
    def gitlab_code() -> SearchFilter:
        """Код из GitLab"""
        return SearchFilter().by_source_type(['gitlab']).by_category(['code'])
    
    @staticmethod
    def user_training_data() -> SearchFilter:
        """Пользовательские данные для обучения"""
        return SearchFilter().by_source_type(['local_files', 'user_upload']).by_category(['training_data'])
    
    @staticmethod
    def recent_updates(days: int = 7) -> SearchFilter:
        """Недавно обновленные документы"""
        from datetime import timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        return SearchFilter().by_date_range(start_date, end_date, 'updated_at')
    
    @staticmethod
    def high_quality_content(min_score: float = 0.7) -> SearchFilter:
        """Высококачественный контент"""
        return SearchFilter().by_quality_score(min_score)
    
    @staticmethod
    def by_project_context(project_key: str) -> SearchFilter:
        """Все документы в контексте проекта"""
        return SearchFilter().by_project([project_key])
    
    @staticmethod
    def documentation_sources() -> SearchFilter:
        """Источники документации"""
        return SearchFilter().by_source_type(['confluence', 'gitlab']).by_category(['documentation'])
    
    @staticmethod
    def code_and_architecture() -> SearchFilter:
        """Код и архитектура"""
        return SearchFilter().by_category(['code', 'architecture', 'documentation']) 