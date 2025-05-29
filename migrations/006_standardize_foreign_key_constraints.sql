-- Migration: 006_standardize_foreign_key_constraints.sql
-- Purpose: Standardize foreign key constraint rules (ON DELETE/UPDATE) across all tables.
-- This migration ensures consistent behavior when referenced records are updated or deleted.

-- Begin transaction
BEGIN;

-- 1. Create a temporary table to store foreign key information
CREATE TEMPORARY TABLE fk_constraints AS
SELECT
    tc.table_schema,
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.update_rule,
    rc.delete_rule
FROM
    information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
    JOIN information_schema.referential_constraints AS rc
      ON rc.constraint_name = tc.constraint_name
      AND rc.constraint_schema = tc.table_schema
WHERE
    tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public';

-- 2. Standardize foreign key constraints for tourism_faqs if it exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND table_name = 'tourism_faqs'
        AND constraint_name = 'tourism_faqs_category_id_fkey'
    ) THEN
        -- First, drop the existing constraint
        ALTER TABLE tourism_faqs DROP CONSTRAINT tourism_faqs_category_id_fkey;

        -- Then, recreate it with standard rules
        ALTER TABLE tourism_faqs
        ADD CONSTRAINT tourism_faqs_category_id_fkey
        FOREIGN KEY (category_id) REFERENCES faq_categories(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;
    END IF;
END $$;

-- 3. Standardize foreign key constraints for destinations if it exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND table_name = 'destinations'
        AND constraint_name = 'destinations_parent_id_fkey'
    ) THEN
        -- First, drop the existing constraint
        ALTER TABLE destinations DROP CONSTRAINT destinations_parent_id_fkey;

        -- Then, recreate it with standard rules
        ALTER TABLE destinations
        ADD CONSTRAINT destinations_parent_id_fkey
        FOREIGN KEY (parent_id) REFERENCES destinations(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;
    END IF;
END $$;

-- 4. Standardize foreign key constraints for transportation_routes if they exist
DO $$
BEGIN
    -- Check and fix origin_id constraint
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND table_name = 'transportation_routes'
        AND constraint_name = 'transportation_routes_origin_id_fkey'
    ) THEN
        ALTER TABLE transportation_routes DROP CONSTRAINT transportation_routes_origin_id_fkey;

        ALTER TABLE transportation_routes
        ADD CONSTRAINT transportation_routes_origin_id_fkey
        FOREIGN KEY (origin_id) REFERENCES destinations(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;
    END IF;

    -- Check and fix destination_id constraint
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND table_name = 'transportation_routes'
        AND constraint_name = 'transportation_routes_destination_id_fkey'
    ) THEN
        ALTER TABLE transportation_routes DROP CONSTRAINT transportation_routes_destination_id_fkey;

        ALTER TABLE transportation_routes
        ADD CONSTRAINT transportation_routes_destination_id_fkey
        FOREIGN KEY (destination_id) REFERENCES destinations(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;
    END IF;

    -- Check and fix transportation_type constraint
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND table_name = 'transportation_routes'
        AND constraint_name = 'transportation_routes_transportation_type_fkey'
    ) THEN
        ALTER TABLE transportation_routes DROP CONSTRAINT transportation_routes_transportation_type_fkey;

        ALTER TABLE transportation_routes
        ADD CONSTRAINT transportation_routes_transportation_type_fkey
        FOREIGN KEY (transportation_type) REFERENCES transportation_types(type)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;
    END IF;
END $$;

-- 5. Standardize foreign key constraints for restaurants if they exist
DO $$
BEGIN
    -- Check and fix city_id constraint
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND table_name = 'restaurants'
        AND constraint_name = 'restaurants_city_id_fkey'
    ) THEN
        ALTER TABLE restaurants DROP CONSTRAINT restaurants_city_id_fkey;

        ALTER TABLE restaurants
        ADD CONSTRAINT restaurants_city_id_fkey
        FOREIGN KEY (city_id) REFERENCES cities(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL;
    END IF;

    -- Check and fix region_id constraint
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND table_name = 'restaurants'
        AND constraint_name = 'restaurants_region_id_fkey'
    ) THEN
        ALTER TABLE restaurants DROP CONSTRAINT restaurants_region_id_fkey;

        ALTER TABLE restaurants
        ADD CONSTRAINT restaurants_region_id_fkey
        FOREIGN KEY (region_id) REFERENCES regions(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL;
    END IF;

    -- Check and fix type_id constraint
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND table_name = 'restaurants'
        AND constraint_name = 'restaurants_type_id_fkey'
    ) THEN
        ALTER TABLE restaurants DROP CONSTRAINT restaurants_type_id_fkey;

        ALTER TABLE restaurants
        ADD CONSTRAINT restaurants_type_id_fkey
        FOREIGN KEY (type_id) REFERENCES restaurant_types(type)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;
    END IF;

    -- Check and fix cuisine_id constraint
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND table_name = 'restaurants'
        AND constraint_name = 'restaurants_cuisine_id_fkey'
    ) THEN
        ALTER TABLE restaurants DROP CONSTRAINT restaurants_cuisine_id_fkey;

        ALTER TABLE restaurants
        ADD CONSTRAINT restaurants_cuisine_id_fkey
        FOREIGN KEY (cuisine_id) REFERENCES cuisines(type)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;
    END IF;
END $$;

-- 6. Standardize foreign key constraints for hotels if they exist
DO $$
BEGIN
    -- Check and fix type constraint
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND table_name = 'hotels'
        AND constraint_name = 'hotels_type_fkey'
    ) THEN
        ALTER TABLE hotels DROP CONSTRAINT hotels_type_fkey;
    END IF;

    -- Check and fix type_id constraint
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND table_name = 'hotels'
        AND constraint_name = 'hotels_type_id_fkey'
    ) THEN
        ALTER TABLE hotels DROP CONSTRAINT hotels_type_id_fkey;

        ALTER TABLE hotels
        ADD CONSTRAINT hotels_type_id_fkey
        FOREIGN KEY (type_id) REFERENCES accommodation_types(type)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;
    END IF;
END $$;

-- 7. Add missing foreign key constraints
-- Add constraint for hotels.city_id if it doesn't exist
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'hotels'
        AND column_name = 'city_id'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND table_name = 'hotels'
        AND constraint_name = 'hotels_city_id_fkey'
    ) THEN
        ALTER TABLE hotels
        ADD CONSTRAINT hotels_city_id_fkey
        FOREIGN KEY (city_id) REFERENCES cities(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL;
    END IF;
END $$;

-- 8. Document the standardized foreign key constraint rules
CREATE OR REPLACE FUNCTION document_fk_rules() RETURNS void AS $$
BEGIN
    RAISE NOTICE 'Foreign Key Constraint Standards:';
    RAISE NOTICE '1. ON UPDATE CASCADE - When a referenced record is updated, update the foreign key to match.';
    RAISE NOTICE '2. ON DELETE RESTRICT - Prevent deletion of referenced records if they are in use.';
    RAISE NOTICE '3. ON DELETE SET NULL - When a referenced record is deleted, set the foreign key to NULL.';
    RAISE NOTICE '4. ON DELETE CASCADE - When a referenced record is deleted, delete the referencing records too.';
    RAISE NOTICE '';
    RAISE NOTICE 'Usage Guidelines:';
    RAISE NOTICE '- Use RESTRICT for core reference data that should not be deleted if in use.';
    RAISE NOTICE '- Use SET NULL for optional relationships where the referenced entity can be removed.';
    RAISE NOTICE '- Use CASCADE for child records that cannot exist without their parent.';
END;
$$ LANGUAGE plpgsql;

SELECT document_fk_rules();

-- Clean up temporary objects
DROP FUNCTION document_fk_rules();
DROP TABLE fk_constraints;

-- Commit transaction
COMMIT;
