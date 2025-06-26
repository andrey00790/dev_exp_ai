# 🧪 AI Assistant - Руководство по тестированию

## 📋 Содержание

1. [Общие принципы](#общие-принципы)
2. [Структура тестов](#структура-тестов)
3. [Типы тестов](#типы-тестов)
4. [Запуск тестов](#запуск-тестов)
5. [Написание тестов](#написание-тестов)
6. [Отладка тестов](#отладка-тестов)
7. [CI/CD интеграция](#cicd-интеграция)

## 🎯 Общие принципы

### Пирамида тестирования
```
     🔺 E2E Tests (5-10%)
    🔺🔺 Integration Tests (20-30%)
   🔺🔺🔺 Unit Tests (60-70%)
```

### Правила написания тестов
1. **Fast** - Тесты должны выполняться быстро
2. **Independent** - Тесты не должны зависеть друг от друга
3. **Repeatable** - Результат должен быть предсказуемым
4. **Self-Validating** - Тест должен четко показывать успех/неудачу
5. **Timely** - Тесты пишутся вместе с кодом

## 📁 Структура тестов

```
tests/
├── conftest.py                 # Общие фикстуры и конфигурация
├── unit/                       # Юнит тесты (60-70%)
│   ├── test_api_users.py      # Тесты API endpoints
│   ├── test_search_service.py # Тесты бизнес-логики
│   ├── test_auth.py           # Тесты аутентификации
│   └── test_models.py         # Тесты моделей данных
├── integration/                # Интеграционные тесты (20-30%)
│   ├── test_api_v1.py         # Тесты API интеграции
│   ├── test_database.py       # Тесты работы с БД
│   └── test_external_apis.py  # Тесты внешних API
├── e2e/                        # End-to-end тесты (5-10%)
│   ├── test_user_journey.py   # Полные пользовательские сценарии
│   └── test_workflows.py      # Бизнес-процессы
├── performance/                # Тесты производительности
│   ├── test_load.py           # Нагрузочные тесты
│   └── test_stress.py         # Стресс-тесты
└── fixtures/                   # Тестовые данные
    ├── sample_documents.json
    └── mock_responses.json
```

## 🔬 Типы тестов

### 1. Юнит тесты

**Что тестируем:**
- Отдельные функции и методы
- Бизнес-логику сервисов
- Валидацию данных
- Обработку ошибок

**Пример:**
```python
# tests/unit/test_search_service.py
import pytest
from unittest.mock import Mock, AsyncMock

from app.services.search_service import SearchService

class TestSearchService:
    @pytest.fixture
    def search_service(self):
        return SearchService()
    
    @pytest.fixture
    def mock_vector_db(self):
        mock = Mock()
        mock.search = AsyncMock(return_value=[
            {"id": "doc1", "score": 0.95, "content": "test content"}
        ])
        return mock
    
    async def test_semantic_search_success(self, search_service, mock_vector_db):
        # Arrange
        search_service.vector_db = mock_vector_db
        query = "test query"
        
        # Act
        results = await search_service.semantic_search(query)
        
        # Assert
        assert len(results) == 1
        assert results[0]["score"] > 0.9
        mock_vector_db.search.assert_called_once_with(query)
    
    async def test_search_with_invalid_query(self, search_service):
        # Arrange
        empty_query = ""
        
        # Act & Assert
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await search_service.semantic_search(empty_query)
```

### 2. Интеграционные тесты

**Что тестируем:**
- Взаимодействие между компонентами
- Работу с базой данных
- API endpoints с реальными зависимостями
- Внешние интеграции

**Пример:**
```python
# tests/integration/test_api_v1.py
import pytest
from fastapi.testclient import TestClient

from tests.conftest import create_test_app

@pytest.mark.integration
class TestSearchAPI:
    @pytest.fixture
    def client(self):
        app = create_test_app()
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer test-token"}
    
    def test_search_endpoint_integration(self, client, auth_headers):
        # Arrange
        search_request = {
            "query": "authentication best practices",
            "sources": ["confluence_main"],
            "limit": 5
        }
        
        # Act
        response = client.post(
            "/api/v1/search/", 
            json=search_request,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total_results" in data
        assert isinstance(data["results"], list)
    
    def test_search_with_database(self, client, auth_headers, test_db):
        # Тест с реальной базой данных
        # Предварительно заполняем тестовыми данными
        pass
```

### 3. End-to-End тесты

**Что тестируем:**
- Полные пользовательские сценарии
- Интеграцию фронтенда и бэкенда
- Критические бизнес-процессы

**Пример:**
```python
# tests/e2e/test_user_journey.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By

@pytest.mark.e2e
class TestUserJourney:
    @pytest.fixture
    def driver(self):
        driver = webdriver.Chrome()
        yield driver
        driver.quit()
    
    def test_complete_search_workflow(self, driver):
        # 1. Открытие приложения
        driver.get("http://localhost:3000")
        
        # 2. Логин
        login_button = driver.find_element(By.ID, "login-button")
        login_button.click()
        
        # 3. Поиск
        search_input = driver.find_element(By.ID, "search-input")
        search_input.send_keys("API documentation")
        
        search_button = driver.find_element(By.ID, "search-button")
        search_button.click()
        
        # 4. Проверка результатов
        results = driver.find_elements(By.CLASS_NAME, "search-result")
        assert len(results) > 0
        
        # 5. Просмотр детальной информации
        results[0].click()
        
        detail_content = driver.find_element(By.ID, "result-detail")
        assert detail_content.is_displayed()
```

### 4. Тесты производительности

**Что тестируем:**
- Время отклика API
- Пропускную способность
- Использование памяти
- Масштабируемость

**Пример:**
```python
# tests/performance/test_load.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
from tests.conftest import create_test_app

@pytest.mark.performance
class TestAPIPerformance:
    @pytest.fixture
    def client(self):
        app = create_test_app()
        return TestClient(app)
    
    def test_search_response_time(self, client):
        # Arrange
        search_request = {"query": "test", "limit": 10}
        
        # Act
        start_time = time.time()
        response = client.post("/api/v1/search/", json=search_request)
        end_time = time.time()
        
        # Assert
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 2.0  # Максимум 2 секунды
    
    def test_concurrent_requests(self, client):
        # Тест на 100 одновременных запросов
        def make_request():
            return client.post("/api/v1/search/", json={"query": "test"})
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(100)]
            responses = [f.result() for f in futures]
        
        # Проверяем, что все запросы успешны
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 95  # 95% успешных запросов
```

## 🚀 Запуск тестов

### Основные команды

```bash
# Все тесты
python -m pytest tests/

# Только юнит тесты
python -m pytest tests/unit/ -v

# Только интеграционные тесты
python -m pytest tests/integration/ -v

# Конкретный файл
python -m pytest tests/unit/test_api_users.py -v

# Конкретный тест
python -m pytest tests/unit/test_api_users.py::TestUsersAPI::test_create_user -v

# С покрытием кода
python -m pytest tests/ --cov=app --cov-report=html

# Параллельный запуск
python -m pytest tests/ -n auto

# С отладочной информацией
python -m pytest tests/unit/test_api_users.py -v -s --tb=long
```

### Фильтрация тестов

```bash
# По маркерам
python -m pytest -m "unit"
python -m pytest -m "integration"
python -m pytest -m "e2e"
python -m pytest -m "not slow"

# По ключевым словам
python -m pytest -k "search"
python -m pytest -k "api and user"
python -m pytest -k "not database"

# Только упавшие тесты
python -m pytest --lf

# Остановка на первой ошибке
python -m pytest -x

# Показать самые медленные тесты
python -m pytest --durations=10
```

### Конфигурация pytest

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --disable-warnings
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    performance: Performance tests
    api: API tests
    database: Database tests
```

## ✍️ Написание тестов

### Структура теста (AAA Pattern)

```python
def test_example():
    # Arrange - подготовка данных и моков
    user_data = {"name": "Test User", "email": "test@example.com"}
    mock_service = Mock()
    mock_service.create_user.return_value = {"id": 1, **user_data}
    
    # Act - выполнение тестируемого действия
    result = user_service.create_user(user_data)
    
    # Assert - проверка результата
    assert result["id"] == 1
    assert result["name"] == "Test User"
    mock_service.create_user.assert_called_once_with(user_data)
```

### Использование фикстур

```python
# conftest.py - глобальные фикстуры
@pytest.fixture
def test_db():
    """Создает тестовую базу данных"""
    # Setup
    engine = create_test_engine()
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    yield db
    
    # Teardown
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_user():
    """Создает тестового пользователя"""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "name": "Test User",
        "is_active": True
    }

# test_*.py - использование фикстур
def test_user_creation(test_db, sample_user):
    # Используем фикстуры в тесте
    user = User(**sample_user)
    test_db.add(user)
    test_db.commit()
    
    assert user.id is not None
```

### Мокирование зависимостей

```python
from unittest.mock import Mock, AsyncMock, patch

class TestLLMService:
    @pytest.fixture
    def mock_openai_client(self):
        mock = Mock()
        mock.chat.completions.create = AsyncMock(
            return_value=Mock(
                choices=[Mock(message=Mock(content="Test response"))]
            )
        )
        return mock
    
    @patch('app.services.llm_service.OpenAI')
    async def test_generate_response(self, mock_openai_class, mock_openai_client):
        # Arrange
        mock_openai_class.return_value = mock_openai_client
        service = LLMService()
        
        # Act
        response = await service.generate_response("Test prompt")
        
        # Assert
        assert response == "Test response"
        mock_openai_client.chat.completions.create.assert_called_once()
```

### Тестирование исключений

```python
def test_invalid_user_data():
    # Проверка конкретного исключения
    with pytest.raises(ValueError, match="Email is required"):
        create_user({"name": "Test"})  # Без email
    
    # Проверка типа исключения
    with pytest.raises(ValidationError):
        validate_user_data({})

def test_http_exceptions():
    with pytest.raises(HTTPException) as exc_info:
        raise HTTPException(status_code=404, detail="User not found")
    
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()
```

### Параметризованные тесты

```python
@pytest.mark.parametrize("email,expected", [
    ("test@example.com", True),
    ("invalid-email", False),
    ("", False),
    ("test@", False),
    ("@example.com", False),
])
def test_email_validation(email, expected):
    result = validate_email(email)
    assert result == expected

@pytest.mark.parametrize("user_data,error_message", [
    ({"name": ""}, "Name cannot be empty"),
    ({"email": "invalid"}, "Invalid email format"),
    ({"age": -1}, "Age must be positive"),
])
def test_user_validation_errors(user_data, error_message):
    with pytest.raises(ValidationError, match=error_message):
        validate_user(user_data)
```

## 🐛 Отладка тестов

### Отладочные техники

```python
# 1. Добавление print statements
def test_debug_example():
    result = some_function()
    print(f"Result: {result}")  # Запуск с -s чтобы увидеть print
    assert result == expected

# 2. Использование pdb
def test_with_debugger():
    import pdb; pdb.set_trace()  # Точка останова
    result = some_function()
    assert result == expected

# 3. Логирование в тестах
import logging
logging.basicConfig(level=logging.DEBUG)

def test_with_logging():
    logger = logging.getLogger(__name__)
    logger.debug("Starting test")
    result = some_function()
    logger.debug(f"Got result: {result}")
    assert result == expected
```

### Запуск с отладкой

```bash
# Показать print statements
python -m pytest tests/unit/test_api.py -s

# Подробный traceback
python -m pytest tests/unit/test_api.py --tb=long

# Остановка на первой ошибке
python -m pytest tests/unit/test_api.py -x

# Повторный запуск только упавших тестов
python -m pytest --lf

# Интерактивная отладка при ошибке
python -m pytest tests/unit/test_api.py --pdb
```

### Анализ покрытия кода

```bash
# Генерация отчета о покрытии
python -m pytest tests/ --cov=app --cov-report=html

# Показать строки без покрытия
python -m pytest tests/ --cov=app --cov-report=term-missing

# Минимальный процент покрытия
python -m pytest tests/ --cov=app --cov-fail-under=80
```

## 🔄 CI/CD интеграция

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: password
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest-cov
    
    - name: Run unit tests
      run: |
        python -m pytest tests/unit/ -v --cov=app
    
    - name: Run integration tests
      run: |
        python -m pytest tests/integration/ -v
      env:
        DATABASE_URL: postgresql://postgres:password@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Makefile для тестов

```makefile
# Makefile
.PHONY: test test-unit test-integration test-e2e test-coverage

test: test-unit test-integration

test-unit:
	python -m pytest tests/unit/ -v

test-integration:
	python -m pytest tests/integration/ -v

test-e2e:
	python -m pytest tests/e2e/ -v

test-coverage:
	python -m pytest tests/ --cov=app --cov-report=html --cov-report=term

test-performance:
	python -m pytest tests/performance/ -v

test-docker:
	docker-compose -f docker-compose.test.yml up --abort-on-container-exit

clean-test:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -f .coverage
```

### Pre-commit hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: Run tests
        entry: python -m pytest tests/unit/ -q
        language: system
        pass_filenames: false
        always_run: true
      
      - id: coverage
        name: Check coverage
        entry: python -m pytest tests/unit/ --cov=app --cov-fail-under=80
        language: system
        pass_filenames: false
        always_run: true
```

## 📊 Метрики качества

### Целевые показатели

- **Покрытие кода**: > 80%
- **Время выполнения юнит тестов**: < 30 секунд
- **Время выполнения всех тестов**: < 5 минут
- **Процент прохождения тестов**: > 95%

### Мониторинг качества

```bash
# Проверка качества кода
flake8 app/ tests/
black --check app/ tests/
mypy app/

# Анализ сложности кода
radon cc app/ -a
radon mi app/

# Поиск дублирования кода
pylint app/ tests/
```

---

*Это руководство поможет вам эффективно тестировать AI Assistant и поддерживать высокое качество кода.* 