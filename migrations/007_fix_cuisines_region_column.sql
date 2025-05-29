-- Migration: 007_fix_cuisines_region_column.sql
-- Purpose: Fix the region column in the cuisines table by migrating to region_id

-- Begin transaction
BEGIN;

-- 1. Create helper function to find region_id from region name
CREATE OR REPLACE FUNCTION find_region_id_by_name(p_region_name text) RETURNS text AS $$
DECLARE
    v_region_id text;
BEGIN
    -- First try exact match on name->>'en'
    SELECT id INTO v_region_id
    FROM regions
    WHERE name->>'en' = p_region_name
    LIMIT 1;
    
    -- If not found, try exact match on name->>'ar'
    IF v_region_id IS NULL THEN
        SELECT id INTO v_region_id
        FROM regions
        WHERE name->>'ar' = p_region_name
        LIMIT 1;
    END IF;
    
    -- If still not found, try fuzzy match
    IF v_region_id IS NULL THEN
        SELECT id INTO v_region_id
        FROM regions
        WHERE name->>'en' ILIKE '%' || p_region_name || '%'
        ORDER BY similarity(name->>'en', p_region_name) DESC
        LIMIT 1;
    END IF;
    
    RETURN v_region_id;
END;
$$ LANGUAGE plpgsql;

-- 2. Add region_id column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'cuisines'
        AND column_name = 'region_id'
    ) THEN
        ALTER TABLE cuisines ADD COLUMN region_id text;
    END IF;
END $$;

-- 3. Migrate data from region text column to region_id
UPDATE cuisines
SET region_id = find_region_id_by_name(region)
WHERE region_id IS NULL AND region IS NOT NULL;

-- 4. Verify migration
DO $$
DECLARE
    missing_count bigint;
BEGIN
    SELECT COUNT(*) INTO missing_count
    FROM cuisines
    WHERE region_id IS NULL AND region IS NOT NULL;
    
    IF missing_count > 0 THEN
        RAISE WARNING 'Some cuisines records could not be migrated from region to region_id: % records', missing_count;
    END IF;
END $$;

-- 5. Drop the redundant column
ALTER TABLE cuisines DROP COLUMN region;

-- 6. Add comment
COMMENT ON COLUMN cuisines.region_id IS 'Foreign key to regions table. Join with regions to get region name and other details.';

-- 7. Add foreign key constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND table_name = 'cuisines'
        AND constraint_name = 'cuisines_region_id_fkey'
    ) THEN
        ALTER TABLE cuisines
        ADD CONSTRAINT cuisines_region_id_fkey
        FOREIGN KEY (region_id) REFERENCES regions(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL;
    END IF;
END $$;

-- Clean up temporary objects
DROP FUNCTION find_region_id_by_name(text);

-- Commit transaction
COMMIT;
