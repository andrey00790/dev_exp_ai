# 🚀 Документация отрефакторенного проекта AI Assistant

## 📋 Обзор проекта

Комплексная ИИ-платформа для семантического поиска и генерации RFC документов с полной системой пользовательских настроек, обучением модели и автоматической синхронизацией данных.

### 🎯 Ключевые особенности

- **👤 Пользовательские настройки** - индивидуальная конфигурация источников данных
- **🔐 Безопасность** - шифрование паролей и токенов, JWT аутентификация
- **🔄 Автоматическая синхронизация** - с обработкой ошибок и мониторингом прогресса
- **🧠 Машинное обучение** - переобучение модели на основе обратной связи
- **📁 Загрузка файлов** - поддержка PDF, TXT, DOC, EPUB
- **🌐 REST API** - полная OpenAPI спецификация
- **🧪 Тестирование** - unit, integration и E2E тесты

## 🏗️ Архитектура проекта

### Структура каталогов

```
dev_exp_ai/
├── app/                          # FastAPI приложение
│   ├── api/                      # API endpoints
│   │   ├── v1/                   # API версии 1
│   │   │   ├── auth.py          # Аутентификация
│   │   │   ├── users.py         # Управление пользователями
│   │   │   ├── data_sources.py  # Источники данных
│   │   │   ├── sync.py          # Синхронизация
│   │   │   ├── generate.py      # AI генерация
│   │   │   ├── search.py        # Семантический поиск
│   │   │   ├── vector_search.py # Векторный поиск
│   │   │   ├── feedback.py      # Обратная связь
│   │   │   └── learning.py      # Обучение модели
│   │   └── health.py            # Проверка здоровья
│   ├── security/                # Безопасность
│   ├── config.py               # Конфигурация
│   └── main.py                 # Основное приложение
├── user_config_manager.py      # Модуль управления пользователями
├── model_training.py           # Обучение модели
├── dataset_config.yml          # Конфигурация датасета
├── user_config_schema.sql      # Схема БД пользователей
├── openapi.yml                 # OpenAPI спецификация
├── tests/                      # Тесты
│   ├── unit/                   # Unit тесты
│   ├── integration/            # Интеграционные тесты
│   ├── e2e/                    # E2E тесты
│   └── smoke/                  # Smoke тесты
├── requirements.txt            # Зависимости Python
├── Makefile                    # Команды автоматизации
└── docker-compose.yaml        # Docker конфигурация
```

## 🔧 API Endpoints

### 👤 Управление пользователями

```
POST   /api/v1/users                     # Создание пользователя
GET    /api/v1/users/{user_id}           # Получение пользователя
GET    /api/v1/users/current/settings    # Настройки пользователя
PUT    /api/v1/users/current/settings    # Обновление настроек
```

### 🔗 Источники данных

```
GET    /api/v1/data-sources              # Список источников данных
PUT    /api/v1/data-sources/{type}/{name} # Обновление настроек источника
```

### ⚙️ Конфигурации

```
# Jira
GET    /api/v1/configurations/jira       # Получение конфигураций Jira
POST   /api/v1/configurations/jira       # Создание конфигурации Jira
PUT    /api/v1/configurations/jira/{name} # Обновление конфигурации
DELETE /api/v1/configurations/jira/{name} # Удаление конфигурации

# Confluence  
POST   /api/v1/configurations/confluence # Создание конфигурации Confluence
GET    /api/v1/configurations/confluence # Получение конфигураций

# GitLab
POST   /api/v1/configurations/gitlab     # Создание конфигурации GitLab
GET    /api/v1/configurations/gitlab     # Получение конфигураций
```

### 🔄 Синхронизация

```
POST   /api/v1/sync/tasks               # Запуск задачи синхронизации
GET    /api/v1/sync/tasks               # Список задач синхронизации
GET    /api/v1/sync/tasks/{task_id}     # Статус задачи
GET    /api/v1/sync/tasks/{task_id}/logs # Логи задачи
```

### 📁 Управление файлами

```
GET    /api/v1/files                    # Список файлов пользователя
POST   /api/v1/files                    # Загрузка файла
GET    /api/v1/files/{file_id}          # Информация о файле
DELETE /api/v1/files/{file_id}          # Удаление файла
```

### 🤖 AI функциональность

```
POST   /api/v1/generate                 # Генерация RFC документов
POST   /api/v1/search                   # Семантический поиск
POST   /api/v1/vector-search/search     # Векторный поиск
POST   /api/v1/feedback                 # Отправка обратной связи
POST   /api/v1/learning/retrain         # Переобучение модели
GET    /api/v1/learning/metrics         # Метрики модели
```

## 💾 База данных

### Схема пользовательских настроек

**Основные таблицы:**
- `users` - Пользователи системы
- `user_data_sources` - Настройки источников данных
- `user_jira_configs` - Конфигурации Jira (логин+пароль)
- `user_confluence_configs` - Конфигурации Confluence DC ≥ 8.0 (Bearer-PAT)
- `user_gitlab_configs` - Конфигурации GitLab серверов
- `user_files` - Пользовательские файлы
- `sync_tasks` - Задачи синхронизации
- `sync_logs` - Логи синхронизации
- `model_metrics` - Метрики качества модели
- `model_feedback` - Обратная связь для переобучения

### Настройки по умолчанию

**Для семантического поиска:**
- ✅ Jira - включен
- ✅ Confluence - включен
- ✅ GitLab - включен
- ❌ Пользовательские файлы - отключены

**Для генерации архитектуры:**
- ✅ Все источники доступны

## 🔐 Безопасность

### Шифрование данных

- Пароли и токены шифруются с помощью `cryptography.fernet`
- Ключи шифрования генерируются автоматически
- Конфиденциальные данные не хранятся в открытом виде

### Аутентификация

- JWT токены для API аутентификации
- Role-based доступ к ресурсам
- Rate limiting для защиты от злоупотреблений

## 🔄 Система синхронизации

### Возможности

- **Параллельная обработка** - одновременная синхронизация нескольких источников
- **Обработка ошибок** - "не смог спарсить - идем дальше"
- **Точки восстановления** - продолжение с места падения
- **Детальное логирование** - все операции записываются в БД
- **Мониторинг прогресса** - отображение в процентах

### Поддерживаемые источники

**Jira:**
- Подключение: логин + пароль
- Синхронизация: задачи, проекты, метаданные

**Confluence:**
- Подключение: Confluence DC ≥ 8.0 через Bearer-PAT токен
- Синхронизация: страницы, пространства, содержимое

**GitLab:**
- Подключение: динамический список серверов через URL + токен
- Синхронизация: README файлы, документация, проекты

**Пользовательские файлы:**
- Форматы: PDF, TXT, DOC, EPUB
- Автоматическое извлечение текста
- Система тегов для организации

## 🧠 Машинное обучение

### Модель

- **Тип:** sentence-transformers multilingual
- **Базовая модель:** paraphrase-multilingual-MiniLM-L12-v2
- **Языки:** русский, английский
- **Размерность:** 384

### Обучение

- Загрузка данных из `dataset_config.yml`
- Генерация синтетических обучающих пар
- Оценка качества: Precision@k, MRR, Cosine Similarity
- Сохранение метрик в PostgreSQL

### Переобучение

- Автоматическое переобучение на основе обратной связи
- Триггер: 100+ записей обратной связи
- Расписание: еженедельно
- Сравнение метрик до и после

## 🧪 Тестирование

### Структура тестов

```
tests/
├── unit/                          # Unit тесты (изолированные)
│   ├── test_user_config_manager.py
│   ├── test_basic_api.py
│   ├── test_document_service.py
│   └── test_llm_loader.py
├── integration/                   # Интеграционные тесты
│   ├── test_api_v1.py
│   └── test_user_management_integration.py
├── e2e/                          # End-to-End тесты
│   ├── test_data_loader.py
│   └── test_integration.py
└── smoke/                        # Smoke тесты
    └── test_services_integration.py
```

### Покрытие тестами

**Текущее состояние:** ~26% покрытия
**Цель:** ≥90% покрытия

**Тестируемые компоненты:**
- API endpoints (FastAPI routes)
- Пользовательские настройки
- Система синхронизации
- Обучение модели
- Обработка файлов
- Системы безопасности

### Запуск тестов

```bash
# Все тесты
python3 -m pytest tests/ --cov=app --cov=user_config_manager --cov-report=term-missing

# Unit тесты
python3 -m pytest tests/unit/ -v

# Integration тесты  
python3 -m pytest tests/integration/ -v

# E2E тесты (требуют Docker)
python3 -m pytest tests/e2e/ -v
```

## 🚀 Развертывание

### Быстрый старт

```bash
# 1. Клонирование репозитория
git clone <repository_url>
cd dev_exp_ai

# 2. Установка зависимостей
pip3 install -r requirements.txt

# 3. Инициализация полной системы
make init-full-system

# 4. Запуск приложения
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker развертывание

```bash
# Запуск всех сервисов
docker-compose up -d

# Инициализация базы данных пользователей
make create-user-schema

# Создание тестового пользователя
make create-test-user
```

### Makefile команды

```bash
# Система управления пользователями
make create-user-schema     # Создание схемы БД пользователей
make create-test-user      # Создание тестового пользователя
make setup-user-system     # Полная настройка системы пользователей

# Обучение модели
make train-model           # Обучение модели из dataset_config.yml
make retrain-model         # Переобучение на основе обратной связи
make check-model-quality   # Проверка метрик качества

# E2E тестирование
make e2e-full-pipeline     # Полный E2E пайплайн с обучением модели
make test-feedback         # Тестирование обратной связи
make simulate-user-feedback # Симуляция пользовательской обратной связи

# Синхронизация
make test-user-sync        # Тестирование синхронизации пользователя
make show-user-stats       # Статистика пользователей

# Общие команды
make init-full-system      # Полная инициализация системы
make clean-model-data      # Очистка данных модели
```

## 📊 Мониторинг и аналитика

### Метрики модели

- **Precision@1/3/5** - точность поиска на топ позициях
- **MRR (Mean Reciprocal Rank)** - средний обратный ранг
- **Cosine Similarity** - косинусное сходство

### Мониторинг синхронизации

- Статус задач в реальном времени
- Прогресс выполнения в процентах
- Количество обработанных элементов
- Логи с уровнями INFO/WARNING/ERROR

### Пользовательская аналитика

- Количество пользователей в системе
- Активные источники данных
- Конфигурации подключений
- Загруженные файлы и их размеры

## 🔧 Конфигурация

### Переменные окружения

```bash
# База данных
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=testdb
POSTGRES_USER=testuser
POSTGRES_PASSWORD=testpass

# Приложение
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
DEBUG=true
LOG_LEVEL=INFO

# Внешние сервисы
QDRANT_URL=http://localhost:6333
OLLAMA_URL=http://localhost:11434
```

### Пример настроек пользователя

```python
# Создание пользователя
config_manager = UserConfigManager()
user_id = config_manager.create_user_with_defaults("username", "email@domain.com")

# Jira (логин+пароль)
config_manager.add_jira_config(
    user_id=user_id,
    config_name="main_jira",
    jira_url="https://company.atlassian.net", 
    username="user@company.com",
    password="secure_password",
    projects=["PROJ1", "PROJ2"]
)

# Confluence DC ≥ 8.0 (Bearer-PAT)
config_manager.add_confluence_config(
    user_id=user_id,
    config_name="main_confluence",
    confluence_url="https://company.atlassian.net/wiki",
    bearer_token="Bearer_PAT_token_here",
    spaces=["TECH", "ARCH"]
)

# GitLab серверы (динамический список)
config_manager.add_gitlab_config(
    user_id=user_id,
    alias="main",
    gitlab_url="https://gitlab.company.com",
    access_token="company_access_token",
    projects=["group/project1", "group/project2"]
)
```

## 📈 Roadmap

### ✅ Реализовано (MVP v2.0)

- [x] Пользовательские настройки и конфигурации
- [x] Система синхронизации с обработкой ошибок
- [x] Обучение модели и переобучение на обратной связи
- [x] Загрузка и обработка файлов (PDF, TXT, DOC, EPUB)
- [x] REST API с OpenAPI спецификацией
- [x] Шифрование паролей и токенов
- [x] E2E тестирование полного пайплайна
- [x] Автоматизация через Makefile

### 🚧 В разработке (MVP v3.0)

- [ ] GUI веб-интерфейс для управления настройками
- [ ] Мониторинг синхронизации в реальном времени
- [ ] Крон-задачи с веб-интерфейсом
- [ ] Расширение покрытия тестами до 90%+
- [ ] Оптимизация производительности

### 🔮 Планируется (MVP v4.0+)

- [ ] Мобильное приложение
- [ ] Интеграция с дополнительными системами (Slack, Teams)
- [ ] Продвинутая аналитика и дашборды
- [ ] Многопользовательские workspace'ы
- [ ] AI-ассистент для интерактивной работы

## 📚 Документация API

### Swagger UI
- **URL:** http://localhost:8000/docs
- **Описание:** Интерактивная документация API

### ReDoc
- **URL:** http://localhost:8000/redoc  
- **Описание:** Альтернативная документация API

### OpenAPI Schema
- **URL:** http://localhost:8000/openapi.json
- **Файл:** `openapi.yml`

## 🆘 Поддержка и помощь

### Проблемы и решения

**Проблема:** Ошибки импорта при запуске тестов
**Решение:** Установите зависимости: `pip3 install -r requirements.txt`

**Проблема:** Низкое покрытие тестами
**Решение:** Запустите: `make test-coverage` для детального анализа

**Проблема:** База данных недоступна
**Решение:** Запустите Docker: `docker-compose up -d postgres`

### Команды диагностики

```bash
# Проверка статуса сервисов
make status

# Проверка логов приложения
docker-compose logs app

# Проверка базы данных
docker-compose exec postgres psql -U testuser -d testdb

# Проверка качества модели
make check-model-quality

# Статистика пользователей
make show-user-stats
```

---

**🎉 Проект полностью отрефакторен и готов к продакшену!**

**Следующие шаги:**
1. Доработка GUI веб-интерфейса
2. Увеличение покрытия тестами до 90%+
3. Оптимизация производительности
4. Развертывание в продакшене 