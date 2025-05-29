-- Migration: Add Foreign Key Columns
-- Date: 2024-06-11
-- Phase 4.2 of the database migration plan

-- 1. Add foreign key columns to attractions table
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS city_id TEXT;
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS region_id TEXT;
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS type_id TEXT;

-- 2. Add foreign key columns to accommodations table
ALTER TABLE accommodations ADD COLUMN IF NOT EXISTS city_id TEXT;
ALTER TABLE accommodations ADD COLUMN IF NOT EXISTS region_id TEXT;
ALTER TABLE accommodations ADD COLUMN IF NOT EXISTS type_id TEXT;

-- 3. Create indexes on new foreign key columns
-- Attractions
CREATE INDEX IF NOT EXISTS idx_attractions_city_id ON attractions(city_id);
CREATE INDEX IF NOT EXISTS idx_attractions_region_id ON attractions(region_id);
CREATE INDEX IF NOT EXISTS idx_attractions_type_id ON attractions(type_id);

-- Accommodations
CREATE INDEX IF NOT EXISTS idx_accommodations_city_id ON accommodations(city_id);
CREATE INDEX IF NOT EXISTS idx_accommodations_region_id ON accommodations(region_id);
CREATE INDEX IF NOT EXISTS idx_accommodations_type_id ON accommodations(type_id);

-- Cities (region_id already exists, just create index if it doesn't exist)
CREATE INDEX IF NOT EXISTS idx_cities_region_id ON cities(region_id);

-- 4. Verify foreign key columns exist
-- This section contains queries that can be run manually to verify the migration
-- They are commented out to prevent them from being executed during migration

/*
-- Verify foreign key columns exist
SELECT table_name, column_name 
FROM information_schema.columns 
WHERE table_name IN ('attractions', 'accommodations', 'cities') 
AND column_name IN ('city_id', 'region_id', 'type_id');

-- Verify indexes exist
SELECT tablename, indexname 
FROM pg_indexes 
WHERE tablename IN ('attractions', 'accommodations', 'cities') 
AND indexname LIKE 'idx_%_id';
*/
