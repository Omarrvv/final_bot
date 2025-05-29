-- Migration: 031_add_missing_hnsw_indexes_v2.sql
-- Purpose: Add missing HNSW indexes for embedding columns

-- Begin transaction
BEGIN;

-- Add dimensions to vector columns if needed
ALTER TABLE restaurants ALTER COLUMN embedding SET DATA TYPE vector(1536);
ALTER TABLE accommodations ALTER COLUMN embedding SET DATA TYPE vector(1536);
ALTER TABLE attractions ALTER COLUMN embedding SET DATA TYPE vector(1536);
ALTER TABLE cities ALTER COLUMN embedding SET DATA TYPE vector(1536);

-- Add HNSW indexes for tables missing them
CREATE INDEX IF NOT EXISTS idx_restaurants_embedding ON restaurants USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64');
CREATE INDEX IF NOT EXISTS idx_accommodations_embedding ON accommodations USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64');
CREATE INDEX IF NOT EXISTS idx_attractions_embedding ON attractions USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64');
CREATE INDEX IF NOT EXISTS idx_cities_embedding ON cities USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64');

-- Commit transaction
COMMIT;
