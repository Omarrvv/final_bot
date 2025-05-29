-- Migration to extract frequently queried attributes from JSONB columns
-- This script adds dedicated columns for frequently queried attributes

-- Add comments to document JSONB structure
COMMENT ON COLUMN attractions.data IS 'Additional attraction data in JSONB format. Expected structure: 
{
  "popularity": integer (1-10),
  "year_built": integer,
  "entrance_fee": numeric,
  "opening_hours": string
}';

COMMENT ON COLUMN restaurants.data IS 'Additional restaurant data in JSONB format. Expected structure:
{
  "contact": {
    "email": string,
    "phone": string,
    "website": string,
    "social_media": {
      "facebook": string,
      "instagram": string
    }
  },
  "features": {
    "wifi": boolean,
    "alcohol": boolean,
    "parking": boolean,
    "smoking": boolean,
    "takeout": boolean,
    "delivery": boolean,
    "reservations": boolean,
    "outdoor_seating": boolean,
    "wheelchair_accessible": boolean
  },
  "menu_items": array of objects,
  "opening_hours": object,
  "dietary_options": object
}';

-- Extract frequently queried attributes from attractions.data
ALTER TABLE attractions ADD COLUMN opening_hours VARCHAR(255);
ALTER TABLE attractions ADD COLUMN entrance_fee NUMERIC;
ALTER TABLE attractions ADD COLUMN popularity INTEGER;

-- Update the new columns with data from the JSONB column
UPDATE attractions SET 
  opening_hours = data->>'opening_hours',
  entrance_fee = (data->>'entrance_fee')::NUMERIC,
  popularity = (data->>'popularity')::INTEGER
WHERE data IS NOT NULL;

-- Extract frequently queried attributes from restaurants.data
ALTER TABLE restaurants ADD COLUMN phone VARCHAR(255);
ALTER TABLE restaurants ADD COLUMN email VARCHAR(255);
ALTER TABLE restaurants ADD COLUMN website VARCHAR(255);

-- Update the new columns with data from the JSONB column
UPDATE restaurants SET 
  phone = data->'contact'->>'phone',
  email = data->'contact'->>'email',
  website = data->'contact'->>'website'
WHERE data IS NOT NULL;

-- Create indexes on the new columns
CREATE INDEX idx_attractions_popularity ON attractions(popularity);
CREATE INDEX idx_attractions_entrance_fee ON attractions(entrance_fee);
CREATE INDEX idx_restaurants_phone ON restaurants(phone);
CREATE INDEX idx_restaurants_email ON restaurants(email);

-- Remove the extracted attributes from the JSONB data to avoid duplication
-- This is optional and can be done later if needed
-- UPDATE attractions SET data = data - 'opening_hours' - 'entrance_fee' - 'popularity'
-- WHERE data IS NOT NULL;

-- UPDATE restaurants SET data = jsonb_set(
--   jsonb_set(
--     jsonb_set(
--       data,
--       '{contact}',
--       (data->'contact') - 'phone' - 'email' - 'website'
--     ),
--     '{contact}',
--     CASE
--       WHEN (data->'contact') - 'phone' - 'email' - 'website' = '{}'::jsonb
--       THEN NULL
--       ELSE (data->'contact') - 'phone' - 'email' - 'website'
--     END
--   ),
--   '{contact}',
--   CASE
--     WHEN data->'contact' IS NULL OR (data->'contact') - 'phone' - 'email' - 'website' = '{}'::jsonb
--     THEN NULL
--     ELSE (data->'contact') - 'phone' - 'email' - 'website'
--   END
-- )
-- WHERE data IS NOT NULL;
