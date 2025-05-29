-- Migration: Migrate data from text fields to JSONB
-- Date: 2024-06-10
-- Phase 3.2 of the database migration plan

-- 1. Add missing JSONB columns to cities table
ALTER TABLE cities ADD COLUMN IF NOT EXISTS name JSONB;
ALTER TABLE cities ADD COLUMN IF NOT EXISTS description JSONB;

-- 2. Create GIN indexes for JSONB columns if they don't exist
CREATE INDEX IF NOT EXISTS idx_cities_name_jsonb ON cities USING gin(name jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_cities_description_jsonb ON cities USING gin(description jsonb_path_ops);

-- 3. Migrate data from text fields to JSONB columns
-- Attractions
UPDATE attractions SET name = jsonb_build_object(
    'en', name_en,
    'ar', name_ar
)
WHERE (name IS NULL OR jsonb_typeof(name) = 'null')
  AND (name_en IS NOT NULL OR name_ar IS NOT NULL);

UPDATE attractions SET description = jsonb_build_object(
    'en', description_en,
    'ar', description_ar
)
WHERE (description IS NULL OR jsonb_typeof(description) = 'null')
  AND (description_en IS NOT NULL OR description_ar IS NOT NULL);

-- Accommodations
UPDATE accommodations SET name = jsonb_build_object(
    'en', name_en,
    'ar', name_ar
)
WHERE (name IS NULL OR jsonb_typeof(name) = 'null')
  AND (name_en IS NOT NULL OR name_ar IS NOT NULL);

UPDATE accommodations SET description = jsonb_build_object(
    'en', description_en,
    'ar', description_ar
)
WHERE (description IS NULL OR jsonb_typeof(description) = 'null')
  AND (description_en IS NOT NULL OR description_ar IS NOT NULL);

-- Cities
UPDATE cities SET name = jsonb_build_object(
    'en', name_en,
    'ar', name_ar
)
WHERE (name IS NULL OR jsonb_typeof(name) = 'null')
  AND (name_en IS NOT NULL OR name_ar IS NOT NULL);

-- 4. Fix reference integrity issues
-- Fix the attraction type for Bibliotheca Alexandrina
UPDATE attractions
SET type = 'cultural_center'
WHERE id = 'bibliotheca_alexandrina' AND type = 'cultural';

-- Fix the accommodation types
UPDATE accommodations
SET type = 'luxury_hotel'
WHERE type = 'luxury';

-- Add missing types to lookup tables if they don't exist
INSERT INTO attraction_types (type) VALUES ('cultural_center') ON CONFLICT DO NOTHING;
INSERT INTO accommodation_types (type) VALUES ('luxury_hotel') ON CONFLICT DO NOTHING;

-- 5. Verify migration
-- This section contains queries that can be run manually to verify the migration
-- They are commented out to prevent them from being executed during migration

/*
-- Verify JSONB columns are populated
SELECT 'attractions' as table_name, COUNT(*) as total_rows, 
       COUNT(name) as rows_with_name_jsonb, 
       COUNT(description) as rows_with_description_jsonb
FROM attractions
UNION ALL
SELECT 'accommodations' as table_name, COUNT(*) as total_rows, 
       COUNT(name) as rows_with_name_jsonb, 
       COUNT(description) as rows_with_description_jsonb
FROM accommodations
UNION ALL
SELECT 'cities' as table_name, COUNT(*) as total_rows, 
       COUNT(name) as rows_with_name_jsonb
FROM cities;

-- Verify reference integrity issues are fixed
SELECT a.id, a.type 
FROM attractions a 
LEFT JOIN attraction_types t ON a.type = t.type 
WHERE t.type IS NULL;

SELECT a.id, a.type 
FROM accommodations a 
LEFT JOIN accommodation_types t ON a.type = t.type 
WHERE t.type IS NULL;
*/
