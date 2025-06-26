# 🚀 AI Assistant - Шпаргалка для разработчика

**Все команды для быстрого старта в одном месте**

---

## ⚡ **БЫСТРЫЙ СТАРТ (5 минут)**

```bash
# 1️⃣ Клонирование и настройка
git clone <repo> && cd dev_exp_ai
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp env.example .env.local

# 2️⃣ Настройка .env.local (добавьте ваши API ключи)
nano .env.local

# 3️⃣ Запуск сервисов
docker-compose up -d postgres redis qdrant

# 4️⃣ Запуск бэкенда (терминал 1)
export $(cat .env.local | xargs)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 5️⃣ Запуск фронтенда (терминал 2)
cd frontend && npm install && npm run dev
```

**✅ Готово!** 
- API: http://localhost:8000/docs
- Фронтенд: http://localhost:3000

---

## 🔧 **ОБЯЗАТЕЛЬНЫЕ .env.local настройки**

```bash
# Минимум для работы
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_assistant
REDIS_URL=redis://localhost:6379
QDRANT_HOST=localhost
QDRANT_PORT=6333
SECRET_KEY=dev-secret-key
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

---

## 🐛 **ЧАСТЫЕ ОШИБКИ И БЫСТРЫЕ РЕШЕНИЯ**

| Ошибка | Быстрое решение |
|--------|----------------|
| `ModuleNotFoundError: No module named 'app'` | `pwd` → должен быть в `dev_exp_ai/` |
| `database "ai_assistant" does not exist` | `docker-compose exec postgres createdb -U postgres ai_assistant` |
| `redis connection error` | `docker-compose up -d redis && redis-cli ping` |
| `qdrant 404 error` | `curl http://localhost:6333/health` |
| `npm install errors` | `rm -rf node_modules package-lock.json && npm install` |
| `CORS error` | Проверить `allow_origins` в `app/main.py` |
| `Port already in use` | `lsof -i :8000` → убить процесс |

---

## 📋 **ПРОВЕРКА ЗДОРОВЬЯ СИСТЕМЫ**

```bash
# Проверка всех сервисов (скопируйте и запустите)
echo "🔍 Проверка системы..."
echo "Python: $(python3 --version)"
echo "Node: $(node --version)"
echo "Docker: $(docker --version)"
echo "Services:"
curl -s http://localhost:8000/health && echo " ✅ Backend OK" || echo " ❌ Backend FAIL"
curl -s http://localhost:3000 && echo " ✅ Frontend OK" || echo " ❌ Frontend FAIL"
redis-cli ping && echo " ✅ Redis OK" || echo " ❌ Redis FAIL"
curl -s http://localhost:6333/health && echo " ✅ Qdrant OK" || echo " ❌ Qdrant FAIL"
psql postgresql://postgres:password@localhost:5432/ai_assistant -c "SELECT 1" && echo " ✅ PostgreSQL OK" || echo " ❌ PostgreSQL FAIL"
```

---

## 🛠️ **ПОЛЕЗНЫЕ КОМАНДЫ ДЛЯ ОТЛАДКИ**

### **Бэкенд отладка**
```bash
# Логи FastAPI
tail -f logs/app.log

# Перезапуск с отладкой
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

# Проверка API
curl http://localhost:8000/health
curl http://localhost:8000/docs

# Тестирование
pytest tests/ -v
```

### **Фронтенд отладка**
```bash
# Запуск с отладкой
npm run dev

# Проверка ошибок
npm run lint
npx tsc --noEmit

# Тесты
npm run test
```

### **Docker отладка**
```bash
# Статус сервисов
docker-compose ps

# Логи
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f qdrant

# Перезапуск
docker-compose down && docker-compose up -d postgres redis qdrant

# Очистка
docker-compose down -v
docker system prune -a
```

---

## 🎯 **ПОРТЫ И АДРЕСА**

| Сервис | Порт | URL | Назначение |
|--------|------|-----|------------|
| FastAPI | 8000 | http://localhost:8000 | Backend API |
| React | 3000 | http://localhost:3000 | Frontend |
| PostgreSQL | 5432 | localhost:5432 | База данных |
| Redis | 6379 | localhost:6379 | Кэш |
| Qdrant | 6333 | http://localhost:6333 | Векторная БД |
| Swagger UI | 8000 | http://localhost:8000/docs | API документация |
| ReDoc | 8000 | http://localhost:8000/redoc | API документация |

---

## 🔍 **МОНИТОРИНГ И ПРОФИЛИРОВАНИЕ**

```bash
# Проверка производительности API
ab -n 100 -c 10 http://localhost:8000/health

# Мониторинг ресурсов
htop  # CPU и память
iotop  # Диск I/O

# Размер фронтенд бандла
cd frontend && npm run build && du -sh dist/

# Профилирование Python
pip install py-spy
py-spy top --pid $(pgrep -f uvicorn)
```

---

## 🧪 **ТЕСТИРОВАНИЕ**

```bash
# Бэкенд тесты
pytest tests/ -v                    # Все тесты
pytest tests/unit/ -v               # Unit тесты
pytest tests/integration/ -v        # Интеграционные тесты
pytest --cov=app tests/             # С покрытием

# Фронтенд тесты
cd frontend
npm run test                        # Jest тесты
npm run test:ui                     # UI тесты

# E2E тесты
cd tests/e2e
make test-e2e                       # End-to-end тесты
```

---

## 📦 **УПРАВЛЕНИЕ ЗАВИСИМОСТЯМИ**

```bash
# Python зависимости
pip install package-name             # Установка
pip freeze > requirements.txt       # Сохранение
pip install -r requirements.txt     # Установка из файла

# Node.js зависимости
cd frontend
npm install package-name             # Установка
npm install package-name --save-dev  # Dev зависимость
npm update                          # Обновление всех
npm audit fix                       # Исправление уязвимостей
```

---

## 🔄 **WORKFLOW ДЛЯ ЕЖЕДНЕВНОЙ РАЗРАБОТКИ**

### **Начало работы**
```bash
cd dev_exp_ai
source venv/bin/activate
docker-compose up -d postgres redis qdrant
export $(cat .env.local | xargs)
```

### **Запуск (2 терминала)**
```bash
# Терминал 1: Бэкенд
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Терминал 2: Фронтенд
cd frontend && npm run dev
```

### **Перед коммитом**
```bash
# Форматирование и проверка
black app/
flake8 app/
cd frontend && npm run lint
pytest tests/ -v
```

### **Конец работы**
```bash
# Остановка сервисов
docker-compose down
deactivate  # Выход из venv
```

---

## 🆘 **ЭКСТРЕННОЕ ВОССТАНОВЛЕНИЕ**

### **Если все сломалось**
```bash
# 1. Полная очистка
docker-compose down -v
docker system prune -a
rm -rf venv/ frontend/node_modules/

# 2. Заново все
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install

# 3. Перезапуск
docker-compose up -d postgres redis qdrant
export $(cat .env.local | xargs)
uvicorn app.main:app --reload
```

### **Если нужна помощь**
```bash
# Диагностика системы
echo "=== SYSTEM INFO ==="
uname -a
python3 --version
node --version
docker --version

echo "=== PORTS ==="
lsof -i :8000,3000,5432,6379,6333

echo "=== PROCESSES ==="
ps aux | grep -E "(uvicorn|node|docker)"

echo "=== DISK SPACE ==="
df -h

echo "=== MEMORY ==="
free -h
```

---

## 💡 **ПОЛЕЗНЫЕ ССЫЛКИ**

- **📚 Полное руководство:** [LOCAL_DEVELOPMENT_GUIDE.md](./LOCAL_DEVELOPMENT_GUIDE.md)
- **🌐 FastAPI документация:** https://fastapi.tiangolo.com/
- **⚛️ React документация:** https://react.dev/
- **🐳 Docker документация:** https://docs.docker.com/
- **🔧 Swagger UI:** http://localhost:8000/docs
- **📖 ReDoc:** http://localhost:8000/redoc

---

**💻 Эта шпаргалка покрывает 95% ежедневных задач разработки!**
**📌 Сохраните в закладки или распечатайте для быстрого доступа** 