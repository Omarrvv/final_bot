-- Add missing columns to hotels for migration compatibility
ALTER TABLE hotels ADD COLUMN IF NOT EXISTS name_en TEXT;
ALTER TABLE hotels ADD COLUMN IF NOT EXISTS name_ar TEXT;
ALTER TABLE hotels ADD COLUMN IF NOT EXISTS description_en TEXT;
ALTER TABLE hotels ADD COLUMN IF NOT EXISTS description_ar TEXT;
ALTER TABLE hotels ADD COLUMN IF NOT EXISTS city TEXT;

-- Optionally, fill these columns with placeholder values if needed for migration
UPDATE hotels SET name_en = COALESCE(name_en, name->>'en') WHERE name_en IS NULL AND name IS NOT NULL;
UPDATE hotels SET name_ar = COALESCE(name_ar, name->>'ar') WHERE name_ar IS NULL AND name IS NOT NULL;
UPDATE hotels SET description_en = COALESCE(description_en, description->>'en') WHERE description_en IS NULL AND description IS NOT NULL;
UPDATE hotels SET description_ar = COALESCE(description_ar, description->>'ar') WHERE description_ar IS NULL AND description IS NOT NULL;
UPDATE hotels SET city = NULL WHERE city IS NULL; -- Set to NULL or populate as needed
