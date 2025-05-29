-- Migration: 013_standardize_timestamp_data_types.sql
-- Purpose: Standardize timestamp data types to timestamp with time zone

-- Begin transaction
BEGIN;

-- 1. Fix feedback.created_at data type
ALTER TABLE feedback ALTER COLUMN created_at TYPE timestamp with time zone;

-- 2. Fix test_attractions timestamp columns
ALTER TABLE test_attractions ALTER COLUMN created_at TYPE timestamp with time zone;
ALTER TABLE test_attractions ALTER COLUMN updated_at TYPE timestamp with time zone;

-- 3. Fix test_restaurants timestamp columns
ALTER TABLE test_restaurants ALTER COLUMN created_at TYPE timestamp with time zone;
ALTER TABLE test_restaurants ALTER COLUMN updated_at TYPE timestamp with time zone;

-- 4. Fix perf_attractions timestamp columns
ALTER TABLE perf_attractions ALTER COLUMN created_at TYPE timestamp with time zone;
ALTER TABLE perf_attractions ALTER COLUMN updated_at TYPE timestamp with time zone;

-- Commit transaction
COMMIT;
