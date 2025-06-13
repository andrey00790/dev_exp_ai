# 🧪 Требования к тестированию (Мультиязычная поддержка)

## 🌐 Мультиязычная система

Система теперь поддерживает **русский** и **английский** языки с полным набором тестов для каждого языка.

### Поддерживаемые языки
- **Русский (ru)**: 120+ тестовых кейсов семантического поиска + 30 RFC сценариев
- **Английский (en)**: 120+ тестовых кейсов семантического поиска + 30 RFC сценариев
- **Смешанный режим (all)**: 240+ кейсов семантического поиска + 60 RFC сценариев

## Общие требования

### Инструменты тестирования
- **Основной фреймворк**: `pytest`
- **Покрытие кода**: `pytest-cov` (опционально)
- **Асинхронное тестирование**: `pytest-asyncio`

### Команды запуска
```bash
# Полный запуск тестов
pytest -v

# Быстрый запуск с остановкой на первой ошибке
pytest --maxfail=1 --disable-warnings -q

# Запуск с покрытием кода
pytest --cov=. --cov-report=html
```

### Минимальные требования
- **Покрытие кода**: ≥ 80%
- **Мокирование внешних источников**: Все внешние API (GitLab, Confluence) должны быть замокированы
- **Покрытие cron скриптов**: Все скрипты в `core/cron/` покрываются unit/integration тестами

## 🔍 Семантический поиск (Мультиязычный)

### Автоматическая оценка качества

#### Скрипт оценки
```bash
# Русский язык
python3 evaluate_semantic_search.py --testset tests/semantic_search_eval.yml --language ru

# Английский язык  
python3 evaluate_semantic_search.py --testset tests/semantic_search_eval.yml --language en

# Все языки одновременно
python3 evaluate_semantic_search.py --testset tests/semantic_search_eval.yml --language all
```

#### Метрики качества
1. **Cosine Similarity** - между embeddings запроса и найденных документов
2. **Precision@k** - точность поиска для k=1,3,5 результатов
3. **MRR (Mean Reciprocal Rank)** - средний обратный ранг первого релевантного результата

#### Процесс оценки (мультиязычный)
```yaml
# Структура тестового набора
query: "OAuth 2.0 authentication implementation REST API"
expected_documents: 
  - "oauth2_guide.md"
  - "rest_auth.md" 
  - "jwt_tokens.md"
relevance_scores: [1.0, 0.9, 0.8]
language: "en"  # Новое поле для языка
```

#### Логирование результатов
- Автоматическое логирование Precision по всем тестовым кейсам
- **Языковая разбивка**: Russian (30 queries), English (105 queries)
- Разбивка по ролям (Developer, Architect, QA/SDET, DevOps/SRE, etc.) с указанием языков
- Сохранение результатов в JSON для анализа трендов

### Тестовые наборы (Обновлено v2.0)

#### Структура данных
- **Файл**: `tests/semantic_search_eval.yml`
- **Общий объем**: 240+ тестовых кейсов
- **Языки**: ru (русский), en (английский)
- **Роли**: 8 ролей по 30 кейсов каждая (15 рус + 15 англ)

#### Покрытие ролей (Мультиязычное)
1. **Developer / Разработчик** (30 кейсов)
   - API design, authentication, caching / Дизайн API, аутентификация, кеширование
   - Local storage, SSR, offline-first / Локальное хранилище, SSR, офлайн-приложения
   - CI/CD, мобильная разработка / CI/CD, mobile development

2. **System/Business Analyst / Системный/Бизнес Аналитик** (30 кейсов)
   - User stories, stakeholder analysis / Пользовательские истории, анализ стейкхолдеров
   - ROI calculation, gap analysis / Расчет ROI, gap анализ
   - Requirements engineering / Инжиниринг требований

3. **System Architect / Системный Архитектор** (30 кейсов)
   - Micropatterns (Circuit Breaker, CQRS) / Микропаттерны
   - Availability, scalability patterns / Доступность, масштабируемость
   - Distributed systems design / Дизайн распределенных систем

4. **Business Architect / Бизнес Архитектор** (30 кейсов)
   - Capability mapping, domain modeling / Картирование способностей, моделирование доменов
   - Data ownership, governance / Владение данными, управление
   - Enterprise architecture frameworks / Фреймворки корпоративной архитектуры

5. **QA/SDET** (30 кейсов)
   - API testing automation / Автоматизация тестирования API
   - Chaos testing, negative testing / Хаос-тестирование, негативное тестирование
   - Performance and security testing / Тестирование производительности и безопасности

6. **DevOps/SRE/Security / DevOps/SRE/Безопасность** (30 кейсов)
   - SLIs/SLOs, error budgets / SLI/SLO, бюджеты ошибок
   - Incident response, Vault secrets / Реагирование на инциденты, управление секретами
   - RBAC, K8s security, CI/CD / RBAC, безопасность K8s, CI/CD

7. **Product Manager / Продакт Менеджер** (30 кейсов)
   - Product roadmaps, feature prioritization / Продуктовые дорожные карты, приоритизация
   - A/B testing, user feedback analysis / A/B тестирование, анализ отзывов
   - Go-to-market strategies / Go-to-market стратегии

8. **Quality Engineer / Инженер Качества** (30 кейсов)
   - Test automation frameworks / Фреймворки автоматизации тестирования
   - Quality metrics, risk-based testing / Метрики качества, риск-ориентированное тестирование
   - Test case design techniques / Техники дизайна тестовых случаев

## 🏗️ Генерация архитектуры (RFC) - Мультиязычная

### Валидация документов

#### Скрипт валидации
```bash
# Русский RFC
python3 validate_rfc.py --rfc path/to/rfc.md --template tests/rfc_generation_eval.yml --case-id sd_001_ru

# Английский RFC
python3 validate_rfc.py --rfc path/to/rfc.md --template tests/rfc_generation_eval.yml --case-id sd_001_en
```

#### Критерии проверки (Языково-специфичные)

##### 1. YAML Header
- **Обязательность**: Наличие YAML заголовка
- **Обязательные поля**: 
  - `title`, `author`, `status`, `created`, `rfc_number`
- **Новое поле**: `language` (ru/en) - опционально, но рекомендовано
- **Валидация статуса**: draft, proposed, accepted, rejected, superseded
- **Формат даты**: ISO 8601

##### 2. Структурная полнота (По языкам)
- **Минимальный порог**: ≥ 90% обязательных секций
- **Языково-специфичные секции**: 
  - EN: "Problem Statement", "Requirements", "Architecture"
  - RU: "Постановка задачи", "Требования", "Архитектура"
- **Проверка содержания**: Каждая секция должна иметь контент
- **Соответствие шаблону**: По типу архитектуры и языку

##### 3. Качество Markdown (Языковые проверки)
- **Синтаксис**: Валидация разметки
- **Ссылки**: Проверка внутренних ссылок
- **Код блоки**: Указание языка программирования
- **Русская типографика**: Рекомендации по многоточию (… vs ...)
- **Структура**: Заголовки с контентом

##### 4. Техническая глубина (Мультиязычные термины)
- **Оценка контента**: Анализ технических терминов на русском и английском
- **Русские термины**: архитектура, безопасность, мониторинг, производительность
- **English terms**: architecture, security, monitoring, performance
- **Соответствие сложности**: Адаптация под уровень (low/medium/high)
- **Минимальный объем**: ≥ 2000 слов для полной оценки

### Тестовые сценарии (Обновлено v2.0)

#### Файл тестов
- **Путь**: `tests/rfc_generation_eval.yml`
- **Количество кейсов**: 60 тестовых сценариев (30 рус + 30 англ)

#### Категории архитектур (Мультиязычные)

##### System Design (20 кейсов: 10 рус + 10 англ)
- TinyURL / Дизайн TinyURL, CDN / Глобальная архитектура CDN
- Real-time Chat / Система чата реального времени
- Instagram Feed / Лента фотографий Instagram
- Payment Systems / Система обработки платежей
- Video Streaming / Платформа видеостриминга

##### Microservices & Patterns (20 кейсов: 10 рус + 10 англ)
- E-commerce Microservices / Микросервисы электронной коммерции
- CQRS + Event Sourcing / CQRS Event Sourcing для банкинга
- Saga Pattern / Saga для распределенных транзакций
- Circuit Breaker / Circuit Breaker для устойчивости
- API Gateway / API Gateway с ограничением скорости

##### Infrastructure & DevOps (20 кейсов: 10 рус + 10 англ)
- Kubernetes Production / Продакшн кластер Kubernetes
- GitOps CI/CD Pipeline / GitOps CI/CD пайплайн  
- Terraform IaC / Terraform инфраструктура как код
- Observability Platform / Наблюдаемость Prometheus Grafana
- Zero-Trust Security / Zero-Trust сетевая безопасность

#### Соглашения по именованию
```yaml
# Русские кейсы
case_id: "sd_001_ru", "ms_001_ru", "infra_001_ru"
language: "ru"

# Английские кейсы  
case_id: "sd_001_en", "ms_001_en", "infra_001_en"
language: "en"
```

## 🧪 E2E Интеграционные тесты

### Локальные инстансы сервисов

Полноценная E2E тестовая среда с реальными локальными инстансами:

#### Архитектура E2E среды
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

#### Сервисы и порты
| Сервис | Порт | Credentials | Назначение |
|--------|------|-------------|------------|
| **Jira** | 8080 | admin/admin | Управление задачами |
| **Confluence** | 8090 | admin/admin | База знаний |
| **GitLab** | 8088 | root/testpassword123 | Репозитории кода |
| **Elasticsearch** | 9200 | - | Семантический поиск |
| **Redis** | 6379 | - | Кеширование |
| **PostgreSQL** | 5432 | atlassian/atlassian | База данных |

### Быстрый старт E2E

```bash
# Переход в E2E директорию
cd tests/e2e

# Установка зависимостей
make setup

# Запуск всех сервисов (займет 5-10 минут)
make start

# Загрузка тестовых данных
make load-data

# Запуск E2E тестов
make test
```

### Типы E2E тестов

#### 1. Интеграционные тесты по сервисам
```bash
# Jira интеграция
pytest -k "jira" -v

# Confluence интеграция  
pytest -k "confluence" -v

# GitLab интеграция
pytest -k "gitlab" -v

# Elasticsearch интеграция
pytest -k "elasticsearch" -v
```

#### 2. Многоязычные тесты
```bash
# Тесты русскоязычной функциональности
pytest -k "russian" -v

# Тесты многоязычного поиска
pytest -k "multilingual" -v

# Кросс-языковые сценарии
pytest -k "cross_language" -v
```

#### 3. Кросс-системные тесты
```bash
# Интеграция между системами
pytest -k "cross_system" -v

# End-to-end workflows
pytest test_integration.py::TestCrossSystemIntegration -v
```

### Автоматическое наполнение тестовыми данными

#### Jira тестовые данные
- **Проекты**: TEST, API
- **Задачи** (мультиязычные):
  - "Реализация OAuth 2.0 аутентификации" (русский)
  - "API rate limiting implementation" (английский)
  - "Микросервисы архитектура документация" (русский)

#### Confluence тестовые данные
- **Пространство**: TESTSPACE
- **Страницы** (мультиязычные):
  - "OAuth 2.0 Authentication Guide" (английский)
  - "Руководство по API Gateway" (русский)
  - "Microservices Architecture Patterns" (английский)

#### GitLab тестовые данные
- **Проекты**: api-gateway, auth-service
- **Файлы**: README.md, docs/ с мультиязычным контентом
- **Коммиты**: Реалистичная история изменений

#### Elasticsearch индексы
- **Индекс**: test_documents
- **Документы**: Проиндексированные страницы с метаданными:
  - language: "ru" / "en"
  - source: "jira" / "confluence" / "gitlab"
  - tags: ["oauth", "api-gateway", "microservices"]

### E2E сценарии тестирования

#### Сценарий 1: Семантический поиск между системами
```python
def test_cross_system_semantic_search():
    # 1. Поиск в Elasticsearch
    es_results = es.search(query="OAuth authentication")
    
    # 2. Поиск связанных задач в Jira
    jira_issues = jira.search_issues('summary ~ "OAuth"')
    
    # 3. Поиск документации в Confluence
    confluence_pages = confluence.search_content("OAuth 2.0")
    
    # 4. Проверка релевантности результатов
    assert all_results_relevant(es_results, jira_issues, confluence_pages)
```

#### Сценарий 2: Многоязычный workflow
```python
def test_multilingual_workflow():
    # 1. Создание задачи на русском в Jira
    issue = jira.create_issue({
        "summary": "Реализация аутентификации",
        "description": "Техническое задание на русском языке"
    })
    
    # 2. Создание документации в Confluence
    page = confluence.create_page(
        title="Техническая спецификация",
        body="<p>Описание на русском языке</p>"
    )
    
    # 3. Автоматическая индексация в Elasticsearch
    verify_document_indexed(page.title, language="ru")
    
    # 4. Семантический поиск на русском языке
    results = semantic_search("техническая спецификация аутентификация")
    assert len(results) > 0
```

#### Сценарий 3: Синхронизация данных
```python
async def test_data_synchronization():
    # 1. Создание контента в GitLab
    project = gitlab.projects.create({"name": "new-service"})
    project.files.create({
        "file_path": "README.md",
        "content": "# New Service\nRussian: Новый сервис",
        "commit_message": "Initial commit"
    })
    
    # 2. Имитация синхронизации
    sync_gitlab_to_elasticsearch(project)
    
    # 3. Проверка доступности в поиске
    await asyncio.sleep(2)  # Время индексации
    results = search_documents("new service новый сервис")
    assert len(results) > 0
```

### Управление E2E средой

#### Docker Compose управление
```bash
# Запуск конкретных сервисов
docker-compose up -d postgres elasticsearch redis

# Только Atlassian сервисы
docker-compose up -d jira confluence

# Просмотр логов
docker-compose logs -f jira
make logs-confluence

# Отладка контейнеров
make debug-jira
make debug-postgres
```

#### Управление данными
```bash
# Создание бэкапа
make backup-data

# Восстановление из бэкапа
make restore-data BACKUP=postgres_backup_20241201.sql

# Очистка всех данных
make clean
```

#### Мониторинг ресурсов
```bash
# Статус всех сервисов
make status

# Использование ресурсов
make monitor

# Проверка здоровья сервисов
curl http://localhost:8080/status  # Jira
curl http://localhost:9200/_cluster/health  # Elasticsearch
```

### CI/CD интеграция E2E

#### GitHub Actions пример
```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Run E2E Tests
        run: |
          cd tests/e2e
          make ci-test
          
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: e2e-results
          path: tests/e2e/e2e-results.xml
```

#### Jenkins Pipeline пример
```groovy
pipeline {
    agent any
    stages {
        stage('E2E Tests') {
            steps {
                script {
                    dir('tests/e2e') {
                        sh 'make ci-test'
                    }
                }
            }
            post {
                always {
                    publishTestResults testResultsPattern: 'tests/e2e/e2e-results.xml'
                }
            }
        }
    }
    post {
        always {
            sh 'cd tests/e2e && make clean'
        }
    }
}
```

### Требования к E2E среде

#### Системные требования
- **RAM**: 8GB+ рекомендуется
- **CPU**: 4+ cores
- **Диск**: 20GB+ свободного места
- **Docker**: 20.10+ с Compose v2
- **Время**: Первый запуск ~15 минут, последующие ~5-8 минут

#### Оптимизация производительности
```bash
# Только инфраструктурные сервисы для разработки
make dev-start

# Быстрые тесты без полного перезапуска
make test-quick

# Параллельный запуск тестов
pytest -n auto test_integration.py
```

## 📊 Автоматизация и мониторинг (Мультиязычный)

### CI/CD интеграция
```bash
# В pipeline
pytest tests/ --cov=. --cov-fail-under=80

# Русские тесты
python3 evaluate_semantic_search.py --testset tests/semantic_search_eval.yml --language ru
python3 validate_rfc.py --rfc generated_rfc_ru.md --template tests/rfc_generation_eval.yml --case-id sd_001_ru

# Английские тесты
python3 evaluate_semantic_search.py --testset tests/semantic_search_eval.yml --language en  
python3 validate_rfc.py --rfc generated_rfc_en.md --template tests/rfc_generation_eval.yml --case-id sd_001_en

# Комплексная оценка
python3 evaluate_semantic_search.py --testset tests/semantic_search_eval.yml --language all

# E2E тесты
cd tests/e2e && make ci-test
```

### Метрики качества (По языкам)
- **Precision@3 threshold**: ≥ 70% (для каждого языка отдельно)
- **MRR threshold**: ≥ 60% (для каждого языка отдельно)
- **RFC validation**: ≥ 90% секций + техническая глубина ≥ 60%
- **Code coverage**: ≥ 80%
- **E2E tests pass rate**: ≥ 95%

### Отчетность (Мультиязычная)
- JSON результаты с timestamp и языковой разбивкой
- Language breakdown: Russian vs English метрики
- Breakdown по ролям и категориям с указанием языков
- Trending analysis по языкам
- Alert при падении метрик ниже threshold для любого языка
- E2E JUnit XML отчеты для CI/CD

### Примеры вывода
```bash
# Языковая статистика
LANGUAGE BREAKDOWN:
Russian (30 queries):
  P@1: 0.0000, P@3: 0.0000, MRR: 0.0000, Cosine Sim: 0.7501
English (105 queries):  
  P@1: 0.0000, P@3: 0.0000, MRR: 0.0000, Cosine Sim: 0.7477

# RFC валидация с флагами
RFC VALIDATION: document.md 🇷🇺
Case ID: sd_001_ru | Language: Russian

RFC VALIDATION: document.md 🇺🇸  
Case ID: sd_001_en | Language: English

# E2E тесты статус
✅ Jira Integration: 15/15 tests passed
✅ Confluence Integration: 12/12 tests passed  
✅ GitLab Integration: 8/8 tests passed
✅ Cross-System Integration: 5/5 tests passed
```

### Непрерывное улучшение
- Еженедельный review метрик по языкам
- Обновление тестовых наборов для каждого языка
- Адаптация threshold под бизнес-требования
- A/B тестирование новых алгоритмов поиска на мультиязычных данных
- Сравнительный анализ качества по языкам
- Регулярное обновление E2E тестовых данных
- Мониторинг производительности E2E среды 