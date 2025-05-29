-- migrations/20250706_standardize_jsonb.sql
-- Standardize JSONB columns across all tables

-- Transaction to ensure all changes are applied atomically
BEGIN;

-- Create a function to standardize JSONB fields
CREATE OR REPLACE FUNCTION standardize_jsonb_field(input_value JSONB, field_name TEXT) 
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    -- Handle NULL values
    IF input_value IS NULL THEN
        RETURN jsonb_build_object(
            'en', '',
            'ar', ''
        );
    END IF;
    
    -- Handle different input types
    CASE jsonb_typeof(input_value)
        WHEN 'object' THEN
            -- Already an object, ensure it has en and ar keys
            result := input_value;
            
            -- Add missing keys with empty values
            IF NOT (result ? 'en') THEN
                result := result || jsonb_build_object('en', '');
            END IF;
            
            IF NOT (result ? 'ar') THEN
                result := result || jsonb_build_object('ar', '');
            END IF;
            
            RETURN result;
        WHEN 'string' THEN
            -- Convert string to object with en and ar keys
            RETURN jsonb_build_object(
                'en', input_value,
                'ar', ''
            );
        WHEN 'array' THEN
            -- Convert first array element to object with en and ar keys
            IF jsonb_array_length(input_value) > 0 THEN
                RETURN jsonb_build_object(
                    'en', input_value->0,
                    'ar', ''
                );
            ELSE
                RETURN jsonb_build_object(
                    'en', '',
                    'ar', ''
                );
            END IF;
        ELSE
            -- For other types, convert to string and use as en value
            RETURN jsonb_build_object(
                'en', input_value::text,
                'ar', ''
            );
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- Create a temporary table to track conversion statistics
CREATE TEMPORARY TABLE jsonb_conversion_stats (
    table_name text,
    column_name text,
    total_rows int,
    converted_rows int,
    failed_rows int
);

-- Function to update statistics
CREATE OR REPLACE FUNCTION update_jsonb_conversion_stats(
    p_table_name text,
    p_column_name text,
    p_total_rows int,
    p_converted_rows int,
    p_failed_rows int
) RETURNS void AS $$
BEGIN
    INSERT INTO jsonb_conversion_stats (table_name, column_name, total_rows, converted_rows, failed_rows)
    VALUES (p_table_name, p_column_name, p_total_rows, p_converted_rows, p_failed_rows);
END;
$$ LANGUAGE plpgsql;

-- Standardize JSONB fields in attractions table
DO $$
DECLARE
    total_count int;
    converted_count int;
    failed_count int;
BEGIN
    -- Count total rows
    SELECT COUNT(*) INTO total_count FROM attractions;
    
    -- Create backups of JSONB columns
    ALTER TABLE attractions ADD COLUMN IF NOT EXISTS name_backup JSONB;
    ALTER TABLE attractions ADD COLUMN IF NOT EXISTS description_backup JSONB;
    
    UPDATE attractions SET 
        name_backup = name,
        description_backup = description
    WHERE name IS NOT NULL OR description IS NOT NULL;
    
    -- Standardize name column
    UPDATE attractions 
    SET name = standardize_jsonb_field(name, 'name')
    WHERE name IS NOT NULL;
    
    -- Standardize description column
    UPDATE attractions 
    SET description = standardize_jsonb_field(description, 'description')
    WHERE description IS NOT NULL;
    
    -- Count successfully converted rows
    SELECT COUNT(*) INTO converted_count 
    FROM attractions 
    WHERE (name IS NOT NULL AND name ? 'en' AND name ? 'ar') 
       OR (description IS NOT NULL AND description ? 'en' AND description ? 'ar');
    
    -- Calculate failed rows
    failed_count := total_count - converted_count;
    
    -- Update statistics
    PERFORM update_jsonb_conversion_stats(
        'attractions', 
        'name/description', 
        total_count, 
        converted_count, 
        failed_count
    );
END $$;

-- Standardize JSONB fields in restaurants table
DO $$
DECLARE
    total_count int;
    converted_count int;
    failed_count int;
BEGIN
    -- Count total rows
    SELECT COUNT(*) INTO total_count FROM restaurants;
    
    -- Create backups of JSONB columns
    ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS name_backup JSONB;
    ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS description_backup JSONB;
    
    UPDATE restaurants SET 
        name_backup = name,
        description_backup = description
    WHERE name IS NOT NULL OR description IS NOT NULL;
    
    -- Standardize name column
    UPDATE restaurants 
    SET name = standardize_jsonb_field(name, 'name')
    WHERE name IS NOT NULL;
    
    -- Standardize description column
    UPDATE restaurants 
    SET description = standardize_jsonb_field(description, 'description')
    WHERE description IS NOT NULL;
    
    -- Count successfully converted rows
    SELECT COUNT(*) INTO converted_count 
    FROM restaurants 
    WHERE (name IS NOT NULL AND name ? 'en' AND name ? 'ar') 
       OR (description IS NOT NULL AND description ? 'en' AND description ? 'ar');
    
    -- Calculate failed rows
    failed_count := total_count - converted_count;
    
    -- Update statistics
    PERFORM update_jsonb_conversion_stats(
        'restaurants', 
        'name/description', 
        total_count, 
        converted_count, 
        failed_count
    );
END $$;

-- Standardize JSONB fields in accommodations table
DO $$
DECLARE
    total_count int;
    converted_count int;
    failed_count int;
BEGIN
    -- Count total rows
    SELECT COUNT(*) INTO total_count FROM accommodations;
    
    -- Create backups of JSONB columns
    ALTER TABLE accommodations ADD COLUMN IF NOT EXISTS name_backup JSONB;
    ALTER TABLE accommodations ADD COLUMN IF NOT EXISTS description_backup JSONB;
    
    UPDATE accommodations SET 
        name_backup = name,
        description_backup = description
    WHERE name IS NOT NULL OR description IS NOT NULL;
    
    -- Standardize name column
    UPDATE accommodations 
    SET name = standardize_jsonb_field(name, 'name')
    WHERE name IS NOT NULL;
    
    -- Standardize description column
    UPDATE accommodations 
    SET description = standardize_jsonb_field(description, 'description')
    WHERE description IS NOT NULL;
    
    -- Count successfully converted rows
    SELECT COUNT(*) INTO converted_count 
    FROM accommodations 
    WHERE (name IS NOT NULL AND name ? 'en' AND name ? 'ar') 
       OR (description IS NOT NULL AND description ? 'en' AND description ? 'ar');
    
    -- Calculate failed rows
    failed_count := total_count - converted_count;
    
    -- Update statistics
    PERFORM update_jsonb_conversion_stats(
        'accommodations', 
        'name/description', 
        total_count, 
        converted_count, 
        failed_count
    );
END $$;

-- Standardize JSONB fields in cities table
DO $$
DECLARE
    total_count int;
    converted_count int;
    failed_count int;
BEGIN
    -- Count total rows
    SELECT COUNT(*) INTO total_count FROM cities;
    
    -- Create backups of JSONB columns
    ALTER TABLE cities ADD COLUMN IF NOT EXISTS name_backup JSONB;
    ALTER TABLE cities ADD COLUMN IF NOT EXISTS description_backup JSONB;
    
    UPDATE cities SET 
        name_backup = name,
        description_backup = description
    WHERE name IS NOT NULL OR description IS NOT NULL;
    
    -- Standardize name column
    UPDATE cities 
    SET name = standardize_jsonb_field(name, 'name')
    WHERE name IS NOT NULL;
    
    -- Standardize description column
    UPDATE cities 
    SET description = standardize_jsonb_field(description, 'description')
    WHERE description IS NOT NULL;
    
    -- Count successfully converted rows
    SELECT COUNT(*) INTO converted_count 
    FROM cities 
    WHERE (name IS NOT NULL AND name ? 'en' AND name ? 'ar') 
       OR (description IS NOT NULL AND description ? 'en' AND description ? 'ar');
    
    -- Calculate failed rows
    failed_count := total_count - converted_count;
    
    -- Update statistics
    PERFORM update_jsonb_conversion_stats(
        'cities', 
        'name/description', 
        total_count, 
        converted_count, 
        failed_count
    );
END $$;

-- Output conversion statistics
SELECT * FROM jsonb_conversion_stats;

-- Update schema_migrations table
INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
VALUES ('20250706', 'standardize_jsonb', NOW(), md5('20250706_standardize_jsonb'), 0, 'success')
ON CONFLICT (version) DO NOTHING;

-- Drop temporary objects
DROP FUNCTION IF EXISTS standardize_jsonb_field;
DROP FUNCTION IF EXISTS update_jsonb_conversion_stats;
DROP TABLE IF EXISTS jsonb_conversion_stats;

COMMIT;
