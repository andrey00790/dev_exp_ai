# 🛠️ AI Assistant MVP - Руководство разработчика

**Версия:** 8.0 Production Ready  
**Дата:** 22 декабря 2024  
**Статус:** ✅ **100% Production Ready**

---

## 🏗️ **АРХИТЕКТУРА СИСТЕМЫ**

### **Обзор компонентов**

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React 18 + TypeScript]
        PWA[Progressive Web App]
        Voice[Voice Input/Output]
        I18N[Internationalization]
    end
    
    subgraph "API Gateway"
        API[FastAPI Backend]
        Auth[JWT + SSO Authentication]
        HIPAA[HIPAA Compliance]
    end
    
    subgraph "Core Services"
        Search[Semantic Search Service]
        RFC[RFC Generation Service]  
        Docs[Documentation Service]
        Analytics[AI Analytics Service]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL)]
        Redis[(Redis Cache)]
        Qdrant[(Vector DB)]
        Files[(File Storage)]
    end
    
    subgraph "External Integrations"
        Confluence[Confluence API]
        GitLab[GitLab API]
        Jira[Jira API]
        OpenAI[OpenAI/Anthropic]
    end
    
    UI --> API
    API --> Search
    API --> RFC
    API --> Docs
    API --> Analytics
    Search --> Qdrant
    RFC --> PG
    Docs --> Files
    Analytics --> Redis
    API --> Confluence
    API --> GitLab
    API --> Jira
    RFC --> OpenAI
```

### **Ключевые компоненты**

#### **Frontend (React + TypeScript)**
```typescript
frontend/
├── src/
│   ├── components/          # React компоненты
│   │   ├── VoiceInput/     # 🎤 Голосовой ввод (NEW)
│   │   ├── Chat/           # 💬 Чат интерфейс
│   │   └── Analytics/      # 📊 Аналитика
│   ├── hooks/              # React хуки
│   │   └── useVoiceRecognition.ts  # 🎤 Voice API (NEW)
│   ├── i18n/               # 🌍 Интернационализация (NEW)
│   │   └── locales/        # EN/RU переводы
│   ├── pages/              # Страницы приложения
│   └── services/           # API клиенты
├── public/
│   ├── manifest.json       # 📱 PWA манифест (NEW)
│   └── icons/              # PWA иконки
└── serviceWorker.ts        # 🔄 Offline поддержка (NEW)
```

#### **Backend (FastAPI + Python)**
```python
app/
├── api/v1/                 # REST API endpoints
│   ├── auth.py            # 🔐 Аутентификация
│   ├── search_advanced.py # 🔍 Семантический поиск
│   ├── ai_advanced.py     # 🤖 AI генерация
│   ├── data_sources.py    # 📊 Управление источниками
│   └── ai_analytics.py    # 📈 AI аналитика
├── security/              # 🛡️ Безопасность
│   ├── auth.py           # JWT + RBAC
│   ├── hipaa_compliance.py # 🏥 HIPAA (NEW)
│   └── input_validation.py # ✅ Валидация
├── services/              # Бизнес логика
│   ├── vector_search_service.py
│   ├── ai_optimization_service.py
│   └── ai_analytics_service.py
└── models/                # ORM модели
    ├── user.py
    └── data_source.py
```

#### **Databases & Storage**
```yaml
# PostgreSQL - Основная БД
databases:
  primary:
    engine: PostgreSQL 15+
    schemas: [users, sessions, rfcs, analytics]
    features: [JSONB, full-text search, partitioning]
  
# Qdrant - Векторная БД
vector_db:
  engine: Qdrant 1.9.0+
  collections: [search_sources, embeddings]
  dimensions: 1536 (OpenAI ada-002)
  
# Redis - Кэш и сессии  
cache:
  engine: Redis 7+
  usage: [sessions, API cache, rate limiting]
```

### **Потоки данных**

#### **1. Поиск документов**
```python
# Поток: User Query → Vector Search → Results
def semantic_search_flow():
    user_query = "Docker deployment guide"
    
    # 1. Векторизация запроса
    query_vector = embed_query(user_query)
    
    # 2. Поиск в Qdrant
    results = qdrant_client.search(
        collection_name="search_sources",
        query_vector=query_vector,
        limit=10
    )
    
    # 3. Ранжирование и фильтрация
    filtered_results = apply_filters(results, user_filters)
    
    # 4. Возврат результатов
    return format_search_results(filtered_results)
```

#### **2. Генерация RFC**
```python
# Поток: User Input → AI Processing → Document Generation
async def rfc_generation_flow():
    # 1. Анализ запроса пользователя
    initial_request = "Create notification system"
    context = extract_context(initial_request)
    
    # 2. Генерация уточняющих вопросов
    questions = await generate_questions(context)
    
    # 3. Сбор ответов пользователя
    answers = await collect_user_answers(questions)
    
    # 4. Генерация финального RFC
    rfc_content = await generate_rfc_document(
        context=context,
        answers=answers,
        template="technical_rfc"
    )
    
    return rfc_content
```

---

## 🚀 **ЛОКАЛЬНАЯ РАЗРАБОТКА**

### **Быстрый старт**

#### **1. Клонирование и setup**
```bash
# Клонировать репозиторий
git clone https://github.com/company/ai-assistant-mvp.git
cd ai-assistant-mvp

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows

# Установить зависимости
pip install -r requirements.txt
```

#### **2. Настройка окружения**
```bash
# Скопировать шаблон переменных окружения
cp .env.template .env.local

# Отредактировать .env.local
nano .env.local
```

**Конфигурация .env.local:**
```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aiassistant_dev
REDIS_URL=redis://localhost:6379

# AI Providers  
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here

# Vector Database
QDRANT_URL=http://localhost:6333

# Security
JWT_SECRET_KEY=your-development-secret-key-change-in-production
ENCRYPTION_KEY=your-32-byte-encryption-key-here

# HIPAA (для тестирования)
HIPAA_COMPLIANCE_ENABLED=false

# Frontend Development
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

#### **3. Запуск инфраструктуры через Docker**
```bash
# Запустить только базы данных
docker-compose -f docker-compose.dev.yml up -d postgres redis qdrant

# Проверить статус
docker-compose -f docker-compose.dev.yml ps
```

#### **4. Инициализация БД**
```bash
# Запустить миграции
alembic upgrade head

# Создать тестового пользователя
python scripts/create_test_user.py
```

#### **5. Запуск Backend**
```bash
# Активировать venv
source venv/bin/activate

# Запустить в режиме разработки
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Проверить здоровье
curl http://localhost:8000/health
```

#### **6. Запуск Frontend (опционально)**
```bash
cd frontend

# Установить зависимости (первый раз)
npm install

# Запустить dev сервер
npm start

# Доступ: http://localhost:3000
```

### **Точки входа для дебага**

#### **Backend точки входа**
```python
# 1. app/main.py - Главная точка входа
def main():
    app = create_app()  # 🔍 Breakpoint здесь
    return app

# 2. app/api/v1/search_advanced.py - Семантический поиск
@router.post("/search")
async def semantic_search(request: SearchRequest):
    # 🔍 Breakpoint для отладки поиска
    results = await vector_search_service.search(
        query=request.query,
        filters=request.filters
    )
    return results

# 3. app/api/v1/ai_advanced.py - Генерация RFC  
@router.post("/generate")
async def generate_rfc(request: GenerateRequest):
    # 🔍 Breakpoint для отладки генерации
    session = await rfc_service.create_session(request)
    return session

# 4. app/services/vector_search_service.py - Векторный поиск
class VectorSearchService:
    async def search(self, query: str, filters: dict):
        # 🔍 Breakpoint для отладки Qdrant
        vector = await self.vectorize_query(query)
        results = await self.qdrant_search(vector)
        return results
```

#### **Frontend точки входа**
```typescript
// 1. src/main.tsx - React точка входа
const root = ReactDOM.createRoot(document.getElementById('root')!);
root.render(<App />); // 🔍 Breakpoint здесь

// 2. src/pages/AdvancedSearch.tsx - Поиск
const handleSearch = async (query: string) => {
  // 🔍 Breakpoint для отладки поиска
  const results = await searchApi.semanticSearch(query);
  setResults(results);
};

// 3. src/components/VoiceInput/VoiceInput.tsx - Голосовой ввод  
const startListening = () => {
  // 🔍 Breakpoint для отладки voice API
  if (recognitionRef.current) {
    recognitionRef.current.start();
  }
};

// 4. src/hooks/useVoiceRecognition.ts - Voice hook
export const useVoiceRecognition = (options = {}) => {
  // 🔍 Breakpoint для отладки speech recognition
  const [state, setState] = useState<VoiceRecognitionState>({
    isListening: false,
    transcript: ''
  });
};
```

### **Настройка отладки в IDE**

#### **VS Code Launch Configuration**
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/venv/bin/uvicorn",
      "args": [
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
      ],
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env.local"
    },
    {
      "name": "Debug Current Python File",
      "type": "python", 
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env.local"
    }
  ]
}
```

#### **PyCharm Configuration**
```bash
# Run Configuration для FastAPI
Script path: /path/to/venv/bin/uvicorn
Parameters: app.main:app --host 0.0.0.0 --port 8000 --reload
Environment variables: Из .env.local файла
Working directory: /path/to/ai-assistant-mvp
```

---

## 🔁 **CI/CD ПРОЦЕССЫ**

### **Структура тестов**

#### **Тесты локации**
```bash
tests/
├── unit/                    # Unit тесты
│   ├── test_auth.py        # Аутентификация
│   ├── test_search.py      # Поиск
│   ├── test_rfc_generation.py
│   └── test_hipaa_compliance.py  # 🏥 HIPAA (NEW)
├── integration/            # Интеграционные тесты  
│   ├── test_api_v1.py     # API endpoints
│   ├── test_data_sources_api.py  # Data sources
│   └── test_vector_search.py     # Qdrant интеграция
├── e2e/                   # End-to-end тесты
│   ├── test_user_flows.py # Пользовательские сценарии
│   └── test_voice_input.py # 🎤 Voice tests (NEW)
└── frontend/              # Frontend тесты
    ├── components/        # React component tests
    └── utils/            # Utility tests
```

#### **Запуск тестов локально**
```bash
# Unit тесты (быстрые)
pytest tests/unit/ -v

# Integration тесты  
pytest tests/integration/ -v

# E2E тесты (медленные)
pytest tests/e2e/ -v

# Тесты с покрытием
pytest --cov=app --cov-report=html tests/

# Фронтенд тесты
cd frontend && npm test

# Все тесты
make test-all
```

### **GitHub Actions Pipeline**

#### **.github/workflows/main.yml**
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      qdrant:
        image: qdrant/qdrant:v1.9.0
        
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
        
    - name: Run migrations
      run: alembic upgrade head
      
    - name: Run tests
      run: |
        pytest tests/unit/ --cov=app
        pytest tests/integration/
        
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  test-frontend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
        
    - name: Install dependencies
      run: cd frontend && npm ci
      
    - name: Run tests
      run: cd frontend && npm test -- --coverage --watchAll=false
      
    - name: Build frontend
      run: cd frontend && npm run build

  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Run HIPAA compliance check
      run: |
        python -m pytest tests/unit/test_hipaa_compliance.py
        
    - name: Security scan
      uses: pypa/gh-action-pip-audit@v1.0.8

  deploy-staging:
    needs: [test-backend, test-frontend, security-scan]
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    
    steps:
    - name: Deploy to staging
      run: echo "Deploy to staging environment"

  deploy-production:
    needs: [test-backend, test-frontend, security-scan]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    
    steps:
    - name: Deploy to production
      run: echo "Deploy to production environment"
```

### **Coverage отчеты**

#### **Где смотреть покрытие:**
```bash
# HTML отчет (локально)
pytest --cov=app --cov-report=html tests/
open htmlcov/index.html

# Терминальный отчет
pytest --cov=app --cov-report=term-missing tests/

# XML отчет (для CI)
pytest --cov=app --cov-report=xml tests/

# Coverage цель: 85%+ для production
```

#### **Allure отчеты (опционально)**
```bash
# Установка
pip install allure-pytest

# Запуск с Allure
pytest --alluredir=allure-results tests/

# Генерация отчета
allure serve allure-results
```

---

## 📝 **КОНФИГУРАЦИОННЫЕ ФАЙЛЫ**

### **Backend конфигурации**

#### **requirements.txt**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.13.1
psycopg2-binary==2.9.9
redis==5.0.1
qdrant-client==1.6.9
openai==1.3.7
anthropic==0.7.7
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
httpx==0.25.2
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
```

#### **alembic.ini**
```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://postgres:postgres@localhost/aiassistant

[loggers]
keys = root,sqlalchemy,alembic

[handlers] 
keys = console

[formatters]
keys = generic
```

#### **app/config.py**
```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost/aiassistant"
    redis_url: str = "redis://localhost:6379"
    qdrant_url: str = "http://localhost:6333"
    
    # AI Providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    # Security
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # HIPAA Compliance
    hipaa_compliance_enabled: bool = False
    hipaa_encryption_key: str = ""
    
    # Voice Features
    voice_input_enabled: bool = True
    speech_language: str = "en-US"
    
    class Config:
        env_file = ".env.local"

settings = Settings()
```

### **Frontend конфигурации**

#### **package.json**
```json
{
  "name": "ai-assistant-frontend",
  "version": "8.0.0",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^4.9.5",
    "@mui/material": "^5.14.20",
    "react-i18next": "^13.5.0",
    "i18next": "^23.7.6",
    "lucide-react": "^0.294.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": ["react-app", "react-app/jest"]
  }
}
```

#### **tsconfig.json**
```json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "es6"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"]
}
```

### **Docker конфигурации**

#### **docker-compose.dev.yml**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: ai-assistant-postgres-dev
    environment:
      POSTGRES_DB: aiassistant_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    container_name: ai-assistant-redis-dev
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  qdrant:
    image: qdrant/qdrant:v1.9.0
    container_name: ai-assistant-qdrant-dev
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
```

---

## 🔧 **ПОЛЕЗНЫЕ КОМАНДЫ**

### **Makefile команды**
```makefile
# Development
.PHONY: dev
dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

.PHONY: install
install:
	pip install -r requirements.txt
	cd frontend && npm install

.PHONY: test
test:
	pytest tests/ -v

.PHONY: test-cov
test-cov:
	pytest --cov=app --cov-report=html tests/

.PHONY: lint
lint:
	flake8 app/
	black --check app/
	cd frontend && npm run lint

.PHONY: format
format:
	black app/
	cd frontend && npm run format

# Database
.PHONY: migrate
migrate:
	alembic upgrade head

.PHONY: migration
migration:
	alembic revision --autogenerate -m "$(name)"

.PHONY: db-reset
db-reset:
	dropdb aiassistant_dev --if-exists
	createdb aiassistant_dev
	alembic upgrade head

# Infrastructure
.PHONY: infra-up
infra-up:
	docker-compose -f docker-compose.dev.yml up -d

.PHONY: infra-down
infra-down:
	docker-compose -f docker-compose.dev.yml down

.PHONY: logs
logs:
	docker-compose -f docker-compose.dev.yml logs -f
```

### **Debugging команды**
```bash
# Проверка здоровья системы
curl http://localhost:8000/health

# Проверка API документации
open http://localhost:8000/docs

# Проверка метрик
curl http://localhost:8000/metrics

# Проверка логов
tail -f logs/app.log

# Проверка БД соединения
psql postgresql://postgres:postgres@localhost/aiassistant_dev

# Проверка Redis
redis-cli ping

# Проверка Qdrant
curl http://localhost:6333/collections
```

---

## 📚 **Дополнительные ресурсы**

### **Документация**
- 📖 **API Docs**: http://localhost:8000/docs (автогенерируемая)
- 🏗️ **Architecture**: `docs/architecture/ARCHITECTURE.md`
- 🔐 **Security**: `docs/security/SECURITY_GUIDE.md`
- 🏥 **HIPAA**: `docs/compliance/HIPAA_COMPLIANCE_GUIDE.md`

### **Инструменты разработки**
- 🐛 **Отладка**: VS Code / PyCharm debugger
- 📊 **Профилирование**: `py-spy`, `memory_profiler`
- 🧪 **Тестирование**: pytest, Jest, Playwright
- 📈 **Мониторинг**: Grafana, Prometheus

### **Стандарты кода**
- 🐍 **Python**: PEP 8, Black formatter, Type hints
- 🌐 **TypeScript**: ESLint, Prettier, Strict mode
- 📝 **Docstrings**: Google Style для Python, JSDoc для TS
- 🔍 **Linting**: flake8, mypy, eslint

---

**📅 Версия руководства:** 8.0  
**🔄 Последнее обновление:** 22 декабря 2024  
**📬 Обратная связь:** dev@aiassistant.com

**🎯 Статус разработки: ✅ 100% Production Ready** 