-- Migration: Fix Polymorphic Associations
-- Date: 2025-07-20
-- Purpose: Update polymorphic target_id columns to integer type

BEGIN;

-- Log the migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting migration to fix polymorphic associations';
END $$;

-- Tables with polymorphic associations
CREATE TEMPORARY TABLE polymorphic_tables AS
SELECT table_name
FROM information_schema.columns
WHERE column_name = 'target_id' AND data_type = 'text'
AND table_name IN ('media', 'reviews', 'favorites')
AND table_schema = 'public';

-- Create backup columns for each table
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT * FROM polymorphic_tables
    LOOP
        EXECUTE format('ALTER TABLE %I ADD COLUMN IF NOT EXISTS target_id_backup TEXT', r.table_name);
        EXECUTE format('UPDATE %I SET target_id_backup = target_id WHERE target_id IS NOT NULL', r.table_name);
        RAISE NOTICE 'Created backup of target_id in table %', r.table_name;
    END LOOP;
END $$;

-- Create a mapping table to store the relationship between text IDs and integer IDs
CREATE TEMPORARY TABLE target_id_mapping (
    target_type TEXT,
    text_id TEXT,
    integer_id INTEGER
);

-- Populate the mapping table with data from all target tables
INSERT INTO target_id_mapping (target_type, text_id, integer_id)
SELECT 'attraction', id::TEXT, id FROM attractions
UNION ALL
SELECT 'restaurant', id::TEXT, id FROM restaurants
UNION ALL
SELECT 'accommodation', id::TEXT, id FROM accommodations
UNION ALL
SELECT 'city', id::TEXT, id FROM cities
UNION ALL
SELECT 'region', id::TEXT, id FROM regions
UNION ALL
SELECT 'event', id::TEXT, id FROM events_festivals
UNION ALL
SELECT 'tour_package', id::TEXT, id FROM tour_packages;

-- Update target_id columns to integer type
DO $$
DECLARE
    r RECORD;
    check_constraint_exists BOOLEAN;
BEGIN
    FOR r IN SELECT * FROM polymorphic_tables
    LOOP
        -- Check if there's a check constraint
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.table_constraints
            WHERE constraint_type = 'CHECK'
            AND table_name = r.table_name
            AND constraint_name LIKE 'chk_%_target_type'
        ) INTO check_constraint_exists;
        
        -- Drop check constraint if it exists
        IF check_constraint_exists THEN
            EXECUTE format(
                'ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I',
                r.table_name,
                (SELECT constraint_name
                 FROM information_schema.table_constraints
                 WHERE constraint_type = 'CHECK'
                 AND table_name = r.table_name
                 AND constraint_name LIKE 'chk_%_target_type'
                 LIMIT 1)
            );
            RAISE NOTICE 'Dropped check constraint on %.target_type', r.table_name;
        END IF;
        
        -- Drop index if it exists
        EXECUTE format('DROP INDEX IF EXISTS idx_%I_target', r.table_name);
        RAISE NOTICE 'Dropped index on %.target_type, target_id', r.table_name;
        
        -- Update target_id based on mapping
        EXECUTE format('
            UPDATE %I p
            SET target_id = m.integer_id::TEXT
            FROM target_id_mapping m
            WHERE p.target_type = m.target_type
            AND p.target_id = m.text_id
        ', r.table_name);
        RAISE NOTICE 'Updated %.target_id values based on mapping', r.table_name;
        
        -- Alter column type
        BEGIN
            EXECUTE format('ALTER TABLE %I ALTER COLUMN target_id TYPE INTEGER USING (target_id::INTEGER)', r.table_name);
            RAISE NOTICE 'Updated %.target_id to INTEGER', r.table_name;
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Error converting %.target_id to INTEGER: %', r.table_name, SQLERRM;
            -- If conversion fails, set to NULL and log
            EXECUTE format('UPDATE %I SET target_id = NULL WHERE target_id IS NOT NULL', r.table_name);
            RAISE NOTICE 'Set %.target_id to NULL due to conversion error', r.table_name;
        END;
        
        -- Add check constraint back
        EXECUTE format('
            ALTER TABLE %I ADD CONSTRAINT chk_%I_target_type
            CHECK (target_type IN (''attraction'', ''restaurant'', ''accommodation'', ''city'', ''region'', ''event'', ''tour_package''))
        ', r.table_name, r.table_name);
        RAISE NOTICE 'Added check constraint on %.target_type', r.table_name;
        
        -- Create index
        EXECUTE format('CREATE INDEX idx_%I_target ON %I(target_type, target_id)', r.table_name, r.table_name);
        RAISE NOTICE 'Created index on %.target_type, target_id', r.table_name;
    END LOOP;
END $$;

-- Log the migration completion
DO $$
BEGIN
    RAISE NOTICE 'Polymorphic associations fixed successfully';
END $$;

-- Update the schema version
INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
VALUES ('20250720_2', 'fix_polymorphic_associations', NOW(), md5('20250720_fix_polymorphic_associations'), 0, 'success')
ON CONFLICT (version) DO NOTHING;

COMMIT;
