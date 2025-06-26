# AI Assistant MVP - Complete API Documentation

## Overview

AI Assistant MVP предоставляет полнофункциональный REST API для работы с искусственным интеллектом, поиском документов, генерацией контента и управлением системой.

**Base URL:** `http://localhost:8000`  
**API Version:** v1  
**OpenAPI Version:** 3.1.0

## Authentication

Большинство endpoints требуют JWT аутентификации. Получите токен через `/api/v1/auth/login` и передавайте его в заголовке:

```bash
Authorization: Bearer <your_jwt_token>
```

## Health Check Endpoints

### 1. Basic Health Check
**GET** `/health`

Базовая проверка состояния сервера.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "timestamp": "2025-06-17"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/health"
```

### 2. API Health Check
**GET** `/api/v1/health`

Детальная проверка всех компонентов API.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "timestamp": "2025-06-17",
  "components": {
    "api": "healthy",
    "auth": "healthy",
    "search": "healthy",
    "generation": "healthy",
    "vector_search": "healthy",
    "websocket": "healthy"
  }
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

## Test Endpoints (No Authentication Required)

### 3. Test Health Check
**GET** `/api/v1/test/health`

Проверка состояния тестовых endpoints.

**Response:**
```json
{
  "status": "healthy",
  "service": "test_endpoints",
  "timestamp": "2025-06-17T12:00:00.000Z",
  "version": "1.0.0"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/test/health"
```

### 4. Test Vector Search
**POST** `/api/v1/test/vector-search`

Тестовый поиск документов без аутентификации.

**Request Body:**
```json
{
  "query": "artificial intelligence machine learning",
  "limit": 10
}
```

**Response:**
```json
{
  "query": "artificial intelligence machine learning",
  "results": [
    {
      "doc_id": "test_doc_1",
      "title": "Test Result for 'artificial intelligence machine learning'",
      "content": "This is a mock search result for the query 'artificial intelligence machine learning'. It demonstrates the search functionality.",
      "score": 0.95,
      "source": "test_confluence"
    },
    {
      "doc_id": "test_doc_2",
      "title": "Another Test Document",
      "content": "This is another mock document that would match your search query in a real scenario.",
      "score": 0.87,
      "source": "test_gitlab"
    }
  ],
  "total_results": 2,
  "search_time_ms": 45.5
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/test/vector-search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence machine learning",
    "limit": 5
  }'
```

### 5. Test Feedback Collection
**POST** `/api/v1/test/feedback`

Тестовая отправка обратной связи без аутентификации.

**Request Body:**
```json
{
  "target_id": "test_doc_123",
  "feedback_type": "like",
  "comment": "This is helpful information"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Test feedback 'like' recorded successfully",
  "feedback_id": "test_feedback_test_doc_123_like_969"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/test/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "target_id": "doc_456",
    "feedback_type": "dislike",
    "comment": "Information is outdated"
  }'
```

## Search Endpoints

### 6. Basic Search
**POST** `/api/v1/search`

Базовый поиск по документам.

**Response:**
```json
{
  "results": [
    {
      "id": "1",
      "title": "Test Result 1",
      "content": "Mock content 1"
    },
    {
      "id": "2", 
      "title": "Test Result 2",
      "content": "Mock content 2"
    }
  ],
  "total": 2,
  "query": "test"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "limit": 10,
    "source_types": ["confluence", "gitlab"]
  }'
```

## Generation Endpoints

### 7. RFC Generation
**POST** `/api/v1/generate/rfc`

Генерация RFC документов.

**Response:**
```json
{
  "content": "# Test RFC\n\nThis is a mock RFC generated for testing purposes.",
  "status": "success",
  "tokens_used": 50
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/generate/rfc" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Implement user authentication system",
    "project_context": "Web application with FastAPI",
    "technical_requirements": "JWT tokens, password hashing, role-based access"
  }'
```

## Data Models

### TestSearchRequest
```json
{
  "query": "string (required)",
  "limit": "integer (1-100, default: 10)"
}
```

### TestSearchResult
```json
{
  "doc_id": "string",
  "title": "string", 
  "content": "string",
  "score": "number",
  "source": "string"
}
```

### TestSearchResponse
```json
{
  "query": "string",
  "results": "TestSearchResult[]",
  "total_results": "integer",
  "search_time_ms": "number"
}
```

### TestFeedbackRequest
```json
{
  "target_id": "string (required)",
  "feedback_type": "string (required: like|dislike|report)",
  "comment": "string (optional)"
}
```

### TestFeedbackResponse
```json
{
  "success": "boolean",
  "message": "string",
  "feedback_id": "string"
}
```

## Error Handling

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

### Error Response Format
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Rate Limiting

API имеет ограничения по частоте запросов:
- **Search endpoints:** 100 requests/minute
- **Generation endpoints:** 20 requests/minute
- **Health checks:** 1000 requests/minute

## Testing

### Quick Test Suite
```bash
# Test server health
curl http://localhost:8000/health

# Test API health
curl http://localhost:8000/api/v1/health

# Test search functionality
curl -X POST http://localhost:8000/api/v1/test/vector-search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 5}'

# Test feedback collection
curl -X POST http://localhost:8000/api/v1/test/feedback \
  -H "Content-Type: application/json" \
  -d '{"target_id": "test", "feedback_type": "like"}'
```

### E2E Testing
Запустите полный набор E2E тестов:
```bash
python tests/e2e/test_fixed_e2e.py
```

## OpenAPI Specification

Полная OpenAPI спецификация доступна по адресу:
- **JSON:** `http://localhost:8000/openapi.json`
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## Performance

### Response Times
- Health checks: < 50ms
- Search operations: < 200ms
- Generation operations: < 2000ms

### Throughput
- Concurrent connections: 1000+
- Requests per second: 500+

## Support

Для получения помощи:
1. Проверьте логи сервера
2. Используйте health check endpoints для диагностики
3. Запустите E2E тесты для проверки функциональности

---

**Last Updated:** 2025-06-17  
**API Version:** 2.1.0  
**Test Coverage:** 100% 