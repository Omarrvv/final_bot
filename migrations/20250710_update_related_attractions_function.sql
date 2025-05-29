-- Migration: Update find_related_attractions Function
-- Date: 2025-07-10
-- Purpose: Update the find_related_attractions function to use the junction table instead of the array column

BEGIN;

-- Log the migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting migration to update find_related_attractions function';
END $$;

-- Drop the existing function
DROP FUNCTION IF EXISTS find_related_attractions(text, integer);

-- Create the updated function that uses the junction table
CREATE OR REPLACE FUNCTION find_related_attractions(
    p_attraction_id INTEGER,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    id INTEGER,
    name JSONB,
    type TEXT,
    subcategory_id TEXT,
    city_id INTEGER,
    region_id INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.id,
        a.name,
        a.type,
        a.subcategory_id,
        a.city_id,
        a.region_id
    FROM 
        attraction_relationships ar
        JOIN attractions a ON ar.related_attraction_id = a.id
    WHERE 
        ar.attraction_id = p_attraction_id
    ORDER BY
        a.name->>'en'
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Log the migration completion
DO $$
BEGIN
    RAISE NOTICE 'find_related_attractions function updated successfully';
END $$;

-- Update the schema version if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'schema_migrations') THEN
        INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
        VALUES ('20250710', 'update_related_attractions_function', NOW(), md5('20250710_update_related_attractions_function'), 0, 'success')
        ON CONFLICT (version) DO NOTHING;
    END IF;
END $$;

COMMIT;
