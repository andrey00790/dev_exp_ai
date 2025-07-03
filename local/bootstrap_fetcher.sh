#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# bootstrap_fetcher.sh
#
# Автоматизированная загрузка обучающих материалов из resource_config.yml
#
# Функциональность:
#   • Проверяет зависимости (Python, pip, yaml)
#   • Устанавливает необходимые пакеты
#   • Запускает bootstrap_fetcher.py
#   • Интегрируется с существующим workflow
# ──────────────────────────────────────────────────────────────────────────────

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Путь к скрипту
SCRIPT_DIR="$(cd "$(dirname "$0")" >/dev/null 2>&1 && pwd)"
BOOTSTRAP_FETCHER="${SCRIPT_DIR}/bootstrap_fetcher.py"
CONFIG_FILE="${SCRIPT_DIR}/resource_config.yml"
OUTPUT_DIR="${SCRIPT_DIR}/bootstrap"

# Функции для вывода
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
    log_info "🔍 Проверяем зависимости..."
    
    # Проверяем Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 не найден! Установите Python 3.8+"
        exit 1
    fi
    
    # Проверяем pip
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        log_error "pip не найден! Установите pip"
        exit 1
    fi
    
    # Определяем команду pip
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    else
        PIP_CMD="pip"
    fi
    
    log_success "Python и pip найдены"
}

# Установка Python зависимостей
install_python_deps() {
    log_info "📦 Устанавливаем Python зависимости..."
    
    # Список необходимых пакетов
    REQUIRED_PACKAGES=(
        "PyYAML>=6.0"
        "requests>=2.25.0"
        "pathlib"
    )
    
    for package in "${REQUIRED_PACKAGES[@]}"; do
        log_info "Устанавливаем $package..."
        $PIP_CMD install --quiet "$package" || {
            log_error "Не удалось установить $package"
            exit 1
        }
    done
    
    log_success "Все зависимости установлены"
}

# Проверка файлов
check_files() {
    log_info "📁 Проверяем необходимые файлы..."
    
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "Файл конфигурации не найден: $CONFIG_FILE"
        exit 1
    fi
    
    if [[ ! -f "$BOOTSTRAP_FETCHER" ]]; then
        log_error "Скрипт загрузчика не найден: $BOOTSTRAP_FETCHER"
        exit 1
    fi
    
    # Создаем выходную директорию если её нет
    mkdir -p "$OUTPUT_DIR"
    
    log_success "Все файлы на месте"
}

# Показ справки
show_help() {
    cat << EOF
🚀 Bootstrap Fetcher - Автоматизированная загрузка обучающих материалов

ИСПОЛЬЗОВАНИЕ:
    $0 [ОПЦИИ]

ОПЦИИ:
    -h, --help          Показать эту справку
    -t, --test          Тестовый режим (загрузить только 5 ресурсов)
    -c, --category CAT  Загрузить только ресурсы категории CAT
    -o, --output DIR    Папка для сохранения (по умолчанию: bootstrap)
    -n, --max-resources N   Максимальное количество ресурсов
    --no-install        Пропустить установку зависимостей
    --dry-run          Только показать что будет загружено

ПРИМЕРЫ:
    $0                          # Загрузить все ресурсы
    $0 --test                   # Тестовая загрузка (5 ресурсов)
    $0 --category system_design # Только System Design материалы
    $0 --max-resources 10       # Только первые 10 ресурсов

ФАЙЛЫ:
    Конфигурация: $CONFIG_FILE
    Загрузчик:    $BOOTSTRAP_FETCHER
    Выходная папка: $OUTPUT_DIR

EOF
}

# Разбор аргументов
parse_args() {
    # Параметры по умолчанию
    TEST_MODE=false
    CATEGORY=""
    MAX_RESOURCES=""
    SKIP_INSTALL=false
    DRY_RUN=false
    CUSTOM_OUTPUT=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -t|--test)
                TEST_MODE=true
                shift
                ;;
            -c|--category)
                CATEGORY="$2"
                shift 2
                ;;
            -o|--output)
                CUSTOM_OUTPUT="$2"
                shift 2
                ;;
            -n|--max-resources)
                MAX_RESOURCES="$2"
                shift 2
                ;;
            --no-install)
                SKIP_INSTALL=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            *)
                log_error "Неизвестная опция: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Переопределяем выходную папку если задана
    if [[ -n "$CUSTOM_OUTPUT" ]]; then
        OUTPUT_DIR="$CUSTOM_OUTPUT"
    fi
    
    # В тестовом режиме ограничиваем количество ресурсов
    if [[ "$TEST_MODE" = true ]] && [[ -z "$MAX_RESOURCES" ]]; then
        MAX_RESOURCES=5
    fi
}

# Построение команды запуска
build_command() {
    PYTHON_CMD="python3 $BOOTSTRAP_FETCHER"
    
    # Добавляем параметры
    if [[ -n "$CUSTOM_OUTPUT" ]]; then
        PYTHON_CMD="$PYTHON_CMD --output $CUSTOM_OUTPUT"
    fi
    
    if [[ -n "$CATEGORY" ]]; then
        PYTHON_CMD="$PYTHON_CMD --category $CATEGORY"
    fi
    
    if [[ -n "$MAX_RESOURCES" ]]; then
        PYTHON_CMD="$PYTHON_CMD --max-resources $MAX_RESOURCES"
    fi
    
    echo "$PYTHON_CMD"
}

# Dry run - показать что будет загружено
dry_run() {
    log_info "🔍 Dry Run Mode - анализируем конфигурацию..."
    
    # Простой анализ YAML файла
    if command -v grep &> /dev/null && command -v wc &> /dev/null; then
        TOTAL_RESOURCES=$(grep -c "^  - name:" "$CONFIG_FILE" || echo "unknown")
        CATEGORIES=$(grep -A 1 "category:" "$CONFIG_FILE" | grep -v "category:" | sort | uniq | wc -l)
        
        log_info "📊 Найдено ресурсов: $TOTAL_RESOURCES"
        log_info "📁 Найдено категорий: $CATEGORIES"
        
        if [[ -n "$CATEGORY" ]]; then
            FILTERED=$(grep -A 2 -B 1 "category: $CATEGORY" "$CONFIG_FILE" | grep -c "name:" || echo "0")
            log_info "🎯 Ресурсов в категории '$CATEGORY': $FILTERED"
        fi
        
        if [[ -n "$MAX_RESOURCES" ]]; then
            log_info "🔢 Будет загружено: максимум $MAX_RESOURCES ресурсов"
        fi
    fi
    
    log_info "📁 Выходная папка: $OUTPUT_DIR"
    log_info "⚙️ Команда запуска: $(build_command)"
    
    log_success "Dry run завершен. Запустите без --dry-run для начала загрузки."
}

# Основная функция загрузки
run_fetcher() {
    log_info "🚀 Запускаем загрузку материалов..."
    
    # Строим команду
    CMD=$(build_command)
    
    # Показываем информацию о запуске
    if [[ "$TEST_MODE" = true ]]; then
        log_warning "🧪 ТЕСТОВЫЙ РЕЖИМ - загружаем только $MAX_RESOURCES ресурсов"
    fi
    
    if [[ -n "$CATEGORY" ]]; then
        log_info "🎯 Категория: $CATEGORY"
    fi
    
    log_info "📁 Выходная папка: $OUTPUT_DIR"
    log_info "⚙️ Команда: $CMD"
    
    # Запускаем
    echo ""
    eval "$CMD"
    EXIT_CODE=$?
    
    # Обрабатываем результат
    if [[ $EXIT_CODE -eq 0 ]]; then
        log_success "✅ Загрузка завершена успешно!"
    elif [[ $EXIT_CODE -eq 1 ]]; then
        log_warning "⚠️ Загрузка завершена с некоторыми ошибками"
    elif [[ $EXIT_CODE -eq 130 ]]; then
        log_warning "⚠️ Загрузка прервана пользователем"
    else
        log_error "❌ Загрузка завершена с ошибками (код: $EXIT_CODE)"
    fi
    
    # Показываем содержимое выходной папки
    if [[ -d "$OUTPUT_DIR" ]]; then
        log_info "📁 Содержимое $OUTPUT_DIR:"
        find "$OUTPUT_DIR" -type f -name "*.txt" -o -name "*.pdf" -o -name "*.zip" | head -10 | while read -r file; do
            size=$(du -h "$file" 2>/dev/null | cut -f1 || echo "?")
            echo "  📄 $(basename "$file") ($size)"
        done
        
        if [[ -f "$OUTPUT_DIR/download_stats.json" ]]; then
            log_info "📊 Статистика сохранена в $OUTPUT_DIR/download_stats.json"
        fi
    fi
    
    return $EXIT_CODE
}

# Главная функция
main() {
    echo "🎓 Bootstrap Fetcher - Автоматизированная загрузка обучающих материалов"
    echo "═══════════════════════════════════════════════════════════════════════════"
    
    # Разбираем аргументы
    parse_args "$@"
    
    # Dry run режим
    if [[ "$DRY_RUN" = true ]]; then
        check_files
        dry_run
        exit 0
    fi
    
    # Основной процесс
    check_files
    
    if [[ "$SKIP_INSTALL" = false ]]; then
        check_dependencies
        install_python_deps
    else
        log_info "⏭️ Пропускаем установку зависимостей"
    fi
    
    run_fetcher
    exit $?
}

# Запуск если скрипт вызван напрямую
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 