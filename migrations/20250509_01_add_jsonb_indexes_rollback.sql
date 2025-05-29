-- Rollback for Migration: add_jsonb_indexes
-- Version: 20250509_01
-- Created: 2025-05-09T19:32:52.680359
-- Description: Remove JSONB indexes added in the migration

-- Drop GIN indexes for JSONB columns
DROP INDEX IF EXISTS idx_accommodations_data_gin;
DROP INDEX IF EXISTS idx_analytics_event_data_gin;
DROP INDEX IF EXISTS idx_attractions_data_gin;
DROP INDEX IF EXISTS idx_sessions_data_gin;

-- Drop expression indexes for specific JSONB fields
DROP INDEX IF EXISTS idx_regions_name_ar;
DROP INDEX IF EXISTS idx_regions_name_en;
DROP INDEX IF EXISTS idx_restaurants_data_name;
DROP INDEX IF EXISTS idx_restaurants_data_description;

-- Drop expression indexes for multilingual fields
DROP INDEX IF EXISTS idx_cities_name_en;
DROP INDEX IF EXISTS idx_cities_name_ar;
DROP INDEX IF EXISTS idx_attractions_name_en;
DROP INDEX IF EXISTS idx_attractions_name_ar;
DROP INDEX IF EXISTS idx_accommodations_name_en;
DROP INDEX IF EXISTS idx_accommodations_name_ar;

