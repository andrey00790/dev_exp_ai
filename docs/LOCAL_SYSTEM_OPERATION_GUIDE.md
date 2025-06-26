# AI Assistant - Local System Operation Guide

Complete guide for operating the AI Assistant platform as a full containerized system locally.

## 🎯 Overview

This guide covers running the AI Assistant as a complete system using Docker containers, similar to production but on your local machine. Perfect for:

- **System testing** - Test complete workflows
- **Demo purposes** - Show the full platform
- **Integration testing** - Test with external services
- **Performance testing** - Load testing and benchmarks

---

## 🚀 Quick System Start

### One-Command Deployment

```bash
# Start complete system
make system-up

# Access the system
open http://localhost:8000/docs    # API Documentation
open http://localhost:3000         # Frontend
```

### System with Monitoring

```bash
# Start system with full monitoring stack
make system-up-full

# Access monitoring
open http://localhost:3001         # Grafana (admin/admin123)
open http://localhost:9090         # Prometheus
```

---

## 📋 System Components

### Core Services

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| **Backend API** | `ai_assistant_backend` | 8000 | Main API server |
| **Frontend** | `ai_assistant_frontend` | 3000 | React web interface |
| **PostgreSQL** | `ai_assistant_postgres` | 5432 | Primary database |
| **Redis** | `ai_assistant_redis` | 6379 | Cache & sessions |
| **Qdrant** | `ai_assistant_qdrant` | 6333, 6334 | Vector database |

### Optional Services

| Service | Container | Port | Profile | Purpose |
|---------|-----------|------|---------|---------|
| **Data Ingestion** | `ai_assistant_ingestion` | - | `ingestion` | Data processing |
| **Prometheus** | `ai_assistant_prometheus` | 9090 | `monitoring` | Metrics collection |
| **Grafana** | `ai_assistant_grafana` | 3001 | `monitoring` | Metrics visualization |

---

## 🛠 System Management

### Starting the System

```bash
# Basic system (API + Frontend + Databases)
make system-up

# Full system with monitoring
make system-up-full

# Check system status
make system-status
```

### Stopping the System

```bash
# Stop all services
make system-down

# Stop and remove volumes (⚠️ data loss)
docker-compose -f deployment/docker/docker-compose.simple.yml down -v
```

### System Health & Monitoring

```bash
# Check system health
make health

# Detailed health check
make health-detailed

# View system status
make status

# Monitor logs
make system-logs
```

### System Restart

```bash
# Restart entire system
make system-restart

# Restart specific service
docker-compose -f deployment/docker/docker-compose.simple.yml restart backend
```

---

## 📊 Monitoring & Observability

### Grafana Dashboards

Access: http://localhost:3001 (admin/admin123)

**Available Dashboards:**
- **Application Overview** - API performance, response times
- **Database Metrics** - PostgreSQL performance
- **System Resources** - CPU, memory, disk usage
- **AI Processing** - LLM request metrics

### Prometheus Metrics

Access: http://localhost:9090

**Key Metrics:**
- `http_requests_total` - API request count
- `http_request_duration_seconds` - Request latency
- `database_connections_active` - DB connections
- `vector_search_duration_seconds` - Search performance

### Application Logs

```bash
# All system logs
make system-logs

# Specific service logs  
docker logs ai_assistant_backend -f
docker logs ai_assistant_frontend -f
docker logs ai_assistant_postgres -f

# Application logs with filtering
docker logs ai_assistant_backend 2>&1 | grep ERROR
```

---

## 🔧 Configuration Management

### Environment Configuration

System uses production-like configuration in `deployment/docker/docker-compose.full.yml`:

```yaml
environment:
  - DATABASE_URL=postgresql://ai_user:ai_password_secure_2024@postgres:5432/ai_assistant
  - REDIS_URL=redis://redis:6379/0
  - QDRANT_URL=http://qdrant:6333
  - ENVIRONMENT=production
  - DEBUG=false
```

### Custom Configuration

Create `.env.local` file in project root:

```bash
# .env.local - Override production defaults
OPENAI_API_KEY=sk-your-actual-key
ANTHROPIC_API_KEY=sk-ant-your-actual-key
DEBUG=true
LOG_LEVEL=INFO
```

### Service Configuration

```bash
# Edit service configuration
vim deployment/docker/docker-compose.full.yml

# Restart specific service after config change
docker-compose -f deployment/docker/docker-compose.full.yml restart backend
```

---

## 🗄 Database Operations

### Database Access

```bash
# Access PostgreSQL directly
docker exec -it ai_assistant_postgres psql -U ai_user -d ai_assistant

# Run SQL file
docker exec -i ai_assistant_postgres psql -U ai_user -d ai_assistant < backup.sql

# Database shell via adminer (if running)
open http://localhost:8080
```

### Database Backup & Restore

```bash
# Create backup
docker exec ai_assistant_postgres pg_dump -U ai_user ai_assistant > backup_$(date +%Y%m%d).sql

# Restore from backup
docker exec -i ai_assistant_postgres psql -U ai_user ai_assistant < backup_20231201.sql

# Full database reset (⚠️ destructive)
docker-compose -f deployment/docker/docker-compose.simple.yml stop postgres
docker-compose -f deployment/docker/docker-compose.simple.yml rm -f postgres
docker volume rm ai_assistant_postgres_data
make system-up
```

### Migration Management

```bash
# Check migration status
docker exec ai_assistant_backend alembic current

# Apply migrations
docker exec ai_assistant_backend alembic upgrade head

# View migration history  
docker exec ai_assistant_backend alembic history
```

---

## 🔍 Data Management

### Vector Database (Qdrant)

```bash
# Access Qdrant API
curl http://localhost:6333/collections

# Qdrant web UI
open http://localhost:6333/dashboard

# Check collections and data
curl http://localhost:6333/collections/documents/info
```

### Redis Cache Management

```bash
# Access Redis CLI
docker exec -it ai_assistant_redis redis-cli

# Check cache statistics  
docker exec ai_assistant_redis redis-cli info stats

# Clear cache (if needed)
docker exec ai_assistant_redis redis-cli flushall
```

### Data Ingestion

```bash
# Start data ingestion service
docker-compose -f deployment/docker/docker-compose.full.yml --profile ingestion up -d

# Check ingestion logs
docker logs ai_assistant_ingestion -f

# Trigger manual sync
curl -X POST http://localhost:8000/api/v1/sync/run-startup-sync
```

---

## 🧪 Testing the System

### Smoke Tests

```bash
# Basic system health
curl http://localhost:8000/health

# API functionality
curl http://localhost:8000/api/v1/search/simple?q=test

# Frontend accessibility
curl -I http://localhost:3000
```

### Load Testing

```bash
# Start system for load testing
make system-up

# Run load tests
make test-load

# Monitor during load test
make system-logs
```

### Integration Testing

```bash
# Run integration tests against system
make test-integration

# Run E2E tests
make test-e2e
```

---

## 🚀 Performance Optimization

### Resource Monitoring

```bash
# Check container resources
docker stats

# System resource usage
htop
df -h
```

### Performance Tuning

1. **Database Performance**
   ```bash
   # Tune PostgreSQL settings
   docker exec ai_assistant_postgres psql -U ai_user -d ai_assistant -c "
     ALTER SYSTEM SET shared_buffers = '256MB';
     ALTER SYSTEM SET max_connections = 200;
     SELECT pg_reload_conf();
   "
   ```

2. **Redis Optimization**
   ```bash
   # Check Redis memory usage
   docker exec ai_assistant_redis redis-cli info memory
   
   # Optimize Redis config (already configured in docker-compose)
   # maxmemory 512mb, allkeys-lru policy
   ```

3. **Application Scaling**
   ```bash
   # Scale backend instances
   docker-compose -f deployment/docker/docker-compose.full.yml up -d --scale backend=3
   
   # Load balance with nginx (add nginx config)
   ```

---

## 🔐 Security Operations

### Security Monitoring

```bash
# Check running processes
docker exec ai_assistant_backend ps aux

# Check network connections
docker exec ai_assistant_backend netstat -tlnp

# Review application logs for security events
docker logs ai_assistant_backend 2>&1 | grep -i "auth\|security\|error"
```

### Access Control

```bash
# View active user sessions
docker exec ai_assistant_redis redis-cli keys "session:*"

# Check API key usage (if implemented)
curl http://localhost:8000/api/v1/monitoring/api-usage
```

### Security Updates

```bash
# Update container images
docker-compose -f deployment/docker/docker-compose.full.yml pull

# Restart with new images
make system-restart
```

---

## 📦 Backup & Recovery

### Complete System Backup

```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)

# Database backup
docker exec ai_assistant_postgres pg_dump -U ai_user ai_assistant | gzip > backups/$(date +%Y%m%d)/database.sql.gz

# Vector database backup
docker exec ai_assistant_qdrant tar czf - /qdrant/storage > backups/$(date +%Y%m%d)/qdrant.tar.gz

# Configuration backup
tar czf backups/$(date +%Y%m%d)/config.tar.gz deployment/ config/ .env*

# Application data backup (if any)
docker exec ai_assistant_backend tar czf - /app/data > backups/$(date +%Y%m%d)/appdata.tar.gz
```

### System Recovery

```bash
# Stop system
make system-down

# Restore database
zcat backups/20231201/database.sql.gz | docker exec -i ai_assistant_postgres psql -U ai_user ai_assistant

# Restore vector database
docker exec -i ai_assistant_qdrant tar xzf - -C / < backups/20231201/qdrant.tar.gz

# Restart system
make system-up
```

### Automated Backup

Create `scripts/backup-system.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/ai-assistant"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database
docker exec ai_assistant_postgres pg_dump -U ai_user ai_assistant | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Vector DB
docker exec ai_assistant_qdrant tar czf - /qdrant/storage > $BACKUP_DIR/qdrant_$DATE.tar.gz

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "*.gz" -type f -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Make executable and add to cron
chmod +x scripts/backup-system.sh
(crontab -l; echo "0 2 * * * /path/to/scripts/backup-system.sh") | crontab -
```

---

## 🐛 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker daemon
docker info

# Check available resources
docker system df
docker system prune -f

# Check port conflicts
netstat -tlnp | grep :8000
```

#### Database Connection Issues
```bash
# Check PostgreSQL logs
docker logs ai_assistant_postgres

# Test connection
docker exec ai_assistant_postgres pg_isready -U ai_user

# Reset database password
docker exec ai_assistant_postgres psql -U postgres -c "ALTER USER ai_user PASSWORD 'new_password';"
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Check system load
uptime
free -h

# Optimize if needed
docker system prune -f
```

#### Network Issues
```bash
# Check container networking
docker network ls
docker network inspect deployment_ai_network

# Test service connectivity
docker exec ai_assistant_backend ping postgres
docker exec ai_assistant_backend curl http://qdrant:6333/health
```

### Emergency Procedures

#### Complete System Reset
```bash
# ⚠️ WARNING: This will destroy all data
make system-down
docker system prune -a -f --volumes
make system-up
```

#### Service Recovery
```bash
# Restart failed service
docker-compose -f deployment/docker/docker-compose.full.yml restart <service_name>

# Recreate problematic service
docker-compose -f deployment/docker/docker-compose.full.yml up -d --force-recreate <service_name>
```

#### Data Corruption Recovery
```bash
# Stop system
make system-down

# Restore from backup
# (see Backup & Recovery section)

# Start system
make system-up

# Verify data integrity
make health-detailed
```

---

## 📈 Scaling & Performance

### Horizontal Scaling

```bash
# Scale backend services
docker-compose -f deployment/docker/docker-compose.full.yml up -d --scale backend=3

# Add load balancer (nginx)
# Edit docker-compose to add nginx service
```

### Vertical Scaling

Edit resource limits in `docker-compose.full.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Performance Monitoring

```bash
# Real-time resource monitoring
watch docker stats

# Application metrics
curl http://localhost:8000/api/v1/monitoring/metrics

# Database performance
docker exec ai_assistant_postgres psql -U ai_user -d ai_assistant -c "SELECT * FROM pg_stat_activity;"
```

---

## 🔗 Integration with External Services

### API Keys Configuration

Set in `.env.local`:
```bash
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
GITHUB_TOKEN=ghp_your-token
SLACK_BOT_TOKEN=xoxb-your-token
```

### External Data Sources

Configure via API or admin interface:
- Confluence endpoints
- GitLab repositories  
- Jira projects
- Slack workspaces

### Webhook Configuration

```bash
# Example: Configure GitHub webhooks
curl -X POST http://localhost:8000/api/v1/webhooks/github \
  -H "Content-Type: application/json" \
  -d '{"url": "https://api.github.com", "token": "your-token"}'
```

---

## 📚 Additional Resources

- [Local Development Guide](LOCAL_DEVELOPMENT_GUIDE.md) - Development setup
- [Production Deployment Guide](PRODUCTION_DEPLOYMENT_GUIDE.md) - Kubernetes deployment
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Monitoring Dashboards](http://localhost:3001) - Grafana dashboards

---

## 💡 Best Practices

### Daily Operations

1. **Morning Health Check**
   ```bash
   make health
   make status
   ```

2. **Resource Monitoring**
   ```bash
   docker stats --no-stream
   df -h
   ```

3. **Log Review**
   ```bash
   make system-logs | grep ERROR
   ```

### Weekly Maintenance

1. **System Cleanup**
   ```bash
   docker system prune -f
   ```

2. **Backup Verification**
   ```bash
   ls -la backups/
   ```

3. **Security Updates**
   ```bash
   docker-compose pull
   make system-restart
   ```

### Monthly Tasks

1. **Performance Review**
   - Check Grafana dashboards
   - Review resource usage trends
   - Optimize if needed

2. **Backup Rotation**
   - Archive old backups
   - Test recovery procedures

3. **Configuration Review**
   - Update service configurations
   - Review security settings

---

This guide provides comprehensive coverage of local system operations. For production deployment, refer to the [Production Deployment Guide](PRODUCTION_DEPLOYMENT_GUIDE.md). 