-- Migration: 001_consolidate_name_description_columns.sql
-- Purpose: Consolidate redundant name_en/name_ar and description_en/description_ar columns
-- into the JSONB name and description columns as the single source of truth.
-- This migration ensures all data is preserved before removing redundant columns.

-- Function to safely migrate text data to JSONB
CREATE OR REPLACE FUNCTION migrate_text_to_jsonb(
    p_table_name text,
    p_text_col_en text,
    p_text_col_ar text,
    p_jsonb_col text
) RETURNS void AS $$
DECLARE
    update_sql text;
BEGIN
    -- Update English values where they exist and JSONB doesn't have 'en' key
    update_sql := format('
        UPDATE %I
        SET %I = CASE
            WHEN %I IS NOT NULL AND (%I IS NULL OR NOT %I ? ''en'')
            THEN COALESCE(%I, ''{}''::jsonb) || jsonb_build_object(''en'', %I)
            ELSE %I
        END
        WHERE %I IS NOT NULL;
    ', p_table_name, p_jsonb_col, p_text_col_en, p_jsonb_col, p_jsonb_col, p_jsonb_col, p_text_col_en, p_jsonb_col, p_text_col_en);
    
    EXECUTE update_sql;
    
    -- Update Arabic values where they exist and JSONB doesn't have 'ar' key
    update_sql := format('
        UPDATE %I
        SET %I = CASE
            WHEN %I IS NOT NULL AND (%I IS NULL OR NOT %I ? ''ar'')
            THEN COALESCE(%I, ''{}''::jsonb) || jsonb_build_object(''ar'', %I)
            ELSE %I
        END
        WHERE %I IS NOT NULL;
    ', p_table_name, p_jsonb_col, p_text_col_ar, p_jsonb_col, p_jsonb_col, p_jsonb_col, p_text_col_ar, p_jsonb_col, p_text_col_ar);
    
    EXECUTE update_sql;
END;
$$ LANGUAGE plpgsql;

-- Begin transaction
BEGIN;

-- 1. Migrate data from text columns to JSONB columns
-- Accommodations table
SELECT migrate_text_to_jsonb('accommodations', 'name_en', 'name_ar', 'name');
SELECT migrate_text_to_jsonb('accommodations', 'description_en', 'description_ar', 'description');

-- Attractions table
SELECT migrate_text_to_jsonb('attractions', 'name_en', 'name_ar', 'name');
SELECT migrate_text_to_jsonb('attractions', 'description_en', 'description_ar', 'description');

-- Cities table
SELECT migrate_text_to_jsonb('cities', 'name_en', 'name_ar', 'name');

-- Hotels table
SELECT migrate_text_to_jsonb('hotels', 'name_en', 'name_ar', 'name');
SELECT migrate_text_to_jsonb('hotels', 'description_en', 'description_ar', 'description');

-- Regions table
SELECT migrate_text_to_jsonb('regions', 'name_en', 'name_ar', 'name');

-- Restaurants table
SELECT migrate_text_to_jsonb('restaurants', 'name_en', 'name_ar', 'name');
SELECT migrate_text_to_jsonb('restaurants', 'description_en', 'description_ar', 'description');

-- 2. Verify data migration (create verification function)
CREATE OR REPLACE FUNCTION verify_jsonb_migration(
    p_table_name text,
    p_text_col_en text,
    p_text_col_ar text,
    p_jsonb_col text
) RETURNS TABLE(
    missing_count bigint,
    table_name text,
    column_name text
) AS $$
DECLARE
    verify_sql text;
    result record;
BEGIN
    -- Check for any rows where text data exists but is not in JSONB
    verify_sql := format('
        SELECT COUNT(*) as missing_count, %L as table_name, %L as column_name
        FROM %I
        WHERE (
            (%I IS NOT NULL AND (%I IS NULL OR %I->>''en'' IS NULL OR %I->>''en'' <> %I))
            OR
            (%I IS NOT NULL AND (%I IS NULL OR %I->>''ar'' IS NULL OR %I->>''ar'' <> %I))
        )
    ', p_table_name, p_jsonb_col, p_table_name, p_text_col_en, p_jsonb_col, p_jsonb_col, p_jsonb_col, p_text_col_en,
       p_text_col_ar, p_jsonb_col, p_jsonb_col, p_jsonb_col, p_text_col_ar);
    
    RETURN QUERY EXECUTE verify_sql;
END;
$$ LANGUAGE plpgsql;

-- Run verification and store results in a temporary table
CREATE TEMPORARY TABLE migration_verification AS
SELECT * FROM verify_jsonb_migration('accommodations', 'name_en', 'name_ar', 'name')
UNION ALL
SELECT * FROM verify_jsonb_migration('accommodations', 'description_en', 'description_ar', 'description')
UNION ALL
SELECT * FROM verify_jsonb_migration('attractions', 'name_en', 'name_ar', 'name')
UNION ALL
SELECT * FROM verify_jsonb_migration('attractions', 'description_en', 'description_ar', 'description')
UNION ALL
SELECT * FROM verify_jsonb_migration('cities', 'name_en', 'name_ar', 'name')
UNION ALL
SELECT * FROM verify_jsonb_migration('hotels', 'name_en', 'name_ar', 'name')
UNION ALL
SELECT * FROM verify_jsonb_migration('hotels', 'description_en', 'description_ar', 'description')
UNION ALL
SELECT * FROM verify_jsonb_migration('regions', 'name_en', 'name_ar', 'name')
UNION ALL
SELECT * FROM verify_jsonb_migration('restaurants', 'name_en', 'name_ar', 'name')
UNION ALL
SELECT * FROM verify_jsonb_migration('restaurants', 'description_en', 'description_ar', 'description');

-- Check if any verification failed
DO $$
DECLARE
    total_missing bigint;
BEGIN
    SELECT SUM(missing_count) INTO total_missing FROM migration_verification;
    
    IF total_missing > 0 THEN
        RAISE EXCEPTION 'Migration verification failed: % records have inconsistencies', total_missing;
    END IF;
END $$;

-- 3. Drop redundant columns (only after verification passes)
-- Accommodations table
ALTER TABLE accommodations DROP COLUMN name_en;
ALTER TABLE accommodations DROP COLUMN name_ar;
ALTER TABLE accommodations DROP COLUMN description_en;
ALTER TABLE accommodations DROP COLUMN description_ar;

-- Attractions table
ALTER TABLE attractions DROP COLUMN name_en;
ALTER TABLE attractions DROP COLUMN name_ar;
ALTER TABLE attractions DROP COLUMN description_en;
ALTER TABLE attractions DROP COLUMN description_ar;

-- Cities table
ALTER TABLE cities DROP COLUMN name_en;
ALTER TABLE cities DROP COLUMN name_ar;

-- Hotels table
ALTER TABLE hotels DROP COLUMN name_en;
ALTER TABLE hotels DROP COLUMN name_ar;
ALTER TABLE hotels DROP COLUMN description_en;
ALTER TABLE hotels DROP COLUMN description_ar;

-- Regions table
ALTER TABLE regions DROP COLUMN name_en;
ALTER TABLE regions DROP COLUMN name_ar;

-- Restaurants table
ALTER TABLE restaurants DROP COLUMN name_en;
ALTER TABLE restaurants DROP COLUMN name_ar;
ALTER TABLE restaurants DROP COLUMN description_en;
ALTER TABLE restaurants DROP COLUMN description_ar;

-- Clean up temporary objects
DROP FUNCTION migrate_text_to_jsonb(text, text, text, text);
DROP FUNCTION verify_jsonb_migration(text, text, text, text);
DROP TABLE migration_verification;

-- Commit transaction
COMMIT;
