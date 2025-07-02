# AI Assistant - Complete Development & Deployment Makefile
# Команды для разработки, тестирования и развертывания

.PHONY: help install dev test deploy clean

# Переменные
PYTHON = python3
PIP = pip3
VENV = venv
DOCKER_COMPOSE = docker-compose
KUBECTL = kubectl
HELM = helm
PYTEST = pytest
PYTEST_ARGS = -v --tb=short

# Цвета для вывода
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
PURPLE = \033[0;35m
CYAN = \033[0;36m
NC = \033[0m # No Color

##@ 📋 Справка
help: ## Показать справку по командам
	@echo "$(GREEN)🤖 AI Assistant - Команды разработки и развертывания$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(CYAN)🌐 После запуска доступны:$(NC)"
	@echo "  • API Docs:      http://localhost:8000/docs"
	@echo "  • Health:        http://localhost:8000/health"
	@echo "  • Frontend:      http://localhost:3000"
	@echo "  • Adminer:       http://localhost:8080"
	@echo "  • Redis UI:      http://localhost:8081"
	@echo "  • Qdrant UI:     http://localhost:6333/dashboard"
	@echo "  • MailHog:       http://localhost:8025"
	@echo "  • Grafana:       http://localhost:3001"
	@echo "  • Prometheus:    http://localhost:9090"

##@ 🚀 Быстрый старт
quick-start: ## Быстрый старт для разработки (инфраструктура + локальное приложение)
	@echo "$(GREEN)🚀 Быстрый старт AI Assistant...$(NC)"
	$(MAKE) install
	$(MAKE) dev-infra-up
	@echo "$(CYAN)💡 Теперь запустите приложение: make dev$(NC)"

setup-dev: install dev-infra-up migrate load-test-data ## Полная настройка окружения разработки
	@echo "$(GREEN)✅ Окружение разработки готово!$(NC)"
	@echo "$(CYAN)Запустите приложение: make dev$(NC)"

##@ 🛠 Установка и настройка
install: ## Установка зависимостей Python
	@echo "$(BLUE)📦 Установка зависимостей...$(NC)"
	@if [ ! -d "$(VENV)" ]; then python3 -m venv $(VENV); fi
	./$(VENV)/bin/pip install --upgrade pip
	./$(VENV)/bin/pip install -r requirements.txt
	@echo "$(GREEN)✅ Зависимости установлены$(NC)"

install-dev: install ## Установка dev зависимостей
	@echo "$(BLUE)🔧 Установка dev зависимостей...$(NC)"
	./$(VENV)/bin/pip install -r config/environments/requirements-dev.txt || true
	./$(VENV)/bin/pip install black pylint mypy pytest-cov flake8 || true
	@echo "$(GREEN)✅ Dev зависимости установлены$(NC)"

##@ 🐳 Инфраструктура разработки
dev-infra-up: ## Запустить инфраструктуру (БД, Redis, Qdrant)
	@echo "$(GREEN)🔧 Запуск инфраструктуры для разработки...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres redis qdrant
	@echo "$(GREEN)✅ Инфраструктура запущена!$(NC)"
	@echo "$(CYAN)📊 Статус: make dev-infra-status$(NC)"
	@echo "$(CYAN)🔌 Подключения:$(NC)"
	@echo "  • PostgreSQL: localhost:5432 (ai_user/ai_password_dev)"
	@echo "  • Redis:      localhost:6379"
	@echo "  • Qdrant:     localhost:6333"

dev-infra-up-full: ## Запустить инфраструктуру + админ панели + LLM
	@echo "$(GREEN)🔧 Запуск полной инфраструктуры...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml --profile admin --profile llm up -d
	@echo "$(GREEN)✅ Полная инфраструктура запущена!$(NC)"
	@echo "$(CYAN)🌐 Дополнительные сервисы:$(NC)"
	@echo "  • Adminer:    http://localhost:8080"
	@echo "  • Redis UI:   http://localhost:8081"
	@echo "  • Ollama:     http://localhost:11434"

dev-infra-up-monitoring: ## Запустить инфраструктуру + мониторинг
	@echo "$(GREEN)📊 Запуск инфраструктуры с мониторингом...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml --profile monitoring up -d
	@echo "$(GREEN)✅ Инфраструктура с мониторингом запущена!$(NC)"
	@echo "$(CYAN)📈 Мониторинг:$(NC)"
	@echo "  • Grafana:    http://localhost:3001 (admin/admin123)"
	@echo "  • Prometheus: http://localhost:9090"

dev-infra-down: ## Остановить инфраструктуру
	@echo "$(YELLOW)🛑 Остановка инфраструктуры...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml down
	@echo "$(GREEN)✅ Инфраструктура остановлена$(NC)"

dev-infra-status: ## Статус инфраструктуры
	@echo "$(BLUE)📊 Статус инфраструктуры:$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml ps

dev-infra-logs: ## Логи инфраструктуры
	@echo "$(GREEN)📋 Логи инфраструктуры:$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f

dev-infra-clean: ## Очистить данные инфраструктуры
	@echo "$(RED)🧹 ВНИМАНИЕ: Удаление всех данных инфраструктуры!$(NC)"
	@read -p "Вы уверены? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		$(DOCKER_COMPOSE) -f docker-compose.dev.yml down -v; \
		docker volume prune -f; \
		echo "$(GREEN)✅ Данные очищены$(NC)"; \
	else \
		echo ""; \
		echo "$(YELLOW)Отменено$(NC)"; \
	fi

##@ 🏃 Локальная разработка
dev: ## Запуск приложения в режиме разработки
	@echo "$(GREEN)🏃 Запуск приложения в режиме разработки...$(NC)"
	@echo "$(YELLOW)💡 Убедитесь что инфраструктура запущена: make dev-infra-up$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export ENVIRONMENT=development && \
	 export DATABASE_URL=postgresql://ai_user:ai_password_dev@localhost:5432/ai_assistant && \
	 export REDIS_URL=redis://localhost:6379/0 && \
	 export QDRANT_URL=http://localhost:6333 && \
	 export DEBUG=true && \
	 export LOG_LEVEL=DEBUG && \
	 export SECRET_KEY=dev-secret-key-not-for-production && \
	 ./$(VENV)/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-debug: ## Запуск с подробной отладкой
	@echo "$(YELLOW)🐛 Запуск в режиме отладки...$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export ENVIRONMENT=development && \
	 export DATABASE_URL=postgresql://ai_user:ai_password_dev@localhost:5432/ai_assistant && \
	 export REDIS_URL=redis://localhost:6379/0 && \
	 export QDRANT_URL=http://localhost:6333 && \
	 export DEBUG=true && \
	 export LOG_LEVEL=DEBUG && \
	 export SECRET_KEY=dev-secret-key-not-for-production && \
	 ./$(VENV)/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

##@ 🐳 Docker Окружения
# Переменные для Docker Compose файлов
DOCKER_PATH = deployment/docker
COMPOSE_DEV = -f docker-compose.dev.yml
COMPOSE_TEST = -f docker-compose.tests.yml
COMPOSE_FULL = -f docker-compose.full.yml
COMPOSE_PROD = -f docker-compose.prod.yml
COMPOSE_LOAD = -f docker-compose.load-test.yml

up-dev: ## 🔧 Запустить окружение для разработки (только инфраструктура)
	@echo "$(GREEN)🔧 Запуск окружения для разработки...$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_DEV) up -d postgres redis qdrant
	@echo "$(GREEN)✅ Development infrastructure started!$(NC)"
	@echo "$(CYAN)🗄️  PostgreSQL: localhost:5432 (ai_user/ai_password_dev)$(NC)"
	@echo "$(CYAN)🔍 Qdrant:     http://localhost:6333$(NC)"
	@echo "$(CYAN)📨 Redis:      localhost:6379$(NC)"
	@echo "$(CYAN)💡 Run app:    make dev$(NC)"

up-dev-full: ## 🚀 Запустить полное окружение разработки (+ админ панели)
	@echo "$(GREEN)🚀 Запуск полного окружения разработки...$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_DEV) --profile admin up -d
	@echo "$(GREEN)✅ Full development environment started!$(NC)"
	@echo "$(CYAN)📖 App:        http://localhost:8000$(NC)"
	@echo "$(CYAN)🗄️  PostgreSQL: localhost:5432$(NC)"
	@echo "$(CYAN)🔍 Qdrant:     http://localhost:6333$(NC)"
	@echo "$(CYAN)📨 Redis:      localhost:6379$(NC)"
	@echo "$(CYAN)🔧 Adminer:    http://localhost:8080$(NC)"
	@echo "$(CYAN)📊 Redis UI:   http://localhost:8081$(NC)"

up-dev-with-llm: ## 🤖 Запустить разработку + LLM (Ollama)
	@echo "$(GREEN)🤖 Запуск разработки с LLM...$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_DEV) --profile admin --profile llm up -d
	@echo "$(GREEN)✅ Development with LLM started!$(NC)"
	@echo "$(CYAN)🤖 Ollama:     http://localhost:11434$(NC)"

up-dev-monitoring: ## 📊 Запустить разработку с мониторингом
	@echo "$(GREEN)📊 Запуск разработки с мониторингом...$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_DEV) --profile monitoring up -d
	@echo "$(GREEN)✅ Development with monitoring started!$(NC)"
	@echo "$(CYAN)📊 Grafana:    http://localhost:3001 (admin/admin123)$(NC)"
	@echo "$(CYAN)📈 Prometheus: http://localhost:9090$(NC)"

##@ 🧪 Тестовые окружения
up-test: ## 🧪 Запустить базовое тестовое окружение (unit/integration)
	@echo "$(GREEN)🧪 Запуск базового тестового окружения...$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_TEST) up -d test-postgres test-redis test-qdrant test-app
	@echo "$(GREEN)✅ Test environment started!$(NC)"
	@echo "$(CYAN)🧪 Test App:   http://localhost:8001$(NC)"
	@echo "$(CYAN)🗄️  Test DB:    localhost:5433$(NC)"
	@echo "$(CYAN)🔍 Test Qdrant: http://localhost:6335$(NC)"
	@echo "$(CYAN)📨 Test Redis:  localhost:6380$(NC)"

up-test-e2e: ## 🎯 Запустить полное E2E тестовое окружение (+ Jira, Confluence, GitLab)
	@echo "$(GREEN)🎯 Запуск E2E тестового окружения (это займет 10-15 минут)...$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_TEST) --profile e2e up -d
	@echo "$(GREEN)✅ E2E environment started!$(NC)"
	@echo "$(YELLOW)⏳ Ожидание инициализации сервисов (5-10 минут)...$(NC)"
	@echo "$(CYAN)🧪 Test App:    http://localhost:8001$(NC)"
	@echo "$(CYAN)📋 Jira:       http://localhost:8082$(NC)"
	@echo "$(CYAN)📝 Confluence: http://localhost:8083$(NC)"
	@echo "$(CYAN)🦊 GitLab:     http://localhost:8084$(NC)"
	@echo "$(CYAN)🔍 Elastic:    http://localhost:9201$(NC)"
	@echo "$(CYAN)💾 ClickHouse: http://localhost:8125$(NC)"
	@echo "$(CYAN)📊 YDB:        http://localhost:8766$(NC)"

up-test-load: ## ⚡ Запустить окружение для нагрузочных тестов
	@echo "$(GREEN)⚡ Запуск окружения для нагрузочных тестов...$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_LOAD) up -d
	@echo "$(GREEN)✅ Load test environment started!$(NC)"

##@ 🛑 Остановка окружений
down-dev: ## 🛑 Остановить окружение разработки
	@echo "$(YELLOW)🛑 Остановка окружения разработки...$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_DEV) down

down-test: ## 🛑 Остановить тестовое окружение
	@echo "$(YELLOW)🛑 Остановка тестового окружения...$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_TEST) down

down-test-e2e: ## 🛑 Остановить E2E тестовое окружение
	@echo "$(YELLOW)🛑 Остановка E2E тестового окружения...$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_TEST) --profile e2e down

down-all: ## 🛑 Остановить все окружения
	@echo "$(RED)🛑 Остановка всех Docker окружений...$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_DEV) down || true
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_TEST) down || true
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_FULL) down || true
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_PROD) down || true
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_LOAD) down || true
	@echo "$(GREEN)✅ All environments stopped$(NC)"

##@ 📊 Статус и мониторинг
status-dev: ## 📊 Статус окружения разработки
	@echo "$(BLUE)📊 Статус окружения разработки:$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_DEV) ps

status-test: ## 📊 Статус тестового окружения
	@echo "$(BLUE)📊 Статус тестового окружения:$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_TEST) ps

status-all: ## 📊 Статус всех окружений
	@echo "$(BLUE)📊 Статус всех окружений:$(NC)"
	@echo "$(GREEN)Development:$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_DEV) ps 2>/dev/null || echo "  Not running"
	@echo "$(GREEN)Testing:$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_TEST) ps 2>/dev/null || echo "  Not running"

logs-dev: ## 📋 Логи окружения разработки
	@echo "$(GREEN)📋 Логи окружения разработки:$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_DEV) logs -f

logs-test: ## 📋 Логи тестового окружения
	@echo "$(GREEN)📋 Логи тестового окружения:$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_TEST) logs -f

##@ 🧪 Тестирование (с Docker)
test-with-docker: up-test ## 🧪 Запуск всех тестов с Docker окружением
	@echo "$(BLUE)🧪 Запуск тестов с Docker окружением...$(NC)"
	@sleep 30  # Ожидание готовности сервисов
	@export PYTHONPATH=$$PWD && \
	 export DATABASE_URL=postgresql://test_user:test_password@localhost:5433/ai_test && \
	 export REDIS_URL=redis://localhost:6380/0 && \
	 export QDRANT_URL=http://localhost:6335 && \
	 export TESTING=true && \
	 $(PYTEST) $(PYTEST_ARGS) tests/unit/ tests/integration/
	@$(MAKE) down-test

test-unit-docker: up-test ## 🔬 Unit тесты с Docker
	@echo "$(BLUE)🔬 Запуск unit тестов с Docker...$(NC)"
	@sleep 20
	@export PYTHONPATH=$$PWD && \
	 export DATABASE_URL=postgresql://test_user:test_password@localhost:5433/ai_test && \
	 export REDIS_URL=redis://localhost:6380/0 && \
	 export QDRANT_URL=http://localhost:6335 && \
	 export TESTING=true && \
	 $(PYTEST) $(PYTEST_ARGS) tests/unit/ -m "not slow"
	@$(MAKE) down-test

test-integration-docker: up-test ## 🔗 Integration тесты с Docker
	@echo "$(BLUE)🔗 Запуск integration тестов с Docker...$(NC)"
	@sleep 30
	@export PYTHONPATH=$$PWD && \
	 export DATABASE_URL=postgresql://test_user:test_password@localhost:5433/ai_test && \
	 export REDIS_URL=redis://localhost:6380/0 && \
	 export QDRANT_URL=http://localhost:6335 && \
	 export TESTING=true && \
	 $(PYTEST) $(PYTEST_ARGS) tests/integration/ --timeout=300
	@$(MAKE) down-test

test-e2e-docker: up-test-e2e load-test-data-e2e ## 🎭 E2E тесты с полным Docker окружением
	@echo "$(BLUE)🎭 Запуск E2E тестов с полным окружением...$(NC)"
	@echo "$(YELLOW)⏳ Ожидание готовности всех сервисов (3-5 минут)...$(NC)"
	@sleep 180
	@export PYTHONPATH=$$PWD && \
	 export DATABASE_URL=postgresql://test_user:test_password@localhost:5433/ai_test && \
	 export REDIS_URL=redis://localhost:6380/0 && \
	 export QDRANT_URL=http://localhost:6335 && \
	 export JIRA_URL=http://localhost:8082 && \
	 export CONFLUENCE_URL=http://localhost:8083 && \
	 export GITLAB_URL=http://localhost:8084 && \
	 export TESTING=true && \
	 $(PYTEST) $(PYTEST_ARGS) tests/e2e/ --timeout=600
	@$(MAKE) down-test-e2e

test-load-docker: up-test-load ## ⚡ Нагрузочные тесты с Docker
	@echo "$(BLUE)⚡ Запуск нагрузочных тестов...$(NC)"
	@sleep 30
	@export PYTHONPATH=$$PWD && ./$(VENV)/bin/python tests/performance/test_core_functionality_load.py
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_LOAD) down

##@ 📦 Управление данными
load-test-data-basic: ## 📊 Загрузить базовые тестовые данные
	@echo "$(GREEN)📊 Загрузка базовых тестовых данных...$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_TEST) run --rm test-data-loader

load-test-data-e2e: ## 📊 Загрузить данные для E2E тестов
	@echo "$(GREEN)📊 Загрузка данных для E2E тестов...$(NC)"
	cd $(DOCKER_PATH) && LOAD_E2E_DATA=true $(DOCKER_COMPOSE) $(COMPOSE_TEST) --profile e2e run --rm test-data-loader

clean-test-data: ## 🧹 Очистить тестовые данные
	@echo "$(YELLOW)🧹 Очистка тестовых данных...$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_TEST) down -v

##@ 🔨 Сборка и развертывание
build-dev: ## 🔨 Собрать образы для разработки
	@echo "$(BLUE)🔨 Сборка образов для разработки...$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_DEV) build

build-test: ## 🔨 Собрать образы для тестов
	@echo "$(BLUE)🔨 Сборка образов для тестов...$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_TEST) build

build-all: ## 🔨 Собрать все образы
	@echo "$(BLUE)🔨 Сборка всех образов...$(NC)"
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_DEV) build
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_TEST) build
	cd $(DOCKER_PATH) && $(DOCKER_COMPOSE) $(COMPOSE_FULL) build

##@ 🎯 Быстрые команды для разработчиков
quick-test: ## ⚡ Быстрое тестирование (только unit, без Docker)
	@echo "$(BLUE)⚡ Быстрое unit тестирование...$(NC)"
	@export PYTHONPATH=$$PWD && $(PYTEST) $(PYTEST_ARGS) tests/unit/ -x --tb=short -q

quick-test-file: ## ⚡ Быстрое тестирование файла (make quick-test-file FILE=tests/unit/test_file.py)
	@if [ -z "$(FILE)" ]; then echo "$(RED)Укажите файл: make quick-test-file FILE=tests/unit/test_file.py$(NC)"; exit 1; fi
	@echo "$(BLUE)⚡ Тестирование файла $(FILE)...$(NC)"
	@export PYTHONPATH=$$PWD && $(PYTEST) $(PYTEST_ARGS) $(FILE) -v

dev-reset: down-dev up-dev ## 🔄 Быстрый перезапуск окружения разработки

test-reset: down-test up-test ## 🔄 Быстрый перезапуск тестового окружения

##@ 📚 Документация и справка
docs-docker: ## 📚 Показать документацию по Docker окружениям
	@echo "$(GREEN)📚 AI Assistant - Docker Environments Documentation$(NC)"
	@echo ""
	@echo "$(CYAN)🔧 Development Environments:$(NC)"
	@echo "  make up-dev          - Только инфраструктура (БД, Redis, Qdrant)"
	@echo "  make up-dev-full     - + админ панели (Adminer, Redis UI)"
	@echo "  make up-dev-with-llm - + локальный LLM (Ollama)"
	@echo "  make up-dev-monitoring - + мониторинг (Grafana, Prometheus)"
	@echo ""
	@echo "$(CYAN)🧪 Test Environments:$(NC)"
	@echo "  make up-test         - Базовое тестовое окружение"
	@echo "  make up-test-e2e     - Полное E2E окружение (+ Jira, Confluence, GitLab)"
	@echo "  make up-test-load    - Нагрузочное тестирование"
	@echo ""
	@echo "$(CYAN)🧪 Test Commands:$(NC)"
	@echo "  make test-with-docker      - Все тесты с Docker"
	@echo "  make test-unit-docker      - Unit тесты с Docker"  
	@echo "  make test-integration-docker - Integration тесты с Docker"
	@echo "  make test-e2e-docker       - E2E тесты с полным окружением"
	@echo "  make test-load-docker      - Нагрузочные тесты"
	@echo ""
	@echo "$(CYAN)⚡ Quick Commands:$(NC)"
	@echo "  make quick-test           - Быстрые unit тесты (без Docker)"
	@echo "  make quick-test-file FILE=path - Тест конкретного файла"
	@echo "  make dev-reset           - Перезапуск разработки"
	@echo "  make test-reset          - Перезапуск тестов"

help-docker: docs-docker ## Алиас для docs-docker

# Значение по умолчанию
.DEFAULT_GOAL := help

# Алиасы для совместимости
docker-up: system-up
docker-down: system-down
docker-logs: system-logs
docker-status: system-status

# Дополнительные команды
load-test-data: ## Загрузить тестовые данные
	@echo "📊 Loading test data..."
	python tools/scripts/create_data.py

backup-db: ## Создать бэкап базы данных
	@echo "💾 Creating database backup..."
	pg_dump ai_assistant > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Значение по умолчанию
.DEFAULT_GOAL := help 