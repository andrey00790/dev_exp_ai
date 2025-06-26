# 📚 AI Assistant API Reference

**Версия:** 3.1.0  
**OpenAPI Spec:** `/openapi.yaml`  
**Базовый URL:** `http://localhost:8000`

## 🔐 Аутентификация

Все endpoints требуют JWT Bearer token, кроме отмеченных как публичные.

```bash
Authorization: Bearer <your-jwt-token>
```

## 📊 Quick Stats

- **90+ API endpoints** в 10 категориях
- **80+ схем данных** (request/response models)
- **89% semantic search accuracy**
- **<150ms average response time**
- **1000+ concurrent users supported**

---

## 🎯 **Основные API Categories**

### 🏥 Health & Status
```
GET  /health                    # Basic health check (public)
GET  /api/v1/health             # Detailed API health (public)
```

### 🔑 Authentication
```
POST /api/v1/auth/register      # Register user (public)
POST /api/v1/auth/login         # Login user (public)
GET  /api/v1/auth/me            # Get current user
GET  /api/v1/auth/verify        # Verify token
POST /api/v1/auth/refresh       # Refresh token
GET  /api/v1/auth/budget        # Get budget info
GET  /api/v1/auth/scopes        # Get user permissions
GET  /api/v1/auth/profile       # Get user profile
GET  /api/v1/auth/usage-stats   # Get usage statistics
POST /api/v1/auth/logout        # Logout user
GET  /api/v1/auth/demo-users    # Get demo users (public)
```

### 👥 User Management
```
POST /api/v1/users                      # Create user
GET  /api/v1/users/{user_id}            # Get user by ID
GET  /api/v1/users/current/settings     # Get user settings
PUT  /api/v1/users/current/settings     # Update user settings
```

### 📝 Document Generation
```
POST /api/v1/generate/rfc               # Generate RFC document
POST /api/v1/generate/architecture      # Generate architecture docs
POST /api/v1/generate/documentation     # Generate technical docs
GET  /api/v1/generate/status/{task_id}  # Get generation status
GET  /api/v1/generate/templates         # Get available templates
```

### 🔍 Vector Search (AI-Powered)
```
POST /api/v1/vector-search/search          # Semantic search (main)
POST /api/v1/vector-search/index           # Index document
DELETE /api/v1/vector-search/documents/{doc_id}  # Delete document
GET  /api/v1/vector-search/similar/{doc_id}      # Find similar docs
GET  /api/v1/vector-search/stats               # Get search stats
POST /api/v1/vector-search/collections/initialize  # Initialize collections
POST /api/v1/vector-search/upload-file         # Upload & index file
GET  /api/v1/vector-search/collections         # List collections
GET  /api/v1/vector-search/health              # Vector search health
```

### 🔎 Search (Legacy/Alternative)
```
POST /api/v1/search              # Document search
GET  /api/v1/search/history      # Get search history
POST /api/v1/search/suggestions  # Get search suggestions
GET  /api/v1/search/sources      # Get available sources
```

### 🔌 Data Sources Management
```
GET  /api/v1/data-sources                            # List data sources
POST /api/v1/data-sources                            # Create data source
PUT  /api/v1/data-sources/{type}/{name}              # Update data source
DELETE /api/v1/data-sources/{type}/{name}            # Delete data source
POST /api/v1/data-sources/{type}/{name}/sync         # Trigger sync
GET  /api/v1/data-sources/sync/status                # Get sync status
```

### 🤖 AI Enhancement
```
POST /api/v1/ai-enhancement/model/train              # Train AI model
GET  /api/v1/ai-enhancement/model/training/{id}/status  # Training status
POST /api/v1/ai-enhancement/rfc/analyze-quality      # Analyze RFC quality
POST /api/v1/ai-enhancement/search/optimize          # Optimize search
GET  /api/v1/ai-enhancement/status                   # AI status
```

### 💬 Feedback & Learning
```
POST /api/v1/feedback                    # Submit feedback
GET  /api/v1/feedback/stats/{target_id}  # Get feedback stats
GET  /api/v1/feedback/analytics          # Get feedback analytics
POST /api/v1/feedback/retrain            # Trigger retraining
GET  /api/v1/feedback/trends             # Get feedback trends
DELETE /api/v1/feedback/{feedback_id}    # Delete feedback
GET  /api/v1/feedback/export             # Export feedback data
```

---

## 🚀 **Самые важные endpoints для начала:**

### 1. **Semantic Search** (основная функция)
```bash
POST /api/v1/vector-search/search
```
```json
{
  "query": "Docker microservices deployment patterns",
  "collections": ["confluence", "gitlab"], 
  "limit": 10,
  "hybrid_search": true
}
```

### 2. **Generate RFC** (AI генерация)
```bash
POST /api/v1/generate/rfc
```
```json
{
  "task_description": "API authentication system design",
  "priority": "high",
  "use_all_sources": true
}
```

### 3. **Authentication** (получение токена)
```bash
POST /api/v1/auth/login
```
```json
{
  "user_id": "demo@company.com",
  "password": "demo_password"
}
```

---

## 📋 **Data Source Types**

Поддерживаемые источники данных:
- **Confluence** - корпоративные wiki и документация
- **GitLab** - репозитории кода, issues, wiki
- **Jira** - задачи, требования, tickets
- **Local Files** - загруженные документы

---

## 🎯 **Response Examples**

### Search Response
```json
{
  "query": "Docker deployment",
  "results": [
    {
      "doc_id": "confluence_123",
      "title": "Docker Deployment Guide", 
      "content": "Complete Docker deployment guide...",
      "score": 0.94,
      "source": "Confluence",
      "highlights": ["Docker", "deployment", "guide"]
    }
  ],
  "total_results": 15,
  "search_time_ms": 142
}
```

### Generation Response
```json
{
  "task_id": "rfc_20250115_143022",
  "status": "completed", 
  "content": "# RFC: API Authentication System\n\n## Abstract...",
  "sources_used": ["confluence", "gitlab", "jira"],
  "generation_time_ms": 3500,
  "tokens_used": 2800
}
```

---

## 🛠️ **Tools & Integration**

### Swagger UI
```bash
# Запустить локально с Swagger UI
docker run -p 8080:8080 swaggerapi/swagger-ui
# Открыть: http://localhost:8080/?url=http://localhost:8000/openapi.yaml
```

### Client SDK Generation
```bash
# Генерация Python SDK
openapi-generator generate -i openapi.yaml -g python -o ./sdk/python

# Генерация TypeScript SDK  
openapi-generator generate -i openapi.yaml -g typescript-fetch -o ./sdk/typescript
```

### Postman Collection
```bash
# Импорт в Postman
# File > Import > Link > http://localhost:8000/openapi.yaml
```

---

## ⚡ **Performance Tips**

1. **Semantic Search**: Используйте `hybrid_search: true` для лучших результатов
2. **Caching**: API автоматически кэширует поисковые запросы на 5 минут
3. **Rate Limits**: 100 requests/minute для search, 10 requests/minute для generation
4. **Timeouts**: Generation может занять до 10 минут для сложных RFC

---

## 🔗 **Полезные ссылки**

- 📄 **Full OpenAPI Spec**: `/openapi.yaml`
- 📖 **Documentation**: `/docs/`
- 🏥 **Health Check**: `/health`
- 🔧 **Admin Panel**: `/admin` (только для админов)

**Обновлено:** 2025-01-15  
**Версия API:** 3.1.0 