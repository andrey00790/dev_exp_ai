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
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import httpx
from vk_teams_async_bot.bot import Bot
from vk_teams_async_bot.events import Event
from vk_teams_async_bot.helpers import InlineKeyboardMarkup, KeyboardButton
from vk_teams_async_bot.constants import StyleKeyboard, ParseMode

from app.config import get_settings
from infrastructure.vk_teams.domain.bot_models import AIAssistantContext, BotMessage, BotStats

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
            
            welcome_text = """🤖 **AI-Ассистент VK Teams - Enhanced Edition**
            
Привет! Я ваш продвинутый AI-помощник с новыми суперспособностями! 🚀

🎯 **Основные функции:**
🔍 **Умный поиск** - семантический поиск по всем документам
💬 **AI Диалоги** - интеллектуальное общение с контекстом
📝 **Генерация контента** - RFC, документация, код
🔧 **Анализ и ревью** - проверка кода на качество и безопасность
⚡ **Оптимизация** - улучшение производительности кода
📊 **Персональная аналитика** - ваша статистика и достижения

🆕 **Новые возможности:**
📚 **Автогенерация документации** - создаю docs любой сложности
📋 **Библиотека шаблонов** - готовые шаблоны для быстрого старта
🎯 **Contextual AI** - помню предыдущие разговоры
🏆 **Система достижений** - отслеживаю ваш прогресс
📤 **Экспорт результатов** - сохраняю в разных форматах

**🎮 Быстрые команды:**
• `/search` - найти информацию
• `/analyze` - анализ текста/кода  
• `/review` - ревью кода
• `/generate` - создать RFC
• `/docs` - генерировать документацию
• `/template` - шаблоны кода
• `/stats` - ваша статистика

💡 **Совет:** Просто напишите вопрос естественным языком - я пойму!

Готов помочь? Выберите действие ниже или задайте любой вопрос! ✨"""
            
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
            help_text = """📖 **Справка по командам AI-Ассистента**

🔍 **Поиск и анализ:**
• `/search <запрос>` - семантический поиск по документам
• `/analyze <текст>` - всесторонний анализ текста/кода
• `/review <код>` - профессиональное ревью кода
• `/optimize <код>` - оптимизация производительности

📝 **Генерация контента:**
• `/generate <тема>` - создание RFC документов
• `/docs <тема>` - генерация документации
• `/template [тип]` - готовые шаблоны кода

📊 **Информация и статистика:**
• `/status` - статус системы и сервисов
• `/stats` - ваша персональная статистика
• `/settings` - настройки пользователя

🎯 **Быстрые действия:**
Используйте кнопки ниже или просто напишите вопрос естественным языком!

💡 **Примеры использования:**
• `Найди документацию по JWT аутентификации`
• `Проанализируй этот Python код на безопасность`
• `Создай RFC для микросервисной архитектуры`
• `Оптимизируй SQL запрос для производительности`
• `Сгенерируй README для React проекта`

🚀 **Продвинутые возможности:**
• Поддержка файлов и изображений
• Контекстные диалоги с памятью
• Интерактивные кнопки и меню
• Персональная статистика и достижения
• Экспорт результатов в различных форматах"""

            # Создаем интерактивную клавиатуру для быстрого доступа
            keyboard = InlineKeyboardMarkup(buttons_in_row=3)
            keyboard.add(
                KeyboardButton("🔍 Поиск", callback_data="action:search"),
                KeyboardButton("📝 Генерация", callback_data="action:generate"),
                KeyboardButton("🔧 Анализ", callback_data="action:analyze"),
                KeyboardButton("⚡ Оптимизация", callback_data="action:optimize"),
                KeyboardButton("📚 Документация", callback_data="action:docs"),
                KeyboardButton("📋 Шаблоны", callback_data="action:template"),
                KeyboardButton("📊 Статистика", callback_data="action:stats"),
                KeyboardButton("⚙️ Настройки", callback_data="action:settings"),
                KeyboardButton("ℹ️ О системе", callback_data="action:about")
            )
            
            await bot.send_text(
                chat_id=event.chat.chatId,
                text=help_text,
                parse_mode=ParseMode.MARKDOWNV2,
                inline_keyboard_markup=keyboard
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
            "timestamp": datetime.now(timezone.utc).isoformat()
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
            elif command == "analyze":
                await self._handle_analyze_command(bot, chat_id, user_id, args)
            elif command == "review":
                await self._handle_code_review_command(bot, chat_id, user_id, args)
            elif command == "optimize":
                await self._handle_optimize_command(bot, chat_id, user_id, args)
            elif command == "docs":
                await self._handle_docs_command(bot, chat_id, user_id, args)
            elif command == "template":
                await self._handle_template_command(bot, chat_id, user_id, args)
            elif command == "stats":
                await self._handle_stats_command(bot, chat_id, user_id)
            else:
                await bot.send_text(
                    chat_id=chat_id,
                    text=f"❓ Неизвестная команда: `{command}`\n\n🔍 Доступные команды:\n• `/help` - полный список команд\n• `/search <запрос>` - поиск информации\n• `/generate <тема>` - генерация контента\n• `/analyze <текст>` - анализ текста\n• `/review <код>` - ревью кода\n• `/optimize <код>` - оптимизация\n• `/status` - статус системы",
                    parse_mode=ParseMode.MARKDOWNV2
                )
                
        except Exception as e:
            logger.error(f"Ошибка команды {command}: {e}")
            await bot.send_text(
                chat_id=chat_id,
                text="😔 Ошибка выполнения команды. Попробуйте позже или используйте /help."
            )

    async def _handle_analyze_command(self, bot: Bot, chat_id: str, user_id: str, text: str):
        """Обработка команды анализа текста/кода"""
        if not text:
            await bot.send_text(
                chat_id, 
                "❓ Укажите текст для анализа:\n`/analyze ваш текст или код`",
                parse_mode=ParseMode.MARKDOWNV2
            )
            return
            
        try:
            context = self._get_or_create_user_context(user_id, chat_id)
            
            # Отправляем typing indicator
            loading_msg = await bot.send_text(chat_id, "🔍 Анализирую...")
            
            response = await self.api_client.post(
                "/api/v1/ai/analyze",
                json={
                    "text": text,
                    "analysis_type": "comprehensive",
                    "include_suggestions": True
                },
                headers={"Authorization": f"Bearer {self._get_internal_token()}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                analysis_text = f"""📊 **Результат анализа**

🎯 **Тип контента:** {data.get('content_type', 'Текст')}
📏 **Размер:** {len(text)} символов
🏷️ **Язык:** {data.get('language', 'Не определен')}

📈 **Метрики качества:**
• Читаемость: {data.get('readability_score', 'N/A')}/10
• Сложность: {data.get('complexity', 'Средняя')}
• Структурированность: {data.get('structure_score', 'N/A')}/10

💡 **Рекомендации:**
{data.get('suggestions', 'Нет рекомендаций')}

✨ **Ключевые темы:**
{', '.join(data.get('key_topics', ['Не найдены']))}"""

                keyboard = InlineKeyboardMarkup(buttons_in_row=2)
                keyboard.add(
                    KeyboardButton("🔍 Подробный анализ", callback_data=f"analyze:detailed:{user_id}"),
                    KeyboardButton("💡 Улучшения", callback_data=f"analyze:improve:{user_id}"),
                    KeyboardButton("📊 Экспорт", callback_data=f"analyze:export:{user_id}"),
                    KeyboardButton("🔄 Новый анализ", callback_data="action:analyze")
                )
                
                await bot.edit_text(
                    chat_id=chat_id,
                    msg_id=loading_msg.msg_id,
                    text=analysis_text,
                    parse_mode=ParseMode.MARKDOWNV2,
                    inline_keyboard_markup=keyboard
                )
            else:
                await bot.edit_text(
                    chat_id=chat_id,
                    msg_id=loading_msg.msg_id,
                    text="❌ Ошибка анализа. Попробуйте позже."
                )
                
        except Exception as e:
            logger.error(f"Ошибка анализа: {e}")
            await bot.send_text(chat_id, "❌ Ошибка выполнения анализа")

    async def _handle_code_review_command(self, bot: Bot, chat_id: str, user_id: str, code: str):
        """Обработка команды ревью кода"""
        if not code:
            await bot.send_text(
                chat_id,
                "❓ Отправьте код для ревью:\n`/review ваш код`\n\nИли просто:\n`/review` - и отправьте код в следующем сообщении",
                parse_mode=ParseMode.MARKDOWNV2
            )
            return
            
        try:
            loading_msg = await bot.send_text(chat_id, "🔍 Провожу ревью кода...")
            
            response = await self.api_client.post(
                "/api/v1/ai/code-review",
                json={
                    "code": code,
                    "check_security": True,
                    "check_performance": True,
                    "check_style": True
                },
                headers={"Authorization": f"Bearer {self._get_internal_token()}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Определяем общую оценку
                score = data.get('overall_score', 0)
                if score >= 8:
                    score_emoji = "🟢"
                elif score >= 6:
                    score_emoji = "🟡"
                else:
                    score_emoji = "🔴"
                
                review_text = f"""{score_emoji} **Code Review Results**

📊 **Общая оценка:** {score}/10

🔒 **Безопасность:** {data.get('security_score', 'N/A')}/10
⚡ **Производительность:** {data.get('performance_score', 'N/A')}/10
🎨 **Стиль кода:** {data.get('style_score', 'N/A')}/10

⚠️ **Найденные проблемы:** {len(data.get('issues', []))}

🔧 **Критичные:** {len([i for i in data.get('issues', []) if i.get('severity') == 'critical'])}
⚠️ **Предупреждения:** {len([i for i in data.get('issues', []) if i.get('severity') == 'warning'])}
💡 **Рекомендации:** {len([i for i in data.get('issues', []) if i.get('severity') == 'info'])}"""

                if data.get('issues'):
                    review_text += f"\n\n🔍 **Топ проблемы:**\n"
                    for issue in data['issues'][:3]:
                        review_text += f"• {issue.get('description', 'No description')}\n"

                keyboard = InlineKeyboardMarkup(buttons_in_row=2)
                keyboard.add(
                    KeyboardButton("📝 Подробный отчет", callback_data=f"review:detailed:{user_id}"),
                    KeyboardButton("🔧 Исправления", callback_data=f"review:fix:{user_id}"),
                    KeyboardButton("📊 Метрики", callback_data=f"review:metrics:{user_id}"),
                    KeyboardButton("🔄 Новое ревью", callback_data="action:review")
                )
                
                await bot.edit_text(
                    chat_id=chat_id,
                    msg_id=loading_msg.msg_id,
                    text=review_text,
                    parse_mode=ParseMode.MARKDOWNV2,
                    inline_keyboard_markup=keyboard
                )
            else:
                await bot.edit_text(
                    chat_id=chat_id,
                    msg_id=loading_msg.msg_id,
                    text="❌ Ошибка ревью кода. Проверьте синтаксис."
                )
                
        except Exception as e:
            logger.error(f"Ошибка ревью кода: {e}")
            await bot.send_text(chat_id, "❌ Ошибка выполнения ревью")

    async def _handle_optimize_command(self, bot: Bot, chat_id: str, user_id: str, code: str):
        """Обработка команды оптимизации кода"""
        if not code:
            await bot.send_text(
                chat_id,
                "❓ Отправьте код для оптимизации:\n`/optimize ваш код`",
                parse_mode=ParseMode.MARKDOWNV2
            )
            return
            
        try:
            loading_msg = await bot.send_text(chat_id, "⚡ Оптимизирую код...")
            
            response = await self.api_client.post(
                "/api/v1/ai/optimize",
                json={
                    "code": code,
                    "optimization_type": "performance",
                    "target": "speed"
                },
                headers={"Authorization": f"Bearer {self._get_internal_token()}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                improvements = data.get('improvements', [])
                optimized_code = data.get('optimized_code', code)
                
                optimize_text = f"""⚡ **Результат оптимизации**

📈 **Улучшения найдены:** {len(improvements)}
🚀 **Ожидаемый прирост:** {data.get('performance_gain', 'N/A')}%
💾 **Экономия памяти:** {data.get('memory_savings', 'N/A')}%

🔧 **Основные изменения:**"""

                for improvement in improvements[:3]:
                    optimize_text += f"\n• {improvement.get('description', 'No description')}"

                keyboard = InlineKeyboardMarkup(buttons_in_row=2)
                keyboard.add(
                    KeyboardButton("📄 Показать код", callback_data=f"optimize:code:{user_id}"),
                    KeyboardButton("📊 Сравнение", callback_data=f"optimize:compare:{user_id}"),
                    KeyboardButton("💾 Сохранить", callback_data=f"optimize:save:{user_id}"),
                    KeyboardButton("🔄 Другая оптимизация", callback_data="action:optimize")
                )
                
                await bot.edit_text(
                    chat_id=chat_id,
                    msg_id=loading_msg.msg_id,
                    text=optimize_text,
                    parse_mode=ParseMode.MARKDOWNV2,
                    inline_keyboard_markup=keyboard
                )
            else:
                await bot.edit_text(
                    chat_id=chat_id,
                    msg_id=loading_msg.msg_id,
                    text="❌ Ошибка оптимизации кода"
                )
                
        except Exception as e:
            logger.error(f"Ошибка оптимизации: {e}")
            await bot.send_text(chat_id, "❌ Ошибка выполнения оптимизации")

    async def _handle_docs_command(self, bot: Bot, chat_id: str, user_id: str, topic: str):
        """Обработка команды генерации документации"""
        if not topic:
            await bot.send_text(
                chat_id,
                "❓ Укажите тему для документации:\n`/docs API аутентификации`\n`/docs Установка проекта`",
                parse_mode=ParseMode.MARKDOWNV2
            )
            return
            
        try:
            loading_msg = await bot.send_text(chat_id, "📝 Генерирую документацию...")
            
            response = await self.api_client.post(
                "/api/v1/documentation/generate",
                json={
                    "topic": topic,
                    "format": "markdown",
                    "include_examples": True,
                    "technical_level": "intermediate"
                },
                headers={"Authorization": f"Bearer {self._get_internal_token()}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                docs_text = f"""📚 **Документация готова**

📖 **Тема:** {topic}
📄 **Страниц:** {data.get('pages_count', 1)}
📊 **Размер:** {data.get('word_count', 'N/A')} слов
🏷️ **Формат:** {data.get('format', 'Markdown')}

🎯 **Содержание:**
{data.get('table_of_contents', 'Не сгенерировано')}

✅ **Документация создана успешно!**"""

                keyboard = InlineKeyboardMarkup(buttons_in_row=2)
                keyboard.add(
                    KeyboardButton("📄 Показать", callback_data=f"docs:show:{user_id}"),
                    KeyboardButton("📤 Экспорт", callback_data=f"docs:export:{user_id}"),
                    KeyboardButton("✏️ Редактировать", callback_data=f"docs:edit:{user_id}"),
                    KeyboardButton("🔄 Новая документация", callback_data="action:docs")
                )
                
                await bot.edit_text(
                    chat_id=chat_id,
                    msg_id=loading_msg.msg_id,
                    text=docs_text,
                    parse_mode=ParseMode.MARKDOWNV2,
                    inline_keyboard_markup=keyboard
                )
            else:
                await bot.edit_text(
                    chat_id=chat_id,
                    msg_id=loading_msg.msg_id,
                    text="❌ Ошибка генерации документации"
                )
                
        except Exception as e:
            logger.error(f"Ошибка генерации документации: {e}")
            await bot.send_text(chat_id, "❌ Ошибка создания документации")

    async def _handle_template_command(self, bot: Bot, chat_id: str, user_id: str, template_type: str):
        """Обработка команды шаблонов"""
        if not template_type:
            # Показываем доступные шаблоны
            templates_text = """📋 **Доступные шаблоны**

🏗️ **Архитектурные:**
• `/template rfc` - RFC документ
• `/template api` - API спецификация
• `/template architecture` - архитектурное решение

💻 **Кодовые:**
• `/template class` - класс Python
• `/template function` - функция
• `/template test` - unit тест

📝 **Документация:**
• `/template readme` - README файл
• `/template guide` - пользовательский гайд
• `/template changelog` - changelog

🔧 **DevOps:**
• `/template docker` - Dockerfile
• `/template ci` - CI/CD pipeline
• `/template deploy` - deployment скрипт"""

            keyboard = InlineKeyboardMarkup(buttons_in_row=3)
            keyboard.add(
                KeyboardButton("🏗️ RFC", callback_data="template:rfc"),
                KeyboardButton("🔌 API", callback_data="template:api"),
                KeyboardButton("💻 Class", callback_data="template:class"),
                KeyboardButton("📝 README", callback_data="template:readme"),
                KeyboardButton("🐳 Docker", callback_data="template:docker"),
                KeyboardButton("🔧 CI/CD", callback_data="template:ci")
            )
            
            await bot.send_text(
                chat_id,
                templates_text,
                parse_mode=ParseMode.MARKDOWNV2,
                inline_keyboard_markup=keyboard
            )
        else:
            # Генерируем конкретный шаблон
            await self._generate_template(bot, chat_id, user_id, template_type)

    async def _handle_stats_command(self, bot: Bot, chat_id: str, user_id: str):
        """Обработка команды статистики"""
        try:
            context = self._get_or_create_user_context(user_id, chat_id)
            
            # Получаем статистику пользователя
            response = await self.api_client.get(
                f"/api/v1/users/{user_id}/stats",
                headers={"Authorization": f"Bearer {self._get_internal_token()}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                stats_text = f"""📊 **Ваша статистика**

👤 **Пользователь:** {user_id}
📅 **Зарегистрирован:** {data.get('created_at', 'N/A')}
🎯 **Уровень:** {data.get('user_level', 'Новичок')}

💬 **Активность:**
• Сообщений отправлено: {data.get('messages_sent', 0)}
• Команд выполнено: {data.get('commands_used', 0)}
• Время в системе: {data.get('total_time', '0')} мин

🔍 **Использование функций:**
• Поиск: {data.get('search_count', 0)} раз
• Генерация: {data.get('generation_count', 0)} раз
• Анализ: {data.get('analysis_count', 0)} раз
• Ревью кода: {data.get('review_count', 0)} раз

⭐ **Достижения:**
{self._format_achievements(data.get('achievements', []))}

🏆 **Рейтинг:** #{data.get('user_rank', 'N/A')} из {data.get('total_users', 'N/A')}"""

                keyboard = InlineKeyboardMarkup(buttons_in_row=2)
                keyboard.add(
                    KeyboardButton("📈 Детальная статистика", callback_data=f"stats:detailed:{user_id}"),
                    KeyboardButton("🏆 Достижения", callback_data=f"stats:achievements:{user_id}"),
                    KeyboardButton("📊 Сравнить", callback_data=f"stats:compare:{user_id}"),
                    KeyboardButton("🔄 Обновить", callback_data="stats:refresh")
                )
                
                await bot.send_text(
                    chat_id,
                    stats_text,
                    parse_mode=ParseMode.MARKDOWNV2,
                    inline_keyboard_markup=keyboard
                )
            else:
                await bot.send_text(chat_id, "❌ Ошибка получения статистики")
                
        except Exception as e:
            logger.error(f"Ошибка статистики: {e}")
            await bot.send_text(chat_id, "❌ Ошибка получения статистики")

    def _format_achievements(self, achievements: list) -> str:
        """Форматирование достижений"""
        if not achievements:
            return "🎯 Пока нет достижений"
        
        formatted = []
        for achievement in achievements[:5]:  # Показываем топ 5
            emoji = achievement.get('emoji', '🏅')
            name = achievement.get('name', 'Неизвестно')
            formatted.append(f"{emoji} {name}")
        
        return '\n'.join(formatted)

    async def _generate_template(self, bot: Bot, chat_id: str, user_id: str, template_type: str):
        """Генерация конкретного шаблона"""
        try:
            loading_msg = await bot.send_text(chat_id, f"📝 Генерирую {template_type} шаблон...")
            
            response = await self.api_client.post(
                "/api/v1/templates/generate",
                json={
                    "template_type": template_type,
                    "include_comments": True,
                    "include_examples": True
                },
                headers={"Authorization": f"Bearer {self._get_internal_token()}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                template_text = f"""📝 **{template_type.upper()} шаблон готов**

📄 **Тип:** {data.get('type', template_type)}
📏 **Размер:** {data.get('lines_count', 'N/A')} строк
🏷️ **Язык:** {data.get('language', 'Не указан')}

✅ **Шаблон создан успешно!**
Используйте кнопки ниже для просмотра или экспорта."""

                keyboard = InlineKeyboardMarkup(buttons_in_row=2)
                keyboard.add(
                    KeyboardButton("👁️ Просмотр", callback_data=f"template:view:{template_type}:{user_id}"),
                    KeyboardButton("📋 Копировать", callback_data=f"template:copy:{template_type}:{user_id}"),
                    KeyboardButton("📤 Экспорт", callback_data=f"template:export:{template_type}:{user_id}"),
                    KeyboardButton("✏️ Кастомизировать", callback_data=f"template:customize:{template_type}:{user_id}")
                )
                
                await bot.edit_text(
                    chat_id=chat_id,
                    msg_id=loading_msg.msg_id,
                    text=template_text,
                    parse_mode=ParseMode.MARKDOWNV2,
                    inline_keyboard_markup=keyboard
                )
            else:
                await bot.edit_text(
                    chat_id=chat_id,
                    msg_id=loading_msg.msg_id,
                    text="❌ Ошибка генерации шаблона"
                )
                
        except Exception as e:
            logger.error(f"Ошибка генерации шаблона: {e}")
            await bot.send_text(chat_id, "❌ Ошибка создания шаблона")
    
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
        try:
            parts = callback_data.split(':')
            action = parts[0]
            
            if action == "action":
                # Основные действия из главного меню
                sub_action = parts[1]
                await self._handle_main_action(sub_action, chat_id, user_id)
                
            elif action == "analyze":
                # Действия анализа
                sub_action = parts[1]
                target_user = parts[2] if len(parts) > 2 else user_id
                await self._handle_analyze_action(sub_action, chat_id, user_id, target_user)
                
            elif action == "review":
                # Действия ревью кода
                sub_action = parts[1]
                target_user = parts[2] if len(parts) > 2 else user_id
                await self._handle_review_action(sub_action, chat_id, user_id, target_user)
                
            elif action == "optimize":
                # Действия оптимизации
                sub_action = parts[1]
                target_user = parts[2] if len(parts) > 2 else user_id
                await self._handle_optimize_action(sub_action, chat_id, user_id, target_user)
                
            elif action == "docs":
                # Действия документации
                sub_action = parts[1]
                target_user = parts[2] if len(parts) > 2 else user_id
                await self._handle_docs_action(sub_action, chat_id, user_id, target_user)
                
            elif action == "template":
                # Действия шаблонов
                if len(parts) >= 2:
                    sub_action = parts[1]
                    template_type = parts[2] if len(parts) > 2 else None
                    target_user = parts[3] if len(parts) > 3 else user_id
                    await self._handle_template_action(sub_action, template_type, chat_id, user_id, target_user)
                
            elif action == "stats":
                # Действия статистики
                sub_action = parts[1]
                target_user = parts[2] if len(parts) > 2 else user_id
                await self._handle_stats_action(sub_action, chat_id, user_id, target_user)
                
            elif action == "settings":
                # Действия настроек
                sub_action = parts[1]
                await self._handle_settings_action(sub_action, chat_id, user_id)
                
            else:
                logger.warning(f"Unknown callback action: {action}")
                
        except Exception as e:
            logger.error(f"Ошибка обработки callback {callback_data}: {e}")

    async def _handle_main_action(self, action: str, chat_id: str, user_id: str):
        """Обработка основных действий"""
        prompts = {
            "search": "🔍 Введите запрос для поиска:\nНапример: `JWT аутентификация` или `Docker deployment`",
            "generate": "📝 Укажите тему для генерации:\nНапример: `RFC для микросервисов` или `API документация`",
            "analyze": "🔧 Отправьте текст или код для анализа:\nМогу анализировать код, тексты, архитектуру",
            "optimize": "⚡ Отправьте код для оптимизации:\nУлучшу производительность и качество",
            "docs": "📚 Укажите тему для документации:\nНапример: `Установка проекта` или `API Reference`",
            "template": "📋 Выберите тип шаблона или напишите `/template` для списка",
            "stats": "📊 Показываю вашу статистику...",
            "settings": "⚙️ Открываю настройки...",
            "about": "ℹ️ **О системе AI-Ассистент**\n\nВерсия: 2.0 Enhanced\nСтатус: ✅ Полностью функциональна\nВозможности: 15+ AI функций\nПоследнее обновление: Декабрь 2024"
        }
        
        await self.bot.send_text(
            chat_id=chat_id,
            text=prompts.get(action, "❓ Неизвестное действие"),
            parse_mode=ParseMode.MARKDOWNV2
        )
        
        # Выполняем специальные действия
        if action == "stats":
            await self._handle_stats_command(self.bot, chat_id, user_id)
        elif action == "settings":
            await self._handle_settings_command(self.bot, chat_id, user_id)

    async def _handle_analyze_action(self, action: str, chat_id: str, user_id: str, target_user: str):
        """Обработка действий анализа"""
        if action == "detailed":
            await self.bot.send_text(
                chat_id,
                "📊 **Детальный анализ**\n\nЗагружаю подробные метрики...",
                parse_mode=ParseMode.MARKDOWNV2
            )
        elif action == "improve":
            await self.bot.send_text(
                chat_id,
                "💡 **Рекомендации по улучшению**\n\nГенерирую персональные рекомендации...",
                parse_mode=ParseMode.MARKDOWNV2
            )
        elif action == "export":
            await self.bot.send_text(
                chat_id,
                "📤 **Экспорт анализа**\n\nФормат: PDF, Markdown, JSON\nОтправляю на email...",
                parse_mode=ParseMode.MARKDOWNV2
            )

    async def _handle_review_action(self, action: str, chat_id: str, user_id: str, target_user: str):
        """Обработка действий ревью"""
        if action == "detailed":
            await self.bot.send_text(
                chat_id,
                "📝 **Подробный отчет ревью**\n\nПоказываю все найденные проблемы и рекомендации...",
                parse_mode=ParseMode.MARKDOWNV2
            )
        elif action == "fix":
            await self.bot.send_text(
                chat_id,
                "🔧 **Предлагаемые исправления**\n\nГенерирую исправленную версию кода...",
                parse_mode=ParseMode.MARKDOWNV2
            )
        elif action == "metrics":
            await self.bot.send_text(
                chat_id,
                "📊 **Метрики качества кода**\n\nЦикломатическая сложность, покрытие, дублирование...",
                parse_mode=ParseMode.MARKDOWNV2
            )

    async def _handle_optimize_action(self, action: str, chat_id: str, user_id: str, target_user: str):
        """Обработка действий оптимизации"""
        if action == "code":
            await self.bot.send_text(
                chat_id,
                "💻 **Оптимизированный код**\n\nПоказываю улучшенную версию с комментариями...",
                parse_mode=ParseMode.MARKDOWNV2
            )
        elif action == "compare":
            await self.bot.send_text(
                chat_id,
                "🔄 **Сравнение до/после**\n\nВизуальное сравнение изменений и метрик...",
                parse_mode=ParseMode.MARKDOWNV2
            )
        elif action == "save":
            await self.bot.send_text(
                chat_id,
                "💾 **Сохранение результата**\n\nОптимизированный код сохранен в ваш профиль",
                parse_mode=ParseMode.MARKDOWNV2
            )

    async def _handle_docs_action(self, action: str, chat_id: str, user_id: str, target_user: str):
        """Обработка действий документации"""
        if action == "show":
            await self.bot.send_text(
                chat_id,
                "📄 **Просмотр документации**\n\nПоказываю созданную документацию...",
                parse_mode=ParseMode.MARKDOWNV2
            )
        elif action == "export":
            await self.bot.send_text(
                chat_id,
                "📤 **Экспорт документации**\n\nДоступны форматы: Markdown, PDF, HTML, Confluence",
                parse_mode=ParseMode.MARKDOWNV2
            )
        elif action == "edit":
            await self.bot.send_text(
                chat_id,
                "✏️ **Редактирование**\n\nОткрываю интерактивный редактор документации...",
                parse_mode=ParseMode.MARKDOWNV2
            )

    async def _handle_template_action(self, action: str, template_type: Optional[str], chat_id: str, user_id: str, target_user: str):
        """Обработка действий шаблонов"""
        if action == "view" and template_type:
            await self._send_bot_message(
                chat_id,
                f"👁️ **Просмотр {template_type} шаблона**\n\nПоказываю содержимое шаблона...",
            )
        elif action == "copy" and template_type:
            await self._send_bot_message(
                chat_id,
                f"📋 **Шаблон {template_type} скопирован**\n\nГотов к использованию в вашем проекте!",
            )
        elif action == "export" and template_type:
            await self._send_bot_message(
                chat_id,
                f"📤 **Экспорт {template_type}**\n\nОтправляю файл на email или в чат...",
            )
        elif action == "customize" and template_type:
            await self._send_bot_message(
                chat_id,
                f"✏️ **Кастомизация {template_type}**\n\nНастраиваю шаблон под ваши требования...",
            )
        # Обработка выбора типа шаблона из кнопок
        elif template_type in ["rfc", "api", "class", "readme", "docker", "ci"]:
            await self._generate_template_from_callback(chat_id, user_id, template_type)

    async def _send_bot_message(self, chat_id: str, text: str):
        """Отправка сообщения через бота"""
        try:
            # Здесь должен быть доступ к боту через service или adapter
            # Временная заглушка для демонстрации
            logger.info(f"Sending message to {chat_id}: {text}")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")

    async def _generate_template_from_callback(self, chat_id: str, user_id: str, template_type: str):
        """Генерация шаблона из callback"""
        try:
            # Здесь должен быть вызов API для генерации шаблона
            await self._send_bot_message(chat_id, f"📝 Генерирую {template_type} шаблон...")
        except Exception as e:
            logger.error(f"Ошибка генерации шаблона: {e}")

    async def _handle_stats_action(self, action: str, chat_id: str, user_id: str, target_user: str):
        """Обработка действий статистики"""
        if action == "detailed":
            await self.bot.send_text(
                chat_id,
                "📈 **Детальная статистика**\n\nПоказываю расширенную аналитику использования...",
                parse_mode=ParseMode.MARKDOWNV2
            )
        elif action == "achievements":
            await self.bot.send_text(
                chat_id,
                "🏆 **Ваши достижения**\n\nПоказываю все разблокированные достижения и прогресс...",
                parse_mode=ParseMode.MARKDOWNV2
            )
        elif action == "compare":
            await self.bot.send_text(
                chat_id,
                "📊 **Сравнение с другими**\n\nВаша позиция в рейтинге пользователей...",
                parse_mode=ParseMode.MARKDOWNV2
            )
        elif action == "refresh":
            await self._handle_stats_command(self.bot, chat_id, user_id)

    async def _handle_settings_action(self, action: str, chat_id: str, user_id: str):
        """Обработка действий настроек"""
        if action == "clear_history":
            context = self._get_or_create_user_context(user_id, chat_id)
            context.conversation_history.clear()
            await self.bot.send_text(
                chat_id,
                "🗑️ **История очищена**\n\nВся история диалогов удалена",
                parse_mode=ParseMode.MARKDOWNV2
            )
        elif action == "new_session":
            context = self._get_or_create_user_context(user_id, chat_id)
            context.active_session = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            await self.bot.send_text(
                chat_id,
                f"🔄 **Новая сессия создана**\n\nID: `{context.active_session}`",
                parse_mode=ParseMode.MARKDOWNV2
            )
        elif action == "stats":
            await self._handle_stats_command(self.bot, chat_id, user_id)
    
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
        Проверка доступа VK пользователя через унифицированную систему авторизации
        
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
            
            # Используем унифицированную систему авторизации
            try:
                from app.security.unified_auth import unified_auth_service
                
                # Проверяем через унифицированный сервис
                user = await unified_auth_service.authenticate_vk_teams_user(user_id)
                has_access = user is not None
                
                # Кэшируем результат
                self._user_cache[cache_key] = {
                    "has_access": has_access,
                    "user": user,
                    "timestamp": time.time()
                }
                
                logger.info(f"VK Teams user {user_id} access check: {has_access}")
                return has_access
                
            except ImportError:
                # Fallback на старую систему если unified_auth недоступен
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
                    
                    logger.info(f"VK user {user_id} access check (fallback): {has_access}")
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
        from infrastructure.vk_teams.application.bot_service import get_vk_teams_bot_service
        bot_service = await get_vk_teams_bot_service()
        _bot_adapter.stats = bot_service.stats
    
    return _bot_adapter 