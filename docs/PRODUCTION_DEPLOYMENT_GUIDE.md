# AI Assistant - Production Deployment Guide

Complete guide for deploying AI Assistant platform to production using Kubernetes and Helm.

## 🎯 Overview

This guide covers production deployment of AI Assistant on Kubernetes using Helm charts. The deployment includes:

- **High Availability** - Multi-replica services
- **Scalability** - Auto-scaling based on load
- **Security** - Network policies, RBAC, TLS
- **Monitoring** - Prometheus + Grafana
- **Data Persistence** - Persistent volumes
- **Load Balancing** - Ingress controllers

---

## 🔧 Prerequisites

### Infrastructure Requirements

- **Kubernetes Cluster** - v1.24+
- **Helm** - v3.8+
- **kubectl** - Configured for your cluster
- **Ingress Controller** - nginx, traefik, or similar
- **Cert Manager** - For TLS certificates (optional)
- **Storage Class** - For persistent volumes

### Minimum Resources

- **CPU**: 4 cores
- **Memory**: 8GB RAM
- **Storage**: 100GB
- **Nodes**: 3+ (for HA)

### External Dependencies

- **PostgreSQL** - Can use external or in-cluster
- **Redis** - Can use external or in-cluster
- **Container Registry** - For custom images
- **DNS** - For ingress domains

---

## 🚀 Quick Deployment

### 1. Prepare Environment

```bash
# Create namespace
kubectl create namespace ai-assistant

# Add any required secrets
kubectl create secret generic ai-secrets \
  --from-literal=openai-api-key="sk-your-key" \
  --from-literal=anthropic-api-key="sk-ant-your-key" \
  -n ai-assistant
```

### 2. Configure Values

```bash
# Copy and edit values file
cp deployment/helm/ai-assistant/values.yaml values-prod.yaml

# Edit for your environment
vim values-prod.yaml
```

### 3. Deploy with Helm

```bash
# Install AI Assistant
make helm-install

# Or manually:
helm install ai-assistant deployment/helm/ai-assistant/ \
  --namespace ai-assistant \
  --create-namespace \
  --values values-prod.yaml \
  --wait
```

### 4. Verify Deployment

```bash
# Check status
make helm-status

# Check pods
kubectl get pods -n ai-assistant

# Check services
kubectl get svc -n ai-assistant
```

---

## 📋 Configuration

### Production Values

Edit `values-prod.yaml` for your environment:

```yaml
# values-prod.yaml
global:
  imageRegistry: "your-registry.com"
  imagePullSecrets: 
    - name: registry-secret

app:
  name: ai-assistant
  namespace: ai-assistant
  
  image:
    repository: your-registry.com/ai-assistant
    tag: "v1.0.0"
    pullPolicy: IfNotPresent
  
  replicaCount: 3
  
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

# Database configuration
postgresql:
  enabled: true
  auth:
    postgresPassword: "your-secure-password"
    username: "ai_assistant_user"
    password: "your-secure-password"
    database: "ai_assistant_prod"
  
  primary:
    persistence:
      enabled: true
      size: 100Gi
      storageClass: "fast-ssd"
  
  resources:
    limits:
      cpu: 2000m
      memory: 2Gi
    requests:
      cpu: 1000m
      memory: 1Gi

# Redis configuration
redis:
  enabled: true
  auth:
    enabled: true
    password: "redis-secure-password"
  
  master:
    persistence:
      enabled: true
      size: 20Gi
      storageClass: "fast-ssd"
  
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 500m
      memory: 512Mi

# Qdrant vector database
qdrant:
  enabled: true
  
  persistence:
    enabled: true
    size: 200Gi
    storageClass: "fast-ssd"
  
  resources:
    limits:
      cpu: 4000m
      memory: 8Gi
    requests:
      cpu: 2000m
      memory: 4Gi

# Ingress configuration
ingress:
  enabled: true
  className: "nginx"
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
  
  hosts:
    - host: api.ai-assistant.company.com
      paths:
        - path: /
          pathType: Prefix
          service: app
    - host: app.ai-assistant.company.com
      paths:
        - path: /
          pathType: Prefix
          service: frontend
  
  tls:
    - secretName: ai-assistant-tls
      hosts:
        - api.ai-assistant.company.com
        - app.ai-assistant.company.com

# Autoscaling
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

# Monitoring
monitoring:
  enabled: true
  
  prometheus:
    enabled: true
    serviceMonitor:
      enabled: true
      
  grafana:
    enabled: true
    adminPassword: "secure-grafana-password"

# Security
security:
  podSecurityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
  
  securityContext:
    allowPrivilegeEscalation: false
    readOnlyRootFilesystem: true
    capabilities:
      drop:
        - ALL

# Network policies
networkPolicy:
  enabled: true
```

---

## 🔐 Security Configuration

### TLS/SSL Setup

```bash
# Install cert-manager (if not already installed)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml

# Create cluster issuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@company.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Secrets Management

```bash
# Create secrets for API keys
kubectl create secret generic ai-api-keys \
  --from-literal=openai-api-key="sk-your-openai-key" \
  --from-literal=anthropic-api-key="sk-ant-your-anthropic-key" \
  --from-literal=jwt-secret="your-jwt-secret-key" \
  -n ai-assistant

# Create database secrets
kubectl create secret generic ai-db-secrets \
  --from-literal=postgres-password="your-secure-db-password" \
  --from-literal=redis-password="your-secure-redis-password" \
  -n ai-assistant

# Container registry secret (if using private registry)
kubectl create secret docker-registry registry-secret \
  --docker-server=your-registry.com \
  --docker-username=your-username \
  --docker-password=your-password \
  --docker-email=your-email@company.com \
  -n ai-assistant
```

### RBAC Configuration

```yaml
# rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ai-assistant
  namespace: ai-assistant
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: ai-assistant
  name: ai-assistant-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ai-assistant-rolebinding
  namespace: ai-assistant
subjects:
- kind: ServiceAccount
  name: ai-assistant
  namespace: ai-assistant
roleRef:
  kind: Role
  name: ai-assistant-role
  apiGroup: rbac.authorization.k8s.io
```

```bash
# Apply RBAC
kubectl apply -f rbac.yaml
```

---

## 📊 Monitoring & Observability

### Prometheus Configuration

```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: ai-assistant
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
      - "alert_rules.yml"
    
    scrape_configs:
      - job_name: 'ai-assistant'
        kubernetes_sd_configs:
          - role: pod
            namespaces:
              names:
                - ai-assistant
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            action: keep
            regex: true
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
            action: replace
            target_label: __metrics_path__
            regex: (.+)
```

### Grafana Dashboards

```bash
# Import AI Assistant dashboard
kubectl create configmap ai-assistant-dashboard \
  --from-file=dashboard.json=monitoring/grafana/dashboards/ai-assistant.json \
  -n ai-assistant
```

### Alerting Rules

```yaml
# alert-rules.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alert-rules
  namespace: ai-assistant
data:
  alert_rules.yml: |
    groups:
    - name: ai-assistant-alerts
      rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
          description: "Error rate is {{ $value }} requests per second"
      
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High response time
          description: "95th percentile response time is {{ $value }} seconds"
      
      - alert: DatabaseConnectionHigh
        expr: database_connections_active / database_connections_max > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: Database connection pool nearly exhausted
```

---

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure kubectl
      uses: azure/setup-kubectl@v3
      with:
        version: 'latest'
    
    - name: Set up Helm
      uses: azure/setup-helm@v3
      with:
        version: '3.12.0'
    
    - name: Login to registry
      run: |
        echo ${{ secrets.REGISTRY_PASSWORD }} | docker login ${{ secrets.REGISTRY_URL }} -u ${{ secrets.REGISTRY_USERNAME }} --password-stdin
    
    - name: Build and push image
      run: |
        docker build -t ${{ secrets.REGISTRY_URL }}/ai-assistant:${{ github.ref_name }} .
        docker push ${{ secrets.REGISTRY_URL }}/ai-assistant:${{ github.ref_name }}
    
    - name: Deploy with Helm
      run: |
        helm upgrade --install ai-assistant deployment/helm/ai-assistant/ \
          --namespace ai-assistant \
          --create-namespace \
          --set app.image.tag=${{ github.ref_name }} \
          --set app.image.repository=${{ secrets.REGISTRY_URL }}/ai-assistant \
          --values values-prod.yaml \
          --wait
```

---

## 🔧 Operations & Maintenance

### Regular Operations

```bash
# Check deployment status
make helm-status

# View logs
make helm-logs

# Update deployment
make helm-upgrade

# Scale manually if needed
kubectl scale deployment ai-assistant --replicas=5 -n ai-assistant
```

### Backup Procedures

```bash
# Database backup
kubectl exec -it ai-assistant-postgresql-0 -n ai-assistant -- pg_dump -U ai_assistant_user ai_assistant_prod | gzip > backup-$(date +%Y%m%d).sql.gz

# Qdrant backup
kubectl exec -it ai-assistant-qdrant-0 -n ai-assistant -- tar czf - /qdrant/storage > qdrant-backup-$(date +%Y%m%d).tar.gz
```

### Rolling Updates

```bash
# Update image version
helm upgrade ai-assistant deployment/helm/ai-assistant/ \
  --namespace ai-assistant \
  --set app.image.tag=v1.1.0 \
  --values values-prod.yaml

# Monitor rollout
kubectl rollout status deployment/ai-assistant -n ai-assistant
```

---

## 🐛 Troubleshooting

### Common Issues

```bash
# Check pod status
kubectl get pods -n ai-assistant

# Describe problematic pod
kubectl describe pod <pod-name> -n ai-assistant

# Check logs
kubectl logs <pod-name> -n ai-assistant

# Check events
kubectl get events -n ai-assistant --sort-by='.lastTimestamp'
```

### Performance Issues

```bash
# Check resource usage
kubectl top pods -n ai-assistant
kubectl top nodes

# Check HPA status
kubectl get hpa -n ai-assistant

# Scale manually if needed
kubectl scale deployment ai-assistant --replicas=10 -n ai-assistant
```

### Network Issues

```bash
# Test service connectivity
kubectl exec -it <pod-name> -n ai-assistant -- curl http://ai-assistant-postgresql:5432

# Check ingress
kubectl get ingress -n ai-assistant
kubectl describe ingress ai-assistant -n ai-assistant
```

---

## 📈 Scaling & Performance

### Horizontal Scaling

Automatic scaling is configured via HPA:

```yaml
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

### Vertical Scaling

Update resource limits:

```yaml
resources:
  limits:
    cpu: 4000m
    memory: 8Gi
  requests:
    cpu: 2000m
    memory: 4Gi
```

### Database Scaling

For high-load scenarios, consider:
- Read replicas for PostgreSQL
- Redis Cluster mode
- External managed databases (RDS, Cloud SQL)

---

This guide provides the foundation for production deployment. Adapt the configuration based on your specific infrastructure and requirements. 