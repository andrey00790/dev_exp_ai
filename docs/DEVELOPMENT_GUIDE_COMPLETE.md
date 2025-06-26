# 🚀 AI Assistant - Полное руководство разработчика

## 📋 Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Локальная разработка](#локальная-разработка)
3. [Тестирование](#тестирование)
4. [Отладка](#отладка)
5. [Docker-деплой](#docker-деплой)
6. [Продакшн деплой](#продакшн-деплой)
7. [Архитектура](#архитектура)
8. [Troubleshooting](#troubleshooting)

## 🏃‍♂️ Быстрый старт

### Предварительные требования
```bash
# Python 3.11+
python3 --version

# Docker и Docker Compose
docker --version
docker-compose --version

# Git
git --version
```

### Клонирование и настройка
```bash
# Клонирование репозитория
git clone <repository-url>
cd dev_exp_ai

# Установка зависимостей
pip3 install -r requirements.txt

# Создание .env файла
cp config/production.env .env
# Отредактируйте .env под ваши нужды
```

## 🛠 Локальная разработка

### Структура проекта
```
dev_exp_ai/
├── app/                    # Основное приложение
│   ├── api/v1/            # API endpoints
│   ├── models/            # Модели данных
│   ├── services/          # Бизнес-логика
│   ├── security/          # Аутентификация и безопасность
│   └── monitoring/        # Мониторинг и метрики
├── frontend/              # React фронтенд
├── tests/                 # Тесты
├── docs/                  # Документация
├── deployment/            # Docker и деплой конфигурации
└── scripts/               # Утилитарные скрипты
```

### Запуск локально (без Docker)

#### 1. Подготовка окружения
```bash
# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt
```

#### 2. Настройка переменных окружения
```bash
# Создание .env файла
cat > .env << EOF
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_assistant
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# LLM Providers
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Vector Database
QDRANT_URL=http://localhost:6333

# Monitoring
ENABLE_MONITORING=true
ENABLE_APM=false  # Для локальной разработки

# Debug
DEBUG=true
LOG_LEVEL=INFO
EOF
```

#### 3. Запуск сервисов
```bash
# Запуск PostgreSQL (через Docker)
docker run -d --name postgres \
  -e POSTGRES_DB=ai_assistant \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 postgres:15

# Запуск Redis
docker run -d --name redis -p 6379:6379 redis:7

# Запуск Qdrant
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant

# Запуск приложения
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. Запуск фронтенда
```bash
cd frontend
npm install
npm run dev
```

### Полезные команды для разработки

```bash
# Быстрая проверка системы
python3 debug_helper.py

# Быстрое тестирование основных компонентов
python3 quick_test.py

# Запуск AI Assistant CLI
python3 ai_assistant_cli.py

# Форматирование кода
black app/ tests/
isort app/ tests/

# Проверка типов
mypy app/

# Линтинг
flake8 app/ tests/
```

## 🧪 Тестирование

### Структура тестов
```
tests/
├── unit/              # Юнит тесты
├── integration/       # Интеграционные тесты
├── e2e/              # End-to-end тесты
├── performance/       # Тесты производительности
└── conftest.py       # Общие фикстуры
```

### Запуск тестов

#### Все тесты
```bash
# Запуск всех тестов
python3 -m pytest tests/

# С покрытием кода
python3 -m pytest tests/ --cov=app --cov-report=html

# Только быстрые тесты
python3 -m pytest tests/unit/ -v

# Параллельный запуск
python3 -m pytest tests/ -n auto
```

#### Специфические тесты
```bash
# Только API тесты
python3 -m pytest tests/unit/test_api* -v

# Только интеграционные тесты
python3 -m pytest tests/integration/ -v

# Конкретный тест
python3 -m pytest tests/unit/test_api_users.py::TestUsersAPIFinal::test_create_user_endpoint -v

# С отладочной информацией
python3 -m pytest tests/unit/test_api_users.py -v -s --tb=long
```

#### Тестирование с Docker
```bash
# Запуск тестов в Docker
make test-docker

# Интеграционные тесты с реальными сервисами
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

### Создание новых тестов

#### Юнит тест
```python
# tests/unit/test_my_feature.py
import pytest
from unittest.mock import Mock, AsyncMock

from app.services.my_service import MyService

class TestMyService:
    @pytest.fixture
    def service(self):
        return MyService()
    
    async def test_my_method(self, service):
        # Arrange
        expected_result = "test"
        
        # Act
        result = await service.my_method("input")
        
        # Assert
        assert result == expected_result
```

#### Интеграционный тест
```python
# tests/integration/test_my_integration.py
import pytest
from fastapi.testclient import TestClient

from tests.conftest import create_test_app

@pytest.mark.integration
class TestMyIntegration:
    @pytest.fixture
    def client(self):
        app = create_test_app()
        return TestClient(app)
    
    def test_api_integration(self, client):
        response = client.post("/api/v1/my-endpoint", json={"test": "data"})
        assert response.status_code == 200
```

## 🐛 Отладка

### Инструменты отладки

#### 1. Debug Helper
```bash
# Диагностика системы
python3 debug_helper.py

# Проверка конкретного компонента
python3 debug_helper.py --component search
python3 debug_helper.py --component llm
python3 debug_helper.py --component auth
```

#### 2. Логирование
```python
# Настройка логирования в коде
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Добавление отладочных логов
logger.debug("Debug message with data: %s", data)
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)
```

#### 3. Профилирование
```bash
# Профилирование производительности
python3 -m cProfile -o profile.stats app/main.py

# Анализ профиля
python3 -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)
"
```

#### 4. Отладка в IDE

**VSCode launch.json:**
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI Debug",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "app.main:app",
                "--reload",
                "--host", "0.0.0.0",
                "--port", "8000"
            ],
            "env": {
                "DEBUG": "true"
            },
            "console": "integratedTerminal"
        },
        {
            "name": "Debug Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": [
                "tests/unit/test_api_users.py",
                "-v", "-s"
            ],
            "console": "integratedTerminal"
        }
    ]
}
```

### Частые проблемы и решения

#### 1. Проблемы с импортами
```bash
# Проверка Python path
python3 -c "import sys; print('\n'.join(sys.path))"

# Добавление текущей директории в PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 2. Проблемы с базой данных
```bash
# Проверка подключения к БД
python3 -c "
from app.database.session import get_db
try:
    next(get_db())
    print('✅ Database connection OK')
except Exception as e:
    print(f'❌ Database error: {e}')
"
```

#### 3. Проблемы с зависимостями
```bash
# Проверка установленных пакетов
pip list | grep -E "(fastapi|uvicorn|sqlalchemy|redis|openai)"

# Переустановка зависимостей
pip install --force-reinstall -r requirements.txt
```

## 🐳 Docker-деплой

### Локальный Docker-деплой

#### 1. Простой запуск
```bash
# Сборка и запуск всех сервисов
./docker-commands.sh start

# Или через make
make docker-up

# Проверка статуса
docker-compose ps
```

#### 2. Сервисы
```yaml
# docker-compose.local.yml
services:
  ai-assistant:    # Основное приложение (порт 8000)
  postgres:        # База данных (порт 5432)
  redis:          # Кэш (порт 6379)
  adminer:        # Веб-интерфейс БД (порт 8080)
  redis-commander: # Веб-интерфейс Redis (порт 8081)
```

#### 3. Полезные команды
```bash
# Просмотр логов
docker-compose logs -f ai-assistant
docker-compose logs -f postgres

# Подключение к контейнеру
docker-compose exec ai-assistant bash
docker-compose exec postgres psql -U postgres -d ai_assistant

# Перезапуск сервиса
docker-compose restart ai-assistant

# Остановка и очистка
./docker-commands.sh stop
./docker-commands.sh clean
```

#### 4. Отладка в Docker
```bash
# Запуск в режиме отладки
docker-compose -f docker-compose.dev.yml up

# Подключение отладчика
docker-compose exec ai-assistant python -m pdb app/main.py

# Мониторинг ресурсов
docker stats
```

### Production Docker

#### 1. Оптимизированная сборка
```bash
# Сборка production образа
docker build -f Dockerfile.prod -t ai-assistant:prod .

# Многоэтапная сборка с оптимизациями
docker build --target production -t ai-assistant:prod .
```

#### 2. Docker Compose для продакшна
```bash
# Запуск в продакшн режиме
docker-compose -f docker-compose.prod.yml up -d

# С мониторингом
docker-compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml up -d
```

## 🚀 Продакшн деплой

### AWS ECS Deployment

#### 1. Подготовка инфраструктуры
```bash
# Terraform для создания инфраструктуры
cd terraform/
terraform init
terraform plan
terraform apply
```

#### 2. Сборка и публикация образа
```bash
# Логин в ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

# Сборка и пуш
docker build -t ai-assistant:latest .
docker tag ai-assistant:latest <account>.dkr.ecr.us-east-1.amazonaws.com/ai-assistant:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/ai-assistant:latest
```

#### 3. Деплой через ECS
```bash
# Обновление сервиса
aws ecs update-service --cluster ai-assistant-cluster --service ai-assistant-service --force-new-deployment

# Мониторинг деплоя
aws ecs describe-services --cluster ai-assistant-cluster --services ai-assistant-service
```

### Kubernetes Deployment

#### 1. Helm Chart
```bash
# Установка через Helm
helm install ai-assistant ./deployment/helm/ai-assistant/ \
  --set image.tag=latest \
  --set ingress.enabled=true \
  --set monitoring.enabled=true
```

#### 2. Kubectl команды
```bash
# Применение манифестов
kubectl apply -f deployment/k8s/

# Проверка статуса
kubectl get pods -l app=ai-assistant
kubectl get services
kubectl get ingress

# Логи
kubectl logs -f deployment/ai-assistant
```

### CI/CD Pipeline

#### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          python -m pytest tests/
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster prod --service ai-assistant --force-new-deployment
```

### Мониторинг продакшна

#### 1. Метрики и алерты
```bash
# Prometheus метрики
curl http://localhost:8000/metrics

# Grafana дашборды
open http://localhost:3000

# Алерты в Slack/Email
# Настраиваются через Alertmanager
```

#### 2. Логирование
```bash
# Централизованные логи через ELK
# Логи в JSON формате для структурированного анализа

# Проверка логов
kubectl logs -f deployment/ai-assistant | jq .
```

#### 3. Трейсинг
```bash
# Jaeger для распределенного трейсинга
open http://localhost:16686

# APM метрики
# Настроено через OpenTelemetry
```

## 🏗 Архитектура

### Компоненты системы

```mermaid
graph TD
    A[Frontend React] --> B[API Gateway]
    B --> C[Authentication Service]
    B --> D[Search Service]
    B --> E[LLM Service]
    B --> F[Vector Search Service]
    
    C --> G[PostgreSQL]
    D --> G
    D --> H[Qdrant Vector DB]
    E --> I[OpenAI/Anthropic APIs]
    F --> H
    
    J[Redis Cache] --> D
    J --> E
    
    K[Monitoring] --> L[Prometheus]
    K --> M[Grafana]
    K --> N[Jaeger]
```

### Основные сервисы

1. **API Layer** (`app/api/v1/`)
   - Аутентификация и авторизация
   - Семантический поиск
   - Генерация RFC/документации
   - Управление данными

2. **Business Logic** (`app/services/`)
   - LLM интеграции
   - Векторный поиск
   - Обработка документов
   - Аналитика

3. **Data Layer** (`app/models/`)
   - PostgreSQL для структурированных данных
   - Qdrant для векторного поиска
   - Redis для кэширования

4. **Security** (`app/security/`)
   - JWT аутентификация
   - Валидация входных данных
   - Контроль бюджета
   - Rate limiting

## 🔧 Troubleshooting

### Частые ошибки и решения

#### 1. "ModuleNotFoundError"
```bash
# Решение: добавить в PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Или установить в режиме разработки
pip install -e .
```

#### 2. "Database connection failed"
```bash
# Проверка статуса PostgreSQL
docker ps | grep postgres

# Проверка подключения
psql postgresql://postgres:password@localhost:5432/ai_assistant

# Пересоздание базы
docker-compose down -v
docker-compose up postgres
```

#### 3. "Redis connection failed"
```bash
# Проверка Redis
redis-cli ping

# Перезапуск Redis
docker restart redis
```

#### 4. "OpenAI API key not found"
```bash
# Проверка переменных окружения
echo $OPENAI_API_KEY

# Установка ключа
export OPENAI_API_KEY="your-key-here"
```

#### 5. "Tests failing"
```bash
# Очистка кэша pytest
rm -rf .pytest_cache/

# Запуск с отладкой
python -m pytest tests/unit/test_api_users.py -v -s --tb=long

# Проверка фикстур
python -m pytest --fixtures tests/
```

### Полезные команды диагностики

```bash
# Проверка системы
python3 debug_helper.py

# Проверка портов
netstat -tulpn | grep -E "(8000|5432|6379|6333)"

# Проверка Docker
docker system df
docker system prune

# Проверка логов
tail -f logs/app.log
journalctl -u ai-assistant -f

# Проверка производительности
htop
iotop
```

### Контакты для поддержки

- **GitHub Issues**: [Ссылка на репозиторий]
- **Документация**: `docs/`
- **Wiki**: [Ссылка на wiki]
- **Slack**: #ai-assistant-dev

---

## 📚 Дополнительные ресурсы

- [API Documentation](./API_DOCUMENTATION_COMPLETE.md)
- [Architecture Guide](./architecture/ARCHITECTURE.md)
- [Security Guide](./SECURITY_GUIDE.md)
- [Performance Guide](./PERFORMANCE_GUIDE.md)
- [Contributing Guide](./CONTRIBUTING.md)

---

*Последнее обновление: $(date)* 