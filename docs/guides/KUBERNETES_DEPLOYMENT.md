# ⚓ Kubernetes деплой с Helm

Руководство по развертыванию AI Assistant MVP в Kubernetes кластере с использованием Helm charts.

## 📋 Предварительные требования

### Обязательные компоненты
- **Kubernetes** >= 1.24
- **Helm** >= 3.8
- **kubectl** настроенный для вашего кластера
- **Docker** для сборки образов

### Рекомендуемые компоненты
- **Ingress Controller** (nginx, traefik)
- **Cert-Manager** для SSL сертификатов
- **Prometheus/Grafana** для мониторинга
- **Persistent Volume** provider

### Ресурсы кластера
- **Nodes**: минимум 3 worker nodes
- **CPU**: минимум 8 cores total
- **RAM**: минимум 16GB total
- **Storage**: минимум 100GB persistent storage

## 🚀 Быстрый деплой

### 1. Подготовка образов
```bash
# Сборка и пуш образов в registry
docker build -t your-registry/ai-assistant:latest .
docker build -t your-registry/ai-assistant-frontend:latest ./frontend

docker push your-registry/ai-assistant:latest
docker push your-registry/ai-assistant-frontend:latest
```

### 2. Установка зависимостей Helm
```bash
# Добавить Bitnami репозиторий
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### 3. Создание namespace
```bash
kubectl create namespace ai-assistant
```

### 4. Установка через Helm
```bash
# Установка с настройками по умолчанию
helm install ai-assistant deployment/helm/ai-assistant \
  --namespace ai-assistant \
  --set app.image.repository=your-registry/ai-assistant \
  --set frontend.image.repository=your-registry/ai-assistant-frontend
```

### 5. Проверка статуса
```bash
# Статус Helm релиза
helm status ai-assistant --namespace ai-assistant

# Статус подов
kubectl get pods -n ai-assistant

# Логи
kubectl logs -f deployment/ai-assistant -n ai-assistant
```

## ⚙️ Конфигурация

### Основные параметры values.yaml

```yaml
# Образы приложения
app:
  image:
    repository: your-registry/ai-assistant
    tag: "v1.0.0"
  replicaCount: 3

frontend:
  image:
    repository: your-registry/ai-assistant-frontend
    tag: "v1.0.0"
  replicaCount: 2

# Ingress настройки
ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: ai-assistant.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
          service: frontend
        - path: /api
          pathType: Prefix
          service: app

# База данных
postgresql:
  enabled: true
  auth:
    database: "ai_assistant"
    username: "ai_user"
    password: "secure-password"
  primary:
    persistence:
      size: 50Gi

# Ресурсы
app:
  resources:
    limits:
      cpu: 2000m
      memory: 4Gi
    requests:
      cpu: 1000m
      memory: 2Gi
```

### Создание кастомного values файла
```bash
# Создать values-production.yaml
cat > values-production.yaml << EOF
global:
  imageRegistry: "your-registry.com"

app:
  replicaCount: 5
  image:
    tag: "v1.2.0"
  resources:
    limits:
      cpu: 2000m
      memory: 4Gi
    requests:
      cpu: 1000m
      memory: 2Gi

postgresql:
  auth:
    postgresPassword: "$(openssl rand -base64 32)"
    password: "$(openssl rand -base64 32)"
  primary:
    persistence:
      size: 100Gi
      storageClass: "fast-ssd"

ingress:
  hosts:
    - host: ai-assistant.production.com
  tls:
    - secretName: ai-assistant-tls
      hosts:
        - ai-assistant.production.com

monitoring:
  enabled: true
  prometheus:
    enabled: true
  grafana:
    enabled: true
EOF

# Установка с кастомными настройками
helm upgrade --install ai-assistant deployment/helm/ai-assistant \
  --namespace ai-assistant \
  --values values-production.yaml
```

## 🔐 Безопасность

### 1. Создание секретов
```bash
# Секреты базы данных
kubectl create secret generic ai-assistant-secrets \
  --from-literal=database-url="postgresql://user:password@host:5432/database" \
  --from-literal=redis-password="redis-secure-password" \
  --namespace ai-assistant

# API ключи
kubectl create secret generic ai-assistant-api-keys \
  --from-literal=openai-api-key="your-openai-key" \
  --from-literal=anthropic-api-key="your-anthropic-key" \
  --namespace ai-assistant
```

### 2. RBAC настройки
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
  resources: ["pods", "services", "configmaps"]
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

### 3. Network Policies
```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-assistant-netpol
  namespace: ai-assistant
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
    - podSelector:
        matchLabels:
          app: ai-assistant-postgresql
    ports:
    - protocol: TCP
      port: 5432
```

## 📊 Мониторинг

### 1. Prometheus ServiceMonitor
```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ai-assistant
  namespace: ai-assistant
spec:
  selector:
    matchLabels:
      app: ai-assistant
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

### 2. Grafana Dashboard
```bash
# Импорт готового dashboard
kubectl create configmap ai-assistant-dashboard \
  --from-file=monitoring/grafana/dashboards/ai-assistant-dashboard.json \
  --namespace monitoring
```

### 3. Алерты
```yaml
# alerts.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: ai-assistant-alerts
  namespace: ai-assistant
spec:
  groups:
  - name: ai-assistant
    rules:
    - alert: AIAssistantDown
      expr: up{job="ai-assistant"} == 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "AI Assistant is down"
    - alert: HighMemoryUsage
      expr: container_memory_usage_bytes{pod=~"ai-assistant-.*"} / container_spec_memory_limit_bytes > 0.9
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "High memory usage detected"
```

## 🔄 Автомасштабирование

### 1. Horizontal Pod Autoscaler
```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-assistant-hpa
  namespace: ai-assistant
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-assistant
  minReplicas: 3
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
```

### 2. Vertical Pod Autoscaler
```yaml
# vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: ai-assistant-vpa
  namespace: ai-assistant
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-assistant
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: ai-assistant
      maxAllowed:
        cpu: 4000m
        memory: 8Gi
      minAllowed:
        cpu: 500m
        memory: 1Gi
```

## 🔧 Операции и обслуживание

### Обновление приложения
```bash
# Обновление образа
helm upgrade ai-assistant deployment/helm/ai-assistant \
  --namespace ai-assistant \
  --set app.image.tag=v1.1.0 \
  --reuse-values

# Проверка статуса обновления
kubectl rollout status deployment/ai-assistant -n ai-assistant

# Откат в случае проблем
kubectl rollout undo deployment/ai-assistant -n ai-assistant
```

### Масштабирование
```bash
# Ручное масштабирование
kubectl scale deployment ai-assistant --replicas=5 -n ai-assistant

# Проверка статуса
kubectl get pods -n ai-assistant -l app=ai-assistant
```

### Бэкапы
```bash
# Бэкап базы данных
kubectl exec -n ai-assistant deployment/ai-assistant-postgresql -- \
  pg_dump -U ai_user ai_assistant > backup-$(date +%Y%m%d).sql

# Бэкап Helm values
helm get values ai-assistant -n ai-assistant > values-backup.yaml

# Бэкап конфигурации
kubectl get all,configmap,secret -n ai-assistant -o yaml > k8s-backup.yaml
```

### Логи и отладка
```bash
# Логи приложения
kubectl logs -f deployment/ai-assistant -n ai-assistant

# Логи всех подов
kubectl logs -f -l app=ai-assistant -n ai-assistant --max-log-requests=10

# Подключение к поду для отладки
kubectl exec -it deployment/ai-assistant -n ai-assistant -- /bin/bash

# Проверка событий
kubectl get events -n ai-assistant --sort-by='.lastTimestamp'
```

## 🌍 Мультикластерный деплой

### 1. ArgoCD GitOps
```yaml
# argocd-application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ai-assistant-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/ai-assistant
    targetRevision: main
    path: deployment/helm/ai-assistant
    helm:
      valueFiles:
      - values-production.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: ai-assistant
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### 2. Flux CD
```yaml
# helmrelease.yaml
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: ai-assistant
  namespace: ai-assistant
spec:
  interval: 10m
  chart:
    spec:
      chart: ./deployment/helm/ai-assistant
      sourceRef:
        kind: GitRepository
        name: ai-assistant-repo
  values:
    app:
      image:
        tag: v1.0.0
    ingress:
      hosts:
        - host: ai-assistant.production.com
```

## 📋 Чеклист деплоя

### Перед деплоем
- [ ] Образы собраны и загружены в registry
- [ ] Секреты созданы в кластере
- [ ] Persistent Volumes настроены
- [ ] Ingress Controller установлен
- [ ] Мониторинг настроен
- [ ] Бэкап стратегия определена

### После деплоя
- [ ] Все поды в статусе Running
- [ ] Health checks проходят
- [ ] Ingress доступен
- [ ] База данных подключена
- [ ] Метрики собираются
- [ ] Логи пишутся корректно
- [ ] Автомасштабирование работает

### Тестирование
- [ ] API endpoints отвечают
- [ ] Frontend загружается
- [ ] Аутентификация работает
- [ ] Поиск функционирует
- [ ] Генерация RFC работает
- [ ] Performance тесты пройдены

## 🆘 Устранение неполадок

### Частые проблемы

#### 1. Поды не запускаются
```bash
# Проверить события
kubectl describe pod <pod-name> -n ai-assistant

# Проверить ресурсы
kubectl top pods -n ai-assistant

# Проверить лимиты
kubectl describe nodes
```

#### 2. Проблемы с сетью
```bash
# Проверить сервисы
kubectl get svc -n ai-assistant

# Проверить endpoints
kubectl get endpoints -n ai-assistant

# Тест сетевой связности
kubectl run test-pod --rm -i --tty --image=busybox -- /bin/sh
nslookup ai-assistant.ai-assistant.svc.cluster.local
```

#### 3. Проблемы с хранилищем
```bash
# Проверить PVC
kubectl get pvc -n ai-assistant

# Проверить PV
kubectl get pv

# Проверить StorageClass
kubectl get storageclass
```

#### 4. Проблемы с Helm
```bash
# Статус релиза
helm status ai-assistant -n ai-assistant

# История релизов
helm history ai-assistant -n ai-assistant

# Откат к предыдущей версии
helm rollback ai-assistant 1 -n ai-assistant
```

---

**💡 Совет**: Используйте staging окружение для тестирования изменений перед деплоем в production. 