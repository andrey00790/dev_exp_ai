-- AI Assistant Database Initialization Script
-- This script sets up the initial database schema and configuration

-- Connect to the database
\c ai_assistant;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema for application tables
CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS logs;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Set default search path
ALTER DATABASE ai_assistant SET search_path TO app, public;

-- Create basic application tables structure
CREATE TABLE IF NOT EXISTS app.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Documents table
CREATE TABLE IF NOT EXISTS app.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(1000),
    content TEXT,
    document_type VARCHAR(100),
    source_type VARCHAR(100),
    source_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_documents_source_type ON app.documents(source_type);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON app.documents(created_at);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA app TO ai_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA app TO ai_user;

-- Insert default admin user (password: admin123)
INSERT INTO app.users (username, email, hashed_password, is_superuser, is_active) 
VALUES ('admin', 'admin@aiassistant.local', '$2b$12$LQv3c1yqBw.h2WBdPt0zUOZ8xLB7Qqdo7JKjD7wJz3cGqbL9Q0zBK', TRUE, TRUE) 
ON CONFLICT (username) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'AI Assistant database initialization completed!';
END $$; 