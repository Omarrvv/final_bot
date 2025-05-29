-- Migration: 005_standardize_timestamp_columns.sql
-- Purpose: Standardize timestamp column naming and data types across all tables.
-- This migration ensures consistent use of created_at and updated_at columns.

-- Begin transaction
BEGIN;

-- 1. Fix analytics table timestamp column
ALTER TABLE analytics RENAME COLUMN "timestamp" TO created_at;
ALTER TABLE analytics ALTER COLUMN created_at TYPE timestamp with time zone USING created_at::timestamp with time zone;

-- 2. Fix analytics_events table timestamp column if it exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'analytics_events'
        AND column_name = 'timestamp'
    ) THEN
        ALTER TABLE analytics_events RENAME COLUMN "timestamp" TO created_at;
    END IF;
END $$;

-- 3. Fix chat_logs table timestamp column if it exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'chat_logs'
        AND column_name = 'timestamp'
    ) THEN
        ALTER TABLE chat_logs RENAME COLUMN "timestamp" TO created_at;
    END IF;
END $$;

-- 4. Fix vector_search_metrics table timestamp column if it exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'vector_search_metrics'
        AND column_name = 'timestamp'
    ) THEN
        ALTER TABLE vector_search_metrics RENAME COLUMN "timestamp" TO created_at;
    END IF;
END $$;

-- 5. Fix connection_pool_stats table timestamp column if it exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'connection_pool_stats'
        AND column_name = 'timestamp'
    ) THEN
        ALTER TABLE connection_pool_stats RENAME COLUMN "timestamp" TO created_at;
    END IF;
END $$;

-- 6. Fix sessions table timestamp columns
-- First, add new properly typed columns
ALTER TABLE sessions ADD COLUMN created_at_new timestamp with time zone;
ALTER TABLE sessions ADD COLUMN updated_at_new timestamp with time zone;
ALTER TABLE sessions ADD COLUMN expires_at_new timestamp with time zone;

-- Migrate data from text columns to properly typed columns
UPDATE sessions
SET
    created_at_new = CASE
                        WHEN created_at IS NULL THEN NULL
                        ELSE created_at::timestamp with time zone
                     END,
    updated_at_new = CASE
                        WHEN updated_at IS NULL THEN NULL
                        ELSE updated_at::timestamp with time zone
                     END,
    expires_at_new = CASE
                        WHEN expires_at IS NULL THEN NULL
                        ELSE expires_at::timestamp with time zone
                     END;

-- Drop old columns and rename new ones
ALTER TABLE sessions DROP COLUMN created_at;
ALTER TABLE sessions DROP COLUMN updated_at;
ALTER TABLE sessions DROP COLUMN expires_at;

ALTER TABLE sessions RENAME COLUMN created_at_new TO created_at;
ALTER TABLE sessions RENAME COLUMN updated_at_new TO updated_at;
ALTER TABLE sessions RENAME COLUMN expires_at_new TO expires_at;

-- 7. Add updated_at columns with triggers where missing
-- First, create a function for the trigger
CREATE OR REPLACE FUNCTION update_timestamp() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Check each table and add updated_at column and trigger if needed
DO $$
DECLARE
    table_rec RECORD;
    has_updated_at BOOLEAN;
    trigger_exists BOOLEAN;
BEGIN
    FOR table_rec IN
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        AND table_name NOT IN ('schema_migrations', 'vector_indexes', 'vector_search_metrics')
    LOOP
        -- Check if updated_at column exists
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = table_rec.table_name
            AND column_name = 'updated_at'
        ) INTO has_updated_at;

        -- Check if update_timestamp trigger exists
        SELECT EXISTS (
            SELECT 1 FROM pg_trigger
            JOIN pg_proc ON pg_trigger.tgfoid = pg_proc.oid
            JOIN pg_class ON pg_trigger.tgrelid = pg_class.oid
            WHERE pg_class.relname = table_rec.table_name
            AND pg_proc.proname = 'update_timestamp'
        ) INTO trigger_exists;

        -- Add updated_at column if it doesn't exist
        IF NOT has_updated_at THEN
            EXECUTE format('
                ALTER TABLE %I ADD COLUMN updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
            ', table_rec.table_name);

            RAISE NOTICE 'Added updated_at column to %', table_rec.table_name;
        END IF;

        -- Add trigger if it doesn't exist
        IF has_updated_at AND NOT trigger_exists THEN
            EXECUTE format('
                CREATE TRIGGER update_timestamp
                BEFORE UPDATE ON %I
                FOR EACH ROW
                EXECUTE FUNCTION update_timestamp()
            ', table_rec.table_name);

            RAISE NOTICE 'Added update_timestamp trigger to %', table_rec.table_name;
        END IF;
    END LOOP;
END $$;

-- 8. Add created_at columns where missing
DO $$
DECLARE
    table_rec RECORD;
    has_created_at BOOLEAN;
BEGIN
    FOR table_rec IN
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        AND table_name NOT IN ('schema_migrations', 'vector_indexes', 'vector_search_metrics')
    LOOP
        -- Check if created_at column exists
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = table_rec.table_name
            AND column_name = 'created_at'
        ) INTO has_created_at;

        -- Add created_at column if it doesn't exist
        IF NOT has_created_at THEN
            EXECUTE format('
                ALTER TABLE %I ADD COLUMN created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
            ', table_rec.table_name);

            RAISE NOTICE 'Added created_at column to %', table_rec.table_name;
        END IF;
    END LOOP;
END $$;

-- 9. Add comments to timestamp columns
DO $$
DECLARE
    table_rec RECORD;
    has_created_at BOOLEAN;
    has_updated_at BOOLEAN;
BEGIN
    FOR table_rec IN
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        AND table_name NOT IN ('schema_migrations', 'vector_indexes', 'vector_search_metrics')
    LOOP
        -- Check if created_at column exists
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = table_rec.table_name
            AND column_name = 'created_at'
        ) INTO has_created_at;

        -- Check if updated_at column exists
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = table_rec.table_name
            AND column_name = 'updated_at'
        ) INTO has_updated_at;

        -- Add comments
        IF has_created_at THEN
            EXECUTE format('
                COMMENT ON COLUMN %I.created_at IS ''Timestamp when the record was created''
            ', table_rec.table_name);
        END IF;

        IF has_updated_at THEN
            EXECUTE format('
                COMMENT ON COLUMN %I.updated_at IS ''Timestamp when the record was last updated''
            ', table_rec.table_name);
        END IF;
    END LOOP;
END $$;

-- Commit transaction
COMMIT;
