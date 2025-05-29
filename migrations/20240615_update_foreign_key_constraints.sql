-- Migration: Update Foreign Key Constraints
-- Date: 2024-06-15
-- Updates foreign key constraints with appropriate ON DELETE and ON UPDATE actions

-- 1. Drop existing constraints that need to be changed
ALTER TABLE attractions DROP CONSTRAINT IF EXISTS fk_attractions_type;
ALTER TABLE accommodations DROP CONSTRAINT IF EXISTS fk_accommodations_type;
ALTER TABLE cities DROP CONSTRAINT IF EXISTS cities_user_id_fkey;
ALTER TABLE cities DROP CONSTRAINT IF EXISTS fk_cities_user;

-- 2. Recreate constraints with appropriate actions

-- attractions.type_id: Change ON DELETE from SET NULL to RESTRICT
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_attractions_type' AND conrelid = 'attractions'::regclass
    ) THEN
        ALTER TABLE attractions
        ADD CONSTRAINT fk_attractions_type
        FOREIGN KEY (type_id) REFERENCES attraction_types(type)
        ON DELETE RESTRICT ON UPDATE CASCADE;
    END IF;
END $$;

-- accommodations.type_id: Change ON DELETE from SET NULL to RESTRICT
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_accommodations_type' AND conrelid = 'accommodations'::regclass
    ) THEN
        ALTER TABLE accommodations
        ADD CONSTRAINT fk_accommodations_type
        FOREIGN KEY (type_id) REFERENCES accommodation_types(type)
        ON DELETE RESTRICT ON UPDATE CASCADE;
    END IF;
END $$;

-- cities.user_id: Change ON UPDATE from NO ACTION to CASCADE
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_cities_user' AND conrelid = 'cities'::regclass
    ) THEN
        ALTER TABLE cities
        ADD CONSTRAINT fk_cities_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE SET NULL ON UPDATE CASCADE;
    END IF;
END $$;

-- 3. Verify constraints
-- This section contains queries that can be run manually to verify the migration
-- They are commented out to prevent them from being executed during migration

/*
-- Verify foreign key constraints and their actions
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS referenced_table,
    ccu.column_name AS referenced_column,
    rc.delete_rule,
    rc.update_rule
FROM
    information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        AND ccu.table_schema = tc.table_schema
    JOIN information_schema.referential_constraints AS rc
        ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_name IN ('attractions', 'accommodations', 'cities')
ORDER BY tc.table_name, kcu.column_name;
*/
