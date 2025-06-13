# 🚀 AI Assistant MVP - Roadmap следующих шагов

## 🎯 Текущее состояние (✅ Выполнено)

### ✅ **Базовая архитектура MVP**
- ✅ **Профессиональные RFC шаблоны** на основе GitHub/Stripe/ADR стандартов
- ✅ **Template Service** для заполнения шаблонов с LLM интеграцией
- ✅ **API endpoints** для генерации, поиска, обратной связи
- ✅ **Демонстрационные скрипты** и примеры генерации
- ✅ **Health monitoring** с детальной диагностикой
- ✅ **Полное покрытие тестами** (25/25 тестов проходят)

### ✅ **Multi-LLM Architecture (ВЫПОЛНЕНО!)**
- ✅ **Enhanced LLM Client** с поддержкой множественных провайдеров
- ✅ **Ollama Provider** - локальные модели (Mistral, Llama2, CodeLlama)
- ✅ **OpenAI Provider** - GPT-4, GPT-3.5-turbo с cost tracking
- ✅ **Anthropic Provider** - Claude 3 (Opus/Sonnet/Haiku)
- ✅ **Smart LLM Router** с 6 стратегиями маршрутизации
- ✅ **Автоматический fallback** между провайдерами
- ✅ **Cost optimization** и лимиты на запрос
- ✅ **Performance analytics** и recommendations

### ✅ **Learning Pipeline (ВЫПОЛНЕНО!)**
- ✅ **Feedback collection** и автоматическое переобучение
- ✅ **Quality scoring** с LLM-based evaluation
- ✅ **Learning examples** накопление и analysis
- ✅ **Auto-retraining triggers** при достижении 10+ примеров
- ✅ **Learning stats API** для мониторинга

### ✅ **Management & Monitoring APIs**
- ✅ **LLM Health checks** всех провайдеров
- ✅ **Usage statistics** с детальными метриками
- ✅ **Performance monitoring** и benchmarking
- ✅ **Dynamic routing strategy** переключение
- ✅ **Cost tracking** и optimization recommendations

### ✅ **Code Documentation Generation (НОВОЕ!)**
- ✅ **AI-powered code analysis** с поддержкой 13+ языков программирования
- ✅ **Multiple documentation types** (README, API docs, Technical specs, User guides)
- ✅ **AST-based analysis** для Python, Regex parsing для JS/Java/TypeScript
- ✅ **Architecture pattern detection** (FastAPI, Django, React, Spring Boot)
- ✅ **Security & performance analysis** кода
- ✅ **LLM integration** для профессионального контента
- ✅ **REST API endpoints** (`/api/v1/documentation/*`)
- ✅ **Comprehensive testing** (12 новых тестов, 47 total passing)

### ✅ **Developer Experience**
- ✅ **Wrapper script** `run_server.py` для удобного запуска
- ✅ **Environment-based configuration** через .env файлы
- ✅ **Comprehensive error handling** и logging
- ✅ **Backward compatibility** со старым API



## 🐳 **Infrastructure & Deployment Architecture (КРИТИЧНО!)**

### 🏠 **Local Development Stack**

**Цель:** Полная локализация системы с запуском одной командой

**Архитектура для Mac M3 Pro (32GB RAM, 512GB SSD):**
```yaml
# docker-compose.yml
version: '3.8'
services:
  # Core Application
  ai-assistant:
    image: ai-assistant:latest
    platform: linux/arm64  # Apple Silicon optimization
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/ai_assistant
      - QDRANT_URL=http://qdrant:6333
      - OLLAMA_URL=http://ollama:11434
    depends_on: [postgres, qdrant, ollama]
    
  # Vector Database
  qdrant:
    image: qdrant/qdrant:latest
    platform: linux/arm64
    volumes:
      - qdrant_data:/qdrant/storage
    ports: ["6333:6333"]
    
  # Metadata & Analytics Database  
  postgres:
    image: postgres:15-alpine
    platform: linux/arm64
    environment:
      POSTGRES_DB: ai_assistant
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    
  # Local LLM Server
  ollama:
    image: ollama/ollama:latest
    platform: linux/arm64
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    
  # Optional: Monitoring
  prometheus:
    image: prom/prometheus:latest
    platform: linux/arm64
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      
volumes:
  postgres_data:
  qdrant_data: 
  ollama_data:
```

**Одна команда для запуска:**
```bash
# Полный локальный стек
make local-up

# Или напрямую
docker-compose up -d --build
```

### ☸️ **Production Kubernetes Deployment**

**Цель:** Enterprise-grade deployment с автомасштабированием

**Helm Chart Architecture:**
```yaml
# helm/ai-assistant/values.yaml
global:
  domain: ai-assistant.company.com
  environment: production
  
# Application Deployment
app:
  replicaCount: 3
  image:
    repository: ai-assistant
    tag: "1.0.0"
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 20
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80
    
# Qdrant Vector Database
qdrant:
  enabled: true
  replicaCount: 3
  persistence:
    enabled: true
    size: 100Gi
    storageClass: ssd
  resources:
    requests:
      memory: 4Gi
      cpu: 1000m
    limits:
      memory: 8Gi
      cpu: 2000m
      
# PostgreSQL Database
postgresql:
  enabled: true
  architecture: replication
  primary:
    persistence:
      enabled: true
      size: 50Gi
  readReplicas:
    replicaCount: 2
    
# Ollama LLM Server (optional for hybrid deployment)
ollama:
  enabled: true
  replicaCount: 2
  resources:
    requests:
      memory: 8Gi
      cpu: 2000m
    limits:
      memory: 16Gi
      cpu: 4000m
```

**Одна команда для production deployment:**
```bash
# Production deployment
helm install ai-assistant ./helm/ai-assistant \
  --namespace ai-assistant \
  --create-namespace \
  --values ./helm/ai-assistant/values-production.yaml

# Or with make
make k8s-deploy ENV=production
```

### 🗄️ **Database Architecture**

**PostgreSQL Schema Design:**
```sql
-- Core metadata tables
CREATE SCHEMA ai_assistant;

-- User sessions and interactions
CREATE TABLE ai_assistant.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Generated RFCs with full history
CREATE TABLE ai_assistant.rfcs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES ai_assistant.sessions(id),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    template_used VARCHAR(100),
    llm_provider VARCHAR(50),
    generation_time_ms INTEGER,
    tokens_used INTEGER,
    cost_usd DECIMAL(10,6),
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Learning pipeline data
CREATE TABLE ai_assistant.learning_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfc_id UUID REFERENCES ai_assistant.rfcs(id),
    user_feedback INTEGER CHECK (user_feedback BETWEEN 1 AND 5),
    feedback_text TEXT,
    quality_score DECIMAL(3,2),
    improvement_areas TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- Search queries and results
CREATE TABLE ai_assistant.search_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES ai_assistant.sessions(id),
    query_text TEXT NOT NULL,
    query_vector_id VARCHAR(255), -- Qdrant point ID
    results_count INTEGER,
    response_time_ms INTEGER,
    relevance_scores DECIMAL(3,2)[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- Data sources metadata
CREATE TABLE ai_assistant.data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(50) NOT NULL, -- 'learning_materials', 'search_sources', 'user_content'
    source_name VARCHAR(255) NOT NULL,
    file_path TEXT,
    vector_ids TEXT[], -- Array of Qdrant point IDs
    processing_status VARCHAR(50) DEFAULT 'pending',
    quality_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- LLM provider performance metrics
CREATE TABLE ai_assistant.llm_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    request_type VARCHAR(50), -- 'generation', 'search', 'evaluation'
    response_time_ms INTEGER,
    tokens_input INTEGER,
    tokens_output INTEGER,
    cost_usd DECIMAL(10,6),
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_sessions_created_at ON ai_assistant.sessions(created_at);
CREATE INDEX idx_rfcs_session_id ON ai_assistant.rfcs(session_id);
CREATE INDEX idx_rfcs_created_at ON ai_assistant.rfcs(created_at);
CREATE INDEX idx_search_queries_session_id ON ai_assistant.search_queries(session_id);
CREATE INDEX idx_data_sources_type ON ai_assistant.data_sources(source_type);
CREATE INDEX idx_llm_metrics_provider ON ai_assistant.llm_metrics(provider, model);
```

**Qdrant Collections Architecture:**
```python
# Vector database collections
collections = {
    # Learning materials vectors
    "learning_materials": {
        "vectors": {
            "size": 1536,  # OpenAI embeddings
            "distance": "Cosine"
        },
        "payload_schema": {
            "source_id": "keyword",
            "source_type": "keyword", 
            "content_type": "keyword",  # book, course, video, etc.
            "category": "keyword",      # system_design, devops, etc.
            "chunk_index": "integer",
            "metadata": "json"
        }
    },
    
    # Corporate search sources
    "search_sources": {
        "vectors": {
            "size": 1536,
            "distance": "Cosine"
        },
        "payload_schema": {
            "source_id": "keyword",
            "source_type": "keyword",   # confluence, jira, gitlab
            "project": "keyword",
            "team": "keyword",
            "created_date": "datetime",
            "metadata": "json"
        }
    },
    
    # User uploaded content
    "user_content": {
        "vectors": {
            "size": 1536,
            "distance": "Cosine"
        },
        "payload_schema": {
            "source_id": "keyword",
            "user_id": "keyword",
            "content_type": "keyword",
            "privacy_level": "keyword",
            "metadata": "json"
        }
    }
}
```

## 🏗️ **Data Classification Architecture (ОБНОВЛЕНО!)**

### 📊 **Типы данных с инфраструктурной интеграцией:**

```yaml
data_sources:
  learning_materials:
    storage: 
      vectors: qdrant.learning_materials
      metadata: postgresql.data_sources
      files: /data/learning/
    sources: [dataset_config.yml, user_uploads]
    usage: [model_training, fine_tuning]
    
  search_sources:
    storage:
      vectors: qdrant.search_sources  
      metadata: postgresql.data_sources
      cache: redis.search_cache
    sources: [confluence, jira, gitlab, apis]
    usage: [semantic_search, context_retrieval]
    
  user_content:
    storage:
      vectors: qdrant.user_content
      metadata: postgresql.data_sources
      files: /data/user/
    sources: [uploads, internal_docs]
    usage: [hybrid_all_purposes]
```

## 🧪 **Testing & Validation System (КРИТИЧНО!)**

### 🔍 **1. Semantic Search Testing**

**Цель:** Валидация качества семантического поиска с enterprise-grade метриками

**Компоненты:**
```python
# testing/semantic_search/
├── test_data_generator.py      # Генерация тестовых данных
├── search_evaluator.py         # Метрики и валидация
├── knowledge_base_builder.py   # Создание тестовой базы знаний
├── benchmark_runner.py         # Автоматизированное тестирование
└── feedback_collector.py       # Сбор человеческих оценок
```

**Тестовая база знаний:**
- **GitLab Mock Data:** 2000+ issues, MRs, wiki pages
- **Confluence Mock Data:** 1500+ документов различных типов
- **User Content:** 500+ internal documents и guidelines
- **Synthetic Data:** 2000+ сгенерированных технических документов

**Test Dataset Requirements:**
- **Минимум 10,000 запросов** с ground truth ответами
- **1000+ вопросов** по доменам:
  - System Design (200 вопросов)
  - Business Analysis (200 вопросов) 
  - Architecture (200 вопросов)
  - DevOps (200 вопросов)
  - QA Engineering (200 вопросов)

**Метрики качества:**
```python
search_metrics = {
    "precision_at_k": [1, 3, 5, 10],
    "recall_at_k": [1, 3, 5, 10], 
    "ndcg_at_k": [1, 3, 5, 10],
    "mean_reciprocal_rank": "MRR",
    "response_time_ms": "average, p95, p99",
    "relevance_score": "human_evaluation",
    "coverage": "документов_найдено/всего_релевантных"
}
```

**Feedback System:**
- 👍/👎 для каждого результата поиска
- Текстовые комментарии от пользователей
- Ранжирование результатов (1-5 звезд)
- A/B тестирование разных моделей embeddings

### 📝 **2. RFC Generation Testing**

**Цель:** Валидация качества генерации RFC документов

**Test Cases (Минимум 1000+ кейсов):**
```python
rfc_test_cases = {
    "new_feature": 400,        # Проектирование нового функционала
    "modify_existing": 300,    # Изменение существующих систем  
    "analyze_current": 300     # Анализ текущего состояния
}

domains = {
    "authentication_systems": 200,
    "microservices_architecture": 200, 
    "data_processing_pipelines": 200,
    "monitoring_alerting": 200,
    "api_design": 200
}
```

**Validation Framework:**
```python
# testing/rfc_generation/
├── test_case_generator.py      # Автогенерация test cases
├── rfc_validator.py           # Валидация структуры и содержания
├── quality_metrics.py         # Метрики качества RFC
├── human_evaluator.py         # Человеческая оценка
└── benchmark_suite.py         # Комплексное тестирование
```

**Метрики качества RFC:**
```python
rfc_metrics = {
    # Текстовые метрики
    "bleu_score": "vs ground truth",
    "rouge_l": "vs reference docs", 
    "meteor_score": "semantic similarity",
    
    # Структурные метрики
    "completeness": "все_секции_заполнены",
    "consistency": "внутренняя_согласованность",
    "template_compliance": "соответствие_шаблону",
    
    # Performance метрики
    "generation_time_sec": "average, p95, p99",
    "token_count": "input + output",
    "cost_usd": "cost per RFC",
    
    # Человеческие оценки
    "clarity_score": "1-5 scale",
    "technical_accuracy": "1-5 scale", 
    "actionability": "1-5 scale",
    "overall_quality": "1-5 scale"
}
```

### 📥 **3. Dataset Auto-Loading System**

**Цель:** Автоматическая загрузка и обработка материалов из dataset_config.yml

**Компоненты:**
```python
# core/dataset_automation/
├── config_parser.py           # Парсинг dataset_config.yml
├── content_downloader.py      # Загрузка контента из URLs
├── format_processor.py        # Обработка PDF, GitHub repos, etc.
├── quality_checker.py         # Валидация загруженного контента
├── model_trainer.py           # Автоматическое обучение моделей
└── scheduler.py               # Периодическое обновление
```

**Supported Content Types:**
```python
content_processors = {
    "github_repos": GitHubProcessor(),      # Clone + extract docs/code
    "pdf_documents": PDFProcessor(),        # Text extraction + OCR
    "web_pages": WebProcessor(),            # HTML parsing + cleaning
    "courses": CourseProcessor(),           # Video transcription + materials  
    "academic_papers": PaperProcessor(),    # Citation extraction + processing
    "documentation": DocsProcessor()       # API docs, wikis, guides
}
```

**Training Pipeline:**
```python
# Автоматический цикл обучения
training_pipeline = {
    1: "download_new_materials(dataset_config.yml)",
    2: "preprocess_and_validate(content)",
    3: "update_knowledge_base(vectorstore)", 
    4: "fine_tune_models(learning_materials)",
    5: "evaluate_performance(test_suite)",
    6: "deploy_best_model(quality_threshold)",
    7: "schedule_next_update(24h)"
}
```

## 🎯 Приоритетный план развития

### 🔥 ВЫСОКИЙ ПРИОРИТЕТ (1-2 недели)

#### 1. **🐳 Containerization & Local Development (КРИТИЧНО!)**

**Статус:** Основа для всех deployment сценариев

**Задачи:**
1. **Docker Compose Stack**
   - Полная контейнеризация приложения
   - Multi-stage builds для оптимизации
   - ARM64 support для Apple Silicon
   - Health checks для всех сервисов

2. **Database Integration**
   - PostgreSQL schema initialization
   - Qdrant collections setup
   - Database migrations system
   - Connection pooling optimization

3. **Local Development Environment** 
   - One-command setup: `make local-up`
   - Automated data seeding
   - Development-specific configurations
   - Hot reload поддержка

**Файлы для создания:**
```
deployment/
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   └── .dockerignore
├── database/
│   ├── init.sql
│   ├── migrations/
│   └── seeds/
└── Makefile
```

#### 2. **🧪 Testing Infrastructure Setup (КРИТИЧНО!)**

**Статус:** Фундамент для enterprise deployment

**Задачи:**
1. **Test Data Generation Pipeline**
   - Создание synthetic dataset для поиска (10K запросов)
   - Генерация RFC test cases (1K кейсов)
   - Mock корпоративных данных (GitLab, Confluence)

2. **Metrics & Evaluation Framework**
   - Реализация поисковых метрик (Precision@K, Recall@K, NDCG)
   - RFC качественные метрики (BLEU, ROUGE, структурные)
   - Человеческая evaluation система

3. **Automated Testing Suite**
   - Continuous benchmarking
   - A/B testing framework
   - Performance regression detection

**Файлы для создания:**
```
testing/
├── semantic_search/
│   ├── test_data_generator.py
│   ├── search_evaluator.py
│   ├── knowledge_base_builder.py
│   └── benchmark_runner.py
├── rfc_generation/
│   ├── test_case_generator.py
│   ├── rfc_validator.py
│   ├── quality_metrics.py
│   └── human_evaluator.py
└── dataset_automation/
    ├── config_parser.py
    ├── content_downloader.py
    └── model_trainer.py
```

#### 3. **📊 Database Integration**

**Статус:** Архитектурная основа для всех данных

**Компоненты:**
```python
# core/database/
├── connection.py              # PostgreSQL connection management
├── models.py                  # SQLAlchemy models
├── qdrant_client.py          # Qdrant integration
├── migrations/               # Database schema migrations
└── repositories/             # Data access layer
```

### 🔶 СРЕДНИЙ ПРИОРИТЕТ (2-4 недели)

#### 4. **☸️ Kubernetes Deployment**

**Helm Chart Development:**
- Complete helm chart с best practices
- ConfigMaps и Secrets management
- Horizontal Pod Autoscaling
- Service mesh готовность (Istio)
- Monitoring integration (Prometheus/Grafana)

#### 5. **🔗 Automated Data Pipeline**

**Dataset Config Auto-Processing:**
- Автоматическая загрузка всех материалов из dataset_config.yml
- Intelligent preprocessing для разных типов контента
- Incremental updates и change detection
- Quality validation и content filtering

#### 6. **🧪 Advanced Model Training**

**OpenSource Model Optimization:**
- Fine-tuning локальных моделей на domain-specific data
- Hyperparameter optimization с metric-guided search
- Model ensemble для улучшения качества
- Continuous learning от user feedback

### 🔷 НИЗКИЙ ПРИОРИТЕТ (1-2 месяца)

#### 7. **🌐 Production-Ready Web UI**
#### 8. **🔐 Enterprise Security**  
#### 9. **⚡ Performance Optimization**
#### 10. **🌍 Advanced Integrations**

## 📋 Конкретные следующие шаги

### 🎯 Неделя 1: Containerization & Infrastructure

1. **Понедельник:** Docker Setup
```bash
# Создаем infrastructure
mkdir -p deployment/{docker,database,helm}
mkdir -p deployment/database/{migrations,seeds}
```

2. **Вторник-Среда:** Database Integration
- PostgreSQL schema design
- Qdrant collections setup
- Connection management
- Migration system

3. **Четверг-Пятница:** Docker Compose Stack
- Multi-service composition
- Health checks
- Volume management
- Network configuration

### 🎯 Неделя 2: Testing Infrastructure

1. **Понедельник:** Setup testing framework
```bash
# Создаем testing структуру
mkdir -p testing/{semantic_search,rfc_generation,dataset_automation}
mkdir -p testing/data/{search_queries,rfc_cases,mock_corporate}
```

2. **Вторник-Среда:** Test Data Generation
- Создание 10K search queries с ground truth
- Генерация 1K RFC test cases
- Mock GitLab/Confluence data

3. **Четверг-Пятница:** Metrics Implementation
- Поисковые метрики (Precision@K, NDCG)
- RFC качественные метрики
- Baseline measurements

## 🛠️ Готовые команды для полной инфраструктуры

### 🐳 **Containerization Setup (Mac M3 Pro)**

```bash
# 1. Создание полной infrastructure
mkdir -p deployment/{docker,database,helm,monitoring}
mkdir -p deployment/database/{migrations,seeds}
mkdir -p testing/{semantic_search,rfc_generation,dataset_automation}
mkdir -p core/storage/{learning_materials,search_sources,user_content}

# 2. Установка всех зависимостей
pip install psycopg2-binary sqlalchemy alembic qdrant-client
pip install uvicorn[standard] gunicorn
pip install scikit-learn pandas numpy nltk rouge-score sacrebleu 
pip install sentence-transformers evaluate datasets

# 3. Создание Dockerfile с ARM64 поддержкой
cat > deployment/docker/Dockerfile << 'EOF'
# Multi-stage build для оптимизации
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim as runtime
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# 4. Docker Compose с полным стеком
cat > deployment/docker/docker-compose.yml << 'EOF'
version: '3.8'

services:
  app:
    build: 
      context: ../..
      dockerfile: deployment/docker/Dockerfile
    platform: linux/arm64  # Mac M3 Pro optimization
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/ai_assistant
      - QDRANT_URL=http://qdrant:6333
      - OLLAMA_URL=http://ollama:11434
    depends_on:
      postgres: {condition: service_healthy}
      qdrant: {condition: service_healthy}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # PostgreSQL для метаданных
  postgres:
    image: postgres:15-alpine
    platform: linux/arm64
    environment:
      POSTGRES_DB: ai_assistant
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ../../deployment/database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports: ["5432:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Qdrant для векторной БД
  qdrant:
    image: qdrant/qdrant:latest
    platform: linux/arm64
    ports: ["6333:6333"]
    volumes: [qdrant_data:/qdrant/storage]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Ollama для локальных LLM
  ollama:
    image: ollama/ollama:latest
    platform: linux/arm64
    ports: ["11434:11434"]
    volumes: [ollama_data:/root/.ollama]
    environment: [OLLAMA_HOST=0.0.0.0]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  qdrant_data:
  ollama_data:
EOF

# 5. PostgreSQL schema initialization
cat > deployment/database/init.sql << 'EOF'
-- AI Assistant MVP Database Schema
CREATE SCHEMA IF NOT EXISTS ai_assistant;

-- User sessions
CREATE TABLE ai_assistant.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Generated RFCs
CREATE TABLE ai_assistant.rfcs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES ai_assistant.sessions(id),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    template_used VARCHAR(100),
    llm_provider VARCHAR(50),
    generation_time_ms INTEGER,
    tokens_used INTEGER,
    cost_usd DECIMAL(10,6),
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Learning pipeline data
CREATE TABLE ai_assistant.learning_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rfc_id UUID REFERENCES ai_assistant.rfcs(id),
    user_feedback INTEGER CHECK (user_feedback BETWEEN 1 AND 5),
    feedback_text TEXT,
    quality_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Data sources metadata
CREATE TABLE ai_assistant.data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(50) NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    vector_ids TEXT[],
    processing_status VARCHAR(50) DEFAULT 'pending',
    quality_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Search queries tracking
CREATE TABLE ai_assistant.search_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES ai_assistant.sessions(id),
    query_text TEXT NOT NULL,
    query_vector_id VARCHAR(255),
    results_count INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- LLM performance metrics
CREATE TABLE ai_assistant.llm_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    request_type VARCHAR(50),
    response_time_ms INTEGER,
    tokens_input INTEGER,
    tokens_output INTEGER,
    cost_usd DECIMAL(10,6),
    success BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_sessions_created_at ON ai_assistant.sessions(created_at);
CREATE INDEX idx_rfcs_session_id ON ai_assistant.rfcs(session_id);
CREATE INDEX idx_data_sources_type ON ai_assistant.data_sources(source_type);
CREATE INDEX idx_llm_metrics_provider ON ai_assistant.llm_metrics(provider, model);
EOF

# 6. Makefile для удобного управления
cat > Makefile << 'EOF'
.PHONY: local-up local-down build test k8s-deploy

# 🚀 One-command local deployment
local-up:
	@echo "🚀 Starting AI Assistant MVP (Mac M3 Pro optimized)..."
	cd deployment/docker && docker-compose up -d --build
	@echo "⏳ Waiting for services to be ready..."
	sleep 30
	@echo "✅ AI Assistant MVP is running!"
	@echo "   🌐 API: http://localhost:8000"
	@echo "   ❤️  Health: http://localhost:8000/health"
	@echo "   🔍 Qdrant: http://localhost:6333"
	@echo "   🗄️  PostgreSQL: localhost:5432"
	@echo "   🤖 Ollama: http://localhost:11434"

local-down:
	cd deployment/docker && docker-compose down -v
	@echo "🛑 AI Assistant MVP stopped"

local-logs:
	cd deployment/docker && docker-compose logs -f

# Build and test
build:
	cd deployment/docker && docker-compose build

test:
	PYTHONPATH=. pytest tests/ -v --tb=short

test-with-coverage:
	PYTHONPATH=. pytest tests/ -v --cov=. --cov-report=html

# Database operations
db-migrate:
	alembic upgrade head

db-seed:
	python3 deployment/database/seeds/seed_data.py

# Kubernetes deployment
k8s-deploy:
	helm install ai-assistant deployment/helm/ai-assistant \
		--namespace ai-assistant \
		--create-namespace \
		--values deployment/helm/ai-assistant/values-production.yaml

k8s-upgrade:
	helm upgrade ai-assistant deployment/helm/ai-assistant

k8s-uninstall:
	helm uninstall ai-assistant --namespace ai-assistant

# Testing infrastructure
benchmark:
	python3 testing/benchmark_runner.py

load-test:
	python3 testing/load_test.py --users 100 --duration 60s

# Dataset automation
dataset-download:
	python3 core/dataset_automation/config_parser.py --source dataset_config.yml

# Health checks
health-check:
	@echo "🔍 Checking all services..."
	@curl -s http://localhost:8000/health | jq .
	@curl -s http://localhost:6333/health | jq .
	@curl -s http://localhost:11434/api/tags | jq .

# Performance monitoring
monitor:
	@echo "📊 Opening monitoring dashboard..."
	open http://localhost:3000
EOF

# 7. Environment configuration для containerized setup
cat >> .env.local << 'EOF'

# 🐳 Containerized Environment Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_assistant
QDRANT_URL=http://localhost:6333
OLLAMA_URL=http://localhost:11434

# Docker settings
COMPOSE_PROJECT_NAME=ai_assistant
COMPOSE_FILE=deployment/docker/docker-compose.yml

# Development optimizations
RELOAD=true
DEBUG=true
LOG_LEVEL=info

# Apple Silicon optimizations
DOCKER_DEFAULT_PLATFORM=linux/arm64
DOCKER_BUILDKIT=1

# Resource limits for Mac M3 Pro (32GB RAM)
MAX_MEMORY_USAGE=16GB
MAX_CPU_CORES=8

# Testing configuration
TESTING_MODE=enabled
TEST_DATA_PATH=./testing/data
MIN_TEST_QUERIES=10000
MIN_RFC_CASES=1000

# Dataset automation
DATASET_AUTO_DOWNLOAD=true
DATASET_UPDATE_INTERVAL=24h
CONTENT_QUALITY_THRESHOLD=0.7

# Model training
AUTO_FINE_TUNING=true
TRAINING_BATCH_SIZE=32
EVALUATION_FREQUENCY=daily

# Metrics collection
ENABLE_METRICS_COLLECTION=true
HUMAN_EVALUATION_SAMPLE_SIZE=100
A_B_TEST_TRAFFIC_SPLIT=0.1
EOF

# 8. Создание базового Helm chart для Kubernetes
mkdir -p deployment/helm/ai-assistant/templates
cat > deployment/helm/ai-assistant/Chart.yaml << 'EOF'
apiVersion: v2
name: ai-assistant
description: AI Assistant MVP Helm Chart
type: application
version: 1.0.0
appVersion: "1.0.0"
EOF

cat > deployment/helm/ai-assistant/values.yaml << 'EOF'
# Default values for ai-assistant
global:
  domain: ai-assistant.local
  environment: development

app:
  replicaCount: 2
  image:
    repository: ai-assistant
    tag: "latest"
    pullPolicy: IfNotPresent
  
  service:
    type: ClusterIP
    port: 8000
  
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80

# Qdrant vector database
qdrant:
  enabled: true
  replicaCount: 2
  image:
    repository: qdrant/qdrant
    tag: latest
  persistence:
    enabled: true
    size: 50Gi
    storageClass: fast-ssd

# PostgreSQL database
postgresql:
  enabled: true
  auth:
    database: ai_assistant
    username: postgres
    password: password
  primary:
    persistence:
      enabled: true
      size: 20Gi

# Ollama LLM server
ollama:
  enabled: true
  replicaCount: 1
  image:
    repository: ollama/ollama
    tag: latest
  resources:
    requests:
      memory: 4Gi
      cpu: 1000m
    limits:
      memory: 8Gi
      cpu: 2000m
EOF

# 9. Проверка Docker и создание сети
docker network create ai-assistant-network 2>/dev/null || true

# 10. Проверка dataset_config.yml для автоматизации
python3 -c "
import yaml
try:
    with open('dataset_config.yml', 'r') as f:
        config = yaml.safe_load(f)
    print(f'✅ Dataset config found: {len(config.get(\"resources\", []))} resources')
    for r in config.get('resources', [])[:3]:
        print(f'   - {r.get(\"name\", \"Unknown\")}: {r.get(\"category\", \"Unknown\")}')
except FileNotFoundError:
    print('⚠️  dataset_config.yml not found - будет создан автоматически')
except Exception as e:
    print(f'❌ Error parsing dataset_config.yml: {e}')
"

echo ""
echo "🎯 Полная инфраструктура готова! Запускаем одной командой:"
echo ""
echo "   make local-up"
echo ""
echo "Это запустит:"
echo "   🐳 Docker Compose с PostgreSQL + Qdrant + Ollama + App"
echo "   🔍 Автоматическую проверку health checks"
echo "   📊 Мониторинг доступности всех сервисов"
echo "   🚀 Готовую к работе систему на http://localhost:8000"
echo ""
```

### ☸️ **Production Kubernetes Commands**

```bash
# Helm chart для production deployment
helm install ai-assistant deployment/helm/ai-assistant \
  --namespace ai-assistant \
  --create-namespace \
  --set global.environment=production \
  --set app.autoscaling.enabled=true \
  --set app.autoscaling.maxReplicas=20 \
  --set qdrant.persistence.size=100Gi \
  --set postgresql.primary.persistence.size=50Gi

# Проверка deployment
kubectl get pods -n ai-assistant
kubectl get services -n ai-assistant

# Scaling по требованию
kubectl scale deployment ai-assistant --replicas=5 -n ai-assistant
```

## 🛠️ Готовые команды для начала

```bash
# 1. Создание infrastructure
mkdir -p deployment/{docker,database,helm,monitoring}
mkdir -p deployment/database/{migrations,seeds}
mkdir -p testing/{semantic_search,rfc_generation,dataset_automation}

# 2. Database setup dependencies
pip install psycopg2-binary sqlalchemy alembic qdrant-client

# 3. Containerization dependencies  
pip install uvicorn[standard] gunicorn

# 4. Testing dependencies
pip install scikit-learn pandas numpy nltk rouge-score sacrebleu 
pip install sentence-transformers evaluate datasets

# 5. Создание базовых файлов инфраструктуры
cat > deployment/docker/Dockerfile << 'EOF'
# Multi-stage build для оптимизации
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim as runtime
WORKDIR /app

# Copy dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# 6. Базовый docker-compose.yml
cat > deployment/docker/docker-compose.yml << 'EOF'
version: '3.8'

services:
  app:
    build: 
      context: ../..
      dockerfile: deployment/docker/Dockerfile
    platform: linux/arm64
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/ai_assistant
      - QDRANT_URL=http://qdrant:6333
      - OLLAMA_URL=http://ollama:11434
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15-alpine
    platform: linux/arm64
    environment:
      POSTGRES_DB: ai_assistant
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ../../deployment/database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    platform: linux/arm64
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  ollama:
    image: ollama/ollama:latest
    platform: linux/arm64
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  qdrant_data:
  ollama_data:
EOF

# 7. Makefile для удобного управления
cat > Makefile << 'EOF'
.PHONY: local-up local-down build test k8s-deploy

# Local development
local-up:
	cd deployment/docker && docker-compose up -d --build
	@echo "🚀 AI Assistant MVP is running locally!"
	@echo "   - API: http://localhost:8000"
	@echo "   - Health: http://localhost:8000/health"
	@echo "   - Qdrant: http://localhost:6333"
	@echo "   - PostgreSQL: localhost:5432"

local-down:
	cd deployment/docker && docker-compose down -v

local-logs:
	cd deployment/docker && docker-compose logs -f

# Build and test
build:
	cd deployment/docker && docker-compose build

test:
	PYTHONPATH=. pytest tests/ -v --tb=short

test-with-coverage:
	PYTHONPATH=. pytest tests/ -v --cov=. --cov-report=html

# Database operations
db-migrate:
	alembic upgrade head

db-seed:
	python3 -c "from deployment.database.seeds import seed_data; seed_data()"

# Kubernetes operations
k8s-deploy:
	helm install ai-assistant deployment/helm/ai-assistant \
		--namespace ai-assistant \
		--create-namespace

k8s-upgrade:
	helm upgrade ai-assistant deployment/helm/ai-assistant

k8s-uninstall:
	helm uninstall ai-assistant --namespace ai-assistant

# Testing and benchmarking
benchmark:
	python3 testing/benchmark_runner.py

load-test:
	python3 testing/load_test.py

# Data operations
dataset-download:
	python3 core/dataset_automation/config_parser.py

# Monitoring
monitor:
	@echo "📊 Monitoring dashboard: http://localhost:3000"
	cd deployment/monitoring && docker-compose up -d
EOF

# 8. Обновление .env.local для containerized environment
cat >> .env.local << 'EOF'

# Containerized Environment
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_assistant
QDRANT_URL=http://localhost:6333
OLLAMA_URL=http://localhost:11434

# Docker Compose settings
COMPOSE_PROJECT_NAME=ai_assistant
COMPOSE_FILE=deployment/docker/docker-compose.yml

# Development settings
RELOAD=true
DEBUG=true
LOG_LEVEL=info

# Testing Configuration
TESTING_MODE=enabled
TEST_DATA_PATH=./testing/data
MIN_TEST_QUERIES=10000
MIN_RFC_CASES=1000

# Dataset Automation
DATASET_AUTO_DOWNLOAD=true
DATASET_UPDATE_INTERVAL=24h
CONTENT_QUALITY_THRESHOLD=0.7

# Model Training
AUTO_FINE_TUNING=true
TRAINING_BATCH_SIZE=32
EVALUATION_FREQUENCY=daily

# Metrics & Evaluation
ENABLE_METRICS_COLLECTION=true
HUMAN_EVALUATION_SAMPLE_SIZE=100
A_B_TEST_TRAFFIC_SPLIT=0.1
EOF

# 9. Проверка Docker и создание сети
docker network create ai-assistant-network 2>/dev/null || true

# 10. Запуск системы одной командой
echo "🎯 Готово! Запускаем систему одной командой:"
echo "make local-up"
```

## 🎯 Критерии успеха

### **После Containerization:**
- [ ] `make local-up` запускает полный стек за 2 минуты
- [ ] Все сервисы проходят health checks
- [ ] PostgreSQL и Qdrant интегрированы и работают
- [ ] ARM64 optimization для Mac M3 Pro
- [ ] Hot reload работает в dev режиме

### **После Testing Infrastructure:**
- [ ] 10,000+ search queries с ground truth ответами
- [ ] 1,000+ RFC test cases по всем доменам
- [ ] Автоматические метрики (Precision@K, BLEU, ROUGE)
- [ ] Baseline measurements для всех моделей
- [ ] Human evaluation framework работает

### **После Kubernetes Deployment:**
- [ ] `helm install` разворачивает production-ready систему
- [ ] Автомасштабирование работает (HPA)
- [ ] Мониторинг интегрирован (Prometheus/Grafana)
- [ ] Rolling updates без downtime
- [ ] Load balancing между репликами

## 📊 Infrastructure Benchmarks

### **Local Development Targets (Mac M3 Pro):**
```yaml
performance_targets:
  startup_time: "< 120 seconds"  # Full stack up
  memory_usage: "< 16GB total"   # All containers
  cpu_usage: "< 50% sustained"   # Under normal load
  storage_usage: "< 20GB"        # Including models
  
health_checks:
  app_response_time: "< 2s"
  postgres_connection: "< 100ms"
  qdrant_search: "< 500ms"
  ollama_inference: "< 10s"
```

### **Production Kubernetes Targets:**
```yaml
scalability_targets:
  min_replicas: 2
  max_replicas: 20
  target_cpu: 70%
  target_memory: 80%
  
availability_targets:
  uptime: 99.9%
  rto: "< 5 minutes"    # Recovery Time Objective
  rpo: "< 1 hour"       # Recovery Point Objective
  
performance_targets:
  requests_per_second: 1000
  concurrent_users: 500
  p95_response_time: "< 2s"
```

## 💬 Рекомендации по реализации

**🏆 Приоритет #1:** **Containerization** - основа для всех deployment сценариев

**🏆 Приоритет #2:** **Database Integration** - правильная архитектура данных с самого начала

**🏆 Приоритет #3:** **Testing Infrastructure** - валидация качества на всех уровнях

**Ключевые принципы:**
1. **Infrastructure as Code** - все в Docker/Helm/Terraform
2. **Database-First Architecture** - PostgreSQL + Qdrant с самого начала
3. **One-Command Deployment** - как локально, так и в production
4. **Apple Silicon Optimization** - все контейнеры ARM64-ready

**Система готова к enterprise deployment с полной containerization!** 🚀 