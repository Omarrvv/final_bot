-- Migration: 018_standardize_media_id.sql
-- Purpose: Standardize ID for media table

-- Begin transaction
BEGIN;

-- 1. Create a mapping table
CREATE TABLE id_mapping_media (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

-- 2. Populate mapping table
INSERT INTO id_mapping_media (old_id)
SELECT id FROM media ORDER BY id;

-- 3. Add new integer ID column
ALTER TABLE media ADD COLUMN integer_id serial;

-- 4. Drop old primary key constraint
ALTER TABLE media DROP CONSTRAINT IF EXISTS media_pkey;

-- 5. Drop old ID column
ALTER TABLE media DROP COLUMN id;

-- 6. Rename new ID column
ALTER TABLE media RENAME COLUMN integer_id TO id;

-- 7. Add primary key constraint
ALTER TABLE media ADD PRIMARY KEY (id);

-- 8. Clean up mapping table
DROP TABLE id_mapping_media;

-- Commit transaction
COMMIT;
