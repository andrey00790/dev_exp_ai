# 🔧 AI Assistant - Troubleshooting Guide

**Версия:** 2.0 | **Дата:** Январь 2025 | **Статус:** Актуальный

---

## 🚨 Быстрая диагностика

### System Health Check
```bash
# Проверка всех сервисов одной командой
make system-health

# Или вручную:
curl http://localhost:8000/health | jq .
curl http://localhost:3000/health | jq .
docker ps | grep ai-assistant
```

### Common Quick Fixes
```bash
# Перезапуск всей системы
make restart

# Очистка кэша
make cache-clear

# Переиндексация данных
make reindex

# Проверка логов
make logs-tail
```

---

## 🔍 Диагностические команды

### Backend API Issues

**Проверка состояния API:**
```bash
# Health check
curl -v http://localhost:8000/health

# Detailed health
curl http://localhost:8000/health/detailed | jq .

# Metrics
curl http://localhost:8000/metrics | grep -E "(request|error|latency)"

# OpenAPI schema
curl http://localhost:8000/openapi.json | jq .info
```

**Database connectivity:**
```bash
# PostgreSQL connection
pg_isready -h localhost -p 5432 -U ai_user

# Connection test через Python
python -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('postgresql://ai_user:password@localhost/ai_assistant')
    result = await conn.fetchval('SELECT 1')
    print(f'DB connection: {result}')
    await conn.close()
asyncio.run(test())
"

# Active connections
docker exec -it ai-assistant-postgres psql -U ai_user -d ai_assistant -c "
SELECT count(*) as active_connections FROM pg_stat_activity;
"
```

**Vector Database (Qdrant):**
```bash
# Qdrant health
curl http://localhost:6333/health | jq .

# Collections status
curl http://localhost:6333/collections | jq .

# Collection info
curl http://localhost:6333/collections/ai_documents | jq .

# Count points
curl http://localhost:6333/collections/ai_documents/points/count | jq .
```

### Frontend Issues

**Build and dev server:**
```bash
cd frontend

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# Development server
npm run dev

# Build issues
npm run build 2>&1 | tee build.log

# Type checking
npm run type-check
```

**Browser console errors:**
```bash
# Check console for errors in browser
# F12 -> Console tab

# Common fixes:
# 1. Clear browser cache (Ctrl+Shift+R)
# 2. Disable ad blockers
# 3. Check network tab for failed requests
```

---

## 🐛 Типичные проблемы и решения

### Problem 1: API returns 500 errors

**Симптомы:**
- Все API запросы возвращают 500
- Health check fails
- Логи показывают Database connection errors

**Диагностика:**
```bash
# 1. Проверить логи API
docker logs ai-assistant-backend -f

# 2. Проверить подключение к БД
docker exec -it ai-assistant-postgres pg_isready

# 3. Проверить переменные окружения
docker exec -it ai-assistant-backend env | grep DATABASE_URL
```

**Решение:**
```bash
# 1. Перезапустить БД
docker restart ai-assistant-postgres

# 2. Проверить пароли в .env
grep DATABASE_URL .env

# 3. Переинициализировать БД если нужно
make db-reset
```

### Problem 2: Search returns no results

**Симптомы:**
- Поиск возвращает пустые результаты
- Даже точные запросы не работают
- Qdrant доступен

**Диагностика:**
```bash
# 1. Проверить количество документов
curl http://localhost:6333/collections/ai_documents/points/count

# 2. Проверить embedding service
curl -X POST http://localhost:8000/api/v1/test/embedding \
  -H "Content-Type: application/json" \
  -d '{"text": "test query"}'

# 3. Проверить логи поиска
docker logs ai-assistant-backend | grep -i search
```

**Решение:**
```bash
# 1. Переиндексировать документы
curl -X POST http://localhost:8000/api/v1/admin/reindex

# 2. Проверить настройки коллекции
curl http://localhost:6333/collections/ai_documents

# 3. Пересоздать коллекцию если нужно
curl -X DELETE http://localhost:6333/collections/ai_documents
curl -X POST http://localhost:8000/api/v1/admin/initialize
```

### Problem 3: High memory usage

**Симптомы:**
- Docker containers потребляют >8GB RAM
- System становится медленной
- OOM kills в логах

**Диагностика:**
```bash
# 1. Проверить использование памяти
docker stats

# 2. Memory profiling для backend
docker exec -it ai-assistant-backend python -c "
import psutil
process = psutil.Process()
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"

# 3. Проверить кэш Redis
docker exec -it ai-assistant-redis redis-cli info memory
```

**Решение:**
```bash
# 1. Очистить кэш
docker exec -it ai-assistant-redis redis-cli FLUSHALL

# 2. Настроить memory limits в docker-compose
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G

# 3. Перезапустить с ограничениями
docker-compose down && docker-compose up -d
```

### Problem 4: Slow API responses

**Симптомы:**
- API responses >5 seconds
- Timeouts в frontend
- Высокий CPU usage

**Диагностика:**
```bash
# 1. Проверить метрики производительности
curl http://localhost:8000/metrics | grep request_duration

# 2. Database query analysis
docker exec -it ai-assistant-postgres psql -U ai_user -d ai_assistant -c "
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
"

# 3. Проверить connection pool
docker logs ai-assistant-backend | grep -i "connection\|pool"
```

**Решение:**
```bash
# 1. Оптимизировать database connections
# В .env увеличить pool size
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# 2. Добавить индексы если нужно
docker exec -it ai-assistant-postgres psql -U ai_user -d ai_assistant -c "
CREATE INDEX CONCURRENTLY idx_documents_created_at ON documents(created_at);
"

# 3. Настроить Redis caching
# Проверить hit rate
docker exec -it ai-assistant-redis redis-cli info stats | grep hit
```

---

## 📊 Мониторинг и алерты

### Grafana Dashboards

**Доступ к мониторингу:**
```bash
# Grafana
open http://localhost:3001
# Login: admin / admin

# Prometheus
open http://localhost:9090

# Key metrics to watch:
# - API response time (95th percentile < 2s)
# - Error rate (< 1%)
# - Memory usage (< 80%)
# - Database connections (< 80% of pool)
```

### Setting up alerts

**Prometheus alerts config:**
```yaml
# prometheus/rules/alerts.yml
groups:
  - name: ai-assistant
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 2m
        annotations:
          summary: "High error rate detected"
          
      - alert: SlowResponses
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
        for: 5m
        annotations:
          summary: "Slow API responses"
```

---

## 🔧 Performance Optimization

### Database Tuning

**PostgreSQL optimization:**
```sql
-- Check slow queries
SELECT query, mean_exec_time, calls, total_exec_time 
FROM pg_stat_statements 
WHERE mean_exec_time > 1000  -- queries slower than 1s
ORDER BY mean_exec_time DESC;

-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_documents_vector_search 
ON documents USING gin(to_tsvector('english', content));

-- Analyze and vacuum
ANALYZE documents;
VACUUM ANALYZE documents;
```

**Connection pooling:**
```python
# app/database/session.py
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,        # Увеличить для высокой нагрузки
    max_overflow=30,     # Дополнительные соединения
    pool_pre_ping=True,  # Проверка соединений
    pool_recycle=3600,   # Пересоздание каждый час
)
```

### Vector Search Optimization

**Qdrant optimization:**
```bash
# Optimize collection parameters
curl -X PUT http://localhost:6333/collections/ai_documents \
-H "Content-Type: application/json" \
-d '{
  "optimizers_config": {
    "default_segment_number": 2,
    "max_segment_size": 20000,
    "memmap_threshold": 20000
  },
  "hnsw_config": {
    "m": 16,
    "ef_construct": 200
  }
}'

# Create payload index for filtering
curl -X PUT http://localhost:6333/collections/ai_documents/index \
-H "Content-Type: application/json" \
-d '{
  "field_name": "source_type",
  "field_schema": "keyword"
}'
```

---

## 🔐 Security Issues

### SSL/TLS Problems

**Certificate issues:**
```bash
# Check certificate
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Certificate expiry
openssl x509 -in cert.pem -text -noout | grep "Not After"

# Let's Encrypt renewal
certbot renew --dry-run
```

### Authentication Issues

**JWT token problems:**
```bash
# Decode JWT token
echo "your.jwt.token" | base64 -d

# Check token expiry
python -c "
import jwt
token = 'your.jwt.token'
decoded = jwt.decode(token, options={'verify_signature': False})
print(f'Expires: {decoded.get(\"exp\")}')
"

# Reset JWT secret
# Generate new secret and restart API
openssl rand -hex 32
```

---

## 📋 Diagnostic Checklists

### Before Production Deployment
- [ ] All health checks pass
- [ ] Database migrations applied
- [ ] SSL certificates valid
- [ ] Monitoring configured
- [ ] Backup procedures tested
- [ ] Load testing completed
- [ ] Security scan passed

### During Incident Response
- [ ] Check system health dashboard
- [ ] Review recent deployments
- [ ] Check external service status
- [ ] Examine error logs
- [ ] Verify database connectivity
- [ ] Test API endpoints manually
- [ ] Check resource usage (CPU/Memory/Disk)

### Post-Incident
- [ ] Root cause identified
- [ ] Fix implemented and tested
- [ ] Monitoring alerts updated
- [ ] Documentation updated
- [ ] Team retrospective scheduled

---

## 📞 Emergency Contacts

### On-Call Escalation
```
Level 1: DevOps Engineer
- Slack: @oncall-devops
- Phone: +7-XXX-XXX-XXXX

Level 2: Senior SRE  
- Slack: @oncall-sre
- Phone: +7-XXX-XXX-XXXX

Level 3: Engineering Manager
- Email: eng-manager@company.com
- Phone: +7-XXX-XXX-XXXX
```

### Service Dependencies
```bash
# External service status pages:
echo "OpenAI: https://status.openai.com/"
echo "Anthropic: https://status.anthropic.com/"
echo "GitHub: https://www.githubstatus.com/"
echo "Docker Hub: https://status.docker.com/"

# Internal dependencies:
curl http://internal-service.company.com/health
```

---

**Quick Reference:**
- 🆘 Emergency shutdown: `make emergency-stop`
- 🔄 Quick restart: `make restart`  
- 📊 System status: `make status`
- 📋 Full health check: `make health-check`
- 🧹 Clean everything: `make clean-all` 