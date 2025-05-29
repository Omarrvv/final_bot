-- Migration: Remove Array Columns
-- Date: 2025-07-10
-- Purpose: Verify data in junction tables and remove redundant array columns

BEGIN;

-- Log the migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting migration to remove array columns';
END $$;

-- First, verify that data exists in junction tables
DO $$
DECLARE
    attraction_relationships_count INTEGER;
    itinerary_attractions_count INTEGER;
    itinerary_cities_count INTEGER;
    tour_package_attractions_count INTEGER;
    tour_package_destinations_count INTEGER;
    
    attractions_with_related_count INTEGER;
    itineraries_with_attractions_count INTEGER;
    itineraries_with_cities_count INTEGER;
    tour_packages_with_attractions_count INTEGER;
    tour_packages_with_destinations_count INTEGER;
BEGIN
    -- Count records in junction tables
    SELECT COUNT(*) INTO attraction_relationships_count FROM attraction_relationships;
    SELECT COUNT(*) INTO itinerary_attractions_count FROM itinerary_attractions;
    SELECT COUNT(*) INTO itinerary_cities_count FROM itinerary_cities;
    SELECT COUNT(*) INTO tour_package_attractions_count FROM tour_package_attractions;
    SELECT COUNT(*) INTO tour_package_destinations_count FROM tour_package_destinations;
    
    -- Count records in array columns
    SELECT COUNT(*) INTO attractions_with_related_count FROM attractions WHERE related_attractions IS NOT NULL AND array_length(related_attractions, 1) > 0;
    SELECT COUNT(*) INTO itineraries_with_attractions_count FROM itineraries WHERE attractions IS NOT NULL AND array_length(attractions, 1) > 0;
    SELECT COUNT(*) INTO itineraries_with_cities_count FROM itineraries WHERE cities IS NOT NULL AND array_length(cities, 1) > 0;
    
    -- Check if tour_packages table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tour_packages') THEN
        EXECUTE 'SELECT COUNT(*) FROM tour_packages WHERE attractions IS NOT NULL AND array_length(attractions, 1) > 0' INTO tour_packages_with_attractions_count;
        EXECUTE 'SELECT COUNT(*) FROM tour_packages WHERE destinations IS NOT NULL AND array_length(destinations, 1) > 0' INTO tour_packages_with_destinations_count;
    ELSE
        tour_packages_with_attractions_count := 0;
        tour_packages_with_destinations_count := 0;
    END IF;
    
    -- Log the counts
    RAISE NOTICE 'Junction table counts: attraction_relationships=%, itinerary_attractions=%, itinerary_cities=%, tour_package_attractions=%, tour_package_destinations=%',
        attraction_relationships_count, itinerary_attractions_count, itinerary_cities_count, tour_package_attractions_count, tour_package_destinations_count;
    
    RAISE NOTICE 'Array column counts: attractions.related_attractions=%, itineraries.attractions=%, itineraries.cities=%, tour_packages.attractions=%, tour_packages.destinations=%',
        attractions_with_related_count, itineraries_with_attractions_count, itineraries_with_cities_count, tour_packages_with_attractions_count, tour_packages_with_destinations_count;
    
    -- Check if we need to run additional data migration
    IF attraction_relationships_count < attractions_with_related_count OR
       itinerary_attractions_count < itineraries_with_attractions_count OR
       itinerary_cities_count < itineraries_with_cities_count OR
       (tour_packages_with_attractions_count > 0 AND tour_package_attractions_count < tour_packages_with_attractions_count) OR
       (tour_packages_with_destinations_count > 0 AND tour_package_destinations_count < tour_packages_with_destinations_count) THEN
        RAISE EXCEPTION 'Data migration is incomplete. Please run the data migration script first.';
    END IF;
END $$;

-- Remove related_attractions from attractions
ALTER TABLE attractions
    DROP COLUMN IF EXISTS related_attractions;

-- Remove array columns from itineraries
ALTER TABLE itineraries
    DROP COLUMN IF EXISTS cities,
    DROP COLUMN IF EXISTS attractions,
    DROP COLUMN IF EXISTS restaurants,
    DROP COLUMN IF EXISTS accommodations;

-- Remove array columns from tour_packages if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tour_packages') THEN
        EXECUTE 'ALTER TABLE tour_packages
            DROP COLUMN IF EXISTS attractions,
            DROP COLUMN IF EXISTS destinations';
    END IF;
END $$;

-- Log the migration completion
DO $$
BEGIN
    RAISE NOTICE 'Array columns removed successfully';
END $$;

-- Update the schema version if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'schema_migrations') THEN
        INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status)
        VALUES ('20250710', 'remove_array_columns', NOW(), md5('20250710_remove_array_columns'), 0, 'success')
        ON CONFLICT (version) DO NOTHING;
    END IF;
END $$;

COMMIT;
