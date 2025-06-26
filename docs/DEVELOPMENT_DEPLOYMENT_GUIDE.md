# 🚀 AI Assistant - Руководство по разработке и деплою

## 📋 Содержание

1. [Локальная разработка](#-локальная-разработка)
2. [Локальная работа системы](#-локальная-работа-системы)
3. [Продакшн деплой через Helm](#-продакшн-деплой-через-helm)
4. [Архитектура и компоненты](#-архитектура-и-компоненты)
5. [Troubleshooting](#-troubleshooting)

---

## 🔧 Локальная разработка

### Быстрый старт для разработчика

```bash
# 1. Клонируем репозиторий
git clone <repository-url>
cd dev_exp_ai

# 2. Устанавливаем зависимости
make install

# 3. Запускаем инфраструктуру (БД, Redis, Qdrant)
make dev-infra-up

# 4. Запускаем приложение в режиме разработки
make dev
```

### Детальная настройка

#### 1. Системные требования

- **Python**: 3.11+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Make**: для команд автоматизации
- **Git**: для версионирования

#### 2. Установка зависимостей

```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt
```

#### 3. Переменные окружения

Создайте файл `.env` в корне проекта:

```bash
# Основные настройки
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-dev-secret-key

# База данных (для локальной разработки)
DATABASE_URL=postgresql://ai_user:ai_password_dev@localhost:5432/ai_assistant

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_URL=http://localhost:6333

# AI API ключи (опционально)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Логирование
LOG_LEVEL=DEBUG
LOG_FILE=logs/app.log
```

#### 4. Инфраструктура для разработки

```bash
# Базовая инфраструктура (PostgreSQL, Redis, Qdrant)
make dev-infra-up

# С админ панелями (добавляет Adminer, Redis UI)
make dev-infra-up-full

# С локальным LLM (добавляет Ollama)
make dev-infra-up-llm

# Проверка статуса
make dev-infra-status

# Просмотр логов
make dev-infra-logs
```

#### 5. Доступные сервисы в режиме разработки

| Сервис | URL | Логин/Пароль |
|--------|-----|--------------|
| PostgreSQL | localhost:5432 | ai_user / ai_password_dev |
| Redis | localhost:6379 | - |
| Qdrant | localhost:6333 | - |
| Adminer | http://localhost:8080 | - |
| Redis UI | http://localhost:8081 | admin / admin123 |
| Ollama | http://localhost:11434 | - |
| Mailhog | http://localhost:8025 | - |

#### 6. Запуск приложения

```bash
# Режим разработки с hot-reload
make dev

# Или обычный запуск
make start

# Проверка здоровья
make health
```

#### 7. Тестирование

```bash
# Все тесты
make test

# Unit тесты
make test-unit

# Integration тесты  
make test-integration

# Smoke тесты
make test-smoke
```

#### 8. Полезные команды разработки

```bash
# Остановить инфраструктуру
make dev-infra-down

# Очистить данные (ВНИМАНИЕ: удаляет все данные!)
make dev-infra-clean

# Проверка кода
make lint

# Очистка временных файлов
make clean

# Логи приложения
make logs
```

---

## 🚀 Локальная работа системы

### Запуск полной системы

Для запуска полной системы со всеми компонентами (включая frontend):

```bash
# Запуск полной системы
make system-up

# Проверка статуса
make system-status

# Просмотр логов
make system-logs

# Остановка
make system-down
```

### Доступные сервисы полной системы

| Сервис | URL | Описание |
|--------|-----|----------|
| Frontend | http://localhost:3000 | React веб-интерфейс |
| Backend API | http://localhost:8000 | FastAPI сервер |
| API Docs | http://localhost:8000/docs | Swagger документация |
| Health Check | http://localhost:8000/health | Проверка здоровья |

### Конфигурация полной системы

Полная система использует `deployment/docker/docker-compose.simple.yml` и включает:

- **Frontend**: React приложение
- **Backend**: FastAPI сервер
- **PostgreSQL**: База данных
- **Redis**: Кэш
- **Qdrant**: Векторная база данных
- **Ollama**: Локальный LLM (опционально)

### Переменные окружения для полной системы

```bash
# В deployment/docker/.env
POSTGRES_DB=ai_assistant
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
VITE_API_URL=http://localhost:8000
```

---

## ⎈ Продакшн деплой через Helm

### Предварительные требования

- **Kubernetes**: 1.24+
- **Helm**: 3.8+
- **kubectl**: настроенный для кластера
- **Ingress Controller**: nginx-ingress
- **Cert Manager**: для HTTPS сертификатов

### Быстрый деплой

```bash
# Установка через Helm
make helm-install

# Проверка статуса
make helm-status

# Просмотр логов
make helm-logs
```

### Детальная настройка Helm деплоя

#### 1. Подготовка кластера

```bash
# Создание namespace
kubectl create namespace ai-assistant

# Установка nginx-ingress (если не установлен)
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx

# Установка cert-manager (если не установлен)
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true
```

#### 2. Конфигурация values.yaml

Отредактируйте `deployment/helm/ai-assistant/values.yaml`:

```yaml
# Основные настройки
app:
  image:
    repository: your-registry/ai-assistant
    tag: "v1.0.0"
  
  env:
    ENVIRONMENT: production
    LOG_LEVEL: INFO

# Ingress настройки
ingress:
  enabled: true
  hosts:
    - host: ai-assistant.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
          service: frontend
        - path: /api
          pathType: Prefix
          service: app
  tls:
    - secretName: ai-assistant-tls
      hosts:
        - ai-assistant.yourdomain.com

# База данных
postgresql:
  auth:
    postgresPassword: "your-strong-password"
    username: "ai_user"
    password: "your-strong-password"
    database: "ai_assistant"
  primary:
    persistence:
      size: 100Gi

# Redis
redis:
  auth:
    password: "your-redis-password"
  master:
    persistence:
      size: 20Gi

# Qdrant
qdrant:
  persistence:
    size: 200Gi
  resources:
    limits:
      cpu: 4000m
      memory: 8Gi
    requests:
      cpu: 2000m
      memory: 4Gi
```

#### 3. Секреты

```bash
# Создание секретов для API ключей
kubectl create secret generic ai-secrets \
  --namespace ai-assistant \
  --from-literal=openai-api-key="your-openai-key" \
  --from-literal=anthropic-api-key="your-anthropic-key" \
  --from-literal=secret-key="your-app-secret-key"
```

#### 4. Установка

```bash
# Установка с кастомными значениями
helm install ai-assistant deployment/helm/ai-assistant/ \
  --namespace ai-assistant \
  --values deployment/helm/ai-assistant/values.yaml \
  --values your-custom-values.yaml

# Обновление
make helm-upgrade

# Удаление
make helm-uninstall
```

#### 5. Мониторинг продакшн деплоя

```bash
# Статус pods
kubectl get pods -n ai-assistant

# Логи приложения
kubectl logs -l app.kubernetes.io/name=ai-assistant -n ai-assistant -f

# Описание сервисов
kubectl describe svc -n ai-assistant

# Ingress информация
kubectl get ingress -n ai-assistant
```

#### 6. Масштабирование

```yaml
# В values.yaml
app:
  replicaCount: 5

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
```

---

## 🏗 Архитектура и компоненты

### Компоненты системы

```mermaid
graph TB
    subgraph "Frontend"
        UI[React App]
    end
    
    subgraph "Backend"
        API[FastAPI Server]
        WS[WebSocket Handler]
    end
    
    subgraph "Databases"
        PG[(PostgreSQL)]
        RD[(Redis)]
        QD[(Qdrant)]
    end
    
    subgraph "External"
        AI[AI APIs]
        CONF[Confluence]
        JIRA[Jira]
        GL[GitLab]
    end
    
    UI --> API
    UI --> WS
    API --> PG
    API --> RD
    API --> QD
    API --> AI
    API --> CONF
    API --> JIRA
    API --> GL
```

### Структура проекта

```
dev_exp_ai/
├── app/                    # Основное приложение
│   ├── api/               # API endpoints
│   ├── models/            # Модели данных
│   ├── services/          # Бизнес-логика
│   ├── security/          # Аутентификация
│   └── websocket.py       # WebSocket обработчик
├── frontend/              # React фронтенд
├── deployment/            # Конфигурации деплоя
│   ├── docker/           # Docker Compose файлы
│   └── helm/             # Helm чарты
├── scripts/               # Утилиты и скрипты
├── tests/                 # Тесты
├── docker-compose.dev.yaml # Инфраструктура для разработки
└── Makefile              # Команды автоматизации
```

### Порты и сервисы

| Компонент | Порт | Описание |
|-----------|------|----------|
| Frontend | 3000 | React приложение |
| Backend API | 8000 | FastAPI сервер |
| PostgreSQL | 5432 | Основная БД |
| Redis | 6379 | Кэш и сессии |
| Qdrant | 6333 | Векторная БД |
| Adminer | 8080 | Админка БД |
| Redis UI | 8081 | Админка Redis |
| Mailhog | 8025 | Email тестирование |
| Ollama | 11434 | Локальный LLM |

---

## 🔧 Troubleshooting

### Частые проблемы

#### 1. Проблемы с Docker

```bash
# Проверка Docker
docker --version
docker-compose --version

# Очистка Docker
docker system prune -f
docker volume prune -f

# Пересборка образов
docker-compose -f docker-compose.dev.yaml build --no-cache
```

#### 2. Проблемы с базой данных

```bash
# Проверка подключения к PostgreSQL
psql -h localhost -p 5432 -U ai_user -d ai_assistant

# Пересоздание БД
make dev-infra-down
make dev-infra-clean
make dev-infra-up
```

#### 3. Проблемы с зависимостями

```bash
# Переустановка зависимостей
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# Проверка конфликтов
pip check
```

#### 4. Проблемы с портами

```bash
# Проверка занятых портов
lsof -i :8000
lsof -i :5432
lsof -i :6379

# Остановка процессов
sudo kill -9 <PID>
```

#### 5. Проблемы с Helm

```bash
# Проверка Helm
helm version
kubectl cluster-info

# Отладка деплоя
helm install ai-assistant deployment/helm/ai-assistant/ --dry-run --debug

# Логи Kubernetes
kubectl describe pod <pod-name> -n ai-assistant
kubectl logs <pod-name> -n ai-assistant
```

### Логи и отладка

```bash
# Логи приложения
make logs

# Логи инфраструктуры
make dev-infra-logs

# Логи системы
make system-logs

# Логи Helm
make helm-logs

# Проверка здоровья
make health
curl http://localhost:8000/health
```

### Полезные команды

```bash
# Полная очистка и перезапуск
make dev-infra-down
make dev-infra-clean
make clean
make dev-infra-up
make dev

# Проверка всех сервисов
make dev-infra-status
make health

# Быстрая помощь
make help
```

---

## 📚 Дополнительные ресурсы

- **API Документация**: http://localhost:8000/docs
- **Архитектура**: [docs/architecture/](../architecture/)
- **Тестирование**: [COMPLIANCE_AND_TESTING_REPORT.md](../COMPLIANCE_AND_TESTING_REPORT.md)
- **Требования**: [docs/requirements/](../requirements/)

---

## 🤝 Поддержка

Если у вас возникли проблемы:

1. Проверьте [Troubleshooting](#-troubleshooting)
2. Посмотрите логи: `make logs`
3. Проверьте статус: `make dev-infra-status`
4. Создайте issue в репозитории

**Удачной разработки! 🚀** 