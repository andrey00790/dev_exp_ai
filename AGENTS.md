# 🤖 AI Development Agents - Rules & Standards

**Версия:** 1.0
**Дата:** 16 июня 2025
**Статус:** ✅ Актуальные правила разработки

## 🎯 **Текущий статус проекта**

### ✅ **MVP ЗАВЕРШЕН (100%)**
Все 6 итераций развития успешно завершены. Система готова к production deployment.

### 🚀 **Следующая фаза: Production Security**
**Приоритет 1**: Реализация аутентификации и безопасности

## 📋 **Правила разработки**

### **1. Принцип атомарности**
- Каждая задача должна быть завершена полностью
- Не переходить к следующей задаче без завершения текущей
- Обязательное тестирование после каждого изменения

### **2. Security First**
- Любой API endpoint должен иметь аутентификацию
- Валидация всех входных данных
- Rate limiting для дорогих операций

## 🛠️ **Development Workflow**

### **Phase 1: Production Security (CURRENT)**

#### **Task 1.1: JWT Authentication (2 дня)**
Требования:
1. Создать app/security/auth.py с JWT implementation
2. Добавить authentication middleware ко всем API routes
3. Создать login/logout UI components

#### **Task 1.2: Cost Control (1 день)**
Требования:
1. Добавить user_budgets таблицу в PostgreSQL
2. Создать cost tracking для LLM API calls

#### **Task 1.3: Security Hardening (1-2 дня)**
Требования:
1. Обновить все зависимости с уязвимостями (текущий: 42)
2. Добавить input validation middleware

## 🎯 **Next Action Protocol**

### **Когда получаешь команду "приступай к следующему шагу":**

1. **Проверить текущий статус** в ROADMAP.md
2. **Начать с Task 1.1: JWT Authentication**
3. **Следовать принципу атомарности** - завершить полностью

**🎯 Ready for next phase: Implement Production Security**
**📝 Current Priority: Task 1.1 - JWT Authentication**
**🚀 Ready to execute on command: "приступай к следующему шагу"**