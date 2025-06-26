# 🛠️ Руководство по локальной разработке и отладке

Полное пошаговое руководство по запуску и отладке AI Assistant локально.

---

## 📋 **Подготовка окружения**

### **Системные требования**
- **Python 3.11+** (для бэкенда)
- **Node.js 18+** (для фронтенда)
- **Docker & Docker Compose** (для сервисов)
- **Git** (для работы с репозиторием)

### **Проверка системы**
```bash
# Проверка Python
python3 --version

# Проверка Node.js
node --version && npm --version

# Проверка Docker
docker --version && docker-compose --version

# Проверка доступности портов
lsof -i :8000  # FastAPI
lsof -i :3000  # React  
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :6333  # Qdrant
```

---

## 🔧 **БЭКЕНД (FastAPI) - Пошагово**

### **Шаг 1: Клонирование и настройка**

```bash
# Клонирование репозитория
git clone <repository-url>
cd dev_exp_ai

# Проверка файлов
ls -la  # Убедитесь что есть app/, requirements.txt, docker-compose.yml
```

### **Шаг 2: Python окружение**

```bash
# Создание виртуального окружения
python3 -m venv venv

# Активация (macOS/Linux)
source venv/bin/activate

# Активация (Windows)
# venv\Scripts\activate

# Проверка активации
which python  # Должен показать путь к venv

# Обновление pip
pip install --upgrade pip
```

### **Шаг 3: Установка зависимостей**

```bash
# Установка основных зависимостей
pip install -r requirements.txt

# Проверка установки ключевых пакетов
pip show fastapi uvicorn sqlalchemy psycopg2-binary redis qdrant-client

# В случае ошибок с psycopg2 на macOS:
# brew install postgresql
```

### **Шаг 4: Настройка переменных окружения**

```bash
# Копирование примера
cp env.example .env.local

# Редактирование переменных
nano .env.local  # или code .env.local
```

**Минимальный .env.local для локальной разработки:**
```bash
# === ОСНОВНЫЕ НАСТРОЙКИ ===
ENVIRONMENT=development
SECRET_KEY=dev-secret-key-change-me
LOG_LEVEL=DEBUG

# === БАЗА ДАННЫХ ===
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_assistant

# === AI СЕРВИСЫ (получите ключи) ===
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# === REDIS ===
REDIS_URL=redis://localhost:6379

# === VECTOR DATABASE ===
QDRANT_HOST=localhost
QDRANT_PORT=6333

# === БЕЗОПАСНОСТЬ ===
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# === МОНИТОРИНГ ===
ENABLE_METRICS=true
METRICS_PORT=9090
```

### **Шаг 5: Запуск инфраструктуры (Docker)**

```bash
# Запуск только сервисов (без приложения)
docker-compose up -d postgres redis qdrant

# Проверка статуса
docker-compose ps

# Проверка логов
docker-compose logs postgres
docker-compose logs redis  
docker-compose logs qdrant

# Проверка подключения к сервисам
psql postgresql://postgres:password@localhost:5432/ai_assistant -c "SELECT version();"
redis-cli ping
curl http://localhost:6333/health
```

### **Шаг 6: Настройка базы данных**

```bash
# Если у вас есть alembic
alembic upgrade head

# Или создание таблиц напрямую (если нет alembic)
python3 -c "
from app.database.session import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print('✅ База данных создана')
"

# Создание тестового пользователя (если есть скрипт)
python3 scripts/create_test_user.py
```

### **Шаг 7: Запуск бэкенда**

```bash
# Загрузка переменных окружения
export $(cat .env.local | xargs)

# Запуск с автоматической перезагрузкой (для разработки)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

# Альтернативный способ через Python
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Запуск в production режиме
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### **Шаг 8: Проверка работы бэкенда**

```bash
# Проверка health endpoint
curl http://localhost:8000/health

# Проверка главной страницы API
curl http://localhost:8000/

# Проверка OpenAPI документации
open http://localhost:8000/docs

# Проверка ReDoc документации
open http://localhost:8000/redoc

# Проверка конкретного API endpoint
curl -X POST "http://localhost:8000/api/v1/auth/demo-users" | jq
```

---

## 🎨 **ФРОНТЕНД (React) - Пошагово**

### **Шаг 1: Переход в директорию фронтенда**

```bash
cd frontend

# Проверка файлов
ls -la  # Убедитесь что есть package.json, src/, vite.config.ts
```

### **Шаг 2: Установка Node.js зависимостей**

```bash
# Проверка Node.js версии
node --version  # Должен быть 18+

# Очистка кэша (если были проблемы)
npm cache clean --force

# Установка зависимостей
npm install

# Проверка установленных пакетов
npm list --depth=0

# В случае ошибок с node-gyp на macOS:
# xcode-select --install
```

### **Шаг 3: Настройка окружения фронтенда**

```bash
# Создание файла переменных окружения
cp .env.example .env.local

# Редактирование настроек
nano .env.local
```

**Пример .env.local для фронтенда:**
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Development settings
VITE_APP_ENV=development
VITE_ENABLE_DEBUG=true

# Feature flags
VITE_ENABLE_VOICE=true
VITE_ENABLE_PWA=true
VITE_ENABLE_ANALYTICS=false

# WebSocket
VITE_WS_URL=ws://localhost:8000/ws
```

### **Шаг 4: Запуск фронтенда для разработки**

```bash
# Запуск development сервера
npm run dev

# Альтернативный запуск с конкретным портом
npm run dev -- --port 3001

# Запуск с открытием браузера
npm run dev -- --open

# Запуск с внешним доступом
npm run dev -- --host 0.0.0.0
```

### **Шаг 5: Проверка работы фронтенда**

```bash
# Фронтенд должен быть доступен по адресу
open http://localhost:3000

# Проверка API подключения (в консоли браузера)
fetch('http://localhost:8000/health').then(r => r.json()).then(console.log)

# Проверка компонентов
# Откройте DevTools (F12) и проверьте Console на ошибки
```

---

## 🐛 **ОТЛАДКА И TROUBLESHOOTING**

### **🔍 Отладка бэкенда**

#### **1. Проверка логов**
```bash
# Логи FastAPI (если запущен с --log-level debug)
tail -f logs/app.log

# Логи Docker сервисов
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f qdrant

# Проверка системных логов
journalctl -f -u docker
```

#### **2. Интерактивная отладка Python**
```bash
# Запуск Python shell с загруженными моделями
python3 -c "
from app.database.session import get_db
from app.models.user import User
print('✅ Модели загружены успешно')
"

# Интерактивная отладка с ipdb
pip install ipdb

# Добавить в код: import ipdb; ipdb.set_trace()
# Затем запустить: uvicorn app.main:app --reload
```

#### **3. Проверка подключений к сервисам**
```bash
# PostgreSQL
psql postgresql://postgres:password@localhost:5432/ai_assistant -c "\dt"

# Redis
redis-cli ping
redis-cli info

# Qdrant
curl http://localhost:6333/collections
curl http://localhost:6333/health

# Проверка открытых портов
netstat -tulnp | grep :8000
```

#### **4. Отладка API endpoints**
```bash
# Детальная отладка с curl
curl -v -X POST "http://localhost:8000/api/v1/auth/demo-users" \
  -H "Content-Type: application/json"

# Проверка авторизации
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo@company.com", "password": "demo_password"}' | jq -r '.access_token')

curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/auth/me"
```

### **🎨 Отладка фронтенда**

#### **1. Проверка консоли браузера**
```javascript
// Откройте DevTools (F12) в браузере
// Console tab - проверьте ошибки JavaScript
// Network tab - проверьте HTTP запросы к API
// Sources tab - поставьте breakpoints в коде
```

#### **2. Отладка компонентов React**
```bash
# Установка React DevTools (расширение браузера)
# Chrome: https://chrome.google.com/webstore/detail/react-developer-tools
# Firefox: https://addons.mozilla.org/en-US/firefox/addon/react-devtools/

# Проверка состояния компонентов в React DevTools
# Components tab - иерархия компонентов
# Profiler tab - производительность рендеринга
```

#### **3. Отладка сетевых запросов**
```bash
# Проверка соединения с API
curl -X GET "http://localhost:8000/health"

# Проверка CORS настроек
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: X-Requested-With" \
  -X OPTIONS "http://localhost:8000/api/v1/health"
```

#### **4. Отладка билда**
```bash
# Проверка TypeScript ошибок
npx tsc --noEmit

# Линтинг кода
npm run lint

# Запуск тестов
npm run test

# Сборка production версии
npm run build
npm run preview  # Просмотр собранной версии
```

---

## 🔧 **ПОЛЕЗНЫЕ КОМАНДЫ ДЛЯ РАЗРАБОТКИ**

### **Бэкенд команды**
```bash
# Перезапуск с очисткой кэша
pip install --force-reinstall -r requirements.txt

# Проверка кода
black app/  # Форматирование
flake8 app/  # Линтинг
mypy app/   # Проверка типов

# Тестирование
pytest tests/ -v
pytest --cov=app tests/  # С покрытием

# Миграции БД
alembic revision --autogenerate -m "Description"
alembic upgrade head

# Очистка БД
docker-compose down -v  # Удалит все data volumes
```

### **Фронтенд команды**
```bash
# Обновление зависимостей
npm update
npm audit fix

# Очистка и переустановка
rm -rf node_modules package-lock.json
npm install

# Анализ бандла
npm run build
npx vite-bundle-analyzer dist

# Форматирование кода
npx prettier --write src/
```

### **Docker команды**
```bash
# Полная пересборка
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# Логи в реальном времени
docker-compose logs -f ai-assistant

# Подключение к контейнеру
docker-compose exec postgres psql -U postgres -d ai_assistant
docker-compose exec redis redis-cli

# Очистка Docker
docker system prune -a
```

---

## 📊 **МОНИТОРИНГ И ПРОФИЛИРОВАНИЕ**

### **Бэкенд мониторинг**
```bash
# Проверка производительности API
ab -n 100 -c 10 http://localhost:8000/health

# Мониторинг ресурсов
htop  # CPU и память
iotop  # Дисковые операции

# Профилирование Python кода
pip install py-spy
py-spy top --pid $(pgrep -f uvicorn)
```

### **Фронтенд мониторинг**
```bash
# Анализ производительности в браузере
# DevTools > Performance tab > Record

# Проверка размера бандла
npm run build
du -sh dist/

# Lighthouse audit (в Chrome DevTools)
# DevTools > Lighthouse tab > Generate report
```

---

## 🆘 **Частые проблемы и решения**

### **Проблемы с бэкендом**

**❌ Проблема:** `ModuleNotFoundError: No module named 'app'`
```bash
# ✅ Решение: Убедитесь что запускаете из корневой директории
pwd  # Должно показать путь к dev_exp_ai
python3 -m uvicorn app.main:app --reload
```

**❌ Проблема:** `connection to server failed: FATAL: database "ai_assistant" does not exist`
```bash
# ✅ Решение: Создайте базу данных
docker-compose exec postgres createdb -U postgres ai_assistant
```

**❌ Проблема:** `redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379`
```bash
# ✅ Решение: Проверьте что Redis запущен
docker-compose up -d redis
redis-cli ping  # Должен ответить PONG
```

**❌ Проблема:** `qdrant_client.http.exceptions.UnexpectedResponse: status: 404`
```bash
# ✅ Решение: Проверьте Qdrant и создайте коллекции
curl http://localhost:6333/health
curl -X POST "http://localhost:8000/api/v1/vector-search/collections/initialize"
```

### **Проблемы с фронтендом**

**❌ Проблема:** `npm ERR! peer dep missing: react@^18.0.0`
```bash
# ✅ Решение: Переустановите зависимости
rm -rf node_modules package-lock.json
npm install
```

**❌ Проблема:** `CORS error when calling API`
```bash
# ✅ Решение: Проверьте настройки CORS в бэкенде
# В app/main.py должно быть:
# allow_origins=["http://localhost:3000"]
```

**❌ Проблема:** `Module not found: Can't resolve 'some-module'`
```bash
# ✅ Решение: Установите недостающий модуль
npm install some-module
# Или обновите импорты в коде
```

---

## 🚀 **Быстрый старт (TL;DR)**

### **Все в одном терминале:**
```bash
# 1. Подготовка
git clone <repo> && cd dev_exp_ai
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp env.example .env.local

# 2. Настройка переменных окружения (.env.local)
# Добавьте OPENAI_API_KEY и ANTHROPIC_API_KEY

# 3. Запуск сервисов
docker-compose up -d postgres redis qdrant

# 4. Запуск бэкенда (терминал 1)
export $(cat .env.local | xargs)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Запуск фронтенда (терминал 2)
cd frontend && npm install && npm run dev

# 6. Проверка
open http://localhost:8000/docs  # API документация
open http://localhost:3000       # Фронтенд
```

---

## 📞 **Получение помощи**

**🐛 Если что-то не работает:**

1. **Проверьте логи**: `docker-compose logs -f`
2. **Проверьте переменные окружения**: `env | grep -E "(DATABASE|API_KEY|REDIS)"`
3. **Проверьте порты**: `lsof -i :8000,3000,5432,6379,6333`
4. **Очистите кэш**: `docker system prune -a && npm cache clean --force`

**📋 Создайте issue с информацией:**
- Операционная система и версия
- Версии Python, Node.js, Docker
- Полный текст ошибки
- Шаги для воспроизведения

**📚 Полезные ссылки:**
- [FastAPI документация](https://fastapi.tiangolo.com/)
- [React документация](https://react.dev/)
- [Docker Compose документация](https://docs.docker.com/compose/)

---

**✅ Happy coding!** Теперь у вас есть полное руководство для локальной разработки и отладки AI Assistant. 