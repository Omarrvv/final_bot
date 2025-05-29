-- Migration: 010_standardize_remaining_foreign_keys.sql
-- Purpose: Standardize remaining foreign key constraints that don't follow the standard rules

-- Begin transaction
BEGIN;

-- 1. Fix feedback.session_id foreign key
ALTER TABLE feedback DROP CONSTRAINT IF EXISTS feedback_session_id_fkey;
ALTER TABLE feedback ADD CONSTRAINT feedback_session_id_fkey
FOREIGN KEY (session_id) REFERENCES sessions(id)
ON UPDATE CASCADE
ON DELETE SET NULL;

-- 2. Fix destination_seasons.destination_id foreign key
-- Note: We're keeping ON DELETE CASCADE as these are child records that should be deleted with the parent
ALTER TABLE destination_seasons DROP CONSTRAINT IF EXISTS destination_seasons_destination_id_fkey;
ALTER TABLE destination_seasons ADD CONSTRAINT destination_seasons_destination_id_fkey
FOREIGN KEY (destination_id) REFERENCES destinations(id)
ON UPDATE CASCADE
ON DELETE CASCADE;

-- 3. Fix destination_events.destination_id foreign key
-- Note: We're keeping ON DELETE CASCADE as these are child records that should be deleted with the parent
ALTER TABLE destination_events DROP CONSTRAINT IF EXISTS destination_events_destination_id_fkey;
ALTER TABLE destination_events ADD CONSTRAINT destination_events_destination_id_fkey
FOREIGN KEY (destination_id) REFERENCES destinations(id)
ON UPDATE CASCADE
ON DELETE CASCADE;

-- 4. Fix transportation_stations.destination_id foreign key
ALTER TABLE transportation_stations DROP CONSTRAINT IF EXISTS transportation_stations_destination_id_fkey;
ALTER TABLE transportation_stations ADD CONSTRAINT transportation_stations_destination_id_fkey
FOREIGN KEY (destination_id) REFERENCES destinations(id)
ON UPDATE CASCADE
ON DELETE SET NULL;

-- 5. Fix transportation_route_stations.route_id foreign key
-- Note: We're keeping ON DELETE CASCADE as these are child records that should be deleted with the parent
ALTER TABLE transportation_route_stations DROP CONSTRAINT IF EXISTS transportation_route_stations_route_id_fkey;
ALTER TABLE transportation_route_stations ADD CONSTRAINT transportation_route_stations_route_id_fkey
FOREIGN KEY (route_id) REFERENCES transportation_routes(id)
ON UPDATE CASCADE
ON DELETE CASCADE;

-- 6. Fix transportation_route_stations.station_id foreign key
ALTER TABLE transportation_route_stations DROP CONSTRAINT IF EXISTS transportation_route_stations_station_id_fkey;
ALTER TABLE transportation_route_stations ADD CONSTRAINT transportation_route_stations_station_id_fkey
FOREIGN KEY (station_id) REFERENCES transportation_stations(id)
ON UPDATE CASCADE
ON DELETE RESTRICT;

-- 7. Fix cities.user_id foreign key
ALTER TABLE cities DROP CONSTRAINT IF EXISTS cities_user_id_fkey;
ALTER TABLE cities ADD CONSTRAINT cities_user_id_fkey
FOREIGN KEY (user_id) REFERENCES users(id)
ON UPDATE CASCADE
ON DELETE SET NULL;

-- 8. Fix destination_images.destination_id foreign key
-- Note: We're keeping ON DELETE CASCADE as these are child records that should be deleted with the parent
ALTER TABLE destination_images DROP CONSTRAINT IF EXISTS destination_images_destination_id_fkey;
ALTER TABLE destination_images ADD CONSTRAINT destination_images_destination_id_fkey
FOREIGN KEY (destination_id) REFERENCES destinations(id)
ON UPDATE CASCADE
ON DELETE CASCADE;

-- 9. Fix regions.user_id foreign key
ALTER TABLE regions DROP CONSTRAINT IF EXISTS regions_user_id_fkey;
ALTER TABLE regions ADD CONSTRAINT regions_user_id_fkey
FOREIGN KEY (user_id) REFERENCES users(id)
ON UPDATE CASCADE
ON DELETE SET NULL;

-- 10. Fix sessions.user_id foreign key
ALTER TABLE sessions DROP CONSTRAINT IF EXISTS sessions_user_id_fkey;
ALTER TABLE sessions ADD CONSTRAINT sessions_user_id_fkey
FOREIGN KEY (user_id) REFERENCES users(id)
ON UPDATE CASCADE
ON DELETE SET NULL;

-- 11. Fix attraction_subcategories.parent_type foreign key
ALTER TABLE attraction_subcategories DROP CONSTRAINT IF EXISTS attraction_subcategories_parent_type_fkey;
ALTER TABLE attraction_subcategories ADD CONSTRAINT attraction_subcategories_parent_type_fkey
FOREIGN KEY (parent_type) REFERENCES attraction_types(type)
ON UPDATE CASCADE
ON DELETE RESTRICT;

-- 12. Fix attractions.subcategory_id foreign key
ALTER TABLE attractions DROP CONSTRAINT IF EXISTS attractions_subcategory_id_fkey;
ALTER TABLE attractions ADD CONSTRAINT attractions_subcategory_id_fkey
FOREIGN KEY (subcategory_id) REFERENCES attraction_subcategories(id)
ON UPDATE CASCADE
ON DELETE SET NULL;

-- 13. Fix itineraries.type_id foreign key
ALTER TABLE itineraries DROP CONSTRAINT IF EXISTS itineraries_type_id_fkey;
ALTER TABLE itineraries ADD CONSTRAINT itineraries_type_id_fkey
FOREIGN KEY (type_id) REFERENCES itinerary_types(id)
ON UPDATE CASCADE
ON DELETE RESTRICT;

-- 14. Fix events_festivals.category_id foreign key
ALTER TABLE events_festivals DROP CONSTRAINT IF EXISTS events_festivals_category_id_fkey;
ALTER TABLE events_festivals ADD CONSTRAINT events_festivals_category_id_fkey
FOREIGN KEY (category_id) REFERENCES event_categories(id)
ON UPDATE CASCADE
ON DELETE RESTRICT;

-- 15. Fix practical_info.category_id foreign key
ALTER TABLE practical_info DROP CONSTRAINT IF EXISTS practical_info_category_id_fkey;
ALTER TABLE practical_info ADD CONSTRAINT practical_info_category_id_fkey
FOREIGN KEY (category_id) REFERENCES practical_info_categories(id)
ON UPDATE CASCADE
ON DELETE RESTRICT;

-- 16. Fix tour_packages.category_id foreign key
ALTER TABLE tour_packages DROP CONSTRAINT IF EXISTS tour_packages_category_id_fkey;
ALTER TABLE tour_packages ADD CONSTRAINT tour_packages_category_id_fkey
FOREIGN KEY (category_id) REFERENCES tour_package_categories(id)
ON UPDATE CASCADE
ON DELETE RESTRICT;

-- 17. Fix cities.region_id foreign key
ALTER TABLE cities DROP CONSTRAINT IF EXISTS cities_region_id_fkey;
ALTER TABLE cities ADD CONSTRAINT cities_region_id_fkey
FOREIGN KEY (region_id) REFERENCES regions(id)
ON UPDATE CASCADE
ON DELETE SET NULL;

-- Commit transaction
COMMIT;
