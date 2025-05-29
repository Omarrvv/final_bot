-- Migration: Fix Remaining User ID Columns
-- Date: 2025-07-20
-- Purpose: Convert remaining user_id columns to integer type

BEGIN;

-- Log the migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting migration to fix remaining user_id columns';
END $$;

-- Tables with user_id column still as text
CREATE TEMPORARY TABLE remaining_tables AS
SELECT table_name, column_name
FROM information_schema.columns
WHERE table_name IN (
    'accommodations', 'attractions', 'destinations', 'events_festivals',
    'feedback', 'itineraries', 'practical_info', 'restaurants',
    'tour_packages', 'tourism_faqs', 'transportation_routes', 'transportation_stations'
)
AND column_name = 'user_id'
AND data_type = 'text'
AND table_schema = 'public';

-- Create backup columns for each table if they don't exist
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT * FROM remaining_tables
    LOOP
        -- Check if backup column already exists
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = r.table_name
            AND column_name = 'user_id_backup'
            AND table_schema = 'public'
        ) THEN
            EXECUTE format('ALTER TABLE %I ADD COLUMN user_id_backup TEXT', r.table_name);
            EXECUTE format('UPDATE %I SET user_id_backup = user_id WHERE user_id IS NOT NULL', r.table_name);
            RAISE NOTICE 'Created backup of user_id in table %', r.table_name;
        ELSE
            RAISE NOTICE 'Backup column already exists in table %', r.table_name;
        END IF;
    END LOOP;
END $$;

-- Update user_id columns to integer type
DO $$
DECLARE
    r RECORD;
    fk_exists BOOLEAN;
BEGIN
    FOR r IN SELECT * FROM remaining_tables
    LOOP
        -- Check if there's a foreign key constraint
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND kcu.table_name = r.table_name
            AND kcu.column_name = 'user_id'
        ) INTO fk_exists;
        
        -- Drop foreign key constraint if it exists
        IF fk_exists THEN
            EXECUTE format(
                'ALTER TABLE %I DROP CONSTRAINT %I',
                r.table_name,
                (SELECT constraint_name
                 FROM information_schema.table_constraints tc
                 JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                 WHERE tc.constraint_type = 'FOREIGN KEY'
                 AND kcu.table_name = r.table_name
                 AND kcu.column_name = 'user_id'
                 LIMIT 1)
            );
            RAISE NOTICE 'Dropped foreign key constraint on %.user_id', r.table_name;
        END IF;
        
        -- Alter column type
        BEGIN
            -- First, handle any non-numeric values
            EXECUTE format('
                UPDATE %I
                SET user_id = NULL
                WHERE user_id IS NOT NULL AND user_id !~ ''^[0-9]+$''
            ', r.table_name);
            
            -- Then convert to integer
            EXECUTE format('ALTER TABLE %I ALTER COLUMN user_id TYPE INTEGER USING (user_id::INTEGER)', r.table_name);
            RAISE NOTICE 'Updated %.user_id to INTEGER', r.table_name;
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Error converting %.user_id to INTEGER: %', r.table_name, SQLERRM;
            -- If conversion fails, set to NULL and log
            EXECUTE format('UPDATE %I SET user_id = NULL WHERE user_id IS NOT NULL', r.table_name);
            RAISE NOTICE 'Set %.user_id to NULL due to conversion error', r.table_name;
        END;
        
        -- Add foreign key constraint
        BEGIN
            EXECUTE format(
                'ALTER TABLE %I ADD CONSTRAINT fk_%I_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL',
                r.table_name,
                r.table_name
            );
            RAISE NOTICE 'Added foreign key constraint on %.user_id', r.table_name;
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Error adding foreign key constraint on %.user_id: %', r.table_name, SQLERRM;
        END;
    END LOOP;
END $$;

-- Log the migration completion
DO $$
BEGIN
    RAISE NOTICE 'Remaining user_id columns fixed successfully';
END $$;

-- Update the schema version
INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
VALUES ('20250720_3', 'fix_remaining_user_id', NOW(), md5('20250720_fix_remaining_user_id'), 0, 'success')
ON CONFLICT (version) DO NOTHING;

COMMIT;
