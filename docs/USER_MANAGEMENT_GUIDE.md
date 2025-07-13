# 👥 User Management Guide - Руководство по управлению пользователями

**Версия:** 1.0.0  
**Дата:** 13 января 2025  
**Статус:** Production Ready

---

## 🎯 Обзор

Система AI Assistant поддерживает создание и управление пользователями с различными уровнями доступа. Пользователи могут быть обычными пользователями или администраторами с расширенными правами.

---

## 🔐 Типы пользователей

### 👤 Обычный пользователь
- **Scopes**: `basic`, `search`
- **Budget**: $1000.0
- **Права**: Базовый поиск и использование API

### 👑 Администратор
- **Scopes**: `admin`, `basic`, `search`, `generate`
- **Budget**: $10000.0
- **Права**: Полный доступ к системе, управление пользователями

---

## 🚀 Предустановленные пользователи

### 1. **admin@vkteam.ru** (VK Team Admin)
- **Пароль**: `admin`
- **Тип**: Администратор
- **User ID**: `vkteam_admin`
- **Создан**: ✅ По умолчанию

### 2. **admin@example.com** (Admin)
- **Пароль**: `admin`
- **Тип**: Администратор
- **User ID**: `admin_user`
- **Создан**: ✅ По умолчанию

### 3. **user@example.com** (Test User)
- **Пароль**: `user123`
- **Тип**: Пользователь
- **User ID**: `user_001`
- **Создан**: ✅ По умолчанию

---

## 🛠️ Способы создания пользователей

### 1. Через командную строку (CLI)

#### Создание обычного пользователя
```bash
python create_user.py create --email user@company.com --password secret123 --name "John Doe"
```

#### Создание администратора
```bash
python create_user.py create --email admin@company.com --password admin123 --name "Admin User" --admin
```

#### Просмотр всех пользователей
```bash
python create_user.py list
```

#### Информация о пользователе
```bash
python create_user.py info --email user@company.com
```

#### Смена пароля
```bash
python create_user.py password --email user@company.com --new-password newpass123
```

#### Удаление пользователя
```bash
python create_user.py delete --email user@company.com
```

### 2. Через API

#### Аутентификация
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@vkteam.ru",
    "password": "admin"
  }'
```

**Пример ответа:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "user_id": "vkteam_admin",
    "email": "admin@vkteam.ru",
    "name": "VK Team Admin",
    "is_active": true,
    "scopes": ["admin", "basic", "search", "generate"],
    "budget_limit": 10000.0,
    "current_usage": 0.0
  }
}
```

#### Регистрация нового пользователя
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@company.com",
    "password": "password123",
    "name": "New User"
  }'
```

---

## 🔧 Управление пользователями

### CLI команды

#### Просмотр всех пользователей
```bash
python create_user.py list
```

**Вывод:**
```
📋 Users in system (4 total):
  👑 admin@vkteam.ru (VK Team Admin) ✅
    ID: vkteam_admin
    Scopes: admin, basic, search, generate
    Budget: $10000.0 (used: $0.0)

  👤 newuser@example.com (New User) ✅
    ID: user_5
    Scopes: basic
    Budget: $100.0 (used: $0.0)
```

#### Получение информации о пользователе
```bash
python create_user.py info --email admin@vkteam.ru
```

**Вывод:**
```
👤 User Information:
  Email: admin@vkteam.ru
  Name: VK Team Admin
  User ID: vkteam_admin
  Type: 👑 Admin
  Status: ✅ Active
  Scopes: admin, basic, search, generate
  Budget: $10000.0
  Current Usage: $0.0
```

---

## 🔐 Аутентификация и авторизация

### Получение JWT токена

```bash
# Сохранить токен в переменную
export JWT_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@vkteam.ru", "password": "admin"}' | jq -r '.access_token')

# Использовать токен в запросах
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/v1/users
```

### Проверка токена
```bash
curl -X GET http://localhost:8000/api/v1/auth/verify \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## 📊 Уровни доступа (Scopes)

### Базовые уровни
- **`basic`**: Базовый доступ к API
- **`search`**: Доступ к поиску и семантическому анализу
- **`generate`**: Создание документов и RFC
- **`admin`**: Административные функции

### Матрица доступа

| Функция | basic | search | generate | admin |
|---------|-------|--------|----------|-------|
| Health Check | ✅ | ✅ | ✅ | ✅ |
| Document Search | ❌ | ✅ | ✅ | ✅ |
| AI Generation | ❌ | ❌ | ✅ | ✅ |
| User Management | ❌ | ❌ | ❌ | ✅ |
| System Settings | ❌ | ❌ | ❌ | ✅ |

---

## 🎨 Бюджетная система

### Лимиты по умолчанию
- **Пользователь**: $1000.0
- **Администратор**: $10000.0

### Отслеживание использования
Система автоматически отслеживает использование API для каждого пользователя:
- Стоимость запросов к LLM
- Использование векторного поиска
- Генерация документов

---

## 🔄 Автоматизация

### Создание пользователей через скрипт
```bash
#!/bin/bash
# Создать несколько пользователей
users=(
  "john@company.com:password123:John Doe"
  "jane@company.com:password456:Jane Smith"
  "admin@company.com:admin123:Company Admin:admin"
)

for user in "${users[@]}"; do
  IFS=':' read -ra USER_DATA <<< "$user"
  email="${USER_DATA[0]}"
  password="${USER_DATA[1]}"
  name="${USER_DATA[2]}"
  admin_flag="${USER_DATA[3]}"
  
  cmd="python create_user.py create --email $email --password $password --name \"$name\""
  if [ "$admin_flag" == "admin" ]; then
    cmd="$cmd --admin"
  fi
  
  eval $cmd
done
```

---

## 🛡️ Безопасность

### Хеширование паролей
- Используется **bcrypt** для безопасного хранения паролей
- Пароли никогда не сохраняются в открытом виде
- Поддержка настраиваемого количества раундов хеширования

### JWT токены
- **Время жизни**: 1800 секунд (30 минут)
- **Алгоритм**: HS256
- **Информация в токене**: user_id, email, scopes, name

### Рекомендации по безопасности
1. Используйте сложные пароли (минимум 8 символов)
2. Регулярно обновляйте пароли
3. Ограничивайте время жизни JWT токенов
4. Используйте HTTPS в production

---

## 🔧 Настройка

### Переменные окружения
```bash
# JWT конфигурация
export SECRET_KEY="your-secret-key-here"
export ACCESS_TOKEN_EXPIRE_MINUTES=30

# Базовая конфигурация
export DATABASE_URL="postgresql://user:password@localhost/aiassistant"
```

### Конфигурация в коде
```python
# app/security/auth.py
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

---

## 🚨 Устранение неполадок

### Частые проблемы

#### 1. "User already exists"
```bash
# Проверить существующих пользователей
python create_user.py list

# Удалить пользователя если нужно
python create_user.py delete --email user@example.com
```

#### 2. "Invalid credentials"
```bash
# Проверить информацию о пользователе
python create_user.py info --email user@example.com

# Сменить пароль
python create_user.py password --email user@example.com --new-password newpass123
```

#### 3. "Token expired"
```bash
# Получить новый токен
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@vkteam.ru", "password": "admin"}'
```

---

## 📱 Примеры использования

### Создание команды разработчиков
```bash
# Создать администратора проекта
python create_user.py create \
  --email lead@company.com \
  --password leadpass123 \
  --name "Tech Lead" \
  --admin

# Создать разработчиков
python create_user.py create \
  --email dev1@company.com \
  --password devpass123 \
  --name "Developer 1"

python create_user.py create \
  --email dev2@company.com \
  --password devpass123 \
  --name "Developer 2"
```

### Массовое создание пользователей
```bash
# Создать CSV файл с пользователями
echo "email,password,name,admin" > users.csv
echo "user1@company.com,pass123,User One,false" >> users.csv
echo "user2@company.com,pass456,User Two,false" >> users.csv
echo "admin@company.com,admin123,Admin User,true" >> users.csv

# Скрипт для импорта
while IFS=',' read -r email password name admin; do
  cmd="python create_user.py create --email $email --password $password --name \"$name\""
  if [ "$admin" == "true" ]; then
    cmd="$cmd --admin"
  fi
  eval $cmd
done < users.csv
```

---

## 📈 Мониторинг пользователей

### Статистика использования
```bash
# Получить статистику всех пользователей
python create_user.py list | grep -E "(Budget|used)"
```

### Активные пользователи
```bash
# Найти активных пользователей
python create_user.py list | grep "✅"
```

---

## 🔗 Связанные документы

- **[API Reference](./API_REFERENCE_COMPLETE.md)** - Полная документация API
- **[API Testing Guide](./API_TESTING_GUIDE.md)** - Руководство по тестированию
- **[Authentication Guide](./guides/AUTH_GUIDE.md)** - Подробное руководство по аутентификации
- **[Security Guide](./guides/SECURITY_GUIDE.md)** - Рекомендации по безопасности

---

**📅 Последнее обновление**: 13 января 2025  
**🏷️ Версия**: 1.0.0  
**📊 Статус**: Production Ready  
**👥 Предустановленные пользователи**: admin@vkteam.ru (admin), admin@example.com (admin), user@example.com (user123) 