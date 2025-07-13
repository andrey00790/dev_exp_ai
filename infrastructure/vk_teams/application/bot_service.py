"""
VK Teams Bot Service

Основной сервис для управления VK Teams ботом:
- Настройка и конфигурация бота
- Запуск/остановка бота
- Мониторинг состояния
- Статистика использования
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from vk_teams_async_bot.bot import Bot
from vk_teams_async_bot.events import Event
from vk_teams_async_bot.filter import Filter
from vk_teams_async_bot.handler import CommandHandler, MessageHandler

from app.config import get_settings
from infrastructure.vk_teams.domain.bot_models import BotConfig, BotStats

logger = logging.getLogger(__name__)


class VKTeamsBotService:
    """
    Основной сервис для работы с VK Teams ботом
    """
    
    def __init__(self):
        self.bot: Optional[Bot] = None
        self.config: Optional[BotConfig] = None
        self.is_running: bool = False
        self.stats: BotStats = BotStats()
        self.start_time: Optional[datetime] = None
        self._polling_task: Optional[asyncio.Task] = None
        
        # Кэш для быстрого доступа к настройкам
        self.settings = get_settings()
        
    async def configure_bot(
        self,
        bot_token: str,
        api_url: str,
        webhook_url: Optional[str] = None,
        auto_start: bool = True,
        allowed_users: Optional[List[str]] = None,
        allowed_chats: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Настройка VK Teams бота
        
        Args:
            bot_token: Токен бота
            api_url: URL API VK Teams
            webhook_url: URL webhook'а (опционально)
            auto_start: Автоматический запуск после настройки
            allowed_users: Список разрешенных пользователей
            allowed_chats: Список разрешенных чатов
            
        Returns:
            Результат настройки
        """
        try:
            # Создаем конфигурацию
            self.config = BotConfig(
                bot_token=bot_token,
                api_url=api_url,
                webhook_url=webhook_url,
                allowed_users=allowed_users or [],
                allowed_chats=allowed_chats or []
            )
            
            # Создаем экземпляр бота
            self.bot = Bot(bot_token=bot_token, url=api_url)
            
            # Настраиваем обработчики
            await self._setup_handlers()
            
            # Проверяем соединение
            try:
                bot_info = await self.bot.self_get()
                logger.info(f"Бот успешно настроен: {bot_info}")
                
                self.config.bot_id = bot_info.get("userId")
                self.config.bot_name = bot_info.get("firstName", "VK Teams Bot")
                
            except Exception as e:
                logger.error(f"Ошибка проверки бота: {e}")
                raise ValueError(f"Не удается подключиться к боту: {e}")
            
            # Автоматический запуск
            if auto_start:
                await self.start_bot()
                
            return {
                "success": True,
                "message": "Бот успешно настроен",
                "config": {
                    "bot_id": self.config.bot_id,
                    "bot_name": self.config.bot_name,
                    "api_url": api_url,
                    "webhook_url": webhook_url,
                    "auto_started": auto_start and self.is_running
                }
            }
            
        except Exception as e:
            logger.error(f"Ошибка настройки бота: {e}")
            raise e
    
    async def start_bot(self) -> Dict[str, Any]:
        """
        Запуск VK Teams бота
        
        Returns:
            Результат запуска
        """
        try:
            if not self.bot or not self.config:
                raise ValueError("Бот не настроен. Сначала выполните configure_bot()")
            
            if self.is_running:
                return {
                    "success": True,
                    "message": "Бот уже запущен",
                    "start_time": self.start_time.isoformat() if self.start_time else None
                }
            
            # Запускаем polling в фоновой задаче
            self._polling_task = asyncio.create_task(self._start_polling())
            
            self.is_running = True
            self.start_time = datetime.now(timezone.utc)
            self.stats.start_time = self.start_time
            
            logger.info("VK Teams бот запущен")
            
            return {
                "success": True,
                "message": "Бот успешно запущен",
                "start_time": self.start_time.isoformat(),
                "bot_id": self.config.bot_id
            }
            
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            self.is_running = False
            raise e
    
    async def stop_bot(self) -> Dict[str, Any]:
        """
        Остановка VK Teams бота
        
        Returns:
            Результат остановки
        """
        try:
            if not self.is_running:
                return {
                    "success": True,
                    "message": "Бот уже остановлен"
                }
            
            # Останавливаем polling задачу
            if self._polling_task and not self._polling_task.done():
                self._polling_task.cancel()
                try:
                    await self._polling_task
                except asyncio.CancelledError:
                    pass
            
            self.is_running = False
            uptime = None
            
            if self.start_time:
                uptime = datetime.now(timezone.utc) - self.start_time
                self.stats.total_uptime += uptime
            
            logger.info("VK Teams бот остановлен")
            
            return {
                "success": True,
                "message": "Бот успешно остановлен",
                "uptime_seconds": uptime.total_seconds() if uptime else 0
            }
            
        except Exception as e:
            logger.error(f"Ошибка остановки бота: {e}")
            raise e
    
    async def get_bot_status(self) -> Dict[str, Any]:
        """
        Получение статуса бота
        
        Returns:
            Информация о статусе бота
        """
        try:
            status_info = {
                "is_active": self.is_running,
                "bot_id": self.config.bot_id if self.config else None,
                "bot_name": self.config.bot_name if self.config else None,
                "webhook_url": self.config.webhook_url if self.config else None,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "stats": self.stats.to_dict()
            }
            
            # Если бот запущен, добавляем uptime
            if self.is_running and self.start_time:
                uptime = datetime.now(timezone.utc) - self.start_time
                status_info["uptime_seconds"] = uptime.total_seconds()
            
            # Последняя активность
            if self.stats.last_message_time:
                status_info["last_activity"] = self.stats.last_message_time.isoformat()
            
            return status_info
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            raise e
    
    async def get_bot_statistics(self) -> Dict[str, Any]:
        """
        Получение детальной статистики бота
        
        Returns:
            Детальная статистика использования
        """
        return {
            "total_messages": self.stats.total_messages,
            "total_commands": self.stats.total_commands,
            "total_errors": self.stats.total_errors,
            "unique_users": len(self.stats.unique_users),
            "unique_chats": len(self.stats.unique_chats),
            "start_time": self.stats.start_time.isoformat() if self.stats.start_time else None,
            "last_message_time": self.stats.last_message_time.isoformat() if self.stats.last_message_time else None,
            "total_uptime_seconds": self.stats.total_uptime.total_seconds(),
            "most_active_users": self.stats.get_most_active_users(),
            "most_active_chats": self.stats.get_most_active_chats(),
            "command_usage": dict(self.stats.command_usage),
            "hourly_activity": self.stats.get_hourly_activity()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Проверка здоровья бота
        
        Returns:
            Информация о здоровье системы
        """
        health_info = {
            "is_healthy": True,
            "checks": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Проверка конфигурации
            health_info["checks"]["config"] = {
                "status": "ok" if self.config else "error",
                "message": "Конфигурация присутствует" if self.config else "Конфигурация отсутствует"
            }
            
            # Проверка состояния бота
            health_info["checks"]["bot_status"] = {
                "status": "ok" if self.is_running else "warning",
                "message": "Бот запущен" if self.is_running else "Бот остановлен"
            }
            
            # Проверка соединения с API (если бот настроен)
            if self.bot:
                try:
                    await self.bot.self_get()
                    health_info["checks"]["api_connection"] = {
                        "status": "ok",
                        "message": "Соединение с API работает"
                    }
                except Exception as e:
                    health_info["checks"]["api_connection"] = {
                        "status": "error",
                        "message": f"Ошибка соединения с API: {e}"
                    }
                    health_info["is_healthy"] = False
            else:
                health_info["checks"]["api_connection"] = {
                    "status": "warning",
                    "message": "Бот не инициализирован"
                }
            
            # Проверка статистики
            health_info["checks"]["stats"] = {
                "status": "ok",
                "message": f"Обработано сообщений: {self.stats.total_messages}"
            }
            
        except Exception as e:
            logger.error(f"Ошибка проверки здоровья: {e}")
            health_info["is_healthy"] = False
            health_info["error"] = str(e)
        
        return health_info
    
    async def _setup_handlers(self):
        """
        Настройка обработчиков команд и сообщений
        """
        if not self.bot:
            return
        
        # Импортируем адаптер здесь, чтобы избежать циклических импортов
        from infrastructure.vk_teams.infrastructure.bot_adapter_simple import get_vk_teams_bot_adapter
        
        adapter = await get_vk_teams_bot_adapter()
        
        # Обработчик команды /start
        async def cmd_start(event: Event, bot: Bot):
            await adapter.handle_start_command(event, bot)
        
        # Обработчик команды /help
        async def cmd_help(event: Event, bot: Bot):
            await adapter.handle_help_command(event, bot)
        
        # Обработчик всех сообщений
        async def handle_message(event: Event, bot: Bot):
            await adapter.handle_text_message(event, bot)
            
        # Регистрируем обработчики
        self.bot.dispatcher.add_handler(
            CommandHandler(callback=cmd_start, filters=Filter.command("/start"))
        )
        
        self.bot.dispatcher.add_handler(
            CommandHandler(callback=cmd_help, filters=Filter.command("/help"))
        )
        
        self.bot.dispatcher.add_handler(
            MessageHandler(callback=handle_message, filters=Filter.text())
        )
    
    async def _start_polling(self):
        """
        Запуск polling режима бота
        """
        try:
            if self.bot:
                await self.bot.start_polling()
        except asyncio.CancelledError:
            logger.info("Polling остановлен")
        except Exception as e:
            logger.error(f"Ошибка в polling: {e}")
            self.is_running = False


# Глобальный экземпляр сервиса
_bot_service: Optional[VKTeamsBotService] = None


async def get_vk_teams_bot_service() -> VKTeamsBotService:
    """
    Получение экземпляра VK Teams Bot Service
    
    Returns:
        Экземпляр VKTeamsBotService
    """
    global _bot_service
    
    if _bot_service is None:
        _bot_service = VKTeamsBotService()
    
    return _bot_service 