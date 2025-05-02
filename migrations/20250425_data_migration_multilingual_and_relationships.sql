-- Data Migration: Migrate multilingual fields and relationships
-- Step 1: Migrate name_en/name_ar and description_en/description_ar to JSONB columns
UPDATE attractions SET name = jsonb_build_object('en', name_en, 'ar', name_ar) WHERE name IS NULL;
UPDATE attractions SET description = jsonb_build_object('en', description_en, 'ar', description_ar) WHERE description IS NULL;
UPDATE restaurants SET name = jsonb_build_object('en', name_en, 'ar', name_ar) WHERE name IS NULL;
UPDATE restaurants SET description = jsonb_build_object('en', description_en, 'ar', description_ar) WHERE description IS NULL;
UPDATE accommodations SET name = jsonb_build_object('en', name_en, 'ar', name_ar) WHERE name IS NULL;
UPDATE accommodations SET description = jsonb_build_object('en', description_en, 'ar', description_ar) WHERE description IS NULL;
UPDATE hotels SET name = jsonb_build_object('en', name_en, 'ar', name_ar) WHERE name IS NULL;
UPDATE hotels SET description = jsonb_build_object('en', description_en, 'ar', description_ar) WHERE description IS NULL;

-- Step 2: Migrate city text fields to city_id foreign keys
UPDATE attractions a SET city_id = c.id FROM cities c WHERE (a.city = c.name_en OR a.city = c.name_ar) AND a.city_id IS NULL;
UPDATE restaurants r SET city_id = c.id FROM cities c WHERE (r.city = c.name_en OR r.city = c.name_ar) AND r.city_id IS NULL;
UPDATE accommodations acc SET city_id = c.id FROM cities c WHERE (acc.city = c.name_en OR acc.city = c.name_ar) AND acc.city_id IS NULL;
UPDATE hotels h SET city_id = c.id FROM cities c WHERE (h.city = c.name_en OR h.city = c.name_ar) AND h.city_id IS NULL;

-- Step 3: Migrate type/cuisine/region to lookup tables
-- Populate accommodation_types from existing data
INSERT INTO accommodation_types(type)
SELECT DISTINCT type FROM accommodations WHERE type IS NOT NULL AND type <> ''
ON CONFLICT DO NOTHING;
-- Populate attraction_types from existing data
INSERT INTO attraction_types(type)
SELECT DISTINCT type FROM attractions WHERE type IS NOT NULL AND type <> ''
ON CONFLICT DO NOTHING;
-- Populate cuisines from existing data
INSERT INTO cuisines(type)
SELECT DISTINCT cuisine FROM restaurants WHERE cuisine IS NOT NULL AND cuisine <> ''
ON CONFLICT DO NOTHING;
-- Populate regions from existing data
INSERT INTO regions(name)
SELECT DISTINCT region FROM cities WHERE region IS NOT NULL AND region <> ''
ON CONFLICT DO NOTHING;

-- Link main tables to lookup tables
UPDATE accommodations acc SET type_id = acc.type WHERE acc.type IS NOT NULL AND acc.type_id IS NULL;
UPDATE attractions a SET type_id = a.type WHERE a.type IS NOT NULL AND a.type_id IS NULL;
UPDATE restaurants r SET cuisine_id = r.cuisine WHERE r.cuisine IS NOT NULL AND r.cuisine_id IS NULL;
UPDATE cities c SET region_id = c.region WHERE c.region IS NOT NULL AND c.region_id IS NULL;

-- (Optional) Validate that all city_id, type_id, cuisine_id, region_id are now set
-- SELECT COUNT(*) FROM attractions WHERE city_id IS NULL OR type_id IS NULL;
-- SELECT COUNT(*) FROM restaurants WHERE city_id IS NULL OR cuisine_id IS NULL;
-- SELECT COUNT(*) FROM accommodations WHERE city_id IS NULL OR type_id IS NULL;
-- SELECT COUNT(*) FROM hotels WHERE city_id IS NULL;
