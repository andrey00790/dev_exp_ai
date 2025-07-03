# 🚀 AI Assistant MVP - Production Deployment Guide

**Версия:** 1.0.0  
**Дата:** 16 июня 2025  
**Статус:** ✅ Production Ready

## 📋 Содержание
1. [Системные требования](#системные-требования)
2. [Подготовка environment](#подготовка-environment)
3. [Развертывание backend](#развертывание-backend)
4. [Развертывание frontend](#развертывание-frontend)
5. [База данных и сервисы](#база-данных-и-сервисы)
6. [Безопасность](#безопасность)
7. [Мониторинг](#мониторинг)
8. [Backup и восстановление](#backup-и-восстановление)

---

## 🖥️ Системные требования

### **Минимальные требования**
- **CPU:** 4 cores
- **RAM:** 8 GB
- **Disk:** 100 GB SSD
- **OS:** Ubuntu 20.04+ / RHEL 8+ / macOS 12+

### **Рекомендуемые для production**
- **CPU:** 8+ cores
- **RAM:** 16+ GB
- **Disk:** 500+ GB NVMe SSD
- **OS:** Ubuntu 22.04 LTS

### **Внешние сервисы**
- **PostgreSQL:** 13+
- **Qdrant:** 1.9.0+
- **Redis:** 6.0+ (опционально)
- **Nginx:** 1.18+ (reverse proxy)

---

## 🔧 Подготовка Environment

### **1. Установка зависимостей**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.11 python3.11-venv nodejs npm nginx postgresql-client

# macOS
brew install python@3.11 node postgresql nginx

# Docker (альтернатива)
docker --version  # убедитесь что установлен
```

### **2. Клонирование проекта**
```bash
git clone <repository-url> ai-assistant
cd ai-assistant
git checkout main  # или production branch
```

### **3. Environment файлы**
```bash
# Создание production конфигурации
cp .env.example .env.production

# Настройка переменных
vim .env.production
```

**Пример .env.production:**
```env
# Application
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=your-domain.com,api.your-domain.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_assistant_prod
POSTGRES_DB=ai_assistant_prod
POSTGRES_USER=ai_assistant_user
POSTGRES_PASSWORD=secure_password_here

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-api-key

# AI Services
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
OLLAMA_BASE_URL=http://localhost:11434

# Security
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Monitoring
PROMETHEUS_ENABLED=true
SENTRY_DSN=https://your-sentry-dsn

# CORS
CORS_ORIGINS=https://your-domain.com,https://app.your-domain.com
```

---

## 🐍 Развертывание Backend

### **1. Python Environment**
```bash
# Создание виртуальной среды
python3.11 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt

# Обновление безопасности (важно!)
pip install --upgrade transformers>=4.50.0
pip install --upgrade jinja2>=3.1.6
pip install --upgrade aiohttp>=3.10.11
pip install --upgrade requests>=2.32.2
```

### **2. Database Migration**
```bash
# Создание базы данных
sudo -u postgres createdb ai_assistant_prod
sudo -u postgres createuser ai_assistant_user

# Применение схемы
python app/database/init_db.py

# Миграции (если есть)
python manage.py migrate
```

### **3. Systemd Service**
Создайте `/etc/systemd/system/ai-assistant.service`:
```ini
[Unit]
Description=AI Assistant API
After=network.target
Wants=postgresql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/ai-assistant
Environment=PATH=/opt/ai-assistant/venv/bin
ExecStart=/opt/ai-assistant/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# Активация сервиса
sudo systemctl daemon-reload
sudo systemctl enable ai-assistant
sudo systemctl start ai-assistant
sudo systemctl status ai-assistant
```

### **4. Проверка Backend**
```bash
curl http://localhost:8000/health
# Ожидаемый ответ: {"status": "healthy", ...}
```

---

## ⚛️ Развертывание Frontend

### **1. Build для Production**
```bash
cd frontend

# Установка зависимостей
npm ci

# Исправление безопасности (важно!)
npm audit fix
npm install --save-dev @types/node@latest

# Production build
npm run build

# Проверка размера бандла
ls -lh dist/assets/
```

### **2. Nginx Configuration**
Создайте `/etc/nginx/sites-available/ai-assistant`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Редирект на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL сертификаты
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    
    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # Frontend статика
    location / {
        root /opt/ai-assistant/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # Кэширование
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API прокси
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Таймауты
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # WebSocket поддержка
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
}
```

```bash
# Активация конфигурации
sudo ln -s /etc/nginx/sites-available/ai-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🗃️ База данных и сервисы

### **1. PostgreSQL Setup**
```bash
# Установка PostgreSQL
sudo apt install postgresql postgresql-contrib

# Настройка
sudo -u postgres psql
CREATE DATABASE ai_assistant_prod;
CREATE USER ai_assistant_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_assistant_prod TO ai_assistant_user;
\q

# Настройка pg_hba.conf для production
sudo vim /etc/postgresql/13/main/pg_hba.conf
# Добавить: host ai_assistant_prod ai_assistant_user 127.0.0.1/32 md5
```

### **2. Qdrant Vector Database**
```bash
# Docker способ (рекомендуемый)
docker run -d \
  --name qdrant-prod \
  -p 6333:6333 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant:v1.9.0

# Проверка
curl http://localhost:6333/health
```

### **3. Redis (опционально, для кэширования)**
```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Настройка безопасности
sudo vim /etc/redis/redis.conf
# Раскомментировать: requirepass your_secure_password
sudo systemctl restart redis-server
```

---

## 🔒 Безопасность

### **1. SSL Сертификаты**
```bash
# Let's Encrypt (бесплатно)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# Автообновление
sudo systemctl enable certbot.timer
```

### **2. Firewall**
```bash
# UFW настройка
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow from localhost to any port 8000
sudo ufw allow from localhost to any port 6333
```

### **3. Security Hardening**
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Удаление ненужных пакетов
sudo apt autoremove -y

# Настройка fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### **4. Environment Security**
```bash
# Права доступа
sudo chown -R www-data:www-data /opt/ai-assistant
sudo chmod 640 .env.production
sudo chmod 755 /opt/ai-assistant

# Backup секретов
sudo cp .env.production /root/backup/.env.production.backup
```

---

## 📊 Мониторинг

### **1. Prometheus Setup**
```bash
# Prometheus конфигурация
cat > /etc/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-assistant'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
EOF

sudo systemctl restart prometheus
```

### **2. Grafana Dashboards**
```bash
# Установка Grafana
sudo apt install grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# Доступ: http://localhost:3000 (admin/admin)
```

### **3. Log Management**
```bash
# Logrotate для приложения
sudo vim /etc/logrotate.d/ai-assistant
/var/log/ai-assistant/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload ai-assistant
    endscript
}
```

---

## 💾 Backup и восстановление

### **1. Database Backup**
```bash
#!/bin/bash
# /usr/local/bin/backup-db.sh
BACKUP_DIR="/opt/backups/ai-assistant"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# PostgreSQL backup
pg_dump -h localhost -U ai_assistant_user ai_assistant_prod \
  | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Qdrant backup
docker exec qdrant-prod sh -c 'tar czf - /qdrant/storage' \
  > $BACKUP_DIR/qdrant_backup_$DATE.tar.gz

# Cleanup старых бэкапов (хранить 30 дней)
find $BACKUP_DIR -name "*.gz" -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
# Автоматизация через cron
sudo crontab -e
# Добавить: 0 2 * * * /usr/local/bin/backup-db.sh
```

### **2. Восстановление**
```bash
# PostgreSQL restore
gunzip -c /opt/backups/ai-assistant/db_backup_YYYYMMDD_HHMMSS.sql.gz \
  | psql -h localhost -U ai_assistant_user ai_assistant_prod

# Qdrant restore
docker stop qdrant-prod
docker rm qdrant-prod
tar xzf /opt/backups/ai-assistant/qdrant_backup_YYYYMMDD_HHMMSS.tar.gz
# Запуск нового контейнера с восстановленными данными
```

---

## 🚀 Запуск в Production

### **Финальный чек-лист**
```bash
# 1. Проверка всех сервисов
sudo systemctl status ai-assistant
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis-server
docker ps | grep qdrant

# 2. Тестирование API
curl https://your-domain.com/api/v1/health
curl https://your-domain.com/api/v1/metrics

# 3. Проверка frontend
curl -I https://your-domain.com
# Должен вернуть 200 OK

# 4. SSL проверка
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# 5. Мониторинг
curl http://localhost:9090/targets  # Prometheus targets
```

### **Performance Tuning**
```bash
# Оптимизация PostgreSQL
sudo vim /etc/postgresql/13/main/postgresql.conf
# shared_buffers = 256MB
# effective_cache_size = 1GB
# random_page_cost = 1.1

# Оптимизация Nginx
sudo vim /etc/nginx/nginx.conf
# worker_processes auto;
# worker_connections 1024;
# keepalive_timeout 65;

sudo systemctl restart postgresql nginx
```

---

## ✅ Production Ready!

После выполнения всех шагов система готова к production использованию:

- ✅ **Backend API** работает с Systemd
- ✅ **Frontend** обслуживается через Nginx  
- ✅ **SSL/TLS** настроен с автообновлением
- ✅ **База данных** настроена и защищена
- ✅ **Мониторинг** с Prometheus/Grafana
- ✅ **Backup** автоматизирован
- ✅ **Security** hardening применен

**🎉 AI Assistant MVP готов к полноценному использованию в production!** 