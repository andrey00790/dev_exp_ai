# 🧪 E2E Интеграционные тесты

Полноценная E2E тестовая среда с локальными инстансами Jira, Confluence, GitLab, Elasticsearch и Redis.

## 🏗️ Архитектура E2E среды

```
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│     Jira        │   │   Confluence    │   │     GitLab      │
│   :8080         │   │     :8090       │   │     :8088       │
└─────────────────┘   └─────────────────┘   └─────────────────┘
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                │
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │     :5432       │
                    └─────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ Elasticsearch  │   │     Redis       │   │ Test Data       │
│    :9200        │   │     :6379       │   │    Loader       │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

## 🚀 Быстрый старт

### Требования
- Docker & Docker Compose
- Python 3.11+
- Make (опционально)
- 8GB+ RAM рекомендуется

### Установка и запуск
```bash
# Переход в директорию E2E тестов
cd tests/e2e

# Установка зависимостей
make setup

# Запуск всех сервисов
make start

# Загрузка тестовых данных
make load-data

# Запуск тестов
make test
```

## 📋 Доступные команды

### Основные команды
```bash
make start          # Запустить все сервисы
make stop           # Остановить сервисы  
make clean          # Полная очистка
make test           # Полные E2E тесты
make test-quick     # Быстрые тесты
make status         # Статус сервисов
```

### Специализированные тесты
```bash
make test-multilingual  # Тесты многоязычности
pytest -k "jira"       # Только Jira тесты
pytest -k "russian"    # Только русскоязычные тесты
pytest -k "cross"      # Кросс-системные тесты
```

### Управление данными
```bash
make load-data      # Загрузить тестовые данные
make backup-data    # Создать бэкап
make restore-data BACKUP=file.sql  # Восстановить данные
```

## 🌐 Доступ к сервисам

| Сервис | URL | Credentials |
|--------|-----|-------------|
| **Jira** | http://localhost:8080 | admin / admin |
| **Confluence** | http://localhost:8090 | admin / admin |
| **GitLab** | http://localhost:8088 | root / testpassword123 |
| **Elasticsearch** | http://localhost:9200 | - |
| **Redis** | redis://localhost:6379 | - |

## 📊 Тестовые данные

### Jira
- **Проекты**: TEST, API
- **Задачи**: 
  - Реализация OAuth 2.0 аутентификации (русский)
  - API rate limiting implementation (английский)
  - Микросервисы архитектура документация (русский)

### Confluence
- **Пространство**: TESTSPACE
- **Страницы**:
  - OAuth 2.0 Authentication Guide (английский)
  - Руководство по API Gateway (русский)
  - Microservices Architecture Patterns (английский)

### GitLab
- **Проекты**: api-gateway, auth-service
- **Файлы**: README.md, docs/architecture.md с мультиязычным контентом

### Elasticsearch
- **Индекс**: test_documents
- **Документы**: Проиндексированные страницы из Confluence с метаданными языка

## 🧪 Структура тестов

### TestJiraIntegration
- ✅ Подключение к Jira
- ✅ Создание и поиск проектов
- ✅ Поиск задач на русском языке
- ✅ Поиск задач на английском языке

### TestConfluenceIntegration  
- ✅ Подключение к Confluence
- ✅ Создание пространств
- ✅ Многоязычный поиск страниц
- ✅ Проверка русскоязычного контента

### TestGitLabIntegration
- ✅ Подключение к GitLab
- ✅ Создание проектов
- ✅ Проверка мультиязычных файлов

### TestElasticsearchIntegration
- ✅ Подключение к Elasticsearch
- ✅ Индексация документов
- ✅ Многоязычный семантический поиск

### TestCrossSystemIntegration
- ✅ Поиск между системами
- ✅ Асинхронная синхронизация данных
- ✅ End-to-end workflows

## 🔧 Конфигурация

### Docker Compose
- **Файл**: `docker-compose.yml`
- **Сети**: e2e_network (bridge)
- **Объемы**: Персистентные данные для каждого сервиса
- **Health checks**: Автоматическая проверка готовности сервисов

### Test Data Loader
- **Скрипт**: `test_data_loader.py`
- **Функции**: Автоматическое наполнение всех систем тестовыми данными
- **Многоязычность**: Создание контента на русском и английском языках

### Pytest Configuration
- **Маркеры**: e2e, multilingual, slow, performance
- **Timeouts**: 30 минут для длительных тестов
- **Логирование**: Детальные логи всех операций

## 💡 Советы по использованию

### Разработка
```bash
# Запуск только инфраструктуры (без Atlassian/GitLab)
make dev-start

# Отладка конкретного сервиса
make debug-jira
make logs-confluence

# Мониторинг ресурсов
make monitor
```

### CI/CD интеграция
```bash
# Команда для CI пайплайна
make ci-test

# Результаты в JUnit XML
pytest --junitxml=e2e-results.xml
```

### Troubleshooting
```bash
# Проверка статуса всех сервисов
make status

# Просмотр логов
make logs

# Полная переустановка
make clean && make start
```

## ⚡ Производительность

### Время запуска
- **Первый запуск**: ~10-15 минут (загрузка образов)
- **Последующие**: ~5-8 минут (готовность сервисов)
- **Только тесты**: ~2-3 минуты

### Использование ресурсов
- **RAM**: ~6-8GB для всех сервисов
- **CPU**: Пики при инициализации
- **Диск**: ~15GB для образов и данных

### Оптимизация
- Используйте `make dev-start` для разработки
- Запускайте `make test-quick` для быстрых итераций
- Сохраняйте состояние с `make backup-data`

## 🔍 Примеры тестовых сценариев

### Сценарий 1: Поиск документации по OAuth
```python
# Поиск в Confluence
pages = confluence.search_content("OAuth 2.0")

# Поиск связанных задач в Jira  
issues = jira.search_issues('summary ~ "OAuth"')

# Семантический поиск в Elasticsearch
es_results = es.search(index="test_documents", 
                      body={"query": {"match": {"content": "authentication"}}})
```

### Сценарий 2: Многоязычный workflow
```python
# Создание задачи на русском в Jira
issue = jira.create_issue({
    "summary": "Реализация аутентификации",
    "description": "Техническое задание на русском языке"
})

# Создание связанной документации в Confluence
page = confluence.create_page(
    title="Техническая спецификация",
    body="<p>Описание на русском языке</p>"
)

# Индексация в Elasticsearch с метаданными языка
es.index(index="documents", body={
    "title": "Техническая спецификация", 
    "language": "ru",
    "source": "confluence"
})
```

## 📈 Метрики и мониторинг

### Автоматические проверки
- Health checks всех сервисов
- Проверка доступности API
- Валидация тестовых данных
- Мониторинг производительности

### Reporting
- JUnit XML результаты для CI
- Детальные логи операций
- Метрики времени выполнения
- Coverage отчеты (опционально)

## 🛠️ Расширение тестов

### Добавление новых тестов
1. Создайте класс `TestNewIntegration`
2. Используйте фикстуры для клиентов
3. Добавьте соответствующие маркеры
4. Обновите тестовые данные при необходимости

### Добавление новых сервисов
1. Расширьте `docker-compose.yml`
2. Добавьте health checks
3. Обновите `test_data_loader.py`
4. Создайте фикстуры в `test_integration.py`

### Кастомизация данных
1. Модифицируйте `test_data_loader.py`
2. Добавьте файлы в `test-data/` директории
3. Обновите маппинги Elasticsearch
4. Создайте дополнительные бэкапы 