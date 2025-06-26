#!/bin/bash

# Скрипт для запуска интеграционных тестов с таймаутами
# Использует существующие запущенные сервисы

set -e

echo "🚀 Запуск интеграционных тестов с таймаутами"

# Настройка переменных окружения
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=ai_assistant
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres

export REDIS_HOST=localhost
export REDIS_PORT=6379

export QDRANT_HOST=localhost
export QDRANT_PORT=6333

export ELASTICSEARCH_HOST=localhost
export ELASTICSEARCH_PORT=9200

export OPENAI_API_KEY=test_key

# Проверка существующих сервисов
echo "Проверка доступности сервисов..."

# PostgreSQL
if pg_isready -h localhost -p 5432 2>/dev/null; then
    echo "✅ PostgreSQL доступен"
else
    echo "❌ PostgreSQL недоступен"
fi

# Redis
if redis-cli -h localhost -p 6379 ping 2>/dev/null | grep -q PONG; then
    echo "✅ Redis доступен"
else
    echo "❌ Redis недоступен"
fi

# Qdrant
if curl -s http://localhost:6333/ > /dev/null 2>&1; then
    echo "✅ Qdrant доступен"
else
    echo "❌ Qdrant недоступен"
fi

echo
echo "Запуск интеграционных тестов..."

# Запускаем тесты с timeout и включаем Qdrant/Redis тесты
pytest tests/integration/ \
    --timeout=30 \
    --timeout-method=thread \
    -x \
    -v \
    --tb=short \
    --maxfail=3 \
    --durations=10 \
    --color=yes \
    "$@"

echo
echo "✅ Интеграционные тесты завершены"
