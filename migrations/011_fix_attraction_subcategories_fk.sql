-- Migration: 011_fix_attraction_subcategories_fk.sql
-- Purpose: Fix the attraction_subcategories.parent_type foreign key constraint

-- Begin transaction
BEGIN;

-- Drop and recreate the constraint
ALTER TABLE attraction_subcategories DROP CONSTRAINT IF EXISTS attraction_subcategories_parent_type_fkey;

-- Add the constraint with standardized rules
ALTER TABLE attraction_subcategories ADD CONSTRAINT attraction_subcategories_parent_type_fkey
FOREIGN KEY (parent_type) REFERENCES attraction_types(type)
ON UPDATE CASCADE
ON DELETE CASCADE;

-- Commit transaction
COMMIT;
