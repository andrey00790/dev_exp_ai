# 🚀 Quick Start Development Guide

## 📋 **Немедленные действия (следующие 2 недели)**

### **Day 1-2: Автоматизация инфраструктуры**

#### **1. Подключение недостающих роутеров** ⚡
```bash
# Сканирование всех роутеров в проекте
python tools/scripts/router_integration_tool.py --scan

# Подключение высокоприоритетных роутеров
python tools/scripts/router_integration_tool.py --connect --priority=high

# Тестирование подключения
python tools/scripts/router_integration_tool.py --test
```

**Ожидаемый результат:** Подключено 15-20 критичных роутеров (AI, search, documents, health)

#### **2. Исправление failed тестов** ⚡
```bash
# Анализ всех failed тестов
python tools/scripts/test_fixer_tool.py --analyze

# Автоматическое исправление import ошибок
python tools/scripts/test_fixer_tool.py --fix --category=imports

# Исправление enum сравнений  
python tools/scripts/test_fixer_tool.py --fix --category=enum_comparison

# Повторный запуск тестов
python tools/scripts/test_fixer_tool.py --run
```

**Ожидаемый результат:** Success rate 77% → 85%+ (исправлено 50+ тестов)

### **Day 3-5: Базовая функциональность**

#### **3. Базовые endpoints**
```bash
# Проверка работы базовых маршрутов
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health  
curl http://localhost:8000/docs

# Запуск приложения для проверки
python main.py --port 8000 --host localhost
```

#### **4. Подключение medium priority роутеров**
```bash
# Подключение роутеров среднего приоритета
python tools/scripts/router_integration_tool.py --connect --priority=medium

# Проверка OpenAPI схемы
curl http://localhost:8000/openapi.json | jq '.paths | keys | length'
```

**Ожидаемый результат:** 40+ эндпоинтов доступны через API

### **Day 6-10: Стабилизация**

#### **5. Исправление оставшихся тестов**
```bash
# Исправление по приоритету
python tools/scripts/test_fixer_tool.py --fix --priority=high
python tools/scripts/test_fixer_tool.py --fix --priority=medium

# Запуск всех тестов
make test-quick
```

#### **6. Проверка интеграции**
```bash
# Проверка планировщика синхронизации данных
curl http://localhost:8000/api/v1/data-sync/health

# Проверка бюджет системы (с авторизацией)
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/v1/budget/status

# Проверка VK Teams (если настроен)
curl http://localhost:8000/api/v1/vk-teams/bot/health
```

**Ожидаемый результат:** 90%+ тестов проходят, все системы работают

---

## 🛠 **Инструменты разработки**

### **Router Integration Tool** 🔧
```bash
# Просмотр всех найденных роутеров
python tools/scripts/router_integration_tool.py --scan

# Подключение по категориям
python tools/scripts/router_integration_tool.py --connect --priority=high
python tools/scripts/router_integration_tool.py --connect --priority=medium
python tools/scripts/router_integration_tool.py --connect --priority=low

# Тестирование конкретного роутера
python tools/scripts/router_integration_tool.py --test --router=health
```

### **Test Fixer Tool** 🧪
```bash
# Анализ ошибок по категориям
python tools/scripts/test_fixer_tool.py --analyze

# Исправление по типу ошибок
python tools/scripts/test_fixer_tool.py --fix --category=imports
python tools/scripts/test_fixer_tool.py --fix --category=attributes  
python tools/scripts/test_fixer_tool.py --fix --category=async_await
python tools/scripts/test_fixer_tool.py --fix --category=mocks
python tools/scripts/test_fixer_tool.py --fix --category=enum_comparison

# Исправление по приоритету
python tools/scripts/test_fixer_tool.py --fix --priority=high

# Запуск конкретных тестов
python tools/scripts/test_fixer_tool.py --run --pattern="tests/unit/test_auth*"
```

### **Manual Commands** 📝
```bash
# Тестирование
make unit                    # Unit тесты
make integration             # Integration тесты  
make test-quick             # Быстрые тесты
make coverage               # Test coverage

# Разработка
make lint                   # Линтинг
make format                 # Форматирование
make type-check             # Type checking

# Приложение
python main.py --port 8000  # Запуск сервера
python main.py --demo       # Демо архитектуры
```

---

## 📊 **Контроль прогресса**

### **Еженедельные метрики:**

#### **Неделя 1 цели:**
- [ ] **20+ роутеров подключено** (текущий: 5)
- [ ] **85%+ success rate тестов** (текущий: 77%)
- [ ] **Все базовые endpoints работают** (/health, /docs, etc.)
- [ ] **Data sync scheduler работает** (Confluence, GitLab, Jira)

#### **Неделя 2 цели:**
- [ ] **40+ роутеров подключено** (67% от общего количества)
- [ ] **90%+ success rate тестов** (1000+ тестов проходят)
- [ ] **AI endpoints работают** (генерация, поиск, анализ)
- [ ] **Frontend интеграция** (React + WebSocket)

### **Команды для проверки прогресса:**

#### **Роутеры:**
```bash
# Подсчет подключенных роутеров
grep -c "include_router" main.py

# Проверка endpoints в OpenAPI
curl -s http://localhost:8000/openapi.json | jq '.paths | keys | length'

# Список всех endpoints
curl -s http://localhost:8000/openapi.json | jq '.paths | keys'
```

#### **Тесты:**
```bash
# Быстрая статистика тестов
pytest tests/unit/ --tb=no -q | tail -1

# Детальная статистика
python tools/scripts/test_fixer_tool.py --analyze | grep "Success Rate"

# Coverage
coverage run -m pytest tests/unit/ && coverage report | grep "TOTAL"
```

#### **Системы:**
```bash
# Проверка health всех систем
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/data-sync/health
curl http://localhost:8000/api/v1/budget/health  # если реализован

# Проверка планировщика синхронизации
curl http://localhost:8000/api/v1/data-sync/health | jq .
```

---

## ⚡ **Быстрые команды**

### **Ежедневная рутина:**
```bash
# 1. Запуск и проверка приложения
python main.py --port 8000 &
sleep 5
curl http://localhost:8000/health

# 2. Запуск тестов
make test-quick

# 3. Проверка новых роутеров
python tools/scripts/router_integration_tool.py --scan

# 4. Исправление тестов если нужно
python tools/scripts/test_fixer_tool.py --analyze
```

### **Перед коммитом:**
```bash
# Полная проверка
make lint && make type-check && make test-quick
```

### **Еженедельная проверка:**
```bash
# Полная статистика
echo "=== ROUTER COVERAGE ==="
python tools/scripts/router_integration_tool.py --scan

echo "=== TEST RESULTS ==="  
python tools/scripts/test_fixer_tool.py --analyze

echo "=== API ENDPOINTS ==="
curl -s http://localhost:8000/openapi.json | jq '.paths | keys | length'
```

---

## 🎯 **Критические задачи первой недели**

### **Понедельник:**
1. ✅ Запустить router scanner
2. ✅ Подключить health endpoints  
3. ✅ Исправить 20+ import ошибок

### **Вторник:**
1. ✅ Подключить AI роутеры (generate, search)
2. ✅ Исправить enum сравнения
3. ✅ Проверить data sync scheduler

### **Среда:**
1. ✅ Подключить documents роутеры
2. ✅ Исправить async/await ошибки  
3. ✅ Обновить OpenAPI документацию

### **Четверг:**
1. ✅ Подключить monitoring роутеры
2. ✅ Исправить mock setup ошибки
3. ✅ Проверить все endpoints

### **Пятница:**  
1. ✅ Финальное тестирование
2. ✅ Документирование изменений
3. ✅ Планирование следующей недели

---

**📌 Эта стратегия даст быстрый, измеримый прогресс с минимальными рисками.** 