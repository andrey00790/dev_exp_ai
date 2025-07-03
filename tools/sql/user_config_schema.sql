-- Схема базы данных для пользовательских настроек
-- User configuration database schema

-- =============================================================================
-- ПОЛЬЗОВАТЕЛИ И НАСТРОЙКИ
-- =============================================================================

-- Пользователи системы
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    settings JSONB DEFAULT '{}'::jsonb
);

-- Конфигурации источников данных для пользователей
CREATE TABLE user_data_sources (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL, -- 'confluence', 'jira', 'gitlab', 'user_files', 'mail_cloud', 'bootstrap_config'
    source_name VARCHAR(100) NOT NULL, -- Название источника
    is_enabled_semantic_search BOOLEAN DEFAULT TRUE,
    is_enabled_architecture_generation BOOLEAN DEFAULT TRUE,
    connection_config JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sync_at TIMESTAMP,
    sync_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'success', 'error'
    error_message TEXT,
    sync_schedule VARCHAR(100), -- Cron-like schedule e.g., '0 2 * * *'
    auto_sync_on_startup BOOLEAN DEFAULT TRUE,
    
    UNIQUE(user_id, source_type, source_name)
);

-- Настройки подключений к Jira (логин+пароль)
CREATE TABLE user_jira_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    config_name VARCHAR(100) NOT NULL,
    jira_url VARCHAR(500) NOT NULL,
    username VARCHAR(100) NOT NULL,
    password_encrypted TEXT NOT NULL, -- Зашифрованный пароль
    is_default BOOLEAN DEFAULT FALSE,
    projects JSONB DEFAULT '[]'::jsonb, -- Список проектов для синхронизации
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, config_name)
);

-- Настройки подключений к Confluence DC ≥ 8.0 (Bearer-PAT)
CREATE TABLE user_confluence_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    config_name VARCHAR(100) NOT NULL,
    confluence_url VARCHAR(500) NOT NULL,
    bearer_token_encrypted TEXT NOT NULL, -- Зашифрованный Bearer-PAT токен
    is_default BOOLEAN DEFAULT FALSE,
    spaces JSONB DEFAULT '[]'::jsonb, -- Список пространств для синхронизации
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, config_name)
);

-- Настройки подключений к GitLab (динамический список серверов)
CREATE TABLE user_gitlab_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    alias VARCHAR(100) NOT NULL, -- Псевдоним сервера (main, open, etc.)
    gitlab_url VARCHAR(500) NOT NULL,
    access_token_encrypted TEXT NOT NULL, -- Зашифрованный токен доступа
    is_default BOOLEAN DEFAULT FALSE,
    projects JSONB DEFAULT '[]'::jsonb, -- Список проектов для синхронизации
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, alias)
);

-- Пользовательские файлы и документы (PDF, TXT, DOC, EPUB и др.)
CREATE TABLE user_files (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL, -- 'pdf', 'txt', 'doc', 'epub', etc.
    file_size BIGINT NOT NULL,
    file_path TEXT NOT NULL, -- Путь к файлу в файловой системе/S3
    content_text TEXT, -- Извлеченный текст
    metadata JSONB DEFAULT '{}'::jsonb, -- Дополнительные метаданные
    is_processed BOOLEAN DEFAULT FALSE,
    is_marked_as_user_content BOOLEAN DEFAULT TRUE,
    tags JSONB DEFAULT '[]'::jsonb, -- Теги для категоризации
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- =============================================================================
-- СИСТЕМА СИНХРОНИЗАЦИИ
-- =============================================================================

-- Задачи синхронизации (крон и ручные запуски)
CREATE TABLE sync_tasks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    task_type VARCHAR(20) NOT NULL, -- 'manual', 'scheduled'
    sources JSONB NOT NULL, -- Список источников для синхронизации
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    progress_percentage INTEGER DEFAULT 0,
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    logs JSONB DEFAULT '[]'::jsonb, -- Логи выполнения
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Настройки крон-задач для пользователей
CREATE TABLE user_cron_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    cron_expression VARCHAR(100) NOT NULL, -- '0 2 * * *' для ежедневно в 2 утра
    sources JSONB NOT NULL, -- Источники для автоматической синхронизации
    is_enabled BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Логи синхронизации
CREATE TABLE sync_logs (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES sync_tasks(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    log_level VARCHAR(10) NOT NULL, -- 'INFO', 'WARNING', 'ERROR'
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- КОНФИГУРАЦИЯ ПО УМОЛЧАНИЮ
-- =============================================================================

-- Функция для создания пользователя с настройками по умолчанию
CREATE OR REPLACE FUNCTION create_user_with_defaults(
    p_username VARCHAR(100),
    p_email VARCHAR(255)
) RETURNS INTEGER AS $$
DECLARE
    user_id INTEGER;
BEGIN
    -- Создаем пользователя
    INSERT INTO users (username, email) 
    VALUES (p_username, p_email) 
    RETURNING id INTO user_id;
    
    -- Создаем настройки источников данных по умолчанию
    -- Для семантического поиска включены: Jira, Confluence, GitLab
    -- Пользовательские файлы отключены
    INSERT INTO user_data_sources (user_id, source_type, source_name, is_enabled_semantic_search, is_enabled_architecture_generation, connection_config, auto_sync_on_startup)
    VALUES 
        (user_id, 'jira', 'default', TRUE, TRUE, '{"enabled": true}'::jsonb, TRUE),
        (user_id, 'confluence', 'default', TRUE, TRUE, '{"enabled": true}'::jsonb, TRUE),
        (user_id, 'gitlab', 'default', TRUE, TRUE, '{"enabled": true}'::jsonb, TRUE),
        (user_id, 'user_files', 'default', FALSE, TRUE, '{"enabled": false}'::jsonb, FALSE),
        (user_id, 'bootstrap_config', 'default', TRUE, TRUE, '{"file_path": "dataset_config.yml"}'::jsonb, TRUE);
    
    RETURN user_id;
END;
$$ LANGUAGE plpgsql;

-- Функция для получения активных источников пользователя для семантического поиска
CREATE OR REPLACE FUNCTION get_user_semantic_search_sources(p_user_id INTEGER)
RETURNS TABLE(source_type VARCHAR, source_name VARCHAR, connection_config JSONB) AS $$
BEGIN
    RETURN QUERY
    SELECT uds.source_type, uds.source_name, uds.connection_config
    FROM user_data_sources uds
    WHERE uds.user_id = p_user_id 
      AND uds.is_enabled_semantic_search = TRUE;
END;
$$ LANGUAGE plpgsql;

-- Функция для получения активных источников пользователя для генерации архитектуры
CREATE OR REPLACE FUNCTION get_user_architecture_sources(p_user_id INTEGER)
RETURNS TABLE(source_type VARCHAR, source_name VARCHAR, connection_config JSONB) AS $$
BEGIN
    RETURN QUERY
    SELECT uds.source_type, uds.source_name, uds.connection_config
    FROM user_data_sources uds
    WHERE uds.user_id = p_user_id 
      AND uds.is_enabled_architecture_generation = TRUE;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
-- =============================================================================

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_user_data_sources_user_id ON user_data_sources(user_id);
CREATE INDEX idx_user_data_sources_type ON user_data_sources(source_type);
CREATE INDEX idx_user_files_user_id ON user_files(user_id);
CREATE INDEX idx_user_files_type ON user_files(file_type);
CREATE INDEX idx_sync_tasks_user_id ON sync_tasks(user_id);
CREATE INDEX idx_sync_tasks_status ON sync_tasks(status);
CREATE INDEX idx_sync_logs_task_id ON sync_logs(task_id);
