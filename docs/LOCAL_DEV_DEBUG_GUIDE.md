# 🛠️ AI Assistant - Local Development & Debug Guide

**Версия:** 2.0  
**Дата:** Январь 2025  
**Статус:** Актуальный  

---

## 🎯 Быстрый старт (5 минут)

### 1. Предварительные требования

**Системные требования:**
- Python 3.11+
- Node.js 16+
- Docker Desktop
- Git
- 8GB RAM минимум

**Проверка системы:**
```bash
python --version          # >= 3.11
node --version            # >= 16
docker --version          # >= 20.10
git --version            # >= 2.30
```

### 2. Установка и настройка

```bash
# 1. Клонирование репозитория
git clone <repository-url>
cd dev_exp_ai

# 2. Автоматическая настройка окружения
make quick-start

# 3. Создание .env файла
cp env.example .env
# Отредактируйте переменные окружения
```

### 3. Запуск в development режиме

```bash
# Запуск инфраструктуры (БД, Redis, Qdrant)
make dev-infra-up

# Запуск API сервера (в отдельном терминале)
make dev

# Запуск фронтенда (в третьем терминале)
cd frontend
npm run dev
```

**Доступные эндпоинты:**
- 🌐 **Frontend:** http://localhost:3000
- 🔥 **API:** http://localhost:8000
- 📚 **API Docs:** http://localhost:8000/docs
- 🏥 **Health:** http://localhost:8000/health

---

## 🔧 Переменные окружения

### Основные переменные (.env):

```bash
# Основные настройки
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
SECRET_KEY=your-development-secret-key

# База данных
DATABASE_URL=postgresql://ai_user:ai_password_dev@localhost:5432/ai_assistant

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant (векторная БД)
QDRANT_URL=http://localhost:6333

# AI APIs (необязательно для dev)
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key

# Мониторинг
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
```

### Дополнительные переменные:

```bash
# Аутентификация
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# Upload лимиты
MAX_UPLOAD_SIZE=10MB
ALLOWED_EXTENSIONS=.pdf,.txt,.md,.docx

# Мониторинг
SENTRY_DSN=https://your-sentry-dsn
ENABLE_METRICS=true
```

---

## 🏗️ Архитектура разработки

### Структура проекта:

```
dev_exp_ai/
├── app/                    # FastAPI backend
│   ├── api/               # API endpoints
│   ├── core/              # Базовые утилиты  
│   ├── models/            # Модели данных
│   ├── services/          # Бизнес-логика
│   └── main.py           # Точка входа
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # React компоненты
│   │   ├── pages/         # Страницы
│   │   └── services/      # API клиенты
│   └── package.json
├── tests/                 # Тесты
├── docs/                  # Документация  
└── deployment/           # Docker/K8s configs
```

### Паттерны разработки:

1. **API-first approach** - OpenAPI спецификация
2. **Async/await** - Асинхронные операции
3. **Dependency injection** - FastAPI DI
4. **Type hints** - Строгая типизация
5. **Pydantic** - Валидация данных

---

## 🔍 Отладка и troubleshooting

### Основные команды отладки:

```bash
# Проверка статуса всех сервисов
make status

# Просмотр логов
make logs

# Просмотр логов конкретного сервиса
docker logs ai-assistant-backend -f

# Подключение к БД
make db-connect

# Сброс БД
make db-reset

# Запуск тестов
make test

# Проверка качества кода
make lint
```

### Отладка API:

```bash
# Запуск в debug режиме
export DEBUG=true
python -m uvicorn app.main:app --reload --log-level debug

# Интерактивная отладка с pdb
python -m pdb -m uvicorn app.main:app --reload

# Профилирование производительности
python -m cProfile -o profile.prof -m uvicorn app.main:app
```

### Отладка фронтенда:

```bash
# Запуск в debug режиме
cd frontend
npm run dev -- --debug

# Проверка React DevTools
# Установите расширение React Developer Tools

# Анализ bundle
npm run build:analyze
```

---

## 🧪 Тестирование

### Запуск тестов:

```bash
# Все тесты
make test

# Unit тесты
make test-unit

# Integration тесты
make test-integration

# E2E тесты
make test-e2e

# Тесты с покрытием
make test-coverage
```

### Отладка тестов:

```bash
# Запуск одного теста
pytest tests/test_search.py::TestSearch::test_basic_search -v

# Отладка с pdb
pytest tests/test_search.py::TestSearch::test_basic_search --pdb

# Просмотр print statements
pytest tests/test_search.py::TestSearch::test_basic_search -s
```

---

## 🔧 Hot reload и разработка

### Backend hot reload:

Используется uvicorn с `--reload` флагом:

```bash
# Автоматическая перезагрузка при изменении .py файлов
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend hot reload:

React development server с HMR:

```bash
cd frontend
npm run dev  # Перезагрузка при изменении файлов
```

### Database migrations:

```bash
# Создание миграции
alembic revision --autogenerate -m "Add new table"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1
```

---

## 🚨 Типичные проблемы и решения

### Проблема: Порт уже занят

```bash
# Найти процесс использующий порт
lsof -i :8000

# Завершить процесс
kill -9 <PID>

# Или использовать другой порт
export PORT=8001
python -m uvicorn app.main:app --reload --port $PORT
```

### Проблема: Ошибка подключения к БД

```bash
# Проверить статус PostgreSQL
docker ps | grep postgres

# Перезапустить БД
make db-restart

# Проверить логи БД
docker logs ai-assistant-postgres
```

### Проблема: Не работает векторный поиск

```bash
# Проверить Qdrant
curl http://localhost:6333/

# Перезапустить Qdrant
docker restart ai-assistant-qdrant

# Проверить коллекции
curl http://localhost:6333/collections
```

### Проблема: Медленная работа API

```bash
# Включить профилирование
export ENABLE_PROFILING=true

# Проверить метрики
curl http://localhost:8000/metrics

# Проверить подключения к БД
curl http://localhost:8000/health
```

---

## 🔨 Инструменты разработки

### Рекомендуемые IDE:

1. **VS Code** с расширениями:
   - Python
   - Pylance
   - REST Client
   - Docker
   - GitLens

2. **PyCharm Professional** (для backend)
3. **WebStorm** (для frontend)

### Useful extensions:

```bash
# VS Code settings.json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black"
}
```

### Debugging configuration:

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/app/main.py",
      "console": "integratedTerminal",
      "env": {
        "ENVIRONMENT": "development"
      }
    }
  ]
}
```

---

## 📋 Checklist для разработки

### Перед началом работы:
- [ ] Проверить актуальность веток
- [ ] Обновить зависимости (`pip install -r requirements.txt`)
- [ ] Запустить тесты (`make test`)
- [ ] Проверить переменные окружения

### Перед коммитом:
- [ ] Запустить линтеры (`make lint`)
- [ ] Проверить тесты (`make test`)
- [ ] Обновить документацию
- [ ] Проверить типы (`mypy app/`)

### Перед pull request:
- [ ] Полный тест-сьют (`make test-all`)
- [ ] Проверка безопасности (`make security-check`)
- [ ] Обновить CHANGELOG.md
- [ ] Проверить производительность

---

## 📞 Поддержка

**Получить помощь:**
- 📧 Slack: `#ai-assistant-dev`
- 🐛 Issues: GitHub Issues
- 📖 Docs: `/docs` folder
- 🤝 Code Review: Pull Requests

**Быстрые команды:**
```bash
make help              # Показать все доступные команды
make status            # Статус всех сервисов  
make logs              # Логи системы
make clean             # Очистка временных файлов
make reset             # Полный сброс окружения
```

---

**Минимальная версия окружения:**
- Python 3.11+
- Node.js 16+
- Docker 20.10+
- 8GB RAM
- 10GB свободного места

**Время первого запуска:** ~5-10 минут  
**Время обычного запуска:** ~30 секунд 