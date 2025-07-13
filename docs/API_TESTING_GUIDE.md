# 🧪 API Testing Guide - Руководство по тестированию API

**Версия:** 1.0.0  
**Дата:** 13 января 2025  
**Статус:** Ready for Testing

---

## 🎯 Быстрый старт

### Предварительные требования

1. **Запущенная система**:
   ```bash
   make full-system
   # или
   python main.py --port 8000 --host localhost
   ```

2. **Инструменты для тестирования**:
   - `curl` (встроен в Linux/macOS)
   - `jq` для красивого JSON: `brew install jq` или `apt install jq`

3. **Базовый URL**: `http://localhost:8000`

---

## 🔐 Получение токена для тестирования

### Шаг 1: Проверка здоровья системы
```bash
curl -s http://localhost:8000/health | jq '.'
```

**Ожидаемый ответ:**
```json
{
  "status": "healthy",
  "architecture": "hexagonal",
  "environment": "development",
  "version": "2.0.0"
}
```

### Шаг 2: Получение списка SSO провайдеров (без токена)
```bash
curl -s http://localhost:8000/api/v1/auth/sso/providers | jq '.'
```

**Ожидаемый ответ:**
```json
{
  "providers": [
    {"id": "google", "name": "Google", "enabled": true},
    {"id": "github", "name": "GitHub", "enabled": false}
  ],
  "total": 2
}
```

---

## 🚀 Тестирование основных функций

### ✅ 1. Health Checks

```bash
# Базовая проверка
curl -s http://localhost:8000/health

# Детальная проверка компонентов
curl -s http://localhost:8000/api/v1/health | jq '.'
```

### ✅ 2. API Documentation

```bash
# OpenAPI спецификация
curl -s http://localhost:8000/openapi.json | jq '.info'

# Swagger UI (откроется в браузере)
open http://localhost:8000/docs
```

### ✅ 3. Mock Endpoints (работают без аутентификации)

#### Generate Mock
```bash
curl -s -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello AI"}' | jq '.'
```

**Ожидаемый ответ:**
```json
{
  "generation_id": "gen_12345",
  "type": "document",
  "status": "processing",
  "estimated_completion": 1234567890
}
```

#### Optimize Mock
```bash
curl -s -X POST http://localhost:8000/api/v1/optimize \
  -H "Content-Type: application/json" \
  -d '{"target": "performance"}' | jq '.'
```

**Ожидаемый ответ:**
```json
{
  "optimization_id": "opt_54321",
  "target": "performance",
  "status": "started",
  "current_metrics": {"response_time": 250},
  "target_metrics": {"response_time": 150}
}
```

### ✅ 4. Users Endpoint
```bash
curl -s http://localhost:8000/api/v1/users | jq '.'
```

### ✅ 5. Data Sources
```bash
curl -s http://localhost:8000/api/v1/data-sources | jq '.'
```

---

## 🔧 Тестирование с переменными окружения

### Настройка переменных
```bash
# Базовые настройки
export API_BASE_URL="http://localhost:8000"
export API_V1_URL="$API_BASE_URL/api/v1"

# Если у вас есть JWT токен
export JWT_TOKEN="your_jwt_token_here"
```

### Примеры с переменными
```bash
# Health check
curl -s $API_BASE_URL/health | jq '.'

# SSO providers
curl -s $API_V1_URL/auth/sso/providers | jq '.'

# С токеном (если есть)
curl -s $API_V1_URL/users \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'
```

---

## 🧪 Скрипты для автоматического тестирования

### test_basic_endpoints.sh
```bash
#!/bin/bash

echo "🧪 Testing AI Assistant API..."

API_BASE="http://localhost:8000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_endpoint() {
    local name="$1"
    local url="$2"
    local method="${3:-GET}"
    local data="$4"
    
    echo -n "Testing $name... "
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        response=$(curl -s -X POST "$url" -H "Content-Type: application/json" -d "$data")
    else
        response=$(curl -s "$url")
    fi
    
    if [ $? -eq 0 ] && [ -n "$response" ]; then
        echo -e "${GREEN}✅ OK${NC}"
        echo "  Response: $(echo $response | jq -c '.' 2>/dev/null || echo $response | head -c 100)..."
    else
        echo -e "${RED}❌ FAILED${NC}"
    fi
    echo
}

# Run tests
echo -e "${YELLOW}=== Basic Health Checks ===${NC}"
test_endpoint "Health Check" "$API_BASE/health"
test_endpoint "API Health" "$API_BASE/api/v1/health"

echo -e "${YELLOW}=== Authentication ===${NC}"
test_endpoint "SSO Providers" "$API_BASE/api/v1/auth/sso/providers"

echo -e "${YELLOW}=== Mock Endpoints ===${NC}"
test_endpoint "Generate Mock" "$API_BASE/api/v1/generate" "POST" '{"query": "test"}'
test_endpoint "Optimize Mock" "$API_BASE/api/v1/optimize" "POST" '{"target": "performance"}'

echo -e "${YELLOW}=== Data Endpoints ===${NC}"
test_endpoint "Users" "$API_BASE/api/v1/users"
test_endpoint "Data Sources" "$API_BASE/api/v1/data-sources"

echo -e "${GREEN}🎉 Testing completed!${NC}"
```

### Запуск тестового скрипта
```bash
# Сохранить скрипт в файл
chmod +x test_basic_endpoints.sh
./test_basic_endpoints.sh
```

---

## 🔍 Отладка и диагностика

### Проверка логов
```bash
# Если система запущена через make
tail -f logs/system_full.log

# Если запущена напрямую
# Логи будут в терминале
```

### Проверка портов
```bash
# Проверить что порт 8000 слушается
lsof -i :8000

# Проверить все порты системы
lsof -i :8000 -i :8001 -i :6333 -i :5432
```

### Проверка Docker контейнеров
```bash
# Статус контейнеров
docker ps

# Логи конкретного контейнера
docker logs ai-assistant-qdrant-dev
docker logs ai-assistant-postgres-dev
```

---

## 📊 Benchmark тестирование

### Простой load test
```bash
# Установить apache bench
# Ubuntu: apt install apache2-utils
# macOS: brew install httpie

# Тест health endpoint
ab -n 100 -c 10 http://localhost:8000/health

# Тест с POST запросами
ab -n 50 -c 5 -p data.json -T application/json \
   http://localhost:8000/api/v1/generate
```

### Данные для POST тестов (data.json)
```json
{"query": "test query", "type": "simple"}
```

---

## 🚨 Решение проблем

### Частые ошибки

#### Connection refused
```bash
# Проблема: сервер не запущен
# Решение:
make backend
# или
python main.py
```

#### Address already in use
```bash
# Проблема: порт 8000 занят
# Решение:
pkill -f "python.*main.py"
lsof -ti:8000 | xargs kill -9
```

#### 404 Not Found
```bash
# Проблема: неправильный URL
# Проверить доступные endpoints:
curl http://localhost:8000/docs
```

#### Invalid JSON
```bash
# Проблема: некорректный JSON в POST
# Решение: проверить синтаксис
echo '{"query": "test"}' | jq '.'
```

---

## 📋 Чеклист для тестирования

### ✅ Базовая функциональность
- [ ] Health check отвечает
- [ ] API документация доступна  
- [ ] SSO providers возвращает список
- [ ] Generate endpoint работает
- [ ] Optimize endpoint работает

### ✅ Инфраструктура
- [ ] Postgres доступен (port 5432)
- [ ] Redis доступен (port 6379)
- [ ] Qdrant доступен (port 6333)
- [ ] Ollama доступен (port 11434)

### ✅ Performance
- [ ] Health check < 50ms
- [ ] Generate mock < 200ms
- [ ] API docs загружается < 1s

---

## 🔗 Полезные ссылки

- **API Documentation**: http://localhost:8000/docs
- **OpenAPI Spec**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health
- **Adminer (DB)**: http://localhost:8080
- **Redis Commander**: http://localhost:8081

---

**📅 Последнее обновление**: 13 января 2025  
**🏷️ Версия**: 1.0.0  
**📊 Статус**: Ready for Testing 