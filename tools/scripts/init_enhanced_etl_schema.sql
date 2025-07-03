-- Enhanced ETL Schema for AI Assistant
-- Supports multiple data sources: YDB, ClickHouse, Confluence, GitLab, Jira, Local Files
-- Run this script to upgrade database schema for enhanced ETL capabilities

-- Ensure required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Enhanced ingestion_log table
CREATE TABLE IF NOT EXISTS ingestion_log (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    database_name VARCHAR(255), -- For YDB/ClickHouse database name
    table_name VARCHAR(255),    -- For specific table sync
    
    -- Sync statistics
    rowcount INTEGER DEFAULT 0,
    records_processed INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    
    -- Timing information
    duration_ms BIGINT DEFAULT 0,
    sync_ts TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Status and error tracking
    status VARCHAR(20) DEFAULT 'pending', -- pending, running, completed, failed, cancelled
    error_message TEXT,
    error_count INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    
    -- Sync metadata
    sync_mode VARCHAR(20) DEFAULT 'incremental', -- incremental, full
    last_sync_timestamp TIMESTAMP WITH TIME ZONE,
    batch_size INTEGER,
    
    -- Performance metrics
    avg_processing_time_ms REAL,
    memory_usage_mb INTEGER,
    cpu_usage_percent REAL,
    
    -- Data quality metrics
    data_quality_score REAL,
    schema_changes_detected BOOLEAN DEFAULT FALSE,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Data source configurations table
CREATE TABLE IF NOT EXISTS data_source_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id VARCHAR(255) UNIQUE NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    
    -- Connection configuration
    connection_config JSONB NOT NULL DEFAULT '{}',
    auth_config JSONB DEFAULT '{}',
    
    -- Sync configuration
    sync_config JSONB DEFAULT '{}',
    enabled BOOLEAN DEFAULT TRUE,
    
    -- Health and status
    last_health_check TIMESTAMP WITH TIME ZONE,
    health_status VARCHAR(20) DEFAULT 'unknown', -- healthy, unhealthy, unknown
    health_details JSONB DEFAULT '{}',
    
    -- Metadata
    description TEXT,
    tags TEXT[] DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- Data source schemas table (for schema tracking)
CREATE TABLE IF NOT EXISTS data_source_schemas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id VARCHAR(255) NOT NULL,
    database_name VARCHAR(255),
    table_name VARCHAR(255) NOT NULL,
    
    -- Schema information
    schema_hash VARCHAR(64) NOT NULL,
    column_count INTEGER,
    row_count BIGINT,
    table_size_bytes BIGINT,
    
    -- Schema details
    columns JSONB NOT NULL DEFAULT '[]',
    indexes JSONB DEFAULT '[]',
    constraints JSONB DEFAULT '[]',
    
    -- Discovery metadata
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    schema_version INTEGER DEFAULT 1,
    
    -- Change tracking
    previous_schema_hash VARCHAR(64),
    schema_changes JSONB DEFAULT '[]',
    
    FOREIGN KEY (source_id) REFERENCES data_source_configs(source_id) ON DELETE CASCADE
);

-- Sync schedules table
CREATE TABLE IF NOT EXISTS sync_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id VARCHAR(255) NOT NULL,
    
    -- Schedule configuration
    schedule_type VARCHAR(20) NOT NULL DEFAULT 'interval', -- interval, cron, manual
    interval_minutes INTEGER,
    cron_expression VARCHAR(100),
    
    -- Schedule state
    enabled BOOLEAN DEFAULT TRUE,
    last_run TIMESTAMP WITH TIME ZONE,
    next_run TIMESTAMP WITH TIME ZONE,
    
    -- Execution tracking
    run_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    
    -- Configuration
    max_retries INTEGER DEFAULT 3,
    timeout_minutes INTEGER DEFAULT 60,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (source_id) REFERENCES data_source_configs(source_id) ON DELETE CASCADE
);

-- Sync conflicts table (for conflict resolution)
CREATE TABLE IF NOT EXISTS sync_conflicts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id VARCHAR(255) NOT NULL,
    table_name VARCHAR(255),
    record_id VARCHAR(255),
    
    -- Conflict details
    conflict_type VARCHAR(50) NOT NULL, -- schema_change, data_conflict, duplicate_key
    conflict_description TEXT,
    
    -- Conflict data
    local_data JSONB,
    remote_data JSONB,
    resolved_data JSONB,
    
    -- Resolution
    resolution_status VARCHAR(20) DEFAULT 'pending', -- pending, resolved, ignored
    resolution_method VARCHAR(50), -- manual, auto_merge, prefer_local, prefer_remote
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (source_id) REFERENCES data_source_configs(source_id) ON DELETE CASCADE
);

-- ETL pipeline runs table
CREATE TABLE IF NOT EXISTS etl_pipeline_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_type VARCHAR(20) NOT NULL DEFAULT 'scheduled', -- scheduled, manual, triggered
    
    -- Run details
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds REAL,
    
    -- Status
    status VARCHAR(20) DEFAULT 'running', -- running, completed, failed, cancelled
    
    -- Statistics
    sources_total INTEGER DEFAULT 0,
    sources_successful INTEGER DEFAULT 0,
    sources_failed INTEGER DEFAULT 0,
    
    records_processed INTEGER DEFAULT 0,
    records_indexed INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    
    -- Configuration
    config JSONB DEFAULT '{}',
    
    -- Error tracking
    errors JSONB DEFAULT '[]',
    
    -- Metadata
    triggered_by VARCHAR(255),
    notes TEXT
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_ingestion_log_source ON ingestion_log(source_type, source_name);
CREATE INDEX IF NOT EXISTS idx_ingestion_log_status ON ingestion_log(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_log_sync_ts ON ingestion_log(sync_ts DESC);
CREATE INDEX IF NOT EXISTS idx_ingestion_log_duration ON ingestion_log(duration_ms);

CREATE INDEX IF NOT EXISTS idx_data_source_configs_type ON data_source_configs(source_type);
CREATE INDEX IF NOT EXISTS idx_data_source_configs_enabled ON data_source_configs(enabled);
CREATE INDEX IF NOT EXISTS idx_data_source_configs_health ON data_source_configs(health_status);

CREATE INDEX IF NOT EXISTS idx_data_source_schemas_source ON data_source_schemas(source_id);
CREATE INDEX IF NOT EXISTS idx_data_source_schemas_table ON data_source_schemas(table_name);
CREATE INDEX IF NOT EXISTS idx_data_source_schemas_discovered ON data_source_schemas(discovered_at DESC);

CREATE INDEX IF NOT EXISTS idx_sync_schedules_source ON sync_schedules(source_id);
CREATE INDEX IF NOT EXISTS idx_sync_schedules_enabled ON sync_schedules(enabled);
CREATE INDEX IF NOT EXISTS idx_sync_schedules_next_run ON sync_schedules(next_run);

CREATE INDEX IF NOT EXISTS idx_sync_conflicts_source ON sync_conflicts(source_id);
CREATE INDEX IF NOT EXISTS idx_sync_conflicts_status ON sync_conflicts(resolution_status);
CREATE INDEX IF NOT EXISTS idx_sync_conflicts_created ON sync_conflicts(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_etl_pipeline_runs_started ON etl_pipeline_runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_etl_pipeline_runs_status ON etl_pipeline_runs(status);

-- Create GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_ingestion_log_metadata_gin ON ingestion_log USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_data_source_configs_connection_gin ON data_source_configs USING GIN (connection_config);
CREATE INDEX IF NOT EXISTS idx_data_source_schemas_columns_gin ON data_source_schemas USING GIN (columns);

-- Create updated_at trigger function if not exists
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
DROP TRIGGER IF EXISTS update_ingestion_log_updated_at ON ingestion_log;
CREATE TRIGGER update_ingestion_log_updated_at 
    BEFORE UPDATE ON ingestion_log 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_data_source_configs_updated_at ON data_source_configs;
CREATE TRIGGER update_data_source_configs_updated_at 
    BEFORE UPDATE ON data_source_configs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_sync_schedules_updated_at ON sync_schedules;
CREATE TRIGGER update_sync_schedules_updated_at 
    BEFORE UPDATE ON sync_schedules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default data source configurations
INSERT INTO data_source_configs (source_id, source_type, source_name, connection_config, sync_config, description, tags) VALUES
    ('ydb_production', 'ydb', 'production', 
     '{"endpoint": "grpcs://ydb.example.com:2135", "database": "/production/database", "auth_method": "metadata"}',
     '{"sync_mode": "incremental", "batch_size": 1000, "table_filter": ""}',
     'Production YDB instance', 
     ARRAY['production', 'ydb', 'primary']),
     
    ('clickhouse_analytics', 'clickhouse', 'analytics',
     '{"host": "clickhouse.example.com", "port": 8123, "database": "analytics", "username": "default", "secure": true}',
     '{"sync_mode": "incremental", "batch_size": 10000, "table_filter": "events_,user_"}',
     'Main analytics ClickHouse cluster',
     ARRAY['analytics', 'clickhouse', 'events']),
     
    ('confluence_main', 'confluence', 'main',
     '{"base_url": "https://confluence.example.com", "username": "", "token": ""}',
     '{"sync_mode": "incremental", "batch_size": 50, "space_filter": "TECH,DOC,API"}',
     'Main Confluence instance',
     ARRAY['confluence', 'documentation']),
     
    ('gitlab_main', 'gitlab', 'main',
     '{"base_url": "https://gitlab.example.com", "token": ""}',
     '{"sync_mode": "incremental", "batch_size": 100, "project_filter": "group/project1,group/project2"}',
     'Main GitLab instance',
     ARRAY['gitlab', 'code', 'issues']),
     
    ('local_files_bootstrap', 'local_files', 'bootstrap',
     '{"path": "./local/bootstrap", "include_extensions": ".md,.txt,.pdf,.docx"}',
     '{"sync_mode": "full", "batch_size": 50}',
     'Local bootstrap files',
     ARRAY['local', 'files', 'bootstrap'])
ON CONFLICT (source_id) DO NOTHING;

-- Create views for common queries
CREATE OR REPLACE VIEW active_data_sources AS
SELECT 
    source_id,
    source_type,
    source_name,
    enabled,
    health_status,
    last_health_check,
    description,
    tags,
    created_at,
    updated_at
FROM data_source_configs 
WHERE enabled = TRUE;

CREATE OR REPLACE VIEW sync_summary AS
SELECT 
    il.source_type,
    il.source_name,
    COUNT(*) as total_syncs,
    SUM(CASE WHEN il.status = 'completed' THEN 1 ELSE 0 END) as successful_syncs,
    SUM(CASE WHEN il.status = 'failed' THEN 1 ELSE 0 END) as failed_syncs,
    AVG(il.duration_ms) as avg_duration_ms,
    SUM(il.rowcount) as total_records,
    MAX(il.sync_ts) as last_sync,
    AVG(CASE WHEN il.data_quality_score IS NOT NULL THEN il.data_quality_score END) as avg_quality_score
FROM ingestion_log il
WHERE il.sync_ts >= NOW() - INTERVAL '30 days'
GROUP BY il.source_type, il.source_name;

CREATE OR REPLACE VIEW recent_sync_failures AS
SELECT 
    il.source_type,
    il.source_name,
    il.sync_ts,
    il.error_message,
    il.duration_ms,
    il.retry_count
FROM ingestion_log il
WHERE il.status = 'failed' 
    AND il.sync_ts >= NOW() - INTERVAL '7 days'
ORDER BY il.sync_ts DESC;

-- Create function for cleanup old records
CREATE OR REPLACE FUNCTION cleanup_old_ingestion_logs(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM ingestion_log 
    WHERE sync_ts < NOW() - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Also clean up old conflicts
    DELETE FROM sync_conflicts 
    WHERE created_at < NOW() - INTERVAL '1 day' * (days_to_keep * 2)
        AND resolution_status = 'resolved';
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function for health check summary
CREATE OR REPLACE FUNCTION get_etl_health_summary()
RETURNS TABLE(
    total_sources INTEGER,
    healthy_sources INTEGER,
    unhealthy_sources INTEGER,
    unknown_sources INTEGER,
    recent_failures INTEGER,
    avg_sync_duration_minutes REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*)::INTEGER FROM data_source_configs WHERE enabled = TRUE) as total_sources,
        (SELECT COUNT(*)::INTEGER FROM data_source_configs WHERE enabled = TRUE AND health_status = 'healthy') as healthy_sources,
        (SELECT COUNT(*)::INTEGER FROM data_source_configs WHERE enabled = TRUE AND health_status = 'unhealthy') as unhealthy_sources,
        (SELECT COUNT(*)::INTEGER FROM data_source_configs WHERE enabled = TRUE AND health_status = 'unknown') as unknown_sources,
        (SELECT COUNT(*)::INTEGER FROM ingestion_log WHERE status = 'failed' AND sync_ts >= NOW() - INTERVAL '24 hours') as recent_failures,
        (SELECT AVG(duration_ms / 1000.0 / 60.0)::REAL FROM ingestion_log WHERE status = 'completed' AND sync_ts >= NOW() - INTERVAL '24 hours') as avg_sync_duration_minutes;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your environment)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ai_assistant_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ai_assistant_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO ai_assistant_user;

-- Create maintenance schedule (example using pg_cron if available)
-- SELECT cron.schedule('cleanup-etl-logs', '0 2 * * *', 'SELECT cleanup_old_ingestion_logs(30);');

COMMENT ON TABLE ingestion_log IS 'Enhanced logging for ETL pipeline operations';
COMMENT ON TABLE data_source_configs IS 'Configuration and metadata for data sources';
COMMENT ON TABLE data_source_schemas IS 'Schema tracking and change detection for data sources';
COMMENT ON TABLE sync_schedules IS 'Scheduling configuration for data source synchronization';
COMMENT ON TABLE sync_conflicts IS 'Conflict tracking and resolution for data synchronization';
COMMENT ON TABLE etl_pipeline_runs IS 'High-level ETL pipeline execution tracking'; 