-- Migration: 030_add_foreign_key_constraints.sql
-- Purpose: Add foreign key constraints for city_id and region_id columns

-- Begin transaction
BEGIN;

-- Add foreign key constraints for city_id
ALTER TABLE attractions
ADD CONSTRAINT attractions_city_id_fkey
FOREIGN KEY (city_id) REFERENCES cities(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE accommodations
ADD CONSTRAINT accommodations_city_id_fkey
FOREIGN KEY (city_id) REFERENCES cities(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE restaurants
ADD CONSTRAINT restaurants_city_id_fkey
FOREIGN KEY (city_id) REFERENCES cities(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE hotels
ADD CONSTRAINT hotels_city_id_fkey
FOREIGN KEY (city_id) REFERENCES cities(id) ON UPDATE CASCADE ON DELETE SET NULL;

-- Add foreign key constraints for region_id
ALTER TABLE attractions
ADD CONSTRAINT attractions_region_id_fkey
FOREIGN KEY (region_id) REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE accommodations
ADD CONSTRAINT accommodations_region_id_fkey
FOREIGN KEY (region_id) REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE restaurants
ADD CONSTRAINT restaurants_region_id_fkey
FOREIGN KEY (region_id) REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE cities
ADD CONSTRAINT cities_region_id_fkey
FOREIGN KEY (region_id) REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE cuisines
ADD CONSTRAINT cuisines_region_id_fkey
FOREIGN KEY (region_id) REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL;

-- Commit transaction
COMMIT;
