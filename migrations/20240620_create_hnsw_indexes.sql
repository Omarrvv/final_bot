-- Migration: Create HNSW Indexes for Vector Columns
-- Date: 2024-06-20
-- Phase 6.2 of the database migration plan
-- Description: Replace IVFFLAT indexes with HNSW indexes for better vector search performance

-- 1. Verify pgvector extension version supports HNSW
DO $$
BEGIN
    -- Check if pgvector extension is installed
    IF NOT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    ) THEN
        RAISE EXCEPTION 'pgvector extension is not installed';
    END IF;

    -- Check if pgvector version supports HNSW
    IF NOT EXISTS (
        SELECT 1 FROM pg_am WHERE amname = 'hnsw'
    ) THEN
        RAISE EXCEPTION 'pgvector version does not support HNSW indexes';
    END IF;
END $$;

-- 2. Drop existing IVFFLAT indexes
DROP INDEX IF EXISTS idx_attractions_embedding;
DROP INDEX IF EXISTS idx_accommodations_embedding;
DROP INDEX IF EXISTS idx_cities_embedding;
DROP INDEX IF EXISTS idx_restaurants_embedding;

-- 3. Create HNSW indexes with optimal parameters
-- Attractions
CREATE INDEX idx_attractions_embedding_hnsw
ON attractions USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Accommodations
CREATE INDEX idx_accommodations_embedding_hnsw
ON accommodations USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Cities
CREATE INDEX idx_cities_embedding_hnsw
ON cities USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Restaurants
CREATE INDEX idx_restaurants_embedding_hnsw
ON restaurants USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 4. Verify indexes are created successfully
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO index_count
    FROM pg_indexes
    WHERE indexname LIKE '%hnsw%';

    IF index_count = 4 THEN
        RAISE NOTICE 'Successfully created 4 HNSW indexes';
    ELSE
        RAISE WARNING 'Expected 4 HNSW indexes, but found %', index_count;
    END IF;
END $$;
