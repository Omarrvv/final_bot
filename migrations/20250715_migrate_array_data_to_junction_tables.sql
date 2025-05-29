-- Migration: Migrate Array Data to Junction Tables
-- Date: 2025-07-15
-- Purpose: Move data from array columns to junction tables and prepare for dropping array columns

BEGIN;

-- Log the migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting migration of array data to junction tables';
END $$;

-- 1. Migrate attractions.related_attractions to attraction_relationships
DO $$
DECLARE
    attraction_record RECORD;
    related_id TEXT;
    related_attraction_id INTEGER;
    attraction_id INTEGER;
BEGIN
    RAISE NOTICE 'Migrating attractions.related_attractions to attraction_relationships';
    
    FOR attraction_record IN 
        SELECT id, related_attractions 
        FROM attractions 
        WHERE array_length(related_attractions, 1) > 0
    LOOP
        attraction_id := attraction_record.id;
        
        FOREACH related_id IN ARRAY attraction_record.related_attractions
        LOOP
            -- Convert text ID to integer ID
            BEGIN
                related_attraction_id := related_id::INTEGER;
                
                -- Insert into junction table if not already exists
                INSERT INTO attraction_relationships 
                    (attraction_id, related_attraction_id, relationship_type, created_at, updated_at)
                VALUES 
                    (attraction_id, related_attraction_id, 'related', NOW(), NOW())
                ON CONFLICT (attraction_id, related_attraction_id) DO NOTHING;
                
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Error processing related attraction: % -> %. Error: %', 
                    attraction_id, related_id, SQLERRM;
            END;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Completed migration of attractions.related_attractions';
END $$;

-- 2. Migrate itineraries.attractions to itinerary_attractions
DO $$
DECLARE
    itinerary_record RECORD;
    attraction_id_text TEXT;
    attraction_id_int INTEGER;
    order_idx INTEGER;
BEGIN
    RAISE NOTICE 'Migrating itineraries.attractions to itinerary_attractions';
    
    FOR itinerary_record IN 
        SELECT id, attractions 
        FROM itineraries 
        WHERE array_length(attractions, 1) > 0
    LOOP
        order_idx := 1;
        
        FOREACH attraction_id_text IN ARRAY itinerary_record.attractions
        LOOP
            -- Convert text ID to integer ID
            BEGIN
                attraction_id_int := attraction_id_text::INTEGER;
                
                -- Insert into junction table if not already exists
                INSERT INTO itinerary_attractions 
                    (itinerary_id, attraction_id, order_index, day_number, created_at, updated_at)
                VALUES 
                    (itinerary_record.id, attraction_id_int, order_idx, CEIL(order_idx::FLOAT / 3), NOW(), NOW())
                ON CONFLICT (itinerary_id, attraction_id, day_number) DO NOTHING;
                
                order_idx := order_idx + 1;
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Error processing itinerary attraction: % -> %. Error: %', 
                    itinerary_record.id, attraction_id_text, SQLERRM;
            END;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Completed migration of itineraries.attractions';
END $$;

-- 3. Migrate itineraries.cities to itinerary_cities
DO $$
DECLARE
    itinerary_record RECORD;
    city_id_text TEXT;
    city_id_int INTEGER;
    order_idx INTEGER;
BEGIN
    RAISE NOTICE 'Migrating itineraries.cities to itinerary_cities';
    
    FOR itinerary_record IN 
        SELECT id, cities 
        FROM itineraries 
        WHERE array_length(cities, 1) > 0
    LOOP
        order_idx := 1;
        
        FOREACH city_id_text IN ARRAY itinerary_record.cities
        LOOP
            -- Convert text ID to integer ID
            BEGIN
                city_id_int := city_id_text::INTEGER;
                
                -- Insert into junction table if not already exists
                INSERT INTO itinerary_cities 
                    (itinerary_id, city_id, order_index, stay_duration, created_at, updated_at)
                VALUES 
                    (itinerary_record.id, city_id_int, order_idx, 1, NOW(), NOW())
                ON CONFLICT (itinerary_id, city_id) DO NOTHING;
                
                order_idx := order_idx + 1;
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Error processing itinerary city: % -> %. Error: %', 
                    itinerary_record.id, city_id_text, SQLERRM;
            END;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Completed migration of itineraries.cities';
END $$;

-- 4. Migrate tour_packages.attractions to tour_package_attractions
DO $$
DECLARE
    tour_package_record RECORD;
    attraction_id_text TEXT;
    attraction_id_int INTEGER;
    order_idx INTEGER;
BEGIN
    RAISE NOTICE 'Migrating tour_packages.attractions to tour_package_attractions';
    
    FOR tour_package_record IN 
        SELECT id, attractions 
        FROM tour_packages 
        WHERE array_length(attractions, 1) > 0
    LOOP
        order_idx := 1;
        
        FOREACH attraction_id_text IN ARRAY tour_package_record.attractions
        LOOP
            -- Convert text ID to integer ID
            BEGIN
                attraction_id_int := attraction_id_text::INTEGER;
                
                -- Insert into junction table if not already exists
                INSERT INTO tour_package_attractions 
                    (tour_package_id, attraction_id, order_index, day_number, created_at, updated_at)
                VALUES 
                    (tour_package_record.id, attraction_id_int, order_idx, CEIL(order_idx::FLOAT / 3), NOW(), NOW())
                ON CONFLICT (tour_package_id, attraction_id, day_number) DO NOTHING;
                
                order_idx := order_idx + 1;
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Error processing tour package attraction: % -> %. Error: %', 
                    tour_package_record.id, attraction_id_text, SQLERRM;
            END;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Completed migration of tour_packages.attractions';
END $$;

-- 5. Migrate tour_packages.destinations to tour_package_destinations
DO $$
DECLARE
    tour_package_record RECORD;
    destination_id_text TEXT;
    destination_id_int INTEGER;
    order_idx INTEGER;
BEGIN
    RAISE NOTICE 'Migrating tour_packages.destinations to tour_package_destinations';
    
    FOR tour_package_record IN 
        SELECT id, destinations 
        FROM tour_packages 
        WHERE array_length(destinations, 1) > 0
    LOOP
        order_idx := 1;
        
        FOREACH destination_id_text IN ARRAY tour_package_record.destinations
        LOOP
            -- Convert text ID to integer ID
            BEGIN
                destination_id_int := destination_id_text::INTEGER;
                
                -- Insert into junction table if not already exists
                INSERT INTO tour_package_destinations 
                    (tour_package_id, destination_id, order_index, stay_duration, created_at, updated_at)
                VALUES 
                    (tour_package_record.id, destination_id_int, order_idx, 1, NOW(), NOW())
                ON CONFLICT (tour_package_id, destination_id) DO NOTHING;
                
                order_idx := order_idx + 1;
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Error processing tour package destination: % -> %. Error: %', 
                    tour_package_record.id, destination_id_text, SQLERRM;
            END;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Completed migration of tour_packages.destinations';
END $$;

-- 6. Migrate tourism_faqs.related_destination_ids to tourism_faq_destinations
DO $$
DECLARE
    faq_record RECORD;
    destination_id_text TEXT;
    destination_id_int INTEGER;
BEGIN
    RAISE NOTICE 'Migrating tourism_faqs.related_destination_ids to tourism_faq_destinations';
    
    FOR faq_record IN 
        SELECT id, related_destination_ids 
        FROM tourism_faqs 
        WHERE array_length(related_destination_ids, 1) > 0
    LOOP
        FOREACH destination_id_text IN ARRAY faq_record.related_destination_ids
        LOOP
            -- Convert text ID to integer ID
            BEGIN
                destination_id_int := destination_id_text::INTEGER;
                
                -- Insert into junction table if not already exists
                INSERT INTO tourism_faq_destinations 
                    (tourism_faq_id, destination_id, relevance_score, created_at, updated_at)
                VALUES 
                    (faq_record.id, destination_id_int, 1.0, NOW(), NOW())
                ON CONFLICT (tourism_faq_id, destination_id) DO NOTHING;
                
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Error processing FAQ destination: % -> %. Error: %', 
                    faq_record.id, destination_id_text, SQLERRM;
            END;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Completed migration of tourism_faqs.related_destination_ids';
END $$;

-- Log the migration completion
DO $$
BEGIN
    RAISE NOTICE 'Array data migration to junction tables completed successfully';
END $$;

COMMIT;
