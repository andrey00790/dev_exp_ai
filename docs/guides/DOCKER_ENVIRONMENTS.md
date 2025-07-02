# 🐳 Docker Environments Guide

## Обзор

Все Docker конфигурации централизованы в директории `deployment/docker/` для удобного управления различными окружениями.

## 🏗️ Структура

```
deployment/docker/
├── docker-compose.dev.yml      # Разработка (с профилями)
├── docker-compose.tests.yml    # Тестирование (с профилями) 
├── docker-compose.full.yml     # Полная система
├── docker-compose.prod.yml     # Production
├── docker-compose.load-test.yml # Нагрузочные тесты
├── Dockerfile                  # Основной образ
├── Dockerfile.test             # Образ для тестов
├── Dockerfile.test-loader      # Загрузчик тестовых данных
└── scripts/
    └── load-test-data.py       # Скрипт загрузки данных
```

## 🔧 Окружение разработки

### Базовая инфраструктура
```bash
make up-dev
```
**Запускает:**
- PostgreSQL (localhost:5432)
- Redis (localhost:6379) 
- Qdrant (localhost:6333)

**Для запуска приложения:**
```bash
make dev  # Локально с инфраструктурой в Docker
```

### Полное окружение разработки
```bash
make up-dev-full
```
**Дополнительно запускает:**
- Adminer (localhost:8080) - управление БД
- Redis Commander (localhost:8081) - управление Redis
- Само приложение в Docker

### С локальным LLM
```bash
make up-dev-with-llm
```
**Дополнительно запускает:**
- Ollama (localhost:11434) - локальные LLM модели

### С мониторингом
```bash
make up-dev-monitoring
```
**Дополнительно запускает:**
- Grafana (localhost:3001) - admin/admin123
- Prometheus (localhost:9090)

## 🧪 Тестовые окружения

### Базовое тестовое окружение
```bash
make up-test
```
**Запускает:**
- Test PostgreSQL (localhost:5433)
- Test Redis (localhost:6380)
- Test Qdrant (localhost:6335)
- Test App (localhost:8001)

### E2E тестовое окружение
```bash
make up-test-e2e
```
**Дополнительно запускает:**
- Jira (localhost:8082)
- Confluence (localhost:8083)
- GitLab (localhost:8084)
- Elasticsearch (localhost:9201)
- ClickHouse (localhost:8125)
- YDB (localhost:8766)

⚠️ **Внимание:** E2E окружение требует 10-15 минут для полной инициализации

### Нагрузочное тестирование
```bash
make up-test-load
```
Запускает упрощенное окружение для нагрузочных тестов.

## 🧪 Запуск тестов

### Unit и Integration тесты
```bash
# С Docker окружением
make test-unit-docker
make test-integration-docker
make test-with-docker  # Все вместе

# Быстро без Docker (только unit)
make quick-test
```

### E2E тесты
```bash
make test-e2e-docker  # Полный цикл с окружением
```

### Нагрузочные тесты
```bash
make test-load-docker
```

## 📊 Профили Docker Compose

### Разработка (docker-compose.dev.yml)
- **Без профиля**: app, postgres, redis, qdrant
- **--profile admin**: + adminer, redis-commander
- **--profile llm**: + ollama
- **--profile frontend**: + frontend dev server
- **--profile monitoring**: + grafana, prometheus

### Тестирование (docker-compose.tests.yml)
- **Без профиля**: test-postgres, test-redis, test-qdrant, test-app
- **--profile e2e**: + jira, confluence, gitlab, elasticsearch, clickhouse, ydb
- **--profile tools**: + test-data-loader
- **--profile mocks**: + mock-services

## 📦 Управление данными

### Загрузка тестовых данных
```bash
# Базовые данные для тестов
make load-test-data-basic

# Данные для E2E тестов (включая внешние системы)
make load-test-data-e2e

# Очистка тестовых данных
make clean-test-data
```

## 🔧 Управление окружениями

### Статус и логи
```bash
# Статус
make status-dev
make status-test
make status-all

# Логи
make logs-dev
make logs-test
```

### Остановка
```bash
# Конкретное окружение
make down-dev
make down-test
make down-test-e2e

# Все окружения
make down-all
```

### Перезапуск
```bash
make dev-reset    # down-dev + up-dev
make test-reset   # down-test + up-test
```

## 🔨 Сборка образов

```bash
# Сборка конкретных образов
make build-dev
make build-test

# Сборка всех образов
make build-all
```

## 🌐 Порты и сервисы

### Разработка
| Сервис | Порт | Описание |
|--------|------|----------|
| App | 8000 | Основное приложение |
| PostgreSQL | 5432 | База данных |
| Redis | 6379 | Кэш |
| Qdrant | 6333 | Vector DB |
| Adminer | 8080 | Управление БД |
| Redis UI | 8081 | Управление Redis |
| Ollama | 11434 | LLM сервер |
| Grafana | 3001 | Мониторинг |
| Prometheus | 9090 | Метрики |

### Тестирование
| Сервис | Порт | Описание |
|--------|------|----------|
| Test App | 8001 | Тестовое приложение |
| Test PostgreSQL | 5433 | Тестовая БД |
| Test Redis | 6380 | Тестовый Redis |
| Test Qdrant | 6335 | Тестовый Qdrant |
| Jira | 8082 | Atlassian Jira |
| Confluence | 8083 | Atlassian Confluence |
| GitLab | 8084 | GitLab CE |
| Elasticsearch | 9201 | Поиск |
| ClickHouse | 8125 | Аналитическая БД |
| YDB | 8766 | Yandex Database |

## 🚀 Быстрый старт

### Для разработчика
```bash
# 1. Поднять инфраструктуру
make up-dev

# 2. Запустить приложение локально
make dev
```

### Для тестирования
```bash
# Unit/Integration тесты
make test-with-docker

# E2E тесты (долго!)
make test-e2e-docker
```

### Для полной локальной системы
```bash
make up-dev-full
# Приложение доступно на http://localhost:8000
```

## 🔍 Отладка

### Проверка готовности сервисов
```bash
# Проверка health checks
docker compose -f deployment/docker/docker-compose.dev.yml ps

# Логи конкретного сервиса
docker compose -f deployment/docker/docker-compose.dev.yml logs postgres
```

### Подключение к контейнеру
```bash
# PostgreSQL
docker exec -it ai-assistant-postgres-dev psql -U ai_user -d ai_assistant

# Redis
docker exec -it ai-assistant-redis-dev redis-cli

# Приложение
docker exec -it ai-assistant-dev bash
```

## ⚠️ Важные замечания

1. **E2E окружение требует 4-8GB RAM** для всех сервисов
2. **Первый запуск E2E может занять 15-20 минут** из-за загрузки образов и инициализации
3. **Порты должны быть свободны** - проверьте конфликты перед запуском
4. **Данные сохраняются в Docker volumes** - используйте `down -v` для полной очистки
5. **Тестовые и dev окружения изолированы** - могут работать параллельно

## 📚 Дополнительная документация

- [Архитектура](../architecture/ARCHITECTURE.md)
- [Руководство разработчика](DEVELOPER_GUIDE.md)
- [Тестирование](TESTING_REQUIREMENTS.md) 