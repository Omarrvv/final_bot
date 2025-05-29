-- Migration: Add Foreign Key Constraints
-- Date: 2024-06-13
-- Phase 4.4 of the database migration plan

-- 1. Add foreign key constraints to attractions table
ALTER TABLE attractions
ADD CONSTRAINT fk_attractions_city
FOREIGN KEY (city_id) REFERENCES cities(id)
ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE attractions
ADD CONSTRAINT fk_attractions_region
FOREIGN KEY (region_id) REFERENCES regions(id)
ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE attractions
ADD CONSTRAINT fk_attractions_type
FOREIGN KEY (type_id) REFERENCES attraction_types(type)
ON DELETE SET NULL ON UPDATE CASCADE;

-- 2. Add foreign key constraints to accommodations table
ALTER TABLE accommodations
ADD CONSTRAINT fk_accommodations_city
FOREIGN KEY (city_id) REFERENCES cities(id)
ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE accommodations
ADD CONSTRAINT fk_accommodations_region
FOREIGN KEY (region_id) REFERENCES regions(id)
ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE accommodations
ADD CONSTRAINT fk_accommodations_type
FOREIGN KEY (type_id) REFERENCES accommodation_types(type)
ON DELETE SET NULL ON UPDATE CASCADE;

-- 3. Add foreign key constraint to cities table
ALTER TABLE cities
ADD CONSTRAINT fk_cities_region
FOREIGN KEY (region_id) REFERENCES regions(id)
ON DELETE SET NULL ON UPDATE CASCADE;

-- 4. Verify foreign key constraints
-- This section contains queries that can be run manually to verify the migration
-- They are commented out to prevent them from being executed during migration

/*
-- Verify foreign key constraints exist
SELECT
    tc.table_schema, 
    tc.constraint_name, 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_name IN ('attractions', 'accommodations', 'cities')
ORDER BY tc.table_name, kcu.column_name;
*/
