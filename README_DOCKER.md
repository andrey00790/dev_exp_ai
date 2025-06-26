# 🐳 DOCKER РУКОВОДСТВО ДЛЯ AI ASSISTANT

## 📋 СОДЕРЖАНИЕ

1. [Быстрый старт](#быстрый-старт)
2. [Команды Docker](#команды-docker)
3. [Сервисы](#сервисы)
4. [Разработка](#разработка)
5. [Продакшн](#продакшн)
6. [Отладка](#отладка)
7. [Мониторинг](#мониторинг)

## 🚀 БЫСТРЫЙ СТАРТ

### Минимальная настройка (3 минуты)
```bash
# 1. Клонировать репозиторий
git clone <your-repo>
cd dev_exp_ai

# 2. Запустить все сервисы
./docker-commands.sh start

# 3. Проверить работу
curl http://localhost:8000/health
```

### Альтернативный запуск
```bash
# Через Make
make docker-up

# Через Docker Compose напрямую
docker-compose up -d
```

## 🛠️ КОМАНДЫ DOCKER

### Основные команды
```bash
# Запуск
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
# Режим разработки (с hot reload)
./docker-commands.sh dev
make docker-dev

# Продакшн режим
./docker-commands.sh prod
make docker-prod

# Сборка образов
./docker-commands.sh build
make docker-build

# Тесты в контейнере
./docker-commands.sh test
make docker-test
```

### Команды отладки
```bash
# Войти в контейнер
./docker-commands.sh shell
make docker-shell

# Подключиться к БД
./docker-commands.sh db
make docker-db

# Подключиться к Redis
./docker-commands.sh redis
make docker-redis

# Очистка
./docker-commands.sh clean
make docker-clean
```

## 🏗️ СЕРВИСЫ

### Основные сервисы

#### 1. AI Assistant (Порт 8000)
- **Образ**: `ai-assistant:latest`
- **Описание**: Основное приложение FastAPI
- **URL**: http://localhost:8000
- **Документация**: http://localhost:8000/docs

#### 2. PostgreSQL (Порт 5432)
- **Образ**: `postgres:15-alpine`
- **Описание**: Основная база данных
- **Подключение**: `postgresql://postgres:password@localhost:5432/ai_assistant`
- **Adminer**: http://localhost:8080

#### 3. Redis (Порт 6379)
- **Образ**: `redis:7-alpine`
- **Описание**: Кэширование и сессии
- **Подключение**: `redis://localhost:6379`
- **Commander**: http://localhost:8081

#### 4. Qdrant (Порт 6333)
- **Образ**: `qdrant/qdrant:latest`
- **Описание**: Vector база данных
- **URL**: http://localhost:6333
- **API**: http://localhost:6334

#### 5. Nginx (Порт 80)
- **Образ**: `nginx:alpine`
- **Описание**: Прокси сервер
- **URL**: http://localhost

### Дополнительные сервисы (dev режим)

#### 6. Adminer (Порт 8080)
- **Описание**: Веб-интерфейс для управления БД
- **URL**: http://localhost:8080
- **Логин**: postgres / password

#### 7. Redis Commander (Порт 8081)
- **Описание**: Веб-интерфейс для Redis
- **URL**: http://localhost:8081

## 💻 РАЗРАБОТКА

### Режим разработки
```bash
# Запуск с hot reload
./docker-commands.sh dev

# Или через docker-compose
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

**Особенности режима разработки:**
- Автоперезагрузка при изменении кода
- Монтирование локального кода в контейнер
- Отладочные логи
- Дополнительные инструменты (Adminer, Redis Commander)

### Работа с кодом
```bash
# Войти в контейнер для отладки
./docker-commands.sh shell

# Запустить тесты
./docker-commands.sh test

# Проверить логи
./docker-commands.sh logs ai-assistant
```

### База данных
```bash
# Подключиться к БД
./docker-commands.sh db

# Или через Adminer
open http://localhost:8080

# Создать миграции
docker-compose exec ai-assistant alembic revision --autogenerate -m "New migration"

# Применить миграции
docker-compose exec ai-assistant alembic upgrade head
```

### Redis
```bash
# Подключиться к Redis
./docker-commands.sh redis

# Или через Redis Commander
open http://localhost:8081

# Проверить ключи
docker-compose exec redis redis-cli KEYS "*"
```

## 🚀 ПРОДАКШН

### Продакшн развертывание
```bash
# Запуск продакшн режима
./docker-commands.sh prod

# Или через docker-compose
docker-compose up -d
```

**Особенности продакшн режима:**
- Оптимизированные образы
- Отключен hot reload
- Продакшн логи
- Nginx прокси

### Переменные окружения
```bash
# Создать .env файл
cp .env.example .env

# Настроить переменные
nano .env
```

**Важные переменные:**
```env
# База данных
DATABASE_URL=postgresql://postgres:password@postgres:5432/ai_assistant

# Безопасность
SECRET_KEY=your-production-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI сервисы
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Логирование
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Масштабирование
```bash
# Масштабировать приложение
docker-compose up -d --scale ai-assistant=3

# Проверить статус
docker-compose ps
```

## 🔍 ОТЛАДКА

### Диагностика проблем

#### 1. Проверка статуса
```bash
# Статус всех сервисов
./docker-commands.sh status

# Детальная информация
docker-compose ps
docker-compose top
```

#### 2. Анализ логов
```bash
# Логи всех сервисов
./docker-commands.sh logs

# Логи конкретного сервиса
./docker-commands.sh logs ai-assistant
./docker-commands.sh logs postgres
./docker-commands.sh logs redis

# Логи с фильтрацией
docker-compose logs ai-assistant | grep ERROR
```

#### 3. Проверка ресурсов
```bash
# Использование ресурсов
docker stats

# Использование диска
docker system df

# Проверка volumes
docker volume ls
```

### Частые проблемы

#### Проблема: Контейнер не запускается
```bash
# Проверить логи
./docker-commands.sh logs ai-assistant

# Проверить порты
netstat -tlnp | grep 8000

# Пересобрать образ
./docker-commands.sh build
```

#### Проблема: База данных недоступна
```bash
# Проверить статус PostgreSQL
docker-compose exec postgres pg_isready -U postgres

# Проверить логи БД
./docker-commands.sh logs postgres

# Пересоздать БД
docker-compose down -v
docker-compose up -d
```

#### Проблема: Redis недоступен
```bash
# Проверить статус Redis
docker-compose exec redis redis-cli ping

# Проверить логи Redis
./docker-commands.sh logs redis
```

### Отладка в контейнере
```bash
# Войти в контейнер
./docker-commands.sh shell

# Проверить процессы
ps aux

# Проверить файлы
ls -la /app

# Проверить переменные окружения
env | grep -E "(DATABASE|SECRET|API)"

# Запустить отладчик
python3 -m pdb start_server.py
```

## 📊 МОНИТОРИНГ

### Health checks
```bash
# Проверка здоровья приложения
curl http://localhost:8000/health

# Проверка всех сервисов
docker-compose ps
```

### Метрики
```bash
# Метрики контейнеров
docker stats

# Метрики приложения
curl http://localhost:8000/metrics
```

### Логирование
```bash
# Централизованные логи
docker-compose logs -f

# Логи с временными метками
docker-compose logs -f --timestamps

# Логи с фильтрацией
docker-compose logs -f ai-assistant | grep -E "(ERROR|WARNING)"
```

### Резервное копирование
```bash
# Бэкап базы данных
docker-compose exec postgres pg_dump -U postgres ai_assistant > backup.sql

# Бэкап Redis
docker-compose exec redis redis-cli BGSAVE

# Бэкап volumes
docker run --rm -v ai_assistant_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

## 🔧 ДОПОЛНИТЕЛЬНЫЕ ИНСТРУМЕНТЫ

### Make команды
```bash
# Все Docker команды через Make
make docker-up
make docker-down
make docker-logs
make docker-shell
make docker-test
make docker-clean
```

### Полезные скрипты
```bash
# Быстрый тест
./quick_test.py

# Диагностика
./debug_helper.py

# CLI интерфейс
./ai_assistant_cli.py interactive
```

### Интеграция с IDE
```bash
# VS Code Remote Development
# Подключиться к контейнеру через Remote-Containers extension

# PyCharm Professional
# Настроить Docker interpreter
```

## 📚 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

### Документация
- [Docker Compose](https://docs.docker.com/compose/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Redis](https://redis.io/documentation)

### Полезные команды
```bash
# Очистка системы
docker system prune -a

# Обновление образов
docker-compose pull

# Проверка конфигурации
docker-compose config

# Экспорт переменных
docker-compose run --rm ai-assistant env
```

---

**🎉 Теперь у вас есть полная Docker инфраструктура для AI Assistant!** 