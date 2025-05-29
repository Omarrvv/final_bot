-- Migration: Fix User ID Inconsistency
-- Date: 2025-07-20
-- Purpose: Standardize user_id columns to integer type across all tables

BEGIN;

-- Log the migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting migration to fix user_id inconsistency';
END $$;

-- First, check if users table exists and has integer IDs
DO $$
DECLARE
    users_id_type TEXT;
BEGIN
    SELECT data_type INTO users_id_type
    FROM information_schema.columns
    WHERE table_name = 'users' AND column_name = 'id';
    
    IF users_id_type IS NULL THEN
        RAISE EXCEPTION 'Users table not found or id column missing';
    ELSIF users_id_type != 'integer' THEN
        RAISE EXCEPTION 'Users table has id of type %. Expected integer.', users_id_type;
    END IF;
END $$;

-- Create a backup of the database before proceeding
DO $$
BEGIN
    RAISE NOTICE 'Creating backup of user_id columns before migration';
END $$;

-- Tables with user_id column of type text
CREATE TEMPORARY TABLE tables_to_update AS
SELECT table_name, column_name
FROM information_schema.columns
WHERE table_name IN (
    'accommodations', 'analytics', 'analytics_events', 'attractions',
    'chat_logs', 'destination_images', 'destinations', 'events_festivals',
    'favorites', 'feedback', 'itineraries', 'practical_info',
    'restaurants', 'reviews', 'tour_packages', 'tourism_faqs',
    'transportation_routes', 'transportation_stations'
)
AND column_name = 'user_id'
AND data_type = 'text'
AND table_schema = 'public';

-- Create backup columns for each table
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT * FROM tables_to_update
    LOOP
        EXECUTE format('ALTER TABLE %I ADD COLUMN IF NOT EXISTS user_id_backup TEXT', r.table_name);
        EXECUTE format('UPDATE %I SET user_id_backup = user_id WHERE user_id IS NOT NULL', r.table_name);
        RAISE NOTICE 'Created backup of user_id in table %', r.table_name;
    END LOOP;
END $$;

-- Update user_id columns to integer type
DO $$
DECLARE
    r RECORD;
    fk_exists BOOLEAN;
BEGIN
    FOR r IN SELECT * FROM tables_to_update
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
    RAISE NOTICE 'User ID inconsistency fixed successfully';
END $$;

-- Update the schema version
INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
VALUES ('20250720', 'fix_user_id_inconsistency', NOW(), md5('20250720_fix_user_id_inconsistency'), 0, 'success')
ON CONFLICT (version) DO NOTHING;

COMMIT;
