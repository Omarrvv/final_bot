-- Migration: Standardize Foreign Key Constraints
-- Date: 2025-07-10
-- Purpose: Standardize foreign key constraints across all tables

BEGIN;

-- Log the migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting migration to standardize foreign key constraints';
END $$;

-- Function to add foreign key if it doesn't exist
CREATE OR REPLACE FUNCTION add_foreign_key_if_not_exists(
    p_table TEXT,
    p_column TEXT,
    p_ref_table TEXT,
    p_ref_column TEXT,
    p_constraint_name TEXT,
    p_on_delete TEXT DEFAULT 'NO ACTION',
    p_on_update TEXT DEFAULT 'NO ACTION'
) RETURNS VOID AS $$
DECLARE
    v_constraint_exists BOOLEAN;
BEGIN
    -- Check if the constraint already exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = p_constraint_name
        AND table_name = p_table
    ) INTO v_constraint_exists;
    
    -- If the constraint doesn't exist, add it
    IF NOT v_constraint_exists THEN
        EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES %I(%I) ON DELETE %s ON UPDATE %s',
            p_table, p_constraint_name, p_column, p_ref_table, p_ref_column, p_on_delete, p_on_update);
        RAISE NOTICE 'Added foreign key constraint % to table %', p_constraint_name, p_table;
    ELSE
        RAISE NOTICE 'Foreign key constraint % already exists on table %', p_constraint_name, p_table;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Standardize foreign keys for accommodations
SELECT add_foreign_key_if_not_exists(
    'accommodations', 'city_id', 'cities', 'id', 
    'fk_accommodations_city', 'SET NULL', 'CASCADE'
);

SELECT add_foreign_key_if_not_exists(
    'accommodations', 'region_id', 'regions', 'id', 
    'fk_accommodations_region', 'SET NULL', 'CASCADE'
);

SELECT add_foreign_key_if_not_exists(
    'accommodations', 'user_id', 'users', 'id', 
    'fk_accommodations_user', 'SET NULL', 'CASCADE'
);

SELECT add_foreign_key_if_not_exists(
    'accommodations', 'type_id', 'accommodation_types', 'id', 
    'fk_accommodations_type', 'SET NULL', 'CASCADE'
);

-- Standardize foreign keys for attractions
SELECT add_foreign_key_if_not_exists(
    'attractions', 'city_id', 'cities', 'id', 
    'fk_attractions_city', 'SET NULL', 'CASCADE'
);

SELECT add_foreign_key_if_not_exists(
    'attractions', 'region_id', 'regions', 'id', 
    'fk_attractions_region', 'SET NULL', 'CASCADE'
);

SELECT add_foreign_key_if_not_exists(
    'attractions', 'user_id', 'users', 'id', 
    'fk_attractions_user', 'SET NULL', 'CASCADE'
);

SELECT add_foreign_key_if_not_exists(
    'attractions', 'type_id', 'attraction_types', 'id', 
    'fk_attractions_type', 'SET NULL', 'CASCADE'
);

SELECT add_foreign_key_if_not_exists(
    'attractions', 'subcategory_id', 'attraction_subcategories', 'id', 
    'fk_attractions_subcategory', 'SET NULL', 'CASCADE'
);

-- Standardize foreign keys for restaurants
SELECT add_foreign_key_if_not_exists(
    'restaurants', 'city_id', 'cities', 'id', 
    'fk_restaurants_city', 'SET NULL', 'CASCADE'
);

SELECT add_foreign_key_if_not_exists(
    'restaurants', 'region_id', 'regions', 'id', 
    'fk_restaurants_region', 'SET NULL', 'CASCADE'
);

SELECT add_foreign_key_if_not_exists(
    'restaurants', 'user_id', 'users', 'id', 
    'fk_restaurants_user', 'SET NULL', 'CASCADE'
);

SELECT add_foreign_key_if_not_exists(
    'restaurants', 'type_id', 'restaurant_types', 'id', 
    'fk_restaurants_type', 'SET NULL', 'CASCADE'
);

SELECT add_foreign_key_if_not_exists(
    'restaurants', 'cuisine_id', 'cuisine_types', 'id', 
    'fk_restaurants_cuisine', 'SET NULL', 'CASCADE'
);

-- Standardize foreign keys for cities
SELECT add_foreign_key_if_not_exists(
    'cities', 'region_id', 'regions', 'id', 
    'fk_cities_region', 'SET NULL', 'CASCADE'
);

SELECT add_foreign_key_if_not_exists(
    'cities', 'user_id', 'users', 'id', 
    'fk_cities_user', 'SET NULL', 'CASCADE'
);

-- Standardize foreign keys for itineraries
SELECT add_foreign_key_if_not_exists(
    'itineraries', 'user_id', 'users', 'id', 
    'fk_itineraries_user', 'SET NULL', 'CASCADE'
);

SELECT add_foreign_key_if_not_exists(
    'itineraries', 'type_id', 'itinerary_types', 'id', 
    'fk_itineraries_type', 'RESTRICT', 'CASCADE'
);

-- Drop the helper function
DROP FUNCTION add_foreign_key_if_not_exists(TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT);

-- Log the migration completion
DO $$
BEGIN
    RAISE NOTICE 'Foreign key constraints standardized successfully';
END $$;

-- Update the schema version if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'schema_migrations') THEN
        INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
        VALUES ('20250710', 'standardize_foreign_keys', NOW(), md5('20250710_standardize_foreign_keys'), 0, 'success')
        ON CONFLICT (version) DO NOTHING;
    END IF;
END $$;

COMMIT;
