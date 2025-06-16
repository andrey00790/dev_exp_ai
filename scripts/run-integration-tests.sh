#!/bin/bash
set -e

echo "🚀 Запуск интеграционных тестов (PostgreSQL + Qdrant)"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    error "Docker не установлен!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose не установлен!"
    exit 1
fi

# Создаем директории если их нет
mkdir -p logs test-data/integration scripts

# Останавливаем существующие контейнеры
log "Останавливаем существующие контейнеры..."
docker-compose -f docker-compose.integration.yml down --remove-orphans || true

# Очищаем volumes если нужно
if [ "$1" = "--clean" ]; then
    log "Очищаем volumes..."
    docker-compose -f docker-compose.integration.yml down -v
    docker volume prune -f
fi

# Собираем образы
log "Собираем Docker образы..."
docker-compose -f docker-compose.integration.yml build

# Запускаем сервисы
log "Запускаем сервисы..."
docker-compose -f docker-compose.integration.yml up -d

# Ждем готовности сервисов
log "Ожидаем готовности сервисов..."
timeout 300 bash -c '
    while ! docker-compose -f docker-compose.integration.yml ps | grep -q "healthy"; do
        echo "Ожидание готовности сервисов..."
        sleep 5
    done
'

# Проверяем статус сервисов
log "Проверяем статус сервисов..."
docker-compose -f docker-compose.integration.yml ps

# Запускаем тесты
log "Запускаем интеграционные тесты..."

# 1. Тесты базы данных PostgreSQL
log "1. Тесты базы данных PostgreSQL..."
docker-compose -f docker-compose.integration.yml exec -T app_test \
    python -m pytest tests/integration/test_database_integration.py -v --tb=short \
    --junitxml=/app/logs/database-integration-tests.xml \
    --html=/app/logs/database-integration-tests.html \
    || TEST_FAILED=1

# 2. Тесты кэширования в PostgreSQL
log "2. Тесты кэширования в PostgreSQL..."
docker-compose -f docker-compose.integration.yml exec -T app_test \
    python -m pytest tests/integration/test_postgresql_cache.py -v --tb=short \
    --junitxml=/app/logs/postgresql-cache-tests.xml \
    || TEST_FAILED=1

# 3. Тесты поиска в PostgreSQL
log "3. Тесты поиска в PostgreSQL..."
docker-compose -f docker-compose.integration.yml exec -T app_test \
    python -m pytest tests/integration/test_postgresql_search.py -v --tb=short \
    --junitxml=/app/logs/postgresql-search-tests.xml \
    || TEST_FAILED=1

# 4. Тесты векторного поиска Qdrant
log "4. Тесты векторного поиска Qdrant..."
docker-compose -f docker-compose.integration.yml exec -T app_test \
    python -m pytest tests/integration/test_qdrant_integration.py -v --tb=short \
    --junitxml=/app/logs/qdrant-integration-tests.xml \
    || TEST_FAILED=1

# 5. Интеграционные тесты API
log "5. Интеграционные тесты API..."
docker-compose -f docker-compose.integration.yml exec -T app_test \
    python -m pytest tests/integration/test_api_integration.py -v --tb=short \
    --junitxml=/app/logs/api-integration-tests.xml \
    || TEST_FAILED=1

# 6. Тесты производительности
log "6. Тесты производительности..."
docker-compose -f docker-compose.integration.yml exec -T app_test \
    python -m pytest tests/integration/test_performance.py -v --tb=short \
    --junitxml=/app/logs/performance-tests.xml \
    || TEST_FAILED=1

# 7. Smoke тесты
log "7. Smoke тесты..."
docker-compose -f docker-compose.integration.yml exec -T app_test \
    python -m pytest tests/smoke/ -v --tb=short \
    --junitxml=/app/logs/smoke-tests.xml \
    || TEST_FAILED=1

# Собираем логи
log "Собираем логи..."
docker-compose -f docker-compose.integration.yml logs > logs/docker-compose.log

# Копируем отчеты
log "Копируем отчеты..."
docker cp $(docker-compose -f docker-compose.integration.yml ps -q app_test):/app/logs/ ./logs/integration/ || true

# Проверяем результаты
if [ "$TEST_FAILED" = "1" ]; then
    error "Некоторые тесты не прошли!"
    
    # Показываем логи неудачных тестов
    log "Логи приложения:"
    docker-compose -f docker-compose.integration.yml logs app_test | tail -50
    
    # Показываем логи PostgreSQL
    log "Логи PostgreSQL:"
    docker-compose -f docker-compose.integration.yml logs postgres | tail -20
    
    # Показываем логи Qdrant
    log "Логи Qdrant:"
    docker-compose -f docker-compose.integration.yml logs qdrant | tail -20
    
    # Останавливаем сервисы если тесты не прошли
    if [ "$2" != "--keep-running" ]; then
        log "Останавливаем сервисы..."
        docker-compose -f docker-compose.integration.yml down
    fi
    
    exit 1
else
    success "Все интеграционные тесты прошли успешно! 🎉"
    
    # Показываем статистику
    log "Статистика тестов:"
    find logs/integration -name "*.xml" -exec echo "📊 {}" \; -exec grep -o 'tests="[0-9]*"' {} \; 2>/dev/null || true
    
    # Показываем статистику использования ресурсов
    log "Статистика ресурсов:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" || true
    
    # Останавливаем сервисы
    if [ "$2" != "--keep-running" ]; then
        log "Останавливаем сервисы..."
        docker-compose -f docker-compose.integration.yml down
    else
        warning "Сервисы оставлены запущенными (--keep-running)"
        log "Для остановки выполните: docker-compose -f docker-compose.integration.yml down"
        log "PostgreSQL доступен на localhost:5433"
        log "Qdrant доступен на localhost:6334"
        log "Приложение доступно на localhost:8001"
    fi
fi

success "Интеграционные тесты завершены!"
log "Отчеты сохранены в директории logs/integration/" 