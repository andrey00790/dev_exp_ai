from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
import uuid

from models.search import (
    DataSource, ConfigureSourceRequest, SyncTriggerRequest,
    SyncResult, SyncStatusResponse, SourceType, SyncStatus
)


class DataSourceServiceInterface(ABC):
    """Interface for data source management service."""
    
    @abstractmethod
    async def list_sources(self, include_disabled: bool = False) -> List[DataSource]:
        """Возвращает список источников данных."""
        pass
    
    @abstractmethod
    async def create_source(self, request: ConfigureSourceRequest) -> DataSource:
        """Создает новый источник данных."""
        pass
    
    @abstractmethod
    async def update_source(self, source_id: str, request: ConfigureSourceRequest) -> Optional[DataSource]:
        """Обновляет источник данных."""
        pass
    
    @abstractmethod
    async def delete_source(self, source_id: str) -> bool:
        """Удаляет источник данных."""
        pass
    
    @abstractmethod
    async def test_connection(self, source_type: SourceType, config: dict) -> bool:
        """Тестирует подключение к источнику."""
        pass
    
    @abstractmethod
    async def trigger_sync(self, request: SyncTriggerRequest) -> List[SyncResult]:
        """Запускает синхронизацию источников."""
        pass
    
    @abstractmethod
    async def get_sync_status(self) -> SyncStatusResponse:
        """Возвращает статус синхронизации."""
        pass


class MockDataSourceService(DataSourceServiceInterface):
    """Mock implementation for development."""
    
    def __init__(self):
        self._sources: dict[str, DataSource] = {}
        self._sync_results: List[SyncResult] = []
    
    async def list_sources(self, include_disabled: bool = False) -> List[DataSource]:
        """Возвращает mock список источников."""
        mock_sources = [
            DataSource(
                id="confluence-main",
                name="Main Confluence",
                source_type=SourceType.CONFLUENCE,
                is_enabled=True,
                config={
                    "url": "https://company.atlassian.net",
                    "space_keys": ["ARCH", "DEV", "PROD"]
                },
                last_sync=datetime.now(),
                created_at=datetime.now()
            ),
            DataSource(
                id="gitlab-rfcs",
                name="GitLab RFC Repository",
                source_type=SourceType.GITLAB,
                is_enabled=True,
                config={
                    "url": "https://gitlab.company.com",
                    "project_ids": [123, 456]
                },
                last_sync=datetime.now(),
                created_at=datetime.now()
            )
        ]
        
        if include_disabled:
            mock_sources.append(
                DataSource(
                    id="old-jira",
                    name="Legacy Jira",
                    source_type=SourceType.JIRA,
                    is_enabled=False,
                    config={},
                    created_at=datetime.now()
                )
            )
        
        return [s for s in mock_sources if include_disabled or s.is_enabled]
    
    async def create_source(self, request: ConfigureSourceRequest) -> DataSource:
        """Создает mock источник данных."""
        source = DataSource(
            id=str(uuid.uuid4()),
            name=request.name,
            source_type=request.source_type,
            is_enabled=request.is_enabled,
            config=request.config,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self._sources[source.id] = source
        return source
    
    async def update_source(self, source_id: str, request: ConfigureSourceRequest) -> Optional[DataSource]:
        """Обновляет mock источник данных."""
        source = self._sources.get(source_id)
        if not source:
            return None
        
        source.name = request.name
        source.source_type = request.source_type
        source.is_enabled = request.is_enabled
        source.config = request.config
        source.updated_at = datetime.now()
        
        self._sources[source_id] = source
        return source
    
    async def delete_source(self, source_id: str) -> bool:
        """Удаляет mock источник данных."""
        if source_id in self._sources:
            del self._sources[source_id]
            return True
        return False
    
    async def test_connection(self, source_type: SourceType, config: dict) -> bool:
        """Mock тест подключения."""
        # Простая проверка наличия обязательных полей
        if source_type == SourceType.CONFLUENCE:
            return "url" in config and "api_token" in config
        elif source_type == SourceType.JIRA:
            return "url" in config and "api_token" in config and "username" in config
        elif source_type == SourceType.GITLAB:
            return "url" in config and "access_token" in config
        return True
    
    async def trigger_sync(self, request: SyncTriggerRequest) -> List[SyncResult]:
        """Mock синхронизация."""
        import random
        
        sources = await self.list_sources()
        if request.source_ids:
            sources = [s for s in sources if s.id in request.source_ids]
        
        results = []
        for source in sources:
            # Симулируем результаты синхронизации
            docs_processed = random.randint(10, 100)
            docs_added = random.randint(0, docs_processed // 3)
            docs_updated = random.randint(0, docs_processed // 3)
            
            result = SyncResult(
                source_id=source.id,
                source_name=source.name,
                status=SyncStatus.COMPLETED,
                documents_processed=docs_processed,
                documents_added=docs_added,
                documents_updated=docs_updated,
                documents_deleted=0,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                duration_seconds=random.uniform(30, 300)
            )
            results.append(result)
        
        self._sync_results = results
        return results
    
    async def get_sync_status(self) -> SyncStatusResponse:
        """Возвращает mock статус синхронизации."""
        if not self._sync_results:
            # Если синхронизация не запускалась, создаем mock результаты
            await self.trigger_sync(SyncTriggerRequest())
        
        overall_status = SyncStatus.COMPLETED
        if any(r.status == SyncStatus.FAILED for r in self._sync_results):
            overall_status = SyncStatus.FAILED
        elif any(r.status == SyncStatus.IN_PROGRESS for r in self._sync_results):
            overall_status = SyncStatus.IN_PROGRESS
        
        total_processed = sum(r.documents_processed for r in self._sync_results)
        
        return SyncStatusResponse(
            results=self._sync_results,
            overall_status=overall_status,
            message=f"Последняя синхронизация завершена. Обработано документов: {total_processed}"
        )


# Global instance
_data_source_service_instance = None

def get_data_source_service() -> DataSourceServiceInterface:
    """Dependency injection для data source service."""
    global _data_source_service_instance
    if _data_source_service_instance is None:
        _data_source_service_instance = MockDataSourceService()
    return _data_source_service_instance 