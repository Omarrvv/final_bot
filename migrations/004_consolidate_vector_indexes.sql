-- Migration: 004_consolidate_vector_indexes.sql
-- Purpose: Standardize on HNSW indexes for vector search and remove redundant IVFFlat indexes.
-- HNSW (Hierarchical Navigable Small World) indexes generally provide better performance
-- for approximate nearest neighbor searches compared to IVFFlat.

-- Begin transaction
BEGIN;

-- 1. Record existing vector indexes in a temporary table for reference
CREATE TEMPORARY TABLE vector_index_migration AS
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM
    pg_indexes
WHERE
    indexdef LIKE '%vector%' AND
    (indexdef LIKE '%ivfflat%' OR indexdef LIKE '%hnsw%');

-- 2. Drop IVFFlat indexes (HNSW indexes will remain)
DROP INDEX IF EXISTS idx_accommodations_embedding;
DROP INDEX IF EXISTS idx_attractions_embedding;
DROP INDEX IF EXISTS idx_cities_embedding;
DROP INDEX IF EXISTS idx_hotels_embedding;
DROP INDEX IF EXISTS idx_regions_embedding;
DROP INDEX IF EXISTS idx_restaurants_embedding;

-- 3. Rename HNSW indexes to standard naming convention
ALTER INDEX IF EXISTS idx_accommodations_embedding_hnsw RENAME TO idx_accommodations_embedding;
ALTER INDEX IF EXISTS idx_attractions_embedding_hnsw RENAME TO idx_attractions_embedding;
ALTER INDEX IF EXISTS idx_cities_embedding_hnsw RENAME TO idx_cities_embedding;
ALTER INDEX IF EXISTS idx_hotels_embedding_hnsw RENAME TO idx_hotels_embedding;
ALTER INDEX IF EXISTS idx_regions_embedding_hnsw RENAME TO idx_regions_embedding;
ALTER INDEX IF EXISTS idx_restaurants_embedding_hnsw RENAME TO idx_restaurants_embedding;
ALTER INDEX IF EXISTS idx_destinations_embedding_hnsw RENAME TO idx_destinations_embedding;
ALTER INDEX IF EXISTS idx_tourism_faqs_embedding_hnsw RENAME TO idx_tourism_faqs_embedding;
ALTER INDEX IF EXISTS idx_practical_info_embedding_hnsw RENAME TO idx_practical_info_embedding;
ALTER INDEX IF EXISTS idx_tour_packages_embedding_hnsw RENAME TO idx_tour_packages_embedding;
ALTER INDEX IF EXISTS idx_events_festivals_embedding_hnsw RENAME TO idx_events_festivals_embedding;
ALTER INDEX IF EXISTS idx_itineraries_embedding_hnsw RENAME TO idx_itineraries_embedding;

-- 4. Create HNSW indexes where they don't exist but should
-- Check if we need to create any missing HNSW indexes
DO $$
DECLARE
    tables_with_embedding RECORD;
    has_hnsw_index BOOLEAN;
BEGIN
    FOR tables_with_embedding IN
        SELECT table_name
        FROM information_schema.columns
        WHERE column_name = 'embedding'
        AND table_schema = 'public'
    LOOP
        -- Check if an HNSW index exists for this table
        SELECT EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE tablename = tables_with_embedding.table_name
            AND (indexdef LIKE '%hnsw%' OR indexname = 'idx_' || tables_with_embedding.table_name || '_embedding')
            AND indexdef LIKE '%embedding%'
        ) INTO has_hnsw_index;

        -- If no HNSW index exists, create one
        IF NOT has_hnsw_index THEN
            EXECUTE format('
                CREATE INDEX idx_%s_embedding ON public.%s
                USING hnsw (embedding public.vector_cosine_ops)
                WITH (m=''16'', ef_construction=''64'')
            ', tables_with_embedding.table_name, tables_with_embedding.table_name);

            RAISE NOTICE 'Created HNSW index for %', tables_with_embedding.table_name;
        END IF;
    END LOOP;
END $$;

-- 5. Update vector_indexes table to reflect the changes if it exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'vector_indexes'
    ) THEN
        INSERT INTO vector_indexes (table_name, column_name, index_type, dimension, creation_time, duration_seconds)
        SELECT
            tablename,
            'embedding',
            'hnsw',
            1536,
            CURRENT_TIMESTAMP,
            0.0
        FROM
            pg_indexes
        WHERE
            (indexdef LIKE '%hnsw%' OR indexname LIKE 'idx_%_embedding')
            AND indexdef LIKE '%embedding%'
            AND tablename NOT IN (
                SELECT table_name
                FROM vector_indexes
                WHERE index_type = 'hnsw' AND column_name = 'embedding'
            );
    END IF;
END $$;

-- 6. Add comments to tables explaining the vector search capabilities
DO $$
DECLARE
    tables_with_embedding RECORD;
BEGIN
    FOR tables_with_embedding IN
        SELECT table_name
        FROM information_schema.columns
        WHERE column_name = 'embedding'
        AND table_schema = 'public'
    LOOP
        EXECUTE format('
            COMMENT ON COLUMN %I.embedding IS
            ''Vector embedding for semantic search. Use vector operators (<->, <=>) for similarity search.''
        ', tables_with_embedding.table_name);
    END LOOP;
END $$;

-- Clean up temporary objects
DROP TABLE vector_index_migration;

-- Commit transaction
COMMIT;
