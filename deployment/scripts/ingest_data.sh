#!/bin/bash

# AI Assistant Data Ingestion Script
# Запуск процесса загрузки данных из всех источников

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

# Определение команды docker compose
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# Проверка что система запущена
check_system_running() {
    log_info "Checking if AI Assistant system is running..."
    
    if ! curl -s http://localhost:8000/health >/dev/null 2>&1; then
        log_error "AI Assistant system is not running!"
        log_info "Please start the system first: ./start_system.sh"
        exit 1
    fi
    
    if ! curl -s http://localhost:6333/health >/dev/null 2>&1; then
        log_error "Qdrant vector database is not running!"
        exit 1
    fi
    
    log_success "System is running and ready for data ingestion"
}

# Проверка конфигурации
check_configuration() {
    log_info "Checking ingestion configuration..."
    
    if [ ! -f "local/config/local_config.yml" ]; then
        log_error "Configuration file not found: local/config/local_config.yml"
        log_info "Please create the configuration file first"
        exit 1
    fi
    
    # Проверка директории bootstrap
    if [ ! -d "local/bootstrap" ]; then
        log_warning "Bootstrap directory not found, creating..."
        mkdir -p local/bootstrap
    fi
    
    # Подсчет файлов в bootstrap
    bootstrap_files=$(find local/bootstrap -type f \( -name "*.pdf" -o -name "*.txt" -o -name "*.epub" -o -name "*.md" -o -name "*.rst" -o -name "*.docx" \) 2>/dev/null | wc -l)
    log_info "Found $bootstrap_files files in bootstrap directory"
    
    log_success "Configuration checked"
}

# Создание контейнера для ingestion
prepare_ingestion_container() {
    log_info "Preparing data ingestion container..."
    
    # Сборка образа ingestion если не существует
    if ! docker images | grep -q "ai_assistant.*ingestion"; then
        log_info "Building ingestion container..."
        $DOCKER_COMPOSE -f docker-compose.full.yml build data_ingestion
    fi
    
    log_success "Ingestion container ready"
}

# Запуск процесса ingestion
run_ingestion() {
    log_info "Starting data ingestion process..."
    
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                  Data Ingestion Started                     ║"
    echo "║                                                              ║"
    echo "║  This process will load data from:                          ║"
    echo "║  • Confluence servers (if configured)                       ║"
    echo "║  • GitLab repositories (if configured)                      ║"
    echo "║  • Local bootstrap files                                    ║"
    echo "║                                                              ║"
    echo "║  Progress will be shown below...                            ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # Запуск ingestion контейнера
    $DOCKER_COMPOSE -f docker-compose.full.yml run --rm \
        --name ai_assistant_ingestion_runner \
        data_ingestion \
        python scripts/ingest_once.py /app/config/local_config.yml
    
    ingestion_exit_code=$?
    
    if [ $ingestion_exit_code -eq 0 ]; then
        log_success "Data ingestion completed successfully!"
    else
        log_error "Data ingestion failed with exit code: $ingestion_exit_code"
        return $ingestion_exit_code
    fi
}

# Показать статистику после ingestion
show_ingestion_stats() {
    log_info "Retrieving ingestion statistics..."
    
    # Проверка файла статистики
    if docker exec ai_assistant_backend test -f /app/logs/ingestion_stats.json 2>/dev/null; then
        echo -e "\n${BLUE}=== Ingestion Statistics ===${NC}"
        docker exec ai_assistant_backend cat /app/logs/ingestion_stats.json | python -m json.tool 2>/dev/null || {
            log_warning "Could not parse statistics file"
        }
    else
        log_warning "Statistics file not found"
    fi
    
    # Проверка количества документов в базе
    echo -e "\n${BLUE}=== Database Status ===${NC}"
    
    # Проверка через API
    if curl -s http://localhost:8000/api/v1/health >/dev/null 2>&1; then
        api_response=$(curl -s http://localhost:8000/api/v1/health)
        echo "API Health: $(echo $api_response | python -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")"
    fi
    
    # Проверка Qdrant коллекций
    if curl -s http://localhost:6333/collections >/dev/null 2>&1; then
        collections=$(curl -s http://localhost:6333/collections | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    collections = data.get('result', {}).get('collections', [])
    for col in collections:
        print(f\"Collection: {col['name']}, Points: {col.get('points_count', 0)}\")
except:
    print('Could not parse collections')
" 2>/dev/null)
        
        if [ -n "$collections" ]; then
            echo -e "\n${BLUE}=== Vector Collections ===${NC}"
            echo "$collections"
        fi
    fi
}

# Проверка качества данных
validate_data_quality() {
    log_info "Validating data quality..."
    
    # Тестовый поиск
    test_query="test"
    search_result=$(curl -s -X POST http://localhost:8000/api/v1/test/vector-search \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$test_query\", \"limit\": 5}" 2>/dev/null)
    
    if echo "$search_result" | grep -q "total_results"; then
        total_results=$(echo "$search_result" | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('total_results', 0))
except:
    print(0)
" 2>/dev/null)
        
        if [ "$total_results" -gt 0 ]; then
            log_success "Search functionality working - found $total_results results"
        else
            log_warning "Search working but no results found"
        fi
    else
        log_warning "Could not validate search functionality"
    fi
}

# Показать следующие шаги
show_next_steps() {
    echo -e "\n${BLUE}=== Next Steps ===${NC}"
    echo -e "1. ${GREEN}Test the API:${NC}"
    echo -e "   curl http://localhost:8000/api/v1/health"
    echo -e ""
    echo -e "2. ${GREEN}Try search:${NC}"
    echo -e "   curl -X POST http://localhost:8000/api/v1/test/vector-search \\"
    echo -e "        -H \"Content-Type: application/json\" \\"
    echo -e "        -d '{\"query\": \"your search query\", \"limit\": 5}'"
    echo -e ""
    echo -e "3. ${GREEN}View API documentation:${NC}"
    echo -e "   http://localhost:8000/docs"
    echo -e ""
    echo -e "4. ${GREEN}Monitor logs:${NC}"
    echo -e "   docker-compose -f docker-compose.full.yml logs -f backend"
    echo -e ""
    echo -e "5. ${GREEN}Re-run ingestion (if needed):${NC}"
    echo -e "   ./ingest_data.sh"
    echo -e ""
    echo -e "6. ${GREEN}Add more data:${NC}"
    echo -e "   - Update local/config/local_config.yml"
    echo -e "   - Add files to local/bootstrap/"
    echo -e "   - Run ./ingest_data.sh again"
}

# Функция очистки при прерывании
cleanup() {
    log_info "Cleaning up..."
    $DOCKER_COMPOSE -f docker-compose.full.yml stop data_ingestion 2>/dev/null || true
    docker rm ai_assistant_ingestion_runner 2>/dev/null || true
}

# Установка обработчика сигналов
trap cleanup EXIT INT TERM

# Главная функция
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                AI Assistant Data Ingestion                  ║"
    echo "║              Multi-source Data Loading                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    check_system_running
    check_configuration
    prepare_ingestion_container
    
    # Запуск ingestion
    if run_ingestion; then
        show_ingestion_stats
        validate_data_quality
        show_next_steps
        
        echo -e "\n${GREEN}🎉 Data ingestion completed successfully!${NC}"
        echo -e "${GREEN}📊 Your AI Assistant is now ready with loaded data!${NC}"
        return 0
    else
        log_error "Data ingestion failed!"
        echo -e "\n${RED}❌ Please check the logs for details:${NC}"
        echo -e "   docker-compose -f docker-compose.full.yml logs data_ingestion"
        return 1
    fi
}

# Обработка аргументов командной строки
case "$1" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "This script loads data from configured sources into AI Assistant:"
        echo "• Confluence servers"
        echo "• GitLab repositories" 
        echo "• Local bootstrap files"
        echo ""
        echo "Options:"
        echo "  --dry-run         Show what would be processed (not implemented)"
        echo "  --force           Force re-ingestion of all data"
        echo "  --help, -h        Show this help"
        echo ""
        echo "Configuration:"
        echo "  Edit local/config/local_config.yml to configure data sources"
        echo "  Add files to local/bootstrap/ for local file ingestion"
        echo ""
        echo "Prerequisites:"
        echo "  AI Assistant system must be running (./start_system.sh)"
        exit 0
        ;;
    --force)
        log_info "Force mode enabled - will re-ingest all data"
        export FORCE_REINGEST=true
        main
        ;;
    --dry-run)
        log_warning "Dry-run mode not yet implemented"
        exit 1
        ;;
    "")
        main
        ;;
    *)
        log_error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac 