-- =====================================================
-- Migration: Add source_name to prediction_results
-- Description: Add column to store file name or chat title
-- Created: 2025-10-20
-- =====================================================

-- Add source_name column to prediction_results table
ALTER TABLE prediction_results
ADD COLUMN IF NOT EXISTS source_name VARCHAR(255);

-- Add comment for documentation
COMMENT ON COLUMN prediction_results.source_name IS 'Name of the source (filename for uploads, title for chats)';

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_prediction_results_source_name ON prediction_results(source_name);

-- Migration complete
