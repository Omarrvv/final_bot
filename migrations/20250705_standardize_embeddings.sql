-- migrations/20250705_standardize_embeddings.sql
-- Standardize embedding storage across all tables

-- Transaction to ensure all changes are applied atomically
BEGIN;

-- Ensure pgvector extension is installed
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a function to safely convert various embedding formats to vector
CREATE OR REPLACE FUNCTION safe_to_vector(input_value ANYELEMENT)
RETURNS vector AS $$
DECLARE
    result vector;
BEGIN
    -- Handle NULL values
    IF input_value IS NULL THEN
        RETURN NULL;
    END IF;

    -- Handle different input types
    CASE pg_typeof(input_value)::text
        WHEN 'text' THEN
            -- Try to parse JSON string
            BEGIN
                -- Remove any whitespace and try to convert to vector
                result := TRIM(BOTH '[]' FROM REPLACE(input_value::text, ' ', ''))::vector;
                RETURN result;
            EXCEPTION WHEN OTHERS THEN
                -- If that fails, return NULL and log error
                RAISE WARNING 'Could not convert string to vector: %', input_value;
                RETURN NULL;
            END;
        WHEN 'vector' THEN
            -- Already a vector, just return it
            RETURN input_value;
        WHEN 'json' THEN
            -- Convert JSON array to vector
            BEGIN
                result := input_value::text::vector;
                RETURN result;
            EXCEPTION WHEN OTHERS THEN
                RAISE WARNING 'Could not convert JSON to vector: %', input_value;
                RETURN NULL;
            END;
        WHEN 'jsonb' THEN
            -- Convert JSONB array to vector
            BEGIN
                result := input_value::text::vector;
                RETURN result;
            EXCEPTION WHEN OTHERS THEN
                RAISE WARNING 'Could not convert JSONB to vector: %', input_value;
                RETURN NULL;
            END;
        ELSE
            -- For other types, try direct conversion
            BEGIN
                result := input_value::text::vector;
                RETURN result;
            EXCEPTION WHEN OTHERS THEN
                RAISE WARNING 'Could not convert % to vector: %', pg_typeof(input_value)::text, input_value;
                RETURN NULL;
            END;
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- Create a temporary table to track conversion statistics
CREATE TEMPORARY TABLE embedding_conversion_stats (
    table_name text,
    total_rows int,
    converted_rows int,
    failed_rows int
);

-- Function to update statistics
CREATE OR REPLACE FUNCTION update_conversion_stats(
    p_table_name text,
    p_total_rows int,
    p_converted_rows int,
    p_failed_rows int
) RETURNS void AS $$
BEGIN
    INSERT INTO embedding_conversion_stats (table_name, total_rows, converted_rows, failed_rows)
    VALUES (p_table_name, p_total_rows, p_converted_rows, p_failed_rows);
END;
$$ LANGUAGE plpgsql;

-- Update attractions table
DO $$
DECLARE
    total_count int;
    null_count int;
    converted_count int;
BEGIN
    -- Count total rows and null embeddings
    SELECT COUNT(*) INTO total_count FROM attractions;
    SELECT COUNT(*) INTO null_count FROM attractions WHERE embedding IS NULL;

    -- Create a backup of the embedding column
    ALTER TABLE attractions ADD COLUMN IF NOT EXISTS embedding_backup text;
    UPDATE attractions SET embedding_backup = embedding::text WHERE embedding IS NOT NULL;

    -- Convert embeddings to vector type
    UPDATE attractions
    SET embedding = safe_to_vector(embedding)
    WHERE embedding IS NOT NULL;

    -- Count successfully converted rows
    SELECT COUNT(*) INTO converted_count FROM attractions WHERE embedding IS NOT NULL;

    -- Update statistics
    PERFORM update_conversion_stats(
        'attractions',
        total_count,
        converted_count,
        total_count - converted_count - null_count
    );

    -- Ensure column is vector type
    ALTER TABLE attractions ALTER COLUMN embedding TYPE vector USING embedding::vector;
END $$;

-- Update restaurants table
DO $$
DECLARE
    total_count int;
    null_count int;
    converted_count int;
BEGIN
    -- Count total rows and null embeddings
    SELECT COUNT(*) INTO total_count FROM restaurants;
    SELECT COUNT(*) INTO null_count FROM restaurants WHERE embedding IS NULL;

    -- Create a backup of the embedding column
    ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS embedding_backup text;
    UPDATE restaurants SET embedding_backup = embedding::text WHERE embedding IS NOT NULL;

    -- Convert embeddings to vector type
    UPDATE restaurants
    SET embedding = safe_to_vector(embedding)
    WHERE embedding IS NOT NULL;

    -- Count successfully converted rows
    SELECT COUNT(*) INTO converted_count FROM restaurants WHERE embedding IS NOT NULL;

    -- Update statistics
    PERFORM update_conversion_stats(
        'restaurants',
        total_count,
        converted_count,
        total_count - converted_count - null_count
    );

    -- Ensure column is vector type
    ALTER TABLE restaurants ALTER COLUMN embedding TYPE vector USING embedding::vector;
END $$;

-- Update accommodations table
DO $$
DECLARE
    total_count int;
    null_count int;
    converted_count int;
BEGIN
    -- Count total rows and null embeddings
    SELECT COUNT(*) INTO total_count FROM accommodations;
    SELECT COUNT(*) INTO null_count FROM accommodations WHERE embedding IS NULL;

    -- Create a backup of the embedding column
    ALTER TABLE accommodations ADD COLUMN IF NOT EXISTS embedding_backup text;
    UPDATE accommodations SET embedding_backup = embedding::text WHERE embedding IS NOT NULL;

    -- Convert embeddings to vector type
    UPDATE accommodations
    SET embedding = safe_to_vector(embedding)
    WHERE embedding IS NOT NULL;

    -- Count successfully converted rows
    SELECT COUNT(*) INTO converted_count FROM accommodations WHERE embedding IS NOT NULL;

    -- Update statistics
    PERFORM update_conversion_stats(
        'accommodations',
        total_count,
        converted_count,
        total_count - converted_count - null_count
    );

    -- Ensure column is vector type
    ALTER TABLE accommodations ALTER COLUMN embedding TYPE vector USING embedding::vector;
END $$;

-- Update cities table
DO $$
DECLARE
    total_count int;
    null_count int;
    converted_count int;
BEGIN
    -- Count total rows and null embeddings
    SELECT COUNT(*) INTO total_count FROM cities;
    SELECT COUNT(*) INTO null_count FROM cities WHERE embedding IS NULL;

    -- Create a backup of the embedding column
    ALTER TABLE cities ADD COLUMN IF NOT EXISTS embedding_backup text;
    UPDATE cities SET embedding_backup = embedding::text WHERE embedding IS NOT NULL;

    -- Convert embeddings to vector type
    UPDATE cities
    SET embedding = safe_to_vector(embedding)
    WHERE embedding IS NOT NULL;

    -- Count successfully converted rows
    SELECT COUNT(*) INTO converted_count FROM cities WHERE embedding IS NOT NULL;

    -- Update statistics
    PERFORM update_conversion_stats(
        'cities',
        total_count,
        converted_count,
        total_count - converted_count - null_count
    );

    -- Ensure column is vector type
    ALTER TABLE cities ALTER COLUMN embedding TYPE vector USING embedding::vector;
END $$;

-- Add constraints to ensure embeddings are valid
DO $$
BEGIN
    -- Check if constraint exists for attractions
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'valid_attraction_embedding'
    ) THEN
        ALTER TABLE attractions ADD CONSTRAINT valid_attraction_embedding
            CHECK (embedding IS NULL OR embedding::text <> '[]');
    END IF;

    -- Check if constraint exists for restaurants
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'valid_restaurant_embedding'
    ) THEN
        ALTER TABLE restaurants ADD CONSTRAINT valid_restaurant_embedding
            CHECK (embedding IS NULL OR embedding::text <> '[]');
    END IF;

    -- Check if constraint exists for accommodations
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'valid_accommodation_embedding'
    ) THEN
        ALTER TABLE accommodations ADD CONSTRAINT valid_accommodation_embedding
            CHECK (embedding IS NULL OR embedding::text <> '[]');
    END IF;

    -- Check if constraint exists for cities
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'valid_city_embedding'
    ) THEN
        ALTER TABLE cities ADD CONSTRAINT valid_city_embedding
            CHECK (embedding IS NULL OR embedding::text <> '[]');
    END IF;
END $$;

-- Output conversion statistics
SELECT * FROM embedding_conversion_stats;

-- Update schema_migrations table
INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
VALUES ('20250705', 'standardize_embeddings', NOW(), md5('20250705_standardize_embeddings'), 0, 'success')
ON CONFLICT (version) DO NOTHING;

-- Drop temporary objects
DROP FUNCTION IF EXISTS safe_to_vector;
DROP FUNCTION IF EXISTS update_conversion_stats;
DROP TABLE IF EXISTS embedding_conversion_stats;

COMMIT;
