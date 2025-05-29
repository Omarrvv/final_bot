-- Migration: Create Transportation Tables
-- Date: 2024-06-23
-- Description: Create tables for transportation options between destinations

-- 1. Create transportation_types table
CREATE TABLE IF NOT EXISTS transportation_types (
    type TEXT PRIMARY KEY,
    name JSONB,
    description JSONB,
    icon TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Populate transportation_types table with initial data
INSERT INTO transportation_types (type, name, description, icon)
VALUES
    ('train', 
     '{"en": "Train", "ar": "قطار"}',
     '{"en": "Rail transportation between cities", "ar": "النقل بالسكك الحديدية بين المدن"}',
     'train'),
    ('bus', 
     '{"en": "Bus", "ar": "حافلة"}',
     '{"en": "Intercity bus services", "ar": "خدمات الحافلات بين المدن"}',
     'bus'),
    ('domestic_flight', 
     '{"en": "Domestic Flight", "ar": "رحلة طيران داخلية"}',
     '{"en": "Air travel between Egyptian cities", "ar": "السفر الجوي بين المدن المصرية"}',
     'airplane'),
    ('ferry', 
     '{"en": "Ferry", "ar": "عبّارة"}',
     '{"en": "Water transportation across the Nile or other waterways", "ar": "النقل المائي عبر النيل أو الممرات المائية الأخرى"}',
     'ship'),
    ('nile_cruise', 
     '{"en": "Nile Cruise", "ar": "رحلة نيلية"}',
     '{"en": "Multi-day cruise ships traveling along the Nile River", "ar": "سفن الرحلات البحرية متعددة الأيام المسافرة على طول نهر النيل"}',
     'cruise'),
    ('taxi', 
     '{"en": "Taxi", "ar": "سيارة أجرة"}',
     '{"en": "Taxi services for shorter distances", "ar": "خدمات سيارات الأجرة للمسافات القصيرة"}',
     'taxi'),
    ('microbus', 
     '{"en": "Microbus", "ar": "ميكروباص"}',
     '{"en": "Small vans operating as shared taxis on fixed routes", "ar": "حافلات صغيرة تعمل كسيارات أجرة مشتركة على طرق ثابتة"}',
     'minibus'),
    ('car_rental', 
     '{"en": "Car Rental", "ar": "تأجير سيارات"}',
     '{"en": "Self-drive car rental services", "ar": "خدمات تأجير السيارات للقيادة الذاتية"}',
     'car'),
    ('private_transfer', 
     '{"en": "Private Transfer", "ar": "نقل خاص"}',
     '{"en": "Pre-arranged private transportation services", "ar": "خدمات النقل الخاصة المرتبة مسبقًا"}',
     'car-side'),
    ('camel_ride', 
     '{"en": "Camel Ride", "ar": "ركوب الجمل"}',
     '{"en": "Traditional camel transportation, primarily for tourists", "ar": "وسائل النقل التقليدية بالجمال، في المقام الأول للسياح"}',
     'camel')
ON CONFLICT (type) DO NOTHING;

-- 3. Create transportation_routes table
CREATE TABLE IF NOT EXISTS transportation_routes (
    id SERIAL PRIMARY KEY,
    origin_id TEXT NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    destination_id TEXT NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    transportation_type TEXT NOT NULL REFERENCES transportation_types(type),
    name JSONB,
    description JSONB,
    distance_km DOUBLE PRECISION,
    duration_minutes INTEGER,
    frequency JSONB,
    schedule JSONB,
    price_range JSONB,
    booking_info JSONB,
    amenities JSONB,
    tips JSONB,
    data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT,
    CONSTRAINT unique_route UNIQUE (origin_id, destination_id, transportation_type)
);

-- 4. Create indexes for transportation_routes table
CREATE INDEX IF NOT EXISTS idx_transportation_routes_origin_id ON transportation_routes (origin_id);
CREATE INDEX IF NOT EXISTS idx_transportation_routes_destination_id ON transportation_routes (destination_id);
CREATE INDEX IF NOT EXISTS idx_transportation_routes_transportation_type ON transportation_routes (transportation_type);
CREATE INDEX IF NOT EXISTS idx_transportation_routes_name_gin ON transportation_routes USING GIN (name);
CREATE INDEX IF NOT EXISTS idx_transportation_routes_description_gin ON transportation_routes USING GIN (description);
CREATE INDEX IF NOT EXISTS idx_transportation_routes_data_gin ON transportation_routes USING GIN (data);

-- 5. Create transportation_stations table
CREATE TABLE IF NOT EXISTS transportation_stations (
    id TEXT PRIMARY KEY,
    name JSONB NOT NULL,
    description JSONB,
    destination_id TEXT NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    station_type TEXT NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    address JSONB,
    contact_info JSONB,
    facilities JSONB,
    accessibility JSONB,
    data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT
);

-- 6. Create indexes for transportation_stations table
CREATE INDEX IF NOT EXISTS idx_transportation_stations_destination_id ON transportation_stations (destination_id);
CREATE INDEX IF NOT EXISTS idx_transportation_stations_station_type ON transportation_stations (station_type);
CREATE INDEX IF NOT EXISTS idx_transportation_stations_name_gin ON transportation_stations USING GIN (name);
CREATE INDEX IF NOT EXISTS idx_transportation_stations_description_gin ON transportation_stations USING GIN (description);
CREATE INDEX IF NOT EXISTS idx_transportation_stations_data_gin ON transportation_stations USING GIN (data);

-- 7. Create transportation_route_stations table (junction table)
CREATE TABLE IF NOT EXISTS transportation_route_stations (
    route_id INTEGER NOT NULL REFERENCES transportation_routes(id) ON DELETE CASCADE,
    station_id TEXT NOT NULL REFERENCES transportation_stations(id) ON DELETE CASCADE,
    stop_order INTEGER NOT NULL,
    arrival_offset_minutes INTEGER,
    departure_offset_minutes INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (route_id, station_id)
);

CREATE INDEX IF NOT EXISTS idx_transportation_route_stations_route_id ON transportation_route_stations (route_id);
CREATE INDEX IF NOT EXISTS idx_transportation_route_stations_station_id ON transportation_route_stations (station_id);

-- 8. Create function to find routes between destinations
CREATE OR REPLACE FUNCTION find_transportation_routes(
    p_origin_id TEXT,
    p_destination_id TEXT,
    p_transportation_type TEXT DEFAULT NULL
)
RETURNS TABLE (
    id INTEGER,
    origin_id TEXT,
    destination_id TEXT,
    transportation_type TEXT,
    name JSONB,
    description JSONB,
    distance_km DOUBLE PRECISION,
    duration_minutes INTEGER,
    price_range JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.origin_id,
        r.destination_id,
        r.transportation_type,
        r.name,
        r.description,
        r.distance_km,
        r.duration_minutes,
        r.price_range
    FROM 
        transportation_routes r
    WHERE 
        r.origin_id = p_origin_id
        AND r.destination_id = p_destination_id
        AND (p_transportation_type IS NULL OR r.transportation_type = p_transportation_type)
    ORDER BY 
        r.duration_minutes ASC;
END;
$$ LANGUAGE plpgsql;

-- 9. Create function to find all routes from a destination
CREATE OR REPLACE FUNCTION find_routes_from_destination(
    p_origin_id TEXT,
    p_transportation_type TEXT DEFAULT NULL
)
RETURNS TABLE (
    id INTEGER,
    origin_id TEXT,
    destination_id TEXT,
    destination_name JSONB,
    transportation_type TEXT,
    name JSONB,
    distance_km DOUBLE PRECISION,
    duration_minutes INTEGER,
    price_range JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.origin_id,
        r.destination_id,
        d.name AS destination_name,
        r.transportation_type,
        r.name,
        r.distance_km,
        r.duration_minutes,
        r.price_range
    FROM 
        transportation_routes r
    JOIN
        destinations d ON r.destination_id = d.id
    WHERE 
        r.origin_id = p_origin_id
        AND (p_transportation_type IS NULL OR r.transportation_type = p_transportation_type)
    ORDER BY 
        r.transportation_type, r.duration_minutes ASC;
END;
$$ LANGUAGE plpgsql;

-- 10. Create function to find all routes to a destination
CREATE OR REPLACE FUNCTION find_routes_to_destination(
    p_destination_id TEXT,
    p_transportation_type TEXT DEFAULT NULL
)
RETURNS TABLE (
    id INTEGER,
    origin_id TEXT,
    origin_name JSONB,
    destination_id TEXT,
    transportation_type TEXT,
    name JSONB,
    distance_km DOUBLE PRECISION,
    duration_minutes INTEGER,
    price_range JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.origin_id,
        d.name AS origin_name,
        r.destination_id,
        r.transportation_type,
        r.name,
        r.distance_km,
        r.duration_minutes,
        r.price_range
    FROM 
        transportation_routes r
    JOIN
        destinations d ON r.origin_id = d.id
    WHERE 
        r.destination_id = p_destination_id
        AND (p_transportation_type IS NULL OR r.transportation_type = p_transportation_type)
    ORDER BY 
        r.transportation_type, r.duration_minutes ASC;
END;
$$ LANGUAGE plpgsql;
