# 🤖 AI Development Agents - Rules & Standards

**Версия:** 1.0
**Дата:** 16 июня 2025
**Статус:** ✅ Актуальные правила разработки

## 🎯 **Текущий статус проекта**

### ✅ **MVP ЗАВЕРШЕН (100%)**
Все 6 итераций развития успешно завершены. Система готова к production deployment.

### 🚀 **Следующая фаза: Production Security**
**Приоритет 1**: Реализация аутентификации и безопасности
**Приоритет 2**: Performance optimization
**Приоритет 3**: Feature enhancement

## 📋 **Правила разработки**

### **1. Принцип атомарности**
- Каждая задача должна быть завершена полностью
- Не переходить к следующей задаче без завершения текущей
- Обязательное тестирование после каждого изменения

### **2. Quality Gates**
```python
# Перед завершением любой задачи:
- [ ] Unit tests проходят (если есть)
- [ ] Integration tests работают
- [ ] API endpoints отвечают корректно
- [ ] Frontend компилируется без ошибок
- [ ] Нет критических security issues
```

### **3. Security First**
- Любой API endpoint должен иметь аутентификацию
- Валидация всех входных данных
- Rate limiting для дорогих операций
- Логирование всех действий пользователей

## 🛠️ **Development Workflow**

### **Phase 1: Production Security (CURRENT)**

#### **Task 1.1: JWT Authentication (2 дня)**
```python
# Требования:
1. Создать app/security/auth.py с JWT implementation
2. Добавить authentication middleware ко всем API routes
3. Создать login/logout UI components
4. Написать unit tests для auth системы

# Критерии готовности:
- [ ] Все 71 API endpoints требуют authentication
- [ ] JWT tokens работают (access + refresh)
- [ ] Login/logout через GUI работает
- [ ] Rate limiting: 10 requests/minute для AI endpoints
- [ ] Unit tests покрывают auth logic

# Acceptance Test:
curl -X POST http://localhost:8000/api/v1/search  # Should return 401
```

#### **Task 1.2: Cost Control (1 день)**
```python
# Требования:
1. Добавить user_budgets таблицу в PostgreSQL
2. Создать cost tracking для LLM API calls
3. Добавить budget checking middleware
4. Создать cost dashboard в Settings UI

# Критерии готовности:
- [ ] User budgets сохраняются в DB
- [ ] Cost tracking работает для OpenAI/Anthropic calls
- [ ] Budget exceeded блокирует дальнейшие вызовы
```

#### **Task 1.3: Security Hardening (1-2 дня)**
```bash
# Требования:
1. Обновить все зависимости с уязвимостями
2. Добавить input validation middleware
3. Настроить security headers

# Критерии готовности:
- [ ] Vulnerable dependencies < 5 (текущий: 42)
- [ ] Input validation на всех POST/PUT endpoints
- [ ] Security headers настроены
```

## 🎯 **Next Action Protocol**

### **Когда получаешь команду "приступай к следующему шагу":**

1. **Проверить текущий статус** в ROADMAP.md
2. **Определить следующую задачу** из Phase 1
3. **Начать с Task 1.1: JWT Authentication**
4. **Следовать принципу атомарности** - завершить полностью
5. **Обновить ROADMAP.md** с прогрессом

### **Task 1.1 First Steps:**
```python
# 1. Создать структуру:
mkdir -p app/security
touch app/security/auth.py

# 2. Установить зависимости:
pip install python-jose[cryptography] passlib[bcrypt]

# 3. Создать базовую auth логику
# 4. Добавить Depends(auth) ко всем API routes
# 5. Создать login/logout endpoints
```

**🎯 Ready for next phase: Implement Production Security**
**📝 Current Priority: Task 1.1 - JWT Authentication**
**⏰ Estimated time: 2 days**
**🚀 Ready to execute on command: "приступай к следующему шагу"**