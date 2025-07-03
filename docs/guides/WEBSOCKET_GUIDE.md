# WebSocket Руководство

## Обзор

Наше приложение поддерживает WebSocket соединения для обмена сообщениями в реальном времени, уведомлений и мониторинга состояния системы.

## Возможности

- ✅ **Управление соединениями** - автоматическое подключение/отключение пользователей
- ✅ **Персональные сообщения** - отправка сообщений конкретному пользователю
- ✅ **Broadcast сообщения** - отправка сообщений всем подключенным пользователям
- ✅ **Heartbeat/Ping-Pong** - поддержание соединения активным
- ✅ **Статистика соединений** - информация о количестве подключений
- ✅ **Обработка ошибок** - автоматическое удаление неактивных соединений
- ✅ **Уведомления** - система real-time уведомлений

## API Endpoints

### WebSocket Соединения

#### 1. Подключение с User ID
```
ws://localhost:8000/api/v1/ws/{user_id}
```

#### 2. Анонимное подключение
```
ws://localhost:8000/api/v1/ws
```

### REST API для управления

#### 1. Получить статистику соединений
```http
GET /api/v1/ws/stats
```

**Ответ:**
```json
{
  "total_connections": 5,
  "connected_users": ["user1", "user2", "user3"],
  "users_count": 3
}
```

#### 2. Отправить уведомление пользователю
```http
POST /api/v1/ws/notify/{user_id}
Content-Type: application/json

{
  "notification_type": "info",
  "message": {
    "title": "Новое сообщение",
    "content": "У вас есть новое сообщение"
  }
}
```

#### 3. Broadcast уведомление
```http
POST /api/v1/ws/broadcast
Content-Type: application/json

{
  "notification_type": "system",
  "message": {
    "title": "Системное обслуживание",
    "content": "Система будет недоступна с 23:00 до 01:00"
  },
  "exclude_user": "admin"  // опционально
}
```

## Типы сообщений

### 1. Соединение установлено
```json
{
  "type": "connection_status",
  "data": {
    "status": "connected",
    "user_id": "user123",
    "timestamp": "2024-01-15T10:30:00Z",
    "total_connections": 5
  }
}
```

### 2. Ping-Pong
**Отправить:**
```json
{
  "type": "ping"
}
```
**Получить:**
```json
{
  "type": "pong",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 3. Получить статистику
**Отправить:**
```json
{
  "type": "get_stats"
}
```
**Получить:**
```json
{
  "type": "stats",
  "data": {
    "total_connections": 5,
    "user_connections": 2,
    "connected_users": ["user1", "user2", "user3"]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 4. Heartbeat (автоматический)
```json
{
  "type": "heartbeat",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 5. Уведомления
```json
{
  "type": "notification",
  "notification_type": "info",
  "data": {
    "title": "Новое сообщение",
    "content": "У вас есть новое сообщение"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 6. Disconnect
**Отправить для корректного отключения:**
```json
{
  "type": "disconnect"
}
```

## Примеры использования

### JavaScript Client

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/my_user_id');

ws.onopen = function(event) {
    console.log('Connected to WebSocket');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
    
    switch(data.type) {
        case 'connection_status':
            console.log('Connection established:', data.data);
            break;
        case 'notification':
            showNotification(data.notification_type, data.data);
            break;
        case 'pong':
            console.log('Pong received');
            break;
        case 'stats':
            updateConnectionStats(data.data);
            break;
    }
};

ws.onclose = function(event) {
    console.log('WebSocket connection closed');
};

// Отправить ping
function sendPing() {
    ws.send(JSON.stringify({type: 'ping'}));
}

// Получить статистику
function getStats() {
    ws.send(JSON.stringify({type: 'get_stats'}));
}

// Корректное отключение
function disconnect() {
    ws.send(JSON.stringify({type: 'disconnect'}));
    ws.close();
}
```

### Python Client

```python
import asyncio
import websockets
import json

async def websocket_client():
    uri = "ws://localhost:8000/api/v1/ws/python_user"
    
    async with websockets.connect(uri) as websocket:
        # Отправить ping
        await websocket.send(json.dumps({"type": "ping"}))
        
        # Слушать сообщения
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")
            
            if data.get("type") == "pong":
                print("Pong received!")
            elif data.get("type") == "notification":
                print(f"Notification: {data}")

# Запуск
asyncio.run(websocket_client())
```

## Программное использование в приложении

### Отправка уведомлений

```python
from app.websocket import send_notification_to_user, broadcast_notification

# Отправить уведомление конкретному пользователю
await send_notification_to_user(
    user_id="user123",
    notification_type="info",
    data={
        "title": "Новый документ",
        "content": "Добавлен новый документ в систему",
        "url": "/documents/123"
    }
)

# Broadcast уведомление всем пользователям
await broadcast_notification(
    notification_type="system",
    data={
        "title": "Обновление системы",
        "content": "Система будет обновлена в 23:00"
    },
    exclude_user="admin"  # исключить админа
)
```

### Проверка статистики соединений

```python
from app.websocket import manager

# Количество соединений пользователя
user_connections = manager.get_user_connections_count("user123")

# Общее количество соединений
total_connections = manager.get_total_connections_count()

# Список подключенных пользователей
connected_users = manager.get_connected_users()

print(f"User connections: {user_connections}")
print(f"Total connections: {total_connections}")
print(f"Connected users: {connected_users}")
```

## Тестирование

Запустите тесты WebSocket функциональности:

```bash
pytest tests/unit/test_websocket.py -v
```

### Интерактивное тестирование

1. Запустите приложение:
```bash
uvicorn app.main:app --reload
```

2. Откройте тестовую страницу:
```
http://localhost:8000/api/v1/ws/test
```

3. Используйте интерфейс для тестирования всех функций WebSocket

## Обработка ошибок

- **Неактивные соединения** автоматически удаляются при ошибках отправки
- **JSON ошибки** возвращают сообщение об ошибке клиенту
- **Timeout соединений** обрабатываются через heartbeat механизм
- **Неожиданные отключения** логируются и корректно очищаются

## Безопасность

- WebSocket endpoints поддерживают аутентификацию через токены
- REST API для управления требует авторизации
- Валидация всех входящих сообщений
- Ограничение на количество соединений (может быть настроено)

## Мониторинг

WebSocket соединения логируются и могут быть отслежены через:
- Логи приложения
- Метрики соединений через `/api/v1/ws/stats`
- Интеграция с системами мониторинга

## Примеры интеграции

### С AI Analytics сервисом

```python
# В AI Analytics сервисе
from app.websocket import broadcast_notification

async def notify_analysis_complete(analysis_result):
    await broadcast_notification(
        notification_type="ai_analysis",
        data={
            "title": "Анализ завершен",
            "result": analysis_result,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### С системой документооборота

```python
# При добавлении нового документа
from app.websocket import send_notification_to_user

async def notify_new_document(user_id, document):
    await send_notification_to_user(
        user_id=user_id,
        notification_type="document",
        data={
            "title": "Новый документ",
            "document_id": document.id,
            "document_title": document.title,
            "url": f"/documents/{document.id}"
        }
    )
``` 