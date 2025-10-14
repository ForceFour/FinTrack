-- =====================================================
-- Migration: Add Duplicate Tracking to Prediction Results
-- Description: Add fields to track duplicate transactions detected during processing
-- Created: 2025-10-14
-- =====================================================

-- Add duplicate tracking columns
ALTER TABLE prediction_results
ADD COLUMN IF NOT EXISTS duplicates_detected INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS duplicates_skipped INTEGER DEFAULT 0;

-- Add comments for documentation
COMMENT ON COLUMN prediction_results.duplicates_detected IS 'Number of duplicate transactions detected during processing';
COMMENT ON COLUMN prediction_results.duplicates_skipped IS 'Number of duplicate transactions skipped during processing';

-- Add index for querying duplicate statistics
CREATE INDEX IF NOT EXISTS idx_prediction_results_duplicates 
ON prediction_results(duplicates_detected) 
WHERE duplicates_detected > 0;

-- Add a view for duplicate statistics
CREATE OR REPLACE VIEW prediction_duplicate_stats AS
SELECT 
    user_id,
    COUNT(*) as total_workflows,
    SUM(duplicates_detected) as total_duplicates_detected,
    SUM(duplicates_skipped) as total_duplicates_skipped,
    AVG(duplicates_detected) as avg_duplicates_per_workflow,
    MAX(duplicates_detected) as max_duplicates_in_workflow
FROM prediction_results
WHERE status = 'completed'
GROUP BY user_id;

-- Grant access to the view
GRANT SELECT ON prediction_duplicate_stats TO authenticated;

COMMENT ON VIEW prediction_duplicate_stats IS 'Statistics on duplicate transactions detected across all workflows per user';
