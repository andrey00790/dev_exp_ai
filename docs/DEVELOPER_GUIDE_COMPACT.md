# 👨‍💻 AI Assistant - Developer Guide

**Версия:** 2.0 | **Дата:** Январь 2025 | **Статус:** Актуальный

---

## 🏗️ Архитектурные принципы

### Основные паттерны
- **API-first** - OpenAPI спецификация как источник истины
- **Async/await** - асинхронная обработка на всех уровнях  
- **Dependency Injection** - через FastAPI и Pydantic
- **Event-driven** - WebSocket для real-time обновлений
- **Microservices-ready** - модульная архитектура

### Структура проекта
```
app/
├── api/v1/           # API endpoints
├── core/             # Базовые утилиты (async_utils, exceptions)
├── models/           # Pydantic модели
├── services/         # Бизнес-логика
├── security/         # Аутентификация, авторизация
└── main.py          # FastAPI app

frontend/
├── src/components/   # React компоненты
├── src/pages/        # Страницы приложения
├── src/services/     # API клиенты
└── src/stores/       # State management
```

---

## 🔧 Стандарты разработки

### Backend (Python/FastAPI)

**Стиль кода:**
```python
# Используйте type hints везде
async def search_documents(
    query: str,
    filters: SearchFilters,
    user: User = Depends(get_current_user)
) -> SearchResponse:
    """Search documents with semantic filtering."""
    pass

# Async/await для всех I/O операций
async def process_document(doc_id: str) -> ProcessingResult:
    async with aiohttp.ClientSession() as session:
        result = await session.get(f"/api/docs/{doc_id}")
        return await result.json()
```

**Обработка ошибок:**
```python
from app.core.exceptions import DocumentNotFoundError

@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    try:
        doc = await document_service.get_by_id(doc_id)
        return doc
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
```

### Frontend (React/TypeScript)

**Компоненты:**
```typescript
// Используйте TypeScript interfaces
interface SearchProps {
  query: string;
  onResults: (results: SearchResult[]) => void;
  loading?: boolean;
}

// Functional components с hooks
const SearchComponent: React.FC<SearchProps> = ({ query, onResults, loading = false }) => {
  const [results, setResults] = useState<SearchResult[]>([]);
  
  useEffect(() => {
    if (query) {
      searchAPI.search(query).then(setResults);
    }
  }, [query]);

  return <div>...</div>;
};
```

---

## 🔄 Development Workflow

### Git Flow
```bash
# Feature branches
git checkout -b feature/semantic-search-improvements
git commit -m "feat: improve search relevance algorithm"
git push origin feature/semantic-search-improvements

# Создание PR
gh pr create --title "Improve semantic search" --body "Description..."
```

### Pre-commit hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy
```

### Testing Strategy
```python
# Unit tests (pytest)
@pytest.mark.asyncio
async def test_semantic_search():
    result = await search_service.search("python best practices")
    assert len(result.documents) > 0
    assert result.documents[0].relevance_score > 0.8

# Integration tests
@pytest.mark.integration
async def test_search_api_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/search", json={"query": "test"})
        assert response.status_code == 200
```

---

## 📊 Performance Guidelines

### Database Optimization
```python
# Используйте connection pooling
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# Асинхронные запросы
async def get_documents(limit: int = 10):
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(Document).limit(limit)
        )
        return result.scalars().all()
```

### Caching Strategy
```python
# Redis для кэширования
from app.core.cache import cache

@cache.cached(timeout=300)  # 5 minutes
async def get_search_results(query: str) -> SearchResponse:
    return await search_service.search(query)

# Vector search caching
@cache.cached(timeout=3600, key_prefix="embeddings:")
async def get_document_embeddings(doc_id: str) -> List[float]:
    return await embedding_service.get_embeddings(doc_id)
```

---

## 🔐 Security Best Practices

### Authentication
```python
from app.security.auth import get_current_user

@router.post("/api/v1/documents")
async def create_document(
    document: DocumentCreate,
    current_user: User = Depends(get_current_user)
):
    # Проверка разрешений
    if not current_user.can_create_documents():
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return await document_service.create(document, user_id=current_user.id)
```

### Input Validation
```python
from pydantic import BaseModel, validator

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    min_score: float = 0.0
    
    @validator('query')
    def query_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()
    
    @validator('limit')
    def limit_must_be_reasonable(cls, v):
        if v > 100:
            raise ValueError('Limit cannot exceed 100')
        return v
```

---

## 🧪 Testing

### Test Structure
```
tests/
├── unit/             # Изолированные unit тесты
├── integration/      # API endpoint тесты
├── e2e/             # End-to-end тесты
└── conftest.py      # Pytest конфигурация
```

### Mocking External Services
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
async def mock_openai_service():
    with patch('app.services.openai_service.OpenAIService') as mock:
        mock.return_value.generate_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3]
        )
        yield mock

@pytest.mark.asyncio
async def test_document_processing(mock_openai_service):
    doc = await document_service.process_document("test content")
    assert doc.embedding is not None
```

---

## 📦 Deployment

### Docker Build
```dockerfile
# Multi-stage build для оптимизации
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
```bash
# Development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=...
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Slow API responses**
```bash
# Check metrics
curl http://localhost:8000/metrics | grep request_duration

# Database query analysis
EXPLAIN ANALYZE SELECT * FROM documents WHERE ...;

# Redis connection check
redis-cli ping
```

**2. Memory leaks**
```python
# Memory profiling
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Your code here
    pass

# Monitor memory usage
import psutil
print(f"Memory usage: {psutil.virtual_memory().percent}%")
```

**3. Vector search issues**
```bash
# Qdrant health check
curl http://localhost:6333/health

# Collection status
curl http://localhost:6333/collections/documents

# Reindex if needed
curl -X POST http://localhost:6333/collections/documents/points/reindex
```

---

## 📚 Key Libraries

### Backend
```python
# Core
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0

# Database
sqlalchemy[asyncio]>=2.0.0
alembic>=1.12.0
asyncpg>=0.28.0

# AI/ML
openai>=1.0.0
anthropic>=0.7.0
sentence-transformers>=2.2.0

# Caching & Queue
redis>=5.0.0
celery>=5.3.0

# Monitoring
prometheus-client>=0.17.0
structlog>=23.0.0
```

### Frontend
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "typescript": "^5.0.0",
    "@tanstack/react-query": "^4.0.0",
    "axios": "^1.0.0",
    "react-router-dom": "^6.0.0",
    "tailwindcss": "^3.0.0"
  }
}
```

---

## 🎯 Release Process

```bash
# 1. Version bump
bump2version minor  # or major/patch

# 2. Create release
git tag v2.1.0
git push origin v2.1.0

# 3. Build and push
docker build -t ai-assistant:v2.1.0 .
docker push registry.company.com/ai-assistant:v2.1.0

# 4. Deploy
helm upgrade ai-assistant ./helm/ --set image.tag=v2.1.0
```

---

**Быстрые ссылки:**
- 📖 [API Docs](http://localhost:8000/docs)
- 🔧 [Makefile commands](../Makefile)
- 🧪 [Testing Guide](../tests/README.md)
- 🚀 [Deployment Guide](./PRODUCTION_RUNBOOK.md) 