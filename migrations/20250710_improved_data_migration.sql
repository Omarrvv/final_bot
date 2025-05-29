-- Improved Data Migration Script
-- Date: 2025-07-10
-- Purpose: Properly migrate data from array columns to junction tables with accurate ID mapping

BEGIN;

-- Log the migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting improved data migration from array columns to junction tables';
END $$;

-- Function to migrate attraction relationships with proper ID mapping
CREATE OR REPLACE FUNCTION migrate_attraction_relationships_improved() RETURNS void AS $$
DECLARE
    attraction_record RECORD;
    related_id INTEGER;
    related_name TEXT;
    migration_count INTEGER := 0;
BEGIN
    -- Don't clear existing data, just add missing relationships
    
    FOR attraction_record IN SELECT id, related_attractions FROM attractions 
                            WHERE related_attractions IS NOT NULL 
                            AND array_length(related_attractions, 1) > 0
    LOOP
        FOREACH related_name IN ARRAY attraction_record.related_attractions
        LOOP
            -- Try to find the related attraction by name or ID
            BEGIN
                -- First try to convert the related_name to integer (if it's already an ID)
                related_id := related_name::INTEGER;
                
                -- Verify this ID exists
                PERFORM 1 FROM attractions WHERE id = related_id;
                
                IF NOT FOUND THEN
                    related_id := NULL;
                END IF;
            EXCEPTION WHEN OTHERS THEN
                -- If conversion fails, try to find by name
                SELECT id INTO related_id FROM attractions 
                WHERE name->>'en' = related_name 
                   OR name->>'ar' = related_name
                   OR name_en = related_name  -- Try legacy columns if they exist
                   OR name_ar = related_name;
            END;
            
            -- If we found a related attraction and the relationship doesn't exist yet
            IF related_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM attraction_relationships 
                WHERE attraction_id = attraction_record.id 
                AND related_attraction_id = related_id
            ) THEN
                -- Insert into junction table
                INSERT INTO attraction_relationships (attraction_id, related_attraction_id, relationship_type)
                VALUES (attraction_record.id, related_id, 'related');
                
                migration_count := migration_count + 1;
            END IF;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Migrated % attraction relationships', migration_count;
END;
$$ LANGUAGE plpgsql;

-- Function to migrate itinerary attractions with proper ID mapping
CREATE OR REPLACE FUNCTION migrate_itinerary_attractions_improved() RETURNS void AS $$
DECLARE
    itinerary_record RECORD;
    attraction_id INTEGER;
    attraction_name TEXT;
    order_idx INTEGER;
    migration_count INTEGER := 0;
BEGIN
    -- Don't clear existing data, just add missing relationships
    
    FOR itinerary_record IN SELECT id, attractions FROM itineraries 
                           WHERE attractions IS NOT NULL 
                           AND array_length(attractions, 1) > 0
    LOOP
        order_idx := 1;
        FOREACH attraction_name IN ARRAY itinerary_record.attractions
        LOOP
            -- Try to find the attraction by name or ID
            BEGIN
                -- First try to convert to integer (if it's already an ID)
                attraction_id := attraction_name::INTEGER;
                
                -- Verify this ID exists
                PERFORM 1 FROM attractions WHERE id = attraction_id;
                
                IF NOT FOUND THEN
                    attraction_id := NULL;
                END IF;
            EXCEPTION WHEN OTHERS THEN
                -- If conversion fails, try to find by name
                SELECT id INTO attraction_id FROM attractions 
                WHERE name->>'en' = attraction_name 
                   OR name->>'ar' = attraction_name
                   OR name_en = attraction_name  -- Try legacy columns if they exist
                   OR name_ar = attraction_name;
            END;
            
            -- If we found an attraction and the relationship doesn't exist yet
            IF attraction_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM itinerary_attractions 
                WHERE itinerary_id = itinerary_record.id 
                AND attraction_id = attraction_id
            ) THEN
                -- Insert into junction table
                INSERT INTO itinerary_attractions (itinerary_id, attraction_id, order_index, day_number)
                VALUES (itinerary_record.id, attraction_id, order_idx, CEIL(order_idx::float / 3));
                
                migration_count := migration_count + 1;
            END IF;
            
            order_idx := order_idx + 1;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Migrated % itinerary attractions', migration_count;
END;
$$ LANGUAGE plpgsql;

-- Function to migrate itinerary cities with proper ID mapping
CREATE OR REPLACE FUNCTION migrate_itinerary_cities_improved() RETURNS void AS $$
DECLARE
    itinerary_record RECORD;
    city_id INTEGER;
    city_name TEXT;
    order_idx INTEGER;
    migration_count INTEGER := 0;
BEGIN
    -- Don't clear existing data, just add missing relationships
    
    FOR itinerary_record IN SELECT id, cities FROM itineraries 
                           WHERE cities IS NOT NULL 
                           AND array_length(cities, 1) > 0
    LOOP
        order_idx := 1;
        FOREACH city_name IN ARRAY itinerary_record.cities
        LOOP
            -- Try to find the city by name or ID
            BEGIN
                -- First try to convert to integer (if it's already an ID)
                city_id := city_name::INTEGER;
                
                -- Verify this ID exists
                PERFORM 1 FROM cities WHERE id = city_id;
                
                IF NOT FOUND THEN
                    city_id := NULL;
                END IF;
            EXCEPTION WHEN OTHERS THEN
                -- If conversion fails, try to find by name
                SELECT id INTO city_id FROM cities 
                WHERE name->>'en' = city_name 
                   OR name->>'ar' = city_name
                   OR name_en = city_name  -- Try legacy columns if they exist
                   OR name_ar = city_name;
            END;
            
            -- If we found a city and the relationship doesn't exist yet
            IF city_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM itinerary_cities 
                WHERE itinerary_id = itinerary_record.id 
                AND city_id = city_id
            ) THEN
                -- Insert into junction table
                INSERT INTO itinerary_cities (itinerary_id, city_id, order_index, stay_duration)
                VALUES (itinerary_record.id, city_id, order_idx, 2);
                
                migration_count := migration_count + 1;
            END IF;
            
            order_idx := order_idx + 1;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Migrated % itinerary cities', migration_count;
END;
$$ LANGUAGE plpgsql;

-- Execute the improved migration functions
SELECT migrate_attraction_relationships_improved();
SELECT migrate_itinerary_attractions_improved();
SELECT migrate_itinerary_cities_improved();

-- Drop the migration functions
DROP FUNCTION migrate_attraction_relationships_improved();
DROP FUNCTION migrate_itinerary_attractions_improved();
DROP FUNCTION migrate_itinerary_cities_improved();

-- Log the migration completion
DO $$
BEGIN
    RAISE NOTICE 'Improved data migration completed successfully';
END $$;

-- Update the schema version if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'schema_migrations') THEN
        INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
        VALUES ('20250710_2', 'improved_data_migration', NOW(), md5('20250710_improved_data_migration'), 0, 'success')
        ON CONFLICT (version) DO NOTHING;
    END IF;
END $$;

COMMIT;
