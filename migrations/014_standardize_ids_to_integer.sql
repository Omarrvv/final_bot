-- Migration: 014_standardize_ids_to_integer.sql
-- Purpose: Standardize all table IDs to integer type
-- This is a high-impact migration that should be executed with caution

-- Begin transaction
BEGIN;

-- Create a sequence for each table that will be converted
-- This ensures we have unique integer IDs for each table

-- 1. Create ID mapping tables to preserve relationships during migration
CREATE TABLE id_mapping_accommodations (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

CREATE TABLE id_mapping_attractions (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

CREATE TABLE id_mapping_cities (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

CREATE TABLE id_mapping_regions (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

CREATE TABLE id_mapping_restaurants (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

-- 2. Populate mapping tables with existing IDs
INSERT INTO id_mapping_accommodations (old_id)
SELECT id FROM accommodations ORDER BY id;

INSERT INTO id_mapping_attractions (old_id)
SELECT id FROM attractions ORDER BY id;

INSERT INTO id_mapping_cities (old_id)
SELECT id FROM cities ORDER BY id;

INSERT INTO id_mapping_regions (old_id)
SELECT id FROM regions ORDER BY id;

INSERT INTO id_mapping_restaurants (old_id)
SELECT id FROM restaurants ORDER BY id;

-- 3. Add new integer ID columns to tables
ALTER TABLE accommodations ADD COLUMN integer_id serial;
ALTER TABLE attractions ADD COLUMN integer_id serial;
ALTER TABLE cities ADD COLUMN integer_id serial;
ALTER TABLE regions ADD COLUMN integer_id serial;
ALTER TABLE restaurants ADD COLUMN integer_id serial;

-- 4. Update foreign key columns in related tables
-- For accommodations
UPDATE accommodations a
SET city_id = (SELECT new_id FROM id_mapping_cities WHERE old_id = a.city_id)
WHERE city_id IS NOT NULL;

UPDATE accommodations a
SET region_id = (SELECT new_id FROM id_mapping_regions WHERE old_id = a.region_id)
WHERE region_id IS NOT NULL;

-- For attractions
UPDATE attractions a
SET city_id = (SELECT new_id FROM id_mapping_cities WHERE old_id = a.city_id)
WHERE city_id IS NOT NULL;

UPDATE attractions a
SET region_id = (SELECT new_id FROM id_mapping_regions WHERE old_id = a.region_id)
WHERE region_id IS NOT NULL;

-- For restaurants
UPDATE restaurants r
SET city_id = (SELECT new_id FROM id_mapping_cities WHERE old_id = r.city_id)
WHERE city_id IS NOT NULL;

UPDATE restaurants r
SET region_id = (SELECT new_id FROM id_mapping_regions WHERE old_id = r.region_id)
WHERE region_id IS NOT NULL;

-- 5. Modify column types for foreign keys
ALTER TABLE accommodations 
    ALTER COLUMN city_id TYPE integer USING city_id::integer,
    ALTER COLUMN region_id TYPE integer USING region_id::integer;

ALTER TABLE attractions 
    ALTER COLUMN city_id TYPE integer USING city_id::integer,
    ALTER COLUMN region_id TYPE integer USING region_id::integer;

ALTER TABLE restaurants 
    ALTER COLUMN city_id TYPE integer USING city_id::integer,
    ALTER COLUMN region_id TYPE integer USING region_id::integer;

-- 6. Drop old primary key constraints
ALTER TABLE accommodations DROP CONSTRAINT accommodations_pkey;
ALTER TABLE attractions DROP CONSTRAINT attractions_pkey;
ALTER TABLE cities DROP CONSTRAINT cities_pkey;
ALTER TABLE regions DROP CONSTRAINT regions_pkey;
ALTER TABLE restaurants DROP CONSTRAINT restaurants_pkey;

-- 7. Rename ID columns
ALTER TABLE accommodations DROP COLUMN id;
ALTER TABLE accommodations RENAME COLUMN integer_id TO id;

ALTER TABLE attractions DROP COLUMN id;
ALTER TABLE attractions RENAME COLUMN integer_id TO id;

ALTER TABLE cities DROP COLUMN id;
ALTER TABLE cities RENAME COLUMN integer_id TO id;

ALTER TABLE regions DROP COLUMN id;
ALTER TABLE regions RENAME COLUMN integer_id TO id;

ALTER TABLE restaurants DROP COLUMN id;
ALTER TABLE restaurants RENAME COLUMN integer_id TO id;

-- 8. Add primary key constraints
ALTER TABLE accommodations ADD PRIMARY KEY (id);
ALTER TABLE attractions ADD PRIMARY KEY (id);
ALTER TABLE cities ADD PRIMARY KEY (id);
ALTER TABLE regions ADD PRIMARY KEY (id);
ALTER TABLE restaurants ADD PRIMARY KEY (id);

-- 9. Add foreign key constraints
ALTER TABLE accommodations 
    ADD CONSTRAINT accommodations_city_id_fkey FOREIGN KEY (city_id) REFERENCES cities(id) ON UPDATE CASCADE ON DELETE SET NULL,
    ADD CONSTRAINT accommodations_region_id_fkey FOREIGN KEY (region_id) REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE attractions 
    ADD CONSTRAINT attractions_city_id_fkey FOREIGN KEY (city_id) REFERENCES cities(id) ON UPDATE CASCADE ON DELETE SET NULL,
    ADD CONSTRAINT attractions_region_id_fkey FOREIGN KEY (region_id) REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE restaurants 
    ADD CONSTRAINT restaurants_city_id_fkey FOREIGN KEY (city_id) REFERENCES cities(id) ON UPDATE CASCADE ON DELETE SET NULL,
    ADD CONSTRAINT restaurants_region_id_fkey FOREIGN KEY (region_id) REFERENCES regions(id) ON UPDATE CASCADE ON DELETE SET NULL;

-- 10. Clean up mapping tables
DROP TABLE id_mapping_accommodations;
DROP TABLE id_mapping_attractions;
DROP TABLE id_mapping_cities;
DROP TABLE id_mapping_regions;
DROP TABLE id_mapping_restaurants;

-- Commit transaction
COMMIT;
