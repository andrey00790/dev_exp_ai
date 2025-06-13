# services/data_sync_service.py
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import base64
from gitlab import Gitlab

from user_config_manager import UserConfigManager, get_user_config_manager
from models.search import SourceType

# Настройка логгера
logger = logging.getLogger(__name__)

class SourceFetcher(ABC):
    """Абстрактный класс для выкачивания данных из источников."""
    
    @abstractmethod
    async def fetch(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Выкачивает данные и возвращает список документов."""
        pass

class JiraFetcher(SourceFetcher):
    """Выкачивает данные из Jira."""
    async def fetch(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info(f"Выкачивание данных из Jira: {config.get('project_keys')}")
        # Здесь будет логика для подключения к Jira API и выкачивания данных
        await asyncio.sleep(2) # Имитация работы
        return [{"source": "jira", "content": "Jira issue content"}]

class ConfluenceFetcher(SourceFetcher):
    """Выкачивает данные из Confluence."""
    async def fetch(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info(f"Выкачивание данных из Confluence: {config.get('space_keys')}")
        await asyncio.sleep(2)
        return [{"source": "confluence", "content": "Confluence page content"}]

class GitLabFetcher(SourceFetcher):
    """Выкачивает данные из GitLab."""
    async def fetch(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info(f"Выкачивание данных из GitLab: {config.get('project_ids')}")

        url = config.get("url")
        token = config.get("access_token")
        project_ids = config.get("project_ids", [])

        if not url or not token:
            raise ValueError("GitLab 'url' and 'access_token' are required")

        gl = Gitlab(url, private_token=token)

        docs: List[Dict[str, Any]] = []
        loop = asyncio.get_running_loop()

        for pid in project_ids:
            def _fetch_project(p: int) -> Optional[Dict[str, Any]]:
                try:
                    project = gl.projects.get(p)
                    readme = project.files.get(file_path="README.md", ref=project.default_branch or "main")
                    content = base64.b64decode(readme.content).decode()
                    return {"source": "gitlab", "project_id": p, "content": content}
                except Exception as exc:
                    logger.warning(f"Не удалось получить данные проекта {p}: {exc}")
                    return None

            result = await loop.run_in_executor(None, _fetch_project, pid)
            if result:
                docs.append(result)

        return docs

class BootstrapConfigFetcher(SourceFetcher):
    """Читает данные из bootstrap_config.yml."""
    async def fetch(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        file_path = config.get("file_path", "dataset_config.yml")
        logger.info(f"Чтение данных из bootstrap config: {file_path}")
        # Здесь будет логика для чтения и парсинга YAML файла
        await asyncio.sleep(1)
        return [{"source": "bootstrap_config", "content": "Content from YAML"}]

class MailCloudFetcher(SourceFetcher):
    """Выкачивает данные из облака Mail.ru."""
    async def fetch(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info(f"Выкачивание данных из Mail.ru Cloud: {config.get('folder_path')}")
        await asyncio.sleep(3)
        return [{"source": "mail_cloud", "content": "Content from Mail.ru Cloud"}]


class DataSyncService:
    """Сервис для синхронизации данных из различных источников."""
    
    def __init__(self, config_manager: UserConfigManager):
        self.config_manager = config_manager
        self.scheduler = AsyncIOScheduler()
        self.fetchers = {
            SourceType.JIRA: JiraFetcher(),
            SourceType.CONFLUENCE: ConfluenceFetcher(),
            SourceType.GITLAB: GitLabFetcher(),
            "bootstrap_config": BootstrapConfigFetcher(),
            "mail_cloud": MailCloudFetcher(),
        }

    async def sync_source(self, user_id: int, source_type: str, source_name: str) -> None:
        """Синхронизирует один источник для пользователя."""
        logger.info(f"Запуск синхронизации для: user_id={user_id}, source={source_type}:{source_name}")
        
        try:
            # Получаем конфиг
            sources = self.config_manager.get_user_data_sources(user_id, source_type)
            source_config = next((s for s in sources if s.source_name == source_name), None)

            if not source_config or not source_config.is_enabled_semantic_search:
                logger.warning(f"Источник {source_type}:{source_name} не найден или отключен.")
                return

            # Обновляем статус
            self.config_manager.update_sync_status(user_id, source_type, source_name, "running")
            
            # Выкачиваем данные
            fetcher = self.fetchers.get(source_type)
            if not fetcher:
                raise ValueError(f"Нет обработчика для источника: {source_type}")
                
            documents = await fetcher.fetch(source_config.connection_config)
            
            # Здесь будет логика для индексации документов в Qdrant
            logger.info(f"Получено {len(documents)} документов из {source_type}:{source_name}. Начинаем индексацию...")
            
            # Обновляем статус и время последней синхронизации
            self.config_manager.update_sync_status(user_id, source_type, source_name, "success")
            logger.info(f"Синхронизация для {source_type}:{source_name} успешно завершена.")

        except Exception as e:
            logger.error(f"Ошибка при синхронизации {source_type}:{source_name}: {e}", exc_info=True)
            self.config_manager.update_sync_status(user_id, source_type, source_name, "error", str(e))

    def schedule_sync_jobs(self):
        """Планирует задачи синхронизации на основе настроек пользователей."""
        logger.info("Планирование фоновых задач синхронизации...")
        users = self.config_manager.get_all_users() # Предполагаем, что есть такой метод

        for user in users:
            sources = self.config_manager.get_user_data_sources(user.id)
            for source in sources:
                if source.sync_schedule:
                    self.scheduler.add_job(
                        self.sync_source,
                        trigger=CronTrigger.from_crontab(source.sync_schedule),
                        args=[user.id, source.source_type, source.source_name],
                        id=f"sync_{user.id}_{source.source_type}_{source.source_name}",
                        replace_existing=True
                    )
        
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Планировщик запущен.")

    async def sync_on_startup(self):
        """Запускает синхронизацию при старте для всех пользователей и источников с флагом auto_sync_on_startup."""
        logger.info("Запуск синхронизации при старте приложения...")
        # Эта логика должна быть расширена для получения всех пользователей
        users_for_startup_sync = [1] # Заглушка
        
        for user_id in users_for_startup_sync:
            sources = self.config_manager.get_user_data_sources(user_id)
            for source in sources:
                if source.auto_sync_on_startup and source.is_enabled_semantic_search:
                    asyncio.create_task(self.sync_source(user_id, source.source_type, source.source_name))


# DI для сервиса
_data_sync_service: Optional[DataSyncService] = None

def get_data_sync_service() -> DataSyncService:
    global _data_sync_service
    if _data_sync_service is None:
        config_manager = get_user_config_manager()
        _data_sync_service = DataSyncService(config_manager)
    return _data_sync_service 