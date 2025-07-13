# 🚀 Полное руководство по настройке VK Teams интеграции с нуля

## 📋 Содержание
1. [Подготовка и требования](#1-подготовка-и-требования)
2. [Создание бота в VK Teams](#2-создание-бота-в-vk-teams)
3. [Настройка VK приложения (опционально)](#3-настройка-vk-приложения-опционально)
4. [Конфигурация AI Assistant](#4-конфигурация-ai-assistant)
5. [Настройка webhook](#5-настройка-webhook)
6. [Запуск и тестирование](#6-запуск-и-тестирование)
7. [Продвинутая настройка](#7-продвинутая-настройка)
8. [Мониторинг и устранение проблем](#8-мониторинг-и-устранение-проблем)

---

## 1. **Подготовка и требования**

### ✅ **Что вам понадобится:**

1. **VK Teams аккаунт** (корпоративный или личный)
2. **AI Assistant** уже запущен и работает
3. **Публичный домен с HTTPS** для webhook'ов (для production)
4. **Права администратора** в VK Teams (для создания ботов)

### 🔧 **Проверка готовности системы:**

```bash
# Убедитесь что AI Assistant работает
curl -s http://localhost:8000/health

# Ответ должен быть:
# {"status":"healthy","architecture":"hexagonal","environment":"development","version":"2.0.0"}

# Проверьте, что VK Teams интеграция доступна
curl -s http://localhost:8000/api/v1/vk-teams/bot/health

# Ответ должен быть:
# {"status":"healthy","service":"vk-teams-bot","timestamp":"..."}
```

---

## 2. **Создание бота в VK Teams**

### 🤖 **Шаг 1: Создание бота через @MetaBot**

1. **Откройте VK Teams** на любом устройстве
2. **Найдите контакт @MetaBot** или перейдите по ссылке: https://teams.vk.com/contact/@metabot
3. **Отправьте команду:**
   ```
   /newbot
   ```

4. **Следуйте инструкциям MetaBot'а:**

   **MetaBot спросит:** "Как назовём вашего бота?"
   ```
   AI Assistant Bot
   ```

   **MetaBot спросит:** "Теперь пришлите описание бота"
   ```
   Интеллектуальный ассистент для поиска информации, генерации документов и анализа кода. Поддерживает семантический поиск, создание RFC, code review и многое другое.
   ```

   **MetaBot спросит:** "Пришлите аватар для бота"
   ```
   Загрузите изображение логотипа или отправьте /skip
   ```

### 📝 **Шаг 2: Получение токена**

После создания бота **MetaBot отправит вам сообщение с токеном:**

```
Готово! Вот токен вашего бота:
001.1234567890.abcdefghijklmnopqrstuvwxyz:1234567890abcdef

Сохраните токен в надёжном месте!
```

**⚠️ ВАЖНО:** Сохраните этот токен! Он понадобится для настройки.

### 🔧 **Шаг 3: Базовая настройка бота**

**MetaBot предложит настроить бота:**

1. **Команды:** Настройте список команд для автодополнения
   ```
   /start - Приветствие и справка
   /help - Список всех команд
   /search - Поиск информации
   /generate - Генерация документов
   /analyze - Анализ кода
   /status - Статус системы
   ```

2. **Права доступа:** Выберите, кто может добавлять бота в чаты
   - Только администраторы (рекомендуется)
   - Любые пользователи

---

## 3. **Настройка VK приложения (опционально)**

> 💡 **Примечание:** Этот шаг нужен только если вы хотите ограничить доступ к боту определенными VK пользователями

### 📱 **Шаг 1: Создание VK приложения**

1. **Перейдите на:** https://vk.com/apps?act=manage
2. **Нажмите "Создать приложение"**
3. **Выберите тип:** "Веб-сайт"
4. **Заполните данные:**
   - **Название:** AI Assistant VK Integration
   - **Адрес сайта:** https://your-domain.com
   - **Базовый домен:** your-domain.com

### 🔑 **Шаг 2: Получение ключей**

После создания приложения получите:
- **ID приложения** (Application ID)
- **Защищённый ключ** (Secret Key)

### 👥 **Шаг 3: Список разрешённых пользователей**

Получите VK ID пользователей, которым разрешён доступ:

1. **Откройте профиль пользователя в VK**
2. **ID находится в URL:** `https://vk.com/id123456789` → ID = `123456789`
3. **Или используйте API:** `https://vk.com/dev/users.get`

---

## 4. **Конфигурация AI Assistant**

### 📁 **Шаг 1: Создание файла конфигурации**

Создайте файл `.env.vk_teams` в корне проекта:

```bash
# ============================================================================
# VK Teams Bot Configuration
# ============================================================================

# Основные настройки бота
VK_TEAMS_BOT_TOKEN=001.1234567890.abcdefghijklmnopqrstuvwxyz:1234567890abcdef
VK_TEAMS_BOT_NAME=AI Assistant Bot
VK_TEAMS_ENABLED=true

# URL для VK Teams API
VK_TEAMS_API_URL=https://api.internal.myteam.mail.ru/bot/v1

# Webhook URL (замените на ваш домен)
VK_TEAMS_WEBHOOK_URL=https://your-domain.com/api/v1/vk-teams/webhook/events

# Настройки безопасности
VK_TEAMS_VERIFY_SIGNATURE=true
VK_TEAMS_SECRET_KEY=your-random-secret-key-here

# ============================================================================
# VK OAuth Configuration (опционально)
# ============================================================================

# Включить проверку доступа через VK OAuth
VK_OAUTH_ENABLED=false

# Данные VK приложения (если VK_OAUTH_ENABLED=true)
VK_OAUTH_CLIENT_ID=your_vk_app_id
VK_OAUTH_CLIENT_SECRET=your_vk_app_secret
VK_OAUTH_REDIRECT_URI=https://your-domain.com/api/v1/auth/vk/callback

# Список разрешённых VK пользователей (через запятую)
ALLOWED_VK_USERS=123456789,987654321,555666777

# ============================================================================
# AI Assistant Configuration
# ============================================================================

# URL вашего AI Assistant API
AI_ASSISTANT_API_URL=http://localhost:8000
AI_ASSISTANT_API_KEY=your-api-key-if-needed

# Настройки интеграции
VK_TEAMS_AUTO_START=true
VK_TEAMS_DEFAULT_LANGUAGE=ru
VK_TEAMS_MAX_MESSAGE_LENGTH=4096
VK_TEAMS_TIMEOUT_SECONDS=30
```

### 🔧 **Шаг 2: Загрузка конфигурации**

Добавьте загрузку конфигурации в основной `.env` файл:

```bash
# Добавьте в ваш основной .env файл
source .env.vk_teams
```

Или объедините файлы:

```bash
# Объедините конфигурации
cat .env.vk_teams >> .env
```

### 📝 **Шаг 3: Настройка через переменные окружения**

Альтернативно, можете добавить переменные прямо в основной `.env`:

```bash
# Добавьте в .env
echo "" >> .env
echo "# VK Teams Configuration" >> .env
echo "VK_TEAMS_BOT_TOKEN=001.your_bot_token_here" >> .env
echo "VK_TEAMS_ENABLED=true" >> .env
echo "VK_TEAMS_API_URL=https://api.internal.myteam.mail.ru/bot/v1" >> .env
echo "VK_TEAMS_WEBHOOK_URL=https://your-domain.com/api/v1/vk-teams/webhook/events" >> .env
```

---

## 5. **Настройка webhook**

### 🌐 **Вариант A: Для разработки (локальный сервер)**

#### **Шаг 1: Установка ngrok**

```bash
# Установка ngrok для туннелирования
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Или через brew на macOS
brew install ngrok

# Или скачайте с https://ngrok.com/download
```

#### **Шаг 2: Регистрация и настройка ngrok**

1. **Зарегистрируйтесь на:** https://ngrok.com
2. **Получите authtoken:** https://dashboard.ngrok.com/get-started/your-authtoken
3. **Настройте ngrok:**

```bash
# Добавьте ваш authtoken
ngrok authtoken YOUR_NGROK_AUTHTOKEN
```

#### **Шаг 3: Запуск туннеля**

```bash
# Запустите ngrok (в отдельном терминале)
ngrok http 8000

# Вы получите URL вида: https://abc123.ngrok.io
```

#### **Шаг 4: Обновление конфигурации**

```bash
# Обновите webhook URL в .env
VK_TEAMS_WEBHOOK_URL=https://abc123.ngrok.io/api/v1/vk-teams/webhook/events
```

### 🏢 **Вариант B: Для production (публичный сервер)**

#### **Шаг 1: Настройка домена**

Убедитесь что ваш домен доступен и настроен SSL:

```bash
# Проверьте доступность
curl -I https://your-domain.com/health

# Должен вернуть 200 OK
```

#### **Шаг 2: Настройка nginx (если используется)**

Добавьте в конфигурацию nginx:

```nginx
# /etc/nginx/sites-available/ai-assistant
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    # SSL сертификаты
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # Основное приложение
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Специальная настройка для VK Teams webhook
    location /api/v1/vk-teams/webhook/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Увеличенные таймауты для обработки AI запросов
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

#### **Шаг 3: Проверка доступности**

```bash
# Проверьте доступность webhook endpoint
curl -X POST https://your-domain.com/api/v1/vk-teams/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": "ping"}'

# Должен вернуть успешный ответ
```

---

## 6. **Запуск и тестирование**

### 🚀 **Шаг 1: Запуск AI Assistant**

```bash
# Остановите старый процесс если он работает
pkill -f "python.*main.py"

# Запустите с новой конфигурацией
python main.py --port 8000 --host localhost
```

### 🔧 **Шаг 2: Конфигурация через API**

```bash
# Получите JWT токен для доступа к API
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@vkteam.ru", "password": "admin"}' | jq -r '.access_token')

# Настройте VK Teams бота
curl -X POST "http://localhost:8000/api/v1/vk-teams/bot/configure" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "bot_token": "001.your_bot_token_here",
    "api_url": "https://api.internal.myteam.mail.ru/bot/v1",
    "webhook_url": "https://your-domain.com/api/v1/vk-teams/webhook/events",
    "auto_start": true,
    "allowed_users": [],
    "allowed_chats": []
  }'
```

**Ожидаемый ответ:**
```json
{
  "success": true,
  "message": "Bot configured successfully",
  "config": {
    "bot_id": "your_bot_id",
    "is_active": true,
    "webhook_url": "https://your-domain.com/api/v1/vk-teams/webhook/events"
  }
}
```

### 🧪 **Шаг 3: Тестирование бота**

#### **3.1 Проверка статуса:**

```bash
curl -X GET "http://localhost:8000/api/v1/vk-teams/bot/status" \
  -H "Authorization: Bearer $TOKEN"
```

#### **3.2 Тест в VK Teams:**

1. **Найдите вашего бота** в VK Teams (по имени, которое вы указали)
2. **Отправьте сообщение:** `/start`
3. **Ожидаемый ответ:**
   ```
   🤖 Привет! Я AI Assistant Bot
   
   Я помогу вам с поиском информации, генерацией документов и анализом кода.
   
   Доступные команды:
   /help - Список всех команд
   /search - Поиск информации
   /generate - Генерация документов
   /analyze - Анализ кода
   /status - Статус системы
   
   Просто напишите мне вопрос или используйте команды!
   ```

#### **3.3 Тест функционала:**

```
# Тест поиска
/search REST API документация

# Тест генерации
/generate RFC для микросервиса пользователей

# Тест анализа
/analyze как оптимизировать производительность Python кода

# Обычный вопрос
Объясни принципы SOLID в программировании
```

### 📊 **Шаг 4: Проверка логов**

```bash
# Просмотр логов в реальном времени
tail -f app.log | grep -E "(vk.teams|bot|webhook)"

# Или через журнал приложения
curl -X GET "http://localhost:8000/api/v1/vk-teams/bot/stats" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 7. **Продвинутая настройка**

### 🔐 **Настройка безопасности**

#### **7.1 Включение проверки подписи:**

```bash
# Добавьте в .env
VK_TEAMS_VERIFY_SIGNATURE=true
VK_TEAMS_SECRET_KEY=your-super-secret-key-min-32-characters
```

#### **7.2 Настройка списка разрешённых пользователей:**

```bash
# Через переменные окружения
ALLOWED_VK_USERS=123456789,987654321,555666777

# Или через API
curl -X POST "http://localhost:8000/api/v1/vk-teams/bot/configure" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "allowed_users": ["123456789", "987654321"],
    "allowed_chats": ["chat_id_1", "chat_id_2"]
  }'
```

### 🎨 **Настройка интерфейса**

#### **7.1 Кастомизация сообщений:**

Создайте файл `config/vk_teams_messages.yml`:

```yaml
# Сообщения бота
messages:
  welcome: |
    🤖 Добро пожаловать в AI Assistant!
    
    Я ваш интеллектуальный помощник для:
    • 🔍 Поиска информации
    • 📝 Генерации документов
    • 🔧 Анализа кода
    • 🚀 Автоматизации задач
    
    Напишите мне любой вопрос или используйте команды!
    
  help: |
    📚 Доступные команды:
    
    🔍 **Поиск:**
    /search <запрос> - Поиск по документам
    
    📝 **Генерация:**
    /generate <описание> - Создание документов
    /rfc <описание> - Генерация RFC
    
    🔧 **Анализ:**
    /analyze <код> - Анализ кода
    /review <код> - Code review
    
    ⚙️ **Система:**
    /status - Статус системы
    /stats - Статистика
    
  error: |
    ❌ Произошла ошибка при обработке запроса.
    
    Попробуйте:
    • Переформулировать вопрос
    • Использовать команды /help
    • Обратиться к администратору
    
  access_denied: |
    🚫 Доступ ограничен
    
    Для использования бота обратитесь к администратору.
```

#### **7.2 Настройка кнопок:**

```yaml
# Быстрые кнопки
quick_buttons:
  - text: "🔍 Поиск"
    command: "/search"
  - text: "📝 Генерация"
    command: "/generate"
  - text: "🔧 Анализ"
    command: "/analyze"
  - text: "❓ Помощь"
    command: "/help"
```

### 📈 **Настройка мониторинга**

#### **7.1 Включение детального логирования:**

```bash
# Добавьте в .env
LOG_LEVEL=DEBUG
VK_TEAMS_LOG_MESSAGES=true
VK_TEAMS_LOG_REQUESTS=true
```

#### **7.2 Настройка метрик:**

```bash
# Prometheus метрики
curl http://localhost:8000/metrics | grep vk_teams

# Собственные метрики
curl -X GET "http://localhost:8000/api/v1/vk-teams/bot/metrics" \
  -H "Authorization: Bearer $TOKEN"
```

#### **7.3 Webhook для мониторинга:**

```bash
# Настройка webhook для уведомлений
VK_TEAMS_MONITORING_WEBHOOK=https://your-monitoring-system.com/webhook
VK_TEAMS_ALERT_ON_ERRORS=true
VK_TEAMS_ALERT_THRESHOLD=10
```

---

## 8. **Мониторинг и устранение проблем**

### 📊 **Мониторинг работы бота**

#### **8.1 Проверка статуса:**

```bash
# Статус бота
curl "http://localhost:8000/api/v1/vk-teams/bot/status" | jq

# Статистика
curl "http://localhost:8000/api/v1/vk-teams/bot/stats" | jq

# Здоровье системы
curl "http://localhost:8000/api/v1/vk-teams/bot/health" | jq
```

#### **8.2 Проверка webhook'а:**

```bash
# Тест webhook'а
curl -X POST "http://localhost:8000/api/v1/vk-teams/webhook/test" \
  -H "Content-Type: application/json" \
  -d '{"test_event": "ping", "test_data": {"message": "Hello Bot!"}}'
```

### 🔧 **Частые проблемы и решения**

#### **Проблема 1: Бот не отвечает на сообщения**

**Диагностика:**
```bash
# Проверьте логи
tail -f app.log | grep -i "vk.teams\|bot\|webhook"

# Проверьте webhook
curl -I https://your-domain.com/api/v1/vk-teams/webhook/events
```

**Возможные причины:**
- Неверный webhook URL
- Проблемы с SSL сертификатом
- Блокировка файерволом
- Неверный токен бота

**Решение:**
```bash
# Перенастройте webhook
curl -X POST "http://localhost:8000/api/v1/vk-teams/bot/configure" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"webhook_url": "https://correct-domain.com/api/v1/vk-teams/webhook/events"}'
```

#### **Проблема 2: Ошибки авторизации**

**Диагностика:**
```bash
# Проверьте токен
curl -X GET "http://localhost:8000/api/v1/vk-teams/bot/status" \
  -H "Authorization: Bearer invalid_token"
```

**Решение:**
```bash
# Получите новый токен
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@vkteam.ru", "password": "admin"}' | jq -r '.access_token')
```

#### **Проблема 3: VK OAuth не работает**

**Диагностика:**
```bash
# Проверьте конфигурацию VK OAuth
curl "http://localhost:8000/api/v1/auth/vk/config"

# Проверьте доступ пользователя
curl "http://localhost:8000/api/v1/auth/vk/check-access/123456789"
```

**Решение:**
```bash
# Убедитесь что VK приложение настроено правильно
VK_OAUTH_CLIENT_ID=correct_client_id
VK_OAUTH_CLIENT_SECRET=correct_secret
VK_OAUTH_REDIRECT_URI=https://your-domain.com/api/v1/auth/vk/callback
```

#### **Проблема 4: Медленная работа бота**

**Диагностика:**
```bash
# Проверьте статистику
curl "http://localhost:8000/api/v1/vk-teams/bot/stats" | jq '.performance'

# Проверьте нагрузку на систему
curl "http://localhost:8000/api/v1/monitoring/metrics/current" | jq
```

**Решение:**
```bash
# Увеличьте таймауты
VK_TEAMS_TIMEOUT_SECONDS=60
VK_TEAMS_MAX_CONCURRENT_REQUESTS=5

# Оптимизируйте AI модель
AI_MODEL_CACHE_ENABLED=true
AI_MODEL_MAX_TOKENS=2048
```

### 📝 **Полезные команды для диагностики**

```bash
# Полная диагностика системы
echo "=== AI Assistant Status ==="
curl -s http://localhost:8000/health | jq

echo "=== VK Teams Bot Status ==="
curl -s "http://localhost:8000/api/v1/vk-teams/bot/status" \
  -H "Authorization: Bearer $TOKEN" | jq

echo "=== Budget Status ==="
curl -s "http://localhost:8000/api/v1/budget/system-stats" \
  -H "Authorization: Bearer $TOKEN" | jq

echo "=== System Metrics ==="
curl -s "http://localhost:8000/api/v1/monitoring/metrics/current" | jq

echo "=== Logs (last 20 lines) ==="
tail -20 app.log
```

### 🚀 **Автоматизация мониторинга**

Создайте скрипт `monitor_vk_teams.sh`:

```bash
#!/bin/bash

# Скрипт мониторинга VK Teams бота
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@vkteam.ru", "password": "admin"}' | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ Ошибка получения токена авторизации"
    exit 1
fi

echo "🔍 Проверка статуса VK Teams бота..."
STATUS=$(curl -s "http://localhost:8000/api/v1/vk-teams/bot/status" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.is_active')

if [ "$STATUS" = "true" ]; then
    echo "✅ VK Teams бот активен"
else
    echo "❌ VK Teams бот неактивен"
    echo "🔄 Попытка перезапуска..."
    
    curl -s -X POST "http://localhost:8000/api/v1/vk-teams/bot/start" \
      -H "Authorization: Bearer $TOKEN"
    
    echo "✅ Команда перезапуска отправлена"
fi

echo "📊 Статистика за последний час:"
curl -s "http://localhost:8000/api/v1/vk-teams/bot/stats" \
  -H "Authorization: Bearer $TOKEN" | jq '.messages_last_hour'
```

Запустите его в cron:

```bash
# Добавьте в crontab (каждые 5 минут)
*/5 * * * * /path/to/monitor_vk_teams.sh >> /var/log/vk_teams_monitor.log 2>&1
```

---

## 🎉 **Заключение**

Теперь у вас полностью настроенная интеграция VK Teams с AI Assistant! 

### ✅ **Что у вас есть:**

1. **Полнофункциональный VK Teams бот** с AI возможностями
2. **Безопасная авторизация** через VK OAuth (опционально)
3. **Webhook интеграция** для real-time обработки сообщений
4. **Мониторинг и логирование** всех операций
5. **Масштабируемая архитектура** с поддержкой множества пользователей

### 🚀 **Следующие шаги:**

1. **Добавьте бота в ваши рабочие чаты**
2. **Обучите команду использованию бота**
3. **Настройте дополнительные источники данных**
4. **Кастомизируйте ответы под вашу предметную область**
5. **Настройте интеграции с другими системами**

### 📚 **Дополнительные ресурсы:**

- **[VK Teams Bot API](https://teams.vk.com/botapi/)** - Официальная документация
- **[AI Assistant API Reference](docs/API_REFERENCE_COMPLETE.md)** - Документация по API
- **[VK Teams Integration Guide](docs/integrations/VK_TEAMS_INTEGRATION.md)** - Расширенная документация
- **[Budget System Guide](docs/BUDGET_SYSTEM_GUIDE.md)** - Управление бюджетами
- **[User Management Guide](docs/USER_MANAGEMENT_GUIDE.md)** - Управление пользователями

**Удачного использования! 🤖✨** 