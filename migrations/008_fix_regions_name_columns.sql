-- Migration: 008_fix_regions_name_columns.sql
-- Purpose: Fix the name_en and name_ar columns in the regions table by migrating to JSONB name column

-- Begin transaction
BEGIN;

-- 1. Migrate data from text columns to JSONB column
UPDATE regions
SET name = CASE
    WHEN name IS NULL THEN jsonb_build_object('en', name_en, 'ar', name_ar)
    WHEN NOT name ? 'en' AND name_en IS NOT NULL THEN name || jsonb_build_object('en', name_en)
    WHEN NOT name ? 'ar' AND name_ar IS NOT NULL THEN name || jsonb_build_object('ar', name_ar)
    ELSE name
END
WHERE name_en IS NOT NULL OR name_ar IS NOT NULL;

-- 2. Verify data migration
DO $$
DECLARE
    missing_count bigint;
BEGIN
    SELECT COUNT(*) INTO missing_count
    FROM regions
    WHERE (name_en IS NOT NULL AND (name IS NULL OR name->>'en' IS NULL OR name->>'en' <> name_en))
       OR (name_ar IS NOT NULL AND (name IS NULL OR name->>'ar' IS NULL OR name->>'ar' <> name_ar));
    
    IF missing_count > 0 THEN
        RAISE EXCEPTION 'Migration verification failed: % records have inconsistencies', missing_count;
    END IF;
END $$;

-- 3. Drop redundant columns
ALTER TABLE regions DROP COLUMN name_en;
ALTER TABLE regions DROP COLUMN name_ar;

-- 4. Add comment
COMMENT ON COLUMN regions.name IS 'Multilingual name in JSONB format with language codes as keys (e.g., {"en": "English Name", "ar": "Arabic Name"})';

-- Commit transaction
COMMIT;
