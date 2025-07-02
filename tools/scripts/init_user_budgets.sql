-- User Budget System - PostgreSQL Schema
-- Task 1.2: Cost Control for AI Assistant MVP

-- Create user_budgets table for tracking user spending limits
CREATE TABLE IF NOT EXISTS user_budgets (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    total_budget DECIMAL(10,4) NOT NULL DEFAULT 100.0000,
    used_budget DECIMAL(10,4) NOT NULL DEFAULT 0.0000,
    budget_period VARCHAR(20) NOT NULL DEFAULT 'monthly', -- monthly, weekly, daily
    budget_start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    budget_end_date TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '1 month'),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_user_active_budget UNIQUE (user_id, is_active),
    CONSTRAINT positive_budget_amounts CHECK (total_budget >= 0 AND used_budget >= 0),
    CONSTRAINT budget_not_negative CHECK (used_budget <= total_budget * 1.1), -- Allow 10% overage
    CONSTRAINT valid_budget_period CHECK (budget_period IN ('daily', 'weekly', 'monthly', 'yearly'))
);

-- Create LLM API usage tracking table
CREATE TABLE IF NOT EXISTS llm_usage_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    request_id VARCHAR(255) NOT NULL,
    service_provider VARCHAR(50) NOT NULL, -- openai, anthropic, ollama
    model_name VARCHAR(100) NOT NULL,
    endpoint_name VARCHAR(100) NOT NULL, -- search, generate, documentation
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd DECIMAL(10,6) NOT NULL DEFAULT 0.000000,
    request_duration_ms INTEGER NOT NULL DEFAULT 0,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,
    request_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexing for performance
    INDEX idx_user_timestamp (user_id, request_timestamp),
    INDEX idx_cost_timestamp (cost_usd, request_timestamp),
    INDEX idx_provider_model (service_provider, model_name)
);

-- Create budget alerts table
CREATE TABLE IF NOT EXISTS budget_alerts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    alert_type VARCHAR(50) NOT NULL, -- warning_80, warning_90, budget_exceeded, quota_reached
    threshold_percentage INTEGER NOT NULL,
    current_usage DECIMAL(10,4) NOT NULL,
    budget_limit DECIMAL(10,4) NOT NULL,
    alert_sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    
    INDEX idx_user_alerts (user_id, alert_sent_at)
);

-- Create cost tracking summary view for easy reporting
CREATE OR REPLACE VIEW user_cost_summary AS
SELECT 
    ub.user_id,
    ub.email,
    ub.total_budget,
    ub.used_budget,
    ub.budget_period,
    ub.budget_start_date,
    ub.budget_end_date,
    (ub.used_budget / ub.total_budget * 100)::DECIMAL(5,2) AS usage_percentage,
    (ub.total_budget - ub.used_budget) AS remaining_budget,
    CASE 
        WHEN ub.used_budget >= ub.total_budget THEN 'EXCEEDED'
        WHEN ub.used_budget >= ub.total_budget * 0.95 THEN 'CRITICAL'
        WHEN ub.used_budget >= ub.total_budget * 0.80 THEN 'WARNING'
        ELSE 'ACTIVE'
    END AS budget_status,
    COUNT(ul.id) AS total_requests,
    COALESCE(SUM(ul.cost_usd), 0) AS calculated_cost,
    AVG(ul.cost_usd) AS avg_request_cost,
    MAX(ul.request_timestamp) AS last_request_at
FROM user_budgets ub
LEFT JOIN llm_usage_logs ul ON ub.user_id = ul.user_id 
    AND ul.request_timestamp >= ub.budget_start_date 
    AND ul.request_timestamp <= ub.budget_end_date
WHERE ub.is_active = TRUE
GROUP BY ub.user_id, ub.email, ub.total_budget, ub.used_budget, 
         ub.budget_period, ub.budget_start_date, ub.budget_end_date;

-- Insert initial budgets for existing demo users
INSERT INTO user_budgets (user_id, email, total_budget, used_budget, budget_period) 
VALUES 
    ('admin_001', 'admin@example.com', 1000.0000, 0.0000, 'monthly'),
    ('user_001', 'user@example.com', 100.0000, 0.0000, 'monthly')
ON CONFLICT (user_id, is_active) DO NOTHING;

-- Create function to update user budget usage
CREATE OR REPLACE FUNCTION update_user_budget_usage(
    p_user_id VARCHAR(255),
    p_cost_amount DECIMAL(10,6)
) RETURNS BOOLEAN AS $$
DECLARE
    current_used DECIMAL(10,4);
    budget_limit DECIMAL(10,4);
    new_used DECIMAL(10,4);
BEGIN
    -- Get current budget info
    SELECT used_budget, total_budget INTO current_used, budget_limit
    FROM user_budgets 
    WHERE user_id = p_user_id AND is_active = TRUE;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'No active budget found for user %', p_user_id;
    END IF;
    
    new_used := current_used + p_cost_amount;
    
    -- Update the budget
    UPDATE user_budgets 
    SET used_budget = new_used,
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id AND is_active = TRUE;
    
    -- Check if alert needed
    IF new_used >= budget_limit * 0.8 AND current_used < budget_limit * 0.8 THEN
        INSERT INTO budget_alerts (user_id, email, alert_type, threshold_percentage, current_usage, budget_limit)
        SELECT user_id, email, 'warning_80', 80, new_used, budget_limit
        FROM user_budgets WHERE user_id = p_user_id AND is_active = TRUE;
    END IF;
    
    IF new_used >= budget_limit * 0.95 AND current_used < budget_limit * 0.95 THEN
        INSERT INTO budget_alerts (user_id, email, alert_type, threshold_percentage, current_usage, budget_limit)
        SELECT user_id, email, 'warning_95', 95, new_used, budget_limit
        FROM user_budgets WHERE user_id = p_user_id AND is_active = TRUE;
    END IF;
    
    IF new_used >= budget_limit AND current_used < budget_limit THEN
        INSERT INTO budget_alerts (user_id, email, alert_type, threshold_percentage, current_usage, budget_limit)
        SELECT user_id, email, 'budget_exceeded', 100, new_used, budget_limit
        FROM user_budgets WHERE user_id = p_user_id AND is_active = TRUE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_budgets_user_id ON user_budgets(user_id);
CREATE INDEX IF NOT EXISTS idx_user_budgets_active ON user_budgets(is_active, user_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_user_cost ON llm_usage_logs(user_id, cost_usd);
CREATE INDEX IF NOT EXISTS idx_llm_usage_timestamp ON llm_usage_logs(request_timestamp);

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE ON user_budgets TO ai_assistant_user;
-- GRANT SELECT, INSERT ON llm_usage_logs TO ai_assistant_user;  
-- GRANT SELECT ON user_cost_summary TO ai_assistant_user;

COMMIT; 