# 🚀 ЛОКАЛЬНОЕ РАЗВЕРТЫВАНИЕ AI ASSISTANT

## 📋 БЫСТРЫЙ СТАРТ

### Вариант 1: Docker Compose (Рекомендуется)
```bash
# 1. Клонировать репозиторий
git clone <your-repo>
cd dev_exp_ai

# 2. Создать .env файл
cp env.example .env
# Отредактируйте .env файл с вашими API ключами

# 3. Запустить все сервисы
./docker-commands.sh start

# 4. Проверить работу
curl http://localhost:8000/health
```

### Вариант 2: Локальная разработка
```bash
# 1. Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Запустить сервер
python3 start_server.py
```

## 🐳 DOCKER КОМАНДЫ

### Основные команды
```bash
# Запуск всех сервисов
./docker-commands.sh start
make docker-up

# Остановка
./docker-commands.sh stop
make docker-down

# Перезапуск
./docker-commands.sh restart
make docker-restart

# Логи
./docker-commands.sh logs
make docker-logs

# Статус
./docker-commands.sh status
make docker-status
```

### Команды разработки
```bash
# Режим разработки (hot reload)
./docker-commands.sh dev
make docker-dev

# Войти в контейнер для отладки
./docker-commands.sh shell
make docker-shell

# Подключиться к БД
./docker-commands.sh db
make docker-db

# Тесты в контейнере
./docker-commands.sh test
make docker-test
```

## 🏗️ СЕРВИСЫ

После запуска доступны:

| Сервис | URL | Описание |
|--------|-----|----------|
| API | http://localhost:8000 | Основное приложение |
| API Docs | http://localhost:8000/docs | Swagger документация |
| Health | http://localhost:8000/health | Проверка здоровья |
| Adminer | http://localhost:8080 | Управление PostgreSQL |
| Redis UI | http://localhost:8081 | Управление Redis |

### Учетные данные
- **PostgreSQL**: postgres / password
- **Database**: ai_assistant
- **Redis**: без пароля

## ⚙️ НАСТРОЙКА

### Переменные окружения (.env)
```env
# Основные настройки
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here
LOG_LEVEL=INFO

# База данных
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_assistant

# AI сервисы (обязательно!)
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Redis
REDIS_URL=redis://localhost:6379
```

### Структура проекта
```
dev_exp_ai/
├── app/                    # Основное приложение
├── tests/                  # Тесты
├── scripts/                # Скрипты
├── docker-compose.local.yml # Docker конфигурация
├── Dockerfile              # Docker образ
├── requirements.txt        # Python зависимости
├── start_server.py         # Запуск сервера
└── docker-commands.sh      # Docker команды
```

## 🧪 ТЕСТИРОВАНИЕ

### Быстрые тесты
```bash
# Проверка системы
python3 quick_test.py

# Диагностика
python3 debug_helper.py

# Все тесты
make test
```

### Тесты в Docker
```bash
# Unit тесты
make docker-test

# Конкретный тест
docker-compose exec ai-assistant python -m pytest tests/unit/test_ai_advanced.py -v
```

## 🔍 ОТЛАДКА

### Проверка статуса
```bash
# Статус Docker сервисов
./docker-commands.sh status

# Логи конкретного сервиса
./docker-commands.sh logs ai-assistant
./docker-commands.sh logs postgres
./docker-commands.sh logs redis
```

### Подключение к сервисам
```bash
# PostgreSQL
./docker-commands.sh db
# или через Adminer: http://localhost:8080

# Redis
./docker-commands.sh redis
# или через Redis Commander: http://localhost:8081

# Контейнер приложения
./docker-commands.sh shell
```

### Частые проблемы

#### 1. Контейнер не запускается
```bash
# Проверить логи
./docker-commands.sh logs ai-assistant

# Пересобрать образ
./docker-commands.sh build
```

#### 2. База данных недоступна
```bash
# Проверить статус PostgreSQL
docker-compose exec postgres pg_isready -U postgres

# Пересоздать БД
./docker-commands.sh clean
./docker-commands.sh start
```

#### 3. API не отвечает
```bash
# Проверить здоровье
curl http://localhost:8000/health

# Проверить порты
netstat -tlnp | grep 8000
```

## 💻 РАЗРАБОТКА

### Локальная разработка
```bash
# Активировать venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Запустить в режиме разработки
make dev
# или
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker разработка
```bash
# Запустить в режиме разработки
./docker-commands.sh dev

# Код автоматически перезагружается при изменениях
```

### Добавление новых зависимостей
```bash
# Добавить в requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# Пересобрать образ
./docker-commands.sh build
```

## 📚 ПОЛЕЗНЫЕ КОМАНДЫ

### Make команды
```bash
make help           # Справка
make install        # Установить зависимости
make start          # Запустить сервер
make test           # Запустить тесты
make clean          # Очистить временные файлы
make docker-up      # Запустить Docker
make docker-down    # Остановить Docker
make setup-docker   # Настроить Docker окружение
```

### Docker команды
```bash
./docker-commands.sh help      # Справка
./docker-commands.sh start     # Запустить
./docker-commands.sh stop      # Остановить
./docker-commands.sh dev       # Режим разработки
./docker-commands.sh shell     # Войти в контейнер
./docker-commands.sh clean     # Очистить все
```

### Утилиты
```bash
python3 quick_test.py          # Быстрые тесты
python3 debug_helper.py        # Диагностика
python3 ai_assistant_cli.py    # CLI интерфейс
```

## 🎯 СЛЕДУЮЩИЕ ШАГИ

1. **Настройте API ключи** в .env файле
2. **Запустите систему**: `./docker-commands.sh start`
3. **Проверьте работу**: http://localhost:8000/docs
4. **Запустите тесты**: `python3 quick_test.py`
5. **Начните разработку**: `./docker-commands.sh dev`

---

**🎉 Готово! AI Assistant готов к использованию!** 