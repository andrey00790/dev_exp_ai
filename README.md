# 🤖 AI Assistant MVP - Enterprise Ready

[![Build Status](https://github.com/your-org/ai-assistant/workflows/CI/badge.svg)](https://github.com/your-org/ai-assistant/actions)
[![Coverage](https://codecov.io/gh/your-org/ai-assistant/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/ai-assistant)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)

**Intelligent AI Assistant для поиска, анализа и генерации технической документации**

---

## 🎯 **Обзор**

AI Assistant - это enterprise-ready платформа для работы с техническими документами, основанная на **векторном поиске** и **генеративном ИИ**. Система интегрируется с Confluence, GitLab, Jira и другими источниками данных, предоставляя единый интерфейс для поиска информации и генерации документов.

### 🌟 **Ключевые возможности**

- 🔍 **Семантический поиск** - ИИ-powered поиск по всем документам
- 📝 **Генерация RFC** - автоматическое создание технических документов
- 🏗️ **Анализ архитектуры** - диаграммы и рекомендации
- 🔐 **Enterprise Security** - JWT, RBAC, Rate Limiting
- 📊 **Мониторинг** - Prometheus, Grafana, Real-time metrics
- 🤖 **VK Teams Bot** - интеграция с мессенджером
- 🌐 **Modern UI** - React-based веб-интерфейс
- 🐳 **Docker Ready** - unified environment с 9 профилями

---

## 🚀 **Быстрый старт**

### **Требования**
- **Python 3.11+**
- **Docker & Docker Compose**
- **Node.js 18+** (для frontend)
- **8GB RAM** (рекомендуется 16GB)
- **PostgreSQL 15+** (включен в Docker)

### **Установка за 5 минут**

```bash
# 1. Клонируем проект
git clone https://github.com/your-org/ai-assistant.git
cd ai-assistant

# 2. Создаем виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# 3. Устанавливаем зависимости
pip install -r requirements.txt

# 4. Запускаем полную систему
make up-dev-full

# 5. Открываем браузер
# http://localhost:8000      - API
# http://localhost:8000/docs - Swagger UI
# http://localhost:3000      - Frontend
```

**🎉 Готово! Система запущена и готова к использованию.**

---

## 📋 **Содержание**

- [1. Запуск проекта локально](#1-запуск-проекта-локально)
- [2. Инфраструктура для разработки](#2-инфраструктура-для-разработки)
- [3. Тестирование](#3-тестирование)
- [4. Импорт данных](#4-импорт-данных)
- [5. Production развертывание](#5-production-развертывание)
- [6. Мониторинг](#6-мониторинг)
- [7. Решение проблем](#7-решение-проблем)
- [8. VK Teams интеграция](#8-vk-teams-интеграция)
- [9. Работа с GUI](#9-работа-с-gui)
- [10. API Documentation](#10-api-documentation)
- [11. Архитектура](#11-архитектура)
- [12. Поддержка](#12-поддержка)

---

## 1. **Запуск проекта локально**

### 🐳 **Docker Compose (рекомендуется)**

```bash
# Основные сервисы (app, postgres, redis, qdrant)
make up

# Полная система с UI и мониторингом
make up-dev-full

# Только бэкенд с admin панелями
make up-dev

# С LLM сервисами (Ollama)
make up-dev-llm
```

### 🔧 **Локальная разработка**

```bash
# 1. Запускаем инфраструктуру
make up

# 2. Запускаем приложение локально
make dev

# 3. Запускаем с отладкой
make dev-debug
```

### 📋 **Доступные сервисы**

| Сервис | URL | Описание |
|--------|-----|----------|
| **API** | http://localhost:8000 | FastAPI приложение |
| **Swagger UI** | http://localhost:8000/docs | API документация |
| **Frontend** | http://localhost:3000 | React веб-интерфейс |
| **Adminer** | http://localhost:8080 | База данных |
| **Redis UI** | http://localhost:8081 | Redis управление |
| **Grafana** | http://localhost:3001 | Мониторинг |
| **Prometheus** | http://localhost:9090 | Метрики |
| **Qdrant** | http://localhost:6333 | Векторная БД |

---

## 2. **Инфраструктура для разработки**

### 🛠️ **Запуск только инфраструктуры**

```bash
# Базовые сервисы (БД, Redis, Qdrant)
make up

# С admin панелями
make up-dev

# Полная инфраструктура
make up-dev-full
```

### 🔧 **Разработка бэкенда**

```bash
# 1. Запускаем инфраструктуру
make up-dev

# 2. Разрабатываем локально
export PYTHONPATH=$PWD
export DATABASE_URL=postgresql://ai_user:ai_password_dev@localhost:5432/ai_assistant
export REDIS_URL=redis://localhost:6379/0
export QDRANT_URL=http://localhost:6333

# 3. Запускаем приложение
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 🎨 **Разработка frontend**

```bash
# 1. Запускаем бэкенд
make up-dev

# 2. Переходим в frontend
cd frontend

# 3. Устанавливаем зависимости
npm install

# 4. Запускаем dev server
npm run dev
```

### 📊 **Мониторинг разработки**

```bash
# Статус всех сервисов
make status

# Детальный статус
make status-detailed

# Логи
make logs

# Логи конкретного сервиса
make logs-app
make logs-db
```

---

## 3. **Тестирование**

### 🧪 **Полный набор тестов**

```bash
# Unit тесты
make test-unit

# Integration тесты
make test-integration

# E2E тесты
make test-e2e-full

# Нагрузочные тесты
make test-load-locust

# Smoke тесты
make test-smoke

# Все тесты
make test-all
```

### 🎭 **E2E тестирование**

```bash
# Запуск E2E окружения (займет 10-15 минут)
make up-e2e

# Ожидание готовности сервисов
sleep 600

# Запуск E2E тестов
make test-e2e-full

# Доступные E2E сервисы
# http://localhost:8001 - E2E приложение
# http://localhost:8082 - Jira
# http://localhost:8083 - Confluence
# http://localhost:8084 - GitLab
```

### ⚡ **Нагрузочное тестирование**

```bash
# Запуск load testing окружения
make up-load

# Открыть Locust UI
# http://localhost:8089

# Настройки тестирования:
# - Host: http://load-app:8000
# - Users: 50
# - Spawn rate: 2
# - Duration: 600s
```

### 📊 **Результаты тестов**

```bash
# Отчеты
./test-results/          # Playwright отчеты
./coverage/             # Coverage отчеты
./performance/          # Performance отчеты

# Логи тестов
./logs/test-*.log       # Логи тестирования
```

---

## 4. **Импорт данных**

### 🎓 **Bootstrap ETL процесс**

```bash
# Полный ETL процесс
make bootstrap

# Тест bootstrap
make test-bootstrap

# Ручной запуск
python local/bootstrap_fetcher.py
```

### 📁 **Источники данных**

#### **Confluence**
```bash
# Настройка в config/datasources.yaml
confluence:
  url: "https://your-confluence.com"
  username: "your-username"
  password: "your-password"
  spaces: ["DEV", "ARCH", "DOCS"]
```

#### **GitLab**
```bash
# Настройка в config/datasources.yaml
gitlab:
  url: "https://gitlab.com"
  token: "your-access-token"
  projects: ["group/project1", "group/project2"]
```

#### **Jira**
```bash
# Настройка в config/datasources.yaml
jira:
  url: "https://your-jira.com"
  username: "your-username"
  password: "your-password"
  projects: ["PROJ1", "PROJ2"]
```

#### **Локальные файлы**
```bash
# Добавляем файлы в
./test-data/
├── confluence/
├── gitlab/
├── jira/
└── local-docs/

# Запускаем импорт
make bootstrap
```

### 🔄 **Синхронизация данных**

```bash
# Однократная синхронизация
curl -X POST http://localhost:8000/api/v1/datasources/sync

# Настройка расписания
# Редактируем core/cron/crontab.example
0 2 * * * /app/scripts/sync_data.sh
```

---

## 5. **Production развертывание**

### 🐳 **Docker Production**

```bash
# 1. Сборка production образов
make build

# 2. Настройка переменных окружения
cp .env.example .env.production

# 3. Настройка production конфигурации
vim .env.production

# 4. Запуск production
docker-compose -f docker-compose.production.yml up -d
```

### ☁️ **AWS ECS/EKS**

```bash
# 1. Terraform инфраструктура
cd terraform
terraform init
terraform plan
terraform apply

# 2. Helm deployment
cd deployment/helm
helm install ai-assistant ./ai-assistant/
```

### 🔧 **Настройка production**

#### **Переменные окружения**
```bash
# Основные
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# База данных
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://host:6379/0

# Qdrant
QDRANT_URL=http://host:6333

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# External APIs
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

#### **Nginx конфигурация**
```nginx
upstream ai_assistant {
    server app:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://ai_assistant;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 📊 **Health checks**

```bash
# Application health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/api/v1/health

# Detailed health
curl http://localhost:8000/api/v1/monitoring/health
```

---

## 6. **Мониторинг**

### 📈 **Grafana Dashboards**

```bash
# Запуск с мониторингом
make up-dev-full

# Grafana доступна на:
# http://localhost:3001
# Логин: admin
# Пароль: admin123
```

**Доступные дашборды:**
- **System Overview** - общие метрики системы
- **API Performance** - производительность API
- **Database Metrics** - метрики базы данных
- **Search Analytics** - аналитика поиска
- **User Activity** - активность пользователей

### 🔍 **Prometheus метрики**

```bash
# Prometheus доступен на:
# http://localhost:9090

# Основные метрики:
# - http_requests_total
# - response_time_seconds
# - database_connections
# - search_queries_total
# - ai_generation_requests
# - cache_hits_total
```

### 📊 **Real-time мониторинг**

```bash
# WebSocket подключение для real-time метрик
ws://localhost:8000/ws/metrics

# API endpoints
GET /api/v1/monitoring/metrics/current
GET /api/v1/monitoring/performance/summary
GET /api/v1/ws/stats
```

### 🚨 **Алертинг**

```bash
# Настройка алертов в monitoring/alertmanager/
vim monitoring/alertmanager/config.yml

# Правила алертов в monitoring/prometheus/
vim monitoring/prometheus/alerts.yml
```

---

## 7. **Решение проблем**

### 🔧 **Частые проблемы**

#### **Проблема: Порт 8000 занят**
```bash
# Найти процесс
lsof -i :8000
netstat -tulpn | grep 8000

# Убить процесс
pkill -f "python.*main.py"
pkill -f "uvicorn"

# Запустить на другом порту
uvicorn main:app --port 8001
```

#### **Проблема: База данных недоступна**
```bash
# Проверить статус
make status

# Перезапустить БД
docker-compose restart postgres

# Проверить подключение
docker-compose exec postgres pg_isready -U ai_user
```

#### **Проблема: Qdrant не работает**
```bash
# Проверить статус
curl http://localhost:6333/health

# Очистить данные
rm -rf ./data/qdrant/*

# Перезапустить
docker-compose restart qdrant
```

### 📋 **Диагностические команды**

```bash
# Системная проверка
python local/final_polish_check.py

# Проверка конфигурации
docker-compose config

# Проверка сети
docker network ls
docker network inspect ai-network

# Проверка volumes
docker volume ls
docker volume inspect ai-assistant_postgres_data
```

### 🔍 **Логи и отладка**

```bash
# Логи приложения
make logs-app

# Логи базы данных
make logs-db

# Все логи
make logs

# Детальная отладка
export LOG_LEVEL=DEBUG
make dev-debug
```

### 🆘 **Аварийное восстановление**

```bash
# Полный сброс
make down-volumes
make clean-data

# Восстановление из бэкапа
make restore-data BACKUP=filename.sql

# Переустановка
make install
make up-dev-full
```

---

## 8. **VK Teams интеграция**

AI Assistant включает полнофункциональную интеграцию с VK Teams через чат-бота с AI возможностями.

### 🚀 **Быстрый старт (5 минут)**

**Полное руководство:** [VK Teams Quick Start](docs/VK_TEAMS_QUICK_START.md)

```bash
# 1. Создайте бота в VK Teams (@MetaBot → /newbot)
# 2. Добавьте токен в .env
echo "VK_TEAMS_BOT_TOKEN=001.your_token_here" >> .env
echo "VK_TEAMS_ENABLED=true" >> .env

# 3. Настройте ngrok для разработки
ngrok http 8000
echo "VK_TEAMS_WEBHOOK_URL=https://abc123.ngrok.io/api/v1/vk-teams/webhook/events" >> .env

# 4. Запустите и настройте
python main.py --port 8000
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -d '{"email": "admin@vkteam.ru", "password": "admin"}' | jq -r '.access_token')
curl -X POST "http://localhost:8000/api/v1/vk-teams/bot/configure" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"bot_token": "001.your_token_here", "auto_start": true}'

# 5. Тестируйте в VK Teams: /start
```

### 🤖 **Возможности бота**

- **🔍 Семантический поиск** - поиск по всем подключенным источникам
- **📝 Генерация документов** - RFC, техдок, анализ требований
- **🔧 Code Review** - анализ кода и рекомендации по улучшению
- **💬 AI Чат** - интеллектуальные ответы на любые вопросы
- **📊 Аналитика** - статистика использования и мониторинг

### 📚 **Документация**

#### 📖 **Основные руководства:**
- **[🚀 Быстрый старт](docs/VK_TEAMS_QUICK_START.md)** - Настройка за 5 минут
- **[📘 Полное руководство](docs/VK_TEAMS_COMPLETE_SETUP_GUIDE.md)** - Детальная настройка с нуля
- **[🔐 VK OAuth Guide](docs/integrations/VK_OAUTH_GUIDE.md)** - Настройка авторизации через VK

#### 🔧 **Техническая документация:**
- **[VK Teams Integration](docs/integrations/VK_TEAMS_INTEGRATION.md)** - Архитектура и API
- **[VK Teams README](docs/integrations/VK_TEAMS_README.md)** - Обзор интеграции

### 💬 **Основные команды бота**

```bash
/start              # Приветствие и справка
/help               # Полный список команд
/search <запрос>    # Поиск информации
/generate <тема>    # Генерация документов
/analyze <код>      # Анализ кода
/review <код>       # Code review
/status             # Статус системы
/settings           # Настройки пользователя
```

### 🔧 **Управление ботом через API**

```bash
# Получение токена
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -d '{"email": "admin@vkteam.ru", "password": "admin"}' | jq -r '.access_token')

# Статус бота
curl "http://localhost:8000/api/v1/vk-teams/bot/status" \
  -H "Authorization: Bearer $TOKEN"

# Конфигурация бота
curl -X POST "http://localhost:8000/api/v1/vk-teams/bot/configure" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "bot_token": "001.your_token",
    "webhook_url": "https://your-domain.com/api/v1/vk-teams/webhook/events",
    "auto_start": true
  }'

# Запуск/остановка
curl -X POST "http://localhost:8000/api/v1/vk-teams/bot/start" \
  -H "Authorization: Bearer $TOKEN"

curl -X POST "http://localhost:8000/api/v1/vk-teams/bot/stop" \
  -H "Authorization: Bearer $TOKEN"

# Статистика использования
curl "http://localhost:8000/api/v1/vk-teams/bot/stats" \
  -H "Authorization: Bearer $TOKEN"
```

### 🔐 **Настройка безопасности (опционально)**

#### **VK OAuth авторизация:**
1. Создайте VK приложение: [vk.com/apps?act=manage](https://vk.com/apps?act=manage)
2. Настройте переменные окружения:

```bash
# VK OAuth Configuration
VK_OAUTH_ENABLED=true
VK_OAUTH_CLIENT_ID=12345678
VK_OAUTH_CLIENT_SECRET=your_secret_key
VK_OAUTH_REDIRECT_URI=https://your-domain.com/api/v1/auth/vk/callback

# Список разрешённых пользователей (VK ID)
ALLOWED_VK_USERS=123456789,987654321,555666777
```

#### **Ограничение доступа:**
```bash
# Через API
curl -X POST "http://localhost:8000/api/v1/vk-teams/bot/configure" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "allowed_users": ["123456789", "987654321"],
    "allowed_chats": ["chat_id_1", "chat_id_2"]
  }'
```

### 📊 **Мониторинг и диагностика**

```bash
# Проверка здоровья системы
curl "http://localhost:8000/api/v1/vk-teams/bot/health"

# Детальная статистика
curl "http://localhost:8000/api/v1/vk-teams/bot/stats" \
  -H "Authorization: Bearer $TOKEN" | jq

# Логи в реальном времени
tail -f app.log | grep -E "(vk.teams|bot|webhook)"

# Тест webhook'а
curl -X POST "http://localhost:8000/api/v1/vk-teams/webhook/test" \
  -d '{"test": "ping"}'
```

### 🚀 **Production развертывание**

Для production среды:

1. **Настройте HTTPS домен** вместо ngrok
2. **Используйте реальный webhook URL:** `https://your-domain.com/api/v1/vk-teams/webhook/events`
3. **Настройте мониторинг** и алерты
4. **Включите VK OAuth** для безопасности
5. **Настройте backup** конфигурации бота

**Подробная инструкция:** [Production Setup Guide](docs/VK_TEAMS_COMPLETE_SETUP_GUIDE.md#7-продвинутая-настройка)

---

## 9. **Работа с GUI**

### 🌐 **Веб-интерфейс**

```bash
# Запуск с frontend
make up-dev-full

# Доступ к интерфейсу
# http://localhost:3000
```

#### **Основные разделы:**
- **🏠 Dashboard** - обзор системы и метрики
- **🔍 Search** - семантический поиск документов
- **📝 Generate** - генерация RFC и документов
- **📊 Analytics** - аналитика использования
- **⚙️ Settings** - настройки системы
- **👥 Users** - управление пользователями

### 🔍 **Поиск документов**

#### **Интерфейс поиска:**
1. Выберите источники данных (Confluence, GitLab, Jira)
2. Введите поисковый запрос
3. Настройте фильтры (даты, теги, типы)
4. Выберите тип поиска (семантический/гибридный)

#### **Возможности:**
- **Smart Search** - ИИ понимает контекст запроса
- **Filtering** - фильтрация по источникам и метаданным
- **Highlighting** - подсветка релевантных фрагментов
- **Export** - экспорт результатов в различные форматы

### 📝 **Генерация документов**

#### **RFC Generation:**
1. Выберите **Generate → RFC**
2. Заполните форму:
   - Заголовок и описание
   - Тип RFC (архитектура, процесс, стандарт)
   - Путь к проекту (опционально)
   - Включить диаграммы
3. Нажмите **Generate**

#### **Возможности:**
- **Architecture Analysis** - автоматический анализ кода
- **Mermaid Diagrams** - генерация диаграмм
- **Multi-source Context** - использование всех источников
- **Templates** - профессиональные шаблоны

### 📊 **Аналитика и мониторинг**

#### **Dashboards:**
- **System Health** - состояние системы
- **Search Analytics** - статистика поиска
- **User Activity** - активность пользователей
- **Performance Metrics** - метрики производительности

#### **Real-time Updates:**
- WebSocket подключение для live данных
- Автоматическое обновление метрик
- Алерты и уведомления

### ⚙️ **Настройки системы**

#### **Data Sources:**
- Настройка подключений к источникам
- Управление синхронизацией
- Мониторинг статуса подключений

#### **Search Configuration:**
- Настройка весов источников
- Конфигурация поиска
- Управление индексами

#### **User Management:**
- Управление пользователями
- Настройка ролей и прав
- Аудит действий

---

## 10. **API Documentation**

### 📚 **Swagger UI**

```bash
# Интерактивная документация
http://localhost:8000/docs

# OpenAPI спецификация
http://localhost:8000/openapi.json
```

### 🔍 **Основные API endpoints**

#### **Поиск**
```bash
# Векторный поиск
POST /api/v1/vector-search/search
POST /api/v1/vector-search/search/enhanced

# Обычный поиск
POST /api/v1/search/
GET /api/v1/search/enhanced
```

#### **Генерация**
```bash
# RFC генерация
POST /api/v1/generate/rfc
POST /api/v1/generate/rfc/enhanced

# AI генерация
POST /api/v1/ai/generate
POST /api/v1/ai/analysis
```

#### **Аутентификация**
```bash
# Вход
POST /api/v1/auth/login

# Refresh токен
POST /api/v1/auth/refresh

# Профиль пользователя
GET /api/v1/auth/me
```

#### **Мониторинг**
```bash
# Метрики
GET /api/v1/monitoring/metrics/current
GET /api/v1/monitoring/performance/summary

# Здоровье системы
GET /health
GET /api/v1/health
```

### 🔐 **Аутентификация API**

```bash
# Получение токена
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Использование токена
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/v1/search/
```

---

## 11. **Архитектура**

### 🏗️ **Общая архитектура**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   AI Services   │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (LLM/Vector)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   Redis Cache   │    │   Qdrant        │
│   (Main DB)     │    │   (Session)     │    │   (Vector DB)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🔄 **Hexagonal Architecture**

```
     ┌─────────────────────────────────────────────────────────────┐
     │                    APPLICATION LAYER                        │
     │  ┌─────────────────────────────────────────────────────────┐│
     │  │                  DOMAIN LAYER                           ││
     │  │  ┌─────────────────────────────────────────────────────┐││
     │  │  │               CORE BUSINESS LOGIC                   │││
     │  │  │  • Search Services                                  │││
     │  │  │  • Generation Services                              │││
     │  │  │  • Analytics Services                               │││
     │  │  └─────────────────────────────────────────────────────┘││
     │  └─────────────────────────────────────────────────────────┘│
     └─────────────────────────────────────────────────────────────┘
                                    │
         ┌─────────────────────────────────────────────────────────┐
         │                 INFRASTRUCTURE LAYER                    │
         │  • Database Adapters                                    │
         │  • External API Clients                                 │
         │  • Message Brokers                                      │
         │  • File Systems                                         │
         └─────────────────────────────────────────────────────────┘
```

### 📦 **Модули системы**

#### **Core Modules:**
- **`app/`** - FastAPI приложение
- **`domain/`** - Бизнес-логика
- **`adapters/`** - Внешние интеграции
- **`infrastructure/`** - Инфраструктурные сервисы

#### **AI Modules:**
- **`domain/ai_analysis/`** - ИИ анализ
- **`domain/code_optimization/`** - Оптимизация кода
- **`domain/rfc_generation/`** - Генерация RFC

#### **Integration Modules:**
- **`domain/integration/`** - Интеграции с внешними системами
- **`infrastructure/vk_teams/`** - VK Teams интеграция

---

## 12. **Поддержка**

### 📚 **Документация**

- **[Функциональные требования](docs/requirements/FUNCTIONAL_NON_FUNCTIONAL_REQUIREMENTS.md)**
- **[Требования к тестированию](docs/requirements/TESTING_REQUIREMENTS.md)**
- **[Руководство разработчика](docs/guides/DEVELOPER_GUIDE.md)**
- **[Руководство по развертыванию](docs/guides/DEPLOYMENT_GUIDE.md)**
- **[VK Teams интеграция](docs/integrations/VK_TEAMS_INTEGRATION.md)**

### 🐛 **Сообщение об ошибках**

```bash
# Создание issue
1. Перейдите в Issues
2. Выберите соответствующий шаблон
3. Приложите логи и скриншоты
4. Укажите шаги для воспроизведения
```

### 💬 **Контакты**

- **📧 Email**: support@ai-assistant.com
- **💬 Telegram**: @ai_assistant_support
- **🌐 Wiki**: https://wiki.ai-assistant.com
- **📱 VK Teams**: Наш бот для быстрой поддержки

### 🔄 **Обновления**

```bash
# Проверка обновлений
git pull origin main

# Обновление зависимостей
pip install -r requirements.txt

# Применение миграций
make migrate

# Перезапуск системы
make restart
```

---

## 🎯 **Roadmap**

### 📅 **Ближайшие планы**
- [ ] **Мультиязычность** - поддержка русского и английского
- [ ] **Advanced Analytics** - детальная аналитика использования
- [ ] **File Upload** - загрузка собственных документов
- [ ] **Collaborative Features** - совместная работа с документами
- [ ] **Mobile App** - мобильное приложение

### 🚀 **Долгосрочные цели**
- [ ] **Enterprise SSO** - интеграция с корпоративными системами
- [ ] **AI Assistants** - специализированные ИИ помощники
- [ ] **Auto-Documentation** - автоматическая документация кода
- [ ] **Marketplace** - магазин плагинов и расширений

---

## 🧪 **Тестирование API**

### 🚀 **Быстрый тест API**

```bash
# Автоматический тест всех эндпоинтов
./test_api.sh

# Тест с performance метриками
./test_api.sh --performance

# Тест удаленного сервера
./test_api.sh http://your-server:8000
```

### 📋 **Ручное тестирование**

```bash
# Базовые проверки
curl -s http://localhost:8000/health | jq '.'
curl -s http://localhost:8000/api/v1/auth/sso/providers | jq '.'

# Тест генерации (без аутентификации)
curl -s -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello AI"}' | jq '.'

# Тест оптимизации
curl -s -X POST http://localhost:8000/api/v1/optimize \
  -H "Content-Type: application/json" \
  -d '{"target": "performance"}' | jq '.'
```

### 📖 **Документация API**

- **[API Testing Guide](docs/API_TESTING_GUIDE.md)** - Полное руководство по тестированию
- **[API Reference](docs/API_REFERENCE_COMPLETE.md)** - Документация всех эндпоинтов с curl примерами
- **[Swagger UI](http://localhost:8000/docs)** - Интерактивная документация API
- **[OpenAPI Spec](http://localhost:8000/openapi.json)** - Спецификация OpenAPI

### 🔧 **Полезные ссылки для тестирования**

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Adminer (DB)**: http://localhost:8080
- **Redis Commander**: http://localhost:8081
- **Qdrant**: http://localhost:6333
- **Ollama**: http://localhost:11434

---

## 👥 **Управление пользователями**

### 🔐 **Предустановленные пользователи**

```bash
# VK Team Admin (полные права)
Email: admin@vkteam.ru
Password: admin
Scopes: admin, basic, search, generate
Budget: $10,000

# Example Admin  
Email: admin@example.com
Password: admin
Scopes: admin, basic
Budget: $1,000

# Test User
Email: user@example.com  
Password: user123
Scopes: basic
Budget: $100
```

### 🛠️ **Создание пользователей**

```bash
# Создать обычного пользователя
python create_user.py create --email user@company.com --password secret123 --name "John Doe"

# Создать администратора
python create_user.py create --email admin@company.com --password admin123 --name "Admin User" --admin

# Просмотреть всех пользователей
python create_user.py list

# Информация о пользователе
python create_user.py info --email user@company.com
```

### 💰 **Система управления бюджетами**

AI Assistant включает продвинутую систему управления бюджетами с **автоматическим пополнением** и **мониторингом расходов**.

#### 🔄 **Автоматическое пополнение**

```bash
# Проверить статус бюджета
curl -X GET http://localhost:8000/api/v1/budget/status \
  -H "Authorization: Bearer $JWT_TOKEN"

# Ответ:
{
  "current_usage": 25.50,
  "budget_limit": 1000.0,
  "remaining_balance": 974.50,
  "usage_percentage": 2.55,
  "budget_status": "ACTIVE",
  "last_refill": {
    "amount": 1000.0,
    "timestamp": "2024-01-15T00:00:00Z",
    "type": "reset"
  }
}
```

#### 📊 **История пополнений**

```bash
# Просмотреть историю пополнений
curl -X GET http://localhost:8000/api/v1/budget/history \
  -H "Authorization: Bearer $JWT_TOKEN"

# Для администраторов - статистика системы
curl -X GET http://localhost:8000/api/v1/budget/system-stats \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### ⚡ **Ручное пополнение (для администраторов)**

```bash
# Пополнить бюджет пользователя
curl -X POST http://localhost:8000/api/v1/budget/refill \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "amount": 500.0,
    "refill_type": "add",
    "reason": "Дополнительное пополнение"
  }'

# Запустить пополнение немедленно
curl -X POST http://localhost:8000/api/v1/budget/scheduler/run-now \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### 🔧 **Конфигурация автоматического пополнения**

Настройка в файле `config/budget_config.yml`:

```yaml
auto_refill:
  enabled: true
  schedule:
    cron: "0 0 * * *"  # Каждый день в полночь
    timezone: "Europe/Moscow"
  refill_settings:
    refill_type: "reset"  # reset или add
    by_role:
      admin:
        amount: 10000.0
        reset_usage: true
      user:
        amount: 1000.0
        reset_usage: true
      basic:
        amount: 100.0
        reset_usage: true
    individual_users:
      "admin@vkteam.ru":
        amount: 15000.0
        custom_schedule: "0 0 1 * *"  # Раз в месяц
```

#### 🚨 **Мониторинг бюджетов**

```bash
# Получить метрики для мониторинга
curl -X GET http://localhost:8000/api/v1/budget/monitoring/budget/metrics \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Перезапустить планировщик
curl -X POST http://localhost:8000/api/v1/budget/scheduler/restart \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### 📈 **Типы пополнения**

1. **Reset** - обнуляет использование, устанавливает новый лимит
2. **Add** - добавляет к существующему лимиту, накапливает остатки

#### 🛡️ **Безопасность**

- Лимиты на сумму разового пополнения
- Аудит всех операций
- Защита от злоупотреблений
- Автоматические уведомления

### 🚀 **Аутентификация через API**

```bash
# Получить JWT токен
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@vkteam.ru", "password": "admin"}'

# Использовать токен
export JWT_TOKEN="your_jwt_token_here"
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/v1/users
```

### 📚 **Документация по пользователям**

- **[User Management Guide](docs/USER_MANAGEMENT_GUIDE.md)** - Полное руководство по управлению пользователями
- **[Budget System Guide](docs/BUDGET_SYSTEM_GUIDE.md)** - Подробное руководство по системе бюджетов
- **[Authentication Guide](docs/guides/AUTH_GUIDE.md)** - Подробное руководство по аутентификации
- **[Security Guide](docs/guides/SECURITY_GUIDE.md)** - Рекомендации по безопасности

---

## 📄 **Лицензия**

Этот проект лицензируется под MIT License - см. файл [LICENSE](LICENSE) для деталей.

---

## 🙏 **Благодарности**

- **FastAPI** - для отличного веб-фреймворка
- **OpenAI** - за мощные языковые модели
- **Qdrant** - за векторную базу данных
- **React** - за современный UI фреймворк
- **Docker** - за контейнеризацию
- **Наша команда** - за неустанную работу

---

<div align="center">

**🚀 Готов к запуску! Создан для enterprise, оптимизирован для производительности.**

[⬆️ Вернуться к началу](#-ai-assistant-mvp---enterprise-ready)

</div>
