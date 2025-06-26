# 🔌 OpenAPI Setup & Usage Guide

Полное руководство по использованию OpenAPI спецификации AI Assistant API.

## 📋 **Обзор**

**Файл спецификации:** `/openapi.yaml`  
**Версия:** OpenAPI 3.0.3  
**API Версия:** 3.1.0  
**Endpoints:** 90+  
**Схемы данных:** 80+

## 🚀 **Quick Start**

### 1. **Просмотр спецификации**

```bash
# Открыть в браузере
open openapi.yaml

# Валидация YAML синтаксиса
python3 -c "import yaml; yaml.safe_load(open('openapi.yaml')); print('✅ Valid YAML')"
```

### 2. **Swagger UI (Interactive Documentation)**

```bash
# Локально с Docker
docker run -p 8080:8080 -e SWAGGER_JSON=/api/openapi.yaml \
  -v $(pwd)/openapi.yaml:/api/openapi.yaml swaggerapi/swagger-ui

# Открыть: http://localhost:8080
```

### 3. **Postman Integration**

```bash
# Импорт коллекции
# Postman > File > Import > Link > Paste: 
# http://localhost:8000/openapi.yaml
```

---

## 🛠️ **Client SDK Generation**

### **Python SDK**

```bash
# Установка OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# Генерация Python SDK
openapi-generator generate \
  -i openapi.yaml \
  -g python \
  -o ./sdk/python \
  --package-name ai_assistant_sdk

# Использование
cd sdk/python
pip install .
```

```python
import ai_assistant_sdk
from ai_assistant_sdk.api import vector_search_api
from ai_assistant_sdk.model.vector_search_request import VectorSearchRequest

# Создание клиента
configuration = ai_assistant_sdk.Configuration(
    host="http://localhost:8000",
    access_token="your-jwt-token"
)
api_client = ai_assistant_sdk.ApiClient(configuration)
api_instance = vector_search_api.VectorSearchApi(api_client)

# Поиск
search_request = VectorSearchRequest(
    query="Docker deployment patterns",
    limit=10,
    hybrid_search=True
)
response = api_instance.search_documents(search_request)
print(f"Found {len(response.results)} results")
```

### **TypeScript/JavaScript SDK**

```bash
# Генерация TypeScript SDK
openapi-generator generate \
  -i openapi.yaml \
  -g typescript-fetch \
  -o ./sdk/typescript

# Использование
cd sdk/typescript
npm install
```

```typescript
import { Configuration, VectorSearchApi, VectorSearchRequest } from './sdk/typescript';

// Создание клиента
const config = new Configuration({
  basePath: 'http://localhost:8000',
  accessToken: 'your-jwt-token'
});
const api = new VectorSearchApi(config);

// Поиск
const searchRequest: VectorSearchRequest = {
  query: 'Docker deployment patterns',
  limit: 10,
  hybridSearch: true
};

api.searchDocuments({ vectorSearchRequest: searchRequest })
  .then(response => {
    console.log(`Found ${response.results.length} results`);
  });
```

### **Go SDK**

```bash
# Генерация Go SDK
openapi-generator generate \
  -i openapi.yaml \
  -g go \
  -o ./sdk/go \
  --package-name aiassistant
```

### **Java SDK**

```bash
# Генерация Java SDK
openapi-generator generate \
  -i openapi.yaml \
  -g java \
  -o ./sdk/java \
  --library=resttemplate
```

---

## 🔧 **Development Tools**

### **VS Code Extensions**

```json
// .vscode/extensions.json
{
  "recommendations": [
    "42crunch.vscode-openapi",
    "redhat.vscode-yaml",
    "ms-vscode.vscode-json"
  ]
}
```

### **API Testing**

```bash
# curl примеры
curl -X POST "http://localhost:8000/api/v1/vector-search/search" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "API authentication patterns",
    "limit": 5,
    "hybrid_search": true
  }'
```

### **Validation Tools**

```bash
# Swagger Editor для валидации
docker run -p 8081:8080 swaggerapi/swagger-editor

# Spectral для линтинга
npm install -g @stoplight/spectral-cli
spectral lint openapi.yaml
```

---

## 📊 **API Categories Overview**

### **1. Authentication (12 endpoints)**
- User registration/login
- Token management  
- Budget tracking
- Profile management

### **2. Vector Search (9 endpoints)**
- Semantic search
- Document indexing
- File uploads
- Collections management

### **3. Document Generation (5 endpoints)**
- RFC generation
- Architecture docs
- Technical documentation
- Template management

### **4. Data Sources (6 endpoints)**
- Source configuration
- Sync management
- Status monitoring

### **5. AI Enhancement (5 endpoints)**
- Model training
- Quality analysis
- Performance optimization

### **6. Feedback System (7 endpoints)**
- User feedback
- Analytics
- Model retraining

### **7. User Management (4 endpoints)**
- User CRUD operations
- Settings management

### **8. Health & Monitoring (2 endpoints)**
- System health
- Component status

---

## 🔐 **Authentication Examples**

### **JWT Token Flow**

```bash
# 1. Login
LOGIN_RESPONSE=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo@company.com", "password": "demo_password"}')

# 2. Extract token
TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

# 3. Use token for API calls
curl -X POST "http://localhost:8000/api/v1/vector-search/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication patterns", "limit": 5}'
```

### **Demo Users**

```bash
# Получить список demo пользователей
curl "http://localhost:8000/api/v1/auth/demo-users"
```

---

## 📈 **Performance & Limits**

### **Rate Limits**
- **Search endpoints**: 100 requests/minute
- **Generation endpoints**: 10 requests/minute  
- **Authentication**: 5 requests/minute
- **Other endpoints**: 50 requests/minute

### **Response Times**
- **Search**: <150ms average
- **Generation**: 3-30 seconds
- **Authentication**: <100ms
- **Health checks**: <50ms

### **Data Limits**
- **Search query**: 1000 characters max
- **Document upload**: 10MB max
- **Generation input**: 5000 characters max
- **Bulk operations**: 100 items max

---

## 🧪 **Testing with OpenAPI**

### **Automated Testing**

```bash
# Установка Dredd для contract testing
npm install -g dredd

# Тестирование API против спецификации
dredd openapi.yaml http://localhost:8000
```

### **Load Testing**

```bash
# k6 с OpenAPI
npm install -g k6
k6 run --out json=load_test_results.json load_test_script.js
```

---

## 🔄 **CI/CD Integration**

### **GitHub Actions**

```yaml
# .github/workflows/api-validation.yml
name: API Validation
on: [push, pull_request]

jobs:
  validate-openapi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate OpenAPI Spec
        uses: char0n/swagger-editor-validate@v1
        with:
          definition-file: openapi.yaml
```

### **Docker Integration**

```dockerfile
# API documentation container
FROM swaggerapi/swagger-ui:latest
COPY openapi.yaml /usr/share/nginx/html/
ENV SWAGGER_JSON=/usr/share/nginx/html/openapi.yaml
EXPOSE 8080
```

---

## 📚 **Best Practices**

### **Schema Design**
- ✅ Use descriptive names for schemas
- ✅ Include examples in schemas
- ✅ Define proper validation rules
- ✅ Use refs for reusable components

### **Documentation**
- ✅ Provide clear endpoint descriptions
- ✅ Include usage examples
- ✅ Document error responses
- ✅ Keep documentation up-to-date

### **Versioning**
- ✅ Use semantic versioning
- ✅ Document breaking changes
- ✅ Maintain backward compatibility
- ✅ Plan deprecation strategy

---

## 🔗 **Useful Links**

- 📄 **OpenAPI Specification**: https://spec.openapis.org/oas/v3.0.3
- 🛠️ **OpenAPI Generator**: https://openapi-generator.tech/
- 🌐 **Swagger UI**: https://swagger.io/tools/swagger-ui/
- 🔧 **Postman**: https://www.postman.com/
- 📊 **Spectral Linter**: https://stoplight.io/open-source/spectral

---

## 📞 **Support**

При возникновении проблем с API:
1. Проверьте статус системы: `/health`
2. Валидируйте запрос против OpenAPI схемы
3. Проверьте токен аутентификации
4. Обратитесь к [API Reference](API_REFERENCE.md)

**Контакты:**
- 📧 API Support: api-support@company.com
- 🐛 Bug Reports: GitHub Issues
- 💬 General Questions: GitHub Discussions

---

**Обновлено:** 2025-01-15  
**OpenAPI Version:** 3.0.3  
**API Version:** 3.1.0 