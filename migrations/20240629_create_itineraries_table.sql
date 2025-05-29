-- Migration: Create Itineraries Table
-- Date: 2024-06-29
-- Description: Create a table for suggested itineraries that combine multiple attractions

-- 1. Create itinerary_types table
CREATE TABLE IF NOT EXISTS itinerary_types (
    id TEXT PRIMARY KEY,
    name JSONB NOT NULL,
    description JSONB,
    icon TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Populate itinerary_types table with initial data
INSERT INTO itinerary_types (id, name, description, icon)
VALUES
    ('historical',
     '{"en": "Historical", "ar": "تاريخي"}',
     '{"en": "Itineraries focusing on historical sites and monuments", "ar": "مسارات تركز على المواقع والآثار التاريخية"}',
     'landmark'),
    ('cultural',
     '{"en": "Cultural", "ar": "ثقافي"}',
     '{"en": "Itineraries exploring Egyptian culture, arts, and traditions", "ar": "مسارات تستكشف الثقافة والفنون والتقاليد المصرية"}',
     'masks-theater'),
    ('religious',
     '{"en": "Religious", "ar": "ديني"}',
     '{"en": "Itineraries visiting religious sites and pilgrimage destinations", "ar": "مسارات تزور المواقع الدينية ووجهات الحج"}',
     'place-of-worship'),
    ('natural',
     '{"en": "Natural", "ar": "طبيعي"}',
     '{"en": "Itineraries exploring Egypt''s natural landscapes and wildlife", "ar": "مسارات تستكشف المناظر الطبيعية والحياة البرية في مصر"}',
     'mountain'),
    ('adventure',
     '{"en": "Adventure", "ar": "مغامرة"}',
     '{"en": "Itineraries for adventure seekers and outdoor enthusiasts", "ar": "مسارات لمحبي المغامرة وهواة الأنشطة الخارجية"}',
     'person-hiking'),
    ('family',
     '{"en": "Family", "ar": "عائلي"}',
     '{"en": "Itineraries suitable for families with children", "ar": "مسارات مناسبة للعائلات مع الأطفال"}',
     'people-group'),
    ('luxury',
     '{"en": "Luxury", "ar": "فاخر"}',
     '{"en": "High-end itineraries with premium experiences", "ar": "مسارات راقية مع تجارب متميزة"}',
     'crown'),
    ('budget',
     '{"en": "Budget", "ar": "اقتصادي"}',
     '{"en": "Affordable itineraries for budget-conscious travelers", "ar": "مسارات بأسعار معقولة للمسافرين الحريصين على الميزانية"}',
     'money-bill'),
    ('short_stay',
     '{"en": "Short Stay", "ar": "إقامة قصيرة"}',
     '{"en": "Itineraries for travelers with limited time", "ar": "مسارات للمسافرين ذوي الوقت المحدود"}',
     'clock'),
    ('extended',
     '{"en": "Extended", "ar": "ممتد"}',
     '{"en": "Comprehensive itineraries for longer stays", "ar": "مسارات شاملة للإقامات الطويلة"}',
     'calendar-days')
ON CONFLICT (id) DO NOTHING;

-- 3. Create itineraries table
CREATE TABLE IF NOT EXISTS itineraries (
    id SERIAL PRIMARY KEY,
    type_id TEXT NOT NULL REFERENCES itinerary_types(id) ON DELETE CASCADE,
    name JSONB NOT NULL,
    description JSONB NOT NULL,
    duration_days INTEGER NOT NULL,
    regions TEXT[],
    cities TEXT[],
    attractions TEXT[],
    restaurants TEXT[],
    accommodations TEXT[],
    transportation_types TEXT[],
    daily_plans JSONB NOT NULL,
    budget_range JSONB,
    best_seasons TEXT[],
    difficulty_level TEXT,
    target_audience JSONB,
    highlights JSONB,
    practical_tips JSONB,
    images JSONB,
    tags TEXT[],
    is_featured BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    rating NUMERIC(3,2),
    data JSONB DEFAULT '{}'::jsonb,
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT
);

-- 4. Create indexes for itineraries table
CREATE INDEX IF NOT EXISTS idx_itineraries_type_id ON itineraries (type_id);
CREATE INDEX IF NOT EXISTS idx_itineraries_name_gin ON itineraries USING GIN (name);
CREATE INDEX IF NOT EXISTS idx_itineraries_description_gin ON itineraries USING GIN (description);
CREATE INDEX IF NOT EXISTS idx_itineraries_duration_days ON itineraries (duration_days);
CREATE INDEX IF NOT EXISTS idx_itineraries_regions ON itineraries USING GIN (regions array_ops);
CREATE INDEX IF NOT EXISTS idx_itineraries_cities ON itineraries USING GIN (cities array_ops);
CREATE INDEX IF NOT EXISTS idx_itineraries_attractions ON itineraries USING GIN (attractions array_ops);
CREATE INDEX IF NOT EXISTS idx_itineraries_tags ON itineraries USING GIN (tags array_ops);
CREATE INDEX IF NOT EXISTS idx_itineraries_is_featured ON itineraries (is_featured);
CREATE INDEX IF NOT EXISTS idx_itineraries_embedding_hnsw ON itineraries USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64');

-- 5. Create function to search itineraries by text
CREATE OR REPLACE FUNCTION search_itineraries(
    p_query TEXT,
    p_type_id TEXT DEFAULT NULL,
    p_duration_min INTEGER DEFAULT NULL,
    p_duration_max INTEGER DEFAULT NULL,
    p_region TEXT DEFAULT NULL,
    p_city TEXT DEFAULT NULL,
    p_attraction TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    type_id TEXT,
    type_name JSONB,
    name JSONB,
    description JSONB,
    duration_days INTEGER,
    regions TEXT[],
    cities TEXT[],
    attractions TEXT[],
    budget_range JSONB,
    difficulty_level TEXT,
    is_featured BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.id,
        i.type_id,
        t.name AS type_name,
        i.name,
        i.description,
        i.duration_days,
        i.regions,
        i.cities,
        i.attractions,
        i.budget_range,
        i.difficulty_level,
        i.is_featured
    FROM
        itineraries i
    JOIN
        itinerary_types t ON i.type_id = t.id
    WHERE
        (p_type_id IS NULL OR i.type_id = p_type_id)
        AND (p_duration_min IS NULL OR i.duration_days >= p_duration_min)
        AND (p_duration_max IS NULL OR i.duration_days <= p_duration_max)
        AND (p_region IS NULL OR p_region = ANY(i.regions))
        AND (p_city IS NULL OR p_city = ANY(i.cities))
        AND (p_attraction IS NULL OR p_attraction = ANY(i.attractions))
        AND (
            p_query IS NULL
            OR to_tsvector('english', i.name->>'en') @@ plainto_tsquery('english', p_query)
            OR to_tsvector('english', i.description->>'en') @@ plainto_tsquery('english', p_query)
            OR p_query = ANY(i.tags)
        )
    ORDER BY
        i.is_featured DESC,
        i.rating DESC NULLS LAST,
        i.view_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 6. Create function to get itineraries by type
CREATE OR REPLACE FUNCTION get_itineraries_by_type(
    p_type_id TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    name JSONB,
    description JSONB,
    duration_days INTEGER,
    regions TEXT[],
    cities TEXT[],
    attractions TEXT[],
    budget_range JSONB,
    difficulty_level TEXT,
    is_featured BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.id,
        i.name,
        i.description,
        i.duration_days,
        i.regions,
        i.cities,
        i.attractions,
        i.budget_range,
        i.difficulty_level,
        i.is_featured
    FROM
        itineraries i
    WHERE
        i.type_id = p_type_id
    ORDER BY
        i.is_featured DESC,
        i.rating DESC NULLS LAST,
        i.view_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 7. Create function to get featured itineraries
CREATE OR REPLACE FUNCTION get_featured_itineraries(
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    type_id TEXT,
    type_name JSONB,
    name JSONB,
    description JSONB,
    duration_days INTEGER,
    regions TEXT[],
    cities TEXT[],
    attractions TEXT[],
    budget_range JSONB,
    difficulty_level TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.id,
        i.type_id,
        t.name AS type_name,
        i.name,
        i.description,
        i.duration_days,
        i.regions,
        i.cities,
        i.attractions,
        i.budget_range,
        i.difficulty_level
    FROM
        itineraries i
    JOIN
        itinerary_types t ON i.type_id = t.id
    WHERE
        i.is_featured = TRUE
    ORDER BY
        i.rating DESC NULLS LAST,
        i.view_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 8. Create function to get itineraries by region
CREATE OR REPLACE FUNCTION get_itineraries_by_region(
    p_region TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    type_id TEXT,
    type_name JSONB,
    name JSONB,
    description JSONB,
    duration_days INTEGER,
    cities TEXT[],
    attractions TEXT[],
    budget_range JSONB,
    difficulty_level TEXT,
    is_featured BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.id,
        i.type_id,
        t.name AS type_name,
        i.name,
        i.description,
        i.duration_days,
        i.cities,
        i.attractions,
        i.budget_range,
        i.difficulty_level,
        i.is_featured
    FROM
        itineraries i
    JOIN
        itinerary_types t ON i.type_id = t.id
    WHERE
        p_region = ANY(i.regions)
    ORDER BY
        i.is_featured DESC,
        i.rating DESC NULLS LAST,
        i.view_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
