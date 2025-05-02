-- Migration: Implement best practices for Egypt Tourism Chatbot DB
-- Date: 2025-04-25

-- 1. Add hotels table (if not exists) and normalize accommodations
CREATE TABLE IF NOT EXISTS hotels (
    id TEXT PRIMARY KEY,
    city_id TEXT REFERENCES cities(id),
    type TEXT REFERENCES accommodation_types(type),
    name JSONB NOT NULL,
    description JSONB,
    address TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    price_range TEXT,
    data JSONB,
    geom geometry(Point,4326),
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. Add lookup tables for normalization
CREATE TABLE IF NOT EXISTS accommodation_types (
    type TEXT PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS attraction_types (
    type TEXT PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS cuisines (
    type TEXT PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS regions (
    name TEXT PRIMARY KEY
);

-- 3. Add/normalize city_id foreign keys
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS city_id TEXT REFERENCES cities(id);
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS city_id TEXT REFERENCES cities(id);
ALTER TABLE accommodations ADD COLUMN IF NOT EXISTS city_id TEXT REFERENCES cities(id);

-- 4. Add name/description JSONB columns for multilingual support
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS name JSONB;
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS description JSONB;
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS name JSONB;
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS description JSONB;
ALTER TABLE accommodations ADD COLUMN IF NOT EXISTS name JSONB;
ALTER TABLE accommodations ADD COLUMN IF NOT EXISTS description JSONB;

-- 5. Standardize timestamps
ALTER TABLE attractions ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at::timestamptz;
ALTER TABLE attractions ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at::timestamptz;
ALTER TABLE restaurants ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at::timestamptz;
ALTER TABLE restaurants ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at::timestamptz;
ALTER TABLE accommodations ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at::timestamptz;
ALTER TABLE accommodations ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at::timestamptz;

-- 6. Add reviews, favorites, and chat_logs tables
CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    target_id TEXT NOT NULL,
    target_type TEXT NOT NULL,
    rating INTEGER,
    text TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS favorites (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    target_id TEXT NOT NULL,
    target_type TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS chat_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    message TEXT,
    intent TEXT,
    response TEXT,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 7. Add media table
CREATE TABLE IF NOT EXISTS media (
    id TEXT PRIMARY KEY,
    target_id TEXT NOT NULL,
    target_type TEXT NOT NULL,
    url TEXT NOT NULL,
    type TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 8. Normalize cuisine/type/region in restaurants/accommodations/attractions
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS cuisine_id TEXT REFERENCES cuisines(type);
ALTER TABLE accommodations ADD COLUMN IF NOT EXISTS type_id TEXT REFERENCES accommodation_types(type);
ALTER TABLE attractions ADD COLUMN IF NOT EXISTS type_id TEXT REFERENCES attraction_types(type);
ALTER TABLE cities ADD COLUMN IF NOT EXISTS region_id TEXT REFERENCES regions(name);

-- 9. Indexes for new FKs and JSONB
CREATE INDEX IF NOT EXISTS idx_attractions_city_id ON attractions(city_id);
CREATE INDEX IF NOT EXISTS idx_restaurants_city_id ON restaurants(city_id);
CREATE INDEX IF NOT EXISTS idx_hotels_city_id ON hotels(city_id);
CREATE INDEX IF NOT EXISTS idx_attractions_type_id ON attractions(type_id);
CREATE INDEX IF NOT EXISTS idx_restaurants_cuisine_id ON restaurants(cuisine_id);
CREATE INDEX IF NOT EXISTS idx_accommodations_type_id ON accommodations(type_id);
CREATE INDEX IF NOT EXISTS idx_cities_region_id ON cities(region_id);
CREATE INDEX IF NOT EXISTS idx_attractions_name_jsonb ON attractions USING gin(name jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_restaurants_name_jsonb ON restaurants USING gin(name jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_hotels_name_jsonb ON hotels USING gin(name jsonb_path_ops);

-- 10. (Optional) Remove old columns after migration/validation
-- ALTER TABLE attractions DROP COLUMN name_en, DROP COLUMN name_ar, DROP COLUMN description_en, DROP COLUMN description_ar, DROP COLUMN city;
-- ALTER TABLE restaurants DROP COLUMN name_en, DROP COLUMN name_ar, DROP COLUMN description_en, DROP COLUMN description_ar, DROP COLUMN city, DROP COLUMN cuisine, DROP COLUMN region;
-- ALTER TABLE accommodations DROP COLUMN name_en, DROP COLUMN name_ar, DROP COLUMN description_en, DROP COLUMN description_ar, DROP COLUMN city, DROP COLUMN type, DROP COLUMN region;

-- NOTE: Data migration and backfill scripts should be run before dropping columns!
