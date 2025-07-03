-- Инициализация тестовой базы данных
-- Создается при первом запуске PostgreSQL контейнера

-- Создаем схемы
CREATE SCHEMA IF NOT EXISTS app_data;
CREATE SCHEMA IF NOT EXISTS test_data;
CREATE SCHEMA IF NOT EXISTS cache_data;
CREATE SCHEMA IF NOT EXISTS search_data;

-- Создаем расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS app_data.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица конфигураций пользователей
CREATE TABLE IF NOT EXISTS app_data.user_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES app_data.users(id) ON DELETE CASCADE,
    config_type VARCHAR(50) NOT NULL,
    config_name VARCHAR(255) NOT NULL,
    config_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, config_type, config_name)
);

-- Таблица источников данных
CREATE TABLE IF NOT EXISTS app_data.data_sources (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES app_data.users(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    connection_config JSONB NOT NULL,
    sync_config JSONB DEFAULT '{}',
    is_enabled BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, source_type, source_name)
);

-- Таблица документов
CREATE TABLE IF NOT EXISTS app_data.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER REFERENCES app_data.users(id) ON DELETE CASCADE,
    source_id INTEGER REFERENCES app_data.data_sources(id) ON DELETE CASCADE,
    doc_type VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    metadata JSONB DEFAULT '{}',
    vector_id VARCHAR(255), -- ID в векторной БД
    indexed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица обратной связи
CREATE TABLE IF NOT EXISTS app_data.feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES app_data.users(id) ON DELETE CASCADE,
    session_id VARCHAR(255),
    query_text TEXT NOT NULL,
    response_text TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица метрик модели
CREATE TABLE IF NOT EXISTS app_data.model_metrics (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metadata JSONB DEFAULT '{}',
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- === КЭШИРОВАНИЕ В POSTGRESQL ===

-- Таблица для кэша (замена Redis)
CREATE TABLE IF NOT EXISTS cache_data.cache_entries (
    cache_key VARCHAR(255) PRIMARY KEY,
    cache_value JSONB NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для сессий пользователей
CREATE TABLE IF NOT EXISTS cache_data.user_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id INTEGER REFERENCES app_data.users(id) ON DELETE CASCADE,
    session_data JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- === ПОИСК В POSTGRESQL ===

-- Создание таблицы поискового индекса
CREATE TABLE search_data.search_index (
    id SERIAL PRIMARY KEY,
    document_id UUID UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    search_vector TSVECTOR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES app_data.documents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES app_data.users(id) ON DELETE CASCADE
);

-- Таблица для истории поиска
CREATE TABLE IF NOT EXISTS search_data.search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES app_data.users(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    results_count INTEGER DEFAULT 0,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_users_email ON app_data.users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON app_data.users(username);
CREATE INDEX IF NOT EXISTS idx_user_configs_user_id ON app_data.user_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_configs_type ON app_data.user_configs(config_type);
CREATE INDEX IF NOT EXISTS idx_data_sources_user_id ON app_data.data_sources(user_id);
CREATE INDEX IF NOT EXISTS idx_data_sources_type ON app_data.data_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON app_data.documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_source_id ON app_data.documents(source_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON app_data.documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON app_data.feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_rating ON app_data.feedback(rating);
CREATE INDEX IF NOT EXISTS idx_model_metrics_name_version ON app_data.model_metrics(model_name, model_version);

-- Индексы для кэша
CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache_data.cache_entries(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON cache_data.user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON cache_data.user_sessions(expires_at);

-- Индексы для поиска
CREATE INDEX IF NOT EXISTS idx_search_document_id ON search_data.search_index(document_id);
CREATE INDEX IF NOT EXISTS idx_search_user_id ON search_data.search_index(user_id);
CREATE INDEX IF NOT EXISTS idx_search_vector ON search_data.search_index USING gin(search_vector);
CREATE INDEX IF NOT EXISTS idx_search_title_gin ON search_data.search_index USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_search_content_gin ON search_data.search_index USING gin(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON search_data.search_history(user_id);
CREATE INDEX IF NOT EXISTS idx_search_history_created_at ON search_data.search_history(created_at);

-- Функция для обновления search_vector
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для автоматического обновления search_vector
CREATE TRIGGER update_search_vector_trigger
    BEFORE INSERT OR UPDATE ON search_data.search_index
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- Функция для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автоматического обновления updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON app_data.users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_configs_updated_at BEFORE UPDATE ON app_data.user_configs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_data_sources_updated_at BEFORE UPDATE ON app_data.data_sources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON app_data.documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cache_entries_updated_at BEFORE UPDATE ON cache_data.cache_entries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_sessions_updated_at BEFORE UPDATE ON cache_data.user_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_search_index_updated_at BEFORE UPDATE ON search_data.search_index FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Функция для очистки устаревшего кэша
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
    temp_count INTEGER;
BEGIN
    DELETE FROM cache_data.cache_entries WHERE expires_at < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    DELETE FROM cache_data.user_sessions WHERE expires_at < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Функция для полнотекстового поиска
CREATE OR REPLACE FUNCTION search_documents(
    p_user_id INTEGER,
    p_query TEXT,
    p_limit INTEGER DEFAULT 10,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE(
    document_id UUID,
    title TEXT,
    content TEXT,
    rank REAL,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        si.document_id,
        si.title,
        si.content,
        ts_rank(si.search_vector, plainto_tsquery('english', p_query)) as rank,
        si.metadata
    FROM search_data.search_index si
    WHERE si.user_id = p_user_id
    AND si.search_vector @@ plainto_tsquery('english', p_query)
    ORDER BY rank DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- Тестовые данные
INSERT INTO app_data.users (username, email, password_hash) VALUES 
    ('testuser1', 'test1@example.com', 'hashed_password_1'),
    ('testuser2', 'test2@example.com', 'hashed_password_2'),
    ('admin', 'admin@example.com', 'hashed_admin_password')
ON CONFLICT (email) DO NOTHING;

-- Тестовые конфигурации
INSERT INTO app_data.user_configs (user_id, config_type, config_name, config_data) VALUES 
    (1, 'jira', 'default', '{"url": "https://test.atlassian.net", "projects": ["TEST"]}'),
    (1, 'confluence', 'default', '{"url": "https://test.atlassian.net/wiki", "spaces": ["TEST"]}'),
    (2, 'gitlab', 'default', '{"url": "https://gitlab.example.com", "projects": ["test/repo"]}')
ON CONFLICT (user_id, config_type, config_name) DO NOTHING;

-- Тестовые источники данных
INSERT INTO app_data.data_sources (user_id, source_type, source_name, connection_config) VALUES 
    (1, 'jira', 'test-jira', '{"url": "https://test.atlassian.net", "auth": "token"}'),
    (1, 'confluence', 'test-confluence', '{"url": "https://test.atlassian.net/wiki", "auth": "token"}'),
    (2, 'gitlab', 'test-gitlab', '{"url": "https://gitlab.example.com", "auth": "token"}')
ON CONFLICT (user_id, source_type, source_name) DO NOTHING;

-- Тестовые документы
INSERT INTO app_data.documents (user_id, source_id, doc_type, title, content, metadata) VALUES 
    (1, 1, 'jira_issue', 'Test Issue #1', 'This is a test issue for integration testing', '{"priority": "high", "status": "open"}'),
    (1, 2, 'confluence_page', 'Integration Testing Guide', 'Comprehensive guide for integration testing with PostgreSQL', '{"space": "TEST", "author": "testuser1"}'),
    (2, 3, 'gitlab_file', 'README.md', 'Project documentation and setup instructions', '{"repository": "test/repo", "branch": "main"}')
ON CONFLICT DO NOTHING;

-- Добавляем документы в поисковый индекс
INSERT INTO search_data.search_index (document_id, user_id, title, content, metadata)
SELECT id, user_id, title, content, metadata
FROM app_data.documents
ON CONFLICT DO NOTHING;

-- Тестовые записи кэша
INSERT INTO cache_data.cache_entries (cache_key, cache_value, expires_at) VALUES 
    ('test:key1', '{"data": "test_value_1"}', CURRENT_TIMESTAMP + INTERVAL '1 hour'),
    ('test:key2', '{"data": "test_value_2"}', CURRENT_TIMESTAMP + INTERVAL '30 minutes')
ON CONFLICT (cache_key) DO NOTHING;

-- Права доступа
GRANT ALL PRIVILEGES ON SCHEMA app_data TO testuser;
GRANT ALL PRIVILEGES ON SCHEMA test_data TO testuser;
GRANT ALL PRIVILEGES ON SCHEMA cache_data TO testuser;
GRANT ALL PRIVILEGES ON SCHEMA search_data TO testuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA app_data TO testuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA app_data TO testuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA test_data TO testuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA test_data TO testuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cache_data TO testuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA cache_data TO testuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA search_data TO testuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA search_data TO testuser;

-- Логирование
\echo 'Тестовая база данных с поддержкой кэширования и поиска инициализирована успешно!' 