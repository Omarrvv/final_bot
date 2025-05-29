-- Migration: 009_fix_remaining_timestamp_columns.sql
-- Purpose: Fix remaining tables without standardized timestamp columns

-- Begin transaction
BEGIN;

-- 1. Add updated_at column to vector_search_metrics
ALTER TABLE vector_search_metrics ADD COLUMN updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP;

-- 2. Add created_at and updated_at columns to vector_indexes
ALTER TABLE vector_indexes ADD COLUMN created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE vector_indexes ADD COLUMN updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP;

-- 3. Add update_timestamp trigger to vector_search_metrics and vector_indexes
CREATE OR REPLACE FUNCTION update_timestamp() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_timestamp
BEFORE UPDATE ON vector_search_metrics
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_timestamp
BEFORE UPDATE ON vector_indexes
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- 4. Add comments to timestamp columns
COMMENT ON COLUMN vector_search_metrics.created_at IS 'Timestamp when the record was created';
COMMENT ON COLUMN vector_search_metrics.updated_at IS 'Timestamp when the record was last updated';
COMMENT ON COLUMN vector_indexes.created_at IS 'Timestamp when the record was created';
COMMENT ON COLUMN vector_indexes.updated_at IS 'Timestamp when the record was last updated';

-- Note: We're not adding timestamp columns to schema_migrations as it's a system table
-- that typically doesn't need these columns

-- Commit transaction
COMMIT;
