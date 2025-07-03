# �� AI Assistant MVP - Руководство по развертыванию

**Версия:** 2.0  
**Дата актуализации:** 28 декабря 2024  
**Статус:** Актуализировано на основе реальной кодовой базы  

---

## 🎯 ОБЗОР РАЗВЕРТЫВАНИЯ

### Поддерживаемые способы развертывания
1. **Docker Compose** (рекомендуется для разработки и тестирования)
2. **Kubernetes** (рекомендуется для продакшена)
3. **Docker Standalone** (для быстрого тестирования)

### Системные требования

#### Минимальные требования
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
- **Network**: 100 Mbps

#### Рекомендуемые требования (продакшен)
- **CPU**: 8+ cores
- **RAM**: 16+ GB
- **Storage**: 200+ GB SSD
- **Network**: 1 Gbps

### Поддерживаемые операционные системы
- **Linux**: Ubuntu 20.04+, CentOS 8+, RHEL 8+
- **macOS**: 12.0+ (для разработки)
- **Windows**: Windows 10+ с WSL2 (для разработки)

---

## 🐳 DOCKER COMPOSE РАЗВЕРТЫВАНИЕ

### Предварительные требования

#### Установка Docker
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# CentOS/RHEL
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install docker-ce docker-ce-cli containerd.io
sudo systemctl enable --now docker
```

#### Установка Docker Compose
```bash
# Standalone installation
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Конфигурация окружения

#### Создание .env файла
```bash
# Скопируйте и настройте переменные окружения
cp config/production.env .env

# Отредактируйте .env файл
nano .env
```

#### Основные переменные окружения
```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:your_password@postgres:5432/ai_assistant
REDIS_URL=redis://redis:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# AI Services
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Vector Database
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=your_qdrant_api_key

# Search Engine
ELASTICSEARCH_URL=http://elasticsearch:9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=your_elastic_password

# Security
SECRET_KEY=your_super_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# External Integrations
CONFLUENCE_API_TOKEN=your_confluence_token
JIRA_API_TOKEN=your_jira_token
GITLAB_API_TOKEN=your_gitlab_token

# Monitoring
ENABLE_METRICS=true
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Развертывание с Docker Compose

#### Полное развертывание
```bash
# Клонирование репозитория
git clone https://github.com/your-org/ai-assistant-mvp.git
cd ai-assistant-mvp

# Запуск всех сервисов
docker-compose -f deployment/docker/docker-compose.full.yml up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f api
```

#### Компоненты системы
```yaml
# deployment/docker/docker-compose.full.yml
services:
  # Core API
  api:
    build: .
    ports: 
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
      
  # Frontend
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
      
  # Databases
  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=ai_assistant
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
      
  # Vector & Search
  qdrant:
    image: qdrant/qdrant:v1.7.0
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
      
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    ports:
      - "9200:9200"
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
      
  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
      
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
```

### Инициализация базы данных

#### Автоматическая миграция
```bash
# Выполнение миграций
docker-compose exec api alembic upgrade head

# Создание пользователя-администратора
docker-compose exec api python -m scripts.create_admin_user

# Загрузка тестовых данных (опционально)
docker-compose exec api python -m scripts.load_sample_data
```

#### Ручная инициализация
```bash
# Подключение к PostgreSQL
docker-compose exec postgres psql -U postgres -d ai_assistant

-- Создание схемы
CREATE SCHEMA IF NOT EXISTS ai_assistant;

-- Создание пользователя
CREATE USER ai_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ai_assistant TO ai_user;
```

### Проверка развертывания

#### Проверка сервисов
```bash
# Проверка API
curl http://localhost:8000/health

# Проверка frontend
curl http://localhost:3000

# Проверка Prometheus
curl http://localhost:9090/metrics

# Проверка Grafana
curl http://localhost:3001/api/health
```

#### Проверка базы данных
```bash
# PostgreSQL
docker-compose exec postgres pg_isready

# Redis
docker-compose exec redis redis-cli ping

# Qdrant
curl http://localhost:6333/health

# Elasticsearch
curl http://localhost:9200/_cluster/health
```

---

## ☸️ KUBERNETES РАЗВЕРТЫВАНИЕ

### Предварительная подготовка

#### Создание namespace
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-assistant
  labels:
    name: ai-assistant
```

#### Конфигурация ConfigMap
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-assistant-config
  namespace: ai-assistant
data:
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  REDIS_URL: "redis://redis-service:6379/0"
  QDRANT_URL: "http://qdrant-service:6333"
  ELASTICSEARCH_URL: "http://elasticsearch-service:9200"
  ENABLE_METRICS: "true"
```

#### Секреты
```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-assistant-secrets
  namespace: ai-assistant
type: Opaque
stringData:
  DATABASE_URL: "postgresql://postgres:password@postgres-service:5432/ai_assistant"
  SECRET_KEY: "your-super-secret-key"
  JWT_SECRET_KEY: "your-jwt-secret-key"
  OPENAI_API_KEY: "your-openai-api-key"
  ANTHROPIC_API_KEY: "your-anthropic-api-key"
```

### Развертывание компонентов

#### API Deployment
```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-assistant-api
  namespace: ai-assistant
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-assistant-api
  template:
    metadata:
      labels:
        app: ai-assistant-api
    spec:
      containers:
      - name: api
        image: ai-assistant:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: ai-assistant-config
        - secretRef:
            name: ai-assistant-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Database Deployment
```yaml
# k8s/postgres-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: ai-assistant
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: "ai_assistant"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ai-assistant-secrets
              key: POSTGRES_PASSWORD
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
```

#### Services
```yaml
# k8s/services.yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-assistant-api-service
  namespace: ai-assistant
spec:
  selector:
    app: ai-assistant-api
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: ai-assistant
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

#### Ingress
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-assistant-ingress
  namespace: ai-assistant
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: ai-assistant-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ai-assistant-api-service
            port:
              number: 8000
```

### Развертывание в Kubernetes

#### Применение конфигураций
```bash
# Создание namespace
kubectl apply -f k8s/namespace.yaml

# Применение секретов и configmap
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml

# Развертывание компонентов
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# Создание сервисов
kubectl apply -f k8s/services.yaml

# Настройка ingress
kubectl apply -f k8s/ingress.yaml
```

#### Проверка развертывания
```bash
# Проверка pods
kubectl get pods -n ai-assistant

# Проверка services
kubectl get svc -n ai-assistant

# Проверка ingress
kubectl get ingress -n ai-assistant

# Просмотр логов
kubectl logs -f deployment/ai-assistant-api -n ai-assistant
```

---

## 🔧 КОНФИГУРАЦИЯ И НАСТРОЙКА

### Настройка производительности

#### Оптимизация API
```yaml
# В docker-compose или Kubernetes
environment:
  - UVICORN_WORKERS=4
  - UVICORN_MAX_REQUESTS=1000
  - UVICORN_MAX_REQUESTS_JITTER=100
  - DATABASE_POOL_SIZE=20
  - DATABASE_MAX_OVERFLOW=30
  - REDIS_POOL_SIZE=50
```

#### Настройка кэширования
```yaml
# Redis конфигурация
environment:
  - REDIS_MAXMEMORY=2gb
  - REDIS_MAXMEMORY_POLICY=allkeys-lru
  - REDIS_TIMEOUT=300
  - CACHE_TTL=3600
```

#### Оптимизация векторной БД
```yaml
# Qdrant настройки
environment:
  - QDRANT_STORAGE_PATH=/qdrant/storage
  - QDRANT_MAX_SEARCH_DISTANCE=0.8
  - QDRANT_VECTOR_SIZE=1536
  - QDRANT_HNSW_M=16
  - QDRANT_HNSW_EF_CONSTRUCT=200
```

### SSL/TLS конфигурация

#### Использование Let's Encrypt
```yaml
# docker-compose с nginx и certbot
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
      
  certbot:
    image: certbot/certbot
    volumes:
      - ./ssl:/etc/letsencrypt
    command: certonly --webroot --webroot-path=/var/www/html --email your@email.com --agree-tos --no-eff-email -d yourdomain.com
```

#### Nginx конфигурация
```nginx
# nginx.conf
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/fullchain.pem;
    ssl_certificate_key /etc/ssl/certs/privkey.pem;
    
    # API proxy
    location /api/ {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Frontend
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📊 МОНИТОРИНГ И ЛОГИРОВАНИЕ

### Настройка мониторинга

#### Prometheus конфигурация
```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  
scrape_configs:
  - job_name: 'ai-assistant-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
      
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

#### Grafana дашборды
```bash
# Импорт дашбордов
curl -X POST \
  http://admin:password@grafana:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @monitoring/grafana/dashboards/api-metrics.json
```

### Логирование

#### Centralized logging с ELK
```yaml
# docker-compose.logging.yml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
      
  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
      
  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

---

## 🚨 TROUBLESHOOTING

### Общие проблемы

#### Проблемы с базой данных
```bash
# Проверка подключения к PostgreSQL
docker-compose exec postgres pg_isready -h localhost -p 5432

# Сброс базы данных
docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS ai_assistant;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE ai_assistant;"

# Повторная миграция
docker-compose exec api alembic upgrade head
```

#### Проблемы с Redis
```bash
# Проверка Redis
docker-compose exec redis redis-cli ping

# Очистка кэша
docker-compose exec redis redis-cli FLUSHALL

# Проверка использования памяти
docker-compose exec redis redis-cli INFO memory
```

#### Проблемы с API
```bash
# Проверка логов API
docker-compose logs -f api

# Перезапуск API
docker-compose restart api

# Проверка health endpoint
curl -f http://localhost:8000/health || echo "API not healthy"
```

### Диагностика производительности

#### Мониторинг ресурсов
```bash
# Использование ресурсов контейнеров
docker stats

# Использование дискового пространства
docker system df

# Очистка неиспользуемых ресурсов
docker system prune -af
```

#### Профилирование API
```bash
# Включение профилирования
export ENABLE_PROFILING=true
docker-compose restart api

# Анализ slow queries
docker-compose exec postgres psql -U postgres -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

---

## 🔄 ОБНОВЛЕНИЕ И МИГРАЦИЯ

### Обновление версии

#### Blue-Green Deployment
```bash
# Создание новой версии
docker-compose -f docker-compose.blue.yml up -d

# Проверка работоспособности
curl http://localhost:8001/health

# Переключение трафика
nginx -s reload

# Остановка старой версии
docker-compose -f docker-compose.green.yml down
```

#### Rolling Update в Kubernetes
```bash
# Обновление image
kubectl set image deployment/ai-assistant-api api=ai-assistant:v2.0 -n ai-assistant

# Проверка статуса
kubectl rollout status deployment/ai-assistant-api -n ai-assistant

# Откат в случае проблем
kubectl rollout undo deployment/ai-assistant-api -n ai-assistant
```

### Миграция данных

#### Backup базы данных
```bash
# PostgreSQL backup
docker-compose exec postgres pg_dump -U postgres ai_assistant > backup_$(date +%Y%m%d_%H%M%S).sql

# Redis backup
docker-compose exec redis redis-cli BGSAVE
```

#### Восстановление
```bash
# PostgreSQL restore
docker-compose exec -T postgres psql -U postgres ai_assistant < backup_20241228_140000.sql

# Redis restore
docker-compose exec redis redis-cli FLUSHALL
docker cp backup.rdb $(docker-compose ps -q redis):/data/dump.rdb
docker-compose restart redis
```

---

## ✅ CHECKLIST РАЗВЕРТЫВАНИЯ

### Pre-deployment Checklist
- [ ] Docker и Docker Compose установлены
- [ ] .env файл настроен с правильными значениями
- [ ] SSL сертификаты готовы (для продакшена)
- [ ] DNS записи настроены
- [ ] Firewall правила настроены
- [ ] Backup стратегия определена

### Deployment Checklist
- [ ] Все сервисы запущены успешно
- [ ] Health checks проходят
- [ ] База данных инициализирована
- [ ] Миграции выполнены
- [ ] Admin пользователь создан
- [ ] API endpoints отвечают
- [ ] Frontend доступен
- [ ] Мониторинг настроен

### Post-deployment Checklist
- [ ] Функциональное тестирование пройдено
- [ ] Performance тестирование выполнено
- [ ] Security scan пройден
- [ ] Backup протестирован
- [ ] Логи настроены и работают
- [ ] Alerts настроены
- [ ] Документация обновлена

---

**Статус развертывания:** ✅ Production Ready  
**Поддерживаемые платформы:** Docker, Kubernetes  
**Автоматизация:** CI/CD готова  
**Мониторинг:** Полный набор метрик  
**Последнее обновление:** 28 декабря 2024 