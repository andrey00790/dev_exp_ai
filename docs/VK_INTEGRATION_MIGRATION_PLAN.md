# 🚀 План миграции VK интеграции

## 🎯 **Цель миграции**

Создать **единую систему авторизации** поддерживающую:
- ✅ **Email/password** (текущая система)
- ✅ **VK OAuth** (веб GUI)
- ✅ **VK Teams** (чат-бот)
- ✅ **Связывание аккаунтов** (VK ID ↔ internal user)

---

## 📊 **Текущее состояние**

### ✅ **Готово:**
1. **VK Teams инфраструктура** - сервисы, адаптеры, endpoints
2. **VK OAuth базовая реализация** - `VKAuthService`
3. **Документация** - полные руководства по настройке
4. **Unified Auth Service** - универсальная система авторизации
5. **Расширенная модель User** - поддержка VK полей

### ❌ **Требует доработки:**
1. **Интеграция с budget системой** - привязка к VK ID
2. **Frontend VK OAuth** - GUI для авторизации через VK
3. **Миграция существующих пользователей** - добавление VK ID
4. **Тестирование полного flow** - от VK Teams до budget

---

## 🛠 **План реализации**

### **Фаза 1: Подготовка (СДЕЛАНО)**
- [x] Создать unified auth service
- [x] Расширить модель User для VK полей
- [x] Обновить VK Teams адаптер
- [x] Создать конфигурацию VK интеграции

### **Фаза 2: Интеграция с budget системой**

#### **2.1 Обновить budget service**
```python
# app/services/budget_service.py
async def get_user_budget_info_by_vk_id(self, vk_user_id: str) -> Dict[str, Any]:
    """Получение бюджета по VK ID"""
    from app.security.unified_auth import unified_auth_service
    
    user = unified_auth_service.get_user_by_vk_id(vk_user_id)
    if user:
        return await self.get_user_budget_info(user.user_id)
    return {"error": "VK user not found"}
```

#### **2.2 Обновить budget endpoints**
```python
# app/api/v1/budget_management.py
@router.get("/status/vk/{vk_user_id}")
async def get_budget_status_by_vk_id(
    vk_user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Получить статус бюджета по VK ID"""
    # Проверить права доступа
    # Получить бюджет по VK ID
```

### **Фаза 3: Frontend VK OAuth**

#### **3.1 Добавить VK OAuth кнопку**
```tsx
// frontend/src/components/auth/VKLoginButton.tsx
export const VKLoginButton: React.FC = () => {
  const handleVKLogin = () => {
    const vkAuthUrl = `${API_URL}/api/v1/auth/vk/login`;
    window.location.href = vkAuthUrl;
  };

  return (
    <button onClick={handleVKLogin} className="vk-login-btn">
      <VKIcon /> Войти через VK
    </button>
  );
};
```

#### **3.2 Обработка VK callback**
```tsx
// frontend/src/pages/VKCallbackPage.tsx
export const VKCallbackPage: React.FC = () => {
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    
    if (code) {
      // Отправить code на backend для обмена на токены
      handleVKCallback(code, state);
    }
  }, []);
};
```

### **Фаза 4: API endpoints для VK OAuth**

#### **4.1 VK OAuth endpoints**
```python
# app/api/v1/vk_auth.py
@router.get("/login")
async def vk_oauth_login():
    """Инициация VK OAuth авторизации"""
    
@router.get("/callback")
async def vk_oauth_callback(code: str, state: str):
    """Обработка VK OAuth callback"""
    
@router.post("/link-account")
async def link_vk_account(
    vk_code: str,
    current_user: User = Depends(get_current_user)
):
    """Связывание VK аккаунта с текущим пользователем"""
```

### **Фаза 5: Тестирование и развертывание**

---

## 🔧 **Инструкции по настройке**

### **1. Настройка переменных окружения**
```bash
# .env
# VK OAuth
VK_OAUTH_ENABLED=true
VK_OAUTH_CLIENT_ID=your_vk_app_id
VK_OAUTH_CLIENT_SECRET=your_vk_app_secret
VK_OAUTH_REDIRECT_URI=https://your-domain.com/api/v1/auth/vk/callback
ALLOWED_VK_USERS=123456789,987654321

# VK Teams
VK_TEAMS_BOT_TOKEN=001.your_bot_token
VK_TEAMS_ENABLED=true
VK_TEAMS_API_URL=https://api.internal.myteam.mail.ru/bot/v1
VK_TEAMS_WEBHOOK_URL=https://your-domain.com/api/v1/vk-teams/webhook/events
```

### **2. Настройка VK приложения**
1. Создать приложение на [vk.com/dev](https://vk.com/dev)
2. Настроить redirect URI
3. Получить client_id и client_secret
4. Добавить разрешенных пользователей в `ALLOWED_VK_USERS`

### **3. Настройка VK Teams бота**
1. Создать бота через @MetaBot
2. Получить токен бота
3. Настроить webhook URL

### **4. Обновление budget_config.yml**
```yaml
# config/budget_config.yml
auto_refill:
  refill_settings:
    by_role:
      vk_user:
        enabled: true
        amount: 1000.0
        reset_usage: true
      vk_teams:
        enabled: true
        amount: 500.0
        reset_usage: true
```

---

## 🧪 **Тестирование**

### **1. Тест VK Teams авторизации**
```bash
# 1. Запустить приложение
python main.py --port 8000

# 2. Настроить бота
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -d '{"email": "admin@vkteam.ru", "password": "admin"}' | jq -r '.access_token')

curl -X POST "http://localhost:8000/api/v1/vk-teams/bot/configure" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"bot_token": "001.your_token", "auto_start": true}'

# 3. Тестировать в VK Teams: /start
```

### **2. Тест VK OAuth**
```bash
# 1. Открыть: http://localhost:8000/api/v1/auth/vk/login
# 2. Авторизоваться в VK
# 3. Проверить создание пользователя
# 4. Проверить budget статус
```

### **3. Тест связывания аккаунтов**
```bash
# 1. Войти как обычный пользователь
# 2. Связать VK аккаунт
# 3. Проверить что VK ID добавился
# 4. Проверить работу через VK Teams
```

---

## ⚠️ **Критические моменты**

### **1. Безопасность**
- ✅ Проверка allowed users для VK
- ✅ Верификация webhook подписей
- ✅ Валидация VK токенов
- ⚠️ Не хранить VK токены в логах

### **2. Производительность**
- ✅ Кэширование VK user проверок
- ✅ Async обработка webhook'ов
- ⚠️ Rate limiting для VK API вызовов

### **3. Мониторинг**
- ✅ Логирование всех VK операций
- ✅ Метрики использования
- ✅ Алерты при ошибках авторизации

---

## 🚀 **Следующие шаги**

1. **Завершить бюджет интеграцию** - привязка к VK ID
2. **Создать Frontend VK OAuth** - кнопки и обработка callback
3. **Добавить API endpoints** - для VK авторизации и связывания
4. **Протестировать полный flow** - от VK Teams до budget
5. **Задеплоить в production** - с настройкой webhook и SSL

---

**🎯 Результат:** Единая система авторизации поддерживающая все типы пользователей с возможностью плавной миграции между ними. 