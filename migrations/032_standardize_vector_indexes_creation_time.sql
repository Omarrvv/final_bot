-- Migration: 032_standardize_vector_indexes_creation_time.sql
-- Purpose: Standardize vector_indexes.creation_time to timestamp with time zone

-- Begin transaction
BEGIN;

-- Alter the data type of vector_indexes.creation_time
ALTER TABLE vector_indexes
ALTER COLUMN creation_time TYPE timestamp with time zone;

-- Commit transaction
COMMIT;
