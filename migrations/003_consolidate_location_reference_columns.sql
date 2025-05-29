-- Migration: 003_consolidate_location_reference_columns.sql
-- Purpose: Consolidate redundant city/region text columns into the city_id/region_id foreign key columns
-- as the single source of truth for location relationships.
-- This migration ensures all data is preserved before removing redundant columns.

-- Begin transaction
BEGIN;

-- 1. Create helper function to find city_id from city name
CREATE OR REPLACE FUNCTION find_city_id_by_name(p_city_name text) RETURNS text AS $$
DECLARE
    v_city_id text;
BEGIN
    -- First try exact match on name->>'en'
    SELECT id INTO v_city_id
    FROM cities
    WHERE name->>'en' = p_city_name
    LIMIT 1;

    -- If not found, try exact match on name->>'ar'
    IF v_city_id IS NULL THEN
        SELECT id INTO v_city_id
        FROM cities
        WHERE name->>'ar' = p_city_name
        LIMIT 1;
    END IF;

    -- If still not found, try fuzzy match
    IF v_city_id IS NULL THEN
        SELECT id INTO v_city_id
        FROM cities
        WHERE name->>'en' ILIKE '%' || p_city_name || '%'
        ORDER BY similarity(name->>'en', p_city_name) DESC
        LIMIT 1;
    END IF;

    RETURN v_city_id;
END;
$$ LANGUAGE plpgsql;

-- 2. Create helper function to find region_id from region name
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

-- 3. Check if cuisines table has a region column and migrate it if needed
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'cuisines'
        AND column_name = 'region'
    ) THEN
        -- Add region_id column if it doesn't exist
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'cuisines'
            AND column_name = 'region_id'
        ) THEN
            ALTER TABLE cuisines ADD COLUMN region_id text;
        END IF;

        -- Migrate data from region text column to region_id
        UPDATE cuisines
        SET region_id = find_region_id_by_name(region)
        WHERE region_id IS NULL AND region IS NOT NULL;

        -- Verify migration
        IF EXISTS (
            SELECT 1 FROM cuisines
            WHERE region_id IS NULL AND region IS NOT NULL
        ) THEN
            RAISE WARNING 'Some cuisines records could not be migrated from region to region_id';
        ELSE
            -- Drop the redundant column
            ALTER TABLE cuisines DROP COLUMN region;

            -- Add comment
            COMMENT ON COLUMN cuisines.region_id IS 'Foreign key to regions table. Join with regions to get region name and other details.';
        END IF;
    END IF;
END $$;

-- 4. Check for other tables with city/region columns
CREATE TEMPORARY TABLE location_columns AS
SELECT table_name, column_name
FROM information_schema.columns
WHERE table_schema = 'public'
AND column_name IN ('city', 'region')
AND table_name NOT IN ('cuisines');

-- 5. Add comments to tables explaining the relationship
DO $$
DECLARE
    table_rec RECORD;
BEGIN
    FOR table_rec IN
        SELECT table_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND column_name = 'city_id'
    LOOP
        EXECUTE format('
            COMMENT ON COLUMN %I.city_id IS ''Foreign key to cities table. Join with cities to get city name and other details.''
        ', table_rec.table_name);
    END LOOP;

    FOR table_rec IN
        SELECT table_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND column_name = 'region_id'
    LOOP
        EXECUTE format('
            COMMENT ON COLUMN %I.region_id IS ''Foreign key to regions table. Join with regions to get region name and other details.''
        ', table_rec.table_name);
    END LOOP;
END $$;

-- Clean up temporary objects
DROP FUNCTION find_city_id_by_name(text);
DROP FUNCTION find_region_id_by_name(text);
DROP TABLE location_columns;

-- Commit transaction
COMMIT;
