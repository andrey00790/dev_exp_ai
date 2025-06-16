# 📚 AI Assistant MVP - Руководство пользователя

**Версия:** 4.0  
**Дата:** 14.06.2025  
**Статус:** Production Ready (90% MVP)

## 🎯 Обзор системы

AI Assistant MVP - это комплексная платформа для автоматизации архитектурной работы с тремя ключевыми функциями:

1. **🔍 Семантический поиск** - поиск по корпоративным данным (Confluence, Jira, GitLab)
2. **📝 Генерация RFC** - создание архитектурных документов с помощью AI
3. **📖 Генерация документации** - автоматическое создание документации по коду

## 🚀 Быстрый старт

### 1. Запуск системы

```bash
# Полное развертывание одной командой
make bootstrap

# Или пошагово:
git clone <repository>
cd dev_exp_ai
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
docker-compose up -d
make run
```

### 2. Проверка готовности

```bash
# Проверка всех сервисов
make health-check

# Доступные URL:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - Qdrant: http://localhost:6333/dashboard
```

### 3. Первый запуск

1. Откройте браузер: http://localhost:8000/docs
2. Проверьте health endpoint: GET `/health`
3. Готово к использованию!

## 🔍 Функция 1: Семантический поиск

### Описание
Поиск релевантной информации по корпоративным источникам данных с использованием векторного поиска и AI.

### Возможности
- **Векторный поиск** - семантическое понимание запросов
- **Множественные источники** - Confluence, Jira, GitLab, пользовательские файлы
- **Фильтрация** - по источникам, датам, типам контента
- **Ранжирование** - релевантность с оценками

### Пошаговое использование

#### Шаг 1: Базовый поиск
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "микросервисы архитектура API gateway",
    "limit": 10
  }'
```

**Ответ:**
```json
{
  "results": [
    {
      "document": {
        "id": "doc_123",
        "title": "Архитектура микросервисов",
        "content": "API Gateway является центральным компонентом...",
        "source": "confluence",
        "url": "https://company.atlassian.net/wiki/spaces/ARCH/pages/123"
      },
      "score": 0.95,
      "highlights": ["API gateway", "микросервисы"]
    }
  ],
  "total": 25,
  "query_time_ms": 150
}
```

#### Шаг 2: Поиск с фильтрами
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "OAuth 2.0 implementation",
    "limit": 5,
    "filters": {
      "sources": ["confluence", "gitlab"],
      "date_from": "2024-01-01",
      "content_types": ["documentation", "code"]
    }
  }'
```

#### Шаг 3: Векторный поиск (продвинутый)
```bash
curl -X POST "http://localhost:8000/api/v1/vector-search/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "система уведомлений push notifications",
    "collection_name": "search_sources",
    "limit": 10,
    "score_threshold": 0.7
  }'
```

### Настройка источников данных

#### Confluence
```bash
curl -X POST "http://localhost:8000/api/v1/configurations/confluence" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://company.atlassian.net/wiki",
    "bearer_token": "your_bearer_token",
    "spaces": ["TECH", "ARCH", "DEV"]
  }'
```

#### GitLab
```bash
curl -X POST "http://localhost:8000/api/v1/configurations/gitlab" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://gitlab.company.com",
    "access_token": "your_access_token",
    "projects": ["group/project1", "group/project2"]
  }'
```

### Мониторинг качества поиска
```bash
# Оценка качества поиска
python evaluate_semantic_search.py --testset tests/semantic_search_eval.yml

# Целевые метрики:
# - Precision@3: ≥ 70%
# - MRR: ≥ 60%
# - Cosine Similarity: ≥ 0.75
```

## 📝 Функция 2: Генерация RFC

### Описание
Автоматическое создание архитектурных документов (RFC) с помощью AI на основе лучших практик индустрии.

### Возможности
- **Интерактивные вопросы** - AI задает умные вопросы для понимания контекста
- **Профессиональные шаблоны** - на основе стандартов GitHub, Stripe, ADR
- **Три типа задач**: новый функционал, изменение существующего, анализ текущего
- **Multi-LLM** - поддержка OpenAI, Anthropic, Ollama
- **Анализ качества** - автоматическая оценка сгенерированных RFC

### Пошаговое использование

#### Шаг 1: Начало генерации RFC
```bash
curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "new_feature",
    "initial_request": "Разработать систему уведомлений для мобильного приложения",
    "context": "Push уведомления для важных событий и обновлений"
  }'
```

**Ответ:**
```json
{
  "session_id": "session_abc123",
  "questions": [
    {
      "id": "q1",
      "question": "Какие типы уведомлений планируется поддерживать?",
      "type": "multiple_choice",
      "options": ["Push notifications", "In-app notifications", "Email", "SMS"]
    },
    {
      "id": "q2", 
      "question": "Какая ожидаемая нагрузка (уведомлений в день)?",
      "type": "text"
    }
  ],
  "status": "questions_pending"
}
```

#### Шаг 2: Ответы на вопросы AI
```bash
curl -X POST "http://localhost:8000/api/v1/generate/answer" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_abc123",
    "answers": [
      {
        "question_id": "q1",
        "answer": ["Push notifications", "In-app notifications"]
      },
      {
        "question_id": "q2",
        "answer": "100,000 уведомлений в день"
      }
    ]
  }'
```

#### Шаг 3: Генерация финального RFC
```bash
curl -X POST "http://localhost:8000/api/v1/generate/finalize" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_abc123",
    "template": "system_design",
    "llm_provider": "openai"
  }'
```

**Ответ:**
```json
{
  "rfc": {
    "id": "rfc_xyz789",
    "title": "RFC: Система уведомлений для мобильного приложения",
    "content": "# RFC: Система уведомлений\n\n## Обзор\n...",
    "template_used": "system_design",
    "generation_time_ms": 15000,
    "quality_score": 4.2
  },
  "status": "completed"
}
```

### Типы задач RFC

#### 1. Новый функционал (`new_feature`)
```json
{
  "task_type": "new_feature",
  "initial_request": "Создать API для управления пользователями",
  "context": "REST API с CRUD операциями"
}
```

#### 2. Изменение существующего (`modify_existing`)
```json
{
  "task_type": "modify_existing", 
  "initial_request": "Добавить кеширование в существующий API",
  "context": "Текущий API имеет проблемы с производительностью"
}
```

#### 3. Анализ текущего (`analyze_current`)
```json
{
  "task_type": "analyze_current",
  "initial_request": "Проанализировать архитектуру системы аутентификации",
  "context": "Нужно выявить узкие места и предложить улучшения"
}
```

### Анализ качества RFC
```bash
curl -X POST "http://localhost:8000/api/v1/ai-enhancement/rfc/analyze-quality" \
  -H "Content-Type: application/json" \
  -d '{
    "rfc_content": "# RFC: Система уведомлений...",
    "template_type": "system_design"
  }'
```

### Валидация RFC
```bash
# Автоматическая валидация
python validate_rfc.py --rfc path/to/rfc.md --template tests/rfc_generation_eval.yml

# Критерии качества:
# - YAML header: обязателен
# - Section coverage: ≥ 90%
# - Technical depth: ≥ 60%
# - Markdown syntax: валидный
```

## 📖 Функция 3: Генерация документации по коду

### Описание
Автоматическое создание профессиональной документации по коду с анализом архитектуры и выявлением проблем.

### Возможности
- **13+ языков программирования** - Python, JavaScript, TypeScript, Java, Go, Rust и др.
- **Множественные типы документации** - README, API docs, Technical specs, User guides
- **AST-анализ** - глубокий анализ структуры кода
- **Архитектурные паттерны** - автоматическое определение (FastAPI, Django, React, Spring Boot)
- **Security анализ** - выявление потенциальных уязвимостей
- **Performance анализ** - рекомендации по оптимизации

### Пошаговое использование

#### Шаг 1: Загрузка файла кода
```bash
curl -X POST "http://localhost:8000/api/v1/documentation/analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@app/main.py" \
  -F "language=python" \
  -F "doc_type=api_documentation"
```

#### Шаг 2: Анализ проекта
```bash
curl -X POST "http://localhost:8000/api/v1/documentation/analyze-project" \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "/path/to/project",
    "language": "python",
    "doc_types": ["readme", "api_documentation", "technical_specs"],
    "include_patterns": ["*.py", "*.md"],
    "exclude_patterns": ["__pycache__", "*.pyc"]
  }'
```

**Ответ:**
```json
{
  "analysis_id": "analysis_123",
  "project_info": {
    "name": "AI Assistant MVP",
    "language": "python",
    "framework": "fastapi",
    "architecture_pattern": "hexagonal",
    "files_analyzed": 45,
    "lines_of_code": 12500
  },
  "documentation": {
    "readme": "# AI Assistant MVP\n\n## Overview\n...",
    "api_documentation": "# API Documentation\n\n## Endpoints\n...",
    "technical_specs": "# Technical Specifications\n\n## Architecture\n..."
  },
  "analysis": {
    "security_issues": [
      {
        "severity": "medium",
        "description": "Hardcoded API key found",
        "file": "config.py",
        "line": 15
      }
    ],
    "performance_recommendations": [
      "Consider adding database connection pooling",
      "Implement caching for frequently accessed data"
    ],
    "code_quality_score": 8.5
  }
}
```

#### Шаг 3: Генерация конкретного типа документации
```bash
curl -X POST "http://localhost:8000/api/v1/documentation/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": "analysis_123",
    "doc_type": "user_guide",
    "format": "markdown",
    "include_examples": true,
    "include_diagrams": true
  }'
```

### Поддерживаемые языки программирования

| Язык | AST Анализ | Архитектурные паттерны | Security анализ |
|------|------------|------------------------|-----------------|
| Python | ✅ | FastAPI, Django, Flask | ✅ |
| JavaScript | ✅ | React, Vue, Express | ✅ |
| TypeScript | ✅ | Angular, React, Node.js | ✅ |
| Java | ✅ | Spring Boot, Spring MVC | ✅ |
| Go | ✅ | Gin, Echo, Fiber | ✅ |
| Rust | ✅ | Actix, Rocket, Warp | ✅ |
| C# | ✅ | ASP.NET Core, MVC | ✅ |
| PHP | ⚠️ | Laravel, Symfony | ⚠️ |
| Ruby | ⚠️ | Rails, Sinatra | ⚠️ |
| Kotlin | ⚠️ | Spring Boot, Ktor | ⚠️ |
| Swift | ⚠️ | SwiftUI, UIKit | ⚠️ |
| C++ | ⚠️ | - | ⚠️ |
| Scala | ⚠️ | Play, Akka | ⚠️ |

### Типы документации

#### 1. README документация
```json
{
  "doc_type": "readme",
  "include_sections": [
    "overview",
    "installation", 
    "usage",
    "api_reference",
    "contributing",
    "license"
  ]
}
```

#### 2. API документация
```json
{
  "doc_type": "api_documentation",
  "include_sections": [
    "endpoints",
    "request_response_examples",
    "authentication",
    "error_codes",
    "rate_limiting"
  ]
}
```

#### 3. Техническая спецификация
```json
{
  "doc_type": "technical_specs",
  "include_sections": [
    "architecture_overview",
    "database_schema", 
    "security_considerations",
    "performance_requirements",
    "deployment_guide"
  ]
}
```

#### 4. Руководство пользователя
```json
{
  "doc_type": "user_guide",
  "include_sections": [
    "getting_started",
    "step_by_step_tutorials",
    "troubleshooting",
    "faq",
    "best_practices"
  ]
}
```

## 🔧 Настройка и конфигурация

### Переменные окружения

```bash
# .env.local
APP_ENV=development
DEBUG=true

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_assistant
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=optional_api_key

# LLM Providers
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
OLLAMA_URL=http://localhost:11434

# Default LLM Settings
MODEL_MODE=hybrid  # local, cloud, hybrid
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4

# Security
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600  # seconds

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
```

### Конфигурация LLM провайдеров

#### OpenAI
```json
{
  "provider": "openai",
  "models": {
    "gpt-4": {
      "max_tokens": 4096,
      "temperature": 0.7,
      "cost_per_1k_tokens": 0.03
    },
    "gpt-3.5-turbo": {
      "max_tokens": 4096, 
      "temperature": 0.7,
      "cost_per_1k_tokens": 0.002
    }
  }
}
```

#### Anthropic Claude
```json
{
  "provider": "anthropic",
  "models": {
    "claude-3-opus": {
      "max_tokens": 4096,
      "temperature": 0.7,
      "cost_per_1k_tokens": 0.015
    },
    "claude-3-sonnet": {
      "max_tokens": 4096,
      "temperature": 0.7, 
      "cost_per_1k_tokens": 0.003
    }
  }
}
```

#### Ollama (локальные модели)
```json
{
  "provider": "ollama",
  "models": {
    "mistral:instruct": {
      "max_tokens": 4096,
      "temperature": 0.7,
      "cost_per_1k_tokens": 0.0
    },
    "llama2:13b": {
      "max_tokens": 4096,
      "temperature": 0.7,
      "cost_per_1k_tokens": 0.0
    }
  }
}
```

## 📊 Мониторинг и метрики

### Health Check
```bash
curl http://localhost:8000/health
```

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-14T10:30:00Z",
  "services": {
    "database": "healthy",
    "vector_db": "healthy", 
    "llm_providers": {
      "openai": "healthy",
      "anthropic": "healthy",
      "ollama": "healthy"
    }
  },
  "metrics": {
    "uptime_seconds": 3600,
    "total_requests": 1250,
    "avg_response_time_ms": 150
  }
}
```

### Prometheus метрики
```bash
# Доступны на http://localhost:9090/metrics

# Основные метрики:
ai_assistant_requests_total
ai_assistant_request_duration_seconds
ai_assistant_llm_requests_total
ai_assistant_llm_cost_usd_total
ai_assistant_search_precision_score
ai_assistant_rfc_quality_score
```

### Мониторинг качества

#### Семантический поиск
```bash
curl http://localhost:8000/api/v1/monitoring/search-quality
```

#### RFC генерация
```bash
curl http://localhost:8000/api/v1/monitoring/rfc-quality
```

#### Документация кода
```bash
curl http://localhost:8000/api/v1/monitoring/documentation-quality
```

## 🧪 Тестирование

### Запуск тестов
```bash
# Все тесты
make test-all

# По типам
make test-unit          # Unit тесты
make test-integration   # Integration тесты  
make test-e2e          # End-to-end тесты
make test-performance  # Performance тесты

# Качество AI функций
make quality-check     # Semantic search + RFC validation
```

### Тестирование API

#### Семантический поиск
```bash
python evaluate_semantic_search.py --testset tests/semantic_search_eval.yml
```

#### RFC генерация
```bash
python validate_rfc.py --test-mode
```

#### Документация кода
```bash
python test_code_documentation_languages.py
```

## 🔐 Безопасность

### Аутентификация
```bash
# Получение JWT токена
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@company.com",
    "password": "secure_password"
  }'
```

### Использование токена
```bash
curl -X GET "http://localhost:8000/api/v1/search" \
  -H "Authorization: Bearer your_jwt_token"
```

### Rate Limiting
- **100 запросов в час** на пользователя
- **10 LLM запросов в минуту** на пользователя
- **Автоматическая блокировка** при превышении лимитов

## 🚨 Устранение неполадок

### Частые проблемы

#### 1. Сервисы не запускаются
```bash
# Проверка Docker
docker-compose ps

# Перезапуск
docker-compose down && docker-compose up -d

# Логи
docker-compose logs -f
```

#### 2. Qdrant недоступен
```bash
# Проверка статуса
curl http://localhost:6333/dashboard

# Перезапуск Qdrant
docker-compose restart qdrant
```

#### 3. LLM провайдеры не работают
```bash
# Проверка ключей API
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Тест подключения
curl http://localhost:11434/api/tags  # Ollama
```

#### 4. Низкое качество поиска
```bash
# Переиндексация данных
curl -X POST "http://localhost:8000/api/v1/vector-search/reindex"

# Проверка метрик
python evaluate_semantic_search.py
```

### Логи и диагностика
```bash
# Логи приложения
tail -f logs/app.log

# Логи Docker
docker-compose logs -f app

# Системные метрики
curl http://localhost:8000/api/v1/monitoring/system
```

## 📞 Поддержка

### Документация
- **[ROADMAP.md](./ROADMAP.md)** - план развития
- **[README.md](./README.md)** - общий обзор
- **[API Docs](http://localhost:8000/docs)** - интерактивная документация

### Команды разработки
```bash
make help              # Все доступные команды
make bootstrap         # Полная настройка
make gui-dev          # Запуск GUI разработки
make health-check     # Проверка системы
```

### Контакты
- **Issues:** GitHub Issues
- **Documentation:** Этот файл
- **API Reference:** http://localhost:8000/docs

---

**🚀 AI Assistant MVP** - Ваш помощник в архитектурной работе! 