-- Migration: 017_standardize_chat_logs_id.sql
-- Purpose: Standardize ID for chat_logs table

-- Begin transaction
BEGIN;

-- 1. Create a mapping table
CREATE TABLE id_mapping_chat_logs (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

-- 2. Populate mapping table
INSERT INTO id_mapping_chat_logs (old_id)
SELECT id FROM chat_logs ORDER BY id;

-- 3. Add new integer ID column
ALTER TABLE chat_logs ADD COLUMN integer_id serial;

-- 4. Drop old primary key constraint
ALTER TABLE chat_logs DROP CONSTRAINT IF EXISTS chat_logs_pkey;

-- 5. Drop old ID column
ALTER TABLE chat_logs DROP COLUMN id;

-- 6. Rename new ID column
ALTER TABLE chat_logs RENAME COLUMN integer_id TO id;

-- 7. Add primary key constraint
ALTER TABLE chat_logs ADD PRIMARY KEY (id);

-- 8. Clean up mapping table
DROP TABLE id_mapping_chat_logs;

-- Commit transaction
COMMIT;
