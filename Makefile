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

setup-dev: install dev-infra-up migrate ## Полная настройка окружения разработки
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

##@ 🐳 Полная система (Docker)
system-up: ## Запустить полную систему в Docker
	@echo "$(GREEN)🚀 Запуск полной системы...$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.simple.yml up -d
	@echo "$(GREEN)✅ Полная система запущена!$(NC)"
	@echo "$(CYAN)🌐 Доступные сервисы:$(NC)"
	@echo "  • API:        http://localhost:8000"
	@echo "  • Frontend:   http://localhost:3000"
	@echo "  • API Docs:   http://localhost:8000/docs"

system-up-full: ## Запустить систему с мониторингом
	@echo "$(GREEN)🚀 Запуск полной системы с мониторингом...$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.full.yml --profile monitoring up -d
	@echo "$(GREEN)✅ Полная система с мониторингом запущена!$(NC)"

system-down: ## Остановить полную систему
	@echo "$(YELLOW)🛑 Остановка полной системы...$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.simple.yml down
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.full.yml down
	@echo "$(GREEN)✅ Система остановлена$(NC)"

system-status: ## Статус полной системы
	@echo "$(BLUE)📊 Статус полной системы:$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.simple.yml ps || true
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.full.yml ps || true

system-logs: ## Логи полной системы
	@echo "$(GREEN)📋 Логи системы:$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.simple.yml logs -f

system-restart: system-down system-up ## Перезапустить полную систему

##@ 🗄 База данных
migrate: ## Применение миграций
	@echo "$(BLUE)🗄 Применение миграций...$(NC)"
	@export PYTHONPATH=$$PWD && \
	 export DATABASE_URL=postgresql://ai_user:ai_password_dev@localhost:5432/ai_assistant && \
	 ./$(VENV)/bin/alembic upgrade head
	@echo "$(GREEN)✅ Миграции применены$(NC)"

migrate-create: ## Создание новой миграции
	@read -p "Название миграции: " name; \
	export PYTHONPATH=$$PWD && \
	export DATABASE_URL=postgresql://ai_user:ai_password_dev@localhost:5432/ai_assistant && \
	./$(VENV)/bin/alembic revision --autogenerate -m "$$name"

db-reset: ## Сброс базы данных
	@echo "$(RED)🗄 Сброс базы данных...$(NC)"
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml stop postgres
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml rm -f postgres
	@$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres
	@sleep 10
	@$(MAKE) migrate
	@echo "$(GREEN)✅ База данных сброшена$(NC)"

##@ 🧪 Тестирование
test: ## Запуск всех тестов
	@echo "$(BLUE)🧪 Запуск всех тестов...$(NC)"
	@export PYTHONPATH=$$PWD && ./$(VENV)/bin/pytest tests/ -v --tb=short

test-unit: ## Запуск unit тестов
	@echo "$(BLUE)🔬 Запуск unit тестов...$(NC)"
	@export PYTHONPATH=$$PWD && ./$(VENV)/bin/pytest tests/unit/ -v

test-integration: ## Запуск integration тестов
	@echo "$(BLUE)🔗 Запуск integration тестов...$(NC)"
	@export PYTHONPATH=$$PWD && ./$(VENV)/bin/pytest tests/integration/ -v

test-smoke: ## Запуск smoke тестов
	@echo "$(BLUE)💨 Запуск smoke тестов...$(NC)"
	@export PYTHONPATH=$$PWD && ./$(VENV)/bin/pytest tests/smoke/ -v

test-e2e: ## Запуск e2e тестов
	@echo "$(BLUE)🎭 Запуск e2e тестов...$(NC)"
	@export PYTHONPATH=$$PWD && ./$(VENV)/bin/pytest tests/e2e/ -v

test-coverage: ## Тестирование с покрытием кода
	@echo "$(BLUE)📊 Тестирование с покрытием...$(NC)"
	@export PYTHONPATH=$$PWD && ./$(VENV)/bin/pytest --cov=app --cov-report=html --cov-report=term tests/
	@echo "$(GREEN)📊 Отчет сохранен в htmlcov/index.html$(NC)"

test-load: ## Запуск нагрузочных тестов
	@echo "$(BLUE)⚡ Запуск нагрузочных тестов...$(NC)"
	@export PYTHONPATH=$$PWD && ./$(VENV)/bin/python tests/performance/test_core_functionality_load.py

##@ 🔍 Качество кода
lint: ## Проверка кода линтерами
	@echo "$(BLUE)🔍 Проверка кода...$(NC)"
	./$(VENV)/bin/flake8 app/ tests/ || true
	./$(VENV)/bin/pylint app/ --disable=C0114,C0116 || true

format: ## Форматирование кода
	@echo "$(BLUE)✨ Форматирование кода...$(NC)"
	./$(VENV)/bin/black app/ tests/ || true
	./$(VENV)/bin/isort app/ tests/ || true

format-check: ## Проверка форматирования
	@echo "$(BLUE)📏 Проверка форматирования...$(NC)"
	./$(VENV)/bin/black --check app/ tests/ || true
	./$(VENV)/bin/isort --check-only app/ tests/ || true

##@ ⎈ Kubernetes & Helm
helm-install: ## Установка через Helm
	@echo "$(PURPLE)⎈ Установка через Helm...$(NC)"
	@$(HELM) install ai-assistant deployment/helm/ai-assistant/ \
		--namespace ai-assistant \
		--create-namespace \
		--values deployment/helm/ai-assistant/values.yaml \
		--wait
	@echo "$(GREEN)✅ Helm установка завершена$(NC)"

helm-upgrade: ## Обновление Helm релиза
	@echo "$(PURPLE)⎈ Обновление Helm релиза...$(NC)"
	@$(HELM) upgrade ai-assistant deployment/helm/ai-assistant/ \
		--namespace ai-assistant \
		--values deployment/helm/ai-assistant/values.yaml \
		--wait
	@echo "$(GREEN)✅ Helm обновление завершено$(NC)"

helm-uninstall: ## Удаление Helm релиза
	@echo "$(RED)⎈ Удаление Helm релиза...$(NC)"
	@$(HELM) uninstall ai-assistant --namespace ai-assistant
	@echo "$(GREEN)✅ Helm удаление завершено$(NC)"

helm-status: ## Статус Helm деплоя
	@echo "$(BLUE)⎈ Статус Helm:$(NC)"
	@$(HELM) status ai-assistant --namespace ai-assistant

helm-logs: ## Логи Helm деплоя
	@echo "$(GREEN)⎈ Логи Helm:$(NC)"
	@$(KUBECTL) logs -l app.kubernetes.io/name=ai-assistant -n ai-assistant -f

##@ 📊 Мониторинг и диагностика
health: ## Проверка здоровья системы
	@echo "$(BLUE)🏥 Проверка здоровья системы...$(NC)"
	@curl -f http://localhost:8000/health 2>/dev/null | jq . || echo "$(RED)❌ API недоступен$(NC)"

health-detailed: ## Детальная проверка здоровья
	@echo "$(BLUE)🔬 Детальная диагностика...$(NC)"
	@export PYTHONPATH=$$PWD && ./$(VENV)/bin/python debug_helper.py basic || true

logs: ## Просмотр логов приложения
	@echo "$(BLUE)📋 Логи приложения...$(NC)"
	@tail -f logs/app.log 2>/dev/null || echo "$(YELLOW)Файл логов не найден$(NC)"

monitor: ## Запуск мониторинга
	@echo "$(BLUE)📊 Запуск мониторинга...$(NC)"
	@$(DOCKER_COMPOSE) -f monitoring/docker-compose.monitoring.yml up -d || true
	@echo "$(GREEN)Grafana: http://localhost:3001$(NC)"
	@echo "$(GREEN)Prometheus: http://localhost:9090$(NC)"

##@ 🧹 Очистка
clean: ## Очистка временных файлов
	@echo "$(YELLOW)🧹 Очистка временных файлов...$(NC)"
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/ htmlcov/ .coverage 2>/dev/null || true
	@echo "$(GREEN)✅ Временные файлы удалены$(NC)"

clean-docker: ## Очистка Docker ресурсов
	@echo "$(RED)🐳 Очистка Docker ресурсов...$(NC)"
	docker system prune -f
	docker volume prune -f
	@echo "$(GREEN)✅ Docker ресурсы очищены$(NC)"

clean-all: clean clean-docker dev-infra-clean ## Полная очистка
	@echo "$(GREEN)✅ Полная очистка завершена$(NC)"

##@ 📦 Продакшн деплой
build: ## Сборка Docker образов
	@echo "$(BLUE)🐳 Сборка Docker образов...$(NC)"
	docker build -t ai-assistant:latest .
	docker build -f deployment/docker/Dockerfile.prod -t ai-assistant:prod .

deploy-prod: build ## Продакшн развертывание
	@echo "$(GREEN)🏭 Продакшн развертывание...$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.prod.yml up -d

deploy-local: build ## Локальное развертывание через Docker
	@echo "$(GREEN)🚀 Локальное развертывание...$(NC)"
	@$(DOCKER_COMPOSE) -f deployment/docker/docker-compose.simple.yml up -d

##@ ℹ️ Информация
status: ## Статус всех систем
	@echo "$(BLUE)📊 Статус всех систем:$(NC)"
	@echo "$(GREEN)Docker контейнеры:$(NC)"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "$(GREEN)Kubernetes pods:$(NC)"
	@$(KUBECTL) get pods -n ai-assistant 2>/dev/null || echo "Kubernetes недоступен"

info: ## Информация о проекте
	@echo "$(GREEN)🤖 AI Assistant Platform$(NC)"
	@echo "$(BLUE)Версия:$(NC) 1.0.0"
	@echo "$(BLUE)Python:$(NC) $$(python3 --version 2>/dev/null || echo 'Не установлен')"
	@echo "$(BLUE)Docker:$(NC) $$(docker --version 2>/dev/null | head -1 || echo 'Не установлен')"
	@echo "$(BLUE)Kubernetes:$(NC) $$(kubectl version --client --short 2>/dev/null || echo 'Недоступен')"
	@echo ""
	@echo "$(GREEN)🌐 Доступные сервисы после запуска:$(NC)"
	@echo "  API:           http://localhost:8000"
	@echo "  Docs:          http://localhost:8000/docs"
	@echo "  Health:        http://localhost:8000/health"
	@echo "  Frontend:      http://localhost:3000"
	@echo "  Adminer:       http://localhost:8080"
	@echo "  Redis UI:      http://localhost:8081"
	@echo "  Qdrant UI:     http://localhost:6333/dashboard"
	@echo "  MailHog:       http://localhost:8025"
	@echo "  Grafana:       http://localhost:3001"
	@echo "  Prometheus:    http://localhost:9090"

# Значение по умолчанию
.DEFAULT_GOAL := help

# Алиасы для совместимости
docker-up: system-up
docker-down: system-down
docker-logs: system-logs
docker-status: system-status 