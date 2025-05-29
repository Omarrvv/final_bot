-- Migration: 016_standardize_analytics_events_id.sql
-- Purpose: Standardize ID for analytics_events table (simple table with minimal dependencies)

-- Begin transaction
BEGIN;

-- 1. Create a mapping table
CREATE TABLE id_mapping_analytics_events (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

-- 2. Populate mapping table
INSERT INTO id_mapping_analytics_events (old_id)
SELECT id FROM analytics_events ORDER BY id;

-- 3. Add new integer ID column
ALTER TABLE analytics_events ADD COLUMN integer_id serial;

-- 4. Drop old primary key constraint
ALTER TABLE analytics_events DROP CONSTRAINT IF EXISTS analytics_events_pkey;

-- 5. Drop old ID column
ALTER TABLE analytics_events DROP COLUMN id;

-- 6. Rename new ID column
ALTER TABLE analytics_events RENAME COLUMN integer_id TO id;

-- 7. Add primary key constraint
ALTER TABLE analytics_events ADD PRIMARY KEY (id);

-- 8. Clean up mapping table
DROP TABLE id_mapping_analytics_events;

-- Commit transaction
COMMIT;
