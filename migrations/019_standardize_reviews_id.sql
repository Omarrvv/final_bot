-- Migration: 019_standardize_reviews_id.sql
-- Purpose: Standardize ID for reviews table

-- Begin transaction
BEGIN;

-- 1. Create a mapping table
CREATE TABLE id_mapping_reviews (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

-- 2. Populate mapping table
INSERT INTO id_mapping_reviews (old_id)
SELECT id FROM reviews ORDER BY id;

-- 3. Add new integer ID column
ALTER TABLE reviews ADD COLUMN integer_id serial;

-- 4. Drop old primary key constraint
ALTER TABLE reviews DROP CONSTRAINT IF EXISTS reviews_pkey;

-- 5. Drop old ID column
ALTER TABLE reviews DROP COLUMN id;

-- 6. Rename new ID column
ALTER TABLE reviews RENAME COLUMN integer_id TO id;

-- 7. Add primary key constraint
ALTER TABLE reviews ADD PRIMARY KEY (id);

-- 8. Clean up mapping table
DROP TABLE id_mapping_reviews;

-- Commit transaction
COMMIT;
