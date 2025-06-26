# 🛠️ AI Assistant MVP - Руководство разработчика

**Версия:** 4.0  
**Дата:** 14.06.2025  
**Статус:** Production Ready

## 🏗️ Архитектура системы

### Общая архитектура
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   External      │
│   React + TS    │◄──►│   FastAPI       │◄──►│   Services      │
│                 │    │                 │    │                 │
│ • Chat UI       │    │ • REST API      │    │ • OpenAI        │
│ • Search        │    │ • WebSocket     │    │ • Anthropic     │
│ • RFC Gen       │    │ • Auth          │    │ • Ollama        │
│ • Docs Gen      │    │ • Monitoring    │    │ • Confluence    │
│ • Settings      │    │                 │    │ • Jira          │
└─────────────────┘    └─────────────────┘    │ • GitLab        │
                                              └─────────────────┘
           │                       │
           ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Databases     │    │   Infrastructure│
│                 │    │                 │
│ • PostgreSQL    │    │ • Docker        │
│ • Qdrant        │    │ • Prometheus    │
│ • Redis (opt)   │    │ • Nginx         │
└─────────────────┘    └─────────────────┘
```

### Компонентная архитектура

#### Backend (FastAPI)
```
app/
├── main.py                 # Главное приложение
├── config.py              # Конфигурация
├── api/                   # API endpoints
│   ├── health.py          # Health checks
│   └── v1/                # API v1
│       ├── search.py      # Семантический поиск
│       ├── generate.py    # Генерация RFC
│       ├── documentation.py # Генерация документации
│       ├── auth.py        # Аутентификация
│       ├── users.py       # Управление пользователями
│       ├── feedback.py    # Обратная связь
│       └── ...
├── services/              # Бизнес-логика
├── models/               # Pydantic модели
├── security/             # Безопасность
└── monitoring/           # Мониторинг
```

#### Frontend (React + TypeScript)
```
frontend/src/
├── components/           # React компоненты
│   ├── chat/            # Chat интерфейс
│   ├── search/          # Поиск
│   ├── generate/        # Генерация RFC
│   ├── documentation/   # Генерация документации
│   └── settings/        # Настройки
├── pages/               # Страницы
├── hooks/               # Custom hooks
├── services/            # API клиенты
├── stores/              # State management
└── types/               # TypeScript типы
```

## 🔌 API Reference

### Базовый URL
```
http://localhost:8000/api/v1
```

### Аутентификация
```http
POST /auth/login
Content-Type: application/json

{
  "username": "user@company.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Семантический поиск

#### Базовый поиск
```http
POST /search
Authorization: Bearer {token}
Content-Type: application/json

{
  "query": "микросервисы архитектура",
  "limit": 10,
  "filters": {
    "sources": ["confluence", "gitlab"],
    "date_from": "2024-01-01"
  }
}
```

#### Векторный поиск
```http
POST /vector-search/search
Authorization: Bearer {token}
Content-Type: application/json

{
  "query": "OAuth 2.0 implementation",
  "collection_name": "search_sources",
  "limit": 5,
  "score_threshold": 0.7
}
```

### Генерация RFC

#### Начало генерации
```http
POST /generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "task_type": "new_feature",
  "initial_request": "Система уведомлений для мобильного приложения",
  "context": "Push уведомления для важных событий"
}
```

#### Ответы на вопросы
```http
POST /generate/answer
Authorization: Bearer {token}
Content-Type: application/json

{
  "session_id": "session_abc123",
  "answers": [
    {
      "question_id": "q1",
      "answer": ["Push notifications", "In-app notifications"]
    }
  ]
}
```

#### Финализация RFC
```http
POST /generate/finalize
Authorization: Bearer {token}
Content-Type: application/json

{
  "session_id": "session_abc123",
  "additional_requirements": "Поддержка iOS и Android"
}
```

### Генерация документации

#### Анализ кода
```http
POST /documentation/analyze
Authorization: Bearer {token}
Content-Type: application/json

{
  "code_input": {
    "filename": "main.py",
    "content": "from fastapi import FastAPI...",
    "language": "python"
  }
}
```

#### Генерация документации
```http
POST /documentation/generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "documentation_type": "api_docs",
  "code_input": "...",
  "target_audience": "developers",
  "detail_level": "detailed",
  "include_examples": true
}
```

## 🗄️ База данных

### PostgreSQL Schema

#### Основные таблицы
```sql
-- Пользователи
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Сессии генерации RFC
CREATE TABLE generation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    task_type VARCHAR(50) NOT NULL,
    initial_request TEXT NOT NULL,
    context TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Сгенерированные RFC
CREATE TABLE generated_rfcs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES generation_sessions(id),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    template_used VARCHAR(100),
    llm_provider VARCHAR(50),
    generation_time_ms INTEGER,
    quality_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Источники данных
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    source_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    config JSONB NOT NULL,
    is_enabled BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Документы для поиска
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES data_sources(id),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    url VARCHAR(1000),
    metadata JSONB,
    vector_id VARCHAR(255), -- Qdrant point ID
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Обратная связь
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    target_type VARCHAR(50) NOT NULL, -- 'rfc', 'search_result', 'documentation'
    target_id UUID NOT NULL,
    feedback_type VARCHAR(50) NOT NULL, -- 'like', 'dislike', 'rating'
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Метрики LLM
CREATE TABLE llm_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    request_type VARCHAR(50),
    response_time_ms INTEGER,
    tokens_input INTEGER,
    tokens_output INTEGER,
    cost_usd DECIMAL(10,6),
    success BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Qdrant Collections

#### search_sources
```python
{
    "vectors": {
        "size": 1536,  # OpenAI embeddings
        "distance": "Cosine"
    },
    "payload_schema": {
        "source_id": "keyword",
        "source_type": "keyword",
        "title": "text",
        "url": "keyword",
        "created_date": "datetime"
    }
}
```

#### learning_materials
```python
{
    "vectors": {
        "size": 1536,
        "distance": "Cosine"
    },
    "payload_schema": {
        "content_type": "keyword",
        "category": "keyword",
        "difficulty": "keyword",
        "language": "keyword"
    }
}
```

## 🔧 Сервисы

### SearchService
```python
class SearchServiceInterface:
    async def semantic_search(self, query: SemanticSearchQuery) -> List[SearchResult]:
        """Выполняет семантический поиск по документам"""
        
    async def upload_document(self, file: UploadFile, file_type: FileType, 
                            request: UploadFileRequest) -> UploadFileResponse:
        """Загружает и индексирует документ"""
        
    async def get_searched_sources(self, query: SemanticSearchQuery) -> List[str]:
        """Возвращает список источников, по которым производился поиск"""
```

### GenerationService
```python
class GenerationServiceInterface:
    async def start_generation_session(self, request: GenerateRequest) -> GenerationSession:
        """Начинает новую сессию генерации RFC"""
        
    async def generate_initial_questions(self, session: GenerationSession) -> List[AIQuestion]:
        """Генерирует начальные вопросы для сбора информации"""
        
    async def generate_rfc_document(self, session_id: str, 
                                  additional_requirements: str = None) -> GeneratedRFC:
        """Генерирует финальный RFC документ"""
```

### DocumentationService
```python
class DocumentationServiceInterface:
    async def analyze_code(self, request: CodeAnalysisRequest) -> CodeAnalysis:
        """Анализирует код и возвращает структурную информацию"""
        
    async def generate_documentation(self, request: DocumentationRequest) -> DocumentationResponse:
        """Генерирует документацию по коду"""
        
    async def get_supported_capabilities(self) -> Dict[str, Any]:
        """Возвращает поддерживаемые возможности"""
```

## 🤖 LLM Integration

### Multi-LLM Router
```python
class LLMRouter:
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(), 
            "ollama": OllamaProvider()
        }
        
    async def route_request(self, request: LLMRequest) -> LLMResponse:
        """Маршрутизирует запрос к оптимальному провайдеру"""
        
    async def get_best_provider(self, task_type: str, 
                              requirements: Dict[str, Any]) -> str:
        """Выбирает лучшего провайдера для задачи"""
```

### Провайдеры

#### OpenAI Provider
```python
class OpenAIProvider:
    async def generate_text(self, prompt: str, model: str = "gpt-4") -> str:
        """Генерирует текст через OpenAI API"""
        
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Получает векторные представления текстов"""
```

#### Anthropic Provider
```python
class AnthropicProvider:
    async def generate_text(self, prompt: str, model: str = "claude-3-sonnet") -> str:
        """Генерирует текст через Anthropic API"""
```

#### Ollama Provider
```python
class OllamaProvider:
    async def generate_text(self, prompt: str, model: str = "mistral:instruct") -> str:
        """Генерирует текст через локальный Ollama"""
        
    async def list_models(self) -> List[str]:
        """Возвращает список доступных локальных моделей"""
```

## 🔐 Безопасность

### JWT Authentication
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Извлекает текущего пользователя из JWT токена"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return await get_user_by_id(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/search")
@limiter.limit("10/minute")
async def semantic_search(request: Request, query: SemanticSearchQuery):
    """Поиск с ограничением 10 запросов в минуту"""
```

### Input Validation
```python
from pydantic import BaseModel, validator

class SearchQuery(BaseModel):
    query: str
    limit: int = 10
    
    @validator('query')
    def query_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v
        
    @validator('limit')
    def limit_must_be_reasonable(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Limit must be between 1 and 100')
        return v
```

## 📊 Мониторинг

### Prometheus Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

# Счетчики запросов
REQUEST_COUNT = Counter('ai_assistant_requests_total', 'Total requests', ['method', 'endpoint'])

# Время ответа
REQUEST_DURATION = Histogram('ai_assistant_request_duration_seconds', 'Request duration')

# LLM метрики
LLM_REQUESTS = Counter('ai_assistant_llm_requests_total', 'LLM requests', ['provider', 'model'])
LLM_COST = Counter('ai_assistant_llm_cost_usd_total', 'LLM cost in USD', ['provider'])

# Качество AI
SEARCH_PRECISION = Gauge('ai_assistant_search_precision_score', 'Search precision score')
RFC_QUALITY = Gauge('ai_assistant_rfc_quality_score', 'RFC quality score')
```

### Health Checks
```python
@router.get("/health")
async def health_check():
    """Проверка здоровья всех компонентов системы"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Проверка базы данных
    try:
        await database.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Проверка Qdrant
    try:
        await qdrant_client.get_collections()
        health_status["services"]["vector_db"] = "healthy"
    except Exception as e:
        health_status["services"]["vector_db"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return health_status
```

## 🧪 Тестирование

### Unit Tests
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_semantic_search():
    """Тест семантического поиска"""
    response = client.post("/api/v1/search", json={
        "query": "test query",
        "limit": 5
    })
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) <= 5

@pytest.mark.asyncio
async def test_rfc_generation():
    """Тест генерации RFC"""
    # Начинаем генерацию
    response = client.post("/api/v1/generate", json={
        "task_type": "new_feature",
        "initial_request": "Test feature",
        "context": "Test context"
    })
    assert response.status_code == 200
    session_id = response.json()["session_id"]
    
    # Финализируем
    response = client.post("/api/v1/generate/finalize", json={
        "session_id": session_id
    })
    assert response.status_code == 200
    assert "rfc" in response.json()
```

### Integration Tests
```python
@pytest.mark.integration
async def test_full_search_pipeline():
    """Тест полного пайплайна поиска"""
    # Загружаем документ
    with open("test_document.pdf", "rb") as f:
        response = client.post("/api/v1/search/upload", 
                             files={"file": f})
    assert response.status_code == 200
    
    # Ждем индексации
    await asyncio.sleep(2)
    
    # Ищем документ
    response = client.post("/api/v1/search", json={
        "query": "test content from document"
    })
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0
```

### E2E Tests
```python
@pytest.mark.e2e
async def test_complete_user_workflow():
    """Тест полного пользовательского сценария"""
    # 1. Аутентификация
    auth_response = client.post("/api/v1/auth/login", json={
        "username": "test@example.com",
        "password": "testpass"
    })
    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Настройка источника данных
    source_response = client.post("/api/v1/search/sources", 
                                json={"source_type": "confluence", "config": {...}},
                                headers=headers)
    assert source_response.status_code == 200
    
    # 3. Поиск
    search_response = client.post("/api/v1/search", 
                                json={"query": "test"}, 
                                headers=headers)
    assert search_response.status_code == 200
    
    # 4. Генерация RFC
    gen_response = client.post("/api/v1/generate", 
                             json={"task_type": "new_feature", "initial_request": "test"},
                             headers=headers)
    assert gen_response.status_code == 200
```

## 🚀 Развертывание

### Docker Compose
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/ai_assistant
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - postgres
      - qdrant
      
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ai_assistant
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
      
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

volumes:
  postgres_data:
  qdrant_data:
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-assistant
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-assistant
  template:
    metadata:
      labels:
        app: ai-assistant
    spec:
      containers:
      - name: ai-assistant
        image: ai-assistant:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ai-assistant-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

## 📚 Дополнительные ресурсы

### Документация
- **[USER_GUIDE.md](./USER_GUIDE.md)** - Руководство пользователя
- **[ROADMAP.md](./ROADMAP.md)** - План развития
- **[API Docs](http://localhost:8000/docs)** - Интерактивная документация

### Инструменты разработки
```bash
# Форматирование кода
black app/ tests/
isort app/ tests/

# Линтинг
flake8 app/ tests/
mypy app/

# Тестирование
pytest tests/ -v --cov=app

# Безопасность
bandit -r app/
safety check
```

### Полезные команды
```bash
# Разработка
make run              # Запуск dev сервера
make test             # Все тесты
make lint             # Проверка кода
make format           # Форматирование

# Docker
make docker-build     # Сборка образа
make docker-run       # Запуск в Docker
make docker-logs      # Логи контейнеров

# База данных
make db-migrate       # Миграции
make db-seed          # Тестовые данные
make db-reset         # Сброс БД
```

---

**🛠️ AI Assistant MVP Developer Guide** - Все что нужно для разработки! 