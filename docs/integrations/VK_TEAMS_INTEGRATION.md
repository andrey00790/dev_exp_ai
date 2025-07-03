# VK Teams Bot Integration

Документация по интеграции AI-ассистента с VK Teams.

## 🎯 Обзор

VK Teams Bot Integration позволяет пользователям взаимодействовать с функционалом AI-ассистента прямо из VK Teams чатов.

## 🚀 Быстрый старт

### 1. Установка
```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения
```env
VK_TEAMS_BOT_TOKEN=your_bot_token_here
VK_TEAMS_API_URL=https://your-vk-teams-api-url
VK_TEAMS_WEBHOOK_URL=https://your-domain.com/api/v1/vk-teams/webhook/events
VK_TEAMS_ENABLED=true
```

### 3. Конфигурация бота
```bash
curl -X POST "http://localhost:8000/api/v1/vk-teams/bot/configure" \
  -H "Content-Type: application/json" \
  -d '{"bot_token": "token", "api_url": "url", "auto_start": true}'
```

## 📖 Использование

### Команды:
- `/start` - приветствие
- `/help` - справка
- `/search <запрос>` - поиск
- `/generate <описание>` - генерация
- `/status` - статус системы

### Примеры:
```
/search документация по API
/generate RFC для микросервисов
Объясни принципы SOLID
```

## 🔧 API Endpoints

- `GET /api/v1/vk-teams/bot/status` - статус бота
- `POST /api/v1/vk-teams/bot/configure` - настройка
- `POST /api/v1/vk-teams/bot/start` - запуск
- `POST /api/v1/vk-teams/webhook/events` - webhook

## 🔒 Безопасность

- JWT аутентификация для управления
- Списки разрешенных пользователей
- Проверка webhook подписи

## 📊 Мониторинг

```bash
# Статус бота
curl "http://localhost:8000/api/v1/vk-teams/bot/health"

# Статистика
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/vk-teams/bot/stats"
```

## 🐛 Отладка

```bash
# Тест webhook
curl -X POST "http://localhost:8000/api/v1/vk-teams/webhook/test" \
  -H "Content-Type: application/json" \
  -d '{"test_event": "message"}'
``` 