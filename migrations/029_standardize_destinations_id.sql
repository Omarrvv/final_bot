-- Migration: 029_standardize_destinations_id.sql
-- Purpose: Standardize ID for destinations table and update foreign key references

-- Begin transaction
BEGIN;

-- 1. Create a mapping table
CREATE TABLE id_mapping_destinations (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

-- 2. Populate mapping table
INSERT INTO id_mapping_destinations (old_id)
SELECT id FROM destinations ORDER BY id;

-- 3. Add new integer ID column
ALTER TABLE destinations ADD COLUMN integer_id serial;

-- 4. Check for tables referencing destinations.id
DO $$
DECLARE
    ref_table text;
    ref_column text;
BEGIN
    FOR ref_table, ref_column IN
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND ccu.table_name = 'destinations'
          AND ccu.column_name = 'id'
    LOOP
        -- Check if the column exists
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = ref_table
            AND column_name = ref_column
        ) THEN
            -- Drop foreign key constraint
            EXECUTE format('
                DO $inner$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.table_constraints
                        WHERE table_name = %L
                        AND constraint_type = ''FOREIGN KEY''
                        AND constraint_name LIKE %L
                    ) THEN
                        ALTER TABLE %I DROP CONSTRAINT %I;
                    END IF;
                END $inner$;
            ', ref_table, ref_column || '%fkey', ref_table, ref_table || '_' || ref_column || '_fkey');
            
            -- Add integer column for new foreign key
            EXECUTE format('
                ALTER TABLE %I ADD COLUMN %I_integer integer;
            ', ref_table, ref_column);
            
            -- Update with mapped IDs
            EXECUTE format('
                UPDATE %I
                SET %I_integer = (SELECT new_id FROM id_mapping_destinations WHERE old_id = %I::text)
                WHERE %I IS NOT NULL;
            ', ref_table, ref_column, ref_column, ref_column);
            
            -- Drop old foreign key column
            EXECUTE format('
                ALTER TABLE %I DROP COLUMN %I;
            ', ref_table, ref_column);
            
            -- Rename new foreign key column
            EXECUTE format('
                ALTER TABLE %I RENAME COLUMN %I_integer TO %I;
            ', ref_table, ref_column, ref_column);
        END IF;
    END LOOP;
END $$;

-- 5. Handle self-referencing foreign key (parent_id)
-- Drop the constraint
ALTER TABLE destinations DROP CONSTRAINT IF EXISTS destinations_parent_id_fkey;

-- Add integer column for new foreign key
ALTER TABLE destinations ADD COLUMN parent_id_integer integer;

-- Update with mapped IDs
UPDATE destinations
SET parent_id_integer = (SELECT new_id FROM id_mapping_destinations WHERE old_id = parent_id::text)
WHERE parent_id IS NOT NULL;

-- Drop old foreign key column
ALTER TABLE destinations DROP COLUMN parent_id;

-- Rename new foreign key column
ALTER TABLE destinations RENAME COLUMN parent_id_integer TO parent_id;

-- 6. Drop old primary key constraint
ALTER TABLE destinations DROP CONSTRAINT IF EXISTS destinations_pkey;

-- 7. Drop old ID column
ALTER TABLE destinations DROP COLUMN id;

-- 8. Rename new ID column
ALTER TABLE destinations RENAME COLUMN integer_id TO id;

-- 9. Add primary key constraint
ALTER TABLE destinations ADD PRIMARY KEY (id);

-- 10. Add self-referencing foreign key constraint back
ALTER TABLE destinations
ADD CONSTRAINT destinations_parent_id_fkey
FOREIGN KEY (parent_id) REFERENCES destinations(id) ON UPDATE CASCADE ON DELETE RESTRICT;

-- 11. Add foreign key constraints back for other tables
DO $$
DECLARE
    ref_table text;
    ref_column text;
BEGIN
    FOR ref_table, ref_column IN
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND ccu.table_name = 'destinations'
          AND ccu.column_name = 'id'
          AND ref_table != 'destinations' -- Skip self-referencing constraint
    LOOP
        -- Check if the column exists
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = ref_table
            AND column_name = ref_column
        ) THEN
            -- Add foreign key constraint
            EXECUTE format('
                ALTER TABLE %I
                ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES destinations(id) ON UPDATE CASCADE ON DELETE SET NULL;
            ', ref_table, ref_table || '_' || ref_column || '_fkey', ref_column);
        END IF;
    END LOOP;
END $$;

-- 12. Clean up mapping table
DROP TABLE id_mapping_destinations;

-- Commit transaction
COMMIT;
