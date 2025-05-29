-- Migration: Update Functions to Use Junction Tables
-- Date: 2025-07-15
-- Purpose: Update database functions to use junction tables instead of array columns

BEGIN;

-- Log the migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting migration to update functions for junction tables';
END $$;

-- 1. Update search_faqs function to use tourism_faq_destinations
DROP FUNCTION IF EXISTS search_faqs(text, text, text, integer);
CREATE OR REPLACE FUNCTION search_faqs(
    p_query TEXT,
    p_category_id TEXT DEFAULT NULL,
    p_destination_id TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    category_id TEXT,
    category_name JSONB,
    question JSONB,
    answer JSONB,
    tags TEXT[],
    is_featured BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.id,
        f.category_id,
        c.name AS category_name,
        f.question,
        f.answer,
        f.tags,
        f.is_featured
    FROM 
        tourism_faqs f
    JOIN
        faq_categories c ON f.category_id = c.id
    LEFT JOIN
        tourism_faq_destinations fd ON f.id = fd.tourism_faq_id
    WHERE 
        (p_category_id IS NULL OR f.category_id = p_category_id)
        AND (p_destination_id IS NULL OR 
             (p_destination_id::INTEGER = fd.destination_id))
        AND (
            to_tsvector('english', f.question->>'en') @@ plainto_tsquery('english', p_query)
            OR to_tsvector('english', f.answer->>'en') @@ plainto_tsquery('english', p_query)
            OR p_query = ANY(f.tags)
        )
    ORDER BY 
        f.is_featured DESC,
        f.helpful_count DESC,
        f.view_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 2. Update get_faqs_by_destination function to use tourism_faq_destinations
DROP FUNCTION IF EXISTS get_faqs_by_destination(text, integer);
CREATE OR REPLACE FUNCTION get_faqs_by_destination(
    p_destination_id TEXT,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    id INTEGER,
    category_id TEXT,
    category_name JSONB,
    question JSONB,
    answer JSONB,
    is_featured BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.id,
        f.category_id,
        c.name AS category_name,
        f.question,
        f.answer,
        f.is_featured
    FROM 
        tourism_faqs f
    JOIN
        faq_categories c ON f.category_id = c.id
    JOIN
        tourism_faq_destinations fd ON f.id = fd.tourism_faq_id
    WHERE 
        fd.destination_id = p_destination_id::INTEGER
    ORDER BY 
        f.is_featured DESC,
        f.helpful_count DESC,
        f.view_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 3. Update get_tour_packages_by_destination function to use tour_package_destinations
DROP FUNCTION IF EXISTS get_tour_packages_by_destination(text, integer);
CREATE OR REPLACE FUNCTION get_tour_packages_by_destination(
    p_destination_id TEXT,
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
    JOIN
        tour_package_destinations pd ON p.id = pd.tour_package_id
    WHERE 
        pd.destination_id = p_destination_id::INTEGER
    ORDER BY 
        p.is_featured DESC,
        p.rating DESC,
        p.booking_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 4. Update search_tour_packages function to use tour_package_destinations
DROP FUNCTION IF EXISTS search_tour_packages(text, text, text, integer, integer, numeric, integer);
CREATE OR REPLACE FUNCTION search_tour_packages(
    p_query TEXT,
    p_category_id TEXT DEFAULT NULL,
    p_destination_id TEXT DEFAULT NULL,
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
    rating NUMERIC,
    is_featured BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
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
    LEFT JOIN
        tour_package_destinations pd ON p.id = pd.tour_package_id
    WHERE 
        (p_category_id IS NULL OR p.category_id = p_category_id)
        AND (p_destination_id IS NULL OR 
             (p_destination_id::INTEGER = pd.destination_id))
        AND (p_min_duration IS NULL OR p.duration_days >= p_min_duration)
        AND (p_max_duration IS NULL OR p.duration_days <= p_max_duration)
        AND (p_min_rating IS NULL OR p.rating >= p_min_rating)
        AND (
            p_query IS NULL
            OR to_tsvector('english', p.name->>'en') @@ plainto_tsquery('english', p_query)
            OR to_tsvector('english', p.description->>'en') @@ plainto_tsquery('english', p_query)
        )
    ORDER BY 
        p.is_featured DESC,
        p.rating DESC NULLS LAST,
        p.booking_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 5. Update get_itineraries_by_region function to use itinerary_cities
DROP FUNCTION IF EXISTS get_itineraries_by_region(text, integer);
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
    budget_range JSONB,
    difficulty_level TEXT,
    is_featured BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        i.id,
        i.type_id,
        t.name AS type_name,
        i.name,
        i.description,
        i.duration_days,
        i.budget_range,
        i.difficulty_level,
        i.is_featured
    FROM
        itineraries i
    JOIN
        itinerary_types t ON i.type_id = t.id
    JOIN
        itinerary_cities ic ON i.id = ic.itinerary_id
    JOIN
        cities c ON ic.city_id = c.id
    WHERE
        c.region_id = p_region::INTEGER
    ORDER BY
        i.is_featured DESC,
        i.rating DESC NULLS LAST,
        i.view_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Log the migration completion
DO $$
BEGIN
    RAISE NOTICE 'Function updates for junction tables completed successfully';
END $$;

COMMIT;
