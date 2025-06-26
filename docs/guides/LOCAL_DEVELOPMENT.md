# 🚀 Локальная разработка AI Assistant MVP

Это руководство поможет быстро запустить AI Assistant MVP на локальной машине для разработки и тестирования.

## 📋 Системные требования

### Обязательные компоненты
- **Docker** >= 20.10
- **Docker Compose** >= 2.0
- **Git** >= 2.30
- **curl** (для проверки статуса)

### Рекомендуемые компоненты
- **Node.js** >= 18 (для frontend разработки)
- **Python** >= 3.11 (для backend разработки)
- **Helm** >= 3.0 (для Kubernetes деплоя)

### Системные ресурсы
- **RAM**: минимум 8GB, рекомендуется 16GB
- **Диск**: минимум 20GB свободного места
- **CPU**: минимум 4 ядра

## ⚡ Быстрый старт

### 1. Клонирование проекта
```bash
git clone <repository-url>
cd ai-assistant-mvp
```

### 2. Запуск системы одной командой
```bash
make start
```

Эта команда:
- ✅ Проверит системные требования
- ✅ Создаст файл `.env.local` с настройками по умолчанию
- ✅ Запустит все Docker сервисы
- ✅ Дождется готовности всех компонентов
- ✅ Покажет статус системы

### 3. Проверка статуса
```bash
make status
```

### 4. Остановка системы
```bash
make stop
```

## 🌐 Доступные URL

После успешного запуска будут доступны:

| Сервис | URL | Описание |
|--------|-----|----------|
| **Frontend** | http://localhost:3000 | Веб-интерфейс приложения |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger документация |
| **Qdrant** | http://localhost:6333/dashboard | Векторная база данных |
| **PostgreSQL** | localhost:5432 | Основная база данных |

## 🛠️ Команды разработки

### Основные команды
```bash
make help          # Показать все доступные команды
make start          # Запустить всю систему
make stop           # Остановить систему
make restart        # Перезапустить систему
make status         # Показать статус сервисов
make logs           # Показать логи всех сервисов
make clean          # Очистить все данные и контейнеры
```

### Тестирование
```bash
make test           # Запустить все тесты
make test-unit      # Только юнит тесты
make test-integration # Интеграционные тесты
make test-e2e       # End-to-end тесты
```

### Логи и отладка
```bash
make logs           # Все логи
make logs-app       # Логи backend
make logs-frontend  # Логи frontend

# Логи конкретного сервиса
docker compose -f deployment/docker/docker-compose.yaml logs -f postgres
docker compose -f deployment/docker/docker-compose.yaml logs -f qdrant
```

## 🔧 Конфигурация

### Переменные окружения
Файл `.env.local` создается автоматически со следующими настройками:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_assistant
QDRANT_HOST=localhost
ENVIRONMENT=development
```

### Кастомизация конфигурации
Для изменения настроек отредактируйте `.env.local`:

```bash
# Настройки базы данных
DATABASE_URL=postgresql://user:password@host:port/database

# Настройки Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Режим работы
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# AI/LLM настройки
OPENAI_API_KEY=your-api-key
ANTHROPIC_API_KEY=your-api-key
```

## 🐳 Docker Compose конфигурации

Проект включает несколько Docker Compose файлов для разных сценариев:

| Файл | Назначение |
|------|------------|
| `docker-compose.yaml` | Основная локальная разработка |
| `docker-compose.prod.yml` | Production конфигурация |
| `docker-compose.simple.yml` | Минимальная конфигурация |
| `docker-compose.e2e.yml` | End-to-end тестирование |

### Запуск конкретной конфигурации
```bash
# Production конфигурация
docker compose -f deployment/docker/docker-compose.prod.yml up -d

# Минимальная конфигурация (только БД и Qdrant)
docker compose -f deployment/docker/docker-compose.simple.yml up -d
```

## 🔍 Отладка и решение проблем

### Проверка статуса сервисов
```bash
# Статус Docker контейнеров
docker compose -f deployment/docker/docker-compose.yaml ps

# Проверка health checks
curl http://localhost:8000/health
curl http://localhost:6333/dashboard
```

### Частые проблемы

#### 1. Порты уже заняты
```bash
# Проверить какие порты заняты
lsof -i :8000
lsof -i :3000
lsof -i :5432
lsof -i :6333

# Остановить конфликтующие процессы
sudo kill -9 <PID>
```

#### 2. Недостаточно памяти
```bash
# Увеличить лимиты Docker
# Docker Desktop -> Settings -> Resources -> Memory: 8GB+
```

#### 3. Проблемы с базой данных
```bash
# Пересоздать базу данных
make clean
make start

# Проверить подключение к БД
docker exec -it $(docker compose -f deployment/docker/docker-compose.yaml ps -q postgres) \
  psql -U postgres -d ai_assistant -c "SELECT version();"
```

#### 4. Проблемы с Qdrant
```bash
# Проверить статус Qdrant
curl http://localhost:6333/dashboard

# Пересоздать Qdrant данные
docker volume rm ai_assistant_qdrant_data
make restart
```

### Логи для отладки
```bash
# Подробные логи приложения
docker compose -f deployment/docker/docker-compose.yaml logs -f app

# Логи с временными метками
docker compose -f deployment/docker/docker-compose.yaml logs -f -t

# Последние N строк логов
docker compose -f deployment/docker/docker-compose.yaml logs --tail=100 app
```

## 🔄 Обновление и синхронизация

### Обновление кода
```bash
git pull origin main
make restart
```

### Обновление зависимостей
```bash
# Python зависимости
pip install -r config/environments/requirements.txt --upgrade

# Frontend зависимости
cd frontend && npm update

# Docker образы
docker compose -f deployment/docker/docker-compose.yaml pull
make restart
```

### Синхронизация данных
```bash
# Загрузка тестовых данных
make db-seed

# Запуск синхронизации источников данных
curl -X POST http://localhost:8000/api/v1/sync/run-startup-sync
```

## 📊 Мониторинг разработки

### Метрики производительности
```bash
# Использование ресурсов контейнерами
docker stats

# Размер Docker томов
docker system df

# Проверка производительности API
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
```

### Health checks
```bash
# Автоматическая проверка всех сервисов
make health-check

# Ручная проверка
curl -f http://localhost:8000/health && echo "✅ Backend OK"
curl -f http://localhost:3000 && echo "✅ Frontend OK"
curl -f http://localhost:6333/dashboard && echo "✅ Qdrant OK"
```

## 🚀 Продвинутые сценарии

### Разработка только backend
```bash
# Запустить только базовые сервисы
make start-minimal

# Запустить backend локально
PYTHONPATH=. python run_server.py
```

### Разработка только frontend
```bash
# Запустить backend в Docker
make start

# Запустить frontend локально
cd frontend
npm run dev
```

### Тестирование в изоляции
```bash
# Запустить тесты в Docker
docker run --rm -v $(pwd):/app -w /app python:3.11 \
  bash -c "pip install -r config/environments/requirements.txt && pytest tests/"
```

## 📚 Дополнительные ресурсы

- [Руководство по продакшн деплою](PRODUCTION_DEPLOYMENT.md)
- [Kubernetes деплой с Helm](KUBERNETES_DEPLOYMENT.md)
- [Руководство разработчика](DEVELOPER_GUIDE.md)
- [API документация](../architecture/API_DOCS.md)
- [Архитектура системы](../architecture/ARCHITECTURE.md)

---

**💡 Совет**: Для максимальной производительности рекомендуется выделить Docker минимум 8GB RAM и использовать SSD диск. 