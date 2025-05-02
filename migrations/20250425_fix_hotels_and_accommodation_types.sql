-- Fix hotels and accommodation_types creation order
-- 1. Create accommodation_types table before hotels
CREATE TABLE IF NOT EXISTS accommodation_types (
    type TEXT PRIMARY KEY
);

-- 2. Re-create hotels table if previous attempt failed
DROP TABLE IF EXISTS hotels CASCADE;
CREATE TABLE hotels (
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

-- 3. Add indexes for hotels
CREATE INDEX IF NOT EXISTS idx_hotels_city_id ON hotels(city_id);
CREATE INDEX IF NOT EXISTS idx_hotels_name_jsonb ON hotels USING gin(name jsonb_path_ops);
