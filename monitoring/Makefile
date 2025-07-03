# AI Assistant Monitoring Makefile

.PHONY: help start stop status logs clean

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)AI Assistant Monitoring Commands:$(NC)"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

start: ## Start monitoring stack (Prometheus + Grafana)
	@echo "$(GREEN)Starting monitoring stack...$(NC)"
	docker-compose -f docker-compose.monitoring.yml up -d
	@echo "$(GREEN)✅ Monitoring stack started$(NC)"
	@echo "$(YELLOW)Services available at:$(NC)"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana:    http://localhost:3001 (admin/admin)"

stop: ## Stop monitoring stack
	@echo "$(GREEN)Stopping monitoring stack...$(NC)"
	docker-compose -f docker-compose.monitoring.yml down
	@echo "$(GREEN)✅ Monitoring stack stopped$(NC)"

status: ## Show status of monitoring services
	@echo "$(GREEN)Monitoring Services Status:$(NC)"
	docker-compose -f docker-compose.monitoring.yml ps

logs: ## Show logs from monitoring services
	docker-compose -f docker-compose.monitoring.yml logs -f

restart: ## Restart monitoring stack
	@echo "$(GREEN)Restarting monitoring stack...$(NC)"
	docker-compose -f docker-compose.monitoring.yml restart
	@echo "$(GREEN)✅ Monitoring stack restarted$(NC)"

clean: ## Clean monitoring data and containers
	@echo "$(RED)Cleaning monitoring data...$(NC)"
	docker-compose -f docker-compose.monitoring.yml down -v
	@echo "$(GREEN)✅ Monitoring data cleaned$(NC)"

test-metrics: ## Test metrics endpoint
	@echo "$(GREEN)Testing metrics endpoint...$(NC)"
	@curl -s http://localhost:8000/metrics | head -10 || echo "$(RED)❌ Metrics endpoint not available$(NC)"

monitor: ## Open monitoring URLs
	@echo "$(GREEN)Opening monitoring interfaces...$(NC)"
	@command -v open >/dev/null 2>&1 && open http://localhost:9090 || echo "Prometheus: http://localhost:9090"
	@command -v open >/dev/null 2>&1 && open http://localhost:3001 || echo "Grafana: http://localhost:3001" 