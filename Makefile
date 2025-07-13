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
	@echo "$(CYAN)🚀 Основные команды для полной системы:$(NC)"
	@echo "  • make full-system   - Поднять всю систему (backend + frontend + LLM + мониторинг)"
	@echo "  • make full-dev      - Полная разработка + мониторинг"
	@echo "  • make backend       - Только backend"
	@echo "  • make frontend      - Только frontend"
	@echo "  • make llm           - Только LLM сервисы"
	@echo "  • make monitoring    - Только мониторинг"
	@echo "  • make status-system - Статус всей системы"
	@echo "  • make stop-system   - Остановить всю систему"
	@echo ""
	@echo "$(CYAN)🌐 После запуска доступны:$(NC)"
	@echo "  • Backend API:   http://localhost:8000"
	@echo "  • Frontend:      http://localhost:3000"
	@echo "  • API Docs:      http://localhost:8000/docs"
	@echo "  • Health:        http://localhost:8000/health"
	@echo "  • Adminer:       http://localhost:8080"
	@echo "  • Redis UI:      http://localhost:8081"
	@echo "  • Ollama LLM:    http://localhost:11434"
	@echo "  • Qdrant UI:     http://localhost:6333/dashboard"
	@echo "  • Grafana:       http://localhost:3001 (admin/admin123)"
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

##@ 🌐 Полная система
full-system: ## 🚀 Поднять всю систему (backend + frontend + LLM + мониторинг + инфраструктура)
	@echo "$(GREEN)🚀 Запуск полной системы AI Assistant...$(NC)"
	@echo "$(CYAN)📦 Шаг 1: Установка системных зависимостей...$(NC)"
	$(MAKE) install-system
	@echo "$(CYAN)🏗️ Шаг 2: Запуск инфраструктуры...$(NC)"
	$(MAKE) dev-infra-up-full
	@echo "$(CYAN)📊 Шаг 3: Запуск мониторинга...$(NC)"
	$(MAKE) dev-infra-up-monitoring
	@echo "$(CYAN)⏳ Ожидание готовности инфраструктуры (45 секунд)...$(NC)"
	@sleep 45
	@echo "$(CYAN)🎯 Шаг 4: Запуск backend...$(NC)"
	$(MAKE) backend > logs/backend.log 2>&1 &
	@echo "$(CYAN)🎨 Шаг 5: Запуск frontend...$(NC)"
	$(MAKE) frontend > logs/frontend.log 2>&1 &
	@echo "$(GREEN)✅ Полная система запущена!$(NC)"
	@echo "$(CYAN)🌐 Доступные сервисы:$(NC)"
	@echo "  • Backend API:  http://localhost:8000"
	@echo "  • Frontend:     http://localhost:3000"
	@echo "  • API Docs:     http://localhost:8000/docs"
	@echo "  • Health:       http://localhost:8000/health"
	@echo "  • Adminer:      http://localhost:8080"
	@echo "  • Redis UI:     http://localhost:8081"
	@echo "  • Ollama LLM:   http://localhost:11434"
	@echo "  • Grafana:      http://localhost:3001 (admin/admin123)"
	@echo "  • Prometheus:   http://localhost:9090"
	@echo "$(YELLOW)📋 Логи: make logs-system$(NC)"

full-dev: ## 🔧 Полная разработка (backend + frontend + LLM + мониторинг)
	@echo "$(GREEN)🔧 Запуск полной разработки...$(NC)"
	@echo "$(CYAN)📦 Шаг 1: Установка dev зависимостей...$(NC)"
	$(MAKE) install-dev
	@echo "$(CYAN)🏗️ Шаг 2: Запуск инфраструктуры + мониторинг...$(NC)"
	$(MAKE) dev-infra-up-full
	$(MAKE) dev-infra-up-monitoring
	@echo "$(CYAN)⏳ Ожидание готовности инфраструктуры (45 секунд)...$(NC)"
	@sleep 45
	@echo "$(CYAN)🎯 Шаг 3: Запуск backend в режиме разработки...$(NC)"
	$(MAKE) backend-dev > logs/backend-dev.log 2>&1 &
	@echo "$(CYAN)🎨 Шаг 4: Запуск frontend в режиме разработки...$(NC)"
	$(MAKE) frontend-dev > logs/frontend-dev.log 2>&1 &
	@echo "$(GREEN)✅ Полная разработка запущена!$(NC)"
	@echo "$(CYAN)🌐 Все сервисы:$(NC)"
	@echo "  • Backend API:  http://localhost:8000"
	@echo "  • Frontend:     http://localhost:3000"
	@echo "  • API Docs:     http://localhost:8000/docs"
	@echo "  • Adminer:      http://localhost:8080"
	@echo "  • Redis UI:     http://localhost:8081"
	@echo "  • Ollama LLM:   http://localhost:11434"
	@echo "  • Grafana:      http://localhost:3001 (admin/admin123)"
	@echo "  • Prometheus:   http://localhost:9090"
	@echo "$(YELLOW)📋 Логи: make logs-system$(NC)"

system: full-system ## Алиас для full-system

##@ 🎯 Компоненты системы
backend: ## 🎯 Запуск только backend
	@echo "$(BLUE)🎯 Запуск backend...$(NC)"
	@echo "$(YELLOW)💡 Убедитесь что инфраструктура запущена: make dev-infra-up$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export ENVIRONMENT=production && \
	 export DATABASE_URL=postgresql://ai_user:ai_password_dev@localhost:5432/ai_assistant && \
	 export REDIS_URL=redis://localhost:6379/0 && \
	 export QDRANT_URL=http://localhost:6333 && \
	 export DEBUG=false && \
	 export LOG_LEVEL=INFO && \
	 export SECRET_KEY=prod-secret-key && \
	 ./$(VENV)/bin/python main.py --port 8000 --host localhost

backend-dev: ## 🎯 Запуск backend в режиме разработки
	@echo "$(BLUE)🎯 Запуск backend в режиме разработки...$(NC)"
	@echo "$(YELLOW)💡 Убедитесь что инфраструктура запущена: make dev-infra-up$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export ENVIRONMENT=development && \
	 export DATABASE_URL=postgresql://ai_user:ai_password_dev@localhost:5432/ai_assistant && \
	 export REDIS_URL=redis://localhost:6379/0 && \
	 export QDRANT_URL=http://localhost:6333 && \
	 export DEBUG=true && \
	 export LOG_LEVEL=DEBUG && \
	 export SECRET_KEY=dev-secret-key-not-for-production && \
	 ./$(VENV)/bin/python main.py --port 8000 --host localhost

frontend: ## 🎨 Запуск только frontend (production)
	@echo "$(CYAN)🎨 Запуск frontend...$(NC)"
	@if [ ! -d "frontend/node_modules" ]; then \
		echo "$(YELLOW)📦 Установка зависимостей frontend...$(NC)"; \
		cd frontend && npm install; \
	fi
	@echo "$(CYAN)🏗️ Сборка frontend...$(NC)"
	@cd frontend && npm run build
	@echo "$(CYAN)🚀 Запуск frontend сервера...$(NC)"
	@cd frontend && npm run preview -- --port 3000

frontend-dev: ## 🎨 Запуск frontend в режиме разработки
	@echo "$(CYAN)🎨 Запуск frontend в режиме разработки...$(NC)"
	@if [ ! -d "frontend/node_modules" ]; then \
		echo "$(YELLOW)📦 Установка зависимостей frontend...$(NC)"; \
		cd frontend && npm install; \
	fi
	@echo "$(CYAN)🚀 Запуск dev сервера frontend...$(NC)"
	@cd frontend && npm run dev -- --port 3000

llm: ## 🤖 Запуск только LLM сервисов
	@echo "$(PURPLE)🤖 Запуск LLM сервисов...$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.dev.yml --profile llm up -d
	@echo "$(GREEN)✅ LLM сервисы запущены!$(NC)"
	@echo "$(CYAN)🤖 Доступные LLM сервисы:$(NC)"
	@echo "  • Ollama:     http://localhost:11434"
	@echo "  • Ollama API: http://localhost:11434/api/generate"

monitoring: ## 📊 Запуск только мониторинга
	@echo "$(YELLOW)📊 Запуск мониторинга...$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.dev.yml --profile monitoring up -d
	@echo "$(GREEN)✅ Мониторинг запущен!$(NC)"
	@echo "$(CYAN)📈 Доступные сервисы мониторинга:$(NC)"
	@echo "  • Grafana:    http://localhost:3001 (admin/admin123)"
	@echo "  • Prometheus: http://localhost:9090"

##@ 🛑 Остановка компонентов
stop-system: ## 🛑 Остановить всю систему
	@echo "$(YELLOW)🛑 Остановка всей системы...$(NC)"
	@pkill -f "python.*main.py" || true
	@pkill -f "npm.*run.*dev" || true
	@pkill -f "npm.*run.*preview" || true
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.dev.yml down
	@echo "$(GREEN)✅ Вся система остановлена$(NC)"

stop-backend: ## 🛑 Остановить backend
	@echo "$(YELLOW)🛑 Остановка backend...$(NC)"
	@pkill -f "python.*main.py" || true
	@echo "$(GREEN)✅ Backend остановлен$(NC)"

stop-frontend: ## 🛑 Остановить frontend
	@echo "$(YELLOW)🛑 Остановка frontend...$(NC)"
	@pkill -f "npm.*run.*dev" || true
	@pkill -f "npm.*run.*preview" || true
	@echo "$(GREEN)✅ Frontend остановлен$(NC)"

stop-llm: ## 🛑 Остановить LLM сервисы
	@echo "$(YELLOW)🛑 Остановка LLM сервисов...$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.dev.yml --profile llm stop
	@echo "$(GREEN)✅ LLM сервисы остановлены$(NC)"

stop-monitoring: ## 🛑 Остановить мониторинг
	@echo "$(YELLOW)🛑 Остановка мониторинга...$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.dev.yml --profile monitoring stop
	@echo "$(GREEN)✅ Мониторинг остановлен$(NC)"

##@ 📋 Логи системы
logs-system: ## 📋 Логи всей системы
	@echo "$(GREEN)📋 Логи всей системы:$(NC)"
	@echo "$(CYAN)🎯 Backend логи:$(NC)"
	@tail -20 logs/backend.log 2>/dev/null || echo "Backend не запущен"
	@echo ""
	@echo "$(CYAN)🎨 Frontend логи:$(NC)"
	@tail -20 logs/frontend.log 2>/dev/null || echo "Frontend не запущен"
	@echo ""
	@echo "$(CYAN)🐳 Инфраструктура логи:$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.dev.yml logs --tail=10

logs-backend: ## 📋 Логи backend
	@echo "$(GREEN)📋 Логи backend:$(NC)"
	@tail -f logs/backend.log 2>/dev/null || echo "Backend логи не найдены"

logs-frontend: ## 📋 Логи frontend
	@echo "$(GREEN)📋 Логи frontend:$(NC)"
	@tail -f logs/frontend.log 2>/dev/null || echo "Frontend логи не найдены"

logs-llm: ## 📋 Логи LLM сервисов
	@echo "$(GREEN)📋 Логи LLM сервисов:$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.dev.yml --profile llm logs -f

logs-monitoring: ## 📋 Логи мониторинга
	@echo "$(GREEN)📋 Логи мониторинга:$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.dev.yml --profile monitoring logs -f

##@ 🔍 Статус системы
status-system: ## 📊 Статус всей системы
	@echo "$(BLUE)📊 Статус всей системы:$(NC)"
	@echo "$(CYAN)🎯 Backend:$(NC)"
	@if pgrep -f "python.*main.py" > /dev/null; then \
		echo "  ✅ Backend запущен (PID: $$(pgrep -f 'python.*main.py'))"; \
	else \
		echo "  ❌ Backend не запущен"; \
	fi
	@echo "$(CYAN)🎨 Frontend:$(NC)"
	@if pgrep -f "npm.*run" > /dev/null; then \
		echo "  ✅ Frontend запущен (PID: $$(pgrep -f 'npm.*run'))"; \
	else \
		echo "  ❌ Frontend не запущен"; \
	fi
	@echo "$(CYAN)🐳 Инфраструктура:$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.dev.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" | grep -v "^NAME" | head -10

health-system: ## 🩺 Проверка здоровья системы
	@echo "$(BLUE)🩺 Проверка здоровья системы:$(NC)"
	@echo "$(CYAN)🎯 Backend Health:$(NC)"
	@curl -s http://localhost:8000/health > /dev/null 2>&1 && echo "  ✅ Backend: Healthy" || echo "  ❌ Backend: Unhealthy"
	@echo "$(CYAN)🎨 Frontend Health:$(NC)"
	@curl -s http://localhost:3000 > /dev/null 2>&1 && echo "  ✅ Frontend: Healthy" || echo "  ❌ Frontend: Unhealthy"
	@echo "$(CYAN)🤖 LLM Health:$(NC)"
	@curl -s http://localhost:11434/api/version > /dev/null 2>&1 && echo "  ✅ Ollama: Healthy" || echo "  ❌ Ollama: Unhealthy"
	@echo "$(CYAN)📈 Monitoring Health:$(NC)"
	@curl -s http://localhost:3001/api/health > /dev/null 2>&1 && echo "  ✅ Grafana: Healthy" || echo "  ❌ Grafana: Unhealthy"
	@curl -s http://localhost:9090/-/healthy > /dev/null 2>&1 && echo "  ✅ Prometheus: Healthy" || echo "  ❌ Prometheus: Unhealthy"
	@echo "$(CYAN)🗄️ PostgreSQL:$(NC)"
	@docker compose exec -T postgres pg_isready -U ai_user -d ai_assistant > /dev/null 2>&1 && echo "  ✅ PostgreSQL: Ready" || echo "  ❌ PostgreSQL: Not Ready"
	@echo "$(CYAN)🔴 Redis:$(NC)"
	@docker compose exec -T redis redis-cli ping > /dev/null 2>&1 && echo "  ✅ Redis: Ready" || echo "  ❌ Redis: Not Ready"
	@echo "$(CYAN)🎯 Qdrant:$(NC)"
	@docker compose exec -T qdrant curl -s http://localhost:6333/health > /dev/null 2>&1 && echo "  ✅ Qdrant: Ready" || echo "  ❌ Qdrant: Not Ready"

##@ 🛠 Установка и настройка
install: ## Установка зависимостей Python
	@echo "$(BLUE)📦 Установка зависимостей...$(NC)"
	@if [ ! -d "$(VENV)" ]; then python3 -m venv $(VENV); fi
	./$(VENV)/bin/pip install --upgrade pip
	./$(VENV)/bin/pip install -r requirements.txt
	@echo "$(GREEN)✅ Зависимости установлены$(NC)"

install-system: ## Установка системных зависимостей (минимум для запуска)
	@echo "$(BLUE)📦 Установка системных зависимостей...$(NC)"
	@if [ ! -d "$(VENV)" ]; then python3 -m venv $(VENV); fi
	./$(VENV)/bin/pip install --upgrade pip
	./$(VENV)/bin/pip install -r requirements-system.txt
	@echo "$(GREEN)✅ Системные зависимости установлены$(NC)"

install-dev: install ## Установка dev зависимостей
	@echo "$(BLUE)🔧 Установка dev зависимостей...$(NC)"
	./$(VENV)/bin/pip install -r config/environments/requirements-dev.txt || true
	./$(VENV)/bin/pip install black pylint mypy pytest-cov flake8 || true
	@echo "$(GREEN)✅ Dev зависимости установлены$(NC)"

##@ 🐳 Инфраструктура разработки
dev-infra-up: ## Запустить инфраструктуру (БД, Redis, Qdrant)
	@echo "$(GREEN)🔧 Запуск инфраструктуры для разработки...$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.dev.yml up -d postgres redis qdrant
	@echo "$(GREEN)✅ Инфраструктура запущена!$(NC)"
	@echo "$(CYAN)📊 Статус: make dev-infra-status$(NC)"
	@echo "$(CYAN)🔌 Подключения:$(NC)"
	@echo "  • PostgreSQL: localhost:5432 (ai_user/ai_password_dev)"
	@echo "  • Redis:      localhost:6379"
	@echo "  • Qdrant:     localhost:6333"

dev-infra-up-full: ## Запустить инфраструктуру + админ панели + LLM
	@echo "$(GREEN)🔧 Запуск полной инфраструктуры...$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.dev.yml --profile admin --profile llm up -d
	@echo "$(GREEN)✅ Полная инфраструктура запущена!$(NC)"
	@echo "$(CYAN)🌐 Дополнительные сервисы:$(NC)"
	@echo "  • Adminer:    http://localhost:8080"
	@echo "  • Redis UI:   http://localhost:8081"
	@echo "  • Ollama:     http://localhost:11434"

dev-infra-up-monitoring: ## Запустить инфраструктуру + мониторинг
	@echo "$(GREEN)📊 Запуск инфраструктуры с мониторингом...$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.dev.yml --profile monitoring up -d
	@echo "$(GREEN)✅ Инфраструктура с мониторингом запущена!$(NC)"
	@echo "$(CYAN)📈 Мониторинг:$(NC)"
	@echo "  • Grafana:    http://localhost:3001 (admin/admin123)"
	@echo "  • Prometheus: http://localhost:9090"

dev-infra-down: ## Остановить инфраструктуру
	@echo "$(YELLOW)🛑 Остановка инфраструктуры...$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.dev.yml down
	@echo "$(GREEN)✅ Инфраструктура остановлена$(NC)"

dev-infra-status: ## Статус инфраструктуры
	@echo "$(BLUE)📊 Статус инфраструктуры:$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.dev.yml ps

dev-infra-logs: ## Логи инфраструктуры
	@echo "$(GREEN)📋 Логи инфраструктуры:$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.dev.yml logs -f

dev-infra-clean: ## Очистить данные инфраструктуры
	@echo "$(RED)🧹 ВНИМАНИЕ: Удаление всех данных инфраструктуры!$(NC)"
	@read -p "Вы уверены? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.dev.yml down -v; \
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

##@ 🐳 Docker Окружения (Unified)
# Unified Docker Compose with Profiles

# Core services (default)
up: ## 🚀 Запустить основные сервисы (app, postgres, redis, qdrant)
	@echo "$(GREEN)🚀 Запуск основных сервисов...$(NC)"
	docker compose up -d
	@echo "$(GREEN)✅ Основные сервисы запущены!$(NC)"
	@echo "$(CYAN)🌐 Доступные сервисы:$(NC)"
	@echo "  • App:        http://localhost:8000"
	@echo "  • Docs:       http://localhost:8000/docs"
	@echo "  • Health:     http://localhost:8000/health"

# Development with admin tools
up-dev: ## 🔧 Запустить разработку с админ панелями
	@echo "$(GREEN)🔧 Запуск окружения разработки...$(NC)"
	COMPOSE_PROFILES=admin docker compose up -d
	@echo "$(GREEN)✅ Окружение разработки запущено!$(NC)"
	@echo "$(CYAN)🔧 Админ панели:$(NC)"
	@echo "  • Adminer:    http://localhost:8080"
	@echo "  • Redis UI:   http://localhost:8081"

# Full development with all tools
up-dev-full: ## 🚀 Полное окружение разработки (frontend, admin, monitoring)
	@echo "$(GREEN)🚀 Запуск полного окружения разработки...$(NC)"
	COMPOSE_PROFILES=frontend,admin,monitoring docker compose up -d
	@echo "$(GREEN)✅ Полное окружение запущено!$(NC)"
	@echo "$(CYAN)🌐 Все сервисы:$(NC)"
	@echo "  • App:        http://localhost:8000"
	@echo "  • Frontend:   http://localhost:3000"
	@echo "  • Adminer:    http://localhost:8080"
	@echo "  • Redis UI:   http://localhost:8081"
	@echo "  • Grafana:    http://localhost:3001 (admin/admin123)"
	@echo "  • Prometheus: http://localhost:9090"

# Development with LLM
up-dev-llm: ## 🤖 Запустить разработку с LLM сервисами
	@echo "$(GREEN)🤖 Запуск разработки с LLM...$(NC)"
	COMPOSE_PROFILES=admin,llm docker compose up -d
	@echo "$(GREEN)✅ Разработка с LLM запущена!$(NC)"
	@echo "$(CYAN)🤖 LLM сервисы:$(NC)"
	@echo "  • Ollama:     http://localhost:11434"

# E2E Testing Environment
up-e2e: ## 🎯 Запустить E2E тестовое окружение
	@echo "$(GREEN)🎯 Запуск E2E тестового окружения...$(NC)"
	@echo "$(YELLOW)⏳ Это займет 5-10 минут для инициализации всех сервисов...$(NC)"
	COMPOSE_PROFILES=e2e docker compose up -d
	@echo "$(GREEN)✅ E2E окружение запущено!$(NC)"
	@echo "$(CYAN)🧪 E2E сервисы:$(NC)"
	@echo "  • E2E App:    http://localhost:8001"
	@echo "  • E2E DB:     localhost:5433"
	@echo "  • Jira:       http://localhost:8082"
	@echo "  • Confluence: http://localhost:8083"
	@echo "  • GitLab:     http://localhost:8084"

# Load Testing Environment
up-load: ## ⚡ Запустить окружение для нагрузочных тестов
	@echo "$(GREEN)⚡ Запуск окружения для нагрузочных тестов...$(NC)"
	COMPOSE_PROFILES=load docker compose up -d
	@echo "$(GREEN)✅ Load test окружение запущено!$(NC)"
	@echo "$(CYAN)⚡ Load test сервисы:$(NC)"
	@echo "  • Load App:   http://localhost:8002"
	@echo "  • Load DB:    localhost:5434"
	@echo "  • Nginx LB:   http://localhost:8085"
	@echo "  • Locust UI:  http://localhost:8089"

# Bootstrap ETL Process
bootstrap: ## 🎓 Запустить Bootstrap ETL процесс
	@echo "$(GREEN)🎓 Запуск Bootstrap ETL процесса...$(NC)"
	@echo "$(YELLOW)💡 Убедитесь что основные сервисы запущены: make up$(NC)"
	@docker compose ps postgres | grep -q "Up" || (echo "$(RED)❌ PostgreSQL не запущен! Запустите: make up$(NC)" && exit 1)
	@docker compose ps qdrant | grep -q "Up" || (echo "$(RED)❌ Qdrant не запущен! Запустите: make up$(NC)" && exit 1)
	COMPOSE_PROFILES=bootstrap docker compose up bootstrap
	@echo "$(GREEN)✅ Bootstrap процесс завершен!$(NC)"

##@ 🛑 Остановка сервисов

down: ## 🛑 Остановить все сервисы
	@echo "$(YELLOW)🛑 Остановка всех сервисов...$(NC)"
	docker compose down
	@echo "$(GREEN)✅ Все сервисы остановлены$(NC)"

down-volumes: ## 🗑️ Остановить сервисы и удалить volumes (ОСТОРОЖНО!)
	@echo "$(RED)🗑️ ВНИМАНИЕ: Удаление всех данных!$(NC)"
	@read -p "Вы уверены? Все данные будут потеряны! [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		docker compose down -v; \
		echo "$(GREEN)✅ Все сервисы и данные удалены$(NC)"; \
	else \
		echo ""; \
		echo "$(YELLOW)Отменено$(NC)"; \
	fi

restart: down up ## 🔄 Перезапустить основные сервисы

restart-dev: ## 🔄 Перезапустить разработку
	@echo "$(BLUE)🔄 Перезапуск окружения разработки...$(NC)"
	docker compose down
	COMPOSE_PROFILES=admin docker compose up -d
	@echo "$(GREEN)✅ Окружение разработки перезапущено$(NC)"

##@ 📊 Статус и логи

status: ## 📊 Статус всех сервисов
	@echo "$(BLUE)📊 Статус сервисов:$(NC)"
	@docker compose ps

status-detailed: ## 📊 Детальный статус с health checks
	@echo "$(BLUE)📊 Детальный статус сервисов:$(NC)"
	@docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "$(CYAN)🔍 Health checks:$(NC)"
	@docker compose exec -T app curl -s http://localhost:8000/health | head -1 && echo "  ✅ App: Healthy" || echo "  ❌ App: Unhealthy"
	@docker compose exec -T postgres pg_isready -U ai_user -d ai_assistant > /dev/null 2>&1 && echo "  ✅ PostgreSQL: Ready" || echo "  ❌ PostgreSQL: Not Ready"
	@docker compose exec -T redis redis-cli ping > /dev/null 2>&1 && echo "  ✅ Redis: Ready" || echo "  ❌ Redis: Not Ready"
	@docker compose exec -T qdrant curl -s http://localhost:6333/health > /dev/null 2>&1 && echo "  ✅ Qdrant: Ready" || echo "  ❌ Qdrant: Not Ready"

logs: ## 📋 Показать логи основных сервисов
	@echo "$(GREEN)📋 Логи основных сервисов:$(NC)"
	docker compose logs -f --tail=50

logs-app: ## 📋 Логи приложения
	docker compose logs -f app

logs-db: ## 📋 Логи базы данных
	docker compose logs -f postgres

logs-e2e: ## 📋 Логи E2E тестов
	COMPOSE_PROFILES=e2e docker compose logs -f

logs-load: ## 📋 Логи нагрузочных тестов
	COMPOSE_PROFILES=load docker compose logs -f

##@ 🧪 Тестирование (Test Pyramid)
test: ## 🎯 Запуск всех тестов по пирамиде тестирования
	@echo "$(GREEN)🎯 Запуск всех тестов по пирамиде тестирования...$(NC)"
	@echo "$(CYAN)📊 Порядок выполнения:$(NC)"
	@echo "  1. Unit тесты (самые быстрые)"
	@echo "  2. Integration тесты"
	@echo "  3. Contract тесты"
	@echo "  4. Security тесты"
	@echo "  5. Smoke тесты"
	@echo "  6. E2E тесты (самые медленные)"
	@echo ""
	$(MAKE) unit
	$(MAKE) integration
	$(MAKE) contract
	$(MAKE) security
	$(MAKE) smoke
	$(MAKE) e2e
	@echo "$(GREEN)✅ Все тесты завершены!$(NC)"

unit: ## ⚡ Запуск unit тестов
	@echo "$(BLUE)⚡ Запуск unit тестов (параллельно)...$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export TESTING=true && \
	 export ENVIRONMENT=test && \
	 export LOG_LEVEL=WARNING && \
	 ./$(VENV)/bin/pytest tests/unit/ $(PYTEST_ARGS) -n auto --cov=app --cov=domain --cov=adapters --cov=backend --cov-report=term-missing --cov-report=html:htmlcov/unit
	@echo "$(GREEN)✅ Unit тесты завершены$(NC)"

smoke: ## 🚬 Запуск smoke тестов
	@echo "$(YELLOW)🚬 Запуск smoke тестов...$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export TESTING=true && \
	 export ENVIRONMENT=test && \
	 export LOG_LEVEL=WARNING && \
	 ./$(VENV)/bin/pytest tests/smoke/ $(PYTEST_ARGS) --tb=short
	@echo "$(GREEN)✅ Smoke тесты завершены$(NC)"

integration: ## 🔗 Запуск integration тестов
	@echo "$(PURPLE)🔗 Запуск integration тестов...$(NC)"
	@echo "$(YELLOW)💡 Убедитесь что инфраструктура запущена: make dev-infra-up$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export TESTING=true && \
	 export ENVIRONMENT=test && \
	 export DATABASE_URL=postgresql://ai_user:ai_password_dev@localhost:5432/ai_assistant_test && \
	 export REDIS_URL=redis://localhost:6379/1 && \
	 export QDRANT_URL=http://localhost:6333 && \
	 export LOG_LEVEL=WARNING && \
	 ./$(VENV)/bin/pytest tests/integration/ $(PYTEST_ARGS) --cov=app --cov-report=html:htmlcov/integration
	@echo "$(GREEN)✅ Integration тесты завершены$(NC)"

contract: ## 📋 Запуск contract тестов
	@echo "$(CYAN)📋 Запуск contract тестов...$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export TESTING=true && \
	 export ENVIRONMENT=test && \
	 export LOG_LEVEL=WARNING && \
	 ./$(VENV)/bin/pytest tests/contract/ $(PYTEST_ARGS)
	@echo "$(GREEN)✅ Contract тесты завершены$(NC)"

security: ## 🔒 Запуск security тестов
	@echo "$(RED)🔒 Запуск security тестов...$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export TESTING=true && \
	 export ENVIRONMENT=test && \
	 export LOG_LEVEL=WARNING && \
	 ./$(VENV)/bin/pytest tests/security/ $(PYTEST_ARGS)
	@echo "$(GREEN)✅ Security тесты завершены$(NC)"

auth: ## 🔐 Запуск auth тестов
	@echo "$(PURPLE)🔐 Запуск auth тестов...$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export TESTING=true && \
	 export ENVIRONMENT=test && \
	 export DATABASE_URL=postgresql://ai_user:ai_password_dev@localhost:5432/ai_assistant_test && \
	 export REDIS_URL=redis://localhost:6379/1 && \
	 export LOG_LEVEL=WARNING && \
	 ./$(VENV)/bin/pytest tests/auth/ $(PYTEST_ARGS)
	@echo "$(GREEN)✅ Auth тесты завершены$(NC)"

vector: ## 🎯 Запуск vector тестов
	@echo "$(CYAN)🎯 Запуск vector тестов...$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export TESTING=true && \
	 export ENVIRONMENT=test && \
	 export QDRANT_URL=http://localhost:6333 && \
	 export LOG_LEVEL=WARNING && \
	 ./$(VENV)/bin/pytest tests/vector/ $(PYTEST_ARGS)
	@echo "$(GREEN)✅ Vector тесты завершены$(NC)"

performance: ## ⚡ Запуск performance тестов
	@echo "$(YELLOW)⚡ Запуск performance тестов...$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export TESTING=true && \
	 export ENVIRONMENT=test && \
	 export LOG_LEVEL=WARNING && \
	 ./$(VENV)/bin/pytest tests/performance/ $(PYTEST_ARGS) --tb=short
	@echo "$(GREEN)✅ Performance тесты завершены$(NC)"

bootstrap-test: ## 🎓 Запуск bootstrap тестов
	@echo "$(BLUE)🎓 Запуск bootstrap тестов...$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export TESTING=true && \
	 export ENVIRONMENT=test && \
	 export LOG_LEVEL=WARNING && \
	 ./$(VENV)/bin/pytest tests/bootstrap/ $(PYTEST_ARGS)
	@echo "$(GREEN)✅ Bootstrap тесты завершены$(NC)"

e2e: ## 🎭 Запуск E2E тестов (локально)
	@echo "$(GREEN)🎭 Запуск E2E тестов локально...$(NC)"
	@echo "$(YELLOW)💡 Убедитесь что приложение запущено: make dev$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export TESTING=true && \
	 export ENVIRONMENT=test && \
	 export BASE_URL=http://localhost:8000 && \
	 export LOG_LEVEL=WARNING && \
	 ./$(VENV)/bin/pytest tests/e2e/ $(PYTEST_ARGS) --tb=short
	@echo "$(GREEN)✅ E2E тесты завершены$(NC)"

##@ 🔧 Тестирование - Утилиты

test-quick: unit smoke ## ⚡ Быстрое тестирование (unit + smoke)
	@echo "$(GREEN)⚡ Быстрое тестирование завершено$(NC)"

test-coverage: ## 📊 Генерация отчета о покрытии тестами
	@echo "$(BLUE)📊 Генерация отчета о покрытии...$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export TESTING=true && \
	 export ENVIRONMENT=test && \
	 export LOG_LEVEL=WARNING && \
	 ./$(VENV)/bin/pytest tests/unit/ tests/integration/ --cov=app --cov=domain --cov=adapters --cov=backend --cov-report=term-missing --cov-report=html:htmlcov/combined --cov-report=xml:coverage.xml
	@echo "$(GREEN)✅ Отчет о покрытии создан в htmlcov/combined/index.html$(NC)"

test-clean: ## 🧹 Очистка тестовых данных и кеша
	@echo "$(YELLOW)🧹 Очистка тестовых данных...$(NC)"
	@rm -rf htmlcov/ coverage.xml .coverage .pytest_cache/
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Тестовые данные очищены$(NC)"

test-debug: ## 🐛 Запуск тестов с отладкой
	@echo "$(YELLOW)🐛 Запуск тестов с отладкой...$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export TESTING=true && \
	 export ENVIRONMENT=test && \
	 export LOG_LEVEL=DEBUG && \
	 ./$(VENV)/bin/pytest tests/unit/ -v -s --tb=long --capture=no
	@echo "$(GREEN)✅ Отладочные тесты завершены$(NC)"

test-parallel: ## 🚀 Параллельное выполнение тестов
	@echo "$(BLUE)🚀 Параллельное выполнение тестов...$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export TESTING=true && \
	 export ENVIRONMENT=test && \
	 export LOG_LEVEL=WARNING && \
	 ./$(VENV)/bin/pytest tests/unit/ tests/smoke/ tests/contract/ tests/security/ -n auto
	@echo "$(GREEN)✅ Параллельные тесты завершены$(NC)"

test-watch: ## 👁️ Запуск тестов в режиме наблюдения
	@echo "$(CYAN)👁️ Запуск тестов в режиме наблюдения...$(NC)"
	@echo "$(YELLOW)💡 Нажмите Ctrl+C для остановки$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export TESTING=true && \
	 export ENVIRONMENT=test && \
	 export LOG_LEVEL=WARNING && \
	 ./$(VENV)/bin/pytest-watch tests/unit/ -- $(PYTEST_ARGS)

test-specific: ## 🎯 Запуск конкретного теста (TEST=path/to/test)
	@echo "$(BLUE)🎯 Запуск конкретного теста: $(TEST)$(NC)"
	@if [ -z "$(TEST)" ]; then \
		echo "$(RED)❌ Укажите тест: make test-specific TEST=tests/unit/test_example.py$(NC)"; \
		exit 1; \
	fi
	@export PYTHONPATH=$$PWD && \
	 export TESTING=true && \
	 export ENVIRONMENT=test && \
	 export LOG_LEVEL=WARNING && \
	 ./$(VENV)/bin/pytest $(TEST) $(PYTEST_ARGS) -v
	@echo "$(GREEN)✅ Конкретный тест завершен$(NC)"

##@ 🧪 Тестирование с Docker

test-e2e-full: up-e2e ## 🎭 Полные E2E тесты
	@echo "$(BLUE)🎭 Запуск полных E2E тестов...$(NC)"
	@echo "$(YELLOW)⏳ Ожидание готовности сервисов (3 минуты)...$(NC)"
	@sleep 180
	@echo "$(GREEN)🎬 Запуск Playwright тестов...$(NC)"
	COMPOSE_PROFILES=e2e docker compose run --rm e2e-playwright
	@echo "$(GREEN)✅ E2E тесты завершены$(NC)"

test-load-locust: up-load ## ⚡ Нагрузочные тесты с Locust
	@echo "$(BLUE)⚡ Запуск нагрузочных тестов с Locust...$(NC)"
	@echo "$(YELLOW)⏳ Ожидание готовности сервисов (30 секунд)...$(NC)"
	@sleep 30
	@echo "$(GREEN)🚀 Locust UI доступен на http://localhost:8089$(NC)"
	@echo "$(CYAN)💡 Откройте браузер и настройте тест:$(NC)"
	@echo "  • Host: http://load-app:8000"
	@echo "  • Users: 50"
	@echo "  • Spawn rate: 2"
	@echo "$(YELLOW)📊 Нажмите Ctrl+C чтобы остановить$(NC)"
	COMPOSE_PROFILES=load docker compose logs -f locust

test-bootstrap: bootstrap ## 🎓 Тест Bootstrap процесса
	@echo "$(BLUE)🎓 Тестирование Bootstrap процесса...$(NC)"
	@echo "$(GREEN)✅ Bootstrap тест завершен$(NC)"

##@ 🔨 Сборка образов

build: ## 🔨 Собрать все образы
	@echo "$(BLUE)🔨 Сборка всех образов...$(NC)"
	docker compose build
	@echo "$(GREEN)✅ Все образы собраны$(NC)"

build-app: ## 🔨 Собрать образ приложения
	@echo "$(BLUE)🔨 Сборка образа приложения...$(NC)"
	docker compose build app
	@echo "$(GREEN)✅ Образ приложения собран$(NC)"

build-e2e: ## 🔨 Собрать образы для E2E
	@echo "$(BLUE)🔨 Сборка образов для E2E...$(NC)"
	COMPOSE_PROFILES=e2e docker compose build
	@echo "$(GREEN)✅ E2E образы собраны$(NC)"

build-bootstrap: ## 🔨 Собрать образ для Bootstrap
	@echo "$(BLUE)🔨 Сборка образа для Bootstrap...$(NC)"
	COMPOSE_PROFILES=bootstrap docker compose build
	@echo "$(GREEN)✅ Bootstrap образ собран$(NC)"

##@ 📦 Управление данными

backup-data: ## 💾 Создать бэкап данных
	@echo "$(GREEN)💾 Создание бэкапа данных...$(NC)"
	@mkdir -p ./backups/$(shell date +%Y%m%d_%H%M%S)
	@docker compose exec postgres pg_dump -U ai_user ai_assistant > ./backups/$(shell date +%Y%m%d_%H%M%S)/postgres_backup.sql
	@cp -r ./data ./backups/$(shell date +%Y%m%d_%H%M%S)/
	@echo "$(GREEN)✅ Бэкап создан в ./backups/$(shell date +%Y%m%d_%H%M%S)/$(NC)"

clean-data: ## 🧹 Очистить данные (локальные директории)
	@echo "$(RED)🧹 ВНИМАНИЕ: Очистка всех локальных данных!$(NC)"
	@read -p "Вы уверены? Все данные будут потеряны! [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		$(MAKE) down; \
		sudo rm -rf ./data/postgres/* ./data/qdrant/* ./data/redis/* ./data/e2e/* ./data/load/* 2>/dev/null || true; \
		echo "$(GREEN)✅ Данные очищены$(NC)"; \
	else \
		echo ""; \
		echo "$(YELLOW)Отменено$(NC)"; \
	fi

setup-data-dirs: ## 📁 Создать директории для данных
	@echo "$(BLUE)📁 Создание директорий для данных...$(NC)"
	@mkdir -p data/{postgres,qdrant,redis,prometheus,grafana,ollama}
	@mkdir -p data/e2e/{postgres,qdrant,redis,jira,confluence,gitlab/{config,logs,data}}
	@mkdir -p data/load/{postgres,redis}
	@echo "$(GREEN)✅ Директории созданы$(NC)"

##@ 📚 Документация и справка

docs-docker: ## 📚 Документация по Docker окружениям
	@echo "$(GREEN)📚 AI Assistant - Unified Docker Environment$(NC)"
	@echo ""
	@echo "$(CYAN)🚀 Основные команды:$(NC)"
	@echo "  make up              - Основные сервисы"
	@echo "  make up-dev          - Разработка с админ панелями"
	@echo "  make up-dev-full     - Полная разработка"
	@echo "  make up-dev-llm      - Разработка с LLM"
	@echo ""
	@echo "$(CYAN)🧪 Тестирование:$(NC)"
	@echo "  make up-e2e          - E2E тестовое окружение"
	@echo "  make test-e2e-full   - Запуск E2E тестов"
	@echo "  make up-load         - Нагрузочное тестирование"
	@echo "  make test-load-locust - Locust нагрузочные тесты"
	@echo ""
	@echo "$(CYAN)🎓 Bootstrap:$(NC)"
	@echo "  make bootstrap       - ETL процесс загрузки данных"
	@echo "  make test-bootstrap  - Тест Bootstrap процесса"
	@echo ""
	@echo "$(CYAN)📊 Управление:$(NC)"
	@echo "  make status          - Статус сервисов"
	@echo "  make logs            - Логи сервисов"
	@echo "  make down            - Остановить все"
	@echo "  make restart         - Перезапустить"
	@echo ""
	@echo "$(CYAN)💾 Данные:$(NC)"
	@echo "  • Postgres:  ./data/postgres"
	@echo "  • Qdrant:    ./data/qdrant"
	@echo "  • Redis:     ./data/redis"
	@echo "  • E2E:       ./data/e2e/"
	@echo "  • Load:      ./data/load/"

help-docker: docs-docker ## Алиас для docs-docker

# Ensure data directories exist
$(shell mkdir -p data/{postgres,qdrant,redis,prometheus,grafana,ollama})
$(shell mkdir -p data/e2e/{postgres,qdrant,redis,jira,confluence,gitlab/{config,logs,data}})
$(shell mkdir -p data/load/{postgres,redis}) 