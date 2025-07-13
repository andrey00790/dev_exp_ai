#!/bin/bash

# wait-for-services.sh
# Скрипт для ожидания готовности сервисов перед запуском приложения

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для проверки готовности PostgreSQL
wait_for_postgres() {
    echo -e "${YELLOW}Waiting for PostgreSQL...${NC}"
    until pg_isready -h "${DATABASE_HOST:-test-postgres}" -p "${DATABASE_PORT:-5432}" -U "${DATABASE_USER:-test_user}" -d "${DATABASE_NAME:-ai_test}"; do
        echo -e "${YELLOW}PostgreSQL is not ready - sleeping...${NC}"
        sleep 2
    done
    echo -e "${GREEN}PostgreSQL is ready!${NC}"
}

# Функция для проверки готовности Redis
wait_for_redis() {
    echo -e "${YELLOW}Waiting for Redis...${NC}"
    until redis-cli -h "${REDIS_HOST:-test-redis}" -p "${REDIS_PORT:-6379}" ping; do
        echo -e "${YELLOW}Redis is not ready - sleeping...${NC}"
        sleep 2
    done
    echo -e "${GREEN}Redis is ready!${NC}"
}

# Функция для проверки готовности Qdrant
wait_for_qdrant() {
    echo -e "${YELLOW}Waiting for Qdrant...${NC}"
    until curl -f -s "http://${QDRANT_HOST:-test-qdrant}:${QDRANT_PORT:-6333}/health" > /dev/null; do
        echo -e "${YELLOW}Qdrant is not ready - sleeping...${NC}"
        sleep 2
    done
    echo -e "${GREEN}Qdrant is ready!${NC}"
}

# Функция для проверки готовности Elasticsearch (опционально)
wait_for_elasticsearch() {
    if [ "${ELASTICSEARCH_URL}" ]; then
        echo -e "${YELLOW}Waiting for Elasticsearch...${NC}"
        until curl -f -s "${ELASTICSEARCH_URL:-http://test-elasticsearch:9200}/_cluster/health" > /dev/null; do
            echo -e "${YELLOW}Elasticsearch is not ready - sleeping...${NC}"
            sleep 2
        done
        echo -e "${GREEN}Elasticsearch is ready!${NC}"
    fi
}

# Основная функция
main() {
    echo -e "${GREEN}Starting services readiness check...${NC}"
    
    # Ждем готовности основных сервисов
    wait_for_postgres
    wait_for_redis
    wait_for_qdrant
    
    # Ждем готовности дополнительных сервисов если они настроены
    wait_for_elasticsearch
    
    echo -e "${GREEN}All services are ready! Starting application...${NC}"
    
    # Запускаем переданную команду
    exec "$@"
}

# Запускаем основную функцию с переданными аргументами
main "$@" 