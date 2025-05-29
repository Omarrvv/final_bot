-- Migration: Remove Backup Columns
-- Date: 2025-07-10
-- Purpose: Remove redundant backup columns that were created during the migration to JSONB and vector types

BEGIN;

-- Log the migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting migration to remove backup columns';
END $$;

-- Remove backup columns from accommodations
ALTER TABLE accommodations
    DROP COLUMN IF EXISTS embedding_backup,
    DROP COLUMN IF EXISTS name_backup,
    DROP COLUMN IF EXISTS description_backup;

-- Remove backup columns from attractions
ALTER TABLE attractions
    DROP COLUMN IF EXISTS embedding_backup,
    DROP COLUMN IF EXISTS name_backup,
    DROP COLUMN IF EXISTS description_backup;

-- Remove backup columns from cities
ALTER TABLE cities
    DROP COLUMN IF EXISTS embedding_backup,
    DROP COLUMN IF EXISTS name_backup,
    DROP COLUMN IF EXISTS description_backup;

-- Remove backup columns from restaurants
ALTER TABLE restaurants
    DROP COLUMN IF EXISTS embedding_backup,
    DROP COLUMN IF EXISTS name_backup,
    DROP COLUMN IF EXISTS description_backup;

-- Log the migration completion
DO $$
BEGIN
    RAISE NOTICE 'Backup columns removed successfully';
END $$;

-- Update the schema version if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'schema_migrations') THEN
        INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
        VALUES ('20250710', 'remove_backup_columns', NOW(), md5('20250710_remove_backup_columns'), 0, 'success')
        ON CONFLICT (version) DO NOTHING;
    END IF;
END $$;

COMMIT;
