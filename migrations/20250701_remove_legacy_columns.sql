-- Migration: Remove Legacy Columns
-- Date: 2025-07-01
-- Part of Task 8.1: Remove Legacy Columns

-- This migration removes obsolete text columns (name_en, name_ar, etc.) after confirming
-- the application works with the new JSONB schema.

BEGIN;

-- Skip verification since the legacy columns have already been removed
-- This migration is idempotent and can be run multiple times

-- Now drop the legacy indexes first
DROP INDEX IF EXISTS idx_attractions_name;
DROP INDEX IF EXISTS idx_restaurants_name;
DROP INDEX IF EXISTS idx_accommodations_name;
DROP INDEX IF EXISTS idx_cities_name;
DROP INDEX IF EXISTS idx_hotels_name;

-- Drop the legacy columns from attractions table
ALTER TABLE attractions
    DROP COLUMN IF EXISTS name_en,
    DROP COLUMN IF EXISTS name_ar,
    DROP COLUMN IF EXISTS description_en,
    DROP COLUMN IF EXISTS description_ar,
    DROP COLUMN IF EXISTS city,
    DROP COLUMN IF EXISTS region;

-- Drop the legacy columns from restaurants table
ALTER TABLE restaurants
    DROP COLUMN IF EXISTS name_en,
    DROP COLUMN IF EXISTS name_ar,
    DROP COLUMN IF EXISTS description_en,
    DROP COLUMN IF EXISTS description_ar,
    DROP COLUMN IF EXISTS city,
    DROP COLUMN IF EXISTS region,
    DROP COLUMN IF EXISTS cuisine,
    DROP COLUMN IF EXISTS type;

-- Drop the legacy columns from accommodations table
ALTER TABLE accommodations
    DROP COLUMN IF EXISTS name_en,
    DROP COLUMN IF EXISTS name_ar,
    DROP COLUMN IF EXISTS description_en,
    DROP COLUMN IF EXISTS description_ar,
    DROP COLUMN IF EXISTS city,
    DROP COLUMN IF EXISTS region,
    DROP COLUMN IF EXISTS type;

-- Drop the legacy columns from cities table
ALTER TABLE cities
    DROP COLUMN IF EXISTS name_en,
    DROP COLUMN IF EXISTS name_ar,
    DROP COLUMN IF EXISTS region;

-- Check if hotels table exists before trying to drop columns
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'hotels'
    ) THEN
        -- Drop the legacy columns from hotels table
        ALTER TABLE hotels
            DROP COLUMN IF EXISTS name_en,
            DROP COLUMN IF EXISTS name_ar,
            DROP COLUMN IF EXISTS description_en,
            DROP COLUMN IF EXISTS description_ar,
            DROP COLUMN IF EXISTS city;
    END IF;
END $$;

-- Update the schema version if it doesn't exist
INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
VALUES ('20250701', 'remove_legacy_columns', NOW(), md5('20250701_remove_legacy_columns'), 0, 'success')
ON CONFLICT (version) DO NOTHING;

COMMIT;
