# 🔐 VK OAuth Авторизация - Руководство по настройке

## 📋 Обзор

VK OAuth интеграция позволяет ограничить доступ к AI-ассистенту только авторизованным пользователям VKontakte. Это обеспечивает безопасность и контроль доступа через проверку VK ID пользователей.

## 🌟 Основные возможности

- ✅ **OAuth 2.0 авторизация** через VKontakte
- ✅ **Контроль доступа** по списку разрешенных VK ID
- ✅ **Интеграция с VK Teams ботом** - автоматическая проверка пользователей
- ✅ **Гибкая конфигурация** через ENV переменные или YAML файл
- ✅ **JWT токены** для сессий пользователей
- ✅ **Автоматическое создание** пользователей в системе

## 🚀 Быстрая настройка

### 1. Создание VK приложения

1. Перейдите на [vk.com/apps?act=manage](https://vk.com/apps?act=manage)
2. Нажмите **"Создать приложение"**
3. Выберите тип **"Веб-сайт"**
4. Заполните данные:
   - **Название**: AI Assistant
   - **Адрес сайта**: `https://your-domain.com`
   - **Базовый домен**: `your-domain.com`

### 2. Настройка приложения

В настройках VK приложения:

1. **Настройки** → **OAuth**:
   - **Доверенный redirect URI**: `https://your-domain.com/api/v1/auth/vk/callback`
   - **Права доступа**: email (и другие по необходимости)

2. Скопируйте:
   - **ID приложения** (`VK_OAUTH_CLIENT_ID`)
   - **Защищённый ключ** (`VK_OAUTH_CLIENT_SECRET`)

### 3. Конфигурация системы

#### Через переменные окружения

```bash
# Включение VK OAuth
VK_OAUTH_ENABLED=true

# Настройки VK приложения
VK_OAUTH_CLIENT_ID="12345678"
VK_OAUTH_CLIENT_SECRET="your_secret_key"
VK_OAUTH_REDIRECT_URI="https://your-domain.com/api/v1/auth/vk/callback"
VK_OAUTH_SCOPE="email"

# Список разрешенных пользователей (через запятую)
ALLOWED_VK_USERS="123456789,987654321,555666777"
```

#### Через YAML конфигурацию

Создайте файл `config/vk_users.yml`:

```yaml
allowed_vk_users:
  - "123456789"  # ID администратора
  - "987654321"  # ID модератора
  - "555666777"  # ID пользователя
```

### 4. Применение миграций

```bash
# Применение миграций для VK OAuth полей
alembic upgrade head
```

### 5. Перезапуск приложения

```bash
# Docker
docker-compose restart ai-assistant

# Локально
uvicorn app.main:app --reload
```

## 📖 Подробное руководство

### Как узнать VK ID пользователя

#### Способ 1: Через профиль VK
1. Откройте профиль пользователя в VK
2. В адресной строке найдите ID: `vk.com/id123456789`
3. Число после `id` - это VK ID

#### Способ 2: Через настройки VK
1. Перейдите в **Настройки** → **Общее**
2. В правом блоке найдите **"Адрес страницы"**
3. Номер в поле - это ваш VK ID

#### Способ 3: Через API
```bash
curl "https://api.vk.com/method/users.get?user_ids=screen_name&v=5.131"
```

### Добавление нового пользователя

#### Через переменную окружения
```bash
# Добавьте новый ID в список через запятую
ALLOWED_VK_USERS="123456789,987654321,555666777,999888777"
```

#### Через YAML конфигурацию
```yaml
allowed_vk_users:
  - "123456789"
  - "987654321" 
  - "555666777"
  - "999888777"  # Новый пользователь
```

После изменения перезапустите приложение.

### Проверка работы авторизации

#### 1. Проверка доступа пользователя
```bash
curl http://localhost:8000/api/v1/auth/vk/check-access/123456789
```

Ответ:
```json
{
  "vk_user_id": "123456789",
  "has_access": true,
  "message": "Access granted"
}
```

#### 2. Получение конфигурации OAuth
```bash
curl http://localhost:8000/api/v1/auth/vk/config
```

#### 3. Тестирование авторизации
1. Откройте: `http://localhost:8000/api/v1/auth/vk/login`
2. Вы будете перенаправлены на VK для авторизации
3. После подтверждения вернетесь с токеном доступа

## 🤖 Интеграция с VK Teams ботом

VK Teams бот автоматически проверяет доступ пользователей при включенной VK OAuth авторизации.

### Принцип работы
1. Пользователь отправляет сообщение боту
2. Бот извлекает VK ID пользователя
3. Проверяется доступ через VK OAuth API
4. При отсутствии доступа отправляется сообщение с инструкциями

### Сообщение об отказе в доступе
```
🚫 Доступ ограничен

К сожалению, ваш аккаунт VK не авторизован для использования этого AI-ассистента.

Что можно сделать:
1. Обратитесь к администратору для получения доступа
2. Убедитесь, что вы авторизованы через VK OAuth
3. Проверьте, что ваш VK ID добавлен в список разрешенных пользователей

Для получения доступа:
• Свяжитесь с администратором системы
• Предоставьте ваш VK ID: 123456789

Извините за неудобства! 🙏
```

## 🔧 API Endpoints

### Авторизация

- **`GET /api/v1/auth/vk/login`** - Инициация OAuth авторизации
- **`GET /api/v1/auth/vk/callback`** - Обработка OAuth callback
- **`GET /api/v1/auth/vk/config`** - Получение публичной конфигурации

### Проверка доступа

- **`GET /api/v1/auth/vk/check-access/{vk_user_id}`** - Проверка доступа пользователя

#### Пример использования API

```python
import httpx

async def check_user_access(vk_user_id: str) -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8000/api/v1/auth/vk/check-access/{vk_user_id}"
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("has_access", False)
        return False

# Использование
has_access = await check_user_access("123456789")
if has_access:
    print("Пользователь авторизован")
else:
    print("Доступ запрещен")
```

## 🧪 Тестирование

### Запуск тестов
```bash
# Все тесты VK OAuth
pytest tests/unit/test_vk_oauth_auth.py -v

# Конкретный тест
pytest tests/unit/test_vk_oauth_auth.py::TestVKAuthService::test_is_user_allowed_positive -v
```

### Тестовые сценарии

#### Позитивный сценарий
```python
# Пользователь в списке разрешенных
vk_user_id = "123456789"
assert await vk_auth_service.is_user_allowed(vk_user_id) == True
```

#### Негативный сценарий
```python
# Пользователь НЕ в списке разрешенных
vk_user_id = "999999999"
assert await vk_auth_service.is_user_allowed(vk_user_id) == False
```

## 🔒 Безопасность

### Рекомендации по безопасности

1. **Храните секреты безопасно**:
   - Используйте переменные окружения
   - НЕ коммитьте секреты в Git
   - Используйте системы управления секретами

2. **Ограничьте redirect URI**:
   - Указывайте точные URI в настройках VK
   - Используйте HTTPS в production

3. **Регулярно обновляйте списки пользователей**:
   - Удаляйте неактивных пользователей
   - Ведите аудит доступа

4. **Мониторинг**:
   - Логируйте попытки доступа
   - Настройте алерты на подозрительную активность

### Защита от атак

- ✅ **CSRF защита** через state параметр
- ✅ **Валидация redirect URI**
- ✅ **Проверка подписи токенов**
- ✅ **Rate limiting** на endpoints
- ✅ **Логирование безопасности**

## 📊 Мониторинг и отладка

### Логи для отладки

```bash
# Поиск логов VK OAuth
grep "VK OAuth" logs/app.log

# Поиск ошибок авторизации
grep "VK user.*denied access" logs/app.log

# Успешные авторизации
grep "VK OAuth successful" logs/app.log
```

### Метрики

- **Количество авторизаций** - успешных и неуспешных
- **Отказы в доступе** - по VK ID и времени
- **Время ответа** VK API
- **Ошибки интеграции**

## ❗ Troubleshooting

### Частые проблемы

#### 1. "VK OAuth is not enabled"
**Решение**: Проверьте переменную `VK_OAUTH_ENABLED=true`

#### 2. "Invalid redirect URI"
**Решение**: 
- Проверьте настройки VK приложения
- Убедитесь что URI точно совпадает
- Используйте HTTPS в production

#### 3. "User authorization failed"
**Решение**:
- Проверьте права доступа приложения в VK
- Убедитесь что пользователь подтвердил разрешения

#### 4. "Access denied" для бота
**Решение**:
- Добавьте VK ID пользователя в `ALLOWED_VK_USERS`
- Проверьте корректность ID
- Перезапустите приложение после изменений

### Отладка конфигурации

```python
# Проверка настроек
from app.config import get_settings
settings = get_settings()

print(f"VK OAuth enabled: {settings.VK_OAUTH_ENABLED}")
print(f"Client ID: {settings.VK_OAUTH_CLIENT_ID}")
print(f"Redirect URI: {settings.VK_OAUTH_REDIRECT_URI}")
print(f"Allowed users: {settings.ALLOWED_VK_USERS}")
```

## 📝 Changelog

### v1.0.0 (2025-01-04)
- ✅ Первоначальная реализация VK OAuth
- ✅ Интеграция с VK Teams ботом
- ✅ Поддержка конфигурации через ENV и YAML
- ✅ Тесты и документация
- ✅ Миграции базы данных

## 🔗 Полезные ссылки

- [Документация VK API](https://dev.vk.com/reference)
- [OAuth 2.0 VK](https://dev.vk.com/api/access-token/authcode-flow-user)
- [VK Teams Bot API](https://teams.vk.com/botapi/)
- [Управление VK приложениями](https://vk.com/apps?act=manage)

---

**💡 Совет**: Для production окружения рекомендуется использовать переменные окружения для конфигурации и регулярно ротировать секретные ключи. 