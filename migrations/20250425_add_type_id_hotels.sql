-- Add type_id column to hotels for normalized accommodation type reference
ALTER TABLE hotels ADD COLUMN IF NOT EXISTS type_id TEXT REFERENCES accommodation_types(type);

-- Now link hotels.type_id to hotels.type (if possible)
UPDATE hotels SET type_id = type WHERE type IS NOT NULL AND type_id IS NULL;
