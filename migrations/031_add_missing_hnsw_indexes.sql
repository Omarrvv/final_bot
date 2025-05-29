-- Migration: 031_add_missing_hnsw_indexes.sql
-- Purpose: Add missing HNSW indexes for embedding columns

-- Begin transaction
BEGIN;

-- Add HNSW indexes for tables missing them
CREATE INDEX IF NOT EXISTS idx_restaurants_embedding ON restaurants USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64');
CREATE INDEX IF NOT EXISTS idx_accommodations_embedding ON accommodations USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64');
CREATE INDEX IF NOT EXISTS idx_attractions_embedding ON attractions USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64');
CREATE INDEX IF NOT EXISTS idx_cities_embedding ON cities USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64');

-- Commit transaction
COMMIT;
