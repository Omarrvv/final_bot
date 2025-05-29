-- Migration: Generate Missing Embeddings
-- Date: 2025-06-27
-- Phase 6.1 of the database migration plan
-- Description: Generate embeddings for records that are missing them

-- This migration script is a placeholder for the Python script that will generate the embeddings.
-- The actual embedding generation is done by the Python script: scripts/generate_missing_embeddings.py

-- 1. Verify that the vector extension is installed
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    ) THEN
        RAISE EXCEPTION 'pgvector extension is not installed';
    END IF;
END $$;

-- 2. Create a function to check for missing embeddings
CREATE OR REPLACE FUNCTION check_missing_embeddings()
RETURNS TABLE (
    table_name TEXT,
    total_records BIGINT,
    missing_embeddings BIGINT,
    coverage_percentage NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT t.table_name::TEXT, 
           t.total_records::BIGINT,
           t.missing_embeddings::BIGINT,
           t.coverage_percentage::NUMERIC
    FROM (
        SELECT 'attractions' as table_name, 
               COUNT(*) as total_records,
               COUNT(*) FILTER (WHERE embedding IS NULL) as missing_embeddings,
               ROUND(100.0 * COUNT(*) FILTER (WHERE embedding IS NOT NULL) / COUNT(*), 2) as coverage_percentage
        FROM attractions
        UNION ALL
        SELECT 'accommodations' as table_name, 
               COUNT(*) as total_records,
               COUNT(*) FILTER (WHERE embedding IS NULL) as missing_embeddings,
               ROUND(100.0 * COUNT(*) FILTER (WHERE embedding IS NOT NULL) / COUNT(*), 2) as coverage_percentage
        FROM accommodations
        UNION ALL
        SELECT 'cities' as table_name, 
               COUNT(*) as total_records,
               COUNT(*) FILTER (WHERE embedding IS NULL) as missing_embeddings,
               ROUND(100.0 * COUNT(*) FILTER (WHERE embedding IS NOT NULL) / COUNT(*), 2) as coverage_percentage
        FROM cities
        UNION ALL
        SELECT 'restaurants' as table_name, 
               COUNT(*) as total_records,
               COUNT(*) FILTER (WHERE embedding IS NULL) as missing_embeddings,
               ROUND(100.0 * COUNT(*) FILTER (WHERE embedding IS NOT NULL) / COUNT(*), 2) as coverage_percentage
        FROM restaurants
        UNION ALL
        SELECT 'destinations' as table_name, 
               COUNT(*) as total_records,
               COUNT(*) FILTER (WHERE embedding IS NULL) as missing_embeddings,
               ROUND(100.0 * COUNT(*) FILTER (WHERE embedding IS NOT NULL) / COUNT(*), 2) as coverage_percentage
        FROM destinations
        UNION ALL
        SELECT 'tourism_faqs' as table_name, 
               COUNT(*) as total_records,
               COUNT(*) FILTER (WHERE embedding IS NULL) as missing_embeddings,
               ROUND(100.0 * COUNT(*) FILTER (WHERE embedding IS NOT NULL) / COUNT(*), 2) as coverage_percentage
        FROM tourism_faqs
        UNION ALL
        SELECT 'practical_info' as table_name, 
               COUNT(*) as total_records,
               COUNT(*) FILTER (WHERE embedding IS NULL) as missing_embeddings,
               ROUND(100.0 * COUNT(*) FILTER (WHERE embedding IS NOT NULL) / COUNT(*), 2) as coverage_percentage
        FROM practical_info
        UNION ALL
        SELECT 'tour_packages' as table_name, 
               COUNT(*) as total_records,
               COUNT(*) FILTER (WHERE embedding IS NULL) as missing_embeddings,
               ROUND(100.0 * COUNT(*) FILTER (WHERE embedding IS NOT NULL) / COUNT(*), 2) as coverage_percentage
        FROM tour_packages
        UNION ALL
        SELECT 'events_festivals' as table_name, 
               COUNT(*) as total_records,
               COUNT(*) FILTER (WHERE embedding IS NULL) as missing_embeddings,
               ROUND(100.0 * COUNT(*) FILTER (WHERE embedding IS NOT NULL) / COUNT(*), 2) as coverage_percentage
        FROM events_festivals
        UNION ALL
        SELECT 'itineraries' as table_name, 
               COUNT(*) as total_records,
               COUNT(*) FILTER (WHERE embedding IS NULL) as missing_embeddings,
               ROUND(100.0 * COUNT(*) FILTER (WHERE embedding IS NOT NULL) / COUNT(*), 2) as coverage_percentage
        FROM itineraries
    ) t
    ORDER BY t.missing_embeddings DESC;
END;
$$ LANGUAGE plpgsql;

-- 3. Check for missing embeddings before running the Python script
SELECT * FROM check_missing_embeddings();

-- 4. Note: After running this migration, execute the Python script to generate the embeddings:
--    python3 scripts/generate_missing_embeddings.py

-- 5. After running the Python script, verify that all embeddings have been generated:
--    SELECT * FROM check_missing_embeddings();
