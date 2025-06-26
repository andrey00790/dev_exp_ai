# 📚 AI Assistant MVP - Документация и планы

> **Навигационный индекс для всех документов проекта**

## 🎯 ГЛАВНЫЕ ДОКУМЕНТЫ

### 🤖 **[AGENTS.md](./AGENTS.md)** - ОСНОВНОЙ ФАЙЛ
**Назначение:** Актуальное руководство с текущим статусом и следующими задачами  
**Содержит:**
- ✅ Что готово (Infrastructure завершена)
- 🚨 Критические пробелы (Security, Semantic Search)
- 🎯 Приоритизированный бэклог задач
- 📋 Iteration Canvas для следующей задачи
- 🚀 Команды для разработки

**👉 Используй этот файл для выбора следующей задачи!**

---

## 📋 ПЛАНЫ И ROADMAPS

### 🗺️ **[NEXT_STEPS_ROADMAP.md](./NEXT_STEPS_ROADMAP.md)** - Детальная дорожная карта
**Содержит:**
- 🏗️ Infrastructure architecture (Docker, K8s, Database schema)
- 🧪 Testing & Validation system (10K+ search queries, 1K+ RFC tests)
- 📥 Dataset auto-loading system
- 🔍 Semantic search implementation details
- 📊 Production deployment strategy

### 🔐 **[SECURITY_CHECKLIST.md](./SECURITY_CHECKLIST.md)** - Критические требования безопасности
**Содержит:**
- ⚠️ Критические уязвимости (Authentication, Rate Limiting, Cost Controls)
- 🛡️ Рекомендуемые решения с кодом
- 📋 Implementation priority (3 недели)
- ✅ Security validation checklist
- 🎯 Compliance требования (GDPR, SOC 2)

### 🚀 **[INFRASTRUCTURE_IMPROVEMENTS.md](./INFRASTRUCTURE_IMPROVEMENTS.md)** - Отчет о выполненном
**Содержит:**
- ✅ Что сделано в итерации "infra_up"
- 📊 Результаты тестирования (47 тестов проходят)
- 🐳 Docker Compose improvements
- 🗄️ PostgreSQL schema design
- 💨 Smoke tests implementation

---

## 📊 СТАТУС И МЕТРИКИ

### ✅ **Готово (Infrastructure)**
- **FastAPI Application:** Профессиональная архитектура ✅
- **Multi-LLM System:** Ollama, OpenAI, Anthropic с smart routing ✅
- **Testing Pipeline:** 47 тестов (37 unit/integration + 10 smoke) ✅
- **Docker Compose:** Health checks, persistent volumes ✅
- **Developer Experience:** `make bootstrap` одной командой ✅

### 🚨 **Критические пробелы**
- **Security:** Нет аутентификации, rate limiting, cost controls ❌
- **Semantic Search:** Qdrant не интегрирован, нет embeddings ❌
- **Data Sources:** GitLab/Confluence connectors отсутствуют ❌

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

### 🔥 **PRIORITY 1: Security Implementation (3-5 дней)**
- JWT Authentication
- Rate Limiting (10 requests/minute)
- Input Validation & SQL injection protection
- Cost Controls & User budgets

### 🎯 **PRIORITY 2: Semantic Indexing (5-7 дней)**
- Qdrant vector database integration
- OpenAI embeddings pipeline
- Semantic search with relevance scoring

### 🎯 **PRIORITY 3: Data Sources (7-10 дней)**
- GitLab API integration
- Confluence connector
- Auto-sync scheduling

---

## 🛠️ КОМАНДЫ ДЛЯ РАЗРАБОТКИ

```bash
# Проверка статуса
make status

# Полное развертывание
make bootstrap

# Тестирование
make test && make smoke-test

# Development server
make run
```

---

## 🤖 ДЛЯ AI ASSISTANT

**Когда пользователь говорит "сделай следующую задачу":**

1. 📖 Открой **[AGENTS.md](./AGENTS.md)**
2. 🎯 Найди **СЛЕДУЮЩУЮ ЗАДАЧУ (PRIORITY 1)**
3. 📋 Используй **ITERATION CANVAS** как template
4. 🚀 Выполни задачу согласно критериям приёмки
5. ✅ Обнови статус в **AGENTS.md** после завершения

**Текущая следующая задача:** **Security Implementation** (JWT Auth + Rate Limiting + Cost Controls)

---

## 📁 СТРУКТУРА ФАЙЛОВ

```
├── AGENTS.md                    # 🤖 ГЛАВНЫЙ - актуальные задачи
├── NEXT_STEPS_ROADMAP.md       # 🗺️ Детальная дорожная карта  
├── SECURITY_CHECKLIST.md       # 🔐 Security requirements
├── INFRASTRUCTURE_IMPROVEMENTS.md # 🚀 Отчет о выполненном
├── DOCS_INDEX.md               # 📚 Этот файл - навигация
├── README.md                   # 📖 Основная документация
├── dataset_config.yml          # ⚙️ Конфигурация данных
└── app/                        # 💻 Код проекта
```

**🎯 Все готово для продуктивной работы! Следующая задача четко определена.** 