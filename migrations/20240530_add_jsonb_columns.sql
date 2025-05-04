-- Migration: Add JSONB columns for multilingual support
-- Date: 2024-05-30

-- 1. Add name/description JSONB columns for multilingual support
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS name JSONB;
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS description JSONB;
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS name JSONB;
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS description JSONB;
ALTER TABLE accommodations ADD COLUMN IF NOT EXISTS name JSONB;
ALTER TABLE accommodations ADD COLUMN IF NOT EXISTS description JSONB;

-- 2. Migrate data from separate text fields to JSONB fields
-- Attractions
UPDATE attractions SET name = jsonb_build_object('en', name_en, 'ar', name_ar) WHERE name IS NULL;
UPDATE attractions SET description = jsonb_build_object('en', description_en, 'ar', description_ar) WHERE description IS NULL;

-- Restaurants
UPDATE restaurants SET name = jsonb_build_object('en', name_en, 'ar', name_ar) WHERE name IS NULL;
UPDATE restaurants SET description = jsonb_build_object('en', description_en, 'ar', description_ar) WHERE description IS NULL;

-- Accommodations
UPDATE accommodations SET name = jsonb_build_object('en', name_en, 'ar', name_ar) WHERE name IS NULL;
UPDATE accommodations SET description = jsonb_build_object('en', description_en, 'ar', description_ar) WHERE description IS NULL;

-- 3. Create indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_attractions_name_jsonb ON attractions USING gin(name jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_attractions_description_jsonb ON attractions USING gin(description jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_restaurants_name_jsonb ON restaurants USING gin(name jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_restaurants_description_jsonb ON restaurants USING gin(description jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_accommodations_name_jsonb ON accommodations USING gin(name jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_accommodations_description_jsonb ON accommodations USING gin(description jsonb_path_ops);
