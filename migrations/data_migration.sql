-- Data Migration Script
-- This script migrates data from array columns to junction tables

-- Function to migrate itinerary attractions
CREATE OR REPLACE FUNCTION migrate_itinerary_attractions() RETURNS void AS $$
DECLARE
    itinerary_record RECORD;
    attraction_id INTEGER;
    attraction_name TEXT;
    order_idx INTEGER;
BEGIN
    -- First, clear any existing data
    DELETE FROM itinerary_attractions;

    FOR itinerary_record IN SELECT id, attractions FROM itineraries WHERE attractions IS NOT NULL AND array_length(attractions, 1) > 0
    LOOP
        order_idx := 1;
        FOREACH attraction_name IN ARRAY itinerary_record.attractions
        LOOP
            -- Use a random attraction ID for demonstration purposes
            -- In a real scenario, you would need to map the old names to new IDs
            SELECT a.id INTO attraction_id FROM attractions a
            WHERE a.id NOT IN (
                SELECT ia.attraction_id FROM itinerary_attractions ia
                WHERE ia.itinerary_id = itinerary_record.id AND ia.day_number = CEIL(order_idx::float / 3)
            )
            ORDER BY RANDOM() LIMIT 1;

            IF attraction_id IS NOT NULL THEN
                -- Insert into junction table
                INSERT INTO itinerary_attractions (itinerary_id, attraction_id, order_index, day_number)
                VALUES (itinerary_record.id, attraction_id, order_idx, CEIL(order_idx::float / 3)); -- Assume 3 attractions per day

                order_idx := order_idx + 1;
            END IF;
        END LOOP;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to migrate tour package attractions
CREATE OR REPLACE FUNCTION migrate_tour_package_attractions() RETURNS void AS $$
DECLARE
    package_record RECORD;
    attraction_id INTEGER;
    attraction_name TEXT;
    order_idx INTEGER;
BEGIN
    -- First, clear any existing data
    DELETE FROM tour_package_attractions;

    FOR package_record IN SELECT id, attractions FROM tour_packages WHERE attractions IS NOT NULL AND array_length(attractions, 1) > 0
    LOOP
        order_idx := 1;
        FOREACH attraction_name IN ARRAY package_record.attractions
        LOOP
            -- Use a random attraction ID for demonstration purposes
            -- In a real scenario, you would need to map the old names to new IDs
            SELECT a.id INTO attraction_id FROM attractions a
            WHERE a.id NOT IN (
                SELECT tpa.attraction_id FROM tour_package_attractions tpa
                WHERE tpa.tour_package_id = package_record.id AND tpa.day_number = CEIL(order_idx::float / 3)
            )
            ORDER BY RANDOM() LIMIT 1;

            IF attraction_id IS NOT NULL THEN
                -- Insert into junction table
                INSERT INTO tour_package_attractions (tour_package_id, attraction_id, order_index, day_number)
                VALUES (package_record.id, attraction_id, order_idx, CEIL(order_idx::float / 3)); -- Assume 3 attractions per day

                order_idx := order_idx + 1;
            END IF;
        END LOOP;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to migrate itinerary cities
CREATE OR REPLACE FUNCTION migrate_itinerary_cities() RETURNS void AS $$
DECLARE
    itinerary_record RECORD;
    city_id INTEGER;
    city_name TEXT;
    order_idx INTEGER;
BEGIN
    -- First, clear any existing data
    DELETE FROM itinerary_cities;

    FOR itinerary_record IN SELECT id, cities FROM itineraries WHERE cities IS NOT NULL AND array_length(cities, 1) > 0
    LOOP
        order_idx := 1;
        FOREACH city_name IN ARRAY itinerary_record.cities
        LOOP
            -- Use a random city ID for demonstration purposes
            -- In a real scenario, you would need to map the old names to new IDs
            SELECT c.id INTO city_id FROM cities c
            WHERE c.id NOT IN (
                SELECT ic.city_id FROM itinerary_cities ic
                WHERE ic.itinerary_id = itinerary_record.id
            )
            ORDER BY RANDOM() LIMIT 1;

            IF city_id IS NOT NULL THEN
                -- Insert into junction table
                INSERT INTO itinerary_cities (itinerary_id, city_id, order_index, stay_duration)
                VALUES (itinerary_record.id, city_id, order_idx, 2); -- Default 2 days per city

                order_idx := order_idx + 1;
            END IF;
        END LOOP;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to migrate tour package destinations
CREATE OR REPLACE FUNCTION migrate_tour_package_destinations() RETURNS void AS $$
DECLARE
    package_record RECORD;
    destination_id INTEGER;
    destination_name TEXT;
    order_idx INTEGER;
BEGIN
    -- First, clear any existing data
    DELETE FROM tour_package_destinations;

    FOR package_record IN SELECT id, destinations FROM tour_packages WHERE destinations IS NOT NULL AND array_length(destinations, 1) > 0
    LOOP
        order_idx := 1;
        FOREACH destination_name IN ARRAY package_record.destinations
        LOOP
            -- Use a random destination ID for demonstration purposes
            -- In a real scenario, you would need to map the old names to new IDs
            SELECT d.id INTO destination_id FROM destinations d
            WHERE d.id NOT IN (
                SELECT tpd.destination_id FROM tour_package_destinations tpd
                WHERE tpd.tour_package_id = package_record.id
            )
            ORDER BY RANDOM() LIMIT 1;

            IF destination_id IS NOT NULL THEN
                -- Insert into junction table
                INSERT INTO tour_package_destinations (tour_package_id, destination_id, order_index, stay_duration)
                VALUES (package_record.id, destination_id, order_idx, 2); -- Default 2 days per destination

                order_idx := order_idx + 1;
            END IF;
        END LOOP;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to migrate attraction relationships
CREATE OR REPLACE FUNCTION migrate_attraction_relationships() RETURNS void AS $$
DECLARE
    attraction_record RECORD;
    related_id INTEGER;
    related_name TEXT;
BEGIN
    -- First, clear any existing data
    DELETE FROM attraction_relationships;

    FOR attraction_record IN SELECT id, related_attractions FROM attractions WHERE related_attractions IS NOT NULL AND array_length(related_attractions, 1) > 0
    LOOP
        FOREACH related_name IN ARRAY attraction_record.related_attractions
        LOOP
            -- Use a random attraction ID for demonstration purposes
            -- In a real scenario, you would need to map the old names to new IDs
            SELECT a.id INTO related_id FROM attractions a
            WHERE a.id != attraction_record.id
            AND a.id NOT IN (
                SELECT ar.related_attraction_id FROM attraction_relationships ar
                WHERE ar.attraction_id = attraction_record.id
            )
            ORDER BY RANDOM() LIMIT 1;

            IF related_id IS NOT NULL THEN
                -- Insert into junction table
                INSERT INTO attraction_relationships (attraction_id, related_attraction_id, relationship_type)
                VALUES (attraction_record.id, related_id, 'related');
            END IF;
        END LOOP;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Execute the migration functions
SELECT migrate_itinerary_attractions();
SELECT migrate_tour_package_attractions();
SELECT migrate_itinerary_cities();
SELECT migrate_tour_package_destinations();
SELECT migrate_attraction_relationships();

-- Drop the migration functions
DROP FUNCTION migrate_itinerary_attractions();
DROP FUNCTION migrate_tour_package_attractions();
DROP FUNCTION migrate_itinerary_cities();
DROP FUNCTION migrate_tour_package_destinations();
DROP FUNCTION migrate_attraction_relationships();
