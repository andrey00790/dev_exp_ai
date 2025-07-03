#!/bin/bash

# Скрипт для запуска интеграционных тестов с Docker Compose
# Автоматически поднимает все необходимые сервисы

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Запуск интеграционных тестов с Docker Compose${NC}"

# Функция для логирования
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверяем наличие Docker и Docker Compose
if ! command -v docker &> /dev/null; then
    log_error "Docker не установлен"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose не установлен"
    exit 1
fi

# Переходим в корневую директорию проекта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

log_info "Проект: $PROJECT_ROOT"

# Проверяем наличие docker-compose.test.yml
if [ ! -f "docker-compose.test.yml" ]; then
    log_error "Файл docker-compose.test.yml не найден"
    exit 1
fi

# Очистка перед запуском
cleanup() {
    log_info "Очистка Docker контейнеров..."
    docker-compose -f docker-compose.test.yml down --volumes --remove-orphans || true
}

# Функция для ожидания готовности сервиса
wait_for_service() {
    local service=$1
    local host=$2
    local port=$3
    local timeout=${4:-60}
    
    log_info "Ожидание готовности $service ($host:$port)..."
    
    local count=0
    while ! nc -z "$host" "$port" 2>/dev/null; do
        if [ $count -ge $timeout ]; then
            log_error "Таймаут ожидания $service"
            return 1
        fi
        sleep 1
        count=$((count + 1))
    done
    
    log_success "$service готов"
    return 0
}

# Функция для проверки здоровья Qdrant
check_qdrant_health() {
    local host=${1:-localhost}
    local port=${2:-6334}
    local timeout=${3:-30}
    
    log_info "Проверка здоровья Qdrant..."
    
    local count=0
    while [ $count -lt $timeout ]; do
        if curl -s "http://$host:$port/" > /dev/null 2>&1; then
            log_success "Qdrant здоров"
            return 0
        fi
        sleep 2
        count=$((count + 2))
    done
    
    log_error "Qdrant не отвечает"
    return 1
}

# Функция для проверки здоровья Redis
check_redis_health() {
    local host=${1:-localhost}
    local port=${2:-6380}
    local timeout=${3:-30}
    
    log_info "Проверка здоровья Redis..."
    
    local count=0
    while [ $count -lt $timeout ]; do
        if redis-cli -h "$host" -p "$port" ping 2>/dev/null | grep -q PONG; then
            log_success "Redis здоров"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    
    log_error "Redis не отвечает"
    return 1
}

# Функция для проверки здоровья PostgreSQL
check_postgres_health() {
    local host=${1:-localhost}
    local port=${2:-5433}
    local timeout=${3:-30}
    
    log_info "Проверка здоровья PostgreSQL..."
    
    local count=0
    while [ $count -lt $timeout ]; do
        if pg_isready -h "$host" -p "$port" 2>/dev/null; then
            log_success "PostgreSQL здоров"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    
    log_error "PostgreSQL не отвечает"
    return 1
}

# Регистрируем обработчик для очистки
trap cleanup EXIT

# Останавливаем существующие контейнеры
log_info "Останавливаем существующие тестовые контейнеры..."
cleanup

# Запускаем сервисы
log_info "Запуск Docker Compose сервисов..."
docker-compose -f docker-compose.test.yml up -d

# Ждем готовности всех сервисов
log_info "Ожидание готовности сервисов..."

# PostgreSQL
if ! wait_for_service "PostgreSQL" "localhost" "5433" 60; then
    log_error "PostgreSQL не запустился"
    exit 1
fi

# Redis
if ! wait_for_service "Redis" "localhost" "6380" 60; then
    log_error "Redis не запустился"
    exit 1
fi

# Qdrant
if ! wait_for_service "Qdrant" "localhost" "6334" 60; then
    log_error "Qdrant не запустился"
    exit 1
fi

# Elasticsearch
if ! wait_for_service "Elasticsearch" "localhost" "9201" 60; then
    log_error "Elasticsearch не запустился"
    exit 1
fi

# Дополнительные проверки здоровья
log_info "Проверка здоровья сервисов..."

# Проверяем Redis
if ! check_redis_health "localhost" "6380"; then
    log_warning "Redis не прошел проверку здоровья, но продолжаем..."
fi

# Проверяем Qdrant
if ! check_qdrant_health "localhost" "6334"; then
    log_warning "Qdrant не прошел проверку здоровья, но продолжаем..."
fi

# Проверяем PostgreSQL
if ! check_postgres_health "localhost" "5433"; then
    log_warning "PostgreSQL не прошел проверку здоровья, но продолжаем..."
fi

# Настройка переменных окружения для тестов
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5433
export POSTGRES_DB=test_db
export POSTGRES_USER=test_user
export POSTGRES_PASSWORD=test_password

export REDIS_HOST=localhost
export REDIS_PORT=6380

export QDRANT_HOST=localhost
export QDRANT_PORT=6334

export ELASTICSEARCH_HOST=localhost
export ELASTICSEARCH_PORT=9201

export OPENAI_API_KEY=test_key
export OPENAI_API_BASE=http://localhost:8000

# Дополнительное время для стабилизации
log_info "Дополнительное время для стабилизации сервисов..."
sleep 10

# Запуск тестов
log_success "Все сервисы готовы! Запуск интеграционных тестов..."

# Запускаем тесты с подробным выводом
pytest tests/integration/ \
    --timeout=300 \
    --tb=short \
    --maxfail=5 \
    -v \
    --color=yes \
    --durations=10 \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html:htmlcov/integration \
    --junit-xml=test-results/integration-results.xml \
    "$@"

TEST_EXIT_CODE=$?

# Показываем логи сервисов в случае ошибок
if [ $TEST_EXIT_CODE -ne 0 ]; then
    log_error "Тесты завершились с ошибками"
    
    log_info "Логи PostgreSQL:"
    docker-compose -f docker-compose.test.yml logs postgres-test | tail -50
    
    log_info "Логи Redis:"
    docker-compose -f docker-compose.test.yml logs redis-test | tail -50
    
    log_info "Логи Qdrant:"
    docker-compose -f docker-compose.test.yml logs qdrant-test | tail -50
    
    log_info "Логи Elasticsearch:"
    docker-compose -f docker-compose.test.yml logs elasticsearch-test | tail -50
else
    log_success "Все интеграционные тесты прошли успешно!"
fi

exit $TEST_EXIT_CODE 