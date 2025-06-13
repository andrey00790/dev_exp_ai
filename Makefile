.PHONY: up down test healthcheck run bootstrap smoke-test

docker_available := $(shell command -v docker 2>/dev/null)

# Bootstrap - полное развертывание проекта одной командой
bootstrap:
	@echo "🚀 Bootstrapping AI Assistant MVP..."
	@if [ ! -f .env.local ]; then \
		echo "📋 Creating .env.local from .env.example..."; \
		cp .env.example .env.local; \
	fi
	@echo "📦 Installing dependencies..."
	@pip3 install -r requirements.txt
	@echo "🐳 Starting infrastructure..."
	@$(MAKE) up
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@echo "🔍 Running health checks..."
	@$(MAKE) healthcheck
	@echo "🧪 Running tests..."
	@$(MAKE) test
	@echo "💨 Running smoke tests..."
	@$(MAKE) smoke-test
	@echo "✅ Bootstrap complete! AI Assistant MVP is ready."
	@echo "🌐 Application: http://localhost:8000"
	@echo "📊 API Docs: http://localhost:8000/docs"
	@echo "🔍 Qdrant: http://localhost:6333/dashboard"

up:
	@if [ -n "$(docker_available)" ]; then \
		echo "🐳 Starting Docker services..."; \
		docker compose up -d --build; \
		echo "⏳ Waiting for services to start..."; \
		sleep 5; \
	else \
		echo "⚠️  Docker not available, starting locally..."; \
		PYTHONPATH=. nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 & echo $$! > .app.pid; \
		echo "✅ App started with PID $$(cat .app.pid)"; \
	fi

down:
	@if [ -n "$(docker_available)" ]; then \
		echo "🛑 Stopping Docker services..."; \
		docker compose down; \
	else \
		if [ -f .app.pid ]; then \
			kill $$(cat .app.pid) && rm .app.pid && echo "✅ App stopped"; \
		else \
			echo "⚠️  No running app found"; \
		fi; \
	fi

healthcheck:
	@echo "🔍 Checking service health..."
	@if ! curl -fs http://localhost:8000/health >/dev/null 2>&1; then \
		echo "❌ Service not responding, attempting to start..."; \
		PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 & \
		pid=$$!; \
		sleep 5; \
		if curl -f http://localhost:8000/health; then \
			echo "✅ Health check passed"; \
		else \
			echo "❌ Health check failed"; \
			exit 1; \
		fi; \
		kill $$pid; \
	else \
		curl -f http://localhost:8000/health && echo "✅ Service is healthy"; \
	fi

test:
	@echo "🧪 Running tests..."
	@PYTHONPATH=. python3 -m pytest -v --cov=app --cov-report=term-missing --cov-fail-under=80

smoke-test:
	@echo "💨 Running smoke tests..."
	@PYTHONPATH=. python3 -m pytest tests/smoke/ -v --tb=short

run:
	@echo "🚀 Starting development server..."
	@PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Очистка всех данных и контейнеров
clean:
	@echo "🧹 Cleaning up..."
	@if [ -n "$(docker_available)" ]; then \
		docker compose down -v --remove-orphans; \
		docker system prune -f; \
	fi
	@rm -f .app.pid
	@echo "✅ Cleanup complete"

# Показать статус всех сервисов
status:
	@echo "📊 Service Status:"
	@echo "Web API: $$(curl -s http://localhost:8000/health > /dev/null && echo '✅ UP' || echo '❌ DOWN')"
	@echo "Qdrant: $$(curl -s http://localhost:6333/dashboard > /dev/null && echo '✅ UP' || echo '❌ DOWN')"
	@echo "Ollama: $$(curl -s http://localhost:11434/api/tags > /dev/null && echo '✅ UP' || echo '❌ DOWN')"
	@if [ -n "$(docker_available)" ]; then \
		echo "Docker services:"; \
		docker compose ps; \
	fi

# =============================================================================
# E2E PIPELINE WITH MODEL TRAINING
# =============================================================================

.PHONY: e2e-full-pipeline
e2e-full-pipeline: ## Полный E2E пайплайн с обучением модели
	@echo "🚀 Запуск полного E2E пайплайна с обучением модели..."
	docker-compose up -d
	@echo "⏳ Ожидание готовности сервисов (3 минуты)..."
	sleep 180
	python -m pytest test_e2e_extended.py::TestE2EExtendedPipeline::test_complete_e2e_pipeline_with_model_training -v -s --tb=short
	@echo "✅ Полный E2E пайплайн завершён"

.PHONY: train-model
train-model: ## Обучение модели на основе dataset_config.yml
	@echo "🧠 Обучение модели..."
	python model_training.py
	@echo "✅ Обучение модели завершено"

.PHONY: test-feedback
test-feedback: ## Тестирование системы обратной связи
	@echo "🔄 Тестирование системы обратной связи..."
	python -m pytest test_e2e_extended.py::TestE2EExtendedPipeline::test_feedback_and_retraining -v -s
	@echo "✅ Тестирование обратной связи завершено"

.PHONY: test-multilingual
test-multilingual: ## Тестирование мультиязычной функциональности
	@echo "🌐 Тестирование мультиязычной функциональности..."
	python -m pytest test_e2e_extended.py::TestE2EExtendedPipeline::test_multilingual_model_performance -v -s
	@echo "✅ Мультиязычное тестирование завершено"

.PHONY: run-semantic-search-tests
run-semantic-search-tests: ## Запуск тестов семантического поиска
	@echo "🔍 Запуск тестов семантического поиска..."
	python evaluate_semantic_search.py --language all --output results/semantic_search_results.json
	@echo "✅ Тесты семантического поиска завершены"

.PHONY: run-rfc-tests
run-rfc-tests: ## Запуск тестов RFC генерации
	@echo "📝 Запуск тестов RFC генерации..."
	python validate_rfc.py --language all --output results/rfc_validation_results.json
	@echo "✅ Тесты RFC генерации завершены"

.PHONY: check-model-quality
check-model-quality: ## Проверка качества модели в PostgreSQL
	@echo "📊 Проверка качества модели..."
	python -c "
import psycopg2
import json
import os
from datetime import datetime, timedelta

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=os.getenv('POSTGRES_PORT', 5432),
    database=os.getenv('POSTGRES_DB', 'testdb'),
    user=os.getenv('POSTGRES_USER', 'testuser'),
    password=os.getenv('POSTGRES_PASSWORD', 'testpass')
)

with conn.cursor() as cursor:
    cursor.execute('''
        SELECT metric_name, AVG(metric_value) as avg_value, COUNT(*) as count
        FROM model_metrics 
        WHERE timestamp > %s
        GROUP BY metric_name
        ORDER BY metric_name
    ''', (datetime.now() - timedelta(days=7),))
    
    results = cursor.fetchall()
    
    print('📈 Метрики модели за последнюю неделю:')
    for metric_name, avg_value, count in results:
        print(f'  {metric_name}: {avg_value:.3f} (записей: {count})')
        
    cursor.execute('''
        SELECT COUNT(*) as feedback_count
        FROM model_feedback 
        WHERE timestamp > %s
    ''', (datetime.now() - timedelta(days=7),))
    
    feedback_count = cursor.fetchone()[0]
    print(f'💬 Записей обратной связи: {feedback_count}')

conn.close()
"
	@echo "✅ Проверка качества модели завершена"

.PHONY: simulate-user-feedback
simulate-user-feedback: ## Симуляция пользовательской обратной связи
	@echo "👥 Симуляция пользовательской обратной связи..."
	python -c "
import psycopg2
import json
import os
import random
from datetime import datetime

feedback_scenarios = [
    {'query': 'OAuth 2.0 implementation', 'doc': 'OAuth Guide', 'score': 0.95, 'lang': 'en'},
    {'query': 'реализация OAuth 2.0', 'doc': 'Руководство OAuth', 'score': 0.93, 'lang': 'ru'},
    {'query': 'microservices patterns', 'doc': 'Microservices Guide', 'score': 0.88, 'lang': 'en'},
    {'query': 'паттерны микросервисов', 'doc': 'Руководство по микросервисам', 'score': 0.86, 'lang': 'ru'},
]

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=os.getenv('POSTGRES_PORT', 5432),
    database=os.getenv('POSTGRES_DB', 'testdb'),
    user=os.getenv('POSTGRES_USER', 'testuser'),
    password=os.getenv('POSTGRES_PASSWORD', 'testpass')
)

with conn.cursor() as cursor:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_feedback (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            query TEXT NOT NULL,
            document TEXT NOT NULL,
            relevance_score FLOAT NOT NULL,
            language VARCHAR(10),
            user_id VARCHAR(100),
            processed BOOLEAN DEFAULT FALSE,
            metadata JSONB
        )
    ''')
    
    for i in range(20):
        scenario = random.choice(feedback_scenarios)
        cursor.execute('''
            INSERT INTO model_feedback 
            (query, document, relevance_score, language, user_id, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            scenario['query'],
            scenario['doc'],
            scenario['score'] + random.uniform(-0.1, 0.1),
            scenario['lang'],
            f'sim_user_{i}',
            json.dumps({'simulated': True, 'batch': datetime.now().isoformat()})
        ))
    
    conn.commit()
    
print('✅ Создано 20 записей симулированной обратной связи')
conn.close()
"
	@echo "✅ Симуляция обратной связи завершена"

.PHONY: retrain-model
retrain-model: ## Переобучение модели на основе обратной связи
	@echo "🔄 Переобучение модели на основе обратной связи..."
	python -c "
from model_training import ModelTrainer

trainer = ModelTrainer()
feedback_data = trainer.get_feedback_from_postgres()

if len(feedback_data) >= 10:
    print(f'🔄 Найдено {len(feedback_data)} записей обратной связи')
    print('📚 Запуск переобучения...')
    trainer.retrain_with_feedback(feedback_data[:50])  # Ограничиваем для быстрого тестирования
    print('✅ Переобучение завершено')
    
    metrics = trainer.evaluate_model()
    print(f'📊 Новые метрики: {metrics}')
else:
    print(f'⚠️ Недостаточно данных для переобучения: {len(feedback_data)} записей')
"
	@echo "✅ Переобучение модели завершено"

.PHONY: e2e-quick
e2e-quick: ## Быстрый E2E тест (без полного обучения)
	@echo "⚡ Быстрый E2E тест..."
	docker-compose up -d postgres elasticsearch redis
	@echo "⏳ Ожидание готовности базовых сервисов (30 сек)..."
	sleep 30
	python -m pytest test_e2e_extended.py::TestSpecificE2EScenarios::test_concurrent_feedback_processing -v -s
	@echo "✅ Быстрый E2E тест завершён"

.PHONY: e2e-advanced-scenarios
e2e-advanced-scenarios: ## Запуск дополнительных E2E сценариев
	@echo "🎯 Запуск дополнительных E2E сценариев..."
	python -m pytest test_e2e_extended.py::TestE2EExtendedPipeline::_run_advanced_e2e_scenarios -v -s
	@echo "✅ Дополнительные E2E сценарии завершены"

.PHONY: monitor-model-performance
monitor-model-performance: ## Мониторинг производительности модели
	@echo "📈 Мониторинг производительности модели..."
	python -c "
import psycopg2
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=os.getenv('POSTGRES_PORT', 5432),
    database=os.getenv('POSTGRES_DB', 'testdb'),
    user=os.getenv('POSTGRES_USER', 'testuser'),
    password=os.getenv('POSTGRES_PASSWORD', 'testpass')
)

# Получаем данные за последние 30 дней
with conn.cursor() as cursor:
    cursor.execute('''
        SELECT 
            DATE(timestamp) as date,
            metric_name,
            AVG(metric_value) as avg_value
        FROM model_metrics 
        WHERE timestamp > %s
        GROUP BY DATE(timestamp), metric_name
        ORDER BY date DESC, metric_name
    ''', (datetime.now() - timedelta(days=30),))
    
    results = cursor.fetchall()
    
    if results:
        df = pd.DataFrame(results, columns=['date', 'metric', 'value'])
        print('📊 Тренды метрик за последние 30 дней:')
        print(df.pivot(index='date', columns='metric', values='value'))
    else:
        print('⚠️ Нет данных о метриках за последние 30 дней')

conn.close()
"
	@echo "✅ Мониторинг завершён"

# =============================================================================
# DATASET AND TRAINING MANAGEMENT
# =============================================================================

.PHONY: validate-dataset
validate-dataset: ## Валидация конфигурации датасета
	@echo "✅ Валидация dataset_config.yml..."
	python -c "
import yaml
import json

with open('dataset_config.yml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

print('📋 Конфигурация датасета:')
print(f'  Версия: {config['metadata']['version']}')
print(f'  Языки: {config['metadata']['languages']}')
print(f'  Общее количество документов: {config['metadata']['total_documents']}')
print(f'  Категории: {config['metadata']['categories']}')

# Проверяем источники данных
sources = config['data_sources']
enabled_sources = [name for name, conf in sources.items() if conf.get('enabled', False)]
print(f'  Активные источники: {enabled_sources}')

# Проверяем обучающие пары
training_pairs = config.get('training_pairs', {}).get('semantic_search', [])
print(f'  Обучающих пар: {len(training_pairs)}')

# Проверяем конфигурацию модели
model_config = config['model_config']
print(f'  Модель: {model_config['embeddings']['model_name']}')
print(f'  Размерность: {model_config['embeddings']['dimensions']}')
print(f'  Batch size: {model_config['embeddings']['batch_size']}')

print('✅ Конфигурация датасета валидна')
"
	@echo "✅ Валидация датасета завершена"

.PHONY: backup-model
backup-model: ## Создание резервной копии обученной модели
	@echo "💾 Создание резервной копии модели..."
	@if [ -d "./trained_model" ]; then \
		timestamp=$$(date +"%Y%m%d_%H%M%S"); \
		cp -r ./trained_model ./backups/model_backup_$$timestamp; \
		echo "✅ Резервная копия создана: ./backups/model_backup_$$timestamp"; \
	else \
		echo "⚠️ Обученная модель не найдена в ./trained_model"; \
	fi

.PHONY: restore-model
restore-model: ## Восстановление модели из резервной копии
	@echo "🔄 Восстановление модели из резервной копии..."
	@if [ -z "$(BACKUP)" ]; then \
		echo "❌ Укажите резервную копию: make restore-model BACKUP=model_backup_20231201_120000"; \
		exit 1; \
	fi
	@if [ -d "./backups/$(BACKUP)" ]; then \
		rm -rf ./trained_model; \
		cp -r ./backups/$(BACKUP) ./trained_model; \
		echo "✅ Модель восстановлена из $(BACKUP)"; \
	else \
		echo "❌ Резервная копия ./backups/$(BACKUP) не найдена"; \
		exit 1; \
	fi

.PHONY: clean-model-data
clean-model-data: ## Очистка данных модели и метрик
	@echo "🧹 Очистка данных модели..."
	@read -p "Вы уверены? Это удалит все данные модели и метрики (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		rm -rf ./trained_model ./model_output; \
		docker-compose exec postgres psql -U testuser -d testdb -c "TRUNCATE TABLE model_metrics, model_feedback;"; \
		echo "✅ Данные модели очищены"; \
	else \
		echo "❌ Отменено"; \
	fi

# =============================================================================
# ПОЛЬЗОВАТЕЛЬСКИЕ НАСТРОЙКИ
# =============================================================================

.PHONY: create-user-schema
create-user-schema: ## Создание схемы пользовательских настроек
	@echo "🗄️ Создание схемы пользовательских настроек..."
	docker-compose exec -T postgres psql -U testuser -d testdb < user_config_schema.sql
	@echo "✅ Схема пользовательских настроек создана"

.PHONY: create-test-user
create-test-user: ## Создание тестового пользователя с настройками
	@echo "👤 Создание тестового пользователя с настройками..."
	python user_config_manager.py
	@echo "✅ Тестовый пользователь создан"

.PHONY: setup-user-system
setup-user-system: create-user-schema create-test-user ## Настройка полной системы пользователей
	@echo "🎉 Система пользовательских настроек готова!"

.PHONY: test-user-sync
test-user-sync: ## Тестирование синхронизации пользователя
	@echo "🔄 Тестирование пользовательской синхронизации..."
	python -c "
import asyncio
from user_config_manager import UserConfigManager, SyncManager

async def test_sync():
    config_manager = UserConfigManager()
    sync_manager = SyncManager(config_manager)
    
    # Получаем первого пользователя
    with config_manager.db_conn.cursor() as cursor:
        cursor.execute('SELECT id FROM users LIMIT 1')
        row = cursor.fetchone()
        if row:
            user_id = row[0]
            print(f'🧪 Тестируем синхронизацию для пользователя {user_id}')
            
            task_id = await sync_manager.start_sync_task(
                user_id=user_id,
                sources=['jira', 'confluence', 'gitlab'],
                task_type='manual'
            )
            
            print(f'📝 Создана задача синхронизации: {task_id}')
            
            # Ждем немного и проверяем статус
            await asyncio.sleep(2)
            status = sync_manager.get_sync_status(task_id)
            if status:
                print(f'📊 Статус: {status["status"]} ({status["progress_percentage"]}%)')
                
            logs = sync_manager.get_sync_logs(task_id)[:5]  # Последние 5 логов
            print(f'📋 Логов: {len(logs)}')
            for log in logs:
                print(f'  {log["log_level"]}: {log["message"]}')
        else:
            print('❌ Нет пользователей в системе')

asyncio.run(test_sync())
"
	@echo "✅ Тестирование синхронизации завершено"

.PHONY: show-user-stats
show-user-stats: ## Показать статистику пользователей
	@echo "📊 Статистика пользователей..."
	python -c "
import psycopg2
import os

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=os.getenv('POSTGRES_PORT', 5432),
    database=os.getenv('POSTGRES_DB', 'testdb'),
    user=os.getenv('POSTGRES_USER', 'testuser'),
    password=os.getenv('POSTGRES_PASSWORD', 'testpass')
)

with conn.cursor() as cursor:
    # Общая статистика пользователей
    cursor.execute('SELECT COUNT(*) FROM users')
    users_count = cursor.fetchone()[0]
    print(f'👥 Всего пользователей: {users_count}')
    
    # Активные источники данных
    cursor.execute('''
        SELECT source_type, 
               COUNT(*) as total,
               COUNT(CASE WHEN is_enabled_semantic_search THEN 1 END) as enabled_search,
               COUNT(CASE WHEN is_enabled_architecture_generation THEN 1 END) as enabled_arch
        FROM user_data_sources 
        GROUP BY source_type
    ''')
    
    print('🔗 Источники данных:')
    for source_type, total, enabled_search, enabled_arch in cursor.fetchall():
        print(f'  {source_type}: {total} всего | поиск: {enabled_search} | архитектура: {enabled_arch}')
    
    # Конфигурации подключений
    cursor.execute('SELECT COUNT(*) FROM user_jira_configs')
    jira_configs = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM user_confluence_configs')
    confluence_configs = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM user_gitlab_configs')
    gitlab_configs = cursor.fetchone()[0]
    
    print('⚙️ Конфигурации подключений:')
    print(f'  Jira: {jira_configs}')
    print(f'  Confluence: {confluence_configs}')
    print(f'  GitLab: {gitlab_configs}')
    
    # Загруженные файлы
    cursor.execute('SELECT COUNT(*), SUM(file_size) FROM user_files')
    files_count, total_size = cursor.fetchone()
    total_size_mb = (total_size or 0) / (1024 * 1024)
    print(f'📁 Загруженных файлов: {files_count} ({total_size_mb:.1f} MB)')
    
    # Задачи синхронизации
    cursor.execute('''
        SELECT status, COUNT(*) 
        FROM sync_tasks 
        GROUP BY status
    ''')
    
    print('🔄 Задачи синхронизации:')
    for status, count in cursor.fetchall():
        print(f'  {status}: {count}')

conn.close()
"
	@echo "✅ Статистика готова"

# =============================================================================
# ПОЛНАЯ ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ
# =============================================================================

.PHONY: init-full-system
init-full-system: up setup-user-system train-model ## Полная инициализация системы
	@echo "🚀 Полная система инициализирована и готова к работе!"
	@echo ""
	@echo "📋 Доступные команды:"
	@echo "  make e2e-full-pipeline    - Полный E2E пайплайн"
	@echo "  make test-feedback        - Тестирование обратной связи"  
	@echo "  make check-model-quality  - Проверка качества модели"
	@echo "  make simulate-user-feedback - Симуляция обратной связи"
	@echo "  make retrain-model        - Переобучение модели"
	@echo "  make test-user-sync       - Тестирование синхронизации пользователя"
	@echo "  make show-user-stats      - Статистика пользователей"

.PHONY: docker-up-clean
docker-up-clean: ## Запуск Docker с очисткой данных
	@echo "🐳 Запуск Docker с очисткой..."
	docker-compose down -v
	docker-compose up -d
	@echo "⏳ Ожидание готовности сервисов (3 минуты)..."
	sleep 180
	@echo "✅ Docker сервисы готовы"
# User Management Commands
create-user-schema:
	docker-compose exec -T postgres psql -U testuser -d testdb < user_config_schema.sql

