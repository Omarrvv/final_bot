-- Migration: Standardize Foreign Key Constraints
-- Date: 2025-07-04
-- Description: Standardize ON DELETE and ON UPDATE rules for foreign key constraints
-- to ensure consistent behavior across the database.

-- Constraint Strategy:
-- 1. For category references (e.g., category_id): ON DELETE CASCADE, ON UPDATE CASCADE
--    Rationale: If a category is deleted or renamed, all associated records should be updated accordingly.
--
-- 2. For hierarchical references (e.g., parent_id): ON DELETE RESTRICT, ON UPDATE CASCADE
--    Rationale: Prevent deletion of parent records that have children, but allow updates to propagate.
--
-- 3. For entity references (e.g., destination_id): ON DELETE RESTRICT, ON UPDATE CASCADE
--    Rationale: Prevent accidental deletion of referenced entities, but allow updates to propagate.

BEGIN;

-- Create a function to help with constraint management
CREATE OR REPLACE FUNCTION recreate_foreign_key(
    p_table_name TEXT,
    p_column_name TEXT,
    p_referenced_table TEXT,
    p_referenced_column TEXT,
    p_delete_rule TEXT,
    p_update_rule TEXT
) RETURNS VOID AS $$
DECLARE
    v_constraint_name TEXT;
BEGIN
    -- Get the constraint name
    SELECT tc.constraint_name INTO v_constraint_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_name = p_table_name
        AND kcu.column_name = p_column_name;

    -- Drop the existing constraint
    IF v_constraint_name IS NOT NULL THEN
        EXECUTE 'ALTER TABLE ' || p_table_name || ' DROP CONSTRAINT ' || v_constraint_name;
    END IF;

    -- Create the new constraint with the specified rules
    EXECUTE 'ALTER TABLE ' || p_table_name || 
            ' ADD CONSTRAINT ' || p_table_name || '_' || p_column_name || '_fkey' ||
            ' FOREIGN KEY (' || p_column_name || ') REFERENCES ' || 
            p_referenced_table || '(' || p_referenced_column || ')' ||
            ' ON DELETE ' || p_delete_rule || ' ON UPDATE ' || p_update_rule;
END;
$$ LANGUAGE plpgsql;

-- 1. Standardize tourism_faqs constraints
-- Already has ON DELETE CASCADE, but need to update ON UPDATE to CASCADE
SELECT recreate_foreign_key(
    'tourism_faqs',
    'category_id',
    'faq_categories',
    'id',
    'CASCADE',
    'CASCADE'
);

-- 2. Standardize destinations constraints
-- Change parent_id from NO ACTION to RESTRICT for deletion and CASCADE for update
SELECT recreate_foreign_key(
    'destinations',
    'parent_id',
    'destinations',
    'id',
    'RESTRICT',
    'CASCADE'
);

-- Change type from NO ACTION to RESTRICT for deletion and CASCADE for update
SELECT recreate_foreign_key(
    'destinations',
    'type',
    'destination_types',
    'type',
    'RESTRICT',
    'CASCADE'
);

-- 3. Standardize transportation_routes constraints
-- Change origin_id from CASCADE to RESTRICT for deletion and CASCADE for update
SELECT recreate_foreign_key(
    'transportation_routes',
    'origin_id',
    'destinations',
    'id',
    'RESTRICT',
    'CASCADE'
);

-- Change destination_id from CASCADE to RESTRICT for deletion and CASCADE for update
SELECT recreate_foreign_key(
    'transportation_routes',
    'destination_id',
    'destinations',
    'id',
    'RESTRICT',
    'CASCADE'
);

-- Change transportation_type from NO ACTION to RESTRICT for deletion and CASCADE for update
SELECT recreate_foreign_key(
    'transportation_routes',
    'transportation_type',
    'transportation_types',
    'type',
    'RESTRICT',
    'CASCADE'
);

-- 4. Standardize events_festivals constraints
-- Already has ON DELETE CASCADE, but need to update ON UPDATE to CASCADE
SELECT recreate_foreign_key(
    'events_festivals',
    'category_id',
    'event_categories',
    'id',
    'CASCADE',
    'CASCADE'
);

-- 5. Standardize practical_info constraints
-- Already has ON DELETE CASCADE, but need to update ON UPDATE to CASCADE
SELECT recreate_foreign_key(
    'practical_info',
    'category_id',
    'practical_info_categories',
    'id',
    'CASCADE',
    'CASCADE'
);

-- 6. Standardize tour_packages constraints
-- Already has ON DELETE CASCADE, but need to update ON UPDATE to CASCADE
SELECT recreate_foreign_key(
    'tour_packages',
    'category_id',
    'tour_package_categories',
    'id',
    'CASCADE',
    'CASCADE'
);

-- Drop the helper function
DROP FUNCTION recreate_foreign_key;

-- Verify the changes
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
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
AND tc.table_name IN ('tourism_faqs', 'destinations', 'transportation_routes', 'events_festivals', 'practical_info', 'tour_packages')
ORDER BY tc.table_name, kcu.column_name;

COMMIT;
