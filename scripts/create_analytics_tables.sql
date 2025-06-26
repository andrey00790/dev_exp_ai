-- Analytics Database Migration
-- Creates all tables needed for advanced analytics functionality

-- Create usage_metrics table
CREATE TABLE IF NOT EXISTS usage_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
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
CREATE INDEX IF NOT EXISTS ix_usage_metrics_session_id ON usage_metrics(session_id);
CREATE INDEX IF NOT EXISTS ix_usage_metrics_feature ON usage_metrics(feature);
CREATE INDEX IF NOT EXISTS ix_usage_metrics_action ON usage_metrics(action);
CREATE INDEX IF NOT EXISTS ix_usage_metrics_timestamp_feature ON usage_metrics(timestamp, feature);
CREATE INDEX IF NOT EXISTS ix_usage_metrics_user_timestamp ON usage_metrics(user_id, timestamp);
CREATE INDEX IF NOT EXISTS ix_usage_metrics_feature_success ON usage_metrics(feature, success);

-- Create cost_metrics table
CREATE TABLE IF NOT EXISTS cost_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    organization_id INTEGER,
    service VARCHAR(100) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    model VARCHAR(100),
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    requests_count INTEGER DEFAULT 1,
    cost_per_token FLOAT,
    input_cost FLOAT,
    output_cost FLOAT,
    total_cost FLOAT NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    request_id VARCHAR(255),
    feature_context VARCHAR(100),
    budget_category VARCHAR(100),
    is_billable BOOLEAN DEFAULT TRUE,
    metadata JSONB
);

-- Create indexes for cost_metrics
CREATE INDEX IF NOT EXISTS ix_cost_metrics_timestamp ON cost_metrics(timestamp);
CREATE INDEX IF NOT EXISTS ix_cost_metrics_user_id ON cost_metrics(user_id);
CREATE INDEX IF NOT EXISTS ix_cost_metrics_organization_id ON cost_metrics(organization_id);
CREATE INDEX IF NOT EXISTS ix_cost_metrics_service ON cost_metrics(service);
CREATE INDEX IF NOT EXISTS ix_cost_metrics_timestamp_service ON cost_metrics(timestamp, service);
CREATE INDEX IF NOT EXISTS ix_cost_metrics_user_timestamp ON cost_metrics(user_id, timestamp);
CREATE INDEX IF NOT EXISTS ix_cost_metrics_org_timestamp ON cost_metrics(organization_id, timestamp);

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
    disk_io_mb FLOAT,
    network_io_mb FLOAT,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    concurrent_requests INTEGER,
    status_code INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_type VARCHAR(100),
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(255),
    trace_id VARCHAR(255),
    metadata JSONB
);

-- Create indexes for performance_metrics
CREATE INDEX IF NOT EXISTS ix_performance_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS ix_performance_metrics_component ON performance_metrics(component);
CREATE INDEX IF NOT EXISTS ix_performance_metrics_endpoint ON performance_metrics(endpoint);
CREATE INDEX IF NOT EXISTS ix_performance_metrics_timestamp_component ON performance_metrics(timestamp, component);
CREATE INDEX IF NOT EXISTS ix_performance_metrics_endpoint_timestamp ON performance_metrics(endpoint, timestamp);
CREATE INDEX IF NOT EXISTS ix_performance_metrics_success_timestamp ON performance_metrics(success, timestamp);

-- Create user_behavior_metrics table
CREATE TABLE IF NOT EXISTS user_behavior_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    page_path VARCHAR(500),
    event_type VARCHAR(100) NOT NULL,
    event_name VARCHAR(200) NOT NULL,
    element_id VARCHAR(200),
    element_text TEXT,
    click_coordinates JSONB,
    session_duration_ms INTEGER,
    page_view_duration_ms INTEGER,
    referrer VARCHAR(500),
    user_agent VARCHAR(500),
    screen_resolution VARCHAR(20),
    browser VARCHAR(100),
    device_type VARCHAR(50),
    search_query TEXT,
    search_results_count INTEGER,
    selected_result_position INTEGER,
    conversion_event VARCHAR(100),
    conversion_value FLOAT,
    experiment_id VARCHAR(100),
    variant VARCHAR(50),
    metadata JSONB
);

-- Create indexes for user_behavior_metrics
CREATE INDEX IF NOT EXISTS ix_behavior_metrics_timestamp ON user_behavior_metrics(timestamp);
CREATE INDEX IF NOT EXISTS ix_behavior_metrics_user_id ON user_behavior_metrics(user_id);
CREATE INDEX IF NOT EXISTS ix_behavior_metrics_session_id ON user_behavior_metrics(session_id);
CREATE INDEX IF NOT EXISTS ix_behavior_metrics_event_type ON user_behavior_metrics(event_type);
CREATE INDEX IF NOT EXISTS ix_behavior_metrics_user_timestamp ON user_behavior_metrics(user_id, timestamp);
CREATE INDEX IF NOT EXISTS ix_behavior_metrics_session_timestamp ON user_behavior_metrics(session_id, timestamp);
CREATE INDEX IF NOT EXISTS ix_behavior_metrics_event_timestamp ON user_behavior_metrics(event_type, timestamp);

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
CREATE INDEX IF NOT EXISTS ix_aggregated_metrics_aggregation_period ON aggregated_metrics(aggregation_period);
CREATE INDEX IF NOT EXISTS ix_aggregated_metrics_metric_type ON aggregated_metrics(metric_type);
CREATE INDEX IF NOT EXISTS ix_aggregated_metrics_metric_name ON aggregated_metrics(metric_name);
CREATE INDEX IF NOT EXISTS ix_aggregated_metrics_dimension ON aggregated_metrics(dimension);
CREATE INDEX IF NOT EXISTS ix_aggregated_period_type ON aggregated_metrics(aggregation_period, metric_type);

-- Create unique constraint to prevent duplicate aggregations
CREATE UNIQUE INDEX IF NOT EXISTS ix_aggregated_unique ON aggregated_metrics(
    period_start, aggregation_period, metric_type, metric_name, 
    COALESCE(dimension, ''), COALESCE(dimension_value, '')
);

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
    affected_users JSONB,
    affected_features JSONB,
    status VARCHAR(50) DEFAULT 'active',
    reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Create indexes for insight_reports
CREATE INDEX IF NOT EXISTS ix_insight_reports_report_type ON insight_reports(report_type);
CREATE INDEX IF NOT EXISTS ix_insight_reports_period_start ON insight_reports(period_start);
CREATE INDEX IF NOT EXISTS ix_insight_reports_status ON insight_reports(status);
CREATE INDEX IF NOT EXISTS ix_insight_reports_impact_score ON insight_reports(impact_score);
CREATE INDEX IF NOT EXISTS ix_insight_reports_created_at ON insight_reports(created_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for insight_reports
CREATE TRIGGER update_insight_reports_updated_at 
    BEFORE UPDATE ON insight_reports 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample analytics data for testing
INSERT INTO usage_metrics (
    user_id, feature, action, duration_ms, tokens_used, success
) VALUES 
(1, 'search', 'query', 250.5, 150, true),
(1, 'generation', 'create_document', 1850.2, 500, true),
(1, 'search', 'query', 180.3, 100, true),
(2, 'search', 'query', 220.1, 120, true),
(2, 'generation', 'create_rfc', 2200.5, 800, true);

INSERT INTO cost_metrics (
    user_id, service, operation, model, input_tokens, output_tokens, total_tokens, total_cost
) VALUES 
(1, 'openai', 'completion', 'gpt-4', 150, 300, 450, 0.0135),
(1, 'openai', 'completion', 'gpt-4', 500, 200, 700, 0.021),
(2, 'anthropic', 'completion', 'claude-3', 120, 250, 370, 0.0111),
(2, 'openai', 'embedding', 'text-embedding-3-small', 800, 0, 800, 0.0002);

INSERT INTO performance_metrics (
    component, operation, response_time_ms, endpoint, success, status_code
) VALUES 
('api', 'search', 245.5, '/api/v1/vector-search/search', true, 200),
('api', 'generation', 1850.2, '/api/v1/generation/create', true, 200),
('llm', 'completion', 1600.8, null, true, 200),
('database', 'query', 45.2, null, true, 200),
('vectorstore', 'search', 120.3, null, true, 200);

-- Create stored procedure for data cleanup (optional)
CREATE OR REPLACE FUNCTION cleanup_old_analytics_data(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
    cutoff_date TIMESTAMP WITH TIME ZONE;
BEGIN
    cutoff_date := CURRENT_TIMESTAMP - INTERVAL '1 day' * days_to_keep;
    
    -- Clean up old raw metrics (keep aggregated data)
    DELETE FROM usage_metrics WHERE timestamp < cutoff_date;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    DELETE FROM performance_metrics WHERE timestamp < cutoff_date;
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    
    DELETE FROM user_behavior_metrics WHERE timestamp < cutoff_date;
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    
    -- Clean up old insight reports
    DELETE FROM insight_reports WHERE created_at < cutoff_date AND status = 'archived';
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ai_assistant_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ai_assistant_user;

-- Create analytics views for common queries
CREATE OR REPLACE VIEW analytics_summary AS
SELECT 
    'usage' as metric_type,
    COUNT(*) as total_records,
    MIN(timestamp) as earliest_data,
    MAX(timestamp) as latest_data
FROM usage_metrics
UNION ALL
SELECT 
    'cost' as metric_type,
    COUNT(*) as total_records,
    MIN(timestamp) as earliest_data,
    MAX(timestamp) as latest_data
FROM cost_metrics
UNION ALL
SELECT 
    'performance' as metric_type,
    COUNT(*) as total_records,
    MIN(timestamp) as earliest_data,
    MAX(timestamp) as latest_data
FROM performance_metrics
UNION ALL
SELECT 
    'behavior' as metric_type,
    COUNT(*) as total_records,
    MIN(timestamp) as earliest_data,
    MAX(timestamp) as latest_data
FROM user_behavior_metrics;

-- Create daily usage summary view
CREATE OR REPLACE VIEW daily_usage_summary AS
SELECT 
    DATE(timestamp) as date,
    feature,
    COUNT(*) as usage_count,
    COUNT(DISTINCT user_id) as unique_users,
    SUM(tokens_used) as total_tokens,
    AVG(duration_ms) as avg_duration_ms,
    SUM(CASE WHEN success = false THEN 1 ELSE 0 END) as error_count
FROM usage_metrics
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(timestamp), feature
ORDER BY date DESC, usage_count DESC;

-- Create cost summary view
CREATE OR REPLACE VIEW daily_cost_summary AS
SELECT 
    DATE(timestamp) as date,
    service,
    COUNT(*) as request_count,
    SUM(total_cost) as total_cost,
    AVG(total_cost) as avg_cost_per_request,
    SUM(total_tokens) as total_tokens
FROM cost_metrics
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
  AND is_billable = true
GROUP BY DATE(timestamp), service
ORDER BY date DESC, total_cost DESC;

COMMIT; 