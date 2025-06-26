# 🐳 DOCKER РАЗВЕРТЫВАНИЕ AI ASSISTANT

## 🚀 БЫСТРЫЙ СТАРТ (3 минуты)

```bash
# 1. Клонировать репозиторий
git clone <your-repo>
cd dev_exp_ai

# 2. Запустить все сервисы
./docker-commands.sh start

# 3. Проверить работу
curl http://localhost:8000/health
```

## 📋 ДОСТУПНЫЕ СЕРВИСЫ

После запуска доступны:

| Сервис | URL | Описание |
|--------|-----|----------|
| **API** | http://localhost:8000 | Основное приложение |
| **API Docs** | http://localhost:8000/docs | Swagger документация |
| **Health** | http://localhost:8000/health | Проверка здоровья |
| **Adminer** | http://localhost:8080 | Управление PostgreSQL |
| **Redis UI** | http://localhost:8081 | Управление Redis |

### Учетные данные
- **PostgreSQL**: `postgres` / `password`
- **Database**: `ai_assistant`
- **Redis**: без пароля

## 🛠️ КОМАНДЫ

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

# Статус сервисов
./docker-commands.sh status
make docker-status

# Логи всех сервисов
./docker-commands.sh logs
make docker-logs

# Логи конкретного сервиса
./docker-commands.sh logs ai-assistant
./docker-commands.sh logs postgres
./docker-commands.sh logs redis
```

### Команды разработки
```bash
# Пересобрать образы
./docker-commands.sh build
make docker-build

# Войти в контейнер приложения
./docker-commands.sh shell
make docker-shell

# Подключиться к PostgreSQL
./docker-commands.sh db
make docker-db

# Подключиться к Redis
./docker-commands.sh redis
make docker-redis

# Запустить тесты в контейнере
./docker-commands.sh test
make docker-test
```

### Команды очистки
```bash
# Очистить контейнеры и volumes (ОСТОРОЖНО!)
./docker-commands.sh clean
make docker-clean
```

## 🔧 НАСТРОЙКА

### Переменные окружения
Создайте `.env` файл в корне проекта:

```env
# Основные настройки
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here
LOG_LEVEL=INFO

# База данных
DATABASE_URL=postgresql://postgres:password@postgres:5432/ai_assistant

# AI сервисы (ОБЯЗАТЕЛЬНО!)
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Redis
REDIS_URL=redis://redis:6379

# Безопасность
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Файловая структура
```
dev_exp_ai/
├── docker-compose.local.yml    # Docker конфигурация
├── Dockerfile                  # Docker образ приложения
├── docker-commands.sh          # Удобные команды
├── requirements.txt            # Python зависимости
├── scripts/init-db.sql        # Инициализация БД
├── .env                       # Переменные окружения
└── app/                       # Код приложения
```

## 🧪 ТЕСТИРОВАНИЕ

### Быстрая проверка
```bash
# Проверка здоровья API
curl http://localhost:8000/health

# Проверка документации
curl http://localhost:8000/docs

# Быстрые тесты системы
python3 quick_test.py

# Диагностика
python3 debug_helper.py
```

### Тесты в контейнере
```bash
# Все тесты
./docker-commands.sh test

# Unit тесты
docker-compose -f docker-compose.local.yml exec ai-assistant python -m pytest tests/unit/ -v

# Integration тесты
docker-compose -f docker-compose.local.yml exec ai-assistant python -m pytest tests/integration/ -v
```

## 🔍 ОТЛАДКА

### Проверка статуса
```bash
# Статус всех контейнеров
./docker-commands.sh status

# Детальная информация
docker-compose -f docker-compose.local.yml ps
docker-compose -f docker-compose.local.yml top
```

### Анализ логов
```bash
# Логи всех сервисов
./docker-commands.sh logs

# Логи с фильтрацией
./docker-commands.sh logs ai-assistant | grep ERROR
./docker-commands.sh logs postgres | grep ERROR
```

### Подключение к сервисам
```bash
# Войти в контейнер приложения
./docker-commands.sh shell

# Подключиться к PostgreSQL
./docker-commands.sh db
# или через Adminer: http://localhost:8080

# Подключиться к Redis
./docker-commands.sh redis
# или через Redis Commander: http://localhost:8081
```

### Проверка ресурсов
```bash
# Использование ресурсов
docker stats

# Использование диска
docker system df

# Проверка volumes
docker volume ls
```

## 🚨 ЧАСТЫЕ ПРОБЛЕМЫ

### 1. Контейнер не запускается
```bash
# Проверить логи
./docker-commands.sh logs ai-assistant

# Проверить конфигурацию
docker-compose -f docker-compose.local.yml config

# Пересобрать образ
./docker-commands.sh build
```

### 2. База данных недоступна
```bash
# Проверить статус PostgreSQL
docker-compose -f docker-compose.local.yml exec postgres pg_isready -U postgres

# Проверить логи БД
./docker-commands.sh logs postgres

# Пересоздать БД (ОСТОРОЖНО!)
./docker-commands.sh clean
./docker-commands.sh start
```

### 3. Порты заняты
```bash
# Проверить занятые порты
netstat -tlnp | grep -E "(8000|5432|6379|8080|8081)"

# Остановить конфликтующие сервисы
sudo systemctl stop postgresql
sudo systemctl stop redis-server
```

### 4. Недостаточно места на диске
```bash
# Очистить неиспользуемые образы
docker system prune -a

# Очистить volumes (ОСТОРОЖНО!)
docker volume prune
```

## 📊 МОНИТОРИНГ

### Health checks
```bash
# Проверка здоровья приложения
curl http://localhost:8000/health

# Проверка всех сервисов
./docker-commands.sh status
```

### Логирование
```bash
# Централизованные логи
./docker-commands.sh logs

# Логи с временными метками
docker-compose -f docker-compose.local.yml logs -f --timestamps

# Логи с фильтрацией
./docker-commands.sh logs ai-assistant | grep -E "(ERROR|WARNING)"
```

### Резервное копирование
```bash
# Бэкап базы данных
docker-compose -f docker-compose.local.yml exec postgres pg_dump -U postgres ai_assistant > backup.sql

# Восстановление БД
cat backup.sql | docker-compose -f docker-compose.local.yml exec -T postgres psql -U postgres ai_assistant
```

## 🎯 РЕКОМЕНДАЦИИ

### Для разработки
1. **Используйте hot reload**: код автоматически перезагружается
2. **Мониторьте логи**: `./docker-commands.sh logs`
3. **Регулярно обновляйте образы**: `./docker-commands.sh build`

### Для продакшн
1. **Измените пароли** в .env файле
2. **Настройте SSL** сертификаты
3. **Включите мониторинг** и алерты
4. **Настройте резервное копирование**

### Безопасность
1. **Не коммитьте .env** файлы в git
2. **Используйте сильные пароли**
3. **Ограничьте доступ к портам**
4. **Регулярно обновляйте зависимости**

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

- **Make команды**: `make help`
- **Docker команды**: `./docker-commands.sh help`
- **Быстрые тесты**: `python3 quick_test.py`
- **Диагностика**: `python3 debug_helper.py`
- **CLI интерфейс**: `python3 ai_assistant_cli.py`

---

**🎉 AI Assistant готов к использованию с Docker!** 