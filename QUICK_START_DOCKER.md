# 🚀 Quick Start - Unified Docker Compose

## ✅ Готово! Docker Compose объединен и работает

### 🎯 **Основные команды (всё через make)**

```bash
# Базовые сервисы  
make up                    # app + postgres + redis + qdrant

# Разработка
make up-dev               # + админ панели (Adminer, Redis UI)
make up-dev-full          # + frontend + monitoring (Grafana, Prometheus)  
make up-dev-llm           # + локальные LLM (Ollama)

# Тестирование
make up-load              # Нагрузочные тесты (Locust)
make up-e2e               # E2E тесты (Playwright + Jira/Confluence/GitLab)

# ETL
make bootstrap            # Загрузка данных (GitLab + Confluence)
```

### 📊 **Статус и мониторинг**

```bash
make status               # Статус всех сервисов
make status-detailed      # Детальный статус + health checks
make logs                 # Логи основных сервисов
make logs-load            # Логи нагрузочных тестов
```

### 🛑 **Остановка**

```bash
make down                 # Остановить все сервисы
make restart              # Перезапустить основные сервисы
```

## 🌐 **Доступные сервисы**

### **Core (по умолчанию)**
- **App**: http://localhost:8000
- **Docs**: http://localhost:8000/docs  
- **Health**: http://localhost:8000/health

### **Admin Tools (профиль: admin)**
- **Adminer**: http://localhost:8080 (БД админка)
- **Redis UI**: http://localhost:8081

### **Load Testing (профиль: load)**
- **Load App**: http://localhost:8002
- **Locust UI**: http://localhost:8089 (нагрузочные тесты)
- **Nginx LB**: http://localhost:8085

### **Monitoring (профиль: monitoring)**
- **Grafana**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090

### **E2E Testing (профиль: e2e)**
- **E2E App**: http://localhost:8001
- **Jira**: http://localhost:8082  
- **Confluence**: http://localhost:8083
- **GitLab**: http://localhost:8084

## 💾 **Данные сохраняются локально**

```
./data/
├── postgres/      # База данных
├── qdrant/        # Векторная БД  
├── redis/         # Кэш
├── prometheus/    # Метрики
├── grafana/       # Дашборды
├── e2e/          # E2E данные
└── load/         # Load test данные
```

**Данные сохраняются между перезапусками!**

## 🎮 **Примеры использования**

### **Быстрый старт разработки**
```bash
make up-dev
# Откроется: App + Adminer + Redis UI
```

### **Полная разработка**  
```bash
make up-dev-full
# Всё + Frontend + Monitoring
```

### **Нагрузочное тестирование**
```bash
make up-load
# Откройте http://localhost:8089
# Настройте: 50 users, spawn rate 2
# Host: http://load-app:8000
```

### **Мониторинг состояния**
```bash
# Быстрая проверка
curl http://localhost:8000/health

# Детальный статус
make status-detailed
```

## 🔧 **Устранение проблем**

### **Порты заняты**
```bash
# Остановить все контейнеры
make down
docker stop $(docker ps -aq) 2>/dev/null || true

# Перезапустить
make up
```

### **Нет данных**
```bash
# Проверить директории
ls -la data/

# Пересоздать директории
make setup-data-dirs
```

### **Медленный запуск**
```bash
# E2E окружение большое (~15 минут)
# Load окружение быстрое (~1 минута)
# Core сервисы очень быстрые (~30 секунд)
```

## 🏆 **Что изменилось**

| До | После |
|----|----|
| 15+ отдельных compose файлов | 1 unified docker-compose.yml |
| Сложная настройка окружений | Простые `make up-*` команды |
| Docker volumes | Локальные директории `./data/` |
| Конфликты портов | Четкое разделение по профилям |
| Ручная настройка | "Запустил и забыл" |

**Система готова к production!** 🎉 