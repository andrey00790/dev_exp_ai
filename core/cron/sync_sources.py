#!/usr/bin/env python3
"""
Cron скрипт для автоматической синхронизации данных из источников.

Запускается по расписанию для:
- Синхронизации с Confluence, Jira, GitLab
- Обновления векторной базы данных
- Оптимизации: пропуск неизмененных документов
- Метаданные в PostgreSQL

Использование:
    python core/cron/sync_sources.py [--source-id SOURCE_ID] [--force-full]
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Добавляем корневую директорию в путь для импорта модулей
sys.path.append(str(Path(__file__).parent.parent.parent))

from domain.integration.data_source_service import get_data_source_service
from models.search import SyncTriggerRequest, SourceType
from app.config import settings
from domain.integration.data_sync_service import DataSyncService
from user_config_manager import UserConfigManager, get_user_config_manager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sync_sources.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SourceSynchronizer:
    """Класс для синхронизации источников данных."""
    
    def __init__(self):
        self.data_source_service = get_data_source_service()
        self.start_time = datetime.now()
    
    async def sync_all_sources(self, force_full: bool = False) -> bool:
        """
        Синхронизирует все активные источники данных.
        
        Args:
            force_full: Принудительная полная синхронизация
            
        Returns:
            True если синхронизация прошла успешно
        """
        try:
            logger.info("Начинаем синхронизацию всех источников...")
            
            # Получаем список активных источников
            sources = await self.data_source_service.list_sources(include_disabled=False)
            if not sources:
                logger.warning("Нет активных источников для синхронизации")
                return True
            
            logger.info(f"Найдено {len(sources)} активных источников")
            
            # Запускаем синхронизацию
            sync_request = SyncTriggerRequest(
                source_ids=[],  # Пустой список = все источники
                force_full_sync=force_full
            )
            
            results = await self.data_source_service.trigger_sync(sync_request)
            
            # Анализируем результаты
            success_count = 0
            total_docs_processed = 0
            total_docs_added = 0
            total_docs_updated = 0
            total_docs_deleted = 0
            
            for result in results:
                if result.status == "completed":
                    success_count += 1
                    total_docs_processed += result.documents_processed
                    total_docs_added += result.documents_added
                    total_docs_updated += result.documents_updated
                    total_docs_deleted += result.documents_deleted
                    
                    logger.info(
                        f"✅ {result.source_name}: обработано {result.documents_processed}, "
                        f"добавлено {result.documents_added}, обновлено {result.documents_updated}"
                    )
                else:
                    logger.error(f"❌ Ошибка синхронизации {result.source_name}: {result.errors}")
            
            # Логируем сводку
            duration = (datetime.now() - self.start_time).total_seconds()
            logger.info(
                f"Синхронизация завершена за {duration:.1f}с. "
                f"Успешно: {success_count}/{len(results)}. "
                f"Всего обработано: {total_docs_processed} документов "
                f"(+{total_docs_added}, ~{total_docs_updated}, -{total_docs_deleted})"
            )
            
            return success_count == len(results)
            
        except Exception as e:
            logger.error(f"Критическая ошибка синхронизации: {str(e)}", exc_info=True)
            return False
    
    async def sync_specific_source(self, source_id: str, force_full: bool = False) -> bool:
        """
        Синхронизирует конкретный источник данных.
        
        Args:
            source_id: ID источника для синхронизации
            force_full: Принудительная полная синхронизация
            
        Returns:
            True если синхронизация прошла успешно
        """
        try:
            logger.info(f"Начинаем синхронизацию источника {source_id}...")
            
            sync_request = SyncTriggerRequest(
                source_ids=[source_id],
                force_full_sync=force_full
            )
            
            results = await self.data_source_service.trigger_sync(sync_request)
            
            if not results:
                logger.error(f"Источник {source_id} не найден или неактивен")
                return False
            
            result = results[0]
            
            if result.status == "completed":
                duration = result.duration_seconds or 0
                logger.info(
                    f"✅ Синхронизация {result.source_name} завершена за {duration:.1f}с. "
                    f"Обработано: {result.documents_processed}, "
                    f"добавлено: {result.documents_added}, "
                    f"обновлено: {result.documents_updated}"
                )
                return True
            else:
                logger.error(f"❌ Ошибка синхронизации {result.source_name}: {result.errors}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка синхронизации источника {source_id}: {str(e)}", exc_info=True)
            return False
    
    async def health_check(self) -> bool:
        """
        Проверяет состояние системы перед синхронизацией.
        
        Returns:
            True если система готова к синхронизации
        """
        try:
            # Проверяем доступность сервисов
            sources = await self.data_source_service.list_sources()
            logger.info(f"Система готова к синхронизации. Доступно {len(sources)} источников.")
            return True
            
        except Exception as e:
            logger.error(f"Система не готова к синхронизации: {str(e)}")
            return False


async def main():
    """Главная функция cron скрипта."""
    parser = argparse.ArgumentParser(
        description="Синхронизация данных из источников для AI Assistant"
    )
    parser.add_argument(
        "--source-id", 
        help="ID конкретного источника для синхронизации"
    )
    parser.add_argument(
        "--force-full", 
        action="store_true",
        help="Принудительная полная синхронизация (игнорировать кеш)"
    )
    parser.add_argument(
        "--health-check-only",
        action="store_true", 
        help="Только проверить состояние системы"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Подробное логирование"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Включено подробное логирование")
    
    logger.info("🚀 Запуск cron скрипта синхронизации источников данных")
    logger.info(f"Параметры: source_id={args.source_id}, force_full={args.force_full}")
    
    synchronizer = SourceSynchronizer()
    
    # Проверяем состояние системы
    if not await synchronizer.health_check():
        logger.error("❌ Система не готова к синхронизации")
        sys.exit(1)
    
    if args.health_check_only:
        logger.info("✅ Проверка состояния завершена успешно")
        sys.exit(0)
    
    # Выполняем синхронизацию
    if args.source_id:
        success = await synchronizer.sync_specific_source(args.source_id, args.force_full)
    else:
        success = await synchronizer.sync_all_sources(args.force_full)
    
    if success:
        logger.info("✅ Синхронизация завершена успешно")
        sys.exit(0)
    else:
        logger.error("❌ Синхронизация завершена с ошибками")
        sys.exit(1)


if __name__ == "__main__":
    # Создаем директорию для логов, если её нет
    Path("logs").mkdir(exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Синхронизация прервана пользователем")
        sys.exit(130)  # SIGINT exit code
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}", exc_info=True)
        sys.exit(1) 