-- Migration: Add Missing GIN Indexes for JSONB Columns
-- Date: 2024-06-14
-- Addresses the missing GIN indexes for JSONB columns in attractions and accommodations tables

-- 1. Add GIN indexes for JSONB columns in attractions table
CREATE INDEX IF NOT EXISTS idx_attractions_name_jsonb ON attractions USING gin(name jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_attractions_description_jsonb ON attractions USING gin(description jsonb_path_ops);

-- 2. Add GIN indexes for JSONB columns in accommodations table
CREATE INDEX IF NOT EXISTS idx_accommodations_name_jsonb ON accommodations USING gin(name jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_accommodations_description_jsonb ON accommodations USING gin(description jsonb_path_ops);

-- 3. Verify indexes exist
-- This section contains queries that can be run manually to verify the migration
-- They are commented out to prevent them from being executed during migration

/*
-- Verify GIN indexes exist for JSONB columns
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('attractions', 'accommodations', 'cities')
AND indexname LIKE 'idx_%_jsonb';
*/
