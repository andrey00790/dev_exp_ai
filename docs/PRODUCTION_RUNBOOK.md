# 🏭 AI Assistant - Production Runbook

**Версия:** 2.0  
**Дата:** Январь 2025  
**Статус:** Актуальный  
**Уровень:** Production Ready

---

## 🎯 Обзор

Производственное руководство для развертывания AI Assistant в enterprise-окружении с высокой доступностью, масштабируемостью и безопасностью.

**Поддерживаемые платформы:**
- ☁️ **Kubernetes** (рекомендуется)
- 🐳 **Docker Swarm**
- 🏗️ **AWS ECS/Fargate**
- 🔧 **Bare Metal + Docker**

**Системные требования:**
- 🖥️ **CPU:** 8+ cores per node
- 🧠 **RAM:** 32GB+ per node  
- 💾 **Storage:** 200GB+ SSD
- 🌐 **Network:** 1Gbps+
- 🔐 **Security:** TLS 1.3, RBAC, Secrets Management

---

## 🚀 Быстрый Production Deploy

### Kubernetes (рекомендуется)

```bash
# 1. Подготовка cluster
kubectl create namespace ai-assistant-prod

# 2. Установка Helm chart
helm install ai-assistant-prod deployment/helm/ai-assistant/ \
  --namespace ai-assistant-prod \
  --values values-production.yaml \
  --wait --timeout=10m

# 3. Проверка развертывания
kubectl get pods -n ai-assistant-prod
kubectl get ingress -n ai-assistant-prod
```

### Docker Compose Production

```bash
# 1. Установка production конфигурации
cp docker-compose.prod.yml docker-compose.yml
cp .env.production .env

# 2. Запуск с SSL и мониторингом
docker-compose up -d

# 3. Проверка состояния
docker-compose ps
curl -k https://your-domain.com/health
```

---

## 🏗️ Архитектура Production

### High-Level Architecture

```
Internet
    ↓
[Load Balancer (ALB/NLB)]
    ↓
[WAF + CloudFlare]
    ↓
[Kubernetes Ingress (Nginx)]
    ↓
┌─────────────────────────────────┐
│         AI Assistant            │
│                                 │
│  ┌─────────┐  ┌─────────────┐  │
│  │Frontend │  │   Backend   │  │
│  │ (React) │  │  (FastAPI)  │  │
│  │ 3 pods  │  │   5 pods    │  │
│  └─────────┘  └─────────────┘  │
│                                 │
│  ┌─────────┐  ┌─────────────┐  │
│  │ Vector  │  │    Cache    │  │
│  │ (Qdrant)│  │   (Redis)   │  │
│  │ 3 pods  │  │  3 pods     │  │
│  └─────────┘  └─────────────┘  │
└─────────────────────────────────┘
    ↓
[External Services]
┌─────────────────────────────────┐
│ PostgreSQL (RDS)                │
│ Prometheus + Grafana            │
│ External APIs (OpenAI, etc.)    │
└─────────────────────────────────┘
```

### Сетевая архитектура

```
┌─────────────────────────────────┐
│         Public Subnet           │
│                                 │
│  ┌─────────────────────────────┐│
│  │    Load Balancer            ││
│  │    (ALB + NLB)              ││
│  └─────────────────────────────┘│
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│        Private Subnet           │
│                                 │
│  ┌─────────────────────────────┐│
│  │    Kubernetes Cluster       ││
│  │    (AI Assistant)           ││
│  └─────────────────────────────┘│
└─────────────────────────────────┘
              ↓  
┌─────────────────────────────────┐
│         Data Subnet             │
│                                 │
│  ┌─────────────────────────────┐│
│  │    Managed Databases        ││
│  │    (RDS, ElastiCache)       ││
│  └─────────────────────────────┘│
└─────────────────────────────────┘
```

---

## ⚙️ Конфигурация Terraform

### Основная инфраструктура

```bash
# terraform/main.tf
cd terraform/

# Инициализация
terraform init \
  -backend-config="bucket=your-terraform-state-bucket" \
  -backend-config="key=ai-assistant/prod/terraform.tfstate" \
  -backend-config="region=us-east-1"

# Планирование
terraform plan \
  -var="environment=production" \
  -var="domain_name=ai-assistant.your-company.com" \
  -var="certificate_arn=arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012" \
  -out=prod.tfplan

# Применение
terraform apply prod.tfplan
```

### Переменные окружения

```bash
# terraform/terraform.tfvars
environment = "production"
aws_region = "us-east-1"

# Networking
vpc_cidr = "10.0.0.0/16"
private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
public_subnets = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

# EKS Configuration
cluster_name = "ai-assistant-prod"
cluster_version = "1.28"
node_groups = {
  main = {
    instance_types = ["m5.2xlarge"]
    scaling_config = {
      desired_size = 6
      max_size = 20
      min_size = 3
    }
  }
}

# RDS Configuration
db_instance_class = "db.r5.2xlarge"
db_allocated_storage = 500
db_backup_retention_period = 7
db_multi_az = true

# ElastiCache
redis_node_type = "cache.r5.2xlarge"
redis_num_cache_nodes = 3

# Security
enable_waf = true
enable_cloudtrail = true
enable_config = true
```

---

## 🔧 Helm Configuration

### Production Values

```yaml
# values-production.yaml
global:
  imageRegistry: "your-registry.com"
  imagePullSecrets:
    - name: registry-secret
  storageClass: "gp3-encrypted"

# Application
app:
  name: ai-assistant
  namespace: ai-assistant-prod
  
  image:
    repository: ai-assistant-backend
    tag: "v2.0.0"
    pullPolicy: Always
  
  replicaCount: 5
  
  resources:
    limits:
      cpu: 2000m
      memory: 4Gi
    requests:
      cpu: 1000m
      memory: 2Gi
  
  env:
    ENVIRONMENT: production
    LOG_LEVEL: INFO
    DATABASE_URL: postgresql://ai_user:${DB_PASSWORD}@ai-assistant-prod-db:5432/ai_assistant_prod
    REDIS_URL: redis://ai-assistant-prod-redis:6379/0
    QDRANT_URL: http://ai-assistant-prod-qdrant:6333
    
  secrets:
    - name: ai-assistant-secrets
      keys:
        - openai-api-key
        - anthropic-api-key
        - jwt-secret
        - database-password

# Frontend
frontend:
  enabled: true
  replicaCount: 3
  
  image:
    repository: ai-assistant-frontend
    tag: "v2.0.0"
  
  resources:
    limits:
      cpu: 500m
      memory: 1Gi
    requests:
      cpu: 250m
      memory: 512Mi

# Ingress
ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/rate-limit-rpm: "100"
    
  hosts:
    - host: ai-assistant.your-company.com
      paths:
        - path: /
          pathType: Prefix
          service: frontend
        - path: /api
          pathType: Prefix
          service: app
          
  tls:
    - secretName: ai-assistant-tls
      hosts:
        - ai-assistant.your-company.com

# Autoscaling
autoscaling:
  enabled: true
  minReplicas: 5
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

# Monitoring
monitoring:
  enabled: true
  prometheus:
    enabled: true
    retention: "30d"
  grafana:
    enabled: true
    persistence:
      enabled: true
      size: 10Gi
      
# Security
security:
  podSecurityPolicy:
    enabled: true
  networkPolicy:
    enabled: true
  rbac:
    create: true
    
# Backup
backup:
  enabled: true
  schedule: "0 2 * * *"
  retention: "30d"
```

---

## 🔐 Secrets Management

### Kubernetes Secrets

```bash
# Создание основных секретов
kubectl create secret generic ai-assistant-secrets \
  --from-literal=openai-api-key="${OPENAI_API_KEY}" \
  --from-literal=anthropic-api-key="${ANTHROPIC_API_KEY}" \
  --from-literal=jwt-secret="${JWT_SECRET}" \
  --from-literal=database-password="${DB_PASSWORD}" \
  --namespace ai-assistant-prod

# Database secret
kubectl create secret generic ai-assistant-db-secret \
  --from-literal=username="ai_user" \
  --from-literal=password="${DB_PASSWORD}" \
  --namespace ai-assistant-prod

# Registry secret
kubectl create secret docker-registry registry-secret \
  --docker-server=your-registry.com \
  --docker-username=your-username \
  --docker-password=your-password \
  --namespace ai-assistant-prod
```

### AWS Secrets Manager Integration

```yaml
# secrets-store-csi.yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: ai-assistant-secrets
  namespace: ai-assistant-prod
spec:
  provider: aws
  parameters:
    objects: |
      - objectName: "ai-assistant/prod/openai-api-key"
        objectType: "secretsmanager"
        jmesPath:
          - path: "api_key"
            objectAlias: "openai-api-key"
      - objectName: "ai-assistant/prod/database"
        objectType: "secretsmanager"
        jmesPath:
          - path: "password"
            objectAlias: "database-password"
```

---

## 📊 Monitoring & Observability

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'ai-assistant-backend'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: ai-assistant
      - source_labels: [__meta_kubernetes_pod_container_port_name]
        action: keep
        regex: metrics
```

### Grafana Dashboards

```json
# dashboards/ai-assistant-overview.json
{
  "dashboard": {
    "title": "AI Assistant Production Overview",
    "panels": [
      {
        "title": "API Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph", 
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
            "legendFormat": "Error Rate %"
          }
        ]
      }
    ]
  }
}
```

### Alerting Rules

```yaml
# monitoring/rules/ai-assistant.yml
groups:
  - name: ai-assistant
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"
          
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"
          
      - alert: PodCrashLooping
        expr: increase(kube_pod_container_status_restarts_total[1h]) > 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pod is crash looping"
          description: "Pod {{ $labels.pod }} in namespace {{ $labels.namespace }} is crash looping"
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Production Deploy

```yaml
# .github/workflows/production-deploy.yml
name: Production Deployment

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  AWS_REGION: us-east-1
  EKS_CLUSTER_NAME: ai-assistant-prod

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run security scan
        run: |
          docker run --rm -v $(pwd):/workspace \
            securecodewarrior/docker-security-scan:latest \
            scan /workspace
            
  build-and-push:
    needs: security-scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
          
      - name: Login to ECR
        run: |
          aws ecr get-login-password --region $AWS_REGION | \
            docker login --username AWS --password-stdin ${{ secrets.ECR_REGISTRY }}
          
      - name: Build and push images
        run: |
          # Backend
          docker build -t $ECR_REGISTRY/ai-assistant-backend:$GITHUB_SHA .
          docker push $ECR_REGISTRY/ai-assistant-backend:$GITHUB_SHA
          
          # Frontend
          docker build -t $ECR_REGISTRY/ai-assistant-frontend:$GITHUB_SHA frontend/
          docker push $ECR_REGISTRY/ai-assistant-frontend:$GITHUB_SHA
          
  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure kubectl
        run: |
          aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER_NAME
          
      - name: Deploy with Helm
        run: |
          helm upgrade --install ai-assistant-prod deployment/helm/ai-assistant/ \
            --namespace ai-assistant-prod \
            --values values-production.yaml \
            --set app.image.tag=$GITHUB_SHA \
            --set frontend.image.tag=$GITHUB_SHA \
            --wait --timeout=15m
            
      - name: Run smoke tests
        run: |
          kubectl wait --for=condition=ready pod -l app=ai-assistant -n ai-assistant-prod --timeout=300s
          curl -f https://ai-assistant.your-company.com/health
```

---

## 💾 Backup & Recovery

### Database Backup

```bash
# Automated backup script
#!/bin/bash
# backup-db.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgresql"
DB_NAME="ai_assistant_prod"

# Create backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
  -f "$BACKUP_DIR/ai_assistant_backup_$TIMESTAMP.sql"

# Compress backup
gzip "$BACKUP_DIR/ai_assistant_backup_$TIMESTAMP.sql"

# Upload to S3
aws s3 cp "$BACKUP_DIR/ai_assistant_backup_$TIMESTAMP.sql.gz" \
  s3://your-backup-bucket/postgresql/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

### Vector Database Backup

```bash
# Qdrant backup script
#!/bin/bash
# backup-qdrant.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
QDRANT_URL="http://qdrant:6333"
BACKUP_DIR="/backups/qdrant"

# Create snapshot
curl -X POST "$QDRANT_URL/collections/ai_documents/snapshots"

# Download snapshot
SNAPSHOT_NAME=$(curl -s "$QDRANT_URL/collections/ai_documents/snapshots" | jq -r '.result[-1].name')
curl -o "$BACKUP_DIR/qdrant_backup_$TIMESTAMP.snapshot" \
  "$QDRANT_URL/collections/ai_documents/snapshots/$SNAPSHOT_NAME"

# Upload to S3
aws s3 cp "$BACKUP_DIR/qdrant_backup_$TIMESTAMP.snapshot" \
  s3://your-backup-bucket/qdrant/
```

### Recovery Procedures

```bash
# Database recovery
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < backup_file.sql

# Vector database recovery
curl -X PUT "$QDRANT_URL/collections/ai_documents/snapshots/upload" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @backup_file.snapshot
```

---

## 🔍 Health Checks & SLA

### Health Check Endpoints

```bash
# API Health
curl https://ai-assistant.your-company.com/health

# Expected response:
{
  "status": "healthy",
  "version": "2.0.0",
  "environment": "production",
  "uptime": 86400,
  "checks": {
    "database": "healthy",
    "redis": "healthy", 
    "qdrant": "healthy",
    "external_apis": "healthy"
  }
}

# Detailed health check
curl https://ai-assistant.your-company.com/health/detailed

# Readiness probe
curl https://ai-assistant.your-company.com/health/ready

# Liveness probe
curl https://ai-assistant.your-company.com/health/live
```

### SLA Targets

| Метрика | Target | Measurement |
|---------|--------|-------------|
| **Uptime** | 99.9% | Monthly |
| **API Response Time** | <200ms | 95th percentile |
| **Search Response Time** | <2s | 95th percentile |
| **Error Rate** | <0.1% | 5-minute windows |
| **Recovery Time** | <15min | RTO |
| **Data Loss** | <1min | RPO |

---

## 🛡️ Security Hardening

### Network Security

```bash
# Security groups / Network policies
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-assistant-network-policy
  namespace: ai-assistant-prod
spec:
  podSelector:
    matchLabels:
      app: ai-assistant
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
EOF
```

### RBAC Configuration

```yaml
# rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ai-assistant
  namespace: ai-assistant-prod
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ai-assistant-role
  namespace: ai-assistant-prod
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ai-assistant-binding
  namespace: ai-assistant-prod
subjects:
- kind: ServiceAccount
  name: ai-assistant
  namespace: ai-assistant-prod
roleRef:
  kind: Role
  name: ai-assistant-role
  apiGroup: rbac.authorization.k8s.io
```

### Security Scanning

```bash
# Container scanning
trivy image your-registry.com/ai-assistant-backend:latest

# Kubernetes security scan
kube-bench run --targets master,node,etcd,policies

# Network security scan
kube-hunter --remote your-k8s-api-server
```

---

## 🔧 Scaling Strategy

### Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-assistant-hpa
  namespace: ai-assistant-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-assistant
  minReplicas: 5
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

### Cluster Autoscaler

```yaml
# cluster-autoscaler.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
spec:
  template:
    spec:
      containers:
      - image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.21.0
        name: cluster-autoscaler
        command:
        - ./cluster-autoscaler
        - --v=4
        - --stderrthreshold=info
        - --cloud-provider=aws
        - --skip-nodes-with-local-storage=false
        - --expander=least-waste
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/ai-assistant-prod
        - --balance-similar-node-groups
        - --skip-nodes-with-system-pods=false
```

---

## 🚨 Incident Response

### Runbook for Common Issues

#### Issue 1: High Error Rate
```bash
# 1. Check error logs
kubectl logs -l app=ai-assistant -n ai-assistant-prod --tail=100

# 2. Check system metrics
curl https://ai-assistant.your-company.com/metrics

# 3. Scale up if needed
kubectl scale deployment ai-assistant --replicas=10 -n ai-assistant-prod

# 4. Check external dependencies
curl https://api.openai.com/v1/models
```

#### Issue 2: Database Connection Issues
```bash
# 1. Check database connectivity
kubectl exec -it deployment/ai-assistant -n ai-assistant-prod -- \
  pg_isready -h $DB_HOST -p 5432

# 2. Check connection pool
kubectl exec -it deployment/ai-assistant -n ai-assistant-prod -- \
  python -c "
import psycopg2
conn = psycopg2.connect('$DATABASE_URL')
print('Connection successful')
"

# 3. Restart pods if needed
kubectl rollout restart deployment/ai-assistant -n ai-assistant-prod
```

#### Issue 3: Memory Leaks
```bash
# 1. Check memory usage
kubectl top pods -l app=ai-assistant -n ai-assistant-prod

# 2. Get memory profile
kubectl exec -it deployment/ai-assistant -n ai-assistant-prod -- \
  python -m memory_profiler your_script.py

# 3. Restart high-memory pods
kubectl delete pod -l app=ai-assistant -n ai-assistant-prod --field-selector=status.phase=Running
```

### Escalation Matrix

| Severity | Response Time | Escalation |
|----------|---------------|------------|
| **Critical** | 15 minutes | DevOps → SRE → Engineering Manager |
| **High** | 1 hour | DevOps → SRE |
| **Medium** | 4 hours | DevOps |
| **Low** | 1 business day | DevOps |

---

## 📋 Maintenance Procedures

### Regular Maintenance Tasks

```bash
# Daily
- Check system health dashboards
- Review error logs
- Monitor resource usage
- Verify backup completion

# Weekly  
- Update security patches
- Review performance metrics
- Check certificate expiration
- Clean up old logs

# Monthly
- Review capacity planning
- Update dependencies
- Security vulnerability scan
- Disaster recovery testing

# Quarterly
- Full system audit
- Performance optimization
- Backup/restore testing
- Security compliance review
```

### Upgrade Procedures

```bash
# 1. Backup current state
helm get values ai-assistant-prod > backup-values.yaml
kubectl get all -n ai-assistant-prod -o yaml > backup-state.yaml

# 2. Update to new version
helm upgrade ai-assistant-prod deployment/helm/ai-assistant/ \
  --namespace ai-assistant-prod \
  --values values-production.yaml \
  --set app.image.tag=v2.1.0 \
  --wait --timeout=15m

# 3. Verify upgrade
kubectl get pods -n ai-assistant-prod
curl https://ai-assistant.your-company.com/health

# 4. Rollback if needed
helm rollback ai-assistant-prod 1 -n ai-assistant-prod
```

---

## 📞 Support Contacts

### On-Call Rotation

| Role | Primary | Secondary |
|------|---------|-----------|
| **DevOps** | team-devops@company.com | devops-oncall@company.com |
| **SRE** | team-sre@company.com | sre-oncall@company.com |
| **Engineering** | team-engineering@company.com | eng-lead@company.com |

### Emergency Procedures

```bash
# Emergency shutdown
kubectl delete deployment ai-assistant -n ai-assistant-prod

# Emergency scale down
kubectl scale deployment ai-assistant --replicas=0 -n ai-assistant-prod

# Emergency maintenance page
kubectl apply -f emergency-maintenance.yaml
```

---

**Production Readiness Checklist:**
- [ ] Infrastructure deployed via Terraform
- [ ] Kubernetes cluster configured
- [ ] SSL certificates installed
- [ ] Monitoring and alerting configured
- [ ] Backup procedures tested
- [ ] Security hardening applied
- [ ] Load testing completed
- [ ] Incident response procedures documented
- [ ] On-call rotation established
- [ ] Runbooks created and tested 