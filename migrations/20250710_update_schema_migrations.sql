-- Migration: Update Schema Migrations for Backup Columns Removal
-- Date: 2025-07-10
-- Purpose: Record the execution of the backup columns removal migration

BEGIN;

-- Update the schema migrations table
INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
VALUES ('20250710_2', 'remove_backup_columns', NOW(), md5('20250710_remove_backup_columns'), 0, 'success')
ON CONFLICT (version) DO NOTHING;

COMMIT;
