# 🚀 ИНСТРУКЦИЯ ПО УСТАНОВКЕ И РАЗВЕРТЫВАНИЮ AI ASSISTANT

## 📋 ТРЕБОВАНИЯ

- Python 3.11+
- pip
- git

## 🔧 УСТАНОВКА

### 1. Клонирование репозитория
```bash
git clone <your-repo-url>
cd dev_exp_ai
```

### 2. Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими настройками
```

## 🚀 ЗАПУСК

### Быстрый запуск
```bash
python3 start_server.py
```

### Запуск с Docker
```bash
docker-compose up -d
```

### Запуск с Make
```bash
make start
```

## 🔍 ПРОВЕРКА УСТАНОВКИ

### Тест всех компонентов
```bash
python3 test_api.py
```

### Тест отдельных модулей
```bash
python3 -m pytest tests/unit/test_ai_advanced.py -v
```

## 📖 ДОКУМЕНТАЦИЯ

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Redoc: http://localhost:8000/redoc

## 🛠️ РАЗРАБОТКА

### Структура проекта
```
dev_exp_ai/
├── app/                    # Основное приложение
│   ├── api/v1/            # API endpoints
│   ├── services/          # Бизнес-логика
│   ├── models/            # Модели данных
│   └── security/          # Аутентификация
├── tests/                 # Тесты
├── scripts/               # Скрипты
└── docs/                  # Документация
```

### Основные команды
```bash
# Запуск тестов
make test

# Запуск линтера
make lint

# Очистка
make clean

# Логи
make logs
``` 