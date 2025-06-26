# 🚀 AI Assistant - Local Demo (Single-node) Guide

**Версия:** 2.0  
**Дата:** Январь 2025  
**Статус:** Актуальный  

---

## 🎯 Обзор

Данное руководство описывает запуск полной системы AI Assistant в single-node режиме для демонстраций, тестирования и локальной разработки. Все сервисы работают в Docker контейнерах на одной машине.

**Что включено:**
- ✅ FastAPI Backend (порт 8000)
- ✅ React Frontend (порт 3000)
- ✅ PostgreSQL Database (порт 5432)
- ✅ Redis Cache (порт 6379)
- ✅ Qdrant Vector DB (порт 6333)
- ✅ Nginx Proxy (порт 80/443)
- ✅ Prometheus Monitoring (порт 9090)  
- ✅ Grafana Dashboards (порт 3001)
- ✅ Demo Data & Users

---

## ⚡ Быстрый запуск (1 команда)

### Минимальная система:

```bash
# Запуск полной системы одной командой
make system-up

# Проверка статуса
make system-status

# Доступ к интерфейсу
open http://localhost:3000
```

**Время запуска:** 2-3 минуты  
**Готовность:** Когда все health checks зеленые

---

## 🛠️ Пошаговая установка

### 1. Предварительные требования

**Системные требования:**
- Docker Desktop 20.10+
- Docker Compose 2.0+
- 16GB RAM (рекомендуется)
- 20GB свободного места
- Порты 3000, 8000, 5432, 6379, 6333, 9090, 3001 свободны

**Проверка системы:**
```bash
# Проверка Docker
docker --version
docker-compose --version

# Проверка свободных портов
lsof -i :3000 -i :8000 -i :5432
```

### 2. Подготовка окружения

```bash
# Клонирование репозитория
git clone <repository-url>
cd dev_exp_ai

# Создание конфигурации demo
cp docker-compose.dev.yml docker-compose.demo.yml

# Создание .env файла для demo
cat > .env.demo << EOF
# Demo Configuration
ENVIRONMENT=demo
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://ai_user:ai_password_demo@postgres:5432/ai_assistant_demo

# Redis  
REDIS_URL=redis://redis:6379/0

# Qdrant
QDRANT_URL=http://qdrant:6333

# API Keys (demo keys)
OPENAI_API_KEY=${OPENAI_API_KEY:-demo-key}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-demo-key}

# Security
SECRET_KEY=demo-secret-key-change-in-production
JWT_SECRET_KEY=demo-jwt-secret-key

# Demo data
LOAD_DEMO_DATA=true
CREATE_DEMO_USERS=true
EOF
```

### 3. Запуск системы

```bash
# Сборка образов
docker-compose -f docker-compose.demo.yml build

# Запуск всех сервисов
docker-compose -f docker-compose.demo.yml up -d

# Ожидание готовности (может занять 2-3 минуты)
./scripts/wait-for-system.sh
```

### 4. Проверка запуска

```bash
# Проверка статуса контейнеров
docker-compose -f docker-compose.demo.yml ps

# Проверка health checks
curl http://localhost:8000/health
curl http://localhost:3000/health

# Проверка БД
docker exec -it ai-assistant-demo-postgres psql -U ai_user -d ai_assistant_demo -c "\dt"
```

---

## 🌐 Доступные сервисы

### Основные интерфейсы:

| Сервис | URL | Описание | Логин |
|--------|-----|----------|-------|
| **Frontend** | http://localhost:3000 | Основной интерфейс | demo@example.com / demo123 |
| **API Docs** | http://localhost:8000/docs | Swagger UI | - |
| **Health Check** | http://localhost:8000/health | Статус API | - |

### Административные интерфейсы:

| Сервис | URL | Описание | Логин |
|--------|-----|----------|-------|
| **Grafana** | http://localhost:3001 | Мониторинг | admin / admin |
| **Prometheus** | http://localhost:9090 | Метрики | - |
| **Adminer** | http://localhost:8080 | БД админка | ai_user / ai_password_demo |
| **Redis Commander** | http://localhost:8081 | Redis UI | - |
| **Qdrant UI** | http://localhost:6333/dashboard | Vector DB | - |

### Дополнительные сервисы:

| Сервис | URL | Описание |
|--------|-----|----------|
| **MailHog** | http://localhost:8025 | Email тестирование |
| **Jaeger** | http://localhost:16686 | Tracing (опционально) |
| **Ollama** | http://localhost:11434 | Локальные LLM |

---

## 👥 Demo пользователи

### Предустановленные аккаунты:

```bash
# Администратор
Email: admin@example.com
Password: admin123
Role: admin
Описание: Полный доступ ко всем функциям

# Demo пользователь  
Email: demo@example.com
Password: demo123
Role: user
Описание: Стандартный пользователь для демонстрации

# Viewer
Email: viewer@example.com  
Password: viewer123
Role: viewer
Описание: Только просмотр данных

# Developer
Email: dev@example.com
Password: dev123
Role: developer
Описание: Доступ к API и отладке
```

### API токены для тестирования:

```bash
# Получение токена через API
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "demo123"}'

# Использование токена
curl -H "Authorization: Bearer <TOKEN>" \
  http://localhost:8000/api/v1/search?query=test
```

---

## 📊 Demo данные

### Что загружается автоматически:

1. **Документы (100+ файлов):**
   - Техническая документация
   - API руководства
   - Примеры кода
   - RFC шаблоны

2. **Источники данных:**
   - Confluence spaces (demo)
   - Jira projects (demo)
   - GitLab repositories (demo)
   - Локальные файлы

3. **Векторные индексы:**
   - Семантические embedding'и
   - Поисковые коллекции
   - Метаданные документов

4. **Аналитические данные:**
   - История поисков
   - Метрики использования
   - Примеры отчетов

### Загрузка дополнительных данных:

```bash
# Загрузка расширенного dataset
docker exec -it ai-assistant-demo-backend \
  python scripts/load_extended_demo_data.py

# Загрузка тестовых метрик
docker exec -it ai-assistant-demo-backend \
  python scripts/generate_demo_metrics.py

# Создание demo RFC
docker exec -it ai-assistant-demo-backend \
  python scripts/create_demo_rfc.py
```

---

## 🧪 Демонстрационные сценарии

### Сценарий 1: Семантический поиск

```bash
# 1. Откройте http://localhost:3000
# 2. Войдите как demo@example.com / demo123
# 3. Перейдите в "Поиск"
# 4. Введите запрос: "authentication best practices"
# 5. Проверьте результаты с релевантностью
```

### Сценарий 2: Генерация RFC

```bash
# 1. Перейдите в "RFC Generator"
# 2. Выберите тип: "API Design"
# 3. Ответьте на вопросы системы
# 4. Получите сгенерированный RFC
# 5. Экспортируйте в Markdown/PDF
```

### Сценарий 3: AI Analytics

```bash
# 1. Перейдите в "Analytics"
# 2. Посмотрите дашборд использования
# 3. Проверьте метрики производительности
# 4. Изучите рекомендации по оптимизации
```

### Сценарий 4: Мониторинг

```bash
# 1. Откройте http://localhost:3001 (Grafana)
# 2. Войдите как admin / admin
# 3. Изучите AI Assistant Dashboard
# 4. Проверьте алерты и метрики
```

---

## 🔧 Кастомизация demo

### Настройка для конкретной демонстрации:

```bash
# Создание custom demo config
cat > docker-compose.custom-demo.yml << EOF
version: '3.8'
services:
  backend:
    environment:
      - DEMO_COMPANY_NAME=Your Company
      - DEMO_USE_CASE=technical_documentation
      - DEMO_LANGUAGE=en
  
  frontend:
    environment:
      - REACT_APP_DEMO_MODE=true
      - REACT_APP_COMPANY_NAME=Your Company
EOF

# Запуск с кастомизацией
docker-compose -f docker-compose.demo.yml -f docker-compose.custom-demo.yml up -d
```

### Добавление своих данных:

```bash
# Загрузка своих документов
mkdir -p demo-data/documents
cp your-documents/* demo-data/documents/

# Обновление demo data
docker exec -it ai-assistant-demo-backend \
  python scripts/index_custom_documents.py /app/demo-data/documents
```

### Настройка брендинга:

```bash
# Кастомный логотип
cp your-logo.png frontend/public/logo-custom.png

# Кастомные цвета
cat > frontend/src/theme/custom.css << EOF
:root {
  --primary-color: #your-color;
  --secondary-color: #your-secondary;
  --brand-font: 'Your Font', sans-serif;
}
EOF
```

---

## 📈 Мониторинг и метрики

### Ключевые метрики для демонстрации:

```bash
# API Response Times
curl http://localhost:9090/api/v1/query?query=api_request_duration_seconds

# Search Accuracy
curl http://localhost:9090/api/v1/query?query=search_relevance_score

# User Activity
curl http://localhost:9090/api/v1/query?query=active_users_total

# System Health
curl http://localhost:8000/health | jq .
```

### Grafana dashboards:

1. **AI Assistant Overview** - общие метрики
2. **Search Performance** - производительность поиска
3. **User Activity** - активность пользователей
4. **System Resources** - использование ресурсов
5. **API Metrics** - метрики API

---

## 🛠️ Управление системой

### Основные команды:

```bash
# Запуск системы
make demo-start

# Остановка системы
make demo-stop

# Перезапуск системы
make demo-restart

# Проверка статуса
make demo-status

# Просмотр логов
make demo-logs

# Полная очистка
make demo-clean
```

### Управление отдельными сервисами:

```bash
# Перезапуск только backend
docker-compose -f docker-compose.demo.yml restart backend

# Обновление только frontend
docker-compose -f docker-compose.demo.yml up -d --no-deps frontend

# Проверка логов конкретного сервиса
docker-compose -f docker-compose.demo.yml logs -f backend
```

---

## 🚨 Troubleshooting

### Типичные проблемы:

#### 1. Медленный запуск системы

```bash
# Проверка ресурсов
docker stats

# Увеличение лимитов памяти
export DOCKER_MEMORY_LIMIT=8g
docker-compose -f docker-compose.demo.yml up -d
```

#### 2. Ошибки подключения к БД

```bash
# Проверка статуса PostgreSQL
docker-compose -f docker-compose.demo.yml logs postgres

# Пересоздание БД
docker-compose -f docker-compose.demo.yml down postgres
docker volume rm dev_exp_ai_postgres_data
docker-compose -f docker-compose.demo.yml up -d postgres
```

#### 3. Не работает поиск

```bash
# Проверка Qdrant
curl http://localhost:6333/collections

# Переиндексация данных
docker exec -it ai-assistant-demo-backend \
  python scripts/reindex_demo_data.py
```

#### 4. Не загружаются метрики

```bash
# Проверка Prometheus
curl http://localhost:9090/api/v1/targets

# Перезапуск мониторинга
docker-compose -f docker-compose.demo.yml restart prometheus grafana
```

---

## 📋 Checklist для демонстрации

### Перед демонстрацией:
- [ ] Система запущена и все сервисы healthy
- [ ] Demo пользователи созданы
- [ ] Demo данные загружены
- [ ] Все URL доступны
- [ ] Grafana дашборды работают
- [ ] Поиск возвращает результаты

### Во время демонстрации:
- [ ] Показать основные функции (поиск, RFC, аналитику)
- [ ] Продемонстрировать производительность
- [ ] Показать мониторинг в реальном времени
- [ ] Объяснить архитектуру

### После демонстрации:
- [ ] Сохранить логи при необходимости
- [ ] Остановить систему (`make demo-stop`)
- [ ] Очистить временные данные

---

## 🎯 Производительность

**Ожидаемые показатели для demo:**
- Время запуска: 2-3 минуты
- API response time: <200ms
- Поиск: <2 секунды
- Генерация RFC: <60 секунд
- Память: ~8GB всего
- CPU: ~2-4 cores под нагрузкой

**Оптимизация для слабых машин:**
```bash
# Урезанная версия для демо
export DEMO_PROFILE=minimal
make demo-start-minimal
```

---

## 📞 Поддержка

**Быстрая помощь:**
```bash
make demo-help          # Показать все demo команды
make demo-health        # Проверить health всех сервисов
make demo-urls          # Показать все доступные URL
make demo-users         # Показать demo пользователей
```

**Контакты:**
- 📧 Demo Support: demo-support@company.com
- 🐛 Issues: GitHub Issues
- 📖 Docs: `/docs` folder

---

**Время подготовки демо:** 10-15 минут  
**Время демонстрации:** 15-30 минут  
**Ресурсы:** 16GB RAM, 20GB disk, 4 CPU cores 