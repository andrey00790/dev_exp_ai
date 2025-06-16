# AI Assistant MVP - Deployment Guide

## 🚀 Production Deployment Guide

### Prerequisites

#### System Requirements
- **CPU**: 4+ cores (8+ recommended for LLM)
- **RAM**: 16GB minimum (32GB+ recommended)
- **Storage**: 100GB+ SSD
- **GPU**: Optional (NVIDIA GPU for faster LLM inference)
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Docker-compatible

#### Software Requirements
- Docker 20.10+
- Docker Compose 2.0+
- Git
- SSL certificates (for HTTPS)

### 🔧 Quick Start (Docker Compose)

#### 1. Clone Repository
```bash
git clone <repository-url>
cd ai-assistant-mvp
```

#### 2. Environment Configuration
```bash
# Copy and edit production environment
cp config/production.env .env

# Edit environment variables
nano .env

# Required changes:
# - JWT_SECRET_KEY: Generate strong secret key
# - DATABASE_URL: Set secure database credentials
# - OPENAI_API_KEY: Add if using OpenAI (optional)
# - CORS_ORIGINS: Set your domain
```

#### 3. SSL Certificates (Production)
```bash
# Create SSL directory
mkdir -p nginx/ssl

# Add your SSL certificates
cp your-domain.crt nginx/ssl/
cp your-domain.key nginx/ssl/

# Or use Let's Encrypt
certbot certonly --standalone -d yourdomain.com
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/
```

#### 4. Deploy Services
```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

#### 5. Initialize Database
```bash
# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head

# Create demo users (optional)
docker-compose -f docker-compose.prod.yml exec backend python scripts/create_demo_users.py
```

#### 6. Setup Ollama Models
```bash
# Pull required models
docker-compose -f docker-compose.prod.yml exec ollama ollama pull mistral:instruct

# Verify model is available
docker-compose -f docker-compose.prod.yml exec ollama ollama list
```

### 🌐 Service URLs

After deployment, services will be available at:

- **Frontend**: http://localhost (or your domain)
- **Backend API**: http://localhost/api
- **API Documentation**: http://localhost/api/docs
- **Grafana Dashboard**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Qdrant**: http://localhost:6333

### 🔒 Security Configuration

#### 1. Change Default Passwords
```bash
# Database password
# Edit .env file: DATABASE_URL

# Grafana password
# Edit docker-compose.prod.yml: GF_SECURITY_ADMIN_PASSWORD

# JWT Secret
# Edit .env file: JWT_SECRET_KEY (minimum 32 characters)
```

#### 2. Firewall Configuration
```bash
# Allow only necessary ports
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable
```

#### 3. SSL/TLS Setup
```bash
# Update nginx configuration for HTTPS
# Edit nginx/nginx.conf to include SSL configuration
```

### 📊 Monitoring Setup

#### 1. Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-assistant-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

#### 2. Grafana Dashboards
- Import pre-configured dashboards from `monitoring/grafana/dashboards/`
- Default login: admin/admin123
- Change password on first login

### 🔄 Backup & Recovery

#### 1. Database Backup
```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U ai_user ai_assistant > backup.sql

# Restore backup
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U ai_user ai_assistant < backup.sql
```

#### 2. Vector Database Backup
```bash
# Backup Qdrant data
docker-compose -f docker-compose.prod.yml exec qdrant tar -czf /tmp/qdrant-backup.tar.gz /qdrant/storage
docker cp $(docker-compose -f docker-compose.prod.yml ps -q qdrant):/tmp/qdrant-backup.tar.gz ./qdrant-backup.tar.gz
```

#### 3. Application Data Backup
```bash
# Backup uploads and logs
tar -czf app-data-backup.tar.gz uploads/ logs/
```

### 🚀 Scaling & Performance

#### 1. Horizontal Scaling
```yaml
# Scale backend services
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Load balancer configuration needed
```

#### 2. Performance Tuning
```bash
# Database optimization
# Edit postgresql.conf:
# shared_buffers = 256MB
# effective_cache_size = 1GB
# work_mem = 4MB

# Redis optimization
# Edit redis.conf:
# maxmemory 512mb
# maxmemory-policy allkeys-lru
```

#### 3. GPU Acceleration (Optional)
```yaml
# For Ollama GPU support
# Ensure NVIDIA Docker runtime is installed
# Uncomment GPU configuration in docker-compose.prod.yml
```

### 🔍 Troubleshooting

#### Common Issues

1. **Frontend not loading**
   ```bash
   # Check frontend container
   docker-compose -f docker-compose.prod.yml logs frontend
   
   # Verify nginx configuration
   docker-compose -f docker-compose.prod.yml exec nginx nginx -t
   ```

2. **Backend API errors**
   ```bash
   # Check backend logs
   docker-compose -f docker-compose.prod.yml logs backend
   
   # Verify database connection
   docker-compose -f docker-compose.prod.yml exec backend python -c "from app.database import engine; print(engine.url)"
   ```

3. **LLM not responding**
   ```bash
   # Check Ollama status
   docker-compose -f docker-compose.prod.yml exec ollama ollama list
   
   # Pull models if missing
   docker-compose -f docker-compose.prod.yml exec ollama ollama pull mistral:instruct
   ```

4. **Vector search not working**
   ```bash
   # Check Qdrant status
   curl http://localhost:6333/health
   
   # Verify collections
   curl http://localhost:6333/collections
   ```

#### Health Checks
```bash
# Check all services health
docker-compose -f docker-compose.prod.yml ps

# API health check
curl http://localhost/api/health

# Frontend health check
curl http://localhost/health
```

### 📝 Maintenance

#### 1. Updates
```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Restart services
docker-compose -f docker-compose.prod.yml up -d
```

#### 2. Log Management
```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100

# Log rotation (add to crontab)
0 2 * * * docker system prune -f
```

#### 3. Database Maintenance
```bash
# Vacuum database
docker-compose -f docker-compose.prod.yml exec postgres psql -U ai_user -d ai_assistant -c "VACUUM ANALYZE;"
```

### 🌍 Cloud Deployment

#### AWS Deployment
```bash
# Use AWS ECS or EKS
# Configure RDS for PostgreSQL
# Use ElastiCache for Redis
# Configure ALB for load balancing
```

#### Google Cloud Deployment
```bash
# Use Google Cloud Run or GKE
# Configure Cloud SQL for PostgreSQL
# Use Memorystore for Redis
# Configure Cloud Load Balancing
```

#### Azure Deployment
```bash
# Use Azure Container Instances or AKS
# Configure Azure Database for PostgreSQL
# Use Azure Cache for Redis
# Configure Azure Load Balancer
```

### 📞 Support

For deployment issues:
1. Check logs: `docker-compose -f docker-compose.prod.yml logs`
2. Verify configuration: Review `.env` file
3. Test connectivity: Use health check endpoints
4. Monitor resources: Check CPU/Memory usage

---

**Deployment Status**: ✅ Production Ready  
**Last Updated**: June 16, 2025  
**Version**: 1.0.0 