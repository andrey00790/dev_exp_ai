"""
Data Source Service
Сервис для управления источниками данных
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class DataSourceServiceInterface(ABC):
    """Interface for data source service"""

    @abstractmethod
    async def list_sources(
        self, include_disabled: bool = False
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def create_source(self, request) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def update_source(self, source_id: str, request) -> Optional[Dict[str, Any]]:
        pass


class DataSourceService:
    """Сервис управления источниками данных"""

    def __init__(self):
        self.sources = {}

    async def list_sources(
        self, include_disabled: bool = False
    ) -> List[Dict[str, Any]]:
        """Получить список источников"""
        return []

    async def create_source(self, request) -> Dict[str, Any]:
        """Создать новый источник"""
        return {"id": "test_source", "name": "Test Source"}

    async def update_source(self, source_id: str, request) -> Optional[Dict[str, Any]]:
        """Обновить источник"""
        return {"id": source_id, "name": "Updated Source"}

    async def delete_source(self, source_id: str) -> bool:
        """Удалить источник"""
        return True

    async def test_connection(self, source_type: str, config: Dict[str, Any]) -> bool:
        """Тестировать подключение к источнику"""
        return True

    async def trigger_sync(self, request) -> List[Dict[str, Any]]:
        """Запустить синхронизацию"""
        return []

    async def get_sync_status(self) -> Dict[str, Any]:
        """Получить статус синхронизации"""
        return {"status": "idle", "last_sync": None}


# Singleton instance
_data_source_service = None


async def get_data_source_service() -> DataSourceService:
    """Получить экземпляр сервиса источников данных"""
    global _data_source_service
    if _data_source_service is None:
        _data_source_service = DataSourceService()
    return _data_source_service
