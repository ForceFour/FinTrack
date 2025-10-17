-- =====================================================
-- Migration: Create Prediction Results Table
-- Description: Store complete agentic pipeline results
-- Created: 2025-10-14
-- =====================================================

-- Create enum types for better type safety
CREATE TYPE prediction_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'partial');
CREATE TYPE workflow_mode AS ENUM ('full_pipeline', 'quick_classification', 'ingestion_only', 'validation_only', 'background_processing');
CREATE TYPE processing_stage AS ENUM ('initial', 'nl_processing', 'ingestion', 'ner_extraction', 'classification', 'pattern_analysis', 'suggestion', 'safety_guard', 'validation', 'completed', 'error');

-- =====================================================
-- Main Prediction Results Table
-- =====================================================
CREATE TABLE IF NOT EXISTS prediction_results (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id VARCHAR(100) UNIQUE NOT NULL,

    -- Foreign keys
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    transaction_id UUID REFERENCES transactions(id) ON DELETE SET NULL,

    -- Workflow metadata
    workflow_mode workflow_mode NOT NULL DEFAULT 'full_pipeline',
    status prediction_status NOT NULL DEFAULT 'pending',
    current_stage processing_stage DEFAULT 'initial',

    -- Input data
    user_input TEXT,
    input_type VARCHAR(50), -- 'structured', 'unstructured', 'conversational'
    raw_transaction_count INTEGER DEFAULT 0,

    -- Classification results
    predicted_category VARCHAR(100),
    category_confidence DECIMAL(5,4), -- 0.0000 to 1.0000
    category_probabilities JSONB, -- {"food_dining": 0.85, "groceries": 0.10, ...}
    transaction_type VARCHAR(20), -- 'income', 'expense', 'transfer'
    transaction_type_confidence DECIMAL(5,4),

    -- Merchant extraction (NER) results
    merchant_name VARCHAR(255),
    merchant_standardized VARCHAR(255),
    merchant_category VARCHAR(100),
    is_merchant_known BOOLEAN DEFAULT FALSE,
    merchant_confidence DECIMAL(5,4),
    extracted_entities JSONB, -- All NER entities extracted

    -- Pattern analysis results
    spending_patterns JSONB, -- Pattern analyzer output
    pattern_insights JSONB, -- Array of insight objects
    recurring_transactions JSONB, -- Detected recurring patterns
    anomalies_detected JSONB, -- Unusual spending patterns
    pattern_confidence DECIMAL(5,4),

    -- Suggestions and recommendations
    budget_recommendations JSONB, -- Array of budget suggestions
    spending_suggestions JSONB, -- Array of spending optimization tips
    savings_opportunities JSONB, -- Detected savings opportunities
    suggestion_confidence DECIMAL(5,4),
    potential_monthly_savings DECIMAL(10,2),

    -- Security and safety results
    security_alerts JSONB, -- Array of security alert objects
    risk_assessment JSONB, -- Overall risk assessment
    fraud_score DECIMAL(5,4), -- 0.0000 to 1.0000
    anomaly_score DECIMAL(5,4),
    safety_confidence DECIMAL(5,4),
    requires_human_review BOOLEAN DEFAULT FALSE,

    -- Validation results
    validation_errors JSONB, -- Array of validation error messages
    data_quality_score DECIMAL(5,4),
    is_valid BOOLEAN DEFAULT TRUE,

    -- Processing metadata
    processing_history JSONB, -- Array of stage-wise processing logs
    confidence_scores JSONB, -- Stage-wise confidence tracking
    error_log JSONB, -- Array of error objects
    retry_count INTEGER DEFAULT 0,

    -- Performance metrics
    total_processing_time DECIMAL(10,3), -- seconds
    stage_timings JSONB, -- Time taken by each agent
    agent_performance JSONB, -- Individual agent metrics

    -- Final processed transaction
    final_transaction JSONB, -- Complete processed transaction object

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_confidence_ranges CHECK (
        (category_confidence IS NULL OR (category_confidence >= 0 AND category_confidence <= 1)) AND
        (transaction_type_confidence IS NULL OR (transaction_type_confidence >= 0 AND transaction_type_confidence <= 1)) AND
        (merchant_confidence IS NULL OR (merchant_confidence >= 0 AND merchant_confidence <= 1)) AND
        (pattern_confidence IS NULL OR (pattern_confidence >= 0 AND pattern_confidence <= 1)) AND
        (suggestion_confidence IS NULL OR (suggestion_confidence >= 0 AND suggestion_confidence <= 1)) AND
        (safety_confidence IS NULL OR (safety_confidence >= 0 AND safety_confidence <= 1)) AND
        (fraud_score IS NULL OR (fraud_score >= 0 AND fraud_score <= 1)) AND
        (anomaly_score IS NULL OR (anomaly_score >= 0 AND anomaly_score <= 1)) AND
        (data_quality_score IS NULL OR (data_quality_score >= 0 AND data_quality_score <= 1))
    ),
    CONSTRAINT valid_timestamps CHECK (
        started_at <= COALESCE(completed_at, NOW())
    )
);

-- =====================================================
-- Indexes for Performance Optimization
-- =====================================================

-- Primary lookups
CREATE INDEX idx_prediction_results_workflow_id ON prediction_results(workflow_id);
CREATE INDEX idx_prediction_results_user_id ON prediction_results(user_id);
CREATE INDEX idx_prediction_results_transaction_id ON prediction_results(transaction_id);

-- Status and filtering
CREATE INDEX idx_prediction_results_status ON prediction_results(status);
CREATE INDEX idx_prediction_results_workflow_mode ON prediction_results(workflow_mode);
CREATE INDEX idx_prediction_results_current_stage ON prediction_results(current_stage);

-- Time-based queries
CREATE INDEX idx_prediction_results_created_at ON prediction_results(created_at DESC);
CREATE INDEX idx_prediction_results_started_at ON prediction_results(started_at DESC);
CREATE INDEX idx_prediction_results_completed_at ON prediction_results(completed_at DESC) WHERE completed_at IS NOT NULL;

-- Combined indexes for common query patterns
CREATE INDEX idx_prediction_results_user_status ON prediction_results(user_id, status, created_at DESC);
CREATE INDEX idx_prediction_results_user_completed ON prediction_results(user_id, completed_at DESC) WHERE status = 'completed';

-- JSONB indexes for faster queries on nested data
CREATE INDEX idx_prediction_results_category_probs ON prediction_results USING GIN (category_probabilities);
CREATE INDEX idx_prediction_results_extracted_entities ON prediction_results USING GIN (extracted_entities);
CREATE INDEX idx_prediction_results_pattern_insights ON prediction_results USING GIN (pattern_insights);
CREATE INDEX idx_prediction_results_security_alerts ON prediction_results USING GIN (security_alerts);
CREATE INDEX idx_prediction_results_processing_history ON prediction_results USING GIN (processing_history);

-- =====================================================
-- Row Level Security (RLS)
-- =====================================================

-- Enable RLS
ALTER TABLE prediction_results ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own prediction results
CREATE POLICY "Users can view own prediction results" ON prediction_results
    FOR SELECT
    USING (auth.uid()::text = user_id::text);

-- Policy: Users can insert their own prediction results
CREATE POLICY "Users can insert own prediction results" ON prediction_results
    FOR INSERT
    WITH CHECK (auth.uid()::text = user_id::text);

-- Policy: Users can update their own prediction results
CREATE POLICY "Users can update own prediction results" ON prediction_results
    FOR UPDATE
    USING (auth.uid()::text = user_id::text);

-- Policy: Users can delete their own prediction results
CREATE POLICY "Users can delete own prediction results" ON prediction_results
    FOR DELETE
    USING (auth.uid()::text = user_id::text);

-- =====================================================
-- Triggers and Functions
-- =====================================================

-- Function: Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_prediction_results_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update updated_at on modification
CREATE TRIGGER trigger_update_prediction_results_updated_at
    BEFORE UPDATE ON prediction_results
    FOR EACH ROW
    EXECUTE FUNCTION update_prediction_results_updated_at();

-- Function: Auto-set completed_at when status changes to completed
CREATE OR REPLACE FUNCTION set_prediction_completed_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        NEW.completed_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-set completed_at
CREATE TRIGGER trigger_set_prediction_completed_at
    BEFORE UPDATE ON prediction_results
    FOR EACH ROW
    WHEN (NEW.status IS DISTINCT FROM OLD.status)
    EXECUTE FUNCTION set_prediction_completed_at();

-- Function: Calculate overall confidence score
CREATE OR REPLACE FUNCTION calculate_overall_confidence(pred_result prediction_results)
RETURNS DECIMAL(5,4) AS $$
DECLARE
    confidence_sum DECIMAL(10,4) := 0;
    confidence_count INTEGER := 0;
BEGIN
    -- Add non-null confidence scores
    IF pred_result.category_confidence IS NOT NULL THEN
        confidence_sum := confidence_sum + pred_result.category_confidence;
        confidence_count := confidence_count + 1;
    END IF;

    IF pred_result.transaction_type_confidence IS NOT NULL THEN
        confidence_sum := confidence_sum + pred_result.transaction_type_confidence;
        confidence_count := confidence_count + 1;
    END IF;

    IF pred_result.merchant_confidence IS NOT NULL THEN
        confidence_sum := confidence_sum + pred_result.merchant_confidence;
        confidence_count := confidence_count + 1;
    END IF;

    IF pred_result.pattern_confidence IS NOT NULL THEN
        confidence_sum := confidence_sum + pred_result.pattern_confidence;
        confidence_count := confidence_count + 1;
    END IF;

    IF pred_result.suggestion_confidence IS NOT NULL THEN
        confidence_sum := confidence_sum + pred_result.suggestion_confidence;
        confidence_count := confidence_count + 1;
    END IF;

    IF pred_result.safety_confidence IS NOT NULL THEN
        confidence_sum := confidence_sum + pred_result.safety_confidence;
        confidence_count := confidence_count + 1;
    END IF;

    -- Return average confidence or NULL if no scores available
    IF confidence_count > 0 THEN
        RETURN confidence_sum / confidence_count;
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =====================================================
-- Views for Common Queries
-- =====================================================

-- View: Active prediction workflows
CREATE OR REPLACE VIEW active_prediction_workflows AS
SELECT
    id,
    workflow_id,
    user_id,
    workflow_mode,
    status,
    current_stage,
    raw_transaction_count,
    started_at,
    EXTRACT(EPOCH FROM (NOW() - started_at)) as duration_seconds,
    calculate_overall_confidence(prediction_results.*) as overall_confidence
FROM prediction_results
WHERE status IN ('pending', 'processing')
ORDER BY started_at DESC;

-- View: Completed predictions with summary
CREATE OR REPLACE VIEW completed_predictions_summary AS
SELECT
    id,
    workflow_id,
    user_id,
    workflow_mode,
    predicted_category,
    category_confidence,
    transaction_type,
    merchant_standardized,
    is_merchant_known,
    calculate_overall_confidence(prediction_results.*) as overall_confidence,
    fraud_score,
    anomaly_score,
    requires_human_review,
    total_processing_time,
    completed_at,
    created_at
FROM prediction_results
WHERE status = 'completed'
ORDER BY completed_at DESC;

-- View: Failed predictions for debugging
CREATE OR REPLACE VIEW failed_predictions AS
SELECT
    id,
    workflow_id,
    user_id,
    workflow_mode,
    current_stage,
    error_log,
    retry_count,
    started_at,
    updated_at
FROM prediction_results
WHERE status = 'failed'
ORDER BY updated_at DESC;

-- View: High-risk predictions requiring review
CREATE OR REPLACE VIEW high_risk_predictions AS
SELECT
    id,
    workflow_id,
    user_id,
    predicted_category,
    merchant_name,
    fraud_score,
    anomaly_score,
    security_alerts,
    requires_human_review,
    completed_at
FROM prediction_results
WHERE status = 'completed'
    AND (fraud_score > 0.7 OR anomaly_score > 0.7 OR requires_human_review = TRUE)
ORDER BY fraud_score DESC, anomaly_score DESC;

-- =====================================================
-- Helpful Functions for Analytics
-- =====================================================

-- Function: Get user's prediction statistics
CREATE OR REPLACE FUNCTION get_user_prediction_stats(p_user_id UUID)
RETURNS TABLE(
    total_predictions BIGINT,
    completed_predictions BIGINT,
    failed_predictions BIGINT,
    avg_confidence DECIMAL(5,4),
    avg_processing_time DECIMAL(10,3),
    high_risk_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_predictions,
        COUNT(*) FILTER (WHERE status = 'completed')::BIGINT as completed_predictions,
        COUNT(*) FILTER (WHERE status = 'failed')::BIGINT as failed_predictions,
        AVG(calculate_overall_confidence(prediction_results.*)) as avg_confidence,
        AVG(total_processing_time) as avg_processing_time,
        COUNT(*) FILTER (WHERE fraud_score > 0.7 OR anomaly_score > 0.7)::BIGINT as high_risk_count
    FROM prediction_results
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Get recent predictions for a user
CREATE OR REPLACE FUNCTION get_recent_predictions(
    p_user_id UUID,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE(
    workflow_id VARCHAR(100),
    status prediction_status,
    predicted_category VARCHAR(100),
    category_confidence DECIMAL(5,4),
    merchant_name VARCHAR(255),
    overall_confidence DECIMAL(5,4),
    completed_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pr.workflow_id,
        pr.status,
        pr.predicted_category,
        pr.category_confidence,
        pr.merchant_name,
        calculate_overall_confidence(pr.*) as overall_confidence,
        pr.completed_at
    FROM prediction_results pr
    WHERE pr.user_id = p_user_id
    ORDER BY pr.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- Comments for Documentation
-- =====================================================

COMMENT ON TABLE prediction_results IS 'Stores complete results from the AI agentic pipeline for transaction processing';
COMMENT ON COLUMN prediction_results.workflow_id IS 'Unique identifier for the workflow execution';
COMMENT ON COLUMN prediction_results.workflow_mode IS 'Mode of workflow execution (full_pipeline, quick_classification, etc.)';
COMMENT ON COLUMN prediction_results.category_probabilities IS 'JSONB object containing probability distribution across all categories';
COMMENT ON COLUMN prediction_results.extracted_entities IS 'All entities extracted by NER agent (merchants, locations, dates, etc.)';
COMMENT ON COLUMN prediction_results.pattern_insights IS 'Insights from pattern analysis agent (recurring, spikes, trends)';
COMMENT ON COLUMN prediction_results.security_alerts IS 'Array of security alerts from safety guard agent';
COMMENT ON COLUMN prediction_results.processing_history IS 'Complete log of all processing stages with timestamps';
COMMENT ON COLUMN prediction_results.fraud_score IS 'Risk score for potential fraud (0=safe, 1=high risk)';
COMMENT ON COLUMN prediction_results.requires_human_review IS 'Flag indicating if manual review is recommended';

-- =====================================================
-- Grant Permissions
-- =====================================================

-- Grant usage on custom types
GRANT USAGE ON TYPE prediction_status TO authenticated;
GRANT USAGE ON TYPE workflow_mode TO authenticated;
GRANT USAGE ON TYPE processing_stage TO authenticated;

-- Grant access to functions
GRANT EXECUTE ON FUNCTION calculate_overall_confidence(prediction_results) TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_prediction_stats(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_recent_predictions(UUID, INTEGER) TO authenticated;

-- =====================================================
-- Initial Data / Sample Records (Optional - for testing)
-- =====================================================

-- You can uncomment this section to add sample data for testing
/*
INSERT INTO prediction_results (
    workflow_id,
    user_id,
    workflow_mode,
    status,
    user_input,
    predicted_category,
    category_confidence,
    transaction_type,
    merchant_name,
    merchant_standardized,
    completed_at
) VALUES (
    'sample_workflow_001',
    (SELECT id FROM profiles LIMIT 1),
    'full_pipeline',
    'completed',
    'Spent 150 at Keells Super',
    'groceries',
    0.9500,
    'expense',
    'Keells Super',
    'keells',
    NOW()
);
*/

-- =====================================================
-- Migration Complete
-- =====================================================
