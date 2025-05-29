-- Migration: Drop Redundant Array Columns
-- Date: 2025-07-15
-- Purpose: Drop array columns that have been replaced by junction tables

BEGIN;

-- Log the migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting migration to drop redundant array columns';
END $$;

-- Verify that data has been migrated to junction tables
DO $$
DECLARE
    attraction_relationships_count INTEGER;
    itinerary_attractions_count INTEGER;
    itinerary_cities_count INTEGER;
    tour_package_attractions_count INTEGER;
    tour_package_destinations_count INTEGER;
    tourism_faq_destinations_count INTEGER;
    
    attractions_with_related_count INTEGER;
    itineraries_with_attractions_count INTEGER;
    itineraries_with_cities_count INTEGER;
    tour_packages_with_attractions_count INTEGER;
    tour_packages_with_destinations_count INTEGER;
    tourism_faqs_with_destinations_count INTEGER;
BEGIN
    -- Get counts from junction tables
    SELECT COUNT(*) INTO attraction_relationships_count FROM attraction_relationships;
    SELECT COUNT(*) INTO itinerary_attractions_count FROM itinerary_attractions;
    SELECT COUNT(*) INTO itinerary_cities_count FROM itinerary_cities;
    SELECT COUNT(*) INTO tour_package_attractions_count FROM tour_package_attractions;
    SELECT COUNT(*) INTO tour_package_destinations_count FROM tour_package_destinations;
    SELECT COUNT(*) INTO tourism_faq_destinations_count FROM tourism_faq_destinations;
    
    -- Get counts from array columns
    SELECT COUNT(*) INTO attractions_with_related_count FROM attractions WHERE array_length(related_attractions, 1) > 0;
    SELECT COUNT(*) INTO itineraries_with_attractions_count FROM itineraries WHERE array_length(attractions, 1) > 0;
    SELECT COUNT(*) INTO itineraries_with_cities_count FROM itineraries WHERE array_length(cities, 1) > 0;
    SELECT COUNT(*) INTO tour_packages_with_attractions_count FROM tour_packages WHERE array_length(attractions, 1) > 0;
    SELECT COUNT(*) INTO tour_packages_with_destinations_count FROM tour_packages WHERE array_length(destinations, 1) > 0;
    SELECT COUNT(*) INTO tourism_faqs_with_destinations_count FROM tourism_faqs WHERE array_length(related_destination_ids, 1) > 0;
    
    -- Log the counts
    RAISE NOTICE 'Junction table counts: attraction_relationships=%, itinerary_attractions=%, itinerary_cities=%, tour_package_attractions=%, tour_package_destinations=%, tourism_faq_destinations=%',
        attraction_relationships_count, itinerary_attractions_count, itinerary_cities_count, tour_package_attractions_count, tour_package_destinations_count, tourism_faq_destinations_count;
    
    RAISE NOTICE 'Array column counts: attractions.related_attractions=%, itineraries.attractions=%, itineraries.cities=%, tour_packages.attractions=%, tour_packages.destinations=%, tourism_faqs.related_destination_ids=%',
        attractions_with_related_count, itineraries_with_attractions_count, itineraries_with_cities_count, tour_packages_with_attractions_count, tour_packages_with_destinations_count, tourism_faqs_with_destinations_count;
    
    -- Verify that all data has been migrated
    IF attractions_with_related_count > 0 AND attraction_relationships_count = 0 THEN
        RAISE EXCEPTION 'Data migration incomplete: attractions.related_attractions still has data but attraction_relationships is empty';
    END IF;
    
    IF itineraries_with_attractions_count > 0 AND itinerary_attractions_count = 0 THEN
        RAISE EXCEPTION 'Data migration incomplete: itineraries.attractions still has data but itinerary_attractions is empty';
    END IF;
    
    IF itineraries_with_cities_count > 0 AND itinerary_cities_count = 0 THEN
        RAISE EXCEPTION 'Data migration incomplete: itineraries.cities still has data but itinerary_cities is empty';
    END IF;
    
    IF tour_packages_with_attractions_count > 0 AND tour_package_attractions_count = 0 THEN
        RAISE EXCEPTION 'Data migration incomplete: tour_packages.attractions still has data but tour_package_attractions is empty';
    END IF;
    
    IF tour_packages_with_destinations_count > 0 AND tour_package_destinations_count = 0 THEN
        RAISE EXCEPTION 'Data migration incomplete: tour_packages.destinations still has data but tour_package_destinations is empty';
    END IF;
    
    IF tourism_faqs_with_destinations_count > 0 AND tourism_faq_destinations_count = 0 THEN
        RAISE EXCEPTION 'Data migration incomplete: tourism_faqs.related_destination_ids still has data but tourism_faq_destinations is empty';
    END IF;
    
    RAISE NOTICE 'Data migration verification passed. Proceeding with dropping array columns.';
END $$;

-- Drop indexes on array columns first
DROP INDEX IF EXISTS idx_attractions_related_attractions;
DROP INDEX IF EXISTS idx_itineraries_attractions;
DROP INDEX IF EXISTS idx_itineraries_cities;
DROP INDEX IF EXISTS idx_tour_packages_attractions;
DROP INDEX IF EXISTS idx_tour_packages_destinations;
DROP INDEX IF EXISTS idx_tourism_faqs_related_destination_ids;

-- Drop array columns
ALTER TABLE attractions DROP COLUMN IF EXISTS related_attractions;
ALTER TABLE itineraries DROP COLUMN IF EXISTS attractions;
ALTER TABLE itineraries DROP COLUMN IF EXISTS cities;
ALTER TABLE tour_packages DROP COLUMN IF EXISTS attractions;
ALTER TABLE tour_packages DROP COLUMN IF EXISTS destinations;
ALTER TABLE tourism_faqs DROP COLUMN IF EXISTS related_destination_ids;

-- Log the migration completion
DO $$
BEGIN
    RAISE NOTICE 'Redundant array columns dropped successfully';
END $$;

COMMIT;
