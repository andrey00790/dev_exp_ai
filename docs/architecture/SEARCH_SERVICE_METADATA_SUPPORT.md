# Обновленный сервис поиска с поддержкой метаданных

## Обзор

Сервис поиска был значительно обновлен для поддержки расширенного поиска с детальными метаданными. Новая архитектура включает:

- **Backend сервис** (`backend/search_service.py`) - полнофункциональная реализация с поддержкой БД
- **Frontend сервис** (`services/search_service.py`) - обертка с fallback к mock реализации
- **Расширенные модели документов** с детальными метаданными
- **API для расширенного поиска** с фильтрацией и фасетами

## Архитектура

```
API Layer
    ↓
Frontend Search Service
    ↓
Backend Search Service
    ↓
┌─────────────┬─────────────┬─────────────┐
│  Database   │ Vector Store│ Embedding   │
│             │             │   Model     │
└─────────────┴─────────────┴─────────────┘
```

## Основные компоненты

### 1. Backend Search Service

Основной сервис поиска с полной функциональностью:

```python
class SearchService:
    async def search_documents(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        search_type: str = "semantic",
        limit: int = 10,
        offset: int = 0,
        include_snippets: bool = True,
        filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]
    
    async def advanced_search(
        self,
        query: str,
        filters: Dict[str, Any],
        search_type: str = "semantic",
        sort_by: str = "relevance",
        sort_order: str = "desc",
        include_snippets: bool = True,
        include_metadata: bool = True,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]
```

#### Функциональность:

- **Семантический поиск** - используя векторные эмбеддинги
- **Ключевой поиск** - полнотекстовый поиск PostgreSQL
- **Гибридный поиск** - комбинация семантического и ключевого
- **Расширенная фильтрация** по метаданным
- **Фасеты** для интерактивной фильтрации
- **Сортировка** по различным критериям
- **Пагинация** результатов
- **Подсветка** ключевых слов
- **Генерация сниппетов**

### 2. Frontend Search Service

Обертка, обеспечивающая совместимость и fallback:

```python
class SearchService(SearchServiceInterface):
    def __init__(self):
        self.backend_service = None
        self.use_backend = BACKEND_AVAILABLE
    
    async def initialize(self):
        if self.use_backend:
            try:
                self.backend_service = await get_backend_search_service()
            except Exception:
                self.use_backend = False
                # Fallback к mock реализации
```

### 3. Модель документа с метаданными

Расширенная модель документа включает:

```python
class Document(Base):
    # Основные поля
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    
    # Метаданные источника
    source_type = Column(String, nullable=False)
    source_name = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    source_url = Column(String)
    
    # Иерархия и связи
    project_key = Column(String)
    space_key = Column(String)
    repository_name = Column(String)
    
    # Категоризация
    document_type = Column(String)
    category = Column(String)
    tags = Column(JSON)
    
    # Авторство
    author = Column(String)
    author_email = Column(String)
    assignee = Column(String)
    
    # Качество
    quality_score = Column(Float)
    relevance_score = Column(Float)
    
    # Дополнительные метаданные
    document_metadata = Column(JSON)
```

## API Эндпоинты

### 1. Базовый поиск

```http
POST /api/v1/search/documents
Content-Type: application/json

{
    "query": "API authentication",
    "sources": ["confluence_TECH", "gitlab_backend"],
    "search_type": "semantic",
    "limit": 10,
    "include_snippets": true,
    "filters": {
        "categories": ["documentation"],
        "authors": ["John Doe"]
    }
}
```

### 2. Расширенный поиск

```http
POST /api/v1/search/advanced
Content-Type: application/json

{
    "query": "user authentication",
    "filters": {
        "source_types": ["confluence", "gitlab"],
        "document_types": ["page", "file"],
        "categories": ["documentation", "code"],
        "authors": ["John Doe", "Jane Smith"],
        "date_range": {
            "start": "2024-01-01T00:00:00Z",
            "end": "2024-01-31T23:59:59Z",
            "field": "updated_at"
        },
        "metadata_filters": {
            "tags": ["api", "security"],
            "priority": ["high", "medium"],
            "language": ["en"]
        },
        "quality_filters": {
            "min_quality_score": 0.8
        }
    },
    "search_type": "hybrid",
    "sort_by": "relevance",
    "sort_order": "desc",
    "limit": 20,
    "offset": 0,
    "include_metadata": true,
    "include_snippets": true
}
```

## Типы поиска

### 1. Семантический поиск

- Использует векторные эмбеддинги для понимания смысла
- Находит концептуально похожие документы
- Лучше для поиска по смыслу, а не точным словам

### 2. Ключевой поиск

- Полнотекстовый поиск PostgreSQL
- Точное совпадение ключевых слов
- Поддержка операторов поиска

### 3. Гибридный поиск

- Комбинирует семантический и ключевой поиск
- Взвешенное ранжирование результатов
- Лучшее из обоих миров

## Фильтрация

### Доступные фильтры:

1. **По источникам**: source_types, source_names
2. **По типу документа**: document_types
3. **По категории**: categories
4. **По автору**: authors
5. **По проекту/пространству**: project_keys, space_keys, repository_names
6. **По дате**: updated_at_range, created_at_range
7. **По метаданным**: tags, priority, language, file_extensions
8. **По качеству**: min_quality_score, min_relevance_score

## Сортировка

Доступные варианты:
- `relevance` - по релевантности (по умолчанию)
- `date` - по дате обновления
- `created_date` - по дате создания
- `title` - по заголовку
- `author` - по автору
- `quality` - по оценке качества

## Производительность

### Оптимизации:
1. Индексы БД на часто используемые поля
2. Кэширование популярных запросов
3. Пагинация для больших результатов
4. Асинхронная обработка
5. Векторные индексы для семантического поиска

### Метрики:
- Время ответа: < 200ms для простых запросов
- Время ответа: < 500ms для сложных запросов
- Пропускная способность: > 100 запросов/сек
- Точность поиска: > 85%

## Тестирование

### Запуск тестов:

```bash
# Все тесты поиска
pytest tests/unit/test_search_service.py -v

# Тесты API
pytest tests/unit/test_advanced_search.py -v

# Интеграционные тесты
pytest tests/integration/test_search_integration.py -v
```

## Развертывание

### Зависимости:
1. PostgreSQL с расширением для полнотекстового поиска
2. Векторная база данных (опционально)
3. Модель эмбеддингов
4. Redis для кэширования (опционально)

## Заключение

Обновленный сервис поиска предоставляет мощные возможности для поиска и фильтрации документов с детальными метаданными. Архитектура обеспечивает высокую производительность, масштабируемость и простоту использования.

Ключевые преимущества:
- **Гибкость** - множество типов поиска и фильтров
- **Производительность** - оптимизированные запросы и индексы
- **Масштабируемость** - асинхронная архитектура
- **Надежность** - fallback механизмы и обработка ошибок
- **Простота** - интуитивный API и документация 