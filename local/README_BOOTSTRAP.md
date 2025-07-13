# 🎓 AI Assistant Bootstrap Обучение

Система локального обучения AI Assistant данными из различных источников.

## 🚀 Быстрый старт

### 1. Настройка переменных окружения

```bash
# Скопируйте template и заполните реальными данными
cp .env.local.template .env.local
nano .env.local
```

### 2. Запуск инфраструктуры

```bash
# Из корневой директории проекта
make dev-infra-up
```

### 3. Быстрое тестовое обучение

```bash
# Загрузка ограниченного набора данных (для тестирования)
make local-bootstrap-quick
```

### 4. Полное обучение

```bash
# Загрузка всех настроенных источников
make local-bootstrap
```

## 📋 Доступные команды

### Основные команды
- `make local-bootstrap` - Полное обучение всеми данными
- `make local-bootstrap-quick` - Быстрое тестовое обучение  
- `make local-bootstrap-status` - Статус обучения и количество документов
- `make local-bootstrap-clean` - Очистка всех данных

### Источники данных
- `make local-bootstrap-confluence` - Только Confluence
- `make local-bootstrap-gitlab` - Только GitLab
- `make local-bootstrap-files` - Только локальные файлы

### Утилиты
- `make local-setup` - Полная настройка с нуля

## 🔧 Конфигурация

### local_bootstrap_config.yml

Основной конфигурационный файл содержит настройки для:

#### 📖 Confluence
```yaml
confluence:
  enabled: true
  url: "https://your-company.atlassian.net" 
  username: "ai-assistant@company.com"
  api_token: "${CONFLUENCE_API_TOKEN}"
  spaces:
    - "TECH"  # Техническая документация
    - "PROJ"  # Проектная документация
    - "ARCH"  # Архитектура
```

#### 🦊 GitLab
```yaml
gitlab_servers:
  - name: "main_gitlab"
    url: "https://gitlab.company.com"
    api_token: "${GITLAB_API_TOKEN}"
    groups:
      - "backend-team"
      - "frontend-team"
      - "devops-team"
```

#### 📁 Локальные файлы
```yaml
local_files:
  bootstrap_directory: "./local/bootstrap"
  additional_directories:
    - "./docs"
    - "./training_data"
  supported_formats:
    - ".pdf"
    - ".docx" 
    - ".txt"
    - ".md"
```

## 🔐 Настройка доступов

### Confluence API Token
1. Перейдите в https://id.atlassian.com/manage-profile/security/api-tokens
2. Создайте новый API token
3. Добавьте в `.env.local`:
   ```
   CONFLUENCE_API_TOKEN=ATB...xyz
   ```

### GitLab API Token  
1. GitLab → User Settings → Access Tokens
2. Права: `api`, `read_repository`, `read_user`
3. Добавьте в `.env.local`:
   ```
   GITLAB_API_TOKEN=glpat-xyz...
   ```

## 📊 Мониторинг процесса

### Проверка статуса
```bash
make local-bootstrap-status
```

Покажет:
- Количество векторов в Qdrant
- Количество файлов в bootstrap директории
- Статистику по категориям

### Логи
```bash
# Логи находятся в
tail -f logs/bootstrap.log
```

### Qdrant Dashboard
Откройте http://localhost:6333/dashboard для просмотра коллекций

## 🗂️ Структура данных

### Bootstrap директория
```
local/bootstrap/
├── academic/           # Академические материалы
├── system_design/      # Системный дизайн  
├── language_python/    # Python ресурсы
├── cloud_aws/         # AWS материалы
├── security/          # Безопасность
└── ...
```

### Метаданные
Каждый загруженный файл имеет соответствующий `.json` файл с метаданными:
```json
{
  "name": "Awesome Python",
  "category": "language_python", 
  "url": "https://github.com/vinta/awesome-python",
  "downloaded_at": "2024-01-01T12:00:00",
  "file_size": 1024
}
```

## ⚡ Режимы работы

### Быстрый тест (`quick_test`)
- Confluence: 5 страниц
- GitLab: 10 файлов  
- Локальные: 20 файлов
- Время: ~2-3 минуты

### Полная загрузка (`full_load`)
- Все настроенные лимиты
- Confluence: до 500 страниц
- GitLab: до 1000 файлов
- Время: ~15-30 минут

### Инкрементальная (`incremental`)
- Только новые/измененные файлы
- Проверка по дате модификации
- Время: ~5-10 минут

## 🔧 Устранение проблем

### Confluence недоступен
```bash
# Проверьте настройки
curl -u "email:token" "https://your-company.atlassian.net/wiki/rest/api/space"
```

### GitLab недоступен  
```bash
# Проверьте токен
curl --header "PRIVATE-TOKEN: your_token" "https://gitlab.company.com/api/v4/user"
```

### Qdrant недоступен
```bash
# Проверьте подключение
curl http://localhost:6333/collections
```

### Очистка при проблемах
```bash
# Полная очистка и перезапуск
make local-bootstrap-clean
make dev-infra-down
make dev-infra-up
make local-bootstrap-quick
```

## 🎯 Лучшие практики

### 1. Тестируйте сначала
Всегда начинайте с `make local-bootstrap-quick`

### 2. Следите за лимитами
Настройте разумные лимиты в конфигурации

### 3. Регулярные обновления  
Запускайте инкрементальное обучение еженедельно

### 4. Мониторинг ресурсов
Следите за использованием диска и памяти

### 5. Backup данных
Регулярно сохраняйте bootstrap директорию

## 🔗 Связанные файлы

- `local_bootstrap_config.yml` - Основная конфигурация
- `bootstrap_fetcher.py` - Загрузчик материалов
- `ingest_bootstrap.py` - Обработчик для Qdrant
- `resource_config.yml` - Ресурсы для загрузки
- `.env.local` - Локальные переменные окружения 