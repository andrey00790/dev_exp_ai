# 🚀 AI Assistant MVP - Deployment Guide

Полное руководство по развертыванию и настройке AI Assistant MVP с многопоточной загрузкой данных.

## 📋 Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Системные требования](#системные-требования)
3. [Конфигурация](#конфигурация)
4. [Запуск системы](#запуск-системы)
5. [Загрузка данных](#загрузка-данных)
6. [Мониторинг](#мониторинг)
7. [Устранение неполадок](#устранение-неполадок)

## 🚀 Быстрый старт

### 1. Запуск системы одной командой
```bash
./start_system.sh
```

### 2. Настройка источников данных
```bash
# Отредактируйте конфигурацию
nano local/config/local_config.yml

# Добавьте файлы для обучения
cp your-docs/* local/bootstrap/
```

### 3. Загрузка данных
```bash
./ingest_data.sh
```

### 4. Проверка работы
```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## 💻 Системные требования

### Минимальные требования
- **CPU:** 4 ядра
- **RAM:** 8 GB
- **Диск:** 50 GB свободного места
- **Docker:** 20.10+
- **Docker Compose:** 2.0+

### Рекомендуемые требования
- **CPU:** 8+ ядер
- **RAM:** 16+ GB
- **Диск:** 100+ GB SSD
- **Сеть:** Стабильное подключение к интернету

### Поддерживаемые ОС
- Ubuntu 20.04+
- CentOS 8+
- macOS 12+
- Windows 10+ (с WSL2)

## ⚙️ Конфигурация

### Основная конфигурация
Отредактируйте `local/config/local_config.yml`:

```yaml
# Confluence серверы
confluence:
  servers:
    - name: "main_confluence"
      url: "https://your-company.atlassian.net"
      username: "your-email@company.com"
      api_token: "your-confluence-api-token"
      spaces: ["TECH", "PROJ", "DOC"]

# GitLab серверы  
gitlab:
  servers:
    - name: "main_gitlab"
      url: "https://gitlab.company.com"
      token: "glpat-your-gitlab-token"
      groups: ["backend-team", "frontend-team"]

# Настройки обработки
processing:
  max_workers: 10
  batch_size: 50
  timeout_seconds: 300
```

### Переменные окружения
Создайте `.env` файл:

```env
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
SECRET_KEY=your-super-secret-key
ENVIRONMENT=production
DEBUG=false
```

### Локальные файлы
Поместите файлы для обучения в `local/bootstrap/`:
- PDF документы
- Текстовые файлы (.txt)
- Markdown файлы (.md)
- EPUB книги
- DOCX документы

## 🏗️ Запуск системы

### Базовая система
```bash
# Запуск основных сервисов
./start_system.sh

# С фронтендом
./start_system.sh --with-frontend

# С мониторингом
./start_system.sh --monitoring
```

### Ручной запуск
```bash
# Сборка образов
docker-compose -f docker-compose.full.yml build

# Запуск инфраструктуры
docker-compose -f docker-compose.full.yml up -d postgres redis qdrant

# Запуск приложения
docker-compose -f docker-compose.full.yml up -d backend
```

### Проверка статуса
```bash
# Статус контейнеров
docker-compose -f docker-compose.full.yml ps

# Логи
docker-compose -f docker-compose.full.yml logs -f backend

# Здоровье сервисов
curl http://localhost:8000/health
curl http://localhost:6333/health
```

## 📥 Загрузка данных

### Автоматическая загрузка
```bash
# Загрузка из всех настроенных источников
./ingest_data.sh

# Принудительная перезагрузка
./ingest_data.sh --force
```

### Ручная загрузка
```bash
# Запуск контейнера ingestion
docker-compose -f docker-compose.full.yml run --rm data_ingestion \
  python scripts/ingest_once.py /app/config/local_config.yml
```

### Мониторинг загрузки
```bash
# Просмотр логов загрузки
docker-compose -f docker-compose.full.yml logs -f data_ingestion

# Статистика в базе данных
docker exec ai_assistant_postgres psql -U ai_user -d ai_assistant \
  -c "SELECT source_type, COUNT(*) FROM ingested_documents GROUP BY source_type;"

# Статистика в Qdrant
curl http://localhost:6333/collections
```

## 📊 Доступные сервисы

| Сервис | URL | Описание |
|--------|-----|----------|
| API Server | http://localhost:8000 | Основной API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Qdrant UI | http://localhost:6333/dashboard | Векторная БД |
| Frontend | http://localhost:3000 | Веб-интерфейс |
| Grafana | http://localhost:3001 | Мониторинг |
| Prometheus | http://localhost:9090 | Метрики |

## 🔧 Настройка источников данных

### Confluence
1. Создайте API токен в Atlassian
2. Добавьте конфигурацию в `local_config.yml`
3. Укажите нужные пространства (spaces)

### GitLab
1. Создайте Personal Access Token
2. Добавьте права на чтение репозиториев
3. Настройте группы и проекты для сканирования

### Локальные файлы
1. Поместите файлы в `local/bootstrap/`
2. Поддерживаемые форматы: PDF, TXT, MD, EPUB, DOCX
3. Максимальный размер файла: 50MB

## 📈 Мониторинг

### Логи системы
```bash
# Все сервисы
docker-compose -f docker-compose.full.yml logs -f

# Конкретный сервис
docker-compose -f docker-compose.full.yml logs -f backend

# Логи ingestion
tail -f local/logs/ingestion.log
```

### Метрики производительности
```bash
# Статистика API
curl http://localhost:8000/api/v1/health

# Метрики Prometheus
curl http://localhost:8000/metrics

# Статистика Qdrant
curl http://localhost:6333/collections
```

### Мониторинг ресурсов
```bash
# Использование ресурсов контейнерами
docker stats

# Использование диска
df -h
du -sh local/
```

## 🛠️ Устранение неполадок

### Проблемы с запуском

**Ошибка: "Port already in use"**
```bash
# Найти процесс
lsof -ti:8000
# Остановить
kill -9 <PID>
```

**Ошибка: "Docker daemon not running"**
```bash
# Linux
sudo systemctl start docker

# macOS
open -a Docker
```

### Проблемы с базой данных

**PostgreSQL не запускается**
```bash
# Проверка логов
docker-compose -f docker-compose.full.yml logs postgres

# Пересоздание контейнера
docker-compose -f docker-compose.full.yml down
docker volume rm dev_exp_ai_postgres_data
docker-compose -f docker-compose.full.yml up -d postgres
```

**Qdrant недоступен**
```bash
# Проверка статуса
curl http://localhost:6333/health

# Перезапуск
docker-compose -f docker-compose.full.yml restart qdrant
```

### Проблемы с загрузкой данных

**Confluence API ошибки**
- Проверьте API токен
- Убедитесь в правильности URL
- Проверьте права доступа к пространствам

**GitLab API ошибки**
- Проверьте Personal Access Token
- Убедитесь в правах на чтение репозиториев
- Проверьте URL GitLab сервера

**Ошибки обработки файлов**
```bash
# Проверка формата файлов
file local/bootstrap/*

# Проверка размера
ls -lh local/bootstrap/

# Проверка кодировки
file -i local/bootstrap/*.txt
```

### Проблемы с производительностью

**Медленная загрузка данных**
- Увеличьте `max_workers` в конфигурации
- Уменьшите `batch_size` для снижения нагрузки на память
- Проверьте скорость интернет-соединения

**Высокое использование памяти**
- Уменьшите `batch_size`
- Ограничьте `max_file_size_mb`
- Увеличьте RAM или используйте swap

## 🔄 Обновление системы

### Обновление кода
```bash
git pull origin main
docker-compose -f docker-compose.full.yml build
docker-compose -f docker-compose.full.yml up -d
```

### Обновление данных
```bash
# Полная перезагрузка
./ingest_data.sh --force

# Добавление новых файлов
cp new-docs/* local/bootstrap/
./ingest_data.sh
```

### Резервное копирование
```bash
# Резервная копия базы данных
docker exec ai_assistant_postgres pg_dump -U ai_user ai_assistant > backup.sql

# Резервная копия Qdrant
docker exec ai_assistant_qdrant tar -czf - /qdrant/storage > qdrant_backup.tar.gz

# Резервная копия конфигурации
tar -czf config_backup.tar.gz local/config/
```

## 🆘 Получение помощи

### Логи для диагностики
```bash
# Сбор всех логов
mkdir -p debug_logs
docker-compose -f docker-compose.full.yml logs > debug_logs/all_services.log
cp local/logs/* debug_logs/
docker stats --no-stream > debug_logs/docker_stats.txt
```

### Контакты поддержки
- Документация: http://localhost:8000/docs
- Логи системы: `local/logs/`
- Конфигурация: `local/config/local_config.yml`

---

**Система готова к работе! 🎉**

Для получения дополнительной информации обратитесь к документации API или логам системы. 