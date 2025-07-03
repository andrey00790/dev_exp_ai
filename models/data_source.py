#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
models/data_source.py

Модель источников данных для AI Assistant.

Поддерживаемые источники:
1. bootstrap - локальные обучающие материалы
2. confluence - корпоративная документация  
3. jira - задачи и тикеты
4. gitlab - исходный код
5. corporate - внутренние корпоративные материалы

Архитектура: расширяемая, позволяет добавлять новые источники.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
import json
from pathlib import Path
from datetime import datetime

from models.shared.enums import SourceType, ProcessingStatus, ContentType
from models.shared.types import DictAny, ListStr, OptionalStr


@dataclass
class SourceMetadata:
    """Метаданные источника данных"""
    name: str                           # Название источника
    description: Optional[str] = None   # Описание
    category: Optional[str] = None      # Категория (например, "academic", "system_design")
    role: Optional[str] = None         # Роль (например, "Developer", "System Architect")
    url: Optional[str] = None          # Исходный URL
    file_path: Optional[str] = None    # Путь к файлу
    file_size: Optional[int] = None    # Размер файла
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: ListStr = field(default_factory=list)
    additional_data: DictAny = field(default_factory=dict)


@dataclass 
class DataSourceConfig:
    """Конфигурация источника данных"""
    source_type: SourceType
    enabled: bool = True
    priority: int = 1                  # Приоритет обработки (1 = высокий)
    batch_size: int = 100             # Размер батча для обработки
    filters: DictAny = field(default_factory=dict)
    connection_params: DictAny = field(default_factory=dict)
    metadata: Optional[SourceMetadata] = None


@dataclass
class ProcessingResult:
    """Результат обработки источника"""
    source_type: SourceType
    status: ProcessingStatus
    items_processed: int = 0
    items_success: int = 0
    items_failed: int = 0
    items_skipped: int = 0
    processing_time: float = 0.0
    error_message: Optional[str] = None
    artifacts: ListStr = field(default_factory=list)  # Пути к созданным файлам
    metadata: DictAny = field(default_factory=dict)


class DataSourceRegistry:
    """Реестр источников данных"""
    
    def __init__(self):
        self._sources: Dict[str, DataSourceConfig] = {}
        self._processors: Dict[SourceType, callable] = {}
        
    def register_source(self, source_id: str, config: DataSourceConfig):
        """Регистрирует источник данных"""
        self._sources[source_id] = config
        
    def register_processor(self, source_type: SourceType, processor_func: callable):
        """Регистрирует обработчик для типа источника"""
        self._processors[source_type] = processor_func
        
    def get_source(self, source_id: str) -> Optional[DataSourceConfig]:
        """Получает конфигурацию источника"""
        return self._sources.get(source_id)
        
    def get_processor(self, source_type: SourceType) -> Optional[callable]:
        """Получает обработчик для типа источника"""
        return self._processors.get(source_type)
        
    def list_sources(self, enabled_only: bool = True) -> List[DataSourceConfig]:
        """Возвращает список источников"""
        sources = list(self._sources.values())
        if enabled_only:
            sources = [s for s in sources if s.enabled]
        return sorted(sources, key=lambda x: x.priority)
        
    def get_sources_by_type(self, source_type: SourceType) -> List[DataSourceConfig]:
        """Возвращает источники определенного типа"""
        return [s for s in self._sources.values() if s.source_type == source_type]


class DataSourceManager:
    """Менеджер источников данных"""
    
    def __init__(self):
        self.registry = DataSourceRegistry()
        self._initialize_default_sources()
        
    def _initialize_default_sources(self):
        """Инициализирует источники по умолчанию"""
        
        # Bootstrap источник (локальные материалы)
        bootstrap_config = DataSourceConfig(
            source_type=SourceType.BOOTSTRAP,
            enabled=True,
            priority=1,
            metadata=SourceMetadata(
                name="Bootstrap Learning Materials",
                description="Локальные обучающие материалы из resource_config.yml",
                category="educational"
            )
        )
        self.registry.register_source("bootstrap", bootstrap_config)
        
        # Confluence источник
        confluence_config = DataSourceConfig(
            source_type=SourceType.CONFLUENCE,
            enabled=True,
            priority=2,
            metadata=SourceMetadata(
                name="Confluence Documentation",
                description="Корпоративная документация из Confluence",
                category="documentation"
            )
        )
        self.registry.register_source("confluence", confluence_config)
        
        # Jira источник
        jira_config = DataSourceConfig(
            source_type=SourceType.JIRA,
            enabled=True,
            priority=3,
            metadata=SourceMetadata(
                name="Jira Issues",
                description="Задачи и тикеты из Jira",
                category="issues"
            )
        )
        self.registry.register_source("jira", jira_config)
        
        # GitLab источник
        gitlab_config = DataSourceConfig(
            source_type=SourceType.GITLAB,
            enabled=True,
            priority=4,
            metadata=SourceMetadata(
                name="GitLab Repositories",
                description="Исходный код и комментарии из GitLab",
                category="code"
            )
        )
        self.registry.register_source("gitlab", gitlab_config)
        
        # Corporate источник
        corporate_config = DataSourceConfig(
            source_type=SourceType.CORPORATE,
            enabled=False,  # По умолчанию отключен
            priority=5,
            metadata=SourceMetadata(
                name="Corporate Materials",
                description="Внутренние корпоративные материалы",
                category="corporate"
            )
        )
        self.registry.register_source("corporate", corporate_config)
        
    def discover_bootstrap_sources(self, bootstrap_dir: Union[str, Path]) -> List[SourceMetadata]:
        """Автообнаружение источников в папке bootstrap"""
        bootstrap_path = Path(bootstrap_dir)
        discovered = []
        
        if not bootstrap_path.exists():
            return discovered
            
        # Ищем метаданные файлы (.json)
        for metadata_file in bootstrap_path.rglob("*.json"):
            if metadata_file.name == "download_stats.json":
                continue  # Пропускаем общую статистику
                
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                metadata = SourceMetadata(
                    name=data.get('name', metadata_file.stem),
                    description=f"Загружен из {data.get('url', 'unknown')}",
                    category=data.get('category'),
                    role=data.get('role'),
                    url=data.get('url'),
                    file_path=data.get('file_path'),
                    file_size=data.get('file_size'),
                    created_at=datetime.fromisoformat(data['downloaded_at']) if data.get('downloaded_at') else None,
                    tags=[data.get('url_type', 'unknown')]
                )
                discovered.append(metadata)
                
            except Exception as e:
                # Логируем ошибку, но продолжаем
                print(f"Ошибка при обработке метаданных {metadata_file}: {e}")
                
        return discovered
        
    def get_source_filters(self) -> DictAny:
        """Возвращает доступные фильтры для UI"""
        sources = self.registry.list_sources()
        
        filters = {
            "source_types": [s.source_type.value for s in sources],
            "categories": [],
            "roles": []
        }
        
        for source in sources:
            if source.metadata:
                if source.metadata.category:
                    filters["categories"].append(source.metadata.category)
                if source.metadata.role:
                    filters["roles"].append(source.metadata.role)
                    
        # Убираем дубликаты и сортируем
        filters["categories"] = sorted(list(set(filters["categories"])))
        filters["roles"] = sorted(list(set(filters["roles"])))
        
        return filters
        
    def process_source(self, source_id: str, **kwargs) -> ProcessingResult:
        """Обрабатывает указанный источник"""
        config = self.registry.get_source(source_id)
        if not config:
            return ProcessingResult(
                source_type=SourceType.BOOTSTRAP,  # Fallback
                status=ProcessingStatus.FAILED,
                error_message=f"Источник {source_id} не найден"
            )
            
        processor = self.registry.get_processor(config.source_type)
        if not processor:
            return ProcessingResult(
                source_type=config.source_type,
                status=ProcessingStatus.FAILED,
                error_message=f"Обработчик для {config.source_type} не найден"
            )
            
        try:
            result = processor(config, **kwargs)
            result.status = ProcessingStatus.COMPLETED
            return result
        except Exception as e:
            return ProcessingResult(
                source_type=config.source_type,
                status=ProcessingStatus.FAILED,
                error_message=str(e)
            )


# Глобальный экземпляр менеджера
data_source_manager = DataSourceManager()


def get_data_source_manager() -> DataSourceManager:
    """Возвращает глобальный экземпляр менеджера источников данных"""
    return data_source_manager


# Utility функции для работы с источниками
def create_source_metadata_from_file(file_path: Union[str, Path], **kwargs) -> SourceMetadata:
    """Создает метаданные источника из файла"""
    path = Path(file_path)
    
    return SourceMetadata(
        name=path.stem,
        file_path=str(path),
        file_size=path.stat().st_size if path.exists() else None,
        created_at=datetime.fromtimestamp(path.stat().st_ctime) if path.exists() else None,
        **kwargs
    )


def filter_sources_by_criteria(
    sources: List[SourceMetadata], 
    category: OptionalStr = None,
    role: OptionalStr = None,
    tags: Optional[ListStr] = None
) -> List[SourceMetadata]:
    """Фильтрует источники по критериям"""
    filtered = sources
    
    if category:
        filtered = [s for s in filtered if s.category == category]
        
    if role:
        filtered = [s for s in filtered if s.role == role]
        
    if tags:
        filtered = [s for s in filtered if any(tag in s.tags for tag in tags)]
        
    return filtered 