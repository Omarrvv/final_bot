-- Migration: 020_standardize_favorites_id.sql
-- Purpose: Standardize ID for favorites table

-- Begin transaction
BEGIN;

-- 1. Create a mapping table
CREATE TABLE id_mapping_favorites (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

-- 2. Populate mapping table
INSERT INTO id_mapping_favorites (old_id)
SELECT id FROM favorites ORDER BY id;

-- 3. Add new integer ID column
ALTER TABLE favorites ADD COLUMN integer_id serial;

-- 4. Drop old primary key constraint
ALTER TABLE favorites DROP CONSTRAINT IF EXISTS favorites_pkey;

-- 5. Drop old ID column
ALTER TABLE favorites DROP COLUMN id;

-- 6. Rename new ID column
ALTER TABLE favorites RENAME COLUMN integer_id TO id;

-- 7. Add primary key constraint
ALTER TABLE favorites ADD PRIMARY KEY (id);

-- 8. Clean up mapping table
DROP TABLE id_mapping_favorites;

-- Commit transaction
COMMIT;
