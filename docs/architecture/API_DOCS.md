# API Документация AI Assistant MVP

## 📋 Обзор API

AI Assistant MVP предоставляет RESTful API для управления документами и интеграции с AI сервисами.

### Базовый URL
- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

### Версионирование
- **API v1**: `/api/v1/`

### Интерактивная документация
- **Swagger UI**: `{base_url}/docs`
- **ReDoc**: `{base_url}/redoc`

## 🔍 Health Check Endpoints

### GET /health
Базовая проверка состояния сервиса.

**Response 200:**
```json
{
  "status": "healthy",
  "timestamp": 1708123456.789,
  "version": "1.0.0",
  "uptime": 3600.5,
  "environment": "development",
  "checks": {
    "api": "healthy",
    "memory": "healthy",
    "database": "not_configured"
  }
}
```

### GET /api/v1/health
Расширенная проверка состояния всех компонентов.

**Response 200:**
```json
{
  "status": "healthy",
  "timestamp": 1708123456.789,
  "version": "1.0.0",
  "uptime": 3600.5,
  "environment": "development",
  "checks": {
    "api": "healthy",
    "database": "not_configured",
    "vectorstore": "not_configured",
    "llm": "not_configured",
    "memory": "healthy"
  }
}
```

## 📄 Document Management API

### POST /api/v1/documents
Создание нового документа.

**Request Body:**
```json
{
  "title": "System Requirements Specification",
  "content": "Detailed requirements for the system...",
  "doc_type": "srs",
  "tags": ["requirements", "system"],
  "metadata": {
    "author": "architect",
    "version": "1.0",
    "priority": "high"
  }
}
```

**Response 201:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "System Requirements Specification",
  "content": "Detailed requirements for the system...",
  "doc_type": "srs",
  "tags": ["requirements", "system"],
  "metadata": {
    "author": "architect",
    "version": "1.0",
    "priority": "high"
  },
  "created_at": "2024-02-17T10:30:00Z",
  "updated_at": "2024-02-17T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Невалидные данные
- `500 Internal Server Error` - Ошибка сервера

### GET /api/v1/documents/{document_id}
Получение документа по ID.

**Path Parameters:**
- `document_id` (string, required) - Уникальный идентификатор документа

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "System Requirements Specification",
  "content": "Detailed requirements for the system...",
  "doc_type": "srs",
  "tags": ["requirements", "system"],
  "metadata": {
    "author": "architect",
    "version": "1.0"
  },
  "created_at": "2024-02-17T10:30:00Z",
  "updated_at": "2024-02-17T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Документ не найден

### PUT /api/v1/documents/{document_id}
Обновление документа.

**Path Parameters:**
- `document_id` (string, required) - Уникальный идентификатор документа

**Request Body:**
```json
{
  "title": "Updated System Requirements",
  "content": "Updated detailed requirements...",
  "doc_type": "srs",
  "tags": ["requirements", "system", "updated"],
  "metadata": {
    "author": "architect",
    "version": "1.1"
  }
}
```

**Response 200:** (аналогично GET)

**Error Responses:**
- `400 Bad Request` - Невалидные данные
- `404 Not Found` - Документ не найден

### DELETE /api/v1/documents/{document_id}
Удаление документа.

**Path Parameters:**
- `document_id` (string, required) - Уникальный идентификатор документа

**Response 200:**
```json
{
  "success": true,
  "message": "Document 550e8400-e29b-41d4-a716-446655440000 deleted successfully",
  "timestamp": "2024-02-17T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Документ не найден

### GET /api/v1/documents
Получение списка всех документов (для разработки).

**Response 200:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "System Requirements Specification",
    "content": "Detailed requirements...",
    "doc_type": "srs",
    "tags": ["requirements"],
    "metadata": {},
    "created_at": "2024-02-17T10:30:00Z",
    "updated_at": "2024-02-17T10:30:00Z"
  }
]
```

### POST /api/v1/documents/search
Поиск документов по запросу.

**Request Body:**
```json
{
  "query": "system requirements",
  "limit": 10,
  "filters": {
    "doc_type": "srs"
  }
}
```

**Response 200:**
```json
{
  "success": true,
  "message": null,
  "timestamp": "2024-02-17T10:30:00Z",
  "results": [
    {
      "document": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "System Requirements Specification",
        "content": "Detailed requirements...",
        "doc_type": "srs",
        "tags": ["requirements"],
        "metadata": {},
        "created_at": "2024-02-17T10:30:00Z",
        "updated_at": "2024-02-17T10:30:00Z"
      },
      "score": 0.85,
      "highlights": [
        "Title: System Requirements Specification",
        "...system requirements and constraints..."
      ]
    }
  ],
  "total": 1,
  "query": "system requirements"
}
```

## 📊 Data Models

### Document Model
```typescript
interface Document {
  id?: string;                    // UUID, генерируется автоматически
  title: string;                  // Название документа (обязательно)
  content: string;                // Содержимое документа (обязательно)
  doc_type: DocumentType;         // Тип документа (обязательно)
  tags: string[];                 // Теги для категоризации
  metadata: Record<string, any>;  // Дополнительные метаданные
  created_at?: string;            // ISO 8601 timestamp
  updated_at?: string;            // ISO 8601 timestamp
}
```

### DocumentType Enum
```typescript
enum DocumentType {
  SRS = "srs",           // System Requirements Specification
  NFR = "nfr",           // Non-Functional Requirements
  USE_CASE = "use_case", // Use Case Document
  RFC = "rfc",           // Request for Comments
  ADR = "adr",           // Architecture Decision Record
  DIAGRAM = "diagram"    // Diagram Document
}
```

### SearchQuery Model
```typescript
interface SearchQuery {
  query: string;                  // Поисковый запрос (1-1000 символов)
  limit: number;                  // Лимит результатов (1-100, по умолчанию 10)
  filters: Record<string, any>;   // Фильтры поиска
}
```

### SearchResult Model
```typescript
interface SearchResult {
  document: Document;             // Найденный документ
  score: number;                  // Релевантность (0.0-1.0)
  highlights: string[];           // Подсвеченные фрагменты
}
```

### BaseResponse Model
```typescript
interface BaseResponse {
  success: boolean;               // Статус операции
  message?: string;               // Сообщение об ошибке или успехе
  timestamp: string;              // ISO 8601 timestamp
}
```

## 🔐 Аутентификация и авторизация

### Текущее состояние
В текущей версии MVP аутентификация не реализована. Все endpoints доступны без ограничений.

### Планируемая реализация
- **JWT токены** для аутентификации
- **RBAC** (Role-Based Access Control) для авторизации
- **API ключи** для внешних интеграций

## 🚨 Обработка ошибок

### Стандартные HTTP коды ошибок
- `400 Bad Request` - Невалидные входные данные
- `401 Unauthorized` - Не авторизован (планируется)
- `403 Forbidden` - Недостаточно прав (планируется)
- `404 Not Found` - Ресурс не найден
- `422 Unprocessable Entity` - Ошибка валидации Pydantic
- `500 Internal Server Error` - Внутренняя ошибка сервера

### Формат ошибки
```json
{
  "detail": "Document with ID nonexistent-id not found"
}
```

### Ошибки валидации (422)
```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## 📈 Rate Limiting

### Текущие ограничения
В текущей версии rate limiting не реализован.

### Планируемые ограничения
- **100 запросов/минуту** для обычных операций
- **10 запросов/минуту** для создания документов
- **50 запросов/минуту** для поиска

## 🔄 Pagination (планируется)

### Query Parameters
- `page` - Номер страницы (начиная с 1)
- `size` - Размер страницы (по умолчанию 20, максимум 100)

### Response Format
```json
{
  "items": [...],
  "total": 250,
  "page": 1,
  "size": 20,
  "pages": 13
}
```

## 🧪 Примеры использования

### Создание и поиск документа

```bash
# Создание документа
curl -X POST "http://localhost:8000/api/v1/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "API Documentation",
    "content": "This document describes the API endpoints...",
    "doc_type": "rfc",
    "tags": ["api", "documentation"]
  }'

# Поиск документов
curl -X POST "http://localhost:8000/api/v1/documents/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "API documentation",
    "limit": 5
  }'
```

### Обновление документа

```bash
# Получение ID из предыдущего ответа
DOC_ID="550e8400-e29b-41d4-a716-446655440000"

# Обновление документа
curl -X PUT "http://localhost:8000/api/v1/documents/${DOC_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated API Documentation",
    "content": "This updated document describes...",
    "doc_type": "rfc",
    "tags": ["api", "documentation", "updated"]
  }'
```

## 🔮 Планируемые API endpoints

### AI Generation
- `POST /api/v1/generate` - Генерация документов с помощью AI
- `POST /api/v1/improve` - Улучшение существующих документов

### Feedback
- `POST /api/v1/feedback` - Отправка обратной связи
- `GET /api/v1/feedback/stats` - Статистика обратной связи

### Templates
- `GET /api/v1/templates` - Получение шаблонов документов
- `POST /api/v1/templates` - Создание нового шаблона 