#!/bin/bash

# AI Assistant MVP - System Startup Script
# Запуск всей системы одной командой

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для логирования
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

# Проверка зависимостей
check_dependencies() {
    log_info "Checking dependencies..."
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Определение команды docker compose
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        DOCKER_COMPOSE="docker compose"
    fi
    
    log_success "All dependencies are available"
}

# Создание необходимых директорий
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p local/config
    mkdir -p local/bootstrap
    mkdir -p local/logs
    mkdir -p local/uploads
    mkdir -p scripts/ingestion
    
    log_success "Directories created"
}

# Проверка конфигурации
check_configuration() {
    log_info "Checking configuration..."
    
    # Проверка основного конфига
    if [ ! -f "local/config/local_config.yml" ]; then
        log_warning "Configuration file not found. Creating example config..."
        cat > local/config/local_config.yml << 'EOF'
# AI Assistant Data Ingestion Configuration
# Пример конфигурации - настройте под ваши нужды

database:
  url: "postgresql://ai_user:ai_password_secure_2024@postgres:5432/ai_assistant"
  pool_size: 20

vector_db:
  url: "http://qdrant:6333"
  collection_size: 1536

processing:
  max_workers: 10
  chunk_size: 1000
  batch_size: 50
  timeout_seconds: 300

confluence:
  servers: []
  # - name: "main_confluence"
  #   url: "https://your-company.atlassian.net"
  #   username: "your-email@company.com"
  #   api_token: "your-confluence-api-token"
  #   spaces: ["TECH", "PROJ"]

gitlab:
  servers: []
  # - name: "main_gitlab"
  #   url: "https://gitlab.company.com"
  #   token: "glpat-your-gitlab-token"
  #   groups: ["backend-team"]

local_files:
  bootstrap_dir: "/app/bootstrap"
  supported_formats: [".pdf", ".txt", ".epub", ".md", ".rst"]
  max_file_size_mb: 50

text_processing:
  chunk_size: 1000
  chunk_overlap: 200
  language: "ru"

embeddings:
  provider: "openai"
  model: "text-embedding-ada-002"
  batch_size: 100

logging:
  level: "INFO"
  file: "/app/logs/ingestion.log"
EOF
        log_warning "Please edit local/config/local_config.yml with your actual configuration"
    fi
    
    # Проверка .env файла
    if [ ! -f ".env" ]; then
        log_warning "Environment file not found. Creating example .env..."
        cat > .env << 'EOF'
# AI Assistant Environment Variables
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
SECRET_KEY=your-super-secret-key-change-in-production
ENVIRONMENT=development
DEBUG=false
EOF
        log_warning "Please edit .env with your actual API keys"
    fi
    
    log_success "Configuration checked"
}

# Создание примера bootstrap файлов
create_bootstrap_examples() {
    if [ ! -f "local/bootstrap/README.md" ]; then
        log_info "Creating bootstrap example files..."
        
        cat > local/bootstrap/README.md << 'EOF'
# Bootstrap Directory

Поместите здесь файлы для обучения модели:
- PDF документы
- Текстовые файлы (.txt)
- EPUB книги
- Markdown файлы (.md)
- reStructuredText файлы (.rst)

Файлы будут автоматически обработаны и добавлены в векторную базу данных.

## Поддерживаемые форматы:
- .pdf - PDF документы
- .txt - Текстовые файлы
- .epub - Электронные книги
- .md - Markdown файлы  
- .rst - reStructuredText файлы
- .docx - Microsoft Word документы

## Ограничения:
- Максимальный размер файла: 50MB
- Минимальная длина содержимого: 50 символов
EOF

        cat > local/bootstrap/example.txt << 'EOF'
Это пример текстового файла для обучения AI Assistant.

Вы можете добавить сюда любую документацию, руководства, 
технические спецификации или другие текстовые материалы.

AI Assistant будет использовать эту информацию для ответов 
на вопросы и генерации контента.
EOF
        
        log_success "Bootstrap examples created"
    fi
}

# Сборка Docker образов
build_images() {
    log_info "Building Docker images..."
    
    # Создание Dockerfile.backend если не существует
    if [ ! -f "Dockerfile.backend" ]; then
        log_info "Creating Dockerfile.backend..."
        cat > Dockerfile.backend << 'EOF'
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
    fi
    
    # Сборка образов
    $DOCKER_COMPOSE -f docker-compose.full.yml build
    
    log_success "Docker images built"
}

# Запуск системы
start_system() {
    log_info "Starting AI Assistant system..."
    
    # Остановка существующих контейнеров
    $DOCKER_COMPOSE -f docker-compose.full.yml down 2>/dev/null || true
    
    # Запуск основных сервисов
    $DOCKER_COMPOSE -f docker-compose.full.yml up -d postgres redis qdrant
    
    log_info "Waiting for databases to be ready..."
    sleep 30
    
    # Запуск backend
    $DOCKER_COMPOSE -f docker-compose.full.yml up -d backend
    
    log_info "Waiting for backend to be ready..."
    sleep 20
    
    # Запуск frontend (опционально)
    if [ "$1" = "--with-frontend" ]; then
        $DOCKER_COMPOSE -f docker-compose.full.yml up -d frontend
        log_info "Frontend started"
    fi
    
    log_success "AI Assistant system started successfully!"
}

# Проверка статуса системы
check_system_status() {
    log_info "Checking system status..."
    
    # Проверка здоровья сервисов
    echo -e "\n${BLUE}=== Service Status ===${NC}"
    $DOCKER_COMPOSE -f docker-compose.full.yml ps
    
    echo -e "\n${BLUE}=== Health Checks ===${NC}"
    
    # Проверка PostgreSQL
    if docker exec ai_assistant_postgres pg_isready -U ai_user -d ai_assistant >/dev/null 2>&1; then
        log_success "PostgreSQL: Healthy"
    else
        log_error "PostgreSQL: Unhealthy"
    fi
    
    # Проверка Redis
    if docker exec ai_assistant_redis redis-cli ping >/dev/null 2>&1; then
        log_success "Redis: Healthy"
    else
        log_error "Redis: Unhealthy"
    fi
    
    # Проверка Qdrant
    if curl -s http://localhost:6333/health >/dev/null 2>&1; then
        log_success "Qdrant: Healthy"
    else
        log_error "Qdrant: Unhealthy"
    fi
    
    # Проверка Backend
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        log_success "Backend: Healthy"
        echo -e "\n${GREEN}🎉 System is ready!${NC}"
        echo -e "${BLUE}📖 API Documentation: http://localhost:8000/docs${NC}"
        echo -e "${BLUE}🔍 Qdrant UI: http://localhost:6333/dashboard${NC}"
    else
        log_error "Backend: Unhealthy"
    fi
}

# Показать информацию о доступе
show_access_info() {
    echo -e "\n${BLUE}=== Access Information ===${NC}"
    echo -e "${GREEN}🌐 API Server:${NC} http://localhost:8000"
    echo -e "${GREEN}📖 API Docs:${NC} http://localhost:8000/docs"
    echo -e "${GREEN}🔍 Qdrant Dashboard:${NC} http://localhost:6333/dashboard"
    echo -e "${GREEN}📊 Grafana (if enabled):${NC} http://localhost:3001 (admin/admin123)"
    echo -e "${GREEN}📈 Prometheus (if enabled):${NC} http://localhost:9090"
    
    if $DOCKER_COMPOSE -f docker-compose.full.yml ps frontend | grep -q "Up"; then
        echo -e "${GREEN}🖥️ Frontend:${NC} http://localhost:3000"
    fi
    
    echo -e "\n${BLUE}=== Next Steps ===${NC}"
    echo -e "1. Configure your data sources in: ${YELLOW}local/config/local_config.yml${NC}"
    echo -e "2. Add training files to: ${YELLOW}local/bootstrap/${NC}"
    echo -e "3. Run data ingestion: ${YELLOW}./ingest_data.sh${NC}"
    echo -e "4. Monitor logs: ${YELLOW}docker-compose -f docker-compose.full.yml logs -f${NC}"
}

# Главная функция
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                   AI Assistant MVP                          ║"
    echo "║              System Startup Script                          ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    check_dependencies
    create_directories
    check_configuration
    create_bootstrap_examples
    build_images
    start_system "$1"
    
    sleep 10
    
    check_system_status
    show_access_info
    
    echo -e "\n${GREEN}🚀 AI Assistant system is now running!${NC}"
}

# Обработка аргументов командной строки
case "$1" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --with-frontend    Start with frontend"
        echo "  --monitoring       Start with monitoring (Grafana/Prometheus)"
        echo "  --help, -h         Show this help"
        echo ""
        echo "Examples:"
        echo "  $0                 Start basic system"
        echo "  $0 --with-frontend Start with frontend"
        exit 0
        ;;
    --monitoring)
        export COMPOSE_PROFILES=monitoring
        main
        ;;
    *)
        main "$1"
        ;;
esac 