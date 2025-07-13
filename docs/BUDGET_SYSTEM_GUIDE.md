# Система управления бюджетами AI Assistant

## Обзор системы

Система управления бюджетами предоставляет комплексное решение для контроля расходов на LLM API и автоматического пополнения бюджетов пользователей. Система включает:

- **Автоматическое пополнение бюджетов** по расписанию
- **Гибкую конфигурацию** для разных типов пользователей
- **Мониторинг и аналитику** использования бюджетов
- **API для управления** бюджетами вручную
- **Уведомления** о состоянии бюджетов

## Основные компоненты

### 1. Конфигурация системы

Система настраивается через файл `config/budget_config.yml`:

```yaml
# Основные настройки автоматического пополнения
auto_refill:
  enabled: true
  schedule:
    cron: "0 0 * * *"  # Каждый день в полночь
    timezone: "Europe/Moscow"
  refill_settings:
    refill_type: "reset"  # reset или add
    by_role:
      admin:
        amount: 10000.0
        reset_usage: true
      user:
        amount: 1000.0
        reset_usage: true
```

### 2. Сервис управления бюджетами

`app/services/budget_service.py` - основной сервис, который:
- Управляет планировщиком автоматического пополнения
- Выполняет пополнение бюджетов по расписанию
- Предоставляет API для ручного управления
- Ведет историю операций

### 3. API эндпоинты

`app/api/v1/budget_management.py` - REST API для управления бюджетами:
- `GET /api/v1/budget/status` - статус бюджета
- `POST /api/v1/budget/refill` - ручное пополнение
- `GET /api/v1/budget/history` - история операций
- `GET /api/v1/budget/system-stats` - статистика системы

## Использование системы

### Как пользователю проверить свой бюджет

```bash
# Авторизация
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "user123"}'

# Получение токена из ответа
TOKEN="your_jwt_token_here"

# Проверка статуса бюджета
curl -X GET http://localhost:8000/api/v1/budget/status \
  -H "Authorization: Bearer $TOKEN"
```

**Ответ:**
```json
{
  "user_id": "user_001",
  "email": "user@example.com",
  "current_usage": 25.50,
  "budget_limit": 1000.0,
  "remaining_balance": 974.50,
  "usage_percentage": 2.55,
  "budget_status": "ACTIVE",
  "last_refill": {
    "amount": 1000.0,
    "timestamp": "2024-01-15T00:00:00Z",
    "type": "reset"
  },
  "total_refills": 5,
  "total_refilled": 5000.0
}
```

### Как администратору пополнить бюджет пользователя

```bash
# Авторизация как администратор
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@vkteam.ru", "password": "admin"}'

# Ручное пополнение бюджета
curl -X POST http://localhost:8000/api/v1/budget/refill \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "amount": 500.0,
    "refill_type": "add",
    "reason": "Дополнительное пополнение для проекта"
  }'
```

### Как получить историю пополнений

```bash
# Свою историю (для обычного пользователя)
curl -X GET http://localhost:8000/api/v1/budget/history \
  -H "Authorization: Bearer $TOKEN"

# Историю всех пользователей (для администратора)
curl -X GET http://localhost:8000/api/v1/budget/history \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Историю конкретного пользователя (для администратора)
curl -X GET "http://localhost:8000/api/v1/budget/history?user_id=user_001&limit=50" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Автоматическое пополнение бюджетов

### Настройка расписания

Система поддерживает различные типы расписаний:

#### 1. Cron-выражения
```yaml
schedule:
  cron: "0 0 * * *"    # Каждый день в полночь
  cron: "0 0 1 * *"    # Первое число каждого месяца
  cron: "0 0 * * 1"    # Каждый понедельник
```

#### 2. Простые интервалы
```yaml
schedule:
  interval_type: "daily"   # daily, weekly, monthly, hourly
  interval_value: 1        # каждый N дней/недель/месяцев
```

### Типы пополнения

#### Reset (сброс)
```yaml
refill_type: "reset"
```
- Сбрасывает `current_usage` до 0
- Устанавливает `budget_limit` равным сумме пополнения
- Эффективно "обнуляет" счетчик потраченного

#### Add (добавление)
```yaml
refill_type: "add"
```
- Добавляет сумму к существующему `budget_limit`
- Не сбрасывает `current_usage`
- Позволяет накапливать неиспользованные средства

### Настройка по ролям

```yaml
refill_settings:
  by_role:
    admin:
      enabled: true
      amount: 10000.0
      reset_usage: true
    user:
      enabled: true
      amount: 1000.0
      reset_usage: true
    basic:
      enabled: true
      amount: 100.0
      reset_usage: true
```

### Индивидуальные настройки

```yaml
individual_users:
  "admin@vkteam.ru":
    enabled: true
    amount: 15000.0
    reset_usage: true
    custom_schedule: "0 0 1 * *"  # Раз в месяц
  "premium@example.com":
    enabled: true
    amount: 2000.0
    reset_usage: true
    custom_schedule: "0 0 * * 1"  # Каждый понедельник
```

## Мониторинг и аналитика

### Статистика системы

```bash
# Получение статистики (только для администраторов)
curl -X GET http://localhost:8000/api/v1/budget/system-stats \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Ответ:**
```json
{
  "total_refills": 156,
  "successful_refills": 155,
  "failed_refills": 1,
  "success_rate": 0.994,
  "total_amount_refilled": 125000.0,
  "average_refill_amount": 806.45,
  "recent_refills_24h": 12,
  "recent_amount_24h": 8500.0,
  "last_refill": "2024-01-15T00:00:00Z",
  "scheduler_running": true
}
```

### Метрики для мониторинга

```bash
# Получение метрик в формате Prometheus
curl -X GET http://localhost:8000/api/v1/budget/monitoring/budget/metrics \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Управление планировщиком

```bash
# Перезапуск планировщика
curl -X POST http://localhost:8000/api/v1/budget/scheduler/restart \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Запуск пополнения немедленно
curl -X POST http://localhost:8000/api/v1/budget/scheduler/run-now \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Уведомления

### Email уведомления

```yaml
notifications:
  enabled: true
  email:
    enabled: true
    send_on_refill: true
    send_on_low_balance: true
    send_on_emergency_refill: true
    templates:
      refill_success: "Ваш бюджет пополнен на $${amount}. Текущий баланс: $${balance}"
      low_balance: "Низкий остаток бюджета: $${balance}. Лимит: $${limit}"
```

### Webhook уведомления

```yaml
notifications:
  webhook:
    enabled: true
    url: "${BUDGET_WEBHOOK_URL}"
    timeout: 30
    retry_count: 3
```

## Безопасность

### Лимиты безопасности

```yaml
security:
  max_limits:
    single_refill: 100000.0
    daily_total: 500000.0
    monthly_total: 2000000.0
  
  abuse_protection:
    enabled: true
    max_refills_per_day: 10
    max_refills_per_user_per_day: 5
```

### Аудит

```yaml
security:
  audit:
    enabled: true
    log_all_changes: true
    require_approval_above: 50000.0
```

## Интеграция с системой стоимости

### Автоматическое списание

Система интегрирована с `app/security/cost_control.py`:

```python
from app.services.budget_service import get_user_budget_info
from app.security.cost_control import track_llm_request

# Проверка бюджета перед запросом
budget_info = await get_user_budget_info(user_id)
if budget_info["remaining_balance"] < estimated_cost:
    raise HTTPException(402, "Insufficient budget")

# Списание после использования
await track_llm_request(
    user_id=user_id,
    provider="openai",
    model="gpt-4",
    endpoint="/api/v1/generate",
    prompt_tokens=100,
    completion_tokens=50,
    duration_ms=1500
)
```

### Бонусные пополнения

```yaml
bonus_refills:
  enabled: true
  conditions:
    high_usage:
      threshold: 0.9  # 90% использования
      bonus_percent: 0.1  # 10% бонус
    low_usage:
      threshold: 0.3  # 30% использования
      bonus_percent: -0.1  # 10% уменьшение
```

## Разработка и тестирование

### Ускоренный режим для тестирования

```yaml
development:
  fast_mode:
    enabled: true
    interval_seconds: 60  # Пополнение каждую минуту
  
  debug:
    enabled: true
    log_level: "DEBUG"
    detailed_logging: true
```

### Тестовые пользователи

```bash
# Создание тестового пользователя
python create_user.py create test@example.com --password test123 --name "Test User"

# Создание admin пользователя
python create_user.py create testadmin@example.com --password admin123 --name "Test Admin" --admin

# Ручное пополнение для тестирования
python create_user.py manual-refill test@example.com 500.0
```

## Миграции и обновления

### Структура базы данных

```sql
-- Таблица истории пополнений
CREATE TABLE budget_refill_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    refill_type VARCHAR(50) NOT NULL,
    previous_balance DECIMAL(10,2),
    new_balance DECIMAL(10,2),
    status VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    metadata JSONB
);

-- Таблица конфигурации бюджетов
CREATE TABLE budget_user_config (
    user_id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    amount DECIMAL(10,2) NOT NULL,
    reset_usage BOOLEAN DEFAULT TRUE,
    custom_schedule VARCHAR(255),
    last_refill TIMESTAMP,
    refill_count INTEGER DEFAULT 0,
    total_refilled DECIMAL(10,2) DEFAULT 0
);

-- Таблица аудита
CREATE TABLE budget_audit_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    action VARCHAR(255) NOT NULL,
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    performer_id VARCHAR(255)
);
```

## Решение проблем

### Частые проблемы

#### 1. Планировщик не запускается
```bash
# Проверка логов
tail -f app.log | grep budget

# Проверка конфигурации
python -c "
import yaml
with open('config/budget_config.yml') as f:
    config = yaml.safe_load(f)
    print(config['auto_refill']['enabled'])
"

# Ручной запуск
curl -X POST http://localhost:8000/api/v1/budget/scheduler/restart \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### 2. Пополнение не происходит
```bash
# Проверка статуса планировщика
curl -X GET http://localhost:8000/api/v1/budget/system-stats \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Ручное выполнение пополнения
curl -X POST http://localhost:8000/api/v1/budget/scheduler/run-now \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### 3. Ошибки прав доступа
```bash
# Проверка скопов пользователя
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Создание admin пользователя
python create_user.py create admin@example.com --password admin123 --admin
```

### Логи и отладка

```bash
# Включение подробного логирования
export LOG_LEVEL=DEBUG

# Просмотр логов бюджетной системы
tail -f app.log | grep -E "(budget|refill|scheduler)"

# Просмотр статистики в реальном времени
watch -n 5 'curl -s -X GET http://localhost:8000/api/v1/budget/system-stats \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq'
```

## Примеры использования

### Сценарий 1: Настройка для команды разработки

```yaml
# config/budget_config.yml
auto_refill:
  enabled: true
  schedule:
    cron: "0 9 * * 1"  # Каждый понедельник в 9:00
  refill_settings:
    refill_type: "reset"
    by_role:
      admin:
        amount: 5000.0
        reset_usage: true
      user:
        amount: 1000.0
        reset_usage: true
      basic:
        amount: 200.0
        reset_usage: true
    individual_users:
      "lead@company.com":
        amount: 2000.0
        reset_usage: true
      "architect@company.com":
        amount: 3000.0
        reset_usage: true
```

### Сценарий 2: Настройка для продакшена

```yaml
# config/budget_config.yml
auto_refill:
  enabled: true
  schedule:
    cron: "0 0 1 * *"  # Первое число каждого месяца
  refill_settings:
    refill_type: "add"  # Накопление неиспользованных средств
    by_role:
      admin:
        amount: 10000.0
        reset_usage: false
      user:
        amount: 500.0
        reset_usage: false
    max_accumulation:
      enabled: true
      multiplier: 3.0  # Максимум в 3 раза больше лимита
```

### Сценарий 3: Настройка для тестирования

```yaml
# config/budget_config.yml
auto_refill:
  enabled: true
  schedule:
    cron: "*/5 * * * *"  # Каждые 5 минут
  refill_settings:
    refill_type: "reset"
    by_role:
      admin:
        amount: 1000.0
        reset_usage: true
      user:
        amount: 100.0
        reset_usage: true
development:
  fast_mode:
    enabled: true
    interval_seconds: 300  # 5 минут
  debug:
    enabled: true
    log_level: "DEBUG"
```

## Мониторинг производительности

### Ключевые метрики

1. **Время выполнения пополнения** - должно быть < 30 секунд
2. **Успешность пополнений** - должна быть > 99%
3. **Использование памяти** - мониторинг через psutil
4. **Количество активных пользователей** - отслеживание роста

### Alerting

```yaml
# config/budget_config.yml
monitoring:
  alerts:
    enabled: true
    high_usage_alert:
      threshold: 1000000.0  # $1M в день
    error_alert:
      error_rate_threshold: 0.05  # 5% ошибок
    suspicious_activity:
      multiple_refills_threshold: 10  # 10 пополнений в день
```

## Заключение

Система управления бюджетами предоставляет мощные инструменты для:
- Автоматического управления расходами на LLM API
- Гибкой настройки лимитов для разных типов пользователей
- Мониторинга и аналитики использования
- Предотвращения превышения бюджетов

Для получения дополнительной помощи обращайтесь к документации API или используйте встроенные эндпоинты для диагностики. 