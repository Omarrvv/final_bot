-- Data Migration for hotels: fill new multilingual and city columns
-- Step 1: If you have any legacy data for hotels, migrate it into the new columns
-- (Assuming you may have legacy data elsewhere, otherwise these will remain NULL)

-- Step 2: Migrate city text to city_id foreign key
UPDATE hotels h SET city_id = c.id FROM cities c WHERE (h.city = c.name_en OR h.city = c.name_ar) AND h.city_id IS NULL;

-- Step 3: Populate accommodation_types from hotels.type
INSERT INTO accommodation_types(type)
SELECT DISTINCT type FROM hotels WHERE type IS NOT NULL AND type <> ''
ON CONFLICT DO NOTHING;

-- Step 4: Link hotels to accommodation_types
UPDATE hotels SET type_id = type WHERE type IS NOT NULL AND type_id IS NULL;

-- (Optional) Validate that all city_id, type_id are now set
-- SELECT COUNT(*) FROM hotels WHERE city_id IS NULL OR type_id IS NULL;
