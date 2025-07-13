# 🏗️ Hexagonal Architecture Guide

**Проект:** AI Assistant  
**Архитектура:** Hexagonal (Ports & Adapters)  
**Дата:** 2025-01-13  
**Версия:** 1.0

## 🎯 Обзор архитектуры

Система AI Assistant переведена на **чистую гексагональную архитектуру** (Ports & Adapters pattern) согласно принципам Alistair Cockburn. Все зависимости направлены внутрь к доменному ядру, что обеспечивает:

- **Независимость от внешних зависимостей**
- **Простоту тестирования**
- **Гибкость при замене компонентов**
- **Соблюдение принципов SOLID**

## 📂 Структура проекта

```
AI_Assistant/
├── hex_core/                  # 🔵 CORE (Domain Layer)
│   ├── domain/               # Доменные сущности
│   │   ├── auth/            # Аутентификация
│   │   ├── ai_analysis/     # AI анализ
│   │   └── shared/          # Общие модели
│   ├── use_cases/           # Use Cases (Application Services)
│   └── ports/               # Интерфейсы (Ports)
│
├── hex_adapters/             # 🔴 ADAPTERS (Infrastructure)
│   ├── api/                 # Primary Adapters (REST API)
│   ├── database/            # Secondary Adapters (Database)
│   ├── external/            # Secondary Adapters (External APIs)
│   ├── llm/                 # Secondary Adapters (LLM Providers)
│   └── messaging/           # Secondary Adapters (Message Queues)
│
├── hex_infrastructure/       # 🟡 INFRASTRUCTURE
│   ├── config/              # Конфигурация
│   ├── middleware/          # Middleware
│   └── startup/             # Инициализация
│
├── tests/                   # 🧪 TESTS
│   ├── unit/               # Unit тесты
│   ├── integration/        # Integration тесты
│   └── e2e/                # End-to-end тесты
│
└── hex_main.py              # 🚀 Entry Point
```

## 🔵 Core Layer (Доменное ядро)

### Domain Entities
**Расположение:** `hex_core/domain/`

Чистые доменные сущности без внешних зависимостей:

```python
# hex_core/domain/auth/entities.py
@dataclass
class User:
    id: UserId
    email: Email
    name: str
    roles: Set[Role]
    status: UserStatus
    
    def has_permission(self, permission: str) -> bool:
        return any(role.has_permission(permission) for role in self.roles)
```

### Value Objects
**Расположение:** `hex_core/domain/*/value_objects.py`

Неизменяемые объекты-значения:

```python
# hex_core/domain/auth/value_objects.py
@dataclass(frozen=True)
class Email:
    value: str
    
    def __post_init__(self):
        if not self.value or "@" not in self.value:
            raise ValueError("Invalid email format")
```

### Use Cases
**Расположение:** `hex_core/use_cases/`

Бизнес-логика приложения:

```python
# hex_core/use_cases/auth_services.py
class AuthApplicationService:
    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repository = user_repository
    
    async def authenticate_user(self, email: Email, password: Password) -> User:
        # Бизнес-логика аутентификации
        pass
```

### Ports
**Расположение:** `hex_core/ports/`

Интерфейсы для внешних зависимостей:

```python
# hex_core/ports/auth_ports.py
from abc import ABC, abstractmethod

class UserRepositoryPort(ABC):
    @abstractmethod
    async def find_by_email(self, email: Email) -> Optional[User]:
        pass
    
    @abstractmethod
    async def save(self, user: User) -> None:
        pass
```

## 🔴 Adapters Layer (Адаптеры)

### Primary Adapters (API)
**Расположение:** `hex_adapters/api/`

REST API endpoints, которые вызывают Use Cases:

```python
# hex_adapters/api/auth/routes.py
from fastapi import APIRouter, Depends
from hex_core.use_cases.auth_services import AuthApplicationService

router = APIRouter()

@router.post("/login")
async def login(
    request: LoginRequest,
    auth_service: AuthApplicationService = Depends()
):
    user = await auth_service.authenticate_user(
        Email(request.email), 
        Password(request.password)
    )
    return {"token": generate_token(user)}
```

### Secondary Adapters (Database)
**Расположение:** `hex_adapters/database/`

Реализации портов для работы с базой данных:

```python
# hex_adapters/database/user_repository.py
from hex_core.ports.auth_ports import UserRepositoryPort
from hex_core.domain.auth.entities import User

class SqlUserRepository(UserRepositoryPort):
    async def find_by_email(self, email: Email) -> Optional[User]:
        # SQL implementation
        pass
    
    async def save(self, user: User) -> None:
        # SQL implementation
        pass
```

## 🟡 Infrastructure Layer

### Configuration
**Расположение:** `hex_infrastructure/config/`

Конфигурация приложения:

```python
# hex_infrastructure/config/settings.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    redis_url: str
    
    class Config:
        env_file = ".env"
```

### Middleware
**Расположение:** `hex_infrastructure/middleware/`

Middleware для обработки запросов:

```python
# hex_infrastructure/middleware/auth_middleware.py
from fastapi import Request, HTTPException

async def auth_middleware(request: Request, call_next):
    # Authentication logic
    pass
```

## 🚀 Entry Point

### hex_main.py
Основной файл приложения с настройкой DI:

```python
#!/usr/bin/env python3
from hex_core.use_cases.auth_services import AuthApplicationService
from hex_adapters.database.user_repository import SqlUserRepository
from hex_adapters.api.auth.routes import router as auth_router

class HexagonalApp:
    def __init__(self):
        self.app = FastAPI(title="AI Assistant - Hexagonal Architecture")
        self.setup_dependencies()
        self.setup_routes()
    
    def setup_dependencies(self):
        # Dependency Injection setup
        user_repo = SqlUserRepository()
        auth_service = AuthApplicationService(user_repo)
        
    def setup_routes(self):
        self.app.include_router(auth_router, prefix="/api/v1/auth")
```

## 📋 Принципы архитектуры

### 1. Dependency Inversion
```
hex_adapters/api → hex_core/use_cases → hex_core/domain
hex_adapters/database → hex_core/ports ← hex_core/use_cases
```

### 2. Single Responsibility
- **Domain**: Только бизнес-логика
- **Use Cases**: Оркестрация доменных операций
- **Adapters**: Интеграция с внешними системами

### 3. Open/Closed
- Легко добавлять новые адаптеры
- Доменная логика не изменяется

### 4. Interface Segregation
- Узкие интерфейсы портов
- Конкретные реализации в адаптерах

### 5. Liskov Substitution
- Любой адаптер может заменить другой
- Все реализации портов взаимозаменяемы

## 🧪 Тестирование

### Unit Tests
```python
# tests/unit/domain/test_user.py
def test_user_has_permission():
    user = User(id=UserId("123"), email=Email("test@example.com"), ...)
    role = Role(name="admin", permissions={Permission("read_users")})
    user.assign_role(role)
    
    assert user.has_permission("read_users") == True
```

### Integration Tests
```python
# tests/integration/test_auth_service.py
async def test_authenticate_user():
    # Test with real database
    user_repo = SqlUserRepository()
    auth_service = AuthApplicationService(user_repo)
    
    user = await auth_service.authenticate_user(
        Email("test@example.com"), 
        Password("password123")
    )
    
    assert user.email.value == "test@example.com"
```

## 🚀 Запуск приложения

### Development
```bash
python hex_main.py
```

### Production
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker hex_main:create_app()
```

## 📊 Преимущества архитектуры

### ✅ Для разработки:
- **Независимость слоев** - можно разрабатывать параллельно
- **Простота тестирования** - легко создавать моки
- **Гибкость** - легко менять внешние зависимости

### ✅ Для тестирования:
- **Unit tests** - изолированное тестирование доменной логики
- **Integration tests** - тестирование адаптеров
- **E2E tests** - тестирование всего приложения

### ✅ Для продакшена:
- **Масштабируемость** - легко добавлять новые адаптеры
- **Надежность** - изолированные компоненты
- **Производительность** - оптимизированные адаптеры

## 📚 Дополнительные материалы

- [Hexagonal Architecture by Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)
- [Clean Architecture by Robert Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Ports and Adapters Pattern](https://herbertograca.com/2017/09/14/ports-adapters-architecture/)

## 🎯 Следующие шаги

1. **Запустить тесты** - `python -m pytest tests/`
2. **Проверить покрытие** - `coverage run -m pytest && coverage report`
3. **Запустить приложение** - `python hex_main.py`
4. **Развернуть в продакшене** - следовать deployment guide 