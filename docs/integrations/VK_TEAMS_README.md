# 🤖 VK Teams Bot Integration

Интеграция AI-ассистента с VK Teams для взаимодействия через чат-бота.

## ✨ Возможности

- 🔍 **Семантический поиск** - поиск информации по документам
- 📝 **Генерация RFC** - создание технических документов
- 🔧 **Анализ кода** - проверка качества и безопасности
- 💬 **AI Чат** - диалог с искусственным интеллектом
- 📊 **Статистика** - мониторинг использования бота

## 🚀 Быстрый старт

### 1. Подготовка

Убедитесь, что основной AI-ассистент запущен:

```bash
# Установка зависимостей (включает vk-teams-async-bot)
pip install -r requirements.txt

# Запуск основного приложения
python -m uvicorn app.main:app --reload
```

### 2. Создание бота в VK Teams

1. Найдите @MetaBot в VK Teams
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный токен

### 3. Настройка переменных окружения

Добавьте в `.env` файл:

```env
# VK Teams Bot Configuration
VK_TEAMS_BOT_TOKEN=your_bot_token_here
VK_TEAMS_API_URL=https://your-vk-teams-api-url
VK_TEAMS_WEBHOOK_URL=https://your-domain.com/api/v1/vk-teams/webhook/events
VK_TEAMS_ENABLED=true
```

### 4. Конфигурация через API

```bash
# Настройка бота через API
curl -X POST "http://localhost:8000/api/v1/vk-teams/bot/configure" \
  -H "Content-Type: application/json" \
  -d '{
    "bot_token": "YOUR_BOT_TOKEN",
    "api_url": "YOUR_VK_TEAMS_API_URL",
    "auto_start": true
  }'
```

### 5. Или используйте CLI утилиту

```bash
# Настройка через CLI
python vk_teams_bot_cli.py configure \
  --token YOUR_BOT_TOKEN \
  --api-url YOUR_VK_TEAMS_API_URL

# Проверка статуса
python vk_teams_bot_cli.py status

# Тест webhook
python vk_teams_bot_cli.py test
```

## 📖 Использование

### Команды бота

```
/start          - Приветствие и список функций
/help           - Справка по командам
/search <запрос> - Поиск информации
/generate <тема> - Генерация контента
/status         - Статус системы
/settings       - Настройки пользователя
```

### Примеры

```
/search документация по API аутентификации
/generate RFC для микросервисной архитектуры
Объясни принципы SOLID в программировании
Найди информацию о безопасности
```

## 🔧 API Endpoints

### Управление ботом
- `GET /api/v1/vk-teams/bot/status` - статус бота
- `POST /api/v1/vk-teams/bot/configure` - настройка бота
- `POST /api/v1/vk-teams/bot/start` - запуск бота
- `POST /api/v1/vk-teams/bot/stop` - остановка бота
- `GET /api/v1/vk-teams/bot/stats` - статистика

### Webhook обработка
- `POST /api/v1/vk-teams/webhook/events` - основной webhook
- `POST /api/v1/vk-teams/webhook/messages` - обработка сообщений
- `POST /api/v1/vk-teams/webhook/callback` - обработка кнопок

## 🔒 Безопасность

- ✅ JWT аутентификация для управления ботом
- ✅ Поддержка списков разрешенных пользователей и чатов
- ✅ Проверка webhook подписи (опционально)
- ✅ Rate limiting на API endpoints

## 📊 Мониторинг

```bash
# Health check
curl http://localhost:8000/api/v1/vk-teams/bot/health

# Статистика использования  
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/vk-teams/bot/stats
```

## 🧪 Тестирование

```bash
# Запуск тестов VK Teams интеграции
pytest tests/integration/test_vk_teams_integration.py -v

# Тест webhook
curl -X POST http://localhost:8000/api/v1/vk-teams/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test_event": "message"}'
```

## 🐛 Отладка

### Проверка логов
```bash
# Логи бота
tail -f logs/app.log | grep "vk_teams"

# Или установите уровень логирования DEBUG
export LOG_LEVEL=DEBUG
```

### Частые проблемы

1. **Бот не отвечает**
   - Проверьте токен бота
   - Убедитесь что webhook URL доступен
   - Проверьте статус бота через API

2. **Ошибки авторизации**
   - Проверьте JWT токен для API управления
   - Убедитесь что пользователь в списке разрешенных

3. **Медленные ответы**
   - Проверьте производительность AI API
   - Увеличьте timeout настройки

## 🚢 Production

### Docker
```yaml
# docker-compose.yml
services:
  ai-assistant:
    build: .
    environment:
      - VK_TEAMS_BOT_TOKEN=${VK_TEAMS_BOT_TOKEN}
      - VK_TEAMS_API_URL=${VK_TEAMS_API_URL}
      - VK_TEAMS_ENABLED=true
    ports:
      - "8000:8000"
```

### Nginx
```nginx
# VK Teams webhook должен быть доступен через HTTPS
location /api/v1/vk-teams/webhook/ {
    proxy_pass http://ai-assistant:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## 📋 Roadmap

- [ ] Поддержка файлов и изображений
- [ ] Inline кнопки для быстрых действий
- [ ] Групповые чаты
- [ ] Push уведомления
- [ ] Мультиязычность
- [ ] Аналитика диалогов

## 📚 Документация

- [Полная документация VK Teams интеграции](VK_TEAMS_INTEGRATION.md)
- [VK Teams Bot API](https://teams.vk.com/botapi/)
- [SDK vk-teams-async-bot](https://pypi.org/project/vk-teams-async-bot/)

## 🆘 Поддержка

- 🐛 Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 📧 Email: support@aiassistant.com  
- 💬 Telegram: @ai_assistant_support

---

**Статус**: ✅ Готово к использованию  
**Версия**: 1.0.0  
**Последнее обновление**: 2024-12-22 