# 🚀 Руководство по интеграции с VK Teams

## 📋 Содержание
1. [Обзор интеграции](#обзор-интеграции)
2. [Подготовка](#подготовка)
3. [Настройка бота VK Teams](#настройка-бота-vk-teams)
4. [Конфигурация AI Assistant](#конфигурация-ai-assistant)
5. [Развертывание](#развертывание)
6. [Тестирование](#тестирование)
7. [Мониторинг](#мониторинг)
8. [Устранение проблем](#устранение-проблем)

---

## 🎯 Обзор интеграции

AI Assistant полностью интегрирован с VK Teams для предоставления следующих возможностей:

### Основной функционал:
- **Чат-интерфейс**: Полнофункциональный AI-ассистент в VK Teams
- **Семантический поиск**: Поиск по всем подключенным источникам данных
- **RFC генерация**: Создание технических документов
- **Code Review**: Анализ кода и рекомендации
- **Document Analysis**: Обработка и анализ документов

### Архитектура:
```
VK Teams ↔ VK Teams Bot ↔ AI Assistant API ↔ Backend Services
```

---

## 🛠 Подготовка

### Требования:
- **VK Teams** аккаунт (корпоративный или личный)
- **VK Teams Admin** права для создания ботов
- **AI Assistant** развернутый и работающий
- **Публичный URL** для webhook'ов (HTTPS обязательно)

### Инфраструктура:
```bash
# Проверим что AI Assistant работает
curl -s http://localhost:8000/health

# Должен вернуть:
# {"status":"healthy","architecture":"hexagonal","environment":"development","version":"2.0.0"}
```

---

## 🤖 Настройка бота VK Teams

### Шаг 1: Создание бота

1. **Откройте VK Teams** и перейдите в настройки
2. **Найдите раздел "Боты"** или "Интеграции"
3. **Создайте нового бота**:
   - Имя: `AI Assistant Bot`
   - Описание: `Интеллектуальный ассистент для команды`
   - Аватар: Загрузите логотип вашей команды

### Шаг 2: Получение токенов

После создания бота вы получите:
- **Bot Token** (начинается с `001.`)
- **API Base URL** (обычно `https://api.vk.com/...`)

**Сохраните эти данные!** Они понадобятся для конфигурации.

### Шаг 3: Настройка webhook

1. **URL для webhook'а**: `https://your-domain.com/api/v1/integrations/vk-teams/webhook`
2. **Метод**: POST
3. **События для подписки**:
   - `message_new` - новые сообщения
   - `message_reply` - ответы на сообщения
   - `chat_join` - присоединение к чату
   - `chat_leave` - покидание чата

---

## ⚙️ Конфигурация AI Assistant

### Шаг 1: Environment переменные

Создайте файл `.env.vk_teams`:

```bash
# VK Teams Configuration
VK_TEAMS_BOT_TOKEN=001.ваш_токен_бота_здесь
VK_TEAMS_API_URL=https://api.vk.com/method/
VK_TEAMS_WEBHOOK_URL=https://your-domain.com/api/v1/integrations/vk-teams/webhook
VK_TEAMS_SECRET_KEY=ваш_секретный_ключ_для_подписи

# AI Assistant Configuration
AI_ASSISTANT_API_URL=http://localhost:8000
AI_ASSISTANT_API_KEY=ваш_api_ключ

# Webhook Security
VK_TEAMS_VERIFY_SIGNATURE=true
VK_TEAMS_WEBHOOK_SECRET=секретный_ключ_для_вебхука

# Features Configuration
VK_TEAMS_ENABLE_SEARCH=true
VK_TEAMS_ENABLE_RFC_GENERATION=true
VK_TEAMS_ENABLE_CODE_REVIEW=true
VK_TEAMS_ENABLE_DOCUMENT_ANALYSIS=true

# Rate Limiting
VK_TEAMS_RATE_LIMIT_PER_USER=10
VK_TEAMS_RATE_LIMIT_WINDOW=60

# Logging
VK_TEAMS_LOG_LEVEL=INFO
VK_TEAMS_ENABLE_METRICS=true
```

### Шаг 2: Обновление Docker Compose

Обновите `docker-compose.production.yml`:

```yaml
services:
  backend:
    environment:
      # Добавьте VK Teams переменные
      - VK_TEAMS_BOT_TOKEN=${VK_TEAMS_BOT_TOKEN}
      - VK_TEAMS_API_URL=${VK_TEAMS_API_URL}
      - VK_TEAMS_WEBHOOK_URL=${VK_TEAMS_WEBHOOK_URL}
      - VK_TEAMS_SECRET_KEY=${VK_TEAMS_SECRET_KEY}
      
  # Добавьте VK Teams Bot сервис
  vk-teams-bot:
    build:
      context: ./infrastructure/vk_teams
      dockerfile: Dockerfile
    container_name: ai_assistant_vk_teams_bot
    restart: unless-stopped
    environment:
      - VK_TEAMS_BOT_TOKEN=${VK_TEAMS_BOT_TOKEN}
      - AI_ASSISTANT_API_URL=http://backend:8000
      - REDIS_URL=redis://redis:6379/2
    depends_on:
      - backend
      - redis
    networks:
      - ai_assistant_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Шаг 3: Конфигурация Nginx

Добавьте в `nginx/nginx.prod.conf`:

```nginx
# VK Teams webhook endpoint
location /api/v1/integrations/vk-teams/ {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Специальные заголовки для VK Teams
    proxy_set_header X-VK-Teams-Signature $http_x_vk_teams_signature;
    proxy_set_header Content-Type application/json;
    
    # Увеличиваем таймауты для обработки сложных запросов
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}
```

---

## 🚀 Развертывание

### Шаг 1: Подготовка secrets

```bash
# Создайте production secrets
mkdir -p secrets
echo "001.ваш_токен_бота" > secrets/vk_teams_bot_token.txt
echo "ваш_секретный_ключ" > secrets/vk_teams_secret_key.txt

# Установите правильные права
chmod 600 secrets/*
```

### Шаг 2: Сборка и запуск

```bash
# Соберите обновленные образы
docker-compose -f docker-compose.production.yml build

# Запустите сервисы
docker-compose -f docker-compose.production.yml up -d

# Проверьте статус
docker-compose -f docker-compose.production.yml ps
```

### Шаг 3: Настройка webhook в VK Teams

```bash
# Зарегистрируйте webhook
curl -X POST "https://api.vk.com/method/messages.setWebhookUrl" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-domain.com/api/v1/integrations/vk-teams/webhook",
    "access_token": "001.ваш_токен_бота",
    "v": "5.131"
  }'
```

---

## 🧪 Тестирование

### Шаг 1: Базовая проверка

1. **Найдите вашего бота** в VK Teams
2. **Отправьте сообщение**: `/help`
3. **Ожидаемый ответ**:
   ```
   🤖 AI Assistant Bot
   
   Доступные команды:
   /search <запрос> - Семантический поиск
   /rfc <тема> - Генерация RFC
   /analyze <код> - Анализ кода
   /help - Справка
   
   Просто напишите мне любой вопрос!
   ```

### Шаг 2: Тестирование функций

```bash
# В VK Teams попробуйте:

# 1. Поиск
/search как настроить Docker

# 2. Генерация RFC
/rfc система аутентификации пользователей

# 3. Анализ кода
/analyze
```python
def login(username, password):
    if username == "admin" and password == "123":
        return True
    return False
```

# 4. Обычный вопрос
Как оптимизировать производительность базы данных?
```

### Шаг 3: Проверка логов

```bash
# Проверьте логи backend
docker-compose -f docker-compose.production.yml logs backend | grep vk_teams

# Проверьте логи VK Teams bot
docker-compose -f docker-compose.production.yml logs vk-teams-bot

# Проверьте webhook запросы
curl -s http://localhost:8000/api/v1/integrations/vk-teams/status
```

---

## 📊 Мониторинг

### Шаг 1: Метрики

VK Teams интеграция автоматически отправляет метрики в Prometheus:

```prometheus
# Количество сообщений
vk_teams_messages_total{status="success|error"}

# Время ответа
vk_teams_response_time_seconds

# Активные пользователи
vk_teams_active_users_total

# Использование команд
vk_teams_command_usage_total{command="search|rfc|analyze|help"}
```

### Шаг 2: Grafana дашборд

1. **Откройте Grafana**: `http://localhost:3001`
2. **Логин**: admin / admin123
3. **Импортируйте дашборд**: `monitoring/grafana/dashboards/vk-teams.json`

### Шаг 3: Алерты

Настройте алерты в `monitoring/prometheus/alerts/vk-teams.yml`:

```yaml
groups:
  - name: vk_teams
    rules:
      - alert: VKTeamsHighErrorRate
        expr: rate(vk_teams_messages_total{status="error"}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Высокий процент ошибок в VK Teams"
          
      - alert: VKTeamsSlowResponse
        expr: histogram_quantile(0.95, vk_teams_response_time_seconds) > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Медленные ответы VK Teams бота"
```

---

## 🔧 Устранение проблем

### Проблема 1: Бот не отвечает

**Диагностика**:
```bash
# Проверьте webhook
curl -X POST "https://your-domain.com/api/v1/integrations/vk-teams/webhook" \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Проверьте логи
docker-compose logs backend | grep -i vk_teams | tail -20
```

**Решение**:
- Проверьте токен бота
- Убедитесь что webhook зарегистрирован
- Проверьте HTTPS сертификат

### Проблема 2: Ошибки авторизации

**Диагностика**:
```bash
# Проверьте токен
curl -X POST "https://api.vk.com/method/messages.getConversations" \
  -d "access_token=001.ваш_токен&v=5.131"
```

**Решение**:
- Перегенерируйте токен бота
- Проверьте права бота
- Обновите secrets

### Проблема 3: Медленные ответы

**Диагностика**:
```bash
# Проверьте производительность
docker stats

# Проверьте Redis
redis-cli -h localhost -p 6379 info stats
```

**Решение**:
- Увеличьте ресурсы контейнера
- Оптимизируйте запросы к AI
- Включите кэширование

---

## 🔐 Безопасность

### Рекомендации:

1. **Используйте HTTPS** для всех webhook'ов
2. **Проверяйте подписи** VK Teams запросов
3. **Ограничивайте rate limit** на пользователя
4. **Логируйте все запросы** для аудита
5. **Обновляйте токены** регулярно

### Пример конфигурации безопасности:

```python
# app/api/v1/integrations/vk_teams/security.py
import hashlib
import hmac
from fastapi import HTTPException

def verify_vk_teams_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Проверка подписи VK Teams webhook"""
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

def check_rate_limit(user_id: str) -> bool:
    """Проверка rate limit для пользователя"""
    # Реализация rate limiting
    pass
```

---

## 📱 Команды бота

### Основные команды:

| Команда | Описание | Пример |
|---------|----------|--------|
| `/help` | Справка по командам | `/help` |
| `/search <запрос>` | Семантический поиск | `/search настройка Docker` |
| `/rfc <тема>` | Генерация RFC | `/rfc система авторизации` |
| `/analyze <код>` | Анализ кода | `/analyze функция логина` |
| `/status` | Статус системы | `/status` |

### Административные команды:

| Команда | Описание | Права |
|---------|----------|-------|
| `/admin stats` | Статистика использования | Admin |
| `/admin users` | Список активных пользователей | Admin |
| `/admin reload` | Перезагрузка конфигурации | Admin |

---

## 🚀 Итоговая проверка

После настройки выполните полную проверку:

```bash
# 1. Проверка health endpoint
curl -s https://your-domain.com/api/v1/integrations/vk-teams/health

# 2. Проверка метрик
curl -s https://your-domain.com/metrics | grep vk_teams

# 3. Тест в VK Teams
# Отправьте: "Привет, как дела?"
# Ожидаемый ответ: Дружелюбный ответ от AI

# 4. Тест команды
# Отправьте: "/search Docker"
# Ожидаемый ответ: Результаты поиска по Docker

# 5. Проверка логов
docker-compose logs vk-teams-bot | tail -10
```

---

## 🎉 Готово!

Поздравляем! VK Teams интеграция настроена и готова к использованию.

### Что дальше:
1. **Обучите команду** использованию бота
2. **Настройте дополнительные источники данных**
3. **Мониторьте использование** через Grafana
4. **Собирайте обратную связь** для улучшений

### Поддержка:
- **Документация**: `/docs/integrations/VK_TEAMS_README.md`
- **Логи**: `docker-compose logs vk-teams-bot`
- **Метрики**: `http://localhost:3001` (Grafana)
- **API**: `http://localhost:8000/docs` (Swagger)

---

**Удачного использования AI Assistant в VK Teams! 🚀** 