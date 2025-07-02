"""
VK Teams Bot Adapter

Адаптер для интеграции VK Teams бота с существующими API AI-ассистента:
- Обработка сообщений от пользователей
- Вызов существующих API endpoints
- Форматирование ответов для VK Teams
- Управление сессиями и контекстом
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import httpx
from vk_teams_async_bot.bot import Bot
from vk_teams_async_bot.events import Event
from vk_teams_async_bot.helpers import InlineKeyboardMarkup, KeyboardButton
from vk_teams_async_bot.constants import StyleKeyboard, ParseMode

from app.config import get_settings
from domain.vk_teams.bot_models import AIAssistantContext, BotMessage, BotStats

logger = logging.getLogger(__name__)


class VKTeamsBotAdapter:
    """
    Адаптер для интеграции VK Teams бота с AI-ассистентом
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.stats: Optional[BotStats] = None
        self.user_contexts: Dict[str, AIAssistantContext] = {}
        
        # HTTP клиент для внутренних API вызовов
        self.api_client = httpx.AsyncClient(
            base_url=f"http://localhost:{self.settings.SERVER_PORT}",
            timeout=30.0
        )
        
        # Кэш для быстрого доступа к пользовательским данным
        self._user_cache: Dict[str, Dict[str, Any]] = {}
        
        # VK OAuth проверка пользователей
        self._vk_auth_enabled = getattr(self.settings, 'VK_OAUTH_ENABLED', False)
        
    async def handle_event(
        self, 
        event_type: str, 
        event_id: str, 
        timestamp: int, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Обработка входящих событий от VK Teams
        
        Args:
            event_type: Тип события
            event_id: ID события
            timestamp: Временная метка
            payload: Данные события
            
        Returns:
            Результат обработки
        """
        try:
            logger.info(f"Обработка события {event_type} (ID: {event_id})")
            
            if event_type == "newMessage":
                return await self._handle_new_message(payload)
            elif event_type == "callbackQuery":
                return await self._handle_callback_query(payload)
            elif event_type == "editedMessage":
                return await self._handle_edited_message(payload)
            else:
                logger.warning(f"Неизвестный тип события: {event_type}")
                return {"status": "ignored", "reason": f"Unknown event type: {event_type}"}
                
        except Exception as e:
            logger.error(f"Ошибка обработки события {event_id}: {e}")
            if self.stats:
                self.stats.record_error("event_processing", str(e), {"event_type": event_type})
            return {"status": "error", "error": str(e)}
    
    async def handle_message_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка события сообщения
        
        Args:
            event_data: Данные события
            
        Returns:
            Результат обработки
        """
        try:
            payload = event_data.get("payload", {})
            return await self._handle_new_message(payload)
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            return {"status": "error", "error": str(e)}
    
    async def handle_callback_query(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка callback запроса
        
        Args:
            event_data: Данные события
            
        Returns:
            Результат обработки
        """
        try:
            payload = event_data.get("payload", {})
            return await self._handle_callback_query(payload)
        except Exception as e:
            logger.error(f"Ошибка обработки callback: {e}")
            return {"status": "error", "error": str(e)}
    
    async def handle_start_command(self, event: Event, bot: Bot):
        """
        Обработка команды /start
        
        Args:
            event: Событие VK Teams
            bot: Экземпляр бота
        """
        try:
            chat_id = event.chat.chatId
            user_id = event.from_.userId
            
            # Создаем/обновляем контекст пользователя
            context = self._get_or_create_user_context(user_id, chat_id)
            
            welcome_text = """🤖 **AI-Ассистент VK Teams**
            
Привет! Я ваш AI-помощник. Я могу:

🔍 **Поиск информации** - семантический поиск по документам
💬 **Ответы на вопросы** - умные ответы на основе ваших данных  
📝 **Генерация RFC** - создание технических документов
🔧 **Анализ кода** - проверка качества и безопасности
📊 **Аналитика** - insights и отчеты

**Команды:**
• `/help` - показать все команды
• `/search <запрос>` - поиск информации
• `/generate` - генерация документов
• `/analyze` - анализ данных

Просто напишите мне вопрос, и я постараюсь помочь! 🚀"""
            
            # Создаем клавиатуру с основными функциями
            keyboard = self._create_main_menu_keyboard()
            
            await bot.send_text(
                chat_id=chat_id,
                text=welcome_text,
                parse_mode=ParseMode.MARKDOWNV2,
                inline_keyboard_markup=keyboard
            )
            
            # Записываем статистику
            if self.stats:
                message = BotMessage(
                    chat_id=chat_id,
                    user_id=user_id,
                    text="/start",
                    is_command=True,
                    command="start"
                )
                self.stats.record_message(message)
            
        except Exception as e:
            logger.error(f"Ошибка команды /start: {e}")
            await bot.send_text(
                chat_id=event.chat.chatId,
                text="😔 Произошла ошибка. Попробуйте позже."
            )
    
    async def handle_help_command(self, event: Event, bot: Bot):
        """
        Обработка команды /help
        
        Args:
            event: Событие VK Teams
            bot: Экземпляр бота
        """
        try:
            help_text = """📖 **Справка по командам**

**🔍 Поиск и анализ:**
• `/search <запрос>` - семантический поиск
• `/vector_search <запрос>` - векторный поиск
• `/analyze <текст>` - анализ текста

**📝 Генерация контента:**
• `/generate rfc` - создать RFC документ
• `/generate docs` - создать документацию
• `/template` - показать шаблоны

**⚙️ AI функции:**
• `/chat <сообщение>` - диалог с AI
• `/optimize` - оптимизация кода
• `/review` - code review

**📊 Информация:**
• `/status` - статус системы
• `/stats` - статистика использования
• `/settings` - настройки

**💡 Примеры использования:**
• `Найди документацию по API аутентификации`
• `Создай RFC для новой микросервисной архитектуры`
• `Проанализируй этот код на безопасность`

Или просто напишите вопрос естественным языком! 🤖"""
            
            await bot.send_text(
                chat_id=event.chat.chatId,
                text=help_text,
                parse_mode=ParseMode.MARKDOWNV2
            )
            
        except Exception as e:
            logger.error(f"Ошибка команды /help: {e}")
            await bot.send_text(
                chat_id=event.chat.chatId,
                text="😔 Ошибка показа справки."
            )
    
    async def handle_text_message(self, event: Event, bot: Bot):
        """
        Обработка текстовых сообщений
        
        Args:
            event: Событие VK Teams
            bot: Экземпляр бота
        """
        start_time = time.time()
        
        try:
            chat_id = event.chat.chatId
            user_id = event.from_.userId
            text = event.text
            
            logger.info(f"Получено сообщение от {user_id}: {text[:100]}...")
            
            # Проверка VK OAuth авторизации
            if self._vk_auth_enabled:
                if not await self._check_vk_user_access(user_id):
                    await self._send_access_denied_message(bot, chat_id, user_id)
                    return
            
            # Проверяем команды
            if text.startswith('/'):
                await self._handle_command_message(event, bot)
                return
            
            # Получаем контекст пользователя
            context = self._get_or_create_user_context(user_id, chat_id)
            
            # Отправляем typing indicator
            # await bot.send_typing(chat_id)
            
            # Обрабатываем сообщение через AI API
            response = await self._process_ai_request(text, context)
            
            # Отправляем ответ
            await self._send_ai_response(bot, chat_id, response)
            
            # Записываем статистику
            if self.stats:
                response_time = (time.time() - start_time) * 1000
                message = BotMessage(
                    chat_id=chat_id,
                    user_id=user_id,
                    text=text,
                    response_time_ms=response_time
                )
                self.stats.record_message(message)
                context.add_message(message)
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await bot.send_text(
                chat_id=event.chat.chatId,
                text="😔 Произошла ошибка при обработке сообщения. Попробуйте еще раз."
            )
            
            if self.stats:
                self.stats.record_error("message_processing", str(e))
    
    async def test_event_processing(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Тестовая обработка событий
        
        Args:
            test_data: Тестовые данные
            
        Returns:
            Результат тестирования
        """
        return {
            "test_successful": True,
            "processed_data": test_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_new_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка нового сообщения
        """
        try:
            chat = payload.get("chat", {})
            from_user = payload.get("from", {})
            text = payload.get("text", "")
            
            chat_id = chat.get("chatId")
            user_id = from_user.get("userId")
            
            logger.info(f"Новое сообщение от {user_id} в чате {chat_id}: {text}")
            
            return {"status": "processed", "chat_id": chat_id, "user_id": user_id}
            
        except Exception as e:
            logger.error(f"Ошибка обработки нового сообщения: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _handle_callback_query(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка callback query
        """
        try:
            callback_data = payload.get("callbackData", "")
            chat_id = payload.get("message", {}).get("chat", {}).get("chatId")
            user_id = payload.get("from", {}).get("userId")
            
            logger.info(f"Callback от {user_id}: {callback_data}")
            
            # Обрабатываем callback данные
            await self._process_callback_action(callback_data, chat_id, user_id)
            
            return {"status": "processed", "callback_data": callback_data}
            
        except Exception as e:
            logger.error(f"Ошибка обработки callback: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _handle_edited_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка отредактированного сообщения
        """
        return {"status": "ignored", "reason": "Edited messages not processed"}
    
    async def _handle_command_message(self, event: Event, bot: Bot):
        """
        Обработка команд
        """
        text = event.text.strip()
        command_parts = text.split(' ', 1)
        command = command_parts[0][1:]  # Убираем /
        args = command_parts[1] if len(command_parts) > 1 else ""
        
        chat_id = event.chat.chatId
        user_id = event.from_.userId
        
        try:
            if command == "search":
                await self._handle_search_command(bot, chat_id, user_id, args)
            elif command == "generate":
                await self._handle_generate_command(bot, chat_id, user_id, args)
            elif command == "status":
                await self._handle_status_command(bot, chat_id, user_id)
            elif command == "settings":
                await self._handle_settings_command(bot, chat_id, user_id)
            else:
                await bot.send_text(
                    chat_id=chat_id,
                    text=f"❓ Неизвестная команда: `{command}`\nИспользуйте /help для списка команд.",
                    parse_mode=ParseMode.MARKDOWNV2
                )
                
        except Exception as e:
            logger.error(f"Ошибка команды {command}: {e}")
            await bot.send_text(
                chat_id=chat_id,
                text="😔 Ошибка выполнения команды."
            )
    
    async def _process_ai_request(self, text: str, context: AIAssistantContext) -> Dict[str, Any]:
        """
        Обработка запроса через AI API
        
        Args:
            text: Текст запроса
            context: Контекст пользователя
            
        Returns:
            Ответ от AI
        """
        try:
            # Определяем тип запроса и вызываем соответствующий API
            if any(keyword in text.lower() for keyword in ["найди", "поиск", "ищи", "search"]):
                return await self._call_search_api(text, context)
            elif any(keyword in text.lower() for keyword in ["создай", "генерируй", "generate"]):
                return await self._call_generation_api(text, context)
            elif any(keyword in text.lower() for keyword in ["анализ", "проверь", "analyze"]):
                return await self._call_analysis_api(text, context)
            else:
                # Общий чат с AI
                return await self._call_chat_api(text, context)
                
        except Exception as e:
            logger.error(f"Ошибка AI запроса: {e}")
            return {
                "success": False,
                "error": "Ошибка обработки запроса",
                "message": "Попробуйте переформулировать вопрос или обратитесь позже."
            }
    
    async def _call_search_api(self, query: str, context: AIAssistantContext) -> Dict[str, Any]:
        """
        Вызов API поиска
        """
        try:
            response = await self.api_client.post(
                "/api/v1/search",
                json={
                    "query": query,
                    "limit": 5,
                    "include_snippets": True
                },
                headers={"Authorization": f"Bearer {self._get_internal_token()}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "type": "search_results",
                    "data": data,
                    "message": f"Найдено {len(data.get('results', []))} результатов"
                }
            else:
                return {
                    "success": False,
                    "error": f"Ошибка поиска: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Ошибка вызова search API: {e}")
            return {"success": False, "error": str(e)}
    
    async def _call_generation_api(self, prompt: str, context: AIAssistantContext) -> Dict[str, Any]:
        """
        Вызов API генерации
        """
        try:
            response = await self.api_client.post(
                "/api/v1/generate",
                json={
                    "prompt": prompt,
                    "type": "general",
                    "context": context.user_preferences
                },
                headers={"Authorization": f"Bearer {self._get_internal_token()}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "type": "generated_content",
                    "data": data,
                    "message": "Контент успешно сгенерирован"
                }
            else:
                return {
                    "success": False,
                    "error": f"Ошибка генерации: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Ошибка вызова generation API: {e}")
            return {"success": False, "error": str(e)}
    
    async def _call_analysis_api(self, text: str, context: AIAssistantContext) -> Dict[str, Any]:
        """
        Вызов API анализа
        """
        try:
            response = await self.api_client.post(
                "/api/v1/ai/ai_code_analysis",
                json={
                    "code": text,
                    "analysis_type": "comprehensive"
                },
                headers={"Authorization": f"Bearer {self._get_internal_token()}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "type": "analysis_results",
                    "data": data,
                    "message": "Анализ завершен"
                }
            else:
                return {
                    "success": False,
                    "error": f"Ошибка анализа: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Ошибка вызова analysis API: {e}")
            return {"success": False, "error": str(e)}
    
    async def _call_chat_api(self, message: str, context: AIAssistantContext) -> Dict[str, Any]:
        """
        Вызов chat API
        """
        try:
            # Формируем историю для контекста
            history = [
                {"role": "user" if not msg.is_from_bot else "assistant", "content": msg.text}
                for msg in context.get_recent_messages(10)
                if msg.text
            ]
            
            response = await self.api_client.post(
                "/api/v1/ai/ai_advanced",
                json={
                    "message": message,
                    "history": history,
                    "stream": False
                },
                headers={"Authorization": f"Bearer {self._get_internal_token()}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "type": "chat_response",
                    "data": data,
                    "message": data.get("response", "Ответ получен")
                }
            else:
                return {
                    "success": False,
                    "error": f"Ошибка чата: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Ошибка вызова chat API: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_ai_response(self, bot: Bot, chat_id: str, response: Dict[str, Any]):
        """
        Отправка ответа AI пользователю
        """
        try:
            if not response.get("success"):
                await bot.send_text(
                    chat_id=chat_id,
                    text=f"❌ {response.get('error', 'Произошла ошибка')}"
                )
                return
            
            response_type = response.get("type", "unknown")
            data = response.get("data", {})
            
            if response_type == "search_results":
                await self._send_search_results(bot, chat_id, data)
            elif response_type == "generated_content":
                await self._send_generated_content(bot, chat_id, data)
            elif response_type == "analysis_results":
                await self._send_analysis_results(bot, chat_id, data)
            elif response_type == "chat_response":
                await self._send_chat_response(bot, chat_id, data)
            else:
                await bot.send_text(
                    chat_id=chat_id,
                    text=f"✅ {response.get('message', 'Операция выполнена')}"
                )
                
        except Exception as e:
            logger.error(f"Ошибка отправки ответа: {e}")
            await bot.send_text(
                chat_id=chat_id,
                text="😔 Ошибка отправки ответа."
            )
    
    def _get_or_create_user_context(self, user_id: str, chat_id: str) -> AIAssistantContext:
        """
        Получение или создание контекста пользователя
        """
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = AIAssistantContext(
                user_id=user_id,
                chat_id=chat_id
            )
        return self.user_contexts[user_id]
    
    def _create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """
        Создание основной клавиатуры
        """
        keyboard = InlineKeyboardMarkup(buttons_in_row=2)
        
        keyboard.add(
            KeyboardButton(
                text="🔍 Поиск",
                callback_data="action:search",
                style=StyleKeyboard.PRIMARY
            ),
            KeyboardButton(
                text="📝 Генерация",
                callback_data="action:generate", 
                style=StyleKeyboard.BASE
            ),
            KeyboardButton(
                text="🔧 Анализ",
                callback_data="action:analyze",
                style=StyleKeyboard.ATTENTION
            ),
            KeyboardButton(
                text="ℹ️ Справка",
                callback_data="action:help",
                style=StyleKeyboard.BASE
            )
        )
        
        return keyboard
    
    def _get_internal_token(self) -> str:
        """
        Получение токена для внутренних API вызовов
        """
        # Здесь должна быть логика получения токена для системных вызовов
        # Возможно, из переменных окружения или генерация service token
        return "internal-service-token"
    
    async def _handle_search_command(self, bot: Bot, chat_id: str, user_id: str, query: str):
        """Обработка команды поиска"""
        if not query:
            await bot.send_text(chat_id, "❓ Укажите запрос для поиска: `/search ваш запрос`")
            return
            
        context = self._get_or_create_user_context(user_id, chat_id)
        response = await self._call_search_api(query, context)
        await self._send_ai_response(bot, chat_id, response)
    
    async def _handle_generate_command(self, bot: Bot, chat_id: str, user_id: str, prompt: str):
        """Обработка команды генерации"""
        if not prompt:
            await bot.send_text(chat_id, "❓ Укажите что генерировать: `/generate описание`")
            return
            
        context = self._get_or_create_user_context(user_id, chat_id)
        response = await self._call_generation_api(prompt, context)
        await self._send_ai_response(bot, chat_id, response)
    
    async def _handle_status_command(self, bot: Bot, chat_id: str, user_id: str):
        """Обработка команды статуса"""
        try:
            response = await self.api_client.get(
                "/api/v1/health",
                headers={"Authorization": f"Bearer {self._get_internal_token()}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                status_text = f"🟢 **Система работает**\n\nСтатус: {data.get('status', 'unknown')}"
            else:
                status_text = "🔴 **Система недоступна**"
                
            await bot.send_text(chat_id, status_text, parse_mode=ParseMode.MARKDOWNV2)
            
        except Exception as e:
            await bot.send_text(chat_id, "❌ Ошибка получения статуса")
    
    async def _handle_settings_command(self, bot: Bot, chat_id: str, user_id: str):
        """Обработка команды настроек"""
        context = self._get_or_create_user_context(user_id, chat_id)
        
        settings_text = f"""⚙️ **Настройки пользователя**

**ID пользователя:** `{user_id}`
**ID чата:** `{chat_id}`
**Активная сессия:** {context.active_session or 'Нет'}
**Сообщений в истории:** {len(context.conversation_history)}

Используйте кнопки ниже для настройки:"""

        keyboard = InlineKeyboardMarkup(buttons_in_row=1)
        keyboard.add(
            KeyboardButton("🗑️ Очистить историю", callback_data="settings:clear_history"),
            KeyboardButton("🔄 Новая сессия", callback_data="settings:new_session"),
            KeyboardButton("📊 Статистика", callback_data="settings:stats")
        )
        
        await bot.send_text(
            chat_id, 
            settings_text, 
            parse_mode=ParseMode.MARKDOWNV2,
            inline_keyboard_markup=keyboard
        )
    
    async def _process_callback_action(self, callback_data: str, chat_id: str, user_id: str):
        """Обработка callback действий"""
        # Здесь будет логика обработки нажатий на кнопки
        logger.info(f"Processing callback: {callback_data} for user {user_id}")
    
    async def _send_search_results(self, bot: Bot, chat_id: str, data: Dict[str, Any]):
        """Отправка результатов поиска"""
        results = data.get("results", [])
        if not results:
            await bot.send_text(chat_id, "🔍 Результаты не найдены")
            return
            
        text = "🔍 **Результаты поиска:**\n\n"
        for i, result in enumerate(results[:5], 1):
            title = result.get("title", "Без названия")
            score = result.get("score", 0)
            text += f"{i}. **{title}** (релевантность: {score:.2f})\n"
            
        await bot.send_text(chat_id, text, parse_mode=ParseMode.MARKDOWNV2)
    
    async def _send_generated_content(self, bot: Bot, chat_id: str, data: Dict[str, Any]):
        """Отправка сгенерированного контента"""
        content = data.get("content", "Контент не сгенерирован")
        await bot.send_text(chat_id, f"📝 **Сгенерированный контент:**\n\n{content}")
    
    async def _send_analysis_results(self, bot: Bot, chat_id: str, data: Dict[str, Any]):
        """Отправка результатов анализа"""
        analysis = data.get("analysis", "Анализ не выполнен")
        await bot.send_text(chat_id, f"🔧 **Результаты анализа:**\n\n{analysis}")
    
    async def _send_chat_response(self, bot: Bot, chat_id: str, data: Dict[str, Any]):
        """Отправка ответа чата"""
        response = data.get("response", "Ответ не получен")
        await bot.send_text(chat_id, response)
    
    async def _check_vk_user_access(self, user_id: str) -> bool:
        """
        Проверка доступа VK пользователя через VK OAuth API
        
        Args:
            user_id: ID пользователя VK Teams
            
        Returns:
            True если доступ разрешен, False если нет
        """
        try:
            # Проверяем кэш сначала
            cache_key = f"vk_access_{user_id}"
            if cache_key in self._user_cache:
                cache_data = self._user_cache[cache_key]
                # Проверяем что кэш не устарел (5 минут)
                if time.time() - cache_data.get("timestamp", 0) < 300:
                    return cache_data.get("has_access", False)
            
            # Вызываем VK OAuth API для проверки доступа
            response = await self.api_client.get(
                f"/api/v1/auth/vk/check-access/{user_id}",
                headers={"Authorization": f"Bearer {self._get_internal_token()}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                has_access = data.get("has_access", False)
                
                # Кэшируем результат
                self._user_cache[cache_key] = {
                    "has_access": has_access,
                    "timestamp": time.time()
                }
                
                logger.info(f"VK user {user_id} access check: {has_access}")
                return has_access
            else:
                logger.warning(f"VK access check failed for user {user_id}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking VK user access for {user_id}: {e}")
            return False
    
    async def _send_access_denied_message(self, bot: Bot, chat_id: str, user_id: str):
        """
        Отправка сообщения об отказе в доступе
        
        Args:
            bot: Экземпляр бота
            chat_id: ID чата
            user_id: ID пользователя
        """
        try:
            access_denied_text = """🚫 **Доступ ограничен**

К сожалению, ваш аккаунт VK не авторизован для использования этого AI-ассистента.

**Что можно сделать:**
1. Обратитесь к администратору для получения доступа
2. Убедитесь, что вы авторизованы через VK OAuth
3. Проверьте, что ваш VK ID добавлен в список разрешенных пользователей

**Для получения доступа:**
• Свяжитесь с администратором системы
• Предоставьте ваш VK ID: `{user_id}`

Извините за неудобства! 🙏"""
            
            await bot.send_text(
                chat_id=chat_id,
                text=access_denied_text.format(user_id=user_id),
                parse_mode=ParseMode.MARKDOWNV2
            )
            
            # Записываем в статистику отказов
            if self.stats:
                self.stats.record_error("access_denied", f"VK user {user_id} denied access", {
                    "user_id": user_id,
                    "chat_id": chat_id
                })
            
        except Exception as e:
            logger.error(f"Error sending access denied message: {e}")
            # Fallback простое сообщение
            await bot.send_text(
                chat_id=chat_id,
                text="🚫 Доступ запрещен. Обратитесь к администратору."
            )


# Глобальный экземпляр адаптера
_bot_adapter: Optional[VKTeamsBotAdapter] = None


async def get_vk_teams_bot_adapter() -> VKTeamsBotAdapter:
    """
    Получение экземпляра VK Teams Bot Adapter
    
    Returns:
        Экземпляр VKTeamsBotAdapter
    """
    global _bot_adapter
    
    if _bot_adapter is None:
        _bot_adapter = VKTeamsBotAdapter()
        
        # Инициализируем статистику
        from domain.vk_teams.bot_service import get_vk_teams_bot_service
        bot_service = await get_vk_teams_bot_service()
        _bot_adapter.stats = bot_service.stats
    
    return _bot_adapter 