# 🚀 VK Teams Bot - Быстрый старт (5 минут)

## ⚡ Настройка за 5 минут

### 1️⃣ **Создание бота (2 минуты)**

```bash
# 1. Откройте VK Teams
# 2. Найдите @MetaBot
# 3. Отправьте: /newbot
# 4. Назовите бота: AI Assistant Bot
# 5. Сохраните токен: 001.xxxx.xxxx
```

### 2️⃣ **Настройка AI Assistant (1 минута)**

```bash
# Добавьте в .env файл
echo "VK_TEAMS_BOT_TOKEN=001.your_token_here" >> .env
echo "VK_TEAMS_ENABLED=true" >> .env
echo "VK_TEAMS_API_URL=https://api.internal.myteam.mail.ru/bot/v1" >> .env
```

### 3️⃣ **Настройка webhook для разработки (1 минута)**

```bash
# Установите ngrok
brew install ngrok  # macOS
# или
sudo apt install ngrok  # Ubuntu

# Запустите ngrok (в отдельном терминале)
ngrok http 8000

# Скопируйте HTTPS URL (например: https://abc123.ngrok.io)
echo "VK_TEAMS_WEBHOOK_URL=https://abc123.ngrok.io/api/v1/vk-teams/webhook/events" >> .env
```

### 4️⃣ **Запуск (1 минута)**

```bash
# Перезапустите AI Assistant
pkill -f "python.*main.py"
python main.py --port 8000 --host localhost

# Получите токен API
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@vkteam.ru", "password": "admin"}' | jq -r '.access_token')

# Настройте бота
curl -X POST "http://localhost:8000/api/v1/vk-teams/bot/configure" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "bot_token": "001.your_token_here",
    "auto_start": true
  }'
```

### 5️⃣ **Тестирование (30 секунд)**

```bash
# В VK Teams найдите вашего бота и отправьте:
/start

# Ответ должен быть:
# 🤖 Привет! Я AI Assistant Bot
# Я помогу вам с поиском информации...

# Попробуйте команды:
/search документация API
/generate RFC для нового сервиса
Объясни SOLID принципы
```

---

## 🎯 **Готово!** 

Теперь у вас работающий VK Teams бот с AI Assistant!

### 📝 **Полезные команды для бота:**

```
/start - Приветствие
/help - Список команд
/search <запрос> - Поиск информации
/generate <описание> - Генерация документов
/analyze <код> - Анализ кода
/status - Статус системы
```

### 🔧 **Проверка статуса:**

```bash
# Статус бота
curl "http://localhost:8000/api/v1/vk-teams/bot/status" \
  -H "Authorization: Bearer $TOKEN" | jq

# Статистика
curl "http://localhost:8000/api/v1/vk-teams/bot/stats" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### 📚 **Если нужно больше настроек:**

- **[Полное руководство](VK_TEAMS_COMPLETE_SETUP_GUIDE.md)** - Детальная настройка
- **[VK OAuth настройка](integrations/VK_OAUTH_GUIDE.md)** - Ограничение доступа
- **[Продвинутые функции](integrations/VK_TEAMS_INTEGRATION.md)** - Кастомизация

---

## 🆘 **Если что-то не работает:**

### ❌ **Бот не отвечает:**
```bash
# Проверьте логи
tail -f app.log | grep -i vk.teams

# Проверьте webhook
curl -I https://your-ngrok-url.ngrok.io/api/v1/vk-teams/webhook/events
```

### ❌ **Ошибка конфигурации:**
```bash
# Проверьте переменные
env | grep VK_TEAMS

# Перенастройте бота
curl -X POST "http://localhost:8000/api/v1/vk-teams/bot/configure" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"bot_token": "correct_token"}'
```

### ❌ **Проблемы с ngrok:**
```bash
# Перезапустите ngrok с новым URL
ngrok http 8000

# Обновите webhook URL
echo "VK_TEAMS_WEBHOOK_URL=https://new-url.ngrok.io/api/v1/vk-teams/webhook/events" >> .env
```

**💡 Совет:** Для production используйте реальный домен вместо ngrok! 