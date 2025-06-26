# Руководство для разработчиков AI Assistant MVP

## 🚀 Начало работы

### Предварительные требования

- **Python 3.11+** - основной язык разработки
- **Docker Desktop 4.4+** - для оркестрации сервисов
- **Git** - контроль версий
- **IDE**: VS Code, PyCharm или аналогичный
- **RAM ≥24GB, Disk ≥30GB** - системные требования

### Первая установка

1. **Клонирование репозитория:**
```bash
git clone <repository-url>
cd ai_assistant
```

2. **Создание виртуального окружения:**
```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate    # Windows
```

3. **Установка зависимостей:**
```bash
pip install -r requirements.txt
```

4. **Настройка окружения:**
```bash
cp .env.example .env.local
# Отредактируйте .env.local под ваши нужды
```

5. **Первый запуск:**
```bash
make up
make healthcheck
```

---

## 🛠️ Инструменты разработки

### Makefile команды

```bash
# Разработка
make run              # Запуск в режиме разработки (hot-reload)
make up               # Запуск всех сервисов
make down             # Остановка сервисов
make healthcheck      # Проверка состояния

# Тестирование
make test             # Запуск всех тестов с покрытием
pytest tests/unit/    # Только unit тесты
pytest tests/integration/ # Только integration тесты

# Дополнительные команды
make lint             # Проверка стиля кода (планируется)
make format           # Форматирование кода (планируется)
```

### Python окружение

```bash
# Активация виртуального окружения
source .venv/bin/activate

# Установка дополнительных зависимостей для разработки
pip install black flake8 mypy pre-commit

# Настройка pre-commit hooks
pre-commit install
```

---

## 📁 Структура разработки

### Принципы организации кода

1. **Разделение по слоям**: API → Services → Models
2. **Dependency Injection**: через FastAPI Depends
3. **Interface Segregation**: абстракции для всех внешних зависимостей
4. **Single Responsibility**: каждый модуль имеет одну ответственность

### Добавление нового функционала

#### 1. Создание новой модели

```python
# models/new_feature.py
from pydantic import BaseModel
from typing import Optional

class NewFeature(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    # Всегда используйте type hints
```

#### 2. Создание сервиса

```python
# services/new_feature_service.py
from abc import ABC, abstractmethod
from models.new_feature import NewFeature

class NewFeatureServiceInterface(ABC):
    @abstractmethod
    async def create_feature(self, feature: NewFeature) -> NewFeature:
        pass

class NewFeatureService(NewFeatureServiceInterface):
    async def create_feature(self, feature: NewFeature) -> NewFeature:
        # Реализация бизнес логики
        pass
```

#### 3. Создание API endpoint

```python
# app/api/v1/new_feature.py
from fastapi import APIRouter, Depends
from services.new_feature_service import NewFeatureServiceInterface

router = APIRouter()

@router.post("/features")
async def create_feature(
    feature: NewFeature,
    service: NewFeatureServiceInterface = Depends(get_feature_service)
) -> NewFeature:
    return await service.create_feature(feature)
```

#### 4. Регистрация в main.py

```python
# app/main.py
from app.api.v1 import new_feature

def create_app() -> FastAPI:
    # ...
    application.include_router(
        new_feature.router,
        prefix="/api/v1",
        tags=["New Feature"]
    )
```

---

## 🧪 Практики тестирования

### Структура тестов

```
tests/
├── unit/                    # Тесты отдельных компонентов
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/             # Тесты API endpoints
│   ├── test_api_v1.py
│   └── test_health.py
└── e2e/                     # End-to-end тесты (планируется)
    └── test_workflows.py
```

### Написание unit тестов

```python
# tests/unit/test_new_feature_service.py
import pytest
from services.new_feature_service import NewFeatureService
from models.new_feature import NewFeature

@pytest.fixture
def feature_service():
    return NewFeatureService()

@pytest.fixture
def sample_feature():
    return NewFeature(name="Test Feature", description="Test description")

class TestNewFeatureService:
    @pytest.mark.asyncio
    async def test_create_feature(self, feature_service, sample_feature):
        result = await feature_service.create_feature(sample_feature)
        
        assert result.id is not None
        assert result.name == sample_feature.name
        assert result.description == sample_feature.description
```

### Интеграционные тесты

```python
# tests/integration/test_new_feature_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_create_feature_endpoint(client):
    feature_data = {
        "name": "Test Feature",
        "description": "Test description"
    }
    
    response = client.post("/api/v1/features", json=feature_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == feature_data["name"]
    assert "id" in data
```

### Покрытие тестами

```bash
# Запуск с отчетом покрытия
pytest --cov=app --cov=services --cov=models --cov-report=html

# Просмотр HTML отчета
open htmlcov/index.html
```

**Требования**:
- **Минимальное покрытие**: 80%
- **Unit тесты**: для всех сервисов и утилит
- **Integration тесты**: для всех API endpoints
- **Мокирование**: всех внешних зависимостей

---

## 🎨 Стандарты кодирования

### Python стиль

```python
# Хорошо ✅
class DocumentService:
    """Service for managing documents."""
    
    def __init__(self, repository: DocumentRepository) -> None:
        self._repository = repository
    
    async def create_document(self, document: Document) -> Document:
        """Create a new document."""
        if not document.title:
            raise ValueError("Document title is required")
        
        return await self._repository.save(document)

# Плохо ❌
class documentservice:
    def __init__(self, repo):
        self.repo = repo
    
    def create_doc(self, doc):
        return self.repo.save(doc)
```

### Правила именования

- **Файлы и функции**: `snake_case`
- **Классы**: `PascalCase`
- **Константы**: `UPPER_SNAKE_CASE`
- **Приватные методы**: `_leading_underscore`

### Type hints

```python
# Обязательно для всех функций
from typing import List, Optional, Dict, Any

async def search_documents(
    query: str,
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None
) -> List[Document]:
    """Search documents with optional filters."""
    pass
```

### Документация

```python
class DocumentService:
    """Service for managing documents.
    
    This service provides CRUD operations for documents
    and integrates with various storage backends.
    """
    
    async def create_document(self, document: Document) -> Document:
        """Create a new document.
        
        Args:
            document: Document to create
            
        Returns:
            Created document with generated ID and timestamps
            
        Raises:
            ValueError: If document data is invalid
            DocumentExistsError: If document already exists
        """
        pass
```

---

## 🔄 Git workflow

### Структура веток

```
main                 # Продакшн код
├── dev             # Разработка
├── feature/xyz     # Новые функции
├── bugfix/xyz      # Исправления ошибок
└── hotfix/xyz      # Критические исправления
```

### Процесс разработки

1. **Создание ветки:**
```bash
git checkout dev
git pull origin dev
git checkout -b feature/new-document-generation
```

2. **Разработка:**
```bash
# Делайте атомарные коммиты
git add .
git commit -m "feat: add document generation service"

# Следуйте conventional commits
git commit -m "fix: handle empty search queries"
git commit -m "docs: update API documentation"
git commit -m "test: add unit tests for document service"
```

3. **Pull Request:**
```bash
git push origin feature/new-document-generation
# Создайте PR в GitHub/GitLab
```

### Conventional Commits

```bash
feat:     # Новая функциональность
fix:      # Исправление ошибки
docs:     # Изменения в документации
test:     # Добавление или изменение тестов
refactor: # Рефакторинг без изменения функциональности
style:    # Изменения форматирования
ci:       # Изменения CI/CD
```

---

## 🐛 Отладка и логирование

### Настройка логирования

```python
# app/config.py
import logging

logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Использование в коде
logger.info("Document created successfully")
logger.warning("Search query returned no results")
logger.error("Failed to connect to database", exc_info=True)
```

### Отладка API

```bash
# Запуск с отладкой
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

# Использование curl для тестирования
curl -X POST "http://localhost:8000/api/v1/documents" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "content": "Test content", "doc_type": "srs"}'

# Проверка логов
tail -f logs/app.log
```

### Отладка в IDE

```python
# Добавьте точки останова в PyCharm/VS Code
import pdb; pdb.set_trace()  # Для отладки в консоли

# Или используйте встроенный отладчик IDE
```

---

## 🚀 Развертывание

### Локальная разработка

```bash
# Запуск только API
make run

# Запуск всей инфраструктуры
make up
```

### Docker разработка

```bash
# Сборка и запуск всех сервисов
docker-compose up --build

# Запуск только определенных сервисов
docker-compose up app postgres

# Просмотр логов
docker-compose logs -f app
```

### Переменные окружения

```bash
# .env.local для разработки
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Базы данных (используются Docker контейнеры)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

---

## 📊 Мониторинг и метрики

### Health Checks

```bash
# Базовая проверка
curl http://localhost:8000/health

# Расширенная проверка
curl http://localhost:8000/api/v1/health
```

### Логи приложения

```python
# Структурированное логирование
import json
import logging

logger = logging.getLogger(__name__)

def log_api_request(endpoint: str, method: str, status_code: int):
    logger.info(json.dumps({
        "event": "api_request",
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "timestamp": time.time()
    }))
```

---

## 🔧 Конфигурация IDE

### VS Code настройки

```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

### PyCharm настройки

1. **Project Interpreter**: выберите `.venv/bin/python`
2. **Code Style**: настройте PEP8
3. **Test Runner**: выберите pytest
4. **Version Control**: настройте Git integration

---

## 🤝 Code Review

### Чек-лист для PR

- [ ] **Тесты**: Покрытие ≥ 80%
- [ ] **Type hints**: Везде где необходимо
- [ ] **Документация**: Docstrings для публичных методов
- [ ] **Стиль**: Соответствие PEP8
- [ ] **Логирование**: Соответствующие log level'ы
- [ ] **Ошибки**: Proper exception handling
- [ ] **Безопасность**: Нет секретов в коде

### Процесс ревью

1. **Self-review**: проверьте свой код перед PR
2. **Automated checks**: убедитесь что CI проходит
3. **Peer review**: минимум 1 апрув от другого разработчика
4. **Documentation**: обновите документацию если необходимо

---

## 🔮 Следующие шаги

### Планируемые улучшения

1. **PostgreSQL интеграция**
   - SQLAlchemy модели
   - Alembic миграции
   - Connection pooling

2. **Qdrant векторный поиск**
   - Embeddings генерация
   - Semantic search
   - Similarity scoring

3. **LLM интеграция**
   - OpenAI API
   - Ollama поддержка
   - Document generation

4. **Web UI**
   - Chainlit интерфейс
   - Streamlit дашборд
   - Real-time updates

### Как внести вклад

1. Изучите `AGENTS.md` для понимания принципов
2. Выберите задачу из backlog
3. Создайте feature branch
4. Разработайте с тестами (≥80% покрытие)
5. Создайте PR с детальным описанием
6. Пройдите code review

**Важно**: Всегда следуйте принципам SOLID и hexagonal architecture! 