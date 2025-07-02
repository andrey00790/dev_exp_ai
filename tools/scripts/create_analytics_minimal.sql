-- Minimal Analytics Tables (without dependencies)
-- For Phase 4.2 implementation

-- Create users table if not exists (simplified)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert test admin user
INSERT INTO users (email, is_admin) VALUES ('admin@example.com', true) ON CONFLICT DO NOTHING;

-- Create usage_metrics table
CREATE TABLE IF NOT EXISTS usage_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER,
    session_id VARCHAR(255),
    feature VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(200),
    count INTEGER DEFAULT 1 NOT NULL,
    duration_ms FLOAT,
    bytes_processed INTEGER,
    tokens_used INTEGER,
    user_agent VARCHAR(500),
    ip_address VARCHAR(45),
    api_version VARCHAR(20),
    success BOOLEAN DEFAULT TRUE NOT NULL,
    error_code VARCHAR(50),
    error_message TEXT,
    metadata JSONB
);

-- Create indexes for usage_metrics
CREATE INDEX IF NOT EXISTS ix_usage_metrics_timestamp ON usage_metrics(timestamp);
CREATE INDEX IF NOT EXISTS ix_usage_metrics_user_id ON usage_metrics(user_id);
CREATE INDEX IF NOT EXISTS ix_usage_metrics_feature ON usage_metrics(feature);
CREATE INDEX IF NOT EXISTS ix_usage_metrics_timestamp_feature ON usage_metrics(timestamp, feature);

-- Create cost_metrics table
CREATE TABLE IF NOT EXISTS cost_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER,
    organization_id INTEGER,
    service VARCHAR(100) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    model VARCHAR(100),
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    total_cost FLOAT NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    is_billable BOOLEAN DEFAULT TRUE,
    metadata JSONB
);

-- Create indexes for cost_metrics
CREATE INDEX IF NOT EXISTS ix_cost_metrics_timestamp ON cost_metrics(timestamp);
CREATE INDEX IF NOT EXISTS ix_cost_metrics_service ON cost_metrics(service);
CREATE INDEX IF NOT EXISTS ix_cost_metrics_timestamp_service ON cost_metrics(timestamp, service);

-- Create performance_metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    component VARCHAR(100) NOT NULL,
    endpoint VARCHAR(200),
    operation VARCHAR(100) NOT NULL,
    response_time_ms FLOAT NOT NULL,
    cpu_usage_percent FLOAT,
    memory_usage_mb FLOAT,
    status_code INTEGER,
    success BOOLEAN DEFAULT TRUE,
    user_id INTEGER,
    metadata JSONB
);

-- Create indexes for performance_metrics
CREATE INDEX IF NOT EXISTS ix_performance_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS ix_performance_metrics_component ON performance_metrics(component);
CREATE INDEX IF NOT EXISTS ix_performance_metrics_endpoint ON performance_metrics(endpoint);

-- Create user_behavior_metrics table
CREATE TABLE IF NOT EXISTS user_behavior_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    page_path VARCHAR(500),
    event_type VARCHAR(100) NOT NULL,
    event_name VARCHAR(200) NOT NULL,
    search_query TEXT,
    device_type VARCHAR(50),
    metadata JSONB
);

-- Create indexes for user_behavior_metrics
CREATE INDEX IF NOT EXISTS ix_behavior_metrics_timestamp ON user_behavior_metrics(timestamp);
CREATE INDEX IF NOT EXISTS ix_behavior_metrics_user_id ON user_behavior_metrics(user_id);
CREATE INDEX IF NOT EXISTS ix_behavior_metrics_event_type ON user_behavior_metrics(event_type);

-- Create aggregated_metrics table
CREATE TABLE IF NOT EXISTS aggregated_metrics (
    id SERIAL PRIMARY KEY,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    aggregation_period VARCHAR(20) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    dimension VARCHAR(100),
    dimension_value VARCHAR(500),
    count INTEGER,
    sum_value FLOAT,
    avg_value FLOAT,
    min_value FLOAT,
    max_value FLOAT,
    p50_value FLOAT,
    p95_value FLOAT,
    p99_value FLOAT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for aggregated_metrics
CREATE INDEX IF NOT EXISTS ix_aggregated_metrics_period_start ON aggregated_metrics(period_start);
CREATE INDEX IF NOT EXISTS ix_aggregated_metrics_metric_type ON aggregated_metrics(metric_type);

-- Create insight_reports table
CREATE TABLE IF NOT EXISTS insight_reports (
    id SERIAL PRIMARY KEY,
    report_type VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    insights JSONB NOT NULL,
    recommendations JSONB,
    impact_score FLOAT,
    confidence_score FLOAT,
    priority VARCHAR(20),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Insert sample analytics data
INSERT INTO usage_metrics (
    user_id, feature, action, duration_ms, tokens_used, success
) VALUES 
(1, 'search', 'query', 250.5, 150, true),
(1, 'generation', 'create_document', 1850.2, 500, true),
(1, 'search', 'query', 180.3, 100, true),
(1, 'analytics', 'dashboard_view', 120.0, 0, true),
(1, 'analytics', 'export_data', 350.0, 0, true);

INSERT INTO cost_metrics (
    user_id, service, operation, model, input_tokens, output_tokens, total_tokens, total_cost
) VALUES 
(1, 'openai', 'completion', 'gpt-4', 150, 300, 450, 0.0135),
(1, 'openai', 'completion', 'gpt-4', 500, 200, 700, 0.021),
(1, 'anthropic', 'completion', 'claude-3', 120, 250, 370, 0.0111),
(1, 'openai', 'embedding', 'text-embedding-3-small', 800, 0, 800, 0.0002);

INSERT INTO performance_metrics (
    component, operation, response_time_ms, endpoint, success, status_code
) VALUES 
('api', 'analytics_dashboard', 245.5, '/api/v1/analytics/dashboard/usage', true, 200),
('api', 'analytics_metrics', 85.2, '/api/v1/analytics/metrics/usage', true, 200),
('api', 'analytics_insights', 320.8, '/api/v1/analytics/insights/cost', true, 200),
('database', 'analytics_query', 45.2, null, true, 200),
('analytics', 'aggregation', 180.3, null, true, 200);

COMMIT; 