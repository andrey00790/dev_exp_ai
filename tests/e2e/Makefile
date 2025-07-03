# E2E Testing Makefile
# Управление локальными инстансами и тестами

.PHONY: help setup start stop clean test test-quick load-data logs status

# Цвета для вывода
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

help: ## Показать справку
	@echo "$(GREEN)E2E Testing Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

setup: ## Установить зависимости для E2E тестов
	@echo "$(GREEN)Installing E2E test dependencies...$(NC)"
	pip install -r requirements-e2e.txt
	docker --version || (echo "$(RED)Docker not installed$(NC)" && exit 1)
	docker-compose --version || (echo "$(RED)Docker Compose not installed$(NC)" && exit 1)

start: ## Запустить все сервисы (Jira, Confluence, GitLab, ES, Redis)
	@echo "$(GREEN)Starting E2E environment...$(NC)"
	docker-compose up -d
	@echo "$(YELLOW)Waiting for services to start (this may take 5-10 minutes)...$(NC)"
	@sleep 30
	@echo "$(GREEN)Services starting in background. Use 'make status' to check progress$(NC)"
	@echo "$(YELLOW)Services will be available at:$(NC)"
	@echo "  Jira: http://localhost:8080"
	@echo "  Confluence: http://localhost:8090" 
	@echo "  GitLab: http://localhost:8088"
	@echo "  Elasticsearch: http://localhost:9200"

stop: ## Остановить все сервисы
	@echo "$(GREEN)Stopping E2E environment...$(NC)"
	docker-compose down

clean: ## Очистить все данные и контейнеры
	@echo "$(YELLOW)Removing all E2E containers and volumes...$(NC)"
	docker-compose down -v --remove-orphans
	docker system prune -f

load-data: ## Загрузить тестовые данные в сервисы
	@echo "$(GREEN)Loading test data...$(NC)"
	docker-compose run --rm test-data-loader
	@echo "$(GREEN)Test data loaded successfully!$(NC)"

test: start ## Запустить полные E2E тесты
	@echo "$(GREEN)Running full E2E tests...$(NC)"
	@sleep 180  # Ожидание полной инициализации
	pytest test_integration.py -v --tb=short --durations=10
	@$(MAKE) stop

test-quick: ## Запустить быстрые E2E тесты (без перезапуска сервисов)
	@echo "$(GREEN)Running quick E2E tests...$(NC)"
	pytest test_integration.py -v --tb=short -k "not async"

test-multilingual: ## Запустить тесты многоязычности 
	@echo "$(GREEN)Running multilingual E2E tests...$(NC)"
	pytest test_integration.py -v --tb=short -k "multilingual or russian"

status: ## Показать статус всех сервисов
	@echo "$(GREEN)Service Status:$(NC)"
	@docker-compose ps
	@echo ""
	@echo "$(GREEN)Health Checks:$(NC)"
	@curl -s http://localhost:8080/status >/dev/null && echo "  ✅ Jira: Ready" || echo "  ❌ Jira: Not Ready"
	@curl -s http://localhost:8090/status >/dev/null && echo "  ✅ Confluence: Ready" || echo "  ❌ Confluence: Not Ready"
	@curl -s http://localhost:8088/-/health >/dev/null && echo "  ✅ GitLab: Ready" || echo "  ❌ GitLab: Not Ready"
	@curl -s http://localhost:9200/_cluster/health >/dev/null && echo "  ✅ Elasticsearch: Ready" || echo "  ❌ Elasticsearch: Not Ready"

logs: ## Показать логи всех сервисов
	docker-compose logs -f

logs-jira: ## Показать логи Jira
	docker-compose logs -f jira

logs-confluence: ## Показать логи Confluence 
	docker-compose logs -f confluence

logs-gitlab: ## Показать логи GitLab
	docker-compose logs -f gitlab

# Команды для разработки
dev-start: ## Запустить только инфраструктурные сервисы (PostgreSQL, ES, Redis)
	@echo "$(GREEN)Starting infrastructure services...$(NC)"
	docker-compose up -d postgres elasticsearch redis

dev-stop: ## Остановить инфраструктурные сервисы
	docker-compose stop postgres elasticsearch redis

# Управление данными
backup-data: ## Создать бэкап тестовых данных
	@echo "$(GREEN)Creating data backup...$(NC)"
	mkdir -p backups
	docker exec e2e_postgres pg_dump -U atlassian atlassian > backups/postgres_backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Backup created in backups/ directory$(NC)"

restore-data: ## Восстановить данные из бэкапа (указать файл: make restore-data BACKUP=filename.sql)
	@if [ -z "$(BACKUP)" ]; then echo "$(RED)Please specify backup file: make restore-data BACKUP=filename.sql$(NC)"; exit 1; fi
	@echo "$(GREEN)Restoring data from $(BACKUP)...$(NC)"
	docker exec -i e2e_postgres psql -U atlassian atlassian < backups/$(BACKUP)

# Тестирование производительности
perf-test: ## Запустить тесты производительности
	@echo "$(GREEN)Running performance tests...$(NC)"
	pytest test_integration.py -v -k "performance" --benchmark-only

# Очистка
clean-logs: ## Очистить логи Docker
	docker system prune -f --volumes

clean-images: ## Удалить неиспользуемые образы
	docker image prune -f

# Мониторинг ресурсов
monitor: ## Показать использование ресурсов
	@echo "$(GREEN)Resource Usage:$(NC)"
	docker stats --no-stream

# CI/CD интеграция
ci-test: setup start ## Команда для CI/CD пайплайна
	@echo "$(GREEN)Running CI E2E tests...$(NC)"
	@sleep 300  # Больше времени для CI окружения
	pytest test_integration.py -v --tb=short --junitxml=e2e-results.xml
	@$(MAKE) clean

# Отладка
debug-jira: ## Отладочное подключение к Jira контейнеру
	docker exec -it e2e_jira bash

debug-confluence: ## Отладочное подключение к Confluence контейнеру  
	docker exec -it e2e_confluence bash

debug-gitlab: ## Отладочное подключение к GitLab контейнеру
	docker exec -it e2e_gitlab bash

debug-postgres: ## Отладочное подключение к PostgreSQL
	docker exec -it e2e_postgres psql -U atlassian atlassian

# Полезные команды
urls: ## Показать URLs всех сервисов
	@echo "$(GREEN)Service URLs:$(NC)"
	@echo "  Jira:          http://localhost:8080"
	@echo "  Confluence:    http://localhost:8090"
	@echo "  GitLab:        http://localhost:8088"
	@echo "  Elasticsearch: http://localhost:9200"
	@echo "  Redis:         redis://localhost:6379"
	@echo ""
	@echo "$(GREEN)Default Credentials:$(NC)"
	@echo "  Username: admin"
	@echo "  Password: admin"

ports: ## Показать используемые порты
	@echo "$(GREEN)Used Ports:$(NC)"
	@netstat -tuln | grep -E ':8080|:8088|:8090|:9200|:6379|:5432' || echo "No services running" 