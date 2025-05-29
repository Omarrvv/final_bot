-- Migration: 022_standardize_sessions_id.sql
-- Purpose: Standardize ID for sessions table and update foreign key references

-- Begin transaction
BEGIN;

-- 1. Create a mapping table
CREATE TABLE id_mapping_sessions (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

-- 2. Populate mapping table
INSERT INTO id_mapping_sessions (old_id)
SELECT id FROM sessions ORDER BY id;

-- 3. Add new integer ID column
ALTER TABLE sessions ADD COLUMN integer_id serial;

-- 4. Check for tables referencing sessions.id
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
          AND ccu.table_name = 'sessions'
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
                SET %I_integer = (SELECT new_id FROM id_mapping_sessions WHERE old_id = %I::text)
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

-- 5. Drop old primary key constraint
ALTER TABLE sessions DROP CONSTRAINT IF EXISTS sessions_pkey;

-- 6. Drop old ID column
ALTER TABLE sessions DROP COLUMN id;

-- 7. Rename new ID column
ALTER TABLE sessions RENAME COLUMN integer_id TO id;

-- 8. Add primary key constraint
ALTER TABLE sessions ADD PRIMARY KEY (id);

-- 9. Add foreign key constraints back
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
          AND ccu.table_name = 'sessions'
          AND ccu.column_name = 'id'
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
                ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES sessions(id) ON UPDATE CASCADE ON DELETE SET NULL;
            ', ref_table, ref_table || '_' || ref_column || '_fkey', ref_column);
        END IF;
    END LOOP;
END $$;

-- 10. Clean up mapping table
DROP TABLE id_mapping_sessions;

-- Commit transaction
COMMIT;
