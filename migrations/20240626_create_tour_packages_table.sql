-- Migration: Create Tour Packages Table
-- Date: 2024-06-26
-- Description: Create a table for tour packages in Egypt

-- 1. Create tour_package_categories table
CREATE TABLE IF NOT EXISTS tour_package_categories (
    id TEXT PRIMARY KEY,
    name JSONB NOT NULL,
    description JSONB,
    icon TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Populate tour_package_categories table with initial data
INSERT INTO tour_package_categories (id, name, description, icon)
VALUES
    ('classic_tours', 
     '{"en": "Classic Egypt Tours", "ar": "جولات مصر الكلاسيكية"}',
     '{"en": "Traditional tours covering the main historical sites of Egypt", "ar": "جولات تقليدية تغطي المواقع التاريخية الرئيسية في مصر"}',
     'landmark'),
    ('nile_cruises', 
     '{"en": "Nile Cruises", "ar": "رحلات النيل النهرية"}',
     '{"en": "Cruises along the Nile River between Luxor and Aswan", "ar": "رحلات بحرية على طول نهر النيل بين الأقصر وأسوان"}',
     'ship'),
    ('desert_adventures', 
     '{"en": "Desert Adventures", "ar": "مغامرات الصحراء"}',
     '{"en": "Tours exploring the Western Desert, oases, and desert landscapes", "ar": "جولات استكشافية في الصحراء الغربية والواحات والمناظر الطبيعية الصحراوية"}',
     'mountain'),
    ('beach_holidays', 
     '{"en": "Beach Holidays", "ar": "عطلات الشاطئ"}',
     '{"en": "Relaxing holidays at Red Sea and Mediterranean resorts", "ar": "عطلات استرخاء في منتجعات البحر الأحمر والبحر المتوسط"}',
     'umbrella-beach'),
    ('cultural_experiences', 
     '{"en": "Cultural Experiences", "ar": "تجارب ثقافية"}',
     '{"en": "Immersive tours focusing on Egyptian culture, cuisine, and traditions", "ar": "جولات غامرة تركز على الثقافة المصرية والمطبخ والتقاليد"}',
     'masks-theater'),
    ('family_tours', 
     '{"en": "Family Tours", "ar": "جولات عائلية"}',
     '{"en": "Tours designed specifically for families with children", "ar": "جولات مصممة خصيصًا للعائلات مع الأطفال"}',
     'people-group'),
    ('luxury_tours', 
     '{"en": "Luxury Tours", "ar": "جولات فاخرة"}',
     '{"en": "High-end tours with premium accommodations and exclusive experiences", "ar": "جولات راقية مع أماكن إقامة فاخرة وتجارب حصرية"}',
     'crown'),
    ('adventure_tours', 
     '{"en": "Adventure Tours", "ar": "جولات المغامرة"}',
     '{"en": "Active tours including hiking, diving, and other adventure activities", "ar": "جولات نشطة تشمل المشي لمسافات طويلة والغوص وأنشطة المغامرة الأخرى"}',
     'person-hiking'),
    ('religious_tours', 
     '{"en": "Religious Tours", "ar": "جولات دينية"}',
     '{"en": "Tours focusing on religious sites and pilgrimages in Egypt", "ar": "جولات تركز على المواقع الدينية والحج في مصر"}',
     'place-of-worship')
ON CONFLICT (id) DO NOTHING;

-- 3. Create tour_packages table
CREATE TABLE IF NOT EXISTS tour_packages (
    id SERIAL PRIMARY KEY,
    category_id TEXT NOT NULL REFERENCES tour_package_categories(id) ON DELETE CASCADE,
    name JSONB NOT NULL,
    description JSONB NOT NULL,
    duration_days INTEGER NOT NULL,
    price_range JSONB NOT NULL,
    included_services JSONB NOT NULL,
    excluded_services JSONB,
    itinerary JSONB NOT NULL,
    destinations TEXT[] NOT NULL,
    attractions TEXT[],
    accommodations TEXT[],
    transportation_types TEXT[],
    min_group_size INTEGER,
    max_group_size INTEGER,
    difficulty_level TEXT,
    accessibility_info JSONB,
    seasonal_info JSONB,
    booking_info JSONB,
    cancellation_policy JSONB,
    reviews JSONB,
    rating NUMERIC(3,2),
    images JSONB,
    tags TEXT[],
    is_featured BOOLEAN DEFAULT FALSE,
    is_private BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    booking_count INTEGER DEFAULT 0,
    data JSONB DEFAULT '{}'::jsonb,
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT
);

-- 4. Create indexes for tour_packages table
CREATE INDEX IF NOT EXISTS idx_tour_packages_category_id ON tour_packages (category_id);
CREATE INDEX IF NOT EXISTS idx_tour_packages_name_gin ON tour_packages USING GIN (name);
CREATE INDEX IF NOT EXISTS idx_tour_packages_description_gin ON tour_packages USING GIN (description);
CREATE INDEX IF NOT EXISTS idx_tour_packages_destinations ON tour_packages USING GIN (destinations array_ops);
CREATE INDEX IF NOT EXISTS idx_tour_packages_attractions ON tour_packages USING GIN (attractions array_ops);
CREATE INDEX IF NOT EXISTS idx_tour_packages_tags ON tour_packages USING GIN (tags array_ops);
CREATE INDEX IF NOT EXISTS idx_tour_packages_duration_days ON tour_packages (duration_days);
CREATE INDEX IF NOT EXISTS idx_tour_packages_is_featured ON tour_packages (is_featured);
CREATE INDEX IF NOT EXISTS idx_tour_packages_rating ON tour_packages (rating);
CREATE INDEX IF NOT EXISTS idx_tour_packages_embedding_hnsw ON tour_packages USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64');

-- 5. Create function to search tour packages by text
CREATE OR REPLACE FUNCTION search_tour_packages(
    p_query TEXT,
    p_category_id TEXT DEFAULT NULL,
    p_destination TEXT DEFAULT NULL,
    p_min_duration INTEGER DEFAULT NULL,
    p_max_duration INTEGER DEFAULT NULL,
    p_min_rating NUMERIC DEFAULT NULL,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    category_id TEXT,
    category_name JSONB,
    name JSONB,
    description JSONB,
    duration_days INTEGER,
    price_range JSONB,
    destinations TEXT[],
    rating NUMERIC,
    is_featured BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.category_id,
        c.name AS category_name,
        p.name,
        p.description,
        p.duration_days,
        p.price_range,
        p.destinations,
        p.rating,
        p.is_featured
    FROM 
        tour_packages p
    JOIN
        tour_package_categories c ON p.category_id = c.id
    WHERE 
        (p_category_id IS NULL OR p.category_id = p_category_id)
        AND (p_destination IS NULL OR p_destination = ANY(p.destinations))
        AND (p_min_duration IS NULL OR p.duration_days >= p_min_duration)
        AND (p_max_duration IS NULL OR p.duration_days <= p_max_duration)
        AND (p_min_rating IS NULL OR p.rating >= p_min_rating)
        AND (
            p_query IS NULL
            OR to_tsvector('english', p.name->>'en') @@ plainto_tsquery('english', p_query)
            OR to_tsvector('english', p.description->>'en') @@ plainto_tsquery('english', p_query)
            OR p_query = ANY(p.tags)
        )
    ORDER BY 
        p.is_featured DESC,
        p.rating DESC,
        p.booking_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 6. Create function to get tour packages by category
CREATE OR REPLACE FUNCTION get_tour_packages_by_category(
    p_category_id TEXT,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id INTEGER,
    name JSONB,
    description JSONB,
    duration_days INTEGER,
    price_range JSONB,
    destinations TEXT[],
    rating NUMERIC,
    is_featured BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.name,
        p.description,
        p.duration_days,
        p.price_range,
        p.destinations,
        p.rating,
        p.is_featured
    FROM 
        tour_packages p
    WHERE 
        p.category_id = p_category_id
    ORDER BY 
        p.is_featured DESC,
        p.rating DESC,
        p.booking_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 7. Create function to get tour packages by destination
CREATE OR REPLACE FUNCTION get_tour_packages_by_destination(
    p_destination TEXT,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id INTEGER,
    category_id TEXT,
    category_name JSONB,
    name JSONB,
    description JSONB,
    duration_days INTEGER,
    price_range JSONB,
    rating NUMERIC,
    is_featured BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.category_id,
        c.name AS category_name,
        p.name,
        p.description,
        p.duration_days,
        p.price_range,
        p.rating,
        p.is_featured
    FROM 
        tour_packages p
    JOIN
        tour_package_categories c ON p.category_id = c.id
    WHERE 
        p_destination = ANY(p.destinations)
    ORDER BY 
        p.is_featured DESC,
        p.rating DESC,
        p.booking_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 8. Create function to get featured tour packages
CREATE OR REPLACE FUNCTION get_featured_tour_packages(
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    category_id TEXT,
    category_name JSONB,
    name JSONB,
    description JSONB,
    duration_days INTEGER,
    price_range JSONB,
    destinations TEXT[],
    rating NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.category_id,
        c.name AS category_name,
        p.name,
        p.description,
        p.duration_days,
        p.price_range,
        p.destinations,
        p.rating
    FROM 
        tour_packages p
    JOIN
        tour_package_categories c ON p.category_id = c.id
    WHERE 
        p.is_featured = TRUE
    ORDER BY 
        p.rating DESC,
        p.booking_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
