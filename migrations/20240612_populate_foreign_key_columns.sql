-- Migration: Populate Foreign Key Columns
-- Date: 2024-06-12
-- Phase 4.3 of the database migration plan

-- 1. Create regions if they don't exist
INSERT INTO regions (id, name_en, name_ar)
VALUES
  ('lower_egypt', 'Lower Egypt', 'مصر السفلى'),
  ('upper_egypt', 'Upper Egypt', 'مصر العليا'),
  ('mediterranean_coast', 'Mediterranean Coast', 'ساحل البحر المتوسط')
ON CONFLICT (id) DO NOTHING;

-- 2. Update cities.region_id based on region text
UPDATE cities
SET region_id = 'lower_egypt'
WHERE region = 'Lower Egypt' AND region_id IS NULL;

UPDATE cities
SET region_id = 'upper_egypt'
WHERE region = 'Upper Egypt' AND region_id IS NULL;

UPDATE cities
SET region_id = 'mediterranean_coast'
WHERE region = 'Mediterranean Coast' AND region_id IS NULL;

-- 3. Update attractions.city_id based on city text
UPDATE attractions
SET city_id = c.id
FROM cities c
WHERE attractions.city = c.name_en AND attractions.city_id IS NULL;

-- 4. Update attractions.region_id based on region text
UPDATE attractions
SET region_id = r.id
FROM regions r
WHERE attractions.region = r.name_en AND attractions.region_id IS NULL;

-- 5. Update attractions.type_id based on type text
UPDATE attractions
SET type_id = type
WHERE type IS NOT NULL AND type_id IS NULL;

-- 6. Update accommodations.city_id based on city text
UPDATE accommodations
SET city_id = c.id
FROM cities c
WHERE accommodations.city = c.name_en AND accommodations.city_id IS NULL;

-- 7. Update accommodations.region_id based on region text
UPDATE accommodations
SET region_id = r.id
FROM regions r
WHERE accommodations.region = r.name_en AND accommodations.region_id IS NULL;

-- 8. Update accommodations.type_id based on type text
UPDATE accommodations
SET type_id = type
WHERE type IS NOT NULL AND type_id IS NULL;

-- 9. Verify foreign key columns are populated
-- This section contains queries that can be run manually to verify the migration
-- They are commented out to prevent them from being executed during migration

/*
-- Verify cities.region_id is populated
SELECT id, name_en, region, region_id
FROM cities
ORDER BY id;

-- Verify attractions foreign keys are populated
SELECT id, city, city_id, region, region_id, type, type_id
FROM attractions
ORDER BY id;

-- Verify accommodations foreign keys are populated
SELECT id, city, city_id, region, region_id, type, type_id
FROM accommodations
ORDER BY id;
*/
