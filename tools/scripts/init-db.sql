-- AI Assistant Database Initialization Script
-- Создание базовых таблиц и настроек

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Создание схемы для аналитики
CREATE SCHEMA IF NOT EXISTS analytics;

-- Базовая таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица сессий пользователей
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Таблица источников данных
CREATE TABLE IF NOT EXISTS data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'confluence', 'jira', 'gitlab', 'local'
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица документов
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT,
    source_type VARCHAR(50) NOT NULL,
    source_id VARCHAR(255),
    source_url VARCHAR(500),
    metadata JSONB,
    quality_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица конфигураций пользователей
CREATE TABLE IF NOT EXISTS user_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    config_type VARCHAR(50) NOT NULL, -- 'jira', 'confluence', 'search_preferences'
    config_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, config_type)
);

-- Таблица обратной связи
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    feedback_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Аналитические таблицы
CREATE TABLE IF NOT EXISTS analytics.usage_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics.cost_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    service VARCHAR(50) NOT NULL, -- 'openai', 'anthropic', etc.
    operation VARCHAR(100) NOT NULL,
    cost_usd DECIMAL(10, 6) NOT NULL,
    tokens_used INTEGER,
    metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics.performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    response_time_ms INTEGER NOT NULL,
    status_code INTEGER NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token_hash ON user_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_documents_source_type ON documents(source_type);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_title_gin ON documents USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_documents_content_gin ON documents USING gin(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_user_configs_user_id ON user_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);

-- Аналитические индексы
CREATE INDEX IF NOT EXISTS idx_usage_metrics_user_id ON analytics.usage_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_metrics_timestamp ON analytics.usage_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_cost_metrics_user_id ON analytics.cost_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_cost_metrics_timestamp ON analytics.cost_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_endpoint ON analytics.performance_metrics(endpoint);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON analytics.performance_metrics(timestamp);

-- Триггеры для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_sources_updated_at BEFORE UPDATE ON data_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_configs_updated_at BEFORE UPDATE ON user_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Создание тестового пользователя для разработки
INSERT INTO users (email, username, password_hash, full_name, is_admin) 
VALUES (
    'admin@example.com', 
    'admin', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8GvQ6x.9Zu', -- password: admin123
    'Admin User',
    true
) ON CONFLICT (email) DO NOTHING;

INSERT INTO users (email, username, password_hash, full_name, is_admin) 
VALUES (
    'user@example.com', 
    'user', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8GvQ6x.9Zu', -- password: admin123
    'Test User',
    false
) ON CONFLICT (email) DO NOTHING;

-- Создание базовых источников данных
INSERT INTO data_sources (name, type, config) VALUES 
('Local Bootstrap', 'local', '{"path": "/app/bootstrap", "recursive": true}'),
('Example Confluence', 'confluence', '{"base_url": "https://example.atlassian.net", "space_key": "DEV"}'),
('Example GitLab', 'gitlab', '{"base_url": "https://gitlab.example.com", "project_id": "123"}')
ON CONFLICT DO NOTHING;

-- Создание представлений для аналитики
CREATE OR REPLACE VIEW analytics.daily_usage AS
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as total_actions,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(*) FILTER (WHERE action LIKE 'search%') as search_actions,
    COUNT(*) FILTER (WHERE action LIKE 'generate%') as generation_actions
FROM analytics.usage_metrics
GROUP BY DATE(timestamp)
ORDER BY date DESC;

CREATE OR REPLACE VIEW analytics.daily_costs AS
SELECT 
    DATE(timestamp) as date,
    SUM(cost_usd) as total_cost,
    COUNT(*) as total_operations,
    SUM(tokens_used) as total_tokens,
    AVG(cost_usd) as avg_cost_per_operation
FROM analytics.cost_metrics
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Права доступа
GRANT USAGE ON SCHEMA analytics TO ai_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ai_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA analytics TO ai_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ai_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA analytics TO ai_user;

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Пользователи системы';
COMMENT ON TABLE user_sessions IS 'Активные сессии пользователей';
COMMENT ON TABLE data_sources IS 'Источники данных для синхронизации';
COMMENT ON TABLE documents IS 'Документы из различных источников';
COMMENT ON TABLE user_configs IS 'Конфигурации пользователей';
COMMENT ON TABLE feedback IS 'Обратная связь от пользователей';
COMMENT ON TABLE analytics.usage_metrics IS 'Метрики использования системы';
COMMENT ON TABLE analytics.cost_metrics IS 'Метрики стоимости AI операций';
COMMENT ON TABLE analytics.performance_metrics IS 'Метрики производительности API';

-- Финализация
SELECT 'Database initialization completed successfully!' as status; 