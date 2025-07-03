-- AI Assistant MVP Database Initialization Script
-- This script creates the necessary tables and indexes for the AI Assistant MVP

\echo 'Starting AI Assistant MVP database initialization...'

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS ai_assistant;
SET search_path TO ai_assistant, public;

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    tags TEXT[],
    status VARCHAR(50) DEFAULT 'active'
);

-- Sessions table for RFC generation tracking
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500),
    description TEXT,
    priority VARCHAR(50),
    type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'in_progress',
    questions JSONB,
    answers JSONB,
    generated_content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(100)
);

-- Feedback table
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    feedback_type VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- LLM usage metrics table
CREATE TABLE IF NOT EXISTS llm_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    operation VARCHAR(50) NOT NULL,
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6) DEFAULT 0,
    response_time_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    session_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Learning data table for model improvements
CREATE TABLE IF NOT EXISTS learning_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    feedback_rating INTEGER,
    context JSONB,
    source VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL, -- 'search', 'rfc_generation', 'question_answer'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_validated BOOLEAN DEFAULT false,
    validation_score DECIMAL(3, 2)
);

-- Data sources configuration table
CREATE TABLE IF NOT EXISTS data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL, -- 'confluence', 'gitlab', 'jira', 'file_upload'
    config JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    last_sync TIMESTAMP WITH TIME ZONE,
    sync_frequency VARCHAR(50), -- 'hourly', 'daily', 'weekly'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Search queries log for analytics
CREATE TABLE IF NOT EXISTS search_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query TEXT NOT NULL,
    filters JSONB,
    results_count INTEGER,
    response_time_ms INTEGER,
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
\echo 'Creating indexes...'

-- Documents indexes
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_title_gin ON documents USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_documents_content_gin ON documents USING gin(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING gin(metadata);
CREATE INDEX IF NOT EXISTS idx_documents_tags ON documents USING gin(tags);

-- Sessions indexes
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_type ON sessions(type);

-- Feedback indexes
CREATE INDEX IF NOT EXISTS idx_feedback_session_id ON feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_rating ON feedback(rating);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type);

-- LLM metrics indexes
CREATE INDEX IF NOT EXISTS idx_llm_metrics_provider ON llm_metrics(provider);
CREATE INDEX IF NOT EXISTS idx_llm_metrics_model ON llm_metrics(model);
CREATE INDEX IF NOT EXISTS idx_llm_metrics_created_at ON llm_metrics(created_at);
CREATE INDEX IF NOT EXISTS idx_llm_metrics_session_id ON llm_metrics(session_id);

-- Learning data indexes
CREATE INDEX IF NOT EXISTS idx_learning_data_source ON learning_data(source);
CREATE INDEX IF NOT EXISTS idx_learning_data_type ON learning_data(data_type);
CREATE INDEX IF NOT EXISTS idx_learning_data_created_at ON learning_data(created_at);
CREATE INDEX IF NOT EXISTS idx_learning_data_rating ON learning_data(feedback_rating);

-- Search queries indexes
CREATE INDEX IF NOT EXISTS idx_search_queries_created_at ON search_queries(created_at);
CREATE INDEX IF NOT EXISTS idx_search_queries_user_id ON search_queries(user_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_sources_updated_at BEFORE UPDATE ON data_sources 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial data sources configuration
\echo 'Inserting initial configuration...'

INSERT INTO data_sources (name, type, config, status) VALUES
    ('local_files', 'file_upload', '{"max_file_size": "50MB", "allowed_types": ["pdf", "txt", "md", "docx"]}', 'active'),
    ('dataset_config', 'yaml_config', '{"config_file": "dataset_config.yml", "auto_sync": true}', 'active')
ON CONFLICT (name) DO NOTHING;

-- Create views for common queries
CREATE OR REPLACE VIEW active_sessions AS
SELECT 
    session_id,
    title,
    description,
    type,
    priority,
    status,
    created_at,
    updated_at,
    (CASE WHEN completed_at IS NOT NULL THEN 
        EXTRACT(EPOCH FROM (completed_at - created_at)) 
    ELSE 
        EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_at)) 
    END) as duration_seconds
FROM sessions 
WHERE status IN ('in_progress', 'completed');

CREATE OR REPLACE VIEW llm_usage_stats AS
SELECT 
    provider,
    model,
    COUNT(*) as total_requests,
    SUM(tokens_used) as total_tokens,
    SUM(cost_usd) as total_cost,
    AVG(response_time_ms) as avg_response_time,
    SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as success_rate,
    DATE(created_at) as date
FROM llm_metrics 
GROUP BY provider, model, DATE(created_at)
ORDER BY date DESC, total_requests DESC;

CREATE OR REPLACE VIEW feedback_analytics AS
SELECT 
    feedback_type,
    AVG(rating::FLOAT) as avg_rating,
    COUNT(*) as total_feedback,
    COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive_feedback,
    COUNT(CASE WHEN rating <= 2 THEN 1 END) as negative_feedback,
    DATE(created_at) as date
FROM feedback 
GROUP BY feedback_type, DATE(created_at)
ORDER BY date DESC;

-- Set default search path
ALTER DATABASE ai_assistant SET search_path TO ai_assistant, public;

\echo 'AI Assistant MVP database initialization completed successfully!'
\echo 'Created tables: documents, sessions, feedback, llm_metrics, learning_data, data_sources, search_queries'
\echo 'Created views: active_sessions, llm_usage_stats, feedback_analytics' 