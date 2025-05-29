-- Migration: 012_fix_duplicate_fk.sql
-- Purpose: Fix duplicate foreign key constraint on attraction_subcategories.parent_type

-- Begin transaction
BEGIN;

-- Drop the old constraint
ALTER TABLE attraction_subcategories DROP CONSTRAINT IF EXISTS fk_attraction_subcategories_parent_type;

-- Commit transaction
COMMIT;
