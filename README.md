# �� AI Assistant MVP

> **Professional AI-powered RFC Generation & Semantic Search System**

Система для ускорения архитектурного дизайна с автогенерацией RFC документов по лучшим мировым практикам (Google, Uber, Stripe, AWS, Netflix, Facebook, Cloudflare).

---

## 🎯 Ключевые возможности

### 🚀 **AI-генерация RFC документов**
- **Интерактивные вопросы** - AI задает smart questions для полного понимания
- **Мировые стандарты** - шаблоны на базе лучших практик tech giants  
- **Три типа задач**: новый функционал, изменение существующего, анализ текущего

### 🔍 **Семантический поиск** 
- **Корпоративные данные** - интеграция с Confluence, Jira, GitLab
- **Векторный поиск** - релевантные результаты с scoring
- **Multi-source** - единый поиск по всем источникам

### 📖 **AI-генерация документации по коду**
- **Анализ кода** - поддержка 13+ языков программирования (Python, JS, TypeScript, Java, Go, Rust и др.)
- **Множественные типы** - README, API docs, Technical specs, User guides, Code comments
- **Умный анализ** - архитектурные паттерны, security issues, производительность
- **LLM интеграция** - профессиональный контент через AI

### 🧠 **Multi-LLM Architecture**
- **Smart Routing** - автоматический выбор оптимального провайдера
- **Ollama (Local)** - приватные модели (Mistral, Llama2, CodeLlama)
- **OpenAI** - GPT-4/3.5-turbo с cost tracking
- **Anthropic** - Claude 3 (Opus/Sonnet/Haiku)

### 👍 **Learning Pipeline**
- **Feedback Collection** - лайки/дизлайки как в ChatGPT
- **Auto-retraining** - модель улучшается на основе обратной связи
- **Quality Analytics** - метрики и insights для continuous improvement

---

## 📊 Текущий статус

### ✅ **Готово (Infrastructure Complete)**
- **FastAPI Application** с профессиональной архитектурой
- **Multi-LLM System** с 3 провайдерами и smart routing
- **PostgreSQL Schema** с 7 таблицами для enterprise use
- **Docker Compose** с health checks и persistent volumes
- **Comprehensive Testing** (47 тестов: 37 unit/integration + 10 smoke)
- **One-command deployment** (`make bootstrap`)

### 🚨 **Critical Gaps (Production Blockers)**
- **Security** - нет аутентификации, rate limiting, cost controls
- **Semantic Search** - Qdrant не интегрирован, нет embeddings
- **Data Sources** - GitLab/Confluence connectors отсутствуют

**📋 Детальный статус и планы:** [📚 DOCS_INDEX.md](./DOCS_INDEX.md)

---

## 🚀 Quick Start

### ⚡ Один command для всего:

```bash
# Полное развертывание системы
make bootstrap
```

**Что происходит:**
1. Создание `.env.local` из `.env.example`
2. Установка зависимостей (`pip3 install`)
3. Запуск Docker Compose инфраструктуры
4. Health checks всех сервисов
5. Запуск тестов (unit + integration + smoke)
6. Готовность к использованию

### 🛠️ Полезные команды:

```bash
make status        # 📊 Статус всех сервисов
make test          # 🧪 Все тесты
make smoke-test    # 💨 End-to-end тесты  
make run           # 🚀 Development server
make clean         # 🧹 Полная очистка
```

### 🌐 После запуска:

- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Qdrant Dashboard:** http://localhost:6333/dashboard

---

## 🐳 Docker Deployment

### ⚡ Одна команда для всего окружения:

```bash
./start-dev.sh
```

**Что включено:**
- **Frontend:** React + TypeScript (http://localhost:3000)
- **Backend:** FastAPI server (http://localhost:8000)
- **Database:** PostgreSQL (localhost:5432)
- **Vector DB:** Qdrant (http://localhost:6333)
- **LLM:** Ollama local models (http://localhost:11434)

### 🛠️ Manual Docker commands:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Full cleanup
docker-compose down -v --remove-orphans
```

### 📋 Services Overview:

| Service | Port | Description |
|---------|------|-------------|
| **frontend** | 3000 | React UI with Vite dev server |
| **app** | 8000 | FastAPI backend |
| **postgres** | 5432 | PostgreSQL database |
| **qdrant** | 6333 | Vector database |
| **ollama** | 11434 | Local LLM models |

**📖 Подробнее:** [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)

---

## 🏗️ Architecture

### 📁 **Project Structure**
```
ai_assistant/
├── app/                  # FastAPI application ✅
├── services/             # Business logic layer ✅  
├── llm/                  # Multi-LLM system ✅
├── models/               # Pydantic schemas ✅
├── tests/                # Comprehensive tests ✅
├── scripts/              # Database init ✅
├── security/             # Auth & validation (TODO)
├── vectorstore/          # Qdrant integration (TODO)
└── helm/                 # Kubernetes deployment (TODO)
```

### 🐳 **Infrastructure**
- **PostgreSQL** - метаданные и user sessions
- **Qdrant** - векторная БД для semantic search
- **Ollama** - локальные LLM модели (Mistral)
- **Redis** - кеширование и rate limiting (planned)

### 📊 **Database Schema**
7 таблиц для enterprise использования:
- `documents` - хранение документов
- `sessions` - RFC generation sessions  
- `feedback` - пользовательская обратная связь
- `llm_metrics` - метрики использования LLM
- `learning_data` - данные для переобучения
- `data_sources` - конфигурация источников
- `search_queries` - лог поисковых запросов

---

## 🤖 API Examples

### RFC Generation Workflow

```python
import httpx

# 1. Start generation
response = httpx.post("http://localhost:8000/api/v1/generate", json={
    "task_type": "new_feature",
    "initial_request": "Design notification system for mobile app",
    "context": "Push notifications for important events"
})

session_id = response.json()["session_id"]
questions = response.json()["questions"]

# 2. Answer AI questions  
httpx.post("http://localhost:8000/api/v1/generate/answer", json={
    "session_id": session_id,
    "answers": [
        {"question_id": questions[0]["id"], "answer": "Increase user engagement"}
    ]
})

# 3. Generate final RFC
rfc = httpx.post("http://localhost:8000/api/v1/generate/finalize", json={
    "session_id": session_id
}).json()["rfc"]
```

### Semantic Search

```python
# Search across all sources
results = httpx.post("http://localhost:8000/api/v1/search", json={
    "query": "microservices API gateway architecture",
    "limit": 10
}).json()["results"]

for result in results:
    print(f"{result['document']['title']} - Score: {result['score']}")
```

### Feedback Collection

```python
# Like/dislike feedback (ChatGPT style)
httpx.post("http://localhost:8000/api/v1/feedback", json={
    "target_id": rfc["id"],
    "context": "rfc_generation",
    "feedback_type": "like", 
    "rating": 5,
    "comment": "Excellent RFC! All details covered."
})
```

---

## 🧪 Testing & Quality

### 📊 **Test Coverage**
```bash
# Current test results:
✅ Unit + Integration: 25/25 passed
✅ Smoke Tests: 10/11 passed (1 skipped - Qdrant not started)
✅ Total: 35 tests covering all major functionality
```

### 🎯 **Quality Gates**
- **Test Coverage:** ≥80% for all modules
- **Performance:** <2s response time for API calls
- **Security:** All endpoints будут защищены (after security implementation)
- **Documentation:** README для каждого major feature

### 🏃‍♂️ **Running Tests**
```bash
make test                    # All tests
make smoke-test             # End-to-end tests
make test ARGS="-v"         # Verbose output
```

---

## 📚 Documentation & Plans

### 🎯 **For Quick Navigation**
- **[📚 DOCS_INDEX.md](./DOCS_INDEX.md)** - Навигация по всей документации
- **[🤖 AGENTS.md](./AGENTS.md)** - Главный файл с актуальными задачами

### 📋 **Detailed Plans** 
- **[🗺️ NEXT_STEPS_ROADMAP.md](./NEXT_STEPS_ROADMAP.md)** - Полная дорожная карта
- **[🔐 SECURITY_CHECKLIST.md](./SECURITY_CHECKLIST.md)** - Security requirements
- **[🚀 INFRASTRUCTURE_IMPROVEMENTS.md](./INFRASTRUCTURE_IMPROVEMENTS.md)** - Что уже сделано

### 🎯 **Next Priority Tasks**
1. **Security Implementation** (JWT, Rate Limiting, Cost Controls) - 3-5 дней
2. **Semantic Indexing** (Qdrant integration, Embeddings) - 5-7 дней  
3. **Data Sources** (GitLab/Confluence connectors) - 7-10 дней
4. **Production Deployment** (K8s, Monitoring) - 5-7 дней

---

## 🔧 Configuration

### ⚙️ **Environment Setup**
```bash
# Created automatically by `make bootstrap`
cp .env.example .env.local

# Key variables:
APP_ENV=development
POSTGRES_DB=ai_assistant
QDRANT_URL=http://localhost:6333
OLLAMA_URL=http://localhost:11434
MODEL_MODE=local
MODEL_NAME=mistral:instruct
```

### 🔐 **Security Note**
- `.env.local` in `.gitignore` - никогда не коммитится
- `.env.example` - template без secrets  
- All sensitive data через environment variables

---

## 🚀 Development

### 🛠️ **For Developers**
```bash
# Start development
make bootstrap              # Full setup
make run                   # Development server
make status                # Monitor services

# Testing
make test                  # All tests
make smoke-test           # E2E validation

# Cleanup
make clean                 # Full cleanup
```

### 🏗️ **Architecture Principles**
- **SOLID & Hexagonal Architecture**
- **Dependency Injection** (FastAPI Depends)
- **Service Layer Pattern** для бизнес-логики
- **Repository Pattern** для data access

### 📦 **Code Standards**
- **Python 3.11+** с type hints
- **PEP 8** compliance
- **80%+ test coverage** для новых модулей
- **Async/await** для all I/O operations

---

## 🎯 Next Steps

### 🔥 **Immediate Priority: Security Implementation**

**Why Critical:** Система полностью открыта - production blocker!

**Tasks:**
- JWT Authentication для всех API endpoints
- Rate Limiting (10 requests/minute per user)  
- Input Validation & SQL injection protection
- Cost Controls & User budgets для LLM calls

**ETA:** 3-5 дней

**📋 Full details:** [🔐 SECURITY_CHECKLIST.md](./SECURITY_CHECKLIST.md)

---

## 📞 Support & Contributing

### 🤝 **Contributing**
1. Fork the repository
2. Create feature branch (`git checkout -b feature/SecurityImplementation`)
3. Follow code standards (PEP 8, type hints, 80% test coverage)
4. Submit Pull Request

### 📋 **Issue Reporting**
- **Security issues:** Use private communication
- **Bugs & Features:** GitHub Issues
- **Questions:** Check documentation first

### 📖 **Getting Help**
1. **[📚 DOCS_INDEX.md](./DOCS_INDEX.md)** - Start here for navigation
2. **[🤖 AGENTS.md](./AGENTS.md)** - Current status & next tasks
3. API Documentation: http://localhost:8000/docs

---

## 🏆 Project Status

**🎯 Ready for Security Implementation!**

- ✅ **Infrastructure Complete** - 35 tests passing, one-command deployment
- 🚨 **Security Gap** - критический blocker для production
- 📋 **Clear Roadmap** - приоритизированные задачи на месяцы вперед
- 🛠️ **Developer Ready** - отличный DX с `make bootstrap`

**Next command:** Implement security according to [🤖 AGENTS.md](./AGENTS.md) Priority 1 task!

---

🚀 **AI Assistant MVP** - Professional RFC Generation with AI-powered Intelligence!
