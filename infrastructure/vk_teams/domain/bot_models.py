"""
VK Teams Bot Models

Модели данных для работы с VK Teams ботом:
- BotConfig - конфигурация бота
- BotStats - статистика использования
- BotMessage - модель сообщения
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field


class BotConfig(BaseModel):
    """
    Конфигурация VK Teams бота
    """
    bot_token: str = Field(..., description="Токен бота")
    api_url: str = Field(..., description="URL API VK Teams")
    webhook_url: Optional[str] = Field(None, description="URL webhook'а")
    bot_id: Optional[str] = Field(None, description="ID бота")
    bot_name: Optional[str] = Field(None, description="Имя бота")
    allowed_users: List[str] = Field(default_factory=list, description="Разрешенные пользователи")
    allowed_chats: List[str] = Field(default_factory=list, description="Разрешенные чаты")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def is_user_allowed(self, user_id: str) -> bool:
        """
        Проверка разрешений пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если пользователь разрешен
        """
        # Если список пуст, разрешаем всем
        if not self.allowed_users:
            return True
            
        return user_id in self.allowed_users
    
    def is_chat_allowed(self, chat_id: str) -> bool:
        """
        Проверка разрешений чата
        
        Args:
            chat_id: ID чата
            
        Returns:
            True если чат разрешен
        """
        # Если список пуст, разрешаем все чаты
        if not self.allowed_chats:
            return True
            
        return chat_id in self.allowed_chats


class BotMessage(BaseModel):
    """
    Модель сообщения от/к VK Teams
    """
    message_id: Optional[str] = Field(None, description="ID сообщения")
    chat_id: str = Field(..., description="ID чата")
    user_id: str = Field(..., description="ID пользователя")
    text: Optional[str] = Field(None, description="Текст сообщения")
    message_type: str = Field(default="text", description="Тип сообщения")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_command: bool = Field(default=False, description="Является ли сообщение командой")
    command: Optional[str] = Field(None, description="Команда (если применимо)")
    response_time_ms: Optional[float] = Field(None, description="Время ответа в миллисекундах")
    
    @property
    def is_from_bot(self) -> bool:
        """
        Проверка, является ли сообщение от бота
        """
        return self.user_id.endswith("@bot") or "bot" in self.user_id.lower()


class BotStats:
    """
    Статистика использования VK Teams бота
    """
    
    def __init__(self):
        self.total_messages: int = 0
        self.total_commands: int = 0
        self.total_errors: int = 0
        self.unique_users: Set[str] = set()
        self.unique_chats: Set[str] = set()
        self.start_time: Optional[datetime] = None
        self.last_message_time: Optional[datetime] = None
        self.total_uptime: timedelta = timedelta()
        
        # Детальная статистика
        self.user_message_count: Dict[str, int] = defaultdict(int)
        self.chat_message_count: Dict[str, int] = defaultdict(int)
        self.command_usage: Counter = Counter()
        self.hourly_message_count: Dict[int, int] = defaultdict(int)
        self.daily_message_count: Dict[str, int] = defaultdict(int)
        self.response_times: List[float] = []
        
        # Ошибки
        self.error_types: Counter = Counter()
        self.last_errors: List[Dict[str, Any]] = []
    
    def record_message(self, message: BotMessage):
        """
        Записать статистику сообщения
        
        Args:
            message: Сообщение для записи
        """
        self.total_messages += 1
        self.last_message_time = message.timestamp
        
        # Уникальные пользователи и чаты
        self.unique_users.add(message.user_id)
        self.unique_chats.add(message.chat_id)
        
        # Счетчики по пользователям и чатам
        self.user_message_count[message.user_id] += 1
        self.chat_message_count[message.chat_id] += 1
        
        # Команды
        if message.is_command and message.command:
            self.total_commands += 1
            self.command_usage[message.command] += 1
        
        # Временная статистика
        hour = message.timestamp.hour
        self.hourly_message_count[hour] += 1
        
        day_key = message.timestamp.strftime("%Y-%m-%d")
        self.daily_message_count[day_key] += 1
        
        # Время ответа
        if message.response_time_ms:
            self.response_times.append(message.response_time_ms)
            
            # Ограничиваем размер списка
            if len(self.response_times) > 1000:
                self.response_times = self.response_times[-500:]
    
    def record_error(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None):
        """
        Записать ошибку
        
        Args:
            error_type: Тип ошибки
            error_message: Сообщение об ошибке
            context: Дополнительный контекст
        """
        self.total_errors += 1
        self.error_types[error_type] += 1
        
        error_record = {
            "type": error_type,
            "message": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": context or {}
        }
        
        self.last_errors.append(error_record)
        
        # Ограничиваем размер списка ошибок
        if len(self.last_errors) > 100:
            self.last_errors = self.last_errors[-50:]
    
    def get_most_active_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получить самых активных пользователей
        
        Args:
            limit: Лимит результатов
            
        Returns:
            Список самых активных пользователей
        """
        return [
            {"user_id": user_id, "message_count": count}
            for user_id, count in Counter(self.user_message_count).most_common(limit)
        ]
    
    def get_most_active_chats(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получить самые активные чаты
        
        Args:
            limit: Лимит результатов
            
        Returns:
            Список самых активных чатов
        """
        return [
            {"chat_id": chat_id, "message_count": count}
            for chat_id, count in Counter(self.chat_message_count).most_common(limit)
        ]
    
    def get_hourly_activity(self) -> Dict[int, int]:
        """
        Получить активность по часам
        
        Returns:
            Словарь с активностью по часам (0-23)
        """
        return dict(self.hourly_message_count)
    
    def get_daily_activity(self, days: int = 7) -> Dict[str, int]:
        """
        Получить активность по дням
        
        Args:
            days: Количество дней для отображения
            
        Returns:
            Словарь с активностью по дням
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        return {
            day: count for day, count in self.daily_message_count.items()
            if day >= cutoff_str
        }
    
    def get_average_response_time(self) -> Optional[float]:
        """
        Получить среднее время ответа
        
        Returns:
            Среднее время ответа в миллисекундах
        """
        if not self.response_times:
            return None
            
        return sum(self.response_times) / len(self.response_times)
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получить последние ошибки
        
        Args:
            limit: Лимит результатов
            
        Returns:
            Список последних ошибок
        """
        return self.last_errors[-limit:] if self.last_errors else []
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразовать статистику в словарь
        
        Returns:
            Словарь со статистикой
        """
        return {
            "total_messages": self.total_messages,
            "total_commands": self.total_commands,
            "total_errors": self.total_errors,
            "unique_users": len(self.unique_users),
            "unique_chats": len(self.unique_chats),
            "average_response_time_ms": self.get_average_response_time(),
            "uptime_seconds": self.total_uptime.total_seconds(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_message_time": self.last_message_time.isoformat() if self.last_message_time else None
        }


class AIAssistantContext(BaseModel):
    """
    Контекст для интеграции с AI ассистентом
    """
    user_id: str = Field(..., description="ID пользователя")
    chat_id: str = Field(..., description="ID чата")
    conversation_history: List[BotMessage] = Field(default_factory=list, description="История разговора")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="Настройки пользователя")
    active_session: Optional[str] = Field(None, description="ID активной сессии")
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    def add_message(self, message: BotMessage):
        """
        Добавить сообщение в историю
        
        Args:
            message: Сообщение для добавления
        """
        self.conversation_history.append(message)
        self.last_activity = datetime.now(timezone.utc)
        
        # Ограничиваем размер истории
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-25:]
    
    def get_recent_messages(self, count: int = 10) -> List[BotMessage]:
        """
        Получить последние сообщения
        
        Args:
            count: Количество сообщений
            
        Returns:
            Список последних сообщений
        """
        return self.conversation_history[-count:] if self.conversation_history else []
    
    def clear_history(self):
        """
        Очистить историю разговора
        """
        self.conversation_history.clear()
        self.active_session = None 