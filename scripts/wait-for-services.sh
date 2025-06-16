#!/bin/bash
set -e

echo "🔄 Ожидание готовности сервисов..."

# Функция для проверки доступности сервиса
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1

    echo "⏳ Ожидание $service_name ($host:$port)..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "✅ $service_name готов!"
            return 0
        fi
        
        echo "   Попытка $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name не готов после $max_attempts попыток"
    return 1
}

# Функция для проверки HTTP endpoint
wait_for_http() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1

    echo "⏳ Ожидание HTTP $service_name ($url)..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" >/dev/null 2>&1; then
            echo "✅ $service_name HTTP готов!"
            return 0
        fi
        
        echo "   HTTP попытка $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name HTTP не готов после $max_attempts попыток"
    return 1
}

# Проверяем доступность netcat
if ! command -v nc &> /dev/null; then
    echo "Установка netcat..."
    apt-get update && apt-get install -y netcat-openbsd
fi

# Ожидаем готовности основных сервисов
wait_for_service "postgres" "5432" "PostgreSQL"
wait_for_service "qdrant" "6333" "Qdrant"

# Дополнительные HTTP проверки
wait_for_http "http://qdrant:6333/health" "Qdrant"

# Проверяем подключение к PostgreSQL
echo "🔍 Проверка подключения к PostgreSQL..."
until PGPASSWORD=testpass psql -h postgres -U testuser -d testdb -c '\q' 2>/dev/null; do
    echo "   Ожидание готовности PostgreSQL..."
    sleep 2
done
echo "✅ PostgreSQL подключение готово!"

echo "🎉 Все сервисы готовы! Запускаем приложение..."

# Выполняем переданную команду
exec "$@" 