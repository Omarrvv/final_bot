-- Migration: Fix User ID Inconsistency
-- Date: 2025-07-10
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
        RAISE NOTICE 'Users table not found or id column missing. Skipping user_id standardization.';
        RETURN;
    ELSIF users_id_type != 'integer' THEN
        RAISE EXCEPTION 'Users table has id of type %. Expected integer.', users_id_type;
    END IF;
END $$;

-- Create a temporary mapping table for user IDs
CREATE TEMPORARY TABLE user_id_mapping (
    text_id TEXT,
    int_id INTEGER
);

-- Populate with existing mappings if needed
-- This is a placeholder - in a real scenario, you would need to populate this table
-- with mappings from text user IDs to integer user IDs
-- INSERT INTO user_id_mapping SELECT id::text, id FROM users;

-- Update accommodations.user_id
DO $$
BEGIN
    -- First check if the column is text
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'accommodations' AND column_name = 'user_id' AND data_type = 'text'
    ) THEN
        -- Create a backup of the user_id column
        ALTER TABLE accommodations ADD COLUMN user_id_backup TEXT;
        UPDATE accommodations SET user_id_backup = user_id WHERE user_id IS NOT NULL;
        
        -- Update the column type
        ALTER TABLE accommodations ALTER COLUMN user_id TYPE INTEGER USING (user_id::INTEGER);
        
        RAISE NOTICE 'Updated accommodations.user_id to INTEGER';
    ELSE
        RAISE NOTICE 'accommodations.user_id is already INTEGER or does not exist';
    END IF;
END $$;

-- Update attractions.user_id
DO $$
BEGIN
    -- First check if the column is text
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'attractions' AND column_name = 'user_id' AND data_type = 'text'
    ) THEN
        -- Create a backup of the user_id column
        ALTER TABLE attractions ADD COLUMN user_id_backup TEXT;
        UPDATE attractions SET user_id_backup = user_id WHERE user_id IS NOT NULL;
        
        -- Update the column type
        ALTER TABLE attractions ALTER COLUMN user_id TYPE INTEGER USING (user_id::INTEGER);
        
        RAISE NOTICE 'Updated attractions.user_id to INTEGER';
    ELSE
        RAISE NOTICE 'attractions.user_id is already INTEGER or does not exist';
    END IF;
END $$;

-- Update restaurants.user_id
DO $$
BEGIN
    -- First check if the column is text
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'restaurants' AND column_name = 'user_id' AND data_type = 'text'
    ) THEN
        -- Create a backup of the user_id column
        ALTER TABLE restaurants ADD COLUMN user_id_backup TEXT;
        UPDATE restaurants SET user_id_backup = user_id WHERE user_id IS NOT NULL;
        
        -- Update the column type
        ALTER TABLE restaurants ALTER COLUMN user_id TYPE INTEGER USING (user_id::INTEGER);
        
        RAISE NOTICE 'Updated restaurants.user_id to INTEGER';
    ELSE
        RAISE NOTICE 'restaurants.user_id is already INTEGER or does not exist';
    END IF;
END $$;

-- Update itineraries.user_id
DO $$
BEGIN
    -- First check if the column is text
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'itineraries' AND column_name = 'user_id' AND data_type = 'text'
    ) THEN
        -- Create a backup of the user_id column
        ALTER TABLE itineraries ADD COLUMN user_id_backup TEXT;
        UPDATE itineraries SET user_id_backup = user_id WHERE user_id IS NOT NULL;
        
        -- Update the column type
        ALTER TABLE itineraries ALTER COLUMN user_id TYPE INTEGER USING (user_id::INTEGER);
        
        RAISE NOTICE 'Updated itineraries.user_id to INTEGER';
    ELSE
        RAISE NOTICE 'itineraries.user_id is already INTEGER or does not exist';
    END IF;
END $$;

-- Log the migration completion
DO $$
BEGIN
    RAISE NOTICE 'User ID inconsistency fixed successfully';
END $$;

-- Update the schema version if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'schema_migrations') THEN
        INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
        VALUES ('20250710', 'fix_user_id_inconsistency', NOW(), md5('20250710_fix_user_id_inconsistency'), 0, 'success')
        ON CONFLICT (version) DO NOTHING;
    END IF;
END $$;

COMMIT;
